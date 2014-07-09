## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: April 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    sanner@scripps.edu
#    vareille@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
# revision:
#
#########################################################################
#
# $Header$
#
# $Id$
#

import Image
import numpy.oldnumeric as Numeric

from NetworkEditor.datatypes import AnyArrayType

class ViewerType(AnyArrayType):

    from DejaVu.Viewer import Viewer
    def __init__(self, name='viewer', datashape=None, color='yellow',
                 shape='rect', width=None, height=None, klass=Viewer):
        
        AnyArrayType.__init__(self, name=name, color=color, 
                              shape=shape, width=width, height=height, 
                              klass=klass, datashape=datashape)



class ColorMapType(AnyArrayType):

    from DejaVu.colorMap import ColorMap
    def __init__(self, name='ColorMapType', datashape=None, color='magenta',
                 shape='rect', width=None, height=None, klass=ColorMap):
        
        AnyArrayType.__init__(self, name=name, color=color, 
                              shape=shape, width=width, height=height, 
                              klass=klass, datashape=datashape)



class TextureType(AnyArrayType):

    from Image import Image
    def __init__(self, name='texture', datashape=None, color='#995699',
                 shape='rect', width=None, height=None, klass=None):

        AnyArrayType.__init__(self, name=name, color=color, 
                              shape=shape, width=width, height=height, 
                              klass=klass, datashape=datashape)

    def cast(self, data):
        """returns a success status (true, false) and the coerced data
"""
        if self['datashape'] is None:
            from DejaVu.colorMap import ColorMap            
            if isinstance(data, ColorMap):
                return True, data.ramp
        return False, None


class Common2d3dObjectType(AnyArrayType):

    from DejaVu.Common2d3dObject import Common2d3dObject
    def __init__(self, name='geomOrInsert2d', datashape=None, color='red',
                 shape='rect', width=None, height=None, klass=Common2d3dObject):
      
        AnyArrayType.__init__(self, name=name, color=color, 
                              shape=shape, width=width, height=height, 
                              klass=klass, datashape=datashape)


class Insert2dType(AnyArrayType):

    from DejaVu.Insert2d import Insert2d
    def __init__(self, name='insert2d', datashape=None, color='red',
                 shape='rect', width=None, height=None, klass=Insert2d):
      
        AnyArrayType.__init__(self, name=name, color=color, 
                              shape=shape, width=width, height=height, 
                              klass=klass, datashape=datashape)


class GeomType(AnyArrayType):

    from DejaVu.Geom import Geom
    def __init__(self, name='geom', datashape=None, color='red',
                 shape='rect', width=None, height=None, klass=Geom):
      
        AnyArrayType.__init__(self, name=name, color=color, 
                              shape=shape, width=width, height=height, 
                              klass=klass, datashape=datashape)


    def cast(self, data):
        """returns a success status (true, false) and the coerced data
"""
        from DejaVu.Insert2d import Insert2d
        if self['datashape'] is None: 
            if isinstance(data, Insert2d):
                return True, data
        else:
            lArray = Numeric.array(data)
            if lArray.size == 0:
                return False, None
            lArray0 = lArray.ravel()[0]
            while hasattr(lArray0,'shape'):
                lArray0 = lArray0.ravel()[0]
            if isinstance(lArray0, Insert2d):
                return True, lArray
        return False, None
