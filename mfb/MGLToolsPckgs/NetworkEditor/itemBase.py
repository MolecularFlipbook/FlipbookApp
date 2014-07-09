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
#########################################################################

import sys, os
import types
import Tkinter
import threading
import traceback
import warnings
import weakref
import tkMessageBox
import Pmw 

from mglutil.gui.BasicWidgets.Tk.TreeWidget.objectBrowser import ObjectBrowser
from mglutil.util.callback import CallbackManager, CallBackFunction


class UserPanel:
    """Tk frame onto which a user can place selected widgets"""

    def __init__(self, name, master=None, network=None, width=120, height=90):
        #print "UserPanel.__init__"
        
        editor = network.getEditor()
        self.editor = editor
        self.network = network
        self.master = master
        self.widgets = []   # list of widget placed onto this panel

        if not editor.hasGUI:
            return
        
        if master is None:
            self.master = Tkinter.Toplevel()
            self.master.title(name)
            self.master.protocol('WM_DELETE_WINDOW', self.withdraw_cb)

        ## build menu
        if master is None:
            buttonsFrame = Tkinter.Frame(self.master)
            self.buttonRun = Tkinter.Button(buttonsFrame, text='Run / Stop',
                                            command=self.editor.toggleNetworkRun_cb)
            self.buttonRun.pack(side='left', expand=1, fill='x')
            if hasattr(network, 'isApplication') is True:
                self.buttonQuit = Tkinter.Button(buttonsFrame, text='Quit',
                                                 command=self.editor.stopNetworkAndQuit_cb)
                self.buttonQuit.pack(side='left', expand=1, fill='x')
            else:
                self.buttonShowHideNetwork = Tkinter.Button(buttonsFrame, text='Show / Hide Vision',
                                                 command=self.editor.toggleGuiVisibility)
                self.buttonShowHideNetwork.pack(side='left', expand=1, fill='x')
            buttonsFrame.pack(side='top', fill='x')      

        ## build frame for widgets
        self.frame = Tkinter.Frame(
            self.master, relief='sunken', bd=3, bg='#c3d0a6')
        self.frame.configure(width=width, height=height)
        self.frame.pack(side='top', expand=1, fill='both')


    def withdraw_cb(self, event=None):
        """
"""
        #print "withdraw_cb"
        if hasattr(self.network, 'isApplication') is True:
            if len(self.network.userPanels) == 1:
                self.master.quit()
            else:
                self.master.iconify()
        else:
            self.master.iconify()
            self.editor.master.master.master.deiconify()


    def placeWidgetAndLabel(self, widget, relx, rely):
        #print "UserPanel.placeWidgetAndLabel", widget.widgetFrame.winfo_reqwidth()

        labelSide = widget.widgetGridCfg['labelSide']
        if labelSide is None:
            labelSide = 'left'

        widget.widgetFrame.place(relx=relx, rely=rely, anchor=Tkinter.CENTER)
        if labelSide == 'left':
            labelx = .5 * widget.widgetFrame.winfo_width() \
                 / widget.widgetFrame.master.winfo_width()
            widget.tklabel.place(relx=relx-labelx, rely=rely, anchor='e')
        elif labelSide == 'right':
            labelx = .5 * widget.widgetFrame.winfo_width() \
                 / widget.widgetFrame.master.winfo_width()
            widget.tklabel.place(relx=relx+labelx, rely=rely, anchor='w')
        elif labelSide == 'top':
            labely = .5 * widget.widgetFrame.winfo_height() \
                 / widget.widgetFrame.master.winfo_height()
            widget.tklabel.place(relx=relx, rely=rely-labely, anchor='s')
        elif labelSide == 'bottom':
            labely = .5 * widget.widgetFrame.winfo_height() \
                 / widget.widgetFrame.master.winfo_height()
            widget.tklabel.place(relx=relx, rely=rely+labely, anchor='n')
        else:
            warnings.warn('Wrong side for label')


    def rePlaceWidget(self, widget, labelSide=None):
        #print "UserPanel.rePlaceWidget"
        relx = float( widget.widgetFrame.winfo_x() \
                     + .5*widget.widgetFrame.winfo_width() ) \
                                       / widget.widgetFrame.master.winfo_width()
        rely = float(widget.widgetFrame.winfo_y() \
                     + .5*widget.widgetFrame.winfo_height() ) \
                                       / widget.widgetFrame.master.winfo_height()
        self.placeWidgetAndLabel(widget, relx, rely)


    def motionWidget_cb(self, widget, event=None):
        #print "UserPanel.motionWidget_cb"
        relx = float(event.x_root - widget.widgetFrame.master.winfo_rootx()) \
                                       /widget.widgetFrame.master.winfo_width()
        rely = float(event.y_root - widget.widgetFrame.master.winfo_rooty()) \
                                       /widget.widgetFrame.master.winfo_height()
        self.placeWidgetAndLabel(widget, relx, rely)


    def postWidgetMenu(self, widget, event=None):
        #print widget
        widget.menu.post(event.x_root, event.y_root)


    def addWidget(self, widget, widgetPlacerCfg=None):
        #print "UserPanel.addWidget"
        self.widgets.append(widget)

        if hasattr(self.network, 'isApplication') is True:
            widget.menu.delete(1,'end')
            cbpost = CallBackFunction(self.postWidgetMenu, widget)
            widget.tklabel.bind("<Button-3>", cbpost)
            if hasattr(widget.widget, 'canvas'):
                widget.widget.canvas.bind("<Button-3>", cbpost)
            else:
                widget.widget.bind("<Button-3>", cbpost)

        cb = CallBackFunction(self.motionWidget_cb, widget)
        widget.tklabel.bind("<B2-Motion>", cb)
        if hasattr(widget.widget, 'canvas'):
            widget.widget.canvas.bind("<B2-Motion>", cb)
        else:
            widget.widget.bind("<B2-Motion>", cb)

        if widgetPlacerCfg is not None:
            relx = eval(widgetPlacerCfg['relx'])
            rely = eval(widgetPlacerCfg['rely'])
        else:
            relx = .5
            rely = .5

        self.placeWidgetAndLabel(widget, relx, rely)
        # we need this otherwise the widget.widgetFrame.winfo_width 
        # is not set correctly the first time (so the label is hidden behind the widget)
        widget.port.node.network.canvas.update_idletasks()
        self.placeWidgetAndLabel(widget, relx, rely)


    def deleteWidget(self, widget):
        #print "UserPanel.deleteWidget"
        if widget in self.widgets:
            self.widgets.remove(widget)
        
        widget.tklabel.unbind("<Button-2>")
        if hasattr(widget.widget, 'canvas'):
            widget.widget.canvas.unbind("<Button-2>")
            #widget.widget.valueLabel.bind("<Button-2>", self.moveWidget_cb)
        else:
            widget.widget.unbind("<Button-2>")



class ParamPanel:
    """This class provides show / hide for all parameter panels
    """
    def __init__(self, node, master=None, title=None, applyFun=None,
                 dismissFun=None):

        self.node = weakref.ref(node)
        self.visible = 0 # visible=1 means panel is displayed
        

        self.applyFun = applyFun
        self.dismissFun = dismissFun
        if self.dismissFun is None:
            self.dismissFun = self.hide

        if master is None:
            master=Tkinter.Toplevel()
            self.master = master
            if title:
                self.master.title(title)
            self.master.withdraw()
            self.master.protocol('WM_DELETE_WINDOW', self.dismissFun )
        else:
            self.master = master

        # the mainFrame holds the widgetFrame plus some buttons
        self.mainFrame = Tkinter.Frame(self.master)
        self.mainFrame.pack(fill='both',expand=1)

        # add menu entries
        self.createMenus(self.mainFrame)
        
        # the widgetFrame holds the widgets bound to this panel
        self.widgetFrame = Tkinter.Frame(self.mainFrame, borderwidth=3,
                                         bg='#c3d0a6', relief='ridge')
        self.widgetFrame.pack(fill='both', expand=1)

        self.applyButton = Tkinter.Button(self.mainFrame, text="Run node",
                                          command=self.forceRun)
        Pmw.Balloon(self.mainFrame).bind(self.applyButton,"Run node and subnetwork") #tooltip
        self.applyButton.pack(side='left', fill='x', expand=1)
        
        #self.dismissButton = Tkinter.Button(self.mainFrame, text="Dismiss",
        #                                    command=self.dismissFun)
        #Pmw.Balloon(self.mainFrame).bind(self.dismissButton,"keep visible values") #tooltip
        #self.dismissButton.pack(side='left')


    def createMenus(self, parent):
        self.mBar = Tkinter.Frame(parent, relief=Tkinter.RAISED,
                                  borderwidth=2)
        self.mBar.pack(side='top',fill='x')
        self.menuButtons = {}
        self.makeOptionsMenu(self.mBar)
        apply( self.mBar.tk_menuBar, self.menuButtons.values() )
         

    def makeOptionsMenu(self, parent):
        Options_button = Tkinter.Menubutton(parent, text='Options',
                                            underline=0)
        self.menuButtons['Options'] = Options_button
        Options_button.pack(side=Tkinter.LEFT, padx="1m")

		# got rid of useless tearoff
        Options_button.menu = Tkinter.Menu(Options_button, tearoff=False)

        self.immediateTk = Tkinter.IntVar()
        self.immediateTk.set(1)
        Options_button.menu.add_checkbutton(label='Immediate',
                                            variable=self.immediateTk,
                                            command=self.setImmediate)


        Options_button.menu.add_separator()
        Options_button.menu.add_command(label='Dismiss', underline=0, 
                                        command=self.dismissFun)
        Options_button['menu'] = Options_button.menu


    def setImmediate(self, event=None, immediate=None, tagModified=True):
        if tagModified is True:
            self.node()._setModified(True)
        if immediate is not None:
            assert immediate in [0,1,True,False]
            self.immediateTk.set(immediate)


    def show(self):
        """ show paramter panel
"""
        if self.master.winfo_ismapped() == 0:
            self.master.deiconify()
            self.master.lift()

        # we make sure these are on
        self.node().paramPanelTk.set(1)
        self.visible = 1


    def hide(self, event=None):
        if self.master.winfo_ismapped() == 1:
            self.master.withdraw()

        # we make sure these are off
        self.node().paramPanelTk.set(0)
        self.visible = 0


    def toggleVisibility(self, event=None):
        if self.master.winfo_ismapped() == 1:
            self.hide()
        else:
            self.show()


    def destroy(self, event=None):
        if isinstance(self.master, Tkinter.Toplevel):
            self.master.destroy()
        else:
            self.mainFrame.destroy()


    def run(self, event=None):
        # only run if immediate==1. This method is called by the widget's set
        # method
        if self.immediateTk.get():
            if self.applyFun is not None:
                self.applyFun()


    def forceRun(self, event=None):
        # always call the apply fun. This method is called by the 'apply'
        # button at the bottom of this param panel
        if self.applyFun is not None:
            self.applyFun()


class NetworkItemsBase(object):
    """Base class for all objects that can be added to a Canvas."""

    # the following 3  methods are used to maintain backwards compatibility
    # because we changed certain attributes to weakref
    def getEditor(self):
        if self.vEditor is None: return None
        return self.vEditor()
    
    def setEditor(self, editor):
        self.vEditor = weakref.ref(editor)

    def delEditor(self):
        del self.vEditor

    # "self.editor" has to be created here. because we use the property mechan.
    editor = property(getEditor, setEditor, delEditor,
      "Used for backwards compatibility because we changed this to a weakref.")


    def __init__(self, name):
        self.name = name         # item's name

        # for backwards-compatibility we created the following attribute:
        # vEditor will be a weakref to editor and only a network will keep
        # the attribute ".editor" in order to be able to load old networks.
        # newer saved networks will use the method getEditor() to get a handle
        # to the editor
        self.vEditor = None      # comment: see above     

        self._modified = False   # if the item is instanciated, or if certain
                                 # attributes are changed, for example,
                                 # through configure(), this will be set 'True'

        self._original = True    # used for saving networks: if set to False
                                 # indicates this object was created by the
                                 # user (such as adding a node to a network
                                 # or adding a port to a node using the node
                                 # editor

                                 
    def _setModified(self, modified):
        """set the _modified attribute. Users should not call this method"""
        
        assert modified in [True, False]
        self._modified = modified


    def _setOriginal(self, original):
        """set the _original attribute. Users should not call this method"""
        
        assert original in [True, False]
        self._original = original


class NetworkItems(NetworkItemsBase):
    """Base class for objects that can be added to a Canvas.
Network items sublassing this have to extend the buildIcons method to create
a Canvas geometry representing this item.
"""

    def __init__(self, name='NoName'):
        NetworkItemsBase.__init__(self, name)
        
        self.paramPanel = None
        self.iconMaster = None # canvas on which this item is placed
        self.id = None     # Tkinter.Canvas primitive ID that will correspond
                           # to this node
        self.iconTag = None# unique tag shared by all primitives used to
                           # draw this node's icon

        # editor and network are set in the addNode method of Network
        self.network = None # NetworkObject to which this node belongs

        self.objEditor = None
        self.dynamicComputeFunction = None
        
        self.selected = 0
        self.nodeScaleFactor = 1.0
        self.distScaleFactor = 1.0
        self.posx = 0
        self.posy = 0
        self.menu = None
        self.highlightOptions = {'highlightbackground':'red'}
        self.unhighlightOptions = {'highlightbackground':'gray50'}
        self.selectOptions = {'background':'yellow'}
        self.deselectOptions = {'background':'gray85'}    
        self.objectBrowser = None      # introspect object window
        self.editFuncWindowWidth = 500 # width and height of source code editor
        self.editFuncWindowHeight = 200
        self.netSwitchOriginal = None
        self.frozen = False  # set to True to prevent node from running
        self.isSchedulingNode = False # if set to 1, this node and its children
                                  # will not be scheduled. Example: the
                                  # Iterate Node in Vision.StandardNodes

        # lock that needs to be acquired before node can be modified
        # FIXME: we have to update all methods operating on nodes to make
        # them thread safe
        self.runLock = threading.RLock()
        
        # table of functions to call for specific mouse events on canvas
        self.mouseButtonFlag = 0
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
        self.mouseAction = {}
        for event in self.mouseActionEvents:
            self.mouseAction[event] = None

        self.mouseAction['<Button-3>'] = self.postItemMenu
            

    def toggleFrozen_cb(self, event=None):
        if self.frozen:
            self.unfreeze()
        else:
            self.freeze()
        self.frozen = not self.frozen
        self.frozenTk.set(self.frozen)
        self._setModified(True)


    def freeze(self):
        # Note: whether color by library is on or off, we always need to color
        # the node back to the frozen color after deselecting this node 
        col = '#b6d3f6'  # light blue color
        self.unfreezeCol = self.setColor(col)
        self.deselectOptions["fill"] = col
        

    def unfreeze(self):
        # here we have to be more careful and check which mode is currently
        # on: color node by library 0/1. Depending on the status we need
        # to set a different deselect color
        #self.setColor(self.unfreezeCol)
        if self.editor.colorNodeByLibraryTk.get() == 1:
            if self.library is not None:
                col = self.library.color
            else: col = "gray85"
        else:
            col =  "gray85"
        self.deselectOptions['fill'] = col
        self.setColor(col)
        #self.schedule()


    def run(self, force=0, debug=False):
        """run this node.
if force is set, the node will run regardless of the availability of new data.
return 0 if run failed. (Thread safe)"""
        #print "NetworkItems.run", self.name, force, self.forceExecution, self.network.forceExecution
        if force or self.forceExecution:
            self.forceExecution = 1
        elif self.frozen:
            return
        # acquire the node's lock before doing anything to it
        #print "    noderun acquire runLock"

        ed = self.getEditor()

        self.runLock.acquire()

##         import traceback
##         print '******************', self.name
##         traceback.print_stack()

        try:
            ## FIXME ... this is necessary here but is also done in self.computeFunction()

            # if forceExecute is set, we run the node regardless of newdata
            # else we test that at least one parent present new data before
            # running the node
            from NetworkEditor.macros import MacroNode, MacroInputNode, MacroOutputNode
            if self.forceExecution == 0 \
               and self.network.forceExecution == 0 \
               and isinstance(self, MacroInputNode) is False \
               and isinstance(self, MacroOutputNode) is False \
               and len(self.inputPorts) > 0:
                newdata = 0
                for p in self.inputPorts:
                    # here we don't check if the data are valid 
                    # because they are not on the input port yet
                    if p.hasNewData():
                        newdata = 1
                        break
                if newdata == 0:
                    #print 'No new data for', self.name
                    self.runLock.release()
                    return 1

            self.forceExecution = 1
            if isinstance(self, MacroNode) and not self.hasRun:
                    self.macroNetwork.forceExecution = 1

            if isinstance(self, MacroInputNode) is False:
                for lOutputPort in self.outputPorts:
                    lOutputPort.outputData('no data yet')
                if self.isSchedulingNode:
                    self.network.setChildrenOutputToNoDataYet(self)

            if ed.hasGUI and ed.flashNodesWhenRun:
                c = self.iconMaster
                if c is not None:
                    c.tk.call((c._w, 'itemconfigure', self.innerBox, 
                               '-outline', '#FF0000', '-width', 4))
                col = '#000000'
                if (os.name != 'nt') \
                  or not ed.withThreads:
                    ed.update_idletasks()

            if not self.editor.hasGUI: # detached process
                if hasattr(self.network, 'communicator'): # for macro networks
                    self.network.communicator.handleCommunications()

##                 connid = net.socket.fileno()
##                 ifd, ofd, efd = select([connid], [], [], 0)

##                 if connid in ifd:
##                     conn, addr = self.network.socket.accept()
##                     net.socketConnections.append(conn)
##                     print 'Connected by', addr

##                 inids = map( lambda x: x.fileno(), net.socketConnections )
##                 ifd, ofd, efd = select(inids, [], [], 0)

##                 for conn in net.socketConnections:
##                     if conn.fileno() in ifd:
##                         input = conn.recv(4096) #os.read(_pid, 16384)
##                         if len(input)==0: # client diconnected
##                             net.connections.remove(conn)
##                         else:
##                             if debug:
##                                 procid = os.getpid()
##                                 print "process %d input"%procid, repr(input)
##                             mod = __import__('__main__')
##                             exec(input, mod.__dict__)

            if debug:
                print 'in run', self.name, debug
                net = self.network
                net.debugCmd = None
                # FIXME .. not sure this is the proper way to make a variable
                # known in the python shell
                d = sys.modules['__main__'].__dict__
                d['node'] = self 
                debugCmd = net.waitForDebugCommand()

            stat = self.computeFunction()

            if ed.hasGUI and ed.flashNodesWhenRun and stat!='Stop':
                if col=='#557700': # after successfull run of failed node
                    col = self.colorBeforeFail
                    #self.dirty = 1
                #else:
                    #self.dirty = 0
                if c is not None:
                    c.tk.call((c._w, 'itemconfigure', self.innerBox,
                               '-outline', col, '-width', 1))

            if self.network.execStatus != 'stop':
                self.forceExecution = 0

            self.runLock.release()

            if stat == 'Go':
                # force execution of children nodes of trigger output port
                if len(self.specialOutputPorts) \
                  and len(self.specialOutputPorts[0].children):
                    self.scheduleChildren(portList=[self.specialOutputPorts[0]])

            if stat is None:
                return 1
            else:
                return stat

        except KeyboardInterrupt, e:
            raise(KeyboardInterrupt, e)
        except:
            print
            print "***********************************************************"
            print "*** ERROR while executing node: ", self.name
            print "***********************************************************"
            self.forceExecution = 0
            traceback.print_exc()
            if ed.hasGUI and ed.flashNodesWhenRun:
                if col != '#557700':
                    self.colorBeforeFail = col
                c.tk.call((c._w, 'itemconfigure', self.innerBox,
                           '-outline', '#557700'))
                #self.setColor('#557700')
            self.runLock.release()
            return 'stop'


    def postItemMenu(self, event):
        if self.network.postedMenu:
            self.network.postedMenu.unpost()
            self.network.postedMenu = None
        elif self.menu:
            self.menu.post(event.x_root, event.y_root)
            self.network.postedMenu = self.menu


    def editNodeMenu(self, type, *args, **kw):
        apply( eval("self.menu."+type), args, kw )
        

    def __repr__(self):
        return '<%s %s>'%(self.__class__.__name__, self.name)

    
    def rename(self, name, tagModified=True):
        self.name=name
        if tagModified is True:
            self._setModified(True)


    def beforeAddingToNetwork(self, network):
        # get's called when a node is instanciated in a network
        #print 'beforeAddingToNetwork:', self.name 
        pass
    

    def afterAddingToNetwork(self):
        # get's called when a node is instanciated in a network
        #print 'afterAddingToNetwork:', self.name
        pass
        

    def beforeRemovingFromNetwork(self):
        # get's called when a node is deleted from a network
        #print 'beforeRemovingFromNetwork:', self.name
        pass
        

    def afterRemovingFromNetwork(self):
        # get's called when a node is deleted from a network
        #print 'afterRemovingFromNetwork:', self.name
        pass


    def highlight(self, event=None):
        pass
        

    def unhighlight(self, event=None):
        pass


    def select(self):
        self.selected = 1
        if self.iconMaster:
            self.iconMaster.addtag_withtag('selected', self.iconTag)


    def deselect(self):
        self.selected = 0
        if self.iconMaster:
            self.iconMaster.dtag(self.iconTag, 'selected')


    def deleteIcon(self):
        # delete what the item has to delete
        ed = self.getEditor()
        if self.iconMaster:
            self.iconMaster.delete(self.iconTag)
            self.iconTag = None
            
            # Note: I am not sure if we have to destroy the menu at all
            # to avoid memory leaks). But if we do destroy, we have to set
            # postedMenu to None if menu == postedMenu
            if ed.currentNetwork is None:
                return
            if self.menu:
                self.menu.unpost()
                self.network.postedMenu = None
                self.menu.destroy()
                self.menu = None


    def gettags(self):
        if self.iconMaster and self.iconTag:
            return self.iconMaster.gettags(self.iconTag)
        

    def buildIcons(self, canvas):
        """method to be implmented by subclass
        this method should create the geometric primitives for this item
        and tag them all with self.iconTag
        define its uniqueTag
        set its tags
        """

        ed = self.getEditor()

        self.frozenTk = Tkinter.IntVar()
        self.frozenTk.set(self.frozen)
        
        self.paramPanel = ParamPanel(self, master=None, title=self.name,
                                     applyFun=self.schedule_cb,
                                     dismissFun=self.hideParamPanel)
        if self.menu is None:
			# got rid of useless tearoff
            self.menu = Tkinter.Menu(ed, title=self.name, tearoff=False)
            self.menu.add_separator()

            if ed.hasGUI:
                self.menu.bind("<Any-Button>", ed.myButtonPress, '+')
        self.iconMaster = canvas
        

    def hideParamPanel(self, event=None):
        self.paramPanel.hide()


    def schedule_cb(self):
        # virtual method, has to be implemented by subclass
        pass


    def introspect(self):
         if self.objectBrowser is None:
             self.objectBrowser = ObjectBrowser(
                 self, rootName=self.name,
                 title='Introspect Node: %s'%self.name,
                 refresh=self._introspectCB)
         else:
             self.objectBrowser.show()


    def _introspectCB(self):
        """helper method used for the introspect data GUI"""
        return self


    def deletePort(self, p, resize=True):
        """Delete a port from a node. Removes it from the list of ports,
updates the portsDescr list and return the descriptin of the deleted port,
renumber all ports after this ports and mark them modified. Update code.
"""
        # NOTE: this method moved here because we want to subclass it in
        # NetworkNode and in MacroBase
        
        net = self.network
        # save configuration of port about to be deleted
        #cfg = p.configure()

        from ports import InputPort, OutputPort, SpecialInputPort, \
             SpecialOutputPort
        
        # delete port Icon
        if p.visible:
            p.deleteIcon()

        # remove port from list
        ports = None
        if isinstance(p, SpecialInputPort):
            self.specialInputPorts.remove(p)

        elif isinstance(p, SpecialOutputPort):
            self.specialOutputPorts.remove(p)

        elif isinstance(p, InputPort):
            ports = self.inputPorts
            if p.widget and self.getEditor() is not None:
                p.deleteWidget()
                p.deleteIcon()
            self.inputPorts.remove(p)
            del self.inputPortsDescr[p.number]
                
        elif isinstance(p, OutputPort):
            ports = self.outputPorts
            self.outputPorts.remove(p)
            del self.outputPortsDescr[p.number]

        else:
            print "FAILED. Port is neither of class InputPort or OuputPort!"
            return

        # remove all connections from this port
        self.network.deleteConnections(p.connections, 0)

        if self.getEditor() is not None:
            p.relposx = p.computePortPosX()

        # renumber the ports
        if ports:
            for i in range(p.number, len(ports)):
                port = ports[i]
                port.number = i
                if port.visible:
                    port.updateIconPosition()
        
        # delete circular referneces
        del p.data
        del p.node
        del p.network
        del p.vEditor
        del p

        if resize and self.getEditor() is not None:
            self.autoResizeX()
