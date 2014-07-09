## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Arcs3D.py,v 1.29 2008/11/20 00:54:16 vareille Exp $
#
# $Id: Arcs3D.py,v 1.29 2008/11/20 00:54:16 vareille Exp $
#

from opengltk.OpenGL import GL
import math, numpy.oldnumeric as Numeric, types
from math import sqrt, fabs, pi, cos, sin, acos, atan2
from Geom import Geom
from Polylines import Polylines
import datamodel, viewerConst
from viewerFns import checkKeywords, getkw
from DejaVu.colorTool import resetMaterialMemory

def valideFloat(values, length):
    """This function takes a single float, or int or a list of them and a
requested length and returns a list of float of length 1 or length.
"""
    if type(values)==types.FloatType:
        return [values]
    elif type(values)==types.IntType:
        return [float(values)]
    else:
        if len(values)==1:
            return [float(values[0])]
        else:
            assert len(values)==length
            return [float(v) for v in values]

    
class Fan3D(Geom):
    keywords = Geom.keywords + [
        'radii',  """either single float or list of same length as vertices""",
        'angles', """either single float or list of same length as vertices""",
        'vectors', """normalized vector where fan starts,
either single 3D vector or list of same length as vertices""",
        ]
    
    def __init__(self, name=None, check=1, **kw):
        
	if not kw.get('shape'):
	    kw['shape'] = (0,3)    # default shape for sphere set

        self.radii = (0.2,)
        self.angles = (360.0,)
        self.vectors = None
            
        self.degreesPerSegment = 10.
        self.frontPolyMode = self.backPolyMode = GL.GL_FILL
        self.inheritFrontPolyMode = self.inheritBackPolyMode = 0

        apply( Geom.__init__, (self, name, check), kw)

        assert len(self.vertexSet.vertices.ashape)==2
        
        self._modified = False
        

    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object: add faces (polygon or lines) to this object
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redoFlags = apply( Geom.Set, (self, check, 0), kw)

        c = self.vertexSet.vertices

        rad = kw.get('radii')
        if rad is not None:
            values = valideFloat(rad, len(c))
            if values is not None:
                redoFlags |= self._redoFlags['redoDisplayListFlag']
                self.radii = values
                
        ang = getkw(kw, 'angles')
        if ang is not None:
            values = valideFloat(ang, len(c))
            if values is not None:
                redoFlags |= self._redoFlags['redoDisplayListFlag']
                self.angles = values

        vec = getkw(kw, 'vectors')
        if vec is not None:
            if len(vec)==3:
                self.vectors = [vec]
            else:
                assert len(vec)==len(c)
                for v in vec:
                    assert len(v)==3
                self.vectors = vec
            redoFlags |= self._redoFlags['redoDisplayListFlag']

        return self.redoNow(redo, updateOwnGui, redoFlags)


    def Draw(self):
        for i in xrange(len(self.vertexSet)):
            if len(self.radii)==1:
                rad = self.radii[0]
            else:
                rad = self.radii[i]
            if len(self.angles)==1:
                ang = self.angles[0]
            else:
                ang = self.angles[i]

            vx, vy, vz = norm = self.vertexSet.normals.array[i]
            if self.vectors is None:
                # get orthogonal vector
                dx, dy, dz = fabs(vx), fabs(vy), fabs(vz)
                mini= min( [dx, dy, dz] )
                if mini==dx:
                    nov = 1./sqrt( vz*vz+ vy*vy )
                    ovx = 0.
                    ovy = -vz*nov
                    ovz =  vy*nov
                elif mini==dy:
                    nov = 1./sqrt( vz*vz+ vx*vx )
                    ovx = -vz*nov
                    ovy = 0.
                    ovz = vx*nov
                else:
                    nov = 1./sqrt( vy*vy+ vx*vx )
                    ovx = -vy*nov
                    ovy = vx*nov
                    ovz = 0.
                vec = [ovx, ovy, ovz]

            elif len(self.vectors)==1:
                vec = self.vectors[0]
            else:
                vec = self.vectors[i]

            angRad = ang*pi*0.00555555555556
            nsegments = int(ang/self.degreesPerSegment) + 1
            d = angRad / nsegments # increment
            a = 0		   # starting angle
            
            GL.glNormal3fv(norm.astype('f'))
            GL.glPushName(i)
            GL.glBegin(GL.GL_TRIANGLE_FAN)
            if self.materials[GL.GL_FRONT].binding[0]==viewerConst.PER_VERTEX:
                col = self.materials[GL.GL_FRONT].prop[0]
                GL.glColor4fv(col[i])
            center = Numeric.array(self.vertexSet.vertices.array[i])
            vec = Numeric.array(vec).astype('f')
            #vec = vec/sqrt(Numeric.sum(vec*vec))
            vec2 = Numeric.zeros(3, 'f')
            vec2[0] = vec[1]*norm[2] - vec[2]*norm[1]
            vec2[1] = vec[2]*norm[0] - vec[0]*norm[2]
            vec2[2] = vec[0]*norm[1] - vec[1]*norm[0]
            GL.glVertex3fv(center)
            for j in range(nsegments+1):
                p = center + cos(a)*vec*rad + sin(a)*vec2*rad
                GL.glVertex3fv(p.astype('f'))
                a = a+d
            GL.glEnd()
            GL.glPopName()
        return 1


class Arcs3D(Geom):
    """Class for sets of cylinders"""

    keywords = Geom.keywords + [
        'radii',
        'angles',
        'quality',
        ]
    
    def __init__(self, name=None, check=1, **kw):

	if not kw.get('shape'):
	    kw['shape'] = (0,3)    # default shape for sphere set

        self.radii = (0.2,)
        self.angles = (360.0,)

	self.lighting = False
        self.nsegments = 10

        apply( Geom.__init__, (self, name, check), kw)

        assert len(self.vertexSet.vertices.ashape)==2


    def Set(self, check=1, redo=1, updateOwnGui=True, **kw):
        """set data for this object: Set polylines's vertices
check=1 : verify that all the keywords present can be handle by this func 
redo=1 : append self to viewer.objectsNeedingRedo
updateOwnGui=True : allow to update owngui at the end this func
"""
        redoFlags = apply( Geom.Set, (self, check, 0), kw )

        c = self.vertexSet.vertices

        rad = kw.get('radii')
        if rad is not None:
            values = valideFloat(rad, len(c))
            if values is not None:
                self.radii = values
                redoFlags |= self._redoFlags['redoDisplayListFlag']
                
        ang = getkw(kw, 'angles')
        if ang is not None:
            values = valideFloat(ang, len(c))
            if values is not None:
                self.angles = values
                redoFlags |= self._redoFlags['redoDisplayListFlag']
                
        quality = getkw(kw, 'quality')
        if quality is not None:
            assert type(quality)==types.IntType and quality > 1
            self.nsegments = quality
            redoFlags |= self._redoFlags['redoDisplayListFlag']

        return self.redoNow(redo, updateOwnGui, redoFlags)


    def Draw(self):
        n = self.vertexSet.normals.array
        c = self.vertexSet.vertices.array

        ang = self.angles
        if len(self.angles)==1:
            self._arcTemplate(self.anges[0])
            if self.materials[GL.GL_FRONT].binding[1]==viewerConst.PER_VERTEX:
                col = self.materials[GL.GL_FRONT].prop[1]
                for i in xrange(len(self.vertexSet)):
                    if len(self.radii)==1:
                        rad = self.radii[0]
                    else:
                        rad = self.radii[i]
                    GL.glPushName(i)
                    self.arcdraw( c[i], n[i], rad, col[i] )
                    GL.glPopName()
            else:
                col = self.materials[GL.GL_FRONT].prop[1][0]
                for i in xrange(len(self.vertexSet)):
                    if len(self.radii)==1:
                        rad = self.radii[0]
                    else:
                        rad = self.radii[i]
                    GL.glPushName(i)
                    self.arcdraw( c[i], n[i], rad, col )
                    GL.glPopName()
        else:
             if self.materials[GL.GL_FRONT].binding[1]==viewerConst.PER_VERTEX:
                col = self.materials[GL.GL_FRONT].prop[1]
                for i in xrange(len(self.vertexSet)):
                    if i==0 or ang[i]!=ang[i-1]:
                        self._arcTemplate(ang[i])
                    if len(self.radii)==1:
                        rad = self.radii[0]
                    else:
                        rad = self.radii[i]
                    GL.glPushName(i)
                    self.arcdraw( c[i], n[i], rad, col[i] )
                    GL.glPopName()
             else:
                col = self.materials[GL.GL_FRONT].prop[1][0]
                for i in xrange(len(self.vertexSet)):
                    if i==0 or ang[i]!=ang[i-1]:
                        self._arcTemplate(ang[i])
                    if len(self.radii)==1:
                        rad = self.radii[0]
                    else:
                        rad = self.radii[i]
                    GL.glPushName(i)
                    self.arcdraw( c[i], n[i], rad, col )
                    GL.glPopName()
        

    def _arcTemplate(self, angle):

        nsegments = self.nsegments
        assert (nsegments>1)
        import numpy.oldnumeric as Numeric, math

        self.v = Numeric.zeros( ((nsegments+1),3), 'f')
        self.n = Numeric.zeros( ((nsegments+1),3), 'f')
        self.nsegments = nsegments

        angRad = angle*pi*0.00555555555556
        a = -pi 		# starting angle
        d = angRad / nsegments 	# increment

        for i in range(nsegments+1):
            self.n[i][0] = self.v[i][0] = cos(a)
            self.n[i][1] = self.v[i][1] = sin(a)
            self.n[i][2] = 1.0
            self.v[i][2] = 0.0
            a=a+d

    def arcdraw(self, x, n, radius, colxf=None):

        # determine scale and rotation of template
        import math
        sz=0.0
        y = [0, 0, 0]
        for i in (0,1,2):
            y[i] = x[i]+n[i]
        for i in (0,1,2):
            sz=sz+(x[i]-y[i])*(x[i]-y[i])
        sz = sqrt(sz)
        if sz==0.0:
            return
        rx = -180.0*acos((y[2]-x[2])/sz)/pi
        rz = -180.0*atan2(y[0]-x[0],y[1]-x[1])/pi

        GL.glPushMatrix()
        GL.glTranslatef(float(x[0]),float(x[1]),float(x[2]))
        if rz<=180.0 and rz >=-180.0:
            GL.glRotatef(float(rz), 0., 0., 1.)
        GL.glRotatef(float(rx), 1., 0., 0.)
        GL.glScalef(float(radius),float(radius),float(sz))

        # draw circle
        GL.glColor4fv(colxf)
        GL.glBegin(GL.GL_LINE_STRIP)
        for i in range(self.nsegments+1):
            GL.glVertex3fv(self.v[i])

        GL.glEnd()

        GL.glPopMatrix()


if __name__ == '__main__':
    from DejaVu.Arcs3D import Arcs3D, Fan3D
    c = Arcs3D('arc3d', vertices = ((0,0,0), (5.,0.,0.)),
                vnormals = ((1.0,0,0), (0, 1.,0)),
                materials = ( (1,0,0), (0,0,1)),
                radii = (1.0, 2.0),
                angles = ( 360., 180. ))

    f = Fan3D('fan3d', vertices = ((0,0,0), (5.,0.,0.)),
              vnormals = ((0,0,1), (0, 1.,0)),
              materials = ( (1,0,0), (0,0,1)),
              radii = (1.0, 2.0),
              angles = ( 60., 170. ),
              vectors = ((1,1,0), (1,0,0)))
    from DejaVu import Viewer
    vi = Viewer()
    vi.AddObject(c)
    vi.AddObject(f)
    
