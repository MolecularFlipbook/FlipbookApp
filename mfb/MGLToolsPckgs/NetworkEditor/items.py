# Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
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
#
#

import warnings
import re
import Tkinter, Pmw, tkFileDialog
import sys
import math
import numpy.oldnumeric as Numeric
import types
import weakref
import traceback
import string
import threading
import os
import datetime
import user
import inspect
import copy
import random

from tkSimpleDialog import askstring
from mglutil.util.packageFilePath import getResourceFolderWithVersion
from NetworkEditor.ports import InputPort, OutputPort, RunNodeInputPort, \
     TriggerOutputPort, SpecialOutputPort
from mglutil.util.callback import CallBackFunction
from mglutil.util.uniq import uniq
from mglutil.util.misc import ensureFontCase
from mglutil.util.misc import suppressMultipleQuotes
from NetworkEditor.widgets import widgetsTable
from NetworkEditor.Editor import NodeEditor
from NetworkEditor.ports import InputPortsDescr, OutputPortsDescr

# namespace note: node's compute function get compiled using their origin
# module's __dict__ as global name space

from itemBase import NetworkItems

class NetworkNodeBase(NetworkItems):
    """Base class for a network editor Node
    """
    def __init__(self, name='NoName', sourceCode=None, originalClass=None,
                 constrkw=None, library=None, progbar=0, **kw):

        NetworkItems.__init__(self, name)
        self.objEditor = None # will be an instance of an Editor object
        self.network = None    # VPE network

        self.originalClass = originalClass
        if originalClass is None:
            self.originalClass = self.__class__

        self.library = library
        
        self.options = kw
        if constrkw is None:
            constrkw = {}
        self.constrkw = constrkw # dictionary of name:values to be added to
                                 # the call of the constructor when node
                                 # is instanciated from a saved network
                                 # used in getNodeSourceCode and
                                 # getNodesCreationSourceCode
        if not sourceCode:
            sourceCode = """def doit(self):\n\tpass\n"""
        self.setFunction(sourceCode)

        self.readOnly = False

        #self.mtstate = 0 # used by MTScheduler to schedule nodes in sub-tree
        #self.thread = None # will hold a ThreadNode object
        
        self.newData = 0            # set to 1 by outputData of parent node
        self.widthFirstTag = 0      # tag used by widthFirstTraversal
        self.isRootNode = 1 # when a node is created it isnot yet a child
        self.forceExecution = 0 # if the forceExecution flag is set
            # we will always run, else we check if new data is available
        self.expandedIcon = False       # True when widgets in node are shown
        self.widgetsHiddenForScale = False # will be set to true if node scales
                                           # below 1.0 while widget are seen

        # does the node have a progrs bar ?
        self.hasProgBar = progbar
        if self.hasProgBar:
            self.progBarH = 3 # Progress bar width
        else:
            self.progBarH = 0
            
        self.scaleSum = 1.0 # scale factor for this node's icon
        
        self.highlightOptions = {'highlightbackground':'red'}
        self.unhighlightOptions = {'highlightbackground':'gray50'}
        self.selectOptions = {'background':'yellow'}
        self.deselectOptions = {'background':'gray85'}

        self.posx = 0         # position where node will be placed on canvas
        self.posy = 0         # these vales are set in the addNode method of
                              # the canvas to which this node is added
                              
        self.inputPorts = []  # will hold a list of InputPort objects
        self.outputPorts = [] # will hold a list of OutputPort objects

        self._inputPortsID = 0  # used to assign InputPorts a unique number
        self._outputPortsID = 0 # used to assign OutputPorts a unique number

        self._id = None        # a unique node number, which is assigned in
                               # network.addNodes()

        #self.widgets = {}     # {widgetName: PortWidget object }
        #                      # Used to save the widget when it is unbound
        self.specialInputPorts = []
        self.specialOutputPorts = []
        self.specialPortsVisible = False
        self.children = [] # list of children nodes
        self.parents = [] # list of parent nodes
        self.nodesToRunCache = [] # list of nodes to be run when this node
                                  # triggers
        self.condition = None

        self.funcEditorDialog = None

        # ports description, these dictionaries are used to create ports
        # at node's instanciation
        self.inputPortsDescr = InputPortsDescr(self) # [{optionName:optionValue}]
        self.outputPortsDescr = OutputPortsDescr(self) # [{optionName:optionValue}]

        self.widgetDescr = {}  # {widgetName: {optionName:optionValue}}


        self.mouseAction['<Double-Button-1>'] = self.toggleNodeExpand_cb
        self.mouseAction['<Button-2>'] = self.startMoveOneNode

        self.hasMoved = False   # set to True in net.moveSubGraph()


    def onStoppingExecution(self):
        pass


    def beforeAddingToNetwork(self, network):
        NetworkItems.beforeAddingToNetwork(self, network)


    def safeName(self, name):
        """remove all weird symbols from node name so that it becomes a
regular string usabel as a Python variable in a saved network
"""
        name = name.replace(' ', '_') # name cannot contain spaces
        if name[0].isdigit():  # first letter cannot be a number
            name = '_'+name
        if name.isalnum(): return name
        if name.isdigit(): return name
        # replace weird characters by '_'
        newname = ''
        for c in name:
            if c.isalnum():
                newname += c
            else:# if c in ['/', '\\', '~', '$', '!']:
                newname+= '_'
        return newname
    
        
    def getUniqueNodeName(self):
        return '%s_%d'%(self.safeName(self.name), self._id)


    def configure(self, **kw):
        """Configure a NetworkNode object. Going through this framework tags
the node modified. Supports the following keywords:
name:       node name (string)
position:   node position on canvas. Must be a tuple of (x,y) coords
function:   the computational method of this node
expanded:   True or False. If True: expand the node
specialPortsVisible: True or False. If True: show the special ports
paramPanelImmediate: True or False. This sets the node's paramPanel immediate
                     state
"""

        ed = self.getEditor()
        
        for k,v in kw.items():
            if k == 'function':
                #solves some \n issues when loading saved networks
                v = v.replace('\'\'\'', '\'')
                v = v.replace('\"\"\"', '\'')
                v = v.replace('\'', '\'\'\'')
                #v = v.replace('\"', '\'\'\'')
                kw[k] = v
                self.setFunction(v, tagModified=True)
            elif ed is not None and ed.hasGUI:
                if k == 'name':
                    self.rename(v, tagModified=True)
                elif k == 'position':
                    self.move(v[0], v[1], absolute=True, tagModified=True)
                elif k == 'expanded':
                    if self.isExpanded() and v is False:
                        self.toggleNodeExpand_cb()
                    elif not self.isExpanded() and v is True:
                        self.toggleNodeExpand_cb()
                elif k == 'specialPortsVisible':
                    if self.specialPortsVisible and v is False:
                        self.hideSpecialPorts(tagModified=True)
                    elif not self.specialPortsVisible and v is True:
                        self.showSpecialPorts(tagModified=True)
                elif k == 'paramPanelImmediate':
                    self.paramPanel.setImmediate(immediate=v, tagModified=True)
                elif k == 'frozen':
                    if self.frozen is True and v is False:
                        self.toggleFrozen_cb()
                    elif self.frozen is False and v is True:
                        self.toggleFrozen_cb()
                    
                
    def getDescr(self):
        """returns a dict with the current configuration of this node"""
        cfg = {}
        cfg['name'] = self.name
        cfg['position'] = (self.posx, self.posy)
        cfg['function'] = self.sourceCode
        cfg['expanded'] = self.isExpanded()
        cfg['specialPortsVisible'] = self.specialPortsVisible
        cfg['paramPanelImmediate'] = self.paramPanel.immediateTk.get()
        cfg['frozen'] = self.frozen
        return cfg


    def rename(self, name, tagModified=True):
        """Rename a node. remember the name has changed, resize the node if
necessary"""
        if name == self.name or name is None or len(name)==0:
            return
        # if name contains ' " remove them
        name = name.replace("'", "")
        name = name.replace('"', "")
        
        self.name=name
        if self.iconMaster is None:
            return
        canvas = self.iconMaster
        canvas.itemconfigure(self.textId, text=self.name)
        self.autoResizeX()
        if tagModified is True:
            self._setModified(True)


    def displayName(self, displayedName, tagModified=True):
        """display the displyed node name. remember the name has changed, resize the node if
necessary"""
        if displayedName is None or len(displayedName)==0:
            return
        # if name contains ' " remove them
        displayedName = displayedName.replace("'", "")
        displayedName = displayedName.replace('"', "")
        
        if self.iconMaster is None:
            return
        canvas = self.iconMaster
        canvas.itemconfigure(self.textId, text=displayedName)
        self.autoResizeX()
        if tagModified is True:
            self._setModified(True)


    def ischild(self, node):
        """returns True is self is a child node of node
"""
        conn = self.getInConnections()
        for c in conn:
            if c.blocking is True:
                node2 = c.port1.node
                if node2 == node:
                    return True                   
                else:
                    return node2.ischild(node)
        return False

        
    def isMacro(self):
        """Returns False if this node is not a MacroNode, returns True if
        MacroNode"""
        
        return False
    
            
    def startMoveOneNode(self, event):
        # get a handle to the network of this node
        net = self.network
        # save the current selection
        if len(net.selectedNodes):
            self.tempo_curSel = net.selectedNodes[:]
            # clear the current selection
            net.clearSelection()
        # select this node so we can move it
        net.selectNodes([self], undo=0)
        # call the function to register functions for moving selected nodes
        net.moveSelectedNodesStart(event)
        # register an additional function to deselect this node
        # and restore the original selection
        num = event.num
        # FIXME looks like I am binding this many times !
        net.canvas.bind("<ButtonRelease-%d>"%num, self.moveSelectedNodeEnd,
                      '+')

    def moveSelectedNodeEnd(self, event):
        # get a handle to the network of this node
        net = self.network
        # clear the selection (made of this node)
        net.clearSelection()
        # if we saved a selection when we started moving this node, restore it
        if hasattr(self, 'tempo_curSel'):
            net.selectNodes(self.tempo_curSel, undo=0)
            del self.tempo_curSel
        net.canvas.unbind("<ButtonRelease-%d>"%event.num)


    def isModified(self):
        # loop over all input ports, all widgets, all outputports, and report
        # if anything has been modified
        modified = False
        if self._modified:
            return True

        # input ports and widgets
        for p in self.inputPorts:
            if p._modified:
                modified = True
                break
            if p.widget:
                if p.widget._modified:
                    modified = True
                    break
        if modified is True:
            return modified

        # output ports
        for p in self.outputPorts:
            if p._modified:
                modified = True
                break

        return modified

        
    def resetModifiedTag(self):
        """set _modified attribute to False in node, ports, widgets."""
        
        self._modified = False
        for p in self.inputPorts:
            p._modified = False
            if p.widget:
                p.widget._modified = False
        for p in self.outputPorts:
            p._modified = False


    def resetTags(self):
        """set _modified attribute to False in node, ports, widgets.
        Also, sets _original attribute to True in node, ports, widgets
        And we also reset the two flags in all connections from and to ports"""
        
        self._modified = False
        self._original = True
        for p in self.inputPorts:
            p._modified = False
            p._original = True
            if p.widget:
                p.widget._modified = False
                p.widget._original = True
            for c in p.connections:
                c._modified = False
                c._original = True
                
        for p in self.outputPorts:
            p._modified = False
            p._original = True
            for c in p.connections:
                c._modified = False
                c._original = True
                

    def getInputPortByName(self, name):
        # return the an input port given its name
        for p in self.inputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: input port "%s" not found in node %s'%(name, self.name))


    def getOutputPortByName(self, name):
        # return the an output port given its name
        for p in self.outputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: output port "%s" not found in node %s'%(name, self.name))

    def getOutputPortByType(self, type, name=None):
        # return the matching or first output port given its type
        if len(self.outputPorts) == 0:
            return None
        
        lDatatypeObject = \
              self.outputPorts[0].getDatatypeObjectFromDatatype(type)
                                                                
        lPort = None
        for p in self.outputPorts:            
            if p.datatypeObject == lDatatypeObject:
                if p.name == name:
                    return p
                elif p is None:
                    return p                  
                elif lPort is None:
                    lPort = p
        if lPort is not None:   
            return lPort                
        
        return None
        
    def getSpecialInputPortByName(self, name):
        # return the an input port given its name
        for p in self.specialInputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: special input port "%s" not found in node %s'%(name, self.name))


    def getSpecialOutputPortByName(self, name):
        # return the an output port given its name
        for p in self.specialOutputPorts:
            if p.name==name:
                return p
        warnings.warn(
            'WARNING: special output port "%s" not found in node %s'%(name, self.name))


    def getInConnections(self):
        l = []
        for p in self.inputPorts:
            l.extend(p.connections)
        for p in self.specialInputPorts:
            l.extend(p.connections)
        return l


    def getOutConnections(self):
        l = []
        for p in self.outputPorts:
            l.extend(p.connections)
        for p in self.specialOutputPorts:
            l.extend(p.connections)
        return l


    def getConnections(self):
        return self.getInConnections()+self.getOutConnections()


    def getWidgetByName(self, name):
        port = self.inputPortByName[name]
        if port:
            if port.widget:
                return port.widget
        

##############################################################################
# The following methods are needed to save a network
# getNodeDefinitionSourceCode() is called by net.getNodesCreationSourceCode()
##############################################################################
        
    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        """This method builds the text-string to describe a network node
in a saved file.
networkName: string holding the networkName
indent: string of whitespaces for code indentation. Default: ''
ignoreOriginal: True/False. Default: False. If set to True, the node's attr
                _original is ignored (used in cut/copy/paste nodes inside a
                macro that came from a node library where nodes are marked
                original
This method is called by net.getNodesCreationSourceCode()
NOTE: macros.py MacroNode re-implements this method!"""

        lines = []
        nodeName = self.getUniqueNodeName()

        ##################################################################
        # add lines to import node from library, instanciate node, and
        # add node to network
        ##################################################################
        indent, l = self.getNodeSourceCodeForInstanciation(
            networkName, indent=indent, ignoreOriginal=ignoreOriginal)
        lines.extend(l)

        ##################################################################
        # fetch code that desccribes the changes done to this node compared
        # to the base class node
        ##################################################################
        txt = self.getNodeSourceCodeForModifications(
            networkName, indent=indent, ignoreOriginal=ignoreOriginal)
        lines.extend(txt)

        txt = self.getStateDefinitionCode(nodeName=nodeName,indent=indent)
        lines.extend(txt)

        return lines


    def getStateDefinitionCode(self, nodeName, indent=''):
        #print "getStateDefinitionCode"
        return ''


    def getNodeSourceCodeForModifications(self, networkName, indent="",
                                          ignoreOriginal=False):
        """Return the code that describes node modifications compared to the
original node (as described in a node library)"""

        lines = []
        
        ##################################################################
        # add lines for ports if they changed compared to the base class
        ##################################################################
        indent, l =  self.getNodeSourceCodeForPorts(networkName, indent , ignoreOriginal)
        lines.extend(l)

        ##################################################################
        # add lines for widgets: add/delete/configure/unbind, and set value
        ##################################################################
        indent, l =  self.getNodeSourceCodeForWidgets(networkName, indent,
                                                      ignoreOriginal)
        lines.extend(l)

        ##################################################################
        # add lines for node changes (name, expanded, etc)
        ##################################################################
        indent, l = self.getNodeSourceCodeForNode(networkName, indent,
                                                  ignoreOriginal)
        lines.extend(l)

        return lines


    def getNodeSourceCodeForInstanciation(self, networkName="masterNet",
                                          indent="", ignoreOriginal=False,
                                          full=0):
        """This method is called when saving a network. Here, code is
generated to import a node from a library, instanciate the node, and adding it
to the network."""
        
        lines = []
        ed = self.getEditor()
        nodeName = self.getUniqueNodeName()

        ##################################################################
        # Abort if this node is original (for example, inside a macro node)
        ##################################################################
        if self._original is True and not full and not ignoreOriginal:
            return indent, lines

        ed._tmpListOfSavedNodes[nodeName] = self
        
        k = self.__class__

        ##################################################################
        # add line to import node from the library
        ##################################################################
        if self.library is not None:
            libName = self.library.varName
        else:
            libName = None
            #if self.library.file is not None: # user defined library
##             if False: # skip this test!!
##                 l = "from mglutil.util.packageFilePath import "+\
##                     "getObjectFromFile\n"
##                 lines.append(indent+l)
##                 lines.append(indent+"%s = getObjectFromFile( '%s', '%s')\n"%(
##                     k.__name__, self.library.file, k.__name__))
##             else:
##             line = "from "+k.__module__+" import "+k.__name__+"\n"
##             lines.append(indent+line)
##         else:

        line = "from "+k.__module__+" import "+k.__name__+"\n"
        lines.append(indent+line)
        
        ##################################################################
        # add line with constructor keywords if needed
        ##################################################################
        constrkw = ''
        for name, value in self.constrkw.items():
            constrkw = constrkw + name+'='+str(value)+', '

        # this line seems redondant, 
        # but is usefull when the network is saved and resaved
        # especially with pmv nodes
        constrkw = constrkw + "constrkw="+str(self.constrkw)+', '

        ##################################################################
        # add line to instanciate the node
        ##################################################################
        line=nodeName+" = "+k.__name__+"("+constrkw+"name='"+\
              self.name+"'"
        if libName is not None:
            line = line + ", library="+libName
        line = line + ")\n"
        lines.append(indent+line)

        ##################################################################
        # add line to add the node to the network
        ##################################################################
        txt = networkName+".addNode("+nodeName+","+str(self.posx)+","+\
              str(self.posy)+")\n"
        lines.append(indent+txt)
        return indent, lines
    

    def getNodeSourceCodeForPorts(self, networkName, indent="",
                                  ignoreOriginal=False,full=0,
                                  dummyNode=None, nodeName=None):
        """Create code used to save a network which reflects changes of ports
compared to the port definitions in a given network node of a node library.
We create text to configure a port with changes, adding a port or deleting
a port. If optional keyword 'full' is set to 1, we will append text to
configure unchanged ports"""

        lines = []
        ed = self.getEditor()

        if dummyNode is None:
            # we need the base class node
            if issubclass(self.__class__, FunctionNode):
                lKw = {'masternet':self.network}
                lKw.update(self.constrkw)
                dummyNode = apply(self.__class__,(), lKw)
            else:
                dummyNode = self.__class__()
        
        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        ###############################################################
        # created save strings for inputPorts
        ###############################################################
        i = 0
        lDeleted = 0
        for index in range(len(dummyNode.inputPortsDescr)):
            
            # Delete remaining input ports if necessary
            if i >= len(self.inputPorts):
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.inputPortByName['%s'])\n"%(
                #txt = "%s.deletePort(%s.getInputPortByName('%s'))\n"%(
                    nodeName, nodeName,
                    dummyNode.inputPortsDescr[index]['name'])
                lines.append(indent+txt)
                continue

            ip = self.inputPorts[i]

            # delete input port
            if ip._id != index:
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.inputPortByName['%s'])\n"%(
                #txt = "%s.deletePort(%s.getInputPortByName('%s'))\n"%(
                    nodeName, nodeName,
                    dummyNode.inputPortsDescr[index]['name'])
                lines.append(indent+txt)
                lDeleted += 1
                continue

            # modify input port
            else:
                if ip._modified is True or ignoreOriginal is True:
                    if full:
                        changes = ip.getDescr()
                    else:
                        changes = ip.compareToOrigPortDescr()
                    if len(changes):
                        if nodeName != 'self': 
                            lines = self.checkIfNodeForSavingIsDefined(
                                               lines, networkName, indent)
                        txt = "apply(%s.inputPortByName['%s'].configure, (), %s)\n"%(
                            nodeName, dummyNode.inputPortsDescr[ip._id]['name'], str(changes) )
                        #txt = "apply(%s.inputPorts[%s].configure, (), %s)\n"%(
                        #    nodeName, ip.number, str(changes) )
                        lines.append(indent+txt)
                i = i + 1
                continue

        # check if we have to add additional input ports
        for p in self.inputPorts[len(dummyNode.inputPortsDescr) - lDeleted:]:
            if p._modified is True or ignoreOriginal is True:
                descr = p.getDescr()
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "apply(%s.addInputPort, (), %s)\n"%(
                    nodeName, str(descr) )
                lines.append(indent+txt) 
            

        ###############################################################
        # created save strings for outputPorts
        ###############################################################
        i = 0
        for index in range(len(dummyNode.outputPortsDescr)):

            # Delete remaining output ports if necessary
            if i >= len(self.outputPorts):
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.outputPortByName['%s'])\n"%(
                    nodeName, nodeName,
                    dummyNode.outputPortsDescr[index]['name'])
                lines.append(indent+txt)
                continue
                
            op = self.outputPorts[i]

            # delete output port
            if not op._id == index:
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "%s.deletePort(%s.outputPortByName['%s'])\n"%(
                    nodeName, nodeName,
                    dummyNode.outputPortsDescr[index]['name'])
                lines.append(indent+txt)
                continue
                    
            # modify output port
            else:
                if op._modified is True or ignoreOriginal is True:
                    if full:
                        changes = op.getDescr()
                    else:
                        changes = op.compareToOrigPortDescr()
                    if len(changes):
                        if nodeName != 'self': 
                            lines = self.checkIfNodeForSavingIsDefined(
                                               lines, networkName, indent)
                        txt = "apply(%s.outputPortByName['%s'].configure, (), %s)\n"%(
                            nodeName, dummyNode.outputPortsDescr[op._id]['name'], str(changes) )
                        #txt = "apply(%s.outputPorts[%s].configure, (), %s)\n"%(
                        #    nodeName, op.number, str(changes) )
                        lines.append(indent+txt)
                i = i + 1
                continue

        # check if we have to add additional output ports
        for p in self.outputPorts[len(dummyNode.outputPortsDescr):]:
            if p._modified is True or ignoreOriginal is True:
                descr = p.getDescr()
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                txt = "apply(%s.addOutputPort, (), %s)\n"%(
                    nodeName, str(descr) )
                lines.append(indent+txt) 

        # makes the specials ports visible if necessary
        if self.specialPortsVisible:           
            if nodeName != 'self': 
                lines = self.checkIfNodeForSavingIsDefined(
                                   lines, networkName, indent)
            txt = "apply(%s.configure, (), {'specialPortsVisible': True})\n"%(nodeName)
            lines.append(indent+txt) 

        return indent, lines


    def getNodeSourceCodeForWidgets(self, networkName, indent="",
                                    ignoreOriginal=False, full=0,
                                    dummyNode=None, nodeName=None):
        """Create code used to save a network which reflects changes of
widgets compared to the widget definitions in a given network node of a
node library.
We create text to configure a widget with changes, adding a widget or deleting
a widget. If optional keyword 'full' is set to 1, we will append text to
configure unchanged widgets."""

        lines = []
        ed = self.getEditor()

        if dummyNode is None:
            # we need the base class node
            if issubclass(self.__class__, FunctionNode):
                lKw = {'masternet':self.network}
                lKw.update(self.constrkw)
                dummyNode = apply(self.__class__,(), lKw)
            else:
                dummyNode = self.__class__()

        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        for i in range(len(self.inputPorts)):
            p = self.inputPorts[i]
            if p._id >= len(dummyNode.inputPortsDescr):
                origDescr = None
            elif p.name != dummyNode.inputPortsDescr[p._id]['name']:
                origDescr = None
            else:
                try:
                    origDescr = dummyNode.widgetDescr[p.name]
                except:
                    origDescr = None
            w = p.widget
            try:
                ownDescr = w.getDescr()
            except:
                ownDescr = None

            #############################################################
            # if current port has no widget and orig port had no widget:
            # continue
            #############################################################
            if ownDescr is None and origDescr is None:
                pass

            #############################################################
            # if current port has no widget and orig port had a widget:
            # unbind the widget. Also, check if the port was modified:
            # unbinding and deleting a widget sets the port._modifed=True
            #############################################################
            elif ownDescr is None and origDescr is not None:
                if (p._modified is True) or (ignoreOriginal is True):
                    if nodeName != 'self': 
                        lines = self.checkIfNodeForSavingIsDefined(
                                           lines, networkName, indent)
                    ## distinguish between "delete" and "unbind":
                    # 1) Delete event (we don't have _previousWidgetDescr)
                    if p._previousWidgetDescr is None:
                        txt = "%s.inputPortByName['%s'].deleteWidget()\n"%(
                            nodeName, self.inputPortsDescr[i]['name'])
                        #txt = "%s.inputPorts[%d].deleteWidget()\n"%(
                        #    nodeName, i)
                        lines.append(indent+txt)
                    # 2) unbind event (we have _previousWidgetDescr)
                    else:
    
    
                        # first, set widget to current value
                        txt1 =  self.getNodeSourceCodeForWidgetValue(
                            networkName, i, indent, ignoreOriginal, full)
                        lines.extend(txt1)
                        # then unbind widget
                        
                        txt2 = "%s.inputPortByName['%s'].unbindWidget()\n"%(
                            nodeName, self.inputPortsDescr[i]['name'])
                        #txt2 = "%s.inputPorts[%d].unbindWidget()\n"%(
                        #    nodeName, i)
                        lines.append(indent+txt2)

            #############################################################
            # if current port has widget and orig port had no widget:
            # create the widget
            #############################################################
            elif ownDescr is not None and origDescr is None:
                if nodeName != 'self': 
                    lines = self.checkIfNodeForSavingIsDefined(
                                       lines, networkName, indent)
                # create widget
                txt = \
                 "apply(%s.inputPortByName['%s'].createWidget, (), {'descr':%s})\n"%(
                    nodeName, self.inputPortsDescr[i]['name'], str(ownDescr ) )
                #txt = \
                # "apply(%s.inputPorts[%d].createWidget, (), {'descr':%s})\n"%(
                #     nodeName, i, str(ownDescr ) )
                lines.append(indent+txt)

                # Hack to set widget. This fixes the ill sized nodes
                # when new widgets have been added to a node (MS)
                wmaster = ownDescr.get('master', None)
                if wmaster=='node':
                    txt = "%s.inputPortByName['%s'].widget.configure(master='node')\n"%(nodeName, self.inputPortsDescr[i]['name'])
                lines.append(indent+txt)

                # set widget value
                txt = self.getNodeSourceCodeForWidgetValue(
                    networkName, i, indent, ignoreOriginal, full, nodeName)
                lines.extend(txt)
                
            #############################################################
            # if current port has widget and orig port has widget:
            # check if both widgets are the same, then check if changes
            # occured.
            # If widgets are not the same, delete old widget, create new
            #############################################################
            elif ownDescr is not None and origDescr is not None:
                if ownDescr['class'] == origDescr['class']:
                    if p.widget._modified is True or ignoreOriginal is True:
                        if full:
                            changes = ownDescr
                        else:
                            changes = w.compareToOrigWidgetDescr()
                        if len(changes):
                            if nodeName != 'self': 
                                lines = self.checkIfNodeForSavingIsDefined(
                                                   lines, networkName, indent)

                            if changes.has_key('command'):
                                # extract and build the correct CB function name
                                lCommand = changes['command']
                                lCommandStr = str(lCommand)
                                lCbIndex = lCommandStr.find('.')
                                lCbFuncName = nodeName + lCommandStr[lCbIndex:]
                                lCbIndex = lCbFuncName.find(' ')
                                lCbFuncName = lCbFuncName[:lCbIndex]
                                changes['command'] = lCbFuncName
                                
                                # the changes['command'] is now a string
                                # so, we need to get rid of the quote 
                                # that comes with the output
                                lChangesStr = str(changes)  
                                lQuoteIndex = lChangesStr.find(lCbFuncName) 
                                lChanges = lChangesStr[:lQuoteIndex-1] + \
                                       lCbFuncName + \
                                       lChangesStr[lQuoteIndex+len(lCbFuncName)+1:]  
                            else:
                                lChanges = str(changes)
                                
                            txt = \
                            "apply(%s.inputPortByName['%s'].widget.configure, (), %s)\n"%(
                                nodeName, self.inputPortsDescr[i]['name'], lChanges)
                            #txt = \
                            #"apply(%s.inputPorts[%d].widget.configure, (), %s)\n"%(
                            #    nodeName, i, str(changes))
                            lines.append(indent+txt)
                else:
                    if nodeName != 'self': 
                        lines = self.checkIfNodeForSavingIsDefined(
                                           lines, networkName, indent)
                    txt1 = "%s.inputPortByName['%s'].deleteWidget()\n"%(
                        nodeName, self.inputPortsDescr[i]['name'])
                    #txt1 = "%s.inputPorts[%d].deleteWidget()\n"%(
                    #    nodeName,i)
                    txt2 = \
                     "apply(%s.inputPortByName['%s'].createWidget, (), {'descr':%s})\n"%(
                               nodeName, self.inputPortsDescr[i]['name'], str(ownDescr) )
                    #txt2 = \
                    #"apply(%s.inputPorts[%d].createWidget, (), {'descr':%s})\n"%(
                    #           nodeName, i, str(ownDescr) )
                    lines.append(indent+txt1)
                    lines.append(indent+txt2)
                # and set widget value
                txt = self.getNodeSourceCodeForWidgetValue(
                    networkName, i, indent, ignoreOriginal, full, nodeName)
                lines.extend(txt)
                    
        return indent, lines


    def getNodeSourceCodeForWidgetValue(self, networkName, portIndex,
                                        indent="", ignoreOriginal=False,
                                        full=0, nodeName=None):
        """Returns code to set the widget value. Note: here we have to take
        unbound widgets into account."""
        
        #############################################################
        # Setting widget value sets widget _modified=True
        #############################################################
        lines = []
        returnPattern = re.compile('\n') # used when data is type(string)

        p = self.inputPorts[portIndex]

        # we need the base class node
        if issubclass(self.__class__, FunctionNode):
            lKw = {'masternet':self.network}
            lKw.update(self.constrkw)
            dummyNode = apply(self.__class__,(), lKw)
        else:
            dummyNode = self.__class__()
        
        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        #############################################################
        # Get data and original widget description to check if value
        # changed
        #############################################################
        ## do we have a widget ?
        if p.widget:
            ## is it an original widget?
            try:
                origDescr = dummyNode.widgetDescr[p.name]
            except:
                ## or a new widget
                origDescr = {}
            val = p.widget.getDataForSaving()

        ## do we have an unbound widget ?
        elif p.widget is None and p._previousWidgetDescr is not None:
            origDescr = p._previousWidgetDescr
            val = p._previousWidgetDescr['initialValue']
        ## no widget ?
        else:
            return lines

        #############################################################
        # Compare data to default value, return if values are the same
        #############################################################

##         ## CASE 1: BOUND WIDGET:
##         if p.widget:
##             # MS WHY ignor original when cut and copy???
##             # ignoreOriginal is set True when cut|copy
##             #if not p.widget._modified and not ignoreOriginal:
##             #    return lines

##             # 1) compare value to initial value of widget descr
##             wdescr = p.widget.getDescr()
##             if wdescr.has_key('initialValue'):
##                 if val==wdescr['initialValue']: # value is initial value
##                     return lines

##             # 2) else: compare to initialValue in node base class definition
##             else:
##                 # 3) if the widget's original description has an initialValue
##                 if origDescr.has_key('initialValue'):
##                     if val == origDescr['initialValue']:
##                         return lines
##                 # 4) else, compare to widget base class defined initialValue
##                 else:
##                     origWidgetDescr = p.widget.__class__.configOpts
##                     if val == origWidgetDescr['initialValue']['defaultValue']:
##                         return lines
 
##         ## CASE 2: UNBOUND WIDGET:
##         else:
##             descr = dummyNode.widgetDescr[p.name]
##             #if descr.has_key('initialValue') and val == descr['initialValue']:
##             #    return lines

        #############################################################
        # Create text to save widget value
        #############################################################
        if nodeName != 'self': 
            lines = self.checkIfNodeForSavingIsDefined(
                               lines, networkName, indent)
        if p.widget is None:
            #widget has been unbinded in the before or after adding to network
            #as it will be unbinded later we can safely rebind it to set the widget
            datatxt = '%s.inputPortByName[\'%s\'].rebindWidget()\n'%( 
                       nodeName, self.inputPortsDescr[portIndex]['name'])
            lines.append(indent+datatxt)

        if type(val)==types.StringType:
            if returnPattern.search(val): #multi - line data
                datatxt = \
                    '%s.inputPortByName[\'%s\'].widget.set(r"""%s""", run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val)
            else:
                datatxt = '%s.inputPortByName[\'%s\'].widget.set(r"%s", run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val)
        else:
            if hasattr(val, 'getDescr'):
                datatxt = '%s.inputPortByName[\'%s\'].widget.set(%s, run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val.getDescr() )
            else:
                datatxt = '%s.inputPortByName[\'%s\'].widget.set(%s, run=False)\n'%( 
                    nodeName, self.inputPortsDescr[portIndex]['name'], val)
        lines.append(indent+datatxt)

        return lines


    def getNodeSourceCodeForNode(self, networkName, indent="", 
                                 ignoreOriginal=False, full=0, nodeName=None):
        """return code to configure a node with modifications compared to
the node definition in a node library. Note: 
"""
        lines = []
        
        if (self._modified is False) and (ignoreOriginal is False):
            return indent, lines
         
        if full:
            changes = self.getDescr().copy()
        else:
            changes = self.compareToOrigNodeDescr()

        if changes.has_key('name'):
            changes.pop('name') # name is passed to constructor
        if changes.has_key('position'):
            changes.pop('position') # position is set in addNode

        if nodeName is None:
            nodeName = self.getUniqueNodeName()

        if changes.has_key('function'):
            changes.pop('function') 
            # function has to be set separately:
            code, i = self.getNodeSourceCodeForDoit(
                networkName=networkName,
                nodeName=nodeName,
                indent=indent,
                ignoreOriginal=ignoreOriginal)
            if code:
                # Note: the line to add the code to the node is returned
                # within 'code'
                lines.extend(code)

        if len(changes):
            txt = "apply(%s.configure, (), %s)\n"%(
                nodeName, str(changes))
            lines.append(indent+txt)

        return indent, lines


    def getNodeSourceCodeForDoit(self, networkName, nodeName,indent="",
                                 ignoreOriginal=False, full=0):
        lines = []
        ed = self.getEditor()
        
        if (self._modified is True) or (ignoreOriginal is True):
            if nodeName != 'self': 
                lines = self.checkIfNodeForSavingIsDefined(
                                   lines, networkName, indent)
            lines.append(indent+"code = \"\"\"%s\"\"\"\n"%self.sourceCode)
            lines.append(indent+"%s.configure(function=code)\n"% nodeName)

        return lines, indent


    def getAfterConnectionsSourceCode(self, networkName, indent="",
                                      ignoreOriginal=False):
        """Here, we provide a hook for users to generate source code which
might be needed to adress certain events after connections were formed:
for example, connections might generate new ports."""
        
        # The MacroOutputNode subclasses this method and returns real data
        lines = []
        return lines


    def compareToOrigNodeDescr(self):
        """compare this node to the original node as defined in a given node
library, such as StandardNodes. Return a dictionary containing the
differences."""
        
        ownDescr = self.getDescr().copy()
        dummy = self.__class__()  # we need to create a base class node
                                  # we dont need to add the self generated port
                                  # as we only look here for the node modifications

        for k,v in ownDescr.items():
            if k == 'name':
                if v == dummy.name:
                    ownDescr.pop(k)

            elif k == 'position':  # this is a bit tricky: the dummy node
            # has not been added to a net yet, thus we assume a new position
                continue

            elif k == 'function':
                #we don't compare the prototype as it is automatically generated
                #the code itself is what may have be changed
                if v[v.find(':'):] == dummy.sourceCode[dummy.sourceCode.find(':'):]:
                    ownDescr.pop(k)

            elif k == 'expanded':
                if v == dummy.inNodeWidgetsVisibleByDefault:
                    ownDescr.pop(k)

            elif k == 'specialPortsVisible':
                if v == dummy.specialPortsVisible:
                    ownDescr.pop(k)

            elif k == 'paramPanelImmediate': # default value is 0
                if v == 0 or v is False:
                    ownDescr.pop(k)

            elif k == 'frozen': # default is False
                if v == dummy.frozen:
                    ownDescr.pop(k)

        return ownDescr
                                 

    def checkIfNodeForSavingIsDefined(self, lines, networkName, indent):
        """This method fixes a problem with saving macros that come from a
node library. If only a widget value has changed, we do not have a handle
to the node. Thus, we need to create this additional line to get a handle
"""
        
        ed = self.getEditor()
        nodeName = self.getUniqueNodeName()

        if ed._tmpListOfSavedNodes.has_key(nodeName) is False:

            # This part is a bit complicated: we need to define the various
            # macro nodes if we have nested macros and they are not explicitly
            # created (e.g. a macro from a node library)
            from macros import MacroNetwork
            if isinstance(self.network, MacroNetwork):
                roots = self.network.macroNode.getRootMacro()
                for macro in roots[1:]: # skip root, because this is always defined!?
                    nn = macro.getUniqueNodeName() # was nn = 'node%d'%macro._id
                    if ed._tmpListOfSavedNodes.has_key(nn) is False:
                        txt = "%s = %s.macroNetwork.nodes[%d]\n"%(
                            nn, macro.network.macroNode.getUniqueNodeName(),
                            macro.network.nodeIdToNumber(macro._id))
                        lines.append(indent+txt)
                        ed._tmpListOfSavedNodes[nn] = macro                        
                        
            # now process the 'regular' nodes
            #import pdb;pdb.set_trace()
            txt = "%s = %s.nodes[%d]\n"%(nodeName, networkName,
                self.network.nodeIdToNumber(self._id))
            lines.append(indent+txt)
            ed._tmpListOfSavedNodes[nodeName] = self
        return lines
    

#############################################################################
#### The following methods are needed to generate source code (not for saving
#### networks)
#############################################################################


    def saveSource_cb(self, dependencies=False):
        """ the classname is extracted from the given filename
"""
        lPossibleFileName = "New" + self.name + ".py"
        lPossibleFileNameSplit = lPossibleFileName.split(' ')
        initialfile = ''
        for lSmallString in lPossibleFileNameSplit:
            initialfile += lSmallString

        userResourceFolder = self.getEditor().resourceFolderWithVersion
        if userResourceFolder is None:
            return
        userVisionDir = userResourceFolder + os.sep + 'Vision' + os.sep
        userLibsDir = userVisionDir + 'UserLibs' + os.sep
        defaultLibDir = userLibsDir + 'MyDefaultLib'

        file = tkFileDialog.asksaveasfilename(
                    initialdir = defaultLibDir , 
                    filetypes=[('python source', '*.py'), ('all', '*')],
                    title='Save source code in a category folder',
                    initialfile=initialfile
                    )

        if file:
            # get rid of the extension and of the path
            lFileSplit = file.split('/')
            name = lFileSplit[-1].split('.')[0]
            self.saveSource(file, name, dependencies)
            # reload the modified library
            self.getEditor().loadLibModule(str(lFileSplit[-3]))


    def saveSource(self, filename, classname, dependencies=False):
        f = open(filename, "w")
        map( lambda x, f=f: f.write(x), 
             self.getNodeSourceCode(classname, 
                                    networkName='self.masterNetwork',
                                    dependencies=dependencies) )
        f.close()


    def getNodeSourceCode(self, className, networkName='self.network',
                          indent="", dependencies=False):
        """This method is called through the 'save source code' mechanism.

Generate source code describing a node. This code can be put 
into a node library. This is not for saving networks.

dependencies: True/False
    False: the node is fully independent from his original node. 
    True : the node is saved as a subclass of the original node, and only 
           modifications from the original are saved. 
"""
        lines = []

        kw = {} # keywords dict
        kw['dependencies'] = dependencies

        indent0 = indent

        txt, indent  = apply(self.getHeaderBlock, (className, indent), kw)
        lines.extend(txt)

        # this make sure the port types will be avalaible when saved code will run
        lTypes = {}
        lSynonyms = {}
        lPorts = self.inputPorts + self.outputPorts
        for p in lPorts:
            lName = p.datatypeObject.__class__.__name__
            if (lTypes.has_key(lName) is False) and \
               (p.datatypeObject.__module__ != 'NetworkEditor.datatypes'):
                lTypes[lName] = p.datatypeObject.__module__
            lName = p.datatypeObject['name']
            if lSynonyms.has_key(lName) is False:
                lSplitName = lName.split('(')
                lBaseName = lSplitName[0]
                if (len(lSplitName) == 2) and (lSynonyms.has_key(lBaseName) is False):
                    lDict = self.network.getTypeManager().getSynonymDict(lBaseName)
                    if lDict is not None:
                        lSynonyms[lBaseName] = lDict
                lDict = self.network.getTypeManager().getSynonymDict(lName)
                if lDict is not None:
                    lSynonyms[lName] = lDict

        kw['types'] = lTypes
        kw['synonyms'] = lSynonyms
        txt, indent = apply(self.getInitBlock, (className, indent), kw)
        kw.pop('types')
        kw.pop('synonyms')
        lines.extend(txt)

        if dependencies is True:
            nodeName = 'self'
            indent, txt = self.getNodeSourceCodeForNode(self.network,
                                        indent=indent, full=0, nodeName=nodeName)
            lines.extend(txt)

            lines.extend("\n\n" + indent0 + "    " + \
                         "def afterAddingToNetwork(self):\n" + \
                         indent + "pass\n")
            
            constrkw = {}
            constrkw.update( self.constrkw )
            constrkw['name'] = className
            dummyNode = apply( self.originalClass,(),constrkw)
            indent, txt = self.getNodeSourceCodeForPorts(self.network, indent=indent,
                                           ignoreOriginal=False, full=0,
                                           dummyNode=dummyNode, nodeName=nodeName)
            lines.extend(txt)

            indent, txt = self.getNodeSourceCodeForWidgets(self.network, indent=indent,
                                           ignoreOriginal=False, full=0,
                                           dummyNode=dummyNode, nodeName=nodeName)
            lines.extend(txt)
        elif dependencies is False:
            txt = self.getComputeFunctionSourceCode(indent=indent)
            lines.extend(txt)

            txt, indent = apply(self.getPortsCreationSourceCode,
                                (self.inputPorts, 'input', indent), kw)
            lines.extend(txt)
            txt, indent = apply(self.getPortsCreationSourceCode,
                                (self.outputPorts, 'output', indent), kw)
            lines.extend(txt)

            txt, indent = self.getWidgetsCreationSourceCode(indent)
            lines.extend(txt)
        else:
            assert(False)

        indent1 = indent + ' '*4

        lines.extend("\n\n" + indent0 + "    " + \
                     "def beforeAddingToNetwork(self, net):\n")

        # this make sure the host web service is loaded
        if self.constrkw.has_key('host'):

            lines.extend( indent + "try:\n" )

            ## get library import cache
            ## then write libray import code
            cache = self.network.buildLibraryImportCache(
                {'files':[]}, self.network, selectedOnly=False)
            li = self.network.getLibraryImportCode(
                     cache, indent1, editor="net.editor",
                     networkName="net",
                     importOnly=True, loadHost=True)
            lines.extend(li)
            lines.extend( indent + "except:\n" + \
                   indent1 + "print 'Warning! Could not load web services'\n\n")

        # this make sure the port widgets will be avalaible when saved code will run
        lines.extend(indent + "try:\n" )

        lWidgetsClass = []
        for p in self.inputPorts:
            lClass = p.widget.__class__
            lModule = lClass.__module__
            if ( lModule != 'NetworkEditor.widgets') \
                and (lModule != '__builtin__') \
                and (lModule not in lWidgetsClass):
                lWidgetsClass.append(lClass)

        lines.append(indent1 + "ed = net.getEditor()\n")
        for w in lWidgetsClass:
            lWidgetsClassName = w.__name__
            lines.append(indent1 + "from %s import %s\n" % (w.__module__, lWidgetsClassName) )
            lines.extend(indent1 + "if %s not in ed.widgetsTable.keys():\n" % lWidgetsClassName )
            lines.extend(indent1 + 4*' ' + \
                         "ed.widgetsTable['%s'] = %s\n" % (lWidgetsClassName, lWidgetsClassName) )

        lines.extend(indent + "except:\n" + \
               indent1 + "import traceback; traceback.print_exc()\n" + \
               indent1 + "print 'Warning! Could not import widgets'\n")

        lines.extend("\n")
        
        return lines

    ####################################################
    #### Helper Methods follow to generate save file ###
    ####################################################

    def getHeaderBlock(self, className, indent="", **kw):
        """Generate source code to import a node from a library or file."""

        lines = []
        
        dependencies = kw['dependencies']
        
        lNow = datetime.datetime.now().strftime("%A %d %B %Y %H:%M:%S")       
        lCopyright = \
"""########################################################################
#
#    Vision Node - Python source code - file generated by vision
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

"""%(lNow, "Header:", "Id:") # if directly in the txt, CVS fills these fields

        lines.append(lCopyright)

        return lines, indent


    def getInitBlock(self, className, indent="", **kw):
        """Generate source code to define the __init__() method of the node,
        building the correct constrkw dict, etc."""
        lines = []

        dependencies = kw['dependencies']

        lines.append(indent+"# import node's base class node\n")

#        if dependencies is True:
#            mod = self.originalClass.__module__
#            klass = self.originalClass.__name__
#            txt1 = "from %s import %s\n"%(mod,klass)
#            lines.append(indent+txt1)
#            txt2 = "class %s(%s):\n"%(className,klass)
#            lines.append(indent+txt2)
#        else:
#            txt1 = "from NetworkEditor.items import NetworkNode\n"
#            lines.append(indent+txt1)
#            txt2 = "class %s(NetworkNode):\n"%className
#            lines.append(indent+txt2)

        txt1 = "from NetworkEditor.items import NetworkNode\n"
        lines.append(indent+txt1)
        mod = self.originalClass.__module__
        klass = self.originalClass.__name__
        txt1 = "from %s import %s\n"%(mod,klass)
        lines.append(indent+txt1)
        txt2 = "class %s(%s):\n"%(className,klass)
        lines.append(indent+txt2)

        if self.originalClass.__doc__ is not None:
            lines.append(indent+'    \"\"\"'+self.originalClass.__doc__)
            lines.append('\"\"\"\n')

        indent1 = indent + 4*" "
        indent2 = indent1 + 4*" "
        if kw.has_key('types'):
            lines.append(indent1 + "mRequiredTypes = " + kw['types'].__str__() + '\n')

        if kw.has_key('synonyms'):
            lines.append(indent1 + "mRequiredSynonyms = [\n")
            for lkey, lSynonym in kw['synonyms'].items():
                lines.extend(indent2 + lSynonym.__str__() + ',\n')
            lines.append(indent1 + ']\n')

        # build constructor keyword from original class
        # constrkw is not used by the original class but only by NetworkNode
        constrkw = ''
        for name, value in self.constrkw.items():
            constrkw = constrkw + name+'='+str(value)+', '
        constrkw = constrkw + "constrkw = " + str(self.constrkw)+', '

        indent += 4*" "
        lines.append(indent+\
                  "def __init__(self, %s name='%s', **kw):\n" % (
            constrkw, className))
        indent += 4*" "
                      
        lines.append(indent+"kw['constrkw'] = constrkw\n")
        lines.append(indent+"kw['name'] = name\n")

        if dependencies is True:
            klass = self.originalClass.__name__
            lines.append(indent+"apply(%s.__init__, (self,), kw)\n"%klass)          
            
            # we just fully blank everything an recreate them
            # we will need to save only the differences and not everything
            #lines.append(indent+"self.inputPortsDescr = []\n")
            #lines.append(indent+"self.outputPortsDescr = []\n")
            #lines.append(indent+"self.widgetDescr = {}\n")

            if self._modified is True:
                lines.append(indent+"self.inNodeWidgetsVisibleByDefault = %s\n"%self.inNodeWidgetsVisibleByDefault)

        else:
            lines.append(indent+"apply( NetworkNode.__init__, (self,), kw)\n")
            if self.inNodeWidgetsVisibleByDefault:
                lines.append(indent+"self.inNodeWidgetsVisibleByDefault = True\n")

        return lines, indent


    def getPortsCreationSourceCode(self, ports, ptype='input', indent="",**kw):
        """generates code to create ports using the inputportsDescr and
        outputPortsDescr"""

        lines = []

        dependencies = kw['dependencies']

        assert ptype in ['input', 'output']
        for p in ports:
            d = p.getDescr()
            if d is None:
                d = {}
            lines.append(indent+"self.%sPortsDescr.append(\n"%ptype)
            lines.append(indent+ 4*" " + "%s)\n"%str(d) )
                
        return lines, indent


    def getWidgetsCreationSourceCode(self, indent="",**kw):
        """generating code to create widgets using the widgetDescr"""
        lines = []
        for p in self.inputPorts:
            if p.widget is None:
                continue
            d = p.widget.getDescr()
            # save current widget value
            d['initialValue'] = p.widget.getDataForSaving()
            if d is None:
                d = {}
            lines.append(indent+"self.widgetDescr['%s'] = {\n"%p.name)
            lines.append(indent+ 4*" " + "%s\n"%str(d)[1:] ) #ommit first {

        return lines, indent


    def getComputeFunctionSourceCode(self, indent="", **kw):
        lines = []
        nodeName = 'self'
        lines.append(indent+"code = \"\"\"%s\"\"\"\n"%self.sourceCode)
        lines.append(indent+"%s.configure(function=code)\n"% nodeName)
        return lines


###################### END of methods generating source code ################
#############################################################################


    def outputData(self, **kw):
        for p in self.outputPorts:
            if kw.has_key(p.name):
                data = kw[p.name]
                kw.pop(p.name)
                p.outputData(data)
            else:
                ed = self.getEditor()
                if ed.hasGUI:
                    ed.balloons.tagbind(
                        self.network.canvas, 
                        p.id, 
                        p.balloonBase)
        if len(kw):
            for k in kw.keys():
                warnings.warn( "WARNING: port %s not found in node %s"%(k, self.name) )


    def setFunction(self, source, tagModified=True):
        """Set the node's compute function. If tagModified is True, we set
        _modified=True"""

        self.sourceCode = source
        self.dynamicComputeFunction = self.evalString(source)
        if tagModified:
            self._setModified(True)

        # update the source code editor if available
        if self.objEditor is not None:
            if self.objEditor.funcEditorDialog is not None:
                self.objEditor.funcEditorDialog.settext(source)
                

    def scheduleChildren(self, portList=None):
        """run the children of this node in the same thread as the parent
        if portList is None all children are scheduled, else only
        children of the specified ports are scheduled
"""
        #print "NetworkNodeBase.scheduleChildren"
        net = self.network

        # get the list of nodes to run
        if portList is None:
            allNodes = net.getAllNodes(self.children)
            for n in self.children:
                n.forceExecution = 1
        else:
            children = []
            for p in portList:
                children.extend(map (lambda x: x.node, p.children) )
            for n in children:
                n.forceExecution = 1
            # since a node can be a child through multiple ports we have to
            # make the list of children unique
            allNodes = net.getAllNodes(uniq(children))

        if len(allNodes):
            #self.forceExecution = 1
            #print "SCHEDULE CHILDREN", allNodes
            net.runNodes(allNodes)


    def schedule_cb(self, event=None):
        self.forceExecution = 1
        self.schedule()

        
    def schedule(self):
        """start an execution thread for the subtree under that node
"""
        #print "NetworkNodeBase.schedule", self.network.runOnNewData
        net = self.network
        ed = net.getEditor()
        if ed.hasGUI:
            if hasattr(ed, 'buttonBar'):
                bl = ed.buttonBar.toolbarButtonDict
                if bl.has_key('softrun'):
                    bl['softrun'].disable()
                bl['run'].disable()
                #bl['runWithoutGui'].disable()
                #if ed.withThreads is True:
                bl['pause'].enable()
                bl['stop'].enable()
        net.run([self])


    def computeFunction(self):
        # make sure all required input ports present data
        # make sure data is valid and available
        # call self.dynamicComputeFunction
        # Return 'Go' after successful execution or 'Stop' otherwise

        for p in self.outputPorts:
            if p.dataView:
                p.clearDataView()

        if not self.dynamicComputeFunction:
            return 'Stop'
        lArgs = [self,]

        ed = self.getEditor()
        # for each input port of this node
        newData = 0
        for port in self.inputPorts:

            # this make sure the text entries are used even if the user hasn't pressed return
            if ed.hasGUI and port.widget is not None:
                w = port.widget.widget
                if   isinstance(w, Tkinter.Entry) \
                  or isinstance(w, Pmw.ComboBox):
                    before = port.widget.lastUsedValue    
                    after = port.widget.widget.get()
                    if before != after:
                        port.widget._newdata = True
                
            if port.hasNewData():
                newData = 1
            data = port.getData() # returns 'Stop' if bad or missing data
            if type(data) is types.StringType:
                if data.lower()=='stop':
                    # turn node outline to missing data color
                    if ed.hasGUI and ed.flashNodesWhenRun:
                        c = self.iconMaster
                        c.tk.call((c._w, 'itemconfigure', self.innerBox,
                                   '-outline', '#ff6b00', '-width', 4))
                    return 'Stop'
            if port.dataView:
                port.updateDataView()

            # update Data Browser GUI (only if window is not deiconified)
            if port.objectBrowser and \
               port.objectBrowser.root.state()=='normal':
                port.objectBrowser.root.after(
                    100, port.objectBrowser.refresh_cb )

            lArgs.append(data)

        stat = 'Stop'
        if newData \
          or self.forceExecution \
          or (self.network and self.network.forceExecution):
            #print "running %s with:"%self.name, args
            lCurrentDir = os.getcwd()
            if self.network:
                if self.network.filename is not None:
                    lNetworkDir = os.path.dirname(self.network.filename)
                elif hasattr(self.network, 'macroNode') \
                  and self.network.macroNode.network.filename is not None:
                    lNetworkDir = os.path.dirname(self.network.macroNode.network.filename)
                else:
                    import Vision
                    if hasattr(Vision, 'networkDefaultDirectory'):
                        lNetworkDir = Vision.networkDefaultDirectory
                    else:
                        lNetworkDir = '.'

                # MS WHY do we have to go there ? Oct 2010
                # removed it because this prevented networks from .psf file
                # wfrom working as the tmp dir was deleted
                #if os.path.exists(lNetworkDir):
                    os.chdir(lNetworkDir)
            try:
                stat = apply( self.dynamicComputeFunction, tuple(lArgs) )
            finally:
                os.chdir(lCurrentDir)
            if stat is None:
                stat = 'Go'
            for p in self.outputPorts:
                # update Data Viewer GUI
                if p.dataView:
                    p.updateDataView()
                # update Data Browser GUI (only if window is not deiconified)
                if p.objectBrowser and p.objectBrowser.root.state() =='normal':
                    p.objectBrowser.root.after(
                        100, p.objectBrowser.refresh_cb )
                    
            for p in self.inputPorts:
                p.releaseData()

        return stat
 

    def growRight(self, id, dx):
        """Expand (and shrink) the x-dimension of the node icon to (and from)
        the right."""
        # we get the coords
        coords = self.iconMaster.coords(id)
        # compute the middle point using the bounding box of this object
        bbox = self.iconMaster.bbox(id)
        xmid = (bbox[0] + bbox[2]) * 0.5
        # add dx for every x coord right of the middle point
        for i in range(0,len(coords),2):
            if coords[i]>xmid:
                coords[i]=coords[i]+dx
        apply( self.iconMaster.coords, (id,)+tuple(coords) )


    def growDown(self, id, dy):
        """Expand (and shrink) the y-dimension of the node icon to (and from)
        the top."""
         # we get the coords
        coords = self.iconMaster.coords(id)
        # compute the middle point using the bounding box of this object
        bbox = self.iconMaster.bbox(id)
        ymid = (bbox[1] + bbox[3]) * 0.5
        # add dy for every y coord below of the middle point
        for i in range(1,len(coords),2):
            if coords[i]>ymid:
                coords[i]=coords[i]+dy
        apply( self.iconMaster.coords, (id,)+tuple(coords) )

    
    def updateCode(self, port='ip', action=None, tagModified=True, **kw):
        """update signature of compute function in source code.
We re-write the first line with all port names as arguments.
**kw are not used but allow to match updateCode signature of output ports
"""
        code = self.sourceCode
        # handle input port
        if port == 'ip':
            if action=='add' or action=='remove' or action=='create':
                ## This was bas: 13 assumed that was no space between doit( and
                ## self.  If there is a space we lost the f at the end of self
                #signatureBegin = code.index('def doit(')+13
                signatureBegin = code.index('self')+4
                signatureEnd = code[signatureBegin:].index('):')
                signatureEnd = signatureBegin+signatureEnd
                newCode = code[:signatureBegin]
                if action=='create':
                    for p in self.inputPortsDescr:
                        newCode += ', ' + p['name']
                        #if p['required'] is True:
                        #    newCode += "='NA' "
                        #else:
                        #    newCode += '=None '
                else:
                    for p in self.inputPorts:
                        newCode += ', ' + p.name
                        #if p.required is True:
                        #    newCode += "='NA' "
                        #else:
                        #    newCode += '=None '
                newCode = newCode + code[signatureEnd:]
            elif action=='rename':
                newname = kw['newname']
                oldname = kw['oldname']
                newCode = code.replace(oldname, newname)

        # handle output port
        elif port == 'op':
            newname = kw['newname']
            if action==None:
                return
            if action=='add':
                # add comment on how to output data
                olds = "## to ouput data on port %s use\n"%newname
                olds += "## self.outputData(%s=data)\n"%newname
                code += olds
            elif action=='remove':
                oldname = kw['oldname']
                # remove comment on how to output data
                olds = "## to ouput data on port %s use\n"%oldname
                olds += "## self.outputData(%s=data)\n"%oldname
                code = code.replace(olds, '')
            elif action=='rename':
                oldname = kw['oldname']
                olds = "## to ouput data on port %s use\n"%oldname
                olds += "## self.outputData(%s=data)\n"%oldname
                news = "## to ouput data on port %s use\n"%newname
                news += "## self.outputData(%s=data)\n"%newname
                code = code.replace(olds, news)
            else:
                raise ValueError (
                    "action should be either 'add', 'remove', 'rename', got ",
                    action)
            newCode = code

        else:
            warnings.warn("Wrong port type specified!", stacklevel=2)
            return

        # finally, set the new code
        self.setFunction(newCode, tagModified=tagModified)


    def toggleNodeExpand_cb(self, event=None):
        widgetsInNode = self.getWidgetsForMaster('Node')
        if len(widgetsInNode)==0:
            widgetsInParamPanel = self.getWidgetsForMaster('ParamPanel')
            if len(widgetsInParamPanel):
                if self.paramPanel.master.winfo_ismapped() == 1:
                    self.paramPanel.hide()
                    self.paramPanelTk.set(0)
                else:
                    self.paramPanel.show()
                    self.paramPanelTk.set(1)
        else:
            if self.isExpanded():
                self.expandedIcon = False
                self.hideInNodeWidgets()
            
            else:
                self.expandedIcon = True
                self.showInNodeWidgets()
        self._setModified(True)
                

    def getWidthForPorts(self, maxi=None):
        # compute the width in the icon required for input and output ports
        # if maxw is not none, the maximum is return
        if maxi is None:
            maxi = maxwidth = 0
        # find last visible inputport
        if len(self.inputPorts):
            for p in self.inputPorts[::-1]: # going backwards
                if p.visible:
                    break
            maxwidth = p.relposx+2*p.halfPortWidth
        if len(self.outputPorts):
            for p in self.outputPorts[::-1]: # going backwards
                if p.visible:
                    break
            if p.relposx+2*p.halfPortWidth > maxwidth:
                maxwidth = p.relposx+2*p.halfPortWidth
        return max(maxi, int(round(maxwidth*self.scaleSum)))
                

    def getHeightForPorts(self, maxi=None):
        # compute the height in the icon required for input and output ports
        # if maxw is not none, the maximum is return
        maxheight = 0
        if maxi is None:
            maxi = 0
        # find last visible inputport
        if len(self.inputPorts):
            for p in self.inputPorts[::-1]: # going backwards
                if p.visible:
                    break
            maxheight = p.relposy+2*p.halfPortHeight
        if len(self.outputPorts):
            for p in self.outputPorts[::-1]: # going backwards
                if p.visible:
                    break
            if p.relposy+2*p.halfPortHeight > maxheight:
                maxheight = p.relposy+2*p.halfPortHeight
        return max(maxi, int(round(maxheight*self.scaleSum)))

    
    def getWidthForLabel(self, maxi=None):
        # compute the width in the icon required for the label
        # if maxis is not not, the maximum is return
        if maxi is None:
            maxi = 0
        bb = self.iconMaster.bbox(self.textId)
        return max(maxi, 10+(bb[2]-bb[0]) )  # label has 2*5 padding


    def getWidthForNodeWidgets(self,  maxi=None):
        # compute the width in the icon required for node widgets
        # if maxis is not not, the maximum is return
        if maxi is None:
            maxi = 0

        if self.isExpanded():
            return max(maxi, self.nodeWidgetMaster.winfo_reqwidth()+10)
        else:
            return maxi

    
    def autoResizeX(self):
        # we find how wide the innerBox has to be
        canvas = self.iconMaster
        neededWidth = self.getWidthForPorts()
        neededWidth = self.getWidthForLabel(neededWidth)
        neededWidth = self.getWidthForNodeWidgets(neededWidth)
        # get width of current innerbox
        bb = canvas.bbox(self.innerBox)
        w = bb[2]-bb[0]
        self.resizeIcon(dx=neededWidth-w)


    def autoResizeY(self):
        canvas = self.iconMaster
        bb = canvas.bbox(self.textId)
        labelH = 12+self.progBarH+(bb[3]-bb[1])  # label has 2*5 padding
        if self.isExpanded():
            widgetH = self.nodeWidgetMaster.winfo_reqheight()
            if len(self.getWidgetsForMaster('Node')):
                labelH += 6
        else:
            widgetH = 0
        bb = canvas.bbox(self.innerBox)
        curh = bb[3]-bb[1]

        self.resizeIcon(dy=labelH+widgetH-curh)


    def autoResize(self):
        self.autoResizeX()
        self.autoResizeY()
        if len(self.getWidgetsForMaster('node')):
            # resize gets the right size but always grows to the right
            # by hiding and showing the widgets in node we fix this
            self.toggleNodeExpand_cb()
            self.toggleNodeExpand_cb()


    def getSize(self):
        """returns size of this node as a tuple of (width, height) in pixels"""
        bbox = self.iconMaster.bbox(self.outerBox)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return (w, h)
        

    def hideInNodeWidgets(self, rescale=1):
        # hide widgets in node by destroying canvas object holding them
        # the NE widget is not destroyed
        canvas = self.iconMaster
        if rescale:
            self.autoResizeX()
            h = self.nodeWidgetMaster.winfo_reqheight()
            self.resizeIcon(dy=-h-6)
            #bb = canvas.bbox(self.nodeWidgetTkId)
            #self.resizeIcon(dy=bb[1]-bb[3])
        canvas.delete(self.nodeWidgetTkId)


    def showInNodeWidgets(self, rescale=1):
        canvas = self.iconMaster
        widgetFrame = self.nodeWidgetMaster
        
        oldbb = canvas.bbox(self.innerBox)# find current bbox
        #if len(self.nodeWidgetsID):
        #    bb = canvas.bbox(self.nodeWidgetsID[-1]) # find bbox of last widget
        #else:
        #    bb = canvas.bbox(self.textId) # find bbox of text
        bb = canvas.bbox(self.textId) # find bbox of text

        # pack the frame containg the widgets so we can measure it's size
        widgetFrame.pack()
        canvas.update_idletasks()
        h = widgetFrame.winfo_reqheight() # before asking for its size
        w = widgetFrame.winfo_reqwidth()

## FIXME the frame is created with a given size. Since it is on a canvas
## it does not resize when widgets are added or removed
##         newh =0 
##         for p in self.inputPorts:
##             if p.widget and p.widget.inNode:
##                 newh += p.widget.widgetFrame.winfo_reqheight()
##         h = newh-h
        
        tags = (self.iconTag, 'node')
        # compute center (x,y) of canvas window
        # add a window below text for widgets
        self.nodeWidgetTkId = widgetWin = canvas.create_window(
            bb[0]+(w/2), bb[3]+ self.progBarH +(h/2),
            tags=tags, window=widgetFrame )
        if self.selected:
            canvas.addtag_withtag('selected', widgetWin)

        if rescale:
            self.autoResizeX()
            self.resizeIcon(dy=h+6)


    def getWidgetsForMaster(self, masterName):
        """Return a dict of all widgets bound for a given master in a given
        node (self). Masters can be 'Node' or 'ParamPanel'.
        key is an instance of the port, value is an instance of the widget"""
        
        widgets = {}
        for k, v in self.widgetDescr.items():
            master = v.get('master', 'ParamPanel')
            if master.lower()==masterName.lower():
                # find corresponding widget to this port
                for port in self.inputPorts:
                    if port.name == k:
                        widget = port.widget
                        break
                widgets[port] = widget
        return widgets


    def buildIcons(self, canvas, posx, posy, small=False):
        """Build NODE icon with ports etc
"""
        NetworkItems.buildIcons(self, canvas)
        network = self.network

        self.paramPanelTk = Tkinter.IntVar()  # to toggle Param. Panel
        self.paramPanelTk.set(0)

        # build node's Icon
        ed = self.getEditor()
        if ed.hasGUI:
            self.buildNodeIcon(canvas, posx, posy, small=small)
    
        # instanciate output ports
        for p in self.outputPorts:
            p.buildIcons(resize=False)

        # instanciate input ports
        inNode = 0
        for p in self.inputPorts: # this loop first so all port have halfPortWidth
            p.buildIcons( resize=False )

        for p in self.inputPorts:
            p.createWidget()
            if p.widget is not None:
                inNode = max(inNode, p.widget.inNode)

        if ed.hasGUI:
            self.autoResizeX() # in case we added too many ports

            # at least one widget is in the node. We show it if visible by default
            if inNode:
                if self.inNodeWidgetsVisibleByDefault:
                    self.expandedIcon = True
                    self.showInNodeWidgets( rescale=1 )

        # instanciate special input ports
        for ip in self.specialInputPorts:
            ip.buildIcons(resize=False)
            if not self.specialPortsVisible:
                ip.deleteIcon()
                
        # instanciate special output ports
        for op in self.specialOutputPorts:
            op.buildIcons(resize=False)
            if not self.specialPortsVisible:
                op.deleteIcon()

        # this is needed because only now do we know the true relposx of ports
        # if we do not do this here, some port icons might be outside the node
        # but we do not want to autoResize() because that would rebuild widgets
        if ed.hasGUI:
            self.autoResizeX()

            # add command entries to node's pull down
            self.menu.add_command(label='Run', command=self.schedule_cb, underline=0)
            self.menu.add_checkbutton(label="Frozen",
                                      variable = self.frozenTk,
                                      command=self.toggleFrozen_cb,
                                      underline=0)
            #        self.menu.add_command(label='Freeze', command=self.toggleFreeze)
            self.menu.add_separator()
            self.menu.add_command(label='Edit', command=self.edit, underline=0)
            self.menu.add_command(label='Edit compute function',
                                  command=self.editComputeFunction_cb,
                                  underline=14)
            self.menu.add_command(label='Introspect',
                                  command=self.introspect,
                                  underline=0)

            self.menu.add_checkbutton(label="Parameter Panel",
                                      variable = self.paramPanelTk,
                                      command=self.toggleParamPanel_cb,
                                      underline=0)
            
            self.menu.add_separator()
            self.menu.add_command(label='Copy', command=self.copy_cb, underline=0)
            self.menu.add_command(label='Cut', command=self.cut_cb, underline=0)
            self.menu.add_command(label='Delete', command=self.delete_cb, underline=0)
            self.menu.add_command(label='Reset', command=self.replaceWith, underline=0)

            if self.__class__ is FunctionNode and hasattr(self.function, 'serviceName'):
                def buildhostCascadeMenu():
                    self.menu.cascadeMenu.delete(0, 'end')
                    for lKey in self.library.libraryDescr.keys():
                        if lKey.startswith('http://') and lKey != suppressMultipleQuotes(self.constrkw['host']):
                            cb = CallBackFunction( self.replaceWithHost, host=lKey)
                            self.menu.cascadeMenu.add_command(label=lKey, command=cb)
                self.menu.cascadeMenu = Tkinter.Menu(self.menu, tearoff=0, postcommand=buildhostCascadeMenu)
                self.menu.add_cascade(label='Replace with node from', menu=self.menu.cascadeMenu)

            if self.specialPortsVisible:
                self.menu.add_command(label='Hide special ports',
                                      command=self.hideSpecialPorts,
                                      underline=5)
            else:
                self.menu.add_command(label='Show special ports',
                                      command=self.showSpecialPorts,
                                      underline=5)
            

    def addSaveNodeMenuEntries(self):
        """add 'save source code' and 'add to library' entries to node menu'"""

        if self.readOnly:
            return
        
        try:
            self.menu.index('Save as customized node')
        except:
            self.menu.add_separator()
            funcDependent = CallBackFunction(self.saveSource_cb, True)
            funcIndependent = CallBackFunction(self.saveSource_cb, False)
            if hasattr(self, 'geoms') is False: 
                if issubclass(self.__class__, FunctionNode):
                    pass
                    # still in devellopment:
                    #self.menu.add_command(
                    #            label='Save as customized node inheriting',
                    #            command=funcDependent)
                else:
                    self.menu.add_command(
                                label='Save as customized node',
                                command=funcIndependent)

    ## PLEASE NOTE: This will be enabled in a future release of Vision
##             ed = self.network.getEditor()
##             if hasattr(ed, 'addNodeToLibrary'):
##                 fun = CallBackFunction( ed.addNodeToLibrary, self)
##                 self.menu.add_command(label='add to library', command=fun)


    def copy_cb(self, event=None):
        ed = self.network.getEditor()
        self.network.selectNodes([self])
        ed.copyNetwork_cb(event)


    def cut_cb(self, event=None):
        ed = self.network.getEditor()
        self.network.selectNodes([self])
        ed.cutNetwork_cb(event)


    def delete_cb(self, event=None):
        self.network.selectNodes([self])
        nodeList = self.network.selectedNodes[:]
        self.network.deleteNodes(nodeList)


    def edit(self, event=None):
        if self.objEditor:
            self.objEditor.top.master.lift()
            return
        self.objEditor = NodeEditor(self)


    def editComputeFunction_cb(self, event=None):
        if not self.objEditor:
            self.objEditor = NodeEditor(self)

        self.objEditor.editButton.invoke()
            
    
    def evalString(self, str):
        if not str: return
        try:
            function = eval("%s"%str)
        except:
            #try:
                obj = compile(str, '<string>', 'exec')
                if self.__module__ == '__main__':
                    d = globals()
                else:
                    # import the module from which this node comes
                    mn = self.__module__
                    m = __import__(mn)
                    # get the global dictionary of this module
                    ind = string.find(mn, '.')
                    if ind==-1: # not '.' was found
                        d = eval('m'+'.__dict__')
                    else:
                        d = eval('m'+mn[ind:]+'.__dict__')
                # use the module's dictionary as global scope
                exec(obj, d)
                # when a function has names arguments it seems that the
                # co_names is (None, 'functionName')
                if len(obj.co_names)==0:
                    function = None
                else:
                    function = eval(obj.co_names[-1], d)
            #except:
            #    raise ValueError
        return function


    def move(self, dx, dy, absolute=True, tagModified=True):
        """if absolute is set to False, the node moves about the increment
        dx,dy. If absolute is True, the node moves to the position dx,dy
        Connections are updated automatically."""

        if self.editor.hasGUI:
            self.network.moveSubGraph([self], dx, dy, absolute=absolute,
                                      tagModified=tagModified)


    def getSourceCode(self):
        # this method is implemented in subclasses
        # create the source code to rebuild this object
        # used for saving or copying
        pass


    def toggleParamPanel_cb(self, event=None):
        if self.paramPanel.master.winfo_ismapped() == 0:
            self.paramPanel.show()
        else:
            self.paramPanel.hide()


    def ensureRootNode(self):
        # count parent to decide whether or not second node is a root
        lInConnections = self.getInConnections()
        if len(lInConnections) == 0:
            self.isRootNode = 1
            if self not in self.network.rootNodes:
                self.network.rootNodes.append(self)
        else:
            for lConn in lInConnections:
                if lConn.blocking is True:
                    if self in self.network.rootNodes:
                        self.network.rootNodes.remove(self)
                    break;
            else: # we didn't break
                # all the connections are not blocking
                self.isRootNode = 1
                if self not in self.network.rootNodes:
                    self.network.rootNodes.append(self)



class NetworkNode(NetworkNodeBase):
    """This class implements a node that is represented using a Polygon
    """

    def __init__(self, name='NoName', sourceCode=None, originalClass=None,
                 constrkw=None, library=None, progbar=0, **kw):

        apply( NetworkNodeBase.__init__,
               (self, name, sourceCode, originalClass, constrkw, library,
                progbar), kw)
        
        self.highlightOptions = {'highlightbackground':'red'}
        self.unhighlightOptions = {'highlightbackground':'gray50'}
        self.selectOptions = {'fill':'yellow'}
        self.deselectOptions = {'fill':'gray85'}
        self.inNodeWidgetsVisibleByDefault = True

        self.inputPortByName = {}
        self.outputPortByName = {}


    def replaceWithHost(self, klass=None, library=None, host='http://krusty.ucsd.edu:8081/opal2'):
        """a function to replace a node with another node. the connections are recreated.
the connected ports must have the same name in the new node and in the original node.
"""
        #print "replaceWithHost", self, host

        constrkw = copy.deepcopy(self.constrkw)
        if library is None:
            library = self.library
        if library is not None:
            constrkw['library'] = library
        if klass is None:
            klass = self.__class__
        constrkw['klass'] = klass    

        if klass is FunctionNode \
          and hasattr(self.function, 'serviceName') \
          and host is not None:
            constrkw['host'] = suppressMultipleQuotes(host)
            serverName = host.split('http://')[-1]
            serverName = serverName.split('/')[0]
            serverName = serverName.split(':')[0]
            serverName = serverName.replace('.','_')
            
            # to replace exactly with the same one
            #constrkw['functionOrString'] = \
            #         self.function.serviceOriginalName.lower() + '_' + serverName
            
            # to pick any better version
            if self.library.libraryDescr.has_key(host):
                lversion = 0 # replace with the highest version available on the host
                #lversion = self.function.version # replace only if version is at least equal to current
                # to eval we need to bring the main scope into this local scope
                from mglutil.util.misc import importMainOrIPythonMain
                lMainDict = importMainOrIPythonMain()
                for modItemName in set(lMainDict).difference(dir()):
                    locals()[modItemName] = lMainDict[modItemName]
                del constrkw['functionOrString']
                for node in self.library.libraryDescr[host]['nodes']:
                    try:
                        lFunction = eval(node.kw['functionOrString'])
                        if lFunction.serviceName == self.function.serviceName \
                          and lFunction.version >= lversion:
                            constrkw['functionOrString'] = lFunction.serviceOriginalName + '_' + serverName
                    except:
                        pass
        if constrkw.has_key('functionOrString'):
            return apply(self.replaceWith, (), constrkw)
        else:
            return False


    def replaceWith(self, klass=None, **kw):
        """a function to replace a node with another node. the connections are recreated.
the connected ports must have the same name in the new node and in the original node.
"""
        if len(kw) == 0:
            kw = copy.deepcopy(self.constrkw)
        if kw.has_key('library') is False:
            kw['library'] = self.library
        if klass is None:
            klass = self.__class__

        try:
            lNewNode = apply(klass,(),kw)
            lNewNode.inNodeWidgetsVisibleByDefault = self.expandedIcon #by default we want the new node to be in the same state as the curren one
            self.network.addNode(lNewNode, posx=self.posx, posy=self.posy)
            if self.specialPortsVisible is True:
                self.showSpecialPorts()

            lFailure = False
            for port in self.inputPorts:
                if lFailure is False:
                    for connection in port.connections:
                        if lFailure is False:
                            try:
                                self.network.connectNodes(
                                    connection.port1.node, lNewNode,
                                    connection.port1.name, port.name,
                                    blocking=connection.blocking )
                            except:
                                lFailure = True

            for port in self.inputPorts:
                if port.widget is not None:
                    try:
                        lNewNode.inputPortByName[port.name].widget.set(port.widget.get())
                    except:
                        pass

            lDownstreamNodeInputPortSingleConnection = {}
            if lFailure is False:
                for port in self.outputPorts:
                    if lFailure is False:
                        # input ports downstream have to accept multiple connections otherwise they can't be connected
                        for connection in port.connections:
                            lDownstreamNodeInputPortSingleConnection[connection.port2.node] = \
                                                               (connection.port2.name,
                                                                connection.port2.singleConnection)
                            connection.port2.singleConnection = 'multiple'
                            try:
                                self.network.connectNodes(
                                    lNewNode, connection.port2.node,
                                    port.name, connection.port2.name,
                                    blocking=connection.blocking )
                            except:
                                lFailure = True
                # input ports downstream are set back to what they were
                for lNode, portNameSingleConnection in lDownstreamNodeInputPortSingleConnection.items():
                    lNode.inputPortByName[portNameSingleConnection[0]].singleConnection = portNameSingleConnection[1]

            if lFailure is False:
                self.network.deleteNodes([self])
                #print "replaced"
                return True
            else:
                self.network.deleteNodes([lNewNode])

        except Exception, e:
            print e
            #warnings.warn( str(e) )

        return False


    def createPorts(self):
        for kw in self.outputPortsDescr:
            kw['updateSignature'] = False # prevent recreating source code sig.
            op = self.addOutputPort(**kw)

        # create all inputPorts from description
        for kw in self.inputPortsDescr:
            kw['updateSignature'] = False # prevent recreating source code sig.
            ip = self.addInputPort(**kw)
            # create widgets
            ip.createWidget()


        # create all specialPorts
        self.addSpecialPorts()

    def isExpanded(self):
        """returns True if widgets inside the node as displayed"""
        return self.expandedIcon


    def editorVisible(self):
        """returns True if the node Editor is visible"""
        return self.objEditor is not None


    def getColor(self):
        if self.iconMaster is None: return
        return self.iconMaster.itemconfigure(self.innerBox)['fill'][-1]


    def setColor(self, color):
        ## FOR unknown reasons c.tk.call((c._w, 'itemcget', self.innerBox, '-fill') can return 'None' sometimes on SGI when using threads
        c = self.iconMaster
        if c is None:
            print 'Canvas is None'
            return 
        oldCol = c.tk.call((c._w, 'itemcget', self.innerBox, '-fill') )
        while oldCol=='None':
            print "//////////////////////////", oldCol,self.innerBox, c 
            oldCol = c.tk.call((c._w, 'itemcget', self.innerBox, '-fill') )
            print "\\\\\\\\\\\\\\\\\\\\\\",oldCol,self.innerBox, c 
        #oldCol = c.itemconfigure(self.innerBox)['fill'][-1]
        c.tk.call((c._w, 'itemconfigure', self.innerBox, '-fill', color))
        #c.itemconfigure(self.innerBox, fill=color)
        return oldCol

## OBSOLETE was used for nodes that were widgets
##
##      def highlight(self, event=None):
##          if self.iconMaster is None: return
##          apply( self.iconMaster.itemconfigure, (self.innerBox,),
##                 self.highlightOptions )


##      def unhighlight(self, event=None):
##          if self.iconMaster is None: return
##          apply( self.iconMaster.itemconfigure, (self.innerBox,),
##                 self.unhighlightOptions )


    def getFont(self):
        if self.iconMaster is None:
            return
        return self.iconMaster.itemconfigure(self.textId)['font'][-1]
        

    def setFont(self, font):
        # has to be a tuple like this: (ensureFontCase('helvetica'),'-12','bold')
        if self.iconMaster is None:
            return
        assert font is not None and len(font)
        font = tuple(font)
        self.iconMaster.itemconfig(self.textId, font=font)
        

    def select(self):
        NetworkItems.select(self)
        if self.iconMaster is None: return
        apply( self.iconMaster.itemconfigure, (self.innerBox,),
               self.selectOptions )
    

    def deselect(self):
        NetworkItems.deselect(self)
        if self.iconMaster is None: return
        apply( self.iconMaster.itemconfigure, (self.innerBox,),
               self.deselectOptions )


    def resizeIcon(self, dx=0, dy=0):
        if dx:
            self.growRight(self.innerBox, dx)
            self.growRight(self.outerBox, dx)
            self.growRight(self.lowerLine, dx)
            self.growRight(self.upperLine, dx)

            # move the special outputPort icons if visible
            if self.specialPortsVisible:
                for p in self.specialOutputPorts:
                    p.deleteIcon()
                    p.createIcon()

        if dy:
            self.growDown(self.innerBox, dy)
            self.growDown(self.outerBox, dy)
            self.growDown(self.lowerLine, dy)
            self.growDown(self.upperLine, dy)
            for p in self.outputPorts:
                p.relposy = p.relposy + dy
                p.deleteIcon()
                p.createIcon()
                for c in p.connections:
                    if c.id:
                        c.updatePosition()


    def addInputPort(self, name=None, balloon=None, _previousWidgetDescr=None,
                     required=True, datatype='None', width=None, height=None,
                     singleConnection=True, _modified=False,
                     beforeConnect=None, afterConnect=None,
                     beforeDisconnect=None, afterDisconnect=None,
                     updateSignature=True,
                     shape=None, color=None, cast=True
                     , originalDatatype=None, defaultValue=None
                     ):
        """Create input port and creates icon
NOTE: this method does not update the description"""

        number = len(self.inputPorts)
        if name is None:
            name = 'in'+str(number)

        # create unique name
        portNames = []
        for p in self.inputPorts:
            portNames.append(p.name)

        if name in portNames:
            i = number
            while (True):
                newname = name+str(i)
                if newname not in portNames:
                    break
                i = i+1
            name = newname

        # create port    
        ip = InputPort(name, self, datatype, required, balloon,
                       width, height, 
                       singleConnection, beforeConnect,
                       afterConnect, beforeDisconnect, afterDisconnect,
                       shape, color, cast=cast,
                       originalDatatype=originalDatatype,
                       defaultValue=defaultValue
                       )
        self.inputPorts.append(ip)
        if self.iconMaster:
            ip.buildIcons()

        if not self.getEditor().hasGUI:
            ip.createWidget() # create NGWidget

        # and add descr to node.inputPortsDescr if it does not exist
        pdescr = self.inputPortsDescr
        found = False
        for d in pdescr:
            if d['name'] == name:
                found = True
                break
        if not found:
            descr = {'name':name, 'datatype':datatype, 'required':required,
                     'balloon':balloon,
                     'singleConnection':singleConnection}
            self.inputPortsDescr.append(descr)

        if _previousWidgetDescr is not None:
            ip.previousWidgetDescr = _previousWidgetDescr

        # generate unique number, which is used for saving/restoring
        ip._id = self._inputPortsID
        self._inputPortsID += 1

        ip._setModified(True)
        ip._setOriginal(False)

        # change signature of compute function
        if updateSignature is True:
            self.updateCode(port='ip', action='add', tagModified=False)

        self.inputPortByName[name] = ip

        return ip


    def refreshInputPortData(self):
        d = {}
        for p in self.inputPorts:
            d[p.name] = p.getData()
        return d


    def addOutputPort(self, name=None, datatype='None', width=None,
                      height=None, balloon=None, _modified=False,
                      beforeConnect=None, afterConnect=None,
                      beforeDisconnect=None, afterDisconnect=None,
                      updateSignature=True, shape=None, color=None):
        
        """Create output port and creates icon
NOTE: this method does not update the description nor the function's signature"""

        number = len(self.outputPorts)
        if name is None:
            name = 'out'+str(number)

        # create unique name
        portNames = []
        for p in self.outputPorts:
            portNames.append(p.name)

        if name in portNames:
            i = number
            while (True):
                newname = name+str(i)
                if newname not in portNames:
                    break
            i = i+1
            name = newname

        # create port    
        op = OutputPort(name, self, datatype, balloon, width, height,
                        beforeConnect, afterConnect, beforeDisconnect,
                        afterDisconnect)
        
        self.outputPorts.append(op)
        if self.iconMaster:
            op.buildIcons()

        # and add descr to node.outputPortsDescr if it does not exist
        pdescr = self.outputPortsDescr
        found = False
        for d in pdescr:
            if d['name'] == name:
                found = True
                break
        if not found:
            descr = {'name':name, 'datatype':datatype, 'balloon':balloon}
            self.outputPortsDescr.append(descr)

        # generate unique number, which is used for saving/restoring
        op._id = self._outputPortsID
        self._outputPortsID += 1

        op._setModified(True)
        op._setOriginal(False)

        # add comment to code on how to output data on that port
        if updateSignature is True:
            self.updateCode(port='op', action='add', newname=op.name, tagModified=False)

        self.outputPortByName[name] = op
        
        return op


    def deletePort(self, p, resize=True, updateSignature=True):
        NetworkItems.deletePort(self, p, resize)
        # update code first, then delete
        if updateSignature and isinstance(p, InputPort):
            self.updateCode(port='ip', action='remove', tagModified=False)
            self.inputPortByName.pop(p.name)
        elif updateSignature and isinstance(p, OutputPort):
            self.updateCode(port='op', action='remove', newname='', oldname=p.name, tagModified=False)
            self.outputPortByName.pop(p.name)


    def deletePortByName(self, portName, resize=True, updateSignature=True):
        """delete a port by specifying a port name (port names are unique
within a given node)."""
        port = self.findPortByName()
        self.deletePort(port, resize=resize, updateSignature=updateSignature)
        
            

    def showSpecialPorts(self, tagModified=True, event=None):
        self.specialPortsVisible = True
        self._setModified(tagModified)
        for p in self.specialOutputPorts:
            p.createIcon()
        for p in self.specialInputPorts:
            p.createIcon()
        self.menu.entryconfigure('Show special ports',
                                 label='Hide special ports',
                                 command=self.hideSpecialPorts)


        
    def hideSpecialPorts(self, tagModified=True, event=None):
        self.specialPortsVisible = False
        self._setModified(tagModified)
        for p in self.specialOutputPorts:
            p.node.network.deleteConnections(p.connections, undo=1)
            p.deleteIcon()
            
        for p in self.specialInputPorts:
            p.node.network.deleteConnections(p.connections, undo=1)
            p.deleteIcon()
        self.menu.entryconfigure('Hide special ports',
                                 label='Show special ports',
                                 command=self.showSpecialPorts)
        
        

    def addSpecialPorts(self):
        """add special ports to special ports list. But do not build icons"""
        # port to receive an impulse that will trigger the execution of the
        # node
        ip = RunNodeInputPort(self)
        ip.network = self.network
        self.specialInputPorts.append( ip )

        # port that always output an impulse upon successful completion
        # of the node's function
        op = TriggerOutputPort(self)
        op.network = self.network
        self.specialOutputPorts.append( op )
        
        ed = self.getEditor()
        ip.vEditor = weakref.ref( ed )
        op.vEditor = weakref.ref( ed )


    def buildSmallIcon(self, canvas, posx, posy, font=None):
        """build node proxy icon (icons in library categories"""
        if font is None:
            font = self.ed.font['LibNodes']
        font = tuple(font)
    
        self.textId = canvas.create_text(
            posx, posy, text=self.name, justify=Tkinter.CENTER,
            anchor='w', tags='node', font=font)
            
        self.iconTag = 'node'+str(self.textId)
        bb = canvas.bbox(self.textId)       

        # adding the self.id as a unique tag for this node
        canvas.addtag_closest(self.iconTag, posx, posy, start=self.textId)

        bdx1 = 2 # x padding around label
        bdy1 = 0 # y padding around label
        bdx2 = bdx1+3 # label padding + relief width
        bdy2 = bdy1+3 # label padding + relief width
        self.innerBox = canvas.create_rectangle(
            bb[0]-bdx1, bb[1]-bdy1, bb[2]+bdx1, bb[3]+bdy1,
            tags=(self.iconTag,'node'), fill='gray85')
        # the innerBox is the canvas item used to designate this node
        self.id = self.innerBox

        # add a shadow below
        if self.library is not None:
            color1 = self.library.color
        else:
            color1 = 'gray95'

        # upper right triangle
        self.upperLine = canvas.create_polygon(
            bb[0]-bdx2, bb[1]-bdy2, bb[0]-bdx1, bb[1]-bdy1,
            bb[2]+bdx1, bb[3]+bdy1, bb[2]+bdx2, bb[3]+bdy2,
            bb[2]+bdx2, bb[1]-bdy2,
            width=4, tags=(self.iconTag,'node'), fill=color1 )
        
        # lower left triangle
        self.lowerLine = canvas.create_polygon(
            bb[0]-bdx2, bb[1]-bdy2, bb[0]-bdx1, bb[1]-bdy1,
            bb[2]+bdx1, bb[3]+bdy1, bb[2]+bdx2, bb[3]+bdy2,
            bb[0]-bdx2, bb[3]+bdy2,
            width=4, tags=(self.iconTag,'node'), fill='gray45' )

        self.outerBox = canvas.create_rectangle(
            bb[0]-bdx2, bb[1]-bdy2, bb[2]+bdx2, bb[3]+bdy2,
            width=1, tags=(self.iconTag,'node'))

        canvas.tag_raise(self.innerBox, self.outerBox)
        canvas.tag_raise(self.textId, self.innerBox)

        return bb


    def deleteSmallIcon(self, canvas, item):
        # Experimental! 
        node = item.dummyNode
        canvas.delete(node.textId)
        canvas.delete(node.innerBox)
        canvas.delete(node.outerBox)
        canvas.delete(node.iconTag)

 
    def buildNodeIcon(self, canvas, posx, posy, small=False):
        # build a frame that will hold all widgets in node
        if hasattr(self.iconMaster,'tk'):
            self.nodeWidgetMaster = Tkinter.Frame(
                self.iconMaster, borderwidth=3, relief='sunken' , bg='#c3d0a6')

        ed = self.getEditor()

        if small is True:
            font = tuple(ed.font['LibNodes'])
            lInner = 2
            lOuter = 4
        else:
            font = tuple(ed.font['Nodes'])
            lInner = 5
            lOuter = 8

        self.textId = canvas.create_text(
            posx, posy, text=self.name, justify=Tkinter.CENTER,
            anchor='w', tags='node', font=font)
        canvas.tag_bind(self.textId, "<Control-ButtonRelease-1>",
                        self.setLabel_cb)

        self.iconTag = 'node'+str(self.textId)

        # add self.iconTag tag to self.textId
        canvas.itemconfig(self.textId, tags=(self.iconTag,'node'))

        bb = canvas.bbox(self.textId)       

##          # NOTE: THIS LINE ADDS RANDOMLY WRONG TAGS TO NODES >>>> COPY/PASTE
##          # WON'T WORK CORRECTLY!!! WITHOUT THIS LINE, EVERYTHING SEEMS TO
##          # WORK FINE.
##          #adding the self.id as a unique tag for this node
##          canvas.addtag_closest(self.iconTag, posx, posy, start=self.textId)

        progBarH = self.progBarH

        # this method is also called by a network refresh, thus we need to
        # get the description of the node and color it accordingly (frozen
        # or colored by node library)
        color = "gray85"  # default color is gray
        if self.editor.colorNodeByLibraryTk.get() == 1:
            if self.library is not None:
                color = self.library.color # color by node library color
        # if node is frozen, this overwrites everything
        if self.frozen:
            color = '#b6d3f6' # color light blue

        self.innerBox = canvas.create_rectangle(
            bb[0]-lInner, bb[1]-lInner, bb[2]+lInner, bb[3]+lInner+progBarH,
            tags=(self.iconTag,'node'), fill=color)#, width=2 )

        # the innerBox is the canvas item used to designate this node
        self.id = self.innerBox
        
        # add a shadow below (color by Library)
        if self.library is not None:
            color1 = self.library.color
        else:
            color1 = 'gray95'

        self.outerBox = canvas.create_rectangle(
            bb[0]-lOuter, bb[1]-lOuter, bb[2]+lOuter, bb[3]+lOuter+progBarH,
            width=1, tags=(self.iconTag,'node'))

        # get a shortcut to the bounding boxes used later on
        ibb = canvas.bbox(self.innerBox) 
        obb = canvas.bbox(self.outerBox)

        # upper right polygon (this is used to color the node icons upper
        # and right side with the corresponding node library color)
        self.upperLine = canvas.create_polygon(
            # note: we have to compensate +1 and -1 because of '1'-based
            # coord system
            obb[0]+1, obb[1]+1, ibb[0]+1, ibb[1]+1,
            ibb[2]-1, ibb[3]-1, obb[2]-1, obb[3]-1, 
            obb[2]-1, obb[1]+1,
            width=4, tags=(self.iconTag,'node'), fill=color1 )

        # lower left polygon (this is used to 'shade' the node icons lower
        # and right side with a dark grey color to give it a 3-D impression
        self.lowerLine = canvas.create_polygon(
            # note: we have to compensate +1 and -1 because of '1'-based
            # coord system
            obb[0]+1, obb[1]+1, ibb[0]+1, ibb[1]+1,
            ibb[2]-1, ibb[3]-1, obb[2]-1, obb[3]-1,
            obb[0]+1, obb[3]-1,
            width=4, tags=(self.iconTag,'node'), fill='gray45' )

        canvas.tag_raise(self.outerBox)
        canvas.tag_raise(self.innerBox, self.outerBox)
        canvas.tag_raise(self.textId, self.innerBox)

        # add the progress bar
        if self.hasProgBar:
            pbid1 = canvas.create_rectangle(
                bb[0]-3, bb[3]-2, bb[2]+3, bb[3]+1+progBarH,
                tags=(self.iconTag,'node'), fill='green')
            self.pbid1 = pbid1

            pbid2 = canvas.create_rectangle(
                bb[2]+3, bb[3]-2, bb[2]+3, bb[3]+1+progBarH,
                {'tags':(self.iconTag,'node'), 'fill':'red'} )
            self.pbid2 = pbid2

        # and set posx, posy
        self.updatePosXPosY()

        if self.network is not None:
            self.move(posx, posy)
        self.hasMoved = False # reset this attribute because the current
                              # position is now the original position


    def setLabel_cb(self, event):
        self._tmproot = root = Tkinter.Toplevel()
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)
        self._tmpEntry = Tkinter.Entry(root)
        self._tmpEntry.pack()
        self._tmpEntry.bind("<Return>", self.setNewLabel_cb)


    def setNewLabel_cb(self, event):
        name = self._tmpEntry.get()
        self.rename(name)
        self._tmpEntry.destroy()
        self._tmproot.destroy()


    def setProgressBar(self, percent):
        """update node's progress bar. percent should be between 0.0 and 1.0"""
        if not self.hasProgBar:
            return
        canvas = self.iconMaster
        c = canvas.coords(self.pbid1)
        c[0] = c[0] + (c[2]-c[0])*percent
        canvas.coords(self.pbid2, c[0], c[1], c[2], c[3])
        

    def updatePosXPosY(self):
        """set node.posx and node.posy after node has been moved"""

        bbox = self.iconMaster.bbox(self.outerBox)
        self.posx = bbox[0]
        self.posy = bbox[1]


    def setModifiedTag(self):
        """THIS METHOD REMAINS FOR BACKWARDS COMPATIBILITY WITH OLD NETWORKS!
        Sets self._modified=True"""
        self._setModified(True)
        


class NetworkConnection(NetworkItems):
    """This class implements a connection between nodes, drawing
    lines between the centers of 2 ports.
    The mode can be set to 'straight' or 'angles' to have a straight line or
    lines using only right angles.
    smooth=1 option can be used for splines
    joinstyle = 'bevel', 'miter' and 'round'
    """
    arcNum = 0

    def __init__(self, port1, port2, mode='straight', name=None,
                 blocking=True, smooth=False, splitratio=None,
                 hidden=False, **kw):

        if name is None:
            name = port1.node.name+'('+port1.name+')'+'_'+port2.node.name+'('+port2.name+')'

        if splitratio is None:
            splitratio=[random.uniform(.2,.75), random.uniform(.2,.75)] # was [.5, .5]

        NetworkItems.__init__(self, name)
        self.blocking = blocking # when true a child node can not run before 
                                 # the parent node has run
        self.hidden = hidden
        self.id2 = None
        self.iconTag2 = None

        self.port1 = port1
        self.port2 = port2
        port1.children.append(port2)
        #assert self not in port1.connections
        port1.connections.append(self)
        port1.node.children.append(port2.node)
        port2.parents.append(port1)
        #assert self not in port2.connections
        port2.connections.append(self)
        port2.node.parents.append(port1.node)
        leditor = self.port1.editor
        self.mode = mode
        if leditor is not None and hasattr(leditor, 'splineConnections'):
            self.smooth = leditor.splineConnections
        else:
            self.smooth = smooth
        self.splitratio = copy.deepcopy(splitratio)

        w = self.connectionWidth = 3

        if port1.node.getEditor().hasGUI:
            col = port1.datatypeObject['color']
            if not kw.has_key('arrow'): kw['arrow']='last'
            if not kw.has_key('fill'): kw['fill']=col
            if not kw.has_key('width'): kw['width']=w
            if not kw.has_key('width'): kw['width']=w
            if not kw.has_key('activefill'): kw['activefill']='pink'
            kw['smooth'] = self.smooth

            self.lineOptions = kw
            
            self.highlightOptions = {'fill':'red', 'width':w, 'arrow':'last'}
            self.unhighlightOptions = {'width':w, 'arrow':'last'}
            self.unhighlightOptions['fill'] = col
        
            self.selectOptions = {
                'connection0': {'fill':'blue', 'width':w, 'arrow':'last'},
                'connection1': {'fill':'pink', 'width':w, 'arrow':'last'},
                'connection2': {'fill':'purple', 'width':w, 'arrow':'last'},
                }
            self.deselectOptions = {'width':w, 'arrow':'last'}
            self.deselectOptions['fill'] = col

            self.mouseAction['<Button-1>'] = self.reshapeConnection
            
            self.parentMenu = None

            self.isBlockingTk = Tkinter.IntVar()
            self.isBlockingTk.set(self.blocking)


    def reshapeConnection(self, event):
        # get a handle to the network of this node
        c = self.iconMaster
        # register an additional function to reshape connection
        num = event.num
        # FIXME looks like I am binding this many times !
        c.bind("<B%d-Motion>"%num, self.moveReshape,'+')
        c.bind("<ButtonRelease-%d>"%num, self.moveEndReshape, '+')

        
##     def moveReshape(self, event):
##         c = self.iconMaster
##         y = c.canvasy(event.y)
## 	dy = y - self.network.lasty
##         self.network.lasty = y
##         coords = c.coords(self.iconTag)
##         coords[3] = coords[3]+dy
##         coords[5] = coords[5]+dy
##         apply( c.coords, (self.iconTag,)+tuple(coords) )

##     def moveEndReshape(self, event):
##         c = self.iconMaster
##         num = event.num
##         c.unbind("<B%d-Motion>"%num)
##         c.bind("<ButtonRelease-%d>"%num, self.moveEndReshape, '+')

    
    # patch from Karl Gutwin 2003-03-27 16:05 
    def moveReshape(self, event):
        #print "moveReshape"
        c = self.iconMaster
        y = c.canvasy(event.y)
        x = c.canvasx(event.x)
        dy = y - self.network.lasty
        dx = x - self.network.lastx
        self.network.lasty = y
        self.network.lastx = x
        coords = c.coords(self.iconTag)

        if len(coords)==12:
            coords[4] = coords[4]+dx
            coords[6] = coords[6]+dx
            if y > ((coords[5]+coords[7])/2):
                coords[3] = coords[3]+dy
                coords[5] = coords[5]+dy
            else:
                coords[7] = coords[7]+dy
                coords[9] = coords[9]+dy
        else:
            coords[3] = coords[3]+dy
            coords[5] = coords[5]+dy

        self.calculateNewSplitratio(coords)

        apply( c.coords, (self.iconTag,)+tuple(coords) )


    def calculateNewSplitratio(self, coords):

        self.splitratio[0] = coords[0]-coords[4]
        lDistance = coords[0]-coords[-2]
        if lDistance != 0:
            self.splitratio[0] /= float(lDistance)
        if self.splitratio[0] > 2:
            self.splitratio[0] = 2
        elif self.splitratio[0] < -2:
            self.splitratio[0] = -2

        self.splitratio[1] = coords[1]-coords[5]
        lDistance = coords[1]-coords[-1]
        if lDistance != 0:
            self.splitratio[1] /= float(lDistance)
        if self.splitratio[1] > 2:
            self.splitratio[1] = 2
        elif self.splitratio[1] < -2:
            self.splitratio[1] = -2


    def moveEndReshape(self, event):
        c = self.iconMaster
        num = event.num
        c.unbind("<B%d-Motion>"%num)
        c.unbind("<ButtonRelease-%d>"%num)

        
    def getLineCoords(self):
        if isinstance(self.port1, SpecialOutputPort):
            return self.getLineCoordsLeftRightPorts()
        else:
            return self.getLineCoordsTopBottomPorts()

        
    def getLineCoordsLeftRightPorts(self):
        canvas = self.iconMaster
        c1 = self.port1.getCenterCoords()
        c2 = self.port2.getCenterCoords()
        if self.mode == 'straight':
            outOffy = c1[0]+15
            inOffy = c2[0]-15
            return [ c1[0], c1[1], c1[0], outOffy,
                     c2[0], inOffy, c2[0], c2[1] ]

        else: # if self.mode == 'angles':
            dx = c2[0]-c1[0]
            if dx > 30:     # draw just 1 segment down, 1 horizontal and 1 down again
                dx2 = dx * self.splitratio[0]
                outOffx = c1[0]+dx2
                inOffx = c2[0]-(dx-dx2)
                return [ c1[0], c1[1], outOffx, c1[1], inOffx, c2[1],
                         c2[0], c2[1] ]
            else:
                outOffx = c1[0]+15  # go right 15 pixels from output
                inOffx = c2[0]-15   # go left 15 pixel from input
                dy = c2[1]-c1[1]
                dy2 = dy * self.splitratio[1]
                mid = [ outOffx, c1[1]+dy2, inOffx, c2[1]-(dy-dy2) ]
                return [ c1[0], c1[1], outOffx, c1[1] ] + mid + \
                       [ inOffx, c2[1], c2[0], c2[1] ]
 


    def getLineCoordsTopBottomPorts(self):
        # implements straight and angle connections between nodes
        canvas = self.iconMaster
        c1 = self.port1.getCenterCoords()
        c2 = self.port2.getCenterCoords()
        if self.mode == 'straight':
            outOffy = c1[1]+15
            inOffy = c2[1]-15
            return [ c1[0], c1[1], c1[0], outOffy,
                     c2[0], inOffy, c2[0], c2[1] ]

        else: # if self.mode == 'angles':
            dy = c2[1]-c1[1]
            if dy > 30:     # draw just 1 segment down, 1 horizontal and 1 down again
                dy2 = dy * self.splitratio[1]
                outOffy = c1[1]+dy2
                return [ c1[0], c1[1], c1[0], outOffy, c2[0],
                         outOffy, c2[0], c2[1] ]
            else:
                outOffy = c1[1]+15  # go down 15 pixels from output
                inOffy = c2[1]-15   # go up 15 pixel from input
                dx = c2[0]-c1[0]
                dx2 = dx * self.splitratio[0]
                mid = [ c1[0]+dx2, outOffy, c2[0]-(dx-dx2), inOffy ]
                return [ c1[0], c1[1], c1[0], outOffy ] + mid + \
                       [ c2[0], inOffy, c2[0], c2[1] ]
        

    def updatePosition(self):
        if self.iconMaster is None:
            return
        
        # spoted by guillaume, I am not sure what it means
        if self.port1 is None or self.port2 is None:            
            import traceback
            traceback.print_stack()
            print 'IT HAPPENED AGAIN: a conection is missing ports'
            return 
                
        if self.port1.id is None or self.port2.id is None:
            return # one the ports is not visible
        c = self.iconMaster

        coords = self.getLineCoords()
        if self.hidden is False:
            apply( c.coords, (self.id,)+tuple(coords) )
        else:
            if isinstance(self.port1, SpecialOutputPort):
                lcoords1 = (coords[0],coords[1],coords[0]+20,coords[1])
                lcoords2 = (coords[-2]-16,coords[-1],coords[-2],coords[-1])
            else:
                lcoords1 = (coords[0],coords[1],coords[0],coords[1]+20)
                lcoords2 = (coords[-2],coords[-1]-16,coords[-2],coords[-1])
            apply( c.coords, (self.id,)+tuple(lcoords1) )
            apply( c.coords, (self.id2,)+tuple(lcoords2) )


    def highlight(self, event=None):
        if self.iconMaster is None: return
        c = self.iconMaster
        apply( c.itemconfigure, (self.iconTag,), self.highlightOptions )

        
    def unhighlight(self, event=None):
        if self.iconMaster is None: return
        c = self.iconMaster
        apply( c.itemconfigure, (self.iconTag,), self.unhighlightOptions)
        

    def setColor(self, color):
        if self.iconMaster is None: return
        c = self.iconMaster
        apply( c.itemconfigure, (self.iconTag,), {'fill':color} )
        self.unhighlightOptions['fill'] = color
        self.deselectOptions['fill'] = color

        
    def getColor(self):
        return self.deselectOptions['fill']


    def select(self):
        self.selected = 1
        if self.iconMaster is None: return
        sum = self.port1.node.selected + self.port2.node.selected
        if sum==2:
            self.iconMaster.addtag('selected', 'withtag', self.iconTag)
        apply( self.iconMaster.itemconfigure, (self.iconTag,),
               self.selectOptions['connection%d'%sum] )


    def deselect(self):
        NetworkItems.deselect(self)
        if self.iconMaster is None: return
        sum = self.port1.node.selected + self.port2.node.selected
        if sum<2:
            self.iconMaster.dtag(self.iconTag, 'selected')
        if sum==0:
            opt = self.deselectOptions
        else:
            opt = self.selectOptions['connection%d'%sum]
        apply( self.iconMaster.itemconfigure, (self.iconTag,), opt )


    def shadowColors(self, colorTk):
        # for a given Tkcolor return a dark tone 40% and light tone 80%
        c = self.iconMaster
        maxi = float(c.winfo_rgb('white')[0])
        rgb = c.winfo_rgb(colorTk)
        base = ( rgb[0]/maxi*255, rgb[1]/maxi*255, rgb[2]/maxi*255 )
        dark = "#%02x%02x%02x"%(base[0]*0.6,base[1]*0.6,base[2]*0.6)
        light = "#%02x%02x%02x"%(base[0]*0.8,base[1]*0.8,base[2]*0.8)
        return dark, light


    def toggleBlocking_cb(self, event=None):
        self.blocking = not self.blocking
        self.isBlockingTk.set(self.blocking)
        if not self.blocking:
            self.port2.node.ensureRootNode()


    def toggleVisibility_cb(self, event=None):
        self.setVisibility(not self.hidden)


    def setVisibility(self, hidden):
        self.hidden = hidden
        del self.network.connById[self.id]
        if self.id2 is not None:
            del self.network.connById[self.id2]
        self.deleteIcon()
        self.buildIcons(self.network.canvas)
        self.network.connById[self.id] = self
        if self.id2 is not None:
            self.network.connById[self.id2] = self


    def reparent_cb(self, type):
        node = self.port2.node
        self.network.deleteConnections([self])
        node.reparentGeomType(type, reparentCurrent=False)


    def buildIcons(self, canvas):
        """Build CONNECTION icon
"""
        NetworkItems.buildIcons(self, canvas)

        kw = self.lineOptions
        arcTag = '__arc'+str(self.arcNum)
        self.arcNum = self.arcNum + 1
        kw['tags'] = ('connection', arcTag)
        coords = self.getLineCoords()
        if self.hidden is False:
            g = apply( canvas.create_line, tuple(coords), kw )
        else:
            #print "coords", coords
            if isinstance(self.port1, SpecialOutputPort):
                lcoords1 = (coords[0],coords[1],coords[0]+20,coords[1])
                lcoords2 = (coords[-2]-16,coords[-1],coords[-2],coords[-1])
            else:
                lcoords1 = (coords[0],coords[1],coords[0],coords[1]+20)
                lcoords2 = (coords[-2],coords[-1]-16,coords[-2],coords[-1])
            g = apply( canvas.create_line, tuple(lcoords1), kw )
            g2 = apply( canvas.create_line, tuple(lcoords2), kw )
            self.iconTag2 = 'conn'+str(g2)
            self.id2 = g2

        self.iconTag = 'conn'+str(g)
        self.id = g

        cb = CallBackFunction(self.network.deleteConnections, ([self]))
        
        if self.port2.name == 'parent' and hasattr(self.port2.node,'selectedGeomIndex'): 
            # i.e. it's a geometrynode          
            cbSiblings = CallBackFunction(self.reparent_cb, ('siblings'))
            cbAll = CallBackFunction(self.reparent_cb, ('all'))
            self.menu.add_command(label='delete / reparent to root', command=cb)
            self.menu.add_command(label='reparent pointed siblings to root', command=cbSiblings)
            self.menu.add_command(label='reparent all pointed geoms to root', command=cbAll)
        else: 
            self.menu.add_command(label='delete', command=cb)

        if self.hidden is False:
            self.menu.add_command(label='hide', command=self.toggleVisibility_cb)
        else:
            self.menu.add_command(label='show', command=self.toggleVisibility_cb)
        self.menu.add_checkbutton(label='blocking',
                                  variable = self.isBlockingTk,
                                  command=self.toggleBlocking_cb)

        # adding the self.id as a unique tag for this node
        canvas.addtag_withtag(self.iconTag, arcTag )
        if self.hidden is True:
            canvas.addtag_withtag(self.iconTag2, arcTag )

        canvas.dtag( arcTag )
        canvas.lower(g, 'node')


    def getSourceCode(self, networkName, selectedOnly=0, indent="", ignoreOriginal=False, connName='conn'):
        # build and return connection creation source code

        from NetworkEditor.ports import TriggerOutputPort

        lines = []
        conn = self

        if conn._original is True and ignoreOriginal is False:
            return lines

        if selectedOnly and \
           conn.port1.node.selected+conn.port2.node.selected < 2:
            return lines

        node1 = conn.port1.node
        node2 = conn.port2.node

        n1Name = node1.getUniqueNodeName()
        n2Name = node2.getUniqueNodeName()

        lines = node1.checkIfNodeForSavingIsDefined(lines, networkName, indent)
        lines = node2.checkIfNodeForSavingIsDefined(lines, networkName, indent)

        lines.append(indent+'if %s is not None and %s is not None:\n'%(
            n1Name, n2Name))
        if isinstance(conn.port1, TriggerOutputPort):
            line1 = networkName+".specialConnectNodes(\n"
        else:
            line1 = '%s = '%connName +networkName+".connectNodes(\n"
##         line = line + "%s, %s, %d, %d)\n"%(n1Name, n2Name,
##                                           conn.port1.number, conn.port2.number)

        port1Name = conn.port1.name
        port2Name = conn.port2.name

        from macros import MacroInputNode, MacroOutputNode
        # treat connections to MacroInputNode separately
        if isinstance(conn.port1.node, MacroInputNode):
            if len(conn.port1.connections) > 1:
                i = 0
                for c in conn.port1.connections:
                    if c == conn:
                        break
                    else:
                        i = i + 1
                if i == 0:
                    port1Name = 'new'
            else:
                port1Name = 'new'

        # treat connections to MacroOutpuNode separately
        if isinstance(conn.port2.node, MacroOutputNode):
            if len(conn.port2.connections) > 1:
                i = 0
                for c in conn.port2.connections:
                    if c == conn:
                        break
                    else:
                        i = i + 1
                if i == 0:
                    port2Name = 'new'
            else:
                port2Name = 'new'

        line2 = '%s, %s, "%s", "%s", blocking=%s\n'%(
            n1Name, n2Name, port1Name, port2Name, conn.blocking)

        line3 = ''
        if conn.splitratio != [.5,.5]:
            line3 = ', splitratio=%s'%(conn.splitratio)
        if self.hidden is True:
            line3 += ', hidden=True'
        line3 += ')\n'

        lines.append(indent + ' '*4 + 'try:\n')
        lines.append(indent + ' '*8 + line1)
        lines.append(indent + ' '*12 + line2)
        lines.append(indent + ' '*12 + line3)
        lines.append(indent + ' '*4 + 'except:\n')
        lines.append(indent + ' '*8 + \
            'print "WARNING: failed to restore connection between %s and %s in network %s"\n'%(n1Name,n2Name,networkName))

        return lines


    def destroyIcon(self):
        self.deleteIcon()
        self.id = None

        self.id2 = None
        self.network.canvas.delete(self.iconTag2)
        self.iconTag2 = None



class FunctionNode(NetworkNode):
    """
    Base node for Vsiion nodes exposing a function or callable object
    
    The RunFunction node is an example of subclassing this node.
    Opal web services nodes are instance of this node exposing the
    opal web service python wrapper callable object

    This object support creating input ports for all parameters to the
    function. Positional (i.e. without default value) arguments always
    generate an input port visible on the node. For named arguments arguments
    a widget is created base on the type of the default value (e.g. entry for
    string, dial for int and float etc.)
    
    If the function or callable object has a .params attribute this attribute is
    expected to be a dictionary where the key is the name of the argument and the\
    value is dictionary providing additional info about this parameter.
    the folloing keys are recognized in this dictionary:
        {'default': 'False', # default value (not used as it is taken from the function signature)
         'type': 'boolean', 
         'description': 'string' #use to create tooltip
         'ioType': 'INPUT', # can be INPUT, INOUT, 
        }
        if type is FILE a a file browser will be generated
        if type is selection a values keywords should be present and provide a list
        of possible values that will be made available in a combobox widget
    """

    codeBeforeDisconnect = """def beforeDisconnect(self, c):
    # upon disconnecting we want to set the attribute function to None
    c.port2.node.function = None
    # remove all ports beyond the 'function' and 'importString' input ports
    for p in c.port2.node.inputPorts[2:]:
        c.port2.node.deletePort(p)
"""

    def passFunction():
        pass
    passFunc = passFunction


    def __init__(self, functionOrString=None, importString=None,
                 posArgsNames=[], namedArgs={}, **kw):

        if functionOrString is not None or kw.has_key('functionOrString') is False:
            kw['functionOrString'] = functionOrString
        elif kw.has_key('functionOrString') is True:
            functionOrString = kw['functionOrString']
        if importString is not None or kw.has_key('importString') is False:
            kw['importString'] = importString
        elif kw.has_key('importString') is True:
            importString = kw['importString']
        if len(posArgsNames)>0 or kw.has_key('posArgsNames') is False:
            kw['posArgsNames'] = posArgsNames
        elif kw.has_key('posArgsNames') is True:
            posArgsNames = kw['posArgsNames']
        if len(namedArgs)>0 or kw.has_key('namedArgs') is False:
            kw['namedArgs'] = namedArgs
        elif kw.has_key('namedArgs') is True:
            namedArgs = kw['namedArgs']

        if type(functionOrString) == types.StringType:
            # we add __main__ to the scope of the local function
            # the folowing code is similar to: "from __main__ import *"
            # but it doesn't raise any warning, and its probably more local
            # and self and in1 are still known in the scope of the eval function
            from mglutil.util.misc import importMainOrIPythonMain
            lMainDict = importMainOrIPythonMain()
            for modItemName in set(lMainDict).difference(dir()):
                locals()[modItemName] = lMainDict[modItemName]

            if importString is not None:
                try:
                    lImport = eval(importString)
                    if lImport == types.StringType:
                        importString = lImport
                except:
                    pass
                exec(importString)
            if kw.has_key('masternet') is True:
                masterNet = kw['masternet']
            lfunctionOrString = functionOrString
            while type(lfunctionOrString) == types.StringType:
                try:
                    function = eval(lfunctionOrString)
                except NameError:
                    function = None
                lfunctionOrString = function
        else:
            function = functionOrString

        if function is not None and kw.has_key('library'):
            # so we know where to find the current editor
            function._vpe = kw['library'].ed
            function._node = self # so we can find the vision node

        if hasattr(function, 'params') and type(function.params) == types.DictType:
            argsDescription = function.params
        else:
            argsDescription = {}

        if inspect.isclass(function) is True:
            try:
                function = function()
            except:
                function = None 

        if function is None:
            #def testFunction(a, b=1):
            #    print 'testFunction', a, b
            #    return a, b
            function = self.passFunc

        if hasattr(function, 'name'):
            name = function.name
        elif hasattr(function, '__name__'):
            name = function.__name__
        else:
            name = function.__class__.__name__

        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.function = function # function or command to be called
        
        self.posArgsNames = posArgsNames
        self.namedArgs = namedArgs # dict:  key: arg name, value: arg default

        self.outputPortsDescr.append(datatype='None', name='result')
        #for key, value in outputDescr:
        #    self.outputPortsDescr.append(datatype=value, name=key)

        # get arguments description
        from inspect import getargspec
        if hasattr(function, '__call__') and hasattr(function.__call__, 'im_func'): 
            args = getargspec(function.__call__.im_func)
        else:
            args = getargspec(function)

        if len(args[0])>0 and args[0][0] == 'self':
            args[0].pop(0) # get rid of self

        allNames = args[0]

        defaultValues = args[3]
        if defaultValues is None:
            defaultValues = []
        nbNamesArgs = len(defaultValues)
        if nbNamesArgs > 0:
            self.posArgsNames = args[0][:-nbNamesArgs]
        else:
            self.posArgsNames = args[0]
        d = {}
        for name, val in zip(args[0][-nbNamesArgs:], defaultValues):
            d[name] = val

        self.namedArgs = d

        # create widgets and ports for named arguments
        self.buildPortsForPositionalAndNamedArgs(self.posArgsNames,
                                                 self.namedArgs,
                                                 argsDescription=argsDescription)

        # create the constructor arguments such that when the node is restored
        # from file it will have all the info it needs
        if functionOrString is not None \
          and type(functionOrString) == types.StringType:
            self.constrkw['functionOrString'] = "\'"+suppressMultipleQuotes(functionOrString)+"\'"
            if importString is not None:
                self.constrkw['importString'] = "\'"+suppressMultipleQuotes(importString)+"\'"
        elif hasattr(function, 'name'):
            # case of a Pmv command
            self.constrkw['command'] = 'masterNet.editor.vf.%s'%function.name
        elif hasattr(function, '__name__'):
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = "\'"+function.__name__+"\'"
        else:
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = "\'"+function.__class__.__name__+"\'"
        if (importString is None or importString == '') \
          and self.constrkw.has_key('importString') is True:
            del self.constrkw['importString']
        if len(self.posArgsNames) > 0:
            self.constrkw['posArgsNames'] = self.posArgsNames
        elif self.constrkw.has_key('posArgsNames') is True:
            del self.constrkw['posArgsNames']
        if len(self.namedArgs) > 0:
            self.constrkw['namedArgs'] = self.namedArgs
        elif self.constrkw.has_key('namedArgs') is True:
            del self.constrkw['namedArgs']
        if kw.has_key('host') is True:
            self.constrkw['host'] = '\"'+suppressMultipleQuotes(kw['host'])+'\"'
        elif self.constrkw.has_key('host') is True:
            del self.constrkw['host']

        code = """def doit(self, *args):
    # get all positional arguments
    posargs = []
    for pn in self.posArgsNames:
        posargs.append(locals()[pn])
    # build named arguments
    kw = {}
    for arg in self.namedArgs.keys():
        kw[arg] = locals()[arg]
    # call function
    try:
        if hasattr(self.function,'__call__') and hasattr(self.function.__call__, 'im_func'):
            result = apply( self.function.__call__, posargs, kw )
        else:
            result = apply( self.function, posargs, kw )
    except Exception, e:
        from warnings import warn
        warn(str(e))
        result = None
    self.outputData(result=result)
"""
        if code: self.setFunction(code)
        # change signature of compute function
        self.updateCode(port='ip', action='create', tagModified=False)


    def buildPortsForPositionalAndNamedArgs(self, args, namedArgs, argsDescription={},
                                            createPortNow=False):

        lAllPortNames = args + namedArgs.keys()
        for name in lAllPortNames:
            if name in args:
                ipdescr = {'name':name, 'required':True}
                if argsDescription.get(name):
                    lHasDefaultValue = True
                    val = argsDescription[name]['default']
                else:
                    lHasDefaultValue = False
            else:
                ipdescr = {'name':name, 'required':False}
                lHasDefaultValue = True
                val = namedArgs[name]

            dtype = 'None'
            if lHasDefaultValue is True:
                if argsDescription.get(name) and argsDescription[name]['type']=='selection':
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEComboBox',
                        'initialValue':val,
                        'choices':argsDescription[name]['values'],
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif argsDescription.get(name) \
                  and argsDescription[name]['type']=='FILE' \
                  and (   argsDescription[name]['ioType']=='INPUT' \
                       or argsDescription[name]['ioType']=='INOUT'):
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEEntryWithFileBrowser',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) is types.BooleanType:
                    dtype = 'boolean'
                    self.widgetDescr[name] = {
                        'class': 'NECheckButton',
                        'initialValue':val==True,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) in [ types.IntType, types.LongType]:
                    dtype = 'int'
                    self.widgetDescr[name] = {
                        'class': 'NEDial', 'size':50,
                        'showLabel':1, 'oneTurn':1, 'type':'int',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) in [types.FloatType, types.FloatType]:
                    dtype = 'float'
                    self.widgetDescr[name] = {
                        'class': 'NEDial', 'size':50,
                        'showLabel':1, 'oneTurn':1, 'type':'float',
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
                elif type(val) is types.StringType:
                    dtype = 'string'
                    self.widgetDescr[name] = {
                        'class': 'NEEntry', 'width':10,
                        'initialValue':val,
                        'labelGridCfg':{'sticky':'w'},
                        'labelCfg':{'text':name},
                        }
    
                if argsDescription.get(name):
                    self.widgetDescr[name]['labelBalloon'] = argsDescription[name]['description']

                ipdescr.update({'datatype':dtype,
                        'balloon':'Defaults to '+str(val),
                        'singleConnection':True})

            self.inputPortsDescr.append( ipdescr )

            if createPortNow is True:
                # create port
                ip = apply( self.addInputPort, (), ipdescr )
                # create widget if necessary
                if dtype != 'None':
                    ip.createWidget(descr=self.widgetDescr[name])
