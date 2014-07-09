#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/extendedSlider.py,v 1.6 2003/08/29 18:07:13 sophiec Exp $
#
# $Id: extendedSlider.py,v 1.6 2003/08/29 18:07:13 sophiec Exp $
#
import Tkinter
from DejaVu.Slider import Slider
import types

class ExtendedSlider(Slider):
	#"""Composite slider which includes a simple slider 
	#   and an entry window used to set self.value """
	
    def MoveCursor(self, event):
        """Callback function for left mouse button"""
        x = event.x - self.left
        self._MoveCursor(x)
	val =  x
        #minType = type(self.min)
	val = self.min+self.cst1 * x
	if self.incrCanvas:
	    val = round(val/self.incr)*self.incr
            val = eval(self.cursortype+'('+str(val)+')')
            #if minType is types.IntType:
                #val = int(val)
	if val<self.min: val = self.min
	elif val>self.max: val = self.max
	self.contents.set(val)

    def _FixedMoveCursor(self, x):
	"""move cursor to new position which is typed 
	   into the entry window"""
	# compute the new value
	val =  x
        #valType = type(val)
	if self.incrCanvas:
	    val = round(val/self.incr)*self.incr
            val = eval(self.cursortype+'('+str(val)+')')
            #if valType is types.IntType:
                #val  = int(val)
	if val<self.min: val = self.min
	elif val>self.max: val = self.max
	# check if redraw and callback are needed
	if self.val != val:
	    self.val = val
	    self.DrawCursor()
	    if self.immediate: self.Callbacks()

    def set(self, val, update=1):
        """Set Both the cursor and entry window"""
        if val<self.min: val = self.min
        elif val>self.max: val = self.max
        if self.incrCanvas:
            val = round(val/self.incr)*self.incr
        self.val = val
        self.DrawCursor()
        if update: self.Callbacks()
	self.contents.set(val)
        return self.val

    def isOn(self):
        if self.onButton: return self.entrylabel.get()
        else: return 1


    def on_cb(self, event=None):
        if self.onTk.get(): self.enable()
        else: self.disable()

    def disable(self):
        self.onTk.set(0)
        self.entry.configure(state='disabled', bg='#AAAAAA')
	self.draw.unbind( "<1>")
	self.draw.unbind( "<B1-Motion>" )
	self.draw.unbind( "<ButtonRelease>" )


    def enable(self):
        self.onTk.set(1)
        self.entry.configure(state='normal', bg='#CC9999')
	self.draw.bind( "<1>", self.MoveCursor)
	self.draw.bind( "<B1-Motion>", self.MoveCursor)
	self.draw.bind( "<ButtonRelease>", self.MouseUp)
        
        
    def __init__(self, master=None, label=None, minval=0.0, maxval=100.0,
		 incr=None, init=None, width=150, height=20, withValue=1,
		 immediate=0, left=10, right=10, entrytext = None ,
                 textvariable=None, sd='top', labelformat = '%4.2f',
                 cursortype = 'float', onButton=0, lookup=None):
	self.entrytext = entrytext
	try:
		Slider.__init__(self, master, label, minval,maxval,
			incr, init, width, height, withValue, 
			immediate,left, right, labelformat, cursortype,
                        lookup )
	except ValueError:
		print "problem w/Slider.__init__"

        self.onButton = onButton
        if onButton:
            self.onTk = Tkinter.IntVar()
            self.onTk.set(1)
            self.entrylabel = Tkinter.Checkbutton(
                self.frame, text=self.entrytext, variable=self.onTk,
                command=self.on_cb)
            self.entrylabel.pack(side=sd, before=self.draw, anchor='w')
        else:
            self.entrylabel = Tkinter.Label(self.frame)
            self.entrylabel.pack(side=sd, before=self.draw, anchor='w')
            self.entrylabel.config(text=self.entrytext)
	self.entry = Tkinter.Entry(self.frame, width=4, bg='#CC9999')
	self.entry.pack(side=sd, after=self.draw)
        
        if textvariable:
            self.contents = textvariable
        else:
            self.contents = Tkinter.StringVar()
        if not init: init = minval   
        self.contents.set(init)

	self.entry.config(textvariable=self.contents)
	self.entry.bind('<Return>', self.setval)

   
    def setval(self, event):
	"""Bound to Button-1"""
	try:
		newx=float(self.contents.get())
		self._FixedMoveCursor(newx)
                self.Callbacks()

	except ValueError:
		print "numerical values only!"
		self.contents.set('')



if __name__ == '__main__':
    def MyCallback(color):
        print color

    def MyCallback2(color):
        print 'hello'

    exsl1 = ExtendedSlider(None, label='EntryLabel ', height=40,
                 minval=0.1, maxval = 10.0, init=5.0, sd='left')
    exsl1.frame.pack()
    exsl1.AddCallback(MyCallback)


