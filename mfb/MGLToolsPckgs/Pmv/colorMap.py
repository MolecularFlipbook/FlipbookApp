## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/colorMap.py,v 1.2 2007/07/24 17:30:39 vareille Exp $
#
# $Id: colorMap.py,v 1.2 2007/07/24 17:30:39 vareille Exp $
#
from Tkinter import *
from DejaVu.colorTool import RGBRamp, ToRGB, ToHSV
import types, numpy.oldnumeric as Numeric

class ColorMapGUI(Frame):

    def button_cb(self, event=None):
        """call back function for the buttons allowing to toggle between
        different canvases.
        This function hides the currentCanvas and shows the canvas
        corresponding to the active radio button.
        In addition it sets
             self.currentCanvas : used to hide it next time we come in
             self.currentLines : list of Canvas Line objects (one per canvas)
             self.currentValues : list of numerical values (one per canvas)
             self.getColor =  function to be called to represent a color as a
                              Tk string
        """
        var = self.currentCanvasVar.get()
        newCanvas = self.canvas[var]
        self.currentCanvas.forget()
        newCanvas.pack(side=TOP)
        self.currentCanvas = newCanvas
        self.currentLines = self.lines[var]
        self.currentValues = self.values[var]
        self.getColor = self.getColorFunc[var]
        self.current = var
        

    def hueColor(self, val):
        """TkColorString <- hueColor(val)
        val is an integer between 25 and 200.
        returns color to be use to draw hue lines in hue canvas
        """
        return self.hueColor[val-25]
    

    def satColor(self, val):
        """TkColorString <- satColor(val)
        val is an integer between 25 and 200
        returns color to be use to draw saturation lines in saturation canvas
        """
        return self.saturationCol[val-25]


    def valColor(self, val):
        """TkColorString <- satColor(val)
        val is an integer between 25 and 200
        returns color to be use to draw value and opacity lines in canvas
        """
        h = hex(val)[2:]
        if len(h)==1: h = '0'+h
        return '#'+h+h+h


    def createWidgets(self):
        """create Tkinter widgets: 4 canvas and buttons in 2 frames
        """
        # create 4 canvas
        self.canvas = {}
        self.canvas['Hue'] = Canvas(self, relief=SUNKEN, borderwidth=3,
                                    width="200", height="256")
	self.canvas['Hue'].pack(side=TOP)
       
	self.canvas['Sat'] = Canvas(self, relief=SUNKEN, borderwidth=3,
                                    width="200", height="256")

	self.canvas['Val'] = Canvas(self, relief=SUNKEN, borderwidth=3,
                                    width="200", height="256")

	self.canvas['Opa'] = Canvas(self, relief=SUNKEN, borderwidth=3,
                                    width="200", height="256")

        # create frame for min max
        self.minTk = StringVar()
        self.minTk.set(str(self.min))
        self.maxTk = StringVar()
        self.maxTk.set(str(self.max))
        
        minmaxFrame = Frame(self)
        Label(minmaxFrame, text='Min: ').grid(row=0, column=0, sticky='e')
        self.minEntry = Entry(minmaxFrame, textvariable=self.minTk)
        self.minEntry.bind('<Return>', self.min_cb)
        self.minEntry.grid(row=0, column=1, sticky='w')

        Label(minmaxFrame, text='Max: ').grid(row=1, column=0, sticky='e')
        self.maxEntry = Entry(minmaxFrame, textvariable=self.maxTk)
        self.maxEntry.bind('<Return>', self.max_cb)
        self.maxEntry.grid(sticky='w', row=1, column=1 )
        minmaxFrame.pack()

        self.dissmiss = Button(self, text='Dissmiss', command=self.quit)
        self.dissmiss.pack(side=BOTTOM, fill=X)
        
        # create frame for buttons
        self.buttonFrame = Frame(self)
        
        # create radio buttons to switch between canvas
        self.buttonFrame1 = f = Frame(self.buttonFrame)
        self.currentCanvasVar = StringVar()
	self.buttonHue = Radiobutton(f, text='Hue', value = 'Hue',
                                     indicatoron = 0, width=15,
                                     variable = self.currentCanvasVar,
                                     command=self.button_cb)
	self.buttonHue.grid(column=0, row=0, sticky='w')

        self.buttonSat = Radiobutton(f, text='Saturation', value = 'Sat',
                                     indicatoron = 0, width=15,
                                     variable = self.currentCanvasVar,
                                     command=self.button_cb)
	self.buttonSat.grid(column=0, row=1, sticky='w')

	self.buttonVal = Radiobutton(f, text='Brightness', value = 'Val',
                                     indicatoron = 0, width=15,
                                     variable = self.currentCanvasVar,
                                     command=self.button_cb)
	self.buttonVal.grid(column=0, row=2, sticky='w')

	self.buttonOpa = Radiobutton(f, text='Opacity', value = 'Opa',
                                     indicatoron = 0, width=15,
                                     variable = self.currentCanvasVar,
                                     command=self.button_cb)
	self.buttonOpa.grid(column=0, row=3, sticky='w')
        f.pack(side=LEFT)
        
        self.currentCanvas = self.canvas['Hue']
        self.currentCanvasVar.set('Hue')

        # create radio buttons to switch between canvas
        self.buttonFrame2 = f = Frame(self.buttonFrame)
	self.reset = Button(f, text='Reset', width=10, command=self.reset_cb)
        self.reset.grid(column=0, row=1, sticky='w')
	self.read = Button(f, text='Read', width=10, command=self.read_cb)
        self.read.grid(column=0, row=2, sticky='w')
	self.write = Button(f, text='Write', width=10, command=self.write_cb)
        self.write.grid(column=0, row=3, sticky='w')
        f.pack(side=LEFT)
        self.buttonFrame.pack(side=BOTTOM)


    def min_cb(self, event):
        min = float(self.minTk.get())
        if min < self.max:
            self.min = min
            self.callCallbacks()
        else:
            min = self.max-255.0
            self.minTk.set(str(min))
            self.min = min

    def max_cb(self, event):
        max = float(self.maxTk.get())
        if max > self.min:
            self.max = max
            self.callCallbacks()
        else:
            max = self.min+255.0
            self.maxTk.set(str(max))
            self.max = max
            
        
    def quit(self):
        self.master.destroy()

        
    def reset_cb(self):
        var = self.currentCanvasVar.get()

        self.clear(var)
        if var == 'Hue':
            self.rampHue()
            self.drawHue()
        elif var == 'Sat':
            self.constantSaturation(200)
            self.drawSaturation()
        elif var == 'Val':
            self.constantValue(200)
            self.drawValue()
        elif var == 'Opa':
            self.rampOpacity()
            self.drawOpacity()
        self.mouseUp(None) # to call callbacks
        

    def read_cb(self):
        print 'read'


    def write_cb(self):
        print 'write'
        

    def clear(self, name):
        assert name in ['Hue', 'Sat', 'Val', 'Opa' ]
        l = self.lines[name]
        c = self.canvas[name]
        for i in range(256):
            c.delete(l[i])
        self.lines[name] = []
        self.values[name] = []
        if self.current==name:
            self.currentLines = self.lines[name]
            self.currentValues = self.values[name]

    def rampHue(self):
        ramp = RGBRamp(176)
        self.hueFromRGB = map( lambda x, conv=ToHSV: conv(x)[0], ramp )
        ramp = (ramp*255).astype('i')
        for i in range(176):
            r = hex(int(ramp[i][0]))[2:]
            if len(r)==1: r='0'+r
            g = hex(ramp[i][1])[2:]
            if len(g)==1: g='0'+g
            b = hex(ramp[i][2])[2:]
            if len(b)==1: b='0'+b
            self.hueColor.append( '#'+r+g+b)

        v = self.values['Hue']
        for i in range(256):
            v.append(int(i*(175./255.)+25))
        

    def drawHue(self):
        l = self.lines['Hue']
        c = self.canvas['Hue']
        v = self.values['Hue']
        for i in range(256):
            val = v[i]
            col = self.hueColor[val-25]
            l.append( c.create_line( 0, i, val, i, fill=col) )


    def constantSaturation(self, value):
        for i in range(176, -1, -1):
            h = hex(int(i*174/255.))[2:]
            if len(h)==1: h='0'+h
            self.saturationCol.append( '#ff'+h+h )

        v = []
        for i in range(256):
            v.append(value)
        self.values['Sat'] = v

        if self.current=='Sat':
            self.currentValues = v


    def drawSaturation(self):
        c = self.canvas['Sat']
        l = self.lines['Sat']
        v = self.values['Sat']
        for i in range(256):
            val = v[i]
            l.append( c.create_line( 0, i, val, i, fill='red') )

        if self.current=='Sat':
            self.currentLines = l


    def constantValue(self, value):
        v = []
        for i in range(256):
            v.append(value)
        self.values['Val'] = v
        if self.current=='Val':
            self.currentValues = v


    def drawValue(self):
        c = self.canvas['Val']
        l = self.lines['Val']
        v = self.values['Val']
        for i in range(256):
            l.append( c.create_line( 0, i, v[i], i, fill='white') )

        if self.current=='Val':
            self.currentLines = l


    def rampOpacity(self):
        v = []
        for i in range(256):
            v.append(int(i*(175./255.)+25))
        self.values['Opa'] = v
        if self.current=='Opa':
            self.currentValues = v


    def drawOpacity(self):
        c = self.canvas['Opa']
        l = self.lines['Opa']
        v = self.values['Opa']
        for i in range(256):
            val = v[i]
            col = self.valColor(val-25)
            l.append( c.create_line( 0, i, val, i, fill=col) )
        if self.current=='Opa':
            self.currentLines = l


    def addCallback(self, function):
        assert callable(function)
        self.callbacks.append( function )

        
    def buildRamp(self):
        h = map( lambda x, table=self.hueFromRGB: table[x-25],
                 self.values['Hue'] )
        h = Numeric.array(h)
        #h = (Numeric.array(self.values['Hue'])-25)/175.0
        s = (Numeric.array(self.values['Sat'])-25)/175.0
        v = (Numeric.array(self.values['Val'])-25)/175.0
        a = (Numeric.array(self.values['Opa'])-25)/175.0
        self.hsva = map( None, h,s,v,a )
        self.rgbMap = map( ToRGB, self.hsva)


    def callCallbacks(self):
        for f in self.callbacks:
            f( self.rgbMap, self.min, self.max )

        
    def mouseUp(self, event):
        self.buildRamp()
        self.callCallbacks()

                          
    def mouseDown(self, event):
	# canvas x and y take the screen coords from the event and translate
	# them into the coordinate system of the canvas object
        x = min(199, event.x)
        y = min(255, event.y)
        x = max(25, x)
        y = max(0, y)

        c = self.currentCanvas
        self.starty = y
        line = self.currentLines[y]
        col = self.getColor(x)
        newline = c.create_line( 0, y, x, y, fill=col)
        self.currentLines[y] = newline
        self.currentValues[y] = x
        c.delete(line)
        self.startx = x
        

    def mouseMotion(self, event):
	# canvas x and y take the screen coords from the event and translate
	# them into the coordinate system of the canvas object

        # x,y are float
	#x = self.canvasHue.canvasx(event.x)
	#y = self.canvasHue.canvasy(event.y)

        # event.x, event.y are same as x,y but int
        x = min(199, event.x)
        y = min(255, event.y)
        x = max(25, x)
        y = max(0, y)
        c = self.currentCanvas
	if self.starty == y:
            line = self.currentLines[y]
            col = self.getColor(x)
            newline = c.create_line( 0, y, x, y, fill=col)
            self.currentLines[y] = newline
            c.delete(line)
            self.currentValues[y] = x
            
        else: # we need to interpolate for all y's between self.starty and y
            dx = x-self.startx
            dy = y-self.starty
            rat = float(dx)/float(dy)
            if y > self.starty:
                for yl in range(self.starty, y):
                    ddx = int(rat*(yl-self.starty)) + self.startx
                    line = self.currentLines[yl]
                    col = self.getColor(ddx)
                    newline = c.create_line( 0,yl, ddx,yl,fill=col)
                    self.currentLines[yl] = newline
                    c.delete(line)
                    self.currentValues[yl] = ddx
            else:
                for yl in range(self.starty, y, -1):
                    ddx = int(rat*(yl-self.starty)) + self.startx
                    line = self.currentLines[yl]
                    col = self.getColor(ddx)
                    newline = c.create_line( 0,yl, ddx,yl,fill=col)
                    self.currentLines[yl] = newline
                    c.delete(line)
                    self.currentValues[yl] = ddx
            self.starty = y
            self.startx = x

	    # this flushes the output, making sure that 
	    # the rectangle makes it to the screen 
	    # before the next event is handled
	    self.update_idletasks()


    def __init__(self, master=None, min=0.0, max=255.0):
        if master == None:
            master = Toplevel()
	Frame.__init__(self, master)
	Pack.config(self)

        self.min=min
        self.max=max
        self.getColorFunc = { 'Hue':self.hueColor,
                              'Sat':self.satColor,
                              'Val':self.valColor,
                              'Opa':self.valColor
                              }

        self.values = { 'Hue': [],
                        'Sat': [],
                        'Val': [],
                        'Opa': []
                        }
        self.lines = { 'Hue':[], 'Sat':[], 'Val':[], 'Opa':[] }
        self.current = 'Hue'
        self.currentLines = None
        self.currentValues = None

        self.hueColor = []
        self.saturationCol = []

        self.callbacks = []
        self.hueFromRGB = []
        
	self.createWidgets()
        self.rampHue()
        self.drawHue()
        self.constantSaturation(200)
        self.drawSaturation()
        self.constantValue(200)
        self.drawValue()
        self.rampOpacity()
        self.drawOpacity()
        # just so we have the corresponfing RGBramp
        self.buildRamp()

        self.getColor = self.getColorFunc['Hue']
        self.currentLines = self.lines['Hue']
        self.currentValues = self.values['Hue']

	Widget.bind(self.canvas['Hue'], "<ButtonPress-1>", self.mouseDown)
	Widget.bind(self.canvas['Hue'], "<Button1-Motion>", self.mouseMotion)
	Widget.bind(self.canvas['Hue'], "<ButtonRelease-1>", self.mouseUp)
	Widget.bind(self.canvas['Sat'], "<ButtonPress-1>", self.mouseDown)
	Widget.bind(self.canvas['Sat'], "<Button1-Motion>", self.mouseMotion)
	Widget.bind(self.canvas['Sat'], "<ButtonRelease-1>", self.mouseUp)
	Widget.bind(self.canvas['Val'], "<ButtonPress-1>", self.mouseDown)
	Widget.bind(self.canvas['Val'], "<Button1-Motion>", self.mouseMotion)
	Widget.bind(self.canvas['Val'], "<ButtonRelease-1>", self.mouseUp)
	Widget.bind(self.canvas['Opa'], "<ButtonPress-1>", self.mouseDown)
	Widget.bind(self.canvas['Opa'], "<Button1-Motion>", self.mouseMotion)
	Widget.bind(self.canvas['Opa'], "<ButtonRelease-1>", self.mouseUp)
	

if __name__ == '__main__':
    import pdb
    test = ColorMapGUI()
    def cb(ramp, min, max):
        print len(ramp), min, max
    test.addCallback(cb)
#test.mainloop()
