#########################################################################
#
# Date: Nov. 2001  Author: Daniel Stoffler, Michel F. Sanner
#
#       stoffler@scripps.edu
#       sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel F. Sanner and TSRI
#   
# revision: Guillaume Vareille
#  
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Vision/VPE.py,v 1.230.4.2 2012/02/27 20:21:04 sanner Exp $
#
# $Id: VPE.py,v 1.230.4.2 2012/02/27 20:21:04 sanner Exp $
#

import re
import sys
import os
import string
import Pmw, Tkinter
import webbrowser
import warnings
import types

from tkSimpleDialog import askstring

from NetworkEditor.simpleNE import NetworkBuilder,NoGuiNetworkBuilder 
from NetworkEditor.items import NetworkNode
from NetworkEditor.customizedWidgets import kbScrolledCanvas
from NetworkEditor.widgets import PortWidget
from NetworkEditor.ports import InputPort, OutputPort

from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.toolbarbutton import ToolBarButton 
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import kbComboBox
from mglutil.util.packageFilePath import getObjectFromFile
from Vision.nodeLibraries import LoadLibraryPanel, BrowseLibraryPanel, CreateLibraryPanel, AddNodeToUserLibraryPanel
from Vision.Forms import AboutDialog, AcknowlDialog, RefDialog, ChangeFonts,\
     SearchNodesDialog,BugReport
import tkMessageBox
from NetworkEditor.Glyph import Glyph


from NetworkEditor.datatypes import TypeManager
from NetworkEditor.widgets import widgetsTable, PortWidget
from NetworkEditor.macros import MacroNetwork

class NoGuiVPE:
    """Class used to replace the VPE when running without a GUI.
This class serves a place hold4er for the data type manager and also
for multiple networks such as the ones created by macros.
"""
    def __init__(self):
        self.libraries = {}         # stores node libraries

        try:
            # add VisionLibraries to system path
            from Vision.UserLibBuild import addDirToSysPath
            from Vision import __path__
            addDirToSysPath(__path__[0]+'Libraries')
            
            # add UserLibs to system path 
            from mglutil.util.packageFilePath import getResourceFolderWithVersion
            lVisionResourceFolder = getResourceFolderWithVersion() \
                                    + os.sep + 'Vision' + os.sep
            addDirToSysPath(lVisionResourceFolder + 'UserLibs')
        except:
            pass


    def printEvent(self, event):
        print event

        
    def addLibraryInstance(self, lib, modName, varName, force=False):

        if force is False:
            for l in self.libraries.values():
                if l.name == lib.name:
                    return # already loaded
            if lib in self.libraries.values():
                return # already loaded

        assert isinstance(lib, NodeLibrary)

        #remove duplicate nodes (and keep the last ones rather than the first one):
        lNodeDict = {}
        for lNode in lib.nodes:
            lNodeDict[lNode.__name__] = lNode
        lib.nodes = lNodeDict.values()
        for key in lib.libraryDescr.keys():
            lNodeDict = {}
            for lNode in lib.libraryDescr[key]['nodes']:
                lNodeDict[lNode.name] = lNode
            lib.libraryDescr[key]['nodes'] = lNodeDict.values()
            lib.libraryDescr[key]['lastPosy'] = 15

        lib.varName = varName # will be used below (e.g. 'stdlib')
        lib.modName = modName # will be used below (e.g. 'Vision.Stand...')
        
        # add new library to dict
        self.libraries[lib.name] = lib
        # now add any new datatypes to the typeManager
        self.extendTypesTable(lib)
        self.extendSynonymsTable(lib)
        # now add any new widgets to the widgetsTable
        self.extendWidgetsTable(lib)


    def extendTypesTable(self, lib):
        """add new typesTable to the typeManager"""
        for t in lib.typesTable:
            self.typeManager.addType(t) 


    def extendSynonymsTable(self, lib):
        """add new synonymsTable to the typeManager
"""
        for s in lib.synonymsTable:
            self.typeManager.addSynonymDict(s) 


    def extendWidgetsTable(self, lib):
        """add new widgets to widgetsTable"""
        for w in lib.widgets:
            # w has to be instance of Port widgets
            assert issubclass(w, PortWidget)
            # w.__name__ must be different from predefined widgets 
            if w.__name__ not in widgetsTable.keys():
                widgetsTable[w.__name__] = w


class NoGuiExec(NoGuiNetworkBuilder, NoGuiVPE):

    def __init__(self):
        NoGuiNetworkBuilder.__init__(self)
        NoGuiVPE.__init__(self)
        
   
class VisualProgramingEnvironment(NetworkBuilder, NoGuiVPE):

    def addMoreButtonBars(self):
        # allow subclasses to add more button bars under the default bar
        #self.buttonBar1 = self.top.add('ButtonBar1', min=20, max=20, size=20)
        #self.buttonBarFunc1 = {} # key:buttonName, value:function
        pass
    
    def __init__(self, name='NetworkBuilder', master=None, font=None,
                 withShell=1, width=750, height=700, **kw):

        NoGuiVPE.__init__(self)

        self.width = width
        self.height = height

        self.master = master

        # Create a main PanedWidget with module library and editor area
        self.top = Pmw.PanedWidget(master, orient='vertical',
                                   hull_relief='sunken',
                                   hull_width=width, hull_height=height)

        self.top.component('hull').master.title(name)

        # horizontal pane for mnu bar
        menus = self.top.add('MenuBars', min=20, max=40, size=20)

        # horizontal pane for libraries notebook
        if sys.platform == 'win32':
            # the size parameter doesn't seem to be taken in account on win32
            modulePagesPane = self.top.add('ModulePages', min=150, size=200)
            #self.top.configurepane('ModulePages',min=100, size=150 )
        else: 
            modulePagesPane = self.top.add('ModulePages', min=100, size=200)

        #mod = self.top.add('ButtonsModulePages', min=100, size=150)

        # horizontal pane for for buttons
        self.buttonBar = self.top.add('ButtonBar', min=20, max=20, size=20)
        self.buttonBarFunc = {} # key:buttonName, value:function

        self.addMoreButtonBars()

        # horizontal pane for networks notebook
        ed = self.top.add('Editor', min=100)

        #self.topVert = Pmw.PanedWidget(mod,
        #                               orient='horizontal',
        #                               hull_width=width, hull_height=height)
        #buttons = self.topVert.add('buttons',  min=30, size=150)
        #mod = self.topVert.add('ModulePages',  min=100)

        # create scrolled frame for ModulePage (libraries)
        #self.modulePagesF = Tkinter.Frame(self.modulePages)
        self.modulePagesF = Pmw.ScrolledFrame(modulePagesPane,
             borderframe=1, horizscrollbar_width=7, vscrollmode='none',
             frame_relief='flat',
             frame_borderwidth=0, horizflex='fixed',
             vertflex='elastic')
        self.modulePagesF.pack(expand=1, fill='both')
        #self.modulePagesF.component('frame').pack(expand=1, fill='both')
        
        # add notebook for module libraries
        self.ModulePages = Pmw.NoteBook(self.modulePagesF.interior(),
                                        raisecommand=self.selectLibrary)
        #self.ModulePages = Pmw.NoteBook(self.modulePagesF)
        #self.ModulePages = Pmw.NoteBook(modulePagesPane)
        self.ModulePages.pack(fill='both', expand = 1)# padx = 5, pady = 5) 
        

        # add notbook for buttons -- this is no longer used, since we have
        # have now a toolbar with icons!!
        #self.ButtonsPages = Pmw.NoteBook(buttons)
        #self.ButtonsPages.pack(fill = 'both', expand = 1, padx = 5, pady = 5) 
        #self.addStdButtons()
        self.idToNodes = {} # key is canvas, values {nodeID:nodeType}

        # add search widget to search for nodes by name
        
        #iconfile = findFilePath('find1.gif', 'Vision.icons' )
        #findicon = Tkinter.PhotoImage(file=iconfile)

        self.addButtonsToButtonBar(master) # add buttons to buttonBar
        
        
        self.modSearch = kbComboBox( self.buttonBar, labelpos='w',
            entryfield_entry_width=12, selectioncommand=self.searchModules,
            scrolledlist_items = [])
        self.modSearch.pack(side='left', anchor=Tkinter.NW)
           
        # FIXME for some reason this works from the shell but the icon is not
        # visible when done from here ????? Workaround: added icon as last
        # button to the bar
##          self.modSearch.component('label').configure(image=findicon)

        self.lastSearchString = None
        self.searchAfterId = None # used to deselect nodes found by search
        self.lastMatchIndices = [0,0,0] # library index and category index
                                        # of last found node

        apply( NetworkBuilder.__init__, (self, name, ed, font, withShell), kw )
        
##         if __debug__:
##             from NetworkEditor.widgets import WidgetValueChange
##             self.registerListener(WidgetValueChange, self.printEvent)
##             from NetworkEditor.net import AddNodeEvent, ConnectNodes, \
##                  DeleteNodesEvent, DeleteConnectionsEvent
##             self.registerListener(AddNodeEvent, self.printEvent)
##             self.registerListener(ConnectNodes, self.printEvent)
##             self.registerListener(DeleteNodesEvent, self.printEvent)
##             self.registerListener(DeleteConnectionsEvent, self.printEvent)

        self.mBar.destroy()

        self.createMenus(menus)
        self.setFont("Menus", self.font['Menus'])
        
        self.top.pack(expand=1, fill='both')

        handle = self.eventHandler['deleteNetwork']
        handle.AddCallback(self.handleDeleteNetworkButtons)

        # a dictionary holding various forms:
        self.forms = {}              
        self.forms['configureFontsPanel'] = None # a form to change the fonts
        self.forms['loadLibraryPanel']    = None # a widget created by
                                                 # showLoadLibraryForm_cb 
        self.forms['browseLibsPanel']     = None # a widget created by
                                                 # showBrowseLibraryForm_cb
        self.forms['createLibsPanel']     = None # a widget created by
                                                 # showCreateLibraryForm_cb
        self.forms['addNodeToLibsPanel']  = None # a widget created by
                                                 # AddNodeToLibrary_cb
        self.forms['aboutDialog']         = None # aboutDialog window
        self.forms['acknowlDialog']       = None # acknowledgements dialog
        self.forms['refDialog']           = None # references dialog window
        self.forms['searchNodesDialog']   = None # search nodes dialog window
        self.forms['BugReport']         = None #bugreport window
        from NetworkEditor.widgets import widgetsTable
        self.widgetsTable = widgetsTable

        self.userLibsDirs = {}      # stores path to user defined node libs 

        from Vision.UserLibBuild import ensureDefaultUserLibFile
        ensureDefaultUserLibFile()
        from Vision.UserLibBuild import ensureVisionResourceFile
        ensureVisionResourceFile()

        if hasattr(self,"currentNetwork"):
            self.currentNetwork.glyphKeywords ={}
            self.currentNetwork.glyphKeywords['fontstyle']=''
            self.currentNetwork.glyphKeywords['font']= "courier"
            self.currentNetwork.glyphKeywords['fontsize'] = 12 
            self.currentNetwork.glyphKeywords['fill'] = ''
            self.currentNetwork.glyphKeywords['outline'] = "black"
            self.currentNetwork.glyphKeywords['spray'] = False

        self.master.master.master.protocol("WM_DELETE_WINDOW",
                                           self.interactiveExit_cb)

        
    def updateGuiCycle(self):
        """this function is similar to a sleep(3) but in the meanwhile it keeps 
           updating the GUI"""
        from time import sleep
        i = 0
        while i < 300 :
            self.master.update()
            sleep(0.01)
            i = i + 1
        return (self.currentNetwork.execStatus != 'stop')


    def showHideGlyphWidget(self,glyph):
        if glyph ==0:
            self.currentNetwork.glyph =0
            self.currentNetwork.glyphshape = None
            self.currentNetwork.glyphselect =None
            canvas = self.currentNetwork.canvas
            #canvas.unbind("<B1-Motion>")
            #canvas.unbind("<ButtonPress-1>")
            #canvas.unbind("<ButtonRelease-1>")
            #canvas.unbind("<B2-Motion>")
            if  hasattr(self,"glyphbuttonBar"):
                self.top.delete(3)
                self.top.updatelayout()
        else:
            self.currentNetwork.glyph=1
            self.glyphbuttonBar = self.top.insert('glyphButtonBar',before = 3, min=20, max=20, size=20)
            self.glyphbuttonBarFunc = {} # key:buttonName, value:function
            self.addButtonsToglyphButtonBar(self.master)# add buttons to glyphbuttonBar
            #Font
            lab_font  = Tkinter.Label(self.glyphbuttonBar,text="Font")
            lab_font.pack(side='left')
            self.font_style_listbox = kbComboBox(self.glyphbuttonBar,labelpos='w',entryfield_entry_width=7,scrolledlist_items =["courier","Helvetica","Comic Sans MS", "Fixedsys", "Times New Roman", "Verdana"],selectioncommand=self.fontStyle)
            self.font_style_listbox.pack( side='left', anchor=Tkinter.NW)
            self.font_style_listbox.selectitem("courier")
            #Font size
            self.font_size_listbox = kbComboBox(self.glyphbuttonBar,labelpos='w',entryfield_entry_width=3,scrolledlist_items =range(100),selectioncommand=self.fontSize)
            self.font_size_listbox.pack( side='left', anchor=Tkinter.NW)
            self.font_size_listbox.selectitem(6)
            #Fill
            lab_fill  = Tkinter.Label(self.glyphbuttonBar,text="Fill")
            lab_fill.pack(side='left')
            self.fill_style_listbox = kbComboBox(self.glyphbuttonBar,labelpos='w',entryfield_entry_width=5,scrolledlist_items =['','black','white','red','blue','green','yellow'],selectioncommand=self.fillStyle)
            self.fill_style_listbox.pack( side='left', anchor=Tkinter.NW)
            self.fill_style_listbox.selectitem("")
            #Outline
            lab_outline  = Tkinter.Label(self.glyphbuttonBar,text="Outline")
            lab_outline.pack(side='left')
            self.outline_style_listbox = kbComboBox(self.glyphbuttonBar,labelpos='w',entryfield_entry_width=5,scrolledlist_items =['black','white','red','blue','green','yellow'],selectioncommand=self.outlineStyle)
            self.outline_style_listbox.pack( side='left', anchor=Tkinter.NW)
            self.outline_style_listbox.selectitem("black")


    def addUserLibDir(self, pathstr, dirname):
        """Register a user-defined library by adding it to sys.path if needed."""
        
        fullpath = os.path.abspath(pathstr)

        # 1) add to userLibsDirs
        self.userLibsDirs[dirname] = fullpath

        # 2) add to sys.path
        found = False
        for p in sys.path:
            if fullpath == p:
                # do nothing if this one is already in sys.path
                return

        # else, append parent to sys.path
        sys.path.append(fullpath)


    def showAddNodeToLibraryForm_cb(self, event=None):
        # check if we have 1 selected node
        if len(self.currentNetwork.selectedNodes) == 0:
            tkMessageBox.showwarning(
                "Add Node To Library",
                "No node is currently selected!\n\nPlease select one node in the current network to be added to a user library!")
            return

        elif len(self.currentNetwork.selectedNodes) > 1:
            tkMessageBox.showwarning(
                "Add Node To Library",
                "Multiple nodes are currently selected!\n\nPlease select only one node in the current network to be added to a user library!")
            return

        # check if we have user libraries loaded
        libs = []
        for libname, lib in self.libraries.items():
            if lib.mode == 'readWrite':
                libs.append(libname)
        if not len(libs):
            tkMessageBox.showwarning(
                "Add Node To Library",
                "Currently, no user-defined library is loaded!\n\nPlease load a user-defined library, since nodes can only be added to user libraries. For further questions please consult the FAQ located in the main menu 'Help'.")
            return
            

        # display the GUI for adding a node to a user library
        if self.forms['addNodeToLibsPanel'] is None:
            self.forms['addNodeToLibsPanel'] = AddNodeToUserLibraryPanel(self)
        else:
            self.forms['addNodeToLibsPanel'].show()


    def addNodeToUserLibrary(self, node, className, cat, lib):
        """add a node (or macro node) to a user-defined node library."""
        # check if node className is already in lib file
        import sys
        filename = sys.modules[lib.modName].__file__
        if filename[-1] in ["c", "o"]: #.pyc, .pyd -> make .py
            filename = filename[:-1]        

        f = open(filename)
        libSrc = f.readlines()
        f.close()
        found = False
        for line in libSrc:
            if "class %s("%className in line:
                found=True
                break
        if found:
            warnings.warn("Classname %s already declared in %s! Appending to end of file."%(
                className, file) )

        node.name = className
        node.library = lib

        # now grab node's source code
        src = node.getNodeSourceCode(className)
        # then replace "kw['originalClass'] = %s\n"%klass by
        # "kw['originalClass'] = %s\n"%className
        pat = re.compile("originalClass")
        i = 0
        for l in src:
            res = pat.search(l)
            if res:
                break
            i += 1
        if res:
            src[i] = src[i][:res.end()+5] + className + '\n'

        # save source in library
        f = open(filename, 'a')
        map( f.write, src)
        f.write("%s.addNode(%s, '%s', '%s')\n"%(lib.varName, className,
                                                className, cat))
        f.close()

        # since the source file of the library has changed we have
        # to reload the module for the new node to be known
        import sys
        try:            
            reload(sys.modules[lib.modName])
        except RuntimeError, e:
            print "addNodeToUserLibrary: unable to reload library %s\n" % lib.modName, e

        # it appears we do not need to do the following:
##         # reload creates new objects for all things in the module
##         # so we need to update self.libraries to point to the new
##         # instance of the NodeLibrary
##         self.libraries[lib.name] = getattr(sys.modules[lib.modName],
##                                            lib.varName)
        
        # add the node to the library
        #nodeClass = getObjectFromFile( filename, className)
        nodeClass = getattr(sys.modules[lib.modName], className)
        lib.addNode(nodeClass, className, cat)

        # replace node by node from new library
        net = node.network
        posx = node.posx
        posy = node.posy
        net.deleteNodes([node])
        n = nodeClass(library=lib)
        net.addNode(n, posx, posy)
        
    
    def resize_cb(self, event=None):
        NetworkBuilder.resize_cb(self, event)
        if self.width != event.width:
            curwidth = self.width
            self.width = event.width
            # resize all libraries, only if window got larger
            if curwidth < event.width:
                for lib in self.libraries.values():
                    if lib.ed is not None:
                        lib.resizeCategories()
            

    def selectLibrary(self, name):
        # recolor the vertical scrollbar which is displayed when the main
        # window size is shrunk
        if not self.libraries.has_key(name):
            name = name.replace(' ', '_')
        color = self.libraries[name].color
        self.modulePagesF.configure(horizscrollbar_activebackground=color)

        # recolor NetworkArea vertical scrollbar
        self.networkAreaF.configure(horizscrollbar_activebackground=color)
        

    def selectNetwork(self, name):
        # subclass NetworkBuilder selectNetwork()
        NetworkBuilder.selectNetwork(self, name)


    def setNetwork(self, network):
        #print "VPE.setNetwork", network
        NetworkBuilder.setNetwork(self, network)
        if hasattr(self, 'buttonVariables'):
            if network.runOnNewData.value is True:
                self.buttonVariables['runOnNewData'].set(1)
            else:
                self.buttonVariables['runOnNewData'].set(0)

        self.currentNetwork.setSplineConnections( self.splineConnections==1 )

        # set the run, pause and stop buttons
        net = self.currentNetwork
        net.execStatusLock.acquire()
        lexecstatus = net.execStatus
        bl = self.buttonBar.toolbarButtonDict
        if lexecstatus == 'pause':
            bl['run'].disable()
            if bl.has_key('softrun'):
                bl['softrun'].disable()
            bl['pause'].enable()
            bl['pause'].config(relief='sunken')
            bl['stop'].disable()
        elif lexecstatus == 'running':
            bl['run'].disable()
            if bl.has_key('softrun'):
                bl['softrun'].disable()
            bl['pause'].enable()
            bl['pause'].config(relief='flat')
            bl['stop'].enable()
        elif lexecstatus == 'waiting' or lexecstatus == 'stop':
            bl['run'].enable()
            if bl.has_key('softrun'):
                bl['softrun'].enable()
            bl['pause'].disable()
            bl['pause'].config(relief='flat')
            bl['stop'].disable()
        net.execStatusLock.release()

        # set the withoutGUI run and stop buttons
        if hasattr(net, 'processWithoutGui'):
            if bl.has_key('runWithoutGui'):
                bl['runWithoutGui'].disable()
            if bl.has_key('stopWithoutGui'):
                bl['stopWithoutGui'].enable()
        else:
            if bl.has_key('runWithoutGui'):
                bl['runWithoutGui'].enable()
            if bl.has_key('stopWithoutGui'):
                bl['stopWithoutGui'].disable()

        if isinstance(net, MacroNetwork):
            bl['run'].disable()
            if bl.has_key('softrun'):
                bl['softrun'].disable()
            if bl.has_key('runWithoutGui'):
                bl['runWithoutGui'].disable()


    def createMenus(self, parent):
        # subclass NetworkBuilder createMenus
        NetworkBuilder.createMenus(self, parent)
        self.makeLibrariesMenu()
        self.makeHelpMenu()
        self.addToEditMenu()


    def addToEditMenu(self):
        Edit_button = self.menuButtons['Edit']
        Edit_button.menu.add_command(label="Font settings",
                                     command=self.showConfigureFontsForm_cb,
                                     underline=0)


    def updateFastLibs(self):
        from Vision.nodeLibraries import libraries
        for key, value in libraries.items():
            try:
                if hasattr(self,'fastLibsMenu'):
                    self.fastLibsMenu.index(key)
            except:
                if len(value) == 2:
                    func = CallBackFunction(self.loadLibModule, value[0], dependents=value[1])
                else:
                    func = CallBackFunction(self.loadLibModule, value)
                if hasattr(self,'fastLibsMenu'):
                    self.fastLibsMenu.add_command(label=key, command=func)

            try:
                if hasattr(self,'fastLibsMenu2'):
                    self.fastLibsMenu2.index(key)
            except:
                if len(value) == 2:
                    func = CallBackFunction(self.loadLibModule, value[0], dependents=value[1])
                else:
                    func = CallBackFunction(self.loadLibModule, value)
                if hasattr(self,'fastLibsMenu2'):
                    self.fastLibsMenu2.add_command(label=key, command=func)


    def makeLibrariesMenu(self):
        Lib_button = Tkinter.Menubutton(self.mBar, text='Libraries',
                                         underline=0)
        self.menuButtons['Libraries'] = Lib_button
        Lib_button.pack(side=Tkinter.LEFT, padx="1m")

		# got rid of useless tearoff
        Lib_button.menu = Tkinter.Menu(Lib_button, tearoff=False)

        Lib_button.menu.add_command(label="Hide libraries",
                                     command=self.showHideLibraries_cb,
                                     underline=0)
        
        Lib_button.menu.add_separator()

        # Cascade menu for user-defined node libraries
        self.fastLibsMenu = Tkinter.Menu(Lib_button.menu, tearoff=0)
        self.fastLibsMenu.configure(font=self.font['Menus'])
        Lib_button.menu.add_cascade(label="Load library",
                                    menu=self.fastLibsMenu,
                                    underline=0)
        self.updateFastLibs()

        Lib_button.menu.add_command(label="Browse libraries...",
                                    command=self.showBrowseLibraryForm_cb,
                                    underline=0)

        Lib_button.menu.add_separator()

        Lib_button.menu.add_command(label="Resize categories",
                                    command=self.resizeCategories_cb,
                                    underline=0)

        Lib_button.menu.add_separator()

        # Cascade menu for user-defined node libraries
        usermenu = Tkinter.Menu(Lib_button.menu, tearoff=0)
        usermenu.configure(font=self.font['Menus'])

#        Lib_button.menu.add_cascade(label="User Libraries", menu=usermenu)
#        usermenu.add_command(label="Create Library...",
#                                    command=self.showCreateLibraryForm_cb,
#                                    )
#        usermenu.add_command(label="Add Node...",
#                             command=self.showAddNodeToLibraryForm_cb,
#                             )

        def defaultUserLibMessage_cb():
            import tkMessageBox
            tkMessageBox.showinfo("User libraries",
                                  """To save a modified node or a macro in MyDefaultLib:\n
right click on the node, choose "Save source code..."\n
( the save dialog box opens inside the MyDefaultLib directory
~/.mgltools/[Version Number]/Vision/UserLibs/MyDefaultLib )\n
save it in an existing category folder.\n
To create a new category, add a folder inside the directory MyDefaultLib.
\n ------------------------------ \n
You can rename MyDefaultLib until you start using it in saved networks 
(the name of the library is hardcoded in the saved network file)
\n ------------------------------ \n
To create a new Library, add a folder in
~/.mgltools/[Version Number]/Vision/UserLibs/
copy inside it the __init__.py from MyDefaultLib,
and create folders for the categories\n
To load this new library in Vision, use the menu:
 "Libraries - Browse libraries"
""")

        Lib_button.menu.add_command(label="User libraries",
                                    command=defaultUserLibMessage_cb,
                                    underline=0)

        # set up a pointer from the file menubutton back to the file menu
        Lib_button['menu'] = Lib_button.menu


    def makeHelpMenu(self):
        # remove title in menu bar
        self.title.forget()
        Help_button = Tkinter.Menubutton(self.mBar, text='Help',
                                         underline=0)
        self.menuButtons['Help'] = Help_button
        Help_button.menu = Tkinter.Menu(Help_button)
        Help_button.pack(side=Tkinter.LEFT, padx="1m")
        Help_button.menu.add_command(label="About...",
                                     command=self.showAbout)
        Help_button.menu.add_command(label="Acknowledgements...",
                                     command=self.showAcknowl)
        Help_button.menu.add_command(label="Install Vision in a different Python interpreter",
                                     command=self.showInstallVision)
        Help_button.menu.add_command(label="References...",
                                     command=self.showRefs)
        Help_button.menu.add_command(label="Submit Bug Report...",
                                     command=self.showBugReport)
        Help_button.menu.add_command(label="Tutorials and examples",
                                     command=self.showTutorials)
        Help_button.menu.add_separator()
        Help_button.menu.add_command(label="FAQ (opens browser)...",
                                     accelerator="F1",
                                     command=self.showFAQ)

        
        # set up a pointer from the file menubutton back to the file menu
        Help_button['menu'] = Help_button.menu
    def showBugReport(self, event=None):
        """the 'about Vision' dialog window"""
        if self.forms['BugReport'] is None:
            self.forms['BugReport'] = BugReport()
        else:
            self.forms['BugReport'].show()

    def showAbout(self, event=None):
        """the 'about Vision' dialog window"""
        if self.forms['aboutDialog'] is None:
            self.forms['aboutDialog'] = AboutDialog()
        else:
            self.forms['aboutDialog'].show()

            
    def showAcknowl(self, event=None):
        """the 'acknowledgements' dialog window"""
        if self.forms['acknowlDialog'] is None:
            self.forms['acknowlDialog'] = AcknowlDialog()
        else:
            self.forms['acknowlDialog'].show()


    def showTutorials(self):
        import tkMessageBox
        tkMessageBox.showinfo("Tutorials and examples",
"""Tutorials and examples must be downloaded separately from the section "Supplementary Material" at http://mgltools.scripps.edu/downloads

In the archive file, you will find a beginner's tutorial: doc/Tutorial/tutorial.rtf

and Jose Unpingco has prepared some nice video tutorials http://www.osc.edu/blogs/index.php/sip
""")


    def showInstallVision(self):
        import tkMessageBox
        tkMessageBox.showinfo("Install Vision in a different Python interpreter",
"""
Python versions 2.4, 2.5 and 2.6.1 are supported.

The simpliest is to use the provided source code for all platforms
http://mgltools.scripps.edu/downloads

However, the following describes the procedure to make a manual minimum installation:

Vision uses Tkinter ( which needs tcl / tk ), it also requires Pmw and numpy. Please, first verify you have it by typing in a python shell:

import Tkinter
import Pmw
import numpy

If all this works without any error, just copy the following folders:

Vision, NetworkEditor, mglutil, Support, VisionLibraries and WebServices

into the "site-packages" folder in your implementation of Python.

After installation is completed, type in a new python shell:

import Vision
Vision.runVision()

If PIL or matplotlib are installed, the corresponding Vision libraries are then available.
""")


    def showRefs(self, event=None):
        """the 'references' dialog window"""
        if self.forms['refDialog'] is None:
            self.forms['refDialog'] = RefDialog()
        else:
            self.forms['refDialog'].show()


    def showFAQ(self, event=None):
        from mglutil.util.packageFilePath import findFilePath
        file = findFilePath('FAQ.html', 'Vision')
        #file = os.path.join(
        #    os.path.abspath(os.path.curdir), 'Vision/FAQ.html')
        if file:
            webbrowser.open(file)

        
    def searchModules(self, name):
        if name is None or name == '':
            return
        if self.searchAfterId != None:
            self.lastSearchNode.deselect()

        if name != self.lastSearchString: # new search
            self.lastMatchIndices = [0, 0, 0]
        else:
            self.lastMatchIndices[2] = self.lastMatchIndices[2] + 1
            
        pat = re.compile(string.lower(name))
        if name is None or len(name)==0:
            return

        # loop over libraries
        libraries = self.libraries.items()
        lastInd = self.lastMatchIndices
        for libInd in range(lastInd[0], len(libraries)):        
            libName, lib = libraries[libInd]
            #print 'LIB', libName
            self.lastMatchIndices[0] = libInd
            categories = lib.libraryDescr.values()
            # loop over categories
            for catInd in range(lastInd[1], len(lib.libraryDescr)):
                cat = categories[catInd]
                self.lastMatchIndices[1] = catInd
                itemNum=lastInd[2]
                #print 'CAT', catInd
                # loop over nodes
                for nodeInd in range(lastInd[2], len(cat['nodes'])):
                    node = cat['nodes'][nodeInd]
                    self.lastMatchIndices[2] = nodeInd
                    res = pat.search(string.lower(node.name))
                    if res:
                        #print 'NODE MATCH', node.name
                        # show the library
                        self.ModulePages.selectpage(libName)
                        # get a handle to the category canvas
                        canvas = cat['canvas']
                        # scroll the canvas to show the node
                        canvas.selectItem(itemNum)
                        # highlight the node
                        n = node.dummyNode
                        n.select()
                        # set the focus to the entry so we can search again
                        self.modSearch._entryWidget.focus_set()
                        self.lastSearchNode = n
                        # register function to unselect
                        func = CallBackFunction(self.desel, n)
                        self.afterId = canvas.after(1000, func)
                        self.lastSearchString = name
                        return

                    itemNum = itemNum + 1

                # reset node index
                self.lastMatchIndices[2] = 0

            # reset category index
            self.lastMatchIndices[1] = 0
            
        # nothing was found, reset all indices
        self.lastMatchIndices = [0, 0, 0]
        # remove entry from dropdown
        all = list(self.modSearch.getAllValues())
        all.remove(name)
        self.modSearch.setlist(all)
        self.lastSearchString = name


    def setFont(self, *args):
        msg = """Usage: self.setFont(<itemname>, <fontconfig>)
For Example: self.setFont('Menus', (ensureFontCase('helvetica'), 9, 'bold')
Legal itemnames: 'All'
                 'Menus'
                 'LibTabs'
                 'Categories'
                 'LibNodes'
                 'NetTabs'
                 'Nodes'
                 'Root'"""


        # call base class method first
        newargs = [self]
        newargs.extend(list(args))
        apply(NetworkBuilder.setFont, tuple(newargs), {})

        if args is None or args == () or len(args) != 2:
            print msg
            return

        else:
            tag = args[0]
            font = args[1]
            assert len(font) == 3
            font = tuple(font)

        if tag == 'LibTabs' or tag == 'All':
            self.font['LibTabs'] = font
            for tab in self.ModulePages.pagenames():
                libTab = self.ModulePages.tab(tab)
                libTab.configure(font=font)
                # get info to resize the tab
                width = libTab.winfo_reqwidth()
                height = libTab.winfo_reqheight()
                self.ModulePages._pageAttrs[tab]['tabreqwidth'] = width
                self.ModulePages._pageAttrs[tab]['tabreqheight'] = height
            # resize all tabs
            self.ModulePages._pending['tabs'] = 1
            self.ModulePages._layout()

        if tag == 'Categories' or tag == 'All':
            self.font['Categories'] = font
            for lib in self.libraries.keys():
                for category in self.libraries[lib].libraryDescr.keys():
                    canv = self.libraries[lib].libraryDescr[category]['canvas']
                    if canv is not None:
                        try:
                            canv.component('label').configure(font=font)
                        except:
                            print "TclError"

        if tag == 'LibNodes' or tag == 'All':
            self.font['LibNodes'] = font
            for lib in self.libraries.values():
                # set balloon font.
                lib.balloons.component('label').configure(font=font)
                # set node proxy font
                for catName in lib.libraryDescr.keys():
                    cat = lib.libraryDescr[catName]
                    proxy = cat['nodes'][0] # we have to mark only the first
                    proxy.dummyNode.iconMaster.itemconfigure(
                        proxy.dummyNode.textId, font=font)
                    lib.rebuildNodesInCategoryFrame(catName)
            
                            
    def desel(self, node):
        node.deselect()


    def selectFunc(self, name, event=None):
        # for buttonBar
        func = self.buttonBarFunc[name]
        if func:
            func(event=event)


    def glyphselectFunc(self, name, event=None):
        #for glyphbuttonBar
        func = self.glyphbuttonBarFunc[name]
        if func:
            func(event=event)


    def resizeCategories_cb(self, event=None):
        libName = self.ModulePages.getcurselection()
        currLib = self.libraries[libName]
        currLib.resizeCategories()
        

    def addCategory_cb(self, event=None):
        libName = self.ModulePages.getcurselection()
        currLib = self.libraries[libName]
        
        while 1:
            catName = askstring("Library %s"%libName, "Category Name")
            if catName is None: # 'Cancel'
                return
            if not len(catName): # <Enter> without typing anything
                continue
            if not currLib.libraryDescr.has_key(catName):
                break

        if currLib.mode != 'readWrite':
            tkMessageBox.showwarning(
                "Vision Node Library",
                "Error! Node library '%s' cannot be modified!\nOnly User Libraries can be modified."%currLib.name)
            return
            
        currLib.addCategoryFrame(catName)
        currLib.resizeCategories()


    def deleteCategory_cb(self, event=None):
        libName = self.ModulePages.getcurselection()
        currLib = self.libraries[libName]
        
        while 1:
            catName = askstring("Library %s"%libName, "Category Name")
            if catName is None: # 'Cancel'
                return
            if not len(catName): # <Enter> without typing anything
                continue
            if currLib.libraryDescr.has_key(catName):
                break

        if currLib.mode != 'readWrite':
            tkMessageBox.showwarning(
                "Vision Node Library",
                "Error! Node library '%s' cannot be modified!\nOnly User Libraries can be modified."%currLib.name)
            return

        currLib.deleteCategoryFrame(catName)
        del currLib.libraryDescr[catName]
        currLib.resizeCategories()


    def addCircle(self,bbox=[],fill="",outline="black",anchor=None):
        canvas = self.currentNetwork.canvas
        kw={}
        kw['bbox'] = bbox
        kw['fill'] = fill
        kw['outline'] = outline
        kw['anchor'] = anchor
        g = Glyph(canvas = canvas,shape="circle",kw=kw)
        id = g.create_circle(bbox=bbox,fill=fill,outline =outline,anchor=anchor)
        return id


    def addRectangle(self,bbox=[],fill="",outline="black",anchor=None):
        canvas = self.currentNetwork.canvas 
        kw={}
        kw['bbox'] = bbox
        kw['fill'] = fill
        kw['outline'] = outline
        kw['anchor'] = anchor
        g = Glyph(canvas = canvas,shape="rectangle",kw=kw)
        id = g.create_rectangle(bbox=bbox,fill=fill,outline =outline,anchor=anchor)
        return id


    def glyphlab_cb(self,event=None):
        canvas = self.currentNetwork.canvas
        canvas.configure(cursor="cross")
        self.currentNetwork.glyphshape = "text"
        self.currentNetwork.glyphSelect = None


    def glyphcir_cb(self,event=None):
        canvas = self.currentNetwork.canvas
        canvas.configure(cursor="cross")
        self.currentNetwork.glyphshape = "circle"        
        self.currentNetwork.glyphSelect = None


    def glyphrec_cb(self,event=None):
        canvas = self.currentNetwork.canvas
        canvas.configure(cursor="cross")
        self.currentNetwork.glyphshape = "rectangle"    
        self.currentNetwork.glyphSelect = None


    def glyphspray_cb(self,event=None):
        canvas = self.currentNetwork.canvas
        canvas.configure(cursor="spraycan")
        self.currentNetwork.glyphKeywords['spray'] = True


    def glyphfontb_cb(self,event=None):
        self.currentNetwork.glyphKeywords['fontstyle'] = "bold"   


    def glyphfonti_cb(self,event=None):
        self.currentNetwork.glyphKeywords['fontstyle'] = "italic"


    def glyphfontu_cb(self,event=None):
        self.currentNetwork.glyphKeywords['fontstyle'] = "underline"


    def glyphselect_cb(self,event=None):
        canvas = self.currentNetwork.canvas
        canvas.configure(cursor="cross")
        self.currentNetwork.glyphSelect =1
        self.currentNetwork.glyphshape = None


    def glyphcut_cb(self,event=None):
        canvas = self.currentNetwork.canvas
        canvas.configure(cursor="cross")
        self.currentNetwork.glyphSelect =1
        if self.currentNetwork.gselectionboxes:
            c = canvas.coords
            coords = [c(self.currentNetwork.gselectionboxes[0])[0]+2,c(self.currentNetwork.gselectionboxes[0])[1]+2,c(self.currentNetwork.gselectionboxes[1])[0]+2,c(self.currentNetwork.gselectionboxes[1])[1]+2]
            items = canvas.find_enclosed(coords[0],coords[1],coords[2],coords[3])
            for i in items:
                canvas.delete(i)
            for b in self.currentNetwork.gselectionboxes:
                canvas.delete(b)


    def fontStyle(self,val):
        self.currentNetwork.glyphKeywords['font']=val


    def fontSize(self,val):
        self.currentNetwork.glyphKeywords['fontsize']=val


    def fillStyle(self,val):
        self.currentNetwork.glyphKeywords['fill']=val


    def outlineStyle(self,val):
        self.currentNetwork.glyphKeywords['outline']=val


    def addButtonsToglyphButtonBar(self, master):
        glyphbuttonList = [
            {'sep1':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                     'func':None, 'balloon':None}},
            {'label':{'icon1':'text.gif', 'icon2':None, 'state':'normal',
                      'func':self.glyphlab_cb, 'balloon':'Label'}},
            {'circle':{'icon1':'circle.gif', 'icon2':None, 'state':'normal',
                       'func':self.glyphcir_cb, 'balloon':'Circle'}},
            {'rectangle':{'icon1':'rectangle.gif', 'icon2':None,
                          'state':'normal',
                          'func':self.glyphrec_cb, 'balloon':'Rectangle'}},
            {'select':{'icon1':'arrow1.gif', 'icon2':None, 'state':'normal',
                       'func':self.glyphselect_cb, 'balloon':'Select'}},
            {'cut':{'icon1':'cut2.gif', 'icon2':None, 'state':'normal',
                    'func':self.glyphcut_cb, 'balloon':'Cut'}},
            {'Bold':{'icon1':'bold.gif', 'icon2':None, 'state':'normal',
                     'func':self.glyphfontb_cb, 'balloon':'Bold'}},
            {'Italic':{'icon1':'italic.gif', 'icon2':None, 'state':'normal',
                       'func':self.glyphfonti_cb, 'balloon':'Italic'}},
            {'Underline':{'icon1':'underline.gif', 'icon2':None,
                          'state':'normal',
                          'func':self.glyphfontu_cb, 'balloon':'Underline'}},
            {'Spary':{'icon1':'spraycan.gif', 'icon2':None, 'state':'normal',
                      'func':self.glyphspray_cb, 'balloon':'Fill'}},
            ]
        from mglutil.util.packageFilePath import findFilePath
        ICONPATH = findFilePath('Icons', 'Vision')
        for item in glyphbuttonList:
            name=item.keys()[0]
            icon1 = item[name]['icon1']
            icon2 = item[name]['icon2']
            state = item[name]['state']
            func  = item[name]['func']
            balloon = item[name]['balloon']
            ToolBarButton(None, self.glyphbuttonBar, name=name, icon1=icon1,
                          icon2=icon2, state=state,
                          command=self.glyphselectFunc, balloonhelp=balloon,
                          statushelp=balloon,
                          iconpath=ICONPATH )
            self.glyphbuttonBarFunc[name] = func


    def addButtonsToButtonBar(self, master):
        # balloons were moved from the cursor to fix a problem with
        # node library balloons flashing 

        buttonList = [
            {'sep1':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'new':{'icon1':'new.gif', 'icon2':None, 'state':'normal',
                   'func':self.newNet_cb, 'balloon':'new network'}},
            {'open':{'icon1':'open.gif', 'icon2':None, 'state':'normal',
                   'func':self.loadNetwork_cb, 'balloon':'open network'}},
            {'merge':{'icon1':'merge1.gif', 'icon2':'merge2.gif',
                      'state':'disabled',
                   'func':self.mergeNetwork_cb, 'balloon':'merge networks'}},
            {'loadLib':{'type':'menubutton',
                        'icon1':'loadLib2.gif',
                        'func':self.showLoadLibraryForm2_cb,
                        'balloon':'load library'}},

            {'save':{'icon1':'save1.gif', 'icon2':'save2.gif',
                    'state':'disabled', 'func':self.saveNetwork_cb,
                    'balloon':'save network'}},
            {'print':{'icon1':'print1.gif', 'icon2':'print2.gif',
                    'state':'disabled', 'func':self.print_cb,
                    'balloon':'print network'}},

            {'sep3':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'runOnNewData':{'type':'checkbutton',
                             'icon1':'tapclosed.gif',
                             'icon2':'tapopen.gif',
                             'func':self.setRunOnNewData_cb,
                             'balloon':'toggle immediate run'}},

            {'softrun':{'icon1':'run1.gif', 'icon2':'runGreen.gif',
                    'state':'disabled', 'func':self.softrunCurrentNet_cb,
                    'balloon':'soft run current network'}},

            {'run':{'icon1':'run1.gif', 'icon2':'run2.gif',
                    'state':'disabled', 'func':self.runCurrentNet_cb,
                    'balloon':'hard run current network (force run)'}},
        
            {'pause':{'icon1':'pause1.gif', 'icon2':'pause2.gif',
                    'state':'disabled', 'func':self.togglePauseCurrentNet_cb,
                    'balloon':"pause current network's execution"}},
            
            {'stop':{'icon1':'stop1.gif', 'icon2':'stop2.gif',
                    'state':'disabled', 'func':self.stopCurrentNet_cb,
                    'balloon':"stop current network's execution"}},

            {'sep4':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'runWithoutGui':{'icon1':'run1.gif', 'icon2':'runBlack.gif',
                    'state':'disabled', 'func':self.runWithoutGui_cb,
                    'balloon':'run current network without GUI in a separate process'}},

            {'stopWithoutGui':{'icon1':'stop1.gif', 'icon2':'stop2.gif',
                    'state':'disabled', 'func':self.stopWithoutGui_cb,
                    'balloon':"stop execution without GUI"}},

            {'sep5':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'gantt':{'icon1':'teprla1.gif', 'icon2':'teprla1.gif',
                    'state':'enabled', 'func':self.toggleGantt_cb,
                    'balloon':"show/hide GANTT diagram of execution times"}},

            {'debug':{'icon1':'flowengine_6.gif', 'icon2':'flowengine_6.gif',
                    'state':'enabled', 'func':self.debugCurrentNet_cb,
                    'balloon':"build the list of node to execute and step through them"}},

            {'step':{'icon1':'stepover_6.gif', 'icon2':'stepover_6.gif',
                    'state':'disabled', 'func':self.debugStep_cb,
                    'balloon':"Execute current node in node list"}},

            {'sep5a':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'cut':{'icon1':'cut1.gif', 'icon2':'cut2.gif',
                    'state':'disabled', 'func':self.cutNetwork_cb,
                    'balloon':'cut'}},
            {'copy':{'icon1':'copy1.gif', 'icon2':'copy2.gif',
                    'state':'disabled', 'func':self.copyNetwork_cb,
                    'balloon':'copy'}},
            {'paste':{'icon1':'paste1.gif', 'icon2':'paste2.gif',
                    'state':'disabled', 'func':self.pasteNetwork_cb,
                    'balloon':'paste'}},

            {'sep6':{'icon1':'sep.gif', 'icon2':None, 'state':'disabled',
                   'func':None, 'balloon':None}},

            {'find':{'icon1':'find2.gif', 'icon2':'find2.gif',
                    'state':'enabled', 'func':self.searchNodes_cb,
                    'balloon':'open search nodes panel'}},
           ]

        from mglutil.util.packageFilePath import findFilePath
        ICONPATH = findFilePath('Icons', 'Vision')

        self.buttonIcons = {} #otherwise the icon is lost and not displayed (tk bug)
        for item in buttonList:
            name=item.keys()[0]
            icon1 = item[name]['icon1']
            func  = item[name]['func']
            balloon = item[name]['balloon']
            self.buttonBarFunc[name] = func
            if item[name].has_key('type') is False:
                icon2 = item[name]['icon2']
                state = item[name]['state']
                # Note: we pass balloonmaster=None to class ToolBarButton
                # so it will create an attribute 'balloons' in self.buttonBar
                # so Pmw.Balloon will be an instance in self.buttonBar.balloons
                ToolBarButton(None, self.buttonBar, name=name, icon1=icon1,
                          icon2=icon2, state=state,
                          command=self.selectFunc, balloonhelp=balloon,
                          statushelp=balloon,
                          iconpath=ICONPATH )
            else:
                head, ext = os.path.splitext(icon1)
                ICONPATH1 = os.path.join(ICONPATH, icon1)
                if ext == '.gif':
                    Icon = Tkinter.PhotoImage(file=ICONPATH1, master=master)#, master=self.ROOT)
                else:
                    import Image
                    import ImageTk
                    image = Image.open(ICONPATH1)
                    Icon = ImageTk.PhotoImage(image=image, master=master)
                if item[name]['type'] == 'menubutton':
                    self.buttonIcons[name] = Icon
                    lButton = Tkinter.Menubutton(self.buttonBar, 
                                                     text = 'load library',
                                                     image=Icon
                                                     )
                    self.fastLibsMenu2 = Tkinter.Menu(lButton, tearoff=0)
                    self.updateFastLibs()
                    lButton.menu = self.fastLibsMenu2
                    lButton['menu'] = lButton.menu
                elif item[name]['type'] == 'checkbutton':
                    if hasattr(self, 'buttonVariables') is False:
                        self.buttonVariables = {}
                    if self.buttonVariables.has_key(name) is False:
                        self.buttonVariables[name] = Tkinter.IntVar()
                    self.buttonIcons[name] = [Icon,]   
                    lButton = Tkinter.Checkbutton(self.buttonBar,
                                               image=Icon,
                                               indicatoron=0,
                                               variable=self.buttonVariables[name],
                                               command=func,
                                               selectcolor='blue',
                                               background='white',
                                               )

                    if item[name].has_key('icon2'):
                        icon2 = item[name]['icon2']
                        head2, ext2 = os.path.splitext(icon2)
                        ICONPATH2 = os.path.join(ICONPATH, icon2)
                        if ext2 == '.gif':
                            Icon2 = Tkinter.PhotoImage(file=ICONPATH2, master=master)#, master=self.ROOT)
                        else:
                            image2 = Image.open(ICONPATH2)
                            Icon2 = ImageTk.PhotoImage(image=image2, master=master)
                        self.buttonIcons[name].append(Icon2)
                        lButton.configure(selectimage=Icon2)

                # add ballon to this button
                if hasattr(self.buttonBar, 'balloons') is False:
                    self.buttonBar.balloons = Pmw.Balloon(self.buttonBar, yoffset=0)
                self.buttonBar.balloons.bind(lButton, balloon, balloon)
                
                lButton.pack(side=Tkinter.LEFT, padx="1m")
                # add the button to the list stored in the master
                self.buttonBar.toolbarButtonDict[name] = lButton


    def searchNodes_cb(self, event=None):
        """Open the search nodes GUI"""
        if self.forms['searchNodesDialog'] is None:
            self.forms['searchNodesDialog'] = SearchNodesDialog(self)
        else:
            self.forms['searchNodesDialog'].show()


    def runCurrentNet_cb(self, event=None):
        """VPE wrapper of runCurrentNet_cb. toggle button bar buttons"""
        bl = self.buttonBar.toolbarButtonDict
        bl['run'].disable()
        if bl.has_key('softrun'):
            bl['softrun'].disable()
        #if self.withThreads is True:
        #    bl['pause'].enable()
        bl['pause'].enable()
        bl['stop'].enable()
        net = self.currentNetwork
        net.canvas.update_idletasks()
        
        NetworkBuilder.runCurrentNet_cb(self)
        #net.run()

    def debugCurrentNet_cb(self, event=None):
        """VPE wrapper of debugCurrentNet_cb. toggle button bar buttons"""
        bl = self.buttonBar.toolbarButtonDict
        bl['debug'].disable()
        bl['step'].enable()
        #if self.withThreads is True:
        #    bl['pause'].enable()
        net = self.currentNetwork
        net.canvas.update_idletasks()
        net.debug = True

        NetworkBuilder.runCurrentNet_cb(self)
        net.debug = False
        bl['debug'].enable()
        bl['step'].disable()


    def debugStep_cb(self, event=None):
        self.currentNetwork.debugCmd = 'step'
    

    def softrunCurrentNet_cb(self, event=None):
        """VPE wrapper of softrunCurrentNet_cb. toggle button bar buttons"""
        bl = self.buttonBar.toolbarButtonDict
        bl['run'].disable()
        if bl.has_key('softrun'):
            bl['softrun'].disable()
        #if self.withThreads is True:
        #    bl['pause'].enable()
        bl['pause'].enable()
        bl['stop'].enable()
        net = self.currentNetwork
        net.canvas.update_idletasks()
        
        NetworkBuilder.softrunCurrentNet_cb(self)



    def runWithoutGui_cb(self, event=None):
        """VPE wrapper of runWithoutGui_cb. toggle button bar buttons
"""
        if self.currentNetwork is None \
          or len(self.currentNetwork.nodes) == 0:
            warnings.warn('no Network to run without GUI')
            return
        else:
            print "running current network without GUI"

        bl = self.buttonBar.toolbarButtonDict
        if bl.has_key('runWithoutGui'):
            bl['runWithoutGui'].disable()        
        if bl.has_key('stopWithoutGui'):
            bl['stopWithoutGui'].enable()
        net = self.currentNetwork
        net.canvas.update_idletasks()

        # save the temporary file to be run
        if self.currentNetwork.filename is not None:
            lNetworkDir = os.path.dirname(self.currentNetwork.filename)
        else:
            import Vision
            lNetworkDir = Vision.networkDefaultDirectory

        try:
            self.removeTemporaryNetworkFile()
            from tempfile import mktemp
            self.temporaryFilename = mktemp(dir=lNetworkDir)
            self.saveNetwork(self.temporaryFilename, temporary=True)

            self.killRunWithoutGui()

            from subprocess import Popen, PIPE, call, check_call
            if sys.platform == 'win32':
                net.processWithoutGui = Popen(
                    ['python',
                     self.temporaryFilename,'-w'],
                     shell=False, cwd=lNetworkDir)
            else:
                net.processWithoutGui = Popen(
                    [self.resourceFolder+'/pythonsh',
                     self.temporaryFilename,'-w'],
                     shell=False, cwd=lNetworkDir)

            
            ## bind widget in setwork to remote process
            for node in self.currentNetwork.nodes:
                for p in node.inputPorts:
                    if p.widget:
                        p.widget.bindToRemoteProcessNode()

            def verifyProcessWithoutGui():
                net = self.currentNetwork
                #print verifyProcessWithoutGui, net.processWithoutGui.poll()
                if hasattr(net, 'processWithoutGui') \
                  and net.processWithoutGui.poll() != 0:
                    self.after(1000, verifyProcessWithoutGui)
                else:
                    self.stopWithoutGui_cb()

            self.after(1000, verifyProcessWithoutGui)

            # wait for process to start and write self.temporaryFilename.sock
            from os import path
            from time import sleep
            while 1:
                if path.exists(self.temporaryFilename+'.sock'):
                    break
                else:
                    sleep(0.1)

            f = open(self.temporaryFilename+'.sock')
            host, port = f.readlines()[0].split()
            f.close()

            net = self.currentNetwork
            net.remoteProcessSocket = self.currentNetwork.connectToProcess(
                host, int(port))
            
            #net.remoteProcessSocket = net.clientConnect()
##             import socket
##             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##             HOST = ''                 # Symbolic name meaning the local host
##             PORT = 50010              # Arbitrary non-privileged port

##             i = 0
##             from time import sleep
##             while 1:
##                 err = s.connect_ex((HOST, PORT))
##                 print PORT, err
##                 if err == 111:
##                     sleep(0.2)
##                     i +=1
##                     if i == 10:
##                         break
##                     continue
##                 break
##             net.socket = s

        except Exception, e:
            warnings.warn("""can't save or run temporary file to run without GUI,
on unix make sure ksh is installed as /bin/ksh""")
            print e


    def killRunWithoutGui(self):
        """
"""
        net = self.currentNetwork
        if hasattr(net, 'processWithoutGui'):
            if sys.platform == 'win32':
                def kill(pid):
                    """kill function for Win32"""
                    import win32api
                    handle = win32api.OpenProcess(1, 0, pid)
                    return (0 != win32api.TerminateProcess(handle, 0))
                if net.processWithoutGui.poll() is None:
                    kill(net.processWithoutGui.pid)
            else:
                from signal import SIGHUP
                if net.processWithoutGui.poll() is None:
                    os.kill(net.processWithoutGui.pid, SIGHUP)
            del net.processWithoutGui


    def removeTemporaryNetworkFile(self):
        """
"""
        if hasattr(self, 'temporaryFilename'):
            os.remove(self.temporaryFilename)
            os.remove(self.temporaryFilename+'.sock')
            del self.temporaryFilename


    def stopCurrentNet_cb(self, event=None):
        """VPE wrapper of stopCurrentNet_cb. toggle button bar buttons"""
        bl = self.buttonBar.toolbarButtonDict
        if isinstance(self.currentNetwork, MacroNetwork) is False:
            bl['run'].enable()
            if bl.has_key('softrun'):
                bl['softrun'].enable()
        #bl['runWithoutGui'].enable()
        bl['pause'].disable()
        bl['stop'].disable()
        self.currentNetwork.onStoppingExecution()
        NetworkBuilder.stopCurrentNet_cb(self)


    def stopWithoutGui_cb(self, event=None):
        """
"""
        bl = self.buttonBar.toolbarButtonDict
        if isinstance(self.currentNetwork, MacroNetwork) is False:
            if bl.has_key('runWithoutGui'):
                bl['runWithoutGui'].enable()
        if bl.has_key('stopWithoutGui'):
            bl['stopWithoutGui'].disable()
        self.currentNetwork.onStoppingExecution()
        self.killRunWithoutGui()
        self.removeTemporaryNetworkFile()
        for node in self.currentNetwork.nodes:
            for p in node.inputPorts:
                if p.widget:
                    p.widget.unbindFromRemoteProcess()


    def togglePauseCurrentNet_cb(self, event=None):
        """VPE wrapper of togglePauseCurrentNet_cb.
toggle button bar buttons"""
        bl = self.buttonBar.toolbarButtonDict
        net = self.currentNetwork
        net.execStatusLock.acquire()
#        if net.execStatus == 'pause':
#            bl['run'].disable()
#            bl['softrun'].disable()
#            bl['runWithoutGui'].disable()
#        else:
#            bl['run'].disable()
#            bl['softrun'].disable()
#            bl['runWithoutGui'].disable()
        net.execStatusLock.release()
        net.canvas.update_idletasks()
        net.togglePause()
            

    def endOfRun(self, net):
        """VPE wrapper of endOfRun. handle toolbar buttons
"""
        bl = self.buttonBar.toolbarButtonDict
        bl['run'].enable()
        if bl.has_key('softrun'):
            bl['softrun'].enable()
        bl['pause'].disable()
        bl['stop'].disable()
#        if hasattr(self, 'processWithoutGui') is False:
#            bl['runWithoutGui'].enable()
#            bl['stop'].disable()

       
    def addStdButtons(self):
        # note: this method is no longer called, since we have now a
        # toolbar with icons
        self.stdButtonsPage = self.ButtonsPages.add('Std')
        Tkinter.Button(self.stdButtonsPage, text='Load Network',
                       command=self.loadNetwork_cb).pack(expand=1, fill='x')
        
        Tkinter.Button(self.stdButtonsPage, text='Save Network',
                       command=self.saveNetwork_cb).pack(expand=1, fill='x')
        Tkinter.Button(self.stdButtonsPage, text='Run Network',
                       command=self.runNetwork).pack(expand=1, fill='x')
##          self.flowbt = Tkinter.Button(self.stdButtonsPage, text='Disable Flow',
##                                       command=self.flowButton_cb)
##          self.flowbt.pack(expand=1, fill='x')
        self.libButtonsPage = self.ButtonsPages.add('Libraries')
        Tkinter.Button(self.libButtonsPage, text='Load Library',
                       command=self.showLoadLibraryForm_cb).pack(expand=1, fill='x')


    def showConfigureFontsForm_cb(self, event=None):
        if self.forms['configureFontsPanel'] is None:
            self.forms['configureFontsPanel'] = ChangeFonts(editor=self)
        else:
            self.forms['configureFontsPanel'].show()


    def showLoadLibraryForm_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'l':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)
        
        # display the GUI for loading node libraries 
        if self.forms['loadLibraryPanel'] is None:
            self.forms['loadLibraryPanel'] = LoadLibraryPanel(self)
        else:
            self.forms['loadLibraryPanel'].show()


    def showLoadLibraryForm2_cb(self, event=None):
        self.fastLibsMenu.post(event.x_root,event.y_root)


    def showBrowseLibraryForm_cb(self, event=None):
        # display the GUI for browsing all available libraries
        if self.forms['browseLibsPanel'] is None:
            self.forms['browseLibsPanel'] = BrowseLibraryPanel(self)
        else:
            self.forms['browseLibsPanel'].show()


    def showCreateLibraryForm_cb(self, event=None):
        # check if we have a user-created node library directory
        if len(self.userLibsDirs.keys()) == 0:
            tkMessageBox.showwarning(
                "Create Library",
                "ERROR! No directory available.\n\nPlease, create a directory as described in the FAQ!\nConsult menu 'Help'->'FAQ'")
            return

        # display the GUI for creating a new library
        if self.forms['createLibsPanel'] is None:
            self.forms['createLibsPanel'] = CreateLibraryPanel(self)
        else:
            self.forms['createLibsPanel'].show()


    def showSaveLibraryForm_cb(self, event=None):
        # display the GUI for saving a new library
        if self.saveLibsPanel is None:
            self.saveLibsPanel = CreateLibraryPanel(self)
        else:
            self.saveLibsPanel.show()


    def showHideLibraries_cb(self, event=None):
        """Display or hide the node libraries"""
        menu = self.menuButtons['Libraries'].menu
        try:
            menu.index("Show libraries")
            show = True
        except:
            show = False

        if show: # pack the frame
            self.modulePagesF.pack(expand=1, fill='both')
            menu.entryconfigure('Show libraries', label='Hide libraries')
            # extend pane, we need 2 steps, else the pane is displd. too big
            self.top.configurepane('ModulePages', min=150, max=150) 
            self.top.configurepane('ModulePages', min=100, max=10000000) 
            
        else: # forget the frame
            self.modulePagesF.forget()
            menu.entryconfigure('Hide libraries', label='Show libraries')
            # and shrink pane
            self.top.configurepane('ModulePages', min=0, max=0)
        
            
    def addLibraryInstance(self, lib, modName, varName, force=False):
        """load and show library which is provided as an instance of NodeLibary
lib is and instance of NodeLibrary which can be imported from modName (e.g.
Vision.StandarNodes) and is called varName in this module (e.g. stdlib),
"""
        NoGuiVPE.addLibraryInstance(self, lib, modName, varName, force=force)
        self.showLibrary(lib, force=force)


    def loadLibModule(self, module, dependents={}):

        if type(dependents) == types.DictType:
            for dep, depversion in dependents.items():
                try:
                    __import__(dep) # make sure all dependent packages are loadable
                except Exception, e:
                    warnings.warn("""
In order to use the vision library %s,
you need to install: %s %s\n""" %(module,dep,depversion))
                    import traceback
                    traceback.print_stack()
                    print e
                    return
        else:
            for dep in dependents:
                try:
                    __import__(dep) # make sure all dependent packages are loadable
                except Exception, e:
                    warnings.warn("""
In order to use the vision library %s,
you need to install: %s \n""" %(module,dep))
                    import traceback
                    traceback.print_stack()
                    print e
                    return

        from Vision.UserLibBuild import addDirToSysPath
        userLibsDir = module.replace('.', os.sep)
        moduleName = os.path.split(userLibsDir)[-1]
        userLibsDir = os.path.split(userLibsDir)[0]
        try:
            mod = __import__(module,globals(),locals(),[moduleName])
            try:
                reload(mod)
            except RuntimeError, e:
                import traceback
                traceback.print_stack()
                print e
                #print "loadLibModule: unable to reload library %s\n" % module, e
                pass # this is just to hide a potential problem in reloading (matplotlib has this issue) 

            for modItemName in dir(mod):
                modItem = getattr(mod, modItemName)
                from Vision.VPE import NodeLibrary
                if isinstance(modItem, NodeLibrary):
                    self.addLibraryInstance(modItem, module, modItemName, force=True)
        except Exception, e:
            import traceback
            traceback.print_stack()
            traceback.print_exc()
            print e

            
    def addLibraryFromName(self, libname, pathstr=None, dependents=[]):
        lib, modName = self.loadLibrary(libname, pathstr, dependents)
        self.addLibraryInstance(lib, modName, libname)
        
        
    def loadLibrary(self, libname, pathstr=None, dependents=[]):
        # importing a library called libname from pathstr.
        # if libname is found in Vision.nodeLibraries.libraries and pathstr
        # is None pathstr and dependents are looked up in libraries
        # THIS FUNCTION DOES NOT DISPLAY THE LIBRARY IN THE GUI
        from Vision.nodeLibraries import libraries

        if pathstr is None:
            if libname not in libraries.keys():
                raise RuntimeError('Library %s not registered!'%libname)
            else:
                pathstr = libraries[libname][0]
                dependents = libraries[libname][1]

        for dep in dependents:
            # make sure all dependent packages are loadable
            __import__(dep)
                
        nodelib = None
        mod = __import__(pathstr, globals(), locals(), [libname])

        nodelib = getattr(mod,libname)
        return nodelib, pathstr
            
        
    def showLibrary(self, lib, force=False):
        # display a loaded library in the GUI
        #print "showLibrary", lib.name

        if force is False and lib.page is not None:
            return # already displayed

        libname = lib.name.replace('_', ' ')
        if libname in self.ModulePages.pagenames():
            lib.page = self.ModulePages.delete(libname)
        lib.page = self.ModulePages.add(libname)
        lib.balloons = Pmw.Balloon(master=None, yoffset=30)

        lib.ed = self

        # within it own pane, create a scrolled canvas for each category
        lib.top = Pmw.PanedWidget(lib.page, orient='horizontal')
#                                  hull_width=self.width,
#                                  hull_height=self.height)


        # sort categories by name, sort nodenames by name
        catList = lib.libraryDescr.keys()
        catList.sort()

        font = lib.ed.font['LibNodes']
            
        for cat in catList:
            dict = lib.libraryDescr[cat]
            # create the category frames
            lib.addCategoryFrame(cat)

            nodeList = dict['nodes']
            # add icons for nodes in that category
            nodes = {}   # for each category of each library we build a
                         # dictonary of {nodeId:(NodeLibrary, NodeProxy)}
            maxx = 0
            posy = 0
            
            # sort nodeList by node name, ignoring upper- or lower case
            nodeList.sort(lambda x, y: cmp(string.lower(x.name),
                                           string.lower(y.name)))

            # now add dummy nodes to category frame
            for node in nodeList:
                maxx, posy, nodes = lib.addNodeToCategoryFrame(
                                                cat, node, nodes = nodes,
                                                font=font, maxx=maxx, vpe=self)
                dict['lastPosy'] = posy
                
            # update scrolled canvas
            sc_canvas = dict['canvas']
            canvas = sc_canvas.component('canvas')
            canvas.configure(width=150, height=150,
                             scrollregion=tuple((0,0,maxx,posy)))
#            sc_canvas.resizescrollregion()
            self.idToNodes[sc_canvas] = nodes
                        
        lib.top.pack(fill = 'both', expand = 1)
        
        # color this page and tab
        #Pmw.Color.changecolor(lib.page, color, foreground=color)
        
        ##for cat, dict in lib.libraryDescr.items():
        ##    pane = lib.top.add(cat, min=30, size=160)
        Pmw.Color.changecolor(self.ModulePages.component(libname+'-tab'),
                              lib.color)
        self.ModulePages.recolorborders()

        # in order to resize the panes, the library has to be displayed
        # after adding, we will jump back to the previously displayed lib
        oldpage = self.ModulePages.getcurselection()
        self.ModulePages.selectpage(libname)
        lib.resizeCategories()
        self.ModulePages.selectpage(oldpage)

        # and configure the font of the balloon in case in the meantime
        # the font was changed using the setFont() method
        ft = list(lib.ed.font['LibNodes'])
        ft[2] = 'bold' # make this always bold
        lib.balloons.component('label').configure(font=tuple(ft))

        # same goes for the lib tab font
        lfont = lib.ed.font['LibTabs']
        lib.ed.setFont('LibTabs', lfont)
        # and for the category font
        lib.ed.setFont("Categories", lib.ed.font["Categories"])


    def deleteLibrary(self, name):
        """Delete a node library: delete categories widget, delete
notebook tab, delete Tkinter attributes balloons, page, ed, top. Finally,
reset modified attributes such as lastPosy and delete lib from ed.libraries"""
        
        if name not in self.libraries.keys():
            return

        lib = self.libraries[name]

        # 1) delete categories
        lib.top.destroy()
        
        # 2) delete Pmw notebook tab
        self.ModulePages.delete(name)

        # 3) set attributes to None in lib to clear circular references
        #    and also reset some attributes such as lastPosy
        lib.balloons = None
        lib.page = None
        lib.ed = None
        lib.top = None
        for cat in lib.libraryDescr.values():
            cat['lastPosy'] = 15

        # 4) delete lib in self.libraries
        self.libraries.pop(name)
        
        
    # FACTS:
    # event.x, event.y are given in visible canvas coordiantes(always > 0)
    # canvas items coordinates, bbox etc given on absolute canvas coordinates
    # canvas.canvasx(absolute canvas coords) -> coordinates relative to visible
    #                                           region of canvas
    # when moving, evnt.x and event.y are always given relative to source
    # canvas absolute upper left corner 
    #
    # do not use sc_canvas but sc_canvas.component('canvas') in where


    def flowButton_cb(self, event=None):
        if self.isRunning:
            self.stopQueueHandler()
            self.flowbt.configure(text='Enable Flow')
        else:
            self.startQueueHandler()
            self.flowbt.configure(text='Disable Flow')


    def where(self, canvas, event):
        # compute coordinates of event.x and event.y in canvas
        
        # where the corner of the visible canvas is relative to the screen:
        x_org = canvas.winfo_rootx()
        y_org = canvas.winfo_rooty()
        # where the pointer is relative to the canvas widget:
        x = event.x_root - x_org + canvas.canvasx(0) - self.initialWinXoff
        y = event.y_root - y_org + canvas.canvasy(0) - self.initialWinYoff
        # compensate for initial pointer offset
        return x - self.x_off, y - self.y_off

        
    def startDNDnode(self, sc_canvas, event=None):
        # set keyboard focus so we can type to locate node
        sc_canvas.setFocus_cb()
        
        if sc_canvas.find_all() == (): # canvas without nodes
            return

        if self.currentNetwork is None:
            return

        canvas = event.widget
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        x0 = x-2
        y0 = y-2
        # coords of upper left corner of visible canvas (visible origin)
        #print 'canvas (0,0)', sc_canvas.canvasx(0), sc_canvas.canvasy(0)

        # x,y in visible canvas (i.e. relatif to visible origin)
        #print 'canvas vis', event.x, event.y

        # x,y relatif to canvas' (0,0)
        #print 'canvas abs', sc_canvas.canvasx(event.x), sc_canvas.canvasy(event.y)

        # x,y in screen pixels
        #print 'screen pixels', event.x_root, event.y_root

        # coordinate of canvas' origin in screen pixels
        #print 'winfo_root', sc_canvas.winfo_rootx(), sc_canvas.winfo_rooty()

        #canvas.create_rectangle(x0, y0, x+2, y+2, fill='red')

        # find the picked node
        items = canvas.find_overlapping(x0, y0, x+2, y+2)
        nodes = self.idToNodes[sc_canvas]
        self.nodeToCreate = None
        for i in items:
            if i in nodes.keys():
                self.nodeToCreate = nodes[i][1]
                n1 = nodes[i][0]
                bb = sc_canvas.component('canvas').bbox(n1.outerBox)
                break
        if not self.nodeToCreate: return
        

        # where the pointer is relative to upper left corner or selected node
        #bb = self.nodeToCreate.bbox
        self.x_off = event.x - bb[0]
        self.y_off = event.y - bb[1] 

        # save offset of visible canvas
        self.initialWinXoff = canvas.canvasx(0)
        self.initialWinYoff = canvas.canvasy(0)
        
        # create geometry that will move
        x, y = self.where(canvas, event)
        self.dndW = bb[2]-bb[0]
        self.dndH = bb[3]-bb[1]
        self.dndId = canvas.create_rectangle(
            x, y, x+self.dndW, y+self.dndH, width=2)
        
        # remember a few things about where we come from etc ...
        self.eventNum = event.num
        canvas.bind("<B%d-Motion>"%self.eventNum, self.moveDNDnode)
        canvas.bind("<ButtonRelease-%d>"%self.eventNum, self.endDNDnode)
        self.initialCanvas = sc_canvas
        self.currentWin =sc_canvas.winfo_containing(event.x_root, event.y_root)
        self.lastx = x
        self.lasty = y


    def moveDNDnode(self, event):

        canvas = self.currentWin
        # find canvas under cursor
        win = canvas.winfo_containing(event.x_root, event.y_root)

        if win != self.currentWin: # we change window
            if win==self.currentNetwork.canvas or \
               win==self.initialCanvas.component('canvas'):

                x, y = self.where(win, event)
                # delete box in previous window
                self.currentWin.delete(self.dndId)

                # set focus to win we we keep getting motion events
                win.focus_set()

                self.dndId = win.create_rectangle(
                    x, y, x+self.dndW, y+self.dndH, width=2)

                # remember current canvas etc...
                self.lastx = x
                self.lasty = y
                self.currentWin = win

        else: # motion inside self.currentWin
            x, y = self.where(win, event)
            dx = x - self.lastx
            dy = y - self.lasty
            canvas.move(self.dndId, dx, dy)
            self.lastx = x
            self.lasty = y


    def endDNDnode(self, event=None):
        # if we are on the editor canvas create node
        canvas = self.initialCanvas.component('canvas')
        canvas.unbind("<B%d-Motion>"%self.eventNum)
        canvas.unbind("<ButtonRelease-%d>"%self.eventNum)
        canvas = self.currentWin
        if canvas==self.currentNetwork.canvas:
            # get upper left corner of the square we have dragged down
            bbox = canvas.bbox(self.dndId)
            posx = bbox[0]
            posy = bbox[1]

            kw = self.nodeToCreate.kw
            args = self.nodeToCreate.args            

            # load library if not loaded
            lib = kw['library']
            self.addLibraryInstance(lib, lib.modName, lib.varName)

            node = apply( self.nodeToCreate.nodeClass, args, kw )
            
            ## FIXME ... is this still used ???
            if self.nodeToCreate.functionSourceCode:
                node.setFunction(self.nodeToCreate.functionSourceCode)

            self.currentNetwork.addNode(node, posx, posy)

            # add node to searchNodesDialog if the node came from there
            dia = self.forms['searchNodesDialog']
            if dia:
                w_canvas = dia.searchCanvas.component('canvas')
                if event.widget == w_canvas:
                    # add node to search node panel
                    dia.addNodeToLibPanel(self.nodeToCreate)
                    
        # and finally, delete the dummy box
        if canvas is not None:
            canvas.delete(self.dndId)



    def addNetwork(self, network):
        NetworkBuilder.addNetwork(self, network)
        handle = network.eventHandler['onSelectionChange']
        handle.AddCallback(self.handleSelectionChangeButtons)
        handle.AddCallback(self.handleAddNetworkButtons)
        # bind Vision-specific keystroke events
        network.canvas.bind('<Control-l>', self.showLoadLibraryForm_cb)
        network.canvas.bind('<F1>', self.showFAQ)
       


    def handleSelectionChangeButtons(self):
        """This is called by callback manager on event select or deselect
        nodes and turns on/off menu buttons. Do not confuse this method
        with handleSelectionChangeMenus() of simpleNE, which handles menu
        entries."""

        net = self.currentNetwork

        if len(net.selectedNodes):
            self.buttonBar.toolbarButtonDict['cut'].enable()
            self.buttonBar.toolbarButtonDict['copy'].enable()
        else:
            self.buttonBar.toolbarButtonDict['cut'].disable()
            self.buttonBar.toolbarButtonDict['copy'].disable()

        if self.private_pasteBuffer:
            self.buttonBar.toolbarButtonDict['paste'].enable()
        else:
            self.buttonBar.toolbarButtonDict['paste'].disable()


    def handleAddNetworkButtons(self):
        """This is called by callback manager on the event add network and
        turns on menu buttons."""

        self.buttonBar.toolbarButtonDict['merge'].enable()
        self.buttonBar.toolbarButtonDict['save'].enable()
        self.buttonBar.toolbarButtonDict['print'].enable()
        self.buttonBar.toolbarButtonDict['run'].enable()
        if self.buttonBar.toolbarButtonDict.has_key('softrun'):
            self.buttonBar.toolbarButtonDict['softrun'].enable()
        if self.buttonBar.toolbarButtonDict.has_key('runWithoutGui'):
            self.buttonBar.toolbarButtonDict['runWithoutGui'].enable()


    def handleDeleteNetworkButtons(self, **kw):
        """This is called by callback manager on the event delete network and
        turns on/off menu buttons."""

        if self.currentNetwork is None:
            self.buttonBar.toolbarButtonDict['merge'].disable()
            self.buttonBar.toolbarButtonDict['save'].disable()
            self.buttonBar.toolbarButtonDict['print'].disable()
            self.buttonBar.toolbarButtonDict['run'].disable()
            if self.buttonBar.toolbarButtonDict.has_key('softrun'):
                self.buttonBar.toolbarButtonDict['softrun'].disable()
            if self.buttonBar.toolbarButtonDict.has_key('runWithoutGui'):
                self.buttonBar.toolbarButtonDict['runWithoutGui'].disable()


    def exit_cb(self, event=None):
        # we add attributes to node libraries. Upon exit, we clear these
        # attributes:
        for lib in self.libraries.values():
            libname = lib.name.replace('_', ' ')
            self.deleteLibrary(libname)
        NetworkBuilder.exit_cb(self, event)
            

class NodeLibrary:
    """class used to describe a set of NetworkNodes. This is a container for
    NodeProxy objects"""

    def __init__(self, name, color='gray75', mode='readOnly'):
        self.name = name
        self.page = None # NoteBook page used to display library
        self.ed = None   # editor

        self.modName = None # name of the module this node came from
                            # e.g. 'Vision.StandardNodes'
        self.varName = None # name of the library object in file, e.g. 'stdlib'
        
        self.color = color
        assert mode =='readOnly' or mode=='readWrite'
        self.mode = mode
        self.typesTable = []
        self.synonymsTable = []
        self.widgets = []
        self.libraryDescr = {} # {category: {
                        #       'canvas' : scrolled canvas
                        #       'nodes': [NodeProxy]
                        #       'lastPosy': last Y value }
                        # node category, each category is shown in
                        # a separate scrolled canvas
        self.page = None    # notebook page in which it is displayed
        # Please note: self.top is created in showLibrary()

        # trick: we need an yoffset else the Balloon will or not be shown at
        # all because of window focus
        self.balloons = None # will be add in showLibrary

        self.nodes = [] # list of node's classes present in the library 
        self.nodeNames = []


    def addType(self, datatype):
        """add a datatype to the library. This datatype will be added to the
editor's data type manager when the library is laoded. The argument has to
be an instance of an AnyType object.
"""
        from NetworkEditor.datatypes import AnyType, AnyArrayType
        assert isinstance(datatype, AnyType) or isinstance(datatype, AnyArrayType) 
        self.typesTable.append(datatype)


    def addSynonym(self, synonymName, existingTypeName=None, datashape=None,
                       color=None, shape=None, width=None, height=None):
        """
"""
        lDict = {}
        lDict['synonymName'] = synonymName
        lDict['existingTypeName'] = existingTypeName
        lDict['datashape'] = datashape
        lDict['color'] = color
        lDict['shape'] = shape
        lDict['width'] = width
        lDict['height'] = height
        self.synonymsTable.append(lDict)


    def addWidget(self, widget):
        """add a widget to the library. This widget will be added to the
editor's list of widgets offered in the Port editor when the library is laoded. The argument has to be class subclasing PortWidget.
"""
        assert issubclass(widget, PortWidget)
        if widget not in self.widgets:
            self.widgets.append(widget)

        
    def addNode(self, nodeClass, name, category, args=None, kw=None,
                sourceCode=None):

#        #For WEB SERVICES this must be allowed (this is why it is commented out)
#        # forbid loading several time the same node
#        if nodeClass in self.nodes:
#            txt = "can't load node %s already present in library %s" %(nodeClass, self.name)
#            warnings.warn(txt)
#            return
#        # warn if loading node with the same name
#        if name in self.nodeNames:
#            txt = "loading node %s but this name already exists in library %s" %(name, self.name)
#            warnings.warn(txt)

        if kw is None:
            kw = {}

        if not kw.has_key('library'):
            kw['library'] = self

        if self.libraryDescr.has_key(category):
            nodeList = self.libraryDescr[category]['nodes']
            nodeList.append(
                NodeProxy( nodeClass, name, args=args, kw=kw,
                           functionSourceCode=sourceCode ))
        else:
            self.libraryDescr[category] =  {
                'canvas':None,'nodes':[NodeProxy(
                    nodeClass, name, args=args, kw=kw,
                    functionSourceCode=sourceCode )],
                'lastPosy':15 } # half height of node 

        if self.page: # library is visible in an editor -> add node
            dict = self.libraryDescr[category]
            if category in self.top.panes():
                sc_canvas = dict['canvas']
                # the first node has been added a few lines above
                if len(dict['nodes'])>1:
                    nodes = self.ed.idToNodes[sc_canvas]
                else:
                    nodes = {}
            else: # create new pane with scrolled canvas
                self.addCategoryFrame(category)
                sc_canvas = self.libraryDescr[category]['canvas']
                nodes = {}

            canvas = sc_canvas.component('canvas')
            posy = dict['lastPosy']
            node = dict['nodes'][-1]
            maxx = 0

            if node.name not in self.nodeNames:
                # build a dummy node so we can call its buildNodeIcon method
                maxx, posy, nodes = self.addNodeToCategoryFrame(
                             category, node, nodes=nodes, font=None, 
                             maxx=maxx, vpe=self.ed)
                
            # update scrolled canvas
            canvas.configure(width=150, height=150,
                             scrollregion=tuple((0,0,maxx,posy)))
            
            # register click for drag&drop
            self.ed.idToNodes[sc_canvas] = nodes
            dict['lastPosy'] = posy

        # this ensures that nodes created in a new category get displayed
        if self.ed is not None:
            self.resizeCategories()

        self.nodes.append(nodeClass)
        self.nodeNames.append(name)

##     def addCategory(self, cat):
##         """adds an empty category. This is used for User Libraries"""
##         if not self.libraryDescr.has_key(cat):
##             self.libraryDescr[cat] = {'canvas':None, 'nodes':[], 'lastPosy':15}

            
    def addCategoryFrame(self, cat):
        """Creates a ScrolledCanvas which is part of a nodes-library.
In this frame, dummy nodes can be added which can be dragged and dropped
onto the network editor canvas."""

        if not self.libraryDescr.has_key(cat):
            self.libraryDescr[cat] = {'canvas':None, 'nodes':[], 'lastPosy':15}
        dict = self.libraryDescr[cat]
        pane = self.top.add(cat, size=100) #will be resized below
        itemNames = []
        for node in dict['nodes']:
            itemNames.append(string.lower(node.name))
        itemNames.sort()

        sc_canvas = kbScrolledCanvas(
            pane, borderframe=1, labelpos='n', label_text=cat,
            usehullsize=1, hull_width=120, hull_height=150,
            vscrollmode='static', hscrollmode='none',#'dynamic',
            vertscrollbar_width=8, canvas_bg=self.color,
            itemNames=itemNames)

        self.libraryDescr[cat]['canvas'] = sc_canvas
        sc_canvas.pack(side='left', expand=1, fill='both')
        canvas = sc_canvas.component('canvas')
        cb = CallBackFunction(self.ed.startDNDnode, sc_canvas)
        canvas.bind('<Button-1>', cb )
        #self.top.updatelayout()


    def deleteCategoryFrame(self, cat):
        self.top.delete(cat)


    def resizeCategories(self):

        # set the notebook to fill the width
        # this will remove horiziontal scroll bar which will appear again
        # if main window is shrunk
        self.ed.ModulePages.configure(hull_width=self.ed.width-6)

        if len(self.libraryDescr.keys())==0:
            return # no categories
        # compute how much width the individual panes get
        if self.ed.top.winfo_width() == 1: # first time of instanciation
            self.ed.top.update_idletasks()
        # recalculate size and position of panes and distribute evenly

        # total width
        visWidth = self.ed.width #self.ed.top.winfo_width()
        # get number of categories
        panes = self.top.panes()
        lenLibs = len(panes)

        # find width of vertical scrollbar on the categories
        d = self.libraryDescr
        if d[d.keys()[0]]['canvas'] is not None:
            scwidth = int(d[d.keys()[0]]['canvas'].cget('vertscrollbar_width'))
            # compute size of 1 category 
            libSize = int(visWidth/float(lenLibs))-scwidth
            for p in panes:
                self.top.configurepane(p, size=libSize)


    def addNodeToCategoryFrame(self, cat, node, nodes=None,
                               font=None, maxx=None, vpe=None):
        """Add a dummy node to a library category frame.
"""
        #print "addNodeToCategoryFrame", node.name

        if nodes is None:
            nodes = {}

        if font is None:
            font = self.ed.font['LibNodes']

        if maxx is None:
            maxx = 0

        #build a dummy node
        # so we can call its buldNodeIcon method

        if cat not in self.libraryDescr.keys():
            self.addCategoryFrame(cat)
            
        dict = self.libraryDescr[cat]
        sc_canvas = dict['canvas']
        canvas = sc_canvas.component('canvas')
        posy = dict['lastPosy']
        # n1 is shown in the library notebook widget
        n1 = NetworkNode(name=node.name)
        n1.iconMaster = sc_canvas

        if hasattr(vpe,'drawPortInLibraryGui') and vpe.drawPortInLibraryGui is False:
            n1.buildSmallIcon(sc_canvas, 10, posy, font)
        else:
            # here starts the additions to draw the ports ***************
            if vpe is not None:
                n1.setEditor(vpe)
            nodeConstruct = {'typeManager':vpe.typeManager}
            nodeConstruct.update(node.kw)
            # n2 i sbuilt to lookup the input and output ports
            n2 = apply(node.nodeClass, (), nodeConstruct)
            if len(n2.inputPortsDescr) > len(n2.widgetDescr):
               posy += 2
            n1.buildIcons(sc_canvas, 10, posy, small=True)

            # draw port icons
            n2.id = n1.id
            n2.iconTag = n1.iconTag
            n2.iconMaster = n1.iconMaster
            if vpe is not None:
                n2.setEditor(vpe)
            i = 0
            pcy = n1.posy + 2
            for lPortDesc in n2.inputPortsDescr:
                lKw = lPortDesc.copy()
                lPortName = lKw['name']
                lKw.pop('name')
                try:
                    ip = apply( InputPort, (lPortName, n2), lKw)
                    visible = (n2.widgetDescr.get(ip.name, None) is None)
                    if visible is True: # port is not bind widget
                        if ip.datatypeObject['shape'] == 'diamond':
                            n2.scaleSum = .6
                        else:
                            n2.scaleSum = .7
                        ip.halfPortWidth = ip.datatypeObject['width']/2
                        ip.halfPortHeight = ip.datatypeObject['height']/2
                        ip.createIcon(pcx=14+12*i, pcy=pcy)
                        i += 1
                except Exception, e:
                    warnings.warn("echec input %s" % n2.name)
                    import traceback
                    print traceback.print_stack()
                    print e
            j = 0
            bb = canvas.bbox(n1.id)
            pcy = n1.posy + bb[3] - bb[1] + 2
            for lPortDesc in n2.outputPortsDescr:
                lKw = lPortDesc.copy()
                lPortName = lKw['name']
                lKw.pop('name')
                try:
                    op = apply( OutputPort, (lPortName, n2), lKw)
                    if op.datatypeObject['shape'] == 'diamond':
                        n2.scaleSum = .6
                    else:
                        n2.scaleSum = .7
                    op.halfPortWidth = op.datatypeObject['width']/ 2
                    op.halfPortHeight = op.datatypeObject['height']/2
                    op.createIcon(pcx=14+12*j, pcy=pcy)
                    j += 1
                except Exception, e:
                    warnings.warn("echec ouput %s" % n2.name)
                    import traceback
                    print traceback.print_stack()
                    print e

    		# resize node length
            neededWidth = 4 + 12 * max(i, j)
            neededWidth = n1.getWidthForLabel(neededWidth)
            bb = canvas.bbox(n1.innerBox)
            w = bb[2]-bb[0]
            n1.resizeIcon(dx=neededWidth-w)
            if len(n2.outputPortsDescr) <= 0:
               posy -= 2 
            del n2
    		# here ends the additions to draw the ports ********************

        node.dummyNode = n1
        node.bbox = sc_canvas.bbox(n1.iconTag)
        bb = sc_canvas.bbox(n1.id)
        w = bb[2]-bb[0]
        maxx = max(maxx, w)
        posy = posy + (bb[3]-bb[1]) + 7
        nodes[n1.id] = (n1, node)
        self.balloons.tagbind(sc_canvas, n1.iconTag,
                              node.nodeClass.__doc__)
        return maxx, posy, nodes


    def deleteNodeFromCategoryFrame(self, cat, nodeClass, nodeName=None):
        """Delete a node from a category frame. We need the name of the
        category and the class of the node"""
        # Delete a proxy node from a category frame
        if cat not in self.libraryDescr.keys():
            return

        # find proxy node
        proxy = None # the proxy node to be deleted
        sc_canvas = self.libraryDescr[cat]['canvas']
        i = 0
        for prx in self.libraryDescr[cat]['nodes']:
            if prx.nodeClass == nodeClass:
                if (nodeName is None) or (nodeName == prx.name):
                    proxy = prx
                    break
            i = i + 1

        if proxy is None:
            return
            
        # unbind proxy node balloon
        self.balloons.tagunbind(sc_canvas, proxy.dummyNode.iconTag)
        # delete proxy icon
        proxy.dummyNode.deleteSmallIcon(sc_canvas, proxy)
        # delete proxy node in dict
        del self.libraryDescr[cat]['nodes'][i]
        # now rebuild the list to remove the gap
        self.rebuildNodesInCategoryFrame(cat)
        #remove nodeName from nodeNames list
        self.nodeNames.remove(nodeName)


    def rebuildNodesInCategoryFrame(self, cat):
        # delete and rebuild the nodes in a category frame
                
        if cat not in self.libraryDescr.keys():
            return

        sc_canvas = self.libraryDescr[cat]['canvas']

        # first, find out what is the current font of a proxy node
        font = self.ed.font['LibNodes']
        # now rebuild icons
        maxx = 0
        posy = 0
        nodes = {}
        self.libraryDescr[cat]['lastPosy'] = 15 # FIXME! Half node height
        for node in self.libraryDescr[cat]['nodes']:
            if node.dummyNode is not None:
                node.dummyNode.deleteSmallIcon(sc_canvas, node)
            maxx, posy, nodes = self.addNodeToCategoryFrame(
                    cat, node, nodes=nodes, font=font, maxx=maxx, vpe=self.ed)
            self.libraryDescr[cat]['lastPosy'] = posy

        # register mouse click for drag&drop
        self.ed.idToNodes[sc_canvas] = nodes
        
        # update scrolled canvas
        canvas = sc_canvas.component('canvas')
        canvas.configure(width=150, height=150,
                         scrollregion=tuple((0,0,maxx,posy)))


    def getHeader(self):
        """ returns list of strings describing library header"""
        import os, time
        user = os.environ.get('USER', 'Unknown')
        lines = [
"########################################################################\n",
"#\n",
"# Date: %s     Author: %s\n"%(time.ctime(), user),
"#\n",
"#\n",
"# a user-defined Vision node library\n",
"#\n",
"#########################################################################\n",
"\n",
"from NetworkEditor.items import NetworkNode\n",
"from NetworkEditor.datatypes import AnyArrayType\n",
"from Vision import UserLibBuild\n"
"\n",
"from Vision.VPE import NodeLibrary\n",
"\n",
          ]  
        return lines

    
    def getSourceCode(self, libObjName):
        """returns a list of strings containing the source code of the library"""
        lines = []
        lines.extend(self.getHeader())

        # create library object
        lines.append("%s = NodeLibrary('%s', '%s')\n\n"%(libObjName, self.name,
                                                         self.color))

        # save source code of all nodes
        for catName, cat in self.libraryDescr.items():
            for node in cat['nodes']:
                # create an instance of the node so we ask it for source code
                kw = node.kw
                args = node.args
                className = self.name+'_'+node.nodeClass.__name__
                n = apply( node.nodeClass, args, kw )
                n.modified = {'sourceCode':1, 'inputPorts':1, 'outputPorts':1,
                             'widgets':1 }
                src = n.getNodeSourceCode(className)
                lines.extend( n.getNodeSourceCode(className) )
                lines.append( "\n%s.addNode( %s, '%s', '%s')\n\n\n"%(
                    libObjName, className, n.name, catName) )
        return lines
    

    def saveToFile(self, filename, libObjName):
        # write library to file filename. libObjName is the name of the
        # library object to be created in this file.
        
        f = open(filename, 'w')
        if f:
            lines = self.getSourceCode(libObjName)
            map( f.write, lines)
            f.close()
            
        
    def readFromFile(self, filename):
        pass


class NodeProxy:
    """class used to describe a NetworkNode object in a library"""
    
    def __init__(self, nodeClass, name, args=None, kw=None,
                 functionSourceCode=None):

        self.nodeClass = nodeClass  # class of the node that will be created
                                    # for this library entry
        self.name = name

        # if args or kw is None we have to create empty list or dict
        # explicitly here. args=() or dict={} in the signature results
        # in all instances sharing the same list or dict
        if args is None:
            self.args = ()
        else:
            self.args = args            # arguments for the constructor
        if kw is None:
            self.kw = {}
        else:
            self.kw = kw

        self.kw['name'] = name
        self.bbox = None            # node Icons's bounding box
        self.dummyNode = None       # dummy node used to build icon in lib
        self.functionSourceCode = functionSourceCode
    
    
        
