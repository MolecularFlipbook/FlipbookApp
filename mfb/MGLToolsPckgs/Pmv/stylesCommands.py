#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2010
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/stylesCommands.py,v 1.11 2010/10/29 21:45:49 sanner Exp $
# 
# $Id: stylesCommands.py,v 1.11 2010/10/29 21:45:49 sanner Exp $
#
from mglutil.util.callback import CallbackFunction
import Tkinter, Pmw, os
from Pmv.mvCommand import MVCommand, MVCommandGUI
from DejaVu.states import setRendering, getRendering

class Style:

    def __init__(self, name, func, nbMols, doc):
        self.name = name
        self.func = func
        self.nbMols = nbMols
        self.doc = doc
        
class LoadRenderingStylesCommand(MVCommand):
    """
    The RenderingStylesCommand adds the Styles page to the Tools Notbook
    of the GUI
    \nPackage : Pmv
    \nModule  : stylesCommands
    \nClass   : LoadRenderingStylesCommand
    \nName    : loadRenderingStyles
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.undoRenderingStack = []
        
    def setupUndo(self, name):
        oldRendering = getRendering(self.vf.GUI.VIEWER)
        self.undoRenderingStack.append(oldRendering)
        undoCmd = """from DejaVu.states import setRendering\n
stack = self.%s.undoRenderingStack
if len(stack): setRendering(self.GUI.VIEWER, stack.pop(), True)
"""%self.name
        
        #print 'UNDO', undoCmd
        
        self.vf.undo.addEntry((undoCmd), (name))

    def loadStyles(self):
        # find the location fo the styles directory
        import Image, ImageTk
        from Pmv import styles
        path = styles.__path__[0]
        from glob import glob
        styleFiles = glob(os.path.join(path, "*_style.py"))
        styleFiles.sort()
        self.styleRow = self.styleCol = 0
        inside = self.stylesScrolledFrame.interior()
        self.styles = {}

        currentx = 0
        currenty = 0
        border = 1
        for sfile in styleFiles:
            # import the function
            name = os.path.basename(sfile)[:-9]
            modpath = 'Pmv.styles.'+name+'_style'
            mod = __import__(modpath,{}, {},['*'])

            styleObj = Style(name, mod.applyStyle, mod.numberOfMolecules,
                             mod.__doc__)

            self.styles[name] = styleObj
            
            photoIcon = ImageTk.PhotoImage(
                file=os.path.join(path, name+'_icon.png'))

            cb = CallbackFunction(self.applyStyle, styleObj)
            b = Tkinter.Button(inside, compound='left', image=photoIcon,
                               command=cb)
            b.photo = photoIcon

            width = b.photo.width()
            height = b.photo.height()
            b.place(x=currentx, y=currenty, width=width, height=height )

            textw = Tkinter.Label(inside, text=name, justify='left')
            textw.place(x=width+border, y=currenty)
            textw.update() # to allow label to appear and size to be correct
            currenty += max(textw.winfo_height(), height + border)

            # bind callback to display large version
            photo = ImageTk.PhotoImage(file=os.path.join(path, name+'.png'))
            cb = CallbackFunction(self.showLargeImage, photo, mod.__doc__)
            b.bind('<Enter>', cb)
            b.bind('<Motion>', self.move_cb)
            b.bind('<Leave>', self.leave_cb)
            b.photo1 = photo
            
            #self.balloon.bind(b, mod.__doc__)

            #print 'adding style', name, currenty, self.styleRow,self.styleCol
            
            if self.styleCol == 3:
                self.styleCol = 0
                self.styleRow = self.styleRow + 1
            else:
                self.styleCol = self.styleCol + 1


    def showLargeImage(self, photo, text, event=None):
        self.largeImageRoot = top = Tkinter.Toplevel()
        #top.overrideredirect(True)
        canvas = Tkinter.Canvas(top)
        w = photo.width()
        h = photo.height()
        textw = canvas.create_text(
            0, 0, anchor='nw', text=text, justify='left')
        bb = canvas.bbox(textw)
        canvas.create_image(w/2, h/2+bb[3]+10, image=photo)
        canvas.pack(expand=1, fill='both')
        bb = canvas.bbox('all')
        top.geometry("%dx%d+%d+%d"%(bb[2],bb[3], event.x_root, event.y_root))


    def move_cb(self, event):
        self.largeImageRoot.geometry("+%d+%d"%(event.x_root, event.y_root))


    def leave_cb(self, event):
        self.largeImageRoot.destroy()

        
    def applyStyle(self, styleObj):
        molName1 = self.styleMol1.get()
        molName2 = self.styleMol2.get()
        quality = self.quality.get()

        #print 'applying style %s to (%s, %s)'%(
        #    styleObj.name, molName1, molName2)
        if styleObj.nbMols==1:
            if molName1 is not None:
                self.setupUndo("apply style %s to %s"%(styleObj.name,
                                                       molName1))
                styleObj.func(self.vf, molName1)
        elif styleObj.nbMols==2:
            if molName1 is not None and molName2 is not None:
                self.setupUndo("apply style %s to (%s,%s)"%(
                    styleObj.name, molName1, molName2))
                styleObj.func(self.vf, molName1, molName2, quality)


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            gui = self.vf.GUI

            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

            # add a page for styles
            page = self.StylesMaster = gui.toolsNoteBook.add("Styles")
            #master = self._master = Tkinter.Frame(gui.StylesMaster)
            #master.pack(fill='both', expand=1)

            #p = Pmw.ScrolledFrame(
            #    page, horizflex='expand',vertflex='expand',
            #    vscrollmode='dynamic', hscrollmode='dynamic')
            #p.pack(side='top', anchor='nw', expand=1, fill='both')
            #self.scrolledFrame = p

            ## add a group for styles
            ##
            w = self.styleGroup = Pmw.Group(page, tag_text='Styles')

            p = Pmw.ScrolledFrame(
                w.interior(), horizflex='expand', vertflex='expand',
                vscrollmode='dynamic', hscrollmode='dynamic')
            self.stylesScrolledFrame = p
            p.pack(side='top', anchor='nw', expand=1, fill='y')

            # load the styles
            self.loadStyles()

            self.styleGroup.pack(fill='both', expand=1, padx=10, pady=10)

            ## add a group for arguments
            ##
            self.styleArgsGroup = Pmw.Group(page,
                                            tag_text='Style arguments')
            self.styleArgsGroup.pack(fill='x', expand=1, padx=10, pady=10)

            inside = self.styleArgsGroup.interior()
            # add first molecule argument
            self.styleMol1 = Pmw.ComboBox(
                inside, label_text = 'mol. 1:', labelpos = 'w', dropdown=1,
                scrolledlist_items = ["None"], entryfield_entry_width=5)
            self.styleMol1.selectitem("None")

            self.styleMol1.pack(side='top', anchor='n',
                                fill='x', expand=1, padx=8, pady=8)

            # add second molecule argument
            self.styleMol2 = Pmw.ComboBox(
                inside, label_text = 'mol. 2:', labelpos = 'w', dropdown=1,
                scrolledlist_items = ["None"], entryfield_entry_width=8)
            self.styleMol2.selectitem("None")
            self.styleMol2.pack(side='top', anchor='n',
                                fill='x', expand=1, padx=8, pady=8)

            # add quality argument
            self.quality = Pmw.ComboBox(
                inside, label_text = 'quality:', labelpos = 'w', dropdown=1,
                scrolledlist_items = ['preview', 'display','publication'],
                entryfield_entry_width=8)
            self.quality.selectitem('preview')
            self.quality.pack(side='top', anchor='n',
                              fill='x', expand=1, padx=8, pady=8)

            self.styleArgsGroup.pack(anchor='n', side='top',
                                    fill='x', expand=1, padx=8, pady=8)

            #self.toolsNoteBook.setnaturalsize()
            
            #self.vf.registerListener(DeleteAtomsEvent, self.updateGeom)
            #self.vf.registerListener(AddAtomsEvent, self.updateGeom)
            #self.vf.registerListener(EditAtomsEvent, self.updateGeom)


    def onAddObjectToViewer(self, obj):
        """
        update list of molecules in combo boxes
        """
        if self.vf.hasGui:
            from MolKit.protein import Protein
            # FIXME if only mols use self.vf.Mols
            mols = [x.name for x in self.vf.dashboard.system.children if \
                    isinstance(x, Protein)]

            self.styleMol1.component('scrolledlist').setlist(["None"]+mols)
            self.styleMol2.component('scrolledlist').setlist(["None"]+mols)

            # set combobox to something if nothing has been selected yet
            if self.styleMol1.get()=='None':
                if len(mols):
                    self.styleMol1.selectitem(1) # first molecule

            if self.styleMol2.get()=='None':
                if len(mols)>1:
                    self.styleMol2.selectitem(2) # second molecule
        

                
commandList = [
    {'name':'loadRenderingStyles', 'cmd':LoadRenderingStylesCommand(),
     'gui':None},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
