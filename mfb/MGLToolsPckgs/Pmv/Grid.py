## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/Grid.py,v 1.32.4.1 2011/07/11 16:37:30 rhuey Exp $
#
# $Id: Grid.py,v 1.32.4.1 2011/07/11 16:37:30 rhuey Exp $
#

######################################################################
#
#In this module, class Grid and AutoGrid were defined by Shanrong Zhao
#
#                            Oct. 30, 1998
#
######################################################################

from numpy.oldnumeric import *
from types import *
import string, os, math
#import isocontour
from UTpackages.UTisocontour import isocontour
import Tkinter

##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr

from mglutil.util.callback import CallBackFunction

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ExtendedSliderWidget

##  from DejaVu.extendedSlider import ExtendedSlider
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.bitPatterns import patternList
from DejaVu.colorTool import Map, RGBRamp, array2DToImage
from DejaVu import Texture

from opengltk.OpenGL import GL

#isocontour.setVerboseLevel(1)
isocontour.setVerboseLevel(0)

# six compare object have been defined below
class greatObj:
    def __call__(self,a,b):
        return a > b

class notgreatObj:
    def __call__(self,a,b):
        return a <= b

class lessObj:
    def __call__(self,a,b):
        return a < b

class notlessObj:
    def __call__(self,a,b):
        return a >= b

class equalObj:
    def __call__(self,a,b):
        return a == b

class notequalObj:
    def __call__(self,a,b):
        return a !=  b

def uniqueSort(lst, func=None):
    assert type(lst) in [ListType, TupleType]
    if lst == []: return []
    res = {}
    def add__to__dict(value, d = res):
        d[value] = None
    map(add__to__dict , lst)
    lst2 = res.keys() 
    if func: lst2.sort(func)
    else: lst2.sort()
    return lst2

#######################################################################
#
# class tupleElement, group data as a pseudo SINGLE element
# for example, tupleElement can be used to represent coordinate
# (x,y,z), or the (key,value), or (key,index) pairs. The best
# advantage is: group data act as an object

# The present class tupleElement is not so powerful, but which will be
# enhanced in the future so that we can manipulate COMPLEX array
# elements in addition to number.
class tupleElement:
    def __init__(self, elements = None):
        if elements:
            self.data = tuple(elements)
        else:
            self.data =  tuple(())

    def __repr__(self):
        return repr(self.data)

    def __len__(self): return len(self.data)

    def __getitem__(self, index): 
        return self._rc(self.data[index])

    def __getslice__(self, i, j): 
        return self._rc(self.data[i:j])

    def __cmp__(self, other):
        if isinstance(other,self.__class__):
            return cmp(self.data, other.data)
        else:
            return cmp(self.data, self.__class__(other).data)

    def _rc(self, a):
        if len(shape(a)) == 0: return a
        return self.__class__(a)


#####################################################################
#
# In essense, a template class Set is a binary tree. The advantage of
# of Set is that you could easily to add and delete an element from the
# the set. The disadvatage is that you cannot manipulate those data in
# in a set as a whole.
#
# ATTENTION: set is ABSOLUTELY not a list. If your data behave like a
# list and you want to treat them as a set, please use VECTOR.
# For more information. please have a look at STL (Standard Template
# Library) head file set.h
#
# The Set class below employs LIST to store data, which would be updated
# in the future for both speed and memory management
#
#######################################################################
class Set:
    """
    Base class for sets of objects. The objects are stored in a list.
    For the sake of simplicity, the set is assumed to be homogenous
    Functios below are provided:
            add (+), sub (-), and (&), or (|), xor (^)
    """
    def __init__(self, objects=None, CompFunc= None):

        self.CompObj = CompFunc
        if objects:
            self.DataObj = uniqueSort(objects, self.CompObj)
        else:
            self.DataObj = []

    def __getitem__(self,key):
        return self.DataObj[key]

    def __getslice__(self,i,j):
        return self._rc(self.DataObj[i:j])

    def __repr__(self):
        if self.DataObj: return '<instance of %s> %d object: ' % \
            (self.__class__,len(self.DataObj))+ repr(self.DataObj)

    def __len__(self):
        return len(self.DataObj)

    def __cmp__(self, right):
        if type(right) == ListType:
            return cmp( self.DataObj, right)
        else:
            assert isinstance(right, self.__class__)
            return cmp( self.DataObj, right.DataObj)

    def filter(self, func):
        assert callable(func)
        newlist = filter(func, self.DataObj)
        return self._rc(newlist)

    def __add__(self, right):
        if type(right) == ListType:
            return self._rc( self.DataObj + right, self.CompObj )
        if type(right) == TupleType:
            return self._rc( self.DataObj + list(right), self.CompObj )
        assert isinstance(right, self.__class__)
        return self._rc( self.DataObj+right.DataObj, self.CompObj )

    def __sub__(self, right):
        if type(right) not in [ListType,TupleType]:
            assert isinstance(right, self.__class__)
            rlist = right.DataObj
        else:
            rlist = right

        data = {}
        for item in self.DataObj: data[item] = None
        for ritem in rlist:
            if data.has_key(ritem): del data[ritem]
        return self._rc(data.keys(),self.CompObj)

    # for logical operation, the two operands are required to be sets
    # Since both sets are ordered, it would be better to perform logical
    # operation by 'overlap' method. e.g.
    #        set1      ----------------------
    #                           i|          |j
    #        set2                =====================
    # Only for overlap regions (i,j), special comparision are required. It
    # seems that this would speed logical operation.
    def __and__(self, right): 
        assert isinstance(right, self.__class__)
        if len(self.DataObj) < len(right.DataObj):
            l1 = right.DataObj
            l2 = self.DataObj
        else:
            l1 = self.DataObj
            l2 = right.DataObj

        data = {}
        for item in l1: data[item] = None
        res = {}
        for item in l2:
            if data.has_key(item): res[item] = None

        return self._rc(res.keys(),self.CompObj)

    # !!! In a sense, __or__ is nearly identical to __add__.
    def __or__(self, right):
        assert isinstance(right, self.__class__)
        return self._rc( self.DataObj+right.DataObj, self.CompObj )

    def __xor__(self, right):
        assert isinstance(right, self.__class__)
        if len(self.DataObj) < len(right.DataObj):
            l1 = right.DataObj
            l2 = self.DataObj
        else:
            l1 = self.DataObj
            l2 = right.DataObj

        data = {}
        for item in l1: data[item] = None
        for item in l2:
            if data.has_key(item): del data[item]
            else:  data[item] = None

        return self._rc(data.keys(), self.CompObj)

    def _rc(self,objlst,func):
        return self.__class__(objlst,func)
    

#####################################################################
# function tupleArrayList flat all the arrays first, and then
# combine them. At last, output list
#
def tupleArrayList( arrays ):
    num = len(arrays)
    dimensions = arrays[1].shape
    size = multiply.reduce(dimensions)

    larray = zeros((num,size))                     
    for i in range(num):
        larray[i] = arrays[i].ravel()

    carray = transpose ( array (tuple(larray)) )
    return  map(lambda x: tupleElement(x), carray.tolist())


# associate an list order to each element in the array
def  tupleArrayOrderList( arr ):
    size = multiply.reduce( arr.shape )
    orderarr = arange(size)
    newarray = array([arr.ravel(),orderarr])
    carray = transpose(newarray)
    return  map(lambda x: tupleElement(x), carray.tolist())

# the list in extractOrderList must be in format: [(a1,r1),(a2,r2)...(an,rn)]
def extractOrderList ( lst ):
    arrlist = transpose( array(lst) )
    return arrlist[1].tolist()

# select non zero grid points from an array
def  selectNonZeroGrids ( arr ):
    return nonzero( arr.ravel())

# associate an order list to an array to form a new array
def  tupleArrayOrder( arr ):
    dimensions = list(arr.shape)
    dimensions.append(2)
    lst = tupleArrayOrderList(arr)
    return  reshape( lst, dimensions)

###
# Function tupleArrayElement  : Tuple array elements
# Attention: these array must be of the same dimensions.
# It is you who are responsible for any failures due to
# improper function call
# 
def tupleArrayElement( arrays ):
    dimensions = list(arrays[1].shape)
    dimensions.append(len(arrays))
    # combined list
    clist = tupleArrayList( arrays )
    return  reshape( clist,dimensions)


###
# find those points that are adjactant with the seed element
# Typically, the list is a point list [ point1, point2, ... ]
# eg. [(3,4,5), (3,2,6), (5,2,1) ...]
#
# Input:  list ( tuple, or array), seed
# output: ( group, rest ), both group and rest are lists
#        
def findNeighbours ( lst, seed = None ):
    assert type(lst) in [ListType, TupleType, ArrayType]
    length = len(lst)
    if length == 0: return ([],[])
    arrlst = array(lst)

    if seed == None: firstEle = lst[0]
    else:  firstEle = seed
    size = len( firstEle )

    result = abs( arrlst - array(firstEle))
    compones = ones((size))
    compresult = less_equal ( result, compones )

    resultpositive = product(compresult,1)
    resultnegative = equal(resultpositive,0)
    selectindex = nonzero( resultpositive )
    nonselectindex = nonzero( resultnegative)

    #get and extract the adjactent elements
    #Attention:  array([0]) is FALSE condition !!!!!
    point_1s = take( arrlst, selectindex).tolist()
    point_rest = take(arrlst,nonselectindex).tolist()
    return (point_1s, point_rest)

###
# find a continous region starting from a seed point
# Attention: function below is not suitable for large
# groups since it use list to perform the task.
#
def findOneGroup ( lst, seed = None ):
    res = findNeighbours(lst, seed)
    neighbours = res[0]
    environ = res[1]

    # Below is a tricky loop
    for ele in neighbours:
        res2 = findNeighbours(environ, ele)
        neighbour2 = res2[0]
        environ = res2[1]
        length = len(neighbours)
        neighbours[length:] = neighbour2
    # trick again: return [(x,y,z) ...], instead of [[x,y,z] ...]
    group = map(tuple,neighbours)
    environment =  map(tuple, environ)
    return [group, environment]

###
# Clutering a list of points into groups baset upon their spacial
# location.  return [ group1, group2, ... ].  for each group, the
# data structure looks like [ (x1,y1,z1), (x2,y2,z2), ... ]
#
def findGroups ( lst ):
    groups = []
    res = findOneGroup(lst)
    grp = res[0]
    enviro = res[1]
    groups.append( grp )

    while enviro:
        res = findOneGroup( enviro)
        grp = res[0]
        enviro = res[1]
        groups.append( grp )
    return groups 


#####################################################################
# Class GridPointSet contains a set of grid points. Typically, this
# set is generated by AutoGrid search functions.
#
class GridPointSet(Set):
    def __init__(self, gridobj, pointset, compobj = None):
        self.GridObj = gridobj
        Set.__init__(self, pointset, compobj)
        self.viewer = None
        self.geom = None

    def _rc(self,objlst,func):
        return self.__class__(self.GridObj, objlst, func)

    def index2coordinate(self):
        # coor = ( index - centerIndex) * spacing + center
        CI =array(self.GridObj.shape)
        CI = (CI - 1)/2
        center = array(self.GridObj.CENTER)
        return (array(self.DataObj)-CI)*self.GridObj.SPACING+center

    # group grid points, loci is the miminum loci size
    def findGroups(self):
        return findGroups (self.DataObj)

    # color grids. color means "red, blue, yellow" or RGB color(,,)
    # self.color("red"); self.color((1,0,0))
    def color(self, color):
        colortable = {'GREEN':  ( 0.0, 1.0, 0.0),
                'BLUE' :  ( 0.0, 0.0, 1.0),
                'WHITE':  ( 1.0, 1.0, 1.0),
                'RED'  :  ( 1.0, 0.0, 0.0),
                'YELLOW': ( 1.0, 1.0, 0.0),
                'CYAN' :  ( 0.0, 1.0, 1.0),
                'MAGENTA':( 1.0, 0.0, 1.0),
                'BLACK' : ( 0.0, 0.0, 0.0) }
        if type(color) == StringType:
            colorname = string.upper(color)
            if colortable.has_key(colorname):
                color = colortable[colorname]
            else:
                raise ValueError('bad color name')
        else:
            assert type(color) == TupleType    
        self.geom.Set(materials=(color,), inheritMaterial=0)

    def colorByValue(self):
        from DejaVu import colorTool
        cmap = colorTool.RGBRamp()
        val = self.getValue()
        color  = colorTool.Map(val, cmap)
        self.geom.Set(materials=color, inheritMaterial=0)

    def  getValue(self):
        lst = self.GridObj.To1Ds(self.DataObj)
        return( take(self.GridObj.array.ravel(), lst) )

    def  display(self, viewer = None):
        from DejaVu.Spheres import Spheres
        from DejaVu import Viewer

        if viewer==None:
            raise None
        else:
            assert isinstance(viewer, Viewer) 
            self.viewer = viewer

        if not self.geom:
            pts = self.index2coordinate()
            self.geom = Spheres('GridPoints', centers = pts,
                radii = 0.2, protected=True)
            self.viewer.AddObject(self.geom)


#####################################################################
# In essence,  class Grid is an adaptor to Numeric Array so
# that user can manipulate Grid just like it's an array.
# 
class Grid:
    def __init__(self, data, typecode = None):
        if typecode == None:
            self.array = asarray(data)
        else:
            self.array = array(data, typecode)

        self.shape = self.array.shape
        self.base = self._base()
        self.flat = self.array.ravel()
        self.min = minimum.reduce(self.array.ravel())
        self.max = maximum.reduce(self.array.ravel())
        self.typecode = self.array.dtype.char
        self.name = string.split(str(self.__class__))[0]
        # data below are for viewer
        self.viewer = None
        self.geom = None
        if not hasattr(self, 'SPACING'): self.SPACING=1.0
        if not hasattr(self, 'CENTER'): self.CENTER=(0.,0.,0.)


    def doSlice(self, isovar=0, timestep=0, axis='x', sliceNum=10):
        #in this case have to recalculate self.the_data
        #from swig import swig
        if not hasattr(self, 'the_data'):
            self.initIsoContour(step=1)
        #sl = isocontour.getSlice(self.the_data, isovar, timestep, axis,sliceNum)
        #print sl.width
        #print sl.height
        #print sl.datatype
        #print sl.fdata
        #sld = swig.getfloatarray(sl.fdata,(sl.width,sl.height))
        sld = isocontour.getSliceArray(self.the_data, isovar,
                           timestep, axis,sliceNum)
        #print sld.shape
        #return sl,sld
        return sld

    def doSlice2(self, isovar=0, timestep=0, axis='x', sliceNum=10):
        if not hasattr(self, 'da'):
            sh = (1,1,self.shape[0],self.shape[1],self.shape[2])
            self.da = zeros(sh).astype('f')
            self.da[0][0] = array(reshape(swapaxes(self.array,0,2),self.shape)).astype('f')
        d = swapaxes(self.da, 2, 4)
        if axis=='x':
            sld = array(transpose(d[isovar,timestep,sliceNum]))
        elif axis=='y':
            sld = array(transpose(d[isovar,timestep,:,sliceNum]))
        elif axis=='z':
            sld = array(transpose(d[isovar,timestep,:,:,sliceNum]))
        return sld.shape, sld

    def buildSliceVertices(self, width, height, axis,  sliceNum):
        cen = array(self.CENTER).astype('f')
        dim = array(self.NELEMENTS).astype('f')
        span = array(self.SPACING).astype('f')
        orig = cen -((dim-1)/2)*span

        #NB:
        #for x-perpendicular slice, 
        #coords for y and z corners are origin PLUS whole extent
        #for x-perpendicular slice, 
        #coord for x corners is origin +sliceNum/totalNum * extent
        # for y- or z- perpendicular slice, 
        #coords found in same fashion
        nelements = array(self.NELEMENTS)
        nelements = nelements -1
        #NB: self.step is ALWAYS one for these slices
        extent = span*nelements
        axisList=['x','y','z']
        axisInd=axisList.index(axis)
        partialExtent=(float(sliceNum)/float(nelements[axisInd]))*extent
        self.pE=partialExtent
        #partialExtent = extent * (sliceNum/(height-1.))
        #NB the order of visiting the corner pts of slice are probably wrong...
        #keep order x->y->z->x
        #so that for each axis, next point has delta in next axis
        if axis == 'x':
            v = array([orig +  (partialExtent[0], 0, 0),
                orig + (partialExtent[0], extent[1],0),
                orig + (partialExtent[0], extent[1],extent[2]),
                orig + (partialExtent[0], 0,extent[2])
                ] )
        elif axis == 'y':
            v = array([
                orig +  (0,partialExtent[1],  0),
                ##orig + (extent[0], partialExtent[1], 0),
                orig + (0, partialExtent[1], extent[2]),
                orig + (extent[0], partialExtent[1], extent[2]),
                ##orig + (0, partialExtent[1], extent[2])
                orig + (extent[0], partialExtent[1], 0)
                 ] )
        elif axis == 'z':
            v = array([orig +  (0,0,partialExtent[2]),
                orig + (extent[0], 0, partialExtent[2]),
                orig + (extent[0], extent[1],partialExtent[2]),
                orig + (0, extent[1],  partialExtent[2])
                ] )
        return v

    def buildTextureCoords(self, width, height, axis, sliceNum):
        dim1=dim2=1
        while dim1<width: dim1 = dim1<<1
        while dim2<height: dim2 = dim2<<1
        maxI=float(width)/float(dim1)
        max2=float(height)/float(dim2)
        return ((0,0), (maxI,0), (maxI, max2), (0, max2))

    #def initIso2DContour(self, step=1):
        #notes from 6/30:
        #d = swapaxes(self.da, 2,4)
        #sld = array(transpose(d[0,0,30]))
        #sld.shape=(1,1,61,61)
        #first arg is slice data, then origin, then spacing of data...
        #data = isocontour.newDatasetRegFloat2D(sld,(0,0),(.1,.1))
        #isoc = isocontour.getContour2d(data,0,0,-.71)
        #center = array(self.CENTER).astype('f')
        #dim = array(self.shape).astype('f')
        #span = array(self.SPACING).astype('f')
        #orig = center - ((dim-1)/2)*span
        #nb: this is wrong->error message is that daSmallhas wrong shape...
        #self.the_data2D = isocontour.newDatasetRegFloat2D(self.daSmall[1:],
                #orig[:2].astype('f'), (span*step,)*2 )
        #self.info2D = isocontour.getDatasetInfo(self.the_data2D)

    def initIsoContour(self, step=3):
            
        self.step=step
        sh = (1,1,self.shape[0],self.shape[1],self.shape[2])
        self.da = zeros(sh).astype('f')
        self.da[0][0] = array( reshape( swapaxes( self.array, 0, 2), self.shape ) ).astype('f')
        #to gain control over sampling step(s)
        try:
            self.daSmall = array(self.da[:,:,::step[0],::step[1],::step[2]]).astype('f')
            stepthree=1
        except:
            self.daSmall = array(self.da[:,:,::step,::step,::step]).astype('f')
            stepthree=0
        center = array(self.CENTER).astype('f')
        dim = array(self.shape).astype('f')
        span = array(self.SPACING).astype('f')
        orig = center - ((dim-1)/2)*span
        #print 'span*step,)*3=', (span*step,)*3
        if stepthree:
            self.the_data = isocontour.newDatasetRegFloat3D(self.daSmall,
                orig.astype('f'), (span*step[0],span*step[1],span*step[2]) )
        else:
            self.the_data = isocontour.newDatasetRegFloat3D(self.daSmall,
                orig.astype('f'), (span*step,)*3 )
        self.info = isocontour.getDatasetInfo(self.the_data)

    #isovar is 0, timestep = 0
    def getIsoContour(self, val=-0.71):
        isoc = isocontour.getContour3d(self.the_data, 0, 0, val,
                                   isocontour.NO_COLOR_VARIABLE)
        vert = zeros((isoc.nvert,3)).astype('f')
        norm = zeros((isoc.nvert,3)).astype('f')
        col = zeros((isoc.nvert)).astype('f')
        tri = zeros((isoc.ntri,3)).astype('i')
        isocontour.getContour3dData(isoc, vert, norm, col, tri, 1)
        #print 'vert.shape=', vert.shape
        #print 'vert=', vert
        #if len(vert)<20:
            #print 'vert=', vert
        #else:
            #print 'vert[:3]=', vert[:3]
        #print 'tri.shape=', tri.shape
        #print 'tri[:3]=', tri[:3]
        #print 'col.shape=', col.shape
        #print 'col[:3]=', col[:3]
        return vert, norm, col, tri


        
    # calculate the base for each dimension, which will be used
    # when we convert linear index into an array index
    def _base(self):
        dimensions = self.shape
        base = []
        length = len(dimensions)
        for i in range(length):
            b = 1
            # base size = dimension[i+1]* ... * dimension[length]
            for j in range( i+1, length ):
                b = b*dimensions[j]
            base.append(b)
        return tuple(base)

    # convert an flat index into an array index. For example, for
    # array(3,2,4), the tenth element corresponds to (1,0,2). i.e.
    # (1* 8 + 0* 4 + 2* 1), (8,4,1) is the base for array(3,2,4)
    def To3D(self, index):
        res = []
        index = int(index)
        length = len(self.shape)
        base = self.base
        Index = []
        for i in range(length):
            xyz = index / base[i]
            index = index - xyz*base[i]
            Index.append(xyz)
        res.append(tuple(Index))
        return res

    # for the sake of efficiency, another similar functions
    # is also provided, which is a loop of 1DTo3D(...) 
    def To3Ds(self, indices):
        length = len(self.shape)
        base = self.base
        Indices = []
        for index in indices:
            index = int(index)
            Index = []
            for i in range(length):
                xyz = index / base[i]
                index = index - xyz*base[i]
                Index.append(xyz)
            Indices.append(tuple(Index))
        return Indices

    # Attention: the return index is an array, not a list
    def To1Ds(self, indices):
        length = len(self.shape)
        base = array(self.base)
        arrIndex = array(indices)
        return sum( arrIndex*base, -1)


    def __repr__(self):
        return self.name+repr(self.array.shape)

    def __array__(self,t=None):
        if t: return asarray(self.array,t)
        return asarray(self.array)
 
    # bugs found in float function
    #def __float__(self):
        #return float(asarray(self.array))

    # Grid get and set functions (both attribute and slices)
    def __len__(self): return len(self.array)

    def __getitem__(self, index): 
        return self._rc(self.array[index])

    def __getslice__(self, i, j): 
        return self._rc(self.array[i:j])

    def __setitem__(self, index, value): self.array[index] = \
        asarray(value,self.typecode)
    def __setslice__(self, i, j, value): self.array[i:j] = asarray(value)

    # Arithematic operation, add, sub, mul, div and the like
    def __abs__(self): return self._rc(absolute(self.array))
    def __neg__(self): return self._rc(-self.array)

    def __add__(self, other): 
        return self._rc(self.array+asarray(other))
    __radd__ = __add__

    def __sub__(self, other): 
        return self._rc(self.array-asarray(other))
    def __rsub__(self, other): 
        return self._rc(asarray(other)-self.array)

    def __mul__(self, other): 
        return self._rc(multiply(self.array,asarray(other)))
    __rmul__ = __mul__

    def __div__(self, other): 
        return self._rc(divide(self.array,asarray(other)))
    def __rdiv__(self, other): 
        return self._rc(divide(asarray(other),self.array))

    def __pow__(self,other): 
        return self._rc(power(self.array,asarray(other)))
    def __rpow__(self,other): 
        return self._rc(power(asarray(other),self.array))

    def __sqrt__(self): 
        return self._rc(sqrt(self.array))

    def tostring(self): return self.array.tostring()
    
    def byteswapped(self): return self._rc(self.array.byteswap())
    def astype(self,typecode): return self._rc(self.array.astype(typecode))
    def typecode(self): return self.array.dtype.char
    
    def itemsize(self): return  self.array.itemsize
    def iscontiguous(self): return self.array.flags.contiguous

    # Attention: the function below is very import, especially
    # for drived class. You could overload this function.
    def _rc(self, a):
        if len(shape(a)) == 0: return a
        else: return self.__class__(a)

    # An interface function to class GridPointSet
    def _GridPoint(self,index):
        return GridPointSet (self, self.To3D(index))
    
    def _GridPointSet(self, data):
               #return self.1DTo3Ds(data), 3d coordinate list
        return GridPointSet (self, self.To3Ds(data))
    
    def findMaxGrid(self):
        return self._GridPoint( argmax(self.array.ravel()))

    def findMaxValue(self):
        return max(self.array.ravel())
    
    def findMinGrid(self):
        return self._GridPoint( argmin(self.array.ravel()))

    def findMinValue(self):
        return min(self.array.ravel())

    def findTopGrids(self,n):
        sortarrIndex1D = argsort(self.array.ravel())
        return self._GridPointSet( sortarrIndex1D[-n:] )

    def findTopValues(self,n):
        sortarr1D = sort(self.array.ravel())
        return  sortarr1D[-n:]
    
    def findBottomGrids(self,n):
        sortarrIndex1D = argsort(self.array.ravel())
        return self._GridPointSet( sortarrIndex1D[:n] )

    def findBottomValues(self,n):
        sortarr1D = sort(self.array.ravel())
        return sortarr1D[:n]
    
    # find the grids which is above,equal ot below specified value
    def  _findGrid(self, arr):
        indices = nonzero(arr.ravel())
        return self._GridPointSet( indices)
    
    def  findAboveGrids(self,value):
        result = greater(self.array, value)
        return self._findGrid ( result )
    
    def  findAboveEqualGrids(self,value):
        result = greater_equal(self.array,value)
        return self._findGrid ( result )
    
    def  findBelowGrids(self,value):
        result = less(self.array,value)
        return self._findGrid ( result )
    
    def  findBelowEqualGrids(self,value):
        result = less_equal(self.array,value)
        return self._findGrid ( result )
    
    def  findBetweenGrids(self,low,hi):
        result= greater(self.array,low)*less(self.array,hi)
        return self._findGrid ( result )

    def  findBetweenEqualGrids(self,low,hi):
        result= greater_equal(self.array,low)*less_equal(self.array,hi)
        return self._findGrid ( result )

    # find the value which satisfying conditions. return list
    def  _findValue( self,arr):
        indices = nonzero(arr.ravel())
        result = take(self.array.ravel(), indices)
        return result.tolist()

    def  findAboveValues(self,value):
        result = greater(self.array, value)
        return self._findValue ( result )
    
    def  findAboveEqualValues(self,value):
        result = greater_equal(self.array,value)
        return self._findValue ( result )
    
    def  findBelowValues(self,value):
        result = less(self.array,value)
        return self._findValue ( result )
    
    def  findBelowEqualValues(self,value):
        result = less_equal(self.array,value)
        return self._findValue( result )
    
    def  findBetweenValues(self,low,hi):
        result= greater(self.array,low)*less(self.array,hi)
        return self._findValue ( result )

    def  findBetweenEqualValues(self,low,hi):
        result= greater_equal(self.array,low)*less_equal(self.array,hi)
        return self._findValue ( result )

    # find order (or index) of a value in a grid object
    def  findOrder(self, value):
        sortIndex = argsort(self.array.ravel())
        length = len(sortIndex)
        begin = 0
        end = length -1

        # initial comparision
        MIN = self.array.flat[sortIndex[0]]
        MAX = self.array.flat[sortIndex[-1]]
        if value <= MIN: return 0
        if value == MAX: return end
        if value > MAX: return length

        # determine the order of value
        middle = ( begin + end ) /2
        while begin < end:
            pos = sortIndex[middle]
            if self.array.flat[pos] == value:
                return middle
            elif  self.array.flat[pos] > value:
                end = middle
            else:
                begin = middle + 1
            middle = ( begin + end ) /2
        return  middle

    # get the value of the ith element 
    def get_ith_element ( self, i):
        sortIndex = argsort(self.array.ravel())
        return self.array.flat[ sortIndex[i] ]

    # statistical information on Grid values
    def findGridNumbers ( self, low, hi):
        result= greater_equal(self.array,low)*less(self.array,hi)
        return len(nonzero(result.ravel()))

    # call: (intervals, MIN, MAX, tick)
    def distribution(self,intervals = 100,MIN=None,MAX = None,tick =0):
        if MIN == None: MIN = self.findMinValue()
        if MAX == None: MAX = self.findMaxValue()
        step = ( MAX - MIN) / intervals
        varray1 = arange(intervals)* step + MIN
        varray2 = arange(1,intervals+1)* step + MIN
        result = map( self.findGridNumbers, varray1, varray2 )
        if tick == 0 :
            return  result
        else:
            return map(None, result, varray1,varray2)
    
    # display Gridbox
    def displayBox(self,viewer=None, materials=None):
        """Draws the Grid box"""
        from DejaVu.Box import Box
        from DejaVu.Viewer import Viewer
        #print 'materials = ', materials
        #if viewer==None:
        #    print "must specify viewer"
        #    return
        if hasattr(self, 'box'): 
            return
        sh=array(self.shape)
        sh2=(sh-1)/2
        pt1=(sh-1)/2*self.SPACING
        pt2=0.0-pt1
        if hasattr(self, 'GRID_DATA_FILE'):
            nstr=string.split(self.GRID_DATA_FILE,'.')[0]+'_box'
        else:
            nstr='box'
        if not materials:
            materials = ((0,0,1),(0,1,0),(0,0,1),(0,1,0),(1,0,0),(1,0,0),)
        #print 'calling Box constructor with materials = ', materials
        self.box=Box(nstr,cornerPoints=(pt2,pt1), materials=materials,
                     inheritMaterial=0, inheritLineWidth=0)
        if viewer != None : 
            viewer.AddObject(self.box)
        if hasattr(self, 'CENTER'):
            self.box.Set(center=self.CENTER)
        self.box.RedoDisplayList()

        
    def display(self, viewer=None):
        """Draws the Grid box"""
        from DejaVu.IndexedPolylines import IndexedPolylines
        from DejaVu import Viewer      
        if viewer==None:
            raise "viewer is None"
            #self.viewer = self.GetViewer()
        else:
            assert isinstance(viewer, Viewer)
            self.viewer = viewer

        if not self.geom:
            x, y, z = self.shape
            (rx,ry,rz)=( (x-1)/2 , (y-1)/2, (z-1)/2 )
            #self.corners = ((0,0,0), (x,0,0), (0, y, 0), (x,y,0),
                    #(0,0,z), (x,0,z), (0, y, z), (x,y,z))
            self.corners = ((-rx,ry,rz),(rx,ry,rz),(-rx,-ry,rz),
                    (rx,-ry,rz), (-rx,ry,-rz),(rx,ry,-rz),
                    (-rx,-ry,-rz), (rx,-ry,-rz))
            self.indices = ( (0,2,3,1), (1,3,7,5), (5,7,6,4),
                     (0,4,6,2), (0,1,5,4), (2,6,7,3) )
            self.geom = IndexedPolylines('Grid',
                             vertices = self.corners,
                             faces = self.indices, protected=True)
            self.viewer.AddObject(self.geom)

###################################################################

def ReadAutoGridMap(file):
    f = open(file, 'r')

    try:
        GRID_PARAMETER_FILE = string.split(f.readline())[1]
    except:
        GRID_PARAMETER_FILE = ''
    GRID_DATA_FILE = string.split(f.readline())[1]
    MACROMOLECULE = string.split(f.readline())[1]

    # spacing
    SPACING = float(string.split(f.readline())[1])

    # number of points and center
    (nx,ny,nz) = string.split(f.readline())[1:4]
    NELEMENTS = (nx,ny,nz) = (int(nx)+1, int(ny)+1, int(nz)+1)
    (cx,cy,cz) = string.split(f.readline())[1:4]
    CENTER = ( float(cx),float(cy), float(cz))

    # read grid points
    points = map( lambda x: float(x), f.readlines())
    TMPGRIDS = swapaxes(reshape( points,(nz,ny,nx)), 0, 2)
    GRIDS = array(TMPGRIDS)
    f.close()
    return (GRID_PARAMETER_FILE, GRID_DATA_FILE,MACROMOLECULE,
           SPACING, NELEMENTS, CENTER, GRIDS)

from Volume.IO.dxReader import ReadDX

class DX(Grid):
    def __init__(self, file, typecode = None,gui=None, viewer=None):
        
        # type - dependent initialization maybe unsafe
        # Obviously, only original AutoGrid Object has
        # additional attributes
        reader = ReadDX()
        grid = reader.read(file,True)
        #Grid.__init__(self, results[6], typecode)
        self.GRID_PARAMETER_FILE = file
        self.GRID_DATA_FILE = file
        self.MACROMOLECULE = None
        self.SPACING = grid.stepSize[0]
        self.NELEMENTS = grid.dimensions
        self.CENTER = grid.centerPoint()
        Grid.__init__(self, grid.data, typecode)
        self.gui=gui
        self.viewer=viewer
    
    
class AutoGrid(Grid):
    def __init__(self, data, typecode = None,gui=None, viewer=None):
        
        if ( type(data) == StringType):
            # type - dependent initialization maybe unsafe
            # Obviously, only original AutoGrid Object has
            # additional attributes
            results = ReadAutoGridMap(data)
            #Grid.__init__(self, results[6], typecode)
            self.GRID_PARAMETER_FILE = results[0]
            self.GRID_DATA_FILE = results[1]
            self.MACROMOLECULE = results[2]
            self.SPACING = results[3]
            self.NELEMENTS = results[4]
            self.CENTER = results[5]
            Grid.__init__(self, results[6], typecode)
            self.SPACING = results[3]
            self.CENTER = results[5]
            self.gui=gui
            self.viewer=viewer
        else:
            Grid.__init__(self, data, typecode)

    def index2coordinate(self, index):
        # coor = ( index - centerIndex) * spacing + center
        CI =array(self.shape)
        CI = (CI - 1)/2
        center = array(self.CENTER)
        return tuple ((array(index)-CI)*self.SPACING+center)

    def coordinate2index( self, coordinate):
        c = array(self.CENTER)
        CI =array(self.shape)
        CI = (CI - 1)/2
        return tuple( map(int,(array(coordinate)-c)/self.SPACING+CI) )
        
    def display(self, viewer=None):
        Grid.display(self,viewer=viewer)
        scale = self.SPACING
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glScalef( float(scale), float(scale), float(scale))
        center = array( self.CENTER ) / scale
        GL.glTranslatef(float(center[0]), float(center[1]), float(center[2]))
        GL.glMultMatrixf(self.geom.Matrix)
        self.geom.Matrix = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        self.geom.Matrix.shape = (16,)
        GL.glPopMatrix()



class AutoGridSurfaceGui:

    def __init__(self,grid,vf):
        self.grid=grid
        self.vf = vf
        self.master = None
        self.vVar = None
        self.isovalue = None				
        self.setVar = None
        self.renderModeVar = None
        self.boxvVar = None				
        if self.vf.hasGui:
            self.master=vf.GUI.ROOT
            #for Surface visibility:
            self.vVar=Tkinter.IntVar(self.master)
            self.vVar.set(0)
            #for isovalue
            self.isovalueVar=Tkinter.StringVar(self.master)
            self.isovalueVar.set('-0.071')
            #for sampling
            self.setVar=Tkinter.StringVar(self.master)
            ne=grid.NELEMENTS
            if ne[0]==ne[1]==ne[2]: 
                self.setVar.set(3)
            else: 
                self.setVar.set(1)
            #for rendermode
            self.renderModeVar=Tkinter.IntVar(self.master)
            #for box visibility
            self.boxvVar=Tkinter.IntVar(self.master)
        #for box 
        self.box=None
        self.oldVals=[]
        grid.color = self.getColor()
        grid.surfaceGUI=self
        #keep a list of entry widgets to forget for cleanup
        self.entry_widgets = []

    def delete_all_widgets(self, event=None):
        for widget in self.entry_widgets:
            widget.grid_forget()

    def initColorVars(self):
        self.colorVars={}
        keyList=['C','N','n','O','S','H','A','f','c','b','I','F','M','X','e','NA','OA','SA','HD']
        colorList=[((1,1,1),),((0,0,1),),((0,.2,1),),((1,0,0),),((1,1,0),),
            ((0,1.0,1.0),),((0,1,0),),((0,.5,.5,),),((0.5,0.5,0,),),
            ((.5,0,.5,),),((.2,.2,.6,),),((.6,.4,0),),((0.2,1,0.2),),
            ((0.2,0.2,1),),((0.1,0.1,0.1),), ((0,0,1),), ((1,0,0),),((1,1,0),),((0,1,1),)]
        for i in range(len(keyList)):
            self.colorVars[keyList[i]]=colorList[i]

    def getColor(self):
        if not hasattr(self,'colorVars'): self.initColorVars()
        if self.grid.atType in self.colorVars.keys():
            return self.colorVars[self.grid.atType]
        else:
            return ((1,1,1),)

    def makeIfdEntry(self,ifd,bButtons,box=1,visibility=1,set=1,slider=1,rendermode=1):
        #NB: it could be more flexible if other functions +/or gridcfgs etc passed
        
        if not hasattr(ifd,'form'):
            t="Error: form not initialized"
            self.vf.warningMsg(t, title="AutoGridSurfaceGui WARNING")
            return
        form=ifd.form
        #before making new entries, forget the bottom ones:
        for item in bButtons:
            ifd.entryByName[item]['widget'].grid_forget()
        columnctr=0
        gridname = os.path.basename(self.grid.name)
        if visibility:
            entry={'name':'%sVisBut'%self.grid.name,
                'widgetType':Tkinter.Checkbutton,
                'text':gridname,
                'variable':self.vVar,
                'gridcfg':{'sticky':Tkinter.W},
                'command': self.changeVisibility}
            ifd.entryByName[entry['name']]=entry
            form.addEntry(entry)
            columnctr=columnctr+1
            self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])
        if set:
            entry={'name':'%ssetEnt'%self.grid.name,
                   'widgetType':Tkinter.Entry,
                   'wcfg':{'width':5,
                       'textvariable':self.setVar},
                   'gridcfg':{'sticky':Tkinter.W,'row':-1,
                      'column':1}}
##              entry={'name':'%ssetEnt'%self.grid.name,
##                  'widgetType':Tkinter.Entry,
##                  'wcfg':{'width':5},
##                  'textvariable':self.setVar,
##                      'gridcfg':{'sticky':Tkinter.W,'row':-1,'column':1}}
                #'commandArgs':form,
                #'command': self.updateSetVal}
            form.addEntry(entry)
            ifd.entryByName[entry['name']]=entry
            self.setWidget=ifd.entryByName[entry['name']]['widget']
            ###setting command and commandArgs in entry didn't work!!!?!!!
            self.setWidget.bind('<Return>',self.updateSetVal)
            #add to list to delete:
            self.entry_widgets.append(self.setWidget)
            self.form=form
            columnctr=columnctr+1
        if slider:
            if self.grid.atType in ['z', 'Z']:
                minval = self.grid.min
                maxval = self.grid.max
            elif self.grid.atType!='e':
                minval = self.grid.min
                if minval<0:
                    maxval = -minval
                elif minval<1:
                    maxval = 2.
                else:
                    maxval=2.*minval
            else:
                minval = -3.0
                maxval = 3.0
                
            ##  entry = {'name':'%sSlider'%self.grid.name,
##                  'widgetType':ExtendedSlider,
##                  'command': self.CallBack,
##                  'type':float,
##                  'wcfg':{'label': " ",'minval':minval,'immediate':1,
##                  'maxval':maxval,'init':-0.071, 'sd':'right'},
##                  'gridcfg':{'sticky':Tkinter.W,'row':-1,
##                  'column':2, 'columnspan':2} }
            
            entry = {'name':'%sSlider'%self.grid.name,
                    'widgetType': ExtendedSliderWidget,
                    'wcfg':{'label':" ",
                    'minval':minval, 'maxval':maxval,
                    'immediate':1,
                    'init':-0.071,
                    'labelsCursorFormat':'%4.4f',
                    'command':self.CallBack,
                    'sliderType':'float',
                    'entrypackcfg':{'side':'right'}},
                    'gridcfg':{'sticky':Tkinter.W, 
                    'row':-1, 'column':2,'columnspan':2}}
            form.addEntry(entry)
            ifd.entryByName[entry['name']]=entry
            newslider=ifd.entryByName[entry['name']]['widget']
            self.slider=newslider
            self.entry_widgets.append(self.slider)
            columnctr=columnctr+2
        if rendermode:
            entry={'name':'%sRenderBut'%self.grid.name,
                'widgetType':Tkinter.Checkbutton,
                'text':'LINE',
                'variable':self.renderModeVar,
                'gridcfg':{'sticky':Tkinter.W,'row':-1,'column':4},
                'command': CallBackFunction(self.changeRenderMode,ifd)}
            ifd.entryByName[entry['name']]=entry
            form.addEntry(entry)
            self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])
            columnctr=columnctr+1
        if box:
            #print 'called grid.displayBox with materials= blue'
            
            
            self.grid.displayBox(self.vf.GUI.VIEWER, materials=((0.,0.,1.),))
            self.boxvVar.set(1)
            entry={'name':'%sBoxBut'%self.grid.name,
                'widgetType':Tkinter.Checkbutton,
                'text':'ShowBox',
                'variable':self.boxvVar,
                'gridcfg':{'sticky':Tkinter.W,'row':-1,'column':5},
                'command': self.changeBox}
            ifd.entryByName[entry['name']]=entry
            form.addEntry(entry)
            self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])
            columnctr=columnctr+1
        rowctr=2
        for item in bButtons:
            #better to increment row and column + use newvalues here
            #THIS ISN'T GENERAL!!
            gridcfg=ifd.entryByName[item]['gridcfg']
            gridcfg['row']=gridcfg['row']+rowctr
            gridcfg['column']=gridcfg['column']
            gridcfg=ifd.entryByName[item]['widget'].grid(gridcfg)
        #4/1: should srf be displayed when added (?)
        self.vVar.set(1)
        self.changeVisibility()


    def changeVisibility(self,event=None):
        if self.vVar.get():
            if self.grid.srf:
                self.grid.srf.Set(visible=1)
            else:
                self.getMap()
                self.grid.srf.Set(visible=1)
        else:
            if self.grid.srf: self.grid.srf.Set(visible=0)
        self.vf.GUI.VIEWER.Redraw()
            

    def changeBox(self,event=None):
        if self.boxvVar.get():
            self.grid.box.Set(visible=1)
        else:
            self.grid.box.Set(visible=0)
        self.vf.GUI.VIEWER.Redraw()


    def changeRenderMode(self,ifd,event=None):
        if not self.grid.srf:
            #in this case build the surface AND display it
            self.getMap()    
            #also need to set visibility check button
            self.vVar.set(1)
        if self.renderModeVar.get():
            self.grid.srf.Set(frontPolyMode=GL.GL_LINE)
            #self.grid.srf.RenderMode(mode=GL.GL_LINE,face=GL.GL_FRONT)
            ifd.entryByName['%sRenderBut'%self.grid.name]['widget'].config(text='LINE')
        else:
            self.grid.srf.Set(frontPolyMode=GL.GL_FILL)
            #self.grid.srf.RenderMode(mode=GL.GL_FILL,face=GL.GL_FRONT)
            ifd.entryByName['%sRenderBut'%self.grid.name]['widget'].config(text='FILL')
        ifd.form.lift()
        self.vf.GUI.VIEWER.Redraw()
            

    def CallBack(self,event=None):
        val=round(self.slider.get(),3)
        self.isovalueVar.set(str(val))
        g=self.grid
        if not hasattr(g, 'the_data'):
            atSet=int(self.setVar.get())
            g.initIsoContour(atSet)
        g.vert,g.norm,g.col,g.tri=g.getIsoContour(val)
        if g.srf: g.srf.Set(vertices=g.vert,vnormals=g.norm,faces=g.tri)
        self.vf.GUI.VIEWER.Redraw()

    def updateIsoVal(self,isoval,atSet=1):
        #val=round(self.slider.get(),3)
        self.isovalueVar = isoval#.set(str(val))
        g=self.grid
        if not hasattr(g, 'the_data'):
            g.initIsoContour(atSet)
        g.vert,g.norm,g.col,g.tri=g.getIsoContour(isoval)
        if g.srf: g.srf.Set(vertices=g.vert,vnormals=g.norm,faces=g.tri)
        if self.vf.hasGui :
            self.vf.GUI.VIEWER.Redraw()

    def updateSetVal(self, event=None):
        val=event.widget.get()
        intVal=int(val)
        if intVal>5 or intVal<1:
            self.vf.warningMsg('Only1,2,3,4 or 5 valid', title="AutoGridSurfaceGui WARNING:")
            ne=self.grid.NELEMENTS
            if ne[0]==ne[1]==ne[2]: 
                self.setVar.set(3)
            else: 
                self.setVar.set(1)
        self.getMap()


    def initMap(self):
        grid=self.grid
        atType=grid.atType
        atSet=1
        atIsovalue=-0.07			
        if self.vf.hasGui:
            atSet=int(self.setVar.get())
            atIsovalue=float(self.isovalueVar.get())
        atColor=grid.color
        var=self.vVar

        grid.initIsoContour(atSet)
        vert,norm,col,tri=grid.getIsoContour(atIsovalue)
        grid.srf=IndexedPolygons('iso_%s'%grid.name,vertices=vert,
            vnormals=norm, faces=tri, materials=atColor, inheritMaterial=0,
            inheritLineWidth=0, protected=True,)

        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
            grid.srf.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)

        #THINK ABOUT THIS!!!
        grid.srf.pickable=1
        #grid.srf.pickable=0
        grid.srf.atType=atType
        grid.srf.Set(frontPolyMode=GL.GL_LINE)
        #grid.srf.RenderMode(mode=GL.GL_LINE,face=GL.GL_FRONT)
        grid.srf.grid=grid
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(grid.srf)
            #is this necessary???
            self.renderModeVar.set(1)
            grid.srf.RedoDisplayList()
        #checkOnAddMoleculeRNC(self.vf)
        #oldVals keys are types, values lists
        self.oldVals=[atSet,atIsovalue,atColor]
        #grid.srf.RedoDisplayList()

    def updateMap(self):
        grid=self.grid
        atType=grid.atType
        atSet=1
        atIsovalue=-0.07
        if self.vf.hasGui:		
            atSet=int(self.setVar.get())
            atIsovalue=float(self.isovalueVar.get())
        atColor=grid.color
        var=self.vVar

        grid.srf.pickable=1
        #grid.srf.pickable=0
        if self.vf.hasGui: 
		   v=var.get()
        else : 
           v=1				   
        if not v:
            grid.srf.Set(visible=0)
        else:
            grid.srf.Set(visible=1)
            #do possible update here:
            #CHECK FOR CHANGES?
            if atSet!=self.oldVals[0]:
                grid.initIsoContour(atSet)
                self.oldVals[0]=atSet
                grid.vert,grid.norm,grid.col,grid.tri=grid.getIsoContour(atIsovalue)
                grid.srf.Set(vertices=grid.vert, vnormals=grid.norm,
                             faces=grid.tri, materials=atColor, visible=1,
                             inheritMaterial=0)
            elif atIsovalue!=self.oldVals[1]:
                self.oldVals[1]=atIsovalue
                grid.vert,grid.norm,grid.col,grid.tri=grid.getIsoContour(atIsovalue)
                grid.srf.Set(vertices=grid.vert, vnormals=grid.norm,
                             faces=grid.tri, materials=atColor,visible=1,
                             inheritMaterial=0)
            elif atColor!=self.oldVals[2]:
                grid.srf.Set(materials=atColor, visible=1, inheritMaterial=0)
            self.oldVals=[atSet,atIsovalue,atColor]
        if self.vf.hasGui:
            grid.srf.RedoDisplayList()

    def getMap(self):
        grid=self.grid
        atType=grid.atType
        if self.vf.hasGui:
            atSet=int(self.setVar.get())
            atIsovalue=float(self.isovalueVar.get())
        atColor=grid.color
        var=self.vVar

        if not grid.srf:
            #this is initialization
            self.initMap()
        else:
            #grid has been initialized:
            #update visibility,atSet,atIsovalue,atColor
            self.updateMap()
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.Redraw()


class AutoGridSliceGui:

    def __init__(self,grid,vf):
        self.grd=grid
        self.vf = vf
        self.master=vf.GUI.ROOT
        if not hasattr(self.grd,'initminmax'):
            self.grd.initminmax = 0
        self.grd.slices={}
        self.grd.slices['x']=[]
        self.grd.slices['y']=[]
        self.grd.slices['z']=[]
        self.axisVars={}
        self.vVars={}
        self.scaleWidgets={}
        grid.sliceGUI=self
        self.axisList=['x','y','z']
        #for now, self.grd.step has to be 1
        assert hasattr(self.grd, 'srf')
        assert hasattr(self.grd, 'surfaceGUI')
        if self.grd.step!=1:
            self.grd.surfaceGUI.setVar.set('1')
            self.grd.surfaceGUI.updateMap()
        self.entry_widgets = []
            
    

    def delete_all_widgets(self, event=None):
        for widget in self.entry_widgets:
            widget.grid_forget()


    def makeIfdEntry(self,axis,ifd,bButtons,visibility=1,scaleWidget=1):
        #NB: it could be more flexible if other functions +/or gridcfgs etc passed
        if not hasattr(ifd,'form'):
            t="Error: form not initialized"
            self.vf.warningMsg(t, title="AutoGridSliceGui WARNING:")
            return

        form=ifd.form
        snum=len(self.grd.slices[axis])
        #on first call: snum=0
        key = axis + str(snum)
        gridname = os.path.basename(self.grd.name)
        extKey=gridname+'_'+key
        self.vVars[key]=Tkinter.IntVar(self.master)
        self.vVars[key].set(1)
        if not hasattr(self.grd, 'widgets'):
            self.grd.widgets=[]
            self.grd.gcfgs=[]
        #before making new entries, forget the bottom ones:
        for itemList in bButtons:
            for item in itemList: 
                ifd.entryByName[item]['widget'].grid_forget()
            
        columnctr=0
        if visibility:
            #this needs local key for ifd name + extKey for text
            entry={'name':'%sVisBut'%key,
                'widgetType':Tkinter.Checkbutton,
                'text':extKey,
                'variable':self.vVars[key],
                'gridcfg':{'sticky':Tkinter.W},
                'command': CallBackFunction(self.changeSliceVisibility,extKey,form)}
            ifd.entryByName[entry['name']]=entry
            form.addEntry(entry)
            self.grd.widgets.append(ifd.entryByName[entry['name']]['widget'])
            self.grd.gcfgs.append(ifd.entryByName[entry['name']]['gridcfg'])
            self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])
            columnctr=columnctr+1
        axisIndex=self.axisList.index(axis)
        tcolors=['red','green','blue']
        minval = 0
        maxval = (self.grd.NELEMENTS[axisIndex]-1)/(self.grd.step*1.0)
        entry={'name':'%sScale'%key,
            'widgetType':Tkinter.Scale,
            'wcfg':{'from':minval,'orient':'horizontal','sliderrelief':'sunken',
                'sliderlength':'6','length':'2.5i',
                'tickinterval':maxval/2,
                'troughcolor':tcolors[axisIndex],
                'to':maxval,'command':CallBackFunction(self.CallBack,extKey,axis)},
            'gridcfg':{'sticky':'we','row':-1,'column':1, 'columnspan':4} }
        form.addEntry(entry)
        ifd.entryByName[entry['name']]=entry
        newscale=ifd.entryByName[entry['name']]['widget']
        newscale.grd=self.grd
        newscale.axis=axis
        newscale.nm=snum
        newscale.ky=key
        self.grd.widgets.append(ifd.entryByName[entry['name']]['widget'])
        self.grd.gcfgs.append(ifd.entryByName[entry['name']]['gridcfg'])
        self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])
        self.scaleWidgets[key]=newscale


        if not self.grd.initminmax:
            #add the label entry for max/min of grd
            #add two entries for max and min of colormap of slices here
            labStr = gridname[:-4] + '_colormap\nmin/max:'
            entry={'name':'%sLab'%gridname,
                'widgetType':Tkinter.Label,
                'wcfg':{ 'text':labStr },
                'gridcfg':{'sticky':'w'} }
            form.addEntry(entry)
            ifd.entryByName[entry['name']]=entry
            newentry=ifd.entryByName[entry['name']]['widget']
            self.entry_widgets.append(newentry)
            newentry.grd=self.grd
            self.grd.widgets.append(newentry)
            self.grd.gcfgs.append(ifd.entryByName[entry['name']]['gridcfg'])
            self.grd.cmapMin = self.grd.min
            if self.grd.max > 0.0:
                self.grd.cmapMax = 0.0
            else:
                self.grd.cmapMax = self.grd.max

            newMinVar = Tkinter.StringVar();
            newMinVar.set(self.grd.cmapMin)
            entry={'name':'%sMinEnt'%key,
                'widgetType':Tkinter.Entry,
                'wcfg':{'textvariable':newMinVar,
                'width':6,
                },
                'gridcfg':{'sticky':'we','row':-1,'column':1} }
            form.addEntry(entry)
            ifd.entryByName[entry['name']]=entry
            newentry=ifd.entryByName[entry['name']]['widget']
            newentry.bind('<Return>', CallBackFunction(self.setMin, newMinVar))
            newentry.grd=self.grd
            self.grd.widgets.append(ifd.entryByName[entry['name']]['widget'])
            self.grd.gcfgs.append(ifd.entryByName[entry['name']]['gridcfg'])
            self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])

            newMaxVar = Tkinter.StringVar();
            newMaxVar.set(self.grd.cmapMax)
            entry={'name':'%sMaxEnt'%key,
                'widgetType':Tkinter.Entry,
                'wcfg':{'textvariable':newMaxVar,
                'width':6,
                },
                'gridcfg':{'sticky':'w','row':-1,'column':2} }
            form.addEntry(entry)
            ifd.entryByName[entry['name']]=entry
            newentry=ifd.entryByName[entry['name']]['widget']
            newentry.bind('<Return>', CallBackFunction(self.setMax, newMaxVar))
            newentry.grd=self.grd
            self.grd.widgets.append(ifd.entryByName[entry['name']]['widget'])
            self.grd.gcfgs.append(ifd.entryByName[entry['name']]['gridcfg'])
            self.entry_widgets.append(ifd.entryByName[entry['name']]['widget'])
            self.grd.initminmax = 1

        columnctr=columnctr+1
        rowctr=2
        for itemList in bButtons:
            #better to increment row and column + use newvalues here
            #THIS ISN'T GENERAL!!
            columnctr=0
            for item in itemList:
                gridcfg=ifd.entryByName[item]['gridcfg']
                gridcfg['row']=gridcfg['row']+rowctr+2
                gridcfg['column']=columnctr
                #gridcfg['column']=gridcfg['column']+columnctr
                gridcfg=ifd.entryByName[item]['widget'].grid(gridcfg)
                columnctr=columnctr+1
            rowctr=rowctr+1
        form.lift()
        

    def setMin(self, var, event=None):
        self.grd.cmapMin = float(var.get())


    def setMax(self, var, event=None):
        self.grd.cmapMax = float(var.get())


    def changeSliceVisibility(self, extKey, event=None):
        key=string.split(extKey,'_')[-1]
        axis=key[0]
        num=int(key[1:])
        if self.vVars[key].get():
            #slices entries are geometries:
            if self.grd.slices[axis][num]:
                self.grd.slices[axis][num].Set(visible=1)
            else:
                newVal = int(self.scaleWidgets[key].get())
                self.addSlice(axis)
        else:
            if self.grd.slices[axis][num]: 
                self.grd.slices[axis][num].Set(visible=0)
        self.vf.GUI.VIEWER.Redraw()


    def CallBack(self, extKey, axis, event=None):
        #print "plist=",self.grd.slices[axis]
        if not len(self.grd.slices[axis]):return
        key=string.split(extKey,'_')[-1]
        num=int(key[1:])
        if len(self.grd.slices[axis])<num: return
        scale=self.scaleWidgets[key]
        val=scale.get()
        ival = int(val)
        #fix this someday
        #ival = int(math.floor(ival/self.grd.step))
        g=scale.grd
        axis= scale.axis
        plist=self.grd.slices[axis]
        #if just built scale, don't try to move it
        if scale.nm >= len(plist): return
        p=plist[scale.nm]
        self.moveSlice(axis,p,ival)
        self.vf.GUI.VIEWER.Redraw()


    def addSlice(self,axis):
        snum = len(self.grd.slices[axis])
        key = axis + str(snum)
        extKey = self.grd.name+'_'+key
        ###THIS IS THE CHANGE!
        min = self.grd.cmapMin
        max = self.grd.cmapMax
        #if self.grd.min<-3: min=-3
        #else: min=self.grd.min
        #if self.grd.max>0:max=0
        #else:max=self.grd.max
        ind = self.axisList.index(axis)    
        pat = patternList[2+ind]
        #all slices are initialized at len(slices) (?)
        v,tx,t2 = self.calcSlice(axis,snum,min,max)
        #p = IndexedPolygons(extKey, vertices=v, faces=((0,1,2,3),),
        #                    textureCoords=tx, inheritMaterial=0,
        #                    culling=GL.GL_NONE)
        p = IndexedPolygons(extKey, protected=True,)
        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
            p.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
        p.Set(vertices=v, faces=((0,1,2,3),), 
                texture=t2, textureCoords=tx, 
                inheritMaterial=0, culling=GL.GL_NONE, blendFunctions=(1,1),
                frontPolyMode=GL.GL_FILL, backPolyMode=GL.GL_FILL)
        #p.RenderMode(GL.GL_FILL,face=GL.GL_BACK)
        #p.RenderMode(GL.GL_FILL,face=GL.GL_FRONT)
        self.vf.GUI.VIEWER.AddObject(p)
        #p.texture = t2
        p.polygonstipple.Set(pattern=pat)
        p.Set(stipplePolygons=1)
        self.grd.slices[axis].append(p)
        p.num = snum
        p.scaleWidget = self.scaleWidgets[key]
        p.RedoDisplayList()
        self.vf.GUI.VIEWER.Redraw()
        
    def calcSlice(self,axis,newVal,min,max):
        # MS getSliceArray
##          sl,sld=self.grd.doSlice(0,0,axis,newVal)
##          width=sl.width
##          height=sl.height
        sld = self.grd.doSlice(0,0,axis,newVal)
        width = sld.shape[0]
        height = sld.shape[1]
        v = self.grd.buildSliceVertices(width,height,axis,newVal)
        #build the image
        val = minimum(sld.ravel(),0)
        cmap = RGBRamp()
        #FIX THIS
        tex2Dimage = array2DToImage(val,cmap,width,height,mini=min,maxi=max)
        dim1 = dim2 = 1
        while dim1<width: dim1=dim1<<1
        while dim2<height: dim2=dim2<<1
        t2 = Texture.Texture()
        t2.Set(enable=1, image=tex2Dimage, auto=0)
        #t2=Texture.Texture(enable=1,image=tex2Dimage, auto=0)
        t2.width = dim1
        t2.height = dim2
        tx = self.grd.buildTextureCoords(width,height,axis,newVal)
        return v, tx, t2

    def moveSlice(self, axis, p, newVal):
        ##THIS IS CHANGE #@
        min = self.grd.cmapMin
        max = self.grd.cmapMax
        #if self.grd.min<-3: min=-3
        #else: min=self.grd.min
        #if self.grd.max>0:max=0
        #else:max=self.grd.max
        v, tx, t2=self.calcSlice(axis,newVal,min,max)
        #p=self.grd.slices[axis][num]
        p.Set(vertices=v, textureCoords=tx)
        p.texture=t2
        ind=self.axisList.index(axis)
        pat= patternList[2+ind]
        p.polygonstipple.Set(pattern=pat)
        p.RedoDisplayList()

