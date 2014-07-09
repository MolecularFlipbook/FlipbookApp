## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Sophie Coon, Michel F. SANNER, Kevin CHAN
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/drawShape.py,v 1.2 2007/07/24 17:30:37 vareille Exp $
#
# $Id: drawShape.py,v 1.2 2007/07/24 17:30:37 vareille Exp $
#

import Tkinter, numpy.oldnumeric as Numeric
from DejaVu.IndexedPolygons import IndexedPolygons

class DrawShape:
    """ gui to allow user to draw an arbitrary shape and get points and normals
    for the shape. """

    def __init__(self, master, grid=10):
    
	self.root = Tkinter.Toplevel(master)

	# add a title
	self.title = Tkinter.Label(self.root,text='Draw a Shape')
        description = 'click left mouse button to set a point\n click right mouse button to stop drawing\n draw points clockwise'
        self.details = Tkinter.Label(self.root, text=description)
	self.title.pack(side='top', anchor='n')
        self.details.pack(side='bottom')

	self.f = Tkinter.Frame(self.root)
	self.c = Tkinter.Canvas(self.f, borderwidth = 3, relief='ridge')
	self.c.grid(column=4, rowspan=5)

	Tkinter.Widget.bind(self.c, "<Button-1>", self.mouseDown)
	Tkinter.Widget.bind(self.c, "<Button-3>", self.endShape)
	Tkinter.Widget.bind(self.c, "<Motion>", self.mouseMotion)
        self.hasFirstPoint = 0
        
	self.but=Tkinter.Button(self.f, text='clear',command=self.clear)
	self.but.grid(row=4, column=2)
	self.dup = Tkinter.IntVar()
        smooth = Tkinter.Radiobutton(self.f, text = 'smooth edges',
                                     var = self.dup, value = 0)
	sharp = Tkinter.Radiobutton(self.f, text = 'sharp edges',
                                    var = self.dup, value = 1)
	smooth.grid(row=0, columnspan=3)
        sharp.grid(row=1, columnspan=3)
        self.cap1 = Tkinter.IntVar()
        self.cap2 = Tkinter.IntVar()
        cap1 = Tkinter.Checkbutton(self.f, text = 'front cap', var = self.cap1)
        cap2 = Tkinter.Checkbutton(self.f, text = 'end cap', var = self.cap2)
        cap1.grid(row=2, columnspan=3)
        cap2.grid(row=3, columnspan=3)
        
        # list of points in contour
        self.shape = []
        self.end = 0
        
	# this is a "tagOrId" for the line we draw on the canvas
	self.rubberbandLine = None

	# this is the size of the gridding squares
	self.griddingSize = grid

        # how much 1 grid space is in real world
        self.gridToWorld = 0.1

	# build the OK Cancel buttons
	ok = Tkinter.Button(self.f, text='OK', command=self.OK_cb)
	cancel = Tkinter.Button(self.f, text='Cancel', command=self.Cancel_cb)
	cancel.grid(row=4, column=1)
	ok.grid(row=4, column=0)
	self.f.pack(side='bottom', anchor='s')

    def mouseDown(self, event):
	# canvas x and y take the screen coords from the event and translate
	# them into the coordinate system of the canvas object
	x = self.c.canvasx(event.x, self.griddingSize)
	y = self.c.canvasy(event.y, self.griddingSize)

        if len(self.shape)>0: # after first point
	    self.newline=self.c.create_line(self.shape[-1][0],
                                            self.shape[-1][1],
                                            x, y, tags='segment')
	self.shape.append((x,y))

        if self.rubberbandLine:
            self.c.delete(self.rubberbandLine)
        self.rubberbandLine = self.c.create_line(x, y, x, y, tags='rubber')

    def endShape(self, event):
        self.end = 1
        if self.rubberbandLine:
            self.c.delete(self.rubberbandLine)

    def mouseMotion(self, event):
	# canvas x and y take the screen coords from the event and translate
	# them into the coordinate system of the canvas object

        if len(self.shape)==0: return
        if self.end: return

	x = self.c.canvasx(event.x, self.griddingSize)
	y = self.c.canvasy(event.y, self.griddingSize)

	if (self.shape[-1][0] != event.x)  and (self.shape[-1][1] != event.y): 
	    self.c.delete(self.rubberbandLine)
	    self.rubberbandLine = self.c.create_line(
		self.shape[-1][0], self.shape[-1][1], x, y)
	    # this flushes the output, making sure that 
	    # the rectangle makes it to the screen 
	    # before the next event is handled
	    self.f.update_idletasks()

    def End(self):
        import math
       
        # center the points around the origin
        sca = (1.0/self.griddingSize)*self.gridToWorld
	points = Numeric.array(self.shape, 'f')* sca
	xsum, ysum = 0, 0
	if points:
            repeat = 0
            comp = points[-1]-points[0]
            if abs(comp[0])<.01 and abs(comp[1])<.01: repeat = -1
	    for i in range(len(points)+repeat):
		xsum = xsum + points[i][0]
		ysum = ysum + points[i][1]
	    xcenter = xsum/(len(points)+repeat)
	    ycenter = ysum/(len(points)+repeat)
	    origin = (xcenter, ycenter)
	    points = points - origin
	    points[:,1:] = points[:,1:]*-1

            # 3D
            o = Numeric.ones((len(points), 1))
            points = Numeric.concatenate((points, o), 1)

            # calculate normals to each side
            normals = Numeric.zeros((len(points)-1, 3), 'f')
            for i in range(len(points)-1):
                diff = points[i+1] - points[i]
                if diff[1]==0:
                    normals[i][0] = 0.0
                    normals[i][1] = diff[0]/abs(diff[0])
                else:
                    slope = -diff[0]/diff[1]
                    size = -math.sqrt(1+slope**2)*(diff[1]/abs(diff[1]))
                    normals[i][0] = 1.0/size
                    normals[i][1] = slope/size
            
            # duplicate vertices
	    if self.dup.get():
		pts = Numeric.concatenate((points, points), 1)
		self.points = Numeric.reshape(pts, (2*len(points), 3))
                norms1 = Numeric.concatenate((Numeric.reshape(normals[-1],
                                                             (1,3)),
                                             normals))
                norms2 = Numeric.concatenate((normals,
                                              Numeric.reshape(normals[0],
                                                              (1,3))))
                norms = Numeric.concatenate((norms1, norms2), 1)
                self.normals = Numeric.reshape(norms, (2*len(points), 3))
            # single vertices: average normals
	    else:
                self.points = points
                self.normals = Numeric.zeros((len(points), 3)).astype('f')
                for i in range(len(points)-1):
                    n = (normals[i-1]+normals[i])/2
                    self.normals[i] = n.astype('f')
                self.normals[len(points)-1] = self.normals[0]
	    print self.points
      	else: self.points, self.normals = [], []
	#now use points to make a polyline or polygon or whatever

    def OK_cb(self, event=None):
	"""call back for OK button"""
        if not hasattr(self, 'points'): self.End()
	if self.points: self.root.quit()

    def Cancel_cb(self):
	"""call back for Cancel button"""
	self.points = []
        self.normals = []
	self.root.quit()

    def clear(self):
	self.shape=[]
        self.end = 0
	self.pointindex=0
	self.c.delete(self.c.gettags('segment'))

    def go(self):
	"""start chooser in modal mode"""
	self.root.grab_set()
	self.root.mainloop()
	self.root.destroy()
	return self.points, self.normals, self.dup.get(), self.cap1.get(),\
               self.cap2.get()

if __name__ =='__main__':
    import pdb
    root=Tkinter.Tk()
    myDraw=DrawShape(root)
    val = myDraw.go()
