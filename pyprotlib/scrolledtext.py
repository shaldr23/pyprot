from tkinter import *
class ScrolledText(Text):
    '''
    Class to create text widget with possibility of scrolling
    '''
    def __init__(self, root, **kargs):
        self.frame=Frame(root)
        self.scrollbar = Scrollbar(self.frame)
        Text.__init__(self, self.frame, wrap=WORD,
                      yscrollcommand=self.scrollbar.set, **kargs)
        self.scrollbar.config(command=self.yview)
    def pack(self, **kargs):
        self.frame.pack(**kargs)
        Text.pack(self, side=LEFT)
        self.scrollbar.pack(side=LEFT, fill=Y)
        
        
