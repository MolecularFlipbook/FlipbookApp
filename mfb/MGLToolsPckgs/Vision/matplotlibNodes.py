## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Dec 2004 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, and TSRI
#
#########################################################################

# latest working version of matplotlib is 0.87.7 using numpy 1.0.3
# latest working version of matplotlib is 0.87.6 using Numeric 23.8
# (matplotlib 0.87.7 has a small bug using Numeric 23.8)
# there are multiple bugs in matplotlib when using Numeric 24.2

#TODO:
# - add and verify controls such as size, labels, legends etc
# - maybe encapsulate all these common options into a single node
# - alpha values per axis
# - use axes rather than subplot
#

try:
    import matplotlib
except:
    import warnings
    import sys
    if sys.platform == 'linux2':
        warnings.warn("""to use matplotlib, you need first to install openssl
the mgltools 32 bit linux binaries need openssl version 0.9.7
the mgltools 64 bit linux binaries need openssl version 0.9.8
you can have both openssl versions (0.9.7 and 0.9.8) installed on your computer.
""", stacklevel=2)
        
import Tkinter
import types
import weakref
import Pmw,math,os, sys

from numpy.oldnumeric import array
from matplotlib.colors import cnames
from matplotlib.lines import Line2D,lineStyles,TICKLEFT, TICKRIGHT, TICKUP, TICKDOWN
#from matplotlib.transforms import Value
from matplotlib import rcParams

#mplversion = int(matplotlib.__version__.split(".")[2])
mplversion = map(int, matplotlib.__version__.split("."))
#print "mplversion:", mplversion


"""
This module implements Vision nodes exposing matplotlib functionatility.

MPLBaseNE:
---------
The class provides a base class for all nodes exposing matplotlib functionality

its purpose is to to create the attributes described below and implement
methods shared by all nodes.

Attributes:
    self.figure = None:  # node's figure object
    # This attribute always points to the matplotlib Figure object which has
    # a FigureCanvasTkAgg object in its .canvas attribute

    # self.canvas FigureCanvasTkAgg

    self.axes = None
    # This attribute points to the matplotlib Axes instance used by this node

    self.axes.figure # figure in which the axes is currently drawn

Methods:        
    def createFigure(self, master=None, width=None, height=None, dpi=None,
                     facecolor=None, edgecolor=None, frameon=None,
                     packOpts=None, toolbar=True):

    # This method is used by all nodes if they need to create a Figure object
    # from the matplotlib library and a FigureCanvasTkAgg object for this
    # figure.

    def setFigure(self, figure):
    # This method place the node's axes object into the right Figure
	   

    def beforeRemovingFromNetwork(self):
    # this method is called when a node is deleted from a network.  Its job is
    # to delete FigureCanvasTkAgg and Axes when appropriate.
    

MPLFigure:
-----------
The MPLFigure node allows the creation of a plotting area in which one
or more Axes can be added, where an Axes is a 2D graphical representation
of a data set (i.e. 2D plot).  A 'master' can be apecified to embed the figure
in other panels.  This node provides control over parameter that apply to the
MPLFigure such, width, height, dpi, etc.


Plotting Node:
-------------
Plotting nodes such as Histogram, Plot, Scatter, Pie, etc. take adtasets and
render them as 2D plots.  They alwas own the axes.
If the data to be rendered is the only input to these nodes, they will create
a default Figure, add a default Plot2D to this figure, and draw the data in
this default 2D plot.
"""

from mglutil.util.callback import CallBackFunction
from NetworkEditor.widgets import TkPortWidget, PortWidget
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from Vision import UserLibBuild
from NetworkEditor.items import NetworkNode

# make sure Tk is used as a backend
if not 'matplotlib.backends' in sys.modules:
    matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
from matplotlib.figure import Figure as OriginalFigure
from matplotlib.axes import Axes, Subplot #, PolarSubplot, PolarAxes
from matplotlib.pylab import *
from Vision.colours import get_colours
from Vision.posnegFill import posNegFill
import numpy
from matplotlib.artist import setp
##
##  QUESTIONS
##  Does this have to be Tk specific or could I use FigureCanvasAgg
##  !FigureCanvasAgg is OK

##  Should I use FigureManagerBase rather than FigureCanvasAgg ?
##  ! FigureCanvas Agg is OK

##  how to destroy a figure ?
##  ! seems to work

##  figure should have a set_dpi method
##  ! use figure.dpi.set() for now but might become API later

##  how to remove the tool bar ?
##  ! John added a note about this

##  What option in a Figure can beset without destroying the Figure
##    and which ones are constructor only options ?
##  ! nothing should require rebuilding a Figure

##  Why does add_axes return the axis that already exists if the values for
##    building the Axes object are the same ? either this has to change or
##    adding an instance of an Axes should be fixed (prefered)
##  !John made a note to add an argument to matplotlib

##  Pie seems to have a problem when shadow is on !
##  !Find out the problem, because shadows are on even when check button is off
##  !for ce aspect ratio to square

##  Plot lineStyle, color, linewidth etc should be set by a set node that uses
##    introspection on the patch? to find otu what can be set ??
## !Use ObjectInspector

## why is figimage not an axes method ?
## !use imshow

from matplotlib.cbook import iterable
try:
    from matplotlib.dates import DayLocator, HourLocator, \
         drange, date2num
    from pytz import timezone
except:
    pass

try:
    from pytz import common_timezones
except:
    common_timezones=[]
#global variables
locations={'best' : 0,
          'upper right'  : 1, 
          'upper left'   : 2,
          'lower left'   : 3,
          'lower right'  : 4,
          'right'        : 5,
          'center left'  : 6,
          'center right' : 7,
          'lower center' : 8,
          'upper center' : 9,
          'center'       : 10,}
colors={
        'blue' : 'b',
        'green' : 'g',
        'red' : 'r',
        'cyan' : 'c',
        'magenta' :'m',
        'yellow' :'y',
        'black': 'k',
        'white' : 'w',
        }          

markers= {
		'square'         :  's',
		'circle'	 :  'o',
		'triangle up'    :  '^',
		'triangle right' :  '>',
		'triangle down'  :  'v',
		'triangle left'  :  '<',
		'diamond'	 :  'd',
		'pentagram'	 :  'p',
		'hexagon'	 :  'h',
		'octagon'	 :  '8',
		}
 
cmaps=['autumn','bone', 'cool','copper','flag','gray','hot','hsv','jet','pink', 'prism', 'spring', 'summer', 'winter']

def get_styles():
    styles={}
    for ls in Line2D._lineStyles.keys():
        styles[Line2D._lineStyles[ls][6:]]=ls
        for ls in Line2D._markers.keys():
            styles[Line2D._markers[ls][6:]]=ls
	        #these styles are not recognized
            if styles.has_key('steps'):
                del styles['steps']
            for s in  styles.keys():
                if s =="nothing":
                    del styles['nothing']
                if s[:4]=='tick':
                    del styles[s]
    return styles           

class Figure(OriginalFigure):

    # sub class Figure to override add_axes
    def add_axes(self, *args, **kwargs):
	"""hack to circumvent the issue of not adding an axes if the constructor
params have already been seen"""
        
        if kwargs.has_key('force'):
	    force = kwargs['force']
	    del kwargs['force']
        else:
	    force = False

	if iterable(args[0]):
	    key = tuple(args[0]), tuple(kwargs.items())
        else:
	    key = args[0], tuple(kwargs.items())            
	    
	if not force and self._seen.has_key(key):
	    ax = self._seen[key]
	    self.sca(ax)
	    return ax

        if not len(args): return        
	if isinstance(args[0], Axes):
	    a = args[0]
	    # this is too early, if done here bbox is 0->1
	    #a.set_figure(self)
	    a.figure = self
        else:
	    rect = args[0]
	    #ispolar = popd(kwargs, 'polar', False)
            ispolar = kwargs.get('polar', False)
            if ispolar != False:
                del kwargs['polar']
	    if ispolar:
	        a = PolarAxes(self, rect, **kwargs)
	    else:
                a = Axes(self, rect, **kwargs)            

	self.axes.append(a)
	self._axstack.push(a)
	self.sca(a)
	self._seen[key] = a
	return a



class MPLBaseNE(NetworkNode):
    """Base class for node wrapping the maptlotlib objects

"""
    def __init__(self, name='MPLBase', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.figure = None  # matplotlib Figure instance belonging to this node
        self.axes = None    # matplotlib Axes instance

	# this is true for Figures who create the Tk Toplevel
	# or plotting nodes that have no figure parent node
	# it is used to decide when the Toplevel should be destroyed
        self.ownsMaster = False


    def setDrawArea(self, kw):
        ax = self.axes
        #ax.clear()
        if kw.has_key('left'):
            rect = [kw['left'], kw['bottom'], kw['width'], kw['height']]
            ax.set_position(rect)
        if kw.has_key('frameon'):    
            ax.set_frame_on(kw['frameon'])

        if kw.has_key("title"):    
            if type(kw['title'])==types.StringType:
                ax.set_title(kw['title'])
            else:
                print 'Set title as Object'
        if kw.has_key("xlabel"):        
            ax.set_xlabel(kw['xlabel'])
        if kw.has_key("ylabel"):    
            ax.set_ylabel(kw['ylabel'])
        if kw.has_key("xlimit"): 
            if kw['xlimit']!='':
                ax.set_xlim(eval(kw['xlimit']))
        if kw.has_key("ylimit"):    
            if kw['ylimit']!='':
                ax.set_ylim(eval(kw['ylimit']))
        if kw.has_key("xticklabels"):        
            if not kw['xticklabels']:
                ax.set_xticklabels([])
        if kw.has_key("yticklabels"):    
            if not kw['yticklabels']:
                ax.set_yticklabels([])
        if kw.has_key("axison"):
            if kw['axison']:
                ax.set_axis_on()
            else:
                ax.set_axis_off()	
        if kw.has_key("autoscaleon"):
            if kw['autoscaleon']:
                ax.set_autoscale_on(True)
            else:
                ax.set_autoscale_on(False)
        if kw.has_key("adjustable"):
            ax.set_adjustable(kw['adjustable'])
        if kw.has_key("aspect"):
            ax.set_aspect(kw['aspect'])
        if kw.has_key("anchor"):
            ax.set_anchor(kw['anchor'])
            
        if kw.has_key("axisbelow"):
            if kw['axisbelow']==1:
               val=True
            else:
               val=False
            rcParams['axes.axisbelow']=val
            ax.set_axisbelow(val)
        #grid properties
        if kw.has_key("gridOn"):
            if kw['gridOn']==1:
                ax._gridOn=True
                val=True
                if kw.has_key('gridcolor'):
                    gcolor=kw['gridcolor']
                else:
                    gcolor=rcParams['grid.color']
                if  kw.has_key('gridlinestyle'):
                    glinestyle=kw['gridlinestyle']
                else:
                    glinestyle=rcParams['grid.linestyle']
                if  kw.has_key('gridlinewidth'):
                    glinewidth=kw['gridlinewidth']
                else:
                    glinewidth=rcParams['grid.linewidth']
                if kw.has_key('whichgrid'):
                    whichgrid=kw['whichgrid']
                else:
                    whichgrid='major'
                ax.grid(val,color=gcolor, linestyle=glinestyle, linewidth=glinewidth,which=whichgrid)
        else:
            val=False
            ax.grid(val)
          
        if kw.has_key("facecolor"):
            ax.set_axis_bgcolor(kw['facecolor'])
        if kw.has_key("edgecolor"):
            if hasattr(ax, "axesFrame"):
                ax.axesFrame.set_edgecolor(kw['edgecolor'])
            elif hasattr(ax, "axesPatch"):
                ax.axesPatch.set_edgecolor(kw['edgecolor'])
#        if kw.has_key('zoomx'):
#            #Zoom in on the x xaxis numsteps (plus for zoom in, minus for zoom out)
#            ax.zoomx(kw['zoomx'])
#            
#        if kw.has_key('zoomy'):
#            #Zoom in on the x xaxis numsteps (plus for zoom in, minus for zoom out)
#            ax.zoomy(kw['zoomy'])
             
        if kw.has_key("xtick.color"):
                for i in ax.xaxis.get_ticklabels():
                    i.set_color(kw['xtick.color'])    
        if kw.has_key("ytick.color"):        
            for i in ax.yaxis.get_ticklabels():
                    i.set_color(kw['ytick.color'])
	    
        if kw.has_key('xtick.labelrotation'):
            for i in ax.xaxis.get_ticklabels():
                    i.set_rotation(float(kw['xtick.labelrotation']))    
        if kw.has_key('ytick.labelrotation'):
            for i in ax.yaxis.get_ticklabels():
                    i.set_rotation(float(kw['ytick.labelrotation']))
        if kw.has_key("xtick.labelsize"):
           for i in ax.xaxis.get_ticklabels():
                    i.set_size(float(kw['xtick.labelsize']))
        if kw.has_key("ytick.labelsize"):    
            for i in ax.yaxis.get_ticklabels():
                    i.set_size(float(kw['ytick.labelsize']))
        if kw.has_key("linewidth"):
            if hasattr(ax, "axesFrame"):
                ax.axesFrame.set_linewidth(float(kw['linewidth']))
            elif hasattr(ax, "axesPatch"):
                ax.axesPatch.set_linewidth(float(kw['linewidth']))
                    
        #marker
        if  kw.has_key("markeredgewidth"):
            for i in ax.get_xticklines():
                i.set_markeredgewidth(kw['markeredgewidth'])
            for i in ax.get_yticklines():
                i.set_markeredgewidth(kw['markeredgewidth'])
            
        if kw.has_key("markeredgecolor"):
            for i in ax.get_xticklines():
                i.set_markeredgecolor(kw['markeredgecolor'])
            for i in ax.get_yticklines():
                i.set_markeredgecolor(kw['markeredgecolor'])
            
        if kw.has_key("markerfacecolor"):
            for i in ax.get_xticklines():
                i.set_markerfacecolor(kw['markerfacecolor'])
            for i in ax.get_yticklines():
                i.set_markerfacecolor(kw['markerfacecolor'])
            
        #figure_patch properties 
        if  kw.has_key("figpatch_linewidth"):
            ax.figure.figurePatch.set_linewidth(kw['figpatch_linewidth'])
        if kw.has_key("figpatch_facecolor"):    
            ax.figure.figurePatch.set_facecolor(kw['figpatch_facecolor'])
        if kw.has_key("figpatch_edgecolor"):    
            ax.figure.figurePatch.set_edgecolor(kw['figpatch_edgecolor'])
        if kw.has_key("figpatch_antialiased"):    
            ax.figure.figurePatch.set_antialiased(kw['figpatch_antialiased'])    
        
        #Text properties
        if kw.has_key('text'):
            for i in kw['text']:
              if type(i)==types.DictType:  
                tlab=i['textlabel']
                posx=i['posx']
                posy=i['posy']
                horizontalalignment=i['horizontalalignment']
                verticalalignment=i['verticalalignment']
                rotation=i['rotation']
                ax.text(x=posx,y=posy,s=tlab,horizontalalignment=horizontalalignment,verticalalignment=verticalalignment,rotation=rotation,transform = ax.transAxes)
        if kw.has_key("text.color"):
            for t in ax.texts:
                t.set_color(kw['text.color'])
        if kw.has_key("text.usetex"):
            rcParams['text.usetex']=kw['text.usetex']
        if kw.has_key("text.dvipnghack"):
            rcParams['text.dvipnghack']=kw['text.dvipnghack']
        if kw.has_key("text.fontstyle"):
            for t in ax.texts:
                t.set_fontstyle(kw['text.fontstyle'])
        if kw.has_key("text.fontangle"):
            for t in ax.texts:
                t.set_fontangle(kw['text.fontangle'])
        if kw.has_key("text.fontvariant"):
            for t in ax.texts:
                t.set_fontvariant(kw['text.fontvariant'])
        if kw.has_key("text.fontweight"):
            for t in ax.texts:
                t.set_fontweight(kw['text.fontweight'])
        if kw.has_key("text.fontsize"):
            for t in ax.texts:
                t.set_fontsize(kw['text.fontsize'])
            
        #Font
        if kw.has_key("Font.fontfamily"):
            for t in ax.texts:
                t.set_family(kw['Font.fontfamily'])
        if kw.has_key("Font.fontstyle"):
            for t in ax.texts:
                t.set_fontstyle(kw['Font.fontstyle'])
        if kw.has_key("Font.fontangle"):
            for t in ax.texts:
                t.set_fontangle(kw['Font.fontangle'])
        if kw.has_key("Font.fontvariant"):
            for t in ax.texts:
                t.set_fontvariant(kw['Font.fontvariant'])
        if kw.has_key("Font.fontweight"):
            for t in ax.texts:
                t.set_fontweight(kw['Font.fontweight'])
        if kw.has_key("Font.fontsize"):
            for t in ax.texts:
                t.set_fontsize(kw['Font.fontsize'])
        
        #Legend Properties
        
        if mplversion[0]==0 and mplversion[2]<=3 :
            if kw.has_key('legendlabel'):
                if ',' in kw['legendlabel']:
                    x=kw['legendlabel'].split(",")
                else:
                    x=(kw['legendlabel'],)
                if kw.has_key('legend.isaxes'):
                    isaxes=kw['legend.isaxes']
                else:    
                    isaxes=rcParams['legend.isaxes']

                if kw.has_key('legend.numpoints'):
                    numpoints=kw['legend.numpoints']
                else:    
                    numpoints=rcParams['legend.numpoints'] 

                if kw.has_key('legend.pad'):
                    borderpad=kw['legend.pad']
                else:    
                    borderpad=rcParams['legend.pad'] 

                if kw.has_key('legend.markerscale'):
                    markerscale=kw['legend.markerscale']
                else:
                    markerscale=rcParams['legend.markerscale']
                if kw.has_key('legend.labelsep'):
                    labelspacing=kw['legend.labelsep']
                else:    
                    labelspacing=rcParams['legend.labelsep']
                if kw.has_key('legend.handlelen'):
                    handlelength=kw['legend.handlelen']
                else:    
                    handlelength=rcParams['legend.handlelen']
                if kw.has_key('legend.handletextsep'):
                    handletextpad=kw['legend.handletextsep']
                else:    
                    handletextpad=rcParams['legend.handletextsep'] 
                if kw.has_key('legend.axespad'):
                    borderaxespad=kw['legend.axespad']
                else:    
                    borderaxespad=rcParams['legend.axespad']
                if kw.has_key('legend.shadow'):
                    shadow=kw['legend.shadow']
                else:    
                    shadow=rcParams['legend.shadow']
                #import pdb;pdb.set_trace()
                leg=self.axes.legend(tuple(x),loc=kw['legendlocation'],
                                     #isaxes=isaxes,
                                     numpoints=numpoints,
                                     pad=borderpad,
                                     labelsep=labelspacing,
                                     handlelen=handlelength,
                                     handletextsep=handletextpad,
                                     axespad=borderaxespad,
                                     shadow=shadow,
                                     markerscale=markerscale)
                if kw.has_key('legend.fontsize'):
                   setp(ax.get_legend().get_texts(),fontsize=kw['legend.fontsize'])
        elif mplversion[0] > 0:
            if kw.has_key('legendlabel'):
                if ',' in kw['legendlabel']:
                    x=kw['legendlabel'].split(",")
                else:
                    x=(kw['legendlabel'],)
                if kw.has_key('legend.isaxes'):
                    isaxes=kw['legend.isaxes']
                else:    
                    isaxes=rcParams['legend.isaxes']

                if kw.has_key('legend.numpoints'):
                    numpoints=kw['legend.numpoints']
                else:    
                    numpoints=rcParams['legend.numpoints'] 

                if kw.has_key('legend.borderpad'):
                    borderpad=kw['legend.borderpad']
                else:    
                    borderpad=rcParams['legend.borderpad'] 

                if kw.has_key('legend.markerscale'):
                    markerscale=kw['legend.markerscale']
                else:
                    markerscale=rcParams['legend.markerscale']
                if kw.has_key('legend.labelspacing'):
                    labelspacing=kw['legend.labelspacing']
                else:    
                    labelspacing=rcParams['legend.labelspacing']
                if kw.has_key('legend.handlelength'):
                    handlelength=kw['legend.handlelength']
                else:    
                    handlelength=rcParams['legend.handlelength']
                if kw.has_key('legend.handletextpad'):
                    handletextpad=kw['legend.handletextpad']
                else:    
                    handletextpad=rcParams['legend.handletextpad'] 
                if kw.has_key('legend.borderaxespad'):
                    borderaxespad=kw['legend.borderaxespad']
                else:    
                    borderaxespad=rcParams['legend.borderaxespad']
                if kw.has_key('legend.shadow'):
                    shadow=kw['legend.shadow']
                else:    
                    shadow=rcParams['legend.shadow']
                #import pdb;pdb.set_trace()
                leg=self.axes.legend(tuple(x),loc=kw['legendlocation'],
                                     #isaxes=isaxes,
                                     numpoints=numpoints,
                                     borderpad=borderpad,
                                     labelspacing=labelspacing,
                                     handlelength=handlelength,
                                     handletextpad=handletextpad,
                                     borderaxespad=borderaxespad,
                                     shadow=shadow,
                                     markerscale=markerscale)
                if kw.has_key('legend.fontsize'):
                   setp(ax.get_legend().get_texts(),fontsize=kw['legend.fontsize'])

        #Tick Options
        if kw.has_key('xtick.major.pad'):
            for i in ax.xaxis.majorTicks:
                i.set_pad(kw['xtick.major.pad'])
        if kw.has_key('xtick.minor.pad'):
            for i in ax.xaxis.minorTicks:
                i.set_pad(kw['xtick.minor.pad'])
        if kw.has_key('ytick.major.pad'):
            for i in ax.yaxis.majorTicks:
                i.set_pad(kw['ytick.major.pad'])
        if kw.has_key('ytick.minor.pad'):
            for i in ax.yaxis.minorTicks:
                i.set_pad(kw['ytick.minor.pad'])        
        if kw.has_key('xtick.major.size'):
            rcParams['xtick.major.size']=kw['xtick.major.size']
        if kw.has_key('xtick.minor.size'):
            rcParams['xtick.minor.size']=kw['xtick.minor.size']
        if kw.has_key('xtick.direction'):
           rcParams['xtick.direction']=kw['xtick.direction']
        if kw.has_key('ytick.major.size'):
            rcParams['ytick.major.size']=kw['ytick.major.size']    
        if kw.has_key('ytick.minor.size'):
            rcParams['ytick.minor.size']=kw['ytick.minor.size']
        if kw.has_key('ytick.direction'):
            rcParams['ytick.direction']=kw['ytick.direction']  
             
        
            
    def beforeRemovingFromNetwork(self):
        #print 'remove'
        NetworkNode.beforeRemovingFromNetwork(self)
	# this happens for drawing nodes with no axes specified
	if self.axes:
                
                self.axes.figure.delaxes(self.axes) # feel a little strange !
                self.canvas._tkcanvas.master.destroy()
        elif self.canvas:
            self.canvas._tkcanvas.master.destroy()


    def onlyDataChanged(self, data):
        """returns true if only he first port (i.e. data) has new data.
"""
	# This can be used to accelerate redraw by only updating the data
	# rather than redrawing the whole figure
	# see examples/animation_blit_tk.py
        ports = self.inputPorts
	if not ports[0].hasNewValidData():
	    return False
        for p in self.inputPorts:
	    if p.hasNewValidData():
	        return False

	return True



class MPLFigureNE(MPLBaseNE):
    """This node instanciates a Figure object and its FigureCanvasTkAgg object
in its .canvas attribute.
It also provide control over parameters such as width, height, dpi, etc.

Input:
    plots     - Matplotlib Axes objects
    figwidth  - width in inches
    figheigh  - height in inches
    dpi       - resolution; defaults to rc figure.dpi
    facecolor - the background color; defaults to rc figure.facecolor
    edgecolor - the border color; defaults to rc figure.edgecolor
    master    - Defaults to None, creating a topLevel
    nbRows    - number of rows for subgraph2D
    nbColumns - number of columns for subgraph2D
    frameon   - boolean
    hold      - boolean
    toolbar   - boolean (init option only)
    packOpts  - string representation of packing options

Output:
    canvas:  MPLFigure Object

Todo:
    legend
    text
    image ?
"""

    def afterAddingToNetwork(self):
        self.figure = Figure()

        master = Tkinter.Toplevel()
        master.title(self.name)
        self.canvas = FigureCanvasTkAgg(self.figure, master)
        self.figure.set_canvas(self.canvas)

        packOptsDict = {'side':'top', 'fill':'both', 'expand':1}
        self.canvas.get_tk_widget().pack( *(), **packOptsDict )

        toolbar = NavigationToolbar2TkAgg(self.canvas, master)
        

    def __init__(self, name='Figure2', **kw):
        kw['name'] = name
        apply( MPLBaseNE.__init__, (self,), kw )

        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    node1 = c.port1.node
    node2 = c.port2.node
    if node2.figure.axes:
        node2.figure.delaxes(node1.axes)
    if node1.figure.axes:    
        node1.figure.delaxes(node1.axes)
    node1.figure.add_axes(node1.axes)
"""
        ip = self.inputPortsDescr
        ip.append(datatype='MPLAxes', required=False, name='plots',
                  singleConnection=False,
                  beforeDisconnect=codeBeforeDisconnect)
        ip.append(datatype='float', required=False, name='width')
        ip.append(datatype='float', required=False, name='height')
        ip.append(datatype='float', required=False, name='linewidth', defaultValue=1)
        ip.append(datatype='int', required=False, name='dpi')
        ip.append(datatype='colorRGB', required=False, name='facecolor')
        ip.append(datatype='colorRGB', required=False, name='edgecolor')
        ip.append(datatype='None', required=False, name='master')
        ip.append(datatype='int', required=False, name='nbRows')
        ip.append(datatype='int', required=False, name='nbColumns')
        ip.append(datatype='boolean', required=False, name='frameon', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='hold', defaultValue=False)
        ip.append(datatype='boolean', required=False, name='toolbar')
        ip.append(datatype='None', required=False, name='packOpts')

	op = self.outputPortsDescr
        op.append(datatype='MPLFigure', name='figure')

        self.widgetDescr['width'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':8.125,
            'labelCfg':{'text':'width in inches'} }

        self.widgetDescr['height'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':6.125,
            'labelCfg':{'text':'height in inches'} }

        self.widgetDescr['linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':2, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'linewidth'} }

        self.widgetDescr['dpi'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':10, 'type':'int',
            'wheelPad':2, 'initialValue':80,
            'labelCfg':{'text':'DPI'} }

        self.widgetDescr['nbRows'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':10, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'nb. rows'} }

        self.widgetDescr['nbColumns'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':10, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'nb. col'} }

        self.widgetDescr['frameon'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':1, 'labelCfg':{'text':'frame'} }

        self.widgetDescr['hold'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':0, 'labelCfg':{'text':'hold'} }

        self.widgetDescr['toolbar'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':1, 'labelCfg':{'text':'toolbar'} }

        self.widgetDescr['packOpts'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'packing Opts.:'},
            'initialValue':'{"side":"top", "fill":"both", "expand":1}'}

        code = """def doit(self, plots, width, height, linewidth, dpi, facecolor,
edgecolor, master, nbRows, nbColumns, frameon, hold, toolbar, packOpts):

    self.figure.clear()
    if plots is not None:
        for p in plots:
            self.figure.add_axes(p)

    figure = self.figure
    # configure size
    if width is not None or height is not None:
        defaults = matplotlib.rcParams

        if width is None:
            width = defaults['figure.figsize'][0]
        elif height is None:
            height = defaults['figure.figsize'][1]

    figure.set_size_inches(width,height)

    # configure dpi
    if dpi is not None:
        figure.set_dpi(dpi)

    # configure facecolor
    if facecolor is not None:
        figure.set_facecolor(facecolor)

    # configure edgecolor
    if edgecolor is not None:
        figure.set_edgecolor(facecolor)

    # configure frameon
    if edgecolor is not None:
        figure.set_edgecolor(facecolor)

    # not sure linewidth is doing anything here
    figure.figurePatch.set_linewidth(linewidth)
    figure.hold(hold)

    # FIXME for now we store this here but we might want to add this as
    # regular attributes to Figure which would be used with subplot
    #figure.nbRows = nbRows
    #figure.nbColumns = nbColumns

    self.canvas.draw()
    
    self.outputData(figure=self.figure)
"""
        self.setFunction(code)

class MPLImageNE(MPLBaseNE):
    """This node creates a PIL image

Input:
    plots     - Matplotlib Axes objects
    figwidth  - width in inches
    figheigh  - height in inches
    dpi       - resolution; defaults to rc figure.dpi
    facecolor - the background color; defaults to rc figure.facecolor
    edgecolor - the border color; defaults to rc figure.edgecolor
    faceAlpha - alpha value of background
    edgeAlpha - alpha value of edge
    frameon   - boolean
    hold      - boolean
    toolbar   - boolean (init option only)
    packOpts  - string representation of packing options

Output:
    canvas:  MPLFigure Object

Todo:
    legend
    text
    image ?
"""

    def __init__(self, name='imageFigure', **kw):
        kw['name'] = name
        apply( MPLBaseNE.__init__, (self,), kw )

        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    node1 = c.port1.node
    node2 = c.port2.node
    if node1.figure.axes:
        node1.figure.delaxes(node1.axes)
    node1.figure.add_axes(node1.axes)
"""
        ip = self.inputPortsDescr
        ip.append(datatype='MPLAxes', required=False, name='plots',
                  singleConnection=False,
                  beforeDisconnect=codeBeforeDisconnect)
        ip.append(datatype='float', required=False, name='width')
        ip.append(datatype='float', required=False, name='height')
        ip.append(datatype='int', required=False, name='dpi')
        ip.append(datatype='colorsRGB', required=False, name='facecolor')
        ip.append(datatype='colorsRGB', required=False, name='edgecolor')
        ip.append(datatype='float', required=False, name='alphaFace', defaultValue=0.5)
        ip.append(datatype='float', required=False, name='alphaEdge', defaultValue=0.5)
        ip.append(datatype='boolean', required=False, name='frameon', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='hold', defaultValue=False)

        op = self.outputPortsDescr
        op.append(datatype='image', name='image')

        self.widgetDescr['width'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':6.4,
            'labelCfg':{'text':'width in inches'} }

        self.widgetDescr['height'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':4.8,
            'labelCfg':{'text':'height in inches'} }

        self.widgetDescr['dpi'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':10, 'type':'int',
            'wheelPad':2, 'initialValue':80,
            'labelCfg':{'text':'DPI'} }

        self.widgetDescr['alphaFace'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'wheelPad':2, 'initialValue':0.5, 'min':0.0, 'max':1.0,
            'labelCfg':{'text':'alpha Face'} }

        self.widgetDescr['alphaEdge'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'wheelPad':2, 'initialValue':0.5, 'min':0.0, 'max':1.0,
            'labelCfg':{'text':'alphaEdge'} }

        self.widgetDescr['frameon'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':1, 'labelCfg':{'text':'frame'} }

        self.widgetDescr['hold'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':0, 'labelCfg':{'text':'hold'} }

        code = """def doit(self, plots, width, height, dpi, facecolor, edgecolor,
alphaFace, alphaEdge, frameon, hold):
    figure = self.figure
    try:
       self.canvas.renderer.clear()
    except AttributeError:
        pass
    figure.clear()
   
    # Powers of 2 image to be clean
    if width>height:
        htc = float(height)/width
        w = 512
        h = int(round(512*htc))
    else:
        wtc = float(width)/height
        w = int(round(512*wtc))
        h = 512
    
    figure.set_size_inches(float(w)/dpi, float(h)/dpi)
    
    for p in plots:
        if hasattr(p,"figure"):
            p.figure.set_figwidth(float(w) / dpi)
            p.figure.set_figheight(float(h) / dpi)
            figure.add_axes(p)
            p.set_figure(figure)
            p.axesPatch.set_alpha(alphaFace)

    # configure dpi
    if dpi is not None:
        figure.set_dpi(dpi)

    # configure facecolor
    if facecolor is not None:
        figure.set_facecolor(tuple(facecolor[0]))

    # configure edgecolor
    if edgecolor is not None:
        figure.set_edgecolor(tuple(edgecolor[0]))

    # configure frameon
    if frameon is not None:
        figure.set_frameon(frameon)

    figure.hold(hold)

    figure.figurePatch.set_alpha(alphaEdge)
    self.canvas.draw() # force a draw

    import Image
    im = self.canvas.buffer_rgba(0,0)
    ima = Image.frombuffer("RGBA", (w, h), im)
    ima = ima.transpose(Image.FLIP_TOP_BOTTOM)

    self.outputData(image=ima)
"""
        self.setFunction(code)


    def beforeRemovingFromNetwork(self):
        #print 'remove'
        NetworkNode.beforeRemovingFromNetwork(self)
        # this happens for drawing nodes with no axes specified
        if self.axes:
            self.axes.figure.delaxes(self.axes) # feel a little strange !
            
    def afterAddingToNetwork(self):
        self.figure = Figure()
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        self.canvas = FigureCanvasAgg(self.figure)



class MPLDrawAreaNE(NetworkNode):
    """Class for configuring the axes.
    The following options can be set.
    left,bottom,width,height ----allows to set the position of the axes.
    frame on/off --- allows to on or off frame
    hold on/off --- allows to on or off hold.When hold is True, subsequent plot commands will be added to
                    the current axes.  When hold is False, the current axes and figure will be cleared on
                    the next plot command
    title --- allows to set title of the figure
    xlabel  ---allows to set xlabel of the figure
    ylabel ---allows to set ylabel of the figure
    xlimit --- set autoscale off before setting xlimit.
    y limit --- set autoscale off before setting  ylimit.
    xticklabels on/off --- allows to on or off  xticklabels
    yticklabels on/off --- allows to on or off  yticklabels
    axis on/off        --- allows to on or off  axis
    autoscale on/off ---   when on sets default axes limits ,when off sets limit from xlimit and ylimit  entries.
    """

    def __init__(self, name='Draw Area', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='left', defaultValue=.1)
        ip.append(datatype='float', required=False, name='bottom', defaultValue=.1)
        ip.append(datatype='float', required=False, name='width', defaultValue=.8)
        ip.append(datatype='float', required=False, name='height', defaultValue=.8)
        ip.append(datatype='boolean', required=False, name='frameon', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='hold', defaultValue=False)
        ip.append(datatype='string', required=False, name='title', defaultValue='Figure')
        ip.append(datatype='string', required=False, name='xlabel', defaultValue='X')
        ip.append(datatype='string', required=False, name='ylabel', defaultValue='Y')
        ip.append(datatype='string', required=False, name='xlimit', defaultValue='')
        ip.append(datatype='string', required=False, name='ylimit', defaultValue='')
        ip.append(datatype='boolean', required=False, name='xticklabels', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='yticklabels', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='axison', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='autoscaleon', defaultValue=True)
        self.widgetDescr['left'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.1,
            'labelCfg':{'text':'left (0. to 1.)'} }

        self.widgetDescr['bottom'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.1,
            'labelCfg':{'text':'bottom (0. to 1.)'} }

        self.widgetDescr['width'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.8,
            'labelCfg':{'text':'width (0. to 1.)'} }

        self.widgetDescr['height'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.8,
            'labelCfg':{'text':'height (0. to 1.0)'} }

        self.widgetDescr['frameon'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelGridCfg':{'sticky':'w'},
            'initialValue':1, 'labelCfg':{'text':'frame'} }

        self.widgetDescr['hold'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelGridCfg':{'sticky':'w'},
            'initialValue':0, 'labelCfg':{'text':'hold'} }

        self.widgetDescr['title'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'title'},'labelGridCfg':{'sticky':'w'},
            'initialValue':'Figure:'}

        self.widgetDescr['xlabel'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'X label'},'labelGridCfg':{'sticky':'w'},
            'initialValue':'X'}

        self.widgetDescr['ylabel'] = {
            'class':'NEEntry', 'master':'ParamPanel','labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Y label'},
            'initialValue':'Y'}

        self.widgetDescr['xlimit'] = {
            'class':'NEEntry', 'master':'ParamPanel','labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'X limit'},
            'initialValue':''}

        self.widgetDescr['ylimit'] = {
            'class':'NEEntry', 'master':'ParamPanel','labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Y limit'},
            'initialValue':''}
            
        self.widgetDescr['xticklabels'] = {
         'class':'NECheckButton', 'master':'ParamPanel','labelGridCfg':{'sticky':'w'},
            'initialValue':1, 'labelCfg':{'text':'xticklabels'} }   

        self.widgetDescr['yticklabels'] = {
        'class':'NECheckButton', 'master':'ParamPanel','labelGridCfg':{'sticky':'w'},'labelGridCfg':{'sticky':'w'},
            'initialValue':1, 'labelCfg':{'text':'yticklabels'} }
            
            
        self.widgetDescr['axison'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':1, 'labelCfg':{'text':'axis on'} }
        self.widgetDescr['autoscaleon'] = {
            'class':'NECheckButton', 'master':'ParamPanel','labelGridCfg':{'sticky':'w'},
            'initialValue':1, 'labelCfg':{'text':'autoscale on'} }
	op = self.outputPortsDescr
        op.append(datatype='MPLDrawArea', name='drawAreaDef')
        
        code = """def doit(self, left, bottom, width, height, frameon, hold, title,
xlabel, ylabel, xlimit, ylimit, xticklabels, yticklabels, axison, autoscaleon):

    kw = {'left':left, 'bottom':bottom, 'width':width, 'height':height,
    'frameon':frameon, 'hold':hold, 'title':title, 'xlabel':xlabel,
    'ylabel':ylabel, 'axison':axison, 'xticklabels': xticklabels,'yticklabels': yticklabels,'xlimit':xlimit,'ylimit':ylimit,'autoscaleon':autoscaleon}
    
    self.outputData(drawAreaDef=kw)
"""
        self.setFunction(code)


class MPLMergeTextNE(NetworkNode):
    """Class for writting multiple labels in the axes.Takes input from Text
    nodes.
    """
    def __init__(self, name='MergeText', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='MPLDrawArea', required=False,name='textlist',singleConnection=False)
        op = self.outputPortsDescr
        op.append(datatype='MPLDrawArea', name='drawAreaDef')
        code = """def doit(self,textlist):
    kw={'text':textlist}
    self.outputData(drawAreaDef=kw)
"""
        self.setFunction(code)
        
class MPLPlottingNode(MPLBaseNE):
    """Base class for plotting nodes"""

    def afterAddingToNetwork(self):

        self.figure = Figure()
        self.axes = self.figure.add_subplot( 111 )
        self.axes.node = weakref.ref(self)

        master = Tkinter.Toplevel()
        master.title(self.name)
        self.canvas = FigureCanvasTkAgg(self.figure, master)
        self.figure.set_canvas(self.canvas)

        packOptsDict = {'side':'top', 'fill':'both', 'expand':1}
        self.canvas.get_tk_widget().pack( *(), **packOptsDict )
        self.canvas._master.protocol('WM_DELETE_WINDOW',self.canvas._master.iconify)
        toolbar = NavigationToolbar2TkAgg(self.canvas, master)


    def setDrawAreaDef(self, drawAreaDef):
        newdrawAreaDef={}
        if drawAreaDef:
         if len(drawAreaDef)==1 and drawAreaDef[0] is not None:
            #for d in drawAreaDef[0].keys():
            #    newdrawAreaDef[d]=drawAreaDef[0][d]
            newdrawAreaDef = drawAreaDef[0]
         elif len(drawAreaDef)>1:
            for dAD in drawAreaDef:
                if type(dAD)== types.DictType:
                    for j in dAD.keys():
                        newdrawAreaDef[j]=dAD[j]
        self.setDrawArea(newdrawAreaDef)
    
    codeBeforeDisconnect ="""def beforeDisconnect(self,c):
        node=c.port2.node
        node.axes.clear()
        node.canvas.draw() """     
        
########################################################################
####
####    PLOTTING NODES
####
########################################################################

class FillNE(MPLPlottingNode):
    """plots filled polygons. 
x  - list of x vertices
y  - list of y vertices
fillcolor - color 
"""
    
    def __init__(self, name='Fill', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string', required=False, name='fillcolor', defaultValue='w')
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False)
        self.widgetDescr['fillcolor'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'white',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'fillcolor:'}}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype='None', name='fig') 
        code = """def doit(self, x, y, fillcolor, drawAreaDef):
    self.axes.clear()
    ax=self.axes
    p=ax.fill(x,y,fillcolor)
    self.setDrawAreaDef(drawAreaDef)
    self.canvas.draw()    
    self.outputData(axes=self.axes,fig=p)
"""
        self.setFunction(code)

class PolarAxesNE(MPLPlottingNode):
    """ This node  plots on PolarAxes 
Input:
    y          - sequence of values
    x          - None; sequence of values
Adjustable parameters:
    grid --grid on or off(default is on)
    gridcolor --color of the grid
    gridlinewidth --linewidth of the grid 
    gridlinestyle --gridlinestyle
    xtickcolor -- color of xtick
    ytickcolor -- color of ytick
    xticksize --size of xtick
    yticksize --size of ytick
"""
    def __init__(self, name='PolarAxes', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        self.styles={}
        for ls in Line2D._lineStyles.keys():
           self.styles[Line2D._lineStyles[ls][6:]]=ls
        for ls in Line2D._markers.keys():
           self.styles[Line2D._markers[ls][6:]]=ls
	    #these styles are not recognized
        #del self.styles['steps']
        for s in  self.styles.keys():
           
           if s =="nothing":
               del self.styles['nothing']
           if s[:4]=='tick':
               del self.styles[s]
        self.colors=colors
        ip = self.inputPortsDescr
        #ip.append(datatype='MPLAxes', required=False, name='p',
                  #singleConnection=True)#,beforeDisconnect=codeBeforeDisconnect)
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',  name='x',beforeDisconnect=self.codeBeforeDisconnect) 
        ip.append(datatype='string', required=False, name='lineStyle', defaultValue='solid')
        ip.append(datatype='None', required=False, name='color', defaultValue='black')
        ip.append(datatype='boolean', required=False, name='grid', defaultValue=1)
        ip.append(datatype='str', required=False, name='gridlineStyle', defaultValue='--')
        ip.append(datatype='str', required=False, name='gridcolor', defaultValue='gray')
        ip.append(datatype='float', required=False, name='gridlinewidth', defaultValue=1)
        ip.append(datatype='str', required=False, name='axisbg', defaultValue='white')
        ip.append(datatype='str', required=False, name='xtickcolor', defaultValue='black')
        ip.append(datatype='str', required=False, name='ytickcolor', defaultValue='black')
        ip.append(datatype='float', required=False, name='xticksize', defaultValue=12)
        ip.append(datatype='float', required=False, name='yticksize', defaultValue=12)
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False)
        self.widgetDescr['grid'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'initialValue':1, 'labelCfg':{'text':'grid'} ,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},}
        self.widgetDescr['lineStyle'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.styles.keys(),
            'fixedChoices':True,
            'initialValue':'solid',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'line style:'}}
        self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.colors.keys(),
            'fixedChoices':True,
            'initialValue':'black',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'color:'}}
        self.widgetDescr['gridlineStyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':lineStyles.keys(),
            'fixedChoices':True,
            'initialValue':'--',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'gridlinestyle:'}}  
        self.widgetDescr['gridcolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'gray',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'gridcolor:'}}    
        self.widgetDescr['gridlinewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'gridlinewidth'},
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'}}
        self.widgetDescr['axisbg'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'white',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'axisbg:'}}
        self.widgetDescr['xtickcolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'black',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'xtickcolor:'}}
        self.widgetDescr['ytickcolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'black',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'ytickcolor:'}}    
        self.widgetDescr['xticksize'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':12,
            'labelCfg':{'text':'xticksize'},'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'} }
        self.widgetDescr['yticksize'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':12,
            'labelCfg':{'text':'yticksize'},'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLFigure', name='figure')
        code = """def doit(self, y, x, lineStyle, color, grid, gridlineStyle,
gridcolor, gridlinewidth, axisbg, xtickcolor, ytickcolor, xticksize, yticksize, drawAreaDef):
        
        self.figure.clear()
        self.setDrawAreaDef(drawAreaDef)
        if grid==1:
            matplotlib.rc('grid',color=gridcolor,linewidth=gridlinewidth,linestyle=gridlineStyle) 
        matplotlib.rc('xtick',color=xtickcolor,labelsize=xticksize)
        matplotlib.rc('ytick',color=ytickcolor,labelsize=yticksize)
        colorChar = self.colors[color]
        lineStyleChar = self.styles[lineStyle]
        new_axes=self.figure.add_axes(self.axes.get_position(),polar=True,axisbg=axisbg)        
        self.axes=new_axes
        self.axes.plot(x, y, colorChar+lineStyleChar)  
        if grid!=1:
                new_axes.grid(grid)
        self.canvas.draw()
        self.outputData(figure=self.figure)
"""
        self.setFunction(code)



class StemNE(MPLPlottingNode):
    """A stem plot plots vertical lines (using linefmt) at each x location
from the baseline to y, and places a marker there using markerfmt.  A
horizontal line at 0 is is plotted using basefmt
input: list of x values 
Return value is (markerline, stemlines, baseline) .
"""    
    def __init__(self, name='Stem', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,),kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list',required=True, name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',required=True, name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string',required=False,name='stemlinestyle', defaultValue='--')
        ip.append(datatype='string',required=False,name='stemlinecolor', defaultValue='b')
        ip.append(datatype='string',required=False,name='markerstyle', defaultValue='o')
        ip.append(datatype='string',required=False,name='markerfacecolor', defaultValue='b')
        ip.append(datatype='string',required=False,name='baselinecolor', defaultValue='b')
        ip.append(datatype='string',required=False,name='baselinestyle', defaultValue='-')
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False)
        self.widgetDescr['stemlinestyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['-.','--','-',':'],
            'fixedChoices':True,
            'initialValue':'--',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'stemlinestyle:'}}
        self.widgetDescr['stemlinecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(),
            'fixedChoices':True,
            'initialValue':'b',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'stemlinecolor:'}}
        self.widgetDescr['markerstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':Line2D._markers.keys(),
            'fixedChoices':True,
            'initialValue':'o',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'markerstyle:'}}
        self.widgetDescr['markerfacecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(),
            'fixedChoices':True,
            'initialValue':'k',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'markerfacecolor:'}}
        self.widgetDescr['baselinestyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['-.','--','-',':'],
            'fixedChoices':True,
            'initialValue':'-',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'baselinestyle:'}}
        self.widgetDescr['baselinecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(),
            'fixedChoices':True,
            'initialValue':'k',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'baselinecolor:'}}
                
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='stem')
        code = """def doit(self, x, y, stemlinestyle, stemlinecolor, markerstyle,
markerfacecolor, baselinecolor, baselinestyle, drawAreaDef):
    self.axes.clear()
    linefmt=stemlinecolor+stemlinestyle
    markerfmt=markerfacecolor+markerstyle
    basefmt= baselinecolor+baselinestyle
    markerline, stemlines, baseline = self.axes.stem(x, y, linefmt=linefmt, markerfmt=markerfmt, basefmt=basefmt )
    self.setDrawAreaDef(drawAreaDef)
    self.canvas.draw()
    self.outputData(stem=self.axes)
"""
        self.setFunction(code)
       
class MultiPlotNE(MPLPlottingNode):
    """This node allows to plot multiple plots on same axes
input: axes instances
    """        
    def __init__(self, name='MultiPlot', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,),kw )
        ip = self.inputPortsDescr
        ip.append(datatype='MPLAxes', required=True, name='multiplot', singleConnection=False,beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef', singleConnection=False)   
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='multiplot')          
        code = """def doit(self, plots, drawAreaDef):
    self.axes.clear()
    ax=self.axes
    if len(plots)>0:
        ax.set_xlim(plots[0].get_xlim())
        ax.set_ylim(plots[0].get_ylim())
    for p in plots:
        if p.patches!=[]:
            for pt in p.patches:
                ax.add_patch(pt)
        elif p.lines!=[]:
          if p.lines!=[]:
            for pt in p.lines:
                ax.add_line(pt)  
        elif p.collections!=[]:
          if p.collections!=[]:
            for pt in p.collections:
                ax.add_collection(pt)
        else:
          ax.add_artist(p)
    ax.autoscale_view()
    self.setDrawAreaDef(drawAreaDef) 
    self.canvas.draw()
    self.outputData(multiplot=self.axes)
"""
        self.setFunction(code)
        
class TablePlotNE(MPLPlottingNode):
    """Adds a table to the current axes and plots bars.  
input:
cellText - list of values
rowLabels - list of labels
rowColours - list of colors
colLabels  - list of labels
colColours - list of colors
location - location where the table to be placed.
""" 
    def __init__(self, name='TablePlot', **kw):
        """
        TABLE(cellText=None, cellColours=None,
              cellLoc='right', colWidths=None,
              rowLabels=None, rowColours=None, rowLoc='left',
              colLabels=None, colColours=None, colLoc='center',
              loc='bottom', bbox=None):

        Adds a table to the current axes and plots bars.  
        """
        kw['name'] = name
        locs=locations.keys()
        locs.append("bottom")
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list',required=True, name='values',singleConnection="auto",beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',required=True, name='rowLabels',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',required=True, name='colLabels',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',required=False, name='rowColors')
        ip.append(datatype='list',required=False, name='colColors')
        ip.append(datatype='string',required=False, name='location', defaultValue='bottom')
        ip.append(datatype='MPLDrawArea',required=False,name='drawAreaDef',singleConnection=False)
        self.widgetDescr['location'] = {
        'class':'NEComboBox', 'master':'node',
            'choices':locs,
            'fixedChoices':True,
            'initialValue':'bottom',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Location:'}}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')

        code = """def doit(self, values, rowLabels, colLabels, rowColors,
colColors, location, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    #self.axes.set_position([0.2, 0.2, 0.7, 0.6])
    data=[]
    nd=[]
    for val in values :
        for v in val:
            nd.append(float(v))
        data.append(nd)
        nd=[]
    #rcolours = get_colours(len(colLabels))
    rows = len(data)
    ind = arange(len(colLabels)) + 0.3  # the x locations for the groups
    cellText = []
    width = 0.4     # the width of the bars
    yoff = array([0.0] * len(colLabels)) # the bottom values for stacked bar chart
    for row in xrange(rows):
        self.axes.bar(ind, data[row], width, bottom=yoff, color=rowColors[row])
        yoff = yoff + data[row]
        cellText.append(['%1.1f' % x for x in yoff])
    the_table = self.axes.table(cellText=cellText,
                  rowLabels=rowLabels,
                  rowColours=rowColors,
                  colColours=colColors,
                  colLabels=colLabels,
                  loc=location)
    if location=="bottom":
        self.axes.set_xticks([])
        self.axes.set_xticklabels([])
    self.canvas.draw()
    self.outputData(plot=self.axes)
"""
        self.setFunction(code)
        
class HistogramNE(MPLPlottingNode):
    """This nodes takes a list of values and builds a histogram using matplotlib
http://matplotlib.sourceforge.net/matplotlib.pylab.html#-hist

Compute the histogram of x.  bins is either an integer number of
bins or a sequence giving the bins.  x are the data to be binned.
 
The return values is (n, bins, patches)
 
If normed is true, the first element of the return tuple will be the
counts normalized to form a probability distribtion, ie,
n/(len(x)*dbin)
        
Addition kwargs: hold = [True|False] overrides default hold state

Input:
    values:    sequence of values
    bins=10:   number of dequence giving the gins
    normed=0   normalize

Output:
    plot       Matplotlib Axes object
"""    
    def __init__(self, name='Histogram', **kw):
        kw['name'] = name

        apply( MPLPlottingNode.__init__, (self,), kw )
        self.colors=cnames
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='values',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False, name='bins', defaultValue=10)
        ip.append(datatype='boolean', required=False, name='normed', defaultValue=False)
        ip.append(datatype='float', required=False, name='patch_antialiased', defaultValue=1)
        ip.append(datatype='float', required=False, name='patch_linewidth', defaultValue=1)
        ip.append(datatype='string', required=False, name='patch_edgecolor', defaultValue='black')
        ip.append(datatype='string', required=False, name='patch_facecolor', defaultValue='blue')
        ip.append(datatype='MPLDrawArea',required=False,name='drawAreaDef',singleConnection=False)
        self.widgetDescr['bins'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10, 'type':'int', 'wheelPad':2,
            'initialValue':10,
            'labelCfg':{'text':'# of bins'} }

        self.widgetDescr['normed'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':1, 'labelCfg':{'text':'normalize'},
            }
        self.widgetDescr['patch_linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'linewidth'} }
        self.widgetDescr['patch_antialiased'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'antialiased:'},
            'initialValue':1,}
        self.widgetDescr['patch_edgecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.colors.keys(),
            'fixedChoices':True,
            'initialValue':'black',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'edgecolor:'}}
        self.widgetDescr['patch_facecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.colors.keys(),
            'fixedChoices':True,
            'initialValue':'blue',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'facecolor:'}}
	op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')

        code = """def doit(self, values, bins, normed, patch_antialiased,
patch_linewidth, patch_edgecolor, patch_facecolor, drawAreaDef):
    self.axes.clear()
    n, bins, patches = self.axes.hist(values, bins=bins, normed=normed)
    self.setDrawAreaDef(drawAreaDef)
    if self.axes.patches:
        for p in self.axes.patches:
            p.set_linewidth(patch_linewidth)
            p.set_edgecolor(patch_edgecolor)
            p.set_facecolor(patch_facecolor)
            p.set_antialiased(patch_antialiased)
    self.canvas.draw()
    self.outputData(plot=self.axes)
"""
        self.setFunction(code)

#Plot Nodes

class PlotNE(MPLPlottingNode):
    """This nodes takes two lists of values and plots the the second against the first.

Input:
    y          - sequence of values
    x          - None; sequence of values
    figure     - None; MPLFigure object object into which to place the drawing

Output:
    plot       Matplotlib Axes object
    line:   - line
"""
    
    def __init__(self, name='Plot', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        self.styles=get_styles()
        self.colors=colors        
	self.joinstyles = Line2D.validJoin
        self.capstyles = Line2D.validCap 
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', required=False, name='x')
        ip.append(datatype='string', required=False, name='lineStyle', defaultValue='solid')
        ip.append(datatype='None', required=False, name='color', defaultValue='black')
        ip.append(datatype='boolean', required=False, name='line_antialiased', defaultValue=1)
        ip.append(datatype='float', required=False, name='line_linewidth', defaultValue=1)
        ip.append(datatype='string', required=False, name='solid_joinstyle', defaultValue='miter')
        ip.append(datatype='string', required=False, name='solid_capstyle', defaultValue='projecting')
        ip.append(datatype='string', required=False, name='dash_capstyle', defaultValue='butt')
        ip.append(datatype='string', required=False, name='dash_joinstyle', defaultValue='miter')
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False)
        
	self.widgetDescr['lineStyle'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.styles.keys(),
            'fixedChoices':True,
            'initialValue':'solid',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'line style:'}}

	self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.colors.keys(),
            'fixedChoices':True,
            'initialValue':'black',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'color:'}}
            
        self.widgetDescr['dash_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'butt',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash_capstyle:'}}
        self.widgetDescr['dash_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash _joinstyle:'}}
        self.widgetDescr['solid_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'projecting',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_capstyle:'}}
        self.widgetDescr['solid_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_joinstyle:'}}
        self.widgetDescr['line_linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'linewidth'} }
        
        self.widgetDescr['line_antialiased'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'antialiased:'},
            'initialValue':1,}        
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        
        code = """def doit(self, y, x, lineStyle, color, line_antialiased,
line_linewidth, solid_joinstyle, solid_capstyle, dash_capstyle, dash_joinstyle,
drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    colorChar = self.colors[color]
    lineStyleChar = self.styles[lineStyle]
    if x is None:
        l = self.axes.plot(y, colorChar+lineStyleChar)
    else:
        l = self.axes.plot(x, y, colorChar+lineStyleChar)
    #line properties
    if  self.axes.lines:
        for l in self.axes.lines:
            l.set_linewidth(line_linewidth)
            l.set_antialiased(line_antialiased)
            l.set_solid_joinstyle(solid_joinstyle)
            l.set_solid_capstyle(solid_capstyle)
            l.set_dash_capstyle(dash_capstyle)
            l.set_dash_joinstyle(dash_joinstyle)
            
    self.canvas.draw()
    self.outputData(plot=self.axes)
"""
        self.setFunction(code)

class PlotDateNE(MPLPlottingNode):
    """This nodes takes two lists of values and plots the the second against the first.

Input:
    y          - sequence of dates
    x          - sequence of dates
optional arguements:    
    lineStyle  - line style
    color      - color of the line
                 (lineStyle+colorchar --fmt)
    tz         - timezone
    xdate      - is True, the x-axis will be labeled with dates
    ydate      - is True, the y-axis will be labeled with dates  
Output:
    plot       Matplotlib Axes object
    line:   - line
pytz is required.
checks for pytz module and returns if not
"""   
    def __init__(self, name='PlotDate', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        self.styles=get_styles()
        self.colors=colors        
	self.joinstyles = Line2D.validJoin
        timezones=common_timezones
        self.capstyles = Line2D.validCap 
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string', required=False, name='lineStyle', defaultValue='solid')
        ip.append(datatype='None', required=False, name='color', defaultValue='black')
        ip.append(datatype='string', required=False, name='tz', defaultValue='US/PACIFIC')
        ip.append(datatype='boolean', required=False, name='xdate', defaultValue=True)
        ip.append(datatype='boolean', required=False, name='ydate', defaultValue=False)
        ip.append(datatype='boolean', required=False, name='line_antialiased', defaultValue=1)
        ip.append(datatype='float', required=False, name='line_linewidth', defaultValue=1)
        ip.append(datatype='string', required=False, name='solid_joinstyle', defaultValue='miter')
        ip.append(datatype='string', required=False, name='solid_capstyle', defaultValue='projecting')
        ip.append(datatype='string', required=False, name='dash_capstyle', defaultValue='butt')
        ip.append(datatype='string', required=False, name='dash_joinstyle', defaultValue='miter')
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False)
        
	self.widgetDescr['lineStyle'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.styles.keys(),
            'fixedChoices':True,
            'initialValue':'circle',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'line style:'}}

	self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.colors.keys(),
            'fixedChoices':True,
            'initialValue':'blue',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'color:'}}
            
        self.widgetDescr['tz'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':timezones,
            'fixedChoices':True,
            'initialValue':'US/PACIFIC',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'timezone:'}}
            
        self.widgetDescr['xdate'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'xdate:'},
            'initialValue':1,}
        
        self.widgetDescr['ydate'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'ydate:'},
            'initialValue':0,}
            
        self.widgetDescr['dash_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'butt',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash_capstyle:'}}
        self.widgetDescr['dash_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash _joinstyle:'}}
        self.widgetDescr['solid_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'projecting',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_capstyle:'}}
        self.widgetDescr['solid_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_joinstyle:'}}
        self.widgetDescr['line_linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'linewidth'} }
        
        self.widgetDescr['line_antialiased'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'antialiased:'},
            'initialValue':1,}        
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        
        code = """def doit(self, y, x, lineStyle, color, tz, xdate, ydate,
line_antialiased, line_linewidth, solid_joinstyle, solid_capstyle, dash_capstyle,
dash_joinstyle, drawAreaDef):
    try:
       from pytz import common_timezones
    except:
       print  "Could not import pytz "
       return
    self.axes.clear() 
    self.setDrawAreaDef(drawAreaDef)
    colorChar = self.colors[color]
    lineStyleChar = self.styles[lineStyle]
    rcParams['timezone'] = tz
    tz=timezone(tz)
    fmt= colorChar+lineStyleChar
    l = self.axes.plot_date(x, y, fmt=colorChar+lineStyleChar, tz=tz, xdate= xdate,ydate= ydate)
    #line properties 
    if  self.axes.lines:
        for l in self.axes.lines:
            l.set_linewidth(line_linewidth)
            l.set_antialiased(line_antialiased)
            l.set_solid_joinstyle(solid_joinstyle)
            l.set_solid_capstyle(solid_capstyle)
            l.set_dash_capstyle(dash_capstyle)
            l.set_dash_joinstyle(dash_joinstyle)
            
    self.canvas.draw()
    self.outputData(plot=self.axes)
"""
        self.setFunction(code)

class PieNE(MPLPlottingNode):
    """plots a pie diagram for a list of numbers.  The size of each wedge
will be the fraction x/sumnumbers).

Input:
    fractions - sequence of values
    labels    - None; sequence of labels (has to match length of factions
    explode   - None; float or sequence of values which specifies the
                fraction of the radius to offset that wedge.
		if a single float is given the list is generated automatically
    shadow    - True; if True, will draw a shadow beneath the pie.
    format    - None; fromat string used to label the wedges with their
                numeric value
Output:
    plot      - Matplotlib Axes object
    patches   - sequence of matplotlib.patches.Wedge
    texts     - list of the label Text instances
    autotextsline - list of text instances for the numeric labels (only if
                    format is not None
"""
    
    def __init__(self, name='Pie', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='fractions',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', required=False, name='labels')
        ip.append(datatype='None', required=False, name='explode')
        ip.append(datatype='boolean', required=False, name='shadow')
        ip.append(datatype='string', required=False, name='format')
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)

        self.widgetDescr['explode'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10, 'type':'float', 
            'initialValue':0.05, 'wheelPad':2,
            'labelCfg':{'text':'explode'} }

        self.widgetDescr['shadow'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':1, 'labelCfg':{'text':'shadow'}}

        self.widgetDescr['format'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'format:'},
            'initialValue':'%1.1f%%'}
        
	op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        op.append(datatype='None', name='patches')
        op.append(datatype='None', name='texts')
        op.append(datatype='None', name='autotextsline')
        
        code = """def doit(self, fractions, labels, shadow, explode, format,
drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    if isinstance(explode, float) or isinstance(explode, int):
        explode = [explode]*len(fractions)
    res = self.axes.pie(fractions, explode=explode, labels=labels,
                  autopct=format, shadow=shadow)
    if format is None:
        patches, texts = res
	autotextsline = None
    else:
        patches, texts, autotextsline = res
    self.canvas.draw()

    self.outputData(plot=self.axes, patches=patches, texts=texts, autotextsline=autotextsline)
"""
        self.setFunction(code)
        
#Spy Nodes

class SpyNE(MPLPlottingNode):
    """Plots the sparsity pattern of the matrix Z using plot markers.
input:
    Z - matrix
optional arguements:
    marker - marker
    markersize -markersize    
    The line handles are returned
"""

    def __init__(self, name='Spy', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None',name = 'Z',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string', required=False, name='marker', defaultValue='s')
        ip.append(datatype='None', required=False, name='markersize', defaultValue=10)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['marker'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':markers.values(),
            'fixedChoices':True,
            'initialValue':'s',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'markers:'}}
        self.widgetDescr['markersize'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10, 'type':'float', 
            'initialValue':10.0, 'wheelPad':2,
            'labelCfg':{'text':'size'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        code = """def doit(self, Z, marker, markersize, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    l=self.axes.spy(Z,marker=marker,markersize=markersize)
    self.canvas.draw()    
    self.outputData(plot=self.axes)
"""
        self.setFunction(code)

class Spy2NE(MPLPlottingNode):
    """SPY2 plots the sparsity pattern of the matrix Z as an image
input:
    Z - matrix
The image instance is returned
"""
    def __init__(self, name='Spy2', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None',name = 'Z',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        op.append(datatype='None', name='image')
        code = """def doit(self, Z, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    im=self.axes.spy2(Z)
    self.canvas.draw()
    self.outputData(plot=self.axes,image=im)
"""
        self.setFunction(code)
        
class VlineNE(MPLPlottingNode):
    """Plots vertical lines at each x from ymin to ymax.  ymin or ymax can be
scalars or len(x) numpy arrays.  If they are scalars, then the
respective values are constant, else the heights of the lines are
determined by ymin and ymax
x - array
ymin or ymax can be scalars or len(x) numpy arrays
color+marker - fmt is a plot format string, eg 'g--'
Returns a list of lines that were added
"""    
    def __init__(self, name='Vline', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list',name = 'x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',name = 'ymin',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list',name = 'ymax',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string', required=False, name='color', defaultValue='k')
        ip.append(datatype='string', required=False, name='linestyle', defaultValue='-')
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':colors.values(),
            'fixedChoices':True,
            'initialValue':'k',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'color:'}}
        
        self.widgetDescr['linestyle'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['solid','dashed','dashdot','dotted'],
            'fixedChoices':True,
            'initialValue':'solid',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'linestyle:'}}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        op.append(datatype='None', name='lines')
        code = """def doit(self, x, ymin, ymax, color, linestyle, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    lines=self.axes.vlines(x, ymin, ymax, color=color, linestyle=linestyle )
    self.canvas.draw()
    self.outputData(plot=self.axes,lines=lines)
"""
        self.setFunction(code) 

            
#Scatter Nodes
from math import fabs

class ScatterNE(MPLPlottingNode):
    """plots a scatter diagram for two lists of numbers.

Input:
    x         - sequence of values
    y         - sequence of values
    s         - None; sequence of values for size in area
    c         - None, string or sequence of colors
    marker    - 'circle', marker

Output:
    plot       Matplotlib Axes object
    patches   - matplotlib.collections.RegularPolyCollection instance
"""
    def getPointInBin(self, data, sortind, x, eps):
        #dichotomous search for indices of values in data within x+-eps
        if len(sortind)>2:
            if data[sortind[0]]==x: return data, [sortind[0]]
            elif data[sortind[-1]]==x: return data, [sortind[-1]]
            elif len(sortind)==2: return data, sortind
            else:
                mid = len(sortind)/2
                if fabs(data[sortind[mid]]-x)<eps:
                    if fabs(data[sortind[0]]-x)<eps:
                        return data, sortind[:mid]
                    elif fabs(data[sortind[-1]]-x)<eps:
                        return data, sortind[mid:]

                if data[sortind[mid]]>x:
                    data, sortind = self.getPointInBin(data, sortind[:mid],
                                                       x, eps)
                elif data[sortind[mid]]<x:
                    data, sortind = self.getPointInBin(data, sortind[mid:],
                                                       x, eps)
        return data, sortind


    def on_click(self, event):
        # get the x and y pixel coords
        if event.inaxes:
            d1 = self.inputPorts[0].getData()
            d2 = self.inputPorts[1].getData()

            mini = min(d1)
            maxi = max(d1)
            epsx = (maxi-mini)/200.
            import numpy
            d1s = numpy.argsort(d1)
            
            x, y = event.xdata, event.ydata
            dum, v1 = self.getPointInBin(d1, d1s, x, epsx)
            mini = min(d2)
            maxi = max(d2)
            epsy = (maxi-mini)/200.
            result = []
            for v in v1:
                if fabs(x - d1[v])<epsx and fabs(y - d2[v])<epsy:
                    result.append(v)
                #print v,  x - d1[v], epsx, y - d2[v], epsy

            if len(result):
                print 'point:', result, x, d1[result[0]], y, d2[result[0]]
                self.outputData(pick=result)
                self.scheduleChildren([self.outputPorts[2]])
                return result
            else:
                print "NO POINT"
                return None


    def afterAddingToNetwork(self):
        MPLPlottingNode.afterAddingToNetwork(self)
        self.figure.canvas.mpl_connect('button_press_event', self.on_click)


    def __init__(self, name='Scatter', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )

        self.cutoff = 10.0
        self.joinstyles = Line2D.validJoin
        self.capstyles = Line2D.validCap
        self.colors = colors
        self.markers = markers 
        self.widgetDescr['s'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10, 'type':'float', 
            'initialValue':1.0, 'wheelPad':2,
            'labelCfg':{'text':'size'} }

        self.widgetDescr['c'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.colors.values(),
            'fixedChoices':True,
            'initialValue':'k',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'color:'}}
        

	self.widgetDescr['marker'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.markers.keys(),
            'fixedChoices':True,
            'initialValue':'circle',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'markers:'}}
         
        self.widgetDescr['dash_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'butt',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash_capstyle:'}}

        self.widgetDescr['dash_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash _joinstyle:'}}

        self.widgetDescr['solid_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'projecting',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_capstyle:'}}

        self.widgetDescr['solid_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_joinstyle:'}}
        
        self.widgetDescr['linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'linewidth'} }
               
        self.widgetDescr['line_antialiased'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'antialiased:'},
            'initialValue':1,}
        
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False, name='s')
        ip.append(datatype='None', required=False, name='c', defaultValue='k')
        ip.append(datatype='string', required=False, name='marker', defaultValue='circle')
        ip.append(datatype='string', required=False, name='solid_joinstyle', defaultValue='miter')
        ip.append(datatype='string', required=False, name='solid_capstyle', defaultValue='projecting')
        ip.append(datatype='string', required=False, name='dash_capstyle', defaultValue='butt')
        ip.append(datatype='string', required=False, name='dash_joinstyle', defaultValue='miter')
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False) 
	op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        op.append(datatype='None', name='patches')
        op.append(datatype='int', name='pick')
        
        code = """def doit(self, x, y, s, c, marker, solid_joinstyle,
solid_capstyle, dash_capstyle, dash_joinstyle, drawAreaDef):
    kw={'solid_joinstyle':solid_joinstyle,'solid_capstyle':solid_capstyle,'dash_capstyle':dash_capstyle,'dash_joinstyle':dash_joinstyle}
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    if self.markers.has_key(marker):
        marker = self.markers[marker]
    res = self.axes.scatter( x, y, s, c, marker)
    #collections properties
    if  self.axes.lines:
        for c in self.axes.collections:
            c.set_solid_joinstyle(solid_joinstyle)
            c.set_solid_capstyle(solid_capstyle)
            c.set_dash_capstyle(dash_capstyle)
            c.set_dash_joinstyle(dash_joinstyle)
    self.canvas.draw()
    self.outputData(plot=self.axes, patches=res)
"""
        self.setFunction(code)


class ScatterClassicNE(MPLPlottingNode):
    """plots a scatter diagram for two lists of numbers.

Input:
    x         - sequence of values
    y         - sequence of values
    s         - None; sequence of values for size in area
    c         - None, string or sequence of colors
    
Output:
    plot       Matplotlib Axes object
    patches   - matplotlib.collections.RegularPolyCollection instance
"""
    
    def __init__(self, name='ScatterClassic', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        
        self.joinstyles = Line2D.validJoin
        self.capstyles = Line2D.validCap
        self.colors=colors
        self.markers =markers 
        self.widgetDescr['s'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10, 'type':'float', 
            'initialValue':1.0, 'wheelPad':2,
            'labelCfg':{'text':'size'} }

        self.widgetDescr['c'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.colors.values(),
            'fixedChoices':True,
            'initialValue':'k',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'color:'}}
        

        self.widgetDescr['dash_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'butt',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash_capstyle:'}}
        self.widgetDescr['dash_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'dash _joinstyle:'}}
        self.widgetDescr['solid_capstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.capstyles,
            'fixedChoices':True,
            'initialValue':'projecting',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_capstyle:'}}
        self.widgetDescr['solid_joinstyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':self.joinstyles,
            'fixedChoices':True,
            'initialValue':'miter',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'solid_joinstyle:'}}
        
        self.widgetDescr['linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':60, 'height':21, 'oneTurn':2, 'type':'int',
            'wheelPad':2, 'initialValue':1,
            'labelCfg':{'text':'linewidth'} }
               
        self.widgetDescr['line_antialiased'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'antialiased:'},
            'initialValue':1,}
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False, name='s')
        ip.append(datatype='None', required=False, name='c')
        ip.append(datatype='string', required=False, name='solid_joinstyle', defaultValue='miter')
        ip.append(datatype='string', required=False, name='solid_capstyle', defaultValue='projecting')
        ip.append(datatype='string', required=False, name='dash_capstyle', defaultValue='butt')
        ip.append(datatype='string', required=False, name='dash_joinstyle', defaultValue='miter')
        ip.append(datatype='MPLDrawArea', required=False,name='drawAreaDef',singleConnection=False) 
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        op.append(datatype='None', name='patches')
        code = """def doit(self, x, y, s, c, solid_joinstyle, solid_capstyle,
dash_capstyle, dash_joinstyle, drawAreaDef):
    kw={'solid_joinstyle':solid_joinstyle,'solid_capstyle':solid_capstyle,'dash_capstyle':dash_capstyle,'dash_joinstyle':dash_joinstyle}
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    res = self.axes.scatter_classic( x, y, s, c)
    #collections properties
    if  self.axes.lines:
        for c in self.axes.collections:
            c.set_solid_joinstyle(solid_joinstyle)
            c.set_solid_capstyle(solid_capstyle)
            c.set_dash_capstyle(dash_capstyle)
            c.set_dash_joinstyle(dash_joinstyle)
    self.canvas.draw()
    self.outputData(plot=self.axes, patches=res)
"""
        self.setFunction(code)
        
class FigImageNE(MPLPlottingNode):
    """plots an image from a 2d array fo data

Input:
    data        - 2D array of data

Output:
    plot       Matplotlib Axes object
    image     - image.FigureImage instance 
"""
    
    def __init__(self, name='Figimage', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='data',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string',required=False, name='cmap', defaultValue='jet')
        ip.append(datatype='string',required=False, name='imaspect', defaultValue='equal')
        ip.append(datatype='string',required=False, name='interpolation', defaultValue='bilinear')
        ip.append(datatype='string',required=False, name='origin', defaultValue='upper')
        ip.append(datatype='None', required=False, name='alpha', defaultValue=1.)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        imaspects=['auto', 'equal']
        interpolations =['nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric','catrom', 'gaussian', 'bessel', 'mitchell', 'sinc','lanczos', 'blackman']
        self.widgetDescr['cmap'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cmaps,
            'fixedChoices':True,
            'initialValue':'jet',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'cmap:'}}
        self.widgetDescr['imaspect'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':imaspects,
            'fixedChoices':True,
            'initialValue':'equal',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'aspect:'}}  
        self.widgetDescr['interpolation'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':interpolations,
            'fixedChoices':True,
            'initialValue':'bilinear',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'interpolation:'}}
        self.widgetDescr['origin'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['upper','lower',],
            'fixedChoices':True,
            'initialValue':'upper',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'origin:'}}
        self.widgetDescr['alpha'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1, 'type':'float', 
	    'initialValue':1.0, 'wheelPad':2, 
            'labelCfg':{'text':'alpha'} }
            
            
	op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='plot')
        op.append(datatype='None', name='image')
        
        code = """def doit(self, data, cmap, imaspect, interpolation, origin,
alpha, drawAreaDef):
    kw={'cmap':cmap,'imaspect':imaspect,'interpolation':interpolation,'origin':origin,'alpha':alpha}
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    self.setDrawArea(kw)
    im = self.axes.imshow(data)
    #image properties
    cmp=cm.get_cmap(cmap)
    im.set_cmap(cmp)
    im.set_interpolation(interpolation)
    im.set_alpha(alpha)
    im.origin=origin
    self.axes.set_aspect(imaspect)
    self.canvas.draw()
    self.outputData(plot=self.axes, image=im)
"""
        self.setFunction(code)


#PSEUDO COLOR PLOTS

class PcolorMeshNE(MPLPlottingNode):
    """This class is for making a pseudocolor plot.
input: 
    arraylistx      - array
    arraylisty      - array
    arraylistz      - may be a masked array
optional arguements:
    cmap    - cm.jet : a cm Colormap instance from matplotlib.cm.
            defaults to cm.jet
    shading - 'flat' : or 'faceted'.  If 'faceted', a black grid is
            drawn around each rectangle; if 'flat', edge colors are same as
            face colors
    alpha   - blending value
    PCOLORMESH(Z) - make a pseudocolor plot of matrix Z
    PCOLORMESH(X, Y, Z) - a pseudo color plot of Z on the matrices X and Y
    Return value is a matplotlib.collections.PatchCollection
        object
"""
    def __init__(self, name='PcolorMesh', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )   
        ip = self.inputPortsDescr
        ip.append(datatype='None', required=False,name='arraylistx')
        ip.append(datatype='None', required=False,name='arraylisty')
        ip.append(datatype='None', name='arraylistz',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string',required=False,  name='cmap', defaultValue='jet')
        ip.append(datatype='string',required=False,  name='shading', defaultValue='faceted')
        ip.append(datatype='float',required=False,  name='alpha', defaultValue=1.)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['cmap'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cmaps,
            'fixedChoices':True,
            'initialValue':'jet',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'cmap:'}}
        self.widgetDescr['shading'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['flat','faceted'],
            'fixedChoices':True,
            'initialValue':'faceted',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'shading:'}}
        self.widgetDescr['alpha'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float', 
	    'initialValue':1.0, 'wheelPad':2, 
            'labelCfg':{'text':'alpha'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype='None', name='patches')
        
        code = """def doit(self, x, y, z, cmap, shading, alpha, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    #pseudo color plot of Z
    Qz=z
    cmap = cm.get_cmap(cmap)
    if x==None or y==None:
        C=self.axes.pcolormesh(Qz,cmap=cmap,shading=shading,alpha=alpha)
    else:
        #a pseudo color plot of Z on the matrices X and Y
        Qx,Qy=array(x),array(y)
        C=self.axes.pcolormesh(Qx,Qy,Qz,cmap=cmap,shading=shading,alpha=alpha)
    
    self.canvas.draw()
    self.outputData(axes=self.axes,patches=C)
"""
        self.setFunction(code)

class PcolorNE(MPLPlottingNode):
    """This class is for making a pseudocolor plot.
input: 
    arraylistx      - may be a array
    arraylisty      - may be a array
    arraylistz      - may be a masked array
optional arguements:
    cmap    - cm.jet : a cm Colormap instance from matplotlib.cm.
            defaults to cm.jet
    shading - 'flat' : or 'faceted'.  If 'faceted', a black grid is
            drawn around each rectangle; if 'flat', edge colors are same as
            face colors
    alpha   - blending value
    PCOLOR(Z) - make a pseudocolor plot of matrix Z
    PCOLOR(X, Y, Z) - a pseudo color plot of Z on the matrices X and Y
    Return value is a matplotlib.collections.PatchCollection
        object
"""
    def __init__(self, name='Pcolor', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )   
        ip = self.inputPortsDescr
        ip.append(datatype='None', required=False,name='arraylistx')
        ip.append(datatype='None', required=False,name='arraylisty')
        ip.append(datatype='None', name='arraylistz',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string',required=False,  name='cmap', defaultValue='jet')
        ip.append(datatype='string',required=False,  name='shading', defaultValue='faceted')
        ip.append(datatype='float',required=False,  name='alpha', defaultValue=1.)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['cmap'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cmaps,
            'fixedChoices':True,
            'initialValue':'jet',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'cmap:'}}
        self.widgetDescr['shading'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['flat','faceted'],
            'fixedChoices':True,
            'initialValue':'faceted',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'shading:'}}
        self.widgetDescr['alpha'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float', 
	    'initialValue':1.0, 'wheelPad':2, 
            'labelCfg':{'text':'alpha'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype='None', name='patches')
        
        code = """def doit(self, x, y, z, cmap, shading, alpha, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    #pseudo color plot of Z
    Qz=z
    cmap = cm.get_cmap(cmap)
    if x==None or y==None:
        C=self.axes.pcolor(Qz,cmap=cmap,shading=shading,alpha=alpha)
    else:
        #a pseudo color plot of Z on the matrices X and Y
        Qx,Qy=array(x),array(y)
        C=self.axes.pcolor(Qx,Qy,Qz,cmap=cmap,shading=shading,alpha=alpha)
    
    self.canvas.draw()
    self.outputData(axes=self.axes,patches=C)
"""
        self.setFunction(code)
        
class PcolorClassicNE(MPLPlottingNode):
    """This class is for making a pseudocolor plot.
input: 
    arraylistx      - array
    arraylisty      - array
    arraylistz      - may be a masked array
optional arguements:
    cmap    - cm.jet : a cm Colormap instance from matplotlib.cm.
            defaults to cm.jet
    shading - 'flat' : or 'faceted'.  If 'faceted', a black grid is
            drawn around each rectangle; if 'flat', edge colors are same as
            face colors
    alpha   - blending value
    PCOLOR_CLASSIC(Z) - make a pseudocolor plot of matrix Z
    PCOLOR_CLASSIC(X, Y, Z) - a pseudo color plot of Z on the matrices X and Y
    Return value is a matplotlib.collections.PatchCollection
        object
"""
    def __init__(self, name='PcolorClassic', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )   
        ip = self.inputPortsDescr
        ip.append(datatype='None', required=False,name='arraylistx')
        ip.append(datatype='None', required=False,name='arraylisty')
        ip.append(datatype='None', name='arraylistz',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string',required=False,  name='cmap', defaultValue='jet')
        ip.append(datatype='string',required=False,  name='shading', defaultValue='faceted')
        ip.append(datatype='float',required=False,  name='alpha', defaultValue=.75)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['cmap'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cmaps,
            'fixedChoices':True,
            'initialValue':'jet',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'cmap:'}}
        self.widgetDescr['shading'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['flat','faceted'],
            'fixedChoices':True,
            'initialValue':'faceted',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'shading:'}}
        self.widgetDescr['alpha'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float', 
	    'initialValue':0.75, 'wheelPad':2, 
            'labelCfg':{'text':'alpha'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype='None', name='patches')
        
        code = """def doit(self, x, y, z, cmap, shading, alpha, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    #pseudo color plot of Z
    Qz=z
    cmap = cm.get_cmap(cmap)
    if x==None or y==None:
        C=self.axes.pcolor_classic(Qz,cmap=cmap,shading=shading,alpha=alpha)
    else:
        #a pseudo color plot of Z on the matrices X and Y
        Qx,Qy=array(x),array(y)
        C=self.axes.pcolor_classic(Qx,Qy,Qz,cmap=cmap,shading=shading,alpha=alpha)
    
    self.canvas.draw()
    self.outputData(axes=self.axes,patches=C)
"""
        self.setFunction(code)
        
class ContourNE(MPLPlottingNode):
    """contour and contourf draw contour lines and filled contours.
input:
    arraylistx      :array 
    arraylisty      :array
    arraylistz      :array
optional arguements:
    length_colors   : no of colors required to color contour
    cmap            :a cm Colormap instance from matplotlib.cm.
    origin          :'upper'|'lower'|'image'|None.
    linewidth       :linewidth
    hold:
    contour(Z) make a contour plot of n arrayZ
    contour(X,Y,Z) X,Y specify the (x,y) coordinates of the surface
    
"""
    
    def __init__(self, name='Contour', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', required=False, name='arraylistx')
        ip.append(datatype='None', required=False,name='arraylisty')
        ip.append(datatype='None', name='arraylistz',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string', required=False,  name='contour', defaultValue='default')
        ip.append(datatype='int', required=False, name='length_colors')
        ip.append(datatype='string', required=False, name='cmap', defaultValue='jet')
        ip.append(datatype='string', required=False, name='colors', defaultValue='black')
        ip.append(datatype='string', required=False, name='origin', defaultValue='upper')
        ip.append(datatype='int', required=False, name='linewidth', defaultValue=1)
        ip.append(datatype='boolean', required=False, name='hold', defaultValue=0)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['contour'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['default','filledcontour'],
            'fixedChoices':True,
            'initialValue':'default',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'contour:'}}
        self.widgetDescr['length_colors'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'no. of colors:'},
            'initialValue':10}
        self.widgetDescr['cmap'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cmaps,
            'fixedChoices':True,
            'initialValue':'jet',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'cmap:'}}
        self.widgetDescr['colors'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'black',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'colors:'}}
        self.widgetDescr['linewidth'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':4, 'type':'int', 
	        'initialValue':1, 'wheelPad':2,
            'labelCfg':{'text':'linewidth'} }    
        self.widgetDescr['origin'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['upper','lower','image',None],
            'fixedChoices':True,
            'initialValue':'upper',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'origin:'}}
        
        self.widgetDescr['hold'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'hold'},
            'initialValue':0,}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype='None', name='contour')
        code = """def doit(self, arraylistx, arraylisty, arraylistz, contour,
length_colors, cmapval, colors, origin, linewidth, hold, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)            
    axes_list=self.axes.figure.axes
    if len(axes_list):
        for i in axes_list:
          if not isinstance(i,Subplot):
            self.axes.figure.delaxes(i)
    import numpy
    #Z=10.0*(numpy.array(z2) - numpy.array(z1))
    Z=arraylistz
    if length_colors:
        cmap = cm.get_cmap(cmapval,int(length_colors))
    else:
        cmap=eval("cm.%s" %cmapval)
    if arraylistx==None or arraylisty==None:
        #contour plot of an array Z
        if contour=='default':    
            CS=self.axes.contour(Z,cmap=cmap,linewidths=linewidth,origin=origin,hold=hold)
            self.axes.clabel(CS,inline=1)
        else:
            CS=self.axes.contourf(numpy.array(Z),cmap=cmap,origin=origin)
    else:
        #(x,y) coordinates of the surface
        X=numpy.array(arraylistx)
        Y=numpy.array(arraylisty)
        if contour=='default':
            CS=self.axes.contour(X,Y,Z,cmap=cmap,linewidths=linewidth,origin=origin,hold=hold) 
            self.axes.clabel(CS,inline=1)    
        else:
            CS=self.axes.contourf(X,Y,numpy.array(Z),cmap=cmap,origin=origin)
    self.canvas.draw()
    self.outputData(axes=self.axes,contour=CS)
"""
        self.setFunction(code)
        
class SpecgramNE(MPLPlottingNode):
    """plots a spectrogram of data in arraylistx.
NFFT    -   Data are split into NFFT length segements 
Fs      -   samplingFrequency
cmap    -   colormap
nOverlap-   the amount of overlap of each segment.
Returns  im
im is a matplotlib.image.AxesImage    
""" 
    def __init__(self, name='Specgram', **kw):
       
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='arraylistx',singleConnection='auto',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='int', name='NFFT', defaultValue=256)
        ip.append(datatype='int', name='Fs', defaultValue=2)
        ip.append(datatype='string', required=False, name='cmap')
        ip.append(datatype='int', name='nOverlap', defaultValue=128)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['NFFT'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'NFFT (powOf 2):'},'width':10,
            'type':'int',
            'initialValue':256}
            
        self.widgetDescr['Fs'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':2,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Fs'} }
        self.widgetDescr['cmap'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cmaps,
            'fixedChoices':True,
            'initialValue':'jet',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'cmap:'}}
        self.widgetDescr['nOverlap'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'nOverlap:'},'width':10,
            'type':'int','labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype=None,name='image')
        code="""def doit(self, x, NFFT, Fs, cmapval, nOverlap, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    cmap=eval("cm.%s" %cmapval)
    Pxx, freqs, bins, im=self.axes.specgram(x, NFFT=int(NFFT), Fs=Fs,cmap=cmap,noverlap=int(nOverlap))
    self.canvas.draw()
    self.outputData(axes=self.axes,image=im)
"""
        self.setFunction(code)

class CSDNE(MPLPlottingNode):
    """plots a cross spectral density of data in arraylistx,arraylisty.
NFFT    -   Data are split into NFFT length segements 
Fs      -   samplingFrequency
nOverlap-   the amount of overlap of each segment.
"""
    def __init__(self, name='CSD', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype=None, name='arraylistx',singleConnection='auto',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype=None, name='arraylisty',singleConnection='auto',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='int', name='NFFT', defaultValue=256)
        ip.append(datatype='int', name='Fs', defaultValue=2)
        ip.append(datatype='int', name='nOverlap', defaultValue=128)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['NFFT'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'NFFT (powOf 2):'},'width':10,
            'type':'int',
            'initialValue':256}
            
        self.widgetDescr['Fs'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':2,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Fs'} }
        
        self.widgetDescr['nOverlap'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'nOverlap:'},'width':10,
            'type':'int','labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code="""def doit(self, arraylistx, arraylisty, NFFT, Fs, nOverlap,
drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    Pxx, freqs=self.axes.csd(arraylistx,arraylisty, NFFT=int(NFFT), Fs=Fs,noverlap=int(nOverlap))
    self.canvas.draw()
    self.outputData(axes=self.axes)
"""
        self.setFunction(code)
       
class PSDNE(MPLPlottingNode):
    """plots a cross spectral density of data in arraylistx.
NFFT    -   Data are split into NFFT length segements 
Fs      -   samplingFrequency
nOverlap-   the amount of overlap of each segment.
"""
    def __init__(self, name='PSD', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype=None, name='arraylistx',singleConnection='auto',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='int', required=False,name='NFFT', defaultValue=256)
        ip.append(datatype='int', required=False,name='Fs', defaultValue=2)
        ip.append(datatype='int', required=False,name='nOverlap', defaultValue=0)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['NFFT'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'NFFT (powOf 2):'},'width':10,
            'type':'int',
            'initialValue':256}
            
        self.widgetDescr['Fs'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':2,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Fs'}}
        
        self.widgetDescr['nOverlap'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelCfg':{'text':'nOverlap:'},'width':10,
            'type':'int','labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code="""def doit(self, x, NFFT, Fs, nOverlap, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    self.axes.psd(x,NFFT=int(NFFT), Fs=Fs,noverlap=int(nOverlap))
    self.canvas.draw()
    self.outputData(axes=self.axes)
"""
        self.setFunction(code)
        
class LogCurveNE(MPLPlottingNode):
    """This node is to make a loglog plot with log scaling on the x and y axis.
input:
x      - list
y      - list
basex  - base of the x logarithm
basey  - base of the y logarithm
"""
       
    def __init__(self, name='LogCurve', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='string',required=False, name='logCurve', defaultValue='log')
        ip.append(datatype='float',required=False, name='basex', defaultValue=10)
        ip.append(datatype='float',required=False, name='basey', defaultValue=10)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['logCurve'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['logbasex','logbasey'],
            'fixedChoices':True,
            'initialValue':'logbasex',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'logCurve:'}}
        self.widgetDescr['basex'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':10,
            'labelCfg':{'text':'basex'} }
        self.widgetDescr['basey'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':10,
            'labelCfg':{'text':'basey'} }    
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code="""def doit(self, x, y, logCurve, basex, basey, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    if logCurve=="logbasex":
        log_curve=self.axes.loglog(x,y,basex=basex)
    else:
        log_curve=self.axes.loglog( x,y,basey=basey)
    
    self.canvas.draw()
    self.outputData(axes=self.axes)
"""
        self.setFunction(code)
        
class SemilogxNE(MPLPlottingNode):
    """This node is to make a semilog plot with log scaling on the xaxis.
input:
    x      - list
    basex  - base of the x logarithm
    """
       
    def __init__(self, name='Semilogx', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='float',required=False, name='basex', defaultValue=10)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['basex'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':10,
            'labelCfg':{'text':'basex'} }
            
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code="""def doit(self, x, y, basex, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    self.axes.semilogx(x,y,basex=basex)
    self.canvas.draw()
    self.outputData(axes=self.axes)
"""
        self.setFunction(code)
        
class SemilogyNE(MPLPlottingNode):
    """This node is to make a semilog plot with log scaling on the y axis.
input:
    y      - list
    basey  - base of the y logarithm
    """
       
    def __init__(self, name='Semilogy', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='float',required=False, name='basey', defaultValue=10)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['basey'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':10,
            'labelCfg':{'text':'basey'} }
            
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code="""def doit(self, x, y, basey, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    self.axes.semilogy(x,y,basey=basey)
    self.canvas.draw()
    self.outputData(axes=self.axes)
"""
        self.setFunction(code)

class BoxPlotNE(MPLPlottingNode):
    """ To plot a box and whisker plot for each column of x.
The box extends from the lower to upper quartile values
of the data, with a line at the median.  The whiskers
extend from the box to show the range of the data.  Flier
points are those past the end of the whiskers.
input:
        x       -       Numeric array
optional arguements:
        notch   -       notch = 0 (default) produces a rectangular box plot.
                        notch = 1 will produce a notched box plot
        sym     -       (default 'b+') is the default symbol for flier points.
                        Enter an empty string ('') if you dont want to show fliers.
        vert    -       vert = 1 (default) makes the boxes vertical.
                        vert = 0 makes horizontal boxes.  This seems goofy, but
                        thats how Matlab did it.
        whis    -       (default 1.5) defines the length of the whiskers as
                        a function of the inner quartile range.  They extend to the
                        most extreme data point within ( whis*(75%-25%) ) data range.
        positions-      (default 1,2,...,n) sets the horizontal positions of
                        the boxes. The ticks and limits are automatically set to match
                        the positions.
        widths    -     either a scalar or a vector and sets the width of
                        each box. The default is 0.5, or 0.15*(distance between extreme
                        positions) if that is smaller.
        
Returns a list of the lines added
"""
    def __init__(self, name='BoxPlot', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list', name='x',singleConnection='auto',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='list', required=False, name='positions')
        ip.append(datatype=None, required=False, name='widths', defaultValue=.15)
        ip.append(datatype='boolean', required=False, name='notch', defaultValue=0)
        ip.append(datatype='boolean', required=False, name='vert', defaultValue=0)
        ip.append(datatype='string', required=False, name='color', defaultValue='b')
        ip.append(datatype='string', required=False, name='linestyle', defaultValue='-')
        ip.append(datatype='float', required=False, name='whis', defaultValue=1.5)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['notch'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'notch:'},'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0,}
        self.widgetDescr['vert'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'vert:'},'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0,}
        self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'color:'}}
        self.widgetDescr['linestyle'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':get_styles().values(),
            'fixedChoices':True,
            'initialValue':'-',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'linestyle:'}}
        self.widgetDescr['whis'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':1.5,'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'whis'} }    
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype=None, name='lines')
        code="""def doit(self, x, positions, widths, notch, vert, color, linestyle,
whis, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    sym=color+linestyle
    ll=self.axes.boxplot(x,notch=notch, sym=sym, vert=vert, whis=whis,positions=positions,widths=widths)
    self.canvas.draw()
    self.outputData(axes=self.axes,lines=ll) """
        self.setFunction(code)


class BarNE(MPLPlottingNode):
    """Plots a horizontal bar plot with rectangles bounded by
left, left+width, bottom, bottom+height  (left, right, bottom and top edges)
bottom, width, height, and left can be either scalars or sequences
input:
     height      -   the heights (thicknesses) of the bars
    left        -   the x coordinates of the left edges of the bars
    
Optional arguments:
    bottom      -   can be either scalars or sequences
    width       -   can be either scalars or sequences
    color       -    specifies the colors of the bars
    edgecolor   -    specifies the colors of the bar edges
    xerr        -    if not None, will be used to generate errorbars
                    on the bar chart
    yerr        -    if not None, will be used to generate errorbars
                    on the bar chart
    ecolor      -   specifies the color of any errorbar
    capsize     -       determines the length in points of the error bar caps
    align       - 'edge' | 'center'
                  'edge' aligns the horizontal bars by their bottom edges in bottom, while
                  'center' interprets these values as the y coordinates of the bar centers.
Return value is a list of Rectangle patch instances
"""
    def __init__(self, name='Bar', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None',  name='left',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None',  name='height',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False,name='bottom', defaultValue=0)    
        ip.append(datatype='None', required=False,name='width', defaultValue=.8)
        ip.append(datatype='None', required=False, name='xerr')    
        ip.append(datatype='None', required=False, name='yerr')
        ip.append(datatype='string', required=False, name='color', defaultValue='b')
        ip.append(datatype='string', required=False, name='edgecolor', defaultValue='b')
        ip.append(datatype='string', required=False, name='ecolor', defaultValue='b')
        ip.append(datatype='int', required=False, name='capsize', defaultValue=3)
        ip.append(datatype='list', required=False, name='align', defaultValue='edge')
        ip.append(datatype='list', required=False, name='orientation', defaultValue='vertical')
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
            
        self.widgetDescr['align'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['edge','center'], 
            'fixedChoices':True,
            'initialValue':'edge',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'align:'}}
        self.widgetDescr['orientation'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['vertical','horizontal'], 
            'fixedChoices':True,
            'initialValue':'vertical',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'orientation:'}}
        self.widgetDescr['edgecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'edgecolor:'}}
        self.widgetDescr['ecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'ecolor:'}}
        self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'color:'}}
        self.widgetDescr['capsize'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':3,'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'capsize'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype=None, name='patches')
        code="""def doit(self, left, height, bottom, width, xerr, yerr, color,
edgecolor, ecolor, capsize, align, orientation, drawAreaDef):        
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    patches=self.axes.bar(left,height,bottom=bottom, width=width, 
             color=color, edgecolor=edgecolor, xerr=xerr, yerr=yerr, ecolor=ecolor, capsize=capsize,
             align=align,orientation=orientation)        
    self.canvas.draw()
    self.outputData(axes=self.axes,patches=patches) """
        self.setFunction(code)


class BarHNE(MPLPlottingNode):
    """Plots a horizontal bar plot with rectangles bounded by
left, left+width, bottom, bottom+height  (left, right, bottom and top edges)
bottom, width, height, and left can be either scalars or sequences
input:
    bottom      -   can be either scalars or sequences
    width       -   can be either scalars or sequences
Optional arguments:
    height      -   the heights (thicknesses) of the bars
    left        -   the x coordinates of the left edges of the bars
    color       -    specifies the colors of the bars
    edgecolor   -    specifies the colors of the bar edges
    xerr        -    if not None, will be used to generate errorbars
                    on the bar chart
    yerr        -    if not None, will be used to generate errorbars
                    on the bar chart
    ecolor      -   specifies the color of any errorbar
    capsize     -       determines the length in points of the error bar caps
    align       - 'edge' | 'center'
                  'edge' aligns the horizontal bars by their bottom edges in bottom, while
                  'center' interprets these values as the y coordinates of the bar centers.
Return value is a list of Rectangle patch instances
"""
    def __init__(self, name='BarH', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='bottom',beforeDisconnect=self.codeBeforeDisconnect)    
        ip.append(datatype='None', name='width',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False, name='height', defaultValue=.8)
        ip.append(datatype='None', required=False, name='left', defaultValue=0)
        ip.append(datatype='None', required=False, name='xerr')    
        ip.append(datatype='None', required=False, name='yerr')
        ip.append(datatype='string', required=False, name='color', defaultValue='b')
        ip.append(datatype='string', required=False, name='edgecolor', defaultValue='b')
        ip.append(datatype='string', required=False, name='ecolor', defaultValue='b')
        ip.append(datatype='int', required=False, name='capsize', defaultValue=3)
        ip.append(datatype='list', required=False, name='align', defaultValue='edge')
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
            
        self.widgetDescr['align'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['edge','center'], 
            'fixedChoices':True,
            'initialValue':'edge',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'align:'}}
        self.widgetDescr['edgecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'edgecolor:'}}
        self.widgetDescr['ecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'ecolor:'}}
        self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'color:'}}
        self.widgetDescr['capsize'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':3,'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'capsize'} }
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        op.append(datatype=None, name='patches')
        code="""def doit(self, bottom, width, height, left, xerr, yerr, color,
edgecolor, ecolor, capsize, align, drawAreaDef):        
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    patches=self.axes.barh(bottom, width, height=height, left=left,
             color=color, edgecolor=edgecolor, xerr=xerr, yerr=yerr, ecolor=ecolor, capsize=capsize,
             align=align)        
    self.canvas.draw()
    self.outputData(axes=self.axes,patches=patches) """
        self.setFunction(code)

class QuiverNE(MPLPlottingNode):
    """Makes a vector plot (U, V) with arrows on a grid (X, Y) 
If X and Y are not specified, U and V must be 2D arrays.  Equally spaced
X and Y grids are then generated using the meshgrid command.
color  -color 
S      -used to scale the vectors.Use S=0 to disable automatic scaling.
        If S!=0, vectors are scaled to fit within the grid and then are multiplied by S.
pivot  -'mid','tip' etc
units  - 'inches','width','x','y'
width  - a scalar that controls the width of the arrows
"""
    def __init__(self, name='Quiver', **kw):
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        
        ip.append(datatype='None', name='u',beforeDisconnect=self.codeBeforeDisconnect)    
        ip.append(datatype='None', name='v',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False,name='x')    
        ip.append(datatype='None', required=False,name='y')
        ip.append(datatype='None', required=False, name='color')
        ip.append(datatype='float', required=False, name='S', defaultValue=.2)
        ip.append(datatype='float', required=False, name='width', defaultValue=1.)
        ip.append(datatype='string', required=False, name='pivot', defaultValue='tip')
        ip.append(datatype='string', required=False, name='units', defaultValue='inches')
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['color'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'color:'}}
        self.widgetDescr['S'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1,
            'type':'float','precision':3,
            'wheelPad':2, 'initialValue':0.20,'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'S'} }
        self.widgetDescr['width'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1,
            'type':'float','precision':3,
            'wheelPad':2, 'initialValue':0.002,'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'width'} }
        
        self.widgetDescr['pivot'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['tip','mid'], 
            'fixedChoices':True,
            'initialValue':'tip',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'pivot:'}}
        self.widgetDescr['units'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['inches','width','x','y'], 
            'fixedChoices':True,
            'initialValue':'units',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'units:'}}    
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')    
        code="""def doit(self, u, v, x, y, color, S, width, pivot, units, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    if x!=None:
        self.axes.quiver(x,y,u,v,S,pivot=pivot,color=color,width=width,units=units)
    else:
        self.axes.quiver(u,v,S,color=color,width=width,units=units)
    self.canvas.draw()
    self.outputData(axes=self.axes) """
        self.setFunction(code)
    
        
class ErrorBarNE(MPLPlottingNode):
    """Plot x versus y with error deltas in yerr and xerr.
Vertical errorbars are plotted if yerr is not None
Horizontal errorbars are plotted if xerr is not None.
input:
    x       -       scalar or sequence of vectors
    y       -       scalar or sequence of vectors
    xerr    -       scalar or sequence of vectors, plots a single error bar at x, y.,default is None
    yerr    -       scalar or sequence of vectors, plots a single error bar at x, y.,default is None
    
optional arguements:
    controlmarkers - controls errorbar markers(with props: markerfacecolor, markeredgecolor, markersize and
                  markeredgewith)
    fmt      -   plot format symbol for y.  if fmt is None, just
                 plot the errorbars with no line symbols.  This can be useful
                 for creating a bar plot with errorbars
    ecolor   -   a matplotlib color arg which gives the color the
                 errorbar lines; if None, use the marker color.
    capsize  -   the size of the error bar caps in points
    barsabove-   if True, will plot the errorbars above the plot symbols
                 default is below
"""
    def __init__(self, name='ErrorBar', **kw):
        
        kw['name'] = name
        apply( MPLPlottingNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='x',beforeDisconnect=self.codeBeforeDisconnect)    
        ip.append(datatype='None', name='y',beforeDisconnect=self.codeBeforeDisconnect)
        ip.append(datatype='None', required=False, name='xerr')    
        ip.append(datatype='None', required=False, name='yerr')
        ip.append(datatype='string', required=False, name='format', defaultValue='b-')
        ip.append(datatype='string', required=False, name='ecolor', defaultValue='b')
        ip.append(datatype='int', required=False, name='capsize', defaultValue=3)
        ip.append(datatype='boolean', required=False, name='barsabove', defaultValue=0)
        ip.append(datatype='boolean', required=False, name='controlmarkers', defaultValue=0)
        ip.append(datatype='MPLDrawArea', required=False, name='drawAreaDef',singleConnection=False)
        self.widgetDescr['format'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':get_styles().values(),
            'fixedChoices':True,
            'initialValue':'-',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'format:'}}
        
        self.widgetDescr['ecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':colors.values(), 
            'fixedChoices':True,
            'initialValue':'b',          
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'ecolor:'}}
        self.widgetDescr['capsize'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':1, 'type':'float',
            'wheelPad':2, 'initialValue':3,'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'capsize'} }    
        self.widgetDescr['barsabove'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'barsabove:'},'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0,}    
        self.widgetDescr['controlmarkers'] = {
            'class':'NECheckButton', 'master':'node',
            'labelCfg':{'text':'barsabove:'},'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'initialValue':0,}
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code="""def doit(self, x, y, xerr, yerr, format, ecolor, capsize,
barsabove, controlmarkers, drawAreaDef):
    self.axes.clear()
    self.setDrawAreaDef(drawAreaDef)
    fmt=ecolor+format
    if controlmarkers == 0:
        self.axes.errorbar(x,y,xerr=xerr,yerr=yerr,fmt=fmt,ecolor=ecolor,capsize=capsize,barsabove=barsabove)
    else:
        def set_markerparams(dAD):
            if dAD.has_key('marker'):
                marker = dAD['marker']
            else:
                marker = 'solid'
            if dAD.has_key('markerfacecolor'):   
                markerfacecolor = dAD['markerfacecolor']
            else:
                markerfacecolor = 'blue'
            if dAD.has_key('markeredgecolor'): 
                markeredgecolor = dAD['markeredgecolor']
            else:
                markeredgecolor = 'blue'
            if dAD.has_key('markersize'):
                markersize = dAD['markersize']  
            else:
                markersize = 6
            if dAD.has_key('makeredgewidth'):
                makeredgewidth = dAD['makeredgewidth']
            else:
                makeredgewidth = 0.5
            return marker,markerfacecolor,markeredgecolor,markersize,makeredgewidth
        if drawAreaDef:
            markerdict={}
            if len(drawAreaDef) == 1 and type(drawAreaDef[0])==types.DictType:
                for d in drawAreaDef[0].keys():
                    if d[:6]=="marker":
                        markerdict[d]=drawAreaDef[0][d]
            if len(drawAreaDef)>1:
                for dAD in drawAreaDef:
                    if type(dAD) == types.DictType:
                        for d in dAD.keys():
                            if d[:6]=="marker":
                                markerdict[d]=dAD[d]
                
        if markerdict!={}:          
            marker,markerfacecolor,markeredgecolor,markersize,makeredgewidth=set_markerparams(markerdict)
            self.axes.errorbar(x, y, xerr=xerr,yerr=yerr, marker=marker,
                           mfc=markerfacecolor, mec=markeredgecolor, ms=markersize, mew=makeredgewidth)
    self.canvas.draw()
    self.outputData(axes=self.axes) """
        self.setFunction(code)
        
        
        
###########################################################################
#
# Nodes generating data for demos
#
###########################################################################

class RandNormDist(NetworkNode):
    """
Outputs values describing a randomized normal distribution

Input:
    mu    - 
    sigma - 
    dpi   - number of value points

Output:
    data:  list of values
    mu    - 
    sigma - 
"""
    def __init__(self, name='RandNormDist', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='float', name='mu')
        ip.append(datatype='float', name='sigma')
        ip.append(datatype='int', name='npts')
   
        self.widgetDescr['mu'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':100,
            'labelCfg':{'text':'mu'} }

        self.widgetDescr['sigma'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':15,
            'labelCfg':{'text':'sigma'} }

        self.widgetDescr['npts'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':1000, 'type':'int',
            'wheelPad':2, 'initialValue':10000,
            'labelCfg':{'text':'nb. points'} }

	op = self.outputPortsDescr
        op.append(datatype='list', name='data')
        op.append(datatype='float', name='mu')
        op.append(datatype='float', name='sigma')

        code = """def doit(self, mu, sigma, npts):
    from numpy.oldnumeric.mlab import randn
    self.outputData( data=mu+sigma*randn(npts), mu=mu, sigma=sigma )
"""
        self.setFunction(code)



class SinFunc(NetworkNode):
    """
Outputs values describing a sinusoidal function.

Input:
    start  -  first x value 
    end    -  last x value
    step   -  step size

Output:
    x:  list x values
    y = list of y values
"""
    def __init__(self, name='SinFunc', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='float', name='x0')
        ip.append(datatype='float', name='x1')
        ip.append(datatype='float', name='step')
   
        self.widgetDescr['x0'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10., 'type':'float',
            'wheelPad':2, 'initialValue':0.,
            'labelCfg':{'text':'x0'} }

        self.widgetDescr['x1'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10., 'type':'float',
            'wheelPad':2, 'initialValue':3.,
            'labelCfg':{'text':'x1'} }

        self.widgetDescr['step'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':10., 'type':'float',
            'wheelPad':2, 'initialValue':0.01,
            'labelCfg':{'text':'nb. points'} }

	op = self.outputPortsDescr
        op.append(datatype='list', name='x')
        op.append(datatype='list', name='y')

        code = """def doit(self, x0, x1, step):
    import numpy
    x = numpy.arange(x0, x1, step)
    y = numpy.sin(2*numpy.pi*x)
   
    self.outputData( x=x, y=y)
"""
        self.setFunction(code)



class SinFuncSerie(NetworkNode):
    """
Outputs a list of y values of a sinusoidal function

Input:

Output:
    x:  list y values
"""
    def __init__(self, name='SinFuncSerie', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

##         ip = self.inputPortsDescr
##         ip.append(datatype='float', name='x0')
##         ip.append(datatype='float', name='x1')
##         ip.append(datatype='float', name='step')
   
##         self.widgetDescr['x0'] = {
##             'class':'NEThumbWheel','master':'node',
##             'width':75, 'height':21, 'oneTurn':10., 'type':'float',
##             'wheelPad':2, 'initialValue':0.,
##             'labelCfg':{'text':'x0'} }

##         self.widgetDescr['x1'] = {
##             'class':'NEThumbWheel','master':'node',
##             'width':75, 'height':21, 'oneTurn':10., 'type':'float',
##             'wheelPad':2, 'initialValue':3.,
##             'labelCfg':{'text':'x1'} }

## 
##        self.widgetDescr['step'] = {
##             'class':'NEThumbWheel','master':'ParamPanel',
##             'width':75, 'height':21, 'oneTurn':10., 'type':'float',
##             'wheelPad':2, 'initialValue':0.01,
##             'labelCfg':{'text':'nb. points'} }

	op = self.outputPortsDescr
        op.append(datatype='list', name='X')

        code = """def doit(self):
    import numpy
    ind = numpy.arange(60)

    x_tmp=[]
    for i in range(100):
        x_tmp.append(numpy.sin((ind+i)*numpy.pi/15.0))

    X=numpy.array(x_tmp)

    self.outputData(X=X)
"""
        self.setFunction(code)

class MatPlotLibOptions(NetworkNode):
    """This node allows to set various rendering Options.
    Choose a category from,
    Axes,Font,Figure,Text,Tick,Grid,Legend.
    if "Grid" choosen,allows you to set following properties
    gridOn/Off,gridlinewidth,gridlinestyle,gridcolor,whichgrid major/minor.
    To ignore any property rightclick on property(sets to default value when
    ignored)
    """
    def __init__(self, name='Set Matplotlib Options', canvas=None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(name='matplotlibOptions', datatype='dict')

        self.widgetDescr['matplotlibOptions'] = {
            'class':'NEMatPlotLibOptions', 'lockedOnPort':True}      
	op = self.outputPortsDescr
        op.append(datatype='dict', name='matplotlibOptions')

        code = """def doit(self, matplotlibOptions):
        self.outputData(matplotlibOptions=matplotlibOptions)
"""
        self.setFunction(code)


class NEMatPlotLibOptions(PortWidget):
    configOpts = PortWidget.configOpts.copy()
    ownConfigOpts = {}
    ownConfigOpts['initialValue'] = {
        'defaultValue':{}, 'type':'dict',
        }

    configOpts.update(ownConfigOpts)

    def __init__(self, port, **kw):
        
        # call base class constructor
        apply( PortWidget.__init__, (self, port), kw)
        
        colors=cnames
        self.styles=lineStyles
        self.markers = markers
        from DejaVu import viewerConst
        self.main_props=['Axes','Font','Text','Figure','Tick','Grid','Legend']#,'MathText',
        self.booleanProps =['axisbelow','gridOn','figpatch_antialiased','text.usetex','text.dvipnghack',
                            'hold','legend.isaxes','legend.shadow','mathtext.mathtext2']#visible
        if mplversion[0]==0 and mplversion[2]<=3:
            self.twProps=['linewidth','xtick.labelsize','xtick.labelrotation','ytick.labelsize',
                          'ytick.labelrotation','gridlinewidth','figpatch_linewidth','markeredgewidth',
                          #'zoomx','zoomy',
                          'legend.numpoints','legend.pad','legend.markerscale','legend.handlelen',
                          'legend.axespad','legend.labelsep','legend.handletextsep','xtick.major.size',
                          'ytick.major.size','xtick.minor.size','ytick.minor.size','xtick.major.pad',
                          'ytick.major.pad','xtick.minor.pad','ytick.minor.pad','font.size']
        elif mplversion[0] > 0:
            self.twProps=['linewidth','xtick.labelsize','xtick.labelrotation','ytick.labelsize',
                          'ytick.labelrotation','gridlinewidth','figpatch_linewidth','markeredgewidth',
                          #'zoomx','zoomy',
                          'legend.numpoints','legend.borderpad','legend.markerscale','legend.handlelength',
                          'legend.borderaxespad','legend.labelspacing','legend.handletextpad','xtick.major.size',
                          'ytick.major.size','xtick.minor.size','ytick.minor.size','xtick.major.pad',
                          'ytick.major.pad','xtick.minor.pad','ytick.minor.pad','font.size']
        self.choiceProps ={'facecolor':tuple(colors.keys()),
        'edgecolor':tuple(colors.keys()),
        'gridcolor':tuple(colors.keys()),
        'xtick.color':tuple(colors.keys()),
        'ytick.color':tuple(colors.keys()),
        'figpatch_facecolor':tuple(colors.keys()),
        'figpatch_edgecolor':tuple(colors.keys()),
        'marker':tuple(self.markers.values()),
        'markeredgecolor':tuple(colors.keys()),
        'markerfacecolor':tuple(colors.keys()),
        'gridlinestyle':tuple(self.styles.keys()),
        'adjustable':('box','datalim'),
        'anchor':('C', 'SW', 'S', 'SE', 'E', 'NE', 'N', 'NW', 'W'),
        'aspect':('auto', 'equal' ,'normal',),
        'text.color':tuple(colors.keys()),
        'text.fontstyle':('normal',),
        'text.fontvariant':('normal',),
        'text.fontweight':('normal',),
        'text.fontsize':('medium','small','large'),
        'xtick.direction':('in','out'),
        'ytick.direction':('in','out'),
        'text.fontangle':('normal',),
        'font.family':('serif',),
        'font.style':('normal',),
        'font.variant':('normal',),
        'font.weight':('normal',),
        'mathtext.rm':('cmr10.ttf',),
        'mathtext.it':('cmmi10.ttf',),
        'mathtext.tt':('cmtt10.ttf',),
        'mathtext.mit':('cmmi10.ttf',),
        'mathtext.cal':('cmsy10.ttf',),
        'mathtext.nonascii' : ('cmex10.ttf',),
        'legend.fontsize':('small','medium','large'),
        'titlesize':('large','medium','small'),
        'whichgrid':('minor','major')
        }
        

        self.frame = Tkinter.Frame(self.widgetFrame, borderwidth=3,
                                   relief = 'ridge')

        self.propWidgets = {} # will hold handle to widgets created
        self.optionsDict = {} # widget's value
        self.labels={}
        self.delvar=0
        self.new_list_to_add=[] 
        self.delete_proplist=[]

        self.initialvalues={'font.family':'serif','font.style':'normal','font.variant':'normal',
                            'font.weight':'normal','font.size':12.0,'text.color':'black','text.usetex':False,
                            'text.dvipnghack':False,'text.fontstyle':'normal','text.fontangle':'normal',
                            'text.fontvariant':'normal','text.fontweight':'normal','text.fontsize':'medium',
                            'axisbelow':False,'hold':True,'facecolor':'white','edgecolor':'black','linewidth':1,
                            'titlesize':'large','gridOn':False,'legend.isaxes':True,'legend.numpoints':4,
                            'legend.fontsize':"small",'legend.markerscale':0.6,
                            #'legend.pad':0.2,'legend.labelsep':0.005, 'legend.handlelen':0.05,
                            #'legend.handletextsep':0.02, 'legend.axespad':0.02,
                            'legend.shadow':True,'xtick.major.size':5,'xtick.minor.size':2,
                            'xtick.major.pad':3,'xtick.minor.pad':3,'xtick.labelsize':10,'xtick.labelrotation':0,
                            'ytick.labelsize':10,'ytick.labelrotation':0, 'xtick.color':'black','xtick.direction':'in',
                            'ytick.major.size':5,'ytick.minor.size':2,'ytick.major.pad':3,'ytick.minor.pad':3,
                            'ytick.color':'black','ytick.direction':'in','gridcolor':'black','gridlinestyle':':',
                            'gridlinewidth':0.5,'whichgrid':'major','mathtext.mathtext2':False,'mathtext.rm': 'cmr10.ttf',
                            'mathtext.it':'cmmi10.ttf','mathtext.tt':'cmtt10.ttf','mathtext.mit':'cmmi10.ttf',
                            'mathtext.cal':'cmsy10.ttf','mathtext.nonascii' : 'cmex10.ttf','figpatch_linewidth':1.0,
                            'figpatch_facecolor':'darkgray','figpatch_edgecolor':'white','marker':'s','markeredgewidth':0.5,
                            'markeredgecolor':'black','markerfacecolor':'blue',
                            #'zoomx':0,'zoomy':0,
                            'adjustable':'box','aspect':'auto','anchor':'C','figpatch_antialiased':False}
        if mplversion[0]==0 and mplversion[2]<=3:
            self.initialvalues.update({'legend.pad':0.2, 'legend.labelsep':0.005, 'legend.handlelen':0.05, 'legend.handletextsep':0.02,  'legend.axespad':0.02})
        elif mplversion[0]>0:
            self.initialvalues.update({'legend.borderpad':0.2, 'legend.labelspacing':0.005,  'legend.handlelength':0.05, 'legend.handletextpad':0.02,   'legend.borderaxespad':0.02} )
 
        import Pmw
        #items = self.booleanProps +self.choiceProps.keys()+self.twProps
        items=self.main_props
        w = Pmw.Group(self.frame, tag_text='Choose a Category')
        val=items[0]
        cb=CallBackFunction(self.properties_list, (val,))
        
        self.chooser = Pmw.ComboBox(
            w.interior(), label_text='', labelpos='w',
            entryfield_entry_width=20, scrolledlist_items=items,selectioncommand=cb)
        self.chooser.pack(padx=2, pady=2, expand='yes', fill='both')
 	w.pack(fill = 'x', expand = 1, side='top')
        # configure without rebuilding to avoid enless loop
        apply( self.configure, (False,), kw)
        self.frame.pack(expand='yes', fill='both')
        w1 = Pmw.Group(self.frame, tag_text='choose a Property')
        self.propWidgetMaster = w1.interior()
         
        
        cb = CallBackFunction( self.mainChoices, (val,))
        self.chooser1 = Pmw.ComboBox(w1.interior(), label_text='', labelpos='w',entryfield_entry_width=20, scrolledlist_items=self.new_list_to_add,selectioncommand=cb)
        self.chooser1.pack(padx=2, pady=2, expand='yes', fill='both')
        w1.pack(fill = 'x', expand = 1, side='top')
        self.chooser1.grid(row=len(self.propWidgets), column=1, sticky='w')
        if self.initialValue is not None:
            self.set(self.initialValue, run=0)
        self._setModified(False) # will be set to True by configure method
        

    def properties_list(self,prop1,prop2):
             
            prop=prop2
            if prop=='Text':
                list_to_add=['text.color','text.usetex','text.dvipnghack','text.fontstyle','text.fontangle','text.fontvariant','text.fontweight','text.fontsize']    
            elif prop=='Axes':
                list_to_add=['axisbelow','hold','facecolor','edgecolor','linewidth','titlesize','marker','markeredgewidth','markeredgecolor','markerfacecolor',
                             #'zoomx','zoomy',
                             'adjustable','anchor','aspect']
            elif prop=='Grid':
                list_to_add=['gridOn','gridlinewidth','gridcolor','gridlinestyle','whichgrid']
            elif  prop=='Legend':
                if mplversion[0]==0 and mplversion[2]<=3:
                    list_to_add=['legend.isaxes','legend.numpoints','legend.fontsize','legend.pad','legend.markerscale','legend.labelsep','legend.handlelen','legend.handletextsep','legend.axespad','legend.shadow']
                elif mplversion[0] > 0:
                    list_to_add=['legend.isaxes','legend.numpoints','legend.fontsize','legend.borderpad','legend.markerscale','legend.labelspacing','legend.handlelength','legend.handletextpad','legend.borderaxespad','legend.shadow']
            elif prop=="Tick":
                list_to_add=['xtick.major.pad','ytick.major.pad','xtick.minor.pad','ytick.minor.pad','xtick.color','ytick.color','xtick.labelsize','ytick.labelsize','xtick.labelrotation','ytick.labelrotation']
                #['xtick.major.size','ytick.major.size','xtick.minor.size','ytick.minor.size','xtick.major.pad','ytick.major.pad','xtick.minor.pad','ytick.minor.pad','xtick.color','ytick.color','xtick.size','ytick.size','xtick.direction','ytick.direction']
            elif prop=="Font":
                list_to_add=['font.family','font.style','font.variant','font.weight','font.size']
            elif prop=="MathText":
                list_to_add=['mathtext.mathtext2','mathtext.rm','mathtext.it','mathtext.tt','mathtext.mit',  'mathtext.cal','mathtext.nonascii' ,]
            elif prop=="Figure":
                list_to_add=['figpatch_antialiased','figpatch_linewidth','figpatch_edgecolor','figpatch_facecolor']
            
            self.new_list_to_add=list_to_add
            self.chooser1.setlist(self.new_list_to_add)
            
            
            
    def mainChoices(self,prop,val):
        self.addProp(val)
       
    def deleteProp(self):
        
        prop=self.property
        widget= self.propWidgets[prop][0]
        if prop in self.choiceProps:
            widget.selectitem(self.initialvalues[prop])
            widget.update_idletasks()
            self.setChoice((prop,), self.initialvalues[prop])
        if prop in  self.booleanProps:
            widget.deselect()
        if prop in  self.twProps:
            widget.setValue(self.initialvalues[prop]) 
            self.setTwValue(prop, self.initialvalues[prop])
        self.scheduleNode()
        widget.pack_forget()    
        widget.place_forget()
        widget.grid_forget()
        self.labels[prop].pack_forget()
        self.labels[prop].place_forget()
        self.labels[prop].grid_forget()
        del self.propWidgets[prop]
        del self.labels[prop]

    def addProp(self, prop):
        
        if self.propWidgets.has_key(prop):
            return
        
        labwidget = Tkinter.Label(self.propWidgetMaster, text=prop)
        
        rown=self.propWidgetMaster.size()[1]
        labwidget.grid(padx=2, pady=2, row=rown, column=0,
               sticky='w')
        self.labels[prop]=labwidget
        #Right Click Menu
        popup = Tkinter.Menu(labwidget, tearoff=0)
        #popup.add_command(label="ToolTip")
        #popup.add_separator()
        popup.add_command(label="Ignore",command=self.deleteProp)
        def do_popup(event):
        # display the popup menu
            self.property=labwidget['text'] 
            try:
                popup.tk_popup(event.x_root, event.y_root, 0)
            finally:
                popup.grab_release()
        labwidget.bind("<Button-3>", do_popup)
     
        if prop in self.booleanProps:
            var = Tkinter.IntVar()
            var.set(self.initialvalues[prop])
            cb = CallBackFunction( self.setBoolean, (prop, var))
            widget = Tkinter.Checkbutton(self.propWidgetMaster,
                                         variable=var, command=cb)
            if prop not in self.propWidgets:
                self.propWidgets[prop] = (widget, var.get())
            self.setBoolean( (prop, var) )
            
        elif prop in self.choiceProps:
        
            items = self.choiceProps[prop]
            var = None
            cb = CallBackFunction( self.setChoice, (prop,))
            widget = Pmw.ComboBox(
                self.propWidgetMaster,
                entryfield_entry_width=10,
                scrolledlist_items=items, selectioncommand=cb)
            if prop not in self.propWidgets:
                self.propWidgets[prop] = (widget, var)
            self.setChoice( (prop,), self.initialvalues[prop] )
                    
        elif prop in self.twProps:
            
            cb = CallBackFunction( self.setTwValue,prop) 
            val=self.initialvalues[prop]
            
            self.twwidget=widget =ThumbWheel(width=75, height=21,wheelPad=2,master=self.propWidgetMaster,labcfg={'fg':'black', 'side':'left', 'text':prop},min = 0.0,type='float',showlabel =1,continuous =0,oneTurn =10,value=val,callback=cb)
            if prop not in self.propWidgets:
                self.propWidgets[prop] = (widget,val)
       
        widget.grid(row=rown, column=1, sticky='w')
        
    def setTwValue(self,prop,val):
        self.optionsDict[prop] = val
        if self.port.node.paramPanel.immediateTk.get():
            self.scheduleNode()
            
    def setBoolean(self,args):
        prop, val = args
        #if type(val)==types.InstanceType:
        from mglutil.util.misc import isInstance
        if isInstance(val) is True:
            self.optionsDict[prop] = val.get()
        else:
            self.optionsDict[prop] = val
        if self.optionsDict[prop]==1:
            self.propWidgets[prop][0].select()
        else:
            self.propWidgets[prop][0].deselect()
        if self.port.node.paramPanel.immediateTk.get():
            self.scheduleNode()
        
    def setChoice(self, prop, value):
        self.optionsDict[prop[0]] = value
        self.propWidgets[prop[0]][0].selectitem(value)
        if self.port.node.paramPanel.immediateTk.get():
            self.scheduleNode()

    def set(self, valueDict, run=1):
        self._setModified(True)
        for k,v in valueDict.items():
            self.addProp(k)
            if k in self.booleanProps:
                self.setBoolean( (k, v) )
            elif k in self.choiceProps:
                self.setChoice((k,), v)
            else:
                self.setTwValue(k, v)
        self._newdata = True
        if run:
            self.scheduleNode()


    def get(self):
        return self.optionsDict
        
        
    def configure(self, rebuild=True, **kw):
        action, rebuildDescr = apply( PortWidget.configure, (self, 0), kw)
            
        #  this methods just creates a resize action if width changes
        if self.widget is not None:
            
            if 'width' in kw:
                action = 'resize'

        if action=='rebuild' and rebuild:
            action, rebuildDescr = self.rebuild(rebuildDescr)


        if action=='resize' and rebuild:
            self.port.node.autoResize()

        return action, rebuildDescr



class LegendNE(NetworkNode):
    """This nodes takes two lists of values and plots the the second against the first.

Input:
    labels          - sequence of strings
    loc          -  'best' : 0,
                    'upper right'  : 1, (default)
                    'upper left'   : 2,
                    'lower left'   : 3,
                    'lower right'  : 4,
                    'right'        : 5,
                    'center left'  : 6,
                    'center right' : 7,
                    'lower center' : 8,
                    'upper center' : 9,
                    'center'       : 10,

                    If none of these are suitable, loc can be a 2-tuple giving x,y  in axes coords, ie,
                  loc = 0, 1 is left top
                   loc = 0.5, 0.5 is center, center
    lines     - sequence of lines
Output:
    legend       Matplotlib Axes object
    
"""
    def __init__(self, name='Legend', **kw):
        kw['name'] = name
        
        apply( NetworkNode.__init__, (self,), kw)
        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    
    node1 = c.port1.node
    node2 = c.port2.node
    node1.figure.delaxes(node1.axes)
    node1.figure.add_axes(node1.axes)
"""
        ip = self.inputPortsDescr
        ip.append(datatype='list',required=True, name='label')
        ip.append(datatype='string',required=False, name='location', defaultValue='upper right')
        self.widgetDescr['label'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'Label:'},
            'initialValue':''}    

        self.widgetDescr['location'] = {
        'class':'NEComboBox', 'master':'node',
            'choices':locations.keys(),
            'fixedChoices':True,
            'initialValue':'upper right',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Location:'}}
            
        op = self.outputPortsDescr
        op.append(datatype='MPLDrawArea', name='drawAreaDef')
        code = """def doit(self, label, location):
        kw={ 'legendlabel':label,'legendlocation':location}
        self.outputData(drawAreaDef=kw) """
        self.setFunction(code)

       
class ColorBarNE(NetworkNode):
    """Class for drawing color bar
input :
    plot          - axes instance
    current_image -image instance
    extend        -  both,neither,min or max.If not 'neither', make pointed end(s) for
                     out-of-range values.  These are set for a given colormap using the
                    colormap set_under and set_over methods.
    orientation    - horizontal or vertical
    spacing        -uniform or proportional.Uniform spacing gives each discrete color the same                      space;proportional makes the space proportional to the data interval.
    shrink         -fraction by which to shrink the colorbar
"""

    def __init__(self, name='ColorBar', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='MPLAxes', required=True, name='plot')
        ip.append(datatype='None', required=True, name='current_image')
        ip.append(datatype='string', required=False, name='extend', defaultValue='neither')
        ip.append(datatype='float', required=False, name='orientation', defaultValue='vertical')
        ip.append(datatype='string', required=False, name='spacing', defaultValue='uniform')
        ip.append(datatype='float', required=False, name='shrink', defaultValue=1.)
        self.widgetDescr['shrink'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':1.0,'min':0.0,'max':1.0,
            'labelCfg':{'text':'shrink'} }
        self.widgetDescr['extend'] = {
        'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['both','neither','min','max'],
            'fixedChoices':True,
            'initialValue':'neither',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'extend:'}} 
        self.widgetDescr['orientation'] = {
        'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['vertical','horizontal'],
            'fixedChoices':True,
            'initialValue':'vertical',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'orientation:'}}
        self.widgetDescr['spacing'] = {
        'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['uniform',' proportional'],
            'fixedChoices':True,
            'initialValue':'uniform',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'spacing:'}}  
        op = self.outputPortsDescr
        op.append(datatype='MPLAxes', name='axes')
        code = """def doit(self, plot, current_image, extend, orientation, spacing, shrink):
    axes_list=plot.figure.axes
    if len(axes_list):
        pos=plot.figure.axes[0].get_position()
        for i in axes_list:
          if not isinstance(i,Subplot):
            plot.figure.delaxes(i)
    if current_image!=None:
         pl=plot.figure.colorbar(current_image,cmap=current_image.cmap,shrink=shrink,extend=extend,orientation=orientation,spacing=spacing,filled=True)  
         if orientation=="vertical":
            plot.figure.axes[0].set_position([0.125, 0.1, 0.62, 0.8])
            if shrink>=1.0:
                pl.ax.set_position([0.785, 0.1, 0.03, 0.8])
            else:
                pl.ax.set_position([0.785,pl.ax.get_position()[1],0.03,pl.ax.get_position()[-1]])
                
         else:
            plot.figure.axes[0].set_position([0.125, 0.34, 0.62, 0.56])
            if shrink>=1.0:
                pl.ax.set_position([0.125, 0.18, 0.62, 0.04])
            else:
                pl.ax.set_position([pl.ax.get_position()[0],0.18,pl.ax.get_position()[2],0.04])
         plot.figure.canvas.draw()
    else:
        plot.figure.canvas.delete(pl)
        
    self.outputData(axes=pl)
"""   
    
        self.setFunction(code)

class Text(NetworkNode):
    """Class for writting text in the axes
posx:        x coordinate
posy:        y coordinate
textlabel:   label name
rotation:    angle to be rotated
horizontal alignment: ['center', 'right', 'left']
vertical alignment:   ['center', 'right', 'left']
"""
    def __init__(self, name='Text', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        
        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='posx', defaultValue=.1)
        ip.append(datatype='float', required=False, name='posy', defaultValue=.1)
        ip.append(datatype='string', required=False, name='textlabel', defaultValue='')
        ip.append(datatype='string', required=False, name='rotation', defaultValue=0)
        ip.append(datatype='string', required=False, name='horizontalalignment', defaultValue='center')
        ip.append(datatype='string', required=False, name='verticalalignment', defaultValue='center')
        self.widgetDescr['posx'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'wheelPad':2, 'initialValue':0.1,
            'labelCfg':{'text':'posx'} }

        self.widgetDescr['posy'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':1., 'type':'float',
            'wheelPad':2, 'initialValue':0.1,
            'labelCfg':{'text':'posy'} }

        self.widgetDescr['textlabel'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'text'},
            'initialValue':''}
        
        self.widgetDescr['rotation'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':75, 'height':21, 'oneTurn':10, 'type':'float',
            'wheelPad':2, 'initialValue':0,
            'labelCfg':{'text':'rotation'} }
            
        self.widgetDescr['horizontalalignment'] = {
        'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['center', 'right', 'left'],
            'fixedChoices':True,
            'initialValue':'center',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'horizontalalignment:'}}
        self.widgetDescr['verticalalignment'] = {
        'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['top', 'bottom', 'center'],
            'fixedChoices':True,
            'initialValue':'center',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'verticalalignment:'}}    
                
        op = self.outputPortsDescr
        op.append(datatype='MPLDrawArea', name='drawAreaDef')

        code = """def doit(self, posx, posy, textlabel, rotation, horizontalalignment, verticalalignment):

    kw = {'posx':posx, 'posy':posy, 'textlabel':textlabel, 'horizontalalignment':horizontalalignment, 'verticalalignment':verticalalignment,'rotation':rotation}
    
    self.outputData(drawAreaDef=kw)
"""
        self.setFunction(code)
        
class SaveFig(NetworkNode):
    """Save the current figure.
fname - the filename to save the current figure to.  The
            output formats supported depend on the backend being
            used.  and are deduced by the extension to fname.
            Possibilities are eps, jpeg, pdf, png, ps, svg.  fname
            can also be a file or file-like object - cairo backend
            only.  dpi - is the resolution in dots per inch.  If
            None it will default to the value savefig.dpi in the
            matplotlibrc file
facecolor and edgecolor are the colors of the figure rectangle
orientation - either 'landscape' or 'portrait' 
papertype   - is one of 'letter', 'legal', 'executive', 'ledger', 'a0' through 
                  'a10', or 'b0' through 'b10' - only supported for postscript output
format      - one of 'pdf', 'png', 'ps', 'svg'. It is used to specify the
                  output when fname is a file or file-like object - cairo
                  backend only.
"""
    def __init__(self, name='saveFig', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='MPLFigure', required=False, name='figure')    
        ip.append(datatype=None, required=False, name='fname')
        ip.append(datatype=None, required=False, name='dpi', defaultValue=80)
        ip.append(datatype=None, required=False, name='facecolor', defaultValue='w')
        ip.append(datatype=None, required=False, name='edgecolor', defaultValue='w')
        ip.append(datatype=None, required=False, name='orientation', defaultValue='portrait')
        ip.append(datatype=None, required=False, name='papertype')
        ip.append(datatype=None, required=False, name='format')
        
        self.widgetDescr['fname'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text': 'filename:'},
            'initialValue':''}
            
        self.widgetDescr['dpi'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'int',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':80,
            'labelCfg':{'text':'dpi'} }
            
        self.widgetDescr['facecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'w',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'facecolor:'}}
        
        self.widgetDescr['edgecolor'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':cnames.keys(),
            'fixedChoices':True,
            'initialValue':'w',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'edgecolor:'}}
            
        self.widgetDescr['orientation'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['landscape','portrait'],
            'fixedChoices':True,
            'initialValue':'portrait',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'orientation:'}}
        
        self.widgetDescr['papertype'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['letter', 'legal', 'executive', 'ledger','a0','a1','a2','a3','a4','a5','a6','a7','a8','a9','a10','b0','b1','b2','b3','b4','b5','b6','b7','b8','b9','b10',None],
            'fixedChoices':True,
            'initialValue':'None',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'papertype:'}}
            
        self.widgetDescr['format'] = {
            'class':'NEComboBox', 'master':'ParamPanel',
            'choices':['pdf', 'png', 'ps', 'svg',None],
            'fixedChoices':True,
            'initialValue':'None',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'format:'}} 
            
        code = """def doit(self, figure, fname, dpi, facecolor, edgecolor,
orientation, papertype, format):
    if figure:
        figure.savefig(fname,dpi=dpi,facecolor=facecolor,edgecolor=edgecolor,orientation=orientation,papertype=papertype,format=format)
"""
        self.setFunction(code)
        
    
class MeshGrid(NetworkNode):
    """This class converts vectors x, y with lengths Nx=len(x) and Ny=len(y) to  X, Y and returns them.
where X and Y are (Ny, Nx) shaped arrays with the elements of x
and y repeated to fill the matrix
    """
    def __init__(self, name='MeshGrid', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='list',required=False, name='x')
        ip.append(datatype='list',required=False, name='y')
        op = self.outputPortsDescr
        op.append(datatype='None', name='X')
        op.append(datatype='None', name='Y')
        code = """def doit(self,x,y):
    X,Y=meshgrid(x, y)        
    self.outputData(X=X,Y=Y)
"""
        self.setFunction(code)    

class BivariateNormal(NetworkNode):
    """Bivariate gaussan distribution for equal shape X, Y"""
    def __init__(self, name='BivariateNormal', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='arraylist1')
        ip.append(datatype='None', name='arraylist2')
        ip.append(datatype='float', required=False, name='sigmax', defaultValue=1.)
        ip.append(datatype='float', required=False, name='sigmay', defaultValue=1.)
        ip.append(datatype='float', required=False, name='mux', defaultValue=0.)
        ip.append(datatype='float', required=False, name='muy', defaultValue=0.)
        ip.append(datatype='float', required=False, name='sigmaxy', defaultValue=0.)
        self.widgetDescr['sigmax'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'float',
            'wheelPad':2, 'initialValue':1.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'sigmax'} }
        self.widgetDescr['sigmay'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':1.0,
            'labelCfg':{'text':'sigmay'} }
        self.widgetDescr['mux'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.0,
            'labelCfg':{'text':'mux'} }
        self.widgetDescr['muy'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.0,
            'labelCfg':{'text':'muy'} }
        self.widgetDescr['sigmaxy'] = {
            'class':'NEThumbWheel','master':'ParamPanel',
            'width':61, 'height':21, 'oneTurn':2, 'type':'float',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w'},
            'wheelPad':2, 'initialValue':0.0,
            'labelCfg':{'text':'sigmaxy'} }
        op = self.outputPortsDescr
        op.append(datatype=None, name='z')
        
        code = """def doit(self, x, y, sigmax, sigmay, mux, muy, sigmaxy):
    import numpy
    X=numpy.array(x)
    Y=numpy.array(y)
    z=bivariate_normal( X, Y, sigmax=sigmax, sigmay=sigmay, mux=mux, muy=muy, sigmaxy=sigmaxy)
    self.outputData(z=z)
"""
        self.setFunction(code)
    
###########################################################################
#
#  Create and populate library
#
###########################################################################

from Vision.VPE import NodeLibrary
matplotliblib = NodeLibrary('MatPlotLib', '#99AFD8')
matplotliblib.addNode(MPLFigureNE, 'Figure', 'Input')
matplotliblib.addNode(MPLImageNE, 'ImageFigure', 'Input')
matplotliblib.addNode(MPLDrawAreaNE, 'Draw Area', 'Input')
matplotliblib.addNode(MultiPlotNE, 'MultiPlot', 'Misc')
matplotliblib.addNode(MPLMergeTextNE, 'MergeText', 'Input')
matplotliblib.addNode(ColorBarNE, 'ColorBar', 'Misc')
matplotliblib.addNode(Text, 'Text', 'Input')
matplotliblib.addNode(PolarAxesNE, 'PolarAxes', 'Plotting')
matplotliblib.addNode(HistogramNE, 'Histogram', 'Plotting')
matplotliblib.addNode(PlotNE, 'Plot', 'Plotting')
matplotliblib.addNode(PlotDateNE, 'PlotDate', 'Plotting')
matplotliblib.addNode(PieNE, 'Pie', 'Plotting')
matplotliblib.addNode(SpyNE, 'Spy', 'Plotting')
#matplotliblib.addNode(Spy2NE, 'Spy2', 'Plotting')
matplotliblib.addNode(VlineNE, 'Vline', 'Plotting')
matplotliblib.addNode(ScatterNE, 'Scatter', 'Plotting')
#matplotliblib.addNode(ScatterClassicNE, 'ScatterClassic', 'Plotting')
matplotliblib.addNode(FigImageNE, 'Figimage', 'Plotting')
matplotliblib.addNode(FillNE, 'Fill', 'Plotting')
matplotliblib.addNode(ContourNE, 'Contour', 'Plotting')
matplotliblib.addNode(PcolorMeshNE,'PcolorMesh', 'Plotting')
matplotliblib.addNode(PcolorNE,'Pcolor', 'Plotting')
#matplotliblib.addNode(PcolorClassicNE,'PcolorClassic', 'Plotting')
matplotliblib.addNode(RandNormDist, 'RandNormDist', 'Demo')
matplotliblib.addNode(SinFunc, 'SinFunc', 'Demo')
matplotliblib.addNode(SinFuncSerie, 'SinFuncSerie', 'Demo')
matplotliblib.addNode(MatPlotLibOptions, 'Set Matplotlib options', 'Input')
matplotliblib.addNode(LegendNE, 'Legend', 'Input')
matplotliblib.addNode(TablePlotNE, 'TablePlot', 'Plotting')
matplotliblib.addNode(SpecgramNE, 'Specgram', 'Plotting')
matplotliblib.addNode(CSDNE, 'CSD', 'Plotting')
matplotliblib.addNode(PSDNE, 'PSD', 'Plotting')
matplotliblib.addNode(LogCurveNE, 'LogCurve', 'Plotting')
matplotliblib.addNode(SemilogxNE, 'Semilogx', 'Plotting')
matplotliblib.addNode(SemilogyNE, 'Semilogy', 'Plotting')
matplotliblib.addNode(BoxPlotNE, 'BoxPlot', 'Plotting')
matplotliblib.addNode(ErrorBarNE, 'ErrorBar', 'Plotting')
matplotliblib.addNode(BarHNE, 'BarH', 'Plotting')
matplotliblib.addNode(BarNE, 'Bar', 'Plotting')
matplotliblib.addNode(QuiverNE, 'Quiver', 'Plotting')
matplotliblib.addNode(StemNE,'Stem','Plotting')
matplotliblib.addNode(BivariateNormal,'BivariateNormal','Demo')
matplotliblib.addNode(MeshGrid,'MeshGrid','Demo')
matplotliblib.addNode(SaveFig,'SaveFig','Misc')
matplotliblib.addWidget(NEMatPlotLibOptions)

###########################################################################
#
#  Library specific data types
#
###########################################################################
UserLibBuild.addTypes(matplotliblib, 'Vision.matplotlibTypes')

try:
    UserLibBuild.addTypes(matplotliblib, 'Vision.PILTypes')
except:
    pass

