import requests
import pandas as pd
from collections import Counter
from io import StringIO
import os.path
class Accessor:
    '''
    Class for access to databases and manipulations with dataframe objects.
    Uses FlyBase and Uniprot.
    self.frame is main object. Its values are tuples.
    protlist is a list of proteins or genes.
    'fields' is list of requested columns (database-dependent)
    '''
    up_url='http://www.uniprot.org/uploadlists/'
    fb_url='http://flybase.org/cgi-bin/fbidbatch.html'
    #columns of uniprot tables separated by a space or comma:
    badcols={' ': ['Gene names (ORF)'], ',':['yourlist']}
    def __init__(self, frame=None):
        self.frame=frame
        self.statuscode=None

    def access(self, DB, protlist, fields,**kargs):
        '''
        Method to get access to databases and create dataframe
        '''
        protlist=' '.join(protlist)
        if DB=='uniprot':
            self.frame=self.up_getframe(protlist, fields, **kargs)
        elif DB=='flybase':
            self.frame=self.fb_getframe(protlist, fields, **kargs)
        return self.statuscode

####################################method for uniprot DB###################
            
    def up_getframe(self,protlist,fields,**kargs):
        '''
        kargs are additional parameters for params
        '''
        fields=','.join(fields)
        params = {
            'from':'GENENAME',
            'to':'ACC',
            'format':'tab',
            'query':protlist,
            'taxon': '7227',
            'columns':fields
            }
        params.update(kargs)
        req=requests.get(self.up_url, params)
        self.statuscode=req.status_code
        frame=pd.read_csv(StringIO(req.text), sep='\t',dtype=str)
        newcols=[x.split(':')[0] for x in frame.columns] #delete excess symbols in columns
        frame.columns=newcols
        frame.drop('isomap',1,inplace=True) #delete excess column
        yrl=newcols.pop(newcols.index('yourlist'))
        newcols.remove('isomap')
        newcols.insert(0,yrl) #column 'yourlist' muts be the first
        frame=frame[newcols]
        #data in some fields are separated by spaces or commas. Fix:
        frame=frame.fillna('-')
        for col in frame.columns:
            for i in self.badcols.keys():
                if col in self.badcols[i]:
                    frame[col]=frame[col].apply(lambda x: ';'.join(x.replace('Dmel_','').split(i)))
        frame=Accessor.processable(frame, sep=';', delappendix=['[GO:'])
        #if there are several items in a row of 'yourlist' -
        #split them into several rows.
        while frame['yourlist'].map(lambda x:len(x)>1).any():
            crit=frame['yourlist'].map(lambda x:len(x)>1)
            piece=frame[crit].copy()
            frame.loc[:,'yourlist'][crit]=frame.loc[:,'yourlist'][crit].map(lambda x:x[:1])           
            piece['yourlist']=piece['yourlist'].map(lambda x:x[1:])
            frame=frame.append(piece)
        return frame
    
#######################method for flybase DB##################################

    def fb_getframe(self, protlist, fields, **kargs):
        params={'fields': fields,
                'idlist': protlist,
                'dbname':'fbgn',
                'sel':'fields',
                'allow_syn':'allow_syn',
                'format3':'tsv_file',
                'saveas':'Browser'}
        params.update(kargs)
        req=requests.post(self.fb_url, data=params)
        self.statuscode=req.status_code
        frame=pd.read_csv(StringIO(req.text),sep='\t', dtype=str)
        frame=Accessor.processable(frame, sep=' <newline> ', delappendix=[' ; ',' - unknown ID'])
        return frame

############abstract methods to change dataframe##############################
    
    def termsfreq(frame):
        '''
        Gets dataframe with list elements
        to create new dataframe with terms frequencies
        '''
        #proceding dataframe
        result=frame.sum() # to make united lists in columns  
        result=[Counter(x).most_common() for x in result]
        result=[list(zip(*x)) for x in result]
        result=sum(result,[]) #concatenate inner lists
        result=pd.DataFrame(result).T
        result=Accessor.processable(result,na_rep='')
        #making new header
        #L=frame.columns.tolist()
        L=[[x,'Freq_'+x] for x in frame.columns]
        L=sum(L,[])
        result.columns=L
        return result

    def writeable(frame):
        '''
        Gets dataframe with list elements
        to create new dataframe with strings of '; '-separated terms
        '''
        return frame.applymap(lambda x: '; '.join(x))

    def processable(frame, sep=';', removerep=True, tosort=True,
                    delappendix=None, fillna=True, na_rep='-'):
        '''
        Makes frame with tuple elements from frame with elements separated by sep.
        removerep and tosort - if repeates must be removed in tuples and elements
        to be sorted. delappendix is a list of strings: the end of string in a tuple beginning
        with the pointed strings must be deleted. fillna: whether to fill nan with '-'.
        Applies processcell function.
        '''
        if fillna:
            procframe=frame.fillna(na_rep)
        else:
            procframe=frame.copy()

        def processcell(cell):
            '''
            Nested function for processable to use in applymap method of dataframe.
            Corrects individual cells.
            '''
            cellist=str(cell).split(sep)
            if delappendix:
                for dlp in delappendix:
                    cellist=[x.split(dlp)[0].strip() for x in cellist]
            else:
                cellist=[x.strip() for x in cellist]

            if removerep and tosort:
                cellist=sorted(list(set(cellist)),key=str.upper)
            elif tosort:
                cellist.sort(key=str.upper)
            elif removerep:
                unique=[]
                for i in cellist:
                    if i not in unique: unique.append(i)
                cellist=unique
            celltuple=tuple(cellist)
            return celltuple   

        return procframe.applymap(processcell)

    def removedupl(frame,framecol):
        '''
        For removing duplicates in a column. All data in other columns
        are united in tuples (with repeats removal)
        '''
        def correct(cell):
            res=sorted(list(set(cell)))
            if '-' in res and len(res)>1:
                res.remove('-')
            return tuple(res)
        res=frame.groupby(framecol,sort=False, as_index=False).sum()
        res=res.applymap(correct)
        return res

    def order(frame,framecol,tocol):
        '''
        Function for ordering dataframe lines in a defined way.
        framecol - string name of frame column, tocol - list with
        needed order.
        '''
        frame=Accessor.removedupl(frame,framecol)
        order=tuple((x,) for x in tocol)
        order=pd.DataFrame({framecol:order})
        res=pd.merge(order,frame,how='left')
        res=res.fillna('-')
        res=res.applymap(tuple)
        return res

    def uniteframes(frameslist,framesrow):
        '''
        Unite several tables into one.
        '''
        res=frameslist[0]
        for frame in frameslist[1:]:
            res=pd.merge(res,frame,how='outer')
            res=res.fillna('-')
            res=res.applymap(tuple)
            res=Accessor.removedupl(res, framesrow)            
        return res
        


