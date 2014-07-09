########################################################################
#
# Date: Nov 2001 Authors: Daniel Stoffler, Michel Sanner
#
#    stoffler@scripps.edu
#    sanner@scripps.edu
#
# Copyright: Daniel Stoffler, Michel Sanner and TSRI
#
#########################################################################

from NetworkEditor.widgets import TkPortWidget, PortWidget
from mglutil.gui.BasicWidgets.Tk.xyzGUI import xyzGUI
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.callback import CallbackManager
import Tkinter, string, math

class VectEntry(Tkinter.Frame):
    """ this widget is a specialized Entry for typing in vector values.
        A setValue() method has been added which checks that the input is
        correct. The vector is used *as is* and will not be normalized """

    def __init__(self, master=None, label=None, width=18, callback=None, **kw):
        Tkinter.Frame.__init__(self, master)
        Tkinter.Pack.config(self)

        self.var = Tkinter.StringVar()
        
        self.frame = Tkinter.Frame(self)

        if label and label != '':
            d={'fg':'black','text':label}
            self.tklabel = apply(Tkinter.Label, (self.frame,), d)
            self.tklabel.pack()
            

        kw['width']=width
        self.tkwidget = apply( Tkinter.Entry, (self.frame,), kw )
        self.tkwidget.bind('<Return>', self.setValue_cb)
        self.tkwidget.pack()

        self.tkwidget['textvariable'] = self.var
        self.point = [0., 0, 0]
        self.text = '0 0 0'

        self.frame.pack(side='top', expand=1)

        self.myCallback = callback
        self.callbacks = CallbackManager()
        if self.myCallback:
            self.callbacks.AddCallback(self.myCallback)
    

    def setValue_cb(self, event=None):
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
            self.text = `self.point[0]`+' '+`self.point[1]`+' '+\
                        `self.point[2]`
            self.var.set(self.text)
            self.callbacks.CallCallbacks(self.point)
        except:
            self.text = oldtext
            self.updateField()
        

    def updateField(self):
        self.var.set(self.text)


# used in XYZVectGUI below
class NormVectEntry(VectEntry):
    """ this widget is a specialized Entry for typing in vector values.
        A setValue() method has been added which checks that the input is
        correct. The vector is normalized """

    def __init__(self, master=None, label=None, width=18, callback=None, **kw):
        VectEntry.__init__(self, master, label, width, callback)


    def setValue_cb(self, event=None):
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
            self.point=[]
            self.point.append(float(val[0]))
            self.point.append(float(val[1]))
            self.point.append(float(val[2]))
            
            # compute normalized vector
            n = math.sqrt(self.point[0]*self.point[0]+\
                          self.point[1]*self.point[1]+\
                          self.point[2]*self.point[2])
            if n == 0.0: self.point = [0.0, 0.0, 1.0]
            else: v = [self.point[0]/n, self.point[1]/n, self.point[2]/n]
            self.point = v
            self.text = `self.point[0]`+' '+`self.point[1]`+' '+\
                        `self.point[2]`
            self.var.set(self.text)
            self.callbacks.CallCallbacks(self.point)
        except:
            self.text = oldtext
            self.updateField()
            

    def get(self):
        return self.point


    def set(self, value):
        #called when node is loaded
        self.text = `value[0]`+' '+`value[1]`+' '+`value[2]`
        self.var.set(self.text)
        self.point = value


class XYZVectGUI(xyzGUI):

    def __init__(self, master=None, name='VectXYZ', callback=None,
                 callbackX=None, widthX=100, heightX=26, wheelPadX=4,
                 labcfgX={'text':None}, widthY=100, heightY=26, wheelPadY=4,
                 labcfgY={'text':None}, callbackY=None, widthZ=100,
                 heightZ=26, wheelPadZ=4, callbackZ=None,
                 labcfgZ={'text':None}, **kw):

        xyzGUI.__init__(self, master, name, callback, callbackX, widthX,
                        heightX, wheelPadX, labcfgX, widthY, heightY,
                        wheelPadY, labcfgY, callbackY, widthZ, heightZ,
                        wheelPadZ, callbackZ, labcfgZ)

        
    def createEntries(self, master):
        self.f = Tkinter.Frame(master)
	self.f.grid(column=1, rowspan=6)

        self.entryX = NormVectEntry(master=self.f, label='Vector X', width=18)
        self.entryX.grid(row=0,column=0)
        self.entryX.callbacks.AddCallback(self.entryX_cb)

        self.thumbx = ThumbWheel(master=self.f, width=self.widthX,
                                 height=self.heightX, labcfg=self.labcfgX,
                                 wheelPad=self.wheelPadX)
        self.thumbx.callbacks.AddCallback(self.thumbx_cb)
        self.thumbx.grid(row=1, column=0)

        self.entryY = NormVectEntry(master=self.f, label='Vector Y', width=18)
        self.entryY.grid(row=2,column=0)
        self.entryY.callbacks.AddCallback(self.entryY_cb)


        self.thumby = ThumbWheel(master=self.f, width=self.widthY,
                                 height=self.heightY, labcfg=self.labcfgY,
                                 wheelPad=self.wheelPadY)
        self.thumby.callbacks.AddCallback(self.thumby_cb)
        self.thumby.grid(row=3, column=0)

        self.entryZ = NormVectEntry(master=self.f, label='Vector Z', width=18)
        self.entryZ.grid(row=4,column=0)
        self.entryZ.callbacks.AddCallback(self.entryZ_cb)


        self.thumbz = ThumbWheel(master=self.f, width=self.widthZ,
                                 height=self.heightZ, labcfg=self.labcfgZ,
                                 wheelPad=self.wheelPadZ)
        self.thumbz.callbacks.AddCallback(self.thumbz_cb)
        self.thumbz.grid(row=5, column=0)

        self.f.pack(side='top', expand=1)

        self.setVector([1.0,0,0],'x')
        self.setVector([0.0,1,0],'y')
        self.setVector([0.0,0,1],'z')

    def set(self, x, y, z, v1, v2, v3):
        # called from outside
        self.thumbx.setValue(x)
        self.thumby.setValue(y)
        self.thumbz.setValue(z)
        self.entryX.set(v1)
        self.entryY.set(v2)
        self.entryZ.set(v3)


    def entryX_cb(self, events=None):
        self.callbacks.CallCallbacks(self.entryX.point)
        

    def entryY_cb(self, events=None):
        self.callbacks.CallCallbacks(self.entryY.point)


    def entryZ_cb(self, events=None):
        self.callbacks.CallCallbacks(self.entryZ.point)


 #####################################################################
 # the 'configure' methods:
 #####################################################################

    def configure(self, **kw):
        for key,value in kw.items():
            # the 'set parameter' callbacks
            if key=='labcfgX': self.setLabel(value,'x')
            elif key=='labcfgY': self.setLabel(value,'y')
            elif key=='labcfg': self.setLabel(value,'z')

            elif key=='continuousX': self.setContinuous(value,'x')
            elif key=='continuousY': self.setContinuous(value,'y')
            elif key=='continuousZ': self.setContinuous(value,'z')

            elif key=='precisionX': self.setPrecision(value,'x')
            elif key=='precisionY': self.setPrecision(value,'y')
            elif key=='precisionZ': self.setPrecision(value,'z')

            elif key=='typeX': self.setType(value,'x')
            elif key=='typeY': self.setType(value,'y')
            elif key=='typeZ': self.setType(value,'z')

            elif key=='minX': self.setMin(value,'x')
            elif key=='minY': self.setMin(value,'y')
            elif key=='minZ': self.setMin(value,'z')

            elif key=='maxX': self.setMax(value,'x')
            elif key=='maxY': self.setMax(value,'y')
            elif key=='maxZ': self.setMax(value,'z')

            elif key=='oneTurnX': self.setOneTurn(value,'x')
            elif key=='oneTurnY': self.setOneTurn(value,'y')
            elif key=='oneTurnZ': self.setOneTurn(value,'z')

            elif key=='showLabelX': self.setShowLabel(value,'x')
            elif key=='showLabelY': self.setShowLabel(value,'y')
            elif key=='showLabelZ': self.setShowLabel(value,'z')

            elif key=='incrementX': self.setIncrement(value,'x')
            elif key=='incrementY': self.setIncrement(value,'y')
            elif key=='incrementZ': self.setIncrement(value,'z')

            elif key=='vectX' : self.setVector(value,'x')
            elif key=='vectY' : self.setVector(value,'y')
            elif key=='vectZ' : self.setVector(value,'z')

            ####################################################

            elif key=='lockTypeX': self.lockType(value,'x')
            elif key=='lockTypeY': self.lockType(value,'y')
            elif key=='lockTypeZ': self.lockType(value,'z')

            elif key=='lockMinX': self.lockMin(value,'x')
            elif key=='lockMinY': self.lockMin(value,'y')
            elif key=='lockMinZ': self.lockMin(value,'z')

            elif key=='lockBMinX': self.lockBMin(value,'x')
            elif key=='lockBMinY': self.lockBMin(value,'y')
            elif key=='lockBMinZ': self.lockBMin(value,'z')

            elif key=='lockMaxX': self.lockMax(value,'x')
            elif key=='lockMaxY': self.lockMax(value,'y')
            elif key=='lockMaxZ': self.lockMax(value,'z')

            elif key=='lockBMaxX': self.lockBMax(value,'x')
            elif key=='lockBMaxY': self.lockBMax(value,'y')
            elif key=='lockBMaxZ': self.lockBMax(value,'z')

            elif key=='lockIncrementX': self.lockIncrement(value,'x')
            elif key=='lockIncrementY': self.lockIncrement(value,'y')
            elif key=='lockIncrementZ': self.lockIncrement(value,'z')

            elif key=='lockBIncrementX': self.lockBIncrement(value,'x')
            elif key=='lockBIncrementY': self.lockBIncrement(value,'y')
            elif key=='lockBIncrementZ': self.lockBIncrement(value,'z')

            elif key=='lockPrecisionX': self.lockPrecision(value,'x')
            elif key=='lockPrecisionY': self.lockPrecision(value,'y')
            elif key=='lockPrecisionZ': self.lockPrecision(value,'z')

            elif key=='lockShowLabelX': self.lockShowLabel(value,'x')
            elif key=='lockShowLabelY': self.lockShowLabel(value,'y')
            elif key=='lockShowLabelZ': self.lockShowLabel(value,'z')

            elif key=='lockValueX': self.lockValue(value,'x')
            elif key=='lockValueY': self.lockValue(value,'y')
            elif key=='lockValueZ': self.lockValue(value,'z')

            elif key=='lockContinuousX': self.lockContinuous(value,'x')
            elif key=='lockContinuousY': self.lockContinuous(value,'y')
            elif key=='lockContinuousZ': self.lockContinuous(value,'z')

            elif key=='lockOneTurnX': self.lockOneTurn(value,'x')
            elif key=='lockOneTurnY': self.lockOneTurn(value,'y')
            elif key=='lockOneTurnZ': self.lockOneTurn(value,'z')


    def setVector(self, value, mode):
       if mode == 'x':
           self.entryX.set(value)
       if mode == 'y':
            self.entryY.set(value)
       if mode == 'z':
            self.entryZ.set(value)



class NEXYZVectGUI(TkPortWidget):

    # description of parameters that can only be used with the widget's
    # constructor
    configOpts = PortWidget.configOpts.copy()
    ownConfigOpts = {
        'widthX':{'min':1, 'max':500, 'type':'int', 'defaultValue':100},
        'heightX':{'min':1, 'max':500, 'type':'int', 'defaultValue':26},
        'wheelPadX':{'min':1, 'max':500, 'type':'int', 'defaultValue':4},
        'labcfgX':{'type':'dict','defaultValue':{
            'text':'length X', 'side':'left'}},
        
        'widthY':{'min':1, 'max':500, 'type':'int', 'defaultValue':100},
        'heightY':{'min':1, 'max':500, 'type':'int', 'defaultValue':26},
        'wheelPadY':{'min':1, 'max':500, 'type':'int', 'defaultValue':4},
        'labcfgY':{'type':'dict','defaultValue':{
            'text':'length Y', 'side':'left'}},

        'widthZ':{'min':1, 'max':500, 'type':'int', 'defaultValue':100},
        'heightZ':{'min':1, 'max':500, 'type':'int', 'defaultValue':26},
        'wheelPadZ':{'min':1, 'max':500, 'type':'int', 'defaultValue':4},
        'labcfgZ':{'type':'dict','defaultValue':{
            'text':'length Z', 'side':'left'}},
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
        self.widget = apply( XYZVectGUI, (self.widgetFrame,), widgetcfg)
        self.widget.callbacks.AddCallback(self.newValueCallback)

        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), widgetcfg)

        if self.initialValue:
            self.set(self.initialValue, run=0)
            
        self.modified = False # will be set to True by configure method

        
    def get(self):
        return (self.widget.thumbx.value, self.widget.thumby.value, \
               self.widget.thumbz.value, self.widget.entryX.point, \
               self.widget.entryY.point, self.widget.entryZ.point)
    

    def set(self, val, run=1):
        if val is not None:
            self._setModified(True)
            self.widget.set(val[0],val[1],val[2],val[3],val[4],val[5])
            if self.port.network.runOnNewData.value is True and run:
                self.port.node.schedule()


    def getConstructorOptions(self):
        cfg = PortWidget.getConstructorOptions(self)
        cfg['labcfgX'] = self.widget.thumbx.labcfg
        cfg['callbackX'] = self.widget.thumbx.myCallback
        cfg['widthX'] = self.widget.thumbx.width
        cfg['heightX'] = self.widget.thumbx.height
        cfg['wheelPadX'] = self.widget.thumbx.wheelPad

        cfg['labcfgY'] = self.widget.thumby.labcfg
        cfg['callbackY'] = self.widget.thumby.myCallback
        cfg['widthY'] = self.widget.thumby.width
        cfg['heightY'] = self.widget.thumby.height
        cfg['wheelPadY'] = self.widget.thumby.wheelPad

        cfg['labcfgZ'] = self.widget.thumbz.labcfg
        cfg['callbackZ'] = self.widget.thumbz.myCallback
        cfg['widthZ'] = self.widget.thumbz.width
        cfg['heightZ'] = self.widget.thumbz.height
        cfg['wheelPadZ'] = self.widget.thumbz.wheelPad
        cfg.update(self.configure())
        return cfg


    def getDescr(self):
        cfg = PortWidget.getDescr(self)

        typex = self.widget.thumbx.type
        if typex == int: cfg['typeX'] = 'int'
        else: cfg['typeX'] = 'float'
        typey = self.widget.thumby.type
        if typey == int: cfg['typeY'] = 'int'
        else: cfg['typeY'] = 'float'
        typez = self.widget.thumbz.type
        if typez == int: cfg['typeZ'] = 'int'
        else: cfg['typeZ'] = 'float'

        cfg['continuousX'] = self.widget.thumbx.continuous
        cfg['continuousY'] = self.widget.thumby.continuous
        cfg['continuousZ'] = self.widget.thumbz.continuous

        cfg['precisionX'] = self.widget.thumbx.precision
        cfg['precisionY'] = self.widget.thumby.precision
        cfg['precisionZ'] = self.widget.thumbz.precision

        cfg['minX'] = self.widget.thumbx.min
        cfg['minY'] = self.widget.thumby.min
        cfg['minZ'] = self.widget.thumbz.min

        cfg['maxX'] = self.widget.thumbx.max
        cfg['maxY'] = self.widget.thumby.max
        cfg['maxZ'] = self.widget.thumbz.max

        cfg['oneTurnX'] = self.widget.thumbx.oneTurn
        cfg['oneTurnY'] = self.widget.thumby.oneTurn
        cfg['oneTurnZ'] = self.widget.thumbz.oneTurn

        cfg['showLabelX'] = self.widget.thumbx.showLabel
        cfg['showLabelY'] = self.widget.thumby.showLabel
        cfg['showLabelZ'] = self.widget.thumbz.showLabel

        cfg['incrementX'] = self.widget.thumbx.increment
        cfg['incrementY'] = self.widget.thumby.increment
        cfg['incrementZ'] = self.widget.thumbz.increment

        cfg['vectX'] = self.widget.entryX.point
        cfg['vectY'] = self.widget.entryY.point
        cfg['vectZ'] = self.widget.entryZ.point


        ##############################################

        cfg['lockTypeX'] = self.widget.thumbx.lockType
        cfg['lockTypeY'] = self.widget.thumby.lockType
        cfg['lockTypeZ'] = self.widget.thumbz.lockType

        cfg['lockMinX'] = self.widget.thumbx.lockMin
        cfg['lockMinY'] = self.widget.thumby.lockMin
        cfg['lockMinZ'] = self.widget.thumbz.lockMin

        cfg['lockBMinX'] = self.widget.thumbx.lockBMin
        cfg['lockBMinY'] = self.widget.thumby.lockBMin
        cfg['lockBMinZ'] = self.widget.thumbz.lockBMin

        cfg['lockMaxX'] = self.widget.thumbx.lockMax
        cfg['lockMaxY'] = self.widget.thumby.lockMax
        cfg['lockMaxZ'] = self.widget.thumbz.lockMax

        cfg['lockBMaxX'] = self.widget.thumbx.lockBMax
        cfg['lockBMaxY'] = self.widget.thumby.lockBMax
        cfg['lockBMaxZ'] = self.widget.thumbz.lockBMax

        cfg['lockIncrementX'] = self.widget.thumbx.lockIncrement
        cfg['lockIncrementY'] = self.widget.thumby.lockIncrement
        cfg['lockIncrementZ'] = self.widget.thumbz.lockIncrement

        cfg['lockBIncrementX'] = self.widget.thumbx.lockBIncrement
        cfg['lockBIncrementY'] = self.widget.thumby.lockBIncrement
        cfg['lockBIncrementZ'] = self.widget.thumbz.lockBIncrement

        cfg['lockPrecisionX'] = self.widget.thumbx.lockPrecision
        cfg['lockPrecisionY'] = self.widget.thumby.lockPrecision
        cfg['lockPrecisionZ'] = self.widget.thumbz.lockPrecision

        cfg['lockShowLabelX'] = self.widget.thumbx.lockShowLabel
        cfg['lockShowLabelY'] = self.widget.thumby.lockShowLabel
        cfg['lockShowLabelZ'] = self.widget.thumbz.lockShowLabel

        cfg['lockValueX'] = self.widget.thumbx.lockValue
        cfg['lockValueY'] = self.widget.thumby.lockValue
        cfg['lockValueZ'] = self.widget.thumbz.lockValue

        cfg['lockContinuousX'] = self.widget.thumbx.lockContinuous
        cfg['lockContinuousY'] = self.widget.thumby.lockContinuous
        cfg['lockContinuousZ'] = self.widget.thumbz.lockContinuous

        cfg['lockOneTurnX'] = self.widget.thumbx.lockOneTurn
        cfg['lockOneTurnY'] = self.widget.thumby.lockOneTurn
        cfg['lockOneTurnZ'] = self.widget.thumbz.lockOneTurn

        return cfg
