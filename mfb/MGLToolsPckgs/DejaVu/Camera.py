## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: 2000 Author: Michel F. SANNER
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
# revision: Guillaume Vareille
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Camera.py,v 1.418.2.28 2012/11/09 22:55:21 annao Exp $
#
# $Id: Camera.py,v 1.418.2.28 2012/11/09 22:55:21 annao Exp $
#

"""Camera Module:

This Module implements the Camera class and the Fog class.
"""

## NOTE about share context and sharelist keyword arguments to Camera
##   By default ane new Camera will share its context with camaera 0
## which creates the OpenGL context
## Passing an argument sharecontext=None will make the new camera not share
## the context but still the display lists will be shared.
## Passing sharelist=None in addition to sharecontext=None will create a
## camera with a completely separate OpenGL context.
## All display list are created in the context of the Camera 0 which is the
## one activated in ReallyRedraw when display list are created.

import os, sys, warnings

import Image
import ImageFilter
import ImageChops

import tkMessageBox

from opengltk.OpenGL.GLU import gluPerspective, gluPickMatrix, gluUnProject, gluErrorString, gluLookAt
from opengltk.extent import _gllib
from opengltk.OpenGL.GL import *
from opengltk.extent.utillib import glCleanRotMat
from opengltk.OpenGL import GL

from mglutil.gui import widgetsOnBackWindowsCanGrabFocus

import DejaVu
from DejaVu import loadTogl
from DejaVu.Insert2d import Insert2d
from DejaVu.Spheres import Spheres
from DejaVu.Ellipsoids import Ellipsoids
from DejaVu.Cylinders import Cylinders
from DejaVu import bitPatterns
from DejaVu.cursors import cursorsDict
from DejaVu.Texture import Texture

if hasattr(DejaVu, 'enableVertexArray') is False:
    DejaVu.enableVertexArray = False

if hasattr( DejaVu, 'allowedAntiAliasInMotion') is False:
    DejaVu.allowedAntiAliasInMotion = 0

if hasattr( DejaVu, 'enableSelectionContour') is False:
    DejaVu.enableSelectionContour = False

if hasattr( DejaVu, 'selectionContourSize') is False:
    DejaVu.selectionContourSize = 0

if hasattr( DejaVu, 'selectionContourColor') is False:
    DejaVu.selectionContourColor = (1., 0., 1., .7)

if hasattr( DejaVu, 'selectionPatternSize') is False:
    DejaVu.selectionPatternSize = 6

if hasattr( DejaVu, 'enableSSAO') is False:
    DejaVu.enableSSAO = True

sndDeriv = [ -0.125, -0.125, -0.125,
             -0.125,    1.0, -0.125,
             -0.125, -0.125, -0.125]
    
fstDeriveV1 = [-0.125,  -0.25, -0.125,
               0.0  ,    0.0,  0.0,
               0.125,   0.25,  0.125]

fstDeriveV2 = [ 0.125,   0.25,  0.125,
                0.0  ,    0.0,  0.0,
                -0.125,  -0.25, -0.125]

fstDeriveH1 = [-0.125,    0.0, 0.125,
               -0.25 ,    0.0, 0.25,
               -0.125,    0.0, 0.125]

fstDeriveH2 = [ 0.125,    0.0, -0.125,
                0.25 ,    0.0, -0.25,
                0.125,    0.0, -0.125]
    

from time import time
try:
    from opengltk.extent.utillib import namedPoints
except ImportError:
    def namedPoints(v):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        i = 0
        for p in v:
            glPushName(i)
            glBegin(GL_POINTS)
            glVertex3f(float(p[0]), float(p[1]), float(p[2]))
            glEnd()
            glPopName()
            i = i + 1
        
import Tkinter, os
import numpy.oldnumeric as Numeric
import math
import types
import weakref

import viewerConst, ViewerGUI, jitter
from Geom import Geom
from Transformable import Transformable
import colorTool
import viewerFns
from Trackball import Trackball
from EventHandler import EventManager
from IndexedPolygons import IndexedPolygons
from viewerFns import checkKeywords

import array
matf = array.array('f', [0]*16)


try:
    from opengltk.extent._glextlib import *
except:
    print "no _glextlib"
#    DejaVu.enableSSAO = False

class Fog:

    keywords = [
        'tagModified',
        'enabled',
        'start',
        'end',
        'density',
        'mode',
        'color'
        ]
    

    def Reset(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.color = (0.0, 0.0, 0.0, 1.0)
        self.enabled = False
        self.start = 25
        self.end = 40
        self.mode = GL_LINEAR
        self.density = 0.1
        self._modified = False


    def __init__(self, camera):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.Reset()
        self.camera = weakref.ref(camera) # used to activate right context
                             # the alternative would be to have the Set of
                             # fog values be done trough Camera.Set
        self.name = 'Fog'+camera.name

        
    def getState(self):
        """return a dictionary describing this object's state
This dictionary can be passed to the Set method to restore the object's state
"""
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        state = {'enabled':self.enabled,
                 'start':self.start,
                 'end':self.end,
                 'density':self.density,
                 'color':self.color
                }
        mode='GL_LINEAR'
        if self.mode==GL_EXP: mode='GL_EXP'
        elif self.mode==GL_EXP2: mode='GL_EXP2'
        state['mode'] = mode
        return state

    
    def __repr__(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        return '<Fog enabled=%d from %5.2f to %5.2f mode=%d density=%f \
 color=%s>' % \
               (self.enabled, self.start, self.end, self.mode, self.density,
                repr(self.color) )


    def Set(self, check=1, **kw):
        """Set various fog parameters"""
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        if __debug__:
            if check:
                apply( checkKeywords, ("Fog",self.keywords), kw)
        
        val = kw.get( 'tagModified', True )
        assert val in [True, False]
        self._modified = val

        self.camera().tk.call(self.camera()._w, 'makecurrent')

        val = kw.get( 'enabled')
        if val is not None:
            if val in [False, 0]:
                glDisable(GL_FOG)
            elif val in [True, 1]:
                glFogi(GL_FOG_MODE, self.mode)
                if self.mode == GL_LINEAR:
                    glFogf(GL_FOG_START, float(self.start) )
                    glFogf(GL_FOG_END, float(self.end) )
                else:
                    glFogf(GL_FOG_DENSITY, float(self.density))
                glFogfv(GL_FOG_COLOR, self.color)
                glEnable(GL_FOG)
            else:
                raise ValueError('Bad argument, Only True ot False are possible %s'%val)
            self.enabled = val
            
        val = kw.get( 'start')
        if not val is None:
            if kw.has_key('end'): end = kw.get('end')
            else: end = self.end
            if val < end:
                glFogf(GL_FOG_START, float(val) )
                self.start = val
            else:
                raise AttributeError('start has to be smaller than end=',
                                     self.start, self.end)

        val = kw.get( 'end')
        if not val is None:
            if val > self.start:
                glFogf(GL_FOG_END, float(val) )
                self.end = val
            else:
                raise AttributeError('end has to be larger than start=',
                                     self.start, self.end)

        val = kw.get( 'density')
        if not val is None:
            if val <= 1.0 and val >= 0.0:
                glFogf(GL_FOG_DENSITY, float(val))
                self.density = val
            else:
                raise AttributeError('density has to be <=1.0 and >= 0.0')

        val = kw.get( 'mode')
        if not val is None:
            if val=='GL_LINEAR': val=GL_LINEAR
            elif val=='GL_EXP': val=GL_EXP
            elif val=='GL_EXP2': val=GL_EXP2
            if val in (GL_LINEAR, GL_EXP, GL_EXP2):
                glFogi(GL_FOG_MODE, int(val))
                self.mode = val
            else:
                raise AttributeError('mode has to be GL_LINEAR,GL_EXP or\
GL_EXP2')

        val = kw.get( 'color')
        if not val is None:
            self.color = colorTool.OneColor( val )
            glFogfv(GL_FOG_COLOR, self.color)



class PickObject:
    """Class to represent the result of picking or drag selection
the keys of hits dictionary are geometries,
the values are lists of 2-tuples (vertexIndexe, instance), where vertexInd
is the index of the a vertex of a face of the geometry and instance is a list
of integer providing the instance matrix index for the geometry and all its
parents.
"""
    
    def __init__(self, mode, camera, type='vertices'):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        assert mode in ['pick', 'drag select']
        assert type in ['vertices', 'parts']
        self.type = type
        self.mode = mode
        self.hits = {}
        self.camera = weakref.ref(camera)
        self.p1 = None # intersection of pick ray with front clip plane
        self.p2 = None # intersection of pick ray with back clip plane
        self.event = None # event that triggered picking
        self.box = (0,0,0,0) # screen coordinates of selection box


    def add(self, object=None, vertex=None, instance=0):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if self.hits.has_key(object):
            self.hits[object].append( (vertex, instance) )
        else:
            self.hits[object] = [ (vertex, instance) ]


from math import sqrt, fabs
import Pmw
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
import numpy
from IndexedPolygons import IndexedPolygons
from Spheres import Spheres
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel

# sub class combobox to intercept _postList and populate list when the pull
# down is posted
class DynamicComboBox(Pmw.ComboBox):

    def __init__(self, viewer, parent = None, **kw):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.viewer = viewer
        Pmw.ComboBox.__init__(self, parent, **kw)
        
    def _postList(self, event=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        geomNames = []
        for g in self.viewer.rootObject.AllObjects():
            if isinstance(g, IndexedPolygons):
                geomNames.append(g.fullName)
        
        self.component('scrolledlist').setlist(geomNames)
        Pmw.ComboBox._postList(self, event)


## class OcclusionCamera(Tkinter.Widget, Tkinter.Misc):

##     def orient(self, eyex, eyey, eyez, nx, ny, nz):
##         """Place camera at x,y,z and look along vector nx, ny, nz"""
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

##         glPushMatrix()
##         glLoadIdentity()

##         # compute normal vector
##         if nx==0.0 and ny==0.0:
##             x2=1.
##             y2=0.
##             z2=0.
##         else:
##             z2 = nz
##             if ny==0.0 and nz==0.0:
##                 x2 = 0.0
##                 y2 = 1.0
##             elif nx==0 and nz==0:
##                 x2 = 1.0
##                 y2 = 0.0
##             else:
##                 if fabs(nx)>fabs(ny):
##                     x2 = 0.0
##                     y2 = ny
##                 else:
##                     x2 = nx
##                     y2 = 0.0

##         upx = ny*z2 - nz*y2
##         upy = nz*x2 - nx*z2
##         upz = nx*y2 - ny*x2

##         n = 1. / sqrt(upx*upx + upy*upy + upz*upz)
##         upx *=n
##         upy *=n
##         upz *=n
        
##         gluLookAt( eyex, eyey, eyez, eyex+nx, eyey+ny, eyez+nz, upx, upy, upz)
##         m = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')
##         glPopMatrix()

##         # compute gluLookAt( x, y, z, x+nx, y+ny, z+nz, x3, y3, z3) matrix
##         # http://www.opengl.org/documentation/specs/man_pages/hardcopy/GL/html/glu/lookat.html
## ##         # nx, ny, nz is the vector F (eye->center) (normalized)
## ##         # x, y, z is the eye position

## ##         # s = f x up
## ##         sx = ny*upz - nz*upy
## ##         sy = nz*upx - nx*upz
## ##         sz = nx*upy - ny*upx

## ##         # u = s x f
## ##         ux = sy*nz - sz*ny
## ##         uy = sz*nx - sx*nz
## ##         uz = sx*ny - sy*nx

        
## ##         M = ( sx, ux, -nx, 0, sy, uy, -ny, 0, sz, uz, -nz, 0, -eyex, -eyey, -eyez, 1.)
        
## ##         diff = Numeric.sum(m-M)
## ##         if diff > 0.1:
## ##             raise ValueError

##         self.matrix = m
##         self.Redraw()


##     def computeOcclusion(self, positions, directions):
##         """For a list of pocitions and directions, render the geometry and
##         compute occlusion by summing Zbuffer. Direction have to be normalized"""
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         from time import time
##         t1 = time()
##         occlusionValues = []
##         self.tk.call(self._w, 'makecurrent')

##         OnePercent = len(positions)/100
##         percent = 0
##         counter = 0
##         for pos, dir in zip(positions,directions):
##             if OnePercent>0 and counter % OnePercent == 0:
##                 self.counterText.configure(text=str(percent)+'%')
##                 self.update_idletasks()
##                 percent += 1
##             counter += 1
##             x, y, z = pos
##             nx, ny, nz = dir
##             self.orient(float(x), float(y), float(z),
##                         float(nx), float(ny), float(nz) )
##             zbuf = self.GrabZBufferAsArray()
##             sum = Numeric.sum(zbuf)
##             occlusionValues.append(sum)

##         #print time()-t1
##         return occlusionValues


##     def computeOcclusion_cb(self):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
         
##         self.removeOcclusion()         
         
##         occluderGeoms = self.occluders.getAll(index=2)
##         computeOccluGeoms = self.compOcclusion.getAll(index=2)

##         #print occluderGeoms
##         #print '-------------'
##         #print computeOccluGeoms

##         if len(occluderGeoms)==0:
##             print "WARNING: no occluders"
##             return

##         # allocate new dispaly lists
##         # build display lists for all geoms
##         self.tk.call(self._w, 'makecurrent')
##         for i,g in enumerate(occluderGeoms):
##             if hasattr(g, 'Draw'):
##                 g.oldinheritmaterial = g.inheritMaterial
##                 g.inheritMaterial = True
##                 if isinstance(g, Spheres):
##                     g.oldquality = g.quality
##                     self.tk.call(self.viewer.currentCamera._w, 'makecurrent')
##                     g.deleteTemplate()
##                     #self.tk.call(self._w, 'makecurrent')
##                     g.Set(quality=1)
##                     self.tk.call(self._w, 'makecurrent')
##                     g.makeTemplate()

##                 l = glGenLists(1)
##                 GL.glNewList(l, GL.GL_COMPILE)
##                 status = g.Draw()
##                 #print 'status', status
##                 GL.glEndList()
##                 self.dpyList.append(l)
                
##         # compute occlusion for each geom
##         #self.tk.call(self._w, 'makecurrent')
##         for g in computeOccluGeoms:
##             if isinstance(g, Spheres):
##                 self.near = 3.0
##                 self.setFovy(135.0)
##                 v = g.getVertices()
##                 from math import sqrt
##                 n = sqrt(3,)
##                 occRight = self.computeOcclusion(v, ( (-n,-n,n), )*len(v) )
##                 occLeft = self.computeOcclusion(v, ( (n,n,n), )*len(v) )
##                 occTop = self.computeOcclusion(v, ( (-n,n,-n), )*len(v) )
##                 occBottom = self.computeOcclusion(v, ( (n,-n,-n), )*len(v) )

##                 #occRight = self.computeOcclusion(v, ( (1.,0.,0.), )*len(v) )
##                 #occLeft = self.computeOcclusion(v, ( (-1.,0.,0.), )*len(v) )
##                 #occTop = self.computeOcclusion(v, ( (0.,1.,0.), )*len(v) )
##                 #occBottom = self.computeOcclusion(v, ( (0.,-1.,0.), )*len(v) )
##                 #occFront = self.computeOcclusion(v, ( (0.,0.,1.), )*len(v) )
##                 #occBack = self.computeOcclusion(v, ( (0.,0.,-1.), )*len(v) )
##                 occlusionValues = []
##                 for i in xrange(len(v)):
##                     occlusionValues.append( occRight[i] + occLeft[i] +
##                                             occTop[i] + occBottom[i])# +
##                                             #occFront[i] + occBack[i])
##                 g.occlusionValues = occlusionValues
##                 #g.occlusionValues = occRight
##             else:
##                 self.near = self.near
##                 self.setFovy(self.fovyTW.get())
##                 v, n = g.getOcclusionPointsDir()
##                 #print 'computing for:', g, len(v)
##                 g.occlusionValues = self.computeOcclusion(v, n)

##         # delete display lists
##         for l in self.dpyList:
##             glDeleteLists(l, 1)
##         self.dpyList = []

##         # restore Sphere templates and display list
##         self.tk.call(self.viewer.currentCamera._w, 'makecurrent')
##         #for i,g in enumerate(set.union(set(occluderGeoms), set(computeOccluGeoms))):
##         for i,g in enumerate(occluderGeoms):
##             if hasattr(g, 'Draw'):
##                 g.inheritMaterial = g.oldinheritmaterial
##                 if isinstance(g, Spheres):
##                     self.tk.call(self._w, 'makecurrent')
##                     g.deleteTemplate()
##                     #GL.glDeleteLists(g.templateDSPL[0], 3)
##                     #g.templateDSPL = None
##                     #self.tk.call(self.viewer.currentCamera._w, 'makecurrent')
##                     g.Set(quality=g.oldquality)
##                     self.tk.call(self.viewer.currentCamera._w, 'makecurrent')
##                     g.makeTemplate()
##                     del g.oldquality
        
##         self.applyOcclusion()


##     def normalize(self, values):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         mini = min(values)
##         delta = max(values)-mini
##         off = self.off*delta
##         delta = delta + off
##         nvalues = []
##         for v in values:
##             nv = ((v-mini+off)/delta)
##             #nv = ((v-mini)/delta)
##             nvalues.append(nv)
##         #print 'normalize off:', self.off, 'delta:',delta, min(nvalues), max(nvalues)
##         return nvalues


##     def applyOcclusion(self):#, *dummy):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         #print "applyOcclusion"
        
##         lGeoms = self.compOcclusion.getAll(index=2)
##         if len(lGeoms) == 0:
##             tkMessageBox.showwarning('ambient occlusion','add geometry to apply occlusion')
##         elif hasattr(lGeoms[0], 'occlusionValues') is False:
##             tkMessageBox.showwarning('ambient occlusion','compute occlusion first')
            
        
##         for g in self.compOcclusion.getAll(index=2):
##             # max value is 2500 becauseocculsion rendering is 50x50 pixels
##             # set values below 2400 to 2400. If we do not do this
##             # we sometiems get very small values that kill the range
##             # for instance gpcr

##             #print "g.occlusionValues", g.occlusionValues

##             if isinstance(g, Spheres):
##                 values = numpy.clip(g.occlusionValues, 5000., 7500.0)
##             else:
##                 values = numpy.clip(g.occlusionValues, 2400., 2500.0)

##             if values is None: return
##             ambiScale = self.ambiScale
##             diffScale = self.diffScale

##             #print 'ambiScale:', ambiScale
##             #print 'diffScale:', diffScale

##             #print "values", values
##             nvalues = self.normalize(values)
##             nvalues = numpy.array(nvalues)
##             nvalues.shape = (-1, 1)

##             #print 'nvalues:', g.name, min(nvalues), max(nvalues)
##             # modulate ambient
##             from DejaVu import preventIntelBug_WhiteTriangles
##             if preventIntelBug_WhiteTriangles is False:
##                 prop = numpy.ones( (len(values), 4) )*nvalues
##                 p = prop*ambiScale
##                 p[:,3] = 1
##                 g.materials[1028].getFrom[0][1] = p

##                 # modulate specular
##                 prop = numpy.ones( (len(values), 4) )*nvalues
##                 p = prop*ambiScale
##                 p[:,3] = 1
##                 g.materials[1028].getFrom[0][1] = p
        
##                 # modulate diffuse
##                 prop = numpy.ones( (len(values), 4) )*nvalues
##                 origProp = g.materials[1028].prop[1].copy()
##                 p = prop*diffScale
##                 g.materials[1028].getFrom[1] = [1, p]
##             else:
##                 # modulate diffuse
##                 prop = numpy.ones( (len(values), 4) )*nvalues
##                 origProp = g.materials[1028].prop[1].copy()
##                 g.materials[1028].getFrom[1] = [1, prop]                

##             g.Set(inheritMaterial=False)
##             g.RedoDisplayList()
##             g.viewer.Redraw()


##     def removeOcclusion(self):#, *dummy):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         # reset
##         for g in self.compOcclusion.getAll(index=2):
            
##             from DejaVu import preventIntelBug_WhiteTriangles
##             if preventIntelBug_WhiteTriangles:
##                 g.materials[1028].getFrom[0] = None # same as Materials.py line 107
##                 g.materials[1028].getFrom[1] = None # same as Materials.py line 107
##             else:
##                 g.materials[1028].getFrom[0][1] = 0.6 # same as Materials.py line 107
## #                g.materials[1028].getFrom[1][1] = 0.6 # same as Materials.py line 107
##             g.Set(inheritMaterial=False)
##             g.RedoDisplayList()
##             g.viewer.Redraw()


##     def setOffAndApplyOcclusion(self, val):
##         self.setOff(val)
##         self.applyOcclusion()


##     def __init__(self, master, viewer, cnf={}, **kw):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

##         self.fovy = 90.0
##         self.near = 0.1
##         self.far = 100.
##         self.matrix = None

##         self.dpyList = []
##         self.ambiScale = 0.6 # same as Materials.py line 107
##         self.diffScale = 0.6 # same as Materials.py line 107
##         self.off = 0.4
        
##         self.ownMaster = False # set tot tru is the master of self.Frame
##                                # has to be destroyed when Camera is deleted
##         self.exposeEvent = False # set to true on expose events and reset in
##                                  # Viewer.ReallyRedraw

##         self.frameBorderWidth = 3
##         self.frame = Tkinter.Frame(master, bd=self.frameBorderWidth)
##         cfg = 0

##         self.counterText = Tkinter.Label(self.frame, text='0%')

##         self.fovyTW = ThumbWheel(
##             self.frame, width=70, height=16, type=float, value=self.fovy,
##             callback=self.setFovy_cb, continuous=False, oneTurn=180,
##             wheelPad=2, min=1.0, max=179.99,
##             labCfg = {'text':'cavity darkness:', 'side':'top'}
##             )
##         #self.fovyTW.grid(column=3, row=0)
##         self.fovyTW.pack(side='left')

##         self.compute = Tkinter.Button(self.frame, text='compute',
##                                       command = self.computeOcclusion_cb)
        
##         self.guiFrame = Tkinter.Frame(master, bd=self.frameBorderWidth)
##         frame = self.guiFrame
        
##         # build geometry chooser
##         #objects = []
##         #for g in viewer.rootObject.AllObjects():
##         #    if g.visible and len(g.getVertices())>0:
##         #        objects.append( (g.fullName, 'no comment available', g) )

##         b = Tkinter.Button(frame, text='Update Geom list',
##                            command=self.listGeoms)
##         b.grid(column=0, row=0)
        
##         self.chooser = ListChooser(
##             frame, mode='extended', title='Geometry list', #entries=objects,
##             lbwcfg={'height':12}
##             )
##         self.chooser.grid(column=0, row=1, rowspan=5)

##         b = Tkinter.Button(frame, text='Add', command=self.addGeoms)
##         b.grid(column=1, row=1)
##         b = Tkinter.Button(frame, text='Remove', command=self.removeGeoms)
##         b.grid(column=1, row=2)
        
##         self.compOcclusion = ListChooser(
##             frame, lbwcfg={'height':5}, mode='extended', title='Compute Occlusion',
##             )
##         self.compOcclusion.grid(column=2, row=0, rowspan=3)

##         b = Tkinter.Button(frame, text='Add', command=self.addOccluders)
##         b.grid(column=1, row=4)
##         b = Tkinter.Button(frame, text='Remove', command=self.removeOccluders)
##         b.grid(column=1, row=5)
        
##         self.occluders = ListChooser(
##             frame, lbwcfg={'height':5}, mode='extended', title='Occluders',
##             )
##         self.occluders.grid(column=2, row=3, rowspan=3)


## #        self.ambiScaleTW = ThumbWheel(
## #            frame, width=70, height=16, type=float, value=self.ambiScale,
## #            callback=self.setambiScale, continuous=True, oneTurn=1.,
## #            wheelPad=2, min=0.0001, max=1.,
## #            labCfg = {'text':'ambi. sca.:', 'side':'top'})
## #        self.ambiScaleTW.grid(column=3, row=1)
## #        
## #        self.diffScaleTW = ThumbWheel(
## #            frame, width=70, height=16, type=float, value=self.diffScale,
## #            callback=self.setdiffScale, continuous=True, oneTurn=1.,
## #            wheelPad=2, min=0.0001, max=1.,
## #            labCfg = {'text':'diff. sca.:', 'side':'top'})
## #        self.diffScaleTW.grid(column=3, row=2)

##         self.offTW = ThumbWheel(
##             frame, width=70, height=16, type=float, value=self.off,
##             callback=self.setOffAndApplyOcclusion,
##             continuous=False, oneTurn=1.,
##             wheelPad=2, min=0.0001, max=1.,
##             labCfg = {'text':'overall brightness:', 'side':'top'})
##         self.offTW.grid(column=3, row=3)
        
##         self.apply = Tkinter.Button(frame, text='apply occ.',
##                                     command = self.applyOcclusion)
##         self.apply.grid(column=3, row=4)
##         self.remove = Tkinter.Button(frame, text='remove occ.',
##                                      command = self.removeOcclusion)
##         self.remove.grid(column=3, row=5)

##         self.viewer = viewer
##         from DejaVu.Viewer import AddObjectEvent, RemoveObjectEvent, ReparentObjectEvent
##         viewer.registerListener(AddObjectEvent, self.geomAddedToViewer)
##         viewer.registerListener(RemoveObjectEvent, self.geomRemovedFromViewer)
##         viewer.registerListener(ReparentObjectEvent, self.geomReparented)

##         if not kw.has_key('double'): kw['double'] = 1
##         if not kw.has_key('depth'): kw['depth'] = 1
##         #kw['rgba'] = False
##         #kw['depthsize'] = 20

##         if not kw.has_key('sharecontext') and len(viewer.cameras):
##             # share context with the default camera.
##             cam = viewer.cameras[0]
##             kw['sharecontext'] = cam.uniqID

##         self.width = 50
##         if 'width' in cnf.keys():
##             self.width = cnf['width']
##             cfg = 1
##         self.height = 50
##         if 'height' in cnf.keys():
##             self.height = cnf['height']
##             cfg = 1
##         self.rootx = 320
##         if 'rootx' in cnf.keys():
##             self.rootx = cnf['rootx']
##             del cnf['rootx']
##             cfg = 1
##         self.rooty = 180
##         if 'rooty' in cnf.keys():
##             self.rooty = cnf['rooty']
##             del cnf['rooty']
##             cfg = 1
##         if cfg: self.Geometry()

##         if 'side' in cnf.keys():
##             side = cnf['side']
##             del cnf['side']
##         else: side = 'top'

##         self.frame.pack(side=side)
##         self.compute.pack(side='left')
##         self.counterText.pack(side='left')
##         self.defFrameBack = self.frame.config()['background'][3]

##         loadTogl(self.frame)

##         from Tkinter import TclError
##         try :
##             Tkinter.Widget.__init__(self, self.frame, 'togl', cnf, kw)
##             self.tk.call(self._w, 'makecurrent')
##             glDepthFunc(GL_LESS)
##         except TclError, e:
##             kw.pop('sharecontext')
##             # after this line self.master will be set to self frame
##             Tkinter.Widget.__init__(self, self.frame, 'togl', cnf, kw)

##             self.tk.call(self._w, 'makecurrent')
##             glDepthFunc(GL_LESS)

##         glEnable(GL_DEPTH_TEST)
##         glDisable(GL_LIGHTING)
##         glEnable(GL_CULL_FACE)

##         # create a TK-event manager for this camera
##         self.eventManager = EventManager(self)
##         self.eventManager.AddCallback('<Map>', self.Map)
##         self.eventManager.AddCallback('<Expose>', self.Expose)
##         self.eventManager.AddCallback('<Configure>', self.Expose)

##         self.pack(side=side)

##         frame.pack()
##         self.matrix = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)

##         master.update_idletasks()
##         self.tk.call(viewer.currentCamera._w, 'makecurrent')


##     def listGeoms(self, event=None):
##         self.chooser.clear()
##         objects = []
##         for g in self.viewer.rootObject.AllObjects():
##             if g.visible and len(g.getVertices())>0:
##                 objects.append( (g.fullName, 'no comment available', g) )
##         self.chooser.setlist(objects)
        

##     def geomAddedToViewer(self, event):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         geom = event.object
##         if not hasattr(geom, "getVertices"): return
##         if geom.visible and len(geom.getVertices())>0:
##             self.chooser.add( (geom.fullName, 'no comment available', geom) )

        
##     def geomRemovedFromViewer(self, event):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         #print "geomRemovedFromViewer", event.object.name
##         geom = event.object
##         self.chooser.remove( geom.fullName )

##     # MS not sure we need this function ... viewer.ReparentObject shoudl be used
##     def geomReparented(self, event):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         geom = event.object
##         oldparent = event.oldparent
##         # the listchooser needs to be updated when a geometry gets reparented. 
##         # replace old geometry name  in the listchooser with the new one:
##         oldname = oldparent.fullName + "|" + geom.name
##         allentries = map(lambda x: x[0],self.chooser.entries)
##         if oldname in allentries:
##             ind = allentries.index(oldname)
##             oldentry = self.chooser.entries[ind]
##             self.chooser.remove(ind)
##             self.chooser.insert(ind, (geom.fullName, 'no comment available', geom))
##             if len(oldentry)> 1:
##                 self.chooser.entries[ind] = (geom.fullName, 'no comment available', geom) + oldentry[1:]

       
##     def setambiScale(self, val):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         self.ambiScale = val
        

##     def setdiffScale(self, val):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         self.diffScale = val


##     def setOff(self, val):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         self.off = val


##     def addGeoms(self):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         for g in self.chooser.get(index=2):
##             self.compOcclusion.add( (g.fullName, 'no comment available', g))
##             self.occluders.add( (g.fullName, 'no comment available', g))
##             self.chooser.remove( g.fullName )
##         return

##     def removeGeoms(self):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         for g in self.compOcclusion.get(index=2):
##             if g.fullName not in self.chooser.lb.get(0, 'end'):
##                 self.chooser.add( (g.fullName, 'no comment available', g) )
##             self.compOcclusion.remove( g.fullName )
##         return


##     def addOccluders(self):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         for g in self.chooser.get(index=2):
##             self.occluders.add( (g.fullName, 'no comment available', g))
##             self.chooser.remove( g.fullName )
##         return

##     def removeOccluders(self):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         for g in self.occluders.get(index=2):
##             if g.fullName not in self.chooser.lb.get(0, 'end'):
##                 self.chooser.add( (g.fullName, 'no comment available', g) )
##             self.occluders.remove( g.fullName )
##         return

##     def setFovy_cb(self, *dummy):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         val = self.fovyTW.get()
##         self.setFovy(val)


##     def setFovy(self, fovy):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         #print 'fovy:', fovy, self.near, self.far
##         self.fovy = fovy
##         self.tk.call(self._w, 'makecurrent')
##         glMatrixMode(GL_PROJECTION);
##         glLoadIdentity()

##         gluPerspective(float(fovy),
##                            float(self.width)/float(self.height),
##                            float(self.near), float(self.far))

##         glMatrixMode(GL_MODELVIEW)



##     def GrabZBufferAsArray(self):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         """Grabs the detph buffer and returns it as a Numeric array"""

##         from opengltk.extent import _gllib as gllib
##         width = self.width
##         height = self.height
##         nar = Numeric.zeros(width*height, 'f')

##         glFinish() #was glFlush()
##         gllib.glReadPixels( 0, 0, width, height, GL.GL_DEPTH_COMPONENT,
##                             GL.GL_FLOAT, nar)
##         glFinish()
##         return nar


##     def GrabZBuffer(self, zmin=None, zmax=None):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         """Grabs the detph buffer and returns it as PIL P image"""
##         deptharray = self.GrabZBufferAsArray()

##         # map z values to unsigned byte
##         if zmin is None:
##             zmin = min(deptharray)
##         if zmax is None:
##             zmax = max(deptharray)
##         if (zmax!=zmin):
##             zval1 = 255 * ((deptharray-zmin) / (zmax-zmin))
##         else:
##             zval1 = Numeric.ones(self.width*self.height, 'f')*zmax*255

##         import Image

##         depthImage = Image.fromstring('L', (self.width, self.height),
##                                       zval1.astype('B').tostring())


##         return depthImage


##     def Map(self, *dummy):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         """Cause the opengl widget to redraw itself."""
##         self.tk.call(self._w, 'makecurrent')

##         self.Redraw()


##     def Expose(self, event=None):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         """set the camera's exposeEvent so that at the next redraw
## the camera width and height are updated
## """
##         self.tk.call(self._w, 'makecurrent')

##         self.Redraw()


##     def setGeom(self, geom):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         self.tk.call(self._w, 'makecurrent')
##         self.dpyList = GL.glGenLists(1)
##         GL.glNewList(self.dpyList, GL.GL_COMPILE)
##         if hasattr(geom, 'Draw'):
##             status = geom.Draw()
##         else:
##             status = 0
##         GL.glEndList()
##         self.geom = geom

        
##     def Redraw(self, *dummy):
##         if __debug__:
##          if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
##         #if self.dpyList is None:
##         #    return

##         if self.matrix is None:
##             return
##         if self.dpyList is None:
##             return
##         glClearColor(0, 0, 0, 1 )
##         glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
##         glViewport(0, 0, self.width, self.height)

##         glPushMatrix()
##         glLoadIdentity()
##         glMultMatrixf(self.matrix)
##         for l in self.dpyList:
##             glCallList(l)
##         glPopMatrix()
##         if self.swap:
##             self.tk.call(self._w, 'swapbuffers')


        
## ##         if not self.viewer.isInitialized:
## ##             self.after(100, self.Expose)
## ##         else:
## ##             # if viewer is in autoRedraw mode the next redraw will handle it
## ##             if not self.exposeEvent and self.viewer.autoRedraw:
## ##                 self.viewer.Redraw()
## ##                 self.exposeEvent = True

## ##             for o in self.viewer.rootObject.AllObjects():
## ##                 if o.needsRedoDpyListOnResize or o.scissor:
## ##                     self.viewer.objectsNeedingRedo[o] = None
## ##


class StandardCamera(Transformable, Tkinter.Widget, Tkinter.Misc):
    """Class for Opengl 3D drawing window"""

    initKeywords = [
        'height',
        'width',
        'rgba'
        'redsize',
        'greensize',
        'bluesize',
        'double',
        'depth',
        'depthsize',
        'accum',
        'accumredsize',
        'accumgreensize',
        'accumbluesize',
        'accumalphasize',
        'alpha',
        'alphasize',
        'stencil',
        'stencilsize',
        'auxbuffers',
        'privatecmap',
        'overlay',
        'stereo',
        'time',
        'sharelist',
        'sharecontext',
        'ident',
        'rootx',
        'rooty',
        'side',
        'stereoflag',
        'ssao',
        'SSAO_OPTIONS'
        ]
    
    setKeywords = [
        'tagModified',
        'height',
        'width',
        'fov',
        'near',
        'far',
        'color',
        'antialiased',
        'contours',
        'd1ramp',
        'd1scale',
        'd1off',
        'd1cutL',
        'd1cutH',
        'd2scale',
        'd2off',
        'd2cutL',
        'd2cutH',
        'boundingbox',
        'rotation',
        'translation',
        'scale',
        'pivot',
        'direction',
        'lookAt',
        'lookFrom',
        'projectionType',
        'rootx',
        'rooty',
        'stereoMode',
        'sideBySideRotAngle',
        'sideBySideTranslation',
        'suspendRedraw',
        'drawThumbnail',
        'ssao',
        'SSAO_OPTIONS'        
        ]

    PERSPECTIVE = 0
    ORTHOGRAPHIC = 1

    stereoModesList = ['MONO',
                      'SIDE_BY_SIDE_CROSS',
                      'SIDE_BY_SIDE_STRAIGHT',
                      'STEREO_BUFFERS',
                      'COLOR_SEPARATION_RED_BLUE',
                      'COLOR_SEPARATION_BLUE_RED',
                      'COLOR_SEPARATION_RED_GREEN',
                      'COLOR_SEPARATION_GREEN_RED',
                      'COLOR_SEPARATION_RED_GREENBLUE',
                      'COLOR_SEPARATION_GREENBLUE_RED',
                      'COLOR_SEPARATION_REDGREEN_BLUE',
                      'COLOR_SEPARATION_BLUE_REDGREEN'
                     ]

    def getState(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """return a dictionary describing this object's state
This dictionary can be passed to the Set method to restore the object's state
"""
        states = {
            'height':self.height,
            'width':self.width,
            'rootx':self.rootx,
            'rooty':self.rooty,
            'fov':self.fovy,
            'near':self.near,
            'far':self.far,
            'color':self.backgroundColor,
            'antialiased':self.antiAliased,
            'boundingbox':self.drawBB,
            
            'rotation':list(self.rotation),
            'translation':list(self.translation),
            'scale':list(self.scale),
            'pivot':list(self.pivot),
            'direction':list(self.direction),
            'lookAt':list(self.lookAt),
            'lookFrom':list(self.lookFrom),

            'projectionType':self.projectionType,
            'stereoMode':self.stereoMode,
            'sideBySideRotAngle':self.sideBySideRotAngle,
            'sideBySideTranslation':self.sideBySideTranslation,
            'suspendRedraw':self.suspendRedraw,
            'drawThumbnail':self.drawThumbnailFlag,

            'contours': self.contours,
            'd1ramp':list(self.d1ramp),
            'd1scale': self.d1scale,
            'd1off': self.d1off,
            'd1cutL': self.d1cutL,
            'd1cutH': self.d1cutH,

            'd2scale': self.d2scale,
            'd2off': self.d2off,
            'd2cutL': self.d2cutL,
            'd2cutH': self.d2cutH,
            'ssao':self.ssao,
            }
        if self.ssao:
            d = {}
#            for k in self.SSAO_OPTIONS:
#                d[k] = self.SSAO_OPTIONS[k][0]
            states['SSAO_OPTIONS'] = self.SSAO_OPTIONS
        return states

    def lift(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """brings the window containing the camera in front of others"""
        window = self.frame.master
        if isinstance(window, Tkinter.Tk) or \
           isinstance(window, Tkinter.Toplevel):
            self.frame.master.lift()
        else:
            m = self.master
            while m.master:
                m = m.master
            m.lift()


    def AutoDepthCue(self, nearOffset=0.0, farOffset=0.0, object=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """
        AutoDepthCue(nearOffset=0.0, farOffset=0.0)
        set fog start and end automatically using the bounding box of the
        specified object.
        if delta is the depth of the bounding box,
        start will be set to near+(nearOffset*delta)
        end will be set to farn+(farOffset*delta)
        """
        #print "StandardCamera.AutoDepthCue"
        #print 'BEFORE', self.near, self.far, self.fog.start, self.fog.end, self.nearDefault, self.farDefault
        if object is None:
            object = self.viewer.rootObject
        bb = object.ComputeBB()
        lf = self.lookFrom
        la = self.lookAt
        v = lf-la
        from math import sqrt
        fl = frustrumlength = sqrt( v[0]*v[0] + v[1]*v[1] + v[2]*v[2])

        # compute unit vector in viewing direction
        viewDir1 = v/fl

        # project center of bb to view direction
        # and measure length from lookfrom to projected point
        bbCenter = (bb[1]+bb[0])*.5
        u = bbCenter-lf
        u1 = u/sqrt(numpy.sum(u*u))
        cosAlpha = numpy.dot(viewDir1, u1)
        v = u*cosAlpha
        l = sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]) # length from lookFrom
        
        # subtract from this distance
        halfDiag = bbCenter-bb[1]
        rad = sqrt(numpy.sum(halfDiag*halfDiag))
        d = rad/sqrt(3)
        
        v = (l-d*.5)*viewDir1
        start = sqrt(numpy.sum(v*v))
        v = (l+d)*viewDir1
        end =  sqrt(numpy.sum(v*v))
        #print l, d, start, end
        #far = -min(bb[0])+frustrumlength
        #near= -max(bb[1])+frustrumlength
        #delta = far-near
        #start = near+delta*nearOffset
        #end = far+delta*farOffset
        if start < end:
            self.fog.Set(start=start, end=end)
        # update camera near and far
        #self.Set(near=self.nearDefault, far=self.farDefault)
        #self.Set(near=self.fog.start*.9, far=self.fog.end*1.1)
        self.Set(far=self.fog.end*1.1)
        self.viewer.GUI.NearFarFog.Set(self.near,
                                       self.far,
                                       self.fog.start,
                                       self.fog.end)
        #print 'AFTER', self.near, self.far, self.fog.start, self.fog.end, self.nearDefault, self.farDefault


    def GrabFrontBufferAsArray(self, lock=True, buffer=GL.GL_FRONT):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Grabs the front buffer and returns it as Numeric array of
size camera.width*camera.height*3"""
        from opengltk.extent import _gllib as gllib
        width = self.width
        height = self.height
        nar = Numeric.zeros(3*width*height, Numeric.UnsignedInt8)

        # get the redraw lock to prevent viewer from swapping buffers
        if lock:
            self.viewer.redrawLock.acquire()
            self.tk.call(self._w, 'makecurrent')
        glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)

        current_buffer = int(GL.glGetIntegerv(GL.GL_DRAW_BUFFER)[0])
        # tell OpenGL we want to read pixels from front buffer
	glReadBuffer(buffer)

        glFinish() #was glFlush()
        gllib.glReadPixels( 0, 0, width, height, GL.GL_RGB,
                            GL.GL_UNSIGNED_BYTE, nar)
        glFinish()
        # restore buffer from on which we operate
        glReadBuffer(current_buffer)
        if lock:
            self.viewer.redrawLock.release()
        return nar
    
        
    def GrabFrontBuffer(self, lock=True, buffer=GL.GL_FRONT):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Grabs the detph buffer and returns it as PIL P image"""
        nar = self.GrabFrontBufferAsArray(lock, buffer)

        import Image
        image = Image.fromstring('RGB', (self.width, self.height),
                                 nar.tostring())
        #if sys.platform!='win32':
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        return image

    
    def GrabZBufferAsArray(self, lock=True):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Grabs the detph buffer and returns it as a Numeric array"""

        from opengltk.extent import _gllib as gllib
        width = self.width
        height = self.height
        nar = Numeric.zeros(width*height, 'f')

        if lock:
            # get the redraw lock to prevent viewer from swapping buffers
            self.viewer.redrawLock.acquire()

        glFinish() #was glFlush()
        gllib.glReadPixels( 0, 0, width, height, GL.GL_DEPTH_COMPONENT,
                            GL.GL_FLOAT, nar)
        glFinish()
        if lock:
            self.viewer.redrawLock.release()

        return nar

        
    def GrabZBuffer(self, lock=True, flipTopBottom=True, zmin=None, zmax=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Grabs the detph buffer and returns it as PIL P image"""
        deptharray = self.GrabZBufferAsArray(lock)

        # map z values to unsigned byte
        if zmin is None:
            zmin = min(deptharray)
        if zmax is None:
            zmax = max(deptharray)
        if (zmax!=zmin):
            zval1 = 255 * ((deptharray-zmin) / (zmax-zmin))
        else:
            zval1 = Numeric.ones(self.width*self.height, 'f')*zmax*255

        import Image

        depthImage = Image.fromstring('L', (self.width, self.height),
                                      zval1.astype('B').tostring())

        #if sys.platform!='win32':
        if flipTopBottom is True:
            depthImage = depthImage.transpose(Image.FLIP_TOP_BOTTOM)

        return depthImage
    

    def SaveImage(self, filename, transparentBackground=False):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """None <- cam.SaveImage(filename, transparentBackground=False)
The file format is defined by the filename extension.
Transparent background is only supported in 'png' format.
"""
        im = self.GrabFrontBuffer()
        if transparentBackground:
            errmsg = 'WARNING: transparent background is only supported with the png file format'
            name, ext = os.path.splitext(filename)
            if ext.lower != '.png':
                print errmsg
                filename += '.png'
            def BinaryImage(x):
                if __debug__:
                 if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
                if x==255:
                    return 0
                else:
                    return 255
            # grab z buffer
            z = self.GrabZBuffer()
            # turn 255 (i.e. bg into 0 opacity and everything else into 255)
            alpha = Image.eval(z, BinaryImage)
            im = Image.merge('RGBA', im.split()+(alpha,))
        extension = os.path.splitext(filename)[1]
        kw = {}
        if not extension:
            filename += '.png'
        elif extension in ['.jpg', '.jpeg', '.JPG', '.JPEG']:
            kw = {'quality':95}

        im.save(filename, **kw)


    def ResetTransformation(self, redo=1):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        Transformable.ResetTransformation(self, redo=redo)

        # Point at which we are looking
        self.lookAt = Numeric.array([0.0, 0.0, 0.0])

        # Point at which the camera is
        self.lookFrom = Numeric.array([0.0, 0.0, 30.0])

        # Vector from lookFrom to lookAt
        self.direction = self.lookAt - self.lookFrom

        # Field of view in y direction
        self.fovyNeutral = 40.
        self.fovy = self.fovyNeutral

        self.projectionType = self.PERSPECTIVE
        self.left = 0.
        self.right = 0.
        self.top = 0.
        self.bottom = 0.

        # Position of clipping planes.
        self.nearDefault = .1
        self.near = self.nearDefault
        self.near_real = self.near
        self.farDefault = 50.
        self.far = self.farDefault

        self.SetupProjectionMatrix()


    def ResetDepthcueing(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()    
        self.fog.Set(start = 25, end = 40)


    def BuildTransformation(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Creates the camera's transformation"""

        fx, fy, fz = self.lookFrom
        ax, ay, az = self.lookAt
        #ux, uy, uz = self.up
        gluLookAt( float(fx), float(fy), float(fz),
                   float(ax), float(ay), float(az),
                   float(0), float(1), float(0))
        #lMatrix = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')
        #print 'Before', lMatrix
        #lRotation, lTranslation, lScale = self.Decompose4x4(lMatrix, cleanup=False)
        #print lRotation
        #print lTranslation
        #glLoadIdentity()
        #glTranslatef(float(lTranslation[0]), float(lTranslation[1]), float(lTranslation[2]))
        #glMultMatrixf(lRotation)
        #lMatrix = Numeric.array(glGetDoublev(GL_PROJECTION_MATRIX)).astype('f')
        #print 'After', lMatrix
        
                   #float(ux), float(uy), float(uz) )
## ##         eye = self.lookFrom
## ##         center = self.lookAt
## ##         gluLookAt( eye[0], eye[1], eye[2], center[0], center[1], center[2],
## ##                    0, 1, 0)
## ##         return
## ##          rot = Numeric.reshape(self.rotation, (4,4))
## ##          dir = Numeric.dot(self.direction, rot[:3,:3])
## ##          glTranslatef(dir[0], dir[1], dir[2])
##         glTranslatef(float(self.direction[0]),float(self.direction[1]),float(self.direction[2]))
##         glMultMatrixf(self.rotation)
##         glTranslatef(float(-self.lookAt[0]),float(-self.lookAt[1]),float(-self.lookAt[2]))
## ##          glTranslatef(self.pivot[0],self.pivot[1],self.pivot[2])
## ##          glMultMatrixf(self.rotation)
## ##          glTranslatef(-self.pivot[0],-self.pivot[1],-self.pivot[2])



    def GetMatrix(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Returns the matrix that is used to transform the whole scene to the
        proper camera view"""

        glPushMatrix()
        glLoadIdentity()
        self.BuildTransformation()
        m = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')
        glPopMatrix()
        return Numeric.transpose(m)

    def GetMatrixInverse(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Returns the inverse of the matrix used to transform the whole scene
        to the proper camera view"""

        m = self.GetMatrix()
        m = Numeric.reshape(Numeric.transpose(m), (16,)).astype('f')
        rot, transl, scale = self.Decompose4x4(m)
        sc = Numeric.concatenate((Numeric.reshape(scale,(3,1)), [[1]]))
        n = Numeric.reshape(rot, (4,4))/sc
        tr = Numeric.dot(n, (transl[0], transl[1], transl[2],1) )
        n[:3,3] = -tr[:3]
        return n        


##      def ConcatLookAtRot(self, matrix):
##          """Rotates the lookAt point around the lookFrom point."""
##          matrix = Numeric.transpose(Numeric.reshape( matrix, (4,4) ))

##          rot = Numeric.reshape( self.rotation, (4,4))
##          m = Numeric.dot(rot, matrix)
##          m = Numeric.dot(m, Numeric.transpose(rot))
        
##          dir = Numeric.dot(self.direction, m[:3,:3])
##          self.lookAt = self.lookFrom + dir
##          self.ConcatRotation(Numeric.reshape(matrix, (16,)))
##          self.pivot = self.lookFrom

##      def ConcatLookAtRot(self, matrix):
##          """Rotates the lookAt point around the lookFrom point."""
##          self.SetPivot(self.lookFrom)
##          #print "ConcatLookAtRot", self.pivot
##          self.ConcatRotation(matrix)

##      def ConcatLookFromRot(self, matrix):
##          """Rotates the lookFrom point around the lookAt point."""
##          self.SetPivot(self.lookAt)
##          #print "ConcatLookFromRot", self.pivot
##          self.ConcatRotation(matrix)

        
##      # not implemented
##      def ConcatLookAtTrans(self, trans):
##          pass


    def ConcatRotation(self, matrix):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Rotates the camera around the lookAt point"""

        self._modified = True
        x,y,z = self.lookFrom

        import numpy
        matrix = Numeric.reshape( matrix, (4,4) )
        newFrom = numpy.dot((x,y,z,1), matrix )
        self.Set(lookFrom=newFrom[:3])
        
##         glPushMatrix()
##         glLoadIdentity()
##         matrix = Numeric.reshape( matrix, (4,4) )

## ##          rot = Numeric.reshape( self.rotation, (4,4))
## ##          m = Numeric.dot(rot, matrix)
## ##          m = Numeric.dot(m, Numeric.transpose(rot))
## ##          self.direction = Numeric.dot(self.direction, m[:3,:3])
## ##          self.lookFrom = self.lookAt - self.direction
        
##         matrix = Numeric.reshape( Numeric.transpose( matrix ), (16,) )
##         glMultMatrixf(matrix)
##         glMultMatrixf(self.rotation)
##         self.rotation = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')
##         self.rotation = glCleanRotMat(self.rotation).astype('f')
##         self.rotation.shape = (16,)
##         glPopMatrix()
##         #self.pivot = self.lookAt

        self.viewer.deleteOpenglList() # needed to redraw the clippingplanes little frame


    def ConcatTranslation(self, trans, redo=1):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Translate the camera from lookFrom to looAt"""

        self._modified = True
        newFrom = self.lookFrom+trans
        newAt = self.lookAt+trans
        self.Set(lookFrom = newFrom, lookAt=newAt)

        # FIXME compute deltaZ and update near, far and fog
        
##         trans = Numeric.array(trans)
##         sign = Numeric.add.reduce(trans)
##         if sign > 0.0:
##             n = 1 + (math.sqrt(Numeric.add.reduce(trans*trans)) * 0.01 )
##             newdir = self.direction*n
##             diff = self.direction-newdir
##             diff = math.sqrt(Numeric.add.reduce(diff*diff))
##         else:
##             n = 1 - (math.sqrt(Numeric.add.reduce(trans*trans)) * 0.01 )
##             newdir = self.direction*n
##             diff = self.direction-newdir        
##             diff = -math.sqrt(Numeric.add.reduce(diff*diff))
##         self.direction = newdir
## #        print self.lookFrom, self.near, self.far, self.fog.start, self.fog.end

##         # update near and far
##         near = self.near_real + diff
##         far = self.far + diff
##         if near < far:
##             self.Set(near=near, far=far, redo=redo)

##         # update fog start and end
##         #self.fog.Set(start=self.fog.start, end=self.fog.end + diff)
##         if self.fog.start < self.fog.end + diff:
##             self.fog.Set(end=self.fog.end + diff)

##         # update viewerGUI
##         if self == self.viewer.currentCamera:
##             self.viewer.GUI.NearFarFog.Set(self.near, self.far,
##                                            self.fog.start, self.fog.end)

##         self.lookFrom = self.lookAt - self.direction
        #self.viewer.Redraw()

        self.viewer.deleteOpenglList() # needed to redraw the clippingplanes little frame


    def ConcatScale(self, scale, redo=1):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Open and close camera's FOV
"""
        #print "Camera.ConcatScale", scale
        self._modified = True
        if scale > 1.0 or self.scale[0] > 0.001:
            #fovy = abs(math.atan( math.tan(self.fovy*math.pi/180.) * scale ) * 180.0/math.pi)
            fovy = self.fovy * scale
            if fovy < 180.:
                self.Set(fov=fovy, redo=redo)


    def Geometry(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """
Resize the Tk widget holding the camera to:
     self.widthxself.height+self.rootx+self.rooty
This only applies when the camera is in its own top level.
"""

        # get a handle to the master of the frame containing the Togl widget
        window = self.frame.master

        # if window is a toplevel window
        
        # replaced this test by test for geometry method
        #if isinstance(, Tkinter.Tk) or \
        #   isinstance(self.frame.master, Tkinter.Toplevel):
        if hasattr(window, 'geometry') and callable(window.geometry):
            # we have to set the geoemtry of the window to be the requested
            # size plus 2 times the border width of the frame containing the
            # camera
            off = 2*self.frameBorderWidth
            geom = '%dx%d+%d+%d' % (self.width+off, self.height+off,
                                    self.rootx, self.rooty)
            window.geometry(geom)


    def getGeometry(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """return the posx, posy, width, height of the window containing the camera"""
        geom = self.winfo_geometry()
        size, x, y = geom.split('+')
        w, h = size.split('x')
        return int(x), int(y), int(w), int(h)


    def __repr__(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        return self.name


    def __init__(self, master, screenName, viewer, num, check=1,
                 cnf={}, **kw):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        #print "StandardCamera.__init__"

        self.name = 'Camera'+str(num)
        self.num = num
        self.uniqID = self.name+viewer.uniqID

        # used for unprojection un gluUnProject
        self.unProj_model = None
        self.unProj_proj = None
        self.unProj_view = None

        self.swap = True # set to false to prevent camera from swapping after
                         # redraw (used by tile renderer)
                         
        self.suspendRedraw = False # set to True to prevent camera to be redraw
                                   # Use for ARViewer ( Added by AG 01/12/2006)

        self.lastBackgroundColorInPhotoMode = (0.,0.,0.,1.)

        if __debug__:
            if check:
                apply( checkKeywords, (self.name,self.initKeywords), kw)
        
        self.initialized = 0
        self.swap = True
        Transformable.__init__(self, viewer)

        # FIXME: quick hack. Flag set by SetCurrentXxxx. When set object's
        # transformation and material are saved in log file
        self.hasBeenCurrent = 0
        self._modified = False

        #self.posLog = []
# Once togl will allow to create widgets with same context
# but for now we ignore it ==> no more multiple cameras
#                kw['samecontext'] = 1
#
# Togl Tk widget options as of Version 1.5
# -height [DEFAULT_WIDTH=400], -width [DEFAULT_HEIGHT=400],
# -rgba [true]
# -redsize [1], -greensize [1], -bluesize [1]
# -double [false]
# -depth [false]
# -depthsize [1]
# -accum [false]
# -accumredsize [1], -accumgreensize [1], -accumbluesize [1], -accumalphasize [1]
# -alpha [false], -alphasize [1]
# -stencil [false], -stencilsize [1]
# -auxbuffers [0]
# -privatecmap [false]
# -overlay [false]
# -stereo [false]
# -time [DEFAULT_TIME = "1"]
# -sharelist [NULL]
# -sharecontext [NULL]
# -ident [DEFAULT_IDENT = ""]

        if not kw.has_key('double'): kw['double'] = 1
#        if not kw.has_key('overlay'): kw['overlay'] = 1
        if not kw.has_key('depth'): kw['depth'] = 1

        if not kw.has_key('stencil'): kw['stencil'] = 1

        if hasattr(viewer, 'accumBuffersError') and viewer.accumBuffersError:
            # if we tried to create a context with accumulation buffers before
            # and it failed we set accum to False
            kw['accum'] = 0
        else:
            # if the user did not specify accumulation we turn them on by defaut
            if not kw.has_key('accum'):
                kw['accum'] = 1

        if not kw.has_key('stereo'): kw['stereo'] = 'none'

        if not kw.has_key('ident'):
            kw['ident'] = self.uniqID
#            kw['ident'] = 'camera%d' % num

        if not kw.has_key('sharelist') and len(viewer.cameras):
            # share list with the default camera.
            cam = viewer.cameras[0]
            kw['sharelist'] = cam.uniqID

        if not kw.has_key('sharecontext') and len(viewer.cameras):
            # share context with the default camera.
            cam = viewer.cameras[0]
            kw['sharecontext'] = cam.uniqID
            if not hasattr(cam, 'shareCTXWith'): cam.shareCTXWith = []
            cam.shareCTXWith.append(self)

##         if master is None:
##             from os import path
##             from opengltk.OpenGL import Tk
##             toglInstallDir = path.dirname(path.abspath(Tk.__file__))
##             tclIncludePath = master.tk.globalgetvar('auto_path')
##             master.tk.globalsetvar('auto_path', toglInstallDir + ' ' +
##                                    tclIncludePath)
##             master.tk.call('package', 'require', 'Togl')

        self.frameBorderWidth = 3
        self.frame = Tkinter.Frame(master, bd=self.frameBorderWidth)

        #self.frame.master.protocol("WM_DELETE_WINDOW", self.hide)

        cfg = 0

        if 'width' in cnf.keys():
            self.width = cnf['width']
            cfg = 1
        else:
            cnf['width'] = self.width = 406

        if 'height' in cnf.keys():
            self.height = cnf['height']
            cfg = 1
        else:
            cnf['height'] = self.height = 406

        self.rootx = 320
        if 'rootx' in cnf.keys():
            self.rootx = cnf['rootx']
            del cnf['rootx']
            cfg = 1
        self.rooty = 180
        if 'rooty' in cnf.keys():
            self.rooty = cnf['rooty']
            del cnf['rooty']
            cfg = 1
        if cfg: self.Geometry()

        if 'side' in cnf.keys():
            side = cnf['side']
            del cnf['side']
        else: side = 'top'

        self.frame.pack(fill=Tkinter.BOTH, expand=1, side=side)
        self.defFrameBack = self.frame.config()['background'][3]

        self.ResetTransformation(redo=0)
        self.currentTransfMode = 'Object' # or 'Clip', 'Camera'

        self.renderMode = GL_RENDER
        self.pickNum = 0
        self.objPick = []

        self.drawBB = 0

        self.drawMode = None  # bit 1: for Opaque objects with no dpyList
                              # bit 2: for objects using dpy list
                              # bit 3: for Transp Object with dpyList
                              
        self.drawTransparentObjects = 0
        self.hasTransparentObjects = 0
        self.selectDragRect = 0
        self.fillSelectionBox = 0

        # variable used for stereographic display
        self.sideBySideRotAngle = 3.
        self.sideBySideTranslation = 0.
        self.imageRendered = 'MONO' # can be LEFT_EYE or RIGHT_EYE
        self.stereoMode = 'MONO' # or 'SIDE_BY_SIDE'

        self.backgroundColor = (.0,.0,.0, 1.0)

        self.selectionColor = (1.0, 1.0, 0.0, 1.0)
        self.fillDelay = 200 # delay in miliseconds for filling selection box

        toglVersion = loadTogl(self.frame)
        #print "Togl Version:", toglVersion

        if os.name == 'nt':
            if kw['stereo'] == 'none':
                kw['stereo'] = 0
            else:
                kw['stereo'] = 1

        # after this line self.master will be set to self frame
        from Tkinter import TclError
        from opengltk.exception import GLerror
        try:
            Tkinter.Widget.__init__(self, self.frame, 'togl', cnf, kw)
            try:
                GL.glAccum(GL.GL_LOAD, 1.0)
                viewer.accumBuffersError = False
            except GLerror:
                viewer.accumBuffersError = True
                #viewer.accumBuffersError = False
        except Tkinter.TclError, e:
            print "Warning: disabling accumulation buffers", e
            kw.pop('accum')
            viewer.accumBuffersError = True
            Tkinter.Widget.__init__(self, self.frame, 'togl', cnf, kw)

        #currentcontext = self.tk.call(self._w, 'contexttag')
        #print "StandardCamera.__init__ currentcontext", currentcontext

        if   (DejaVu.preventIntelBug_BlackTriangles is None) \
          or (DejaVu.preventIntelBug_WhiteTriangles is None):
            isIntelOpenGL = GL.glGetString(GL.GL_VENDOR).find('Intel') >= 0
            if isIntelOpenGL is True:
                isIntelGmaRenderer = GL.glGetString(GL.GL_RENDERER).find("GMA") >= 0
                lPreventIntelBugs = isIntelOpenGL and not isIntelGmaRenderer
            else:
                lPreventIntelBugs = False
            if DejaVu.preventIntelBug_BlackTriangles is None:
                DejaVu.preventIntelBug_BlackTriangles = lPreventIntelBugs
            if DejaVu.preventIntelBug_WhiteTriangles is None:
                DejaVu.preventIntelBug_WhiteTriangles = lPreventIntelBugs

        if DejaVu.defaultAntiAlias is None:
            if os.name == 'nt':
                DejaVu.defaultAntiAlias = 0
            else:   
                try:
                    from opengltk.extent import _glextlib # tells us the graphic card is not too bad
                    DejaVu.defaultAntiAlias = 4
                except:
                    DejaVu.defaultAntiAlias = 0

        self.antiAliased = DejaVu.defaultAntiAlias
        self._wasAntiAliased = 0
        self.drawThumbnailFlag = False
        if self.antiAliased == 0:
            self.accumWeigth = 1.
            self.jitter = None
        else:
            self.accumWeigth = 1./self.antiAliased
            self.jitter = eval('jitter._jitter'+str(self.antiAliased))

        self.newList = GL.glGenLists(1)
        self.dpyList = None

        self.visible = 1
        self.ownMaster = False # set tot tru is the master of self.Frame
                               # has to be destroyed when Camera is deleted
        self.exposeEvent = False # set to true on expose events and reset in
                                 # Viewer.ReallyRedraw

        self.firstRedraw = True

        # create a TK-event manager for this camera
        self.eventManager = EventManager(self)
        self.eventManager.AddCallback('<Map>', self.Map)
        self.eventManager.AddCallback('<Expose>', self.Expose)
        self.eventManager.AddCallback('<Configure>', self.Expose)
        self.eventManager.AddCallback('<Enter>', self.Enter_cb)

        self.onButtonUpCBlist = []    # list of functions to be called when
        self.onButtonDownCBlist = []  # mouse button is pressed or depressed
                                      # they take 1 argument of type Tk event

        # register funtion to swi
        self.addButtonDownCB(self.suspendAA)
        self.addButtonUpCB(self.restoreAA)

        self.addButtonDownCB(self.suspendNPR)
        self.addButtonUpCB(self.restoreNPR)

        self.addButtonDownCB(self.reduceSSAOQuality)
        self.addButtonUpCB(self.restoreSSAOQuality)

        self.addButtonUpCB(self.capClippedGeoms)

        # these are used in bindPickingToMouseButton to bind picking to a
        # given mouse button
        self.mouseButtonModifiers = ['None', 'Shift', 'Control', 'Alt',
                                     'Meta']
        # this keys if self.mouseButtonActions are the objects to which the
        # trackball can be attached i.e. 'Object', 'Insert2d', 'Camera' etc.
        # for each such key there is a dict with buttonnum as key (1,2,3)
        # for each such key there is a dict with keys modifiers and values
        # a string describing an action
        #
        # e.g mouseButtonActions['Object'][3]['Shift'] = 'Ztranslation'
        self.mouseButtonActions = {}
        
        for bindings in ['Object', 'Insert2d', 'Camera', 'Clip', 'Light',
                         'Texture', 'Scissor']:
            self.mouseButtonActions[bindings] = { 1:{}, 2:{}, 3:{} }
            bd = self.mouseButtonActions[bindings]
            for b in (1,2,3):
                d = bd[b]
                for mod in self.mouseButtonModifiers:
                    d[mod] = 'None'

        # initialize actions for object
        bd = self.mouseButtonActions['Object']
        for mod in self.mouseButtonModifiers:
            bd[2][mod] = 'picking'

        bd[1]['None'] = 'rotation'
        bd[1]['Shift'] = 'addToSelection'
        bd[1]['Control'] = 'removeFromSelection'
        bd[2]['None'] = 'None'
        #bd[2]['Alt'] = 'camZtranslation'
        bd[2]['Control'] = 'scale'
        bd[2]['Shift'] = 'zoom'
        bd[3]['None'] = 'XYtranslation'
        bd[3]['Control'] = 'pivotOnPixel'
        bd[3]['Shift'] = 'Ztranslation'

        # initialize actions for Insert2d
        bd = self.mouseButtonActions['Insert2d']
        for mod in self.mouseButtonModifiers:
            bd[1][mod] = 'picking'
        #bd[2]['Alt'] = 'camZtranslation'
        bd[2]['Shift'] = 'zoom'

        # initialize actions for Clip
        bd = self.mouseButtonActions['Clip']
        bd[1]['None'] = 'rotation'
        #bd[2]['None'] = 'rotation'
        #bd[2]['Alt'] = 'camZtranslation'
        bd[2]['Control'] = 'scale'
        bd[2]['Shift'] = 'zoom'
        bd[3]['None'] = 'screenXYtranslation'
        bd[3]['Control'] = 'screenZtranslation'
        bd[3]['Shift'] = 'Ztranslation'

        # initialize actions for Light
        bd = self.mouseButtonActions['Light']
        bd[1]['None'] = 'rotation'
        #bd[2]['None'] = 'rotation'
        #bd[2]['Alt'] = 'camZtranslation'
        bd[2]['Shift'] = 'zoom'

        # initialize actions for Camera
        bd = self.mouseButtonActions['Camera']
        bd[1]['None'] = 'camRotation'
        #bd[2]['None'] = 'camRotation'
        #bd[2]['Alt'] = 'camZtranslation'
        #bd[2]['Control'] = 'zoom'
        bd[3]['Shift'] = 'zoom '
        bd[3]['None'] = 'camXYtranslation'
        bd[3]['Control'] = 'camZtranslation'

        # initialize actions for Texture
        bd = self.mouseButtonActions['Texture']
        bd[1]['None'] = 'rotation'
        #bd[2]['None'] = 'rotation'
        #bd[2]['Alt'] = 'camZtranslation'
        bd[2]['Control'] = 'scale'
        bd[2]['Shift'] = 'zoom'
        bd[3]['None'] = 'XYtranslation'
        bd[3]['Shift'] = 'Ztranslation'

        # initialize actions for Scissor
        bd = self.mouseButtonActions['Scissor']
        #bd[2]['Alt'] = 'camZtranslation'
        bd[2]['Control'] = 'scale'
        bd[2]['Shift'] = 'zoom'
        bd[3]['None'] = 'translation'
        bd[3]['Shift'] = 'ratio'

        # define actionName and callback fucntions equivalence
        self.actions = {
            'Object': {
                'picking':self.initSelectionRectangle,
                'addToSelection':self.initSelectionRectangle,
                'removeFromSelection':self.initSelectionRectangle,
                'rotation':viewer.RotateCurrentObject,
                'scale':viewer.ScaleCurrentObject,
                'XYtranslation':viewer.TranslateCurrentObjectXY,
                'Ztranslation':viewer.TranslateCurrentObjectZ,
                'zoom':viewer.ScaleCurrentCamera,
                'camZtranslation':viewer.TranslateCurrentCamera,                
                'pivotOnPixel':viewer.pivotOnPixel,                
                },
            'Insert2d': {
                'picking':self.SetInsert2dPicking,
                'zoom':viewer.ScaleCurrentCamera,
                'camZtranslation':viewer.TranslateCurrentCamera,                
                },
            'Clip': {
                'picking':None,
                'rotation':viewer.RotateCurrentClipPlane,
                'scale':viewer.ScaleCurrentClipPlane,
                'screenXYtranslation':viewer.screenTranslateCurrentObjectXY,
                'Ztranslation':viewer.TranslateCurrentObjectZ,
                'zoom':viewer.ScaleCurrentCamera,
                'camZtranslation':viewer.TranslateCurrentCamera,
                'screenZtranslation':viewer.screenTranslateCurrentObjectZ,
                },
            'Light': {
                'picking':None,
                'rotation':viewer.RotateCurrentDLight,
                'zoom':viewer.ScaleCurrentCamera,
                'camZtranslation':viewer.TranslateCurrentCamera,                
                },
            'Camera': {
                'picking':None,
                'camRotation':viewer.RotateCurrentCamera,
                'zoom':viewer.ScaleCurrentCamera,
                'zoom ':viewer.ScaleCurrentCamera, #it doesn't work if we use the same name
                'camZtranslation':viewer.TranslateCurrentCamera,
                'camXYtranslation':viewer.TranslateXYCurrentCamera, #it doesn't work if we use the same name
                },
            'Texture': {
                'picking':None,
                'rotation':viewer.RotateCurrentTexture,
                'scale':viewer.ScaleCurrentTexture,
                'XYtranslation':viewer.TranslateCurrentTextureXY,
                'Ztranslation':viewer.TranslateCurrentTextureZ,
                'zoom':viewer.ScaleCurrentCamera,
                'camZtranslation':viewer.TranslateCurrentCamera,                
                },
            'Scissor': {
                'picking':None,
                'ratio':viewer.AspectRatioScissor,
                'scale':viewer.ScaleCurrentScissor,
                'translation':viewer.TranslateCurrentScissor,
                'zoom':viewer.ScaleCurrentCamera,
                'camZtranslation':viewer.TranslateCurrentCamera,                
               },
            }

        # add a trackball
        self.AddTrackball()
        for binding in ['Object', 'Insert2d', 'Camera', 'Clip', 'Light',
                        'Texture', 'Scissor']:
            self.actions[binding]['None'] = self.trackball.NoFunc

        if os.name == 'nt': #sys.platform == 'win32':
            self.eventManager.AddCallback(
                "<MouseWheel>", viewer.scaleCurrentCameraMouseWheel)
            #self.bind("<MouseWheel>", viewer.scaleCurrentCameraMouseWheel)
        else:
            self.eventManager.AddCallback(
                "<Button-4>", viewer.scaleCurrentCameraMouseWheel)
            self.eventManager.AddCallback(
                "<Button-5>", viewer.scaleCurrentCameraMouseWheel)
            #self.bind("<Button-4>", viewer.scaleCurrentCameraMouseWheel)
            #self.bind("<Button-5>", viewer.scaleCurrentCameraMouseWheel)

# light model is define in Viewer for all cameras
#        self.lightModel = None
        self.fog = Fog(self)
        self.fog.Set(color=self.backgroundColor)

        self.pack(side='left', expand=1, fill='both')

        # attributes used to draw black outlines
#        self.imCanvastop = None   # top level window for silhouette rendering
        self.contouredImage = None # will hole the final PIL image
        self.outlineim = None # will hole the final contour
        self.outline = None  # accumulation buffer used for AA contour
        self.contours = False # set to True to enable contouring
        self.d1scale = 0.013
        self.d1off = 4
        self.d1cutL = 0
        self.d1cutH = 60

        self.d1ramp = Numeric.arange(0,256,1,'f')
        
        self.d2scale = 0.0  # turn off second derivative
        self.d2off = 1
        self.d2cutL = 150
        self.d2cutH = 255

        self._suspendNPR = False # used during motion
         
        # we save it so it can be reapplied if the projection matrix is recreated
        self.pickMatrix = None

        # prepare contour highlight
        self.contourTextureName = int(glGenTextures(1)[0])
        glPrioritizeTextures(numpy.array([self.contourTextureName]), numpy.array([1.])) # supposedly make this texture fast
        _gllib.glBindTexture(GL_TEXTURE_2D, int(self.contourTextureName) )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        self.stencilTextureName = int(glGenTextures(1)[0])
        # glPrioritizeTextures supposedly make this texture fast
        glPrioritizeTextures(numpy.array([self.stencilTextureName]),
                             numpy.array([1.]))
        _gllib.glBindTexture(GL_TEXTURE_2D, int(self.stencilTextureName) )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        # prepare patterned highlight
        self.textureName = int(glGenTextures(1)[0])
        lTexture = Numeric.array(
        (
          (.0,.0,.0,.8),(.0,.0,.0,.8),(.0,.0,.0,.8),(.0,.0,.0,.8),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.8),(1.,1.,1.,.6),(1.,1.,1.,.6),(.0,.0,.0,.8),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.8),(1.,1.,1.,.6),(1.,1.,1.,.6),(.0,.0,.0,.8),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.8),(.0,.0,.0,.8),(.0,.0,.0,.8),(.0,.0,.0,.8),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
          (.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),(.0,.0,.0,.0),
        ),'f')

        _gllib.glBindTexture(GL_TEXTURE_2D, self.textureName )
        glPrioritizeTextures(numpy.array([self.textureName]), numpy.array([1.])) # supposedly make this texture fast
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        _gllib.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 8, 8, 0, GL_RGBA,
                            GL.GL_FLOAT, lTexture)
        #glEnable(GL_TEXTURE_GEN_S)
        #glEnable(GL_TEXTURE_GEN_T)
        #glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_EYE_LINEAR )
        #glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_EYE_LINEAR )
        #glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_BLEND)

        # to protect our texture, we bind the default texture while we don't use it


                             
        self.dsT = 0
        # to protect our texture, we bind the default texture while we don't use it
        self.ssao_method = 0
        self.copy_depth_ssao = True
        
        
        if 'ssao' not in kw: 
            kw['ssao'] = False
            self.ssao = False
            self.use_mask_depth = 0
            self._oldSSAOSamples = 6
        else :
            self.ssao = kw['ssao']
            self._oldSSAOSamples = 6
        if 'SSAO_OPTIONS' in kw :
            self.SSAO_OPTIONS = kw['SSAO_OPTIONS']
        else :
            self.use_mask_depth = 0
            self.setDefaultSSAO_OPTIONS()            
            
        self.setShaderSSAO()  
        _gllib.glBindTexture(GL_TEXTURE_2D, 0 ) 
        self.setShaderSelectionContour()

        self.cursorStack = []
        self.currentCursor = 'default'
        

    def addButtonDownCB(self, func):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        assert callable(func)
        if func not in self.onButtonDownCBlist:
            self.onButtonDownCBlist.append(func)


    def delButtonDownCB(self, func, silent=False):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if func in self.onButtonDownCBlist:
            self.onButtonDownCBlist.remove(func)
        else:
            if not silent:
                print 'WARNING: delButtonDownCB: function not found', func


    def addButtonUpCB(self, func):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        assert callable(func)
        if func not in self.onButtonUpCBlist:
            self.onButtonUpCBlist.append(func)


    def delButtonUpCB(self, func, silent=False):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if func in self.onButtonUpCBlist:
            self.onButtonUpCBlist.remove(func)
        else:
            if not silent:
                print 'WARNING: delButtonUpCB: function not found', func

    def reduceSSAOQuality(self, event):
        if self.ssao:
            self._oldSSAOSamples = self.SSAO_OPTIONS['samples'][0]
            if len(self.SSAO_OPTIONS['samples']) == 5 :
                self.SSAO_OPTIONS['samples'][-1].set(2)
            else:
                self.SSAO_OPTIONS['samples'][0] = 2
            
    def restoreSSAOQuality(self, event):
        if self.ssao:
            if len(self.SSAO_OPTIONS['samples']) == 5 :
                self.SSAO_OPTIONS['samples'][-1].set(self._oldSSAOSamples)
            else:
                self.SSAO_OPTIONS['samples'][0] = self._oldSSAOSamples
            del self._oldSSAOSamples

            
    def suspendAA(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Function used to turn off anti-aliasing during motion
"""
        #print "suspendAA"
        if self.antiAliased == False:
            self.antiAliased = 0
        assert isinstance(self.antiAliased, types.IntType), self.antiAliased
        if self._wasAntiAliased == 0 : # else it is already suspended
            if self.antiAliased <= DejaVu.allowedAntiAliasInMotion:
                # save the state
                self._wasAntiAliased = self.antiAliased
                # we don't suspend anti alias or anti alias is already suspended
            else:
                # save the state
                self._wasAntiAliased = self.antiAliased
                # we suspend anti alias
                self.antiAliased = 0


    def restoreAA(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Function used to restore anti-aliasing after motion
"""
        #print "restoreAA"
        self.antiAliased = self._wasAntiAliased
        self._wasAntiAliased = 0


    def capClippedGeoms(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Function used to cap clipped geoms when button is released"""

        if self.currentTransfMode!='Clip':
            return
        for geom, cp, capg in self.viewer.cappedGeoms:
            if cp != self.viewer.currentClip:
                continue
            vc, fc = cp.getCapMesh(geom)
            capg.Set(vertices=vc, faces=fc)


    def suspendNPR(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Function used to turn off NPR during motion
"""
        if self.viewer.GUI.contourTk.get() is True:
            self._suspendNPR = True
            self._suspendNPR_rootMaterialsPropDiffuse = self.viewer.rootObject.materials[GL.GL_FRONT].prop[1]
            self._suspendNPR_rootMaterialsbindDiffuse = self.viewer.rootObject.materials[GL.GL_FRONT].binding[1]
            #print "self._suspendNPR_rootMaterialsPropDiffuse", self._suspendNPR_rootMaterialsPropDiffuse
            #print "self._suspendNPR_rootMaterialsbindDiffuse", self._suspendNPR_rootMaterialsbindDiffuse
            if    self._suspendNPR_rootMaterialsbindDiffuse == 1 \
              and len(self._suspendNPR_rootMaterialsPropDiffuse) == 1 \
              and len(self._suspendNPR_rootMaterialsPropDiffuse[0]) >= 3 \
              and self._suspendNPR_rootMaterialsPropDiffuse[0][0] == 1 \
              and self._suspendNPR_rootMaterialsPropDiffuse[0][1] == 1 \
              and self._suspendNPR_rootMaterialsPropDiffuse[0][2] == 1 :
                # root color is set to grey
                self.viewer.rootObject.materials[GL.GL_FRONT].prop[1] = Numeric.array( ((.5, .5, .5, 1.0 ), ), 'f' )
                self.viewer.rootObject.materials[GL.GL_FRONT].binding[1] = viewerConst.OVERALL
            # lighting is turned on
            self._suspendNPR_OverAllLightingIsOn = self.viewer.OverAllLightingIsOn.get()
            self.viewer.OverAllLightingIsOn.set(1)
            self.viewer.deleteOpenglListAndCallRedrawAndCallDisableGlLighting()


    def restoreNPR(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Function used to restore NPR after motion
"""
        if self.viewer.GUI.contourTk.get() is True:
            # root color is set to what it was
            self.viewer.rootObject.materials[GL.GL_FRONT].prop[1] = self._suspendNPR_rootMaterialsPropDiffuse
            self.viewer.rootObject.materials[GL.GL_FRONT].binding[1] = self._suspendNPR_rootMaterialsbindDiffuse
            # lighting is set to what it was
            self.viewer.OverAllLightingIsOn.set(self._suspendNPR_OverAllLightingIsOn)
            self.viewer.deleteOpenglListAndCallRedrawAndCallDisableGlLighting()
            self._suspendNPR = False


    def pushCursor(self, cursorName):
        self.configure(cursor=cursorsDict[cursorName])
        self.cursorStack.append(self.currentCursor)
        self.currentCursor = cursorName


    def popCursor(self):
        if len(self.cursorStack):
            self.currentCursor = cursorName = self.cursorStack.pop(-1)
            self.configure(cursor=cursorsDict[cursorName])

    
    def setCursor(self, buttonNum):
        modDict = self.viewer.kbdModifier
        xform = self.viewer.GUI.Xform.get()
        if modDict['Shift_L']:
            action = self.mouseButtonActions[xform][buttonNum]['Shift']
        elif modDict['Control_L']:
            action = self.mouseButtonActions[xform][buttonNum]['Control']
        elif modDict['Alt_L']:
            action = self.mouseButtonActions[xform][buttonNum]['Alt']
        else:
            action = self.mouseButtonActions[xform][buttonNum]['None']
            
        #print 'AAAAAAAAAAAA', action#, modDict
        if cursorsDict.has_key(action):
            self.configure(cursor=cursorsDict[action])


    def bindAllActions(self, actionDict):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        #print "bindAllActions", actionDict
        for b in (1,2,3):
            d = self.mouseButtonActions[actionDict][b]
            for mod in self.mouseButtonModifiers:
                self.bindActionToMouseButton(d[mod], b, mod, actionDict)


    def findButton(self, action, actionDict):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        for b in (1,2,3):
            d = self.mouseButtonActions[actionDict][b]
            for mod in self.mouseButtonModifiers:
                if d[mod]==action: return b, mod
        return None, None

    
    # FIXME picking and other mouse actions should be unified
    # Press events register the motion and release callbacks
    # this will enable to process picking and others in the same way
    def bindActionToMouseButton(self, action, buttonNum, modifier='None',
                                actionDict='Object'):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """registers callbacks to trigger picking when the specified mouse
button is pressed. buttonNum can be 1,2,3 or 0 to remove call backs
"""
        #print "bindActionToMouseButton", buttonNum, action, modifier, actionDict

        ehm = self.eventManager
        func = self.actions[actionDict][action]

        # find button and modifier to which actions is bound currently
        oldnum, oldmod = self.findButton(action, actionDict)

        if action in ['picking', 'addToSelection', 'removeFromSelection',
                      'pivotOnPixel']:
            if oldnum: # picking action was bound to a mouse button
                # remove the picking callbacks from previous picking button
                if modifier=='None': modifier1=''
                else: modifier1=modifier+'-'
                ev = '<'+modifier1+'ButtonPress-'+str(oldnum)+'>'
                ehm.RemoveCallback(ev, func)
                    
            # remove all motion call back on buttonNum for all modifiers
            if modifier=='None': modifier1=''
            else: modifier1=modifier+'-'
            setattr(self.trackball, modifier1+'B'+str(buttonNum)+'motion',
                    self.trackball.NoFunc)

            # now bind picking to buttonNum for all modifiers
            self.mouseButtonActions[actionDict][buttonNum][modifier] = action
            if modifier=='None': modifier1=''
            else: modifier1=modifier+'-'
            ev = '<'+modifier1+'ButtonPress-'+str(buttonNum)+'>'
            ehm.AddCallback(ev, func)

        else: # not picking
            if oldnum: # action was bound to a mouse button
                # remove the picking callbacks from previous picking button
                if oldmod=='None': mod1=''
                else: mod1=oldmod+'-'
                ev = '<'+mod1+'ButtonPress-'+str(oldnum)+'>'
                oldaction = self.mouseButtonActions[actionDict][buttonNum][oldmod]
                if oldaction=='picking' or oldaction=='pivotOnPixel':
                    ehm.RemoveCallback(ev, self.actions[actionDict][oldaction])

                # remove motion callback on oldbuttonNum for oldmodifier
                if oldmod=='None': mod=''
                else: mod=oldmod
                setattr(self.trackball, mod+'B'+str(oldnum)+'motion',
                        self.trackball.NoFunc)
                self.mouseButtonActions[actionDict][oldnum][oldmod] = 'None'

            # remove picking callback on buttonNum for modifier
            if modifier=='None': mod=''
            else: mod=modifier+'-'
            oldaction = self.mouseButtonActions[actionDict][buttonNum][modifier]
            if oldaction=='picking' or oldaction=='pivotOnPixel':
                ev = '<'+mod+'ButtonPress-'+str(buttonNum)+'>'
                ehm.RemoveCallback(ev, self.actions[actionDict][oldaction])

            
            # now bind picking to buttonNum for all modifiers
            if modifier=='None': mod=''
            else: mod=modifier
            setattr(self.trackball, mod+'B'+str(buttonNum)+'motion', func)
            self.mouseButtonActions[actionDict][buttonNum][modifier] = action

        
    def AddTrackball(self, size=0.8, rscale=2.0, tscale=0.05,
                     sscale=0.01, renorm=97):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Add a Trackball to this camera with default bindings
"""
        #print "AddTrackball"

        self.trackball = Trackball(self, size, rscale, tscale, sscale, renorm )
        ehm = self.eventManager
        #print 'FOO1'
        # COMMENTED OUT BY MS when I moved rotation to button 1
        #self.bindActionToMouseButton('rotation', 1)

##          ehm.AddCallback('<ButtonPress-1>', self.recordMousePosition_cb)
##          ehm.AddCallback('<ButtonRelease-1>', self.SelectPick)
##          ehm.AddCallback('<Shift-ButtonRelease-1>', self.CenterPick_cb)
##          ehm.AddCallback('<Double-ButtonRelease-1>', self.DoubleSelectPick_cb)
##          ehm.AddCallback('<Triple-ButtonRelease-1>', self.TransfCamera_cb)

        # <ButtonPress-1> is set by default to record the mouse position
        # add drawing of first selection rectangle
#        ehm.AddCallback("<ButtonPress-1>", self.initSelectionRectangle )
#        ehm.AddCallback("<Shift-ButtonPress-1>", self.initSelectionRectangle )
#        ehm.AddCallback("<Control-ButtonPress-1>", self.initSelectionRectangle )
#        ehm.AddCallback("<Alt-ButtonPress-1>", self.initSelectionRectangle )


    def ListBoundEvents(self, event=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """List all event bound to a callback function"""

        if not event:
            return self.bind()
        else:
            return self.bind(event)


    def __del__(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Destroy the camera
"""
        #print "StandardCamera.__del__", self
        self.frame.master.destroy()

    
    def Enter_cb(self, event=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Call back function trigger when the mouse enters the camera
"""
        if widgetsOnBackWindowsCanGrabFocus is False:
            lActiveWindow = self.focus_get()
            if    lActiveWindow is not None \
              and ( lActiveWindow.winfo_toplevel() != self.winfo_toplevel() ):
                return

        self.focus_set()
        self.tk.call(self._w, 'makecurrent')
        if not self.viewer:
            return
        self.SelectCamera()
        if not hasattr(self.viewer.GUI, 'Xform'):
            return
        self.viewer.GUI.Xform.set(self.currentTransfMode)
        if self.currentTransfMode=='Object':
            self.viewer.GUI.enableNormalizeButton(Tkinter.NORMAL)
            self.viewer.GUI.enableCenterButton(Tkinter.NORMAL)
        else:
            self.viewer.GUI.enableNormalizeButton(Tkinter.DISABLED)
            self.viewer.GUI.enableCenterButton(Tkinter.DISABLED)


    def _setFov(self, fov):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if fov > 0.0 and fov < 180.0: self.fovy = fov
        else: raise AttributeError('fov has to be < 180.0 and > 0.0 was %f'%fov)
    def _setLookFrom(self, val):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        mat = numpy.array(val, 'f')
        self.lookFrom = mat
        self.direction = self.lookAt - self.lookFrom
        
    def Set(self, check=1, redo=1, **kw):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Set various camera parameters
"""
        #print "Camera.Set", redo
        if __debug__:
            if check:
                apply( checkKeywords, (self.name,self.setKeywords), kw)
        
        val = kw.get( 'tagModified', True )
        assert val in [True, False]
        self._modified = val

        # we disable redraw because autoRedraw could cause ReallyRedraw
        # to set camera.width and camera.height BEFORE te window gets
        # resized by Tk
        if self.viewer.autoRedraw:
            restoreAutoRedraw = True
            self.viewer.stopAutoRedraw()
        else:
            restoreAutoRedraw = False
            
        w = kw.get( 'width')
        if not w is None:
            assert type(w)==types.IntType
            if w > 0:
                self.width = w
            else:
                raise AttributeError('width has to be > 0')

        h = kw.get( 'height')
        if not h is None:
            assert type(h)==types.IntType
            if h > 0:
                # we disable redraw because autoRedraw could cause ReallyRedraw
                # to set camera.width and camera.height BEFORE te window gets
                # resized by Tk
                self.height = h
            else:
                raise AttributeError('height has to be > 0')

        px = kw.get( 'rootx')
        if not px is None:
            px = max(px, 0)
            master = self.frame.master
            while hasattr(master, 'wm_maxsize') is False:
                master = master.master
            xmax, ymax = master.wm_maxsize()
            px = min(px, xmax -100)
            self.rootx = px

        py = kw.get( 'rooty')
        if not py is None:
            py = max(py, 0)
            master = self.frame.master
            while hasattr(master, 'wm_maxsize') is False:
                master = master.master
            xmax, ymax = master.wm_maxsize()
            py = min(py, ymax - 100)
            self.rooty = py

        # if width, height of position of camera changed apply changes
        if w or h or px or py:
            self.Geometry()
            self.viewer.update()

        if restoreAutoRedraw:
            self.viewer.startAutoRedraw()

        fov = kw.get( 'fov')
        if not fov is None:
            if fov > 0.0 and fov < 180.0: self.fovy = fov
            else: raise AttributeError('fov has to be < 180.0 and > 0.0 was %f'%fov)

        near = kw.get( 'near')
        if not near is None:
            if kw.has_key('far'): far = kw.get('far')
            else: far = self.far
            if near >= far:
                raise AttributeError('near sould be smaller than far')
            self.near = max(near, self.nearDefault)
            self.near_real = near
            
        far = kw.get( 'far')
        if not far is None:
            if far <= self.near:
                if self.near == self.nearDefault:
                    self.far = self.near * 1.5
                else:
                    raise AttributeError('far sould be larger than near')
            else:
                self.far = far

        if fov or near or far:
            self.SetupProjectionMatrix()

        val = kw.get( 'color')
        if not val is None:
            color = colorTool.OneColor( val )
            if color:
                self.backgroundColor = color

        val = kw.get( 'antialiased')
        if not val is None:
            if val in jitter.jitterList:
                self.antiAliased = val
                if val!=0:
                    self.accumWeigth = 1.0/val
                    self.jitter = eval('jitter._jitter'+str(val))
            else: raise ValueError('antiAliased can only by one of', \
                                   jitter.jitterList)

        # NPR parameters

        #first derivative
        val = kw.get( 'd1ramp')
        if not val is None:
                self.d1ramp=val

        val = kw.get( 'd1scale')
        if not val is None:
            assert isinstance(val, float)
            assert val>=0.0
            self.d1scale = val

        val = kw.get( 'd1off')
        if not val is None:
            assert isinstance(val, int)
            self.d1off = val

        val = kw.get( 'd1cutL')
        if not val is None:
            assert isinstance(val, int)
            assert val>=0
            self.d1cutL = val

        val = kw.get( 'd1cutH')
        if not val is None:
            assert isinstance(val, int)
            assert val>=0
            self.d1cutH = val

        #second derivative
        val = kw.get( 'd2scale')
        if not val is None:
            assert isinstance(val, float)
            assert val>=0.0
            self.d2scale = val

        val = kw.get( 'd2off')
        if not val is None:
            assert isinstance(val, int)
            self.d2off = val

        val = kw.get( 'd2cutL')
        if not val is None:
            assert isinstance(val, int)
            assert val>=0
            self.d2cutL = val

        val = kw.get( 'd2cutH')
        if not val is None:
            assert isinstance(val, int)
            assert val>=0
            self.d2cutH = val

        val = kw.get( 'contours')
        if not val is None:
            assert val in [True, False]
            if self.contours != val:
                self.contours = val
                if val is True:
                    self.lastBackgroundColorInPhotoMode = self.backgroundColor
                    self.backgroundColor = (1.,1.,1.,1.)
                    if self.viewer.OverAllLightingIsOn.get() == 1:
                        self.viewer.OverAllLightingIsOn.set(0)
                else:
                    self.backgroundColor = self.lastBackgroundColorInPhotoMode
                    if self.viewer.OverAllLightingIsOn.get() == 0:
                        self.viewer.OverAllLightingIsOn.set(1)
                self.fog.Set(color=self.backgroundColor)
                self.viewer.deleteOpenglListAndCallRedrawAndCallDisableGlLighting()
                                                        
#            if val:
#                self.imCanvastop = Tkinter.Toplevel()
#                self.imCanvas = Tkinter.Canvas(self.imCanvastop)
#                self.imCanvas1 = Tkinter.Canvas(self.imCanvastop)
#                self.imCanvas2 = Tkinter.Canvas(self.imCanvastop)
#                self.imCanvas3 = Tkinter.Canvas(self.imCanvastop)
#                self.canvasImage = None
#                self.canvasImage1 = None
#                self.canvasImage2 = None
#                self.canvasImage3 = None
#            elif self.imCanvastop:
#                self.imCanvastop.destroy()
#                self.imCanvas = None
#                self.imCanvas1 = None
#                self.imCanvas2 = None
#                self.imCanvas3 = None

#                if hasattr(self, 'ivi'):
#                    self.ivi.Exit()
#                from opengltk.OpenGL import GL
#                if not hasattr(GL, 'GL_CONVOLUTION_2D'):
#                    print 'WARNING: camera.Set: GL_CONVOLUTION_2D nor supported'
#                    self.contours = False
#                else:
#                    from DejaVu.imageViewer import ImageViewer
#                    self.ivi = ImageViewer(name='zbuffer')
                
        val = kw.get( 'boundingbox')
        if not val is None:
            if val in viewerConst.BB_MODES:
                self.drawBB = val
            else: raise ValueError('boundingbox can only by one of NO, \
ONLY, WITHOBJECT')

        val = kw.get( 'rotation')
        if not val is None:
            self.rotation = Numeric.identity(4, 'f').ravel()
            mat = Numeric.reshape(Numeric.array(val), (4,4)).astype('f')
            self.ConcatRotation(mat)

        val = kw.get( 'translation')
        if not val is None:
            self.translation = Numeric.zeros( (3,), 'f')
            mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
            self.ConcatTranslation(mat, redo=redo)

        val = kw.get( 'scale')
        if not val is None:
            self.SetScale( val, redo=redo )

        val = kw.get( 'pivot')
        if not val is None:
            self.SetPivot( val )

        val = kw.get( 'direction')
        if not val is None:
            mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
            self.direction = mat

        valLookFrom = kw.get('lookFrom')
        if valLookFrom is not None:
            mat = numpy.array(valLookFrom, 'f')
            assert mat.shape==(3,)
            self.lookFrom = mat
            self.direction = self.lookAt - self.lookFrom

        valLookAt = kw.get('lookAt')
        if valLookAt is not None:
            mat = numpy.array(valLookAt, 'f')
            assert mat.shape==(3,)
            self.lookAt = mat
            self.direction = self.lookAt - self.lookFrom

        valUp = kw.get('up')
        if valUp is not None:
            mat = numpy.array(valUp, 'f')
            assert mat.shape==(3,)
            self.up = mat

##         # compute .translation and .rotation used to build camera transformation
##         # FIXME .. could recompute only if one changed
##         if valLookAt is not None \
##           or valLookFrom is not None \
##           or valUp is not None:
##             glPushMatrix()
##             glLoadIdentity()
##             glMatrixMode(GL_MODELVIEW)
##             fx, fy, fz = self.lookFrom
##             ax, ay, az = self.lookAt
##             ux, uy, uz = self.up
##             gluLookAt( float(fx), float(fy), float(fx),
##                        float(ax), float(ay), float(az),
##                        float(ux), float(uy), float(uz) )
##             lMatrix = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')
##             lRotation, lTranslation, lScale = self.Decompose4x4(lMatrix, cleanup=False)
##             glPopMatrix()
##             if numpy.any(lMatrix):
##                 self.rotation = lRotation
##                 self.translation = lTranslation
##             self.lookAt = Numeric.reshape(Numeric.array(valLookAt), (3,)).astype('f')

##         val = kw.get( 'lookAt')
##         if not val is None:
##             mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
##             self.lookAt = mat
##             self.direction = self.lookAt - self.lookFrom

##         val = kw.get( 'lookFrom')
##         if not val is None:
##             mat = Numeric.reshape(Numeric.array(val), (3,)).astype('f')
##             self.lookFrom = mat
##             self.direction = self.lookAt - self.lookFrom

        val = kw.get( 'projectionType')
        if val==self.PERSPECTIVE:
            if self.projectionType==self.ORTHOGRAPHIC:
                self.projectionType = val
                self.OrthogonalToPerspective()
        elif val==self.ORTHOGRAPHIC:
            if self.projectionType==self.PERSPECTIVE:
                self.projectionType = val
                self.PerspectiveToOrthogonal()

        val = kw.get( 'sideBySideRotAngle')
        if not val is None:
            assert type(val)==types.FloatType
            self.sideBySideRotAngle = val
            if self.viewer:
                self.viewer.Redraw()

        val = kw.get( 'sideBySideTranslation')
        if not val is None:
            assert type(val)==types.FloatType
            self.sideBySideTranslation = val
            if self.viewer:
                self.viewer.Redraw()
        
        val = kw.get( 'ssao')
        if not val is None:
            self.ssao = kw["ssao"]
        val = kw.get( 'SSAO_OPTIONS')   
        if not val is None:
            self.SSAO_OPTIONS = kw['SSAO_OPTIONS']
        self._oldSSAOSamples = 6
        val = kw.get( 'stereoMode')
        if val is not None:
            assert val in self.stereoModesList

            glDrawBuffer(GL_BACK)

            if self.viewer is None:
                warnings.warn("""Stereo buffers are not present
or not enabled on this system.

enableStereo must be set to True in:
~/.mgltools/(ver_number)/DejaVu/_dejavurc
"""
)
                val = 'MONO'
            elif self.viewer.activeStereoSupport is False:
                if val == 'STEREO_BUFFERS':
                    warnings.warn("""Stereo buffers are not present
or not enabled on this system.

enableStereo must be set to True in:
~/.mgltools/(ver_number)/DejaVu/_dejavurc
"""
)
                    val = 'MONO'

            self.stereoMode = val
            if self.viewer:
                self.viewer.Redraw()

        val = kw.get( 'suspendRedraw')
        if val is not None:
            assert val in [True, False]
            self.suspendRedraw = val

        val = kw.get( 'drawThumbnail')
        if val is not None:
            assert val in [True, False]
            self.drawThumbnailFlag = val
        

#    def deleteOpenglList(self):
#        #import traceback;traceback.print_stack() 
#        #print "Camera.deleteOpenglList"
#        if self.dpyList is not None:
#            self.tk.call(self._w, 'makecurrent')
#            currentcontext = self.tk.call(self._w, 'contexttag')
#            if currentcontext != self.dpyList[1]:
#                warnings.warn("""deleteOpenglList failed because the current context is the wrong one""")
#                #print "currentcontext != self.dpyList[1]", currentcontext, self.dpyList[1]
#            else:
#                #print '-%d'%self.dpyList[0], currentcontext, "glDeleteLists Viewer"
#                GL.glDeleteLists(self.dpyList[0], 1)
#                self.dpyList = None


    def SwapBuffers(self):
        if __debug__:
            if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.tk.call(self._w, 'swapbuffers')

    def Activate(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Make this Opengl widget the current destination for drawing."""
        self.tk.call(self._w, 'makecurrent')


    def OrthogonalToPerspective(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Compute left, right, top, bottom from field of view"""
        d = self.near + (self.far - self.near)*0.5
        self.fovy = (math.atan(self.top/d) * 360.0) / math.pi
        self.SetupProjectionMatrix()
        

    def PerspectiveToOrthogonal(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Compute left, right, top, bottom from field of view"""

        aspect = self.width / float(self.height)

        fov2 = (self.fovy*math.pi) / 360.0  # fov/2 in radian
        d = self.near + (self.far - self.near)*0.5

        self.top = d*math.tan(fov2)
        self.bottom = -self.top
        self.right = aspect*self.top
        self.left = -self.right
        self.SetupProjectionMatrix()


    def SetupProjectionMatrix(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Setup the projection matrix"""

        if not self.initialized:
            return
        
        self.tk.call(self._w, 'makecurrent')

        glViewport(0, 0, self.width, self.height)

        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()

        glMatrixMode(GL_PROJECTION);
        glLoadIdentity()

##         if self.viewer.tileRender:
##             print 'FUGU'
##             if self.projectionType==self.PERSPECTIVE:
##                 self.viewer.tileRenderCtx.perspective(self.fovy,
##                            float(self.width)/float(self.height),
##                            self.near, self.far)
##             else:
##                 self.viewer.tileRenderCtx.ortho(self.left, self.right,
##                                                 self.bottom, self.top, 
##                                                 self.near, self.far)
##             print 'near', self.viewer.tileRenderCtx.Near
            
        if self.projectionType==self.PERSPECTIVE:
            
            # protect from bug in mac intel when zomming on molecule 1BX4
            if sys.platform == 'darwin':
                if self.fovy < .003:
                    self.fovy = .003

            gluPerspective(float(self.fovy),
                           float(self.width)/float(self.height),
                           float(self.near), float(self.far))
        else:
            glOrtho(float(self.left), float(self.right),
                    float(self.bottom), float(self.top), 
                    float(self.near), float(self.far))
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()


##          from opengltk.OpenGL import GLU

##          GLU.gluLookAt(0., 0., 30., 0.,0.,0., 0.,1.,0.)
##          print 'Mod Mat:', glGetDoublev(GL_MODELVIEW_MATRIX)
##          glLoadIdentity();
    #  The first 6 arguments are identical to the glFrustum() call.
    # 
    #  pixdx and pixdy are anti-alias jitter in pixels. 
    #  Set both equal to 0.0 for no anti-alias jitter.
    #  eyedx and eyedy are depth-of field jitter in pixels. 
    #  Set both equal to 0.0 for no depth of field effects.
    #
    #  focus is distance from eye to plane in focus. 
    #  focus must be greater than, but not equal to 0.0.
    #
    #  Note that AccFrustum() calls glTranslatef().  You will 
    #  probably want to insure that your ModelView matrix has been 
    #  initialized to identity before calling accFrustum().

    def AccFrustum(self, left, right, bottom, top, near, far,
                   pixdx, pixdy, eyedx, eyedy, focus):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        viewport = Numeric.array(glGetDoublev (GL_VIEWPORT))

        xwsize = right - left
        ywsize = top - bottom

        dx = -(pixdx*xwsize/viewport[2] + eyedx*near/focus)
        dy = -(pixdy*ywsize/viewport[3] + eyedy*near/focus)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum (float(left + dx), float(right + dx),
                   float(bottom + dy), float(top + dy),
                   float(near), float(far))
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef (float(-eyedx), float(-eyedy), 0.0)


    #  The first 4 arguments are identical to the gluPerspective() call.
    #  pixdx and pixdy are anti-alias jitter in pixels. 
    #  Set both equal to 0.0 for no anti-alias jitter.
    #  eyedx and eyedy are depth-of field jitter in pixels. 
    #  Set both equal to 0.0 for no depth of field effects.
    #
    #  focus is distance from eye to plane in focus. 
    #  focus must be greater than, but not equal to 0.0.
    #  Note that AccPerspective() calls AccFrustum().

    def AccPerspective(self, pixdx, pixdy, eyedx, eyedy, focus,
                       left=None, right=None, bottom=None, top=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Build perspective matrix for jitter"""

        from math import pi, cos, sin

        fov2 = self.fovy*pi / 360.0;
        if top is None:
            top = self.near / (cos(fov2) / sin(fov2))
        if bottom is None:
            bottom = -top
        if right is None:
            right = top * float(self.width)/float(self.height)
        if left is None:
            left = -right;
        
        self.AccFrustum (left, right, bottom, top, self.near, self.far,
                         pixdx, pixdy, eyedx, eyedy, focus)


    def InitGL(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Initialize some GL features"""

        self.tk.call(self._w, 'makecurrent')
        glEnable(GL_CULL_FACE)
        glEnable(GL_NORMALIZE)  # required if glScale is used,
                                    # else the lighting doesn't work anymore
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)

        # blend function used for line anti-aliasing
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        self.initialized = 1


    def Map(self, *dummy):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Cause the opengl widget to redraw itself."""
        self.Expose()


##     def Configure(self, *dummy):
##         """Cause the opengl widget to redraw itself."""
##         self.tk.call(self._w, 'makecurrent')
##         self.width = self.winfo_width()
##         self.height = self.winfo_height()
##         self.rootx = self.winfo_rootx()
##         self.rooty = self.winfo_rooty()
##         # FIXME .. this is not symetrical ... should we just recompute left, right,
##         # top and botom here ???
##         if self.projectionType==self.ORTHOGRAPHIC:
##             self.PerspectiveToOrthogonal()
##         else:
##             self.SetupProjectionMatrix()

##         self.Expose()


    def Expose(self, event=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """set the camera's exposeEvent so that at the next redraw
the camera width and height are updated
"""
        if not self.viewer.isInitialized:
            self.after(100, self.Expose)
        else:
            # if viewer is in autoRedraw mode the next redraw will handle it
            if not self.exposeEvent and self.viewer.autoRedraw:
                self.viewer.Redraw()
                self.exposeEvent = True

            for o in self.viewer.rootObject.AllObjects():
                if o.needsRedoDpyListOnResize or o.scissor:
                    self.viewer.objectsNeedingRedo[o] = None
        

## moved the width and height into viewer.ReallyRedraw
##     def ReallyExpose(self, *dummy):
##         """Redraw the widget.
##         Make it active, update tk events, call redraw procedure and
##         swap the buffers.  Note: swapbuffers is clever enough to
##         only swap double buffered visuals."""
##         self.tk.call(self._w, 'makecurrent')
##         self.width = self.winfo_width()
##         self.height = self.winfo_height()
##         #self.SetupProjectionMatrix()
##         #self.InitGL()
##         self.Redraw()

    

    def drawOneObjectThumbnail(self, obj):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.ActivateClipPlanes( obj.clipP, obj.clipSide )
        if obj.scissor:
            glEnable(GL_SCISSOR_TEST)
            glScissor(obj.scissorX, obj.scissorY, obj.scissorW, obj.scissorH)

        inst = 0
        v = obj.vertexSet.vertices.array
        v = Numeric.reshape(v, (-1,3)).astype('f')

        for m in obj.instanceMatricesFortran:
            inst = inst + 1
            glPushMatrix()
            glMultMatrixf(m)
            if isinstance(obj, Transformable):            
                v = obj.vertexSet.vertices.array
                if len(v.shape) >2 or v.dtype.char!='f':
                    v = Numeric.reshape(v, (-1,3)).astype('f')
                   
                if len(v) >0:
                    #t1 = time()
                    namedPoints(len(v), v)
                    #glVertexPointer(2, GL_FLOAT, 0, v)
                    #glEnableClientState(GL_VERTEX_ARRAY)
                    #glDrawArrays(GL_POINTS, 0, len(v) )
                    #glDisableClientState(GL_VERTEX_ARRAY)

            else: #Insert2d
                obj.pickDraw()

            glPopMatrix()

        for c in obj.clipP: # disable object's clip planes
            c._Disable()
        if obj.scissor:
            glDisable(GL_SCISSOR_TEST)


    def DrawObjThumbnail(self, obj):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """draws an object for picking purposes. If type is 'vertices' a
display list for vertices identification is used. If type is parts
a display list identifying geometric primitives such as triangles or
lines is used
"""
        if isinstance(obj, Transformable):
            glPushMatrix()
            obj.MakeMat()
            self.ActivateClipPlanes( obj.clipPI, obj.clipSide )
            inst = 0
            for m in obj.instanceMatricesFortran:
                glPushMatrix()
                glMultMatrixf(m)
                for child in obj.children:
                    if child.visible:
                        self.DrawObjThumbnail(child)
                glPopMatrix()
                inst = inst + 1
            if obj.visible:
                self.drawOneObjectThumbnail(obj)
            for c in obj.clipPI: # disable object's clip planes that are
                c._Disable()     # inherited by children
            glPopMatrix()     # Restore the matrix


    def RedrawThumbnail(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        glClear(GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glPointSize(1.0)
        self.BuildTransformation()  # camera transformation
        obj = self.viewer.rootObject
        obj.MakeMat() 
        if len(obj.clipPI):
            self.ActivateClipPlanes( obj.clipPI, obj.clipSide )
        inst = 0
        for m in obj.instanceMatricesFortran:
            glPushMatrix()
            glMultMatrixf(m)
            for child in obj.children:
                if child.visible:
                    self.DrawObjThumbnail(child)
            glPopMatrix()
            inst = inst + 1
        for c in obj.clipPI: c._Disable()
        glPopMatrix()


    def drawThumbnail(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.tk.call(self._w, 'makecurrent')

        glViewport(0, 0, self.width/10, self.height/10)

        glMatrixMode (GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity ()

        # create projection matrix and modeling
#        self.SetupProjectionMatrix()
        if self.projectionType==self.PERSPECTIVE:
            gluPerspective(float(self.fovy),
                           float(self.width)/float(self.height),
                           float(self.near),float(self.far))
        else:
            glOrtho(float(self.left),float(self.right),
                    float(self.bottom), float(self.top), 
                    float(self.near), float(self.far))
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.RedrawThumbnail()
        glFlush ()

        glMatrixMode (GL_PROJECTION)
        glPopMatrix ()
        glMatrixMode(GL_MODELVIEW)

        
    def DoPick(self, x, y, x1=None, y1=None, type=None, event=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Makes a redraw in GL_SELECT mode to pick objects
"""
        if self.stereoMode != 'MONO':
            return
        if type is None:
            type = self.viewer.pickLevel
        if x1 is None: x1 = x
        if y1 is None: y1 = y
        #print 'pick at', x, y, x1, y1

        self.tk.call(self._w, 'makecurrent')
        vp = [0,0,self.width, self.height]

        selectBuf = glSelectBuffer( 1000000 ) 
        # 500000 was insuficient on bigger molecule as 2plv.pdb with MSMS

        y1 = vp[3] - y1
        y = vp[3] - y

        dx = x - x1
        dy = y - y1
        #x = x
        pickWinSize = 10
        
        if math.fabs(dx) < pickWinSize: dx=pickWinSize
        else: x = x1 + (dx/2)

        if math.fabs(dy) < pickWinSize: dy=pickWinSize
        else: y = y1 + (dy/2)

        if dx==pickWinSize and dy==pickWinSize:
            mode = 'pick'
        else: 
            mode = 'drag select'

        abdx = int(math.fabs(dx))
        abdy = int(math.fabs(dy))
        #print 'pick region ', x-math.fabs(dx), y-math.fabs(dy), x+math.fabs(dx), y+math.fabs(dy), mode

        # debug
        glRenderMode (GL_SELECT)
        self.renderMode = GL_SELECT

        glInitNames()
        glPushName(0)

        glMatrixMode (GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity ()

        # create abs(dx)*abs(dy) pixel picking region near cursor location
        gluPickMatrix( x, y, abdx, abdy, vp)

        # we save it so it can be reapplied if the projection matrix is recreated
        self.pickMatrix = glGetFloatv(GL_PROJECTION_MATRIX)

        # create projection matrix and modeling
#        self.SetupProjectionMatrix()
        if self.projectionType==self.PERSPECTIVE:
            gluPerspective(self.fovy,float(self.width)/float(self.height),
                           self.near, self.far)
        else:
            glOrtho(float(self.left),float(self.right),
                    float(self.bottom),float(self.top), 
                    float(self.near), float(self.far))
            
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.RedrawPick(type);
        glFlush ()

        # debug
        ###self.tk.call(self._w, 'swapbuffers')
        ###return PickObject('pick')

        self.renderMode = GL_RENDER;
        # get the number of hits

        selectHits = glRenderMode (GL_RENDER)
        #print "hits", selectHits

        #removed because it generates bug in displaylist
        #if selectHits == 0:
        #    # if we pick the background, root becomes selected
        #    self.viewer.SetCurrentObject(self.viewer.rootObject)
        
        # restore projection matrix
        glMatrixMode (GL_PROJECTION)
        glPopMatrix ()

        # unproject points x and y
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()  # restore matrix for unproject
        self.BuildTransformation()
        self.viewer.rootObject.MakeMat()

        self.unProj_model = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.unProj_proj = glGetDoublev(GL_PROJECTION_MATRIX)
        self.unProj_view = glGetIntegerv(GL_VIEWPORT)
        
        p1 = gluUnProject( (x, y, 0.), self.unProj_model, self.unProj_proj,
                           self.unProj_view)
        p2 = gluUnProject( (x, y, 1.), self.unProj_model, self.unProj_proj,
                           self.unProj_view)
        glLoadIdentity()

        if selectHits:
            if mode == 'pick':
                pick = self.handlePick(selectHits, selectBuf, type)
            else:
                pick = self.handleDragSelect(selectHits, selectBuf, type)
        else:
            pick = PickObject('pick', self)

##          if selectHits and self.viewer.showPickedVertex:
##              self.DrawPickingSphere(pick)
            
        pick.p1 = p1
        pick.p2 = p2
        pick.box = (x, y, x1, y1)
        pick.event = event
        
        self.viewer.lastPick = pick

        #DEBUG used to debug picking
#        from IndexedPolylines import IndexedPolylines
#        l = IndexedPolylines('line', vertices = (self._p1,self._p2), faces=((0,1),) )
#        self.viewer.AddObject(l)
#        return o, parts, self.viewer.lastPickedVertex, self._p1, self._p2 

        return pick

#    ## DEPRECATED, is not using instance for computing coordinates (MS 12/04)
#    def DrawPickingSphere(self, pick):
#        """display a transient sphere at picked vertex"""
#        from warnings import warn
#        warnings.warn('DrawPickingSphere is deprecated',
#                      DeprecationWarning, stacklevel=2)
#        
#        obj = pick.hits.keys()[0]
#        varray = obj.vertexSet.vertices.array
#        coords = Numeric.take( varray, pick.hits[obj] )
#        p = self.viewer.pickVerticesSpheres
#        mat = obj.GetMatrix( obj.LastParentBeforeRoot() )
#        mat = Numeric.transpose(mat)
#        p.Matrix = Numeric.reshape(mat, (16, ))
#        p.SetMatrix(mat)
#        self.viewer.pickVerticesSpheres.Set(vertices=coords,
#                                     transient=self.viewer.pickReminiscence,
#                                     redo=redo)
#        self.Redraw()


    def xyzFromPixel( self, winx, winy):
        """compute x, and y values in scene from x and y corrdinates in event
        find z from Zbuffer.

        pt3d, background = xyzFromPixel( self, winx, winy)

        background is True if pick occured on background"""

        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        # unproject pixel
        self.tk.call(self._w, 'makecurrent')
        glPushMatrix()
        self.BuildTransformation()  # camera transformation
        nar = Numeric.zeros(1, 'f')
        glFinish()
        from opengltk.extent import _gllib as gllib
        gllib.glReadPixels( winx, winy, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT,
                            nar)
        winz = float(nar[0])
        background = winz == 1.0

        #print 'xyzFromPixel: picks',winz, background

        #print "winx, winy, winz", winx, winy, winz
        l3dPoint = gluUnProject( (winx, winy, winz), 
                                 glGetDoublev(GL_MODELVIEW_MATRIX),
                                 glGetDoublev(GL_PROJECTION_MATRIX),
                                 glGetIntegerv(GL_VIEWPORT)
                               )
        #print "l3dPoint", l3dPoint
        glPopMatrix()
        return l3dPoint, background


    def handleDragSelect(self, selectHits, selectBuf, type):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        pick = PickObject('drag select', self, type)
        p = 0
        for i in range(selectHits):
            nb_names = selectBuf[p]
            z1 = float(selectBuf[p+1]) #/ 0x7fffffff
            end = int(p+3+nb_names)
            instance = list(selectBuf[p+3:end-2])
            obj = self.objPick[int(selectBuf[end-2])]
            vertex = selectBuf[end-1]
            #print 'vertex', vertex, obj.name, instance
            pick.add(object=obj, vertex=vertex, instance=instance)
            p = end
        return pick


    def handlePick(self, selectHits, selectBuf, type):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """We are looking for the vertex closest to the viewer"""
        # now handle selection
        mini = 9999999999.9
        p = 0
        vertex = None
        obj = None
        # loop over hits. selectBuf contains for each hit:
        #   - number of names for that hit (num)
        #   - z1
        #   - z2
        #   - instNumRoot, instNumRootParent_1, instNumRootParent_2, ... ,
        #      geomIndex, vertexNum
        # For each parent we have an instance number
        # the geomIndex is the index of the geometry in self.objPick
        # vertexNum is the index of the vertex in the geometry's vertexSet
        #
        pick = PickObject('pick', self, type)
        
        for i in range(selectHits):
            nb_names = selectBuf[p]
            z1 = float(selectBuf[p+1]) #/ 0x7fffffff
            # compute the end of the pick info for this hit
            end = int(p+3+nb_names)
            #print 'vertex', selectBuf[end-1], self.objPick[selectBuf[end-2]], list(selectBuf[p+3:end-2]), z1
            if z1 < mini:
                #end = p+3+nb_names
                mini = z1
                instance = list(selectBuf[p+3:end-2])
                obj = self.objPick[int(selectBuf[end-2])]
                vertex = selectBuf[end-1]
            # advance p to begin of next pick hit data
            p = end
        pick.add( object=obj, vertex=vertex, instance=instance )
        return pick
    

    def drawOneObjectPick(self, obj, type):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        lIsInstanceTransformable = isinstance(obj, Transformable)
        if lIsInstanceTransformable:
            self.ActivateClipPlanes( obj.clipP, obj.clipSide )
            if obj.scissor:
                glEnable(GL_SCISSOR_TEST)
                glScissor(obj.scissorX, obj.scissorY,
                         obj.scissorW, obj.scissorH)

        obj.pickNum = self.pickNum
        self.objPick.append(obj)

        inst = 0
        
        if lIsInstanceTransformable and type=='vertices':
                #print 'using vertices', obj.name
                v = obj.vertexSet.vertices.array
                v = Numeric.reshape(v, (-1,3)).astype('f')

        for m in obj.instanceMatricesFortran:
            glPushName(inst) # instance number
            inst = inst + 1
            glPushName(self.pickNum) # index into self.objPick
            glPushMatrix()
            glMultMatrixf(m)
            if lIsInstanceTransformable:            
                if type=='vertices':
                    #print 'using vertices', obj.name
                    v = obj.vertexSet.vertices.array
                    if len(v.shape) >2 or v.dtype.char!='f':
                        v = Numeric.reshape(v, (-1,3)).astype('f')
                   
                    if len(v) >0:
                        #t1 = time()
                        namedPoints(len(v), v)
                        #print 'draw points:', time()-t1
    ##                  i = 0
    ##                  for p in v:
    ##                      glPushName(i)
    ##                      glBegin(GL_POINTS)
    ##                      glVertex3f(p[0], p[1], p[2])
    ##                      glEnd()
    ##                      glPopName()
    ##                      i = i + 1
                    
    # can't be used since we cannot push and pop names
    ##                  glVertexPointer(2, GL_FLOAT, 0, v)
    ##                  glEnableClientState(GL_VERTEX_ARRAY)
    ##                  glDrawArrays(GL_POINTS, 0, len(v) )
    ##                  glDisableClientState(GL_VERTEX_ARRAY)
                     
                elif type=='parts':
                    if obj.pickDpyList:
                        #print "pick displayFunction"
                        currentcontext = self.viewer.currentCamera.tk.call(self.viewer.currentCamera._w, 'contexttag')
                        if currentcontext != obj.pickDpyList[1]:
                            warnings.warn("""DisplayFunction failed because the current context is the wrong one""")
                            #print "currentcontext != obj.pickDpyList[1]", currentcontext, obj.pickDpyList[1]
                        else:
                            print '#%d'%obj.pickDpyList[0], currentcontext, "glCallList Camera"
                            glCallList(obj.pickDpyList[0])
                    else:
                        #print "displayFunction"
                        obj.DisplayFunction()
                else:
                    print 'Error: bad type for PickRedraw: ',type
            else: #Insert2d
                obj.pickDraw()

            glPopMatrix()
            glPopName() # instance number

            glPopName() # index into self.objPick
        self.pickNum = self.pickNum + 1

        if lIsInstanceTransformable:
            for c in obj.clipP: # disable object's clip planes
                c._Disable()
            if obj.scissor:
                glDisable(GL_SCISSOR_TEST)


    def DrawObjPick(self, obj, type):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """draws an object for picking purposes. If type is 'vertices' a
        display list for vertices identification is used. If type is parts
        a display list identifying geometric primitives such as triangles or
        lines is used"""

        lIsInstanceTransformable = isinstance(obj, Transformable)
        if lIsInstanceTransformable:
            glPushMatrix()
            obj.MakeMat()
            self.ActivateClipPlanes( obj.clipPI, obj.clipSide )

        inst = 0
        for m in obj.instanceMatricesFortran:
            glPushName(inst) # instance number
            glPushMatrix()
            glMultMatrixf(m)
            for child in obj.children:
                if child.visible:
                    self.DrawObjPick(child, type)
            glPopMatrix()
            glPopName() # instance number
            inst = inst + 1
        
        if obj.pickable:
            self.drawOneObjectPick(obj, type)

        if lIsInstanceTransformable:
            for c in obj.clipPI: # disable object's clip planes that are
                c._Disable()     # inherited by children

            glPopMatrix()     # Restore the matrix

               
    def RedrawPick(self, type):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.pickNum = 0
        self.objPick = [ ]
        glClear(GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glPointSize(1.0)
        self.BuildTransformation()  # camera transformation
        obj = self.viewer.rootObject
        obj.MakeMat() 
        if len(obj.clipPI):
            self.ActivateClipPlanes( obj.clipPI, obj.clipSide )
        inst = 0
        for m in obj.instanceMatricesFortran:
            glLoadName(inst)
            glPushMatrix()
            glMultMatrixf(m)
            for child in obj.children:
                if child.visible:
                    self.DrawObjPick(child, type)
            glPopMatrix()
            inst = inst + 1
        for c in obj.clipPI: c._Disable()
        glPopMatrix()

        
    def drawRect(self, P1, P2, P3, P4, fill=0):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if fill: prim=GL_POLYGON
        else: prim=GL_LINE_STRIP
        glBegin(prim)
        glVertex3f( float(P1[0]), float(P1[1]), float(P1[2]) )
        glVertex3f( float(P2[0]), float(P2[1]), float(P2[2]) )
        glVertex3f( float(P3[0]), float(P3[1]), float(P3[2]) )
        glVertex3f( float(P4[0]), float(P4[1]), float(P4[2] ))
        glVertex3f( float(P1[0]), float(P1[1]), float(P1[2] ))
        glEnd()


    def Insert2dPickingCallBack(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        # this shoudn't be necessary but somewhere/sometimes the 
        # current object is set without a call to SetCurrentObject
        # So self.viewer.currentCamera.bindAllActions('Insert2d') is no set
        if isinstance(self.viewer.currentObject, Insert2d) is False:
            assert isinstance(self.viewer.currentObject, Transformable), self.viewer.currentObject
            self.viewer.SetCurrentObject(self.viewer.currentObject)
            return

        self.viewer.currentObject.respondToMouseMove(event)


    def SetInsert2dPicking(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        num = str(self.findButton('picking', 'Insert2d')[0])            
        ehm = self.eventManager
        for mod in self.mouseButtonModifiers:
            if mod == 'None': 
                mod = ''
            else: 
                mod = mod + '-'
            ev = '<' + mod + 'B' + num + '-Motion>'
            #print "ev", ev
            ehm.AddCallback(ev, self.Insert2dPickingCallBack )       
        pick = self.DoPick(event.x, event.y, event=event)
        #if pick and len(pick.hits):
        self.viewer.processPicking(pick)


    def initSelectionRectangle(self, event):
        if __debug__:
            if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if isinstance(self.viewer.currentObject, Insert2d):
            return
        if self.stereoMode != 'MONO':
            return
        self.selectDragRect = 1
        self.afid=None
        self.fill=0
        self.tk.call(self._w, 'makecurrent')
        glPushMatrix()
        self.BuildTransformation()  # camera transformation
        glDrawBuffer(GL_FRONT)
#        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
#        glDisable(GL_CULL_FACE)
        glLineWidth( 1.0 )
        glDisable( GL_LIGHTING )
        glColor3f( float(self.selectionColor[0]), float(self.selectionColor[1]),
                      float(self.selectionColor[2]) )
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_LOGIC_OP)
        glLogicOp(GL_XOR)
        x2 = self._x1 = event.x
        y2 = self._y1 = self.height - event.y

        self.unProj_model = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.unProj_proj = glGetDoublev(GL_PROJECTION_MATRIX)
        self.unProj_view = glGetIntegerv(GL_VIEWPORT)

        from opengltk.extent import _glulib as glulib
        self._P1 = gluUnProject( (self._x1, self._y1, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view )
        self._P2 = gluUnProject( (self._x1, y2, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view )
        self._P3 = gluUnProject( (x2, y2, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view )
        self._P4 = gluUnProject( (x2, self._y1, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view )

        # draw first rectangle
        #self.history = [ ('draw', self._P3) ]
        self.drawRect( self._P1, self._P2, self._P3, self._P4 )
        glPopMatrix()

        # set "<ButtonMotion-1>" to call draw selection rectangle 
        # add un-drawing of last selection rectangle and call functions
        ehm = self.eventManager
        num = str(event.num)#str(self.findButton('picking', 'Object')[0])
        for mod in self.mouseButtonModifiers:
            if mod=='None': mod=''
            else: mod=mod+'-'
            ev = '<'+mod+'B'+num+'-Motion>'
            ehm.AddCallback(ev, self.drawSelectionRectangle )
            ehm.AddCallback("<"+mod+"ButtonRelease-"+num+">",
                            self.endSelectionRectangle )


    def drawSelectionRectangle(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        if not self.selectDragRect: return
        self.tk.call(self._w, 'makecurrent')
        glPushMatrix()
        self.BuildTransformation()  # camera transformation
        #print 'AAAAAAAAAAA2 drawSelectionRectangle'

        # draw over previous rectangle
        #self.history.append( ('hide', self._P3) )
        glDisable(GL_DEPTH_TEST)
        if self.fill:
            self.drawRect( self._P1, self._P2, self._P3, self._P4, 1 )
            self.fill = 0
        else:
            self.drawRect( self._P1, self._P2, self._P3, self._P4, 0 )

        # draw new rectangle
        x2 = event.x
        y2 = self.height - event.y

        self.unProj_model = glGetDoublev(GL_MODELVIEW_MATRIX)

        self._P2 = gluUnProject( (self._x1, y2, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view)
        self._P3 = gluUnProject( (x2, y2, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view)
        self._P4 = gluUnProject( (x2, self._y1, 0.5),
                                 self.unProj_model, self.unProj_proj,
                                 self.unProj_view)
        #self.history.append( ('draw', self._P3) )
        self.drawRect( self._P1, self._P2, self._P3, self._P4, self.fill )
        glPopMatrix()
        glFlush()
        if self.fillSelectionBox:
            if self.afid:
                self.after_cancel(self.afid)
            self.afid = self.after(self.fillDelay, self.DrawFilledSelectionBox)
        

    def DrawFilledSelectionBox(self, event=None):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.fill = 1
        self.tk.call(self._w, 'makecurrent')
        glPushMatrix()
        self.BuildTransformation()  # camera transformation

        # draw over previous rectangle
        self.drawRect( self._P1, self._P2, self._P3, self._P4, 0 )

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_CULL_FACE)
        glColor3f( float(self.selectionColor[0]), float(self.selectionColor[1]),
                      float(self.selectionColor[2] ))
        self.drawRect( self._P1, self._P2, self._P3, self._P4, 1 )
        glFlush()
        glPopMatrix()


    def endSelectionRectangle(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        #print "Camera.endSelectionRectangle"

        if not self.selectDragRect: return

        if self.afid:
            self.after_cancel(self.afid)

        # remove "<Any-ButtonMotion-1>" to call draw selection rectangle 
        # remove un-drawing of last selection rectangle and call functions
        ehm = self.eventManager
        num = str(event.num)#str(self.findButton('picking', 'Object')[0])
        for mod in self.mouseButtonModifiers:
            if mod=='None': mod=''
            else: mod=mod+'-'
            ev = '<'+mod+'B'+num+'-Motion>'
            ehm.RemoveCallback(ev, self.drawSelectionRectangle )
            ehm.RemoveCallback("<"+mod+"ButtonRelease-"+num+">",
                               self.endSelectionRectangle )

        self.selectDragRect = 0
        self.tk.call(self._w, 'makecurrent')
        glPushMatrix()
        self.BuildTransformation()  # camera transformation

        # this line is required for last rectangle to disappear !
        # not sure why
        # oct 2001: apparently not necessary
        #glEnable(GL_COLOR_LOGIC_OP)

        #self.history.append( ('hide', self._P3) )
        self.drawRect( self._P1, self._P2, self._P3, self._P4 )

        #self.drawRect( self._P1, self._P2, self._P3, self._P4 )
        glPopMatrix()
        
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_COLOR_LOGIC_OP)
        #glEnable(GL_LIGHTING)
        if self.viewer is not None:
            self.viewer.enableOpenglLighting()
        glDrawBuffer(GL_BACK)
        pick = self.DoPick(event.x, event.y, self._x1, self.height-self._y1,
                           event=event)
        del self._x1
        del self._y1
        del self._P1
        del self._P2
        del self._P3
        del self._P4
        if self.viewer and len(pick.hits):
            self.viewer.processPicking(pick)

        #print "len(pick.hits)", len(pick.hits)


    def SelectCamera(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """First pick in a non current camera selects it"""

        curCam = self.viewer.currentCamera
        if curCam == self: return 0
        curCam.frame.config( background = self.defFrameBack )
        self.frame.config( background = "#900000" )
        if self.viewer:
            self.viewer.currentCamera = self
            self.viewer.BindTrackballToObject(self.viewer.currentObject)

        self.SetupProjectionMatrix()
        return 1


    def DoubleSelectPick_cb(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Handle a double pick event in this camera"""

        self.DoPick(event.x, event.y, event=event)
        self.viewer.BindTrackballToObject(self.viewer.rootObject)

    ## DEPRECATED, is not using instance for computing coordinates
    def CenterPick_cb(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Handle a pick event. Center the cur. object on the picked vertex"""

        from warnings import warn
        warnings.warn('CenterPick_cbg is deprecated',
                      DeprecationWarning, stacklevel=2)

        pick = self.DoPick(event.x, event.y, event=event)
        if len(pick.hits)==0: return
        
        g = Numeric.zeros( (3), 'f' )
        object = self.viewer.currentObject
        inv = object.GetMatrixInverse()
        for obj, vertInd in pick.hits.items():
            if len(vertInd)==0:
                print 'WARNING: object',obj.name,' is not vertex pickable'
            else:
                m = Numeric.dot( inv, obj.GetMatrix() )
                vert = obj.vertexSet.vertices * m
                vertsel = Numeric.take( vert, vertInd )
                g = g + Numeric.sum(vertsel)/len(vertsel)

        object.SetPivot( g )

##                varray = obj.vertexSet.vertices.array
##                vert = Numeric.take( varray, vertInd )
##                vert = Numeric.concatenate( vert, Numeric.ones( (1,len(vert))), 1)
##                vert = Numeric.dot(m, vert)
##                obj.SetPivot( (Numeric.sum(vert)/len(vert))[:3] )
##                 obj.SetPivot( self.viewer.lastPickedVertex[1] )


    def TransfCamera_cb(self, event):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        self.viewer.BindTrackballToCamera(self.viewer.currentCamera)


    def ActivateClipPlanes(self, cplist, cpside):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """activate a list of clipping planes"""

        if len(cplist)==0: return
        glPushMatrix()
        glLoadIdentity()
        glMultMatrixf(self.rootObjectTransformation)

        glPushAttrib(GL_CURRENT_BIT | GL_LIGHTING_BIT |
                        GL_LINE_BIT)

        glDisable (GL_LIGHTING)
        for c in cplist:         # display them
            if c.visible: 
                # if we push a name here we won't know how many values
                # to skip in handlePick after z1 and z2
                #if self.renderMode == GL_SELECT:
                #    c.pickNum = self.pickNum
                #    self.objPick.append(c)
                #    self.pickNum = self.pickNum + 1
                #    glLoadName(c.pickNum)
                c.DisplayFunction()

        glPopAttrib()

        for c in cplist:         # enable them 
            c._Enable(cpside[c.num])

        glPopMatrix();


    def DrawAllDirectionalLights(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Draw all directional lights"""

        glDisable (GL_LIGHTING)
        for l in self.viewer.lights:
            if l.positional is True or l.visible in (False,0):
                continue
            if self.renderMode == GL_SELECT:
                l.pickNum = self.pickNum
                self.objPick.append(l)
                self.pickNum = self.pickNum + 1
                glLoadName(l.pickNum)
            l.DrawDirectionalLight(self)




    def drawWithCap(self, obj):
        MY_CLIP_PLANE = obj.cap
        # compute clip plane number
        cpn = MY_CLIP_PLANE - GL.GL_CLIP_PLANE0
        #GL.glPushAttrib(GL.GL_ENABLE_BIT | GL.GL_STENCIL_BUFFER_BIT |
        #                GL.GL_POLYGON_BIT | GL_CURRENT_BIT)
        
        ##
        ## SINGLE PASS
        ##
##         GL.glDepthMask(0)
##         GL.glColorMask(0,0,0,0)
##         GL.glDisable(GL_CULL_FACE)
##         GL.glEnable(GL.GL_STENCIL_TEST)
##         GL.glEnable(GL.GL_STENCIL_TEST_TWO_SIDE_EXT)

##         GL.glActiveStencilFaceEXT(GL.GL_BACK)
##         GL.glStencilOp(GL.GL_KEEP,            # stencil test fail
##                     GL.GL_KEEP,            # depth test fail
##                     GL.GL_DECR_WRAP_EXT)  # depth test pass
##         GL.glStencilMask(~0)
##         GL.glStencilFunc(GL_ALWAYS, 0, ~0)

##         GL.glActiveStencilFaceEXT(GL.GL_FRONT)
##         GL.glStencilOp(GL.GL.GL_KEEP,            # stencil test fail
##                     GL.GL.GL_KEEP,            # depth test fail
##                     GL.GL.GL_INCR_WRAP_EXT);  # depth test pass
##         GL.glStencilMask(~0)
##         GL.glStencilFunc(GL.GL_ALWAYS, 0, ~0)
##         obj.Draw()

        ## 2 passes version
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_STENCIL_TEST)
        glStencilMask(1)
        GL.glEnable(GL.GL_DEPTH_TEST)
        #GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
        GL.glColorMask(GL.GL_FALSE, GL.GL_FALSE, GL.GL_FALSE, GL.GL_FALSE)

        # first pass: increment stencil buffer value on back faces
        GL.glStencilFunc(GL.GL_ALWAYS, 0, 0)
        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_INCR)
        GL.glPolygonMode(GL.GL_BACK, GL.GL_FILL)
        GL.glCullFace(GL.GL_FRONT) # render back faces only
        obj.Draw()

        # second pass: decrement stencil buffer value on front faces
        GL.glStencilOp(GL.GL_KEEP, GL.GL_KEEP, GL.GL_DECR)
        GL.glPolygonMode(GL.GL_FRONT, GL.GL_FILL)
        GL.glCullFace(GL.GL_BACK) # render front faces only
        obj.Draw()

        # FIXME this can create problems whent there are multiple geoms
        GL.glClear(GL_DEPTH_BUFFER_BIT)

        # drawing clip planes masked by stencil buffer content
        #_gllib.glBindTexture(GL_TEXTURE_2D, 0)      
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
        GL.glDisable(MY_CLIP_PLANE)
        GL.glDisable(GL.GL_CULL_FACE)
        #GL.glStencilFunc(GL.GL_ALWAYS, 0, 1)
        #GL.glStencilFunc(GL.GL_LESS, 0, 1)
        #GL.glStencilFunc(GL.GL_NOTEQUAL, 0, 1)
        GL.glStencilFunc(GL.GL_NOTEQUAL, 0, 1)
        GL.glMaterialfv( GL.GL_FRONT, GL.GL_DIFFUSE, obj.capFrontColor)
        GL.glMaterialfv( GL.GL_BACK, GL.GL_DIFFUSE, obj.capBackColor)
        GL.glBegin(GL.GL_QUADS) #rendering the plane quad. Note, it should be 
                                #big enough to cover all clip edge area.
        GL.glNormal3fv( (1, 0, 0))

        if obj.clipSide[cpn]==-1:
            pts = [(0,  9999, -9999), (0,  9999,  9999),
                   (0, -9999,  9999), (0, -9999, -9999) ]
        else:
            pts = [ (0, -9999, -9999), (0, -9999,  9999),
                    (0,  9999,  9999), (0,  9999, -9999) ]
            
        cp = self.viewer.clipP[cpn]
        xpts = self.transformPoints(cp.translation, cp.rotation, pts)
        #GL.glDrawBuffer(GL.GL_FRONT)
        for p in xpts:
            GL.glVertex3fv( p )
        GL.glEnd()

        #****** Rendering object ********* 

        #GL.glPopAttrib()
        GL.glDisable(GL.GL_STENCIL_TEST)
        GL.glClear(GL_STENCIL_BUFFER_BIT)

        GL.glEnable(MY_CLIP_PLANE) # enabling clip plane again

        obj.SetupGL()
        obj.Draw()
        GL.glStencilFunc(GL.GL_ALWAYS, 0, 0)
        glStencilMask(0)


    def transformPoints(self, trans, rot, points):
        tx,ty,tz = trans
        pos = []
        for xs,ys,zs in points:
            x = rot[0]*xs + rot[4]*ys + rot[8]*zs + tx
            y = rot[1]*xs + rot[5]*ys + rot[9]*zs + ty
            z = rot[2]*xs + rot[6]*ys + rot[10]*zs + tz
            pos.append( [x,y,z] )
        return pos


    def DrawOneObject(self, obj):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """set up clipping planes, activate scissors and call display function
for all instances of obj
"""
        #print "Camera.DrawOneObject", obj
        
        lIsInstancetransformable = isinstance(obj, Transformable)
        
        if lIsInstancetransformable:

                self.ActivateClipPlanes( obj.clipP, obj.clipSide )
        
                if obj.scissor:
                    glDisable(GL_LIGHTING)
                    lViewport = glGetIntegerv(GL_VIEWPORT)
                    GL.glMatrixMode(GL.GL_PROJECTION)
                    GL.glPushMatrix()
                    GL.glLoadIdentity()
                    GL.glOrtho(float(lViewport[0]),
                               float(lViewport[2]),
                               float(lViewport[1]),
                               float(lViewport[3]),
                               -1, 1)
                    GL.glMatrixMode(GL.GL_MODELVIEW)
                    GL.glPushMatrix()
                    GL.glLoadIdentity()
                    glEnable(GL_COLOR_LOGIC_OP)
                    glLogicOp(GL_XOR)            
                    glBegin(GL_LINE_STRIP)
                    glVertex2f( float(obj.scissorX), float(obj.scissorY ))
                    glVertex2f( float(obj.scissorX+obj.scissorW), float(obj.scissorY ))
                    glVertex2f( float(obj.scissorX+obj.scissorW), float(obj.scissorY+obj.scissorH))
                    glVertex2f( float(obj.scissorX), float(obj.scissorY+obj.scissorH ))
                    glVertex2f( float(obj.scissorX), float(obj.scissorY ))
                    glEnd()
                    glDisable(GL_COLOR_LOGIC_OP)
                    GL.glMatrixMode(GL.GL_PROJECTION)
                    GL.glPopMatrix()
                    GL.glMatrixMode(GL.GL_MODELVIEW)
                    GL.glPopMatrix()
                    glEnable(GL_SCISSOR_TEST)
                    glScissor(obj.scissorX, obj.scissorY, obj.scissorW, obj.scissorH)
                    #glEnable(GL_LIGHTING)
                    if self.viewer is not None:
                        self.viewer.enableOpenglLighting()
                    
                if obj.drawBB: obj.DrawBoundingBox()

        # hack to fix this inheritence problem without slowing down
        # the "many object case (see Expensive inheritence pb above)

        # MS oct 11 2001. removed this code since obj.shadModel is set to
        # the proper value when it is inherited (see RenderMode()) and
        # shading is called by SetupGL for each object
        #if not obj.inheritShading and \
        #   obj.shading != GL_NONE:
        #    glShadeModel(obj.shading)

        if (lIsInstancetransformable and obj.drawBB != viewerConst.ONLY) \
           or isinstance(obj, Insert2d):
            if lIsInstancetransformable and obj.texture:
                glActiveTexture(GL_TEXTURE0)
                _gllib.glBindTexture(GL_TEXTURE_2D, 0)
                obj.texture.Setup()

            if lIsInstancetransformable and obj.invertNormals is True \
              and isinstance(obj, Ellipsoids) is False \
              and isinstance(obj, Cylinders) is False \
              and (isinstance(obj, Spheres) is True and DejaVu.enableVertexArray is True):
                lCwIsOn = True
                GL.glFrontFace(GL.GL_CW)
                #print "GL.glGetIntegerv(GL.GL_FRONT_FACE)",GL.glGetIntegerv(GL.GL_FRONT_FACE)
            else:
                lCwIsOn = False

            mi = 0
            for m in obj.instanceMatricesFortran:
                if lIsInstancetransformable and not obj.inheritMaterial:
                    obj.InitMaterial(mi)
                    obj.InitColor(mi)
                    mi = mi + 1
                glPushMatrix()
                glMultMatrixf(m)
                if obj.immediateRendering or \
                   (self.viewer.tileRender and obj.needsRedoDpyListOnResize):
                    if hasattr(obj, "cap") and obj.cap:
                        self.drawWithCap(obj)
                    else:
                        obj.Draw()
                    #obj.Draw()
                elif self.viewer.singleDpyList:
                    obj.Draw()
                else:
                    obj.DisplayFunction()
                glPopMatrix()

            if lCwIsOn is True:
                GL.glFrontFace(GL.GL_CCW)
                
            #print obj.name, self.glError()
            if lIsInstancetransformable and obj.texture:
                glActiveTexture(GL_TEXTURE0);
                _gllib.glBindTexture(GL_TEXTURE_2D, 0)
                glDisable(obj.texture.dim)

        if lIsInstancetransformable:
            for c in obj.clipP: # disable object's clip planes
                c._Disable()
        
            if obj.scissor:
                glDisable(GL_SCISSOR_TEST)


    def Draw(self, obj, pushAttrib=True):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Draw obj and subtree below it
"""
        #print "Camera.Draw", obj

        assert obj.viewer is not None

        # if object is not visible, all subtree is hidden --> we can return
        if obj.getVisible() in [False, 0]: #not obj.visible:
            return

        if self.drawMode & 5: # immediateRendring draw mode
            if obj.immediateRendering:
                pass
            elif (self.viewer.tileRender and obj.needsRedoDpyListOnResize):
                pass
            else:
                return

        glPushMatrix()                        # Protect our matrix

        lIsInstanceTransformable = isinstance(obj, Transformable)
        if lIsInstanceTransformable: 
            if not obj.inheritXform:
                glPushMatrix()
                glLoadIdentity()
                glMultMatrixf(self.beforeRootTransformation)
            
            obj.MakeMat()

# VERY expensive and I am not sure what I need it for
        if pushAttrib:
            glPushAttrib(GL_CURRENT_BIT | GL_LIGHTING_BIT
                         | GL_POLYGON_BIT)
            glDisable(GL_LIGHTING)

# required for the transparent box of AutoGrid not to affect the molecule's
# color binding. The box is FLAT shaded and this shade models gets propagated
# to the molecule preventing color interpolation over bonds.
# This shows that thi models of inheritence has serious limitations :(
#        gl.glPushAttrib(GL_LIGHTING_BIT)

        if lIsInstanceTransformable:
            obj.SetupGL() # setup GL properties the can be inherited

            # enable and display object's clipping planes that also
            # clip its children
            self.ActivateClipPlanes( obj.clipPI, obj.clipSide )

            if obj.scissor:
                glEnable(GL_SCISSOR_TEST)
                glScissor(obj.scissorX, obj.scissorY, obj.scissorW, obj.scissorH)

        if self.drawMode == 2:
            # recusive call for children
            # for o in obj.children: self.Draw(o)
            mi = 0
            for m in obj.instanceMatricesFortran:
                if lIsInstanceTransformable and not obj.inheritMaterial:
                    obj.InitMaterial(mi)
                    obj.InitColor(mi)
                    mi = mi + 1
                glPushMatrix()
                glMultMatrixf(m)
                map ( self.Draw, obj.children)
                glPopMatrix()

        # Should be done in a function to setup GL properties that cannot
        # be inherited
        # should actually only be done once since all transparent objects
        # have to be drawn after all opaque objects for this to work
        draw = 1
        transp = obj.transparent #obj.isTransparent()
        if obj.immediateRendering or \
           (self.viewer.tileRender and obj.needsRedoDpyListOnResize):
            if transp:
                if not self.drawMode & 4: # only render if immediate & transp
                    draw = 0
            else:
                if not self.drawMode & 1: # only render if immediate & opaque
                    draw = 0
##                 if draw==1:
##                     print 'drawing immediate opaque object'

        if draw and obj.visible:
            if transp:
                if self.drawTransparentObjects:
                    glEnable(GL_BLEND)
                    if not obj.getDepthMask():
                        glDepthMask(GL_FALSE)
                    glBlendFunc(obj.srcBlendFunc, obj.dstBlendFunc)

                    self.DrawOneObject(obj)
                
                    glDisable(GL_BLEND)
                    glDepthMask(GL_TRUE)
                else:
                    self.hasTransparentObjects = 1
            else: # was: elif not self.drawTransparentObjects:
                self.DrawOneObject(obj)

# VERY Expensif
        if pushAttrib:
            glPopAttrib()

        if lIsInstanceTransformable:
            for c in obj.clipPI: # disable object's clip planes that are
                c._Disable()   # inherited by children

            if obj.scissor:
                glDisable(GL_SCISSOR_TEST)

            if not obj.inheritXform:
                glPopMatrix()

        glPopMatrix()                        # Restore the matrix


    def RedrawObjectHierarchy(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        
        glPushMatrix()
        
        # setup GL state for root object
        obj = self.viewer.rootObject
        
        if self.drawBB: obj.DrawTreeBoundingBox()
        if self.drawBB != viewerConst.ONLY:

            # save the transformation before the root object
            # used by some object who do not want to inherit transform
            m = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')
            self.beforeRootTransformation = Numeric.reshape( m, (16,) )

            obj.MakeMat()               # root object transformation
            # mod_opengltk
            #m = glGetDoublev(GL_MODELVIEW_MATRIX).astype('f')
            m = Numeric.array(glGetDoublev(GL_MODELVIEW_MATRIX)).astype('f')

            self.rootObjectTransformation = Numeric.reshape( m, (16,) )
# no reason to push and pop attribute of root object 
#            glPushAttrib(GL_CURRENT_BIT | GL_LIGHTING_BIT |
#                         GL_POLYGON_BIT)

            #obj.InitColor()       # init GL for color with ROOT color
            #obj.InitMaterial()    # init GL for material with ROOT material
            obj.SetupGL()         # setup GL with ROOT properties

            if len(obj.clipPI):
                self.ActivateClipPlanes( obj.clipPI, obj.clipSide )

            # draw all object that do not want a display List
            #print "self.viewer.noDpyListOpaque", self.viewer.noDpyListOpaque
            if len(self.viewer.noDpyListOpaque):
                self.drawMode = 1 # no dispaly list Opaque
                for m in obj.instanceMatricesFortran:
                    glPushMatrix()
                    glMultMatrixf(m)
                    #map( self.Draw, obj.children)
                    map( self.Draw, self.viewer.noDpyListOpaque )
                    glPopMatrix()

            # for "Continuity" (ucsd - nbcr) as we don't have vertexArrays yet
            if hasattr(self, 'vertexArrayCallback'):
                self.vertexArrayCallback()

            # when redraw is triggered by pick event self.viewer has been set
            # to None
            if self.dpyList and self.viewer.useMasterDpyList:
                #print 'calling master list'
                currentcontext = self.tk.call(self._w, 'contexttag')
                if currentcontext != self.dpyList[1]:
                    warnings.warn("""RedrawObjectHierarchy failed because the current context is the wrong one""")
                    #print "currentcontext != self.viewer.dpyList[1]", currentcontext, self.viewer.dpyList[1]
                else:
                    #print '#%d'%self.dpyList[0], currentcontext, "glCallList Camera2"
                    glCallList(self.dpyList[0])

            else:
                #print 'rebuilding master list'
                if self.viewer.useMasterDpyList:
                    lNewList = glGenLists(1)
                    #lNewList = self.newList
                    lContext = self.tk.call(
                                               self._w,
                                               'contexttag' )
                    #print "lNewList StandardCamera.RedrawObjectHierarchy", lNewList, lContext, self.name
                    self.dpyList = ( 
                          lNewList,
                          lContext
                         )

                    glNewList(self.dpyList[0], GL_COMPILE)
                    #print '+%d'%self.dpyList[0], lContext, "glNewList Camera"

                # call for each subtree with root in obj.children
                # for o in obj.children: self.Draw(o)
                self.drawMode = 2
                self.drawTransparentObjects = 0
                self.hasTransparentObjects = 0
                for m in obj.instanceMatricesFortran:
                    glPushMatrix()
                    glMultMatrixf(m)
                    map( self.Draw, obj.children)
                    glPopMatrix()
                    
                if self.hasTransparentObjects:
                    self.drawTransparentObjects = 1
                    for m in obj.instanceMatricesFortran:
                        glPushMatrix()
                        glMultMatrixf(m)
                        map( self.Draw, obj.children)
                        glPopMatrix()

                if self.viewer.useMasterDpyList:
                    #print '*%d'%GL.glGetIntegerv(GL.GL_LIST_INDEX), "glEndList Camera"
                    glEndList()

                    #print "self.viewer.dpyList", self.viewer.dpyList
                    if self.dpyList:
                        currentcontext = self.tk.call(self._w, 'contexttag')
                        if currentcontext != self.dpyList[1]:
                            warnings.warn("""RedrawObjectHierarchy failed because the current context is the wrong one""")
                            #print "currentcontext != self.viewer.dpyList[1]", currentcontext, self.viewer.dpyList[1]
                        else:
                            #print '#%d'%self.dpyList[0], currentcontext, "glCallList Camera3"
                            glCallList(self.dpyList[0])

            # draw all object that do not want a display List
            #print "self.viewer.noDpyListTransp", self.viewer.noDpyListTransp
            if len(self.viewer.noDpyListTransp):
                self.drawTransparentObjects = 1
                self.drawMode = 4
                for m in obj.instanceMatricesFortran:
                    glPushMatrix()
                    glMultMatrixf(m)
                    #map( self.Draw, obj.children)
                    map( self.Draw, self.viewer.noDpyListTransp )
                    glPopMatrix()
                self.drawTransparentObjects = 0

##            glPopAttrib()
            for c in obj.clipPI:
                c._Disable()

        glPopMatrix()


    def _RedrawCamera(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Actual drawing of lights, clipping planes and objects
"""
        if self.stereoMode.startswith('SIDE_BY_SIDE'):
            if self.viewer.tileRender:
                glPushMatrix()
                # setup GL state for camera
                self.BuildTransformation()  # camera transformation
                self.SetupLights() 
                self.DrawAllDirectionalLights()
                if self.imageRendered == 'RIGHT_EYE':
                    glTranslatef( float(-self.sideBySideTranslation), 0, 0 )
                    glRotatef( float(-self.sideBySideRotAngle), 0., 1., 0.)
                elif self.imageRendered == 'LEFT_EYE':
                    glTranslatef( float(self.sideBySideTranslation), 0, 0 )
                    glRotatef( float(self.sideBySideRotAngle), 0., 1., 0.)
                else:
                    assert False, 'self.imageRendered is not set correctly'
                glViewport(0, 0, int(self.width), int(self.height))
                glScalef( 1., 0.5, 1.)
                self.RedrawObjectHierarchy()
                glPopMatrix()

            elif self.stereoMode.endswith('_CROSS'):
                halfWidth = self.width/2
                
                # setup GL state for camera
                glPushMatrix()
                self.BuildTransformation()  # camera transformation
                self.SetupLights()  # set GL lights; moved from Light object to here
                self.DrawAllDirectionalLights()
                
                # render image for right eye
                self.imageRendered = 'RIGHT_EYE'
                glPushMatrix()
                glTranslatef( float(-self.sideBySideTranslation), 0, 0 )
                glRotatef( float(-self.sideBySideRotAngle), 0., 1., 0.)
                glViewport(0, 0, int(halfWidth), int(self.height) )
                glScalef( 1., 0.5, 1.)
                self.RedrawObjectHierarchy()
                glPopMatrix()

                # render image for left eye
                self.imageRendered = 'LEFT_EYE'
                glPushMatrix()
                glTranslatef( float(self.sideBySideTranslation), 0, 0 )
                glRotatef( float(self.sideBySideRotAngle), 0., 1., 0.)
                glScalef( 1., 0.5, 1.)
                glViewport(int(halfWidth), 0, int(halfWidth), int(self.height)) 
                self.RedrawObjectHierarchy()
                glPopMatrix()

                glPopMatrix()
                glViewport(0, 0, int(self.width), int(self.height))
            elif self.stereoMode.endswith('_STRAIGHT'):
                halfWidth = self.width/2

                # setup GL state for camera
                glPushMatrix()
                self.BuildTransformation()  # camera transformation
                self.SetupLights()  # set GL lights; moved from Light object to here
                self.DrawAllDirectionalLights()

                # render image for left eye
                self.imageRendered = 'LEFT_EYE'
                glPushMatrix()
                glTranslatef( float(self.sideBySideTranslation), 0, 0 )
                glRotatef( float(self.sideBySideRotAngle), 0., 1., 0.)
                glScalef( 1., 0.5, 1.)
                glViewport(0, 0, halfWidth, self.height) 
                self.RedrawObjectHierarchy()
                glPopMatrix()

                # render image for right eye
                self.imageRendered = 'RIGHT_EYE'
                glPushMatrix()
                glTranslatef( float(-self.sideBySideTranslation), 0, 0 )
                glRotatef( float(-self.sideBySideRotAngle), 0., 1., 0.)
                glViewport(int(halfWidth), 0, int(halfWidth), int(self.height))
                glScalef( 1., 0.5, 1.)
                self.RedrawObjectHierarchy()
                glPopMatrix()

                glPopMatrix()
                glViewport(0, 0, self.width, self.height)

        elif self.stereoMode.startswith('COLOR_SEPARATION'):
            if self.stereoMode.endswith('_RED_BLUE'):
                left = (GL_TRUE, GL_FALSE, GL_FALSE)
                right = (GL_FALSE, GL_FALSE, GL_TRUE)
            elif self.stereoMode.endswith('_BLUE_RED'):
                left = (GL_FALSE, GL_FALSE, GL_TRUE)
                right = (GL_TRUE, GL_FALSE, GL_FALSE)
            elif self.stereoMode.endswith('_RED_GREEN'):
                left = (GL_TRUE, GL_FALSE, GL_FALSE)
                right = (GL_FALSE, GL_TRUE, GL_FALSE)
            elif self.stereoMode.endswith('_GREEN_RED'):
                left = (GL_FALSE, GL_TRUE, GL_FALSE)
                right = (GL_TRUE, GL_FALSE, GL_FALSE)
            elif self.stereoMode.endswith('_RED_GREENBLUE'):
                left = (GL_TRUE, GL_FALSE, GL_FALSE)
                right = (GL_FALSE, GL_TRUE, GL_TRUE)
            elif self.stereoMode.endswith('_GREENBLUE_RED'):
                left = (GL_FALSE, GL_TRUE, GL_TRUE)
                right = (GL_TRUE, GL_FALSE, GL_FALSE)
            elif self.stereoMode.endswith('_REDGREEN_BLUE'):
                left = (GL_TRUE, GL_TRUE, GL_FALSE)
                right = (GL_FALSE, GL_FALSE, GL_TRUE)
            elif self.stereoMode.endswith('_BLUE_REDGREEN'):
                left = (GL_FALSE, GL_FALSE, GL_TRUE)
                right = (GL_TRUE, GL_TRUE, GL_FALSE)

            glPushMatrix()
            # setup GL state for camera
            self.BuildTransformation()  # camera transformation
            self.SetupLights()  # set GL lights; moved from Light object to here
            self.DrawAllDirectionalLights()

            # render image for left eye
            self.imageRendered = 'MONO' #'LEFT_EYE'
            glPushMatrix()
            glTranslatef( float(self.sideBySideTranslation), 0, 0 )
            glRotatef( float(self.sideBySideRotAngle), 0., 1., 0.)
            glViewport(0, 0, int(self.width), int(self.height)) 
            glColorMask(int(left[0]), int(left[1]), int(left[2]), GL_FALSE)
            self.RedrawObjectHierarchy()
            glPopMatrix()
            self.drawHighlight()
            glClear(GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

            # render image for right eye
            self.imageRendered = 'RIGHT_EYE'
            glPushMatrix()
            glTranslatef( float(-self.sideBySideTranslation), 0, 0 )
            glRotatef( float(-self.sideBySideRotAngle), 0., 1., 0.)
            glViewport(0, 0, int(self.width), int(self.height))
            glColorMask(int(right[0]),int(right[1]),int(right[2]), GL_FALSE)
            self.RedrawObjectHierarchy()
            glPopMatrix()
            self.drawHighlight()

            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
            glPopMatrix()

        elif self.stereoMode == 'STEREO_BUFFERS':
            glPushMatrix()
            # setup GL state for camera
            self.BuildTransformation()  # camera transformation
            self.SetupLights()  # set GL lights; moved from Light object to here
            self.DrawAllDirectionalLights()

            # render image for left eye
            self.imageRendered = 'LEFT_EYE'
            glPushMatrix()
            glTranslatef( float(self.sideBySideTranslation), 0, 0 )
            glRotatef( float(self.sideBySideRotAngle), 0., 1., 0.)
            glViewport(0, 0, int(self.width), int(self.height)) 
            self.RedrawObjectHierarchy()
            glPopMatrix()
            self.drawHighlight()

            # render image for right eye
            self.imageRendered = 'RIGHT_EYE'
            glDrawBuffer(GL_BACK_RIGHT)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT |
                    GL_STENCIL_BUFFER_BIT)
            glPushMatrix()
            glTranslatef( float(-self.sideBySideTranslation), 0, 0 )
            glRotatef( float(-self.sideBySideRotAngle), 0., 1., 0.)
            glViewport(0, 0, int(self.width), int(self.height)) 
            self.RedrawObjectHierarchy()
            glPopMatrix()
            self.drawHighlight()

            glPopMatrix()
            glDrawBuffer(GL_BACK_LEFT)

        else: # default to "Mono mode"
            self.imageRendered = 'MONO'
            glPushMatrix()
            # setup GL state for camera
            self.BuildTransformation()  # camera transformation
            self.SetupLights() 
            self.DrawAllDirectionalLights()
            glViewport(0, 0, int(self.width), int(self.height))
            self.RedrawObjectHierarchy()
            glPopMatrix()


#    def secondDerivative(self, im, width, height):
#        return im.filter(sndDerivK)

    def firstDerivative(self, im, width, height):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        fstDeriveV1K = ImageFilter.Kernel( (3,3), fstDeriveV1, self.d1scale)
        c = im.filter(fstDeriveV1K)

        fstDeriveV2K = ImageFilter.Kernel( (3,3), fstDeriveV2, self.d1scale)
        d = im.filter(fstDeriveV2K)

        fstDeriveH1K = ImageFilter.Kernel( (3,3), fstDeriveH1, self.d1scale)
        e = im.filter(fstDeriveH1K)

        fstDeriveH2K = ImageFilter.Kernel( (3,3), fstDeriveH2, self.d1scale)
        f = im.filter(fstDeriveH2K)

        result1 = ImageChops.add(c, d, 2.)
        result2 = ImageChops.add(e, f, 2.)
        result = ImageChops.add(result1, result2, 2.)
        return result

        ## alternative adding numeric arrays seems slower
##         t1 = time()
##         c = im.filter(fstDeriveV1K)
##         c = Numeric.fromstring(c.tostring(), Numeric.UInt8)

##         d = im.filter(fstDeriveV2K)
##         d = Numeric.fromstring(d.tostring(), Numeric.UInt8)

##         e = im.filter(fstDeriveH1K)
##         e = Numeric.fromstring(e.tostring(), Numeric.UInt8)

##         f = im.filter(fstDeriveH2K)
##         f = Numeric.fromstring(f.tostring(), Numeric.UInt8)
        
##         result = Numeric.fabs(c) + Numeric.fabs(d) +\
##                  Numeric.fabs(e) + Numeric.fabs(f)
##         result.shape = im.size
##         result = Numeric.array( result )*0.25
##         return result
    
    
        
        
    
    def drawNPR(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        t1 = time()

        if self.viewer.tileRender is False:
            zbuf = self.GrabZBuffer(lock=False, flipTopBottom=False)
            #imageZbuf = Image.fromstring('L', (self.width, self.height), zbuf.tostring() )
            #imageZbuf.save("zbuf.png")
        else:
            zbuf = self.GrabZBuffer(lock=False, flipTopBottom=False,
                                    zmin=self.viewer.tileRenderCtx.zmin,
                                    zmax=self.viewer.tileRenderCtx.zmax
                                    )
            imageFinal = Image.new('L', (self.width+2, self.height+2) )

            #padding
            # the 4 corners
            imageFinal.putpixel((0, 0), zbuf.getpixel((0, 0)) )
            imageFinal.putpixel((0, self.height+1), zbuf.getpixel((0, self.height-1)) )
            imageFinal.putpixel((self.width+1, 0), zbuf.getpixel((self.width-1, 0)) )
            imageFinal.putpixel((self.width+1, self.height+1), zbuf.getpixel((self.width-1, self.height-1)) )

            # the top and bottom line
            for i in range(self.width):
                imageFinal.putpixel((i+1, 0), zbuf.getpixel((i, 0)) )
                imageFinal.putpixel((i+1, self.height+1), zbuf.getpixel((i, self.height-1)) )

            # the left and right columns
            for j in range(self.height):
                imageFinal.putpixel((0, j+1), zbuf.getpixel((0, j)) )
                imageFinal.putpixel((self.width+1, j+1), zbuf.getpixel((self.width-1, j)) )

            # the main picture
            imageFinal.paste( zbuf, (1 , 1) )
            zbuf = imageFinal

        d1strong = d2strong = None

        useFirstDerivative = self.d1scale!=0.0
        useSecondDerivative = self.d2scale!=0.0

        if useFirstDerivative:

            if self.viewer.tileRender:
                d1 = self.firstDerivative(zbuf, self.width+2, self.height+2)
                d1 = d1.crop((1,1,self.width+1,self.width+1))
            else:
                d1 = self.firstDerivative(zbuf, self.width, self.height)

            #d1.save('first.jpg')
            #d1strong = Numeric.fromstring(d1.tostring(),Numeric.UInt8)
            #print 'first', min(d1.ravel()), max(d1.ravel()), Numeric.sum(d1.ravel())
            #print self.d1cut, self.d1off
            d1 = Numeric.fromstring(d1.tostring(),Numeric.UInt8)
            #mini = min(d1)
            #maxi = max(d1)
            #print 'd1',mini, maxi
#            d1strong = Numeric.clip(d1, self.d1cutL, self.d1cutH)
#            d1strong = d1strong.astype('f')*self.d1off

            #print 'd1',min(d1strong), max(d1strong)
            #print 'first', d1strong.shape, min(d1strong.ravel()), max(d1strong.ravel()), Numeric.sum(d1strong.ravel())

            # LOOKUP ramp
            #print "self.d1ramp", len(self.d1ramp), self.d1ramp

            #d1strong = Numeric.choose(d1.astype('B'), self.d1ramp )
            d1strong = numpy.zeros(len(d1))
            for index, elt in enumerate(d1.astype('B')):
                 d1strong[index] = self.d1ramp[elt]

            #print 'firstramp', d1strong.shape, min(d1strong.ravel()), max(d1strong.ravel()), Numeric.sum(d1strong.ravel())

        if useSecondDerivative:
            #d2 = self.secondDerivative(zbuf, self.width, self.height)
            sndDerivK = ImageFilter.Kernel( (3,3), sndDeriv, self.d2scale)
            d2 = zbuf.filter(sndDerivK)

            if self.viewer.tileRender:
                d2 = d2.crop((1,1,self.width+1,self.width+1))            

            #d2.save('second.jpg')
            #print 'second1', min(d2.ravel()), max(d2.ravel()), Numeric.sum(d2.ravel())
            #print self.d2cut, self.d2off
            d2 = Numeric.fromstring(d2.tostring(),Numeric.UInt8)
            #mini = min(d2)
            #maxi = max(d2)
            #print 'd2',mini, maxi
            d2strong = Numeric.clip(d2, self.d2cutL, self.d2cutH)
            d2strong = d2strong.astype('f')*self.d2off
            #d2strong = Numeric.where(Numeric.greater(d2,self.d2cutL),
            #                         d2, 0)
            #d2strong = Numeric.where(Numeric.less(d2strong,self.d2cutH),
            #                         d2, 0)
            #d2strong += self.d2off
            #print 'd2',min(d2strong), max(d2strong)
            #print 'second2', d2strong.shape, min(d2strong.ravel()), max(d2strong.ravel()), Numeric.sum(d2strong.ravel())

        if useFirstDerivative and useSecondDerivative:
            self.outline = Numeric.maximum(d1strong, d2strong)
            #self.outline = (d1strong + d2strong)/2
            #self.outlineim = ImageChops.add(d1strong, d2strong)
        elif useFirstDerivative:
            self.outline = d1strong
        elif useSecondDerivative:
            self.outline = d2strong
        else:
            self.outline = None

        ## working OpenGL version
##         zbuf = self.GrabZBuffer(lock=False)
##         self.ivi.setImage(zbuf)

##         deriv = self.ivi.firstDerivative()
##         d1strong = Numeric.where(Numeric.greater(deriv,self.d1cut),
##                                  self.d1scale*(deriv+self.d1off), 0)

##         deriv2 = self.ivi.secondDerivative()
##         d2strong = Numeric.where(Numeric.greater(deriv2,self.d2cut),
##                                  self.d2scale*(deriv2+self.d2off), 0)
##         self.outline = Numeric.maximum(d1strong, d2strong)
##         self.tk.call(self._w, 'makecurrent')

        #print 'time NPR rendering', time()-t1
        return


    def displayNPR(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        t1 = time()
        if self.outline is None:
            return

        lViewport = glGetIntegerv(GL_VIEWPORT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(float(lViewport[0]),
                float(lViewport[0]+lViewport[2]),
                float(lViewport[1]),
                float(lViewport[1]+lViewport[3]),
                -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_DST_COLOR, GL_ZERO);  
        glRasterPos2f(0.0, 0.0)

        self.outline = Numeric.fabs(self.outline-255)
        self.outline = self.outline.astype('B')
#        glActiveTexture(GL_TEXTURE0);
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        _gllib.glDrawPixels(self.width, self.height, 
                            GL_LUMINANCE, GL_UNSIGNED_BYTE, 
                            self.outline )
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        #print 'time NPR display', time()-t1

        
    def RedrawAASwitch(self, *dummy):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """Redraw all the objects in the scene"""

        glStencilMask(1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT |
                GL_STENCIL_BUFFER_BIT)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        glStencilFunc ( GL_ALWAYS, 0, 1 ) ;
        glEnable ( GL_STENCIL_TEST ) ;

        if not self.viewer.accumBuffersError and \
            self.antiAliased and self.renderMode==GL_RENDER:
            dist = math.sqrt(Numeric.add.reduce(self.direction*self.direction))
            # jitter loop
            if self.antiAliased>0:
                sca = 1./self.antiAliased
                accumContour = None

            for i in range(self.antiAliased):
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                if self.projectionType == self.PERSPECTIVE:
                    if self.viewer.tileRender:
                        tr = self.viewer.tileRenderCtx
                        left = tr.tileleft
                        right = tr.tileright
                        bottom = tr.tilebottom
                        top = tr.tiletop
                    else:
                        left=right=top=bottom=None

                    self.AccPerspective (self.jitter[i][0], self.jitter[i][1],
                                      0.0, 0.0, dist, left, right, bottom, top)
                    self._RedrawCamera()
                else:
                    W = self.right-self.left # width in world coordinates
                    H = self.top-self.bottom # height in world coordinates
                    glPushMatrix()
                    glTranslatef (self.jitter[i][0]*W/self.width,
                                  self.jitter[i][1]*H/self.height,
                                  0.0)
                    self._RedrawCamera()
                    glPopMatrix()

                if i==0 and self.ssao :
                    self.copyDepth()

                # we accumulate the back buffer
                glReadBuffer(GL_BACK)
                if i==0:
                    glAccum(GL_LOAD, self.accumWeigth)
                else:
                    glAccum(GL_ACCUM, self.accumWeigth)
                    
                if self.contours and self._suspendNPR is False:
                    self.drawNPR()
                    if self.outline is not None:
                        if accumContour is None:
                            accumContour = self.outline.copy()
                            accumContour *= sca
                        else:
                            accumContour += sca*self.outline
            glAccum (GL_RETURN, 1.0)

            if self.contours and self._suspendNPR is False:
                self.outline = accumContour

        else: # plain drawing
            if self.ssao : self.copy_depth_ssao = True
            self._RedrawCamera()
    
        if self.contours and self._suspendNPR is False:
            self.drawNPR()


        if self.contours and self._suspendNPR is False:
            glViewport(0, 0, self.width, self.height)
            self.displayNPR()

        if    self.stereoMode.startswith('COLOR_SEPARATION') is False \
          and self.stereoMode != 'STEREO_BUFFERS':     
            self.drawHighlight()

        if self.ssao :
            self.drawSSAO()    

        glDisable(GL_STENCIL_TEST)            
        if self.drawThumbnailFlag:
            self.drawThumbnail()

        if self.swap:
            self.tk.call(self._w, 'swapbuffers')           


    def setShaderSelectionContour(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        #import pdb;pdb.set_trace()
        #if DejaVu.enableSelectionContour is True:
        #    if GL.glGetString(GL.GL_VENDOR).find('Intel') >= 0:
        #        DejaVu.enableSelectionContour = False
        #        print "intel (even gma) gpu drivers don't handle properly the stencil with FBO"

        if DejaVu.enableSelectionContour is True:
            try:
                ## do not try to import this before creating the opengl context, it would fail.
                from opengltk.extent import _glextlib
                DejaVu.enableSelectionContour = True
            except ImportError:
                DejaVu.enableSelectionContour = False
                print "could not import _glextlib"

        #import pdb;pdb.set_trace()
        if DejaVu.enableSelectionContour is True:
            extensionsList = glGetString(GL_EXTENSIONS)
            if extensionsList.find('GL_EXT_packed_depth_stencil') < 0:
                DejaVu.enableSelectionContour = False
                print "opengl extension GL_EXT_packed_depth_stencil is not present"

        if DejaVu.enableSelectionContour is True:
            f = _glextlib.glCreateShader(_glextlib.GL_FRAGMENT_SHADER)
    
            # This shader performs a 9-tap Laplacian edge detection filter. 
            # (converted from the separate "edges.cg" file to embedded GLSL string)    
            self.fragmentShaderCode = """
uniform float contourSize;
uniform vec4 contourColor;
uniform sampler2D texUnit;
void main(void)
{
    float lOffset = .001 * contourSize ; // (1./512.);
    vec2 texCoord = gl_TexCoord[0].xy;
    if (     ( texCoord [ 0 ] > lOffset ) // to suppress artifacts on frame buffer bounds
          && ( texCoord [ 1 ] > lOffset ) 
          && ( texCoord [ 0 ] < 1. - lOffset )
          && ( texCoord [ 1 ] < 1. - lOffset ) )
    {
        float c  = texture2D(texUnit, texCoord)[0];
        float bl = texture2D(texUnit, texCoord + vec2(-lOffset, -lOffset))[0];
        float l  = texture2D(texUnit, texCoord + vec2(-lOffset,     0.0))[0];
        float tl = texture2D(texUnit, texCoord + vec2(-lOffset,  lOffset))[0];
        float t  = texture2D(texUnit, texCoord + vec2(    0.0,  lOffset))[0];
        float tr = texture2D(texUnit, texCoord + vec2( lOffset,  lOffset))[0];
        float r  = texture2D(texUnit, texCoord + vec2( lOffset,     0.0))[0];
        float br = texture2D(texUnit, texCoord + vec2( lOffset,  lOffset))[0];
        float b  = texture2D(texUnit, texCoord + vec2(    0.0, -lOffset))[0];
        if ( 8. * (c + -.125 * (bl + l + tl + t + tr + r + br + b)) != 0. )
        {
           gl_FragColor = contourColor; //vec4(1., 0., 1., .7) ;
        }
        else
        {
            //due to bizarre ATI behavior
            gl_FragColor = vec4(1., 0., 0., 0.) ;
        }
    }
}
"""

            _glextlib.glShaderSource(f, 1, self.fragmentShaderCode, 0x7FFFFFFF)
            _glextlib.glCompileShader(f)
            lStatus = 0x7FFFFFFF
            lStatus = _glextlib.glGetShaderiv(f, _glextlib.GL_COMPILE_STATUS, lStatus )
            if lStatus == 0:
                print "compile status", lStatus
                charsWritten  = 0
                shaderInfoLog = '\0' * 2048
                charsWritten, infoLog = _glextlib.glGetShaderInfoLog(f, len(shaderInfoLog), 
                                                                     charsWritten, shaderInfoLog)
                print "shaderInfoLog", shaderInfoLog
                DejaVu.enableSelectionContour = False
                print "selection contour shader didn't compile"
            else:
                self.shaderProgram = _glextlib.glCreateProgram()
                _glextlib.glAttachShader(self.shaderProgram,f)
                _glextlib.glLinkProgram(self.shaderProgram)
                lStatus = 0x7FFFFFFF
                lStatus = _glextlib.glGetProgramiv(self.shaderProgram,
                                                   _glextlib.GL_LINK_STATUS,
                                                   lStatus )
                if lStatus == 0:
                    print "link status", lStatus
                    DejaVu.enableSelectionContour = False
                    print "selection contour shader didn't link"
                else:
                    _glextlib.glValidateProgram(self.shaderProgram)
                    lStatus = 0x7FFFFFFF
                    lStatus = _glextlib.glGetProgramiv(self.shaderProgram,
                                                       _glextlib.GL_VALIDATE_STATUS,
                                                       lStatus )
                    if lStatus == 0:
                        print "validate status", lStatus
                        DejaVu.enableSelectionContour = False
                        print "selection contour shader not validated"
                    else:
                        # Get location of the sampler uniform
                        self.texUnitLoc = int(_glextlib.glGetUniformLocation(self.shaderProgram, "texUnit"))
                        #print "selection contour shader successfully compiled and linked"

                        # Get location of the contourSize uniform
                        self.contourSizeLoc = int(_glextlib.glGetUniformLocation(self.shaderProgram, "contourSize"))

                        # Get location of the contourSize uniform
                        self.contourColorLoc = int(_glextlib.glGetUniformLocation(self.shaderProgram, "contourColor"))


                        ## create a framebuffer to receive the texture
                        self.fb = 0
                        self.fb = _glextlib.glGenFramebuffersEXT(1, self.fb)
                        #print "self.fb", self.fb
                        lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
                        if lCheckMessage != _glextlib.GL_FRAMEBUFFER_COMPLETE_EXT: # 0x8CD5
                            print 'glCheckFramebufferStatusEXT %x'%lCheckMessage
                            DejaVu.enableSelectionContour = False


    def drawHighlight(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
#        lStencil = numpy.zeros(self.width*self.height, dtype='uint32')
#        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
#        _gllib.glReadPixels( 0, 0, self.width, self.height,
#                             GL.GL_STENCIL_INDEX, GL.GL_UNSIGNED_INT,
#                             lStencil)
#        print "lStencil", lStencil[0] # background is 254 # fill is 255
#        lStencilImage = Image.fromstring('L', (self.width, self.height), 
#                                       lStencil.astype('uint8').tostring() )
#        lStencilImage.save("lStencil.png")
#        zbuf = self.GrabZBuffer(lock=False, flipTopBottom=False)
#        imageZbuf = Image.fromstring('L', (self.width, self.height), zbuf.tostring() )
#        imageZbuf.save("lZbuff.png")

        # to draw only the highlight zone from the stencil buffer
        GL.glEnable(GL.GL_STENCIL_TEST)
        glStencilMask(0)
        glStencilFunc(GL_EQUAL, 1, 1)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        lViewport = glGetIntegerv(GL_VIEWPORT)
        glOrtho(float(lViewport[0]),
                float(lViewport[0]+lViewport[2]),
                float(lViewport[1]),
                float(lViewport[1]+lViewport[3]),
                -1, 1)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
#        glActiveTexture(GL_TEXTURE0);
        ## here we apply the patterned highlight
        if DejaVu.selectionPatternSize >= 3:
            #glEnable(GL_COLOR_LOGIC_OP)
            #glLogicOp(GL_AND)
            glEnable(GL_TEXTURE_2D)
            _gllib.glBindTexture(GL_TEXTURE_2D, self.textureName)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glBegin(GL_POLYGON)
            glTexCoord2f(0., 0.)
            glVertex2i(0, 0)
            lTexWidth = float(self.width)/DejaVu.selectionPatternSize # determine how big the pattern will be 
            lTexHeight = float(self.height)/DejaVu.selectionPatternSize
            glTexCoord2f(lTexWidth, 0.)
            glVertex2i(self.width, 0)
            glTexCoord2f(lTexWidth, lTexHeight)
            glVertex2i(self.width, self.height)
            glTexCoord2f(0., lTexHeight)
            glVertex2i(0, self.height)
            glEnd()
            glDisable(GL_BLEND)
            glDisable(GL_TEXTURE_2D)
            #glDisable(GL_COLOR_LOGIC_OP)

        if    DejaVu.enableSelectionContour is True \
          and DejaVu.selectionContourSize != 0:
            from opengltk.extent import _glextlib
            #import pdb;pdb.set_trace()
            ## copying the current stencil to a texture
            _gllib.glBindTexture(GL_TEXTURE_2D, self.stencilTextureName )
            glCopyTexImage2D(GL_TEXTURE_2D, 0, _glextlib.GL_DEPTH_STENCIL_EXT, 0, 0,
                             self.width, self.height, 0)
            ## switch writting to the FBO (Frame Buffer Object)
            _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, self.fb )
            #lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
            #print 'glCheckFramebufferStatusEXT 0 %x'%lCheckMessage
            ## attaching the current stencil to the FBO (Frame Buffer Object)
            _glextlib.glFramebufferTexture2DEXT(_glextlib.GL_FRAMEBUFFER_EXT,
                                         _glextlib.GL_DEPTH_ATTACHMENT_EXT,
                                         GL_TEXTURE_2D, self.stencilTextureName,0)
            #lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
            #print 'glCheckFramebufferStatusEXT 1 %x'%lCheckMessage
            _glextlib.glFramebufferTexture2DEXT(_glextlib.GL_FRAMEBUFFER_EXT,
                                         _glextlib.GL_STENCIL_ATTACHMENT_EXT,
                                         GL_TEXTURE_2D, self.stencilTextureName, 0)
            #lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
            #print 'glCheckFramebufferStatusEXT 2 %x'%lCheckMessage
            ## attaching the texture to be written as FBO
            _gllib.glBindTexture(GL_TEXTURE_2D, self.contourTextureName )
            _gllib.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 
                                   0, GL_RGBA, GL.GL_FLOAT, 0 )
            _glextlib.glFramebufferTexture2DEXT(_glextlib.GL_FRAMEBUFFER_EXT,
                                                _glextlib.GL_COLOR_ATTACHMENT0_EXT,
                                                GL_TEXTURE_2D, self.contourTextureName, 0)
            #lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
            #print 'glCheckFramebufferStatusEXT 3 %x'%lCheckMessage

            ## verifying that everything gets attached to the FBO
            lCheckMessage = _glextlib.glCheckFramebufferStatusEXT(_glextlib.GL_FRAMEBUFFER_EXT)
            if lCheckMessage != _glextlib.GL_FRAMEBUFFER_COMPLETE_EXT: # 0x8CD5
                print 'glCheckFramebufferStatusEXT %x'%lCheckMessage
                DejaVu.enableSelectionContour = False
                _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, 0 )
                print 'opengl frame buffer object not available, selection contour is now disabled.'
                #print 'you may need to set enableSelectionContour to False in the following file:'
                #print '~/.mgltools/(version numer)/DejaVu/_dejavurc'
            else:
                ## writing the stencil to the texture / FBO 
                glClear(GL_COLOR_BUFFER_BIT)
                glBegin(GL_POLYGON)
                glVertex2i(0, 0)
                glVertex2i(self.width, 0)
                glVertex2i(self.width, self.height)
                glVertex2i(0, self.height)
                glEnd()

                ## switch writing to the regular frame buffer (normaly the back buffer)
                _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, 0 )
                
                ## here we obtain the contour of the stencil copied in the texture and draw it
                from opengltk.extent import _glextlib
                _glextlib.glUseProgram( self.shaderProgram )
                _glextlib.glUniform1i( self.texUnitLoc, 0)
                _glextlib.glUniform1f( self.contourSizeLoc, float(DejaVu.selectionContourSize))
                _glextlib.glUniform4f( self.contourColorLoc, 
                                       DejaVu.selectionContourColor[0],
                                       DejaVu.selectionContourColor[1],
                                       DejaVu.selectionContourColor[2],
                                       DejaVu.selectionContourColor[3]
                                     )                
                glEnable(GL_BLEND)
                glStencilFunc(GL_NOTEQUAL, 1, 1) #so the contour is drawn only outside of the highlighted area
                glBegin(GL_POLYGON)
                glTexCoord2i(0, 0)
                glVertex2i(0, 0)
                glTexCoord2i(1, 0)
                glVertex2i(self.width, 0)
                glTexCoord2i(1, 1)
                glVertex2i(self.width, self.height)
                glTexCoord2i(0, 1)
                glVertex2i(0, self.height)
                glEnd()
                glDisable(GL_BLEND)
            _glextlib.glUseProgram( 0 )

        # to protect our texture, we bind the default texture while we don't use it
        _gllib.glBindTexture(GL_TEXTURE_2D, 0)      
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glStencilMask(1)
        glStencilFunc ( GL_ALWAYS, 0, 1 )

#===============================================================================
#     SSAO Shader
#===============================================================================
    def setTextureSSAO(self):
        self.depthtextureName = int(glGenTextures(1)[0])
        glPrioritizeTextures(numpy.array([self.depthtextureName]),
                             numpy.array([1.]))
        _gllib.glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        #_gllib.glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self.width,
        #              self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None);
        #SSAO depthexture
        self.illumtextureName = int(glGenTextures(1)[0])
        glPrioritizeTextures(numpy.array([self.illumtextureName]),
                             numpy.array([1.]))
        _gllib.glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        #_gllib.glTexImage2D (GL_TEXTURE_2D, 0, GL_LUMINANCE, self.width,
        #              self.height, 0, GL_LUMINANCE, GL_UNSIGNED_INT, None);

        #SSAO depthexture
        self.rendertextureName = int(glGenTextures(1)[0])
        glPrioritizeTextures(numpy.array([self.rendertextureName]),
                             numpy.array([1.]))
        _gllib.glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        #_gllib.glTexImage2D (GL_TEXTURE_2D, 0, GL_RGB, self.width,
        #             self.height, 0, GL_RGB, GL_UNSIGNED_INT, None);
        #depth mask texture
        self.depthmasktextureName = int(glGenTextures(1)[0])
        glPrioritizeTextures(numpy.array([self.depthmasktextureName]),
                             numpy.array([1.]))
        _gllib.glBindTexture (GL_TEXTURE_2D, self.depthmasktextureName);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
        glTexParameteri (GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_LUMINANCE);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
        #_gllib.glTexImage2D (GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, self.width,
        #              self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None);
        #SSAO randomtexture
#
#        self.randomTexture = Texture()
#        import Image
#        img = Image.open(DejaVu.__path__[0]+os.sep+"textures"+os.sep+"random_normals.png")
#        self.randomTexture.Set(enable=1, image=img)
        self.randomtextureName = int(glGenTextures(1)[0])
        glPrioritizeTextures(numpy.array([self.randomtextureName]),
                             numpy.array([1.]))
#        _gllib.glBindTexture (GL_TEXTURE_2D, self.randomtextureName);       
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
#        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
#        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE )
#        _gllib.glTexImage2D (GL_TEXTURE_2D, 0, self.randomTexture.format, 
#                             self.randomTexture.width, self.randomTexture.height, 
#                             0, self.randomTexture.format, GL_UNSIGNED_INT, 
#                             self.randomTexture.image);       
        _gllib.glBindTexture (GL_TEXTURE_2D,0)
        
    def setShaderSSAO(self):
        if __debug__:
            if hasattr(DejaVu, 'functionName'): DejaVu.functionName()        
#        if not DejaVu.enableSSAO : #this is case there is no _glextlib
#            return
        try:
            ## do not try to import this before creating the opengl context, it would fail.
            from opengltk.extent import _glextlib
        except ImportError:
            DejaVu.enableSSAO = False
            print "could not import _glextlib, SSAO disable"  
        #import pdb;pdb.set_trace()
        if DejaVu.enableSSAO is True:
            vendor = glGetString(GL_VENDOR)
            render = glGetString(GL_RENDERER)
            extensionsList = glGetString(GL_EXTENSIONS)
            if extensionsList.find('GL_EXT_packed_depth_stencil') < 0:
                DejaVu.enableSSAO = False
                print "opengl extension not present, SSAO disable"
            if vendor.find("Mesa") !=-1 or vendor.find("MESA") != -1 :
                print "MESA Driver found, SSAO disable"
                DejaVu.enableSSAO = False
            if render.find("Mesa") !=-1 or render.find("MESA") != -1 :
                print "MESA Driver found, SSAO disable"
                DejaVu.enableSSAO = False          
        if DejaVu.enableSSAO is True:
            try :
                self.setTextureSSAO()
            except :
                DejaVu.enableSSAO = False
                print "opengl / texture problem,SSAO disable"
                self.ssao = False
                return
#            self.setDefaultSSAO_OPTIONS()
            f = _glextlib.glCreateShader(_glextlib.GL_FRAGMENT_SHADER)
            sfile = open(os.path.join(DejaVu.__path__[0], "shaders", "fragSSAO"))
            lines = sfile.readlines()
            sfile.close()
            self.fragmentSSAOShaderCode=""
            for l in lines :
                self.fragmentSSAOShaderCode+=l
            v = _glextlib.glCreateShader(_glextlib.GL_VERTEX_SHADER)
            sfile = open(os.path.join(DejaVu.__path__[0], "shaders", "vertSSAO"))
            lines = sfile.readlines()
            sfile.close()
            self.vertexSSAOShaderCode=""
            for l in lines :
                self.vertexSSAOShaderCode+=l
            lStatus = 0x7FFFFFFF
            _glextlib.glShaderSource(v, 1, self.vertexSSAOShaderCode, lStatus)
            _glextlib.glCompileShader(v)
            _glextlib.glShaderSource(f, 1, self.fragmentSSAOShaderCode, lStatus)
            _glextlib.glCompileShader(f)

            lStatus1 = _glextlib.glGetShaderiv(f, _glextlib.GL_COMPILE_STATUS, lStatus )
            #print "SSAO compile status frag: %s"%lStatus,
            lStatus2 = _glextlib.glGetShaderiv(v, _glextlib.GL_COMPILE_STATUS, lStatus )
            #print " vertex: %s"%lStatus
            if lStatus1 == 0 or lStatus2 == 0:
#                print "compile status", lStatus
                charsWritten  = 0
                shaderInfoLog = '\0' * 2048
                charsWritten, infoLog = _glextlib.glGetShaderInfoLog(f, len(shaderInfoLog), 
                                                                     charsWritten, shaderInfoLog)
                print "shaderInfoLog", shaderInfoLog
                DejaVu.enableSSAO = False
                print "SSAO shader didn't compile"
            else:
                self.shaderSSAOProgram = _glextlib.glCreateProgram()
                _glextlib.glAttachShader(self.shaderSSAOProgram,v)
                _glextlib.glAttachShader(self.shaderSSAOProgram,f)                
                _glextlib.glLinkProgram(self.shaderSSAOProgram)
                lStatus = 0x7FFFFFFF
                lStatus = _glextlib.glGetProgramiv(self.shaderSSAOProgram,
                                                   _glextlib.GL_LINK_STATUS,
                                                   lStatus )
                if lStatus == 0:
#                    print "link status", lStatus
                    log = ""
                    charsWritten  = 0
                    progInfoLog = '\0' * 2048
                    charsWritten, infoLog = _glextlib.glGetProgramInfoLog(self.shaderSSAOProgram, len(progInfoLog), 
                                                                     charsWritten, progInfoLog)
                    DejaVu.enableSSAO = False
                    print "SSAO shader didn't link"
                    print "log ",progInfoLog
    
                else:
                    _glextlib.glValidateProgram(self.shaderSSAOProgram)
                    lStatus = 0x7FFFFFFF
                    lStatus = _glextlib.glGetProgramiv(self.shaderSSAOProgram,
                                                       _glextlib.GL_VALIDATE_STATUS,
                                                       lStatus )
                    if lStatus == 0:
                        print "SSAO shader did not validate, status:", lStatus
                        DejaVu.enableSSAO = False
                        print "enableSSAO not validated"
                    else:
                        # Get location 
                        self.SSAO_LOCATIONS = {
                'RandomTexture': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'RandomTexture' ),
                'DepthTexture': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'DepthTexture' ),
                'RenderedTexture': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'RenderedTexture' ),
                'LuminanceTexture': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'LuminanceTexture' ),                
                'DepthMaskTexture': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'DepthMaskTexture' ),
                'RenderedTextureWidth': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'RenderedTextureWidth' ),
                'RenderedTextureHeight': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'RenderedTextureHeight' ),                
                'realfar': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'realfar' ),
                #'realnear': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'realnear' ),
#                'fogS': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'fogS' ),
#                'fogE': _glextlib.glGetUniformLocation( self.shaderSSAOProgram, 'fogE' ),
                    }
                        
                        for k in self.SSAO_OPTIONS :
                            self.SSAO_LOCATIONS[k] = _glextlib.glGetUniformLocation( self.shaderSSAOProgram, k )


    def setDefaultSSAO_OPTIONS(self):
        try :
            from opengltk.extent import _glextlib
	except :
            DejaVu.enableSSAO = False
            print "could not import _glextlib, SSAO disabled"  
	
        self.SSAO_OPTIONS={'far': [300.0,0.,1000.,"float"],
                'near': [self.near,0.,100.,"float"],
                'method':[self.ssao_method,0,1,"int"],
                'fix':[0,0,1,"int"],
                'do_noise':[0,0,1,"int"],
                'fog':[0,0,1,"int"],
                'use_fog':[1,0,1,"int"],
                'use_mask_depth':[self.use_mask_depth,0,1,"int"],
		'only_depth':[0,0,1,"int"],
		'mix_depth':[0,0,1,"int"],
                'only_ssao':[0,0,1,"int"],
                'show_mask_depth':[0,0,1,"int"],
                'scale':[1.0,1.0,100.0,"float"],
                'samples': [6,1,8,"int"],
                'rings': [6,1,8,"int"],
                'aoCap': [1.2,0.0,10.0,"float"],
                'aoMultiplier': [100.0,1.,500.,"float"],
                'depthTolerance': [0.0,0.0,1.0,"float"],
                'aorange':[60.0,1.0,500.0,"float"],
                'negative':[0,0,1,"int"],
		'correction':[6.0,0.0,1000.0,"float"],
                #'force_real_far':[0,0,1,"int"],
                }

        self.SSAO_OPTIONS["near"][0] = 2.0
        self.Set(near = 2.0)
        self.SSAO_OPTIONS_ORDER = [
            'use_fog','only_ssao','only_depth','mix_depth',
            'negative','do_noise','near','far','scale','rings',
            'samples','aoCap','aoMultiplier',
            'aorange','depthTolerance','correction','use_mask_depth','fix']


    def copyDepth(self):
        _gllib.glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
        glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self.width,
                         self.height, 0);        
        self.copy_depth_ssao = False


    def copyBuffer(self, depthmask=False):
        if depthmask :
            _gllib.glBindTexture (GL_TEXTURE_2D, self.depthmasktextureName);
            glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self.width,
                      self.height, 0);
            return 
        if self.copy_depth_ssao : 
            _gllib.glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
            glCopyTexImage2D(GL_TEXTURE_2D, 0,GL_DEPTH_COMPONENT, 0, 0, self.width,
                         self.height, 0);
        
        _gllib.glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, 0, 0, self.width,
                      self.height, 0);
        
        _gllib.glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 0, 0, self.width,
                      self.height, 0);        
        
        _gllib.glBindTexture (GL_TEXTURE_2D, 0);
    
    def drawSSAO(self,combine=0):
        if __debug__:
            if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        if DejaVu.enableSSAO is True and self.ssao:
            #if not self.AR.use_mask: 
            self.copyBuffer()
            from opengltk.extent import _glextlib
            
            import numpy
            _glextlib.glBindFramebufferEXT(_glextlib.GL_FRAMEBUFFER_EXT, 0 )

            _glextlib.glUseProgram( self.shaderSSAOProgram )

            glActiveTexture(GL_TEXTURE3);
            _gllib.glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
            _glextlib.glUniform1i(self.SSAO_LOCATIONS['DepthTexture'],3)
            
            glActiveTexture(GL_TEXTURE4);
            _gllib.glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
            _glextlib.glUniform1i(self.SSAO_LOCATIONS['RenderedTexture'],4)
            
            glActiveTexture(GL_TEXTURE5);
            _gllib.glBindTexture (GL_TEXTURE_2D, self.illumtextureName);        
            _glextlib.glUniform1i(self.SSAO_LOCATIONS['LuminanceTexture'],5)
            
            glActiveTexture(GL_TEXTURE6);
            _gllib.glBindTexture (GL_TEXTURE_2D, self.randomtextureName);        
            _glextlib.glUniform1i(self.SSAO_LOCATIONS['RandomTexture'],6)            
            
            glActiveTexture(GL_TEXTURE7);
            _gllib.glBindTexture (GL_TEXTURE_2D, self.depthmasktextureName);        
            _glextlib.glUniform1i(self.SSAO_LOCATIONS['DepthMaskTexture'],7)

            _glextlib.glUniform1f(self.SSAO_LOCATIONS['RenderedTextureWidth'],self.width)
            _glextlib.glUniform1f(self.SSAO_LOCATIONS['RenderedTextureHeight'],self.height)
            
            _glextlib.glUniform1f(self.SSAO_LOCATIONS['realfar'],self.far)
            #_glextlib.glUniform1f(self.SSAO_LOCATIONS['realnear'],self.near)

            for k in self.SSAO_OPTIONS:
                if len(self.SSAO_OPTIONS[k]) == 5 :
                    self.SSAO_OPTIONS[k][0] = self.SSAO_OPTIONS[k][-1].get()
                val = self.SSAO_OPTIONS[k][0]
                if k == "far" :
                    val = self.far + 230.
                    if len(self.SSAO_OPTIONS[k]) == 5 :
                        val = self.SSAO_OPTIONS[k][-1].get()
                if k == "fog" :
                    val = int(self.fog.enabled)
                    if len(self.SSAO_OPTIONS[k]) == 5 :
                        self.SSAO_OPTIONS[k][-1].set(val)
                if self.SSAO_OPTIONS[k][3] == "float":
                    _glextlib.glUniform1f(self.SSAO_LOCATIONS[k],val)
                else : 
                    _glextlib.glUniform1i(self.SSAO_LOCATIONS[k],val)
                
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT |
                GL_STENCIL_BUFFER_BIT) 
            self.drawTexturePolygon()
            self.endSSAO()

    def endSSAO(self):
        if DejaVu.enableSSAO is True :
            from opengltk.extent import _glextlib
            _glextlib.glUseProgram(0)
            glActiveTexture(GL_TEXTURE0);            
            _gllib.glBindTexture (GL_TEXTURE_2D, 0); 
#            _gllib.glBindTexture (GL_TEXTURE_2D,GL_TEXTURE0)

            
            
    def drawTexturePolygon(self):
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        lViewport = glGetIntegerv(GL_VIEWPORT)
        glOrtho(float(lViewport[0]),
                float(lViewport[0]+lViewport[2]),
                float(lViewport[1]),
                float(lViewport[1]+lViewport[3]),
                -1, 1)        
        glEnable(GL_BLEND)

#        glEnable(GL_TEXTURE_2D)
#        if self.dsT == 0 :
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.depthtextureName);
#        elif self.dsT == 1 :
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.illumtextureName);
#        else :
#            _gllib.glBindTexture (GL_TEXTURE_2D, self.rendertextureName);
        glBegin(GL_POLYGON)
        glTexCoord2i(0, 0)
        glVertex2i(0, 0)
        glTexCoord2i(1, 0)
        glVertex2i(self.width, 0)
        glTexCoord2i(1, 1)
        glVertex2i(self.width, self.height)
        glTexCoord2i(0, 1)
        glVertex2i(0, self.height)
        glEnd()
        glDisable(GL_BLEND)  
        _gllib.glBindTexture (GL_TEXTURE_2D, 0);      
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

##     def DrawImage(self, imarray, mode='RGB', format=GL.GL_UNSIGNED_BYTE,
##                   filter=None, swap=False):
##         """Draw an array of pixel in the camera
## """
##         if imarray is None:
##             return

##         GL.glViewport(0, 0, self.width, self.height)
##         GL.glMatrixMode(GL.GL_PROJECTION)
##         GL.glPushMatrix()
##         GL.glLoadIdentity()
##         GL.glOrtho(0, self.width, 0, self.height, -1.0, 1.0)
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPushMatrix()
##         GL.glLoadIdentity()

##         GL.glRasterPos2i( 0, 0)
##         GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

##         if not swap:
##             GL.glDrawBuffer(GL.GL_BACK)

##         if filter:
##             GL.glEnable(GL.GL_CONVOLUTION_2D)
##             GL.glConvolutionFilter2D(GL.GL_CONVOLUTION_2D, GL.GL_LUMINANCE,
##                                      3, 3, GL.GL_LUMINANCE, GL.GL_FLOAT,
##                                      filter)

##         if mode=='RGB':
##             _gllib.glDrawPixels( self.width, self.height,
##                                  GL.GL_RGB, format, imarray)
##         elif mode in ['L','P']:
##             _gllib.glDrawPixels( self.width, self.height,
##                                  GL.GL_LUMINANCE, format, imarray)

##         GL.glMatrixMode(GL.GL_PROJECTION)
##         GL.glPopMatrix()
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPopMatrix()
        
##         GL.glDisable(GL.GL_CONVOLUTION_2D)

##         GL.glFlush()

##         if swap:
##             self.tk.call(self._w, 'swapbuffers')


##     def secondDerivative(self, imarray, mode='RGB', format=GL.GL_UNSIGNED_BYTE,
##                          swap=False):
##         sndDeriv = Numeric.array([ [-0.125, -0.125, -0.125,],
##                                    [-0.125,    1.0, -0.125,],
##                                    [-0.125, -0.125, -0.125,] ], 'f')
##         self.DrawImage(imarray, mode, format, sndDeriv, swap)
##         if not swap:
##             buffer=GL.GL_BACK
##         deriv = self.GrabFrontBufferAsArray(lock=False, buffer=buffer)
##         return Numeric.fabs(deriv).astype('B')
    

##     def firstDerivative(self, imarray, mode='RGB', format=GL.GL_UNSIGNED_BYTE,
##                         swap=False):
##         if not swap:
##             buffer=GL.GL_BACK
##         else:
##             buffer=GL.GL_FRONT
    
##         fstDeriveV = Numeric.array([ [-0.125,  -0.25, -0.125],
##                                      [ 0.0  ,    0.0,  0.0  ],
##                                      [0.125,  0.25, 0.125] ], 'f')

##         self.DrawImage(imarray, mode, format, fstDeriveV, swap)
##         derivV = self.GrabFrontBufferAsArray(lock=False, buffer=buffer)
##         if derivV is None:
##             return None
    
##         fstDeriveV = Numeric.array([ [ 0.125,   0.25,  0.125],
##                                      [ 0.0  ,    0.0,  0.0  ],
##                                      [-0.125,  -0.25, -0.125] ], 'f')

##         self.DrawImage(imarray, mode, format, fstDeriveV, swap)
##         derivV += self.GrabFrontBufferAsArray(lock=False, buffer=buffer)
##         derivV = Numeric.fabs(derivV*0.5)

##         fstDeriveH = Numeric.array([ [-0.125,    0.0, 0.125],
##                                      [-0.25 ,    0.0, 0.25  ],
##                                      [-0.125,    0.0, 0.125] ], 'f')
##         self.DrawImage(imarray, mode, format, fstDeriveH, swap)
##         derivH = self.GrabFrontBufferAsArray(lock=False, buffer=buffer)
        
##         fstDeriveH = Numeric.array([ [ 0.125,    0.0, -0.125],
##                                      [ 0.25 ,    0.0, -0.25  ],
##                                      [ 0.125,    0.0, -0.125] ], 'f')
##         self.DrawImage(imarray, mode, format, fstDeriveH, swap)
##         derivH += self.GrabFrontBufferAsArray(lock=False, buffer=buffer)
##         derivH = Numeric.fabs(derivH*0.5)

##         return derivH+derivV.astype('B')

    
        
    def Redraw(self, *dummy):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

        if self.selectDragRect:
            return
        if not self.initialized:
            return
        if not self.visible:
            return

        # was causing very slow update of light source
        # This function shoudl force redrawing and hence not
        # wait for other things to happen
        #self.update_idletasks()

        # At this point We expect no interruption after this
        # and this OpenGL context should remain the current one until
        # we swap buffers
        self.tk.call(self._w, 'makecurrent')
        #glPushAttrib(GL_ALL_ATTRIB_BITS)

        if not self.viewer.tileRender:
            # only setup camera projection if we are not rendering tiles
            # when tiles are rendered the projection is set by the tile
            # renderer tr.beginTile() method
            if self.projectionType==self.ORTHOGRAPHIC:
                self.PerspectiveToOrthogonal()
            else:
                self.SetupProjectionMatrix()


        if self.renderMode == GL_RENDER:
            # This activate has to be done here, else we get a
            # GLXBadContextState on the alpha. If we are in 
            # GL_SELECT mode we did already an activate in DoPick

            # here we need to restore the camrea's GLstate
            if self.viewer and len(self.viewer.cameras) > 1:
                #self.SetupProjectionMatrix()
                self.fog.Set(enabled=self.fog.enabled)

        r,g,b,a = self.backgroundColor
        glClearColor(r, g, b, a )

        self.RedrawAASwitch()

        while 1:
            errCode = glGetError()
            if not errCode: break
            errString = gluErrorString(errCode)
            print 'GL ERROR: %d %s' % (errCode, errString)

       
    def glError(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        while 1:
            errCode = glGetError()
            if not errCode: return
            errString = gluErrorString(errCode)
            print 'GL ERROR: %d %s' % (errCode, errString)
            

    def SetupLights(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        """ loops over the lights and sets the direction and/or position of a
        light only if it is enabled and the flag is set to positive. Also, if
        there is more than one camera, it always sets the lights that are on"""
        for l in self.viewer.lights:
            if l.enabled is True:
                if len(self.viewer.cameras) > 1:
                    if l.positional is True:
                        glLightfv(l.num, GL_POSITION, l.position)
                        glLightfv(l.num, GL_SPOT_DIRECTION,
                                         l.spotDirection)
                    else:  # directional
                        glLightfv(l.num, GL_POSITION, l.direction)
                else:
                    if l.positional is True:
                        if l.posFlag:
                            glLightfv(l.num, GL_POSITION, l.position)
                            l.posFlag = 0
                        if l.spotFlag:
                            glLightfv(l.num, GL_SPOT_DIRECTION,
                                         l.spotDirection)
                            l.spotFlag = 0
                    else:  #directional
                        if l.dirFlag:
                            #rot = Numeric.reshape(self.rotation, (4,4))
                            #dir = Numeric.dot(l.direction, rot).astype('f')
                            #glLightfv(l.num, GL_POSITION, dir)
                            glLightfv(l.num, GL_POSITION, l.direction)
                            l.dirFlag = 0
                            #self.posLog.append(l.direction)
                            #print 'setting light to ',l.direction
##                              l.posFlag = 0
##                              l.spotFlag = 0
               

    def activeStereoSupport(self):
        if __debug__:
         if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
        try:
            root = Tkinter.Tk()
            root.withdraw()
            loadTogl(root)
            Tkinter.Widget(root, 'togl', (), {'stereo':'native'} )
            #currentcontext = self.tk.call(self._w, 'contexttag')
            #print "StandardCamera.activeStereoSupport currentcontext", currentcontext

            if GL.glGetIntegerv(GL.GL_STEREO)[0] > 0:
                lReturn = True
            else:
                #print 'Stereo buffering is not available'
                lReturn = False

            Tkinter.Widget(root, 'togl', (), {'stereo':'none'} )
            return lReturn

        except Exception, e:
            if str(e)=="Togl: couldn't get visual":
                #print 'Stereo buffering is not available:', e
                lReturn = False
            elif str(e)=="Togl: couldn't choose stereo pixel format":
                #print 'Stereo buffering is not available:', e
                lReturn = False
            else:
                print 'something else happend',e
                lReturn = False
            Tkinter.Widget(root, 'togl', (), {'stereo':'none'} )
            return lReturn


try:
    import pymedia.video.vcodec as vcodec
    
    class RecordableCamera(StandardCamera):
        """Subclass Camera to define a camera supporting saving mpg video
    """

        def __init__(self, master, screenName, viewer, num, check=1,
                     cnf={}, **kw):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

            StandardCamera.__init__( self, *(master, screenName, viewer, num,
                                             check, cnf), **kw)
            # this attribute can be 'recording', 'autoPaused', 'paused' or 'stopped'
            self.videoRecordingStatus = 'stopped'
            self.videoOutputFile = None
            self.pendingAutoPauseID = None
            self.pendingRecordFrameID = None
            self.encoder = None
            self.autoPauseDelay = 1 # auto pause after 1 second
            self.pauseLength = 15 # if recording pauses automatically
                                  # add self.pauseLength frames will be added
                                  # when recording resumes
            self.videoRecorder = None
            self.nbRecordedframes = 0
            self.vidimage = None

        def setVideoOutputFile(self, filename='out.mpg'):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            # open the file
            self.videoOutputFile = open( filename, 'wb' )
            assert self.videoOutputFile, 'ERROR, failed to open file: '+filename


        def setVideoParameters(self, width=None, height=None, pauseLength=0,
                               autoPauseDelay=1, outCodec = 'mpeg1video'):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            # make sure image is dimensions are even
            if width is None:
                width = self.width
            w = self.videoFrameWidth = width - width%2

            if height is None:
                height = self.height
            h = self.videoFrameHeight = height - height%2
            if h != self.height or w != self.width:
                self.Set(width=w, height=h)

            ## FIXME here we should lock the size of the Camera
            ##

            params= { 'type': 0, 'gop_size': 12, 'frame_rate_base': 125,
                     'max_b_frames': 0, 'width': w, 'height': h,
                     'frame_rate': 2997,'deinterlace': 0, #'bitrate': 9800000,
                     'id': vcodec.getCodecID(outCodec)
                     }
##             params= { 'type': 0, 'gop_size': 12, 'frame_rate_base': 125,
##                      'max_b_frames': 0, 'width': w, 'height': h,
##                      'frame_rate': 2997,'deinterlace': 0, 'bitrate': 2700000,
##                      'id': vcodec.getCodecID( 'mpeg1video' )
##                      }
            if outCodec== 'mpeg1video':
                params['bitrate']= 2700000
            else:
                params['bitrate']= 9800000
            self.encoder = vcodec.Encoder( params )
            self.pauseLength = pauseLength
            self.autoPauseDelay = autoPauseDelay


        def start(self):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            # toggle to recording mode
            if self.videoOutputFile is None or self.encoder is None:
                return
            self.videoRecordingStatus = 'recording'
            self.nbRecordedframes = 0 
            self.viewer.master.after(1, self.recordFrame)


        def recordFrame(self, force=False):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()

            if not self.viewer.hasRedrawn and not force:
                return

            root = self.viewer.master

            if self.videoRecordingStatus=='paused':
                self.pendingRecordFrameID = root.after(1, self.recordFrame)
                return
        
##             if self.videoRecordingStatus=='autopaused':
##                 # add frames for pause
##                 #print 'adding %d pause frames --------------', self.pauseLength
##                 imstr = self.lastFrame.tostring()
##                 for i in range(self.pauseLength):
##                     bmpFrame = vcodec.VFrame(
##                         vcodec.formats.PIX_FMT_RGB24, self.lastFrame.size,
##                         (imstr, None, None))
##                     yuvFrame = bmpFrame.convert(vcodec.formats.PIX_FMT_YUV420P)
##                     self.videoOutputFile.write(
##                         self.encoder.encode(yuvFrame).data)
##                 self.videoRecordingStatus = 'recording'

            if self.videoRecordingStatus=='recording' or force:
                if self.pendingAutoPauseID:
                    print 'auto pause id', self.pendingAutoPauseID
                    root.after_cancel(self.pendingAutoPauseID)
                    self.pendingAutoPauseID = None
#                if DejaVu.enableSSAO is True and self.ssao :#and self.vidimage is not None:
#                    image = self.GrabFrontBuffer(lock=False)
#                else :
                image = self.GrabFrontBuffer(lock=False)
                    # FIXME this resizing can be avoided if camera size is locked
                image = image.resize((self.videoFrameWidth,
                                      self.videoFrameHeight))
                self.lastFrame = image
                bmpFrame = vcodec.VFrame(
                    vcodec.formats.PIX_FMT_RGB24, image.size,
                    (self.lastFrame.tostring(), None, None))
                yuvFrame = bmpFrame.convert(vcodec.formats.PIX_FMT_YUV420P)
                self.videoOutputFile.write(self.encoder.encode(yuvFrame).data)
                #self.pendingAutoPauseID = root.after(self.autoPauseDelay*1000,
                #                                     self.autoPause)
                self.viewer.hasRedrawn = False

                self.pendingRecordFrameID = root.after(1, self.recordFrame)
                self.nbRecordedframes += 1

        def Redraw(self):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            StandardCamera.Redraw(self)
            self.viewer.hasRedrawn = True
            self.recordFrame()
            
            
        def autoPause(self):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            #print 'autoPause =========================='
            self.videoRecordingStatus = 'autoPaused'
            if self.pendingRecordFrameID:
                root = self.viewer.master
                root.after_cancel(self.pendingRecordFrameID)    
            self.pendingAutoPauseID = None


        def pause(self):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            #print 'pause =========================='
            self.videoRecordingStatus = 'paused'
            if self.pendingRecordFrameID:
                root = self.viewer.master
                root.after_cancel(self.pendingRecordFrameID)    
            self.pendingAutoPauseID = None


        def stop(self):
            if __debug__:
             if hasattr(DejaVu, 'functionName'): DejaVu.functionName()
            self.videoRecordingStatus = 'stopped'
            self.videoOutputFile.close()
            root = self.viewer.master
            if self.pendingAutoPauseID:
                root.after_cancel(self.pendingAutoPauseID)
            if self.pendingRecordFrameID:
                root.after_cancel(self.pendingRecordFrameID)

    Camera = RecordableCamera

except ImportError:
    Camera = StandardCamera
