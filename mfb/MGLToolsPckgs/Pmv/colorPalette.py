########################################################################
#
# Date: April 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#########################################################################
#
# $Header$
#
# $Id$
#


from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI

#MS added this to get rid of GUI when noGUI is specified
class ColorPaletteNG(ColorMap):
    FLOAT = 0

    def __init__(self, name, colorDict={}, readonly=0, colortype=None,
                 info='', sortedkeys=None, lookupMember=None):

        if len(colorDict) > 0:
            if sortedkeys is None:
                labels = colorDict.keys()
                values = colorDict.values()
            else:
                labels = sortedkeys
                values = []
                for label in labels:
                    values.append(colorDict[label])
        else:
            labels = None
            values = None
        print values
        ColorMap.__init__(self, name=name, ramp=values, labels=labels)

        self.readonly = readonly
        self.info = info
        #self.viewer = None
        self.sortedkeys = sortedkeys
        if colortype is None:
            self.colortype = self.FLOAT
        self.lookupMember = lookupMember

    def _lookup(self, name):
        #print "_lookup", name, type(name)
        try:
            col = ColorMap._lookup(self, name)
            if len(col) == 4:
                return col[:3]
            else:
                return col
        except:
            return (0., 1., 0.)


    def lookup(self, objects):
        # Maybe should try that first in case all the objects don't have the
        # lookup member
        names = objects.getAll(self.lookupMember)
        return map( self._lookup, names)


class ColorPaletteFunctionNG(ColorPaletteNG):

    def __init__(self, name, colorDict={}, readonly=0, colortype=None,
                 info='', sortedkeys=None, lookupFunction = None):
        """ lookupFunction : needs to be function or a lambda function"""
        ColorPaletteNG.__init__(self, name, colorDict, readonly,colortype,
                               info, sortedkeys)
        from types import FunctionType
        if not type(lookupFunction) is FunctionType:
            self.lookupFunction = None

        self.lookupFunction = lookupFunction
                     
          
    def lookup(self, objects):
        # maybe should do that in a try to catch the exception in case it
        # doesnt work
        names = map(self.lookupFunction, objects)
        return map(self._lookup, names)


class ColorPalette(ColorMapGUI):
    
    FLOAT = 0
    INT = 1

    def __init__(self, name, colorDict={}, readonly=0, colortype=None,
                 info='', sortedkeys=None, lookupMember=None):

        if len(colorDict) > 0:
            if sortedkeys is None:
                labels = colorDict.keys()
                values = colorDict.values()
            else:
                labels = sortedkeys
                values = []
                for label in labels:
                    values.append(colorDict[label])
        else:
            labels = None
            values = None

        
        ColorMapGUI.__init__(self, name=name, ramp=values, labels=labels, show=False,
                             numOfBlockedLabels = len(labels) )
        self.readonly = readonly
        self.info = info
        #self.viewer = None
        self.sortedkeys = sortedkeys
        if colortype is None:
            self.colortype = self.FLOAT
        self.lookupMember = lookupMember


    def _lookup(self, name):
        #print "_lookup", name, type(name)
        try:
            col = ColorMap._lookup(self, name)
            if len(col) == 4:
                return col[:3]
            else:
                return col
        except:
            return (0., 1., 0.)


    def lookup(self, objects):
        # Maybe should try that first in case all the objects don't have the
        # lookup member
        names = objects.getAll(self.lookupMember)
        return map( self._lookup, names)
    
    def undisplay(self, *args, **kw):
        pass


    def copy(self):
        """make a deep copy of a palette"""
        import copy
        c = copy.copy(self)
        c.readonly = 0
        c.ramp = copy.deepcopy(self.ramp)
        c.labels = copy.deepcopy(self.labels)
        return c


class ColorPaletteFunction(ColorPalette):

    def __init__(self, name, colorDict={}, readonly=0, colortype=None,
                 info='', sortedkeys=None, lookupFunction = None):
        """ lookupFunction : needs to be function or a lambda function"""
        ColorPalette.__init__(self, name, colorDict, readonly,colortype,
                               info, sortedkeys)
        from types import FunctionType
        if not type(lookupFunction) is FunctionType:
            self.lookupFunction = None

        self.lookupFunction = lookupFunction
                     
          
    def lookup(self, objects):
        # maybe should do that in a try to catch the exception in case it
        # doesnt work
        names = map(self.lookupFunction, objects)
        return map(self._lookup, names)
