from tkinter import *
class Multirename(Frame):
    '''
    The class creates new frame with multiple
    entries correspinding to word for renaming -
    'wordslist'.
    Assumed to be created in Toplevel window.
    renamebutton 'command' must be implemented.
    'getnewnames' method makes a dict of .
    
    '''
    def __init__(self,root,wordslist,*args,**kargs):
        Frame.__init__(self,root,*args,**kargs)
        self.root=root
        root.grab_set()
        self.entries={}
        for word in wordslist:
            frame=Frame(self)
            frame.pack(anchor='e',pady=10)
            label=Label(frame,text=word+': ',font=('',13))
            label.pack(side=LEFT)
            entry=Entry(frame,font=('',13))
            entry.pack(side=LEFT)
            entry.insert(0,word)
            self.entries[word]=entry
        self.renamebutton=Button(self,text='Rename',font=('',13))
        cancelbutton=Button(self,text='Cancel', font=('',13),
                            command=lambda: self.root.destroy())
        cancelbutton.pack(side=LEFT)
        self.renamebutton.pack(side=RIGHT)
        
    def configall(self,**kargs):
        for entry in self.entries:
            entry.config(**kargs)
    def getnewnames(self):
        return {word:entry.get() for (word,entry) in self.entries.items()}
