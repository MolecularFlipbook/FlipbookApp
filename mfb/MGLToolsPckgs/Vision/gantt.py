import Pmw, Tkinter
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

class Gantt:
    """
    Plot a simple Gant diagram for a list of tasks.
The task are specified as a list of (name, start, end) 3-tuples
"""

    def __init__(self, tasks, root=None):

        # create panel if needed
        if root is None:
            root = Tkinter.Toplevel()
            root.title("Execution profile")
            self.ownsMaster = True
        else:
            assert isinstance(root, Tkinter.Toplevel) or\
                   isinstance(root, Tkinter.Frame)
            self.ownsMaster = False
        self.root = root

        self.pixelsPersecond = 100
        self.yoff = 20
        self.scale = 1.0
        
        self.scrolledCanvas = Pmw.ScrolledCanvas(
            root, canvas_width=600, canvas_bg='white',
            vscrollmode='static', hscrollmode='static',
            horizscrollbar_width=10, vertscrollbar_width=10)
        self.canvas = self.scrolledCanvas.component('canvas')
        self.scrollregion=[0 , 0, 4000, 4000]
        self.canvas.configure(scrollregion=tuple(self.scrollregion))

        self.scrolledCanvas.pack(expand=True, fill='both')

        f = self.bframe = Tkinter.Frame(root)
        
        self.scaleTimeTW = ThumbWheel(
            f, showLabel=0, width=70, height=16, type=float, value=0,
            callback=self.setTimeScaleFactor_cb, continuous=True, oneTurn=10,
            wheelPad=2, reportDelta=True)
        self.scaleTimeTW.pack(side='right', anchor='e')

        f.pack(side='bottom', expand=0, fill='x')
        
        self.relativeData = []
        self.setTasks(tasks)
        

    def setTasks(self, tasks):
        self.relativeData = []

        if len(tasks)==0:
            return
        assert len(tasks)
        assert len(tasks[0])==3
        off = tasks[0][1]

        for node,t0,t1 in tasks:
            # name, start, length
            self.relativeData.append( (node.name, t0-off, t1-t0) )
        self.redraw()
        

    def setTimeScaleFactor_cb(self, value, event=None):
        self.scale = self.scale * (1.1)**value
        self.redraw()
        

    def redraw(self):
        pixelPerUnit = 30000 # use that many pixels to draw mini time

        cury = 20
        canvas = self.canvas
        canvas.delete("names")
        canvas.delete("lines")

        for name, start, length in self.relativeData:
            scale = self.scale
            x0 = 10 + scale*start*pixelPerUnit
            x1 = 10 + scale*(start+length)*pixelPerUnit
            canvas.create_text(x0, cury, text=name, anchor='sw',
                               tags=('names'), fill='magenta')
            canvas.create_line(x0, cury, x1, cury, width=3,
                               fill='black', tags=('lines',name))
            canvas.create_text(x0, cury+20, text='%.4f'%length, anchor='sw',
                               tags=('names'), fill='orange')
            cury += self.yoff

## net = self.networks['Network0']
## data = net.lastExecutedNodes
## g = Gantt(data)

## def updateExecutionProfile(net):
##     g.setTasks(net.lastExecutedNodes)

## net.afterRunCb = updateExecutionProfile
#execfile('gantt.py')
