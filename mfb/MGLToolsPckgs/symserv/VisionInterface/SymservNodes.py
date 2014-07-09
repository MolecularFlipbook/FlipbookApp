## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Nov 2001 Authors: Daniel Stoffler, Michel Sanner
#
#    stoffler@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner and TSRI
#
#########################################################################

import warnings
import numpy.oldnumeric as Numeric, math, types
from mglutil.math.rotax import rotax	

from NetworkEditor.items import NetworkNode
from NetworkEditor.macros import MacroNode
from Vision import UserLibBuild

from symserv.symOperators import SymNFold, SymTrans, SymTransXYZ, SymRot,\
     SymHelix, SymMerge, SymMultiply, SymSplit, CenterOfMass, SymOrient,\
     ApplyTransfToCoords, PDBtoMatrix, SymScale, SymTranspose,SymInverse,\
     DistanceBetweenTwoPoints, SymSuperHelix

from symserv.VisionInterface.SymservWidgets import NEXYZVectGUI


def ToList(matricesList):
    """turns a list of lists of 4x4 matrices into a list of 4x4 matrices.
This is used to remove the additional list created because all instanceMatrices
input ports of the nodes in thei file are NOT singleConnection by default.
"""
    if matricesList is None:
        return None

    # if the port is singleConnection we do not have an additional list
    if len(matricesList) and type(matricesList[0])!=types.ListType:
        return matricesList
    
    mats = []
    for m in matricesList:
        mats.extend(m)

    return mats

def importMolKitLib(net):
    try:
        ed = net.getEditor()
        from MolKit.VisionInterface.MolKitNodes import molkitlib
        ed.addLibraryInstance(
            molkitlib, 'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
    except:
        warnings.warn(
            'Warning! Could not import molitlib from MolKit.VisionInterface')


def importVizLib(net):
    try:
        ed = net.getEditor()
        from DejaVu.VisionInterface.DejaVuNodes import vizlib
        ed.addLibraryInstance(
            vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
    except:
        warnings.warn(
            'Warning! Could not import vizlib from DejaVu/VisionInterface')
            

class SaveToFile(NetworkNode):
    """
    save a list of instance matrices to a file

    input:
        matrices: instance matrices
        filename: name of the file in which to save
    """

    def __init__(self, name='Save', **kw):
        kw['name']=name

        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node', 'width':16,
            'initialValue':'', 'labelCfg':{'text':'Filename: '}
            }

	ip = self.inputPortsDescr
        ip.append(datatype='string', name='filename')
        ip.append(datatype='instancemat(0)', name='matrices')

	code = """def doit(self, filename, matrices):
    from symserv.utils import saveInstancesMatsToFile
    if filename:
        saveInstancesMatsToFile(filename, matrices)
"""

        if code: self.setFunction(code)
            

class ReadFromFile(NetworkNode):
    """
    read a list of instance matrices from a file

    input:
        filename: name of the file in which to save
    output:
        matrices: instance matrices
    """

    def __init__(self, name='Save', **kw):
        kw['name']=name

        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'labelCfg':{'text':'Filename: '}
            }

	ip = self.inputPortsDescr
        ip.append(datatype='string', name='filename')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='matrices')

	code = """def doit(self, filename):
    from symserv.utils import readInstancesMatsFromFile
    if filename:
        mats = readInstancesMatsFromFile(filename)
        if mats:
            self.outputData(matrices=mats)
"""

        if code: self.setFunction(code)


class Identity(NetworkNode):
    """Create a stream of transformation set to identity"""

    def __init__(self, name='Identity', symmetry=1, **kw):
        kw['name']=name
        kw['symmetry'] = symmetry
        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['copies'] = {
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':10, 'precision':3, 'increment':1, 'type':'int', 'min':1,
            'lockBMin':0,'lockType':1,'lockIncrement':1,
            'lockBIncrement':1, 'lockMin':1, 'master':'node',
            'initValue':1.0,
            'labelCfg':{'text':'# copies'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='int', name='copies')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

	code = """def doit(self, copies):
    result = []
    for i in xrange(copies):
        result.append(Numeric.identity(4, 'f'))
    self.outputData(outMatrices=result)
"""

        if code: self.setFunction(code)

from mglutil.math.rotax import rotVectToVect

class AlignVectToVect(NetworkNode):
    """Create a stream of rotations that align 3D vectors"""

    def __init__(self, name='Vect2Vect', symmetry=1, **kw):
        kw['name']=name
        kw['symmetry'] = symmetry
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='None', name='vect1')
        ip.append(datatype='None', name='vect2')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

	code = """def doit(self, vect1, vect2):
    from math import sqrt
    try:
        vect1[0][0]
        vect1_1D=False
    except:
        vect1_1D=True
    try:
        vect2[0][0]
        vect2_1D=False
    except:
        vect2_1D=True

    if vect1_1D+vect2_1D == 1:
        if vect1_1D:
            vect1 = list([vect1])*len(vect2)
        else:
            vect2 = list([vect2])*len(vect1)

    if not (vect1_1D or vect2_1D):
        assert len(vect1[0])==3
        assert len(vect2[0])==3
        result = []
        for i in xrange(len(vect1)):
            v1 = vect1[i]
            v2 = vect2[i]
            n1 = 1.0/sqrt(v1[0]*v1[0] + v1[1]*v1[1] + v1[2]*v1[2])
            n2 = 1.0/sqrt(v2[0]*v2[0] + v2[1]*v2[1] + v2[2]*v2[2])
            v1 = (v1[0]*n1, v1[1]*n1, v1[2]*n1)
            v2 = (v2[0]*n2, v2[1]*n2, v2[2]*n2)
            result.append( Numeric.array( rotVectToVect(v1, v2), 'f') )
    else:
        v1 = vect1
        v2 = vect2
        n1 = 1.0/sqrt(v1[0]*v1[0] + v1[1]*v1[1] + v1[2]*v1[2])
        n2 = 1.0/sqrt(v2[0]*v2[0] + v2[1]*v2[1] + v2[2]*v2[2])
        v1 = (v1[0]*n1, v1[1]*n1, v1[2]*n1)
        v2 = (v2[0]*n2, v2[1]*n2, v2[2]*n2)
        result = [Numeric.array( rotVectToVect(v1, v2 ), 'f')]
    self.outputData(outMatrices=result)
"""

        if code: self.setFunction(code)


class PerurbVectorNE(NetworkNode):
    """randomly modifies vector usiing gaussian distribution
    
Input:
    vector: initial vector
    sigma: standard deviation of Gaussian
Output:
    vector: modified vector
"""
    def __init__(self, name='PerurbVector', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.vector = None
        ip = self.inputPortsDescr
        ip.append(datatype='none', name='vector')
        ip.append(datatype='float', name='sigma', defaultValue=.3)
        ip.append(datatype='bool', name='normalize', defaultValue=1)

	self.widgetDescr['vector'] = {
            'class':'NEVectorGUI',
            'size':100, 'continuous':1,'mode':'XY',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'vector'},
            'initialValue':[1.,0,0]}

        self.widgetDescr['sigma'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':0.3, 'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'sigma:'},
            }

	self.widgetDescr['normalize'] = {
            'class':'NECheckButton', 'master':'node', 'initialValue':1,
            'labelCfg':{'text':'normalize'},
            }

        op = self.outputPortsDescr
        op.append(datatype='none', name='vector')

        code = """def doit(self, vector, sigma, normalize):
    if self.inputPorts[0].hasNewValidData():
        self.vector = vector

    x, y, z = self.vector
    from random import gauss
    self.vector = (gauss(x, sigma), gauss(y, sigma), gauss(z,sigma))
    if normalize:
        x, y, z = self.vector
        from math import sqrt
        n = 1./sqrt(x*x + y*y + z*z)
        self.vector = (x*n, y*n, z*n)
    self.outputData(vector = self.vector)
"""
        self.setFunction(code)


class SymNFoldNode(NetworkNode):
    """To be subclassed"""

    def __init__(self, name='Prototype', symmetry=1, **kw):
        kw['name']=name
        kw['symmetry'] = symmetry
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymNFold( (1,0,0), (0,0,0), symmetry, 1 )

	code = """def doit(self, matrices, vector, point, identity):  
    matrices = ToList(matrices)
    self.operator.set(vector=vector, point=point, symmetry=%d,
                      identity=identity)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""%symmetry

        if code: self.setFunction(code)
	
	self.widgetDescr['vector'] = {
            'class':'NEVectorGUI',
            'size':100, 'continuous':1,'mode':'XY',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':str(symmetry)+'-fold vector'},
            'initialValue':[1.,0,0]}
            #'vector':[1.,0,0] }
        
        self.widgetDescr['point'] = {
            'class':'NEVectEntry',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'Point'},
            'initialValue':[0., 0., 0.],
            }
        
        self.widgetDescr['identity'] = {
            'class':'NECheckButton',
            'initialValue':1,
            'labelGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'Identity'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='None', required=False, name='point')
	ip.append(datatype='int', required=False, name='identity')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')


class Sym2FoldNE(SymNFoldNode):
    """Apply a 2-fold symmetry to an incoming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.
The symmetry axis is controlled by a vector gui located in the node parameter
panel. Additionally, a center of origin can be specified as well as the number
of symmetries. The identity checkbutton controls whether the identity matrix
is added or not. """ 
    
    def __init__(self, name='Sym2Fold', **kw):
        kw['name']=name
        kw['symmetry'] = 2
        apply( SymNFoldNode.__init__, (self,), kw)



class Sym3FoldNE(SymNFoldNode):
    """Apply a 3-fold symmetry to an incoming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.
The symmetry axis is controlled by a vector gui located in the node parameter
panel. Additionally, a center of origin can be specified as well as the number
of symmetries. The identity checkbutton controls whether the identity matrix
is added or not. """ 

	
    def __init__(self, name='Sym3Fold', **kw):
        kw['name']=name
        kw['symmetry'] = 3
        apply( SymNFoldNode.__init__, (self,), kw)


class Sym4FoldNE(SymNFoldNode):
    """Apply a 4-fold symmetry to an incoming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.
The symmetry axis is controlled by a vector gui located in the node parameter
panel. Additionally, a center of origin can be specified as well as the number
of symmetries. The identity checkbutton controls whether the identity matrix
is added or not. """ 

    def __init__(self, name='Sym4Fold', **kw):
        kw['name']=name
        kw['symmetry'] = 4
        apply( SymNFoldNode.__init__, (self,), kw)


class Sym5FoldNE(SymNFoldNode):
    """Apply a 5-fold symmetry to an incoming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.
The symmetry axis is controlled by a vector gui located in the node parameter
panel. Additionally, a center of origin can be specified as well as the number
of symmetries. The identity checkbutton controls whether the identity matrix
is added or not. """ 

    def __init__(self, name='Sym5Fold', **kw):
        kw['name']=name
        kw['symmetry'] = 5
        apply( SymNFoldNode.__init__, (self,), kw)


class Sym6FoldNE(SymNFoldNode):
    """Apply a 6-fold symmetry to an incoming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.
The symmetry axis is controlled by a vector gui located in the node parameter
panel. Additionally, a center of origin can be specified as well as the number
of symmetries. The identity checkbutton controls whether the identity matrix
is added or not. """ 

    def __init__(self, name='Sym6Fold', **kw):
        kw['name']=name
        kw['symmetry'] = 6
        apply( SymNFoldNode.__init__, (self,), kw)
	


class SymNFoldNE(NetworkNode):
    """Apply an N-fold symmetry to an incoming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.
The symmetry axis is controlled by a vector gui located in the node parameter
panel. Additionally, a center of origin can be specified as well as the number
of symmetries. The identity checkbutton controls whether the identity matrix
is added or not. """ 

    def __init__(self, name='SymNFold', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymNFold( (1,0,0), (0,0,0), 1, 1 )

	code = """def doit(self, matrices, vector, point, symmetry, identity):

    matrices = ToList(matrices)
    self.operator.set(vector=vector, point=point, symmetry=symmetry,
                      identity=identity)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
	self.widgetDescr['vector'] = {
            'class':'NEVectorGUI',
            'size':100, 'continuous':1,'mode':'XY',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'n-fold vector'},
            'initialValue':[1.,0,0] }
            #'vector':[1.,0,0] }
        
        self.widgetDescr['point'] = {
            'class':'NEVectEntry',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'Point'},
            'initialValue':[1.,0,0],
            }
        
        self.widgetDescr['symmetry'] = {
            'class':'NEDial','size':100,
            'type':'int', 'min':1, 'lockMin':1, 'lockBMin':1,
            'lockType':1, 'oneTurn':10,
            'initialValue':1,
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'# symetries'},
            }
        
        self.widgetDescr['identity'] = {
            'class':'NECheckButton',
            'initialValue':1,
            'labelCfg':{'text':'Identity'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='None', required=False, name='point')
	ip.append(datatype='int', required=False, name='symmetry')
	ip.append(datatype='int', required=False, name='identity')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')
	

class SymTransNE(NetworkNode):
    """Apply a translation to an incomming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices. The axis of translation is controlled by a vector gui widget and the
lenght of the vector by a thumbwheel widget located in the parameter panel. 
The identity checkbutton controls whether the identity matrix is added or not.
""" 
    def __init__(self, name='SymTranslation', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymTrans( (1.0,0.0,0.0), 0.0, 0 )

	code = """def doit(self, matrices, vector, length, identity):
    matrices = ToList(matrices)
    self.operator.set(vector=vector, identity=identity,length=length)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)
"""

        if code: self.setFunction(code)
	
	self.widgetDescr['vector'] = {
            'class':'NEVectorGUI', 'size':100,
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2,'labelSide':'top'},
            'labelCfg':{'text':''},'continuous':1,
            'initialValue':[1.,0,0]
            }
        
        self.widgetDescr['length'] = {
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':1, 'precision':3,
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'vector length:'},
            }
        
	self.widgetDescr['identity'] = {
            'class':'NECheckButton',
            'initialValue':0,
            'labelCfg':{'text':'Identity'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='None', required=False, name='length')
	ip.append(datatype='int', required=False, name='identity')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

		
class SymTransXYZNE(NetworkNode):
    """Apply a translation to an incomming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices. The axis of translation is controlled by a vector gui widget and the
lenght of the vector by a thumbwheel widget located in the parameter panel. 
The identity checkbutton controls whether the identity matrix is added or not.
""" 
    def __init__(self, name='SymTranslationXYZ', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymTransXYZ( (0,0,0, (0,0,0),(0,0,0),(0,0,0)),0 )

	code = """def doit(self, matrices, vector, identity):
    matrices = ToList(matrices)
    self.operator.set(data=vector, identity=identity)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
        self.widgetDescr['vector'] = {
            'class':'NEXYZVectGUI',
            'vectX':'1 0 0','vectY':'0 1 0','vectZ':'0 0 1',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':''},
            }

	self.widgetDescr['identity'] = {
            'class':'NECheckButton',
            'initialValue':0,
            'labelCfg':{'text':'Identity'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='int', required=False, name='identity')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')


class SymRotNE(NetworkNode):
    """Apply a rotation to an incomming stream of 4x4 matrices.
The node then outputs a list of 4x4 matrices, concatenated with any incoming
matrices.The axis of rotation is controlled by a vector gui widget located in
the parameter panel. Additionally, a center of origin can be specified as well
as the rotation angle. The identity checkbutton controls whether the identity
matrix is added or not. """

    def __init__(self, name='SymRotation', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymRot( (1,0,0), (0,0,0), 0, 0 )

	code = """def doit(self, matrices, vector, point, angle, identity):
    matrices = ToList(matrices)
    self.operator.set(vector=vector, point=point, angle=angle,
                      identity=identity)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
	self.widgetDescr['vector'] = {
            'class':'NEVectorGUI', 'size':100,
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'rot. axis'},
            'initialValue':[1.,0,0]
            }
        
        self.widgetDescr['point'] = {
            'class':'NEVectEntry',
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'Point'},
            'initialValue':[0.,0,0]
            }

        self.widgetDescr['angle'] = {
            'class':'NEDial', 'size':100,
            'type':'float', 'oneTurn':360,
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'angle'},
            }
        
	self.widgetDescr['identity'] = {
            'class':'NECheckButton',
            'initialValue':0,
            'labelCfg':{'text':'Identity'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='None', required=False, name='point')
	ip.append(datatype='float', required=False, name='angle')
	ip.append(datatype='int', required=False, name='identity')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

	
class SymHelixNE(NetworkNode):
    """Generates a helix.
Helix parameters are controlled by a VectorGUI widget located in the
parameter panel

Input:
    matrices:  matrices to be pre-multiplied with the helical transformation
    vector: the 3-D vector defining the oriention of the helical axis
    point:  a 3-D point defining the location in space of the helical axis
    angle:  angular value in degrees between 2 consecutive copies
    hrise: displacement along the helical axis between 2 consecutive copies
    copies: number of transformations
"""

    def __init__(self, name='SymHelix', **kw):

        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymHelix( (0.,1.,0.), (0.,0.,0.), 0., 0., 1 )

	code = """def doit(self, matrices, vector, point, angle, hrise, copies):

    matrices = ToList(matrices)
    self.operator.set(vector=vector, point=point, angle=angle, hrise=hrise,
                      copies=copies)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
        # FIXME: radius and increment are switched

        self.widgetDescr['vector'] = {
            'class':'NEVectorGUI', 'size':100, 
            'continuous':1,
            'initialValue':[0.,1.,0],
            'widgetGridCfg':{'labelSide':'top'},
            'labelCfg':{'text':'rot. axis'},
            }

        self.widgetDescr['point'] = {
            'class':'NEVectEntry',
            'initialValue':[0.,0,0],
            'widgetGridCfg':{'labelSide':'top'},
            'labelCfg':{'text':'point'},
            }

        self.widgetDescr['angle'] = {
            'class':'NEDial', 'size':100,
            'oneTurn':360, 'type':'float',
            'widgetGridCfg':{'labelSide':'top'},
            'labelCfg':{'text':'angle'},
            }
            
        self.widgetDescr['hrise'] = {
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':1, 'precision':3, 'type':'float',
            'initValue':1.0,
            'widgetGridCfg':{'labelSide':'top'},
            'labelCfg':{'text':'rise'},
            }

        self.widgetDescr['copies'] = {
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':10, 'precision':3, 'increment':1, 'type':'int', 'min':1,
            'lockBMin':0,'lockType':1,'lockIncrement':1,
            'lockBIncrement':1, 'lockMin':1,
            'initValue':1.0,
            'widgetGridCfg':{'labelSide':'top'},
            'labelCfg':{'text':'# copies'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='None', required=False, name='point')
	ip.append(datatype='float', required=False, name='angle')
	ip.append(datatype='float', required=False, name='hrise')
	ip.append(datatype='int', required=False, name='copies')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

	
class SymSuperHelixNE(NetworkNode):
    """Generates a super helix. This is a helical arrangement (local helix)
    that follows a helical path (overall helix)

Input:
    matrices:  matrices to be pre-multiplied with the helical transformation

    vector1: the 3-D vector defining the oriention of the overal helical axis
    point1:  a 3-D point defining the location in space of the helical axis
    angle1:  angular value in degrees between 2 consecutive copies
    hrise1: displacement along the helical axis between 2 consecutive copies

    vector2: the 3-D vector defining the oriention of the local helical axis
    point2:  a 3-D point defining the location in space of the helical axis
    angle2:  angular value in degrees between 2 consecutive copies
    hrise2: displacement along the helical axis between 2 consecutive copies

    copies: number of transformations
"""

    def __init__(self, name='SymSuperHelix', **kw):

        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymSuperHelix(
            (0.,1.,0.), (0.,0.,0.), 0., 0.,
            (0.,0.,1.), (0.,0.,0.), 0., 0., 1 )

	code = """def doit(self, matrices, vector1, point1, angle1, hrise1, vector2, point2, angle2, hrise2, copies):

    matrices = ToList(matrices)
    self.operator.set(
        vector=vector1, point=point1, angle=angle1, hrise=hrise1,
        vector2=vector2, point2=point2, angle2=angle2, hrise2=hrise2,
        copies=copies)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
        # FIXME: radius and increment are switched

        self.widgetDescr['vector1'] = {
            'class':'NEVectorGUI', 'size':100, 
            'continuous':1,
            'initialValue':[0.,1.,0],
            'widgetGridCfg':{'labelSide':'top', 'column':0, 'row':1},
            'labelCfg':{'text':'overall helical rot. axis'},
            }

        self.widgetDescr['point1'] = {
            'class':'NEVectEntry',
            'initialValue':[0.,0,0],
            'widgetGridCfg':{'labelSide':'top', 'column':0, 'row':3},
            'labelCfg':{'text':'overall helical axis point'},
            }

        self.widgetDescr['angle1'] = {
            'class':'NEDial', 'size':100,
            'oneTurn':360, 'type':'float',
            'widgetGridCfg':{'labelSide':'top', 'column':0, 'row':5},
            'labelCfg':{'text':'overall helical angle'},
            }
            
        self.widgetDescr['hrise1'] = {
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':1, 'precision':3, 'type':'float',
            'initValue':1.0,
            'widgetGridCfg':{'labelSide':'top', 'column':0, 'row':7},
            'labelCfg':{'text':'overall helical rise'},
            }

        self.widgetDescr['vector2'] = {
            'class':'NEVectorGUI', 'size':100,
            'continuous':1,
            'initialValue':[0.,0.,1],
            'widgetGridCfg':{'labelSide':'top', 'column':1, 'row':1},
            'labelCfg':{'text':'local helical rot. axis'},
            }

        self.widgetDescr['point2'] = {
            'class':'NEVectEntry', 
            'initialValue':[0.,0,0],
            'widgetGridCfg':{'labelSide':'top', 'column':1, 'row':3},
            'labelCfg':{'text':'local helical axis point'},
            }

        self.widgetDescr['angle2'] = {
            'class':'NEDial', 'size':100,
            'oneTurn':360, 'type':'float',
            'widgetGridCfg':{'labelSide':'top', 'column':1, 'row':5},
            'labelCfg':{'text':'local helical angle'},
            }
            
        self.widgetDescr['hrise2'] = { 
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':1, 'precision':3, 'type':'float',
            'initValue':1.0,
            'widgetGridCfg':{'labelSide':'top', 'column':1, 'row':7},
            'labelCfg':{'text':'local helical rise'},
            }

        self.widgetDescr['copies'] = {
            'class':'NEThumbWheel', 'width':100, 'height':26, 'wheelPad':4,
            'oneTurn':10, 'precision':3, 'increment':1, 'type':'int', 'min':1,
            'lockBMin':0,'lockType':1,'lockIncrement':1,
            'lockBIncrement':1, 'lockMin':1,
            'initValue':1.0,
            'widgetGridCfg':{'labelSide':'top', 'columnspan':2},
            'labelCfg':{'text':'# copies'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='None', required=False, name='vector1')
	ip.append(datatype='None', required=False, name='point1')
	ip.append(datatype='float', required=False, name='angle1')
	ip.append(datatype='float', required=False, name='hrise1')
	ip.append(datatype='None', required=False, name='vector2')
	ip.append(datatype='None', required=False, name='point2')
	ip.append(datatype='float', required=False, name='angle2')
	ip.append(datatype='float', required=False, name='hrise2')
	ip.append(datatype='int', required=False, name='copies')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')


class SymMergeNE(NetworkNode):
    """Merges incoming matrices"""

    def __init__(self, name='SymMerge', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymMerge()
                          
	code = """def doit(self, matrices):
    matrices = ToList(matrices)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)

        ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
       
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')


class SymMultiplyNE(NetworkNode):
    """SymMultiply multiplies incoming matrices and ouputs them.
    
  - 1 parent is multiplied with itself
  - 2 parents: two valid options:
      * either one of the parents has lenght 1 (1 matrix) which is then
        multiplied to all other matrices of the second parent, or
      * both parents have the same amount of matrices."""

    def __init__(self, name='SymMultiply', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymMultiply()
        
	code = """def doit(self, stream1, stream2):
    if stream1 or stream2:
        if stream1:
            stream1 = stream1[0]
        if stream2:
            stream2 = stream2[0]
        result = self.operator(matA=stream1, matB=stream2)
        self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
        ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='stream1')
	ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='stream2')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')


class SymTransposeNE(NetworkNode):
    """Transpose all incomming (4x4) matrices"""

    def __init__(self, name='Transpose', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        m=Numeric.identity(4).astype('f')
        self.operator = SymTranspose()
        
	code = """def doit(self, matrices):
    matrices = ToList(matrices)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
        ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', singleConnection=False,
                  name='inMatrices')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')
        
class SymInverseNE(NetworkNode):
    """Inverse all incomming (4x4) matrices"""

    def __init__(self, name='Inverse', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        m=Numeric.identity(4).astype('f')
        self.operator = SymInverse()
        
	code = """def doit(self, matrices):
    matrices = ToList(matrices)
    result = self.operator(matrices)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
        ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', singleConnection=False,
                  name='inMatrices')

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

class SymSplitNE(NetworkNode):
    """unselected matrices of the incomming stream are sent to
output port 0, selected matrices are sent to additional output ports which get
created on selection.
selection is done by specifying matrices comma separated indices in the
incomming stream. Ranges can be specified using the ':' or '-'  character.
additional ports are created by using the ';' character.
"""

    def __init__(self, name='SymSplit', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        m=Numeric.identity(4).astype('f')
        self.operator = SymSplit(m, "")
        self.result = None

        self.widgetDescr['entry'] = {
            'class':'NEEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'selector:'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=True,
                  singleConnection=False, name='matrices')
	ip.append(datatype='string', required=False, name='entry')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices0')

	code = """def doit(self, matrices, entry):
    matrices = ToList(matrices)
    self.operator.set(matrices=matrices, chars=entry)
    self.result=self.operator(matrices,entry)
    self.addRemovePorts(len(self.result))
    args = {}
    for i in range(len(self.result)):
        var='outMatrices'+`i`
        if len(self.result[i]) == 0:
            portData = [Numeric.identity(4).astype('f')]
        else: portData=self.result[i]
        args[var]=list(portData)
        apply(self.outputData, (), args)\n"""

        if code: self.setFunction(code)

        # to save and load the split node properly with all its outputPorts:
        # if we have more than 1 output port we save the source code of
        # this node (by setting self.modified = 1)
        if self.result > 1:
            for p in self.outputPorts:
                p._modified = True
        else:
            for p in self.outputPorts:
                p._modified = False
	

    def addRemovePorts(self, nb):
        dynamicOPortsDescr=[]
        if nb > len(self.outputPorts): # we add ports
            loop=nb-len(self.outputPorts)
            for i in range(loop):
                name="outMatrices"+`len(self.outputPorts)+i`
                dynamicOPortsDescr.append({
                  'name': name, 'datatype':'instancemat'})
            for kw in dynamicOPortsDescr:
                ip = apply( self.addOutputPort, (), kw )
            self.outputPortsDescr = self.outputPortsDescr + dynamicOPortsDescr

        elif nb < len(self.outputPorts): # we remove ports
            for i in range(len(self.outputPorts), nb, -1):
                self.deletePort(self.outputPorts[i-1])

        elif nb == len(self.outputPorts): return
                    

class CoMassNE(NetworkNode):
    """ inputs xyz coords, returns center of gravity """

    
    def __init__(self, name='Center of Mass', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = CenterOfMass(None)

	code = """def doit(self, coords):
    if coords and len(coords):
        self.operator.set(coords=coords)
        result=self.operator()
        self.outputData(centerOfMass=result)\n"""

        if code: self.setFunction(code)

	ip = self.inputPortsDescr
        ip.append(datatype='coordinates3D', name='coords')
        
	op = self.outputPortsDescr
        op.append(datatype='list', name='centerOfMass')


    def beforeAddingToNetwork(self, net):
        # import vizlib
        importVizLib(net)


class SymOrientNE(NetworkNode):
    """Apply a rotation to an incomming stream of 4x4 matrices
The rotation is around the center of mass
If the identity check button is checked this node will multiply the incoming
matrices by the identity matrix and the rotation matrix, else only the
rotation matrix is applied.
The axis of rotation is controlled by a VectorGUI widget located in the
parameter panel"""

    def __init__(self, name='SymOrient', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymOrient( [1,0,0], 0, [0,0,0], 0 )

	code = """def doit(self, matrices, centerOfMass, vector, angle, identity):
    matrices = ToList(matrices)
    if centerOfMass and len(centerOfMass):
        self.operator.set(vector=vector, angle=angle,
        center=centerOfMass, identity=identity)
        result = self.operator(matrices)
        self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)
	
	self.widgetDescr['vector'] = {
            'class':'NEVectorGUI', 'size':100,
            'continuous':1,
            'initialValue':[1.,0,0],
            #'vector':[1.,0,0],
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'labelCfg':{'text':'rot. axis'},
            }
       
        self.widgetDescr['angle'] = {
            'class':'NEDial', 'size':100,
            'labelGridCfg':{'columnspan':2},
            'widgetGridCfg':{'columnspan':2, 'labelSide':'top'},
            'oneTurn':360, 'type':'float',
            'labelCfg':{'text':'angle'},
            } 
        
	self.widgetDescr['identity'] = {
            'class':'NECheckButton',
            'initialValue':0,
            'labelCfg':{'text':'Identity'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
	ip.append(datatype='list', required=False, name='centerOfMass')
	ip.append(datatype='None', required=False, name='vector')
	ip.append(datatype='float', required=False, name='angle')
	ip.append(datatype='int', required=False, name='identity')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')



class ApplyTransfToCoordsNE(NetworkNode):
    """ inputs xyz coords, and matrices, returns transformed coords """

    
    def __init__(self, name='Apply Transf to Coords', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = ApplyTransfToCoords([0.,0,0],None)
        
	code = """def doit(self, coords, matrices):
    if coords and len(coords) and matrices and len(matrices):
        matrices = ToList(matrices)
        self.operator.set(coords=coords, matrices=matrices)
        result=self.operator()
        self.outputData(coords=result)\n"""
 
        if code: self.setFunction(code)

	ip = self.inputPortsDescr
        ip.append(datatype='coordinates3D', name='coords')
	ip.append(datatype='instancemat(0)', required=False,
                  singleConnection=False, name='matrices')
        
	op = self.outputPortsDescr
        op.append(datatype='coordinates3D', name='coords')


    def beforeAddingToNetwork(self, net):
        # import vizlib
        importVizLib(net)
       

class DistanceToPoint(NetworkNode):
    """ inputs coords and a point, returns the distances of the coords to
    this point"""

    
    def __init__(self, name='DistanceToPoint', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)
        
        code = """def doit(self, coords, point):
        if len(coords) and len(coords):
            diff = Numeric.array(coords) - Numeric.array(point)
            diff = diff*diff
            dist = Numeric.sqrt( Numeric.add.reduce(diff, 1) )
            self.outputData(dist=dist)\n"""

        if code: self.setFunction(code)
        
        ip = self.inputPortsDescr
        ip.append(datatype='coordinates3D', name='coords')
        ip.append(datatype='None', required=False, name='point', defaultValue=(0,0,0) )
            
        op = self.outputPortsDescr
        op.append(datatype='None', name='dist')

    def beforeAddingToNetwork(self, net):
        # import vizlib
        importVizLib(net)
	

class SymScaleNE(NetworkNode):
    """Apply a scale factor to  inputs matrices (not required).
Outputs scaled matrices.

The scaling factor can be applied to x, y and or z, using the checkbutton
widgets bound to the node."""
    
    def __init__(self, name='Scale', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = SymScale()

	code = """def doit(self, matrices, scaleFactor, scaleX, scaleY, scaleZ):
    if scaleFactor is None:
        return
    if not matrices:
        matrices = None

    selection = [scaleX, scaleY, scaleZ]
        
    result = self.operator(matrices, scaleFactor, selection=selection)
    self.outputData(outMatrices=result)\n"""

        if code: self.setFunction(code)

        ip = self.inputPortsDescr
        ip.append(datatype='instancemat(0)', required=False, name='matrices')
	ip.append(datatype='float', required=False, name='scaleFactor')
        ip.append(datatype='int', name='scaleX', defaultValue=1)
        ip.append(datatype='int', name='scaleY', defaultValue=1)
        ip.append(datatype='int', name='scaleZ', defaultValue=1)

	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='outMatrices')

	self.widgetDescr['scaleX'] = {
            'class':'NECheckButton', 'master':'node',
            'labelGridCfg':{'sticky':'w', 'columnspan':2},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Scale X'},
            'initialValue':1,
            }
	self.widgetDescr['scaleY'] = {
            'class':'NECheckButton', 'master':'node',
            'labelGridCfg':{'sticky':'w', 'columnspan':2},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Scale Y'},
            'initialValue':1,
            }
	self.widgetDescr['scaleZ'] = {
            'class':'NECheckButton', 'master':'node',
            'labelGridCfg':{'sticky':'w', 'columnspan':2},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'Scale Z'},
            'initialValue':1,
            }

class Dist2Points(NetworkNode):
    """Computes the distance between two (x,y,z) points"""
    
    def __init__(self, name='Dist2Points', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = DistanceBetweenTwoPoints()

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='point1')
        ip.append(datatype='list', name='point2')

	op = self.outputPortsDescr
        op.append(datatype='float', name='distance')
        
	code = """def doit(self, point1, point2):
    if point1 and point2:
        result = self.operator(point1, point2)
        self.outputData(distance=result)\n"""

        if code: self.setFunction(code)


class PDBToMatrix(NetworkNode):
    """ inputs PDB file, parses MTRIXn records and returns a list of (4x4)
    matrices. MTRIXn is the default PDB standard, however not everybody seems
    to follow the standard, thus an optional keyword can be passed that
    describes the matrix records in this non-standard PDB file."""
    

    def __init__(self, name='PDBtoMatrix', **kw):
        kw['name']=name
        apply( NetworkNode.__init__, (self,), kw)

        self.operator = PDBtoMatrix()
        
	code = """def doit(self, mol, keyword):
    if mol:
        if keyword is None or keyword == '' or keyword == []:
            keyword = 'MTRIX'
        result = self.operator.getMatrices(mol,keyword)
    if result:
        self.outputData(matrices=result)\n"""

        if code: self.setFunction(code)

	ip = self.inputPortsDescr
        ip.append(datatype='MoleculeSet', name='molecule')
	ip.append(datatype='string', required=False, name='keyword')
        
	op = self.outputPortsDescr
        op.append(datatype='instancemat(0)', name='matrices')


    def beforeAddingToNetwork(self, net):
        # import molkitlib
        importMolKitLib(net)
           

## saving node icos1 ##
from NetworkEditor.macros import MacroNode
class Icos1(MacroNode):

    def __init__(self, constrkw={}, name='Icosahedral1', **kw):
        kw['name'] = name
        apply( MacroNode.__init__, (self,), kw)

    def beforeAddingToNetwork(self, net):
        MacroNode.beforeAddingToNetwork(self, net)
        ## loading libraries ##
        from symserv.VisionInterface.SymservNodes import symlib
        net.editor.addLibraryInstance(
            symlib,"symserv.VisionInterface.SymservNodes", "symlib")
        

    def afterAddingToNetwork(self):
        from NetworkEditor.macros import MacroNode
        MacroNode.afterAddingToNetwork(self)
        ## loading libraries ##
        from symserv.VisionInterface.SymservNodes import symlib
        ## building macro network ##
        node0 = self
        node2 = node0.macroNetwork.opNode
        node2.move(193, 356)
        from symserv.VisionInterface.SymservNodes import Sym5FoldNE
        node3 = Sym5FoldNE(constrkw = {}, name='5-fold', library=symlib)
        node0.macroNetwork.addNode(node3,220,76)
        node3.inputPorts[1].widget.set(
            [0.0, 0.52549288072191591, 0.85079799735929229],0)
        node3.inputPorts[2].widget.set([0.0, 0, 0],0)
        from symserv.VisionInterface.SymservNodes import Sym3FoldNE
        node4 = Sym3FoldNE(constrkw = {}, name='3-fold', library=symlib)
        node0.macroNetwork.addNode(node4,221,142)
        node4.inputPorts[1].widget.set(
            [0.57735026918962584, 0.57735026918962584, 0.57735026918962584],0)
        node4.inputPorts[2].widget.set([0.0, 0, 0],0)
        from symserv.VisionInterface.SymservNodes import Sym2FoldNE
        node5 = Sym2FoldNE(constrkw = {}, name='2-fold', library=symlib)
        node0.macroNetwork.addNode(node5,115,217)
        node5.inputPorts[1].widget.set([1.0, 0.0, 0.0],0)
        node5.inputPorts[2].widget.set([0.0, 0, 0],0)
        node5.inputPorts[3].widget.set(1,0)
        from symserv.VisionInterface.SymservNodes import Sym2FoldNE
        node6 = Sym2FoldNE(constrkw = {}, name='2-fold', library=symlib)
        node0.macroNetwork.addNode(node6,244,218)
        node6.inputPorts[1].widget.set([0.0, 0.0, 1.0],0)
        node6.inputPorts[2].widget.set([0.0, 0, 0],0)
        node6.inputPorts[3].widget.set(0,0)
        from symserv.VisionInterface.SymservNodes import Sym2FoldNE
        node7 = Sym2FoldNE(constrkw = {}, name='2-fold', library=symlib)
        node0.macroNetwork.addNode(node7,381,218)
        node7.inputPorts[1].widget.set([0.0, 1.0, 0.0],0)
        node7.inputPorts[2].widget.set([0.0, 0, 0],0)
        node7.inputPorts[3].widget.set(0,0)
        from symserv.VisionInterface.SymservNodes import SymMergeNE
        node8 = SymMergeNE(constrkw = {}, name='Merge', library=symlib)
        node0.macroNetwork.addNode(node8,233,288)

        ## saving connections for network Icosahedral1 ##
        if node4 is not None and node5 is not None:
            node0.macroNetwork.connectNodes(
                node4, node5, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node4 is not None and node6 is not None:
            node0.macroNetwork.connectNodes(
                node4, node6, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node4 is not None and node7 is not None:
            node0.macroNetwork.connectNodes(
                node4, node7, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node3 is not None and node4 is not None:
            node0.macroNetwork.connectNodes(
                node3, node4, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node5 is not None and node8 is not None:
            node0.macroNetwork.connectNodes(
                node5, node8, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        node2 = node0.macroNetwork.opNode
        if node8 is not None and node2 is not None:
            node0.macroNetwork.connectNodes(
                node8, node2, "outMatrices", "new", blocking=True, doNotSchedule=True)
        if node6 is not None and node8 is not None:
            node0.macroNetwork.connectNodes(
                node6, node8, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node7 is not None and node8 is not None:
            node0.macroNetwork.connectNodes(
                node7, node8, "outMatrices", "matrices", blocking=True, doNotSchedule=True)

        ## modifying MacroOutputNode dynamic ports
        node2.inputPorts[1].configure(singleConnection=True)

        node0.shrink()
        ## reset modifications ##
        node0.resetTags()
        node0.buildOriginalList()


## saving node icosCage ##
from traceback import print_exc
from NetworkEditor.macros import MacroNode
class IcosCage(MacroNode):

    def __init__(self, constrkw={}, name='IcosCage', **kw):
        kw['name'] = name
        apply( MacroNode.__init__, (self,), kw)

    def beforeAddingToNetwork(self, net):
        MacroNode.beforeAddingToNetwork(self, net)
        ## loading libraries ##
        from symserv.VisionInterface.SymservNodes import symlib
        net.editor.addLibraryInstance(
            symlib,"symserv.VisionInterface.SymservNodes", "symlib")
        from Vision.StandardNodes import stdlib
        net.editor.addLibraryInstance(stdlib,"Vision.StandardNodes", "stdlib")
        # also, load vizlib
        importVizLib(net)

    def afterAddingToNetwork(self):
        from NetworkEditor.macros import MacroNode
        MacroNode.afterAddingToNetwork(self)
        ## loading libraries ##
        from symserv.VisionInterface.SymservNodes import symlib
        from Vision.StandardNodes import stdlib
        ## building macro network ##
        node0 = self
        node1 = node0.macroNetwork.ipNode
        node1.move(176, 14)
        node2 = node0.macroNetwork.opNode
        node2.move(197, 334)
        from symserv.VisionInterface.SymservNodes import Sym3FoldNE
        node3 = Sym3FoldNE(constrkw = {}, name='3-fold', library=symlib)
        node0.macroNetwork.addNode(node3,347,40)
        node3.inputPorts[1].widget.set(
            [0.57735026918962584, 0.57735026918962584, 0.57735026918962584],0)
        node3.inputPorts[2].widget.set([0.0, 0, 0],0)
        from symserv.VisionInterface.SymservNodes import Sym2FoldNE
        node4 = Sym2FoldNE(constrkw = {}, name='2-fold', library=symlib)
        node0.macroNetwork.addNode(node4,270,105)
        node4.inputPorts[1].widget.set([1.0, 0.0, 0.0],0)
        node4.inputPorts[2].widget.set([0.0, 0, 0],0)
        node4.inputPorts[3].widget.set(1)
        from symserv.VisionInterface.SymservNodes import Sym2FoldNE
        node5 = Sym2FoldNE(constrkw = {}, name='2-fold', library=symlib)
        node0.macroNetwork.addNode(node5,347,105)
        node5.inputPorts[1].widget.set([0.0, 0.0, 1.0],0)
        node5.inputPorts[2].widget.set([0.0, 0, 0],0)
        node5.inputPorts[3].widget.set(0)
        from symserv.VisionInterface.SymservNodes import Sym2FoldNE
        node6 = Sym2FoldNE(constrkw = {}, name='2-fold', library=symlib)
        node0.macroNetwork.addNode(node6,427,105)
        node6.inputPorts[1].widget.set([0.0, 1.0, 0.0],0)
        node6.inputPorts[2].widget.set([0.0, 0, 0],0)
        node6.inputPorts[3].widget.set(0)
        from symserv.VisionInterface.SymservNodes import SymMergeNE
        node7 = SymMergeNE(constrkw = {}, name='Merge', library=symlib)
        node0.macroNetwork.addNode(node7,347,173)
        from symserv.VisionInterface.SymservNodes import ApplyTransfToCoordsNE
        node8 = ApplyTransfToCoordsNE(
            constrkw = {}, name='Apply Transf to Coords', library=symlib)
        node0.macroNetwork.addNode(node8,146,232)
        from Vision.StandardNodes import Eval
        node9 = Eval(constrkw = {}, name='[0.0, 0.525, 0....', library=stdlib)
        node0.macroNetwork.addNode(node9,14,36)
        node9.inputPorts[0].widget.set("[0.0, 0.525, 0.851]",0)
        from Vision.StandardNodes import Operator2
        node10 = Operator2(constrkw = {}, name='mul', library=stdlib)
        node0.macroNetwork.addNode(node10,103,113)
        apply(node10.inputPorts[1].configure, (), {'datatype': 'float'})
        apply(node10.outputPorts[0].configure, (), {'datatype': 'list'})
        node10.inputPorts[2].widget.set("mul",0)
        node10.inputPorts[3].widget.set(1,0)
        from Vision.StandardNodes import Eval
        node11 = Eval(constrkw = {}, name='[in1]', library=stdlib)
        node0.macroNetwork.addNode(node11,103,174)
        apply(node11.inputPorts[1].configure, (), {'datatype': 'list'})
        node11.inputPorts[0].widget.set("[in1]",0)
        from NetworkEditor.items import NetworkNode
        from Vision.StandardNodes import Generic
        node12 = Generic(constrkw = {}, name='faces', library=stdlib)
        node0.macroNetwork.addNode(node12,431,185)
        apply(node12.addOutputPort, (),
              {'datatype': 'faceIndices', 'name': 'indices'})
        code = """def doit(self):
    self.outputData(indices=[
                     [10, 3, 8], [10, 8, 7], [10, 7, 11], [10, 11,9], [10, 9, 3],
                     [1, 4, 2], [1, 2, 0], [1, 0, 6], [1, 6, 5], [1, 5, 4],
                     [3, 5, 8], [8, 5, 6], [8, 6, 7], [7, 6, 0], [7, 0, 11],
                     [11, 0, 2], [11, 2, 9], [9, 2, 4], [9, 4, 3], [3, 4, 5] 
                     ])
"""
        node12.configure(function=code)
        node13 = Generic(constrkw = {}, name='edges', library=stdlib)
        node0.macroNetwork.addNode(node13,506,214)
        apply(node13.addOutputPort, (),
              {'datatype': 'indice2(0)', 'name': 'indices'})
        code = """def doit(self):
    self.outputData(indices=[ 
                     [0, 1], [1, 2], [0, 2], [0, 6], [6, 1], [0, 7], [7, 6],
                     [0, 11], [2, 11], [9, 4], [9, 3], [3, 4], [4, 5], [3, 5],
                     [9, 10], [3, 10], [3, 8], [5, 8], [8, 10], [10, 7], [8, 7],
                     [10, 11], [7, 11], [11, 9], [9, 2], [2, 4], [4, 1], [1, 5],
                     [5, 6], [6, 8] ])
"""
        node13.configure(function=code)

        ## saving connections for network IcosCage ##
        if node3 is not None and node4 is not None:
            node0.macroNetwork.connectNodes(
                node3, node4, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node3 is not None and node5 is not None:
            node0.macroNetwork.connectNodes(
                node3, node5, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node3 is not None and node6 is not None:
            node0.macroNetwork.connectNodes(
                node3, node6, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node4 is not None and node7 is not None:
            node0.macroNetwork.connectNodes(
                node4, node7, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node5 is not None and node7 is not None:
            node0.macroNetwork.connectNodes(
                node5, node7, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node6 is not None and node7 is not None:
            node0.macroNetwork.connectNodes(
                node6, node7, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node9 is not None and node10 is not None:
            node0.macroNetwork.connectNodes(
                node9, node10, "result", "data1", blocking=True, doNotSchedule=True)
        if node10 is not None and node11 is not None:
            node0.macroNetwork.connectNodes(
                node10, node11, "result", "in1", blocking=True, doNotSchedule=True)
        if node11 is not None and node8 is not None:
            node0.macroNetwork.connectNodes(
                node11, node8, "result", "coords", blocking=True, doNotSchedule=True)
        if node1 is not None and node10 is not None:
            node0.macroNetwork.connectNodes(
                node1, node10, "new", "data2", blocking=True, doNotSchedule=True)
        if node8 is not None and node2 is not None:
            node0.macroNetwork.connectNodes(
                node8, node2, "coords", "new", blocking=True, doNotSchedule=True)
        if node7 is not None and node8 is not None:
            node0.macroNetwork.connectNodes(
                node7, node8, "outMatrices", "matrices", blocking=True, doNotSchedule=True)
        if node12 is not None and node2 is not None:
            node0.macroNetwork.connectNodes(
                node12, node2, "indices", "new", blocking=True, doNotSchedule=True)
        if node13 is not None and node2 is not None:
            node0.macroNetwork.connectNodes(
                node13, node2, "indices", "new", blocking=True, doNotSchedule=True)

        ## modifying MacroOutputNode dynamic ports
        node2.inputPorts[1].configure(singleConnection=True)
        node2.inputPorts[2].configure(singleConnection=True)
        node2.inputPorts[3].configure(singleConnection=True)

        node0.shrink()
        ## reset modifications ##
        node0.resetTags()
        node0.buildOriginalList()



from Vision.VPE import NodeLibrary
symlib = NodeLibrary('SymServer', 'cyan')

symlib.addNode(SymHelixNE, 'Helix', 'Symmetry')
symlib.addNode(SymSuperHelixNE, 'SuperHelix', 'Symmetry')
symlib.addNode(SymRotNE, 'Rotate', 'Transformation')
symlib.addNode(SymOrientNE, 'Orient', 'Transformation')
symlib.addNode(SymTransNE, 'Translate', 'Transformation')
symlib.addNode(SymTransXYZNE, 'Transl. XYZ', 'Transformation')
symlib.addNode(SymScaleNE, 'Scale', 'Transformation')
symlib.addNode(Identity, 'Identity', 'Transformation')
symlib.addNode(AlignVectToVect, 'Vect2Vect', 'Transformation')
symlib.addNode(SymTransposeNE, 'Transpose', 'Transformation')
symlib.addNode(SymInverseNE, 'Inverse', 'Transformation')
symlib.addNode(PerurbVectorNE, 'PerurbVector', 'Transformations')

symlib.addNode(SymMultiplyNE, 'Multiply', 'Mapper')
symlib.addNode(SymMergeNE, 'Merge', 'Mapper')
symlib.addNode(SymNFoldNE, 'N-fold', 'Symmetry')
symlib.addNode(Sym2FoldNE, '2-fold', 'Symmetry')
symlib.addNode(Sym3FoldNE, '3-fold', 'Symmetry')
symlib.addNode(Sym4FoldNE, '4-fold', 'Symmetry') 
symlib.addNode(Sym5FoldNE, '5-fold', 'Symmetry') 
symlib.addNode(Sym6FoldNE, '6-fold', 'Symmetry') 
symlib.addNode(SymSplitNE, 'Split', 'Filter')
symlib.addNode(CoMassNE, 'Center of Mass', 'Mapper')
symlib.addNode(ApplyTransfToCoordsNE,'Apply Transf to Coords','Mapper')
symlib.addNode(DistanceToPoint,'DistanceToPoint','Mapper')
symlib.addNode(Dist2Points,'Dist2Points','Mapper')
symlib.addNode(PDBToMatrix,'PDBtoMatrix','Mapper')

symlib.addNode(Icos1,'Icosahedral1','Macro')
symlib.addNode(IcosCage,'IcosCage','Macro')

symlib.addNode(SaveToFile,'Save','I/O')
symlib.addNode(ReadFromFile,'Read','I/O')

symlib.addWidget(NEXYZVectGUI)

try:
    UserLibBuild.addTypes(symlib, 'MolKit.VisionInterface.MolKitTypes')
except Exception, e:
    print "unable to addTypes from MolKit %s\n" % e
