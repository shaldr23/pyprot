from tkinter import *
from tkinter.filedialog import *
from tkinter.messagebox import *
from pyprotlib.popupmenu import PopupMenu
from pyprotlib.scrolledtext import ScrolledText
from pyprotlib.accessor7 import *
from pyprotlib.guithreads import *
from pyprotlib.multirename import Multirename
import re
import sys
import os.path

############### save-open-close functions #############################################

def on_closing():
    if askokcancel("Quit Program", "Do you want to quit?"):
        root.destroy()
        
def saveinfile():
    frameslist=[]
    for i in range(len(tablesdict['var'])):
        if tablesdict['var'][i].get()==1:
            frameslist.append((tablesdict['frame'][i],tablesdict['name'][i]))
    if not frameslist: 
        writelog('No table to save.')
    else:
        filename = asksaveasfilename(initialdir='/', title='Save your table',
                               filetypes = (('text file','*.txt'),
                                            ('csv file','*.csv'),
                                            ('excel file','*.xlsx')),
                               defaultextension=".")
        if not filename:
            writelog("You didn't save any table.")
        else:
            Threader(writeframes, frameslist, filename)
        

def openfile():
    filename=askopenfilename()
    if not filename:
        writelog("You didn't open any file.")
    else:
        Threader(readframes, filename)

##### logical functions for saving and opening tables used in own thread ###############

def writeframes(frames, filename):
    '''
    frames is a list of frames (like frameslist): [(frame1,name1),...]
    filetypes: 'excel', 'csv', 'txt'.txt is tab-separated csv.
    In case of 'excel' all chosen tables are written
    into different sheets. In other cases - into different
    files with table names added to their names.
    '''
    message='Tables have been saved.'
    wframes=[(Accessor.writeable(frame),name) for (frame,name) in frames]
    root, ext=os.path.splitext(filename)
    try:
        if ext=='.xlsx':
            writer = pd.ExcelWriter(filename)
            for frame, name in wframes:          
                frame.to_excel(writer,name, index=False)
            writer.save()
        elif ext in ('.csv','.txt',''):
            D={'.csv':',', '.txt':'\t','':'\t'}
            for frame, name in wframes:
                appendix='' if len(wframes)==1 else '({})'.format(name)
                savename=root+appendix+ext
                frame.to_csv(savename, sep=D[ext], index=False)
        else:
            message='Unknown format for saving'
    except:
        message='Error occured during saving tables'
    guiqueue.put((writelog,message))

def readframes(filename):
    '''
    opens file on PC and makes dataframe,
    saving into 
    '''
    message='Tables have been read.'
    root,ext=os.path.splitext(filename)
    try:
        if ext in ('.xlsx','.xls'):
            obj = pd.ExcelFile(filename)
            frames=[(obj.parse(sheet),sheet) for sheet in obj.sheet_names]
            frames=[x for x in frames if not x[0].empty]#remove empty frames
        elif ext in ('.csv','.txt',''):
            D={'.csv':',', '.txt':'\t', '':'\t'}
            tablename=os.path.split(root)[1]
            frames=[(pd.read_csv(filename, sep=D[ext]),tablename)]
        else:
            message='Unknown file format.'
    except:
        message='Error occured during opening tables.'
    frames=[(Accessor.processable(frame),name) for (frame,name) in frames]
    guiqueue.put((writelog,message))
    guiqueue.put((createcheckbuts, frames))


##############defining variables########################

log=[] #for logging

databases=[('FlyBase','flybase'),
           ('UniProt','uniprot')]

fields=['gene name',
        'molecular function',
        'biological process',
        'cellular component',
        'interactions',
        'length',
        'mass (kDa)',
        'CG* id']

entrytypes=['gene name',
            'protein name',
            'CG* id',
            'uniprot id',
            'flybase id',
            'auto-determine']

lognum=0 #number of a new log note
tablesdict={i:[] for i in ('name','frame','var','chbut')} #dictionary of lists for existing tables
                                                          #and associated elemens.


guiqueue=queue.Queue() #queue to change gui in main thread

workdir=os.path.split(sys.argv[0])[0]   #path of working directory

iconpath=os.path.join(workdir,'images/PY-UP2.ico')  #path of the icon

####### vars for database-associated fields to restrict inaccessible ones #################

accord=pd.read_csv('db_columns.txt',sep='\t')
accord=accord[accord['gui'].notnull()]
fbaccessible=accord['gui'][accord['fb_req'].notnull()].values
upaccessible=accord['gui'][accord['up_req'].notnull()].values

######## dictionary for renaming output columns ################################

renamecoldict={}
for colname in ('fb_col','up_col'):
    res=accord[accord[colname].notnull()]
    D=dict(zip(res[colname].values,res['gui'].values))
    renamecoldict.update(D)

####################functions############################
    #def __init__(self, DB, protlist, **kargs):



###############################################

def getdata():
    '''
    Function to get access to protein databases.
    Executes another function in another thread.
    '''
    def action():
        prots=prottext.get(1.0,END).strip()
        if not prots:
            guiqueue.put((writelog,'No query has been entered.'))
        else:
            protlist=re.split('\s+', prots) #get protlist from text
            Acc=Accessor()
            Acc.access(dbvar.get(),protlist,getfields())
            frame=Acc.frame.rename(columns=renamecoldict)
            # In case of uniprot: all entry names get upper case.
            # Fixing it (considering the situation may change):
            if dbvar.get()=='uniprot':
                upentries=[x[0] for x in frame['query'].values]
                protdict={x.upper():x for x in protlist}
                frame['query']=[(protdict[x.upper()],) for x in upentries]
            if keepordervar.get():
                frame=Accessor.order(frame,'query',protlist)
            # Make uniform order in columns:
            ordcols=[x for x in ['query']+fields if x in frame.columns]
            frame=frame[ordcols]
            guiqueue.put((createcheckbuts,[(frame,dbvar.get())]))
    def getfields():
        reqcol='up_req' if dbvar.get()=='uniprot' else 'fb_req'
        fieldslist=[fieldsdict['name'][i] for i
                    in range(len(fieldsdict['name']))
                    if fieldsdict['var'][i].get()==1]
        fieldslist=list(accord[reqcol][accord['gui'].isin(fieldslist)])
        return fieldslist
    Threader(action)


def deltables(*args):
    '''
    Function for deletion chosen tables by checkbuttons
    Executed in gui thread
    '''
    names=[]
    L=(len(tablesdict['var']))
    for i in range(L-1,-1,-1): #running from end to escape 'out of range' error
        if tablesdict['var'][i].get()==1:
            tablesdict['chbut'][i].pack_forget()
            names.append(tablesdict['name'][i])
            for key in tablesdict.keys():
                tablesdict[key].pop(i)
    if names:
        message='Tables have been deleted: {}.'.format(', '.join(reversed(names)))
    else:
        message='No tables have been chosen for deletion.'
    writelog(message)
                           
def unitetables():
    '''
    Funtion for making union of tables. Implements Accessor.uniteframes.
    '''
    def action():
        frameslist,nameslist=[],[]
        for frame,name,var in zip(tablesdict['frame'],
                                  tablesdict['name'],tablesdict['var']):
            if var.get():
                frameslist.append(frame)
                nameslist.append(name)

        if len(frameslist)<2:
            message='Unable to unite. At least two tables must be selected'
        else:
            united=Accessor.uniteframes(frameslist,'query')
            message='Union of tables has been made: {}'.format(', '.join(nameslist))
            guiqueue.put((createcheckbuts, [(united,'united')]))
        guiqueue.put((writelog, message))
    Threader(action)

def termsfreq():
    '''
    Function for making terms frequencies. Implements Accessor.termsfreq. 
    '''
    def action():
        frameslist=[]
        for frame,name,var in zip(tablesdict['frame'],
                                  tablesdict['name'],tablesdict['var']):
            if var.get():
                frameslist.append([Accessor.termsfreq(frame),name+'_tf'])
        guiqueue.put((createcheckbuts, frameslist))
    Threader(action)
    
def renametables():
    '''
    Function for renaming tables.
    '''
    def action():
        newnames=M.getnewnames()
        tablesdict['name']=[newnames.get(x,x) for x in tablesdict['name']]
        for i in range(len(tablesdict['name'])):
            tablesdict['chbut'][i].config(text=tablesdict['name'][i])
        Top.destroy()
        diff={x:y for (x,y) in newnames.items() if x!=y}
        if not diff:
            writelog('Tables have not been renamed.')
        else:
            parts=['{} -> {}'.format(x,y) for (x,y) in diff.items()]
            string=', '.join(parts)
            writelog('Tables have been renamed: '+string)

    nameslist=[]
    for name,var in zip(tablesdict['name'],tablesdict['var']):
        if var.get():
            nameslist.append(name)
    if not nameslist:
        writelog('No tables have been chosen for renaming.')
    else:
        Top=Toplevel()
        Top.title('Rename')
        M=Multirename(Top,nameslist)
        M.renamebutton.config(command=action)
        M.pack(padx=30,pady=30)

def createcheckbuts(frames):
    '''
    The function creates checkbuttons associated with tables
    and puts them and associated objects (including frames themselves)
    into tablesdict. Gets iterable of kind: [(frame,name),...].
    If names of frames don't exist or already reserved, give them names
    like 'Table_№'.
    Executed in gui thread and can be put into guiqueue.
    '''
    names=[] #for output in writelog
    for frame,name in frames:        
        if not name:
            name='Table'
        num=1
        while name in tablesdict['name']: #cycle to create a unique name
            s=re.search('\((\d+)\)$',name)
            if s:
                name=name.rstrip(s.group(0))
            name+='({})'.format(str(num))
            num+=1
        names.append(name)
        var=IntVar()
        chbut=Checkbutton(tablesframe, text=name,variable=var)
        chbut.pack(anchor='w')
        for key,obj in (('name', name), ('var',var),
                        ('chbut',chbut),('frame',frame)):
            tablesdict[key].append(obj)
    writelog('New tables have been created: {}.'.format(', '.join(names)))

def writelog(message):
    '''
    Function to save actions in log list
    and display them in logtext  
    '''
    global lognum
    lognum+=1
    ordmessage=str(lognum)+ '. ' + message
    log.append(ordmessage)
    logtext.config(state=NORMAL)
    logtext.insert(END, ordmessage+'\n')
    logtext.config(state=DISABLED)
    logtext.see('end')

def selectallf():
    '''
    Select all fields of checkbuttons
    '''
    for i in range(len(fieldsdict['var'])):
        if fieldsdict['chbut'][i].cget('state')=='normal':
            fieldsdict['var'][i].set(1)
def deselectallf():
    '''
    Deselect all fields of checkbuttons
    '''
    for var in fieldsdict['var']:
        var.set(0)

def dbrestrict():
    '''
    Make some fields disabled dependent on chosen database.
    Is called by dbvar.trace().
    '''
    D={'uniprot':upaccessible,'flybase':fbaccessible}
    accessible=D[dbvar.get()]
    for i in range(len(fieldsdict['name'])):
        fieldsdict['chbut'][i].config(state=NORMAL)
        if fieldsdict['name'][i] not in accessible:
            fieldsdict['var'][i].set(0)
            fieldsdict['chbut'][i].config(state=DISABLED)

###########root and menu########################################

root = Tk()
root.title('PyProt')
root.protocol("WM_DELETE_WINDOW", on_closing)

menubar=Menu(root)
filemenu=Menu(menubar,tearoff=0)
filemenu.add_command(label='Open file as table',command=openfile)
filemenu.add_command(label='Save tables as',command=saveinfile)
menubar.add_cascade(label='Options',menu=filemenu)

root.config(menu=menubar)

############ radiobuttons for databases #####################################

dbframe=Frame(root)
dblabel=Label(dbframe,text='Database:', font=('',12))
dbvar=StringVar()
dbvar.set('uniprot')
dbvar.trace('w',lambda *args: dbrestrict())
dbradbuts=[Radiobutton(dbframe, variable=dbvar, text=x, value=y, font=('',12))
         for (x,y) in databases]

############ radiobuttons to choose entry type #########################################

entrytypesframe=Frame(root)
entvar=StringVar()
entradbuts=[Radiobutton(entrytypesframe, variable=entvar, text=x, value=x, font=('',15))
         for x in entrytypes]

############ checkbuttons for fields #####################################################

fieldsframe=Frame(root) #frame for checkbuttons
fieldslabel=Label(fieldsframe,text='Fields:', font=('',13))

fieldsdict={}   #creating dictionary of fields and
                #associated checkbuttons and IntVars
fieldsdict['name']=fields
fieldsdict['var']=[IntVar() for x in fields]
fieldsdict['chbut']=[Checkbutton(fieldsframe, text=fieldsdict['name'][i],
                                 variable=fieldsdict['var'][i],font=('',10))
                     for i in range(len(fields))]

selectall=Button(fieldsframe,text='Select all',font=('',10,'italic'),command=selectallf)
deselectall=Button(fieldsframe,text='Deselect all',font=('',10,'italic'),command=deselectallf)

############## frame and label for tables ##########################################

tablesframe=Frame(root,height=300,width=200,highlightbackground='black',
                  highlightthickness=2) #frame for checkbuttons of created tables
tableslabel=Label(tablesframe, text='Created tables:',font=('',12,'bold'))

################ text widget for entries and button to yield data ##########################

prottextframe=Frame(root)
protlabel=Label(prottextframe, text='Your query:',font=('',12,'bold'))
prottext=ScrolledText(prottextframe, width=15, height=10) #to paste entries here
PopupMenu(prottext)
getdatabutton=Button(prottextframe,text='Get data',command=getdata,font=('',12,'bold'))

keepordervar=IntVar()
keeporder=Checkbutton(prottextframe,text='Keep query order',variable=keepordervar)
keepordervar.set(1)
################ widgets for logging #######################################################

logtextframe=Frame(root)
loglabel=Label(logtextframe,text='Log:',font=('',12))
logtext=ScrolledText(logtextframe, width=40, height=20) #to display log. DISABLED state.
logtext.config(state=DISABLED)

###### buttons to control tables #############################

butsframe=Frame(root)
buttuple=(('Delete tables',deltables),('Unite tables',unitetables),
          ('Get terms freq.', termsfreq),('Rename tables',renametables))

buttonsdict={elem[0]:Button(butsframe,text=elem[0], command=elem[1],font=('',12))
             for elem in buttuple}

###### packing #################################

prottextframe.pack(side=LEFT,anchor='nw')
protlabel.pack()
prottext.pack()
keeporder.pack()
getdatabutton.pack()

dbframe.pack(side=LEFT,anchor='n')
dblabel.pack(anchor='w')
for i in dbradbuts:
    i.pack(anchor='w')
    

fieldsframe.pack(side=LEFT,anchor='n')
fieldslabel.pack(anchor='w')
for f in fieldsdict['chbut']:
    f.pack(anchor='w')
selectall.pack(anchor='w')
deselectall.pack(anchor='w')

butsframe.pack(side=LEFT,anchor='n')
for i in sorted(buttonsdict.keys()):
    buttonsdict[i].pack(anchor='w',fill=X)

tablesframe.pack(side=LEFT,anchor='nw')
tablesframe.pack_propagate(False)
tableslabel.pack()

logtextframe.pack(side=LEFT)
loglabel.pack()
logtext.pack()

############### starting directives ###############################################

dbrestrict()
root.after(0,execqueue,root, guiqueue)
root.mainloop()

