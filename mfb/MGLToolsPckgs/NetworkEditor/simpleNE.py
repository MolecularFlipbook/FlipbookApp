#########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner, Daniel Stoffler
#
#    sanner@scripps.edu
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler and TSRI
#
# revision: Guillaume Vareille
#  
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/simpleNE.py,v 1.233.2.3 2012/02/27 19:46:55 sanner Exp $
#
# $Id: simpleNE.py,v 1.233.2.3 2012/02/27 19:46:55 sanner Exp $
#



"""
This modules implements the classes NetworkBuilder.
An instance of a SimpleNetworkBuilder provides a Canvas to which NetworkNode
and NetworkConnections can be added to build networks.
The network maintains a list of selected nodes.
Node can have multiple ports. Connections know the 2 nodes they connect and
the port numbers on which they are connected. in a connection, node1 is always
the node from which the connection was initiated and is considered to be the
parent of node2.
Nodes maintain a dictionary of (connections:nodes) paires indicating which node
is conencted by which connection.

Every node has a computeFunction which can be run in a separate thread.
To run a node call the node's schedule method. This will place this node in
a thread safe queue. If the queue is started (see startQueueHandler,
stopQueueHandler), the node's compute function will be called as soon as
all parent nodes are not running.
For data flow, it is the node's compute function task to schedule it's
children node.

node addition and node connection, node selection and deselection,
connection selection and deselection

This file provides an implementation of 1 port networkNodes and multi-port
NetworkNodes as well as an implementation of NetworkConnection.

here is an example of how to use this:

    # instanciate an editor
    editor = NetworkBuilder('My Network Builder')

    # instanciate a node
    node1 = NetworkNode(name='node1')

    # add this node to the editor
    editor.addNode(node1, 100, 100)

    # nodes have several methods tha can be used to alter its representation
    node1.rename('operator1')
    node1.highlight()
    node1.unhighlight()
    
    # create a second node
    node2 = NetworkNode(name='node2')
    editor.addNode(node2, 200, 200)

    # connect these 2 nodes
    conn1 = editor.connectNodes(node1, node2)

    # connections are objects too that can be altered
    conn1.highlight()
    conn1.unhighlight()

    # create a 3rd node and connect it using angular lines
    node3 = NetworkNode(name='node3')
    editor.addNode(node3, 300, 100)
    conn2 = editor.connectNodes(node3, node2, mode='angles')

    # create a 4th node and connect it with a spline
    node4 = NetworkNode(name='node4')
    editor.addNode(node4, 350, 270)
    conn3 = editor.connectNodes(node2, node4, mode='angles', smooth=1)

    # nodes can be moved
    node1.move(200, 100)
    
    # connections can update their representation to reflect node motion
    conn1.updatePosition()

    # nodes can be selected
    editor.selectNodes([node1, node2, node3])
    editor.deselectNodes([node1, node4])
    editor.clearSelection()

    # a sub graph can be moved
    editor.moveSubGraph(editor.selectedNodes, 10, 20)

    # nodes and connections can be deleted
    editor.deleteNodes([node2])

    node5 = NetworkNode(name='node5')
    editor.addNode(node5, 100, 200)
    conn4 = editor.connectNodes(node1, node5, mode='angles')
    editor.deleteConnections([conn4])

    # try nodes of type 2

    n1 = NetworkNode2('test1')
    ed.addNode(n1, 100, 350)
    n1.addOutputPort()

    from NetworkEditor.simpleNE import NetworkNode2
    n2 = NetworkNode2('test2')
    ed.addNode(n2, 300, 350)
    n2.addInputPort()

    from NetworkEditor.simpleNE import NetworkConnection
    ed.connectNodes(n1, n2, 2, 1)

    ed.connectNodes(node5, n2, 0, 2)
    ed.selectNodes([n2])
    ed.moveSubGraph(ed.selectedNodes, 10, 20)

"""

## TODO/bugs
##
#- GUI to expose options (default Connection mode, default lineOptions)
#- GUI to expose bindings in InteractiveNetworkBuilder

#DONE
#- Create MacroNode, expand/shrink MacroNode
#- copy sub-graph
#- Multi-port nodes: resize node when adding ports
#- save/load network
#- gain access to idle and idlelib as a package

#FIXME:
# undo is broken
# hyperbolic scaling is broken (this is not really important, but anyways)


import sys, os
import warnings
import Tkinter, Pmw, tkFileDialog
import traceback
import string
import re
import thread
import weakref
import user

from mglutil.util.idleUtil import getShell
from mglutil.events import EventHandler

from tkSimpleDialog import askstring
from tkMessageBox import askokcancel, showwarning
from SimpleDialog import SimpleDialog

from mglutil.util.callback import CallBackFunction
from mglutil.util.callback import CallbackManager
from mglutil.util.packageFilePath import findResourceFile
from mglutil.util.misc import ensureFontCase

from NetworkEditor.items import NetworkNode, NetworkConnection, NetworkNodeBase
from NetworkEditor.datatypes import TypeManager
from NetworkEditor.widgets import widgetsTable, PortWidget
from NetworkEditor.net import Network
from NetworkEditor.customizedWidgets import mglNoteBook
from NetworkEditor.macros import MacroNetwork
from NetworkEditor.itemBase import UserPanel
from mglutil.util.recentFiles import RecentFiles
from mglutil.util.packageFilePath import getResourceFolder, getResourceFolderWithVersion
from mglutil.util.misc import suppressMultipleQuotes

from Vision.gantt import Gantt

class NoGuiNetworkBuilder(EventHandler):
    """Class used to replace the VPE when running without a GUI.
This class serves a place hold4er for the data type manager and also
for multiple networks such as the ones created by macros.
"""
    def __init__(self):
        EventHandler.__init__(self)
        self.hasGUI = False
        self.networks = {} # dictionary of networks (name:networkObject)

        self.uniqNetworkNumber = 0

        self.typeManager = TypeManager()


    def addNetwork(self, network):
        """None <- addNetwork(network)
adds a Network object to the editor
"""
##          while network.name in self.networks.keys():
##              name = askstring("Network name already used", "Network Name",
##                               initialvalue=network.name)
##              network.rename(name)

        # rename network if it already exists
        while network.name in self.networks.keys():
            if isinstance(network, MacroNetwork):
                macnode = network.macroNode
                macnode.rename(macnode.name+str(self.uniqNetworkNumber))
            
            network.name = network.name+str(self.uniqNetworkNumber)

        self.uniqNetworkNumber = self.uniqNetworkNumber + 1
        
        self.networks[network.name] = network
        network.vEditor = weakref.ref(self)


    def loadNetworkNOGUI(self, name, filename):
        import os
        if not os.path.exists(filename):
            warnings.warn("ERROR: File not found! %s"%filename)
            return

        from NetworkEditor.net import Network
        masterNet = Network(name)
        self.addNetwork(masterNet)
        execfile(filename)
        return masterNet



class NetworkBuilder(Tkinter.Frame, NoGuiNetworkBuilder):
    """
  This class implements a simple network builder that provides a Canvas
to which NetworkNodes can be added. These nodes can be connected by
NetworkConnections.
  The builder stored Nodes and connections in 2 dictionaries where the key is a
unique tag (associated with the geometry in the Canvas) and the value is the
instance of either the node or the connection.
  The Builder also maintains a list of currently selected nodes.
"""

    def __init__(self, name='NoName', master=None, font=None, withShell=1, **kw):
        """instance <- NetworkBuilder(name='NoName', master=None, font=None,
                 withShell=1, **kw)
        master can be a Frame in which the editor has to be packed
        withShell=0 will prevent the creation of an Idle shell (since the
                    default shell is used)
        kw can contain the following named arguments:
        visibleWidth, visibleHeight,
        totalWidth, totalHeight
        any legal keyword for a Canvas
        """
        NoGuiNetworkBuilder.__init__(self)
        self.hasGUI = True

        self.resourceFolder = getResourceFolder()
        self.resourceFolderWithVersion = getResourceFolderWithVersion()

        if kw.has_key('visibleWidth'):   # size of scrollable Canvas
            self.visibleWidth = kw['visibleWidth']
            del kw['visibleWidth']
        else:
            self.visibleWidth = 400

        if kw.has_key('visibleHeight'):  # size of scrollable Canvas
            self.visibleHeight = kw['visibleHeight']
            del kw['visibleHeight']
        else:
            self.visibleHeight= 400     

        if kw.has_key('totalWidth'):     # Total size of Canvas
            self.totalWidth = kw['totalWidth']
            del kw['totalWidth']
        else:
            self.totalWidth = 4000

        if kw.has_key('totalHeight'):    # Total size of Canvas
            self.totalHeight = kw['totalHeight']
            del kw['totalHeight']
        else:
            self.totalHeight = 4000     

        Tkinter.Frame.__init__(self, master)

        # FIXME we should catch whatever exception is thrown if self has no
        # option_readfile method and say something meaningful
        # maybe the name and location of the file should be setable in _vprc
        try:
            if os.path.exists('./Tkinter.defaults'):
                self.option_readfile('./Tkinter.defaults')
        except:
            pass
        
        self.font = {} # dict holding font configuration for various GUI
                       # elements. Now set the defaults
        self.font['Menus']      = (ensureFontCase('helvetica'), 8, 'bold')
        self.font['LibTabs']    = (ensureFontCase('helvetica'), 8, 'bold')
        self.font['Categories'] = (ensureFontCase('helvetica'), 8, 'bold')
        self.font['LibNodes']   = (ensureFontCase('helvetica'), 8, 'normal')
        self.font['NetTabs']    = (ensureFontCase('helvetica'), 8, 'bold')
        self.font['Nodes']      = (ensureFontCase('helvetica'), 8, 'normal')
        self.font['Root']       = (ensureFontCase('helvetica'), 8, 'normal')

        if font is not None: # override default if user specified
            # kw font can be either ['FONT] or ['FONT', SIZE] or
            # ['FONT', SIZE, 'STYLE']
            ft = font[0]
            sz = 8
            sty = 'normal'

            if len(font) == 2:
                sz = font[1]
            elif len(font) == 3:
                sz = font[1]
                sty = font[2]

            fontList = (ft, sz, sty)
            for k in self.font.keys():
                self.font[k] = fontList

        # define self.root as the toplevel in which the editor is
        root = self.master
        while not isinstance(root, Tkinter.Toplevel) and not isinstance(root, Tkinter.Tk):
            root = root.master
        self.root = root

        if self.root.title() == 'Vision':
            self.root.option_add('*font',self.font['Root'])

        self.withShell = withShell # set to one is an IDLE shell is created
        
        #self.master.option_readfile('NetworkEditor/Tkinter.defaults')

        self.name = name       # EditorName

        self.eventHandler = {} # stores callback managers for network events
        self.createCallbackManager('addNetwork')
        self.createCallbackManager('deleteNetwork')

        handle = self.eventHandler['addNetwork']
        handle.AddCallback(self.handleAddNetwork)
        handle = self.eventHandler['deleteNetwork']
        handle.AddCallback(self.handleDeleteNetwork)
           
        threads = 0 # default is 0: do not run multi-threaded scheduling
        self.withThreads = threads
        self.withThreadsTk = Tkinter.IntVar()
        self.withThreadsTk.set(threads)

        self.mainThread = thread.get_ident() #used for idle shell

        self.colorNodeByLibrary = 0
        self.colorNodeByLibraryTk = Tkinter.IntVar()
        self.colorNodeByLibraryTk.set(self.colorNodeByLibrary)

        self.flashNodesWhenRun = 1
        self.flashNodesWhenRunTk = Tkinter.IntVar()
        self.flashNodesWhenRunTk.set(self.flashNodesWhenRun)
        
        self.splineConnections = 0
        self.splineConnectionsTk = Tkinter.IntVar()
        self.splineConnectionsTk.set(self.splineConnections)
                             
        ## USED TO FLASH NETWORK ONCE ONLY
##          self.flashNetworkWhenRun = 1
##          self.flashNetworkWhenRunTk = Tkinter.IntVar()
##          self.flashNetworkWhenRunTk.set(self.flashNetworkWhenRun)

        self.verbose = 0 # when set to 1 to see prints in stdout
        self.verboseTk = Tkinter.IntVar()
        self.verboseTk.set(self.verbose)
        
        self.glyph = 0 # when set to 1 displays glyph widgets 
        self.glyphTk = Tkinter.IntVar()
        self.glyphTk.set(self.glyph)

        self.balloons = Pmw.Balloon(master, yoffset=0)

        self.typeManager = TypeManager()
        self.undoStack = []
        self.currentNetwork = None
        
	Tkinter.Pack.config(self, expand=1, fill='both')

        # register callback to keep track of window width
        # so that we can resize the module libraries
        self.bind('<Configure>', self.resize_cb, '+')

        self.createMenus(self)
        self.setFont("Menus", self.font['Menus'])
        #self.menuButtons['Edit'].menu.invoke("flash Nodes When Run")
        #self.menuButtons['Edit'].menu.invoke("restore Widget Value")

        self.private_pasteBuffer = None # textual description of sub-network
                                        # in copy buffer

        self._tmpListOfSavedNodes = {}   # used for saving networks or source

        self.networkAreaF = Pmw.ScrolledFrame(self,
             borderframe=1, horizscrollbar_width=7, vscrollmode='none',
             frame_relief='flat',
             frame_borderwidth=0, horizflex='fixed',
             vertflex='elastic',
             frame_width=self.visibleWidth,
             frame_height=self.visibleHeight)
        self.networkAreaF.pack(expand=1, fill='both')

        self.networkArea = mglNoteBook(self.networkAreaF.interior(),
                                        raisecommand=self.selectNetwork)
        self.networkArea.pack(fill='both', expand=1, padx=1, pady=1)
 
        # create the Python shell
        if self.withShell:
            self.pyshell = getShell(self.mainThread, rootTk = self.root,
                                    enable_shell=True, enable_edit=False,
                                    debug=False)
            self.pyshell.menubar.children['file'].delete('Close','Exit')
            self.pyshell.menubar.children['file'].add_command(
                label='Clear Ouput', command=self.clearPyShell )
            # hide the Python shell
            self.pyshell.top.withdraw()
            self.pyshell.begin()
            ### ???? what is this ?
            Tkinter._default_root = self.root
            self.pyshell.top.protocol('WM_DELETE_WINDOW',
                                      self.togglePythonShell)

        # add a default network
	net = Network('Network 0')
        self.addNetwork( net )
        # make it the current one
        self.setNetwork( net )
	#net.buildIcons()
        
        self.nbPaste = 1
        self.resizeNetworkArea()

        # create GUI for GANTT plotting of execution time
        self.GANTTmaster = Tkinter.Toplevel(master)
        self.GANTT = Gantt( [ ], root=self.GANTTmaster )
        self.GANTTmaster.protocol('WM_DELETE_WINDOW', self.hideGantt)
        self.hideGantt()

    def panelFromName(self, name):
        return self.currentNetwork.userPanels.get(name, None)


    def createUserPanel_cb(self, event=None):
        defaultName = 'Panel_%d'%len(self.currentNetwork.userPanels.keys())
        name = askstring('Panel Name', "Panel Name", initialvalue=defaultName)
        while name in self.currentNetwork.userPanels.keys():
            name = askstring('Panel Name alread used, New value', "Panel Name",
                             initialvalue=defaultName)
        if name is None or len(name) == 0:
            return
        self.currentNetwork.createUserPanel(name)


    def createUserPanel(self, name, **kw):
        apply(self.currentNetwork.createUserPanel, (name,), kw)


    def deleteUserPanel_cb(self):

        def internal_cb(name):
            self.funcCB = CallBackFunction(self.currentNetwork.deleteUserPanel, name)

        def external_cb():
            master.destroy()
            self.funcCB()

        if len(self.currentNetwork.userPanels) > 0:
            master = Tkinter.Toplevel()
            master.title('Panel deletion')

            name = self.currentNetwork.userPanels.keys()[0]
            self.funcCB = CallBackFunction(self.currentNetwork.deleteUserPanel, name)

            lComboBoxPanels = Pmw.ComboBox(
                       master,
                       label_text='Choose the panel to delete',
                       labelpos='n',
                       entryfield_value=name,
                       scrolledlist_items=self.currentNetwork.userPanels.keys(),
                       selectioncommand=internal_cb
                      )
            lComboBoxPanels.pack(side='top', fill='x')

            buttonsFrame = Tkinter.Frame(master)
            buttonOk = Tkinter.Button( buttonsFrame,
                                       text='OK',
                                       command=external_cb)
            buttonOk.pack(side='left', expand=1, fill='x')
            buttonCancel = Tkinter.Button( buttonsFrame, text='Cancel', command=master.destroy)
            buttonCancel.pack(side='left', expand=1, fill='x')
            buttonsFrame.pack(side='top', fill='x')


    def getNetworkByName(self, name):
        """networkList <- getNetworkByName(self, name)
Return all the network who's name match the name regular expression
"""
        nets = []
        import re
        reg = re.compile(name)
        for netName, net in self.networks.items():
            if reg.match(netName):
                nets.append(net)
        return nets


    def getNodeByName(self, name):
        """nodeList <- getNodeByName(self, name)
Return all the nodes from the current network who's name match the name
regular expression
"""
        return self.currentNetwork.getNodeByName(name)
    

    def resize_cb(self, event=None):
        if self.visibleWidth != event.width:
            curwidth = self.visibleWidth
            self.visibleWidth = event.width
            # resize networkArea only if window got larger
            if curwidth < event.width:
                self.resizeNetworkArea()


    def resizeNetworkArea(self):
        # compute how much width the individual panes get
        if self.winfo_width() == 1: # first time of instanciation
            self.update_idletasks()
        self.networkArea.configure(hull_width=self.visibleWidth-6,
                                   hull_height=self.visibleHeight)
        

    def clearPyShell(self, event=None):
        if self.withShell:
            self.pyshell.text.delete("1.0", "end-1c")


    def createCallbackManager(self, event):
        assert not self.eventHandler.has_key(event)
        self.eventHandler[event] = CallbackManager()
        

    def addCallbackManager(self, event, func, doc, **kw):
        assert self.eventHandler.has_key(event)
        assert callable(func)
        
        self.eventHandler[event].AddCallback(func)


    def showGUI(self):
        self.root.deiconify()


    def hideGUI(self):
        self.root.withdraw()
        

    def toggleGuiVisibility(self):
        if self.root.winfo_ismapped():
            self.hideGUI()
        else:
            self.showGUI()


    def setFont(self, *args):
        msg = """Usage: self.setFont(<itemname>, <fontconfig>)
For Example: self.setFont('Menus', (ensureFontCase('helvetica'), 9, 'bold')
Legal itemnames: 'All'
                 'Menus'
                 'NetTabs'
                 'Nodes'
                 'Root'"""


        if args is None or args == () or len(args) != 2:
            return

        else:
            tag = args[0]
            font = args[1]
            assert len(font) == 3
            font = tuple(font)

        if tag == 'Menus' or tag == 'All':
            self.font['Menus'] = font
            for menu in self.menuButtons.keys():
                # set menu button font
                self.menuButtons[menu].configure(font=font)
                # set cascading menu font
                self.menuButtons[menu].menu.configure(font=font)

        if tag == 'Nodes' or tag == 'All':
            self.font['Nodes'] = font
            # set balloon for ports:
            self.balloons.component('label').configure(font=font)
            for net in self.networks.values():
                for node in net.nodes:
                    node.iconMaster.itemconfigure(node.textId, font=font)
                    
                # call refresh to rebuild nodes
                self.refreshNet_cb(net)

        if tag == 'NetTabs' or tag == 'All':
            self.font['NetTabs'] = font
            for tab in self.networkArea.pagenames():
                netTab = self.networkArea.tab(tab)
                netTab.configure(font=font)
                # get info to resize the tab
                width = netTab.winfo_reqwidth()
                height = netTab.winfo_reqheight()
                self.networkArea._pageAttrs[tab]['tabreqwidth'] = width
                self.networkArea._pageAttrs[tab]['tabreqheight'] = height
            # resize all tabs
            self.networkArea._pending['tabs'] = 1
            self.networkArea._layout()

        if tag == 'Root' or tag == 'All':
            self.font['Root'] = font
            self.root.option_add('*font',font)


    def interactiveExit_cb(self, event=None):
        msg = askokcancel("Quit","Are you sure you want to quit?", master=self.master)
        if msg:
            self.exit_cb(event)


    def exit_cb(self, event=None):
        # Note: do not name this method 'exit', else Tkinter will call it
        # too and the you get red ink upon exiting!
        from NetworkEditor.macros import MacroNetwork
        for net in self.networks.values():
            if not isinstance(net, MacroNetwork):
                self.deleteNetwork(net)

        lMaster = self.root
        lMaster.quit()
        lMaster.destroy()
        while hasattr(lMaster, 'master') and lMaster.master is not None:
            lMaster = lMaster.master
            lMaster.quit()
            lMaster.destroy()

        if self.withShell:
            self.pyshell.close()
            sys.exit(0)
        else:
            import Vision
            if Vision.__dict__.has_key('ed'):
                Vision.__dict__.pop('ed')
            sys.stdin.__exit__() # hack to really exit code.interact


    def handleSelectionChangeMenus(self):
        """This is called by callback manager on event select or deselect
        nodes and turns on/off menu entries and menu buttons."""
        
        net = self.currentNetwork
        menu = self.menuButtons['Edit'].menu

        if len(net.selectedNodes):
            menu.entryconfig("Cut", state=Tkinter.NORMAL)
            menu.entryconfig("Copy", state=Tkinter.NORMAL)
            #menu.entryconfig("Delete", state=Tkinter.NORMAL)
        else:
            menu.entryconfig("Cut", state=Tkinter.DISABLED)
            menu.entryconfig("Copy", state=Tkinter.DISABLED)
            #menu.entryconfig("Delete", state=Tkinter.DISABLED)

        if self.private_pasteBuffer:
            menu.entryconfig("Paste", state=Tkinter.NORMAL)
        else:
            menu.entryconfig("Paste", state=Tkinter.DISABLED)


    def handleAddNetwork(self):
        """This is called by callback manager on the event add network and
        turns on menu entries."""

        menuF = self.menuButtons['File'].menu
        menuE = self.menuButtons['Edit'].menu
        menuN = self.menuButtons['Networks'].menu
       
        menuF.entryconfig("New...", state=Tkinter.NORMAL)
        menuF.entryconfig("Open...", state=Tkinter.NORMAL)
        menuF.entryconfig("Merge...", state=Tkinter.NORMAL)
        menuF.entryconfig("Close...", state=Tkinter.NORMAL)
        menuF.entryconfig("Save...", state=Tkinter.NORMAL)
        menuF.entryconfig("Print", state=Tkinter.NORMAL)
        menuF.entryconfig("Quit", state=Tkinter.NORMAL)

        menuE.entryconfig("Select all", state=Tkinter.NORMAL)
        menuE.entryconfig("Create macro", state=Tkinter.NORMAL)
        menuE.entryconfig("Create user panel", state=Tkinter.NORMAL)
        menuE.entryconfig("Delete user panel", state=Tkinter.NORMAL)

        menuN.entryconfig("Rename...", state=Tkinter.NORMAL)
        menuN.entryconfig("Close...", state=Tkinter.NORMAL)
        menuN.entryconfig("Soft run", state=Tkinter.NORMAL)
        menuN.entryconfig("Hard run", state=Tkinter.NORMAL)
        menuN.entryconfig("Refresh", state=Tkinter.NORMAL)
        menuN.entryconfig("Reset cache", state=Tkinter.NORMAL)
        

    def handleDeleteNetwork(self, **kw):
        """This is called by callback manager on the event delete network and
        turns on menu buttons."""
        menuF = self.menuButtons['File'].menu
        menuE = self.menuButtons['Edit'].menu
        menuN = self.menuButtons['Networks'].menu

        if self.currentNetwork is None:
            menuF.entryconfig("New...", state=Tkinter.NORMAL)
            menuF.entryconfig("Open...", state=Tkinter.NORMAL)
            menuF.entryconfig("Merge...", state=Tkinter.DISABLED)
            menuF.entryconfig("Close...", state=Tkinter.DISABLED)
            menuF.entryconfig("Save...", state=Tkinter.DISABLED)
            menuF.entryconfig("Print", state=Tkinter.DISABLED)
            menuF.entryconfig("Quit", state=Tkinter.NORMAL)

            menuE.entryconfig("Select all", state=Tkinter.DISABLED)
            menuE.entryconfig("Create macro", state=Tkinter.DISABLED)
            menuE.entryconfig("Create user panel", state=Tkinter.DISABLED)
            menuE.entryconfig("Delete user panel", state=Tkinter.DISABLED)

            menuN.entryconfig("Rename...", state=Tkinter.DISABLED)
            menuN.entryconfig("Soft run", state=Tkinter.DISABLED)
            menuN.entryconfig("Hard run", state=Tkinter.DISABLED)
            menuN.entryconfig("Refresh", state=Tkinter.DISABLED)
            menuN.entryconfig("Reset cache", state=Tkinter.DISABLED)


    def copyNetwork_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'c':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)

        # save the source code for the sub-network corresponding to the
        # current selection
        net = self.currentNetwork
        if len(net.selectedNodes)==0:
            self.private_pasteBuffer = None
            # disable paste
            net.eventHandler['onSelectionChange'].CallCallbacks()
            return

        curNet = self.currentNetwork
        # prevent cut/copy of macroinput and macrooutput node
        # by deselecting them 
        from macros import MacroNetwork
        if isinstance(curNet, MacroNetwork):
            curNet.deselectNodes([curNet.ipNode, curNet.opNode])

        # pass ignoreOriginal=True so that we can copy nodes in macro networks
        # that came from a node library (where all nodes are marked original)
        self.private_pasteBuffer = curNet.getNetworkCreationSourceCode(
            selectedOnly=1, withRun=False, ignoreOriginal=True)
        self.private_selectionbb = self.currentNetwork.canvas.bbox('selected')
        # enable paste
        curNet.eventHandler['onSelectionChange'].CallCallbacks()
        self.nbPaste = 1

            
    def cutNetwork_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'x':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)

        # save the source code for the sub-network corresponding to the
        # current selection
        net = self.currentNetwork
        self.copyNetwork_cb(event)
        # Note: if Macro Input/Output nodes were in the selection, the
        # copyNetwork_cb will automatically deselect them (see above)
        net.deleteNodes(net.selectedNodes) 
        # disable CUT and COPY
        self.currentNetwork.eventHandler['onSelectionChange'].CallCallbacks()


    def delete(self, event=None):
        self.currentNetwork.deleteNodes(self.currentNetwork.selectedNodes[:])

        
    def saveNetwork(self, filename, temporary=False):

        try:
            if temporary is False:
                self.currentNetwork.filename = os.path.abspath(filename)

            self.currentNetwork.saveToFile(filename)
        
            #if len(self.currentNetwork.userPanels) > 0:
            #    os.chmod(filename, 0777)
            os.chmod(filename, 0777)
            
            if temporary is False:
                self.currentNetwork._modified = False

        except Exception, e:
            warnings.warn('save Network failed ! %s'%e)


    def saveNetwork_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 's':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)

        # save network
        from macros import MacroNetwork
        if isinstance(self.currentNetwork, MacroNetwork):
            ans = showwarning('Warning', 'This network is inside a macro!')
            return
        name = string.replace(self.currentNetwork.name," ", "")

        if self.currentNetwork.filename is not None:
            lNetworkDir = os.path.dirname(self.currentNetwork.filename)
        else:
            from Vision import networkDefaultDirectory
            lNetworkDir = networkDefaultDirectory

        if self.libraries.has_key('Pmv'):
            file = tkFileDialog.asksaveasfilename(parent = self,
                initialdir = lNetworkDir, 
                filetypes=[('network', '*_pmvnet.py *_net.py'),
                           ('all', '*')],
                title='Save Network',
                initialfile=name+"_pmvnet.py")
        else:
            file = tkFileDialog.asksaveasfilename(parent = self,
                initialdir = lNetworkDir,
                filetypes=[('network', '*_pmvnet.py *_net.py'),
                           ('all', '*')],
                title='Save Network',
                initialfile=name+"_net.py")
        if file:
            self.saveNetwork(file)
            # and also rename the network tab
            if file.endswith('_pmvnet.py'):
                networkName = os.path.basename(file)[:-10]
            else:
                networkName = os.path.basename(file)[:-7]
            self.currentNetwork.rename(networkName)
            self.recentFiles.add(file, 'loadNetwork')

    def showGantt(self):
        # show GANTT diagramm
        self.GANTTmaster.deiconify()
        
            
    def hideGantt(self):
        # hide GANTT diagramm
        self.GANTTmaster.withdraw()

    def toggleGantt_cb(self, event=None):
        if self.GANTTmaster.wm_state()=='withdrawn':
            self.showGantt()
        else:
            self.hideGantt()

    def pasteNetwork_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'v':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)

        if not self.private_pasteBuffer:
            return

        if self.currentNetwork is None:
            # this can happen when all networks were deleted. Yet, I prefer to
            # have the Paste Button Icon active to indicate there is still
            # stuff in the paste_buffer that can be pasted if a new network
            # is created.
            return

        net = self.currentNetwork
        net.clearSelection()
        lastNodeInd = len(net.nodes)
        codeSrc = reduce(lambda x, y: x+y, self.private_pasteBuffer)
        obj = compile(codeSrc, '<string>', 'exec')
        exec(obj, {'self':net, 'masterNet':net} )

        net.unfreeze()
        net.needsResetNodeCache = 1
        net.selectNodes(net.nodes[lastNodeInd:])

        # now shift pasted nodes
        canvas = self.currentNetwork.canvas
        bb = self.private_selectionbb
        dx = bb[2]-bb[0]
        dy = bb[3]-bb[1]
        if dx < dy:
            dx = dx*self.nbPaste
            dy = 10*self.nbPaste
            canvas.move('selected', dx, dy )
        else:
            dx = 10*self.nbPaste
            dy = dy*self.nbPaste
            canvas.move('selected', dx, dy)

        self.nbPaste = self.nbPaste + 1

        for n in self.currentNetwork.selectedNodes:
            n.posx = n.posx+dx
            n.posy = n.posy+dy


    def loadNetwork_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'o':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)

        if self.currentNetwork is not None \
          and self.currentNetwork.filename is not None:
            lNetworkDir = os.path.dirname(self.currentNetwork.filename)
        else:
            from Vision import networkDefaultDirectory
            lNetworkDir = networkDefaultDirectory

        # load network
        file = tkFileDialog.askopenfilename(parent = self,
            initialdir = lNetworkDir,
            title='Load Network',
            filetypes=[('any network', '*_pmvnet.py *_net.py'),
                       ('vision network', '*_net.py'), 
                       ('pmv network', '*_pmvnet.py'),
                       ('all', '*')] )

        if file:
            self.loadNetwork(file, None)
            self.recentFiles.add(file, 'loadNetwork')


    def mergeNetwork_cb(self, event=None):

        if self.currentNetwork is not None \
          and self.currentNetwork.filename is not None:
            lNetworkDir = os.path.dirname(self.currentNetwork.filename)
        else:
            from Vision import networkDefaultDirectory
            lNetworkDir = networkDefaultDirectory

        file = tkFileDialog.askopenfilename(parent = self,
                initialdir = lNetworkDir, 
                filetypes=[('network', '*_pmvnet.py *_net.py'), 
                           ('all', '*')], 
                title='Merge Network')

        if file:
            self.loadNetwork(file, self.currentNetwork)

    
    def loadNetwork(self, filename, network=None, name=None, ins=None,
                    takefocus=True):
        # executes the file containing the network description
        # masterNet is the parent network

        # does file exist? If not, abort
        if not os.path.exists(filename):
            warnings.warn("ERROR: File not found! %s"%filename)
            return

        if takefocus is False and self.currentNetwork is not None:
            lCurrentNetwork = self.currentNetwork
        else:
            lCurrentNetwork = None

        # if not parent net is specified, create a new notebook page
        if network is None:
            # humm seems like i could simply rename the tab here
            # rather than deleting
            if name is None:
                if filename.endswith('_pmvnet.py'):
                    name = os.path.splitext(os.path.basename(filename))[0][:-7]
                else:
                    name = os.path.splitext(os.path.basename(filename))[0][:-4]

            # replace all underscore by minus because Pmw tabs names 
            # cannot have underscores in them
            name = name.replace('_', '-')

            if len(self.networks)==1 and len(self.currentNetwork.nodes)==0:
                self.deleteNetwork(self.currentNetwork)

            network = Network(name, origin='file')
            network.filename = os.path.abspath(filename)
            network.freeze()
            network.needsResetNodeCache = 0
            self.addNetwork(network)
            network.buildIcons() # we need to show the net to create the canvas
                             # BEFORE making it current, else widgets in nodes
                             # are not placed properly
            self.setNetwork(network)
            lastNodeInd = -1

            network.unfreeze()
            
        else: # we are merging into an existing network
            network.clearSelection()
            lastNodeInd = len(network.nodes)

        # doesn't seem usefull
        #lCurrentDir = os.getcwd()
        #lNetworkDir = os.path.dirname(filename)
        #lFileNameWithoutPath = os.path.split(filename)[-1]
        #os.chdir(lNetworkDir)
        #execfile(lFileNameWithoutPath, {}, {'self':self, 'masterNet':network})
        #os.chdir(lCurrentDir)
        execfile(filename, {}, {'self':self, 'masterNet':network})

        # we allow the calling function to set some widget values		
        if ins is not None:
            if type(ins) is not list:
                ins = [ins]
            for lIn in ins:
                lInFound = False
                for lNodes in network.nodes:
                    if lNodes.name == lIn[0]:
                        if lInFound is True:
                            warnings.warn("found several nodes %s"%lIn[0] )
                        lInputPort = lNodes.inputPortByName.get(lIn[1])
                        if lInputPort is None:
                            warnings.warn("node %s doesn't have port %s"%(lIn[0],lIn[1]) )
                        else:
                            if lInputPort.widget is None:
                                warnings.warn("node %s port %s doesn't have a widget to set"%(lIn[0],lIn[1]) )
                            else:
                                lInputPort.widget.set(lIn[2], run=False)
                        lInFound = True
                if lInFound is False:
                    warnings.warn("can't find node %s"%lIn[0] )

        network.needsResetNodeCache = 1
        if lastNodeInd > -1:
            network.selectNodes(network.nodes[lastNodeInd:])

        network._modified = False

        if takefocus is False and lCurrentNetwork in self.networks:
                self.setNetwork(lCurrentNetwork)

        if hasattr(self, 'buttonVariables'):
            if self.currentNetwork.runOnNewData.value is True:
                self.buttonVariables['runOnNewData'].set(1)
            else:
                self.buttonVariables['runOnNewData'].set(0)

        return network # michel asked for this function to return the loaded network


    def addNetwork(self, network):
        """None <- addNetwork(network)
adds a Network object to the editor
"""
##          while network.name in self.networks.keys():
##              name = askstring("Network name already used", "Network Name",
##                               initialvalue=network.name)
##              network.rename(name)

        NoGuiNetworkBuilder.addNetwork(self, network)

        handle = network.eventHandler['onSelectionChange']
        handle.AddCallback(self.handleSelectionChangeMenus)
        self.eventHandler['addNetwork'].CallCallbacks()
        # and build the Pmw.Notebook page, the network canvas etc
        network.buildIcons()
        self.setFont("NetTabs",self.font["NetTabs"])


    def closeNetwork_cb(self, event=None):
        """called from File->Close
"""

        if self.currentNetwork is None: 
            return
        elif isinstance(self.currentNetwork, MacroNetwork):
            self.currentNetwork.macroNode.shrink()
            return

        name = self.currentNetwork.name
        
        text = "Do you want to save the changes you made to\n'"+name+"'?"
        d = SimpleDialog(self, text=text,
                         buttons=["Don't save", "Cancel", "Save"],
                         default=0, title="Close Network Dialog")
        result = d.go()

        if result == 0:
            self.deleteNetwork(self.currentNetwork)
            return
        elif result == 1:
            return
        elif result == 2:
            self.saveNetwork_cb()
            self.deleteNetwork(self.currentNetwork)
            return
        

    def deleteNetwork(self, network, saveValues=0):
        """None <- deleteNetwork(network)
deletes a Network object from the editor
"""
        del self.networks[network.name]
        network.delete(saveValues=saveValues)
        
        if self.currentNetwork == network:
            keys = self.networks.keys()
            if len(keys):
                self.setNetwork(self.networks[keys[0]])
            else:
                # FIXME: we should turn off most menus and buttons
                self.currentNetwork = None
        self.eventHandler['deleteNetwork'].CallCallbacks()
        

    def selectNetwork(self, name):
        """ get's called by Pmw with the original name used to create the page
"""
        
        network = None
        for n in self.networks.values():
            if n.origName == name:
                network = n
                break
        if network:
            if network.canvas:
                self.setNetwork(network)
        else:
            # do nothing. We can enter here when we quit and are deleting
            # macro networks
            return
        

    def renameNetworkTab(self, network, newName):
        na = self.networkArea
        # update the tab name
        na.component(network.origName+'-tab').configure(text=newName)
        

    def setNetwork(self, network):
        #print "setNetwork", network, self.__class__
        if network!=self.currentNetwork and network.canvas:
            self.networkArea.selectpage(network.origName)
            # get rid of any posted menu
            net = self.currentNetwork
            if net and net.postedMenu:
                net.postedMenu.unpost()
                net.postedMenu = None
        self.currentNetwork = network
        self.nbPaste = 0 # no shift on next paste operation
        network.eventHandler['onSelectionChange'].CallCallbacks()
    

    def myButtonPress(self, event=None):
        #add button press callback to clear self.postedMenu attribute
        self.currentNetwork.postedMenu = None

        
    def makeNetworksMenu(self):
        Networks_button = Tkinter.Menubutton(self.mBar,
                                             text='Networks',
                                             underline=0)
        self.menuButtons['Networks'] = Networks_button
        Networks_button.pack(side=Tkinter.LEFT, padx="1m")

        # re-set tearoff
        Networks_button.menu = Tkinter.Menu(Networks_button)#, tearoff=False)
        #Networks_button.menu.add_separator()

        Networks_button.menu.bind("<Any-Button>", self.myButtonPress, '+')

        # NOTE: the 'accelerator' entries are only used to display the key,
        # the binding actually occurs in net.py in bindCallbacks()
        # Vision.VPE.py also adds some events in it's addNetwork() method

        Networks_button.menu.add_command(label='New...',
                                     accelerator="ctrl-n",
                                     command=self.newNet_cb,
                                     underline=0)
        Networks_button.menu.add_command(label='Rename...',
                                     command=self.renameNet_cb,
                                     underline=2)
        Networks_button.menu.add_command(label='Close...',
                                     accelerator="ctrl-w",
                                     command=self.closeNetwork_cb,
                                     underline=0)
        Networks_button.menu.add_command(label='Soft run',
                                     command=self.softrunCurrentNet_cb,
                                     accelerator="ctrl-r",
                                     underline=5)
        Networks_button.menu.add_command(label='Hard run',
                                     command=self.runCurrentNet_cb,
                                     accelerator="ctrl-h",
                                     underline=0)

        if hasattr(self, 'buttonVariables') is False:
            self.buttonVariables = {}
        if self.buttonVariables.has_key('runOnNewData') is False:
            self.buttonVariables['runOnNewData'] = Tkinter.IntVar()
        Networks_button.menu.add_checkbutton(label="Immediate run",
                                           variable=self.buttonVariables['runOnNewData'],
                                           command=self.setRunOnNewData_cb,
                                           accelerator="ctrl-f",
                                           underline=1)

        func = CallBackFunction( self.menuOption_cb, 'withThreads')
        Networks_button.menu.add_checkbutton(label="Run multi-threaded",
                                             variable = self.withThreadsTk,
                                             command=func,
                                             underline=10)

        Networks_button.menu.add_command(label='Copy', command=self.copy_cb, underline=0)
        Networks_button.menu.add_command(label='Cut', command=self.cut_cb, underline=0)
        Networks_button.menu.add_command(label='Paste', command=self.paste_cb, underline=0)

        Networks_button.menu.add_command(label='Refresh',
                                     command=self.refreshNet_cb,
                                     underline=2)
##         # Disabled Reset Widget Values for the time being, the method
##         # can still be called with ed.currentNetwork.resetWidgetValues()
##         Networks_button.menu.add_command(label='Reset Widget Values',
##                                      command=self.resetWidgetValues_cb)
        Networks_button.menu.add_command(label='Reset cache',
                                         command=self.resetCache_cb,
                                         underline=2)
        Networks_button['menu'] = Networks_button.menu

        #Networks_button.menu.add_separator()

        def buildhostCascadeMenu():
            Networks_button.menu.cascadeMenu.delete(0, 'end')
            if self.libraries.has_key('Web Services'):
              for lKey in self.libraries['Web Services'].libraryDescr.keys():
                if lKey.startswith('http://'):
                    cb = CallBackFunction( self.replaceSelectedNodesWithHost, host=lKey)
                    Networks_button.menu.cascadeMenu.add_command(label=lKey, command=cb)
        Networks_button.menu.cascadeMenu = Tkinter.Menu(Networks_button.menu, tearoff=0, postcommand=buildhostCascadeMenu)
        Networks_button.menu.add_cascade(label='Replace with nodes from', menu=Networks_button.menu.cascadeMenu)


    def replaceSelectedNodesWithHost(self, host):
        if len(self.currentNetwork.selectedNodes):
            lNodeList = self.currentNetwork.selectedNodes[:]
        else:
            lNodeList = self.currentNetwork.nodes[:]

        for lNode in lNodeList:
            if    lNode.constrkw.has_key('host') \
              and host != suppressMultipleQuotes(lNode.constrkw['host']):
                lNode.replaceWithHost(host=host)


    def copy_cb(self, event=None):
        self.copyNetwork_cb(event)


    def cut_cb(self, event=None):
        self.cutNetwork_cb(event)


    def paste_cb(self, event=None):
        self.pasteNetwork_cb(event)


    def makeFileMenu(self):
        File_button = Tkinter.Menubutton(self.mBar, text='File', underline=0)
        self.menuButtons['File'] = File_button
        File_button.pack(side=Tkinter.LEFT, padx="1m")

		# re-set tearoff
        File_button.menu = Tkinter.Menu(File_button)#, tearoff=False)
        #File_button.menu.add_separator()

        File_button.menu.add_command(label='New...', underline=0,
                                     accelerator='ctrl-n',
                                     command=self.newNet_cb)
        File_button.menu.add_command(label='Open...', underline=0,
                                     accelerator='ctrl-o',
                                     command=self.loadNetwork_cb)
        File_button.menu.add_command(label='Merge...', underline=0, 
                                     command=self.mergeNetwork_cb)
        File_button.menu.add_command(label='Close...', 
                                     underline=0,
                                     accelerator="ctrl-w", 
                                     command=self.closeNetwork_cb)
        File_button.menu.add_separator()
        File_button.menu.add_command(label='Save...', underline=0,
                                     accelerator="ctrl-s",
                                     command=self.saveNetwork_cb)
        File_button.menu.add_separator()
        File_button.menu.add_command(label='Print', underline=0,
                                     accelerator="ctrl-p",
                                     command=self.print_cb)
        File_button.menu.add_separator()
        File_button.menu.add_command(label='Quit', underline=0, 
                                     accelerator="ctrl-q",
                                     command=self.interactiveExit_cb)
        File_button['menu'] = File_button.menu

        if self.resourceFolderWithVersion is not None:
            rcFile = os.path.join(self.resourceFolderWithVersion,'Vision',"recent.pkl")        
            self.recentFiles = RecentFiles(self, File_button.menu, filePath=rcFile, 
                                       menuLabel = 'Open recent', underline=5)


    def makeEditMenu(self):
        Edit_button = Tkinter.Menubutton(self.mBar, text='Edit', underline=0)
        self.menuButtons['Edit'] = Edit_button
        Edit_button.pack(side=Tkinter.LEFT, padx="1m")

        # got rid of useless tearoff
        Edit_button.menu = Tkinter.Menu(Edit_button, tearoff=False)
        Edit_button.menu.add_separator()

        #Edit_button.menu.add('command', label="Undo", command=self.undo)
        #Edit_button.menu.entryconfig(1, state=Tkinter.DISABLED)
        Edit_button.menu.add_command(label="Undo", accelerator="ctrl-z",
                                     command=self.undo,
                                     state=Tkinter.DISABLED, underline=0)
        Edit_button.menu.add_separator()

        # Please note: accelerators such as Ctrl-a are just for visuals,
        # the real binding of these events takes place in net.py

        Edit_button.menu.add_command(label="Cut", accelerator="ctrl-x",
                                     command=self.cutNetwork_cb, underline=2)
        Edit_button.menu.entryconfig("Cut", state=Tkinter.DISABLED)
        Edit_button.menu.add_command(label="Copy", accelerator="ctrl-c",
                                     command=self.copyNetwork_cb, underline=0)
        Edit_button.menu.entryconfig("Copy", state=Tkinter.DISABLED)
        Edit_button.menu.add_command(label="Paste",  accelerator="ctrl-v",
                                     command=self.pasteNetwork_cb, underline=0)
        Edit_button.menu.entryconfig("Paste", state=Tkinter.DISABLED)
        Edit_button.menu.add_separator()

        #Edit_button.menu.add_checkbutton(label="Options", command=self.options)
        Edit_button.menu.add_command(label="Select all",
                                     accelerator=("ctrl-a"),
                                     command=self.selectAll_cb, underline=7)

        if self.withShell:
            Edit_button.menu.add_separator()
            Edit_button.menu.add_command(label="Show python shell",
                                         command=self.togglePythonShell,
                                         underline=12)

        Edit_button.menu.add_separator()
        func = CallBackFunction( self.menuOption_cb, 'glyph')
        Edit_button.menu.add_checkbutton(label="Glyph",
                                         variable=self.glyphTk,
                                         command=self.toggleshowHideGlyph,
                                         state='disabled',
                                         underline=0)

        func = CallBackFunction( self.menuOption_cb, 'verbose')
        Edit_button.menu.add_checkbutton(label="verbose",
                                         variable=self.verboseTk,
                                         command=func,
                                         underline=0)

        func = CallBackFunction( self.menuOption_cb, 'flashNodesWhenRun')
        Edit_button.menu.add_checkbutton(label="Flash nodes when run",
                                         variable=self.flashNodesWhenRunTk,
                                         command=func,
                                         underline=6)
        func = CallBackFunction( self.menuOption_cb, 'splineConnections')
        Edit_button.menu.add_checkbutton(label="Spline connections",
                                         variable=self.splineConnectionsTk,
                                         command=self.toggleSplineConnections,
                                         underline=0)
        
        Edit_button.menu.add_checkbutton(label="Color node by library",
                                         variable=self.colorNodeByLibraryTk,
                                         command=self.toggleColorNodeByLibrary,
                                         underline=14)
        #hyperbolic scaling is currently broken
        #Edit_button.menu.add_checkbutton(label="hyperbolique scaling",
        #                                 command=self.scaleHyperToggle)

        Edit_button.menu.add_command(label="Create macro",
                                     #accelerator=("ctrl-m"),
                                     command=self.createMacro_cb,
                                     underline=7)

        Edit_button.menu.add_command(label="Create user panel",
                                     #accelerator=("ctrl-a"),
                                     command=self.createUserPanel_cb,
                                     underline=0)

        Edit_button.menu.add_command(label="Delete user panel",
                                     #accelerator=("ctrl-d"),
                                     command=self.deleteUserPanel_cb,
                                     underline=0)

        # set up a pointer from the file menubutton back to the file menu
        Edit_button['menu'] = Edit_button.menu


    def createMenus(self, parent):
        self.mBar = Tkinter.Frame(parent, relief=Tkinter.RAISED, borderwidth=2)
        self.mBar.pack(side='top',fill=Tkinter.X)
        self.menuButtons = {}
        self.makeFileMenu()
        self.makeEditMenu()
        self.makeNetworksMenu()
        apply( self.mBar.tk_menuBar, self.menuButtons.values() )
	self.title = Tkinter.Label(self.mBar, text=self.name)
	self.title.pack(side=Tkinter.RIGHT)

       
    def setUndoLabel(self):
        b = self.menuButtons['Edit']
        if len(self.undoStack)==0:
            b.menu.entryconfig(1, label='Undo',state=Tkinter.DISABLED)
            return
        else:
            l = self.undoStack[-1][1]
            # FIXME!!! since undo is broken, the entry remains disabled
            b.menu.entryconfig(1, label='Undo: '+l,state=Tkinter.DISABLED)


    def undo(self, event=None):
        return
        # FIXME!!! This command is currently broken
        b = self.menuButtons['Edit']
        if len(self.undoStack)==0: return
        command, comment = self.undoStack.pop()
        cmd = command[:string.rfind(command, ')')]+', undo=0)'
        exec( cmd )
        self.setUndoLabel()


    def setupUndo(self, command, comment):
        self.undoStack.append( (command, comment) )
        self.setUndoLabel()


    def scaleHyperToggle(self, event=None):
        cnet = self.currentNetwork
        if cnet.scalingHyper:
            cnet.canvas.unbind("<Motion>")
            cnet.resetScale()
        else:
            cnet.canvas.bind("<Motion>", cnet.scaleHyper_cb)
            cnet.lastx = None # we do not get an event in this callback :(
        cnet.scalingHyper = not cnet.scalingHyper
        
            
    def scaleHyper_cb(self, event):
        if self.lastx is None:
            self.lastx = event.x
            self.lasty = event.y
            return
        cnet = self.currentNetwork
        cnet.scaleHyper(event.x, event.y, cnet.hyperScaleRad)
        self.lastx = event.x
        self.lasty = event.y
    

    def createMacro_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'm':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)
            
        macName = 'macro0'
        i=1
        while macName in self.networks.keys():
            macName = 'macro'+str(i)
            i = i + 1
        macName = askstring('Macro Name', "Macro Name", initialvalue=macName)
        while macName in self.networks.keys():
            macName = askstring('Macro Name already in use', "Macro Name",
                                initialvalue='macro')
        if macName is None or len(macName) == 0:
            return
        self.createMacro(self.currentNetwork, macName)


    def createMacro(self, network, name):
        from NetworkEditor.macros import MacroNode
        n = MacroNode(name)
        network.addNode(n , 100, 100 )
       

    def selectAll_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'a':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)
        
        self.currentNetwork.selectNodes(self.currentNetwork.nodes)


    def menuOption_cb(self, varName):
        """menuOptions(var, varTk toggle menu options
        var: verbose
             colorNodeByLibrary
             flashNodesWhenRun
        """
        varTk = getattr(self, varName+'Tk')
        setattr(self, varName, varTk.get())


    def toggleSplineConnections(self, event=None):
        self.menuOption_cb('splineConnections')
        self.currentNetwork.setSplineConnections(
            self.splineConnections==1 )


    def toggleshowHideGlyph(self,event=None):
        self.menuOption_cb('glyph')
        self.showHideGlyphWidget(
            self.glyph==1 )    


    def toggleColorNodeByLibrary(self, event=None):
        self.menuOption_cb('colorNodeByLibrary')
        for net in self.networks.values():
            for node in net.nodes:

                # if color by library is ON:
                if self.colorNodeByLibraryTk.get() == 1:
                    # no node library?
                    if node.library is None:
                        if node.frozen is True:
                            fcol = '#b6d3f6' # color for frozen state
                        else:
                            fcol = "gray85"
                    # node library?
                    else:
                        if node.frozen is True:
                            fcol = '#b6d3f6' # color for frozen state
                        else:
                            fcol = node.library.color

                # elif color by library is OFF:
                else:
                    if node.frozen is True:
                        fcol = '#b6d3f6' # color for frozen state
                    else:
                        fcol = "gray85"
                    
                
##                 if node.library is not None:
##                     if node.frozen == True:
##                         col = '#b6d3f6' # color for frozen state
##                     else:
##                         if self.colorNodeByLibraryTk.get() == 1:
##                             col = node.library.color
##                         else:
##                             col = 'gray85'
                node.deselectOptions['fill'] = fcol
                node.setColor(fcol)
            

    def newNet_cb(self, event=None):
        # reset keyboard modifier
        # Note: we do that in case this method raises an exception. If we
        # do not call modifierUp() we do not release the focus and Python
        # is basically locking the screen until the process is killed.
        if event and event.keysym == 'n':
            event.keysym = "Control_L"
            self.currentNetwork.modifierUp(event)
            event.keysym = "Control_R"
            self.currentNetwork.modifierUp(event)

        index = 0
        while 1:
            initialvalue = 'Network %d'%index
            if initialvalue not in self.networks.keys():
                break
            index += 1
        name = askstring("Network name", "Network name",
                         initialvalue=initialvalue, 
                         parent = self)
        while name in self.networks.keys():
            name = askstring("Network name already used", "Network name",
                             initialvalue=name, parent = self)
        if name is None or len(name) == 0:
            return
        net = Network(name)
        self.addNetwork(net)
        net.buildIcons()
        self.setNetwork(net)

        
    def renameNet_cb(self, event=None):
        name = None
        while 1:
            name = askstring("Network name already used", "Network name",
                             initialvalue=self.currentNetwork.name)
            if name not in self.networks.keys(): break
        
        if name is None or len(name) == 0:
            return
        self.currentNetwork.rename(name)

        
    def setRunOnNewData_cb(self, event=None):
        #print "setRunOnNewData_cb"
        if self.currentNetwork is not None:
            if self.buttonVariables['runOnNewData'].get() == 1:
                self.currentNetwork.runOnNewData.value = True
            else:
                self.currentNetwork.runOnNewData.value = False


    def toggleRunOnNewData_cb(self, event=None):
        #print "toggleRunOnNewData_cb"
        if self.buttonVariables['runOnNewData'].get() == 0:
            self.buttonVariables['runOnNewData'].set(1)
        else:
            self.buttonVariables['runOnNewData'].set(0)
        self.setRunOnNewData_cb()

            
#    def deleteNet_cb(self, event=None):
#        ans = askokcancel("Confirm network deletion",
#                          "Do you really want to delete the current network?")
#        if ans:
#            self.deleteNetwork(self.currentNetwork)

            
    def runCurrentNet_cb(self, event=None):
        # this is now done in self.currentNetwork.run()
        #self.currentNetwork.forceExecution = 1
        self.currentNetwork.run(roots=self.currentNetwork.rootNodes)

            
    def softrunCurrentNet_cb(self, event=None):
        # this is now done in self.currentNetwork.run()
        #self.currentNetwork.forceExecution = 1
        self.currentNetwork.run()

            
    def togglePauseCurrentNet_cb(self, event=None):
        net = self.currentNetwork
        net.togglePause()

            
    def stopCurrentNet_cb(self, event=None):
        print '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
        net = self.currentNetwork
        net.stop()


    def refreshNet_cb(self, net=None, event=None):
        if net is None:
            net = self.currentNetwork
        for node in net.nodes:
            node.scaleSum = 1.0
        net.destroyIcons(saveValues=1)
        net.buildIcons()
        selnodes = net.selectedNodes[:]
        net.clearSelection()
        net.selectNodes(selnodes)


    def resetWidgetValues_cb(self, event=None):
        self.currentNetwork.resetWidgetValues()


    def resetCache_cb(self, event=None):
        self.currentNetwork.resetNodeCache()


    def print_cb(self, event=None):
        # FIXME: DS: highly experimental... currently, just dumps the
        # postscript data into a file. The user has to print this file
        # manually
        postscript = self.currentNetwork.scrolledCanvas.postscript()
        fd=open('network.ps', 'w')

        fd.write(postscript)
        fd.close()


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


    def configure(self, **kw):
        if len( kw.items() ) == 0: # we return a dict with the current config
            dict = {}
            dict['visibleWidth'] = self.visibleWidth
            dict['visibleHeight'] = self.visibleHeight
            dict['withThreads'] = self.withThreadsTk.get()
            dict['verbose'] = self.verboseTk.get()
            dict['glyph'] = self.glyphTk.get()
            dict['colorNodeByLibrary'] = self.colorNodeByLibraryTk.get()
            dict['flashNodesWhenRun'] = self.flashNodesWhenRunTk.get()
            return dict
            
        for key,value in kw.items():
            if key=='visibleWidth':
                self.visibleWidth = value
                self.resizeNetworkArea()
            elif key=='visibleHeight':
                self.visibleHeight = value
                self.resizeNetworkArea()
            elif key=='withThreads': self.setConfigValue(key, value)
            elif key=='verbose': self.setConfigValue(key, value)
            elif key=='glyph': self.setConfigValue(key, value)
            elif key=='colorNodeByLibrary': self.setConfigValue(key, value)
            elif key=='flashNodesWhenRun': self.setConfigValue(key, value)


    def setConfigValue(self, varName, value):
        assert value in [0,1]
        varTk = getattr(self, varName+'Tk')
        setattr(self, varName, value)
        varTk.set(value)


    def togglePythonShell(self, event=None):
        if not self.withShell:
            return
        b = self.menuButtons['Edit']
        shell = self.pyshell.top
        if shell.state() == 'withdrawn':
            b.menu.entryconfig("Show python shell", label='Hide python shell')
            self.pyshell.top.deiconify()
        else:
            b.menu.entryconfig("Hide python shell", label='Show python shell')
            self.pyshell.top.withdraw()


    def sourceFile(self, resourceFile=None):
        if resourceFile is None or resourceFile == '':
            return
        resourceFileLocation = findResourceFile(self, resourceFile=resourceFile)

        if resourceFileLocation is None or resourceFileLocation == '':
            return
        
        if resourceFileLocation.has_key('currentdir') and \
           not resourceFileLocation['currentdir'] is None:
            path = resourceFileLocation['currentdir']

        elif resourceFileLocation.has_key('home') and \
             not resourceFileLocation['home'] is None:
            path = resourceFileLocation['home']

        elif resourceFileLocation.has_key('package') and \
             not resourceFileLocation['package'] is None:
            path = resourceFileLocation['package']
        else:
            return
        
        if not path:
            return
            
        # now execute the file:
        localDict = sys.modules['__main__'].__dict__
        # save self entry in local dict if it exists
        oldself = None
        if localDict.has_key('self'):
            oldself = localDict['self']

        localDict['self'] = self
        globalDict = self.__dict__

        execfile( path, globalDict, localDict)

        # restore old self on local dict
        if oldself is not None:
            localDict['self'] = oldself
        else:
            localDict.pop('self')


    def stopNetworkAndQuit_cb(self, event=None):
        """
"""
        if self.currentNetwork.execStatus is 'running':
            self.stopCurrentNet_cb(event=event)
        lMaster = self.master
        while hasattr(lMaster, 'master') and lMaster.master is not None:
            lMaster = lMaster.master
            lMaster.quit()
            lMaster.destroy()
        sys.exit(0)


    def toggleNetworkRun_cb(self, event=None):
        """
"""
        net = self.currentNetwork
        net.execStatusLock.acquire()
        if net.execStatus is 'running':
            self.stopCurrentNet_cb(event=event)
        else:
            self.runCurrentNet_cb(event=event)
        net.execStatusLock.release()




if __name__=='__main__':
    ed = NetworkBuilder("test builder")
    top = Tkinter.Toplevel()
    ed1 = NetworkBuilder("test builder1", master=top,
                         visibleWidth=600, totalWidth=3000)
    node1 = NetworkNode(name='node1')
    ed.addNode(node1, 100, 100)
    node1.rename('operator1')
    node1.highlight()
    node1.unhighlight()

    node2 = NetworkNode(name='node2')
    ed.addNode(node2, 200, 200)
    top.mainloop()
    conn1 = ed.connectNodes(node1, node2)
    conn1.highlight()
    conn1.unhighlight()

    node3 = NetworkNode(name='node3')
    ed.addNode(node3, 300, 100)
    conn2 = ed.connectNodes(node3, node2, mode='angles')

    node4 = NetworkNode(name='node4')
    ed.addNode(node4, 350, 270)
    conn3 = ed.connectNodes(node2, node4, mode='angles', smooth=1)
    
    node1.move(200, 100)
    conn1.updatePosition()

    ed.selectNodes([node1, node2, node3])
    ed.deselectNodes([node1, node4])

    ed.moveSubGraph(ed.selectedNodes, 10, 20)

    node5 = NetworkNode(name='node5')
    ed.addNode(node5, 100, 200)
    conn4 = ed.connectNodes(node1, node5, mode='angles')
  
    def connectCB(connection):
        print 'connecting %s with %s'%(connection.port1.node.name,
                                       connection.port2.node.name)
    ed.actionCallback['onAddConnection'].AddCallback(connectCB)
    conn4 = ed.connectNodes(node2, node5)
    
    # try nodes of type 2

    n1 = NetworkNode('test1')
    ed.addNode(n1, 100, 350)
    n1.addOutputPort()

    from NetworkEditor.simpleNE import NetworkNode
    n2 = NetworkNode('test2')
    ed.addNode(n2, 300, 350)
    n2.addInputPort()
    n2.addInputPort(name='test', balloon='test help',
                    required=True, datatype=None, validate=None)


##      from NetworkEditor.simpleNE import NetworkConnection
##      ed.connectNodes(n1, n2, 2, 1)

##      ed.connectNodes(node5, n2, 0, 2)
##      ed.selectNodes([n2])
##      ed.moveSubGraph(ed.selectedNodes, 10, 20)


