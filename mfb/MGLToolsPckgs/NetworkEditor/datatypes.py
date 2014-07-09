## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner, Daniel Stoffler
#
#       sanner@scripps.edu
#       stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler and TSRI
#
# Revision: Guillaume Vareille
#
#########################################################################

import types
import numpy.oldnumeric as Numeric
import warnings
import array   


class AnyArrayType(dict):
    """Base class for defining types of Ports which can handle single values
or arrays of arbitrary shape.

this class must be inherited only !!!! get inspired by class IntType below

the constructor arguments are:

    name: string used to identify an instance of a AnyArrayType object
          ex: float
          
          you can add the datashape to the name
          ex: float(0,>=3,4,0) defines a 4D array with constrains on the
            extent of each dimension. A value of 0 means there is not required extent 
          
Multi dimensional arrays can be specified by passing 
a datashape in parenthesis in the form of a string of comma separated 
expressions.  The number of expressions is the number of dimensions. 
Valid expressions are :
    0  : meaning there is no condition on this dimension.
        (in addition, the leading 0 dimensions are optional)
    x  : length of this dimension must be  x
    >x : length of this dimension must be > x
    <x : length of this dimension must be < x 
    >=x: length of this dimension must be >= x 
    <=x: length of this dimension must be <= x 

for instance a list of vertices can be represented by float(0,3)
    float: describe the smallest elementary datum (one coordinate).
           you can introduce your own elementary type 
           (generally inheriting basic types), this allow you to easily
           define color and shape for this type (see InstancematType below)
           
    3: because there are 3 coordinates per vertex.
    0: because we don't have any limitation on the number of vertices.
       It is a leading 0, therefore this dimension is optional
       (meaning: if you're passing a single vertex [x,y,z], 
       your are not oblige to put it in a list. 
       ex: you can give [x,y,z] or [[x,y,z]])
       
"""
    def __init__(self,
                 # used as a key the datatype manager
                 name='None',  
                 datashape=None,     # describe (0,>=3)
                 klass=None,         # class of Python object passing through port. 
                                     # This is used for data type propagation
                 dataDescr=None,     # string describing data in tool tip
                 color=None,      # color of port icon
                 shape='diamond',    # shape used for port icon
                 width=None, height=None, # width and height of port icon
                ):
        #import traceback;traceback.print_stack()
        #print "AnyArrayType __init__ name datashape", name, datashape

        self['name'] = name
        self['datashape'] = datashape
        self['class'] = klass
        self['dataDescr'] = dataDescr

        if color is None:
            color = 'white'
        self['color'] = color          # port icon color

        if shape is None:
            shape = self._shape(datashape)
        self['shape'] = shape          # port icon

        if width is None:
            width = 12
        self['width'] = width          # port icon width

        if height is None:
            if shape == 'circle' or shape == 'square':
                height = self['width']
            else:
                height = 8
        self['height'] = height        # port icon height

        # list of lambda functions used to check dimension of incoming data
        self.dimensionTest = []

        # compile dimension checking functions that will be used in validate
        if datashape is None:
            self.lenDimensionTest = 0 
        else:

            for dimlim in datashape[1:-1].split(','):
                # this case should be handled using >=1, i.e. required
                # dimension with no constriaint
                #if dimlim=='': # no restirction on this dimension
                #    self.dimensionTest.append( None )

                if dimlim.isdigit(): # we have a fixed extent for this dimension
                    if int(dimlim)!=0:
                        self.dimensionTest.append( lambda x: x==int(dimlim) )
                    else: # no restriction on this dimension
                        self.dimensionTest.append( None )
                else:
                    strg = ''
                    for c in dimlim:
                        if c in ['>', '<']:
                            strg += 'x '+c
                        else:
                            strg += c
                    self.dimensionTest.append( eval('lambda x: %s'%strg) )
        
            self.lenDimensionTest = len(self.dimensionTest)


    def validateDims(self, data):
        """data comes in as a numeric array, and returns True if required
shapes pass tests, returns False is tests fail, or returns number of missing 
dimensions if test pass but optional dims are missing
"""
        
        missingDimensions = self.lenDimensionTest - len(data.shape)           
        for i in range(missingDimensions):
            data.shape = (1,) + data.shape

        for dim,f in zip(data.shape, self.dimensionTest):
            if f is not None:
                if not f(dim):
                    return False, data

        if missingDimensions > 0:
            return missingDimensions, data
        else:
            return True, data


    def _shape(self, datashape):
        """This function is called by the constructor to return the number of
edges used to draw the port icon based on the number of dimensions of the type.
NOTE: this function is only used if the icon shape is not specified as an
argument to the constructor.
"""
        if datashape is not None:
            lDimensions = datashape[1:-1].split(',')
            lShape = len(lDimensions) * 2 - 1
            if lDimensions[0] == '0': 
                lShape -= 1 
        else:
            lShape = 0
        #print "icon shape:", lShape
        return lShape


    def cast(self, data):
        return False, None


    def validate(self, data):
        #print "validate", data
        if self['class'] is None:
            return True, data
        if self['datashape'] is None:
            if isinstance(data, self['class']):
                return True, data
            else:
                return False, None
        try:
            lArray = Numeric.array(data)
            lArray0 = lArray.ravel()[0]
            while hasattr(lArray0,'shape'):
                lArray0 = lArray0.ravel()[0]
            if isinstance(lArray0, self['class']):
                return True, lArray
            else:
                return False, None
        except:
            return False, None


# DEPRECATED CLASS:  use AnyArrayType instead
from UserDict import UserDict
class AnyType(
               UserDict
#               , 
#               AnyArrayType
               ):

    def __init__(self, name='Old None', color='white', shape='diamond',
                 width=12, height=8, klass=None, dataDescr=None
#                 , datashape=None
                 ):
        UserDict.__init__(self)
#        AnyArrayType.__init__(self, name=name, color=color, 
#                              shape=shape, width=width, height=height, 
#                              klass=klass, dataDescr=dataDescr,
#                              datashape=datashape)

#        warnings.warn('AnyType is deprecated, use AnyArrayType instead',
#                      DeprecationWarning, stacklevel=2)

        # Note: use EVEN numbers for width, height, since they will be
        # divided by 2 for halfPortWidth, halfPortHeight
        self.data['name'] = name
        self.data['dataDescr'] = dataDescr
        self.data['shape'] = shape          # port icon
        self.data['width'] = width          # port icon width
        self.data['height'] = height        # port icon height
        self.data['color'] = color          # port icon color
        self.data['class'] = klass
        self.data['datashape'] = None    # added to be compatible with 


    def cast(self, data):
        """returns a success status (true, false) and the coerced data"""
        assert True, data # to silent pychecker
        return False, None


    def validate(self, data):
        """returns true if data if of the proper type"""
        return True



class FloatType(AnyArrayType):
    
    def __init__(self, name='float', datashape=None, color='green', 
                 shape='circle', width=None, height=None):
        AnyArrayType.__init__(self, name=name, color=color,
                              shape=shape, width=width, height=height, 
                              klass=float, datashape=datashape)


    def validate(self, data):
        if self['datashape'] is None:
            if isinstance(data, types.FloatType):
                return True, data
            else:
                return False, None
        try:
            lArray = Numeric.array(data, 'f')
            return True, lArray
        except:
            return False, None


    def cast(self, data):
        if self['datashape'] is None:
            if isinstance(data, types.FloatType):
                return True, data
            try:
                data = float(data)
                return True, data
            except:
                return False, data      
        try:
            lArray = (Numeric.array(data)).astype('f')
            return True, lArray
        except:
            return False, None



class IntType(AnyArrayType):
    
    def __init__(self, name='int', datashape=None,color='yellow', 
                 shape='circle', width=None, height=None):
        AnyArrayType.__init__(self, name=name, color=color,
                              shape=shape, width=width, height=height, 
                              klass=int, datashape=datashape)


    def validate(self, data):
        if self['datashape'] is None:
            if isinstance(data, types.IntType):
                return True, data
            else:
                return False, None
        try:
            lArray = Numeric.array(data, 'i')
            return True, lArray
        except:
            return False, None


    def cast(self, data):
        if self['datashape'] is None:
            if isinstance(data, types.IntType):
                return True, data
            try:
                data = int(data)
                return True, data
            except:
                return False, data      
        try:
            lArray = (Numeric.array(data)).astype('i')
            return True, lArray
        except:
            return False, None



class BooleanType(AnyArrayType):

    def __init__(self, name='boolean', datashape=None, color='yellow', 
                 shape='rect', width=None, height=None):

        AnyArrayType.__init__(self, name=name, color=color,
                              shape=shape, width=width, height=height, 
                              klass=bool, datashape=datashape)


    def validate(self, data):
        if self['datashape'] is None:
            if type(data) == types.BooleanType:
                return True, data
            else:
                return False, None
        try:
            lArray = Numeric.array(data, 'B')
            return True, lArray
        except:
            return False, None


    def cast(self, data):
        if self['datashape'] is None:
            if type(data) == types.BooleanType:
                return True, data
            try:
                data = bool(data)
                return True, data
            except:
                return False, data      
        try:
            #FIXME: this 'b' stands for binary not boolean
            lArray = (Numeric.array(data)).astype('B')
            return True, lArray
        except:
            return False, None



class StringType(AnyArrayType):

    def __init__(self, name='string', datashape=None, color='white', 
                 shape='oval', width=None, height=None):

        AnyArrayType.__init__(self, name=name, color=color,
                              shape=shape, width=width, height=height, 
                              klass=str, datashape=datashape)


    def validate(self, data):
        if self['datashape'] is None:
            if type(data) == types.StringType:
                return True, data
            else:
                return False, None
        try:
            lArray = Numeric.array(data, 'O')
            #lShape = array.shape
            #lArray = map(str, array)
            #array.shape = lShape
            return True, lArray
        except:
            return False, None


    def cast(self, data):
        if self['datashape'] is None:
            if type(data) == types.StringType:
                return True, data
            try:
                data = str(data)
                return True, data
            except:
                return False, data      
        try:
            lArray = (Numeric.array(data)).astype('O')
            return True, lArray
        except:
            return False, None



#class StringType(AnyType):
#
#    def __init__(self):
#        AnyType.__init__(self)
#        self.data['name'] = 'string'
#        self.data['color'] = 'white'
#        self.data['shape'] = 'oval'
#        self.data['width'] = 12  # circle
#        self.data['height'] = 12
#        self.data['class'] = str
#
#    def validate(self, data):
#        return type(data)==types.StringType
#    
#    def cast(self, data):
#        try:
#            return True, str(data)
#        except:
#            return False, data



class ListType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'list'
        self.data['color'] = 'cyan'
        self.data['shape'] = 'oval'
        self.data['width'] = 12  # circle
        self.data['height'] = 12
        self.data['class'] = list


    def validate(self, data):
        return type(data)==types.ListType

    
    def cast(self, data):
        try:
            if type(data)==types.StringType:
                try:
                    lData = eval(data)
                except:
                    lData = data
            else:
                lData = data
            try:
                lData = list(lData)
            except:
                lData = [lData]
            return True, lData
        except:
            return False, data



class TupleType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'tuple'
        self.data['color'] = 'cyan'
        self.data['shape'] = 'oval'
        self.data['width'] = 12  # circle
        self.data['height'] = 12
        self.data['class'] = tuple


    def validate(self, data):
        return type(data)==types.TupleType

    
    def cast(self, data):
        try:
            data = tuple(data)
            return True, data
        except:
            return False, data


    
class DictType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'dict'
        self.data['color'] = 'cyan'
        self.data['shape'] = 'oval'
        self.data['width'] = 12  # circle
        self.data['height'] = 12
        self.data['class'] = dict


    def validate(self, data):
        return type(data)==types.DictType



class ArrayType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'array'
        self.data['color'] = 'cyan'
        self.data['shape'] = 'oval'
        self.data['width'] = 12  # circle
        self.data['height'] = 12
        self.data['class'] = array.array


    def validate(self, data):
        return isinstance(data, array.ArrayType)



class NumericArrayType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'NumericArray'
        self.data['color'] = 'orange'
        self.data['shape'] = 'pentagon'
        self.data['class'] = Numeric.array


    def validate(self, data):
        return isinstance(data, Numeric.ArrayType)


    def cast(self, data):
        try:
            data = Numeric.array(data)
            return True, data
        except:
            return False, data



class VectorType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] = 'vector'
        self.data['color'] = 'cyan'
        self.data['shape'] = 'oval'
        self.data['width'] = 12  # circle
        self.data['height'] = 12
        self.data['class'] = None


    def validate(self, data):
        try:
            if type(data) != types.StringType:
                len(data)
                return True
            else:
                return False
        except:
            return False


    def cast(self, data):
        """returns a success status (true, false) and the coerced data
"""
        if type(data) == types.StringType:
            return True, (data, )
        return False, None



class TriggerOut(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] =  'triggerOut'
        self.data['color'] = 'orange'
        self.data['shape'] = 'square'
        del self.data['class']



class TriggerIn(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] =  'triggerIn'
        self.data['color'] = 'orange'
        self.data['shape'] = 'square'
        del self.data['class']



class TkColorType(AnyType):

    def __init__(self):
        AnyType.__init__(self)
        self.data['name'] =  'tkcolor'
        self.data['color'] = 'orange'
        self.data['shape'] = 'square'
        del self.data['class']

    def validate(self, data):
        import Tkinter
        try:
            Tkinter._default_root.winfo_rgb(data)
            return True
        finally:
            return False



class TypeManager:
    """Port type object manager

This object is used to register port type instances which are associated with
port. new types can be registered by passing an instance of port type object
to the .addType(instance) method. 

The .portTypeInstances dictionary provides a mapping between the a name used
to describe the data acceptable for a port and an instance of a subclass of
AnyArrayType.  This name can be

The .reverseLookUp dictionary is used to obtain a port type from the class of
and object.  This is used top propagate data types to ports that are mutatable
"""

    def __init__(self):

        self.portTypeInstances = {} # key: name+datashape, value: instance
        self.reverseLookUp = {} # key:class, value:typeObject

        self.addType( AnyArrayType() )   

        # basic types
        self.addType( FloatType() )
        self.addType( IntType() )
        #self.addType( ObjectType() )

        self.addType( BooleanType() )
        self.addType( StringType() )    
        # for backward compatibility:
        self.portTypeInstances['str'] = self.portTypeInstances['string']

        # synonyms  
        self.addSynonym('coord2', 'float', '(2)',
                            color='green', shape='oval')
        self.addSynonym('coord3', 'float', '(3)',
                            color='green', shape='rect')
        self.addSynonym('normal3', 'float', '(3)',
                            color='blue', shape='rect')
        self.addSynonym('colorfloat3or4', 'float', '(>=3 and <=4)',
                            color='orange', shape='rect')
        self.addSynonym('instancemat', 'float', '(4,4)',
                            color='cyan', shape='rect')
        self.addSynonym('indice2', 'int', '(2)',
                            color='purple', shape='rect')
        self.addSynonym('indice2+', 'int', '(>=2)',
                            color='purple', shape='rect')
        self.addSynonym('indice3or4', 'int', '(>=3 and <=4)',
                            color='purple', shape='rect')

        self.addSynonym('2Darray', 'float', '(>0,>0)', color='cyan')

        self.addSynonym('object', existingTypeName='None')
        self.addSynonym('colorRGB', existingTypeName='colorfloat3or4')
        self.addSynonym('colorsRGB', existingTypeName='colorRGB',datashape='(0)')
        self.addSynonym('coordinates3D', existingTypeName='coord3',datashape='(0)')
        self.addSynonym('faceIndices', existingTypeName='indice3or4',datashape='(0)')
        self.addSynonym('normals3D', existingTypeName='normal3',datashape='(0)')

        self.addType( AnyType() )
        self.addType( DictType() )
        self.addType( ListType() )
        self.addType( TkColorType() )
        self.addType( TupleType() )
        self.addType( ArrayType() )
        self.addType( NumericArrayType() )
        self.addType( VectorType() )
        self.addType( TriggerIn() )
        self.addType( TriggerOut() )


    def addSynonym(self, synonymName, existingTypeName=None, datashape=None,
                       color=None, shape=None, width=None, height=None):
        """ method to create synonym types
synonymName: can be an existing name with a diferent datashape:
           (existingTypeName must be None, and the basename 'coord3' must be registered)
           self.addSynonym('coord3(3,4)') 
existingTypeName: must be a registered name 
           (it can be datatshaped, if it is already registered like that)
           self.addSynonym('coordinates3D', existingTypeName='coord3',datashape='(3,4)')
           self.addSynonym('coordinates3D', existingTypeName='coord3(4)',datashape='(3)')
           self.addSynonym('coordinates3D', existingTypeName='coord3(3,4)')
"""
        if existingTypeName is None:
            assert datashape is None
            lSplitName = synonymName.split('(')
            existingTypeName = lSplitName[0]
            if len(lSplitName) == 2:
                datashape = '(' + lSplitName[1]
        basicInstance = self.portTypeInstances[existingTypeName]
        innerDatashape = basicInstance['datashape']
        if innerDatashape is not None:
            if datashape is None:
                datashape = innerDatashape
            else:
                innerDatashape = innerDatashape.split('(')[1]
                datashape = datashape.split(')')[0]
                datashape = datashape + ',' + innerDatashape
        if color is None:
            color = basicInstance['color']
        if shape is None:
            shape = basicInstance['shape']
        if width is None:
            width = basicInstance['width']
        if height is None:
            if shape == 'circle' or shape == 'square':
                height = width
            else:
                height = 2 * width / 3
        instance = basicInstance.__class__(
                         name=synonymName, datashape=datashape,
                         color=color, shape=shape, width=width, height=height)
        self.addType( instance )


    def getSynonymDict(self, synonymName):
        lDict = {}
        typeInstance = self.portTypeInstances[synonymName]
        lDict['existingTypeName'] = typeInstance.__class__()['name']
        if lDict['existingTypeName'] == synonymName:
            return None
        lDict['synonymName'] = synonymName        
        lDict['datashape'] = typeInstance['datashape']
        lDict['color'] = typeInstance['color']
        lDict['shape'] = typeInstance['shape']
        lDict['width'] = typeInstance['width']
        lDict['height'] = typeInstance['height']
        return lDict


    def addSynonymDict(self, aDict):
        if aDict.has_key('existingTypeName') is False:
            aDict['existingTypeName'] = None
        if aDict.has_key('datashape') is False:
            aDict['datashape'] = None
        if aDict.has_key('color') is False:
            aDict['color'] = None
        if aDict.has_key('shape') is False:
            aDict['shape'] = None
        if aDict.has_key('width') is False:
            aDict['width'] = None
        if aDict.has_key('height') is False:
            aDict['height'] = None

        self.addSynonym(aDict['synonymName'], 
                        existingTypeName=aDict['existingTypeName'],
                        datashape=aDict['datashape'],
                        color=aDict['color'], shape=aDict['shape'], 
                        width=aDict['width'], height=aDict['height'])


    def addType(self, dtypeinstance):
        """register a port type instance
"""
        #print "addType dtypeinstance", dtypeinstance['name'], dtypeinstance['datashape']
        #import pdb;pdb.set_trace()

        if isinstance(dtypeinstance, AnyType) or \
               isinstance(dtypeinstance, AnyArrayType):

            # we reduce dtypeinstance to its base class name
            splittype = dtypeinstance['name'].split('(')
            basetypename = splittype[0]           

            if dtypeinstance['datashape'] is not None:
                if dtypeinstance['name'].endswith(dtypeinstance['datashape']):
                    # make sure the base type exists
                    if self.portTypeInstances.has_key(basetypename) is None:
                        msg = 'base datatype '+basetypename
                        msg += ' not found in types table when adding %s'%str(dtypeinstance)
                        warnings.warn(msg)
                        return
                storagename = dtypeinstance['name']
            else:
                storagename = basetypename

            if self.portTypeInstances.has_key(storagename):
                if isinstance(dtypeinstance, AnyType):
                    if not ( \
                        isinstance(self.portTypeInstances[storagename], AnyType) \
                        and \
                        (dtypeinstance.data == self.portTypeInstances[storagename].data) \
                            ):
                        msg = 'Warning! datatype '+storagename+' already registered differently'
                        warnings.warn(msg)
                    return
                elif isinstance(dtypeinstance, AnyArrayType):
                    if not ( \
                        isinstance(self.portTypeInstances[storagename], AnyArrayType) \
                        and \
                        (dtypeinstance == self.portTypeInstances[storagename]) \
                            ):
                        msg = 'Warning! datatype '+storagename+' already registered differently'
                        warnings.warn(msg)
                    return

            self.portTypeInstances[storagename] = dtypeinstance

            if dtypeinstance.has_key('class'):
                if not self.reverseLookUp.has_key(dtypeinstance['class']):                
                    self.reverseLookUp[dtypeinstance['class']] = dtypeinstance

        else:
            raise RuntimeError('bad dtypeinstance argument')


    def getType(self, fullName):
        #print "getType fullName", fullName
        #import traceback;traceback.print_stack()
        #import pdb;pdb.set_trace()
        splittype = fullName.split('(')
        typename = splittype[0]
        datashape = None
        if len(splittype)==2:
            datashape = '(' + splittype[1]

        if not self.portTypeInstances.has_key(typename):
            msg = 'base datatype ' + typename
            msg += ' not found in types table'
            warnings.warn(msg)
            #import traceback;traceback.print_stack()
            return self.portTypeInstances['None']

        if self.portTypeInstances.has_key(fullName) is False:
            # base class exist but not with this datashape, we add it            
            self.addSynonym(fullName, typename, datashape)

        return self.portTypeInstances[fullName]



    def getTypeFromClass(self, klass):
        """ return the data type object for types that can be looked up i.e.
have a class attribute """
        return self.reverseLookUp.get(klass, self.reverseLookUp.get(None))


    def get(self, key, default=None):
        return self.portTypeInstances.get(key, default)
