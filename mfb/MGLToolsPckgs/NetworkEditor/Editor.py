#########################################################################
#
# Date: Nov. 2001  Authors: Michel Sanner, Daniel Stoffler
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
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/Editor.py,v 1.84 2009/07/29 16:48:58 sanner Exp $
#
# $Id: Editor.py,v 1.84 2009/07/29 16:48:58 sanner Exp $
#

import Tkinter, Pmw
import string, types

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import kbComboBox
from mglutil.util.callback import CallBackFunction

from NetworkEditor.ports import InputPort, OutputPort
from NetworkEditor.widgets import WidgetEditor
from NetworkEditor.widgets import PortWidget, widgetsTable, createWidgetDescr
from NetworkEditor.gridEditor import GridEditor

## TODO
#
# expose more things, like port color, tags, Tk options
# expose widgets
# write source code describing node
# Disable OK CANCEL in node editor while port editors are open
#

class ObjectEditor:
    """Base class for editors such as node and port editor"""

    def __init__(self, object, type, master=None):
        """Contructor of the editor.
    object is the obect the editor exposes (i.e. a node of a port for
instance).
    type is a string used to name the Editor window 'Node Editor' or 'Port
Editor'. master
    master is an optional container into which to place the editor. If ommited
the editor will appear in its own top level.
"""
        self.nbEditorWindows = 0 # count number of sub windows open
                                   # when more than 1 disable ok apply cancel
                                   # buttons
        self.obj = object # obejct to be edited (node or port)
        self.type = type
        if master is None:
            master = Tkinter.Toplevel()
        self.createForm(master)
        self.values = {} # dict of values describing state of the form
        self.modal = 0
        

    def createForm(self, master):
        """Build the form. Every editor has a frame called top followed by
an Entry allowing to change the edited-object's name.
Every editor also has Ok, Apply, Cancel buttons as the bottom of the form.
These buttons are in a frame called okFrame which is a child of top.
"""
        self.top = Tkinter.Frame(master)
        self.top.master.title(self.type+' Editor: '+self.obj.name)
        self.top.master.protocol('WM_DELETE_WINDOW',self.Dismiss)
        # node name
        self.nameGroup = w = Pmw.Group(self.top, tag_text=self.type+' Name')
        self.nameTk = Tkinter.StringVar()
        self.nameEntry = Tkinter.Entry( w.interior(), textvariable=self.nameTk)
        self.nameEntry.bind('<Return>', self.nameEntryChange_cb)
        self.nameTk.set(self.obj.name)
        self.nameEntry.pack(padx = 6, pady = 6, expand='yes', fill='x')
        w.pack(padx = 6, pady = 6, expand='yes', fill='both')
        self.addOkApplyCancel()
        

    def addOkApplyCancel(self):
        """Add the Ok, Apply and Cancel buttons
"""
        self.okFrame = f = Tkinter.Frame(self.top)
        self.okButton = Tkinter.Button(f, text='OK', command=self.OK)
        self.okButton.pack(side='left', expand=1, fill='x')
        self.applyButton = Tkinter.Button(f, text='Apply',
                                          command=self.Apply)
        self.applyButton.pack(side='left', expand=1, fill='x')
        self.cancelButton = Tkinter.Button(f, text='Cancel',
                                           command=self.Cancel)
        self.cancelButton.pack(side='right', expand=1, fill='x')
        f.pack(side='bottom', expand=1, fill='x')
        self.top.pack(padx=10, pady=10, expand='yes', fill='both')


    def manageEditorButtons(self):
        """Helper function to enable/disable the ok apply cancel buttons.
These buttons are disabled if another window is opened and needs to be closed
before this editor can be closed.
"""
        if self.nbEditorWindows > 0:
            self.applyButton['state'] = 'disabled'
            self.okButton['state'] = 'disabled'
            self.cancelButton['state'] = 'disabled'
        else:
            self.applyButton['state'] = 'normal'
            self.okButton['state'] = 'normal'
            self.cancelButton['state'] = 'normal'
 
    def nameEntryChange_cb(self, event=None):
        # callback fron <return> key in Entry holding name
        pass
    
    
    def Apply(self, event=None):
        """Callback for Apply Button"""
        pass

    def OK(self, event=None):
        """Callback for OK Button, calls Apply and Dismiss"""
        self.Apply()
        self.Dismiss()

    def Cancel(self):
        """Callback for Cancel Button"""
        self.Dismiss()

    def Dismiss(self, event=None):
        """Destroy edit form and reset objcet's point to editor"""
        if not self.modal:
            self.top.master.destroy()
            self.obj.objEditor = None
        else:
            self.top.master.quit()

    def go(self):
        """method for starting an editor in modal form (i.e. the application
blocks until the editor is dismissed
"""
        self.modal=1
        self.top.master.mainloop()
        self.top.master.destroy()
        return self.values
        
        

class NodeEditor(ObjectEditor):
    """Node Editor. Allows to rename, add input and output ports, modifed
the node's functions and start editors for ports and widgets"""

    def __init__(self, node, master=None):
        ObjectEditor.__init__(self, node, 'node', master)
        self.gridEditor = None         # widget grid configuration GUI
        self.funcEditorDialog = None   # edit source code GUI

    
    def nameEntryChange_cb(self, event=None):
        """apply the new name to the node and remember it has been modified"""
        name = self.nameTk.get()
        self.obj.configure(name=name)
        if self.funcEditorDialog is not None:
            self.funcEditorDialog.top.title(
               "Code editor: Node %s"%self.obj.name)
        

    def Apply(self, event=None):
        self.nameEntryChange_cb()
        self.Dismiss()


    def Dismiss(self, event=None):
        if self.funcEditorDialog:
            self.funcEditorDialog.hide()
            self.funcEditorDialog = None
        if self.gridEditor is not None:
            self.gridEditor.Cancel_cb()
            self.gridEditor = None

        for p in self.obj.inputPorts:
            self.deletePortButtons(p)
        for p in self.obj.outputPorts:
            self.deletePortButtons(p)
        ObjectEditor.Dismiss(self)

        
    def createForm(self, master):
        """Create standard editor form and add a Pmw Group for input ports,
one for output ports and a check button for viewing the source node's code.
"""
        ObjectEditor.createForm(self, master)

        # input Ports
        w = Pmw.Group(self.top, tag_pyclass=Tkinter.Button,
                      tag_command=self.newInputPort,
                      tag_text='Add Input Port')
        ipf = self.ipFrame = Tkinter.Frame(w.interior(),)
        Tkinter.Label(ipf, text='port #').grid(row=0, column=0, sticky='ew')
        Tkinter.Label(ipf, text='name').grid(row=0, column=1, sticky='ew')
        Tkinter.Label(ipf, text='edit\nport').grid(row=0, column=2, sticky='ew')
        Tkinter.Label(ipf, text='edit\nwidget').grid(row=0, column=3,
                                                    sticky='ew')
        Tkinter.Label(ipf, text='del.\nport').grid(row=0, column=4,
                                                    sticky='ew')

        for p in self.obj.inputPorts:
            self.addPortToForm(p, ipf)

        self.ipFrame.pack(expand=1, fill='x', padx=3, pady=3)
        w.pack(padx=6, pady=6, expand='yes', fill='both')

        # output Ports
        w = Pmw.Group(self.top, tag_pyclass=Tkinter.Button,
                      tag_command=self.newOutputPort,
                      tag_text='Add Output Port')
        opf = self.opFrame = Tkinter.Frame(w.interior(),)
        Tkinter.Label(opf, text='port #').grid(row=0, column=0, sticky='ew')
        Tkinter.Label(opf, text='name').grid(row=0, column=1, sticky='ew')
        Tkinter.Label(opf, text='edit\nport').grid(row=0, column=2,sticky='ew')
        Tkinter.Label(opf, text='del.\nport').grid(row=0, column=4,
                                                   sticky='ew')

        for p in self.obj.outputPorts:
            self.addPortToForm(p, opf)

        self.opFrame.pack(expand=1, fill='x', padx=3, pady=3)
        w.pack(padx = 6, pady = 6, expand='yes', fill='both')

        # widget grid editor
        w = Pmw.Group(self.top, tag_text='widgets grid config')
        self.editGridVarTk = Tkinter.IntVar()
        self.editGridButton = Tkinter.Checkbutton(
            w.interior(), text='Edit ...', var=self.editGridVarTk,
            command=self.editGrid_cb )
        self.editGridButton.pack(expand='yes', fill='x', padx=3, pady=3)
        w.pack(padx = 6, pady = 6, expand='yes', fill='both')
        
        # compute function
        w = Pmw.Group(self.top, tag_text='compute function')
        self.editButtonVarTk = Tkinter.IntVar()
        self.editButton = Tkinter.Checkbutton(
            w.interior(), text='Edit ...', var=self.editButtonVarTk,
            command=self.editFunction_cb )
        self.editButton.pack(expand='yes', fill='x', padx=3, pady=3)
        w.pack(padx = 6, pady = 6, expand='yes', fill='both')
        self.manageEditorButtons()
        
 
    def addPortToForm(self, port, frame):
        """create a new line of widgets for a new port in the node editor"""
        line = port.number+1

        port.portLabelTk = Tkinter.Label(frame, text=str(port.number))
        port.portLabelTk.grid(row=line, column=0,  sticky='ew')

        port.portNameTk = Tkinter.Label(frame, text=str(port.name))
        port.portNameTk.grid(row=line, column=1, sticky='w')
        
        cb1 = CallBackFunction( self.editPort, port)
        cb2 = CallBackFunction( self.deletePort, port)
        cbvar = Tkinter.IntVar()
        if port.objEditor is not None:
            self.nbEditorWindows += 1
        cbvar.set(int(not port.objEditor==None))
        port.portEditCB = Tkinter.Checkbutton(frame, command=cb1,
                                              variable=cbvar)
        port.portEditCB.var = cbvar
        port.portEditCB.grid(row=line, column=2, sticky='ew')
        port.portDelCB = Tkinter.Checkbutton(frame, command=cb2)
        port.portDelCB.grid(row=line, column=4, sticky='ew')
        if port.widget:
            cb = CallBackFunction( self.editWidget, port)
            port.editWtk = Tkinter.Checkbutton(self.ipFrame,command=cb)
            port.editWtk.grid(row=port.number+1, column=3, sticky='ew')
            
            
    def newInputPort(self, event=None):
        """create a new input port with a default name"""

        self.obj.addSaveNodeMenuEntries()

        port = apply( self.obj.addInputPort, (), {} )
        port._setModified(True)
        
        port.editWtk = None
        port.delWtk = None

        # add port to node edition form
        self.addPortToForm( port, self.ipFrame )
        # and update funcEditorDialog
        if self.funcEditorDialog is not None:
            self.funcEditorDialog.settext(self.obj.sourceCode)
        

    def newOutputPort(self, event=None):
        # create a new output port with a default name
        self.obj.addSaveNodeMenuEntries()

        port = apply( self.obj.addOutputPort, (), {} )
        port._setModified(True)

        # add port to node edition form
        self.addPortToForm( port, self.opFrame )
        # and update funcEditorDialog
        if self.funcEditorDialog is not None:
            self.funcEditorDialog.settext(self.obj.sourceCode)


    def deletePortButtons(self, port):
        """removes widgets for this port from node editor"""

        node = port.node
        
        # remove buttons fot this port form the node editor panel:
        if port.portLabelTk is not None:
            port.portLabelTk.destroy()
        if port.portNameTk is not None:
            port.portNameTk.destroy()
        if port.portEditCB is not None:
            port.portEditCB.destroy()
        if port.portDelCB is not None:
            port.portDelCB.destroy()
        if port.widget:
            if port.editWtk is not None:
                port.editWtk.destroy()

        port.portLabelTk = None
        port.portNameTk = None
        port.portEditCB = None
        port.portDelCB = None
        port.editWtk = None

        
    def deletePort(self, port, event=None):
        """delete a port"""

        self.obj.addSaveNodeMenuEntries()

        # delete port editor is any
        if port.objEditor:
            port.objEditor.Cancel()

        # if the node editor is up update it
        if port.node.objEditor:
            self.deletePortButtons(port)

        # get a handle to port befoer we lose it in deletePort
        node = port.node

        # delete port editor is any
        if port.objEditor:
            port.objEditor.Cancel()
            
        # delete the port from the node's list of ports
        self.obj.deletePort(port, resize=True)
        
        # renumber remaining input ports in editor panel
        if isinstance(port, InputPort):
            for p in node.inputPorts:
                p.portLabelTk.configure(text=str(p.number))
            
        # renumber remaining output ports in editor panel
        elif isinstance(port, OutputPort):
            for p in node.outputPorts:
                p.portLabelTk.configure(text=str(p.number))

        # and update funcEditorDialog
        if self.funcEditorDialog is not None:
            self.funcEditorDialog.settext(self.obj.sourceCode)


    def editGrid_cb(self, event=None):
        """open a widget grid configuration editor"""
        
        # Note, every time activate the checkbutton, we want to build a fresh
        # window, since in the meantime, somebody could have added a new widget
        if self.editGridVarTk.get() == 1:
            self.nbEditorWindows += 1
            self.manageEditorButtons()
            self.gridEditor = GridEditor(node=self.obj)
        else:
            self.gridEditor.Cancel_cb()
            self.gridEditor = None


    def editFunction_cb(self, event=None):
        """callback function of edit source code check button.
Manages button's state, and status of Ok, Apply and Cancel buttons
"""
        if self.editButtonVarTk.get() == 1:
            self.nbEditorWindows += 1
            self.manageEditorButtons()
            if self.funcEditorDialog is None:
                self.displaySourceCode()
            else:
                self.funcEditorDialog.show()
            return
        else:
            self.funcEditorDialog.cancelCmd()


    def displaySourceCode(self):
        """If no source code editor is created yet build one, else just show it
If idlelib is found we use it, else we use default Pmw-based widget.
"""
        if self.funcEditorDialog is None:
            self.funcEditorDialog = SourceCodeEditor(
                    node=self.obj, editor=self)
        else:
            self.funcEditorDialog.show()


    def editPort(self, port, event=None):
        # create a port editor
        if port.objEditor is not None:
            status = port.portEditCB.var.get()
            if status == 1:
                #port.portEditCB.toggle()
                port.objEditor.top.master.deiconify()
            else:
                port.objEditor.top.master.withdraw()
            return

        else:
            port.objEditor = ipEditor = PortEditor(port)
            self.nbEditorWindows += 1
            self.manageEditorButtons()               


    def editWidget(self, port, event=None):
        """start widget editor"""
        if port.widget.objEditor:
            port.widget.objEditor.Cancel_cb()
        else:
            port.widget.edit()



class PortEditor(ObjectEditor):

    def __init__(self, port, master=None):
        """PortEditor constructor.
Port is the port which we want to edit.
"""
        if isinstance(port, InputPort):
            title = 'Input Port'
        elif isinstance(port, OutputPort):
            title = 'Output Port'
        else:
            title = 'Port'
            
        ObjectEditor.__init__(self, port, title, master)
        port.objEditor = self
        self.node = port.node
        self.callbackEditorDialog = None # code editor window
        self.abortApply = 0 # setWidget() can remove port
        nodeEditor = self.node.objEditor
        if nodeEditor is not None:
            port.portEditCB.select()
            nodeEditor.nbEditorWindows -= 1
            nodeEditor.manageEditorButtons()

            
    def createForm(self, master):
        """Create default form and add widgets for setting data type,
start the widget editor, set the required, singleConnection and toolTip
"""
        port = self.obj
        
        ObjectEditor.createForm(self, master)
        #w = Tkinter.Frame(self.top, relief='groove')

        # add protocol for killing this window
        self.top.master.protocol("WM_DELETE_WINDOW", self.Cancel)
        
        w = Pmw.Group(self.top, tag_text='Port options')

        # datatype
        vpe = port.getEditor()
        l = vpe.typeManager.portTypeInstances.keys()
        l.sort()
        self.dataType = kbComboBox( w.interior(), label_text='data type:',
            labelpos='w', entryfield_entry_width=14,
            scrolledlist_items = l )
        if port.datatypeObject:
            self.dataType.setentry(port.datatypeObject['name'])
        self.dataType.grid()

        # Edit Callbacks
        w2 = Pmw.Group(self.top, tag_text='Port callbacks')

        l2 = ['beforeConnect', 'afterConnect', 'beforeDisconnect',
             'afterDisconnect']
        self.chooseCallback = kbComboBox(
            w2.interior(),
            label_text='edit source code',
            labelpos='w', entryfield_entry_width=14,
            scrolledlist_items = l2,
            selectioncommand=self.editCallback)
        self.chooseCallback.grid()
        
        w1 = None
        if isinstance(port, InputPort):
            # required
            var = Tkinter.IntVar()
            var.set(port.required)
            tk = Tkinter.Checkbutton( w.interior(), text='required',
                                      indicatoron=1, variable=var)
            tk.var = var
            tk.grid()
            self.requiredTk = tk
            
            # singleConnection
            from NetworkEditor.macros import MacroNode
            if isinstance(port.node, MacroNode):
                # to avoid multiple list enclosure, MacroInputNode
                # must always be singleConnection.
                # to have multiple connections, 
                # the solution is to duplicate the input port in the macronode
                # (there is no such need for the MacroOutputNode)
                connTypes = ['True']
            else:
                connTypes = ['True', 'False', 'auto']
            self.singleConnectionTk = kbComboBox(
                w.interior(), label_text='single connection:', labelpos='w',
                scrolledlist_items=connTypes, entryfield_entry_width=15 )

            status = str(port.singleConnection)
            self.singleConnectionTk.selectitem(status)
            self.singleConnectionTk.grid()
            
            # widget section
            w1 = Pmw.Group(self.top, tag_text='Widget')

##             # port has a widget add Unbind button
##             if port.widget:
##                 var = Tkinter.IntVar()
##                 tk = Tkinter.Checkbutton(
##                     w.interior(), text='single connection',
##                     variable=var, indicatoron=1)
##                 tk.var = var
##                 tk.grid()
##                 self.unbindWidget = tk
                
            # BIND WIDGET
            widgetList = []
            if port.widget: # this port has a widget
                widgetList.append('Unbind')
            if port._previousWidgetDescr:
                widgetList.append('Rebind')
            widgetList = widgetList + widgetsTable.keys()
            widgetList.sort()

            # widget
            self.widgetType = kbComboBox(
                w1.interior(), label_text='Type:', labelpos='w',
                scrolledlist_items=widgetList, entryfield_entry_width=15 )

            if port.widget:
                self.widgetType.set(port.widget.__class__.__name__)
            
            self.widgetType.grid(row=0, column=0, padx=6, pady=6)

            masterList = ['ParamPanel', 'Node']
            if len(self.obj.network.userPanels.keys()):
                masterList += self.obj.network.userPanels.keys()
                
            self.widgetMaster = kbComboBox(
                w1.interior(), label_text='Place in:', labelpos='w',
                scrolledlist_items=masterList, entryfield_entry_width=15,
                selectioncommand=self.setMaster_cb)
                # self.setMaster_cb() method will update the GUI but not
                # call setMaster(), only Apply button will do that
            
            self.widgetMaster.grid(row=1, column=0, padx=6, pady=6)
            self.widgetMaster.selectitem('ParamPanel')
            # set the choice to current master
            if port.widget:
                if port.widget.inNode is True:
                    self.widgetMaster.selectitem('Node')
                else:
                    if port.widget.master in self.obj.network.userPanels.keys():
                        self.widgetMaster.selectitem(port.widget.master)
                        
            self.editWidgetVarTk = Tkinter.IntVar()
            self.editWidgetButton = Tkinter.Checkbutton(
                w1.interior(), text='Edit Widget...',
                var=self.editWidgetVarTk, command=self.toggleWidgetEditor)

            self.editWidgetButton.grid()
            if self.obj.widget is not None:
                if self.obj.widget.objEditor:
                    self.editWidgetVarTk.set(1)
            

        w.pack(padx = 6, pady = 6, expand='yes', fill='both')

        w2.pack(padx = 6, pady = 6, expand='yes', fill='both')

        if w1:
            w1.pack(padx = 6, pady = 6, expand='yes', fill='both')

        self.tt = Pmw.ScrolledText(self.top, usehullsize=1, borderframe=1,
                       labelpos = 'nw', label_text='ToolTip',
                       hull_width = 300, hull_height = 100, text_wrap='none' )
        if port.balloon:
            self.tt.settext(port.balloon)
        self.tt.pack(padx=5, pady=5, fill='both', expand=1)
        
        self.top.pack(padx=10, pady=10, expand='yes', fill='both')
    
    def nameEntryChange_cb(self, event=None):
        """apply the new name to the node and remember it has been modified"""
        pass
    # disabled callback because we want this to run only if Apply is pressed
##          name = self.nameTk.get()
##          port = self.obj
##          if name != port.name:
##              port.configure(name=name)


    def editCallback(self, event=None):
        mode = self.chooseCallback.get()
        if mode in self.obj.callbacks.keys():
            self.displayCallbackSourceCode(mode)

        
    def displayCallbackSourceCode(self, mode):
        if self.callbackEditorDialog is not None:
            self.callbackEditorDialog.hide()
        self.callbackEditor = None
        self.callbackEditorDialog = CallbackEditor(
            port=self.obj, mode=mode)


    def OK(self, event=None):
        ObjectEditor.OK(self)
        nodeEditor = self.obj.node.objEditor
        if nodeEditor:
            nodeEditor.nbEditorWindows -= 1
            nodeEditor.manageEditorButtons()
            self.obj.portEditCB.toggle()


    def Cancel(self):
        """Callback for Cancel Button"""
        nodeEditor = self.obj.node.objEditor
        port = self.obj
        ObjectEditor.Cancel(self)
        if nodeEditor:
            nodeEditor.nbEditorWindows -= 1
            nodeEditor.manageEditorButtons()
            port.portEditCB.toggle()        
        
    def Apply(self, event=None):
        """Callback for Apply Button"""
        opts = {}
        port = self.obj
        name = self.nameTk.get()
        if name != self.obj.name:
            port.configure(name=name)
            # and rename entry in node editor window
            if hasattr(self.obj, 'portNameTk') and \
               self.obj.portNameTk is not None:
                self.obj.portNameTk.configure(text=name) 

        datatype = self.dataType.get()
        if datatype != port.datatypeObject['name']:
            opts['datatype'] = datatype
            
        if isinstance(port, InputPort):
            required = self.requiredTk.var.get()==1
            if required != port.required:
                opts['required'] = required

            singleConnection = self.singleConnectionTk.get()
            if singleConnection == 'True':
                singleConnection = True
            elif singleConnection == 'False':
                singleConnection = False
            if singleConnection != port.singleConnection:
                opts['singleConnection'] = singleConnection

            widgetName = self.widgetType.get()

            if widgetName == 'Rebind':
                port.rebindWidget()
                widgetList = ['Unbind'] +  widgetsTable.keys()
                widgetList.sort()
                self.widgetType.setlist(widgetList)
                self.widgetType.set('Unbind')

            elif widgetName == 'Unbind':
                port.unbindWidget()
                widgetList = ['Rebind'] +  widgetsTable.keys()
                widgetList.sort()
                self.widgetType.setlist(widgetList)
                self.widgetType.set('Rebind')
                # destroy edit widget checkbutton to node editor 
                if port.editWtk:
                    port.editWtk.destroy()
                    port.editWtk = None
                    
            elif widgetName:
                if port.widget:
                    currentWidget = port.widget
                    oldwname = currentWidget.__class__.__name__
                else:
                    currentWidget = None
                    oldwname = None

                if widgetName != currentWidget.__class__.__name__:
                    # new widget
                    editWidget = self.editWidgetVarTk.get()
                    if editWidget:
                        # Start Widget Editor was check so get wdescr from it
                        form = WidgetEditor(
                            widgetsTable[widgetName].configOpts)
                        wdescr = form.go()
                        wdescr['class'] = widgetName
                        #for k,v in wdescr.items():
                        #    print k, v
                    else:
                        if currentWidget:
                            port._previousWidgetDescr=currentWidget.getDescr()
                        wdescr = createWidgetDescr(widgetName,
                                                   port._previousWidgetDescr)
                    if currentWidget:
                        wdescr['initialValue'] = port.widget.get()
                        port.deleteWidget()

                    port.createWidget(descr=wdescr)
                    if port.widget.inNode:
                        port.node.hideInNodeWidgets()
                        port.node.showInNodeWidgets()

            # add edit widget checkbutton to node editor if applicable,
            # such as if we rebind a widget, or create a new one
            if port.widget and not port.editWtk and \
               hasattr(port.node, 'objEditor') and \
               port.node.objEditor is not None:
                nodeEditor = port.node.objEditor
                cb = CallBackFunction( nodeEditor.editWidget, port)
                port.editWtk = Tkinter.Checkbutton(
                    nodeEditor.ipFrame,command=cb)
                port.editWtk.grid(row=port.number+1, column=3, sticky='ew')

            self.setMaster(self.widgetMaster.get())

        tt = self.tt.get()
        if tt[-1]=='\n':
            tt = tt[:-1]
        if tt != port.balloon and len(tt)>0:
            opts['balloon'] = tt
            
        if len(opts):
            apply( port.configure, (), opts)
            port.node.addSaveNodeMenuEntries()


    def toggleWidgetEditor(self, event=None):
        port = self.obj
        if port.widget is None:
            self.editWidgetVarTk.set(0)
            return

        if port.widget.objEditor is None:
            # open form
            port.widget.edit()
        else:
            # close form
            port.widget.objEditor.Cancel_cb()
            

    def setWidget(self, widgetName):
        # this method does the following
        # update the node editor panels
        # update node.widgetDescr
        # update the port object

        port = self.obj
        node = port.node

        if widgetName == 'rebind from Macro':
            # Here we rebind from macro node to original node
            macroPort = port.widgetInMacro['macroPort']
            wdescr = macroPort.node.widgetDescr[macroPort.name]
            port.widgetInMacro = {}
            self.rebindWidgetFromMacro(macroPort, wdescr)
            self.abortApply = 1 #after that the port no longer exists
            self.Dismiss()
            return

        elif widgetName == 'previous Node':
            # Here we rebind from macro node to original node
            wdescr = port.node.widgetDescr[port.name]
            port.node.objEditor.deletePortButtons(port)
            port.widgetInMacro = {}
            self.rebindWidgetFromMacro(port, wdescr)

            self.abortApply = 1
            self.Dismiss()
            return

        if port.widget is None and port._previousWidgetDescr is None and \
           widgetName is None or widgetName == '':
            return

        # if the port has a widget and the widget chooser in the panel
        # has the same type as the current widget we return
        # this happens when the apply or ok buttons are used and the
        # the widget combobox has not been changed
        if port.widget:
            if widgetName==port.widget.__class__.__name__:
                return

        if widgetName=='Unbind':
            w = 'Unbind'
            widgetList = ['Rebind'] +  widgetsTable.keys()
            self.widgetType.setlist(widgetList)

        elif widgetName=='Rebind':
            w = 'Rebind'
            widgetList = ['Unbind'] +  widgetsTable.keys()
            self.widgetType.setlist(widgetList)

        else:
            # if same widget as already bound: return
            if port.widget and widgetName==port.widget.__class__.__name__:
                return

            # build widget 
            port.createWidget()
            w = port.widget
            
            if isinstance(w, PortWidget):
                widgetList = ['Unbind']
            if port.widget: # current will become previous so
                widgetList.append('Rebind')
            widgetList = widgetList +  widgetsTable.keys()
            self.widgetType.setlist(widgetList)

        port.setWidget(w)
        wmaster = self.masterTk.get()
        
        # and set the master here:
        self.setMaster(wmaster)

        # set the master in the widgetDescr so that setMaster does not
        # rebuild the widget again if Apply is pressed twice or more
        if wmaster == 'Node':
            mMaster = 'node'
        else:
            mMaster = wmaster
        # if we unbind, the node has no widgetDescr so we have to test here
        if node.widgetDescr.has_key(port.name):
            node.widgetDescr[port.name]['master'] = mMaster

        # add/remove edit widget button if not there yet
        if w is not None and port.editWtk is None: # widget but no button
            nodeEd = node.objEditor
            cb = CallBackFunction( nodeEd.editWidget, port)
            port.editWtk = Tkinter.Checkbutton(nodeEd.ipFrame,command=cb)
            port.editWtk.grid(row=port.number+1, column=3, sticky='ew')
        elif w is None and port.editWtk is not None:
            port.editWtk.destroy()
            port.editWtk = None
            
##              if port.delWtk is None:
##                  cb = CallBackFunction( nodeEd.deletePort, port)
##                  port.delWtk = Tkinter.Checkbutton(nodeEd.ipFrame,command=cb)
##                  port.delWtk.grid(row=port.number+1, column=4, sticky='ew')



#    def widgetEditor():
#               
#            self.masterTk = kbComboBox(
#                w, label_text='Master:', labelpos='w',
#                scrolledlist_items = [])
#            self.masterTk.grid(row=lastrow, column=0, columnspan=2)
#
#            wmaster = None
#            if port.widget:
#                # MacroNodes are special: - the only widget for this port that
#                # can be selected is the one that has been bound from a node
#                # inside the macronetwork and the only master that can be
#                # chosen is the previous node
#                from NetworkEditor.macros import MacroNode
#                if isinstance(port.node, MacroNode):
#                    wname = 'previous Node'
#                    self.widgetType.setlist([wname])
#                    self.widgetType.selectitem(wname)
#                    mas = port.node.widgetDescr[port.name]['origMaster']
#                    if mas == 'node':
#                        mas = 'Node'
#                    wmaster = mas
#                else:
#                    name = None
#                    for name,wid in widgetsTable.items():
#                        if wid==port.widget.__class__:
#                            break
#                    if name:
#                        self.widgetType.selectitem(name)
#                        
#                # now choose the appropriate master in the scrollbox
#                if wmaster:
#                    self.updateMasterList(master=wmaster)
#                else:
#                    self.updateMasterList()
#                    
#            # is this a port where the widget has been bound to a macro node
#            elif len(port.widgetInMacro):
#                wname = 'rebind from Macro'
#                self.widgetType.setlist([wname])
#                self.widgetType.selectitem(wname)
#                mas = port.widgetInMacro['master']
#                if mas == 'node':
#                    mas = 'Node'
#                self.masterTk.setlist([mas])
#                self.masterTk.selectitem(mas)
#
#            # else initialize with previousWidget's master to make sure
#            # that a triggered by Apply or OK places it back to the right
#            # panel
#
#            elif port._previousWidgetDescr is not None:
#                widgetList = ['Rebind'] +  widgetsTable.keys()
#                self.widgetType.setlist(widgetList)
#
#                descr = port._previousWidgetDescr
#                if descr.has_key('master'):
#                    wmaster = descr['master']
#                    if wmaster == 'node':
#                        wmaster = 'Node'
#                else: # else used node's param panel (default)
#                    wmaster = 'ParamPanel'
#
#                self.updateMasterList(master=wmaster)
#
#            else:
#                # no widget, no master available then
#                self.updateMasterList(clear=1)


    def rebindWidgetFromMacro(self, port, wdescr):
        cfg0 = port.widget.getConstructorOptions()
        cfg0['master'] = wdescr['origMaster']
#        cfg0['visibleInNode'] = wdescr['origvisibleInNode']
        cfg0['visibleInNodeByDefault'] = wdescr['origvisibleInNodeByDefault']
        cfg1 = port.widget.configure()
        cfg1['master'] = wdescr['origMaster']
        cfg2 = port.widget.get()

        origport = wdescr['origPort']
        orignode = origport.node

        # 2) unbind widget and delete previousWidget
        port.setWidget('Unbind')
        port._previousWidgetDescr = None

        # 3) add widgetDescr to orignode
        del wdescr['origPort']
        del wdescr['origMaster']
#        del wdescr['origvisibleInNode']
        del wdescr['origvisibleInNodeByDefault']
            
        # 4) rebind widget to original node
        orignode.widgetDescr[origport.name] = wdescr
        origport.savedConfiguration = (cfg0, cfg1, cfg2)
        origport.createWidget()


    def setMaster_cb(self, event=None):
        # update GUI: if we change the master, we select in the widget list
        # the current widget whose master will be changed (for example, if
        # we are still in the mode 'unbind' or 'rebind')
        if self.obj.widget:
            self.widgetType.set(self.obj.widget.__class__.__name__)

    
    def setMaster(self, masterName):
        port = self.obj
        if port.widget is None and port._previousWidgetDescr is None:
            self.widgetMaster.component('entryfield').clear()

        if port.widget is None:
            return
        
        node = port.node

        if masterName=='Node':
            masterName = 'node'

        # save widget configuration
        wdescr = port.widget.getDescr()
        # save widget value
        wdescr['initialValue'] = port.widget.get()

        # FIXME, NOTE: IN THIS CURRENT RELEASE, WE DO NOT SUPPORT A MASTER
        # OTHER THAN NODE OR PARAMPANEL!! THE FOLLOWING CODE IS THEREFORE
        # NEVER EXECUTED. NOV-29-2003.
        # WE WILL RE-ACTIVATE THIS IN THE FUTURE
        
        # find if master is a Macro node
        masterlist = ['node', 'ParamPanel']
        if len(self.obj.network.userPanels.keys()):
            masterlist += self.obj.network.userPanels.keys()
        if masterName not in masterlist: # ok, this is a macro

            # Note: simply changing the master of a widget does NOT work:
            # we have to delete the widget and reconstruct it!
            # Unbind/Rebind from one node to another one DOES NOT work.

            # 1) save configuration of this widget to the MacroNode
            # so that the widget can be properly rebuilt
            oldmaster = wdescr['master']
            cfg0 = port.widget.getConstructorOptions()
            cfg0['master'] = 'ParamPanel'
            #cfg0['visibleInNode'] = 0
            cfg0['visibleInNodeByDefault'] = 0
            cfg1 = port.widget.configure()
            cfg1['master'] = 'ParamPanel'
            cfg2 = port.widget.get()

            # 2) unbind widget and delete previousWidgetDescr
            port.setWidget('Unbind')
            port._previousWidgetDescr = None
            self.widgetType.setlist([])
            port.node.widgetDescr[port.name] = wdescr
            del port.node.widgetDescr[port.name]

            # 3) connect this node to a MacroInputNode and up the 'tree'
            from NetworkEditor.macros import MacroNetwork
            net = port.node.network
            portNumber = port.number
            origNumber = port.number
            macroNode = port.node # at first iteration this is of course
                                  # port.node, from then on its the macro node
            while isinstance(net, MacroNetwork):
                ipnode = net.ipNode
                c = net.connectNodes(ipnode, macroNode, 0, portNumber)
                opt = c.deselectOptions
                opt['stipple'] = 'gray25'
                apply (c.iconMaster.itemconfigure, (c.iconTag,), opt)
                macroNode = net.macroNode
                portNumber = c.port1.number-1 # macroNodes have port#-1
                if macroNode.name == masterName:
                    break
                net = macroNode.network

            # 4) add saved configuration to MacroNode
            mip = macroNode.inputPorts[portNumber]
            mip.savedConfiguration = (cfg0, cfg1, cfg2)

            # 5) add widget to MacroNode
            wdescr['master'] = 'ParamPanel'
            macroNode.widgetDescr[mip.name] = wdescr
            mip.createWidget()
            newwidget = macroNode.inputPorts[portNumber].widget

            # 6) store information in original node and macro node
            port.widgetInMacro = {'macroNode':macroNode, 'macroPort':mip,
                                  'master':oldmaster, 'wdescr':wdescr}
            name = mip.name
            macroNode.widgetDescr[name]['origPort'] = port
            macroNode.widgetDescr[name]['origMaster'] = oldmaster
            #macroNode.widgetDescr[name]['origvisibleInNode'] = \
            #                                  wdescr['visibleInNode']
            macroNode.widgetDescr[name]['origvisibleInNodeByDefault']=\
                                          wdescr['visibleInNodeByDefault']

            # 7) close port editor window
            self.abortApply = 1
            self.Dismiss()
            return
        

        changeMaster=1
        if wdescr.has_key('master') and wdescr['master'] == masterName:
            changeMaster = 0
            
        # update the port description in the node
        oldmaster = wdescr['master']
        wdescr['master'] = masterName

        if changeMaster:
            port.widget.configure(master=masterName)
            # unbind widget (this destroys the old widget)
            #port.unbindWidget()
            # delete the not needed previousWidgetDescr
            #port._previousWidgetDescr = None
##              if port.node.isExpanded(): # do not bind widget to expanded node,
##                                         # this leads to unpredictable results!
##                  port.node.toggleNodeExpand_cb()

            # create new widget
            #port.createWidget(descr=wdescr) # create new widget
            #port.node.autoResize()
            #if port.node.inNodeWidgetsVisibleByDefault and not \
            #   port.node.isExpanded():
            #    port.node.toggleNodeExpand_cb()
            

    def updateMasterList(self, event=None, master=None, clear=0):
        """this method is called when a widget is selected and when the
        editor panel is build"""
        port = self.obj

        if master == [] or clear:
            self.masterTk.component('entryfield').clear()
            return

        from NetworkEditor.macros import MacroNetwork, MacroNode
        mymaster = self.masterTk.get()
        if not master:
            master = mymaster

        master = 'ParamPanel'
        if not master or master == '':
            if port.widget:
                mmaster = port.node.widgetDescr[port.name].get('master', None)
                if mmaster:
                    master = mmaster

        masterList = ['ParamPanel', 'Node']
        #macronet = 0

        # add all macro nodes in a 'macro tree'
        net = port.node.network
        while isinstance(net, MacroNetwork):
            macronode = net.macroNode
            masterList.append(macronode.name)
            net = macronode.network
            #macronet = 1
            
        #if not macronet and master == 'Macro':
        #    master = 'ParamPanel'

        self.masterTk.setlist(masterList)
        if master:
            self.masterTk.selectitem(master)

                
        
class InputPortWidgetEditor(ObjectEditor):
    """Widget editor class.
"""

    def __init__(self, widget, master=None):
        ObjectEditor.__init__(self, port, 'Input Port Widget', master)
        self.nameGroup.forget()
        self.createForm(master)

    def createForm(self, master):
        ObjectEditor.createForm(self, master)

        w = Pmw.Group(self.top, 'Widget Options')

        # datatype


class CodeEditorPmw:
    """Reusable Pmw TextDialog widget to edit source code, fitted for the
    needs of the various code editors"""

    def __init__(self, master=None, title='untitled', code=None):
        if code is None:
            code = ""
        lines = code.split('\n')
        height = (len(lines)+10) * 10
        if height > 300:
            height = 300

        width = (max(map(len, lines)) + 1) * 10
        if width > 600:
            width = 600
        elif width < 120:
            width = 120

        self.widget = Pmw.TextDialog(
                      master, scrolledtext_labelpos='n', title=title,
                      defaultbutton=None,
                      buttons=(),
                      label_text='Edit Code:',
                      scrolledtext_usehullsize=1,
                      scrolledtext_hull_width=width,
                      scrolledtext_hull_height=height)

        self.top = self.widget
        self.settext(code)

        # add frame
        frame = Tkinter.Frame(self.widget.interior())
        frame.pack(side='bottom', expand=1, fill='both')
        self.widget.status_bar = frame
        # add top
        self.widget.top = self.widget
        ed.top.protocol("WM_DELETE_WINDOW", self.cancelCmd)
        
    def settext(self, text):
        # settext replaces current text with new one, so no need for a clear()
        self.top.settext(text)


    def gettext(self, event=None):
        return self.top.getvalue()


    def clear(self):
        self.top.settext('')


class CodeEditorIdle:
    """Idle code editor window, fitted to the needs for our various editors"""

    def __init__(self, master=None, title='untitled',  code=None, font=None):
        
        from idlelib.EditorWindow import EditorWindow

        if code is None:
            code = ""
            
        lines = code.split('\n')
        height = len(lines)+5
        if height > 24:
            height = 24

        width = max(map(len, lines)) + 15
        if width > 80:
            width = 80
        elif width < 40:
            width = 40

        ed = self.widget = EditorWindow(width=width, height=height)
        self.top = self.widget.top

        
        # delete menu entry Close and Exit
        for entry in [
            'Close','Exit', 'New Window', 'Save As...', 'Save Copy As...']:

            ed.menubar.children['file'].delete(entry)
            
        #ed.menubar.children['run'].delete(0,'end')
        ed.menubar.delete('Run')
        
        # rebind a bunch of methods
        ed.io.text.bind("<<close-all-windows>>",self.cancelCmd)
        ed.top.bind("<<close-window>>",self.cancelCmd)
        # unbind a bunch of methods

        # FIXME: UNBIND SAVE SHORTCUTS: CTRL+SHIFT+S, ALT+SHIFT+S, F5, ALT+x
        
        ed.io.text.bind("<<open-new-window>>", self.pass_cb)

        # overwrite top.protocol
        ed.top.protocol("WM_DELETE_WINDOW", self.cancelCmd)

        if font is not None:
            ed.io.text.configure(font=font)
            
        self.settext(code)
        
        
        # and set the title of this window
        ed.top.title(title)


    def pass_cb(self, event=None):
        pass

        
    def settext(self, text):
        self.clear()
        self.widget.io.text.insert("1.0", text)
        

    def gettext(self, event=None):
        return self.widget.io.text.get("1.0", 'end')


    def clear(self):
        self.widget.io.text.delete("1.0", "end")
        
 
    def cancelCmd(self, event=None):
        pass


class CodeEditorIdle_python24(CodeEditorIdle):
    """
    Idle code editor window, fitted to the needs for our various editors
    """
    def __init__(self, master=None, title='untitled',  code=None, font=None):
        from idlelib.EditorWindow import EditorWindow  

        if code is None:
            code = ""       
        
        lines = code.split('\n')
        height = len(lines) + 8
        if height > 40:
            height = 40
        
        width = max(map(len, lines))
        if width > 80:
            width = 80
        elif width < 40:
            width = 40

        if master:
            ed = self.widget = EditorWindow(root=master)
        else:
            if hasattr(self, 'editor'):
                self.editor.top.master.inversedict = {}
                self.editor.top.master.vars = {}
                self.editor.top.master.close_all_callback = self.cancelCmd
                self.editor.top.master.root = self.editor.top.master.master
                ed = self.widget = EditorWindow(root=self.editor.top.master.master,
                                                flist=self.editor.top.master)
            else:
                self.port.editor.master.inversedict = {}
                self.port.editor.master.vars = {}
                self.port.editor.master.close_all_callback = self.cancelCmd
                ed = self.widget = EditorWindow(root=self.port.editor.master.master,
                                                flist=self.port.editor.master)

        width *= int(ed.top.tk.call("font", "measure", ed.text["font"], "0")) + 2
        height *= int(ed.top.tk.call("font", "metrics", ed.text["font"], "-linespace")) 
        ed.top.geometry("%dx%d+0+0" % (width, height))
        self.top = self.widget.top
        # delete menu entry Close and Exit
        for entry in [
            'Close','Exit', 'New Window', 'Save As...', 'Save Copy As...']:

            ed.menubar.children['file'].delete(entry)
        ed.menubar.delete("Options")
        ed.menubar.delete('Run')
        
        # rebind a bunch of methods
        ed.io.text.bind("<<close-all-windows>>",self.cancelCmd)
        ed.top.bind("<<close-window>>",self.cancelCmd)
        # unbind a bunch of methods

        # FIXME: UNBIND SAVE SHORTCUTS: CTRL+SHIFT+S, ALT+SHIFT+S, F5, ALT+x
        
        ed.io.text.bind("<<open-new-window>>", self.pass_cb)

        # overwrite top.protocol
        ed.top.protocol("WM_DELETE_WINDOW", self.cancelCmd)

#        if font is not None:
#            ed.io.text.configure(font=font)
            
        self.settext(code)
        # and set the title of this window
        ed.top.title(title)

### Create CodeEditor class, depending on whether idlelib is available or not
try:
    from idlelib.EditorWindow import EditorWindow

    # it gets a bit more complicated now. Python may be shipped with idlelib
    # which is an older version and does not fullfill our needs. Need to test
    # if this is such an old version. Here, the EditorWindow constructor has
    # no keyword width and height. We use inspect...
    from inspect import getargspec
    args = getargspec(EditorWindow.__init__)[0]
    assert "width" in args, \
           "Older version of idlelib detected! Using Pmw code editor instead."
    assert "height" in args, \
           "Older version of idlelib detected! Using Pmw code editor instead."
    
    class CodeEditor(CodeEditorIdle):
        def __init__(self, master=None, title='untitled', code=None,font=None):
            CodeEditorIdle.__init__(self, master, title, code, font)

except:
    try:
        class CodeEditor(CodeEditorIdle_python24):
            def __init__(self, master=None, title='untitled', code=None,font=None):
                CodeEditorIdle_python24.__init__(self, master, title, code, font)
                
    except:       
        import traceback
        traceback.print_exc()
        class CodeEditor(CodeEditorPmw):
            def __init__(self, master=None, title='untitled', code=None,font=None):
                CodeEditorPmw.__init__(self, master, title, code)
        
        

class SourceCodeEditor(CodeEditor):
    """base class for sourc e code editor windows"""

    def __init__(self, master=None, title='untitled', node=None, editor=None):

        self.master = master
        self.node = node        # Network node
        self.editor = editor    # node editor
        
        self.top = None         # Toplevel window holding editor

        code = self.node.sourceCode[:-1]

        if node is not None:
            title = "Code editor: Node %s"%node.name

        CodeEditor.__init__(self, master, title, code,font=node.editor.font['Root'])
        
        ed = self.widget

        # add OK and APPLY Button if code if modifiable
        if node and not node.readOnly:
            b=Tkinter.Button(master=ed.status_bar,
                             text='Ok', command=self.okCmd)
            b.pack(side='left')
            b=Tkinter.Button(master=ed.status_bar,
                             text='Apply', command=self.applyCmd)
            b.pack(side='left')
        # cancel is always accesible
        b=Tkinter.Button(master=ed.status_bar,
                         text='Cancel', command=self.cancelCmd)
        b.pack(side='left')

        self.settext(code)
        ed.top.protocol("WM_DELETE_WINDOW", self.cancelCmd)


    def okCmd(self, event=None):
        self.applyCmd()
        # FIXME: save number of lines and number of chars!! Else if window is
        # resized and dismissed, size is lost
        self.cancelCmd()


    def applyCmd(self, event=None):
        code = self.gettext()
        self.node.configure(function=code)
        self.node.addSaveNodeMenuEntries()
        

    def cancelCmd(self, event=None):
        ed = self.editor
        ed.nbEditorWindows -= 1
        self.node.objEditor.manageEditorButtons()
        self.node.objEditor.editButtonVarTk.set(0)
        self.clear()
        self.settext(self.node.sourceCode)
        self.hide()
        

    def show(self, event=None):
        # reset title
        self.top.title("Code editor: Node %s"%self.node.name)
        # reset source code
        self.settext(self.node.sourceCode)
        self.top.deiconify()
 

    def hide(self, event=None):
        self.top.withdraw()

   

class CallbackEditor(CodeEditor):
    """Edit source code of port callbacks such as 'beforeConnect' or
    'afterDisconnect'."""
    
    def __init__(self, master=None, title='untitled', port=None, mode=None):

        if mode not in port.callbacks.keys():
            return
        self.master = master
        self.port = port        # node's port
        self.mode = mode        # can be 'beforeConnect', 'afterConnect', etc

        code = port.callbacks[mode][1]
        if code is None:
            code = self.getDefaultCode()
                    
        CodeEditor.__init__(self, master, title, code)

        ed = self.widget
        # add OK and APPLY Button 
        b=Tkinter.Button(master=ed.status_bar,
                             text='Ok', command=self.okCmd)
        b.pack(side='left')
        b=Tkinter.Button(master=ed.status_bar,
                         text='Apply', command=self.applyCmd)
        b.pack(side='left')
        # cancel is always accesible
        b=Tkinter.Button(master=ed.status_bar,
                         text='Cancel', command=self.cancelCmd)
        b.pack(side='left')

        ed.top.protocol(
            "WM_DELETE_WINDOW", self.cancelCmd)
        

    def getDefaultCode(self):
        mode = self.mode
        if mode in ['beforeConnect', 'afterDisconnect']:
            code = """def myFunc(self, p1, p2):
    pass
"""
        elif mode in ['afterConnect', 'beforeDisconnect']:
            code = """def myFunc(self, c):
    pass
"""
        else:
            code = ""

        return code

        
    def okCmd(self, event=None):
        self.applyCmd()
        # FIXME: save number of lines and number of chars!! Else if window is
        # resized and dismissed, size is lost
        self.cancelCmd()


    def applyCmd(self, event=None):
        code = self.gettext()
        apply(self.port.configure, (), {self.mode:code} )
        

    def cancelCmd(self, event=None):
        self.clear()
        code = self.port.callbacks[self.mode][1]
        if code is not None:
            self.settext(code)
        self.hide()
        

    def show(self, event=None):
        code = self.port.callbacks[self.mode][1]
        if code is None:
            code = self.getDefaultCode()
        self.settext(code)
        self.top.deiconify()
 

    def hide(self, event=None):
        self.top.withdraw()
