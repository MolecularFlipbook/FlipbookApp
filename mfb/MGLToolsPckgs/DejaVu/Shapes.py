## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 


#############################################################################
#
# Author: Sophie COON, Kevin CHAN, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/Shapes.py,v 1.15 2007/07/24 17:30:41 vareille Exp $
#
# $Id: Shapes.py,v 1.15 2007/07/24 17:30:41 vareille Exp $
#


import numpy.oldnumeric as Numeric, math

from opengltk.OpenGL import GL


"""
This module implements a set of Classes to describe 2D shape that can be used
to  perform an extrusion along a 3D path.
"""
   

class Shape2D:
    """
    Shape2D is a base class describing a 2D shape.
    """
    def __init__(self, contpts, contnorm, vertDup=0, firstDup=0):
        """
        contpts   : list of 3D coordinates of the control points describing the
                    shape2D.
        contnorm  : list of 3D vector specifying the normals at each vertex
                    of the shape2D.
        vertDup   : Flag specifying whether or not to duplicate each vertex and
                    normal.
        firstDup  : Flag specifying whether or not to duplicate the first
                    first vertex.
        """
        self.vertDup = vertDup
        self.firstDup = firstDup
        self.contpts = list(contpts)
        self.contnorm = list(contnorm)
        if vertDup:
            firstDupInd = 2
        else:
            firstDupInd = 1

        if firstDup:
            cont = self.contpts
            newcont = cont + cont[:firstDupInd]
            self.contpts = Numeric.array(newcont)

            contn = self.contnorm
            newcontn = contn + contn[:firstDupInd]
            self.contnorm = Numeric.array(newcontn)
            
        self.lenShape = len(self.contpts)
        
    def returnStringRepr(self):
        """ This method returns the string to be evaluated to create
        the object"""
        cname = self.__class__.__name__
        before = 'from %s import %s'%(self.__module__, cname)
        st = "%s(%s,%s, vertDup=%s, firstDup=%s)"%(cname,
                                                   self.contpts,
                                                   self.contnorm,
                                                   self.vertDup,
                                                   self.firstDup)
        
        return before, st
    
class Triangle2D(Shape2D):
    """ Class derived from Shape2D describing a Triangle."""
    def __init__(self, side = 1.0, vertDup=0, firstDup = 0 ):
        self.side = side
        x = side/2
        y1 = -side/(2*math.sqrt(3))
        y2 = side/math.sqrt(3)
        if not vertDup:
            pts = ( (-x, y1, 1), (0, y2, 1), (x, y1, 1) )
            norms = ((-math.sqrt(3)/2, -.5, 0), (0, 1, 0),
                      (math.sqrt(3)/2, -.5, 0),  )
        else:
            pts   = ( (-x, y1 , 1)    , (-x, y1, 1),
                      ( 0, y2 , 1)    , ( 0, y2, 1),
                      ( x, y1 , 1)    , ( x, y1, 1) )            
            norms = ( (0, -2*x, 0),    ( y1-y2,  x , 0),
                      ( y1-y2,  x , 0),( y2-y1,  x , 0),
                      ( y2-y1,  x , 0),(0, -2*x, 0),)
        
        Shape2D.__init__(self, pts, norms, vertDup=vertDup, firstDup=firstDup)

    def returnStringRepr(self):
        """ This method returns the string to be evaluated to create
        the object"""
        cname = self.__class__.__name__
        before = 'from %s import %s'%(self.__module__, cname)
        st = "%s(side=%s, vertDup=%s, firstDup=%s)"%(cname,
                                                     self.side,
                                                     self.vertDup,
                                                     self.firstDup)
        
        return before, st

class Ellipse2D(Shape2D):
    """ Class derived from Shape2D describing a Ellipse """

        
    def __init__(self, demiGrandAxis ,
                 demiSmallAxis, quality=12, vertDup=0, firstDup=0):
        """demiGrandAxis is 1/2 the width of the ellipse
        demiSmallAxis is 1/2 the height of the ellipse"""
        self.quality = quality
        self.demiGrandAxis = demiGrandAxis
        self.demiSmallAxis = demiSmallAxis
        
        circle = Numeric.zeros( (quality,3) ).astype('f')
        
        circleNormal = Numeric.zeros( (quality,3) ).astype('f')

        # when points are duplicated:
        # norm0 = (x(i-1)-xi,y(i-1)-y, z(i-1)-z(i)) cross (0,0,1) 
        # norm1 = (0, 0, 1) cross (x(i+1)-xi,y(i+1)-y, z(i+1)-z(i))

        # x = y1*z2 - y2*z2
        # y = z1*x2 - z2*x1
        # z = x1*y2 - x2*y1

        for i in range( quality ):
            circle[i][0] = 2*demiGrandAxis*math.cos( i*2*math.pi/quality)
            circle[i][1] = -2*demiSmallAxis*math.sin( i*2*math.pi/quality)
            circle[i][2] = 1

            circleNormal[i][0] = math.cos( i*2*math.pi/quality )
            circleNormal[i][1] = -math.sin( i*2*math.pi/quality )
            circleNormal[i][2] = 0

        if vertDup:
            pts  = Numeric.zeros( (quality*2, 3)) .astype('f')
            norm = Numeric.zeros( (quality*2, 3)) .astype('f')
            # index for pts and norm
            ptsInd = 0
            for ind in range(quality):
                if ind == 0:
                    prev = quality-1
                    next = ind+1
                elif ind == quality-1:
                    next = 0
                    prev = ind-1
                else:
                    next = ind + 1
                    prev = ind - 1

                # Compute the Vprev vector and the Vnext vector
                Vprev = circle[prev]-circle[ind]
                Vnext = circle[next]-circle[ind]

                n0 = [ Vprev[1], -Vprev[0], 0 ]
                n1 = [-Vnext[1],  Vnext[0], 0 ]
                norm[ptsInd], norm[ptsInd+1] = n0, n1
                pts[ptsInd], pts[ptsInd+1] = circle[ind], circle[ind]

                ptsInd = ptsInd + 2
        
            circle = pts
            circleNormal = norm

        Shape2D.__init__(self, circle, circleNormal, vertDup=vertDup,
                         firstDup=firstDup)

    def returnStringRepr(self):
        """ This method returns the string to be evaluated to create
        the object"""
        cname = self.__class__.__name__
        before = 'from %s import %s'%(self.__module__, cname)
        st = "%s(%s, %s, quality=%s,  vertDup=%s, firstDup=%s)"%(cname,
                                                                self.demiGrandAxis,
                                                                self.demiSmallAxis,
                                                                self.quality,
                                                                self.vertDup,
                                                                self.firstDup)
        
        return before, st


class Circle2D(Ellipse2D):
    """ Class derived from Ellipse2D describing a Circle."""
    def __init__(self, radius, quality=12, vertDup=0, firstDup=0):
        self.radius = radius
        Ellipse2D.__init__(self, radius, radius, quality=quality,
                           firstDup=firstDup, vertDup=vertDup)

    def returnStringRepr(self):
        """ This method returns the string to be evaluated to create
        the object"""
        cname = self.__class__.__name__
        before = 'from %s import %s'%(self.__module__, cname)
        st = "%s(%s, quality=%s, vertDup=%s, firstDup=%s)"%(cname,
                                                            self.radius,
                                                            self.quality,
                                                            self.vertDup,
                                                            self.firstDup)
        return before, st


class Rectangle2D(Shape2D):
    """ Class derived from Shape2D describing a Rectangle """
    def __init__(self, width, height, vertDup=0, firstDup=0):
        self.width = width
        self.height = height
        if not vertDup:
            pts = ( (-width, -height, 1), (-width, height, 1),
                    (width, height, 1), (width, -height, 1) )
            norms = ( (-1,-1,0), (-1,1,0), (1,1,0), (1,-1,0) )
        else:
            pts = ( (-width, -height, 1), (-width, -height, 1),
                    (-width, height, 1), (-width, height, 1),
                    (width, height, 1), (width, height, 1),
                    (width, -height, 1), (width, -height, 1) )
            norms = ( (0,-1,0), (-1,0,0), (-1,0,0), (0,1,0),
                      (0,1,0), (1,0,0), (1,0,0), (0,-1,0) )
            

        Shape2D.__init__(self, pts, norms, vertDup=vertDup, firstDup=firstDup)

    def returnStringRepr(self):
        """ This method returns the string to be evaluated to create
        the object"""
        before = 'from %s import %s'%(self.__module__, self.__class__.__name__)
        st = "%s(%s, %s, vertDup=%s, firstDup=%s)"%(self.__class__.__name__,
                                                    self.width, self.height,
                                                    self.vertDup,self.firstDup)
        return before, st


class Square2D(Rectangle2D):
    """ Class derived from Shape2D describing a Square """
    def __init__(self, side, vertDup=0, firstDup=0):
        self.side = side
        Rectangle2D.__init__(self, side, side, vertDup=vertDup,
                             firstDup=firstDup)
    def returnStringRepr(self):
        """ This method returns the string to be evaluated to create
        the object"""
        before = 'from %s import %s'%(self.__module__, self.__class__.__name__)
        st = "%s(%s, vertDup=%s, firstDup=%s)"%(self.__class__.__name__,
                                                       self.side,
                                                       self.vertDup, self.firstDup)
        return before, st

