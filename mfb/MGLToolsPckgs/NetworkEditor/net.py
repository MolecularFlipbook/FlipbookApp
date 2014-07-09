#########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner, Daniel Stoffler
#
#       sanner@scripps.edu
#       stoffler@scripps.edu
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

import sys
import os
import types, math, string, threading, weakref
import Tkinter, Pmw
import traceback, time
from time import time, sleep
import re

from tkSimpleDialog import askstring

from mglutil.gui import widgetsOnBackWindowsCanGrabFocus
from mglutil.util.callback import CallbackManager, CallBackFunction
from mglutil.gui.Misc.Tk.KeybdModMonitor import KeyboardModifierMonitor

from NetworkEditor.itemBase import NetworkItemsBase
from NetworkEditor.items import NetworkNodeBase, NetworkConnection
from NetworkEditor.ports import InputPort, OutputPort, \
     RunChildrenInputPort, RunNodeInputPort
from NetworkEditor.flow import ExecutionThread, AfterExecution
from NetworkEditor.itemBase import UserPanel
from Tkinter import *
from Glyph import Glyph

from mglutil.events import Event

class AddNodeEvent(Event):

    def __init__(self, network, node, x, y):
        """  """
        self.timestamp = time()
        self.network = network
        self.node = node
        self.position = (x,y)

    
class ConnectNodes(Event):

    def __init__(self, network, connection):
        """  """
        self.timestamp = time()
        self.network = network
        self.connection = connection

    
class DeleteNodesEvent(Event):

    def __init__(self, network, nodes):
        """  """
        self.timestamp = time()
        self.network = network
        self.nodes = nodes


class DeleteConnectionsEvent(Event):

    def __init__(self, network, connections):
        """  """
        self.timestamp = time()
        self.network = network
        self.connection = connections


class reference_value:
    def __init__(self, value):
        self.value = value

import socket
from select import select

class Communicator:
    """This class provides support for socket-based communication with a network that is running without a GUI
"""

    def __init__(self, network, host='', portBase=50001, listen=5):
        self.network = network
        self.host = host
        self.socket = s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        i = 0
        while 1:
            try:
                s.bind((self.host, portBase+i))
                break
            except Exception,e:
                print e
                i += 1
                if i==10:
                    raise RuntimeError, "Communicator unable to bind"
                #if e.args[0]==98: # Address already in use
                #elif e.args[0]==22: # socket already bound
        
	s.listen(listen)
	s.setblocking(0)
        self.port = portBase+i
        self.connId = s.fileno()
        self.clientConnections = []
        self.clientInIds = []


    def clientConnect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        i = 0
        from time import sleep
        while 1:
            err = s.connect_ex((self.host, self.port))
            if err == 111:
                sleep(0.2)
                i +=1
                if i == 10:
                    print "Communicator: failed to connect"
                    return None
                continue
            break
        return s
        

    def handleCommunications(self):
        #print "handleCommunications"
        net = self.network
        ifd, ofd, efd = select([self.socket.fileno()], [], [], 0)

        if self.connId in ifd:
            conn, addr = self.socket.accept()
            self.clientConnections.append( (conn, addr) )
            self.clientInIds.append( conn.fileno() )
            print 'Connected by', addr

        if len(self.clientInIds)==0:
            return

        ifd, ofd, efd = select(self.clientInIds, [], [], 0)

        for conn in self.clientConnections:
            if conn[0].fileno() in ifd:
                input = conn[0].recv(4096) #os.read(_pid, 16384)
                if len(input)==0: # client diconnected
                    self.clientInIds.remove(conn[0].fileno())
                    self.clientConnections.remove(conn)
                else:
                    procid = os.getpid()
                    print "process %d input"%procid, repr(input)

                    #mod = __import__('__main__')
                    #mod.__dict__['clientSocket'] = conn[0]
                    #exec(input, mod.__dict__)
                    from mglutil.util.misc import importMainOrIPythonMain
                    lMainDict = importMainOrIPythonMain()
                    lMainDict['clientSocket'] = conn[0]
                    exec(input, lMainDict)


class Network(KeyboardModifierMonitor, NetworkItemsBase):
    """class to hold all the information about a bunch of nodes and connections
"""
    _nodesID = 0    # used to assign a node a unique number
                    # accross all the networks. This is incremented
                    # in the addNodes() method


    def connectToProcess(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        i = 0
        from time import sleep
        while 1:
            err = s.connect_ex((host, port))
            if err == 111:
                sleep(0.2)
                i +=1
                if i == 10:
                    print "Communicator: failed to connect"
                    return None
                continue
            break
        return s

    def generateScript(self):
        """Create a Python script that corresponds to this network
"""
        count = 0
        src = ""
        ndict = {}
        # dump all doit methods
        for node in self.nodes:
            ndict[node] = []
            funcsrc = node.sourceCode.replace('def doit(',
                                              node.name+str(count)+'doit(')
            src += fncscr+'\n'


    def __init__(self, name='Noname', origin='user'):
        
        KeyboardModifierMonitor.__init__(self)
        NetworkItemsBase.__init__(self, name)

        self.origin = origin
        
        # HACK MS, replace by event
        self.afterRunCb = None

        self.canvasFrame=None
        self.filename = None  # file from which the network was loaded if
                              # it is loaded from a file (includes path)
        self.origName = name    # used to delete the Pmw.NoteBook page
                                # correctly after network was renamed

        self.selectedNodes = []
        self.selectedConnections = []
        self.firstItemId = None
        self.canvas = None
        self.debug = False
        
        self.defaultConnectionMode = 'angles'
        self.defaultConnectionOptions = {}
        self.needsResetNodeCache = 1
        self.hyperScaleRad = 200 # radius is pixel in which nodes scale to 1.0
        self.scalingHyper = 0

        self.selectionBox = None    # canvas object used to draw selectionbox

        self.glyphSelect = None
        self.gselectionboxes = []
        self.sbrev =0
        self.circle = None
        self.rectangle = None
        self.currentcircle = None
        self.currentrectangle = None
        self.glyphselectionBox = None

        self.eventHandler = {} # stores callback managers for network events
        self.createCallbackManager('preSelection')

        doc = """Gets called every time the selection changes.
No arguments."""
        self.createCallbackManager('onSelectionChange',doc)

        self.createCallbackManager('loadLibrary')

        doc = """Gets called every time we save a network, to add source code
at the very beginning of a saved network"""
        self.createCallbackManager('saveNetworkBegin', doc)

        doc = """Gets called every time we save a network, to add source code
at the very end of a saved network"""
        self.createCallbackManager('saveNetworkEnd', doc)

        self.nodes = []        # list of nodes in  network
        self.nodesById = {}    # dictionary or nodes
                               # (key: unique tag of the NetworkItem,
                               #  value: NetworkItem instance)

        self.rootNodes = []    # list of nodes with no parents, These are 
                               # used to run the network when a 
                               # node is added it appended tothat list
                               # when a connection is created it is removed
                               # each node has an isRootNode flag

        # these are used for turning picking event into netwokr objects
        self.inPortsId = {}    # dictionary or ports
                               # (key: unique id of the port,
                               #  value: (node, portnumber))

        self.outPortsId = {}   # dictionary or ports
                               # (key: unique id of the port,
                               #  value: (node, portnumber))

        self.connections = []
        self.connById = {}     # dictionary of connections between nodes
                               # (key: unique tag of the NetworkItem,
                               #  value: NetworkItem instance)

                                     
        self.forceExecution = 0 # set to one when a network is forced to
                                # execute. This will force the execution of
                                # all root nodes in subnetworks as well as
                                # pretent all data flwoing into subnetworks is
                                # new
                                
        self.mouseActionEvents = [
            '<Button-1>', '<Shift-Button-1>',
            '<Alt-Button-1>', '<Control-Button-1>',
            '<Double-Button-1>', '<Double-Shift-Button-1>',
            '<Double-Alt-Button-1>', '<Double-Control-Button-1>',
            '<Button-2>', '<Shift-Button-2>',
            '<Alt-Button-2>', '<Control-Button-2>',
            '<Double-Button-2>', '<Double-Shift-Button-2>',
            '<Double-Alt-Button-2>', '<Double-Control-Button-2>',
            '<Button-3>', '<Shift-Button-3>',
            '<Alt-Button-3>', '<Control-Button-3>',
            '<Double-Button-3>', '<Double-Shift-Button-3>',
            '<Double-Alt-Button-3>', '<Double-Control-Button-3>'
            ]

        # table of functions to call for specific mouse events on canvas
        self.mouseButtonFlag = 0
        self.mouseAction = {}
        for event in self.mouseActionEvents:
            self.mouseAction[event] = None

        self.mouseAction['<Button-1>'] = self.startDrawingSelectionBox
        self.mouseAction['<Button-2>'] = self.moveCanvasOrSelectedNodes #self.moveSelectedNodesStart
        self.mouseAction['<Button-3>'] = self.postCanvasMenu
        self.mouseAction['<Shift-Button-3>'] = self.moveCanvasStart
        self.mouseAction['<Shift-Button-2>'] = self.scaleNetworkStart

        # global lock for running a node in this network
        # used to make sure only 1 node runs at a time
        self.RunNodeLock = threading.RLock()

        # global lock for running nodes in this network
        # used to avoid multiple runs to get started simultaneously
        self.RunLock = threading.RLock()
        self.RunLockCond = threading.Condition(self.RunLock)
        
        # lock for modifying execution abortion variable
        self.execStatusLock = threading.RLock()
        self.execStatusCond = threading.Condition(self.execStatusLock)
        self.execStatus = 'waiting' # waiting: ready to run new set of nodes
                                    # pending: set by network.run metho
                                    #     when a new thread is created
                                    # running: nodes are currently running
                                    # stop: execution will stop ASAP
                                    # pause: execution will pause ASAP
                                    # frozen: frozen
        self.runAgain = False       # set to False in runNodes, set to True
                                    # if runNodes is called during a run
                                    
        self.runOnNewData = reference_value(True) # set to false to avoid execution of the
                                            # node and its children node 
                                            # upon connection or new data

        self.lastExecutedNodes = [] # this list is filled by runNodes() each 
                                    # time this method runs a 3-tuple
                                    # (node, starttime, endtime) is added for
                                    # each node BEFORE it executes


        # lock used by iterate node
        self.iterateLock = threading.RLock()
        self.iterateCond = threading.Condition(self.iterateLock)

        self.postedMenu = None
        self.lastPosY = 10 # used in self.addNodes to auto place nodes
        
        self.userPanels = {}  # dictionary of panel created by the user
                              # to place widgets for an application
                              # the key is the panel name
                              # the value is the Tkinter Frame

        self.nodeToRunList = []


    def onStoppingExecution(self):
        self.canvas.update_idletasks()
        for node in self.nodes:
            node.onStoppingExecution()


    def getTypeManager(self):
        ed = self.getEditor()
        if ed is not None:
            return ed.typeManager
        else:
            return self.typeManager


    def getNodeByName(self, name):
        """nodeList <- getNodeByName(self, name)
Return all the nodes who's name match the name regular expression
"""
        nodes = []
        import re
        reg = re.compile(name)
        nodes = filter( lambda x,reg=reg: reg.match(x.name), self.nodes )
        return nodes
    

    def nodeIdToNumber(self, id):
        """return the current index of this node in network.nodes if the node's
        _id is given."""

        for i in range(len(self.nodes)):
            if self.nodes[i]._id == id:
                break
        return i


    def getNodesByIds(self, ids):
        """returns a list of nodes based on a list of ids"""
        found = []
        for node in self.nodes:
            if node._id in ids:
                found.append(node)
        return found

        
    def freeze(self):
        self.runOnNewData.value = False

        
    def unfreeze(self):
        self.runOnNewData.value = True


    def createCallbackManager(self, event, doc=None):
        assert not self.eventHandler.has_key(event)
        self.eventHandler[event] = CallbackManager()
        self.eventHandler[event].doc = doc


    def addCallbackManager(self, event, func):
        assert self.eventHandler.has_key(event)
        assert callable(func)
        
        self.eventHandler[event].AddCallback(func)
        

    def describeCallbackManager(self, event):
        assert self.eventHandler.has_key(event)
        return self.eventHandler[event].doc
    

    def postCanvasMenu(self, event):
        ed = self.getEditor()
        if self.postedMenu:
            self.postedMenu.unpost()
            self.postedMenu = None
        elif ed.menuButtons['Networks'].menu:
            ed.menuButtons['Networks'].menu.post(event.x_root,
                                                          event.y_root)
            self.postedMenu = ed.menuButtons['Networks'].menu


    def delete(self, saveValues=0):
        # this method destroys the network
        # this method is called from editor.deleteNetwork(), use that method
        # to delete a network, which is doing more stuff that is necessary!
        lRunOnNewDataValue = self.runOnNewData.value
        self.runOnNewData.value = False
        nodes = self.nodes[:]

        for n in nodes:
            self.deleteNodes([n])
            n.deleteIcon()
        for c in self.connections:
            c.deleteIcon()
        if self.canvas:
            self.destroyIcons(saveValues=saveValues)

        for p in self.userPanels.values():
            p.master.destroy()
        self.runOnNewData.value = lRunOnNewDataValue


    def destroyIcons(self, saveValues=0):
        # destroy the icons of node, ports, etc, but not the objects itself
        if not self.canvas:
            return
        for n in self.nodes:
            if n.objEditor:
                n.objEditor.Dismiss()
            if n.isExpanded():
                n.toggleNodeExpand_cb()
            for p in n.inputPorts:
                # get rid of all widgets, but save parameters. These will be
                # used in node.createWidgets to reconstruct widgets
                if saveValues and p.widget:
                    wcfg = p.widget.getDescr()
                    wcfg['initialValue'] = p.widget.get()
                    p.node.widgetDescr[p.name] =  wcfg
                p.widget = None
                p.destroyIcon()
            for p in n.outputPorts:
                p.destroyIcon()
                for c in p.connections:
                    c.destroyIcon()
            for p in n.specialInputPorts:
                for c in p.connections:
                    c.destroyIcon()
                p.destroyIcon()
            for p in n.specialOutputPorts:
                for c in p.connections:
                    c.destroyIcon()
                p.destroyIcon()
                
            n.menu.destroy()
            n.menu = None
            n.nodeWidgetsID = [] # ids of widgets in node
            n.iconTag = None
            n.iconMaster = None
            n.id = None # setting id to None will rebuild this icon
                        # in self.buildIcons

        self.destroyCanvas()


    def destroyCanvas(self):
        # delete the Pmw.Notebook page and everything in it
        ed = self.getEditor()
        ed.networkArea.delete(self.origName)
        self.canvas.destroy()
        self.canvasFrame=None
        self.canvas = None
        self.firstItemId = None
        self.nodesById = {}
        self.connById = {}
        self.inPortsId = {}
        self.outPortsId = {}

            
    def buildIcons(self):
        ed = self.getEditor()
        if self.canvas is None:
            self.createCanvas()
            lCanvasWasMissing = True
        else:
            lCanvasWasMissing = False

        for n in self.nodes:
            # Nodes belonging to a MacroNetwork are instanciated here
            if n.id is None:
                n.buildIcons(self.canvas, n.posx, n.posy)
                self.nodesById[n.id] = n
            # FIXME this is a hack ... when macro network is re-displayed
            # the widget appear bu the node is not scaled
            # unless inNode widget is visible by default hide it
            #widgetsInNode = n.getWidgetsForMaster('Node') 
            #for w in widgetsInNode.values():
            #    if not w.visibleInNodeByDefault:
            #        n.hideInNodeWidgets( w, rescale=0 )

        for c in self.connections:
            if not c.id:
                c.buildIcons(self.canvas)
                self.connById[c.id] = c
                if c.id2 is not None:
                    self.connById[c.id2] = c

        if lCanvasWasMissing is True:
            #FIXME this line was added because else nodes with widgets
            # in macros are 'flat' whenthe macro is expanded
            ed.setNetwork(self)

            self.bindCallbacks()


    def rename(self, name):
        ed = self.getEditor()
        if ed is not None:
            if self.name in ed.networks.keys():
                del ed.networks[self.name]
                ed.networks[name] = self
            if self.canvas:
                ed.renameNetworkTab(self, name)
        self.name = name
        self._setModified(True)

        
    def enter(self, event=None):
        if widgetsOnBackWindowsCanGrabFocus is False:
            lActiveWindow = self.canvas.focus_get()
            if    lActiveWindow is not None \
              and ( lActiveWindow.winfo_toplevel() != self.canvas.winfo_toplevel() ):
                return

        self.canvas.focus_set()


    def configure(self, event=None):
        self.visibleWidth = event.width
        self.visibleHeight = event.height


    def bindCallbacks(self):
        # bind mouse button callbacks
        # can only be done after the network has be added to an editor
        # and the draw canas has been created
        ed = self.getEditor()

        if self.canvas is None:
            print 'too early to bind'
            return
        self.canvas.bind("<Any-ButtonPress-1>", self.mouse1Down)
        self.canvas.bind("<Any-ButtonPress-3>", self.mouse1Down)
        self.canvas.bind("<Any-ButtonPress-2>", self.mouse1Down)
        self.canvas.bind("<Any-Double-ButtonPress-1>", self.mouse2Down)
        self.canvas.bind("<Any-Double-ButtonPress-2>", self.mouse2Down)
        self.canvas.bind("<Any-Double-ButtonPress-3>", self.mouse2Down)

        self.canvas.bind("<Any-ButtonRelease-1>", self.mouse1Up)
        self.canvas.bind("<Any-ButtonRelease-2>", self.mouse1Up)
        self.canvas.bind("<Any-ButtonRelease-3>", self.mouse1Up)

        # set the focus so that we get keyboard events, and add callbacks
        self.master = self.canvas.master # hack ot get this to work
        self.canvas.bind('<KeyPress>', self.modifierDown)
        self.canvas.bind("<KeyRelease>", self.modifierUp)

        # bind accelerator keys such as Ctrl-a for selectAll, etc
        self.canvas.bind('<Control-a>', ed.selectAll_cb)
        self.canvas.bind('<Control-c>', ed.copyNetwork_cb)
        #self.canvas.bind('<Control-f>', ed.toggleFreezeNetwork_cb)
        self.canvas.bind('<Control-f>', ed.toggleRunOnNewData_cb)
        self.canvas.bind('<Control-m>', ed.createMacro_cb)
        self.canvas.bind('<Control-n>', ed.newNet_cb)
        self.canvas.bind('<Control-o>', ed.loadNetwork_cb)
        self.canvas.bind('<Control-q>', ed.interactiveExit_cb)
        self.canvas.bind('<Control-p>', ed.print_cb)
        self.canvas.bind('<Control-r>', ed.softrunCurrentNet_cb)
        self.canvas.bind('<Control-h>', ed.runCurrentNet_cb)
        self.canvas.bind('<Control-s>', ed.saveNetwork_cb)
        self.canvas.bind('<Control-v>', ed.pasteNetwork_cb)
        self.canvas.bind('<Control-w>', ed.closeNetwork_cb)
        self.canvas.bind('<Control-x>', ed.cutNetwork_cb)
        self.canvas.bind('<Control-z>', ed.undo)
        
        # bind arrow keys to move nodes with arrows
        func = CallBackFunction(self.arrowKeys_cb, 0, -1)
        self.canvas.bind('<Up>', func)
        func = CallBackFunction(self.arrowKeys_cb, 0, 1)
        self.canvas.bind('<Down>', func)
        func = CallBackFunction(self.arrowKeys_cb, -1, 0)
        self.canvas.bind('<Left>', func)
        func = CallBackFunction(self.arrowKeys_cb, 1, 0)
        self.canvas.bind('<Right>', func)
        # same, with SHIFT: 10x bigger move
        func = CallBackFunction(self.arrowKeys_cb, 0, -10)
        self.canvas.bind('<Shift-Up>', func)
        func = CallBackFunction(self.arrowKeys_cb, 0, 10)
        self.canvas.bind('<Shift-Down>', func)
        func = CallBackFunction(self.arrowKeys_cb, -10, 0)
        self.canvas.bind('<Shift-Left>', func)
        func = CallBackFunction(self.arrowKeys_cb, 10, 0)
        self.canvas.bind('<Shift-Right>', func)
        

    def createCanvas(self):
        """create the Canvas and Title widgets"""

        ed = self.getEditor()
        master = self.canvasFrame = ed.networkArea.add(self.name)
        self.origName = self.name
        self.scrollregion=[0 , 0, ed.totalWidth, ed.totalHeight]
	self.scrolledCanvas = Pmw.ScrolledCanvas(
            master, borderframe=1, #labelpos='n', label_text='main',
            usehullsize=0, hull_width=ed.visibleWidth,
            hull_height=ed.visibleHeight,
            vscrollmode='static', hscrollmode='static')
        self.canvas = self.scrolledCanvas.component('canvas')
        self.canvas.configure(background='grey75', width=ed.visibleWidth,
                              height=ed.visibleHeight,
                              scrollregion=tuple(self.scrollregion) )
        self.firstItemId = self.canvas.create_line(0,0,0,0)

##          import NetworkEditor, os
##          file = os.path.join(NetworkEditor.__path__[0], "back1.gif")
##          self.bg = Tkinter.PhotoImage(file=file)
##          self.bgId = self.canvas.create_image(0, 0, anchor=Tkinter.NW,
##                                             image=self.bg)

        # bind standard callbacks
  	self.canvas.bind('<Configure>', self.configure)
	self.canvas.bind("<Control-z>", ed.undo)
	self.canvas.bind("<Control-Z>", ed.undo)

	# pack 'em up
	self.scrolledCanvas.pack(side=Tkinter.LEFT, expand=1,fill=Tkinter.BOTH)

        self.canvas.bind("<Enter>", self.enter)

#
#  MISC
#
    def setSplineConnections(self, yesno):
        if yesno is True:
            self.defaultConnectionOptions['smooth'] = 1
            for c in self.connections:
                apply( c.iconMaster.itemconfigure, (c.iconTag,),{'smooth':1})
        else:
            self.defaultConnectionOptions['smooth'] = 0
            for c in self.connections:
                apply( c.iconMaster.itemconfigure, (c.iconTag,),{'smooth':0})

#
# save/restore source code generation
#
    def saveToFile(self, filename, copyright=True):
        lines = []
        
        #if len(self.currentNetwork.userPanels) > 0:
            #lines += ['#!%s\n'%sys.executable]

        #lines += ['#!/bin/ksh '+self.resourceFolder+'/pythonsh\n']
        lines += ['#!/bin/ksh ~/.mgltools/pythonsh\n']

        lines += self.getNetworkCreationSourceCode(copyright=copyright)
        f = open(filename, 'w')        
        map( f.write, lines )
        f.close()


    def getNetworkCreationSourceCode(self, networkName='masterNet',
                                     selectedOnly=0, indent="",
                                     withRun=True,
                                     ignoreOriginal=False,
                                     copyright=False,
                                     importOnly=False):

        """returns code to re-create a network containing nodes and connections
selectedOnly: True/False. If set to true, we handle selected nodes only
indent: a string with whitespaces for code indentation
ignoreOriginal: True/False. Default:False. If set to True, we ignore the
                _original attribute of nodes (for example, nodes in a macro
                network that came from a node library where nodes are marked
                original
copyright: if True copyright and network execution code is generated. This is not needed when we copy/paster for instance.
)"""

        ed = self.getEditor()
        ed._tmpListOfSavedNodes = {} # clear this list

        # if selectedOnly is TRUE the sub-network of selected nodes and
        # connections between these nodes are saved
        lines = []
        
        if copyright is True:
            import datetime
            lNow = datetime.datetime.now().strftime("%A %d %B %Y %H:%M:%S") 
        
            lCopyright = \
"""########################################################################
#
#    Vision Network - Python source code - file generated by vision
#    %s 
#    
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner and TSRI
#   
# revision: Guillaume Vareille
#  
#########################################################################
#
# $%s$
#
# $%s$
#

"""%(lNow, "Header:", "Id:")

            lines.append(lCopyright)

            lines.append(indent + """
if __name__=='__main__':
    from sys import argv
    if '--help' in argv or '-h' in argv or '-w' in argv: # run without Vision
        withoutVision = True
        from Vision.VPE import NoGuiExec
        ed = NoGuiExec()
        from NetworkEditor.net import Network
        import os
        masterNet = Network("process-"+str(os.getpid()))
        ed.addNetwork(masterNet)
    else: # run as a stand alone application while vision is hidden
        withoutVision = False
        from Vision import launchVisionToRunNetworkAsApplication, mainLoopVisionToRunNetworkAsApplication
	if '-noSplash' in argv:
	    splash = False
	else:
	    splash = True
        masterNet = launchVisionToRunNetworkAsApplication(splash=splash)
    import os
    masterNet.filename = os.path.abspath(__file__)
"""
)

        lines.append(indent+'from traceback import print_exc\n')

#        lines.append(indent+"#### Network: "+self.name+" ####\n")
#        lines.append(indent+"#### File written by Vision ####\n\n")

        ## save code to create user panels
        for name, value in self.userPanels.items():
            #print "name, value", name, value, dir(value.frame)
            lines.append(indent+
                         "masterNet.createUserPanel('%s' ,width=%d, height=%d)\n"
                         %(name, value.frame.winfo_width(), value.frame.winfo_height() ) )

        ## add stuff that users might want to add at very beginning of network
        callbacks = self.eventHandler['saveNetworkBegin']
        txt = callbacks.CallCallbacks(indent=indent)
        for t in txt:
            lines.extend(t)
        
        ## get library import cache (called recursively)
        ## then write libray import code
        cache = {'files':[]}
        cache = self.buildLibraryImportCache(cache, self, selectedOnly)
        li = self.getLibraryImportCode(cache, indent,
                                       editor="%s.getEditor()"%networkName,
                                       importOnly=importOnly,
                                       loadHost=True)
        lines.extend(li)

        ## add node creation code
        li = self.getNodesCreationSourceCode(networkName, selectedOnly,
                                             indent, ignoreOriginal)
        lines.extend(li)

        ## add code to run individualy each node before the connections
        lines.append(indent+'#%s.run()\n'%networkName)

        ## add code to freeze network execution to avoid executing upon connection
        lines.append(indent+'%s.freeze()\n'%networkName)
        
        ## add connection creation code
        if len(self.connections):
            lines.append(
                '\n'+indent+"## saving connections for network "+\
                "%s ##\n"%self.name)
            for i,conn in enumerate(self.connections): 
                lines.extend(conn.getSourceCode(
                    networkName, selectedOnly, indent, ignoreOriginal,
                    connName='conn%d'%i))

        ## add code to set correctly runOnNewData
        lines.append(indent+'%s.runOnNewData.value = %s\n'%(networkName,self.runOnNewData.value))

        ## allow to add code after connections were formed (connections
        ## might generate new ports, for example -> see MacroOutputNode).
        for node in self.nodes:
            if selectedOnly:
                if not node.selected:
                    continue
            lines.extend(node.getAfterConnectionsSourceCode(
                networkName, indent, ignoreOriginal) )
                         
            
        ## add stuff that users might want to add at very end of network
        callbacks = self.eventHandler['saveNetworkEnd']
        txt = callbacks.CallCallbacks(indent=indent)
        for t in txt:
            lines.extend(t)

        for lNodeName, lNode in ed._tmpListOfSavedNodes.items():
            #print "_tmpListOfSavedNodes", lNodeName, lNode
            if hasattr(lNode, 'vi'):
                lines.extend('\n\ndef loadSavedStates_%s(self=%s, event=None):\n'%(lNodeName, lNodeName) )    
                txt = lNode.vi.getObjectsStateDefinitionCode(
                                    viewerName='self.vi', 
                                    indent='    ',
                                    withMode=False,
                                    includeBinding=False)
                lines.extend(txt)
                txt = lNode.vi.getViewerStateDefinitionCode(
                                    viewerName='self.vi', 
                                    indent='    ',
                                    withMode=False,
                                    rootxy=False)
                lines.extend(txt)
                
                if lNode.__module__ == 'DejaVu.VisionInterface.DejaVuNodes':                
                    lines.extend('%s.restoreStates_cb = %s.restoreStatesFirstRun = loadSavedStates_%s\n'%(lNodeName, lNodeName, lNodeName) )    
                else: # 'Pmv.VisionInterface.PmvNodes':                
                    lines.extend('%s.restoreStates_cb = %s.restoreStatesFirstRun = loadSavedStates_%s\n'%(lNodeName, lNodeName, lNodeName) )    
                    #lines.extend('%s.restoreStates_cb = loadSavedStates_%s\n'%(lNodeName, lNodeName) )    
                lines.extend('%s.menu.add_separator()\n'%lNodeName )    
                lines.extend("%s.menu.add_command(label='Restore states', command=%s.restoreStates_cb)\n"%(lNodeName, lNodeName) )    
        
        # finally, clear the list
        ed._tmpListOfSavedNodes = {}

        if copyright is True:
            lines += """
if __name__=='__main__':
    from sys import argv
    lNodePortValues = []
    if (len(argv) > 1) and argv[1].startswith('-'):
        lArgIndex = 2
    else:
        lArgIndex = 1
    while lArgIndex < len(argv) and argv[lArgIndex][-3:]!='.py':
        lNodePortValues.append(argv[lArgIndex])
        lArgIndex += 1
    masterNet.setNodePortValues(lNodePortValues)
    if '--help' in argv or '-h' in argv: # show help
        masterNet.helpForNetworkAsApplication()
    elif '-w' in argv: # run without Vision and exit
         # create communicator
        from NetworkEditor.net import Communicator
        masterNet.communicator = Communicator(masterNet)
        print 'Communicator listening on port:', masterNet.communicator.port

        import socket
        f = open(argv[0]+'.sock', 'w')
        f.write("%s %i"%(socket.gethostbyname(socket.gethostname()),
                         masterNet.communicator.port))
        f.close()

        masterNet.run()

    else: # stand alone application while vision is hidden
        if '-e' in argv: # run and exit
            masterNet.run()
        elif '-r' in argv or len(masterNet.userPanels) == 0: # no user panel => run
            masterNet.run()
            mainLoopVisionToRunNetworkAsApplication(masterNet.editor)
        else: # user panel
            mainLoopVisionToRunNetworkAsApplication(masterNet.editor)

"""

        return lines


    ##
    ## functions used to run networks as programs
    ##

    def helpForNetworkAsApplication(self):
        help_msg = """Run the network without displaying the Vision network editor.
    (If there is a User panel the network will just load and not run)

        usage: %s <option>

    -r : run (force run if user panels are present)
    -e : run and exit the Python interpreter after running
    -w : run without GUI and exit (will fail if the network has a user panel or creates GUI)
    -h : print this message and list of settable command line parameters

    Setting parameters: parameters can be set using the following syntax
                        nodeName:portName:value

    example: ./mynetwork.py range:toInd:7
             ./mynetwork.py "Entry:entry:'my string'"

The following nodes and ports exist in this network:
""" % sys.argv[0]
        print help_msg
        lNodeDict = {}
        for node in self.nodes:
           lNodeDict[node.name] = node
        self.listInputPorts(lNodeDict)


    def setNodePortValues(self, nodePortValueList):
        #print "setNodePortValues"
        if len(nodePortValueList) != 0:
           lNodeDict = {}
           for node in self.nodes:
               lNodeDict[node.name] = node

           # handle space in node and port names
           portValues = []
           i = 0
           while i<len(nodePortValueList):
               value = nodePortValueList[i]
               while value.count(':') < 2:
                   i+=1
                   value += ' '
                   value += nodePortValueList[i]
               portValues.append(value)
               i += 1

           for lNodePortValue in portValues:
               #print 'AAAAAAAAAAAAAAA', lNodePortValue
               nodeName, portName, value = lNodePortValue.split(':')
               #print 'BBBBBBBBBB', nodeName, portName, value
               ip = lNodeDict[nodeName].getInputPortByName(portName)
               ip.widget.set(eval(value), run=False)


    def buildNodeDict(self, mod):
        nodeDict = {}
        from NetworkEditor.items import NetworkNode
        for name, object in mod.items():
            if isinstance(object, NetworkNode):
                nodeDict[name] = object
        return nodeDict


    def listInputPorts(self, nodeDict):
        for k,v in nodeDict.items():
            print k
            for port in v.inputPorts:
                print "\t", port.name,
                if port.widget:
                    print '\t', port.widget.get()
                else:
                    print
    ##
    ## End functions used to run networks as programs
    ##


    def buildLibraryImportCache(self, cache, network, selectedOnly=False):
        """Loop recursively (if macro nodes are present) over all nodes and
        build a dictionary containing the libraries needed to save a network"""
        
        from macros import MacroNode, MacroInputNode, MacroOutputNode
        for n in network.nodes:

            if selectedOnly:
                if not n.selected:
                    continue

            if isinstance(n, MacroInputNode) or isinstance(n, MacroOutputNode):
                continue

            if isinstance(n, MacroNode): # loop recursively over nodes in macro
                cache = self.buildLibraryImportCache(
                    cache, n.macroNetwork, selectedOnly=False)

                # Note: selectedOnly=False, because we want all nodes inside
                # the macro network
            
            if n.library is not None:
##                 if False: # FIXME: WE DO NOT NEED TO DO THIS ANTYMORE!!
##                 #if n.library.file:
##                     cache['files'].append( (n.library.varName,
##                                             n.library.modName,
##                                             n.library.file) )
##                 else:
                cache[n.library.varName] = n.library.modName
            else:
                pass # Hmmmm? What else could we do here?

            if n.constrkw.has_key('host') is True:
                if cache.has_key('hosts') is False:
                    cache['hosts'] = {}
                cache['hosts'].update({n.constrkw['host']:None})

        return cache
   

    def getLibraryImportCode(self, cache, indent,
                             editor='masterNet.getEditor()',
                             networkName='masterNet',
                             importOnly=False,
                             loadHost=False):

        """Returns code to import libraries.
if importOnly=True, only the import statement is generated. If
importOnly=False (Default), both import statement and adding to library
code is generated
loadHost: allows loading of the webserver host as category
"""

        lines = []
        if importOnly is False:
            lines.append(indent+"## loading libraries ##\n")

        # import code for all libraries
        for k, v in cache.items():
            if k == 'files':
                for var, mod, file in v:
                    l = "from mglutil.util.packageFilePath import "+\
                        "getObjectFromFile\n"
                    lines.append(indent+l)
                    lines.append(indent+\
                                 "%s = getObjectFromFile( '%s', '%s')\n"%(
                                     var, file, var))
            elif k != 'hosts' and v is not None:
                lines.append( indent+"from " + v +" import " + k + "\n")

        # code to add library to the editor
        if importOnly is False:
            lines.append(indent+"try:\n"+indent+'    ' + networkName + '\n')
            lines.append(indent+"except (NameError, AttributeError): # we run the network outside Vision\n")
            indent1 = indent+"    "
            lines.append(indent1 + "from NetworkEditor.net import Network\n")
            lines.append(indent1 + networkName + " = Network()\n\n")

            #lines.append(indent+"if __name__!='__main__' or withoutVision is False:\n")
            #lines.append(indent1+"pass\n")
            addlib = indent+editor+'.addLibraryInstance('
            for k, v in cache.items():
                if k == 'files':
                    for var, mod, file in v:
                        lines.append(
                            indent+addlib+'%s, "%s", "%s", "%s")\n\n'%(
                            var, mod, var, file) )
                elif k != 'hosts':
                    lines.append(indent+addlib+'%s,"%s", "%s")\n\n'%(k, v, k) )
        elif loadHost is True:
            if cache.has_key('hosts'):
                lines.append(indent+networkName+'.getEditor().addLibraryInstance(wslib,"WebServices.VisionInterface.WSNodes", "wslib")\n')

        if importOnly is False or loadHost is True:
            if cache.has_key('hosts'):
                lines.append(indent+'from WebServices.VisionInterface.WSNodes import addOpalServerAsCategory\n')
                for host in cache['hosts'].keys():
                    lines.append(indent+'try:\n')
                    lines.append(indent+"    addOpalServerAsCategory("+host+", replace=False)\n")
                    lines.append(indent+'except:\n')
                    lines.append(indent+'    pass\n')

        return lines


    def getNodesCreationSourceCode(self, networkName, selectedOnly=0,
                                   indent="", ignoreOriginal=False):
        """build a string representation of this network
"""
        lines = []
        for n in self.nodes:
            if selectedOnly:
                if not n.selected:
                    continue
            ## add code that describes nodes
            indent2 = indent + ' '*4
            txt = n.getNodeDefinitionSourceCode(networkName, indent=indent2,
                                                ignoreOriginal=ignoreOriginal)
            if len(txt) > 0:
                ## place node creation code inside try:
                lines.append(indent+'try:\n')
                nodeName = n.getUniqueNodeName()
                n.nameInlastSavedNetwork = nodeName
                lines.append(indent2+"## saving node %s ##\n"%n.name)
                lines.extend(txt)
                ## except part of try
                lines.append(indent+'except:\n')
                msg = 'failed to restore %s named %s in network %s'%(
                    n.__class__.__name__, n.name, networkName)
                lines.append(indent2+'print "WARNING: '+msg+'"\n')
                lines.append(indent2+'print_exc()\n')
                lines.append(indent2+'%s=None\n'%nodeName)
                lines.append('\n')
        return lines


    def getNodes(self, nodesIds):
        """return a list of nodes corresponding to canvasIds"""
        nodes = []
        nodekeys = self.nodesById.keys()
        for n in nodesIds:
            if n in nodekeys:
                nodes.append(self.nodesById[n])
        return nodes


    def getNodesConnsPorts(self, nodesIds):
        """find out what objects correspond to a list of canvasIds
        this method is called by self.pickedItems()"""
        
        nodes = []
        conns = []
        inports = []
        outports = []
        nodekeys = self.nodesById.keys()
        connkeys = self.connById.keys()
        inportkeys = self.inPortsId.keys()
        outportkeys = self.outPortsId.keys()
        for n in nodesIds:
            if n in nodekeys:
                nodes.append(self.nodesById[n])
            elif n in connkeys:
                conns.append(self.connById[n])
            elif n in inportkeys:
                inports.append(self.inPortsId[n])
            elif n in outportkeys:
                outports.append(self.outPortsId[n])
        return nodes, conns, inports, outports
        

    def getConnections(self, nodes):
        """[2Connection], [1Connections], [1nodes] <- getConnections(nodes)
returns 3 lists:
   a list of connections having both nodes in the set
   a list of connections having only 1 node in the set
   the list of nodes connected to a node outside the set
"""
        #print "Network.getConnections"
        nodes = self.expandNodes(nodes)
        conn = []
        for n in nodes:
            n.inset__ = 1
            conn.extend( n.getConnections() )

        twoNodes = [] # connections with 2 nodes in set
        oneNode = []  # connections with only 1 node in set
        no1 = {}      # nodes connected to node outside set
        for c in conn:
            a = hasattr(c.port1.node, 'inset__')
            b = hasattr(c.port2.node, 'inset__')
            if a + b == 1 :
                oneNode.append(c)
                if a: no1[c.port1.node] = None
                if b: no1[c.port2.node] = None
            else:
                twoNodes.append(c)
        for n in nodes:
            delattr(n, 'inset__')
        return twoNodes, oneNode, no1.keys()


    def getNodesAndInputPort(self, nodesIds):
        nodes = []
        portkeys = self.inPortsId.keys()
        for n in nodesIds:
            if n in portkeys:
                nodes.append(self.inPortsId[n])
        return nodes
    

    def getNodesAndOutputPort(self, nodesIds):
        nodes = []
        portkeys = self.outPortsId.keys()
        for n in nodesIds:
            if n in portkeys:
                nodes.append(self.outPortsId[n])
        return nodes
    

    def getNodesAndConnections(self, nodesIds):
        nodes = []
        conn = []
        nodekeys = self.nodesById.keys()
        connkeys = self.connById.keys()
        for n in nodesIds:
            if n in nodekeys:
                nodes.append(self.nodesById[n])
            elif n in connkeys:
                conn.append(self.connById[n])
        return nodes, conn


    def pickedItems(self, event):
        """find out what has been picked"""
        x0 = self.canvas.canvasx(event.x)-5
        y0 = self.canvas.canvasy(event.y)-5
        items = self.canvas.find_overlapping(x0, y0, x0+5, y0+5)
        return self.getNodesConnsPorts(items)


##
## Callback functions for mouse buttons click and double clicking
##
    def mouse1Up(self, event=None):
        self.mouseButtonFlag = self.mouseButtonFlag & ~event.num

        
    def mouse2Up(self, event=None):
        self.mouseButtonFlag = self.mouseButtonFlag & ~event.num


    def mouse1Down(self, event=None, nbClick=1):
        if self.postedMenu:
            self.postedMenu.unpost()
            self.postedMenu = None

	self.origx = self.lastx = self.canvas.canvasx(event.x)
	self.origy = self.lasty = self.canvas.canvasy(event.y)
        self.hasMoved = 0

        mod = self.getModifier()
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag | num

        if nbClick == 1: nbc=''
        elif nbClick == 2: nbc='Double-'
        
        if mod=='None': eventName = '<'+nbc+'Button-'+str(num)+'>'
        else: eventName = '<'+nbc+mod[:-2]+'-Button-'+str(num)+'>'

        # find out what is under the mouse
        nodes, conn, inPorts, outPorts = self.pickedItems(event)
        
        if len(outPorts):
            f = outPorts[0].mouseAction[eventName]
            if f: f(event)
        elif len(inPorts):
            f = inPorts[0].mouseAction[eventName]
            if f: f(event)
        elif len(nodes):
            f = nodes[0].mouseAction[eventName]
            if f: f(event)
        elif len(conn):
            f = conn[0].mouseAction[eventName]
            if f: f(event)
        else: # draw selection box
            f = self.mouseAction[eventName]
            if f: f(event)

    def mouse2Down(self, event=None):
        self.mouse1Down(event, 2)
    

#
#  Functions bound to mouse actions
#
    def startDrawingSelectionBox(self, event):
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag & ~num

        if hasattr(self,"glyph"):
            if self.glyph != 1:
                self.canvas.bind("<ButtonRelease-%d>"%num, self.selectionBoxEnd)
                self.canvas.bind("<B%d-Motion>"%num, self.selectionBoxMotion)
            else:
                    #if self.glyphshape == "circle" or "rectangle":
                        self.canvas.bind("<ButtonPress-%d>"%num,self.glyphSelectionPress)
                        self.canvas.bind("<B%d-Motion>"%num, self.drawGlyphSelectionBox)
                        self.canvas.bind("<ButtonRelease-%d>"%num, self.glyphselectionBoxEnd)
                        self.canvas.bind("<Key>", self.handleKey)
                
        else:
            self.canvas.bind("<ButtonRelease-%d>"%num, self.selectionBoxEnd)
            self.canvas.bind("<B%d-Motion>"%num, self.selectionBoxMotion)


    def glyphSelectionPress(self,event):
        canvas = self.canvas
        self.glyphScale = 0
        self.origx = canvas.canvasx(event.x)
        self.origy= canvas.canvasy(event.y)
        self.sbrev = 0
        self._drag = 0
        if self.gselectionboxes!=[]:
               if self.glyphKeywords['spray']==True:
                    canvas.itemconfigure(CURRENT,{'fill':self.glyphKeywords['fill']})
               if canvas.type(CURRENT) == "rectangle":
                   tags = canvas.gettags(CURRENT)
                   if "sb1" in tags:
                      self.sbrev = 1
                      id = canvas.find_withtag("sb2") 
                      self.x1 = canvas.coords(id)[0]+2
                      self.y1 = canvas.coords(id)[1]+2
                   if "sb2" in tags:
                     id = canvas.find_withtag("sb1")      
                     self.x1 = canvas.coords(id)[0]+2
                     self.y1 = canvas.coords(id)[1]+2
                   if "sb3" in tags:
                      self.sbrev = 1
                      id2 = canvas.find_withtag("sb2") 
                      id1 = canvas.find_withtag("sb1") 
                      self.x1 = canvas.coords(id2)[0]+2
                      self.y1 = canvas.coords(id1)[1]+2
                   if "sb4" in tags:
                      self.sbrev = 1
                      id2 = canvas.find_withtag("sb2") 
                      id1 = canvas.find_withtag("sb1")
                      self.x1 = canvas.coords(id1)[0]+2
                      self.y1 = canvas.coords(id2)[1]+2
                   if self.glyphshape == "circle":
                        if self.currentcircle: 
                            #items = canvas.find_enclosed(self.x1,self.y1,event.x,event.y) 
                            #for it in items:
                            #    if it == self.currentcircle:
                                    canvas.delete(self.currentcircle)
                                    self.currentcircle = None
                   if self.glyphshape == "rectangle":
                        if self.currentrectangle: 
                            #items = canvas.find_enclosed(self.x1,self.y1,event.x,event.y) 
                            #for it in items:
                            #    if it == self.currentrectangle:
                                    canvas.delete(self.currentrectangle) 
                                    self.currentrectangle = None


    def drawGlyphSelectionBox(self, event): 
         self._drag =1
         canvas = self.canvas
         x = canvas.canvasx(event.x)
         y = canvas.canvasy(event.y)
         if not hasattr(self,"x1"):
                x1 = self.origx
                y1 = self.origy
         else:
            x1 =self.x1
            y1 = self.y1

         if self.circle: canvas.delete(self.circle)
         if self.rectangle: canvas.delete(self.rectangle) 
         if self.glyphselectionBox:
             canvas.delete(self.glyphselectionBox)
         if self.gselectionboxes!=[]:
               for g in self.gselectionboxes:
                   canvas.delete(g)
                   self.gselectionboxes=[]
         # check if the mouse moved only a few pixels. If we are below a
         # threshold we assume we did not move. This is usefull for deselecting
         # nodes for people who don't have a steady hand (who move the mouse
         # when releasing the mouse button, or when the mouse pad is very soft
         # and the  mouse moves because it is pressed in the pad...)
         if abs(x1-x) < 10 or abs(y1-y) < 10:
            self.hasMoved = 0
         else:
            self.hasMoved = 1
            if self.sbrev ==1:
                self.glyphselectionBox = canvas.create_rectangle(x, y,
                                                    x1, y1, dash
                                                    =(4,6),width=2,outline="magenta")
                self.glyphselectionBox_bbox =  canvas.bbox(self.glyphselectionBox)
                if hasattr(self,"glyph"):
                    if self.glyph ==1:
                        if self.glyphshape == "circle":
                            bbox = [x, y,x1, y1]
                            self.circle = self.editor.addCircle(bbox=bbox)
                        elif self.glyphshape == "rectangle":
                            self.rectangle = self.editor.addRectangle(bbox=[x, y,x1, y1])
            if self.sbrev ==3:
                self.glyphselectionBox = canvas.create_rectangle(x1, y,x, y1, dash
                                                    =(4,6),width=2,outline="magenta")
                self.glyphselectionBox_bbox =  canvas.bbox(self.glyphselectionBox)
                if hasattr(self,"glyph"):
                    if self.glyph ==1:
                        if self.glyphshape == "circle":
                            bbox = [x1, y,x1, y]
                            self.circle = self.editor.addCircle(bbox=bbox)
                        elif self.glyphshape == "rectangle":
                            self.rectangle = self.editor.addRectangle(bbox=[x, y1,x1, y])
            if self.sbrev ==2:
                self.glyphselectionBox = canvas.create_rectangle(x, y1,
                                                    x1, y, dash
                                                    =(4,6),width=2,outline="magenta")
                self.glyphselectionBox_bbox =  canvas.bbox(self.glyphselectionBox)
                if hasattr(self,"glyph"):
                    if self.glyph ==1:
                        if self.glyphshape == "circle":
                            bbox = [x, y1,x, y1]
                            self.circle = self.editor.addCircle(bbox=bbox)
                        elif self.glyphshape == "rectangle":
                            self.rectangle = self.editor.addRectangle(bbox=[x1, y,x, y1])
            if self.sbrev ==0:
                self.glyphselectionBox = canvas.create_rectangle(x1, y1,
                                                    x, y, dash
                                                    =(4,6),width=2,outline="magenta")

                self.glyphselectionBox_bbox =  canvas.bbox(self.glyphselectionBox)
                if hasattr(self,"glyph"):
                    if self.glyph ==1:
                        if self.glyphshape == "circle":
                            bbox = [x1, y1,x, y]
                            self.circle = self.editor.addCircle(bbox=bbox)
                        elif self.glyphshape == "rectangle":
                            self.rectangle = self.editor.addRectangle(bbox=[x1, y1,x, y]) 
                        #else:
                        #    #scale
                            #if self.glyphselectionBox:
                            #    coords = canvas.coords(self.glyphselectionBox)
                            #    items= canvas.find_enclosed(coords[0],coords[1],coords[2],coords[3])
                            #    for i in items:
                            #        canvas.scale(i, coords[0],coords[1], 1.2, 1.2)
                                 


    # function to draw the box
    def selectionBoxMotion(self, event):
        self.drawSelectionBox(event)
        

    # call back for motion events
    def drawSelectionBox(self, event):
        canvas = self.canvas
        if self.selectionBox: canvas.delete(self.selectionBox)
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        # check if the mouse moved only a few pixels. If we are below a
        # threshold we assume we did not move. This is usefull for deselecting
        # nodes for people who don't have a steady hand (who move the mouse
        # when releasing the mouse button, or when the mouse pad is very soft
        # and the  mouse moves because it is pressed in the pad...)
        if abs(self.origx-x) < 10 or abs(self.origy-y) < 10:
            self.hasMoved = 0
        else:
            self.hasMoved = 1
            self.selectionBox = canvas.create_rectangle(self.origx, self.origy,
                                                    x, y, outline='red')
            self.selectionBox_bbox =  canvas.bbox(self.selectionBox)


    def glyphselectionBoxEnd(self, event):
        canvas = self.canvas
        if self._drag ==0:
           self.undrawSelectionCorners()
           coords = canvas.coords(CURRENT)                
           self.drawSelectionCorners(coords)
           shape = canvas.type(CURRENT)        
           items = canvas.find_all()

           for it in items:
                if canvas.coords(CURRENT) == canvas.coords(it):
                      if shape == "oval":  
                        self.currentcircle = it
                        self.glyphshape = "circle"
                      elif shape == "rectangle":
                        self.currentrectangle = it
                        self.glyphshape = "rectangle"
                      elif shape == "text":
                        self.setCursor(event)
        else:
            if self.glyphshape =="text":
                self.set_focus(event)

            else:    

                if hasattr(self ,"x1"):
                    delattr(self,"x1")
                    delattr(self,"y1")

                x = canvas.canvasx(event.x)
                y = canvas.canvasy(event.y)
                if hasattr(self,"glyphKeywords"):
                    if self.glyphKeywords.has_key("fill"):
                        fillcolor = self.glyphKeywords['fill']

                    if self.glyphKeywords.has_key("outline"):
                        outlinecolor = self.glyphKeywords['outline']
                if self.circle:
                    coords =canvas.coords(self.circle)
                    canvas.delete(self.circle)

                    self.currentcircle = self.editor.addCircle(bbox=coords,fill = fillcolor,outline = outlinecolor,anchor=None )
                    if self.gselectionboxes == []:
                        self.drawSelectionCorners(coords)
                    self.circle = None            
                elif self.rectangle:
                    coords =canvas.coords(self.rectangle)
                    canvas.delete(self.rectangle)

                    self.currentrectangle = self.editor.addRectangle(bbox = coords,fill = fillcolor,outline = outlinecolor)
                    if self.gselectionboxes == []:
                        self.drawSelectionCorners(coords)
                    self.rectangle =  None   
                if self.glyphselectionBox : 
                    coords = canvas.coords( self.glyphselectionBox)
                    if len(coords) == 4 :
                        items = canvas.find_enclosed(coords[0],coords[1],coords[2],coords[3])
                        if self.gselectionboxes == [] :
                                self.drawSelectionCorners(coords)
                        canvas.delete(self.glyphselectionBox)


    def undrawSelectionCorners(self):
        canvas = self.canvas
        if self.gselectionboxes!=[]:
            for g in self.gselectionboxes:
                canvas.delete(g)
            self.gselectionboxes =[]


    def drawSelectionCorners(self,coords):
        canvas = self.canvas
        if len(coords)!=4:
            return
        four_corners = [[coords[0]-4,coords[1]-4, coords[0]+4, coords[1]+4],[coords[2]-4, coords[3]-4,coords[2]+4,coords[3]+4],[coords[0]-4,coords[3]-4, coords[0]+4, coords[3]+4],[coords[2]-4, coords[1]-4,coords[2]+4, coords[1]+4],]
        i =1
        for fc in four_corners:
             gselectbox = canvas.create_rectangle(fc[0],fc[1],fc[2],fc[3],fill="green",tags=("sb"+"%d" %i,))
             self.gselectionboxes.append(gselectbox)    
             i = i+1


    # callback for ending command
    def selectionBoxEnd(self, event):
        
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag & ~num
        canvas = self.canvas
  	canvas.unbind("<B%d-Motion>"%num)
	canvas.unbind("<ButtonRelease-%d>"%num)
        if not self.hasMoved:
            self.clearSelection()
        else:
            if self.selectionBox:
                canvas.delete(self.selectionBox)
            nodesIds = canvas.find_enclosed( self.origx, self.origy,
                          canvas.canvasx(event.x), canvas.canvasy(event.y) )
            nodes = self.getNodes(nodesIds)

            if len(nodes):
                if self.isShift():
                    self.selectNodes(nodes)
                elif self.isControl():
                    self.deselectNodes(nodes)
                else:
                    self.toggleSelection(nodes)

    ##
    ## move canvas
    ##
    def moveCanvasStart(self, event=None):
        num = event.num
        self.lastx = event.x
        self.lasty = event.y
        self.mouseButtonFlag = self.mouseButtonFlag | num
        canvas = self.canvas
        canvas.bind("<B%d-Motion>"%num, self.moveCanvas)
        canvas.bind("<ButtonRelease-%d>"%num, self.moveCanvasEnd)
        canvas.configure(cursor='hand2')


    def moveCanvas(self, event=None):
        ed = self.getEditor()
        dx = event.x - self.lastx
        dy = event.y - self.lasty
        canvas = self.canvas
        xo = max(0, canvas.canvasx(0)-dx)
        yo = max(0, canvas.canvasy(0)-dy)

        canvas.xview_moveto(xo/float(ed.totalWidth))
        canvas.yview_moveto(yo/float(ed.totalHeight))
	self.lastx = event.x
        self.lasty = event.y
        self.canvas.update_idletasks()
    
    
    def moveCanvasEnd(self, event=None):
        num = event.num
        canvas = self.canvas
        canvas.unbind("<B%d-Motion>"%num)
        canvas.unbind("<ButtonRelease-%d>"%num)
        canvas.configure(cursor='')


    def moveCanvasOrSelectedNodes(self, event=None):
        if len(self.selectedNodes) > 0:
            self.moveSelectedNodesStart(event)
        else:
            self.moveCanvasStart(event)


    ##
    ## move selected nodes
    ## if nodes are moved outside the canvas to the left or above they are
    ## deleted.
    def moveSelectedNodesStart(self, event):
        num = event.num
        self.lastx = self.origx = event.x
        self.lasty = self.origy = event.y
        self.mouseButtonFlag = self.mouseButtonFlag | num
        if hasattr(self,"glyph"):   
          if self.glyph==1:
            if self.glyphshape == "text" or "circle" or "rectangle":
                if hasattr(self,"oldx"):
                    delattr(self,"oldx")
                    delattr(self,"oldy")
                self.canvas.bind("<B%d-Motion>"%num, self.moveObject)
            return
        self.canvas.bind("<B%d-Motion>"%num, self.moveSelectedNodes)
        self.canvas.bind("<ButtonRelease-%d>"%num, self.moveSelectedNodesEnd)
        co2, co1, no1 = self.getConnections(self.selectedNodes)
        self.halfSelConn = co1 # connections with only 1 node selected
        self.hasMoved = 0


    def moveSelectedNodes(self, event=None):
        canvas = self.canvas
        dx = event.x - self.lastx
        dy = event.y - self.lasty            
        canvas.move('selected', dx, dy)
            
        for c in self.halfSelConn:
            c.updatePosition()

	self.lastx = event.x
	self.lasty = event.y
        canvas.update_idletasks()
        self.hasMoved = 1

 
    def moveSelectedNodesEnd(self, event=None):
        ed = self.getEditor()
        canvas = self.canvas
#        endx = ed.visibleWidth+10
#        endy = ed.visibleHeight+10
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
# not working        
#        if x < -10 or y < -10 or x > endx or y > endy:
#            self.deleteNodes(self.selectedNodes)

        self.mouseButtonFlag = self.mouseButtonFlag & ~event.num

        # setup undo
        dx = self.origx - event.x
        dy = self.origy - event.y
        nodeNames = self.objectsAsString(self.selectedNodes)
        undoCmd = 'self.moveSubGraph("%s", %d, %d)\n'%(nodeNames, dx, dy)
        ed.setupUndo(undoCmd, 'moveSubGraph')
        for n in self.selectedNodes:
            # we have moved and have to set node.posx and node.posy
            n.updatePosXPosY()

        # tag all nodes that have moved
        for node in self.selectedNodes:
            node.hasMoved = True
            node._setModified(True)
        

    def scale(self, xscale, yscale=None, xo=0, yo=0):
        """Scale the network"""

        ed = self.getEditor()
        if len(self.nodes) == 0:
            return
        if xscale < 0.01:
            return
        if not yscale:
            yscale = xscale
        canvas = self.canvas
        canvas.scale('selected', xo, yo, xscale, yscale)

        # scale the font
        # find out what is the current font of any given node
        node = self.nodes[0]
        font = ed.font['Nodes']
        ft = font[0]
        sz = font[1]
        styl = font[2]

        for n in self.selectedNodes:
            sca = n.scaleSum*self.scaleSum
            size = max(4, int ( round( sz - (sz-2) + sca*(sz-2)) ) )
            if size < 5:
                for n in self.selectedNodes:
                    canvas.itemconfigure(n.textId, text='')
            else:
                font = ( ft, size, styl )
                canvas.itemconfigure(n.textId, text=n.name, font=font)

#  attempt to scale widgets in nodes .. not working well
            # show/hide widgets in node
            widgetsInNode = n.getWidgetsForMaster('Node')
            if len(widgetsInNode):
                if sca < 0.9: # hide widgets in node
                    if n.isExpanded() and not n.widgetsHiddenForScale:
                        n.hideInNodeWidgets()
                        n.widgetsHiddenForScale = True
                else: # show widgets in node if they are hidden due to scaling
                    
                    if n.isExpanded() and n.widgetsHiddenForScale:
                        n.widgetsHiddenForScale = False
                        n.showInNodeWidgets()
                
    def scaleNetworkStart(self, event=None):
        canvas = self.canvas
        bb = canvas.bbox('selected')
        # return if no nodes are selected
        if not bb:
            return
        
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag | num
        canvas.bind("<B%d-Motion>"%num, self.scaleNetworkMotion)
        canvas.bind("<ButtonRelease-%d>"%num, self.scaleNetworkEnd)
        self.scaleSum = 1.0
        c2, self.private_c1, no1 = self.getConnections(self.selectedNodes)

        self.private_xo, self.private_yo = (bb[0]+bb[2])/2, (bb[1]+bb[3])/2
        
        
    def scaleNetworkMotion(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        dx = x - self.lastx
        dy = y - self.lasty
        if math.fabs(dx) > math.fabs(dy): sca = 1.+dx*0.01
        else: sca = 1.+dy*0.01
        self.scaleSum = self.scaleSum*sca
        self.scale(sca, sca, self.private_xo, self.private_yo)
 	self.lastx = x
	self.lasty = y
        for c in self.private_c1:
            c.updatePosition()


    def scaleNetworkEnd(self, event):
        del self.private_c1
        del self.private_xo
        del self.private_yo
        
        for p in self.inPortsId.values():
            if p.node.selected:
                p.relposx = round(p.relposx*self.scaleSum)
        for p in self.outPortsId.values():
            if p.node.selected:
                p.relposx = round(p.relposx*self.scaleSum)
                p.relposy = round(p.relposy*self.scaleSum)

        for n in self.selectedNodes:
            n.scaleSum = n.scaleSum * self.scaleSum

        canvas = self.canvas
        num = event.num
        canvas.unbind("<B%d-Motion>"%num)
        canvas.unbind("<ButtonRelease-%d>"%num)
        

    def resetScaleSelectedNodes(self):
        ed = self.getEditor()
        canvas = self.canvas
        c2, c1, no1 = self.getConnections(self.selectedNodes)
        font = ed.font['Nodes']

        bb = canvas.bbox('selected')
        for n in self.selectedNodes:
            sca = 1.0/n.scaleSum
            canvas.itemconfigure(n.textId, text=n.name, font=font)
            canvas.scale(n.iconTag, (bb[0]+bb[2])/2, (bb[1]+bb[3])/2,
                         sca, sca )
            n.scaleSum = 1.0
            for wn, wd in n.widgetDescr.items():
                if wd['master'] != 'node':
                    continue
                for p in n.inputPorts:
                    if p.name==wn:
                        break
                if p.widget:
                    continue
                p.createWidget(rescale=0)
        for c in c1:
            c.updatePosition()
        for c in c2:
            c.updatePosition()

            
    def scaleHyper(self, xc, yc, rad):
        # xc, yc are mouse coordinates (used to scale distance to mouse)
        rad2= rad*rad
        canvas = self.canvas
        for n in self.nodes:

            nx = n.posx
            ny = n.posy

            # scale back to original position
            sca = 1.0/n.distScaleFactor
            canvas.scale(n.iconTag, self.lastx, self.lasty, sca, sca)
            
            # scale back to original size
            sca = 1.0/n.nodeScaleFactor
            canvas.scale(n.iconTag, nx, ny, sca, sca)

            dist2 = (nx-xc)*(nx-xc) + (ny-yc)*(ny-yc)
            if dist2>rad2:
                nsca = max(float(rad2)/dist2, 0.01)
                dsca = max( (rad*math.sqrt(dist2) + 1)/dist2,  0.01)
                canvas.tag_lower(n.iconTag, self.firstItemId)
            else:
                nsca = 1.0
                dsca = 1.0
                canvas.tag_raise(n.iconTag, self.firstItemId)

            n.nodeScaleFactor = nsca
            n.distScaleFactor = dsca
            #scale node size
            canvas.scale(n.iconTag, nx, ny, nsca, nsca)
            # scale node position
            canvas.scale(n.iconTag, xc, yc, dsca, dsca)

        # maybe we should only do this after we stop moving
        for c in self.connections:
            c.updatePosition()

            
    def resetScale(self, event=None):
        canvas = self.canvas
        for n in self.nodes.values():
            sca = 1.0/n.distScaleFactor
            canvas.scale(n.iconTag, self.lastx, self.lasty, sca, sca)
            n.distScaleFactor = 1.0

            sca = 1.0/n.nodeScaleFactor
            canvas.scale(n.iconTag, n.posx, n.posy, sca, sca)
            n.nodeScaleFactor = 1.0

        # maybe we should only do this after we stop moving
        for c in self.connections:
            c.updatePosition()


    def getObjectsFromNames(self, names, objects):
        """[nodes] <- getObjectsFromNames(names)
        names can be a ';' separated list of names
        objects has to be a ssequence of objects each havinf a name attribute
        for each name in names, the first node matching the name is returned
        regular expressions are allowed
        """
        names = string.split(names, ';')
        nodes = []
        for name in names:
            reg = re.compile(name)
            nodes.extend( filter( lambda x,reg=reg: reg.match(x.name),
                                  objects ) )
        return nodes


    def objectsAsString(self, objects):
        if len(objects)==0: return ''
        str = objects[0].name
        for n in objects[1:]:
            str = str + ';' + n.name
        return str

    
    def expand(self, objects, objectList):
        if type(objects) == types.StringType:
            return self.getObjectsFromNames(objects, objectList)
        else:
            return objects

        
    def expandNodes(self, objects):
        if type(objects) == types.StringType:
            return self.getObjectsFromNames(objects, self.nodes.values())
        else:
            return objects
        

        
    def expandConnections(self, objects):
        if type(objects) == types.StringType:
            return self.getObjectsFromNames(objects, self.connections )
        else:
            return objects


    def resetNodeCache(self):
        # every time a node or connection is added or removed we run this
        # function to invalidate node's cache
        def resetCache(node):
            node.nodesToRunCache = []
        map( resetCache, self.nodes )


#
# adding/deleting network elements
#
    def addNode(self, node, posx=None, posy=None, tagModified=False, undo=1):
        """None <- addNode(node, posx, posy)
Add a node to the network. Here, the attribute _original is set to False, and
all _modified (node, ports, widgets) are reset to False.
node: has to be an instance of a NetworkNode
posx and posy: coordiantes of the center of the node expressed
    in the canva's coordinate system
tagModified: True or False. Sets the _modified flag of the node."""

        if posx is None:
            posx = 10
        if posy is None:
            posy = self.lastPosY + 30
            
        # generate unique node number (unique across all networks/macro nets)
        
        node._id = Network._nodesID
        Network._nodesID += 1
            
        if node.network:
            # MacroNodes have to be treated differently
            from macros import MacroNode
            
            # only print warning if node is not a MacroNode
            if not isinstance(node, MacroNode):
                print 'ERROR: node %s already belongs to network %s!'\
                      %(node.name, node.network.name)
            return

##         if ed is None:
##             err = 'ERROR: network %s has to be added to editor before '% \
##                 self.name
##             err += 'node %s can be added'%node.name
##             print err
##             return
        
        node.beforeAddingToNetwork(self)

        self.nodes.append(node)
        node.network = self

        ed = self.getEditor()
        node.vEditor = weakref.ref( ed )

        # condition used for node execution
        node.condition = threading.Condition(self.RunNodeLock)

        # create all outputPorts from description
        # create output ports before InputPorts because in some cases
        # inputPorts do modify outputPort. Therefore the latter have to be
        # created first (example "select Nodes" in MolKit set the type of
        # the outputport based on the default value of the type widget bound
        # to input port 1
        for kw in node.outputPortsDescr:
            kw['updateSignature'] = False # prevent recreating source code sig.
            op = apply( node.addOutputPort, (), kw )

        # create all inputPorts from description
        for kw in node.inputPortsDescr:
            kw['updateSignature'] = False # prevent recreating source code sig.
            ip = apply( node.addInputPort, (), kw )

        # create all specialPorts
        node.addSpecialPorts()

        # Nodes belonging to a MacroNetwork are instanciated
        # self.buildIcons()
        if self.canvas:
            node.buildIcons(self.canvas, posx, posy)
            self.nodesById[node.id] = node

        self.rootNodes.append(node)
        
        if ed.hasGUI:
            if ed.colorNodeByLibrary and node.library is not None:
                node.deselectOptions['fill'] = node.library.color
                node.setColor(node.library.color)

            ed.setupUndo("self.deleteNodes([self.nodes['%s']])"%\
                         node.id, "AddNode")

            # update posx and posy
            node.updatePosXPosY()
        
        if self.needsResetNodeCache:
            self.resetNodeCache()

        # add node's docstring to node in network
        if ed.hasGUI:
            ed.balloons.tagbind(node.network.canvas, node.iconTag, node.__class__.__doc__)

        node.afterAddingToNetwork()

        from NetworkEditor.macros import MacroNode, MacroInputNode
        if self.runOnNewData.value is True and len(node.inputPorts)==0 \
          and not isinstance(node, MacroNode) \
          and not isinstance(node, MacroInputNode):
            node.run(force=1)

        # reset all _modified events in node, ports, widgets to False
        # and reset all _original events in node, ports, widgets to True
        node.resetTags()

        # FIXME: Do we really need this?
        if tagModified is True:
            node._setModified(True)

        # adding node to a network changes the _original attribute
        # this is used to save nodes properly
        node._setOriginal(False)

        # tag network modified
        self._setModified(True)

        # create an Add node Event
        ed.dispatchEvent( AddNodeEvent(self, node, posx, posy))


    def connectNodes(self, node1, node2, portNode1=0, portNode2=0,
                     mode='angles', name=None,
                     blocking=True, undo=1, 
                     doNotSchedule=False, 
                     doNotCb=False, 
                     **kw):
        """NetworkConnection <- connectNodes(node1, node2, portNode1=1, portNode2=0, mode='angles', name='NoName', blocking=True, undo=1, **kw)
create a networkConnection object that connects these 2 nodes
if doNotSchedule is True, ScheduleNode() is not called, 
if doNotCb is True,  the callbacks afterConnect and beforeConnect ain't called
"""

##         ed = self.getEditor()
##         if ed is None:
##             print 'ERROR: network %d has to be added to editor before nodes can be connected', self.name
##             return

        nodes = self.expandNodes([node1, node2])
        node1 = nodes[0]
        node2 = nodes[1]
        assert isinstance(node1, NetworkNodeBase)
        assert isinstance(node2, NetworkNodeBase)

        if type(portNode2) is types.StringType:
            ip = node2.inputPortByName[portNode2]
            if ip is None:
                return
        else:
            ip = node2.inputPorts[portNode2]

        if ip.singleConnection is True and len(ip.parents) > 0:
            err = """ERROR: port %s is a singleConnection port.
It can only have one parent node"""%ip.name
            return
        
        if node2.isRootNode and blocking is True:
            self.rootNodes.remove(node2)
            node2.isRootNode = 0

        if type(portNode1) is types.StringType:
            op = node1.outputPortByName[portNode1]
            if op is None:
                return
        else:
            op = node1.outputPorts[portNode1]

        # call "before connect" callbacks
        # output port first, then input port
        for p in [op, ip]:
            callback = p.callbacks['beforeConnect'][0]
            if callback is not None:
                callback(p, op, ip)
        #node1.beforeConnect(op, ip)
        #node2.beforeConnect(op, ip)
        
        from macros import MacroInputNode, MacroOutputNode
        # prevent connecting a macroinput node to a macrooutput node
        if isinstance(node1, MacroInputNode) and \
           isinstance(node2, MacroOutputNode):
            return

        portNum1 = op.number
        portNum2 = ip.number
        if isinstance(node1, MacroInputNode) and portNum1==0:
            # add an input port to the macro node
            macroNode = node1.macroNode
            pdescr = node2.inputPortsDescr[portNum2]

            # create unique port names
            name = node2.name+'_'+pdescr['name']
            for ipp in macroNode.inputPortsDescr:
                if ipp['name'] == name:
                    name = name + '_%d'%len(node1.outputPorts)

            ipdescr = pdescr.copy()
            ipdescr['name'] = name

            # to avoid multiple list enclosure, input port macro node 
            # must always be singleConnection.
            # to have multiple connections, 
            # the solution is to duplicate the input port in the macronode
            ipdescr['singleConnection'] = True
            
            # remove before/after connect/disconnect callbacks for these
            # newly ports, else we call them also on these ports which we
            # dont want
            dummy = ipdescr.pop('beforeConnect',None)
            dummy = ipdescr.pop('afterConnect',None)
            dummy = ipdescr.pop('beforeDisconnect',None)
            dummy = ipdescr.pop('afterDisconnect',None)

            # create input ports on MacroNode
            macroNode.inputPortsDescr.append(ipdescr)
            p2 = apply( macroNode.addInputPort, (), ipdescr )
            p2._newdata = 1

            codeAfterDisconnect="""def afterDisconnect(self, port1, port2):
    macni = port1.node
    # remove ports:
    macroNode = macni.macroNode
    # the connection from port1 to port2 was already deleted. Now
    # we will also delete the port icons, but only if no other connections
    # to port1 are present
    for p in macroNode.inputPorts:
        if p.number == (port1.number-1) and len(port1.connections) == 0:
            macroNode.network.deleteConnections(p.connections)
            #remove inputPort in MacroNode
            macroNode.deletePort(p)
    # remove outputPort in MacroInputNode if no connections left
    if len(port1.connections) == 0:
        macni.deletePort(port1)

    for c in macni.getOutConnections():
        c.updatePosition()
"""            

            # create output port on MacroInputNode
            opdescr = { 'name':ipdescr['name'],
                        'datatype':ipdescr.get('datatype','None'),
                        'afterDisconnect':codeAfterDisconnect}

            node1.outputPortsDescr.append( opdescr )
            p1 = apply( node1.addOutputPort, (), opdescr )
            portNum1 = len(node1.outputPorts)-1

            # reassign op to the newly created port
            op = p1

        elif isinstance(node2, MacroOutputNode) and portNum2==0:
            # add an output port to the macro node
            macroNode = node2.macroNode
            pdescr = node1.outputPortsDescr[portNum1]

            # create unique port names
            name = node1.name+'_'+pdescr['name']
            for opp in macroNode.outputPortsDescr:
                if opp['name'] == name:
                    name = name + '_%d'%len(node2.inputPorts)

            opdescr = pdescr.copy()
            opdescr['name'] = name
            # remove before/after connect/disconnect callbacks for these
            # newly ports, else we call them also on these ports which we
            # dont want
            dummy = opdescr.pop('beforeConnect',None)
            dummy = opdescr.pop('afterConnect',None)
            dummy = opdescr.pop('beforeDisconnect',None)
            dummy = opdescr.pop('afterDisconnect',None)

            macroNode.outputPortsDescr.append(opdescr)
            p2 = apply( macroNode.addOutputPort, (), opdescr )

            codeAfterDisconnect = """def afterDisconnect(self, port1, port2):
    macno = port2.node
    # remove ports:
    macroNode = macno.macroNode
    for p in macroNode.outputPorts:
        if p.number == (port2.number-1) and len(port2.connections) == 0:
            macroNode.network.deleteConnections(p.connections)
            #remove outputPort in MacroNode
            macroNode.deletePort(p)
    # remove outputPort in MacroInputNode
    if len(port2.connections) == 0:
        macno.deletePort(port2)

    for c in macno.getInConnections():
        c.updatePosition()
"""

            # create new input port in MacroOutputNode
            ipdescr = { 'name':opdescr['name'], 'required':False,
                        'singleConnection':'auto',
                        'datatype': opdescr.get('datatype', 'None'),
                        'afterDisconnect':codeAfterDisconnect,
                        'required': False
                      }
            node2.inputPortsDescr.append(ipdescr )
            p1 = apply( node2.addInputPort, (), ipdescr )
            portNum2 =len(node2.outputPorts)-1

            # reassign ip to the newly created port
            ip = p1

        # if ip has dataType None and is singleConnection set its type
        # to the type of op
        ed = self.getEditor()
        if ed.hasGUI:
            if ip.datatypeObject['name']=='None' and ip.singleConnection:
                if op.datatypeObject['name']!='None':
                    ip.setDataType(op.datatypeObject, tagModified=False)
            
        conn = apply( NetworkConnection, (op, ip, mode, name, blocking), kw )

        self.connections.append(conn)
        conn.network = self
        conn.vEditor = weakref.ref( ed )

        if ed.hasGUI and self.canvas:
            conn.buildIcons(self.canvas)
            self.connById[conn.id] = conn
            if conn.id2 is not None:
                self.connById[conn.id2] = conn

        # setup undo
        if undo:
            name = self.objectsAsString([conn])
            undoCmd = 'self.deleteConnections("%s")'%name
            if ed.hasGUI:
                ed.setupUndo(undoCmd, 'connectNodes')

        sum = node1.selected+node2.selected
        if sum:
            self.selectConnections([conn], undo=0)
        if self.needsResetNodeCache:
            self.resetNodeCache()

        if doNotCb is False:
            # call "after connect" callbacks if available
            # output port first, then input port
            newconn = conn
            for p in [op, ip]:
                callback = p.callbacks['afterConnect'][0]
                if callback is not None:
                    newconn = callback(p, conn)
                    if newconn is not None:
                        conn = newconn
            #node1.afterConnect(conn)
            #node2.afterConnect(conn)

        #if conn.port1.data != 'no data yet':
        ip._newdata = True
        if self.runOnNewData.value is True:
            #node2.inputPorts[portNode2]._newdata = True
            #ip._newdata = True
            if doNotSchedule is False:
                if conn.port1.data != 'no data yet':
                    node2.schedule()

        # tag network modified
        self._setModified(True)

        # this is a new connection object, thus we set conn._original=False
        conn._setOriginal(False)

        # create an ConnectNodes Event
        ed.dispatchEvent( ConnectNodes(self, conn) )

        return conn
    

    def specialConnectNodes(self, node1, node2, portNode1=0, portNode2=0,
                            mode='angles', name='NoName', undo=1, **kw):
        """NetworkConnection <- specialConnectNodes(node1, node2, portNode1=1, portNode2=0, mode='angles', name='NoName', undo=1, **kw)
        create a networkConnection object that connects these 2 nodes
        """

##         ed = self.getEditor()
##         if ed is None:
##             print 'ERROR: network %d has to be added to editor before nodes can be connected', self.name
##             return

        nodes = self.expandNodes([node1, node2])
        node1 = nodes[0]
        node2 = nodes[1]
        assert isinstance(node1, NetworkNodeBase)
        assert isinstance(node2, NetworkNodeBase)

        if type(portNode2) is types.StringType:
            ip = node2.getSpecialInputPortByName(portNode2)
            if ip is None:
                return
        else:
            ip = node2.specialInputPorts[portNode2]

        if type(portNode1) is types.StringType:
            op = node1.getSpecialOutputPortByName(portNode1)
            if op is None:
                return
        else:
            op = node1.specialOutputPorts[portNode1]

        # call "before connect" callbacks
        # output port first, then input port
        for p in [op, ip]:
            callback = p.callbacks['beforeConnect'][0]
            if callback is not None:
                callback(p, op, ip)
        #node1.beforeConnect(op, ip)
        #node2.beforeConnect(op, ip)
        
        conn = apply( NetworkConnection, (op, ip, mode, name), kw )
        #assert conn not in self.connections
        self.connections.append(conn)
        conn.network = self
        ed = self.getEditor()
        conn.vEditor = weakref.ref( self.getEditor() )

        conn.highlightOptions = {'fill':'red', 'width':4, 'arrow':'last',
                                 'stipple':'gray75'}
        conn.unhighlightOptions = {'fill':'orange', 'width':4, 'arrow':'last',
                                 'stipple':'gray75'}
        conn.selectOptions = {
            'connection0': {'fill':'orange', 'width':4, 'arrow':'last',
                            'stipple':'gray75'},
            'connection1': {'fill':'orange', 'width':4, 'arrow':'last',
                            'stipple':'gray75'},
            'connection2': {'fill':'orange', 'width':4, 'arrow':'last',
                            'stipple':'gray75'},
            }
        conn.deselectOptions = {'fill':'orange', 'width':4, 'arrow':'last',
                                'stipple':'gray75'}

        if self.canvas:
            conn.buildIcons(self.canvas)
            self.connById[conn.id] = conn
            if conn.id2 is not None:
                self.connById[conn.id2] = conn
        conn.deselect()

        if self.needsResetNodeCache:
            self.resetNodeCache()

        # if data is available on parent port, run child
        if (conn.port1.data != 'no data yet') \
          and self.runOnNewData.value is True:
            #self.secondNodePort.node.schedule()
            conn.port2.node.schedule()
            
        # call "after connect" callbacks if available
        # output port first, then input port
        for p in [op, ip]:
            callback = p.callbacks['afterConnect'][0]
            if callback is not None:
                callback(p, conn)
        #node1.afterConnect(conn)
        #node2.afterConnect(conn)

        self._setModified(True)

        conn._setOriginal(False)
        
        # create an ConnectNodes Event
        ed.dispatchEvent( ConnectNodes(self, conn) )

        return conn


    def deleteNodes(self, nodes, undo=1):
        # make a local copy of the list of nodes to make sure that if for
        # instance the list is selectedNodes, the list will not shrink as
        # we deselect nodes in the loop

        # please note, we HAVE to make a copy of self.nodes, since we will
        # subsequently delete items from this list
        nodes = self.expandNodes(nodes)[:]

        # create a DeleteNodes Event
        ed = self.getEditor()
        ed.dispatchEvent( DeleteNodesEvent(self, nodes) )

        for ni in range(len(nodes)):
            n = nodes[ni]

            # remove all connections to this node
            inConnections = n.getInConnections()
            self.deleteConnections(inConnections, 0, schedule=False)
            outConnections = n.getOutConnections()
            self.deleteConnections(outConnections, 0)

            n.beforeRemovingFromNetwork()

            # delete this node's ports
            inNode = 0
            for p in n.inputPorts[:]: # IMPORTANT NOTE: since we will delete
                # the port from n.inputPorts while we are looping over this
                # list, we need to loop over a copy to avoid unpredictable
                # results!
                if p.dataView is not None: # kill data viewer window
                    p.dataView.destroy()
                if p.widget:
                    # close widget editor
                    if p.widget.objEditor:
                        p.widget.objEditor.Cancel_cb()
                    inNode = max(0, p.widget.inNode)
                # close port editor
                if p.objEditor:
                    p.objEditor.Cancel()
                n.deletePort(p, resize=False, updateSignature=False)

            for p in n.outputPorts[:]:
                if p.dataView is not None: # kill data viewer window
                    p.dataView.destroy()
                if p.objEditor:
                    p.objEditor.Cancel()
                n.deletePort(p, resize=False, updateSignature=False)

            for p in n.specialInputPorts[:]:
                n.deletePort(p, resize=False, updateSignature=False)

            for p in n.specialOutputPorts[:]:
                n.deletePort(p, resize=False, updateSignature=False)

            
	    if n.objEditor:
                n.objEditor.Dismiss()

            if n.selected:
                self.selectedNodes.remove(n)

            if n.isExpanded() and inNode:
                n.hideInNodeWidgets( )
                
            old = self.needsResetNodeCache
            self.needsResetNodeCache=0
                
            if n.isRootNode:
                self.rootNodes.remove(n)

            self.needsResetNodeCache=old

            # delete the node's param. panel
            n.paramPanel.destroy()

            self.nodes.remove(n)

            del self.nodesById[n.id]   # remove node from node dictionary
            n.deleteIcon()
            n.afterRemovingFromNetwork()

        if self.needsResetNodeCache:
            self.resetNodeCache()

        self._setModified(True)
            

    def deleteConnections(self, connections, undo=1, schedule=True):
        """Call this method to delete connections. This method will also call
beforeDisconnect() and afterDisconnect() that can be overwritten.
schedule: 
    if we are deleteing the node in port2, we don't want to schedule
    or trigger the callback
"""

        port1 = None
        port2 = None
        
        connections = self.expandConnections(connections)

        # create a DeleteConnectionsEvent Event
        ed = self.getEditor()
        ed.dispatchEvent( DeleteConnectionsEvent(self, connections) )

        for c in connections:
            # we verify if c is still a valid connection as it may 
            # have been destroyed by one of the callback bellow
            try:
                port1 = c.port1
                port2 = c.port2
                node1 = port1.node
                node2 = port2.node
            except:
                continue

            # call port callbacks for beforeDisconnect if available
            for p in [port2, port1]: #first input then output
                callback = p.callbacks['beforeDisconnect'][0]
                if callback is not None:
                    callback(p, c)

            self.deleteConnectionsNoCB(c, undo=undo)

            # if datatype changed because of connection reset datatype
            if port2.datatypeObject['name'] != port2.originalDatatype:
                port2.setDataType(port2.originalDatatype, tagModified=False)
                
            # please note that for example MacroNodes implement a
            # afterDisconnect method which gets called here:
            # also, we have to test if the ports still exists
            for p in [port2, port1]:
                if p is not None:
                    callback = p.callbacks['afterDisconnect'][0]
                    if callback is not None:
                        callback(p, port1, port2)

            #node1.afterDisconnect(port1, port2)
            #node2.afterDisconnect(port1, port2)

            # set _newdata of input port of child node so that when it runs
            # next time it will not know something has changed for thsi port
            port2._newdata = True

            #if not port2.required and schedule is True: 
            if self.runOnNewData.value is True:
                node2.schedule() # the port need to run to reflect its current status

        if self.needsResetNodeCache:
            self.resetNodeCache()

        self._setModified(True)

            


    def deleteConnectionsNoCB(self, c, undo=1):
        """This method deletes connections without calling the
        beforeDisconnect() and afterDisconnect() methods. This method is
        basically doing all the work."""

        if hasattr(c.port2,'_validationStatus'):     
            c.port2._validationStatus = 'unchecked'

        self.connections.remove(c)
        if c.selected:
            self.selectedConnections.remove(c)

        node2 = c.port2.node
        c.port1.children.remove(c.port2)
        c.port1.connections.remove(c)
        c.port1.node.children.remove(node2)
        c.port2.parents.remove(c.port1)
        c.port2.connections.remove(c)
        node2.parents.remove(c.port1.node)

        # delete inputPort data
        c.port2.data = None
        c.port2._newdata = False


        c.port1 = None
        c.port2 = None
        if c.id is not None:
            del self.connById[c.id]
        if c.id2 is not None:
            del self.connById[c.id2]
        c.destroyIcon() # delete connection's icon

        # count parent to decide whether or not second node is a root
        node2.ensureRootNode()

        self._setModified(True)


    def deleteConnection(self, node1, port1, node2, port2):
        """Delete a connection between port1 (output) and port2 (input).
        Port1 and port2 can be either a port instance or the port name."""
                
        if type(port1) == types.StringType:
            port1 = node1.outputPortByName[port1]
        if type(port2) == types.StringType:
            port2 = node2.inputPortByName[port2]

        if hasattr(port2,'_validationStatus'):     
            port2._validationStatus = 'unchecked'

        conn = None
        for i in range(len(port1.connections)):
            conn = port1.connections[i]
            if conn.port2 == port2:
                break
            else:
                conn = None
        if conn:
            self.deleteConnections([conn])
            

    def toggleSelection(self, nodes, undo=1):
        nodes = self.expandNodes(nodes)
        ed = self.getEditor()

        # setup undo
        if undo:
            nodeNames = self.objectsAsString(nodes)
            undoCmd = 'self.toggleSelection("%s")'%nodeNames
            ed.setupUndo(undoCmd, 'toggleSelection')

        for n in nodes:
            if n.selected: self.deselectNodes([n], undo=0)
            else: self.selectNodes([n], undo=0)


    def clearSelection(self, undo=1):

        if len(self.selectedNodes)==0 and len(self.selectedConnections)==0:
            return
        
        # setup undo
        if undo:
            ed = self.getEditor()
            names = self.objectsAsString(self.selectedNodes)
            undoCmd = 'self.selectNodes("%s")\n'%names
            names = self.objectsAsString(self.selectedConnections)
            undoCmd = undoCmd+'self.selectConnections("%s")\n'%names
            ed.setupUndo(undoCmd, 'clearSelection')

        self.deselectNodes(self.selectedNodes[:], undo=0)
        self.deselectConnections(self.selectedConnections[:], undo=0)
        

    def clearSelectedNodes(self, undo=1):

        if len(self.selectedNodes): return

        # setup undo
        if undo:
            ed = self.getEditor()
            names = self.objectsAsString(self.selectedNodes)
            undoCmd = 'self.selectNodes("%s")\n'%names
            ed.setupUndo(undoCmd, 'clearSelectedNodes')

        self.deselectNodes(self.selectedNodes[:], undo=0)
        

    def selectNodes(self, nodes, undo=1):
        self.eventHandler['preSelection'].CallCallbacks(self.selectedNodes)
        nodes = self.expandNodes(nodes)

        # setup undo
        if undo:
            ed = self.getEditor()
            nodeNames = self.objectsAsString(nodes)
            undoCmd = 'self.deselectNodes("%s")'%nodeNames
            ed.setupUndo(undoCmd, 'selectNodes')

        selectedConnections = []
        for n in nodes:
            selectedConnections.extend(n.getConnections())
            if not n.selected:
                n.select()
                self.selectedNodes.append(n)

        if len(selectedConnections):
            self.selectConnections(selectedConnections, undo=0)

        self.eventHandler['onSelectionChange'].CallCallbacks()


    def deselectNodes(self, nodes, undo=1):
        nodes = self.expandNodes(nodes)[:]
        deselectedConnections = []

        # setup undo
        if undo:
            ed = self.getEditor()
            nodeNames = self.objectsAsString(nodes)
            undoCmd = 'self.selectNodes("%s")'%nodeNames
            ed.setupUndo(undoCmd, 'deselectNodes')

        # build a unique list of connections
        deselectedConnections = []
        for n in nodes:
            deselectedConnections.extend(n.getConnections())
            if n.selected:
                n.deselect()
                self.selectedNodes.remove(n)

        if len(deselectedConnections):
            self.selectConnections(deselectedConnections, undo=0)

        self.eventHandler['onSelectionChange'].CallCallbacks()
        
        
    def clearSelectedConnections(self, undo=1):

        if len(self.selectedConnections)==0: return

        # setup undo
        if undo:
            ed = self.getEditor()
            names = self.objectsAsString(self.selectedConnections)
            undoCmd = 'self.selectConnections("%s")\n'%names
            ed.setupUndo(undoCmd, 'clearSelectedConnections')
        self.deselectConnections(self.selectedConnections[:], undo=0)
        

    def selectConnections(self, connections, undo=1):
        connections = self.expandConnections(connections)

        # setup undo
        if undo:
            ed = self.getEditor()
            names = self.objectsAsString(connections)
            undoCmd = 'self.deselectNodes("%s")'%names
            ed.setupUndo(undoCmd, 'selectConnections')

        for c in connections:
            if not c.selected:
                self.selectedConnections.append(c)
            c.select()


    def deselectConnections(self, connections, undo=1):
        connections = self.expandConnections(connections)

        # setup undo
        if undo:
            ed = self.getEditor()
            names = self.objectsAsString(connections)
            undoCmd = 'self.selectNodes("%s")'%names
            ed.setupUndo(undoCmd, 'deselectConnections')

        for c in connections:
            if c.selected:
                self.selectedConnections.remove(c)
            c.deselect()

    
    def arrowKeys_cb(self, dx, dy, event=None):
        """move subgraph of selected nodes when arrow keys are pressed"""

        self.moveSubGraph(self.selectedNodes, dx, dy, absolute=False)


    def moveSubGraph(self, nodes, dx, dy, absolute=False, tagModified=True,
                     undo=1):
        """None <- moveSubGraph(nodes, dx, dy, absolute=False, undo=1)
update the nodes' coordinates and move node's icon, also update connections
If absolute is set to False (default), the graph moves by dx,dy, else it move
TO dx, dy
All nodes have an attribute hasMoved which will be set to True."""

        nodes = self.expandNodes(nodes)
        if len(nodes)==0: return

        # setup undo
        if undo:
            ed = self.getEditor()
            nodeNames = self.objectsAsString(nodes)
            undoCmd = 'self.moveSubGraph("%s", %d, %d)\n'%(nodeNames, -dx, -dy)
            ed.setupUndo(undoCmd, 'moveSubGraph')
        
        canvas = self.canvas
        # update node's coordinates and maybe move node's icon
        for n in nodes:
            if absolute is False:
                posx = dx
                posy = dy
            else:
                posx = dx-n.posx
                posy = dy-n.posy
            # now move
            canvas.move(n.iconTag, posx, posy)
            # and update n.posx, n.posy
            n.updatePosXPosY()
            
        # also, update connections
        co1, co2, no1 = self.getConnections(nodes)
        for c in co1:
            c.updatePosition()
        for c in co2:
            c.updatePosition()

        
        for node in nodes:
            node.hasMoved = True
            if tagModified is True:
                node._setModified(True)
            

    def waitForDebugCommand(self):
        inbuffer = ""
        import os, sys, fcntl
        fd = sys.stdin.fileno()
        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
        
        while not self.debugCmd:
            sleep(0.5)
            # with update_idletasks() shell works but not GUI
            # with update shell doesnot get characters
            self.canvas.update()
            ifd, ofd, efd = select([fd], [], [], 0)

            if fd in ifd:
                #print 'AAAAAAAAAAAAA', ifd
                #print 'BBBB'
                input = os.read(fd, 1024)
                #print 'GOT', len(input), input=='\n', input, inbuffer
                if input != '\n':
                    inbuffer += input
                else:
                    print 'sentence', inbuffer
                    inbuffer = ""

        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)


    def waitForCompletion(self):
        # wait until the network has completed running

        ## the follwoing code makes the test
        ## NetworkEditor/regression/test_netEditing.test_addCodeToNode freeze
        #self.RunLock.acquire()
        #self.RunLockCond.wait()

        while 1:
            self.execStatusLock.acquire()
            status = self.execStatus
            self.execStatusLock.release()
            #print status
            status = status.lower()
            if status == 'pending' or status == 'stop' or status == 'waiting':
                #print 'Done waiting'
                return
            else:
                #print 'waiting for completion'
                sleep(0.1) # 1/10th of a second
                
##              if self.RunLock.acquire(0):
##                  print "waiting for completion GOT THE LOCK"
##                  self.RunLock.release()
##                  return
##              else:
##                  print "waiting for completion waiting"
##                  sleep(0.1) # 1/10th of a second


    def stop(self):
        """set execStatus to 'stop'.
The execution will stop after completion of the current node"""
        self.execStatusLock.acquire()
        stat = self.execStatus
        # we need to set the status for all networks (parent of child,
        # i.e. macros) of this network
        from NetworkEditor.macros import MacroNode
        for node in self.nodes:
            if isinstance(node, MacroNode):
                node.macroNetwork.setExec('stop')
        self.execStatus = 'stop'
        if stat.lower()=='pause':
            self.execStatusCond.notifyAll()
        self.execStatusLock.release()
        
        # mark the current node as haven't been runned
        if len(self.lastExecutedNodes) > 0:
            self.lastExecutedNodes[-1][0].forceExecution = 1


    def start(self):
        """set execStatus to 'pending'.
The network can be run"""

        self.execStatusLock.acquire()
#        if self.execStatus.lower() == 'pause':
#            self.stop()
#            execStatus = 'stop'
#            self.execStatusCond.notifyAll()
#            self.execStatusLock.release()
#            self.waitForCompletion()
#            self.execStatusLock.acquire()
        from NetworkEditor.macros import MacroNode
        for node in self.nodes:
            if isinstance(node, MacroNode):
                node.macroNetwork.setExec('pending')
        self.execStatus = 'pending' # a set of nodes wants to run
        self.execStatusLock.release()


    def pause(self):
        """set execStatus to 'pause'.
The network execution will pause after the completion of the current node"""
        self.execStatusLock.acquire()
        self.execStatus = 'pause'
        from NetworkEditor.macros import MacroNode
        for node in self.nodes:
            if isinstance(node, MacroNode):
                node.macroNetwork.setExec('pause')
        self.execStatusLock.release()


    def togglePause(self, event=None):
        """toggles execStatus between 'pause' and resume"""
        if self.execStatus == 'pause':
            self.resume()
        else:
            self.pause()

        
    def resume(self):
        """set execStatus to 'running'.
Waiting execution threads are notified."""
        self.execStatusLock.acquire()
        self.execStatus = 'running'
        from NetworkEditor.macros import MacroNode
        for node in self.nodes:
            if isinstance(node, MacroNode):
                node.macroNetwork.setExec('running')
        self.execStatusCond.notifyAll()
        self.execStatusLock.release()


    def getExecStatus(self):
        self.execStatusLock.acquire()
        stat = self.execStatus
        self.execStatusLock.release()
        return stat

    
    def checkExecStatus(self):
        # check if the the execution has been aborted or paused
        stop = 0
        self.execStatusLock.acquire()
        if self.execStatus.lower()=='stop':
            print 'exec was stopped'
            stop = 1

        elif self.execStatus.lower()=='pause':
            print 'exec was paused'
            if self.editor.withThreads:
                self.execStatusCond.wait()
                print 'exec was resumed'
                if self.execStatus.lower()=='stop':
                    print 'exec stops after resume'
                    stop = 1
            else:
                self.execStatusLock.release()
                while True:
                    sleep(0.1)
                    if self.canvas is not None:
                        self.canvas.update()
                    self.execStatusLock.acquire()
                    self.execStatusLock.release()
                    if self.execStatus.lower()!='pause':
                        break
                self.execStatusLock.acquire()
        self.execStatusLock.release()

        return stop

    
    def tagSubtree(self, node, val):
        # tag all nodes below node widthFirstTag=val (node is NOT tagged)
        for conn in node.getOutConnections():
            node2 = conn.port2.node
            if not node2.widthFirstTag and conn.blocking is True:
                #print 'tagging node: ', node2.name
                node2.widthFirstTag = val # prevent endless loop on cycles
                self.tagSubtree(node2, 1)


    def setChildrenOutputToNoDataYet(self, node):
        """if node is in a macro, this also sets the children of upper networks.
but this doesn't go down into macros.
"""
        from macros import MacroOutputNode
        for conn in node.getOutConnections():
            #conn.port2._newdata = True
            #conn.port2.data = 'no data yet'
            node2 = conn.port2.node
            for lOutputPort in node2.outputPorts:
                lOutputPort.outputData('no data yet')
                #print "lOutputPort.name", node2.name , lOutputPort.name
                if conn.blocking is True:
                    if isinstance(node2, MacroOutputNode) is True:
                        self.setChildrenOutputToNoDataYet(node2.macroNode)
                    else:
                        self.setChildrenOutputToNoDataYet(node2)


    def widthFirstChildren(self, nodeIndex, allNodes):
        """build a list of nodes corresponding to a width first traversal of
        the network starting from the nodes specified in allNodes.
        Children for which the attribute isSchedulingNode was set to 1 are
        not added.
        A node will not be added to the list before all of its
        parents have been added"""

        from macros import MacroOutputNode
        node = allNodes[nodeIndex]

        # children nodes of scheduling nodes are not scheduled here.
        # MacroOutputNode have to run last
        if node.isSchedulingNode is True: # or isinstance(node, MacroOutputNode):
            if nodeIndex+1<len(allNodes):
                self.widthFirstChildren(nodeIndex+1, allNodes)
            return

        # loop over children of node
        for conn in node.getOutConnections():
            node2 = conn.port2.node
            # node2 is a child of self
            if node2.widthFirstTag and (self.runOnNewData.value is True or node2.forceExecution)\
               and not node2.frozen:
                # check that all parents are already in list
                append = 1
                if isinstance(conn.port2, RunChildrenInputPort):
                    append=0
                    # we need to force the excution of node2 since it gets
                    # added to the list of nodes to run by a special
                    # connection, hence it might not have new data
                    node2.forceExecution = 1
                    # FIXME .. need to get the children append to the list
                elif isinstance(conn.port2, RunNodeInputPort):
                    # we need to force the excution of node2 since it gets
                    # added to the list of nodes to run by a special
                    # connection, hence it might not have new data
                    node2.forceExecution = 1
                    # do not append because connections on this port will
                    # be executed in node.run
                    append=0
                else:
                    for conn3 in node2.getInConnections():
                        if conn3.blocking:
                            node3=conn3.port1.node
                            if node3.widthFirstTag:
                                append = 0
                                break
                            elif (node3.isSchedulingNode is True) and \
                                 (node3 in allNodes):
                                    append = 0
                                    break

                if append: # and not isinstance(node2, MacroOutputNode):
                    allNodes.append(node2)
                    node2.widthFirstTag = 0

                else: # initiate a width first on special children
                    for p in node2.specialOutputPorts:
                        for ip in p.children:
                            node3 = ip.node
                            # make sure all parents of node3 are clean
                            append=1
                            for conn4 in node3.getInConnections():
                                node4 = conn4.port1.node
                                if node4.widthFirstTag:
                                    append = 0
                                    break

                            if append:# and not isinstance(node3, MacroOutputNode):
                                allNodes.append(node3)
                                node3.widthFirstTag = 0
                             
        if nodeIndex+1<len(allNodes):
            self.widthFirstChildren(nodeIndex+1, allNodes)


    def getAllNodes(self, roots):
        """build a list of all the nodes under roots in the order they
        will be executed"""

        if len(roots)==0:
            return[]
        
        from macros import MacroOutputNode, MacroNetwork
        for node in roots:
            node.widthFirstTag = 0

        # tag widthFirstTag=1 all children of roots (root nodes do not get tagged
        # dirty)
        for node in roots:
            self.tagSubtree(node, 1)


        # FIXME this cannot be done here else the next step which tries to
        # remove root node that have been tagged (i.e. are themselves children
        # of another root) would not be removed
        
        # when cycles exist a root might have gotten tagged, remove it
        #for node in roots:
        #    node.widthFirstTag = 0
            
        # build list of valid roots (i.e. are themselves children
        # of another root).  This can happen for isntance when
        # node.scheduleChildren() calls this function with all nodes
        # under a given node.  A child under port 2 might depend on a node
        # that is a child of port 1
        allNodes = []
        for node in roots:
            #if  isinstance(node, MacroOutputNode):
            #    continue
            if not node.widthFirstTag: # it was not found as a child of another root
                allNodes.append(node)

        # build the list of nodes to be executed
        if len(allNodes)>0:
            self.widthFirstChildren(0, allNodes)

        # move all sheduling node to the end of the list
        # else a child of the scheduling might be triggered by the node
        # before all of its parents have run
        schedulingNodes = []
        nodes = []
        for n in allNodes:
            if n.isSchedulingNode is True:
                schedulingNodes.append(n)
            else:
                nodes.append(n)
        allNodes = nodes + schedulingNodes
        
        # add MacroNodeOutput as last node
        #if isinstance(self, MacroNetwork):
        #    allNodes.append(self.opNode)
            #self.opNode.forceExecution = 1
        
        # make all node clean
        for node in self.nodes:
            node.widthFirstTag = 0

        #print 'NETWORK:',self.name, 'getAllNodes', roots, allNodes
        return allNodes


    def endOfRun(self, net):
        """function called after an execution ends
"""
        #print "endOfRun", net.name
        ed = self.getEditor()
        if ed.hasGUI:
            if hasattr(ed, 'endOfRun'):
                ed.endOfRun(net)

        # we restore the viewers states at the end of the fisrt run only
        for n in self.nodes:
            if hasattr(n, 'restoreStatesFirstRun'):
                #print "self.nodes with restoreStatesFirstRun", n
                n.restoreStatesFirstRun()
                del n.restoreStatesFirstRun


    def hardrun(self):
        self.run(roots=self.rootNodes)


    def run(self, roots=None):
        """schedule the subtree of nodes under roots for execution in a separate thread.
if roots is None: SOFT RUN: it will be a soft run where only the nodes with new data 
                            from self.rootNodes will run
                            network.run() launches a soft run
if roots is provided: HARD RUN: every nodes in roots will run (and all their children)
                                network.run(network.rootNodes) launches a hard run
"""
        # try to get the lock for running nodes in this network
        # if we fails it means nodes a running and we just return
        #print
        #print "############ NEW RUN", roots
        #print

        #print "Network.run"
        #import traceback;traceback.print_stack()

        ed = self.getEditor()

        #self.forceExecution = 1

        lrunOnNewData = self.runOnNewData.value
        self.runOnNewData.value = True

        #print "get RunLock"
        if not self.RunLock.acquire(0):
            #print 'could not acquire RunLock for roots', roots
            return
        #print "got it"
        
        if roots is None:
            roots = self.rootNodes
        else:
            self.forceExecution = 1
            #for r in roots:
            #    r.forceExecution=1
                
        if len(roots)==0:
            self.execStatus = 'waiting'
            self.endOfRun(self)
            return

        #print "start", self.execStatus 
        if self.execStatus == 'running':
            #print 'trying to run while running'
            self.runAgain = True
            self.RunLock.release()
            return

        # set execStatus to pending
        self.start()
        
        # get the list of nodes to run
        #print "roots", roots
        allNodes = self.getAllNodes(roots)
        #print "AllNodes", allNodes
        
        if len(allNodes):
            if ed.hasGUI and ed.withThreads:
                # create and start the execution thread
                #print "create exec thread"
                execThread = ExecutionThread(self, allNodes)
                # create a thread that will wait for the end of the execution
                #print "create afterexec"
                endExecThread = AfterExecution(self, self.endOfRun)
                #print "start after exec"
                endExecThread.start()
                #print "start exec"
                # we start the execution thread. It will sit and wait to 
                # acquire net.runNodes in the run method
                execThread.start()
            else:
                self.execStatus = 'running'
                self.runNodes(allNodes)
                self.endOfRun(self)
                self.forceExecution = 0

        self.runOnNewData.value = lrunOnNewData

        #print "release RunLock"
        self.RunLock.release()
        self.execStatus = 'waiting'


    def getSubRunNodes(self, roots=None):
        # same as run, but never creates a new thread
        # used by macro node to execute nodes in macro network in same
        # thread as parent network (if multi-threaded)

        if roots is None:
            roots = self.rootNodes
            for r in roots:
                r.forceExecution=1
        if len(roots)==0:
            return
        allNodes = self.getAllNodes(roots)
        return allNodes


    def runNodes(self, allNodes, resetList=True):
        """run the list of nodes in the same thread as the caller"""
        #import traceback;traceback.print_stack()
        #print "runNodes", allNodes, "in network:", self.name
        self.nodeToRunList += allNodes 
        self.runAgain = False
        allOK = True # will turn to false if one of nodes fails to run
        if resetList is True:
            self.lastExecutedNodes = [] # clear the list
            self.lastExecNodesTimes = [] # clear the list

        try:
            #print "start Run"
            status = 1 # execution status for a node
            # loops over nodes
            #print ' START RUN ======================================'
            #for node in allNodes:
            while len(self.nodeToRunList) > 0:
                node = self.nodeToRunList[0]
                self.nodeToRunList.pop(0)
                #print '    run: ',node.name, node.forceExecution
                stop = self.checkExecStatus()
                if stop:
                    break
                #print 'exec status', stop

                #print 'RUNNING', node.name, node.network.forceExecution
                # run a node
                self.lastExecutedNodes.append( [node, time(), 0] )
                
                status = node.run(debug=self.debug)
                
                self.lastExecutedNodes[-1][-1] = time()
                #print 'node exec status', node.name, status

                # previousely we would simple break out of the loop but
                # this would prevent the excution of nodes in the network that
                # are not under node and hence should really run
                if type(status)==types.StringType and status.lower()=='stop':
                    # node returned 'stop' we have to remove all children
                    # of node from the allNodes list so they will not be run
                    allOK = False
                    for nnode in self.nodeToRunList:
                        if nnode.ischild(node):
                            #print 'removing', nnode
                            self.nodeToRunList.remove(nnode)

                elif status==0: # HUMM not sure when this happens
                    allOK = False
                    break

        except KeyboardInterrupt, e:

            if not self.editor.hasGUI:
                print 'execution stopped'
                sys.exit(1)
            else:
                self.editor.stopCurrentNet_cb()
        except:
            print "*** ERROR during execution"
            traceback.print_exc()

        # notify end of execution (even if it failed or was stopped)
        #print "Run done"
        self.RunLock.acquire()
        #print "notify"
        self.RunLockCond.notifyAll()
        #print "release RunLock after notify"
        self.RunLock.release()

        if self.runAgain:
            if self.canvas is not None:
                self.canvas.update()

            # we can't use allNodes as it is anymore, 
            # maybe a node has been deleted in the doit
            # this is a way to repair allNodes
            for n in allNodes:
                if n not in self.nodes:
                   allNodes.remove(n) 

            self.runNodes(allNodes)

        if self.afterRunCb:
            self.afterRunCb(self)

        if self.editor.hasGUI:
            self.editor.GANTT.setTasks(self.lastExecutedNodes)

        return allOK

    
    def resetWidgetValues(self):
        """Reset all widgets in the current network to the initialValue as
defined in node.widgetDescr. If no nodes are selected, we loop over all nodes,
else we loop over the selected nodes. If a macro node is present, we
recursively call this method in the macro network."""

        if len(self.selectedNodes):
            nodes = self.selectedNodes
        else:
            nodes = self.nodes

        from macros import MacroNode
        for node in nodes:
            if isinstance(node, MacroNode):
                node.macroNetwork.resetWidgetValues()
            dummyNode = apply(node.__class__,(),node.constrkw)
            origWidgetDescr = dummyNode.widgetDescr
            for wname, wdescr in origWidgetDescr.items():
                if node.widgetDescr.has_key(wname):
                    # get a handle to the widget
                    widget = node.getWidgetByName(wname)
                    ## 1) do we have an initiaValue defined here?
                    ndescr = node.widgetDescr[wname]
                    if ndescr.has_key('initialValue'):
                        val = wdescr['initialValue']
                        ndescr['initialValue'] = val
                    ## 2) if not, use configOpt defined in widgets.py
                    else:
                        val = \
                    widget.__class__.configOpts['initialValue']['defaultValue']
                        
                        
                if widget:
                    widget.set(val)


    def createUserPanel(self, name, **kw):
        #print "createUserPanel", name
        if self.userPanels.has_key(name) or self.getEditor() is None:
            #warnings.warn("Name %s already use for a panel"%name)
            return
        if not kw.has_key('master'):
            kw['master']=None
        kw['network']= self
        panel = apply(UserPanel, (name,), kw)
        self.userPanels[name] = panel


    def deleteUserPanel(self, name):
        #print "deleteUserPanel", name
        lPanel = self.userPanels[name]
        for w in lPanel.widgets:
            w.configure(master='ParamPanel')
        lPanel.master.destroy()
        del self.userPanels[name]
        del lPanel


#glyph functions
    def moveObject(self,event):
        # translate to the canvas coordinate system
        if self.glyphselectionBox:
                self.canvas.delete(self.glyphselectionBox)
        self.undrawSelectionCorners()        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        coords =  self.canvas.coords(CURRENT)
        if len(coords)==0:
            return
        if not hasattr(self,"oldx") :
           self.oldx =  self.origx
           self.oldy = self.origy
        ox =coords[0]
        oy = coords[1]
        dx = x - self.oldx
        dy = y - self.oldy
        self.canvas.move(CURRENT,dx,dy)
        self.oldx =  x
        self.oldy = y
        if self.canvas.type(CURRENT) == "text":
            self.canvas.delete("highlight")
            current_coords = self.canvas.coords(CURRENT)
            self.canvas.focus_set() # move focus to canvas
            self.canvas.focus(CURRENT)
            self.canvas.icursor(CURRENT, "@%d,%d" % (current_coords[0],current_coords[1]))
            self.canvas.select_clear()


    def highlight(self,item):
       if self.glyphshape == "text": 
        if self.canvas.bbox(item) == None:
            bbox = self.canvas.bbox(self.glyphselectionBox)
            #return
        else:
            bbox =self.canvas.bbox(item) 
        if self.glyphselectionBox:
                self.canvas.delete(self.glyphselectionBox)
        self.canvas.delete("highlight")
        if bbox:
            self.glyphselectionBox= self.canvas.create_rectangle(
                bbox, 
                tag="highlight",dash=(4,6),width=2,outline="magenta"
                )

            diffx = bbox[0]-bbox[2]
            diffy = bbox[3]-bbox[1]
            if self.canvas.type(CURRENT) != "text":
                if hasattr(self,"glyphKeywords"):
                    if self.glyphKeywords.has_key("font"):
                        font = self.glyphKeywords['font']
                    if self.glyphKeywords.has_key("fontsize"):
                        fontsize = self.glyphKeywords['fontsize']   
                    if self.glyphKeywords.has_key("fontstyle"):
                        fontstyle = self.glyphKeywords['fontstyle']    
                    if self.glyphKeywords.has_key("fill"):
                        fill = self.glyphKeywords['fill']
                        if fill == '':
                            fill = "black"
                it = self.canvas.create_text((bbox[0],bbox[1]+(diffy/2)),text="",font =(font,fontsize,fontstyle) ,fill=fill)
                self.i = it 
            self.canvas.lower(self.glyphselectionBox, self.i)


    def has_focus(self):
        return self.canvas.focus()


    def has_selection(self):
        # hack to work around bug in Tkinter 1.101 (Python 1.5.1)
        return self.canvas.tk.call(self.canvas._w, 'select', 'item')


    def set_focus(self, event):
        
            if self.canvas.type(CURRENT) == "oval" :
                return
            if self.canvas.type(CURRENT) == "text":
                       self.i = CURRENT
            self.highlight(CURRENT)
            # move focus to item
            if hasattr(self,"i"):
                item =self.i
            try:    
               self.canvas.focus_set() # move focus to canvas
               self.canvas.focus(item) # set focus to text item
               self.canvas.select_from(item, 0)
               self.canvas.select_to(item, END)
            except:
                pass


    def setCursor(self, event):
        
        canvas = self.canvas
        self.set_focus(event)
        # move insertion cursor
        
        item = self.has_focus()
        if not item:
            return # or do something else
        # translate to the canvas coordinate system
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.canvas.type(item)=="text":
            self.canvas.icursor(item, "@%d,%d" % (x, y))
            self.canvas.select_clear()
            delattr(self,"i")


    def handleKey(self, event):
        # widget-wide key dispatcher
        item = self.has_focus()
        if not item:
            return
        insert = self.canvas.index(item, INSERT)
        
        if event.char >= " ":
            self.highlight(item)    
            # printable character
            if self.has_selection():
                self.canvas.dchars(item, SEL_FIRST, SEL_LAST)
                self.canvas.select_clear()
            self.canvas.insert(item, "insert", event.char)
            self.highlight(item)

        elif event.keysym == "BackSpace":
            if self.has_selection():
                self.canvas.dchars(item, SEL_FIRST, SEL_LAST)
                self.canvas.select_clear()
            else:
                if insert > 0:
                    self.canvas.dchars(item, insert-1, insert)
            self.highlight(item)

        # navigation
        elif event.keysym == "Home":
            self.canvas.icursor(item, 0)
            self.canvas.select_clear()
        elif event.keysym == "End":
            self.canvas.icursor(item, END)
            self.canvas.select_clear()
        
        elif event.keysym == "Right":
            self.canvas.icursor(item, insert+1)
            self.canvas.select_clear()
        elif event.keysym == "Left":
            self.canvas.icursor(item, insert-1)
            self.canvas.select_clear()
        else:
             #print event.keysym
             pass   
