from tkinter import *
class PopupMenu(Menu):
    '''
    The class makes universal popup menu.
    Needs a dictionary 'commands' of the following
    form: {'label':command,...}
    The default version of commands within this class
    is supposed for text-like objects (Entry, Text).
    Parameter 'expand': whether the default dictionary must
    be updated by the given dictionary or replaced.
    '''
    def __init__(self,root=None,commands={},expand=True,**options):
        super().__init__(root,tearoff=0,**options)
        self.root=root
        self.commands=commands.copy() #maybe deepcopy()
        if expand:  #add standard commands
            self.add_dict()
        self.add_coms()    

    #define 3 functions for default commands
    def copytext(self):
        self.clipboard_clear()
        try:
            self.clipboard_append(self.root.selection_get())
        except TclError:
            pass
    def cuttext(self):
        self.copytext()
        try:
            self.root.delete(SEL_FIRST,SEL_LAST)
        except TclError:
            pass
    def pastetext(self):
        try:
            self.root.delete(SEL_FIRST,SEL_LAST)
        except TclError:
            try:
                self.root.insert(INSERT,self.clipboard_get())
            except TclError:
                pass


    def add_dict(self): #add standard part of dictionary
        self.commands['Copy']=self.copytext
        self.commands['Cut']=self.cuttext
        self.commands['Paste']=self.pastetext
    def add_coms(self):
        for com in sorted(self.commands):
            self.add_command(label=com,command=self.commands[com])
        self.root.bind("<Button-3>", self.popup)

    def popup(self,event):
        self.post(event.x_root, event.y_root)


if __name__=='__main__':   
    root=Tk()
    F=Frame(root)
    F.pack()
    t=Text(root)
    t.pack()
    e=Entry(F)
    e.pack()
    P=PopupMenu(e)
    P2=PopupMenu(t)
    root.mainloop()
