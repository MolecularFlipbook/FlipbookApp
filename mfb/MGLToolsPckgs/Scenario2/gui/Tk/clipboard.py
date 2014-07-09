##
## Author Michel Sanner Feb 2009
##
## Copyrights TSRI and M. Sanner
##

import Tkinter, Pmw

from Scenario2.clipboard import AddMAAToClipBoardEvent, RemoveMAAFromClipBoardEvent
from Scenario2.clipboard import Clipboard

from mglutil.util.callback import CallBackFunction

class ClipboardGUI:
    """
    class displaying the list of MultipleActorActions stored in
    a clipboard object.

    This object handles AddMAAToClipBoardEvent and RemoveMAAFromClipBoardEvent
    events dispatched by the standard scenario event handler
    """

    def __init__(self, clipboard, master=None):
        """
        ClipboardGUI constructor
        
        ClipboardGUIObject <- ClipboardGUI(clipboard, master=None)

        clipboard is an instance of a Clipboard object
        master is a Tk container object. If master is None a Tkinter.Toplevel
        object is created

        This object registers interest in AddMAAToClipBoardEvent and
        RemoveMAAFromClipBoardEvent events with the Clipboard object
        """
        assert isinstance(clipboard, Clipboard)

        self.clipboard = clipboard

        self.master = master

        clipboard.registerListener(AddMAAToClipBoardEvent,
                                   self.addMaaEvent_cb)
        clipboard.registerListener(RemoveMAAFromClipBoardEvent,
                                   self.removeMaaEvent_cb)
        self.createGUI()
        self.refreshGUI()


    def addMaaEvent_cb(self, event=None):
        self._addMAA(event.object)


    def removeMaaEvent_cb(self, event=None):
        self.clearGUI()
        self.refreshGUI()


    def createGUI(self):
        """
        Create a ScrolledFrame to old MAA entries
        """
        if self.master is None:
            self.master = master = Tkinter.Toplevel()
            self.ownsMaster = True
        else:
            self.ownsMaster = False

        # create container
        w = self.MAAContainer = Pmw.ScrolledFrame(
            self.master, labelpos = 'nw', label_text = 'Animations Clipboard',
            usehullsize = 0, hull_width = 40, hull_height = 200)

        w.pack(padx = 5, pady = 3, fill = 'both', expand = 1)
       
        self.maaw = {}   # maa: maa entry widget


    def showMenu_cb(self, maa, event=None):
        """
        configure callback of menu entried with the current orientation and post
        menu
        """
        menu = Tkinter.Menu(self.master, title = "Animation")
        from Scenario2 import addTargetsToMenu
        addTargetsToMenu(menu, maa)
        menu.add_command(label = "Delete",
                  command=CallBackFunction(self.clipboard.removeMaa, maa) )
        menu.add_command(label="Dismiss")
        menu.post(event.x_root, event.y_root)


    def clearGUI(self):
        for maa, entry in self.maaw.items():
            entry.destroy()


    def _addMAA(self, maa):
         """
         Create an entry for a MAA
         """

         master = self.MAAContainer.interior()
       
         self.maaw[maa] = frame = Tkinter.Frame(master)
         
         b = Tkinter.Button(master=frame ,compound='left', text=maa.name,
                            command=maa.run, width=25, height=2)

         b.name = maa.name
         # create the button menu
         b.bind('<Button-3>', CallBackFunction( self.showMenu_cb, maa))
       
         b.pack(side='top')
         frame.pack()


    def refreshGUI(self):

        for maa in self.clipboard.maas:
            self._addMAA(maa)

