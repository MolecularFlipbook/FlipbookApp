## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Ruth HUEY, Michel SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Box.py,v 1.36 2009/09/03 19:24:15 annao Exp $
#
# $Id: Box.py,v 1.36 2009/09/03 19:24:15 annao Exp $
#

import numpy.oldnumeric as Numeric
from opengltk.OpenGL import GL

from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Geom import Geom
from DejaVu.IndexedGeom import IndexedGeom
import datamodel
import viewerConst
from DejaVu.viewerFns import checkKeywords

def uniq(objectSequence):
    """ returns a list with no duplicates"""
    d = {}
    for o in objectSequence: d[id(o)] = o
    return d.values()


class CallBackFunction:
    """Class to allow to specify arguments to a callback function"""

    def __init__(self, function, *args, **kw):
        self.function = function
        self.args = args
        self.kw = kw

    def __call__(self, *args, **kw):
        args = self.args + args
        kw.update(self.kw)
        return apply(self.function, args, kw)


class Box(IndexedPolygons):
    """3-D Polygon with 8 vertices.
    Box has attributes center and xside, yside, zside.

    if vertices are supplied, 
        vertices[2] + vertices[4] are used to define xside, yside, zside 
            + center

    In addition to a set of vertices, a Box can be defined by setting 
    any of these combinations:
        center + side
        center + xside, yside, zside
        origin + side (origin is 'smallest' valued point of vertices)
        origin + xside, yside, zside
        origin + center
        two cornerPoints where cornerPoints are ordered:
                center - halfsides, center + halfsides

    Precedence among these possible parameters is defined as follows:
        side < [x,y,z]side < center < origin < cornerPoints < vertices
    """
    
    
    keywords = IndexedPolygons.keywords + [
        'maxCube',
        'minCube',
        'vertices',
        'side',
        'xside',
        'yside',
        'zside',
        'center',
        'origin',
        'cornerPoints',
        ]


    def __init__(self, name=None, check=1, **kw):

        self.maxCube = None
        self.minCube = None

        if    not kw.get('origin') \
          and not kw.get('center') \
          and not kw.get('cornerPoints') \
          and not kw.get('minCube'):
            kw['origin'] = (0, 0, 0)

        #set up some defaults:
        materials = kw.get('materials')
        #print 'in BOX materials kw=', materials
        if not materials:
            kw['materials'] = ((0,0,1),(0,1,0),(0,0,1),(0,1,0),(1,0,0),(1,0,0),)
        #print 'in BOX after test for materials, kwmaterials=', kw['materials']

        vertices = kw.get('vertices')
        if vertices is not None:
            assert len(vertices)==8
            pt1 = Numeric.array(vertices[2])
            pt2 = Numeric.array(vertices[4])
            self.center = tuple(Numeric.multiply(Numeric.add(pt1,pt2), 0.5))
            self.xside, self.yside, self.zside = \
                Numeric.subtract(pt2,pt1)
        else:
            #set up center 
            center = kw.get('center')
            #if not center: center = (0.,0.,0.)
            self.center = center

            #set up sides
            side = kw.get('side')
            if side:
                self.xside = side
                self.yside = side
                self.zside = side
            else:
                xside = kw.get('xside')
                if not xside: xside = 1.0
                self.xside = xside
                yside = kw.get('yside')
                if not yside: yside = 1.0
                self.yside = yside
                zside = kw.get('zside')
                if not zside: zside = 1.0
                self.zside = zside

        #NB faces shouldn't change
        self.faces=((0,3,2,1),
                (3,7,6,2),
                (7,4,5,6),
                (0,1,5,4),
                (1,2,6,5),
                (0,4,7,3))
        self.funcs = {}
        fkeys = ['center', 'origin', 'centerOrigin', 'xside', \
                'yside', 'zside','maxCube', 'minCube']
        fs = [self.getVertsFromCenter, self.getVertsFromOrigin, \
                self.getVertsFromCenterOrigin, 
                CallBackFunction(self.getVertsFromSide, 'xside'),
                CallBackFunction(self.getVertsFromSide, 'yside'),
                CallBackFunction(self.getVertsFromSide, 'zside'),
                self.setMaxCube, self.setMinCube]
        for i in range(len(fkeys)):
            self.funcs[fkeys[i]] = fs[i]


        self.pickableVertices = 1
        kw['frontPolyMode'] = 'line'
        apply( IndexedPolygons.__init__, (self, name, check), kw )
        self.inheritMaterial = 0
        
        #print 'calling self.Set with ', kw.get('materials')
        #apply(self.Set,(), kw)

        # register functions to compute normals
        self.VertexNormalFunction(self.ComputeVertexNormals)
        self.vertexSet.normals.ComputeMode( viewerConst.AUTO )
        self.FaceNormalFunction(self.ComputeFaceNormals)
        self.faceSet.normals.ComputeMode( viewerConst.AUTO )
        self._PrimitiveType()
        self.GetNormals()
        self.oldFPM = GL.GL_LINE


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object: Set polygon's vertices, faces, normals or materials
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redoFlags = 0

        #newKeyList is list of keys specified in call to Set
        newKeyList = kw.keys()

        # Setting both center AND origin is a special case
        # which sets all side lengths
        centerOrigin = 0
        if 'center' in newKeyList and 'origin' in newKeyList:
            centerOrigin = 1

        side= kw.get( 'side')
        if side:
            kw['xside'] = side
            kw['yside'] = side
            kw['zside'] = side
            newKeyList.extend(['xside','yside', 'zside'])
            newKeyList = uniq(newKeyList)

        apply(self.updateVal, (['xside','yside','zside'],),kw)

        #these are either 1 or None
        self.maxCube = kw.get('maxCube')
        self.minCube = kw.get('minCube')
        if self.minCube and self.maxCube:
            self.center = [ (self.minCube[0] + self.maxCube[0]) * .5 ,
                            (self.minCube[1] + self.maxCube[1]) * .5 ,
                            (self.minCube[2] + self.maxCube[2]) * .5 ]
       
        # kl used to implement this precedence: 
        # side < [x,y,z]side < center < origin < cornerPoints < vertices
        # vertices are dealt with last
        cornerPoints = None
        kl = ['xside', 'yside', 'zside','minCube', 'maxCube', 'center', 'origin'] 
        for key in kl:
            if key in newKeyList:
                newVal = kw.get(key)
                if not newVal: continue
                if key in ['center','origin'] and centerOrigin:
                    self.center = kw.get('center')
                    newVal = kw.get('origin')
                    newKeyList.remove('center')
                    newKeyList.remove('origin')
                    f = self.funcs['centerOrigin']
                else:
                    del kw[key]
                    f = self.funcs[key]
                cornerPoints = apply(f, (newVal,),{})

        #if cornerPoints are specified, they override other info
        newcornerPoints = kw.get('cornerPoints')
        if newcornerPoints:
            cornerPoints = newcornerPoints

        if cornerPoints:
            ptList = self.getVertsFromCornerPts(cornerPoints)
        else:
            ptList = None

        #vertices overrides everything: set center+sides
        newVertices = kw.get('vertices')
        if newVertices is not None:
            assert len(newVertices)==8
            pt1 = Numeric.array(newVertices[2])
            pt2 = Numeric.array(newVertices[4])
            self.center = tuple(Numeric.multiply(Numeric.add(pt1,pt2), 0.5))
            self.xside, self.yside, self.zside = \
                Numeric.subtract(pt2,pt1)
            redoFlags |= self._redoFlags['redoDisplayListFlag']
        elif ptList:
            assert len(ptList)==8
            kw['vertices'] = ptList
            redoFlags |= self._redoFlags['redoDisplayListFlag']

        if kw.get('faces') is None:
            kw['faces'] = self.faces

        redoFlags |= apply( IndexedPolygons.Set, (self, check, 0), kw )

        return self.redoNow(redo, updateOwnGui, redoFlags)


    def updateVal(self, keyList, **kw):
        for item in keyList:
            itemVal = kw.get(item)
            if itemVal:
                setattr(self, item, itemVal)
                #exec('self.'+item+'='+str(itemVal))
            

    def setMaxCube(self, val):
        side = max(self.xside, self.yside, self.zside)
        self.xside = side
        self.yside = side
        self.zside = side
        return self.getVertsFromCenter(self.center)


    def setMinCube(self, val):
        side = min(self.xside, self.yside, self.zside)
        self.xside = side
        self.yside = side
        self.zside = side
        return self.getVertsFromCenter(self.center)


    def getVertsFromSide(self, sideStr, value):
        setattr(self, sideStr, value)
        #exec('self.'+sideStr+'=' + str(value))
        return self.getVertsFromCenter(self.center)


    def getVertsFromCenterOrigin(self, origin):
        #in this case, the origin is pt0
        x0,y0,z0 = origin
        x1,y1,z1 = self.center
        self.xside = x0 + 2*(x1-x0)
        self.yside = y0 + 2*(y1-y0)
        self.zside = z0 + 2*(z1-z0)
        pt1 = (self.xside, self.yside, self.zside)
        return (origin, pt1)
        

    def halfPt(self, pt):
        return  Numeric.multiply(pt, 0.5)


    def getVertsFromOrigin(self, origin):
        #set new center here, also
        side = Numeric.array((self.xside, self.yside, self.zside))
        self.center = tuple(Numeric.add(origin, Numeric.multiply(side, 0.5)))
        pt1=tuple(Numeric.add(origin, side))
        return (origin, pt1)
            

    def getVertsFromCenter(self, center):
        self.center = center
        halfSide = Numeric.multiply(Numeric.array((self.xside, self.yside, self.zside)), 0.5)
        pt1=tuple(Numeric.add(center,halfSide))
        pt0=tuple(Numeric.subtract(center,halfSide))
        return (pt0, pt1)


    def getVertsFromCornerPts(self, cornerPoints):
        # cornerPoints = (center-halfsides, center+halfsides)
        # cornerPoints = (pt0, pt1)
        x1,y1,z1=cornerPoints[1]
        x0,y0,z0=cornerPoints[0]
        self.xside = x1-x0
        self.yside = y1-y0
        self.zside = z1-z0
        center = (x1-(x1-x0)/2., y1-(y1-y0)/2., z1-(z1-z0)/2.)
        self.center = center
        # maxCube sets box to cube with side = largest of x,y,z-side
        # min sets box to cube with side = smallest of x,y,z-side
        # maxCube has precedence over minCube
        if self.maxCube or self.minCube:
            if self.maxCube:
                side = max((x1-x0,y1-y0,z1-z0))
            elif self.minCube:
                side = min((x1-x0,y1-y0,z1-z0))
            self.xside = side
            self.yside = side
            self.zside = side
            pt1=tuple(Numeric.add(center,(side/2.,side/2,side/2)))
            pt0=tuple(Numeric.subtract(center,(side/2,side/2,side/2)))
            x1,y1,z1 = pt1
            x0,y0,z0 = pt0
        #built list of 8 pts
        ptList=((x1,y1,z0),
            (x0,y1,z0),
            (x0,y0,z0),
            (x1,y0,z0),
            (x1,y1,z1),
            (x0,y1,z1),
            (x0,y0,z1),
            (x1,y0,z1))
        return ptList


    def DisplayFunction(self):
        if self.frontPolyMode != self.oldFPM:
            self.RedoDisplayList()
        IndexedPolygons.DisplayFunction(self)


    def Draw(self):
        #print"Box.Draw"
        self.oldFPM = self.frontPolyMode
        if self.frontPolyMode == GL.GL_LINE:
            GL.glDisable(GL.GL_LIGHTING)
            #c is 8x3 array 
            c= self.vertexSet.vertices.array
            #lines parallel to x-axis should be red, y->blue and z->green
            col = ((1,0,0),(0,1,0),(0,0,1))
            #these groups of 4 pairs of points define lines parallel to x, y, and z axes
            alines=[[(c[0],c[1]),(c[2],c[3]),(c[4],c[5]),(c[6],c[7])],
                [(c[0],c[3]),(c[1],c[2]),(c[4],c[7]),(c[5],c[6])],
                [(c[0],c[4]),(c[1],c[5]),(c[3],c[7]),(c[2],c[6])]]
            namectr=0
            for i in range(3):
                if not self.inheritMaterial:
                    GL.glColor3fv(col[i])
                for vpairs in alines[i]:
                    GL.glPushName(namectr)
                    GL.glBegin(GL.GL_LINES)
                    GL.glVertex3dv(list(vpairs[0]))
                    GL.glVertex3dv(list(vpairs[1]))
                    GL.glEnd()
                    GL.glPopName()
                    namectr=namectr+1
            self.viewer.enableOpenglLighting()
            return 1
        else:
            return IndexedPolygons.Draw(self)


class GridBox(Box):
    """ Specialized Box whose dimensions are controlled by spacing and npts
    in a grid.  A GridBox has additional attributes xspacing, yspacing, 
    zspacing and xnpts,ynpts and znpts.
    """

    keywords = Box.keywords + [
        'npts',
        'xnpts',
        'ynpts',
        'znpts',
        'spacing',
        'xspacing',
        'yspacing',
        'zspacing'
        ]


    def __init__(self, name=None, check=1, **kw):

        npts = kw.get('npts')
        if not npts: 
            xnpts = kw.get('xnpts')
            if not xnpts:
                kw['xnpts'] = 40
            ynpts = kw.get('ynpts')
            if not ynpts:
                kw['ynpts'] = 40
            znpts = kw.get('znpts')
            if not ynpts:
                kw['znpts'] = 40
        spacing = kw.get('spacing')
        if not spacing: 
            spacing = (.375,.375,.375)
            kw['spacing'] = (.375, .375, .375)

        apply( Box.__init__, (self, name, check), kw )


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redoFlags = apply( Box.Set, (self, check, 0), kw)

        #newKeyList is list of keys specified in call to Set
        newKeyList = kw.keys()
        npts= kw.get('npts')
        if npts:
            kw['xnpts'] = npts
            kw['ynpts'] = npts
            kw['znpts'] = npts
            newKeyList.extend(['xnpts','ynpts', 'znpts'])

        spacing = kw.get('spacing')
        if spacing:
            assert len(spacing)==3
            kw['xspacing'] = spacing[0]
            kw['yspacing'] = spacing[1]
            kw['zspacing'] = spacing[2]
            newKeyList.extend(['xspacing','yspacing', 'zspacing'])

        newKeyList = uniq(newKeyList)

        #update all 6 attributes
        apply(self.updateVal, (['xnpts','ynpts','znpts', 'xspacing',\
            'yspacing', 'zspacing'],),kw)

        if 'xnpts' in newKeyList or 'xspacing' in newKeyList:
            kw['xside'] = self.xnpts*self.xspacing

        if 'ynpts'  in newKeyList or 'yspacing' in newKeyList:
            kw['yside'] = self.ynpts*self.yspacing

        if 'znpts' in newKeyList or 'zspacing' in newKeyList:
            kw['zside'] = self.znpts*self.zspacing

        return self.redoNow(redo, updateOwnGui, redoFlags)
