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
#########################################################################

#SUGGESTIONS
#
# - create base class for NEDIAL AND NETHUMBWHEEL
# - prefix PortWidget arguments with PW to avoid conflicts with widget args
# - might be easier if configure methods were to consume (i.e. pop) the
#   arguemnts they do handle\
#

__doc__ = """
This file defines the class PortWidget which is used to wrap GUI elements
that are exposed to the visual programming environemnt as widgets.

Widgets can be bound to ports that accept a single value (i.e. a single
parent). They are built from a description dictionary using the
port.createWidget, modified using port.configureWidget method and deleted 
using the port.deleteWidget method.

The subclasses have to implement the following methods:
    configure(rebuild=True, **kw)
    set(value, run=0)
    getDescr()
    get()
    getDataForSaving()

The method customizeWidget is called after the actual widget has been created.

Every option that can be passed to the constructor has to be listed in the
class variable dictionary configOpts. This dictionary is used to create a form
for editing the widget's configuration. The keys of this dictionary are the
keywords that can be passed to the constructor or the configue method.

The configure method has to handle all the keywords of configOpts. In adition
it has to recognize all keywords of the widget that is wrapped and configure
the widget accordingly. All other arguments have to be ignored.
Some options such as master can trigger the rebuilding of a widget.
The method returns a tuple (action, descr) where action can be an
instance of a new widget or 'rebuild' or 'resize' and descr is widget
description modified by the keywords handled by this configuration method.

The set() method is used to set the widget's value. This is the only alteration
of the widget's state which does not set the widget's modified attribute.
When this attribute is set, the widget's description will be saved into a
network file. Value CANNOT be set using configure but must be set using the
set method. The optional argument run=1/0 can be specified to force or prevent
the execution of the node.

The getDescr method has to return the complete description of the widget
as a dictionary (just like widgets are specified in node defintions). This
dictionnary can be passed directly to the widget's constructor.

Widget can appear in the node's parameter panel (master=None or 'ParamPanel')
or inside the node itself (master='node').
Widgets that appear in nodes can be either displayed or not (node.isexpanded())

Every widget is created in (self.master) along with it's label (if any). The
widget itself is created in a frame called widgetFrame created in the
constructor. This is done so that the widget and the label can be placed using
the grid geometry manager. For widgets in nodes the master is the frame
node.nodeWidgetMaster created in node.buildNodeIcon. For widgets in the
parameter panel the master is node.paramPanel.widgetFrame.
"""

import Tkinter, Pmw, warnings
import os, types, string
import warnings
import user

from UserDict import UserDict

from NetworkEditor.itemBase import NetworkItemsBase

from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.gui.BasicWidgets.Tk.Dial import Dial
from mglutil.gui.BasicWidgets.Tk.vector3DGUI import vectorGUI
from mglutil.gui.BasicWidgets.Tk.xyzGUI import xyzGUI
from mglutil.gui.BasicWidgets.Tk.multiButton import MultiCheckbuttons
from mglutil.gui.BasicWidgets.Tk.multiButton import MultiRadiobuttons
from mglutil.gui.BasicWidgets.Tk.multiButton import RegexpGUI
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import kbComboBox
from mglutil.gui.BasicWidgets.Tk.fileBrowsers import FileOpenBrowser, \
     FileSaveBrowser, DirOpenBrowser
from mglutil.util.callback import CallbackManager, CallBackFunction
from mglutil.util.relpath import abs2rel
from mglutil.events import Event

from time import time

class WidgetValueChange(Event):

    def __init__(self, network, node, port, widget, value):
        """  """
        self.timestamp = time()
        self.network = network
        self.node = node
        self.port = port
        self.widget = widget
        self.value = value


class PortWidget(NetworkItemsBase):
    """base class for network editor widgets
port:    Port instance to which the widget is bound

master:    parent widget into which the widget will be created
labelCfg:  configuration dictionary for a Tkinter.Label (use to anme the widget

## FIXME .... labelSide is now in the widgetGridCfgXXX 
labelSide: 'left', 'right', 'bottom', 'top'. Describes relative position
           of label and widget. Is used to compute row and column for gridding.
           Defaults to left.
labelGridCfg: label gridding options (other than 'row' and 'column')
widgetGridCfg: label gridding options (other than 'row' and 'column')
NEwidgetPosition: {'posx':i, 'posy':j} will be used to compute real row and col
initialValue: used to set widget in constructor
"""

    # this dict holds the list of keyword arguments that can be passed to
    # the constructor or the configure method. The defaultValues are REQUIRED
    # because they are used to create the widget's attributes

    configOpts = {
        'master': {
            'defaultValue':'ParamPanel', 'type':'string',
            'description': 'name of the Tk frame in which the widget appears',
#            'validValues': ['node', 'ParamPanel']
            },
        'NEwidgetPosition': {
            'defaultValue':{}, 'type':'dict',
            'description': "dict of type { 'posx':i, 'posy':j} use to place\
 this NEwidget (label+widget) relative to other NEwidgets (2x2 sub-grid)\
 also accepts {'row':i, 'column':j} to specify the real row and column",
            },
##         'labelSide': {
##             'defaultValue':'left', 'type':'string',
##             'validValues': ['left', 'right', 'top', 'bottom'],
##             },
        'widgetGridCfg': {
            'defaultValue': {'labelSide':'left'},
            'type':'dict',
            'description': "grid configuration dict for widgetFrame.\
(other than 'row' and 'column').",
            },
        'labelGridCfg': {
            'defaultValue': {}, 'type':'dict',
            'description': "grid configuration dict for widget label. \
(other than 'row' and 'column').",
            },
        'labelCfg': {
            'defaultValue':{'text':''}, 'type':'dict',
            'description': 'dict of Tkinter.Label options'
            },
        'labelBalloon': {
            'defaultValue':'', 'type':'string',
            'description': 'a string used as ballon for the label'
            },
        'initialValue':{
            'defaultValue':None, 'type':'None',
            },
        'lockedOnPort':{
            'defaultValue':False, 'type':'boolean',
            'description': 'when True this widget cannot be unbound'
            },
        }
    
    # dict of option specific to subclasses
    ownConfigOpts = {}


    def __init__(self, port, **kw):
        name = port.name
        NetworkItemsBase.__init__(self, name)

        self.widget = None # will hold the actual widget 
        self.objEditor = None # will point to widget editor when there is one
        self.widgetFrame = None # parent frame for widget 
            # this allows to grid widgetFrame and tklabel in self.master
            
        #self.labelSide = None # can be 'left', 'right', 'top', bottom'
        
        self.port = port
        self.lockedOnPort = False # when True widget cannot be unbound
        self.inNode = False  # True if widget appears in Node when displayed
        self._newdata = False # set to 1 by set method
                              # reset to 0 after node ran
        self.lastUsedValue = None

        self._trigger = None # function to be called when widget changes value
        self.oldmaster = None # used in rebuilt() when widget moves between panels
        self.tklabel = None  # Tkinter Label object used for widget's label
        self.labelCfg = {}   # options for the widget's label
        self.labelBalloon = None

        # create all attributs that will not be created by configure because
        # they do not appear on kw
        # NOTE: use PortWidget instead self here, else we also get all keys
        # that were added in Subclasses!
        for key in PortWidget.configOpts.keys():
            v = kw.get(key, None)
            default = self.configOpts[key]['defaultValue']
            if isinstance(default, dict):
                default = default.copy()
            setattr(self, key, default)
            #if v is None: # self.configure will not do anyting for this key
            #    setattr(self, key, self.configOpts[key]['defaultValue'])

        self.master = kw.get('master', self.master) # name of the master panel
                           # this will be the master for self.widgetFrame

        node = port.node
        master = self.master
        self.inNode = False

        if master == 'node':
            self.inNode = True
            self.masterTk = node.nodeWidgetMaster
            self._trigger = node.schedule
        elif master == 'ParamPanel':
            self.masterTk = node.paramPanel.widgetFrame
            self._trigger = node.paramPanel.run
        elif master =='macroParamPanel':
            self.masterTk = node.network.macroNode.paramPanel.widgetFrame
            self._trigger = node.schedule
        elif master in port.network.userPanels.keys():
            self.masterTk = port.network.userPanels[master].frame
            self._trigger = node.schedule
        else:
            lNetwork = port.network
            while hasattr(lNetwork, 'macroNode'):
                lNetwork = lNetwork.macroNode.network
                if master in lNetwork.userPanels.keys():
                    self.masterTk = lNetwork.userPanels[master].frame
                    self._trigger = node.schedule
                    break
            else: #we didn't break
                warnings.warn("%s is not a legal master for a widget"%master)
                return

        # create label
        self.tklabel = apply( Tkinter.Label, (self.masterTk,), self.labelCfg)
        self.tklabel.bind("<Button-3>", self.postWidgetMenu)
        self.tklabel.configure(bg='#c3d0a6')

        apply( self.configure, (False,), kw) # configure without rebuilding

        # create widget frame
        self.widgetFrame = Tkinter.Frame(self.masterTk)
        
        self.gridLabelAndWidget()

        # create menu to access port and widget editors and config panel
		# got rid of useless tearoff
        self.menu = Tkinter.Menu(port.node.getEditor(), title='Widget Menu', tearoff=False)
        self.menu.add_separator()

        if master in port.network.userPanels.keys():
            self.menu.add_command(label='Label Editor', underline=0, command=self.label_cb)

        self.menu.add_command(label='Port Editor', underline=0, 
                              command=port.edit)
        self.menu.add_command(label='Widget Editor', underline=0, 
                              command=self.edit)
        if not self.lockedOnPort:
            self.menu.add_command(label='Unbind Widget', underline=0, 
                                  command=self.port.unbindWidget)

        # we need to add an empty panel menu here, since we will delete it
        # in postWidgetMenu and rebuild it
        self.panelmenu = Tkinter.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label='Move to', menu=self.panelmenu, underline=0)

        self.vEditor = port.getEditor()

        self.labelWidgetEditor = None


    def bindToRemoteProcessNode(self):
        # save curret _trigger
        self._oldTrigger = self._trigger

        # build format string to change widget value in remote network
        port = self.port
        node = port.node
        self._cmdStr = '%s.inputPorts[%d].widget.set(' % (
            node.nameInlastSavedNetwork,port.number)
        self._trigger = self._procTrigger


    def _procTrigger(self):
        value = self.get()
        if type(value)==types.StringType:
            cmd = self._cmdStr + "'%s', run=0)"%value
        else:
            cmd = self._cmdStr + str(value) + ', run=0)'
        import os
        procid = os.getpid()
        print 'SENDING', procid, cmd
        self.port.network.remoteProcessSocket.send(cmd)


    def unbindFromRemoteProcess(self):
        self._trigger = self._oldTrigger
        #del self._cmdStr


    def moveWidgetToPanel(self, name):
        #print "moveWidgetToPanel"
        self.widgetGridCfg.pop('row', None)
        self.widgetGridCfg.pop('column', None)
        self.labelGridCfg.pop('row', None)
        self.labelGridCfg.pop('column', None)

        if name == 'Node':
            name = 'node'
        self.configure(master=name)


    def postWidgetMenu(self, event=None):
        """Display menu that allows to display configuration panel or
start port or widget editor"""
        #print "postWidgetMenu"

        self.panelmenu.delete(0, 'end')
        #self.menu.delete(self.menu.index('Move to'))
        #self.menu.add_cascade(label='Move to', menu=self.panelmenu)

        cb = CallBackFunction( self.moveWidgetToPanel, 'Node')
        self.panelmenu.add_command(label='Node', command=cb, underline=0)

        cb = CallBackFunction( self.moveWidgetToPanel, 'ParamPanel')
        self.panelmenu.add_command(label='ParamPanel', command=cb, underline=1)

        if hasattr(self.port.node.network, 'macroNode'):
            cb = CallBackFunction( self.moveWidgetToPanel, 'macroParamPanel')
            self.panelmenu.add_command(label='MacroParamPanel', command=cb, underline=2)

        for name in self.port.network.userPanels.keys():
            cb = CallBackFunction( self.moveWidgetToPanel, name)
            self.panelmenu.add_command(label=name, command=cb)

        lNetwork = self.port.network
        while hasattr(lNetwork, 'macroNode'):
            lNetwork = lNetwork.macroNode.network
            for name in lNetwork.userPanels.keys():
                cb = CallBackFunction( self.moveWidgetToPanel, name)
                self.panelmenu.add_command(label=name, command=cb)

        self.menu.post(event.x_root, event.y_root)


    def getWidgetGridCfg(self):
        """ select the right widgetGridCfg dictionary based on the panel
by default we use se;f.widgetGridCfg, but then check if there is an entry
in the node's widgetDescr that is specific for the master (i.e. 'node',
'ParamPanel' or a user panel
"""
        gridCfg = self.widgetGridCfg 
        # check for panel specific gridCfg
        descr = self.port.node.widgetDescr[self.name]
        if descr.has_key('widgetGridCfg'+self.master):
            gridCfg = descr['widgetGridCfg'+self.master]
            #print 'FFFFFFFF found panel grid', self.master, gridCfg
        return gridCfg

    
    def gridLabelAndWidget(self):
        #print "gridLabelAndWidget"

        if self.master is not None and self.master in self.port.network.userPanels.keys():
            return

        if self.widgetFrame is None:
            return

        # if row and column are specified they are in widgetGridCfg
        # self.labelGridCfg can be used to specify other gridding options such
        # as stick, etc

        port = self.port
        # default gridCfg is widgetGridCfg
        #self.widgetGridCfg

        ## WARNING self.widgetGridCfg is the default but we use a panel
        ## specific dictionary if we find one
        ## WE always find one for user panels

        # get the right widgetGridCfg dict
        gridCfg = self.getWidgetGridCfg()

        # find out how many rows and columns
        self.port.editor.master.update()
        x,y = self.masterTk.grid_size()
        
        hasrow = hascol = True
        labelSide = gridCfg.pop('labelSide', 'left')

        if not gridCfg.has_key('row'):
            # programmer has not provided a row, pack label's rowspan down if
            # labelSide is 'top'
            gridCfg['row'] = y
            if labelSide=='top':
                gridCfg['row'] += self.labelGridCfg.get('rowspan', 1)
            hasrow = False
            
        if not gridCfg.has_key('column'):
            # programmer has not provided a column, pack in column 'columspan'
            # of label if labelSide is left, else pack at column 0
            gridCfg['column'] = 0
            if labelSide=='left':
                gridCfg['column'] += self.labelGridCfg.get('columnspan', 1)
            hascol = False

        # The label will be placed using this row and column info from
        # widgetGridCfg and labelSide
        self.labelGridCfg['row'] = gridCfg['row']
        self.labelGridCfg['column'] = gridCfg['column']

        #print 'HHHHHHHHHHHHH', self.name, self.master, labelSide, hasrow, hascol, x, y, gridCfg
        if labelSide == 'left':
            # subtract columspan for widget's column
            dx = self.labelGridCfg.get('columnspan', 1)
            self.labelGridCfg['column'] -= dx
                
            # if label would be grided at a negative column index and no column
            # was specified by the programmer for the widget, we put the
            # label at 0 and the widget at the label's columnspan
            if self.labelGridCfg['column']<0:
                self.labelGridCfg['column'] = 0
                gridCfg['column'] = dx

            # grid the label
            if len(self.labelCfg['text']):
                apply( self.tklabel.grid, (), self.labelGridCfg)
                
            # grid the widget
            apply( self.widgetFrame.grid, (), gridCfg)

        elif labelSide == 'right':
            # add columspan for widget's column
            dx = self.labelGridCfg.get('columnspan', 1)
            self.labelGridCfg['column'] += dx

            # grid the label
            if len(self.labelCfg['text']):
                apply( self.tklabel.grid, (), self.labelGridCfg)

            # grid the widget
            apply( self.widgetFrame.grid, (), gridCfg)

        elif labelSide == 'top':
            # subtract rowspan for widget's row
            dx = self.labelGridCfg.get('rowspan', 1)
            self.labelGridCfg['row'] -= dx
            # if label would be grided at a negative row index and no row
            # was specified by the programmer for the widget, we put the
            # label at 0 and the widget at the label's rowspan
            if self.labelGridCfg['row']<0:
                self.labelGridCfg['row'] = 0
                gridCfg['row'] = dx

            # grid the label
            if len(self.labelCfg['text']):
                apply( self.tklabel.grid, (), self.labelGridCfg)

            # grid the widget
            apply( self.widgetFrame.grid, (), gridCfg)

        elif labelSide == 'bottom':
            # add rowspan for widget's row
            dx = self.labelGridCfg.get('rowspan', 1)
            self.labelGridCfg['row'] += dx

            # grid the label
            if len(self.labelCfg['text']):
                apply( self.tklabel.grid, (), self.labelGridCfg)
                
            # grid the widget
            apply( self.widgetFrame.grid, (), gridCfg)
        else:
            warnings.warn("%s illegal labelSide"%labelSide)
            
        gridCfg['labelSide'] = labelSide

        
    def edit(self, event=None):
        """start widget editor"""
        if self.objEditor is None:
            form = WidgetEditor(self, None)
            self.objEditor = form
            if self.port.objEditor is not None:
                self.port.objEditor.editWidgetVarTk.set(1)
            

    def label_cb(self):
        #print "label_cb"

        if self.labelWidgetEditor is None:
            self.labelWidgetEditor = LabelWidgetEditor(panel=self.master, widget=self)
        else:
            if self.labelWidgetEditor.master.winfo_ismapped() == 0:
                self.labelWidgetEditor.master.deiconify()
            self.labelWidgetEditor.master.lift()


    def destroy(self):
        # hara kiri
        #if self.inNode and self.port.node.isExpanded():
            #self.port.node.hideInNodeWidgets()

        self.tklabel.destroy()
        self.widgetFrame.destroy()

        if self.labelWidgetEditor is not None:
            self.labelWidgetEditor.master.destroy()
            self.labelWidgetEditor = None

        # kill circular references:
        self.port = None           
        self.objEditor = None
        self.widget = None
        self.master = None
        self.menu = None
        

    def configure(self, rebuild=True, **kw):
        ## handles all keywords found in self.configOpts
        ## returns action, rebuildDescr where action is either None, 'rebuild'
        ##         or 'resize'
        ##         and rebuildDescr is the decsription dict modified for
        ##         the keywords handled by this configure method

        ## for attributes that are of type dict make copies

        action = None # might become 'rebuild' or 'resize'
                              
        if self.widget is None:
            rebuildDescr = kw.copy()
        else:
            rebuildDescr = self.getDescr().copy()
            rebuildDescr.update(kw)
        gridit = False

        # handle labelGridCfg first because handling master keyword might call
        # panel.getPackingDict which needs self.labelGridCfg to be up to date
        v = kw.get('labelGridCfg', None)
        if v:
            self.labelGridCfg.update(v)
            # update rebuildDescr
            rebuildDescr['labelGridCfg'] = self.labelGridCfg
            gridit = True

        widgetPlacerCfg = kw.get('widgetPlacerCfg', None)
        if widgetPlacerCfg: # and self.widgetFrame:
            # update rebuildDescr
            rebuildDescr['widgetPlacerCfg'] = widgetPlacerCfg

        for k, v in kw.items():
            if k == 'master':
                if self.master not in self.port.network.userPanels.keys() \
                   or v != self.master:
                   # the last part (or v != self.master)
                   # has been hadded otherwise you need to say twice that you want
                   # to move the widget from the user panel to the node
                    action = 'rebuild'

                # go from string to Tk widget
                # self.master = self.port.node.findWidgetMasterTk(v)
#                if v!='node' and v!='ParamPanel':
#                    panel = self.port.editor.panelFromName(v)
#                    if panel:
#                        descr = rebuildDescr.get('widgetGridCfg'+v, None)
#                        if descr is None:
#                            # default value for labelSide is oldmaster's
#                            # labelSide. We get the widgetGridCfg of old master
#                            labelSide = self.getWidgetGridCfg()['labelSide']
#                            pd = panel.getPackingDict(self, labelSide)
#                            rebuildDescr['widgetGridCfg'+v] = pd
#                        elif not descr.has_key('row') or \
#                                 not descr.has_key('column'):
#                            labelSide = descr.pop('labelSide', 'left')
#                            pd = panel.getPackingDict(self, labelSide)
#                            rebuildDescr['widgetGridCfg'+v].update(pd)

                self.oldmaster = self.master
                self.master = v
                rebuildDescr['master'] = v

            elif k == 'initialValue':
                rebuildDescr[k] = self.initialValue = v

            elif k == 'lockedOnPort':
                rebuildDescr[k] = self.lockedOnPort = v

##             elif k=='labelSide':
##                 val = self.labelSide
##                 if action!='rebuild':
##                     if val in ['left', 'right'] and v not in ['left', 'right']:
##                         action = 'resize'
##                     if val in ['top', 'bottom'] and v not in ['top', 'bottom']:
##                         action = 'resize'

##                 rebuildDescr['labelSide'] = v #self.labelSide = v
##                 gridit = True
                
            elif k == 'widgetGridCfg':
                self.widgetGridCfg.update(v)
                rebuildDescr['widgetGridCfg'] = self.widgetGridCfg
                gridit = True

            elif k == 'labelCfg':
                if self.master not in self.port.network.userPanels.keys():
                    if len(self.labelCfg['text'])==0 and len(v['text'])>0:
                        apply( self.tklabel.grid, (), self.labelGridCfg)

                    if len(self.labelCfg['text'])>0 and len(v['text'])==0:
                        self.tklabel.grid_forget()

                self.labelCfg.update(v)
                rebuildDescr['labelCfg'] = self.labelCfg
                apply( self.tklabel.configure, (), v)

                if self.master not in self.port.network.userPanels.keys():
                    gridit = True
                    if self.inNode and action!='rebuild':
                        action = 'resize'

            elif k == 'labelBalloon':
                # add balloon string to label
                self.labelBalloon = v
                if self.labelBalloon is not None:
                    self.port.editor.balloons.bind(self.tklabel, self.labelBalloon)
                    rebuildDescr['labelBalloon'] = self.labelBalloon

            elif k == 'NEwidgetPosition':
                assert isinstance(v, dict)
                self.NEwidgetPosition.update(v)# = v.copy()
                rebuildDescr['NEwidgetPosition'] = self.NEwidgetPosition
                gridit = True

            elif k[:13]=='widgetGridCfg' and len(k)>13:
                # widget panels grid configuration dicts
                descr = self.port.node.widgetDescr[self.name]
                if descr.has_key(self.name):
                    descr[self.name].update(v)
                else:
                    self.port.node.widgetDescr[self.name][k] = v
                gridit = True
                
        labelSide = kw.get('labelSide', None)
        if labelSide:
            warnings.warn(
  "'labelSide' in widgetDescr of node %s is deprecated, put labelSide in 'widgetGridCfg'"%self.port.node.name)
            widgetGridCfg = self.getWidgetGridCfg()
            widgetGridCfg['labelSide'] = labelSide
            if action!='rebuild':
                if labelSide in ['left', 'right'] and labelSide not in [
                    'left', 'right']:
                    action = 'resize'
                if labelSide in ['top', 'bottom'] and labelSide not in [
                    'top', 'bottom']:
                    action = 'resize'
            gridit = True

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

            if gridit:
                if self.widget is not None:
                    if self.tklabel is not None:
                        self.tklabel.grid_forget()
                        self.widgetFrame.grid_forget()
                self.gridLabelAndWidget()
            gridit = False
            
        if action=='resize' and rebuild:
            if gridit:
                if self.widget is not None:
                    if self.tklabel is not None:
                        self.tklabel.grid_forget()
                        self.widgetFrame.grid_forget()
                self.gridLabelAndWidget()
            self.port.node.autoResize()
            gridit = False

        if action is None \
          and self.widget is not None \
          and kw.has_key('initialValue'):
            self.set(kw['initialValue'], 0);

        if gridit:
            self.gridLabelAndWidget()

        self._setModified(True)

        return action, rebuildDescr


    def rebuild(self, rebuildDescr):
        #print "rebuild", rebuildDescr

        # if the master has changed and the widget was ina userPanel
        # remove widget from list in userPanel
        value = self.get()
        addWidgetToPanel = False
        if self.oldmaster != rebuildDescr['master']:
##             wdescr = self.port.node.widgetDescr[self.name]
##             gcfg = wdescr.get('widgetGridCfg', None)
##             if gcfg is not None:
##                 if not gcfg.has_key('row'):
##                     rebuildDescr.pop('row', None)
##                 if not gcfg.has_key('column'):
##                     rebuildDescr.pop('column', None)
##             else:
##                 rebuildDescr.pop('row', None)
##                 rebuildDescr.pop('column', None)
                    
            if self.oldmaster in self.port.network.userPanels.keys():
                self.port.network.userPanels[self.oldmaster].deleteWidget(self)
            if rebuildDescr['master'] in self.port.network.userPanels.keys():
                addWidgetToPanel = True
        
        port = self.port
        # unbind widget (this destroys the old widget)
        port.unbindWidget()
        # delete the not needed previousWidgetDescr
        port._previousWidgetDescr = None

        # create new widget
        port.createWidget(descr=rebuildDescr) # create new widget
        port.node.autoResize()
        if port.node.inNodeWidgetsVisibleByDefault and not \
               port.node.isExpanded():
            port.node.toggleNodeExpand_cb()

        #newWidget = apply(self.__class__, (self.port,), rebuildDescr)
        #newWidget._setModified(True)
        #newWidget.port = self.port
        newWidget = port.widget
        if self.objEditor:
            self.objEditor.widget = newWidget
            newWidget.objEditor = self.objEditor

        if addWidgetToPanel:
            panel = port.editor.panelFromName(newWidget.master)
            if panel:
                if rebuildDescr.has_key('widgetPlacerCfg'):
                    widgetPlacerCfg = rebuildDescr['widgetPlacerCfg']
                else:
                    widgetPlacerCfg = None
                panel.addWidget(newWidget, widgetPlacerCfg=widgetPlacerCfg)
        newWidget.set(value,0)

        return newWidget, rebuildDescr


    def getDescr(self):
        # returns the widget's description dictionary
        # such a dictionary
        masterName = None
        if self.inNode:
            masterName = 'node'
        elif self.masterTk==self.port.node.paramPanel.widgetFrame:
            masterName = 'ParamPanel'
        else:
            node = self.port.node
            if hasattr(node.network, 'macroNode'):
                if self.masterTk==node.network.macroNode.paramPanel.widgetFrame:
                    masterName = 'macroParamPanel'
                else:
                    masterName = self.master
            else:
                if self.master in self.port.network.userPanels.keys():
                    masterName = self.master

        descr = {
            'class':self.__class__.__name__,
            # go from Tk widget to string
            #'master': self.port.node.findWidgetMasterName(self),
            'master': masterName,
            #'labelSide': self.labelSide,
            'initialValue': self.initialValue,
            }
        
        if len(self.labelGridCfg.keys()):
            descr['labelGridCfg'] = self.labelGridCfg
        if len(self.widgetGridCfg.keys()):
            descr['widgetGridCfg'] = self.widgetGridCfg
        descr['labelCfg'] = self.labelCfg
        for k,v in self.port.node.widgetDescr[self.name].items():
            if k[:13]=='widgetGridCfg' and len(k)>13:
                descr[k] = v

        widgetPlacerCfg = self.widgetFrame.place_info()
        if widgetPlacerCfg.has_key('relx') and widgetPlacerCfg.has_key('rely'):
            descr['widgetPlacerCfg'] = {'relx': widgetPlacerCfg['relx'],
                                        'rely': widgetPlacerCfg['rely'] }

        return descr

    
    def set(self, value, run=1):
        self._setModified(True)
        self._newdata = True
        if self._trigger and run and self.port.network.runOnNewData.value is True:
            self._trigger(value)


    def get(self):
        # has to be implemented by subclass
        return None


    def getDataForSaving(self):
        # this method is called when a network is saved and the widget
        # value needs to be saved
        # by default, it returns what the widget.get method returns
        # it can be subclassed by widgets in order to provide data that
        # is different from what the widget.get method returns
        return self.get()


    def scheduleNode(self):
        self._setModified(True) # setting widget is a _modified event
        if self._trigger and self.port.network.runOnNewData.value is True:
            self._trigger()


    def newValueCallback(self, event=None):
        #print "PortWidget.newValueCallback"
        ed = self.port.network.getEditor()
        value = self.get()
        ed.dispatchEvent( WidgetValueChange(self.port.network, self.port.node,
                                            self.port, self, value) )
        
        self._newdata = True
        self.scheduleNode()

        
    def compareToOrigWidgetDescr(self):
        """Compare this widget to the widgetDescr defined in a given network
node base class and return a dictionary with the differences
"""
        #print "PortWidget.compareToOrigWidgetDescr", self

        ownDescr = self.getDescr().copy()
        lConstrkw = {'masternet': self.port.network}
        lConstrkw.update(self.port.node.constrkw)
        dummy = apply(self.port.node.__class__,(),lConstrkw) # we need the base class node
        origWidgetDescr = self.__class__.configOpts.copy()
        nodeWidgetDescr = dummy.widgetDescr[self.port.name].copy()

        # create a defaults dict to compare agains for labelGridCfg
        labelGridDefaults = dict(
            rowspan=1, columnspan=1, sticky='w', padx=0, pady=0, ipadx=0,
            ipady=0)
        # update it with whatever we find in the nodeWidgetDescr
        if nodeWidgetDescr.has_key('labelGridCfg'):
            labelGridDefaults.update(nodeWidgetDescr['labelGridCfg'] )

        # create a defaults dict to compare agains for widgetGridCfg
        # FIXME: DIFFERENT ROWS AND COLUMNS FOR DIFFERENT LABELSIDE VALUES!
        widgetGridDefaults = dict(
            row=0, column=1,
            rowspan=1, columnspan=1, sticky='w', padx=0, pady=0, ipadx=0,
            ipady=0, labelSide='left', labelCfg=dict(text=''))
        # update it with whatever we find in the nodeWidgetDescr
        if nodeWidgetDescr.has_key('widgetGridCfg'):
            widgetGridDefaults.update(nodeWidgetDescr['widgetGridCfg'])

        descr = {}
        # compare to widget definitions in node
        for k,v in ownDescr.items():
            if k == 'initialValue':
                if nodeWidgetDescr.has_key('initialValue'):
                    if v == nodeWidgetDescr['initialValue']:
                        continue
                elif v == origWidgetDescr['initialValue']['defaultValue']:
                    continue
                else:
                    descr[k] = v
                continue
                
            elif k == 'labelCfg':
                if nodeWidgetDescr.has_key('labelCfg'):
                    if v['text'] == nodeWidgetDescr['labelCfg']['text']:
                        continue
                elif origWidgetDescr.has_key('labelCfg'):
                    if v['text'] == origWidgetDescr['labelCfg']['defaultValue']['text']:
                        continue

                descr[k] = v
                continue

            # labelGridCfg row and column are always automatically computed
            # by self.gridLabelAndWidget, using 'labelSide'
            elif k == 'labelGridCfg':
                tmpdict = {}
                for tk, tv in v.items():
                    if tk == 'row':
                        continue
                    elif tk == 'column':
                        continue
                    else:
                        if tv != labelGridDefaults[tk]:
                            tmpdict[tk] = tv

                if len(tmpdict.keys()):
                    descr[k] = tmpdict
                continue

            elif k == 'widgetGridCfg' or k == 'widgetGridCfg%s'%self.master:
                tmpdict = {}
                for tk, tv in v.items():
                    if tk == 'row':
                        continue
                    elif tk == 'column':
                        continue
                    else:
                        if tv != widgetGridDefaults[tk]:
                            tmpdict[tk] = tv

                if len(tmpdict.keys()):
                    descr[k] = tmpdict 
                continue
            
            if k in nodeWidgetDescr.keys():
                if v != nodeWidgetDescr[k]:
                    descr[k] = v

            
            # compare to default configuration options of widget
            elif k in origWidgetDescr.keys():
                if v != origWidgetDescr[k]['defaultValue']:
                    descr[k] = v

            # not found in either, so we have to add it
            else:
                descr[k] = v

        return descr


class LabelWidgetEditor:
    """class to manipulate the widget label in user panels
"""

    def __init__(self, panel, widget):
        #print "LabelWidgetEditor.__init__"

        self.master = Tkinter.Toplevel()
        self.master.title('Widget Label Editor')
        self.master.protocol("WM_DELETE_WINDOW", self.master.withdraw)

        self.widget = widget
        self.panel = panel

        labelNameTk = Tkinter.StringVar()
        labelNameTk.set(widget.labelCfg['text'])
        labelSideTk = Tkinter.StringVar()
        labelSideTk.set(widget.widgetGridCfg['labelSide'])

        self.labelName = Tkinter.Label(self.master, text='name:')
        self.labelName.grid(row=0, column=0, sticky='w')
        self.entryName = Tkinter.Entry(self.master, 
                                       width=10,
                                       textvariable=labelNameTk )
        self.entryName.grid(row=0, column=1, sticky='we')
        self.entryName.bind('<Return>', self.renameWidget_cb)

        self.comboSide = Pmw.ComboBox(
                           self.master,
                           label_text='side:',
                           labelpos='w',
                           entryfield_value=self.widget.widgetGridCfg['labelSide'],
                           scrolledlist_items=['left', 'right', 'top', 'bottom'],
                           selectioncommand=self.resideWidget_cb,
                           history=False
                          )
        self.comboSide.grid(row=0, column=3, sticky='we')


    def renameWidget_cb(self, event=None):
        self.widget.labelCfg['text'] = self.entryName.get()
        self.widget.tklabel['text'] = self.widget.labelCfg['text']
        self.widget.port.network.userPanels[self.panel].rePlaceWidget(self.widget)


    def resideWidget_cb(self, event=None):
        #print "resideWidget_cb"
        lComboSide = self.comboSide.get() 
        if lComboSide in ['left','right','top','bottom']:
            self.widget.widgetGridCfg['labelSide'] = self.comboSide.get()
            self.widget.port.network.userPanels[self.panel].rePlaceWidget(self.widget)
        else:
            self.comboSide.set(self.widget.widgetGridCfg['labelSide'])



class NEThumbWheel(PortWidget):
    """NetworkEditor wrapper for Thumbwheel widget.
Handles all PortWidget arguments and all Thumbwheel arguments except for value.
    Name:          default:
    callback       None
    canvasCfg      {}
    continuous     1
    height         40
    increment      0.0
    lockContinuous 0
    lockBMin       0
    lockBMax       0
    lockBIncrement 0
    lockIncrement  0
    lockMin        0
    lockMax        0
    lockOneTurn    0
    lockPrecision  0
    lockShowLabel  0
    lockType       0
    lockValue      0
    min            None
    max            None
    oneTurn        360.
    orient         'horizontal'
    precision      2
    reportDelta    0
    showLabel      1
    type           'float'
    wheelLabCfg    {}
    width          200
    wheelPad       6
"""

    # this dict holds the list of keyword arguments that can be passed to
    # the constructor or the configure method. The defaultValues are REQUIRED
    # because they are used to create the widget's attributes

    configOpts = PortWidget.configOpts.copy()
    configOpts['initialValue'] = {
        'defaultValue':0.0, 'type':'float',
        }
    ownConfigOpts = {
    'callback': {
        'defaultValue':None, 'type': 'None',
        'description':"???",
        },
    'canvasCfg':{
        'defaultValue':{}, 'type':'dict',
        'description': "???"
        },
    'continuous': {
        'defaultValue':True, 'type':'boolean',
        'description':"",
        },
    'height':{
        'defaultValue':40, 'min':5, 'max':500, 'type':'int',
        'description': "Thumbwheel's height"
        },
    'increment': {
        'defaultValue':0.0, 'type':'float',
        'description':"",
        },
    'lockContinuous': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockBMin': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockBMax': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockBIncrement': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockIncrement': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockMin': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockMax': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockOneTurn': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockPrecision': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockShowLabel': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockType': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockValue': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'min': {
        'defaultValue':None, 'type':'float',
        'description':"",
        },
    'max': {
        'defaultValue':None, 'type':'float',
        'description':"",
        },
    'oneTurn': {
        'defaultValue':360., 'type':'float',
        'description':"horizontal of vertical.",
        },
    'orient': {
        'defaultValue':'horizontal', 'type':'string',
        'description':"Can bei 'horizontal' or 'vertical' or None",
        'validValues':['horizontal', 'vertical', None],
        },
    'precision': {
        'defaultValue':2, 'type':'int',
        'validValues': [0,1,2,3,4,5,6,7,8,9], 
        'description':"",
        },
    'reportDelta': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'showLabel': {
        'defaultValue':True, 'type':'boolean',
        'description':"",
        },
    'type': {
        'defaultValue':'float', 'type':'string',
        'validValues': ['float', 'int'],
        'description':"",
        },
    'wheelLabCfg':{
        'defaultValue':{}, 'type':'dict',
        'description': "???"
        },
    'width':{
        'defaultValue':200, 'min':10, 'max':500, 'type':'int',
        'description': "Thumbwheel's width"
        },
    'wheelPad':{
        'defaultValue':6, 'min':1, 'max':500, 'type':'int',
        'description': "width of border around thumbwheel in pixels"
        },
    }
    configOpts.update( ownConfigOpts )


    def __init__(self, port, **kw):
        
##          # create all attributes that will not be created by configure because
##          # they do not appear on kw
##          for key in self.ownConfigOpts.keys():
##              v = kw.get(key, None)
##              if v is None: # self.configure will not do anyting for this key
##                  setattr(self, key, self.ownConfigOpts[key]['defaultValue'])

        # get all arguments handled by NEThumbweel and not by PortWidget
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        # call base class constructor
        apply( PortWidget.__init__, ( self, port), kw)

        # create the Thumbwheel widget
        self.widget = apply( ThumbWheel, (self.widgetFrame,), widgetcfg)
        self.widget.callbacks.AddCallback(self.newValueCallback)
        # rename Options Panel to port name
        self.widget.opPanel.setTitle("%s : %s"%(port.node.name, port.name) )
        # overwrite right mouse button click
        self.widget.canvas.bind("<Button-3>", self.postWidgetMenu)
        self.widget.valueLabel.bind("<Button-3>", self.postWidgetMenu)
        
        # add menu entry to open configuration panel
        self.menu.insert_command(0, label='Option Panel', underline=0, 
                                 command=self.toggleOptionsPanel)

        # register new callback for widget's optionsPanel Apply button
        # NOTE: idf.entryByName is at this time not built
        for k in self.widget.opPanel.idf:
            name = k.get('name', None)
            if name and name == 'ApplyButton':
                k['command'] = self.optionsPanelApply_cb
            elif name and name == 'OKButton':
                k['command'] = self.optionsPanelOK_cb

        # first, set initial value, else, if we have a min or max, the node
        # could run, because such keywords can affect the value
        if self.initialValue is not None:
            self.set(self.widget.type(self.initialValue), run=0)
            
        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)


    def configure(self, rebuild=True, **kw):
        # call base class configure with rebuild=Flase. If rebuilt is needed
        # rebuildDescr will contain w=='rebuild' and rebuildDescr contains
        # modified descr
        action, rebuildDescr = apply( PortWidget.configure, (self, False), kw)

        
        # handle ownConfigOpts entries
        if self.widget is not None:
            widgetOpts = {}
            for k, v in kw.items():
                if k in self.ownConfigOpts.keys():
                    if k in ['width', 'height', 'wheelPad', 'orient']:
                        action = 'rebuild'
                        rebuildDescr[k] = v
                    else:
                        widgetOpts[k] = v

            if len(widgetOpts):
                apply( self.widget.configure, (), widgetOpts)

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

        elif action=='resize' and rebuild:
            if self.widget and rebuild: # if widget exists
                action = None
            
        return action, rebuildDescr

        
    def set(self, value, run=1):
        self._setModified(True)
        self.widget.setValue(value)
        self._newdata = True
        if run:
            self.scheduleNode()


    def get(self):
        return self.widget.get()


    def optionsPanelOK_cb(self, event=None):
        # register this widget to be modified when opPanel is used
        self.widget.opPanel.OK_cb()
        self._setModified(True)


    def optionsPanelApply_cb(self, event=None):
        # register this widget to be modified when opPanel is used
        self.widget.opPanel.Apply_cb()
        self._setModified(True)

        
    def toggleOptionsPanel(self, event=None):
        # rename the options panel title if the node name or port name has
        # changed.
        self.widget.opPanel.setTitle(
            "%s : %s"%(self.port.node.name, self.port.name) )
        self.widget.toggleOptPanel()


    def getDescr(self):
        cfg = PortWidget.getDescr(self)
        for k in self.ownConfigOpts.keys():
            if k == 'type': # type has to be handled separately
                _type = self.widget.type
                if _type == int:
                    _type = 'int'
                else:
                    _type = 'float'
                if _type != self.ownConfigOpts[k]['defaultValue']:
                    cfg[k] = _type
                continue
            val = getattr(self.widget, k)

            if val != self.ownConfigOpts[k]['defaultValue']:
                cfg[k] = val
       
        return cfg


class NEDial(PortWidget):
    """NetworkEditor wrapper for Dial widget.
Handles all PortWidget arguments and all Dial arguments except for value.
    Name:          default:
    callback       None
    continuous     1
    increment      0.0
    lockContinuous 0
    lockBMin       0
    lockBMax       0
    lockBIncrement 0
    lockIncrement  0
    lockMin        0
    lockMax        0
    lockOneTurn    0
    lockPrecision  0
    lockShowLabel  0
    lockType       0
    lockValue      0
    min            None
    max            None
    oneTurn        360.
    precision      2
    showLabel      1
    size           50
    type           'float'
"""

    configOpts = PortWidget.configOpts.copy()
    configOpts['initialValue'] = {
        'defaultValue':0.0, 'type':'float',
        }

    ownConfigOpts = {
    'callback': {
        'defaultValue':None, 'type': 'None',
        'description':"???",
        },
    'continuous': {
        'defaultValue':True, 'type':'boolean',
        'description':"",
        },
    'increment': {
        'defaultValue':0.0, 'type':'float',
        'description':"",
        },
    'lockContinuous': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockBMin': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockBMax': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockBIncrement': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockIncrement': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockMin': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockMax': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockOneTurn': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockPrecision': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockShowLabel': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockType': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'lockValue': {
        'defaultValue':False, 'type':'boolean',
        'description':"",
        },
    'min': {
        'defaultValue':None, 'type':'float',
        'description':"",
        },
    'max': {
        'defaultValue':None, 'type':'float',
        'description':"",
        },
    'oneTurn': {
        'defaultValue':360., 'type':'float',
        'description':"",
        },
    'precision': {
        'defaultValue':2, 'type':'int',
        'description':"number of decimals used in label",
        },
    'showLabel': {
        'defaultValue':True, 'type':'boolean',
        'description':"",
        },
    'size':{
        'defaultValue': 50, 'min':20, 'max':500, 'type':'int'
        },
    'type': {
        'defaultValue':'float', 'type':'string',
        'validValues': ['float', 'int'],
        'description':"",
        },
        }
    configOpts.update( ownConfigOpts )


    def __init__(self, port, **kw):
        
##          # create all attributes that will not be created by configure because
##          # they do not appear on kw
##          for key in self.ownConfigOpts.keys():
##              v = kw.get(key, None)
##              if v is None: # self.configure will not do anyting for this key
##                  setattr(self, key, self.ownConfigOpts[key]['defaultValue'])

        # get all arguments handled by NEThumbweel and not by PortWidget
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        # call base class constructor
        apply( PortWidget.__init__, ( self, port), kw)

        # create the Dial widget
        self.widget = apply( Dial, (self.widgetFrame,), widgetcfg)
        self.widget.callbacks.AddCallback(self.newValueCallback)
        # rename Options Panel to port name
        self.widget.opPanel.setTitle("%s : %s"%(port.node.name, port.name) )

        # overwrite right mouse button click
        self.widget.canvas.bind("<Button-3>", self.postWidgetMenu)

        # add menu entry to open configuration panel
        self.menu.insert_command(0, label='Option Panel', underline=0, 
                                 command=self.toggleOptionsPanel)

        # register new callback for widget's optionsPanel Apply button
        # NOTE: idf.entryByName is at this time not built
        for k in self.widget.opPanel.idf:
            name = k.get('name', None)
            if name and name == 'ApplyButton':
                k['command'] = self.optionsPanelApply_cb
            elif name and name == 'OKButton':
                k['command'] = self.optionsPanelOK_cb

        # first set default value, in case we have a min or max, else the
        # node would run
        if self.initialValue is not None:
            self.set(self.widget.type(self.initialValue), run=0)
            
        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)

        self._setModified(False) # will be set to True by configure method


    def configure(self, rebuild=True, **kw):
        # call base class configure with rebuild=Flase. If rebuilt is needed
        # rebuildDescr will contain w=='rebuild' and rebuildDescr contains
        # modified descr
        action, rebuildDescr = apply( PortWidget.configure, (self, False), kw)
            
        # handle ownConfigOpts entries
        if self.widget is not None:
            widgetOpts = {}
            for k, v in kw.items():
                if k in self.ownConfigOpts:
                    if k =='size':
                        action = 'rebuild'
                        rebuildDescr[k] = v
                    else:
                        widgetOpts[k] = v

            if len(widgetOpts):
                apply( self.widget.configure, (), widgetOpts)

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

        elif action=='resize' and rebuild:
            if self.widget and rebuild: # if widget exists
                action = None

        return action, rebuildDescr


    def set(self, value, run=1):
        self._setModified(True)
        self.widget.setValue(value)
        self._newdata = True
        if run:
            self.scheduleNode()

        
    def get(self):
        return self.widget.get()

        
    def optionsPanelOK_cb(self, event=None):
        # register this widget to be modified when opPanel is used
        self.widget.opPanel.OK_cb()
        self._setModified(True)

    def optionsPanelApply_cb(self, event=None):
        # register this widget to be modified when opPanel is used
        self.widget.opPanel.Apply_cb()
        self._setModified(True)


    def toggleOptionsPanel(self, event=None):
        # rename the options panel title if the node name or port name has
        # changed.
        self.widget.opPanel.setTitle(
            "%s : %s"%(self.port.node.name, self.port.name) )
        self.widget.toggleOptPanel()
        

    def getDescr(self):
        cfg = PortWidget.getDescr(self)
        for k in self.ownConfigOpts.keys():
            if k == 'type': # type has to be handled separately
                _type = self.widget.type
                if _type == int:
                    _type = 'int'
                else:
                    _type = 'float'
                if _type != self.ownConfigOpts[k]['defaultValue']:
                    cfg[k] = _type
                continue
            val = getattr(self.widget, k)
            if val != self.ownConfigOpts[k]['defaultValue']:
                cfg[k] = val
        return cfg


class TkPortWidget(PortWidget):
    """base class for basic Tkinter widgets such as Entry or Button
    these widget all have an attribute tkwidget which is the actual Tkinter
    widget they wrap."""

    configOpts = PortWidget.configOpts.copy()
        
    def __init__(self, port, **kw):
        # this dict is used to save tk options applied to the widget
        # such as width, height, bg, etc....
        self.widgetDescr = {}

        apply( PortWidget.__init__, (self, port), kw)

        # create a Tkvariable to store thwidget's state
        self.var = None


    def configure(self, rebuild=True, **kw):
        # handle all Tkinter keywords for self.widget
        action, rebuildDescr = apply( PortWidget.configure, (self, 0), kw)

        # handle ownConfigOpts entries
        if self.widget is not None:
            widgetOpts = {}
            tkOptions = self.widget.configure()
            for k, v in kw.items():

                # skip base class keywords
                if k in PortWidget.configOpts:
                    continue
                # check if it is a Tk option for this Tk widget
                if tkOptions is not None and k in tkOptions:
                    widgetOpts[k] = v
                
            if len(widgetOpts):
                self.widgetDescr.update(widgetOpts)
                apply( self.widget.configure, (), widgetOpts)

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

        elif action=='resize' and rebuild:
            if self.widget and rebuild:
                action = None
            
        return action, rebuildDescr

 
    def set(self, value, run=1):
        self._setModified(True)
        self.var.set(value)
        self._newdata = True
        if run:
            self.scheduleNode()


    def get(self):
        return self.var.get()


    def getDescr(self):
        cfg = PortWidget.getDescr(self)
        self.widgetDescr.pop('master', None)
        cfg.update(self.widgetDescr)
        return cfg


    
           
class NEEntry(TkPortWidget):
    """widget wrapping a Tkinter Entry widget.
Additional constructor arguments are any Tkinter.Entry arguments.
"""

    configOpts = TkPortWidget.configOpts.copy()

    ownConfigOpts = {}
    ownConfigOpts['initialValue'] = {
        'defaultValue':'', 'type':'string',
        }

    configOpts.update(ownConfigOpts)

    def __init__(self, port, **kw):
        
        # call base class constructor
        apply( TkPortWidget.__init__, (self, port), kw)

        self.var = Tkinter.StringVar()
        widgetcfg = {'textvariable':self.var}

        # create the Entry widget
        self.widget = apply( Tkinter.Entry, (self.widgetFrame,), widgetcfg )
        self.widget.bind('<Return>', self.newValueCallback)
        #self.widget.bind('<FocusOut>', self.newValueCallback)
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
        
        self.widget.pack(side='left')

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), kw)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)

        self._setModified(False) # will be set to True by configure method


    def configure(self, rebuild=True, **kw):
        action, rebuildDescr = apply( TkPortWidget.configure, (self, 0), kw)
            
        #  this methods just creates a resize action if width changes
        if self.widget is not None:
            
            if 'width' in kw:
                action = 'resize'

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)


        if action=='resize' and rebuild:
            self.port.node.autoResize()

        return action, rebuildDescr


    def get(self):
        val = self.var.get()
        if val:
            self._setModified(True)
        # replace " by ' because we wil use " for setting the widget value
        val = val.replace('"', "'")
        return val



class NEEntryNotScheduling(NEEntry):
    def newValueCallback(self, event=None):
        #print "NEEntryNotScheduling.newValueCallback"
        self._newdata = True


class NEEntryWithDirectoryBrowser(NEEntry):
    """widget wrapping a Tkinter Entry widget used to specify a file name.
double clicking on the entry opens a directory browser.
Additional constructor arguments are title, initialDir and any
Tkinter.Entry argument.
"""
    configOpts = NEEntry.configOpts.copy()
    ownConfigOpts = {
        'title':{
            'defaultValue':'Choose Directory:', 'type':'string'
            },
        }
    try:
        from Vision import networkDefaultDirectory
        ownConfigOpts.update({
            'initialDir':{
                'defaultValue':networkDefaultDirectory, 'type':'string'
                },
            })
    except ImportError:
        pass


    configOpts.update( ownConfigOpts )

    
    def __init__(self, port, **kw):
        
        # create all self.title filetypes and initialDir with default values
        # if they are not specified in kw
        for key in self.ownConfigOpts.keys():
            v = kw.get(key, None)
            if v is None: # self.configure will not do anyting for this key
                setattr(self, key, self.ownConfigOpts[key]['defaultValue'])
        
        # get all arguments handled only by this widget and not by base class
        # remove them from kw
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        self.initialDir = None
        
        # call base class constructor
        apply( NEEntry.__init__, (self, port), kw)
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)

        # create the FleBrowser button
        self.FBbutton = Tkinter.Button(self.widgetFrame, text='...',
                                       relief='raised',
                                       command=self.getDirFromBrowser )
        #self.FBbutton.grid(row=0, column=2)
        self.FBbutton.pack(side='right')
        
        # bind right mouse button click
        #self.widget.bind("<Button-3>", self.postWidgetMenu)

        self.widget.pack()

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg) 

        # bind function to display file browser
        # THIS DOES NOT WORK ON LINUX MACHINES
        self.widget.bind('<Double-Button-1>', self.getDirFromBrowser)

        # create the file browser object (this does not display anything)
        self.getDirObj = DirOpenBrowser( parent=self.masterTk,
                                         title=self.title)
        
        self._setModified(False) # will be set to True by configure method


    def configure(self, rebuild=True, **kw):
        action, rebuildDescr = apply( NEEntry.configure, (self, False), kw)
            
        # handle ownConfigOpts entries
        if self.widget is not None:
            
            widgetOpts = {}
            for k, v in kw.items():
                if k=='title':
                    self.title = v
                elif k=='initialDir':
                    self.initialDir = v

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

        elif action=='resize' and rebuild:
            if self.widget and rebuild:
                action = None
            
        return action, rebuildDescr

                
    def getDirFromBrowser(self, event=None):
        # display the directory from the browser
        # print "getDirFromBrowser"

        if self.port.network.filename is not None:
            lNetworkDir = os.path.dirname(self.port.network.filename)
        elif hasattr(self.port.network, 'macroNode') \
          and self.port.network.macroNode.network.filename is not None:
            lNetworkDir = os.path.dirname(self.port.network.macroNode.network.filename)
        else:
            import Vision
            if hasattr(Vision, 'networkDefaultDirectory'):
                lNetworkDir = Vision.networkDefaultDirectory
            else:
                lNetworkDir = '.'

        self.getDirObj.lastDir = lNetworkDir

        folder = self.getDirObj.get()
        if folder:
            folder = os.path.abspath(folder)
            folder = abs2rel(folder, base=lNetworkDir)
            self.set(value=folder, run=0)
            self.scheduleNode()


class NEEntryWithFileBrowser(NEEntry):
    """widget wrapping a Tkinter Entry widget used to specify a file name.
double clicking on the entry opens a file browser.
Additional constructor arguments are filetypes, title, initialDir and any
Tkinter.Entry argument.
"""
    configOpts = NEEntry.configOpts.copy()
    ownConfigOpts = {
        'filetypes':{
            'defaultValue':[('all','*')], 'type':'string',
            'description':"list of tuples defining files types"
            },
        'title':{
            'defaultValue':'Choose File:', 'type':'string'
            },
        }
    try:
        from Vision import networkDefaultDirectory
        ownConfigOpts.update({
            'initialDir':{
                'defaultValue':networkDefaultDirectory, 'type':'string'
                },
            })
    except ImportError:
        pass


    configOpts.update( ownConfigOpts )
   
    
    def __init__(self, port, **kw):
        
        # create all self.title filetypes and initialDir with default values
        # if they are not specified in kw
        for key in self.ownConfigOpts.keys():
            v = kw.get(key, None)
            if v is None: # self.configure will not do anyting for this key
                setattr(self, key, self.ownConfigOpts[key]['defaultValue'])
        
        # get all arguments handled only by this widget and not by base class
        # remove them from kw
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        # call base class constructor
        apply( NEEntry.__init__, (self, port), kw)
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)

        # create the FleBrowser button
        self.FBbutton = Tkinter.Button(self.widgetFrame, text='...',
                                       relief='raised',
                                       command=self.getFileFromBrowser )
        #self.FBbutton.grid(row=0, column=2)
        self.FBbutton.pack(side='right')
        
        # bind right mouse button click
        #self.widget.bind("<Button-3>", self.postWidgetMenu)

        self.widget.pack()

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg) 

        # bind function to display file browser
        # THIS DOES NOT WORK ON LINUX MACHINES
        self.widget.bind('<Double-Button-1>', self.getFileFromBrowser)

        # create the file browser object (this does not display anything)
        self.getFileObj = FileOpenBrowser(parent = self.masterTk,
            #lastDir=self.initialDir,
            title=self.title,
            filetypes=self.filetypes)
        
        self._setModified(False) # will be set to True by configure method


    def configure(self, rebuild=True, **kw):
        action, rebuildDescr = apply( NEEntry.configure, (self, False), kw)
            
        # handle ownConfigOpts entries
        if self.widget is not None:
            
            widgetOpts = {}
            for k, v in kw.items():
                if k=='filetypes':
                    self.filetypes = v
                elif k=='title':
                    self.title = v
                elif k=='initialDir':
                    self.initialDir = v

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

        elif action=='resize' and rebuild:
            if self.widget and rebuild:
                action = None
            
        return action, rebuildDescr

                
    def getFileFromBrowser(self, event=None):
        # display the file browser
        #print "getFileFromBrowser"

        if self.port.network.filename is not None:
            lNetworkDir = os.path.dirname(self.port.network.filename)
        elif hasattr(self.port.network, 'macroNode') \
          and self.port.network.macroNode.network.filename is not None:
            lNetworkDir = os.path.dirname(self.port.network.macroNode.network.filename)
        else:
            import Vision
            if hasattr(Vision, 'networkDefaultDirectory'):
                lNetworkDir = Vision.networkDefaultDirectory
            else:
                lNetworkDir = '.'

        self.getFileObj.lastDir = lNetworkDir

        file = self.getFileObj.get()
        if file:
            file= os.path.abspath(file)
            file = abs2rel(file, base=lNetworkDir)
            self.set(value=file, run=0)
            self.scheduleNode()



class NEEntryWithFileSaver(NEEntryWithFileBrowser):
    """widget wrapping a Tkinter Entry widget used to specify a file name.
double clicking on the entry opens a SAVE file browser.
Additional constructor arguments are filetypes, title, initialDir and any
Tkinter.Entry argument.
"""

    def __init__(self, port, **kw):

        apply( NEEntryWithFileBrowser.__init__, (self, port), kw)
        
        self.getFileObj = FileSaveBrowser(
            #lastDir=self.initialDir,
            title=self.title,
            filetypes=self.filetypes)
        


class NECheckButton(TkPortWidget):
    """widget wrapping a Tkinter Entry widget.
Additional constructor arguments are any Tkinter.Checkbutton arguments.
"""

    configOpts = TkPortWidget.configOpts.copy()

    ownConfigOpts = {
        'initialValue':{
            'defaultValue':0, 'type':'int',
            'validValues': [0,1]},
        }
    configOpts.update( ownConfigOpts )


    def __init__(self, port, **kw):

        # call base class constructor
        apply( TkPortWidget.__init__, (self, port), kw)

        self.var = Tkinter.IntVar()
        widgetcfg = {'variable':self.var, 'command':self.newValueCallback }
        
        # configure without rebuilding to avoid enless loop
        #apply( self.configure, (False,), widgetcfg)

        # create the Checkbutton widget
        self.widget = apply( Tkinter.Checkbutton, (self.widgetFrame,),
                             widgetcfg )
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
        self.widget.pack()

        # configure without rebuilding to avoid enless loop
        #guillaume: this call make the test hang (test_vizlib and test_flextreelib)
        #apply( self.configure, (False,), kw)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)

        self._setModified(False) # will be set to True by configure method


    def set(self, value, run=1):
        self._setModified(True)
        if value:
            self.var.set(1)
        else:
            self.var.set(0)
        self._newdata = True
        if run:
            self.scheduleNode()



class NEButton(TkPortWidget):
    """widget wrapping a Tkinter Button widget.
Additional constructor arguments are any Tkinter.Button arguments.
"""

    configOpts = TkPortWidget.configOpts.copy()

    def __init__(self, port, **kw):

        # call base class constructor
        apply( TkPortWidget.__init__, (self, port), kw)

        self.var = Tkinter.IntVar()
        widgetcfg = {}
        
        cmd = kw.pop('command',None)
        if cmd is None:
            cmd = self.newValueCallback
        widgetcfg['command'] = cmd
        
        # configure without rebuilding to avoid enless loop
        #apply( self.configure, (False,), widgetcfg)

        # create the Button widget
        self.widget = apply( Tkinter.Button, (self.widgetFrame,), widgetcfg )
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
        self.widget.pack()

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), kw)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)

        self._setModified(False) # will be set to True by configure method
        

### useless, use NECheckbutton instead         
##class NERadiobutton(TkPortWidget):
##    """widget wrapping a Tkinter Radiobutton widget.
##Additional constructor arguments are any Tkinter.Radiobutton arguments.
##"""
##
##    configOpts = TkPortWidget.configOpts.copy()
##
##    def __init__(self, port, **kw):
##
##        # call base class constructor
##        apply( TkPortWidget.__init__, (self, port), kw)
##
##        self.var = Tkinter.StringVar()
##        widgetcfg ={'textvariable':self.var}
##        widgetcfg.update( {'command':self.newValueCallback } )
##        
##        # configure without rebuilding to avoid enless loop
##        #apply( self.configure, (False,), widgetcfg)
##
##        # create the Checkbutton widget
##        self.widget = apply( Tkinter.Radiobutton, (self.widgetFrame,),
##                             widgetcfg )
##        # bind right mouse button click
##        self.widget.bind("<Button-3>", self.postWidgetMenu)
##        self.widget.pack()
##
##        # configure without rebuilding to avoid enless loop
##        apply( self.configure, (False,), kw)
##
##        if self.initialValue is not None:
##            self.set(self.initialValue, run=0)
##
##        self._setModified(False) # will be set to True by configure method



class PmwPortWidget(PortWidget):
    """base class for wrapping basic PMW widgets such as ComboBox
"""

    configOpts = PortWidget.configOpts.copy()
        
    def __init__(self, port, **kw):
        # this dict is used to save Pmw widget options applied to the widget
        self.widgetDescr = {}

        apply( PortWidget.__init__, (self, port), kw)

    def configure(self, rebuild=True, **kw):
        # handle all Pmw keywords for self.widget
        action, rebuildDescr = apply( PortWidget.configure, (self, 0), kw)
        # handle ownConfigOpts that create an action
        if self.widget is not None:
            widgetOpts = {}

            for k, v in kw.items():
                # skip base class keywords
                if k in PortWidget.configOpts:
                    continue
                
                # we need to look at components widgets too
                comps = k.split('_')
                w = self.widget
                for c in comps[:-1]:
                    w = self.widget.component(c)
                
                allowedOptions = w.configure()
                # check if it is a Tk option for this Tk widget
                if comps[-1] in allowedOptions:
                    widgetOpts[k] = v

            if len(widgetOpts):
                self.widgetDescr.update(widgetOpts)
                apply( self.widget.configure, (), widgetOpts)

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)

 
        elif action=='resize' and rebuild:
            if self.widget and rebuild:
                action = None
            
        return action, rebuildDescr


    def getPmwOptions(self, widget, options):
        """returns the options that can be passed to a Pmw widget. Note:
        in the future, this method could be more clever and check what
        options are available in the Pmw widget and only allow these options
        as keys"""
        
        pmwkw = {}
        for k,v in options.items():
            if k in ['labelSide', 'widgetGridCfg', 'labelGridCfg']:
                continue
            elif k == 'widgetGridCfg%s'%widget.master:
                continue
            elif k in widget.configOpts:
                continue
            else:
                pmwkw[k] = v
        return pmwkw



class NEComboBox(PmwPortWidget):
    """widget wrapping a Pmw ComboBox widget.
Additional constructor arguments are choices, fixed, any Pmw.ComboBox
arguments.
"""
    configOpts = PmwPortWidget.configOpts.copy()
    ownConfigOpts = {
        'choices':{
            'defaultValue':[], 'type':'list',
            'description':"list of values to choose from in dropdown",
            },
        'fixedChoices':{
            'defaultValue':0, 'type':'boolean',
            'description':"when 1 only entries in list can be chosen",
            },
        'autoList':{
            'defaultValue':False, 'type':'boolean',
            'description':"""when True the list of choices is generated
when the node runs, and therefore there is no need to save the entire list.
Only the the current value will be saved.""",
            },
        }
    configOpts.update( ownConfigOpts )
    

    def __init__(self, port, **kw):
        # get all arguments handled only by this widget and not by base class
        # remove them from kw
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        combokw = { 'dropdown' : kw.pop('dropdown', True) }

        # call base class constructor
        apply( PmwPortWidget.__init__, (self, port), kw)
        for key in self.configOpts.keys():
            v = kw.get(key, None)
            if v is None: # self.configure will not do anyting for this key
                setattr(self, key, self.configOpts[key]['defaultValue'])

        
        # get all combobox arguments
        # replace the selection command
        cmd = kw.pop('selectioncommand', None)
        if cmd:
            self.selectionCommand = cmd
        else:
            self.selectionCommand = None

        combokw['selectioncommand'] = self.set
        d = self.getPmwOptions(self, kw)
        combokw.update(d)

        # prevent Pmw from creating a label
        combokw['labelpos'] = None
        # now, create widget
        if combokw['dropdown'] is True:
            self.widget = apply( kbComboBox, (self.widgetFrame,), combokw)
        else:
            self.widget = apply( Pmw.ComboBox, (self.widgetFrame,), combokw)

        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
        self.widget.pack(side='left', anchor='n',
                         fill='x')#, expand=1, padx=8, pady=8)

        # configure without rebuilding to avoid enless loop
        # now remove selectioncommand and labelspos, they are not part of Pmw
        del combokw['selectioncommand']
        del combokw['labelpos']
        del combokw['dropdown']
        widgetcfg.update(combokw)
        apply( self.configure, (False,), widgetcfg)
        
        if self.initialValue is not None:
            self.set(self.initialValue, run=0)

        self._setModified(False) # will be set to True by configure method


    def configure(self, rebuild=True, **kw):
        #print "NEComboBox.configure", kw
        # handle all Tkinter keywords for self.widget
        action, rebuildDescr = apply( PmwPortWidget.configure, (self, 0), kw)
            
        # handle ownConfigOpts that create an action
        if self.widget is not None:
            PmwOptions = self.widget.configure()
            for k, v in kw.items():
                # check if it is a Tk option for this Tk widget
                if k in ['entryfield_entry_width', 'entry_width']:
                    action = 'resize'
                elif k == 'choices':
                    self.setlist(v)
                elif k == 'fixedChoices':
                    self.fixedChoices = v
                elif k == 'autoList':
                    self.autoList = v

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)
        elif action=='resize' and rebuild:
            if self.widget and rebuild:
                action = None
            self.port.node.autoResize()
                
        return action, rebuildDescr


    def set(self, value, run=1):
        self._setModified(True)
        if value is None:
            return

        if value is '' and run:
            self.scheduleNode()
            return

        # once we get here Pmw has already added entry to list if it was
        # not there
        if self.fixedChoices:
            allValues = self.choices
        else:
            allValues = self.widget.get(0, 'end')
            self.choices = allValues
        newval = False

        if value in allValues:
            self.widget.selectitem(value)
            newval = True
            self._newdata = True
        else:
            self.widget.setentry(value)
            if (len(allValues) > 0) and (value != ''):
                warnings.warn("attribute %s not in the list of choices"%value)
            #self.widget.setentry('')    # clear entry 
            #self.setlist(self.choices)  # remove from list

        if newval and run:
            if callable(self.selectionCommand):
                self.selectionCommand(value)
            self.scheduleNode()
            

    def setlist(self, choices):
        self.widget.component('scrolledlist').setlist(choices)
        self.choices = choices[:]
        self._setModified(True)


    def getlist(self):
        return self.choices[:]
        
        
    def get(self):
        return self.widget.get()


    def getDescr(self):
        cfg = PmwPortWidget.getDescr(self)
        cfg['fixedChoices'] = self.fixedChoices
        cfg['autoList'] = self.autoList
        if self.autoList is False:
            cfg['choices'] = self.choices
#        else:
#            cfg['choices'] = [self.widget.get()]
            
        cfg.update(self.widgetDescr)
        return cfg



class NEVectorGUI(PortWidget):
    """NetworkEditor wrapper for vector3DGUI widget/
Handles all PortWidget arguments and all vector3DGUI arguments except for
vector.
    Name:            default:
    name             vector
    size             200
    continuous       1
    mode             XY
    precision        5
    lockContinuous   0
    lockPrecision    0
    lockMode         0
    callback         None
"""

    # description of parameters that can only be used with the widget's
    # constructor
    configOpts = PortWidget.configOpts.copy()

    configOpts['initialValue'] = {
        'defaultValue':[1.,0,0], 'type':'list',
        }

    ownConfigOpts = {
    'name':{
        'defaultValue':'vector', 'type':'string',
        'description':'title of widget',
        },
    'size':{
        'defaultValue':200, 'min':100, 'max':500, 'type':'int',
        'description': "GUI size"},
    'continuous': {
        'defaultValue':1, 'type':'boolean',
        'description':"",
        },
    'mode': {
        'defaultValue':'XY', 'type':'string',
        'validValues':['XY', 'X', 'Y', 'Z'],
        'description':"any of XY, X, Y, Z",
        },
    'precision': {
        'defaultValue':5, 'type':'int',
        'min':1, 'max':10,
        'description':'this is used only for display purpose.'
        },
    'lockContinuous': {
        'defaultValue':0, 'type':'boolean',
        'description':"",
        },
    'lockPrecision': {
        'defaultValue':0, 'type':'boolean',
        'description':"",
        },
    'lockMode': {
        'defaultValue':0, 'type':'boolean',
        'description':"",
        },
    'callback': {
        'defaultValue':None, 'type': 'None',
        'description':"???",
        },
    }
    configOpts.update( ownConfigOpts )


    def __init__(self, port, **kw):

        # create all attributes that will not be created by configure because
        # they do not appear on kw
        for key in self.ownConfigOpts.keys():
            v = kw.get(key, None)
            if v is None: # self.configure will not do anyting for this key
                setattr(self, key, self.ownConfigOpts[key]['defaultValue'])

        # get all arguments handled by NEThumbweel and not by PortWidget
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        # call base class constructor
        apply( PortWidget.__init__, ( self, port), kw)

        # create the vectorGUI widget
        self.widget = apply( vectorGUI, (self.widgetFrame,), widgetcfg)
        self.widget.callbacks.AddCallback(self.newValueCallback)
        # bind right mouse button click
        self.widget.canvas.bind("<Button-3>", self.postWidgetMenu)

        # register new callback for widget's optionsPanel Dismiss button
        # NOTE: idf.entryByName is at this time not built
        for k in self.widget.opPanel.idf:
            name = k.get('name', None)
            if name and name == 'DismissButton':
                k['command'] = self.optionsPanelDismiss_cb
                break
            
        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)
            
        self._setModified(False) # will be set to True by configure method

        
    def get(self):
        return self.widget.vector


    def set(self, vector, run=1):
        self._setModified(True)
        self.widget.setVector(vector)
        self._newdata = True
        if run:
            self.scheduleNode()


    def optionsPanelDismiss_cb(self, event=None):
        # register this widget to be modified when opPanel is used
        self.widget.opPanel.Dismiss_cb()
        self._setModified(True)


    def configure(self, rebuild=True, **kw):
        # call base class configure with rebuild=Flase. If rebuilt is needed
        # rebuildDescr will contain w=='rebuild' and rebuildDescr contains
        # modified descr
        action, rebuildDescr = apply( PortWidget.configure, (self, False), kw)
            
        # handle ownConfigOpts entries
        if self.widget is not None:

            widgetOpts = {}
            for k, v in kw.items():
                if k in self.ownConfigOpts.keys():
                    if k in ['size']:
                        action = 'rebuild'
                        rebuildDescr[k] = v
                    else:
                        widgetOpts[k] = v

            if len(widgetOpts):
                apply( self.widget.configure, (), widgetOpts)

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)
        elif action=='resize' and rebuild:
            if self.widget and rebuild: # if widget exists
                action = None
            
        return action, rebuildDescr


    def getDescr(self):
        cfg = PortWidget.getDescr(self)
        for k in self.ownConfigOpts.keys():
            val = getattr(self.widget, k)
            if val != self.ownConfigOpts[k]['defaultValue']:
                cfg[k] = val
        return cfg


class NEMultiCheckButtons(PortWidget):
    """This class builds multi-checkbutton panel. Checkbuttons are packed in
    a grid, the name of the button is used as label. valueList is used to add
    the checkbuttons: data is stored in tuples. First entry is a string of
    the button name. Optional second entry is a dictionary with Tkinter
    checkbutton options. Optional third entry is a dictionary with grid
    options.
    Name:               default:
    valueList           []
    callback            None
    sfcfg               {}
    immediate           1
"""
    # description of parameters that can only be used with the widget's
    # constructor
    configOpts = PortWidget.configOpts.copy()
    ownConfigOpts = {
    'callback': {
        'defaultValue':None, 'type': 'None',
        'description':"???",
        },
    'valueList': {
        'defaultValue':[], 'type': 'list',
        'description':"every list entry corresponds to a checkbutton",
        },
    'sfcfg': {
        'defaultValue':{}, 'type': 'dict',
        'description':"scrolled frame Tkinter configuration dict",
        },
    'immediate': {
        'defaultValue':1, 'type': 'boolean',
        'description':"if set to 0, checking a button does not call the \
callback",
        },
    }
    configOpts.update( ownConfigOpts )

    
    def __init__(self, port, **kw):


        # create all attributes that will not be created by configure because
        # they do not appear on kw
        for key in self.ownConfigOpts.keys():
            v = kw.get(key, None)
            if v is None: # self.configure will not do anyting for this key
                setattr(self, key, self.ownConfigOpts[key]['defaultValue'])

        # get all arguments handled by NEThumbweel and not by PortWidget
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)


        # call base class constructor
        apply( PortWidget.__init__, (self, port), kw)
        
        # create the MultiCheckbutton widget
        self.widget = apply( MultiCheckbuttons, (self.widgetFrame,),widgetcfg )
        self.widget.callback = self.newValueCallback
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
       
        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)

        self._setModified(False) # will be set to True by configure method
        self.reGUI = None # the little gui for regular expression syntax
        self.addMyMenu() # this adds a new menu entry to the param.panel menu

        
    def set(self, data, run=0):
        if data is not None:
            self._setModified(True)
            for name in data:
                self.widget.buttonDict[name]['button'].var.set(1)
                self._newdata = True

        if run:
            self.port.node.paramPanel.forceRun()


    def get(self, event=None):
        return self.widget.get()
    

    def getDataForSaving(self, event=None):
        result = []
        onButtons = self.widget.get(mode='Vision')
        for name,value in onButtons:
            if value == 1:
                result.append(name)
        return result
    


    def configure(self, rebuild=True, **kw):
        # call base class configure with rebuild=Flase. If rebuilt is needed
        # rebuildDescr will contain w=='rebuild' and rebuildDescr contains
        # modified descr
        action, rebuildDescr = apply( PortWidget.configure, (self, False), kw)
            
        # handle ownConfigOpts entries
        if self.widget is not None:

            widgetOpts = {}
            for k, v in kw.items():
                if k in self.ownConfigOpts.keys():
                    if k == 'checkbuttonNames':
                        self.widget.rebuild(v)
                    else:
                        widgetOpts[k] = v

            if len(widgetOpts):
                apply( self.widget.configure, (), widgetOpts)
            
        return action, rebuildDescr


    def getDescr(self):
        cfg = PortWidget.getDescr(self)
        data = self.widget.get()
        dt = []
        for val in data:
            dt.append(val[0])
        cfg['checkbuttonNames'] = dt
        return cfg
                

    def addMyMenu(self):
        """Add menu entry to param.Panel menu"""
        paramPanel = self.port.node.paramPanel
        parent = paramPanel.mBar
        
        Special_button = Tkinter.Menubutton(parent, text='Special',
                                            underline=0)
        paramPanel.menuButtons['Special'] = Special_button
        Special_button.pack(side=Tkinter.LEFT, padx="1m")

		# got rid of useless tearoff
        Special_button.menu = Tkinter.Menu(Special_button, tearoff=False)
        Special_button.menu.add_separator()

        Special_button.menu.add_command(label='Check All', underline=0, 
                                        command=self.widget.checkAll)
        Special_button.menu.add_command(label='Uncheck All', underline=0, 
                                        command=self.widget.uncheckAll)
        Special_button.menu.add_command(label='Invert All', underline=0, 
                                        command=self.widget.invertAll)
        Special_button.menu.add_separator()
        Special_button.menu.add_command(label='Regexp', underline=0, 
                                        command=self.toggleRegexpGUI)

        Special_button['menu'] = Special_button.menu

        apply( paramPanel.mBar.tk_menuBar, paramPanel.menuButtons.values() )


    def toggleRegexpGUI(self, event=None):
        if self.reGUI is None:
            self.reGUI = RegexpGUI(callback=self.widget.reSelect) 
        else:
            self.reGUI.toggleVisibility()
            
### use NECombobox instead         
##  class NEMultiRadioButtons(TkPortWidget):
##      """This class builds multi-radiobutton panel. Radiobuttons are packed in
##      a grid, the name of the button is used as label. valueList is used to add
##      the checkbuttons: data is stored in tuples. First entry is a string of
##      the button name. Optional second entry is a dictionary with Tkinter
##      checkbutton options. Optional third entry is a dictionary with grid
##      options."""

##      def __init__(self, port=None, master=None, 
##                   visibleInNodeByDefault=0, callback=None,
##                   label={'text':'File'}, labelSide='left',
##                   gridcfg=None, **kw):
        
##          TkPortWidget.__init__(self, port, master, visibleInNodeByDefault,
##                                callback, label, labelSide, gridcfg)
        
##          kw['callback'] = callback
##          self.tkwidget = apply( MultiRadiobuttons, (self.top,), kw )

##          if labelSide in ['right', 'e', 'bottom', 's']:
##              self.createLabel()
        

##      def set(self, data, run=0):
##          index = self.tkwidget.getIndex(data)
##          self.tkwidget.buttonDict.values()[0]['button'].var.set(index)
        
##          if run:
##              self.port.node.paramPanel.forceRun()


##      def get(self, event=None):
##          return self.tkwidget.get()
    

##      def getDataForSaving(self, event=None):
##          currentVal = self.tkwidget.buttonDict.values()[0]['button'].var.get()
##          name = self.tkwidget.buttonList[currentVal][0]
##          return name
    

##      def configure(self, **kw):
##          if len(kw)==0: # we are saving
##              cfg = PortWidget.configure(self)
##              data = self.tkwidget.get()
##              dt = []
##              for val in data:
##                  dt.append(val[0])
##              cfg['checkbuttonNames'] = dt
##              #if hasattr(self.port.node, 'mode'):
##              #    cfg['mode'] = self.port.node.mode
##              return cfg
##          else: # we are loading
##              if kw.has_key('checkbuttonNames'):
##                  data = kw['checkbuttonNames']
##                  self.tkwidget.rebuild(data)
##              #if kw.has_key('mode'):
##              #    self.port.node.mode = kw['mode']


class NEScrolledText(PmwPortWidget):

    configOpts = PortWidget.configOpts.copy()
    configOpts['initialValue'] = {
        'defaultValue':"", 'type':'string',
        }
    
    ownConfigOpts = {
        'hull_width':{
            'defaultValue':50, 'type':'int',
            'description':"widget width",
            },
        'hull_height':{
            'defaultValue':50, 'type':'int',
            'description':"hull height",
            },
        }
    configOpts.update( ownConfigOpts )
    

    def __init__(self, port, **kw):

        # get all arguments handled only by this widget and not by base class
        # remove them from kw
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                v = kw[k]
                widgetcfg[k] = kw.pop(k)
                setattr(self, k, v)
                
        # call base class constructor
        apply( PmwPortWidget.__init__, (self, port), kw)

        scrollkw = self.getPmwOptions(self, kw)
        
        # create widget
	self.widget = apply( Pmw.ScrolledText, (self.widgetFrame,), scrollkw)
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
        self.widgetFrame.bind("<Button-3>", self.postWidgetMenu)
	self.widget.pack(padx=5, pady=5, fill='both', expand=1)

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)

        self._setModified(False) # will be set to True by configure method

        # overwrite the callback function of the parameter panel's apply button
        self.port.node.paramPanel.applyFun = self.applyButton_cb


    def applyButton_cb(self, event=None):
        """This callback is called when the Apply button of the parameter
        panel is pressed. If we simply call node.schedule_cb() we do not
        modify the node and the value of the widget is not saved"""
        val = self.get()
        self.set(val)


    def get(self):
        data = self.widget.get()
        return data
    

    def set(self, value, run=1):
        if value is None:
            return
        self._setModified(True)
        self._newdata = True
        self.widget.settext(value)
        if self.port.network.runOnNewData.value is True and run:
            self.port.node.schedule()
            

    def configure(self, rebuild=True, **kw):
        # handle all Tkinter keywords for self.widget
        action, rebuildDescr = apply( PmwPortWidget.configure, (self, 0), kw)
            
        # handle ownConfigOpts that create an action
        if self.widget is not None:
            
            PmwOptions = self.widget.configure()
            for k, v in kw.items():
                # check if it is a Tk option for this Tk widget
                if k in ['hull_width', 'hull_height']:
                    action = 'resize'


                elif k == 'initialValue':
                    rebuildDescr['initialValue'] = self.initialValue = v


        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)
        elif action=='resize' and rebuild:
            if self.widget and rebuild:
                action = None

        return action, rebuildDescr


    def getDescr(self):
        cfg = PmwPortWidget.getDescr(self)
        cfg['hull_width'] = self.hull_width
        cfg['hull_height'] = self.hull_height
        cfg.update(self.widgetDescr)
        return cfg
        

class NEXYZGUI(PortWidget):

    # description of parameters that can only be used with the widget's
    # constructor
    configOpts = PortWidget.configOpts.copy()
    ownConfigOpts = {
        'widthX':{'min':1, 'max':500, 'type':'int', 'defaultValue':100},
        'heightX':{'min':1, 'max':500, 'type':'int', 'defaultValue':26},
        'wheelPadX':{'min':1, 'max':500, 'type':'int', 'defaultValue':4},
        'widthY':{'min':1, 'max':500, 'type':'int', 'defaultValue':100},
        'heightY':{'min':1, 'max':500, 'type':'int', 'defaultValue':26},
        'wheelPadY':{'min':1, 'max':500, 'type':'int', 'defaultValue':4},
        'widthZ':{'min':1, 'max':500, 'type':'int', 'defaultValue':100},
        'heightZ':{'min':1, 'max':500, 'type':'int', 'defaultValue':26},
        'wheelPadZ':{'min':1, 'max':500, 'type':'int', 'defaultValue':4},
        }

    configOpts.update( ownConfigOpts )

    def __init__(self, port, **kw):
        
        # create all attributes that will not be created by configure because
        # they do not appear on kw
        for key in self.ownConfigOpts.keys():
            v = kw.get(key, None)
            if v is None: # self.configure will not do anyting for this key
                setattr(self, key, self.ownConfigOpts[key]['defaultValue'])

        # get all arguments handled by NEThumbweel and not by PortWidget
        widgetcfg = {}
        for k in self.ownConfigOpts.keys():
            if k in kw:
                widgetcfg[k] = kw.pop(k)

        # call base class constructor
        apply( PortWidget.__init__, ( self, port), kw)

        # create the Thumbwheel widget
        self.widget = apply( xyzGUI, (self.widgetFrame,), widgetcfg)
        # bind right mouse button click
        self.widget.bind("<Button-3>", self.postWidgetMenu)
        self.widget.callbacks.AddCallback(self.newValueCallback)

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)

        if self.initialValue is not None:
            self.set(self.initialValue, run=0)
            
        self._setModified(False) # will be set to True by configure method

        
    def get(self):
        return self.widget.thumbx.value, self.widget.thumby.value, \
               self.widget.thumbz.value
    

    def set(self, val, run=1):
        self._setModified(True)
        self.widget.set(val[0],val[1],val[2])
        self._newdata = True
        if self.port.network.runOnNewData.value is True and run:
            self.port.node.schedule()


    def configure(self, rebuild=True, **kw):
        # call base class configure with rebuild=Flase. If rebuilt is needed
        # rebuildDescr will contain w=='rebuild' and rebuildDescr contains
        # modified descr
        action, rebuildDescr = apply( PortWidget.configure, (self, False), kw)
            
        # handle ownConfigOpts entries
        if self.widget is not None:

            widgetOpts = {}
            for k, v in kw.items():
                if k in self.ownConfigOpts.keys():
                    if k in ['widthX', 'heightX', 'wheelPadX',
                             'widthY', 'heightY', 'wheelPadY',
                             'widthZ', 'heightZ', 'wheelPadZ',]:
                        action = 'rebuild'
                        rebuildDescr[k] = v
                    else:
                        widgetOpts[k] = v

            if len(widgetOpts):
                apply( self.widget.configure, (), widgetOpts)

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)
        elif action=='resize' and rebuild:
            if self.widget and rebuild: # if widget exists
                action = None
            
        return action, rebuildDescr


    def getDescr(self):
        cfg = PortWidget.getDescr(self)
        for k in self.ownConfigOpts.keys():
            if k == 'typeX': # type has to be handled separately
                _type = self.widget.type
                if _type == int:
                    _type = 'int'
                else:
                    _type = 'float'
                if _type != self.ownConfigOpts[k]['defaultValue']:
                    cfg[k] = _type
                continue
            elif k == 'typeY': # type has to be handled separately
                _type = self.widget.type
                if _type == int:
                    _type = 'int'
                else:
                    _type = 'float'
                if _type != self.ownConfigOpts[k]['defaultValue']:
                    cfg[k] = _type
                continue
            if k == 'typeZ': # type has to be handled separately
                _type = self.widget.type
                if _type == int:
                    _type = 'int'
                else:
                    _type = 'float'
                if _type != self.ownConfigOpts[k]['defaultValue']:
                    cfg[k] = _type
                continue
            val = getattr(self.widget, k)
            if val != self.ownConfigOpts[k]['defaultValue']:
                cfg[k] = val

        return cfg


class NEVectEntry(NEEntry):
    """ this widget is a specialized Entry for typing in vector values
        a setValue() method has been added which checks that the input is
        correct """
    
    configOpts = TkPortWidget.configOpts.copy()

    ownConfigOpts = {
        'initialValue':{
            'defaultValue':'0, 0, 0', 'type':'string',
            },
        }
    configOpts.update( ownConfigOpts )


    def __init__(self, port, **kw):

        # Tkportwidget NEEntry:
        NEEntry.__init__(self, port, **kw)
        self.widget.bind('<Return>', self.setValue_cb)
        
        self.point = [0., 0, 0]
        self.text = "0 0 0"
        if self.initialValue is not None:
            self.set(self.initialValue, run=0)
            
        self.updateField()


    def setValue_cb(self, event=None, run=1):
        v = self.var.get()
        try:
            val = string.split(v)
        except: 
            self.updateField()
            return
       
        if val is None or len(val)!= 3:
            self.updateField()
            return        

        try:
            oldtext = self.text
            self.text = v
            self.point=[]
            self.point.append(float(val[0]))
            self.point.append(float(val[1]))
            self.point.append(float(val[2]))
        except:
            self.text = oldtext
            self.updateField()
            return

        self.updateField()
        self._setModified(True)
        
        if run:
            self.scheduleNode()


    def updateField(self):
        self.var.set(self.text)


    def get(self):
        return self.point


    def set(self, point, run=1):
        self._setModified(True)
        self.point = point
        text = "%s %s %s"%(point[0], point[1], point[2])
        self.text = text
        self.var.set(text)
        self._newdata = True

        if self.port.network.runOnNewData.value is True and run:
            self.port.node.schedule()



widgetsTable = {
    NEButton.__name__: NEButton,
    NEThumbWheel.__name__: NEThumbWheel,
    NECheckButton.__name__: NECheckButton,
    NEMultiCheckButtons.__name__: NEMultiCheckButtons,
    #NEMultiRadioButtons.__name__: NEMultiRadioButtons,
    #NERadiobutton.__name__: NERadiobutton,
    NEEntry.__name__: NEEntry,
    NEEntryNotScheduling.__name__: NEEntryNotScheduling,
    NEScrolledText.__name__: NEScrolledText,
    NEEntryWithFileBrowser.__name__: NEEntryWithFileBrowser,
    NEEntryWithDirectoryBrowser.__name__: NEEntryWithDirectoryBrowser,
    NEEntryWithFileSaver.__name__: NEEntryWithFileSaver,
    NEDial.__name__: NEDial,
    NEVectorGUI.__name__: NEVectorGUI,
    NEComboBox.__name__: NEComboBox,
    NEXYZGUI.__name__:NEXYZGUI,
    NEVectEntry.__name__:NEVectEntry,
}

# used by Editors.py to make widgets available in editor's pull down menus
#publicWidgetsTable = widgetsTable.copy()


def createWidgetDescr( className, descr=None ):
    """This function will return a widget description dictionnary for a widget
of type className. If descr is given it should be another widgetDescr dict.
The option in descr that are suitable for className type widget will be carried
over.
"""
    wdescr = {'class':className}
    if descr:
        klass = widgetsTable[className]
        for k, v in descr.items():
            if k in klass.configOpts:
                wdescr[k] = v
    return wdescr

        

class WidgetEditor:
    """class to build an GUI to let the user input values.
    description has to be a dictionary where the keys is the name of a
    parameters and the value is a dictionary describing the type of value.
    value types can be described using the keywords:
      min, max, type, validValues, defaultValue
    min and max can be int or float or None
    defaultValue: if missing value will default to minimum. If no min we use
                  max, if no max we set to 0
    type can be 'int', 'float' ,'dict', 'list', 'tuple, or string
    validValues is a list of valid entries, this build a ComboBox widget
    one can specify a type or a list of valid values.

    parameters with a list of values will be displayed using a combobox
    all others use entryfield widgets
    
    """
    
    def __init__(self, widget, master=None):
        #print "WidgetEditor.__init__"
        if master is None:
            master = Tkinter.Toplevel()
        self.top = Tkinter.Frame(master)
        master.protocol("WM_DELETE_WINDOW", self.Cancel_cb)
        self.widgetFormName = {}
        self.widget = widget
        self.port = widget.port # widget might change (rebuild), port does not
        widget.objEditor = self
        self.currentValues = {} # dictionnary used to save current values
                                # so we can decide what has changed
        descr = self.widget.configOpts
        
        currentConfig = self.widget.getDescr()
        #for k, v in currentConfig.items():
        #    if k in descr:
        #        if 'defaultValue' in descr[k]:
        #            descr[k]['defaultValue'] = v
        #descr['initialValue']['defaultValue'] = self.widget.get()

        # build widgets for each parameter
        keys = descr.keys()
        keys.sort()
        row = 0
        for k in keys:
            # the following keys are not exposed in the form
            if k in ['master', 'labelCfg', 'labelGridCfg', 'labelSide',
                     'widgetGridCfg', 'callback']:
                continue
            v = descr[k]
            opt = {'command':self.Apply_cb}
            w = None
            gridOpts = {'row':row, 'column':1, 'sticky':'ew'}
            type = v.get('type', None)
            if type is None:
                continue
            curval = currentConfig.pop(k, None)
            if v.has_key('validValues'):
                w = kbComboBox(self.top, scrolledlist_items=v['validValues'] )
                if v.has_key('defaultValue'):
                    opt['value'] = v['defaultValue']
                    w.selectitem(curval or v['defaultValue'])
            else:
                valid = {}

                if type is 'boolean':
                    var = Tkinter.IntVar()
                    opt['variable']=var
                    w = apply( Tkinter.Checkbutton, (self.top,), opt )
                    w.var = var
                    if v.has_key('defaultValue'):
                        opt['value'] = curval or v['defaultValue']
                        var.set(opt['value'])
                    gridOpts = {'row':row, 'column':1, 'sticky':'w'}

                elif type in ['int', 'float']:
                    valid['stringtovalue'] = eval(type)
                    if v.has_key('min'):
                        valid['min'] = v['min']
                        valid['minstrict'] = 0
                    if v.has_key('max'):
                        valid['max'] = v['max']
                        valid['maxstrict'] = 0
                    opt['validate'] = valid

                    if curval:
                        opt['value'] = curval
                    elif v.has_key('defaultValue'):
                        opt['value'] = v['defaultValue']
                    elif v.has_key('min'):
                        opt['value'] = v['min']
                    elif v.has_key('max'):
                        opt['value'] = v['max']
                    else:
                        opt['value'] = eval( type+'(0)')
                    if opt['value'] is None:
                        opt['value'] = 'None'
                    w = apply( Pmw.EntryField, (self.top,), opt )
                elif type in ['dict', 'list', 'tuple']:
                    if v.has_key('defaultValue'):
                        opt['value'] = curval or v['defaultValue']
                    w = apply( Pmw.EntryField, (self.top,), opt )
                elif type == 'string':
                    if v.has_key('defaultValue'):
                        opt['value'] = curval or v['defaultValue']
                    w = apply( Pmw.EntryField, (self.top,), opt )
                else:
                    if v.has_key('defaultValue'):
                        opt['value'] = curval or v['defaultValue']
                    else:
                        print 'skipping ', k, type
            if w:
                lab = Tkinter.Label(self.top, text=k)
                lab.grid(row=row, column=0, sticky='e')
                self.widgetFormName[k] = (w, v, opt['value'])
                apply( w.grid, (), gridOpts)
                row += 1

            self.currentValues[k] = opt['value']

        # add Tkinter Options entry
        row += 1
        Tkinter.Label(self.top, text="Tkinter Options").grid(
            row=row, column=0, sticky='e')

        w = apply( Pmw.EntryField, (self.top,), {'command':self.Apply_cb} )
        opt = {'defaultValue':None, 'type':'string'}

        self.widgetFormName['TkOptions'] = (w, opt, None)
        self.currentValues['TkOptions'] = None
        w.grid(row=row, column=1, sticky='ew')

        row += 1

        # add OK button
        Tkinter.Button(self.top, text='OK', command=self.OK_cb ).grid(
            column=0, row=row, sticky='ew')
        # add Apply button
        Tkinter.Button(self.top, text='Apply', command=self.Apply_cb ).grid(
            column=1, row=row, sticky='ew')
        # add Cancel button
        Tkinter.Button(self.top, text='Cancel', command=self.Cancel_cb ).grid(
            column=2, row=row, sticky='ew')

        self.top.pack()


    def getValues(self):
        result = {}
        for k, w_and_v_and_val in self.widgetFormName.items():
            w, v, value = w_and_v_and_val

            # parse TkOptions, append them to result. Since we parse and
            # append to results, we continue the loop after we are finished
            # parsing this key
            if k == "TkOptions": 
                spl = string.split(w.get(), ",")
                if not len(spl):
                    continue
                for s in spl:
                    if not len(s):
                        continue
                    n,m = string.split(s, '=')
                    n = string.strip(n)
                    m = string.strip(m)
                    result[n] = m
                continue
                
            if   v['type']=='boolean': cast = bool
            elif v['type']=='int':     cast = int
            elif v['type']=='float':   cast = float
            elif v['type']=='dict':    cast = eval
            elif v['type']=='list':    cast = eval
            elif v['type']=='tuple':   cast = eval
            elif v['type']=='string':  cast = str
            else:                      cast = str

            # get result from Pmw.EntryField
            if isinstance(w, Pmw.EntryField):
                val = w.get()
                if val == 'None':
                    if val != value:
                        result[k] = None
                    else:
                        continue
                val = cast(val)
            elif isinstance(w, Tkinter.Checkbutton):
                val = cast(w.var.get())
            else:
                val = cast(w.component('entryfield').get())

            if val != self.currentValues[k]:
                result[k] = val
                self.currentValues[k] = val

        return result


    def Apply_cb(self, event=None):
        values = self.getValues()
        if len(values):
            # call port.configureWidget rather than widget.configure
            # because widget could be destroyed by configure and
            # port.configureWidget deletes the old widget
            #apply( port.configureWidget, (), values)
            w, descr = apply( self.widget.configure, (), values)
            
            # in case we rebuild widget:
            if self.widget != self.port.widget:
                self.widget = self.port.widget
                self.widget.objEditor = self
                

    def OK_cb(self, event=None):
        self.Apply_cb()
        self.Cancel_cb()


    def Cancel_cb(self, event=None):
        # unselect checkbutton in Editor form
        if self.port.node.objEditor:
            self.port.editWtk.deselect()      

        self.widget.objEditor = None
        if self.port.objEditor is not None:
            self.port.objEditor.editWidgetVarTk.set(0)
        self.top.master.destroy()

         
