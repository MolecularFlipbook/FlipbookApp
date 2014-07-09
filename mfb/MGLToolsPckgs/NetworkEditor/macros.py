## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

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
# revision: Guillaume Vareille
#  
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/macros.py,v 1.110 2009/09/02 21:15:37 vareille Exp $
#
# $Id: macros.py,v 1.110 2009/09/02 21:15:37 vareille Exp $
#

import re, string
import Tkinter
import weakref
import types
import datetime

from NetworkEditor.net import Network
from NetworkEditor.items import NetworkNode, NetworkItems
from NetworkEditor.ports import InputPort, OutputPort

################################################################
# to avoid multiple list enclosure, input port macro node 
# must always be singleConnection.
# to have multiple connections, 
# the solution is to duplicate the input port in the macronode
# (there is no such need for the output port macronode)
################################################################


class MacroBase:

    def deletePort(self, p, resize=True, updateSignature=False):
        # call base class method
        # NOTE: we do this, because NetworkNode also subclasses this method
        #       and does some more stuff (like updating the node source code)
        NetworkItems.deletePort(self, p, resize)


    def updateCode(self, port='ip', action=None, tagModified=True, **kw):
        """we do not want to change the compute functions of the macro nodes
        upon adding/deleting ports"""
        pass


class MacroNode(MacroBase, NetworkNode):

    def __init__(self, name='NoName', sourceCode=None,
                 originalClass=None, constrkw={}, library=None, progbar=0,
                 **kw):
        apply( NetworkNode.__init__, (self, name, sourceCode, originalClass,
                                      constrkw, library, progbar), kw)
        self.expanded = 0
        self.isSchedulingNode = True # the outputPort node will schedule all
                             # children of the macro node
        self.hasRun = 0 # set to 1 when the node is executed. This is used to
                        # force the execution of root nodes in macro the first
                        # time the macro network is executed
        self.mouseAction['<Double-Button-1>'] = self.expand
        self.macroNetwork = MacroNetwork(self, self.name)

        # add special nodes for input and output
        self.macroNetwork.ipNode = MacroInputNode(self, 'input Ports')
        self.macroNetwork.opNode = MacroOutputNode(self, 'output Ports')

        code = """def doit(self, *args):

    # propagate forceExecution status
    if self.network.forceExecution:
        self.macroNetwork.forceExecution = self.network.forceExecution

    # copy args to output ports of the macroIpNode
    macroIp = self.macroNetwork.ipNode
    kw = {}
    i = 0
    newData = 0
    for p, data in map(None, self.inputPorts, args):
        if self.macroNetwork.forceExecution or self.inputPorts[i].hasNewValidData(): 
            macroIp.newData = 1
            kw[macroIp.outputPorts[p.number+1].name] = data
        i = i + 1

    if not macroIp.newData and not self.macroNetwork.forceExecution:
        return

    # output the data on the IPnode output ports
    apply( macroIp.outputData, (), kw )
    
    # run root nodes inside macroNetwork (if needed)
    # at the first execution of a macro node all root nodes have to run

    if not self.hasRun or self.macroNetwork.forceExecution:
        # list of roots with InputPortNode as last one
        # because InputPortNode schedules its children
        roots = self.macroNetwork.rootNodes[:]
        self.hasRun = 1
    else:
        roots = []
        for n in self.macroNetwork.rootNodes:
            if self.macroNetwork.forceExecution:
                n.forceExecution = 1
                roots.append(n)
            elif n.newData:
                roots.append(n)

    if len(roots):
        #print 'MacroNode doit', roots, self.hasRun, self.macroNetwork.forceExecution
        subRunNodes = self.macroNetwork.getSubRunNodes(roots = roots)
        # output the data on the IPnode output ports
        apply( macroIp.outputData, (), kw )
        self.macroNetwork.runNodes(subRunNodes)
"""
            
        self.setFunction(code)


    def isMacro(self):
        """Returns False if this node is not a MacroNode, returns True if MacroNode"""
        return True


    def schedule_cb(self, event=None):
        #print "MacroNode.schedule_cb"
        self.macroNetwork.forceExecution = 1
        NetworkNode.schedule_cb(self)


    def beforeRemovingFromNetwork(self):
        # if a macro node is deleted, we also have to delete its macro network
        ed = self.getEditor()
        ed.deleteNetwork(self.macroNetwork)


    def beforeAddingToNetwork(self, network):
        # here we do have a valid network
        self.macroNetwork.vEditor = weakref.ref(network.getEditor())
        self.macroNetwork.runOnNewData = network.runOnNewData

        
    def afterAddingToNetwork(self):
        ed = self.getEditor()
        ed.addNetwork(self.macroNetwork)
        self.macroNetwork.addNode(self.macroNetwork.ipNode, 200, 20)
        self.macroNetwork.addNode(self.macroNetwork.opNode, 200, 280)
        if ed.hasGUI:
            self.macroNetwork.buildIcons()
            # currently, we are now inside the macro network but the macro node
            # was not flagged "expanded=1" yet, so to get back in sync, we do:
            self.expand()

 
    def buildIcons(self, canvas, posx, posy):
        NetworkNode.buildIcons(self, canvas, posx, posy)
        myfont = list(self.getFont())
        if not 'bold' in myfont:
            myfont.append('bold')
        self.setFont(tuple(myfont))
        self.autoResizeX()
        try:
            self.menu.index('expand')
        except:
            self.menu.add_separator()
            self.menu.add_command(label='expand', command=self.expand)
            self.menu.add_command(label='shrink', command=self.shrink)
            self.addSaveNodeMenuEntries()
            

    def expand(self, event=None):
        ed = self.getEditor()
        if not self.expanded:
            ed.menuButtons['Networks'].menu.entryconfig(
                "Close...", state=Tkinter.DISABLED)
            ed.networkArea.showpage(self.macroNetwork.name)
            self.expanded = 1
        else:
            ed.networkArea.selectpage(self.macroNetwork.name)

        
    def shrink(self, event=None):
        ed = self.getEditor()
        if not self.expanded:
            return
        ed.menuButtons['Networks'].menu.entryconfig(
            "Close...", state=Tkinter.NORMAL)
        self.expanded = 0
        ed.networkArea.hidepage(self.macroNetwork.name)
        # make my own network the current one
        # Note: because we can have nested macros, we have to find the one
        # macro node that is currently expanded
        net = self.network
        while isinstance(net, MacroNetwork):
            if net.macroNode.expanded:
                ed.setNetwork(net)
                return
            else:
                net = net.macroNode.network
        # else: we have to set the network to what we got here, or we loose
        # the focus
        ed.setNetwork(net)


    def getRootMacro(self):
        """This method is used to find the root macro node for nested macros"""
        result = [self]
        parent = self

        while isinstance(parent.network, MacroNetwork):
            parent = parent.network.macroNode
            result.append(parent)
        return result[::-1]


    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        """This method builds the text-string to describe a macro node
in a saved file."""
        
        lines = []
        nodeName = self.getUniqueNodeName()

        ###############################################################
        # add lines to import node from macros.py, add macro to network
        ###############################################################

        if self.library:
            txt = NetworkNode.getNodeDefinitionSourceCode(
                self, networkName, indent)
            lines.extend(txt)
            
        else:
            if not self._original:
                txt1 = 'from NetworkEditor.macros import MacroNode\n'
                txt2 = "%s = MacroNode(name='%s')\n"%(nodeName, self.name)
                txt3 = "%s.addNode(%s, %d, %d)\n"%(
                    networkName, nodeName, self.posx, self.posy)

                lines.append(indent+txt1)
                lines.append(indent+txt2)
                lines.append(indent+txt3)
            
        ###############################################################
        # add lines to add all macro nodes first, recursively
        ###############################################################
        
        # We have to add all macro nodes first, and then start in the leaf
        # macros, add the nodes there, and work our way back up
        # (because of connections)
        for node in self.macroNetwork.nodes:
            if isinstance(node, MacroNode):
                txt1 = node.getNodeDefinitionSourceCode(
                    nodeName+".macroNetwork", indent)
                lines.extend(txt1)
        
        ###############################################################
        # check if an original node was deleted
        ###############################################################
        deletedNodes = 0 # count how many nodes have already been deleted
        # NOTE: because we add a line for each node we want to delete,
        # we have to decrement the orignumber by how many nodes we already
        # deleted
        for orignode, orignumber in self.macroNetwork._originalNodes:
            if orignode not in self.macroNetwork.nodes:
                # add handle to macro node
                lines = self.checkIfNodeForSavingIsDefined(
                    lines, networkName, indent)
                # add line to delete node
                txt = "%s.deleteNodes([%s])\n"%(
                    nodeName+".macroNetwork",
                    nodeName+".macroNetwork.nodes["+str(orignumber-deletedNodes)+"]")
                deletedNodes += 1
                lines.append(indent+txt)
 
        ###############################################################
        # check if an original connection was deleted
        ###############################################################
        for origconn, p1, n1, p2, n2 in self.macroNetwork._originalConnections:
            if origconn not in self.macroNetwork.connections:
                # only generate code if the nodes still exist (if not this
                # means, the node has been deleted which will delete the
                # connections so we do not have to add code,
                # and also if ports are not None. If ports were None means
                # that the user deleted the port which we catch below and
                # this also deletes the connection so we need not add code here
            
                invalid = False # this indicates a connection to a deleted
                                # node or port

                # port1 or port2 deleted?
                if type(p1) == types.NoneType or type(p2) == types.NoneType:
                    invalid = True

                # node1 deleted?
                if n1 not in self.macroNetwork.nodes:
                    invalid = True
                # node2 deleted?
                if n2 not in self.macroNetwork.nodes:
                    invalid = True
                    
                # only if both ports still exist do the following
                if not invalid:
                    lines = self.checkIfNodeForSavingIsDefined(
                        lines, networkName, indent)

                    node1 = nodeName+".macroNetwork.nodes[%d]"%(
                        self.macroNetwork.nodeIdToNumber(n1._id),)
                    node2 = nodeName+".macroNetwork.nodes[%d]"%(
                        self.macroNetwork.nodeIdToNumber(n2._id),)
                    txt = "%s.deleteConnection(%s, '%s', %s, '%s')\n"%(
                    nodeName+".macroNetwork", node1, p1.name, node2, p2.name)
                    lines.extend(indent+txt)
            
        ###############################################################
        # add lines to add/modify nodes in a macro network
        ###############################################################
        for node in self.macroNetwork.nodes:
            if not isinstance(node, MacroNode):
                txt2 = node.getNodeDefinitionSourceCode(
                    nodeName+".macroNetwork", indent)
                lines.extend(txt2)

        ###############################################################
        # add lines to create connections in macro networks
        ###############################################################
        macroNetworkName = "%s.macroNetwork"%nodeName
        if len(self.macroNetwork.connections):
            lines.append(
                '\n'+indent+"## saving connections for network "+\
                "%s ##\n"%self.name)
            lines.append(indent+'%s.freeze()\n'%macroNetworkName)
            for conn in self.macroNetwork.connections: 
                lines.extend(conn.getSourceCode(
                    macroNetworkName, False, indent))
            lines.append(indent+'%s.unfreeze()\n'%macroNetworkName)

        ###############################################################
        # add lines to configure dynamically created MacroOutputPorts
        # Note: right now we catch the port name 
        ###############################################################
        txt = self.macroNetwork.ipNode.getDynamicPortsModificationSourceCode(
            macroNetworkName, indent, ignoreOriginal)
        lines.extend(txt)

        ###############################################################
        # add lines to configure dynamically created MacroOutputPorts
        # Note: right now we catch the name and "singleConnection"
        # which might be modified by the user
        ###############################################################
        txt = self.macroNetwork.opNode.getDynamicPortsModificationSourceCode(
            macroNetworkName, indent, ignoreOriginal)
        lines.extend(txt)

        ###############################################################
        # Also, catch singleConnection events on the MacroNode input ports
        # if they were changed compared to the node that is connected to
        # the MacroInput node. We can do this only after we have formed
        # the connections inside the macro network
        ###############################################################
        # find node connected
        txt = []
        for ip in self.inputPorts:
            # add line to allow the renaming of the macronode's input ports
            txt.append(indent+\
                       "%s.inputPorts[%d].configure(name='%s')\n"%(
                       nodeName, ip.number, ip.name) )
            txt.append(indent+\
                       "%s.inputPorts[%d].configure(datatype='%s')\n"%(
                       nodeName, ip.number, ip.datatypeObject['name']) )
        txt.append(indent+"## configure MacroNode input ports\n")
        lines.extend(txt)

        # add line to allow the renaming of the macronode's output ports
        txt = []
        for op in self.outputPorts:
            txt.append(indent+\
                       "%s.outputPorts[%d].configure(name='%s')\n"%(
                       nodeName, op.number, op.name) )
            txt.append(indent+\
                       "%s.outputPorts[%d].configure(datatype='%s')\n"%(
                       nodeName, op.number, op.datatypeObject['name']) )
        txt.append(indent+"## configure MacroNode output ports\n")
        lines.extend(txt)
        
        ###############################################################
        # Shrink the macro node
        ###############################################################
        lines.append(indent+nodeName+".shrink()\n")

        ###############################################################
        # configure macro node: Freeze, etc
        ###############################################################
        ind, txt = self.getNodeSourceCodeForNode(networkName, indent,
                                                 ignoreOriginal)
        lines.extend(txt)

        return lines


    def getNodeSourceCodeForPorts(self, networkName, indent="", full=0):
        """We need to override the baseclass method since we do not want to
        save port modifications to a macro node"""

        lines = []
        return indent, lines


    def getAfterConnectionsSourceCode(self, networkName, indent="",
                                      ignoreOriginal=False):

        """This method allows users to add source code that needs to be
        generated after nodes were connected, which might trigger the
        creation of new ports."""
        
        lines = []
        
        for node in self.macroNetwork.nodes:
            lines.extend(node.getAfterConnectionsSourceCode(
                networkName, indent, ignoreOriginal) )
        
        return lines


    def resetTags(self):
        """This method subclasses NetworkNode.resetTags(). Used to reset
        the attributes _modified and _original in node, ports, widgets, conn"""
        NetworkNode.resetTags(self)
        for node in self.macroNetwork.nodes:
            node.resetTags()
        self.macroNetwork.ipNode._setOriginal(False)
        self.macroNetwork.opNode._setOriginal(False)
        

    def buildOriginalList(self):
        """Summary: used to catch delete node and delete connection events
        in the macro network.
        Puts nodes and connections into the macronetwork._originalNodes
        and macronetwork._originalConnections lists. This is used to find
        out if a node or connection in a macro network of a macro node that
        came from a node library was deleted."""

        macNet = self.macroNetwork
        macNet._originalNodes = []
        macNet._originalConnections = []

        # store instance of node and current number in net.nodes
        for node in macNet.nodes:
            macNet._originalNodes.append( (
                node, self.macroNetwork.nodeIdToNumber(node._id) ) )
            
        # store instance of original connection, port1, node1, port2, node2
        for conn in macNet.connections:
            macNet._originalConnections.append( (
                conn,
                conn.port1, conn.port1.node, conn.port2, conn.port2.node) )



    def getNodeSourceCode(self, className, 
                          networkName='self.masterNetwork', 
                          indent="", dependencies=True):
        """This method is called through the 'save source code' mechanism.

The idea here is to generate source code for a macro network that can
be put into a node library. This is not for saving networks

dependencies: True/False
    False: the saved macro node is fully independent from it's original macro (if any). 
    True : if relevant, the macro node is saved as a subclass of an original 
           macro, only modifications from the original are saved (not implemented yet) 

    in both case, saved macros depend as well of other embeded macros and of nodes from libraries. 
"""
        lines = []
        
        ## get header descr
        headerBlock = self.getHeaderBlock(className, indent)
        lines.extend(headerBlock)

        ## get __init__ descr, and proper indent
        initBlock = self.getInitBlock(className, indent)
        lines.extend(initBlock)

        ## get library import cache
        ## then write libray import code
        cache = {'files':[]}
        cache = self.network.buildLibraryImportCache(
            cache, self.macroNetwork, selectedOnly=False)

        ## get beforeAddingToNetwork descr
        beforeBlock = self.getBeforeBlock(cache, indent)
        lines.extend(beforeBlock)

        ## get afterAddingToNetwork descr
        afterBlock = self.getAfterBlock(cache, networkName, indent)
        lines.extend(afterBlock)

        
        return lines

    ####################################################
    #### Helper Methods follow to generate save file ###
    ####################################################

    def getHeaderBlock(self, className, indent=""):
        lines = []

        lNow = datetime.datetime.now().strftime("%A %d %B %Y %H:%M:%S") 
        
        lCopyright = """########################################################################
#
#    Vision Macro - Python source code - file generated by vision
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

        #lines.append(indent+"from NetworkEditor.macros import MacroNode\n")
        #lines.append(indent+"class "+className+"(MacroNode):\n")

        mod = self.originalClass.__module__
        klass = self.originalClass.__name__
        if klass != 'c':
            lines.append(indent+"from NetworkEditor.macros import MacroNode\n")
        if className == klass:
            txt2 = "class %s(MacroNode):\n"%(className)
            lines.append(indent+txt2)
        else:
            txt1 = "from %s import %s\n"%(mod,klass)
            lines.append(indent+txt1)
            txt2 = "class %s(%s):\n"%(className,klass)
            lines.append(indent+txt2)
                

        if self.originalClass.__doc__ is not None:
            lines.append(indent+'    \"\"\"'+self.originalClass.__doc__)
            lines.append('\"\"\"\n')
        return lines


    def getInitBlock(self, className, indent=""):
        nodeName = self.name
        klass = self.originalClass.__name__
        
        indent = indent + 4*" " # move forward 4
        lines = []
        lines.append("\n")
        lines.append(indent+"def __init__(self, constrkw={}, name='"+\
                     nodeName+"', **kw):\n")
        indent = indent + 4*" " # move forward 4
        lines.append(indent+"kw['name'] = name\n")

##         if self.library:
##             lines.append(indent+"apply(%s.__init__, (self,), kw)\n"%klass)
##         else:
        lines.append(indent+"apply( MacroNode.__init__, (self,), kw)\n")

        # add text for widgetDescr dict
        for p in self.inputPorts:
            w = p.widget
            if w is None:
                continue
            v = w.getConstructorOptions()
            v['class'] = w.__class__.__name__
            lines.append(indent+"""self.widgetDescr['%s'] = %s\n"""%(p.name,
                                                                     str(v)) )
        return lines
        

    def getBeforeBlock(self, cache, indent=""):
        lines = []
        klass = self.originalClass.__name__
        indent = indent + 4*" " # move forward 4

        lines.append("\n")
        lines.append(indent+"def beforeAddingToNetwork(self, net):\n")
        indent = indent + 4*" " # move forward 4
##         if self.library:
##             lines.append(indent+"%s.beforeAddingToNetwork(self, net)\n"%klass)
##         else:
        lines.append(indent+"MacroNode.beforeAddingToNetwork(self, net)\n")
        
        li = self.macroNetwork.getLibraryImportCode(
            cache, indent, editor="net.editor",
            networkName='net',
            importOnly=True, loadHost=True)
        lines.extend(li)

        return lines


    def getAfterBlock(self, cache, networkName, indent="",
                      ignoreOriginal=False):
        # used to save macro node
        # add text for the 'def afterAddingToNetwork' method
        aftBlock = []
        aftBlock.append('\n')
        indent = indent + 4*" " # move forward 4
        aftBlock.append(indent+"def afterAddingToNetwork(self):\n")
        indent = indent + 4 * " " # move forward 4

        aftBlock.append(indent+"masterNet = self.macroNetwork\n")

        ## call base class afterAddingToNetwork
##         if self.library:
##             klass = self.originalClass.__name__
##             mod = self.originalClass.__module__
##             aftBlock.append(indent+"from %s import %s\n"%(mod,klass) )
##             aftBlock.append(indent+"%s.afterAddingToNetwork(self)\n"%klass)
##         else:
        aftBlock.append(
            indent+"from NetworkEditor.macros import MacroNode\n")
        aftBlock.append(indent+"MacroNode.afterAddingToNetwork(self)\n")

        ## loading libraries (we need these to set node libraries)
        li = self.macroNetwork.getLibraryImportCode(
            cache, indent, editor="net.editor",networkName='net', importOnly=True)
        aftBlock.extend(li)

        #lib = self.library
        #self.library = None
        ## add nodes to macro network, connect
        nodeName = self.getUniqueNodeName()
        aftBlock.append(indent+"## building macro network ##\n")
        aftBlock.append(indent+"%s = self\n"%nodeName)
        ed = self.getEditor()

        data = self.macroNetwork.getNetworkCreationSourceCode(
            "self.macroNetwork", False, indent, ignoreOriginal=True, importOnly=True)

        aftBlock.extend(data)

        # add code for MacroInpuPorts port modifications (such as
        # name
        txt = self.macroNetwork.ipNode.getDynamicPortsModificationSourceCode(
            "self.macroNetwork", indent, ignoreOriginal=True)
        aftBlock.extend(txt)

        # add code for MacroOutpuPorts port modifications (such as
        # singleConnection
        txt = self.macroNetwork.opNode.getDynamicPortsModificationSourceCode(
            "self.macroNetwork", indent, ignoreOriginal=True)
        aftBlock.extend(txt)

        ###############################################################
        # to allow the macro in the lib to have the correct port names
        ###############################################################
        txt = []
        txt.append(indent+"## configure MacroNode input ports\n")
        for ip in self.inputPorts:
            # add line to allow the renaming of the macronode's input ports
            txt.append(indent+\
                       "%s.inputPorts[%d].configure(name='%s')\n"%(
                       nodeName, ip.number, ip.name) )
            txt.append(indent+\
                       "%s.inputPorts[%d].configure(datatype='%s')\n"%(
                       nodeName, ip.number, ip.datatypeObject['name']) )
        txt.append(indent+"## configure MacroNode output ports\n")
        for op in self.outputPorts:
            txt.append(indent+\
                       "%s.outputPorts[%d].configure(name='%s')\n"%(
                       nodeName, op.number, op.name) )
            txt.append(indent+\
                       "%s.outputPorts[%d].configure(datatype='%s')\n"%(
                       nodeName, op.number, op.datatypeObject['name']) )
        aftBlock.extend(txt)

        #needed for "save source code"
        aftBlock.append("\n")
        aftBlock.append(indent+"%s.shrink()\n"%nodeName)
        aftBlock.append("\n")

        # add line to reset all tags
        aftBlock.append(indent+"## reset modifications ##\n")
        aftBlock.append(indent+"%s.resetTags()\n"%nodeName)
        aftBlock.append(indent+"%s.buildOriginalList()\n"%nodeName)
        #self.library = lib

        return aftBlock



class MacroInputNode(MacroBase, NetworkNode):

    def __init__(self, macroNode=None, name='NoName', sourceCode=None,
                 originalClass=None, constrkw={}, library=None, progbar=0,
                 **kw):
        self.macroNode = macroNode # node representing the network
        apply( NetworkNode.__init__, (self, name, None, None), kw)

        self.isSchedulingNode = True # this node's function will schedule all
          # children of ports with new data

        self.outputPortsDescr.append({'name':'new',
                                      'balloon':'Add new input port'})

        self.readOnly = 1   # this node should never be edited
        #FIXME we should remove edit entry from node's menu
        # same for MacroInputNode

        code = """def doit(self, *args):
    # run all children of macroIpNode of ports that have new data
    # we add scheduled nodes to a dict so that a given node is not triggered
    # twice or more
    portsWithNewData = []
    for ip, op in map(None, self.macroNode.inputPorts, self.outputPorts[1:]):
        if self.network.forceExecution or ip.hasNewValidData():
            portsWithNewData.append(op)
    #print 'IN MacroInputNode, scheduling:', portsWithNewData
    self.scheduleChildren(portsWithNewData)\n"""

        self.setFunction(code)

        if self.macroNode is not None:
            self.mouseAction['<Double-Button-1>'] = self.macroNode.shrink


    def buildIcons(self, canvas, posx, posy):
        NetworkNode.buildIcons(self, canvas, posx, posy)
        myfont = list(self.getFont())
        if not 'bold' in myfont:
            myfont.append('bold')
        self.setFont(tuple(myfont))
        self.autoResizeX()
        try:
            self.menu.index('shrink')
        except:
            self.menu.add_command(label='shrink',command=self.macroNode.shrink)
        

    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        lines = []

        if not self._modified and ignoreOriginal is False:
            return lines

        #lines = self.checkIfNodeForSavingIsDefined(lines, networkName, indent)

        nodeName = self.getUniqueNodeName()

        # always add a handle to the InputPort node
        txt = "%s = %s.ipNode\n"%(nodeName, networkName)
        lines.append(indent+txt)

        dummy, txt1 = self.getNodeSourceCodeForNode(networkName, indent,
                                                    ignoreOriginal)
        lines.extend(txt1)
        # since position is usually handled by addNode, we have to add
        # a line here to set the correct position
        if self.posx != 200 and self.posy != 20:
            txt2 = "%s.move(%d, %d)\n"%(nodeName, self.posx, self.posy)
            lines.append(indent+txt2)

        return lines


    def getDynamicPortsModificationSourceCode(self, networkName, indent="",
                                              ignoreOriginal=False):

        """This method returns source code to configure newly generated output
ports. Currently, we only catch the renaming of the ports.
"""
        
        lines = []
        if self._original is True and ignoreOriginal is False:
            return lines

        nodeName = self.getUniqueNodeName()

        # catch port modification "singleConnection":
        txt = []
        # add line to allow the renaming of the macronode's output ports
        for op in self.outputPorts[1:]:
            txt = self.checkIfNodeForSavingIsDefined(
                    txt, networkName, indent)
            txt.append(indent+\
                       "%s.outputPorts[%d].configure(name='%s')\n"%(
                       nodeName, op.number, op.name) )

        if len(txt):
            lines.append("\n")
            lines.append(indent+"## modifying MacroInputNode dynamic ports\n")
            lines.extend(txt)
        
        return lines


    def checkIfNodeForSavingIsDefined(self, lines, networkName, indent):
        """This method fixes a problem with saving macros that come from a
node library. If only a widget value has changed, we do not have a handle
to the node. Thus, we need to create this additional line to get a handle"""
        
        ed = self.getEditor()
        nodeName = self.getUniqueNodeName()

        if ed._tmpListOfSavedNodes.has_key(nodeName) is False:
            txt = "%s = %s.ipNode\n"%(nodeName, networkName)
            lines.append(indent+txt)
            ed._tmpListOfSavedNodes[nodeName] = self
        return lines
 

class MacroOutputNode(MacroBase, NetworkNode):

    def __init__(self, macroNode=None, name='NoName', sourceCode=None,
                 originalClass=None, constrkw={}, library=None, progbar=0,
                 **kw):
        self.macroNode = macroNode # node representing the network
        apply( NetworkNode.__init__, (self, name, None, None), kw)

        self.inputPortsDescr.append({'name':'new', 'required':False,
                                     'balloon':'Add new output port'})

        self.readOnly = 1   # this node should never be edited
        #FIXME we should remove edit entry from node's menu
        # same for MacroInputNode
        
        code = """def doit(self, *args):
    # output data on macrOpNode
    forceExecution = self.network.forceExecution
    for op, ip in map(None, self.macroNode.outputPorts, self.inputPorts[1:]):
        # valid, new or not we put whatever data we have on the output ports of the macroNode
        if len(ip.connections)==1:
            op.outputData(ip.getData())
        else:
            op.outputData(self.flatten(ip.getData()))

        # reset network force execution flag after the macro network ran
        self.network.forceExecution = 0
        # force the parent network to execute. This is needed for instance when
        # there are 2 levels of macros with an iterate at the lowest level
        self.macroNode.network.forceExecution = forceExecution
    
    # if we are in the MacroNetwork: schedule the children of the MacroNode
    # to run
    ed = self.getEditor()
    if 1: #self.network==ed.currentNetwork or forceExecution: 
        portsWithNewData = []
        for op, ip in map(None, self.macroNode.outputPorts,
            self.inputPorts[1:]):
            if ip.hasNewValidData():
                portsWithNewData.append(op)
        #print 'ABC', forceExecution, portsWithNewData
        #print 'MacroOutputNode scheduling:', portsWithNewData
        self.macroNode.scheduleChildren(portsWithNewData)\n"""

        self.setFunction(code)

        if self.macroNode is not None:
            self.mouseAction['<Double-Button-1>'] = self.macroNode.shrink


    def flatten(self, data):
        """When input port has multiple parents we want to concatenate the
data provided by all parents as if it came from a single parent since the
output port of the macro will provide all this data on a single port.
"""
        if isinstance(data, list):
            flatdata = []
            for d in data:
                if isinstance(d, list):
                    flatdata.extend(d)
                else:
                    return data
            return flatdata
        else:
            return data
    
                
    def buildIcons(self, canvas, posx, posy):
        NetworkNode.buildIcons(self, canvas, posx, posy)
        myfont = list(self.getFont())
        if not 'bold' in myfont:
            myfont.append('bold')
        self.setFont(tuple(myfont))
        self.autoResizeX()
        try:
            self.menu.index('shrink')
        except:
            self.menu.add_command(label='shrink',command=self.macroNode.shrink)


    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        lines = []
        if not self._modified and ignoreOriginal is False:
            return lines
                
        nodeName = self.getUniqueNodeName()

        #lines = self.checkIfNodeForSavingIsDefined(lines, networkName, indent)
        # always define a handle to OutputPorts Node
        txt = "%s = %s.opNode\n"%(nodeName, networkName)
        lines.append(indent+txt)
        
        # save node modifications
        dummy, txt1 = self.getNodeSourceCodeForNode(networkName, indent,
                                                    ignoreOriginal)
        lines.extend(txt1)
        # since position is usually handled by addNode, we have to add
        # a line here to set the correct position
        if self.posx != 200 and self.posy != 280:
            txt2 = "%s.move(%d, %d)\n"%(nodeName, self.posx, self.posy)
            lines.append(indent+txt2)

        return lines


    def getDynamicPortsModificationSourceCode(self, networkName, indent="",
                                              ignoreOriginal=False):

        """This method returns source code to configure newly generated input
        ports. Currently, we only catch the event 'singleConnection'."""
        
        lines = []
        if self._original is True and ignoreOriginal is False:
            return lines

        nodeName = self.getUniqueNodeName()

        # catch port modification "singleConnection":
        txt = []
        for i in range(1, len(self.inputPorts)):
            p = self.inputPorts[i]
            txt = self.checkIfNodeForSavingIsDefined(
                    txt, networkName, indent)
            status = p.singleConnection
            if p.singleConnection == 'auto':
                status = "'auto'"
            else:
                status = p.singleConnection      
            txt.append(indent+\
                       "%s.inputPorts[%d].configure(singleConnection=%s)\n"%(nodeName,i,status))

        # add line to allow the renaming of the macronode's output ports
        for ip in self.inputPorts[1:]:
            txt.append(indent+\
                       "%s.inputPorts[%d].configure(name='%s')\n"%(
                       nodeName, ip.number, ip.name) )

        if len(txt):
            lines.append("\n")
            lines.append(indent+"## modifying MacroOutputNode dynamic ports\n")
            lines.extend(txt)
        
        return lines


    def checkIfNodeForSavingIsDefined(self, lines, networkName, indent):
        """This method fixes a problem with saving macros that come from a
node library. If only a widget value has changed, we do not have a handle
to the node. Thus, we need to create this additional line to get a handle"""
        
        ed = self.getEditor()
        nodeName = self.getUniqueNodeName()
        if ed._tmpListOfSavedNodes.has_key(nodeName) is False:
            txt = "%s = %s.opNode\n"%(nodeName, networkName)
            lines.append(indent+txt)
            ed._tmpListOfSavedNodes[nodeName] = self
        return lines

      
class MacroNetwork(Network):
    """class to hold all the information about a bunch of nodes and connections
"""
    def __init__(self, macroNode, name='Noname'):
        Network.__init__(self, name)
        self.macroNode = macroNode

        self._originalNodes = []       # list of nodes that belong to a node
                                       # library macro. The list is populated
                                       # upon adding the macro to a network
                                       # and is used for saving macro networks
        self._originalConnections = [] # list of connections that belong to a
                                       # node library macro.


    def setExec(self,status):
        """Loop recursively over nodes in nested macros and set MacroNetwork's
execStatus to 'stop'
"""
        self.execStatus = status
        for n in self.nodes:
            if isinstance(n, MacroNode):
                n.macroNetwork.setExec(status)


    def stop(self):
        """set execStatus to 'stop'.
The execution will stop after completion of the current node.
For a MacroNode, we need to find the master network and invokde its stop method
"""
        master = self.macroNode.network
        while isinstance(master, MacroNetwork):
            master = self.macroNode.network
        master.stop()
