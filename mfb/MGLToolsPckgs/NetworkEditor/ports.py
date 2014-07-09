## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Nov. 2001  Authors: Michel Sanner, Daniel Stoffler
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
# $Header: /opt/cvs/python/packages/share1.5/NetworkEditor/ports.py,v 1.201.2.1 2012/02/27 20:04:33 sanner Exp $
#
# $Id: ports.py,v 1.201.2.1 2012/02/27 20:04:33 sanner Exp $
#

"""
These  objects are created through the addInputPort and addOutputPort methods
of the NetworkNode2 object. They are not intended to be created by a user
or a programer
"""

import types
import numpy.oldnumeric as Numeric
import Tkinter, Pmw
import weakref, warnings

from UserList import UserList
from inspect import getargspec

from NetworkEditor.itemBase import NetworkItems
from NetworkEditor.widgets import PortWidget, widgetsTable
from NetworkEditor.datatypes import AnyType, AnyArrayType
from mglutil.gui.BasicWidgets.Tk.TreeWidget.objectBrowser import ObjectBrowser
from mglutil.util.callback import CallBackFunction


class NGWidget:
    """ dummy class for non graphical widget
"""
    def __init__(self):
        self.value = None
        self._newdata = False


    def set(self, value, run=True):
        self.value = value
        self._newdata = True


    def get(self):
        return(self.value)


    def configure(self, **kw):
        # no need to worry for these
        kw.pop('choices', None)
        kw.pop('min', None)
        kw.pop('max', None)
        if len(kw) != 0:
            print 'WARNING running without GUI: NGWidget.configure() not implemented', kw


    def setlist(self, *args, **kw):
        print 'WARNING running without GUI: NGWidget.setlist() not implemented'



class PortsDescr(list):
    """Class used to describe input and output ports as a list of dictionaries
"""
    def __init__(self, node):
        self.node = weakref.ref(node)

    def append(self, *args, **kw):
        if args is not None:
            if len(args)==1:
                if isinstance(args[0], dict):
                    kw = args[0]
                else:
                    raise ValueError('expected dictionary got ', args)
            elif len(args)>1:
                raise ValueError('bad argument for PortsDescr', args)
        
        assert kw.has_key('name')
        if not kw.has_key('datatype'):
            kw['datatype'] = 'None'

        if self.checkUniqueName(kw['name']):
            list.append(self, kw)
            

class InputPortsDescr(PortsDescr):

    def checkUniqueName(self, name):
        for p in self.node().inputPortsDescr:
            if p['name'] == name:
                msg = 'port name %s already used in inputPortsDescr of node %s'%(name, self.node().name)
                warnings.warn(msg)
                return False
        return True
    

class OutputPortsDescr(PortsDescr):

    def checkUniqueName(self, name):
        for p in self.node().outputPortsDescr:
            if p['name'] == name:
                msg = 'port name %s already used in outputPortsDescr of node %s'%(name, self.node().name)
                warnings.warn(msg)
                return False
        return True



class Port(NetworkItems):
    """base class for input/output ports of network nodes"""

    def __init__(self, name, node, datatype='None',
                 balloon=None, width=None, height=None,
                 beforeConnect=None, afterConnect=None, beforeDisconnect=None,
                 afterDisconnect=None, hasHiddenConnections=False,
                 shape=None, color=None, originalDatatype=None
                 ):
        #print "Port.__init__", name, datatype, originalDatatype
        NetworkItems.__init__(self, name=name)

        self.node = node
        self.network = node.network
        self.objEditor = None                           # port editor widget
        self.connections = []
        self.datatypeObject = None

        if originalDatatype is not None:
            self.originalDatatype = originalDatatype # some ports mutate their datatype
        else:
            self.originalDatatype = datatype # some ports mutate their datatype
                    # upon connection. This used to restore the original type
        self.balloon = balloon
        self.balloonBase = None   # holds the data independent part of tooltip
        self.widget = None

        self.id = None            # canvas id for this port
        self.iconTag = None       # canvas id for all primitives of this port

        self._id = None           # a unique number, used for saving/restoring
                                  # this number is set in addInput/OutputPort()
        
        self.hasHiddenConnections = hasHiddenConnections
        self.menu = None
        self.data = 'no data yet'
        self.dataView = None
        self.relposx = 0          # center (not left or right corner) of port
        self.relposy = 0          # icon
        self.width = width
        self.height = height
        self.shape = shape
        self.color = color
        self.visible = True       # set to false if widget is bound

        # various callback placeholders
        self.callbacks = {'beforeConnect':(None,None),
                          'afterConnect':(None,None),
                          'beforeDisconnect':(None,None),
                          'afterDisconnect':(None,None)}

        # set callbacks: pass code and attribute
        self.setCallback(beforeConnect, 'beforeConnect')
        self.setCallback(afterConnect, 'afterConnect')
        self.setCallback(beforeDisconnect, 'beforeDisconnect')
        self.setCallback(afterDisconnect, 'afterDisconnect')

        self.vEditor = None
        if node.getEditor():
            self.vEditor = weakref.ref( node.getEditor() )  # VPE editor
        self.setDataType(datatype)


    def setCallback(self, code, key):
        """set callbacks for connect & disconnect evens. The dictionary
        self.callbacks holds the various callback methods
        key: name of the callback (such as 'beforeConnect')
        code: source code of the callback"""
        self.callbacks[key] = ( self.node.evalString(code), code )


    def editorVisible(self):
        """returns True if the port's Editor is visible"""
        return self.objEditor is not None


    def getDatatypeObjectFromDatatype(self, datatype):
        ed = self.getEditor()
        tm = ed.typeManager

        if type(datatype) is types.StringType:
            return tm.getType(datatype)
        elif isinstance(datatype, AnyType) or \
                 isinstance(datatype, AnyArrayType):
            return datatype
        elif hasattr(datatype,'__class__'):
            return tm.getTypeFromClass(datatype.__class__)
        
        return tm.getTypeFromClass(None)


    def setDataType(self, datatype, tagModified=True, makeOriginal=False):
        """set the port's data type. Update Port's icon if visible
"""
        #print "setDataType"
        ed = self.getEditor()

        lDatatypeObject = self.getDatatypeObjectFromDatatype(datatype)    
        self.datatypeObject = lDatatypeObject

        if ed.hasGUI:
            if self.iconTag is not None: # port is visible
                self.halfPortWidth = self.datatypeObject['width'] / 2
                self.halfPortHeight = self.datatypeObject['height'] / 2
                self.deleteIcon()
                self.createIcon()

        if tagModified:
            self._setModified(True)

        if makeOriginal:
            self.originalDatatype = datatype
                
            
    def __repr__(self):
        if hasattr(self, 'node'):
            return "<%s: port %d called %s in node %s>"%(
                self.__class__, self.number, self.name, self.node.name)
        elif hasattr(self, 'number'):
            return "<%s: port %d called %s>"%(
                self.__class__, self.number, self.name)
        else:
            return "<%s: port called %s>"%(
                self.__class__, self.name)


    def getColor(self):
        return self.node.iconMaster.itemconfigure(self.id)['fill'][-1]


    def setColor(self, color):
        if self.iconTag:
            oldCol = self.node.iconMaster.itemconfigure(self.id)['fill'][-1]
            self.node.iconMaster.itemconfigure(self.id)['fill'] = color
            return oldCol


    def getCenterCoords(self):
        bb = self.node.iconMaster.bbox(self.id)
        return (bb[0]+bb[2])/2, (bb[1]+bb[3])/2


    def buildIcons(self, resize=True):
        # set port width/height. This is usually specified in datatypeObject,
        # but can also be passed when instanciating a port
        if self.width is None:
            self.width = self.datatypeObject['width']
        if self.height is None:
            self.height = self.datatypeObject['height']
        self.halfPortWidth = self.width/2     
        self.halfPortHeight = self.height/2
        if self.shape is not None:
            self.datatypeObject['shape'] = self.shape
        if self.color is not None:
            self.datatypeObject['color'] = self.color

        if self.iconTag is not None:
            return

        # build port dropdown menu
        ed = self.getEditor()

        # got rid of useless tearoff
        self.menu = Tkinter.Menu(ed, title=self.name, tearoff=False)
        self.menu.add_separator()

        self.menu.add_command(label='Show Data', command=self.showData)
        self.menu.add_command(label='Introspect Data',
                              command=self.browseData)
        self.menu.add_command(label='Edit',
                              command=self.edit)#Port_cb)
        
        if isinstance(self, InputPort):
            lCast = self._cast
            # constructor create a boolean value which gets overwritten
            # by a Tkinter.BooleanVar here. When we come from refreshNet_cb
            # it is already a Tkinter.BooleanVar
            if isinstance(lCast, Tkinter.BooleanVar):
                lCast = lCast.get()
            self._cast = Tkinter.BooleanVar()
            self._cast.set(lCast)
            lFuncCall = CallBackFunction(self._setModified, True)
            self.menu.add_checkbutton(label='Cast Data', 
                                      variable=self._cast,
                                      onvalue=True,
                                      offvalue=False,
                                      command=lFuncCall)
        
            #this way we do not create a dependancy with DejaVu
            if self.name == 'parent' and hasattr(self.node,'selectedGeomIndex'):
                
                self.menu.add_separator()
    
                self.cascadeMenu = Tkinter.Menu(self.menu, tearoff=0)
                            
                self.menu.add_cascade(label='Parenting applies to',
                                      menu=self.cascadeMenu)
                            
                self.cascadeMenuVariable = Tkinter.StringVar()
                self.cascadeMenuVariable.set('current')
                
                self.cascadeMenu.add_radiobutton(
                                         label='None',
                                         variable=self.cascadeMenuVariable,
                                         command=lFuncCall,
                                         value='none', 
                                         underline=0)                                                       
                self.cascadeMenu.add_radiobutton(
                                         label='Current geom',
                                         variable=self.cascadeMenuVariable,
                                         command=lFuncCall,
                                         value='current', 
                                         underline=0)                                                       
                self.cascadeMenu.add_radiobutton(
                                         label='Sibling geoms', 
                                         variable=self.cascadeMenuVariable,
                                         command=lFuncCall,
                                         value='siblings', 
                                         underline=0)    
                self.cascadeMenu.add_radiobutton(
                                         label='All geoms', 
                                         variable=self.cascadeMenuVariable,
                                         command=lFuncCall,
                                         value='all', 
                                         underline=0)     

                self.retainPosition = Tkinter.BooleanVar()
                self.retainPosition.set(False)
                self.menu.add_checkbutton(label='retain position while parenting', 
                                          variable=self.retainPosition,
                                          onvalue=True,
                                          offvalue=False,
                                          command=lFuncCall)
            
            # even when correctly set, it may happens that the menu doesn't
            # show the radio button correctly set at starting .
            # the following line may help
            #self.node.network.canvas.update_idletasks()
                    
        visible = True
        if isinstance(self, InputPort):
            if self.widget is not None:
                visible = False

        elif isinstance(self, SpecialInputPort) or \
             isinstance(self, SpecialOutputPort):
            if not self.node.specialPortsVisible:
                visible = False
                
        self.visible = visible
        if visible: # build port icon
            self.createIcon()

        if resize:
            self.node.autoResizeX()
            

    def showData(self):
        if self.dataView is None:
            self.openDataViewer()
        else:
            self.dataView.lift()


    def openDataViewer(self):
        if isinstance(self, InputPort): type = 'input'
        else: type = 'output'
        self.dataView = Pmw.TextDialog(
            None, scrolledtext_labelpos = 'n',
            title = 'node %s, port %s'%(self.node.name, self.name),
            defaultbutton=0, command=self.dismiss,
            label_text = 'Data %s of Port %d'%(type,self.number) )
        
        self.updateDataView()
        self.dataView.pack()

        
    def dismiss(self, event=None):
        self.dataView.destroy()
        self.dataView = None


    def clearDataView(self):
        if not self.dataView:
            return
        self.dataView.settext('')


    def getDataStr(self, maxLen = None):
        # return a string that would be used in output port's show data

        #if type(self.data)==types.InstanceType:
        from mglutil.util.misc import isInstance
        if isInstance(self.data) is True:
            header = 'data:%s'%self.data.__class__
        else:
            header = 'data:%s'%type(self.data)

        length = 0
        if isinstance(self.data, Numeric.ArrayType):
            header += ', shape:' + str(self.data.shape)
            if len(self.data.shape) == 0:  
                length = 0
            else:
                length = reduce( lambda x,y: x*y, self.data.shape)
        elif hasattr(self.data, '__len__'):
            header += ', length:' + str(len(self.data))
            if type(self.data) == 'str':
                length = len(self.data)
            else:
                length = len(str(self.data))
        header += '\n'
        
        if length > 1000:
            return header + '-'*80 + '\n'+ "Too much data to print"
        
        datastr = repr(self.data)
        if maxLen:
            if len(datastr) < maxLen:
                return header + '-'*80 + '\n'+ datastr
            else:
                return header + '-'*80 + '\n'+ datastr[:maxLen] + '...'
        else:
            return header + '-'*80 + '\n'+ datastr


    def updateDataView(self):
        if not self.dataView:
            return
        self.dataView.settext(self.getDataStr())
        

    def browseData(self):
        """open introspect GUI"""
        if self.objectBrowser is None:
            
            self.objectBrowser = ObjectBrowser(
                self.data, rootName='Data',
                title='node %s, port %s'%(self.node.name, self.name),
                refresh=self._introspectCB)
        else:
            self.objectBrowser.show()


    def _introspectCB(self):
        """helper method used for the introspect data GUI"""
        return self.data


    def edit(self, event=None):
        if self.objEditor:
            self.objEditor.top.master.lift()
            return
        from Editor import PortEditor
        self.objEditor = PortEditor(self)


    def typeName(self, t):
        if type(t)==types.ClassType or type(t)==types.BuiltinFunctionType:
            return t.__name__
        else:
            return type(t).__name__


    def deleteIcon(self):
        """deleting the port's icon"""
        if self.iconTag:
            self.visible = False
            if self.node.network:
                if isinstance(self, InputPort) or \
                   isinstance(self, SpecialInputPort):
                    del self.node.network.inPortsId[self.id]

                elif isinstance(self, OutputPort) or \
                     isinstance(self, SpecialOutputPort):
                    del self.node.network.outPortsId[self.id]
                    
            canvas = self.node.iconMaster
            canvas.delete(self.iconTag)
            self.id = None
            self.iconTag = None
            

    def datatypeStr(self):
        if type(self.datatype)==types.StringType:
            return self.datatype
        # obsolete since all datatypes are now string !?
        tstr = self.typeName(self.datatype)
        d = self.datatype
        while 1:
            try:
                d = d[0]
                tstr = tstr + ' of ' + self.typeName(d)
            except:
                break
        return tstr
            
            
    def createIcon(self, pcx=None, pcy=None):
        #print "createIcon"

        ed = self.getEditor()
        if not ed.hasGUI:
            return

        # recompute posx, since some port.visible might be False (hidden port)
        self.visible = True
        self.relposx = self.computePortPosX()

        canvas = self.node.iconMaster
        
        if pcx is None:
            pcx = self.node.posx + self.relposx + 3
        if pcy is None:
            pcy = self.node.posy + self.relposy + 3
#        bb = canvas.bbox(self.node.id) # node.id == node.innerBox               
#        pcx = bb[0] + self.relposx
#        pcy = bb[1] + self.relposy
        sca = self.node.scaleSum
        w = int(round(self.halfPortWidth*sca))
        h = int(round(self.halfPortHeight*sca))

        color = self.datatypeObject['color']
        shape = self.datatypeObject['shape']

        # add tags
        ptags = ['port', self.node.iconTag]
        if isinstance(self, InputPort):
            ptags.append('inputPort')
        elif isinstance(self, OutputPort):
            ptags.append('outputPort')
        elif isinstance(self, SpecialInputPort):
            ptags.append('specialInputPort')
        elif isinstance(self, SpecialOutputPort):
            ptags.append('specialOutputPort')

        if self.hasHiddenConnections is True:
            lOutlineColor = 'white'
        elif hasattr(self, 'required') and self.required is False:
            lOutlineColor = 'gray50'
        else:
            lOutlineColor = 'black'

        # FIXME: for compatibility reasons, we keep 'rect1', 'rect2', etc
        # In the near future (like next release, we will delete those
        # and only use 'rect', 'oval', ect, since now we can specify the
        # width, height in datatypes
        if shape in [0, 'oval', 'oval1', 'oval2', 'circle']:
            self.id = self.iconTag = canvas.create_oval(
                pcx-w, pcy-h, pcx+w, pcy+h,
                tags=tuple(ptags+[self.node.id]), fill=color,
                outline = lOutlineColor )
        elif shape in [1, 'triang', 'triang1']:
            self.id = self.iconTag = canvas.create_polygon(
                pcx-(h/2)+2, pcy-w+2, pcx-h-2, pcy+w-2, pcx+h+2, pcy+w-2,
                tags=tuple(ptags+[self.node.id]), fill=color,
                outline = lOutlineColor )

        elif shape in [2, 'rect', 'rect1', 'rect2', 'square']:
            self.id = self.iconTag = canvas.create_rectangle(
                pcx-w, pcy-h, pcx+w, pcy+h,
                tags=tuple(ptags+[self.node.id]), fill=color, 
                outline = lOutlineColor )

        elif shape in [3, 'diamond' ]:
            self.id = self.iconTag = canvas.create_polygon(
                pcx-h-3, pcy, pcx, pcy-h-3, pcx+h+3, pcy, pcx, pcy+h+3,
                tags=tuple(ptags+[self.node.id]), fill=color,
                outline = lOutlineColor )

        else: #elif shape in [4, 'pentagon']:
            self.id = self.iconTag = canvas.create_polygon(
                pcx-(h/2)+1, pcy-w+2, pcx-h-4, pcy+w/2-4, pcx-h/2-2, pcy+w-2,
                pcx+h/2, pcy+w-2, pcx+h+2, pcy+w/2-4,
                tags=tuple(ptags+[self.node.id]), fill=color,
                outline = lOutlineColor )

        # add balloon string
        txt = 'name : '+self.name + '\ntype : '+ self.datatypeObject['name']
        if self.datatypeObject['dataDescr'] is not None:
            txt = txt + '\ntype descr. : '+self.datatypeObject['dataDescr']
        txt = txt + '\nindex: '+str(self.number)
        if isinstance(self, InputPort):
            txt = txt + '\nrequired: ' + str(self.required)
            txt = txt + '\nsingle connection: '+ str(self.singleConnection)
        if self.balloon is not None:
            txt = txt + '\nport Descr. :' + self.balloon + '\n'

        # bind balloon
        ed.balloons.tagbind(canvas, self.id, txt)
        self.balloonBase = txt

        if self.node.network is not None:
            if isinstance(self, InputPort) or \
               isinstance(self, SpecialInputPort):
                self.node.network.inPortsId[self.id] = self
            elif isinstance(self, OutputPort) or \
                 isinstance(self, SpecialOutputPort):
                self.node.network.outPortsId[self.id] = self

            if isinstance(self, InputPort):
                self.inputDataBallon()


    def destroyIcon(self):
        """called by net.deleteNodes(): delete port menu, delete port icon"""
        self.menu.destroy()
        self.menu = None
        self.deleteIcon()
        
        
    def computePortPosX(self):
        """compute offset from left. Convention: if a port is invisible, we
set this port's relposx to the values of the last visible
port left of this port, or to 0 and 0, if all ports left of it are invisible
Note: relposx is the center of a port icon, not the left or right edge
"""
        #print "computePortPosX"
        oldposx = self.relposx
        pnumber = self.number
        gap = 5  # gap between 
        
        if pnumber == 0:
            if self.visible:
                relposx = gap + self.halfPortWidth
            else:
                relposx = 0
            return relposx

        if isinstance(self, InputPort):
            ports = self.node.inputPorts
        else:
            ports = self.node.outputPorts

        prevPort = None
        # we loop backwards over ports and try to find one that is visible
        for i in range(len(ports))[(pnumber-1)::-1]: # going backwards
            prevPort = ports[i]
            if prevPort.visible:
                break
            else:
                prevPort = None # reset to None if prevPort is invisible

        if prevPort: # we have a port left of us, that is visible
            if self.visible:
                relposx = prevPort.relposx + prevPort.halfPortWidth + \
                               gap + self.halfPortWidth
            else:
                relposx = prevPort.relposx

        else: # no visible ports left of us
            if self.visible:
                relposx = gap + self.halfPortWidth
            else:
                relposx = 0

        return relposx

        
    def destinationPortsCoords(self, tag):
        # get coordinates of all potential ports to connect to
        canvas = self.node.iconMaster
        items = canvas.find_withtag(tag)
        c = []
        il = []
        getc = canvas.coords
        for i in items:
            if self.id==i: continue
            ci = getc(i)
            c.append( ( (ci[0]+ci[2])/2, (ci[1]+ci[3])/2 ) )
            il.append(i)
        return Numeric.array(c, 'i'), il


    def getDescr(self):
        """Returns a dictionnary providing the port's configuration.
"""
        cfg = {}
        cfg['name'] = self.name
        if self.datatypeObject['name'] != None:
            cfg['datatype'] = self.datatypeObject['name']
        if    isinstance(self, InputPort) \
          and self.datatypeObject['name'] != self.originalDatatype:
            cfg['originalDatatype'] = self.originalDatatype
        if self.balloon:
            cfg['balloon'] = self.balloon
        cfg['width'] = self.halfPortWidth*2
        cfg['height'] = self.halfPortHeight*2

        cfg['color'] = self.datatypeObject['color']
        cfg['shape'] = self.datatypeObject['shape']

        if self.callbacks['beforeConnect'][1] is not None:
            cfg['beforeConnect'] = self.callbacks['beforeConnect'][1]
        if self.callbacks['afterConnect'][1] is not None:
            cfg['afterConnect'] = self.callbacks['afterConnect'][1]
        if self.callbacks['beforeDisconnect'][1] is not None:
            cfg['beforeDisconnect'] = self.callbacks['beforeDisconnect'][1]
        if self.callbacks['afterDisconnect'][1] is not None:
            cfg['afterDisconnect'] = self.callbacks['afterDisconnect'][1]

        return cfg

    
    def configure(self, redo=1, **kw):
        """configure a Port object. This also sets the port's attribute
        _modified=True. Supports the folloing keywords:
width     : icon width (int)
height    : icon on height (int)
name      : port name (string)
balloon   : tooltip describing data (string)
datatype  : datatype (string or data type object)
"""
        changeIcon = 0
        handledOps = {}
        for k,v in kw.items():
            if k == 'width':
                handledOps[k] = v
                if v/2 != self.halfPortWidth:
                    self.halfPortWidth = v/2
                    changeIcon = 1
            elif k=='height':
                handledOps[k] = v
                if v/2 != self.halfPortHeight:
                    self.halfPortHeight = v/2
                    changeIcon = 1
            elif k == 'name':
                v = v.replace(' ', '_')
                handledOps[k] = v
                if v != self.name:
                    if self.node:
                        wdescr = self.node.widgetDescr
                        if wdescr.has_key(self.name):
                            wdescr[v] = wdescr[self.name]
                            del wdescr[self.name]

                    if isinstance(self, InputPort):
                        port = 'ip'
                    else:
                        port = 'op'
                    self.node.updateCode(port=port, action='rename', newname=v,
                                         oldname=self.name, tagModified=True)

                    if isinstance(self,InputPort):
                        self.node.inputPortByName[v] = self
                        self.node.inputPortByName.pop(self.name)
                    else:
                        # OutputPort
                        self.node.outputPortByName[v] = self
                        self.node.outputPortByName.pop(self.name)

                    self.name = v
                    changeIcon = 1
            elif k=='datatype':
                handledOps[k] = v
                self.setDataType(v, tagModified=True)
                changeIcon = 1
            elif k=='originalDatatype':
                self.originalDatatype = v
            elif k=='balloon':
                handledOps[k] = v
                self.balloon = v
                changeIcon = 1
            elif k=='defaultValue':
                handledOps[k] = v
                self.defaultValue = v
            elif k in ['beforeConnect', 'afterConnect', 'beforeDisconnect',
                       'afterDisconnect']:
                handledOps[k] = v
                self.setCallback(v, k)
                
        if len(handledOps.keys()):
                self._setModified(True)

        if redo:
            if changeIcon and self.iconTag:
                self.deleteIcon()
                self.createIcon()
                changeIcon = 0
                
        return changeIcon, handledOps


    def updateIconPosition(self):
        """move this icon to new location, also update connections
"""
        #print "updateIconPosition"
        if not self.visible or not self.id:
            return

        oldposx = self.relposx
        newposx = self.computePortPosX() # move ports
        self.relposx = newposx
        dx = newposx - oldposx
        if not dx:
            return
        # move port icon
        canvas = self.node.iconMaster
        canvas.move(self.id, dx, 0)
        # move connections
        for c in self.connections:
            c.updatePosition()


    def startConnectRubberBand(self, event):
        if isinstance(self, SpecialOutputPort):
            self.ipCoords, self.ipId = self.destinationPortsCoords(
                'specialInputPort')
        else:
            self.ipCoords, self.ipId = self.destinationPortsCoords('inputPort')
        if len(self.ipCoords)==0: return
        c = self.rubberBandOrig = self.getCenterCoords()
        self.secondNodePort = None
        self.oldColor = self.node.getColor()
        self.node.setColor('green')
        canvas = self.node.iconMaster
        self.rubberBandLine = canvas.create_line(
            c[0], c[1], c[0], c[1], width=3, fill='green' )
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag | num
        canvas.bind("<B%d-Motion>"%num, self.drawRubberBand)
        canvas.bind("<ButtonRelease-%d>"%num, self.connectNodesEnd)


    def drawRubberBand(self, event=None):
        canvas = self.node.iconMaster
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)

        # compute distance to all input ports
        dist = self.ipCoords - (x, y)
        dist = Numeric.sum( dist*dist, 1 )
        indsort = Numeric.argsort( dist )
        portId = self.ipId[indsort[0]]
        port = self.node.network.inPortsId[portId] # closest port
        snap = 0
        
        if dist[indsort[0]] < 400 or len(indsort)==1:
            # we are close enough to snap
            if port.node != self.node and \
               port not in self.children:
                x, y = port.getCenterCoords()
                if self.secondNodePort:
                    self.secondNodePort.node.setColor(self.oldColor2)
                self.secondNodePort = port
                self.oldColor2 = port.node.getColor()
                port.node.setColor('green')
                snap = 1

        canvas.coords(self.rubberBandLine,
                    self.rubberBandOrig[0], self.rubberBandOrig[1], x, y )

        if not snap:
            if self.secondNodePort:
                self.secondNodePort.node.setColor(self.oldColor2)
            self.secondNodePort = None


    # end the command, remove rubberband, connect nodes
    def connectNodesEnd(self, event=None):
        num = event.num
        self.mouseButtonFlag = self.mouseButtonFlag & ~num
        self.node.setColor(self.oldColor)
        canvas = self.node.iconMaster
        canvas.unbind("<B%d-Motion>"%num)
        canvas.unbind("<ButtonRelease-%d>"%num)

        canvas.delete(self.rubberBandLine)

        if not self.secondNodePort: return
        self.secondNodePort.node.setColor(self.oldColor2)
        ed = self.node.network
        kw = ed.defaultConnectionOptions
        kw['mode'] = ed.defaultConnectionMode
        kw.update(ed.defaultConnectionOptions)
        #kw['name'] = 'connection %d'%len(ed.connections)
        node1 = self.node
        portNum1 = self.number
        node2 = self.secondNodePort.node
        portNum2 = self.secondNodePort.number
        
        apply( self.createConnection,  ( self, self.secondNodePort ), kw)


    def createConnection(self, port1, port2, **kw):
        ed = self.node.network
        if isinstance(self, SpecialOutputPort):
            conn = apply( ed.specialConnectNodes,
                     (port1.node, port2.node, port1.number, port2.number), kw )
        else:
            conn = apply( ed.connectNodes,
                     (port1.node, port2.node, port1.number, port2.number), kw )


    def compareToOrigPortDescr(self):
        """Compare this port to the original portDescr defined in a given
network node base class and return a dictionary with the differences
"""
        #print "compareToOrigPortDescr", self.name

        id = self._id
        lConstrkw = {'masternet': self.node.network}
        lConstrkw.update(self.node.constrkw)
        dummy = apply(self.node.__class__,(),lConstrkw) # we need the base class node

        if isinstance(self, InputPort):
            origDescr = dummy.inputPortsDescr[id]
            #print "origDescr", origDescr
        elif isinstance(self, OutputPort):
            origDescr = dummy.outputPortsDescr[id]

        ownDescr = self.getDescr().copy()
        #print "ownDescr", ownDescr

        descr = {}
        for k,v in ownDescr.items():
            if k in origDescr.keys():
                if v != origDescr[k]:
                    descr[k] = v
                ownDescr.pop(k)
            elif k == '_previousWidgetDescr':
                ownDescr.pop(k)
            elif k=='datatype' and ownDescr['datatype']== 'None':
                ownDescr.pop(k)
            elif k == 'width' and v == self.datatypeObject['width']:
                ownDescr.pop(k)
            elif k == 'height' and v == self.datatypeObject['height']:
                ownDescr.pop(k)
            elif k == 'color' and v == self.datatypeObject['color']:
                ownDescr.pop(k)
            elif k == 'shape' and v == self.datatypeObject['shape']:
                ownDescr.pop(k)
            elif k == 'required' and v == True:
                ownDescr.pop(k)
            elif k == 'singleConnection' and v == True:
                ownDescr.pop(k)
            elif k == 'cast' and v == True:
                ownDescr.pop(k)

        # and add all the stuff we didnt find in the orig descr
        descr.update(ownDescr)

        #print "descr", descr
        return descr


class InputPort(Port):

    def __init__(self, name, node, datatype=None, required=True,
                 balloon=None, width=None, height=None, singleConnection=True,
                 beforeConnect=None, afterConnect=None, beforeDisconnect=None,
                 afterDisconnect=None, shape=None, color=None, cast=True,
                 originalDatatype=None,
                 _previousWidgetDescr=None, # not used but will silence an "unexpected keyword argument" message
                 defaultValue=None
                 ):

        self.number = len(node.inputPorts)
        self.parents = [] # list of ports connected to this one
        self.widget = None
        self.editWtk = None
        self.delWtk = None
        self._missingDims = None # this will hold the number of missing
                                 # optional dimensions for AnyArrayType ports

        self._cast = cast

        self._previousWidgetDescr = None # Will hold widgetDescr when unbound
        self.widgetInMacro = {}  # used to keep track of widgets re-bound to
                                 # macro nodes 

        Port.__init__(self, name, node, datatype=datatype, balloon=balloon, 
                      width=width, height=height,
                      beforeConnect=beforeConnect, afterConnect=afterConnect, 
                      beforeDisconnect=beforeDisconnect,
                      afterDisconnect=afterDisconnect, shape=shape, color=color,
                      originalDatatype=originalDatatype)

        self.mouseAction['<Button-1>'] = self.selfDefaultValueEditor
        self.defaultValue = defaultValue

        self.required = required
        self.singleConnection = singleConnection # port will accept only one
                 # parent and provide the computational method with
                 # an argument that is not a list created from multiple
                 # parents (usually used for widgets, float, string etc...)

        # when new data is sent trough an output port, _newdata of all input
        # ports of children nodes is set to 1. When a child node has
        # processed the data it resets is to 0
        # Also, when a connection is deleted, the child node's input port's
        # _newdata is set to True (since it used to provide data and doesn't
        # anymore)
        self._newdata = False

        # _validation is set to 'uncheck' when data new is output
        # it is set to 'valid' or 'invalid' in getData
        # it is used in getData to avoid revalidating data
        self._validationStatus = 'unchecked'


    def selfDefaultValueEditor(self, event):
        if self.required is True \
          or len(self.connections) != 0:
            return
        if hasattr(self, 'topEntry') is False:
            self.topEntry = Tkinter.Toplevel()
            self.defaultValueVar = Tkinter.StringVar()
            if type(self.defaultValue) == types.StringType: 
                self.defaultValueVar.set('\''+self.defaultValue +'\'')
            else:
                self.defaultValueVar.set(self.defaultValue)
            self.typedValueTK = Tkinter.Entry(
                               master=self.topEntry,
                               textvariable=self.defaultValueVar,
                               relief='sunken', bg='yellow')
        self.topEntry.overrideredirect(1)
        self.topEntry.bind("<Escape>", self.esc_cb)
        self.topEntry.bind("<Leave>", self.return_cb)
        self.topEntry.bind("<Return>", self.return_cb)
        w = event.widget
        self.topEntry.geometry('+%d+%d'%(w.winfo_rootx() + event.x-30,
                                         w.winfo_rooty() + event.y-10))
        self.typedValueTK.pack()
        self.typedValueTK.focus_set()
        self.typedValueTK.config(cursor='xterm')
        lenDefault = len(self.defaultValueVar.get())
        self.typedValueTK.selection_to(lenDefault)


    def esc_cb(self, event):
        # return should destroy the topEntry
        #print "esc_cb"
        del self.defaultValueVar
        self.typedValueTK.destroy()
        del self.typedValueTK
        self.topEntry.destroy()
        del self.topEntry


    def return_cb(self, event):
        # return should destroy the topEntry
        #print "return_cb"
        try:
            lDefaultValue = eval(self.defaultValueVar.get())
            if lDefaultValue != self.defaultValue:
                self.defaultValue = lDefaultValue
                self._modified = True
                self._newdata = True
                self.data = 'no data yet'
                self.inputDataBallon()
        finally:
            self.esc_cb(event)


    def hasNewData(self):
        # returns 1 if at least 1 parent provides new data

        # if a widget is connected to this port
        if self.widget:
            return self.widget._newdata
        else:
            return self._newdata


    def hasNewValidData(self):
        """returns 1 if at least 1 parent provides new and valid data
"""
        # if a widget is connected to this port
        if self.widget:
            return self.widget._newdata
        elif self.data == 'no data yet':
            return False
        else:
            return self._newdata


    def releaseData(self):
        # the data provided by all connections has been processed
        # successfully by this node
        if self.widget:
            self.widget._newdata = False
            self.widget.lastUsedValue = self.widget.get()
        else:
            self._newdata = False


    def inputDataBallon(self):
        if self.balloonBase and self.id and self.network:
            datastr = self.getInputDataStr(maxLen=80)
            self.getEditor().balloons.tagbind(self.network.canvas, 
                                self.id,
                                self.balloonBase + '\n' + datastr)


    def getInputDataStr(self, maxLen = None):
        # return a string that would be used in input port's show data

        length = 0
        if isinstance(self.data, Numeric.ArrayType):
            if len(self.data.shape) == 0:  
                length = 0
            else:
                length = reduce( lambda x,y: x*y, self.data.shape)
        elif hasattr(self.data, '__len__'):
            try:
                length = len(self.data)
            except TypeError, e:
                length = len(str(self.data))

        if length > 1000:
            return '-'*80 + '\n'+ "Too much data to print"

        datastr = repr(self.data)
        if maxLen:
            if len(datastr) < maxLen:
                return '-'*80 + '\n'+ datastr
            else:
                return '-'*80 + '\n'+ datastr[:maxLen] + '...'
        else:
            return '-'*80 + '\n'+ datastr


    def getDescr(self):
        """Returns a dictionnary providing the port's configuration.
"""
        #print "InputPort getDescr"

        cfg = Port.getDescr(self)

        if self.name == 'parent':
            cfg['retainPosition'] = self.retainPosition.get()
            # for now, we always save it as we don't know yet what
            # will be the definitive default behaviour
            cfg['parenting'] = self.cascadeMenuVariable.get()
        
        cfg['cast'] = self._cast.get()
        cfg['required'] = self.required
        cfg['singleConnection'] = self.singleConnection
        cfg['defaultValue'] = self.defaultValue

        pdscr = self._previousWidgetDescr
        if pdscr is not None and len(pdscr):
            cfg['_previousWidgetDescr'] = pdscr

        return cfg


    def configure(self, redo=1, **kw):
        """configure a InputPort object. Supports the folloing keywords:
width     : icon width (int)
height    : icon on height (int)
name      : port name (string)
datatype  : datatype (string or data type object)
required  : port only runs if valid data is provided on this port (Boolean)
singleConnection : ports accepts only one connection (Boolean)
cast      : data will be casted into desired type only if cast is True   
parenting : type of parenting (if self.name is 'parent')  

"""
        changeIcon, handledOps = apply( Port.configure, (self, 0), kw )
        for k,v in kw.items():
            if k == 'parenting':
                assert self.name == 'parent'
                assert v in ('none','current','siblings','all'), v
                handledOps[k] = v
                if v != self.cascadeMenuVariable.get():
                    self.cascadeMenuVariable.set(v)
            elif k=='retainPosition':
                assert type(v) is types.BooleanType
                handledOps[k] = v
                if v != self.retainPosition.get():
                    self.retainPosition.set(v)
            elif k == 'cast':
                assert (type(v) is types.BooleanType) or (type(v) is types.IntType and v in (0,1) )
                handledOps[k] = v
                if v != self._cast.get():
                    self._cast.set(v)
            elif k == 'required':
                assert type(v) is types.BooleanType
                handledOps[k] = v
                if v != self.required:
                    self.required = v
                    changeIcon = 1
            elif k in ['beforeConnect', 'afterConnect', 'beforeDisconnect',
                       'afterDisconnect']:
                self.setCallback(v, k)
            elif k=='singleConnection':
                assert v in [True, False, 'auto']
                handledOps[k] = v
                if v != self.singleConnection:
                    self.singleConnection = v
                    changeIcon = 1
            elif k=='_previousWidgetDescr':
                self._previousWidgetDescr = v
                self.menu.add_command(label='Rebind Widget', underline=0, 
                                       command=self.rebindWidget)

        if len(handledOps.keys()):
            self._setModified(True)

        # update the port's description
        self.node.inputPortsDescr[self.number].update( handledOps )

        if redo:
            if changeIcon and self.iconTag:
                self.deleteIcon()
                self.createIcon()


    def createWidget(self, rescale=1, descr=None):
        """Method to create and configure a port's widget.
    - if descr is specified update the node's widget description dictionary
    - create the widget from its description
    - hide the port's icon
    - set the port's widget attribute
    
    Options that are only usable with the constructor (not in the configure
    method) are extracted from descr and used to instanciate the widget.
"""
        if descr:
            self.node.widgetDescr[self.name] = descr
        else:
            descr = self.node.widgetDescr.get(self.name, None)

        if descr is None:
            return
        modif = descr.pop('_modified', False)
        descr = descr.copy()

        # we create a non graphical widget that will be delete if the
        # GUI is created and replaced by a real widget

        if not self.getEditor().hasGUI:
            value = descr.get('initialValue', None)
            self.widget = NGWidget()
            if value:
                self.widget.set(value)
            return

        # get a copy of the widget's constructor only options
        widgetClass = descr.pop('class')
        if type(widgetClass) is types.StringType:
            widgetClass = widgetsTable[widgetClass]
        
        # instanciate the widget
        w = apply( widgetClass, (self, ), descr)

        # new widget, thus set _modifed and _original attribute accordingly
        w._setModified(modif)
        w._setOriginal(False)
        
        self.widget = w  # set this port's widget emneter
        # delete port icon, move all icons right of it
        self.deleteIcon()
        self.replosx = self.computePortPosX()
        for port in self.node.inputPorts[self.number+1:]:
            if port.visible:
                port.updateIconPosition()

        # delete all connections to this port
        self.node.network.deleteConnections(self.connections, 0)
        self.node.autoResizeX()
        

##     def configureWidget(self, **descr):
##         # configure widget will create new widget and replace old one for
##         # some options
##         if self.widget:
##             w, descr = apply( self.widget.configure, (self,), descr)
##             if isinstance(w, PortWidget):
##                 w.set( self.widget.get(), run=0l )
##                 self.deleteWidget()
##                 self.widget = w  # set this port's widget emneter
##                 self.node.widgetDescr[self.name] = w.getDescr()
##                 self.deleteIcon()  # hide port icon
##                 if w.inNode:
##                     self.node.hideInNodeWidgets()
##                     self.node.showInNodeWidgets()


    def rebindWidget(self, run=True):
        if self._previousWidgetDescr:
            wdescr = self._previousWidgetDescr
            if not self.node.isExpanded():
                self.node.toggleNodeExpand_cb()

            self.createWidget(descr=wdescr)
            self.node.autoResize()

            if self.network.runOnNewData.value is True and run is True:
                self.node.schedule()


    def unbindWidget(self, force=False):
        #print "unbindWidget"
        ed = self.node.getEditor()
        if ed is None:# or isinstance(self.widget, NGWidget):
            return
        inNode = False
        if self.widget:
            if hasattr(self.widget,'onUnbind'):
                self.widget.onUnbind()

            if isinstance(self.widget, NGWidget) is False:
              try: # Uh, I know, this is not nice, but how else do I find out
                # if a menu entry is added to self.menu??? 
                # do we have this entry alread? If yes, do nothing
                self.menu.index('Rebind Widget')
              except:
                # add new menu entry if not there
                self.menu.add_command(label='Rebind Widget', underline=0, 
                                      command=self.rebindWidget)

              if hasattr(self.widget, 'inNode') and self.widget.inNode:
                inNode = True
                self.node.nodeWidgetMaster.configure(width=1)
                self.node.nodeWidgetMaster.configure(height=1)

              pw = self.widget.getDescr()
            else:
              pw = {}

            pw['initialValue'] = self.widget.get()
            self._previousWidgetDescr = pw
            self.deleteWidget()

            if inNode:
                wM = self.node.nodeWidgetMaster
                width = wM.winfo_reqwidth()
                height = wM.winfo_reqheight() 
                wM.configure(width=width, height=height)

            if ed.hasGUI:
                self.node.autoResize()
                self.node.addSaveNodeMenuEntries()

            # unbinding a widget sets the port _modified flag
            self._setModified(True)


    def deleteWidget(self):
        """destroy the widget, remove the widgetDescription from dict and show
the port icon, return the decription of the deleted widget
"""
        #print "deleteWidget"

        if hasattr(self.widget,'onDelete'):
            self.widget.onDelete()

        wasExpanded = False
        inNode = False
        if isinstance(self.widget, NGWidget) is False:
            inNode = self.widget.inNode
            wdescr = self.widget.configure() # get widget's configuration
        else:
            wdescr = {}

        if inNode and self.node.isExpanded(): # repack node before destroying
            self.node.hideInNodeWidgets()     # widget else we loose size
            wasExpanded = True

        del self.node.widgetDescr[self.name] # update node's widget description dict
        
        # destroy the icon
        if isinstance(self.widget, NGWidget) is False:
          self.widget.destroy()

          if wasExpanded and len(self.node.widgetDescr.keys()):# repack node
            self.node.showInNodeWidgets()                    #before destroying
          else:
            resize=True
            for v in self.node.widgetDescr.values():
                if v.has_key('master') and v['master'] in ['node', 'Node']:
                    resize = False
                    break
            if resize is True and isinstance(self.widget, NGWidget) is False: # only resize, if we have no node widget left
                self.node.nodeWidgetMaster.configure(width=1, height=1)
                self.node.autoResize()

          # create port icon, move ports to the right, move connections
          self.createIcon() # show port's Icon
          self.relposx = self.computePortPosX()
          for port in self.node.inputPorts[self.number+1:]:
            if port.visible:
                port.updateIconPosition()

        self.widget = None

        # deleting a widget sets the port _modified flag
        self._setModified(True)

        return wdescr

        
    def buildIcons(self, resize=True):
        self.relposy = 0
        Port.buildIcons(self, resize=resize)


    def badDataOnInputPort(self, parent):
        self._validationStatus = 'invalid'
        txt = 'Running node: %s \n' % self.node.name
        txt += 'Bad Data on port: %s \n' % self.name
        txt += 'comming from port: %s %s \n' % (parent.node.name, parent.name)
        txt += 'Active Casting:: %s' % self._cast.get() 
        warnings.warn(txt)
        return False, None


    def getParentPortData(self, parent):
        """If data is not already marked as valid, try to validate it,
if it fails, try to cast it, if it fails check for sequence of 1 object of
proper type. Return validation status (true or false) and data. In the 2 latter
cases, status of port's data remains 'unchecked'.
"""
        #print "getParentPortData parent", parent, parent.data
        #print "getParentPortData self", self, self.data

        #if parent.data is None:
        #    import pdb;pdb.set_trace()

        data = parent.data

        for conn in self.connections:
            if conn.port1 == parent:
                theConnection = conn
                break;
        else: # we didn't break
            assert False # we should have found the connection
        if    theConnection.blocking is True \
          and (type(data) == types.StringType) \
          and (data == 'no data yet'):
            return False, data #None

        elif self.datatypeObject is None:
            self._validationStatus='valid'
            return True, data
        #Check is this input port's data has already been validates
        elif self._validationStatus=='valid':
            return True, parent.data
        elif self._validationStatus=='invalid':
            return False, parent.data
        elif self._validationStatus=='missingDims':
            data = parent.data
            for i in range(self._missingDims):
                data = [data]
            return True, data
        elif self._validationStatus=='unchecked':
            # None is always consider has valid data 
            # and all the nodes must knows how to deal with it
            if data is None: 
                return True, data
            # check is data is of proper type
            typeObj = self.datatypeObject
            if isinstance(typeObj, AnyType):
                # validate data
                ok = typeObj.validate(data)
                if ok:
                    self._validationStatus='valid'
                    return True, data

                if self._cast.get() in (0, False): 
                    return self.badDataOnInputPort(parent)                  

                # check for sequence of 1 element and accept if proper type
                try: # force exception if data is not a sequence
                    if len(data)==1: # if sequence of length 1
                        data = data[0]
                        ok = typeObj.validate(data)
                        if ok:
                            return True, data
                except:
                    pass

                # isSequenceType return true for all instances
                #if isSequenceType(data) and len(data)==1:
                #    data = data[0]
                #    ok = typeObj.validate(data)
                #    if ok:
                #        return True, data

                # try to cast if there is a cast function
                ok, castdata = typeObj.cast(data)
                if ok:
                    # we leave it _validationStatus unchecked
                    return True, castdata

                # everything failed
                return self.badDataOnInputPort(parent)

            else:  # AnyArrayType port
                
                # check that data can be turned into Numeric array
                #import pdb;pdb.set_trace()
                ok, lArray = typeObj.validate(data)
                if typeObj['datashape'] is None:
                    if ok is True:
                        self._validationStatus='valid'
                        return True, data
                    else:
                        if self._cast.get() in (0, False): 
                            return self.badDataOnInputPort(parent)                        
                        ok, castdata = typeObj.cast(data)
                        if ok is True:
                            self._validationStatus='unchecked'
                            return True, castdata
                        else:                            
                            # check for sequence of 1 element and accept if proper type
                            try: # force exception if data is not a sequence
                                if len(data)==1: # if sequence of length 1
                                    data = data[0]
                                    ok = typeObj.validate(data)
                                    if ok:
                                        return True, data
                                    else:
                                        ok, castdata = typeObj.cast(data)
                                        if ok is True:
                                            self._validationStatus='unchecked'
                                            return True, castdata
                                        else:
                                            return self.badDataOnInputPort(parent)
                            except:                           
                                return self.badDataOnInputPort(parent)

                if ok is False:
                    if self._cast.get() in (0, False): 
                        return self.badDataOnInputPort(parent)                        
                    else:    
                        # if port allows casting try
                        ok, lArray = typeObj.cast(data)
                        if ok is False:
                            return self.badDataOnInputPort(parent)
                        # the data is tagged unchecked when new data is presented
                        # on the parent port, so we just leave it unchecked
                        else:
                            # remember this data has been casted
                            self._validationStatus='casted'
                            #print "casted"

                # lArray is now a Numeric array of the right data type
                # we now have to check dimensions
                # this functions return True when the dims match, the number
                # of missing optional dimensions, or False if required dims
                # fail the tests
                                      
                status, lArray = typeObj.validateDims(lArray)
                if status is True:
                    if self._validationStatus=='casted':
                        self._validationStatus='unchecked'
                        return True, lArray
                    else:
                        self._validationStatus='valid'
                        return True, data

                elif status is False:
                    return self.badDataOnInputPort(parent)

                else:
                    if self._validationStatus=='casted':
                        self._validationStatus='unchecked'
                        #return True, lArray
                    else:
                        self._validationStatus='missingDims'
                    self._missingDims = status
                    for i in range(status):
                        data = [data]
                    return True, data
                    
                
    def getData(self):
        """ retrieve data for this port.

the data is fetched from the parent port.
1 - if the parent node data is valide we return it
2 - if the data is not valid we return 'Stop' to prevent further execution
3 - if the parent port provide no data ('no data yet'):
    if the port is required we return 'Stop'
    if the port is optional we return 'no data yet'
"""
        #print "getData", self
        #if self.node.name == 'output Ports' and self.name == 'if__if':
        #if self.name == 'nodes':
        #    import pdb;pdb.set_trace()

        ed = self.getEditor()
        
        # if there are connections
        if len(self.parents):

            # if this port accepts only 1 connection
            if self.singleConnection is True:
                ok, allData = self.getParentPortData(self.parents[0])
                if ok is False:
                    if allData=='no data yet': # no data yet
                        if self.required is True:
                            self.data = 'no data yet'
                            self.inputDataBallon()
                            return 'Stop'
                    else: # bad data
                        self.data = 'no data yet'           
                        self.inputDataBallon()
                        if ed.hasGUI and ed.verbose:
                            s='Bad or missing data on port %s in node %s in network %s'%(
                                self.name, self.node.name, self.node.network.name)
                            warnings.warn(s)
                        return 'Stop' # to prevent execution
            else:
                allData = []
                # for each connection
                for parentPort in self.parents:
                    data = parentPort.data
                    ok, data = self.getParentPortData(parentPort)
                    if ok is True:
                        allData.append(data)
                if len(allData)==0:
                    if self.required is True:
                        if ed.hasGUI and ed.verbose:
                            s='Data missing on required port %s in node %s in network %s'%(
                                self.name, self.node.name, self.node.network.name)
                            warnings.warn(s)
                        self.data = 'no data yet'           
                        self.inputDataBallon()
                        return 'Stop'
                    else:
                        allData = 'no data yet'
                elif len(self.parents)==1 and self.singleConnection=='auto':
                    allData = allData[0]
                    
        else: # no parents
            if self.widget: # get value from widget
                allData = self.widget.get()
                # NO validation on data from widgets ???
                #ok, data = self.getParentPortData(self.parents[0])
                #if not ok:
                #   return 'Stop' # to prevent execution
            elif self.required is False:
                allData = self.defaultValue
            else:
                self.data = 'no data yet'           
                self.inputDataBallon()
                return 'Stop'

        if type(allData)==types.StringType and allData == 'no data yet':
            if self.required:
                if ed.hasGUI and ed.verbose:
                    s='Data missing on required port %s in node %s in network %s'%(
                        self.name, self.node.name, self.node.network.name)
                    warnings.warn(s)
                self.data = 'no data yet'           
                self.inputDataBallon()
                return 'Stop'
#            else:
#                # get arguments description
#                sign = getargspec(self.node.dynamicComputeFunction)
#                args, varargs, varkw, defaults = sign
#                if defaults is not None:
#                    optargs = args[-len(defaults):]
#                    for i,argname in enumerate(optargs):
#                        if argname==self.name:
#                            allData = defaults[i]
#                elif len(self.parents) == 0: #no connections
#                    allData = None

        # save data for viewer for instance
        self.data = allData           
        self.inputDataBallon()
        return allData
        

    
class OutputPort(Port):

    def __init__(self, name, node, datatype='None', balloon=None,
                 width=None, height=None,
                 beforeConnect=None, afterConnect=None, beforeDisconnect=None,
                 afterDisconnect=None, shape=None, color=None):

        self.number = len(node.outputPorts)
        self.children = [] # list of ports connected to this one
        
        Port.__init__(self, name, node, datatype, balloon, width, height,
                      beforeConnect, afterConnect, beforeDisconnect,
                      afterDisconnect, shape=shape, color=color)

        self.mouseAction['<Button-1>'] = self.startConnectRubberBand
        self.delWtk = None


    def setDataType(self, datatype, tagModified=True, makeOriginal=False):
        """set the port's data type.
        Update Port's icon if visible
        Update connections color"""

        ed = self.getEditor()
        Port.setDataType(self, datatype, tagModified=tagModified)
        # for output ports we also check to see if input port that are
        # connected take their type from output port
        for c in self.connections:
            p = c.port2

            # we check if the port must be mutated before mutating it
            typename = p.datatypeObject['name']
            if typename=='None' or typename != p.originalDatatype:
                p.setDataType(datatype, tagModified=tagModified)

            if ed.hasGUI:
                # change the connection color
                col = p.datatypeObject['color']
                c.unhighlightOptions['fill'] = col
                c.iconMaster.itemconfigure(c.iconTag, fill=col)

        if tagModified:
            self._setModified(True)

        if makeOriginal:
            self.originalDatatype = datatype
                

    def outputData(self, data):
        self.data = data
        ed = self.getEditor()
        if ed.hasGUI:
            datastr = self.getDataStr(maxLen=80)
            node = self.node
            ed.balloons.tagbind(node.network.canvas, self.id,
                                self.balloonBase+'\n'+datastr)
            
        for c in self.connections:
            p = c.port2
            p._newdata = True
            p._validationStatus = 'unchecked'
            p._missingDims = None
            p.node.newData = 1


    def resetData(self):
        self.data = None
        for c in self.connections:
            c.port2._newdata = False
                   
    
    def configure(self, **kw):
        redo = 0
        redo, handledOps = apply( Port.configure, (self, 0), kw )

        if redo and self.iconTag:
            self.deleteIcon()
            self.createIcon()


    def buildIcons(self, resize=True):
        canvas = self.node.iconMaster
        bb = canvas.bbox(self.node.id)
        self.relposy = bb[3]-bb[1]
        Port.buildIcons(self, resize=resize)


# FIXME maybe special ports should be hardcoded rather than lists
class SpecialInputPort(Port):

    def __init__(self, name, node, datatype='triggerIn', balloon=None,
                 width=8, height=8):

        self.number = len(node.specialInputPorts)
        self.parents = [] # list of ports connected to this one
        self.widget = None

        Port.__init__(self, name, node, datatype, balloon, \
                      width, height)

        self.required = False


    def createIcon(self, pcx=None, pcy=None):
        # compute offest from upper left corner
        self.relposx = 0
        self.relposy = ((self.number*3)+2)*self.halfPortHeight

        Port.createIcon(self, pcx, pcy)

                     
    def computePortPosX(self):
        relposx = 0
        return relposx
    

class RunNodeInputPort(SpecialInputPort):

    def __init__(self, node, datatype='triggerIn'):

        SpecialInputPort.__init__(self, 'runNode', node, datatype,
                                  balloon='trigger this node')
        
        

class RunChildrenInputPort(SpecialInputPort):

    def __init__(self, node, datatype=None):

        SpecialInputPort.__init__(self, 'runChildren', node, datatype,
                                  balloon="trigger this node's children")


class SpecialOutputPort(Port):


    def __init__(self, name, node, datatype='None', balloon=None,
                 width=8, height=8):

        self.children = [] # list of ports connected to this one

        Port.__init__(self, name, node, datatype, balloon,
                            width, height)
        
        self.number = len(node.specialOutputPorts)

        self.mouseAction['<Button-1>'] = self.startConnectRubberBand



    def createIcon(self, pcx=None, pcy=None):
        # compute offest from upper left corner
        self.relposx = 0
        self.relposy = ((self.number*3)+2)*self.halfPortHeight

        Port.createIcon(self, pcx, pcy)


    def computePortPosX(self):
        self.network.canvas.update_idletasks()
        bb = self.node.iconMaster.bbox(self.node.id)
        relposx = bb[2]-bb[0]
        return relposx


class TriggerOutputPort(SpecialOutputPort):

    def __init__(self, node):

        SpecialOutputPort.__init__(self, 'trigger', node, 'triggerOut',
                                   balloon="trigger connected node")

