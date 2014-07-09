## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
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

from mglutil.math.rotax import rotax
from mglutil.math.transformation import Transformation
import numpy
import numpy.oldnumeric as Numeric, math, string


class SymNFold:
    """ vector: list of floats [x, y, z]
        point:  list of floats [x, y, z]
        symmetry int, >= 1
        identity: int, 0 or 1
        """
    
    def __init__(self, vector, point, symmetry, identity):
        self.set(vector, point, symmetry, identity)
        

    def getMatrices(self):
        angle=360.0/self.symmetry
        m=[]
        t=Numeric.array(self.point)*-1

        if self.identity == 1:
            mat = Numeric.identity(4).astype('f')
            m.append(mat)
               
        T = Transformation(trans=t)
        T1 = T.inverse()
        for i in range(self.symmetry-1):
            newList=[]
            newList.extend(list(self.vector))
            newList.append(angle)

            R = Transformation(quaternion=newList)
            
            mt = T1 * R * T
            #newmat = mt.getMatrix()
            newmat = mt.getDejaVuMatrix()
            m.append(newmat)
            angle=angle+360.0/self.symmetry
            
        return m


    def set(self, vector=None, point=None, symmetry=None, identity=None):
        if vector:
            assert len(vector)==3
            self.vector = Numeric.array(vector).astype('f')
        if point:
            assert len(point)==3
            self.point = Numeric.array(point).astype('f')
        if symmetry:
            assert symmetry >= 1
            self.symmetry = symmetry
        if identity is not None:
            assert identity in (0,1)
            self.identity = identity


    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymNFold(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        if applyIndex is given it should be a list of 0-based indices of
        matrices to which this operator's transformation will be applied.
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out
        

class SymTrans:

    def __init__(self, vector=(1.0, 0.0, 0.0), length=0.0, identity=0):
        self.vector = vector
        self.length = length
        self.identity = identity
        

    def getMatrices(self):
        m=[]
        mat=Numeric.identity(4).astype('f')

        if self.length is None or self.length == 0:
            m.append( Numeric.identity(4).astype('f') )
            return m

        if self.identity == 1:
            m.append( Numeric.identity(4).astype('f') )

        mat[:3, 3] = (self.vector*self.length).astype('f')
        m.append(mat)
        return m


    def set(self, vector=None, identity=None, length=None):
        if vector:
            assert len(vector)==3
            self.vector = Numeric.array(vector).astype('f')
        if identity is not None:
            assert identity in (0,1)
            self.identity = identity
        if length is not None:
            self.length = float(length)


    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymTrans(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out



class SymTransXYZ:

    def __init__(self, data, identity):
        self.set(data, identity)
    
    def set(self, data=None, identity=None):
        if data:
            assert len(data)==6
            self.vector1 = Numeric.array(data[3]).astype('f')*float(data[0])
            self.vector2 = Numeric.array(data[4]).astype('f')*float(data[1])
            self.vector3 = Numeric.array(data[5]).astype('f')*float(data[2])
        if identity is not None:
            assert identity in (0,1)
            self.identity = identity


    def getMatrices(self):
        m=[]
        t1=Numeric.array(self.vector1)#*-1  #FIXME: why did we do this?
        t2=Numeric.array(self.vector2)#*-1
        t3=Numeric.array(self.vector3)#*-1

        if self.identity == 1:
            mat = Numeric.identity(4).astype('f')
            m.append(mat)
            
       
        T1 = Transformation(trans=t1)
        T2 = Transformation(trans=t2)
        T3 = Transformation(trans=t3)
            
        mt = T1*T2*T3
        newmat = mt.getMatrix()
        m.append(newmat)
                    
        return m


    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymRot(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out



class SymRot:

    def __init__(self, vector, point, angle, identity):
        self.set(vector, point, angle, identity)
        

    def getMatrices(self):
        m=[]
        t=Numeric.array(self.point)*-1.
        if self.identity == 1:
            mat = Numeric.identity(4).astype('f')
            m.append(mat)
            
        newList=[]
        newList.extend(list(self.vector))
        newList.append(self.angle)
        
        T = Transformation(trans=t)
        R = Transformation(quaternion=newList)
             
        mt = T.inverse() * R * T
        newmat = mt.getMatrix()

        #TR = Transformation(trans=t, quaternion=newList)
        #newmat = TR.getMatrix()
        m.append(newmat)
                    
        return m


    def set(self, vector=None, point=None, angle=None, identity=None):
        if vector:
            assert len(vector)==3
            self.vector = Numeric.array(vector).astype('f')
        if point:
            assert len(point)==3
            self.point = Numeric.array(point).astype('f')
        if angle is None: self.angle = 0.0
        elif angle is not None:
            self.angle = angle
        if identity is not None:
            assert identity in (0,1)
            self.identity = identity


    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymRot(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out


class SymScale:

    def getMatrices(self, scaleFactor, selection=[1, 1, 1]):
        mat = Numeric.identity(4).astype('f')
        # apply scale factor to x, y and/or z

        if selection[0] not in [0, False]:
            mat[0][0] = scaleFactor
        else:
            mat[0][0] = 1.0

        if selection[1] not in [0, False]:
            mat[1][1] = scaleFactor
        else:
            mat[1][1] = 1.0

        if selection[2] not in [0, False]:
            mat[2][2] = scaleFactor
        else:
            mat[2][2] = 1.0

        return mat


    def __call__(self, inMatrices, scaleFactor, applyIndex=None, selection=[True,True,True]):
        """outMatrices <- SymScale(inMatrices, applyIndex=None, selection=[1,1,1])
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        (selection: scale x,y, and/or z) can be 1,True or 0,False)
        """
        
        if not inMatrices:
            inMatrices = [Numeric.identity(4).astype('f')]

        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices(scaleFactor, selection)
        out = []
        for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(im, ownmat) )
        return out


class SymHelix:
    """
Operator to build a stream of transforamtion matrices describing a helical
arrangment.

arguments:
    vector: the 3-D vector defining the oriention of the helical axis
    point:  a 3-D point defining the location in space of the helical axis
    angle:  angular value in degrees between 2 consecutive copies
    hrise: displacement along the helical axis between 2 consecutive copies
    copies: number of transformations
"""
    def __init__(self, vector, point, angle, hrise, copies):
        self.copies = 1
        self.hrise = 0
        self.angle = 0
        self.point = (0.,0.,0.)
        self.vector = (0.,1.,0.)
        self.set(vector=vector, point=point, angle=angle, hrise=hrise,
                 copies=copies)
        

    def normalize(self, v):
        nv = float(math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]))
        return (v[0]/nv, v[1]/nv, v[2]/nv)

    
    def set(self, vector=None, point=None, angle=None, hrise=None,
            copies=None):

        if vector is not None:
            assert len(vector)==3
            self.vector = self.normalize(vector)

        if point is not None:
            assert len(point)==3
            self.point = point
            
        if angle is not None:
            self.angle = angle*math.pi/180.
            
        if hrise is not None:
            self.hrise = hrise
            
        if copies is not None:
            assert copies >= 1
            self.copies=copies


    def getMatrices(self):
        matrices = []
        r = self.hrise
        v = self.vector
        p = self.point
        rv = (r*v[0], r*v[1], r*v[2])

        ## does not work .. some weird problem with the angle (MS)
        # build one increment of transformation
##         R = Transformation(
##             trans=[rv[0], rv[1], rv[2]],
##             quaternion=[v[0], v[1], v[2], self.angle*180/math.pi])
##         T = Transformation(trans=self.point)
##         transform1 = T * R * T.inverse()
##         transform = T * R * T.inverse()
##         matrices.append( transform.getMatrix() )
##         for i in range(self.copies-1):
##             transform = transform*transform1
##             matrices.append( transform.getMatrix() )

        # build rotation and translation matrix about helical axis going
        # rot matrix C style
        R = rotax( p, [p[0]+v[0], p[1]+v[1], p[2]+v[2]],
                   self.angle, False)
        riseMat = Numeric.identity(4).astype('f')
        riseMat[:3, 3] = rv # add the rise
        transform = Numeric.dot(riseMat, R)
        N = Numeric

        matrices.append( N.identity(4).astype('f'))
        for i in range(1,self.copies):
            mat = matrices[i-1]
            mat = Numeric.dot(mat, transform)
            matrices.append(mat)

        return matrices
 

    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymHelix(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out


class SymSuperHelix(SymHelix):
    """
    Build a stream of transforamtion matrices describing a super-helix

    helix 1 is the overall helical arangment
    helix 2 is the loca helical arrangement
    
    arguments: 
    vector: the 3-D vector defining the oriention of the helical axis
    point:  a 3-D point defining the location in space of the helical axis
    angle:  angular value in degrees between 2 consecutive copies
    hrise: displacement along the helical axis between 2 consecutive copies

    vector2: the 3-D vector defining the oriention of the helical axis
    point2:  a 3-D point defining the location in space of the helical axis
    angle2:  angular value in degrees between 2 consecutive copies
    hrise2: displacement along the helical axis between 2 consecutive copies
    copies: number of transformations
    """
    def __init__(self, vector, point, angle, hrise,
                 vector2, point2, angle2, hrise2, copies):

        SymHelix.__init__(self, vector, point, angle, hrise, copies)

        self.hrise2 = 0
        self.angle2 = 0
        self.point2 = (0.,0.,0.)
        self.vector2 = (0.,1.,0.)
        self.set(vector2=vector2, point2=point2, angle2=angle2,
                 hrise2=hrise2)


    def set(self, vector=None, point=None, angle=None, hrise=None,
            vector2=None, point2=None, angle2=None, hrise2=None, copies=None):

        SymHelix.set(self, vector=vector, point=point, angle=angle,
                     hrise=hrise, copies=copies)
            
        if vector2 is not None:
            print vector2
            assert len(vector2)==3
            self.vector2 = self.normalize(vector2)

        if point2 is not None:
            assert len(point2)==3
            self.point2 = point2
            
        if angle2 is not None:
            self.angle2 = angle2*math.pi/180.
            
        if hrise2 is not None:
            self.hrise2 = hrise2
            

    def getMatrices(self):
        pt1 = self.point
        v1 = self.vector
        r1 = self.hrise

        pt2 = self.point2
        v2 = self.vector2
        r2 = self.hrise2

        nbCopies = self.copies

        matrices1 = [] # overall helical transfomations
        matrices2 = [] # local helical transformations

        rv1 = (r1*v1[0], r1*v1[1], r1*v1[2]) # tanslation vector 1
        rv2 = (r2*v2[0], r2*v2[1], r2*v2[2]) # tanslation vector 2

        # rotation matrix for helix 1
        R = rotax( pt1, [pt1[0]+v1[0], pt1[1]+v1[1], pt1[2]+v1[2]],
                   self.angle, False)

        # rise transformation for helix 1
        riseMat1 = numpy.identity(4).astype('f')
        riseMat1[:3, 3] = rv1 # add the rise

        # helical step for helix 1
        transform1 = numpy.dot(riseMat1, R)

        # first transformation is didentity for both helices
        matrices1.append( numpy.identity(4).astype('f') )
        matrices2.append( numpy.identity(4).astype('f') )

        ang2 = self.angle2  # angle for helix 2
        # loop over number of copies
        for i in range(1,nbCopies):
            # take previous transfromation
            mat = matrices1[i-1]
            # add 1 helic step for overall helix
            mat = numpy.dot(mat, transform1)
            # save this in transformation for overall helix
            matrices1.append(mat)

            # move the point defining local helix along first helical axis
            p2t = (pt2[0]+(i*rv1[0]), pt2[1]+(i*rv1[1]), pt2[2]+(i*rv1[2]))

            # build local helix rotation
            R = rotax( p2t, [p2t[0]+v2[0], p2t[1]+v2[1], p2t[2]+v2[2]],
                       ang2, False)
            # build local helix raise
            riseMat2 = numpy.identity(4).astype('f')
            riseMat2[:3, 3] = rv2 # add the rise

            # build helical step for local helix 
            transform2 = numpy.dot(riseMat2, R)
            mat = matrices2[i-1]
            # apply step to previous helical step
            mat = numpy.dot(mat, transform2)
            matrices2.append(mat)

        # combine the overall helix wioth the local helix
        results = []
        results.append(numpy.identity(4).astype('f') )
        for i in range(1,nbCopies):
            results.append( numpy.dot(matrices2[i], matrices1[i]) )

        return results
 

    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymSuperHelix(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out


class SymMerge:

    def __init__(self):
        pass

    def getMatrices(self):
        pass

    def set(self):
        pass
    
    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymMerge(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        return inMatrices
        

class SymMultiply:
    """ SymMultiply multiplies incoming matrices and ouputs them.
        - 1 parent is multiplied with itself
        - 2 parents: two valid options: either one of the parents has
        lenght 1 (1 matrix) which is then multiplied to all other matrices
        of the second parent or both parents have the same amount of
        matrices. """


    def __init__(self):
        pass
    

    def getMatrices(self, matA, matB):

        matInA, matInB = self.set(matA, matB)

        #assert that matrices have either size 1, or equal size
        assert len(matInA) == 1 or len(matInB) == 1 or \
               len(matInA) == len(matInB)

        matrixOut = []

        #now the actual multiplication
	if len(matInA) == 1:
            for i in range(len(matInB)): #loop over node's incoming matrices
                matrixOut.append(Numeric.dot(matInA[0],
                                                           matInB[i]))

        elif len(matInB) == 1:
            for i in range(len(matInA)): #loop over node's incoming matrices
                matrixOut.append(Numeric.dot(matInA[i],
                                                           matInB[0]))


        else:
            for i in range(len(matInA)): #loop over node's incoming matrices
                matrixOut.append(Numeric.dot(matInA[i],
                                                           matInB[i]))

        return matrixOut


    def set(self, inA=None, inB=None):
        
        if inA is None and inB is not None:
            matInA = matInB = inB
        elif inA is not None and inB is None:
            matInA = matInB = inA
        elif inA is not None and inB is not None:
            matInA = inA
            matInB = inB
        elif inA is None and inB is None:
            matInA = matInB = Numeric.identity(4).astype('f') 

        return matInA, matInB


    def __call__(self, matA=None, matB=None):
        """outMatrices <- SymMerge(matA, matB)
        matA: list of 4x4 matrices
        matB: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        out = self.getMatrices(matA, matB)
        return out



class SymSplit:
    """unselected matrices of the incomming stream are sent to
output port 0, selected matrices are sent to additional output ports which get
created on selection.
selection is done by specifying matrices comma separated indices in the
incomming stream. Ranges can be specified using the ':' or '-'  character.
additional ports are created by using the ';' character.
"""


    def __init__(self, matrices, chars):
        self.set(matrices, chars)


    def set(self, matrices=None, chars=None):
        self.inMatrices = matrices
        self.indices = self.processString(chars)


    def processString(self, entry):
        split1=[]
        split2=[]
        l=[]
        ll=[]
        newList=[]
        split1=string.split(entry,';')
        i=0
        for i in range(len(split1)):
            l=string.split(split1[i],',')
            for item in l:
                try:
                    val=int(item)
                    ll.append(val)       
                except:        
                    for c in item:
                        if c == '-' or c == ':':
                            s=string.split(item,c)
                            newList=range(int(s[0]),int(s[1])+1)
                            for i in range(len(newList)):
                                ll.append(newList[i])

            split2.append(ll)
            ll=[]
        return split2


    def getMatrices(self):
        outMatrices=[]
        indicesComp = range(len(self.inMatrices))
        if self.indices[0] == []:
            self.indices[0] = indicesComp
            fullList = []
        else:
            fullList = Numeric.concatenate(self.indices)
            map( indicesComp.remove, fullList )
            self.indices.insert(0,indicesComp)

        for i in range(len(self.indices)):
            outMatrices.append(Numeric.take(self.inMatrices, self.indices[i]))
        return outMatrices


    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymSplit(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """
        if not inMatrices:
            outMatrices = [Numeric.identity(4).astype('f')]
        else:
            outMatrices = self.getMatrices()
        return outMatrices


class CenterOfMass:
    """ imputs xyz coords, outputs center of gravity """
    

    def __init__(self, coords):
        self.set(coords)


    def set(self, coords=None):
        self.coords = coords


    def compute(self):
        if self.coords is None:
            return [0., 0., 0.]
        else:
            self.coords=list(Numeric.sum(self.coords)/len(self.coords))
            return self.coords


    def __call__(self):
        return self.compute()
    
        
class SymOrient:
    """ rotation around center of gravity """

    def __init__(self, vector, angle, center, identity):
        self.set(vector, angle, center, identity)
        

    def getMatrices(self):
        m=[]
        newList=[]
        mat = Numeric.identity(4).astype('f')
        if self.identity == 1:
            m.append(mat)

        newList.extend(list(self.vector))
        newList.append(self.angle)
        t=Numeric.array(self.center)*-1
        
        T = Transformation(trans=t)
        R = Transformation(quaternion=newList)

        mt = T.inverse() * R * T
        newmat = mt.getMatrix()

        m.append(newmat)
        return m


    def set(self, vector=None, angle=None, center=None, identity=None):
        if vector:
            assert len(vector)==3
            self.vector = vector

        if angle is None: self.angle = 0.0
        elif angle is not None:
            self.angle=angle

        if center is None:
            center=[0.,0,0]
        self.center=center

        if identity is not None:
            assert identity in (0,1)
            self.identity = identity


    def __call__(self, inMatrices, applyIndex=None):
        """outMatrices <- SymOrient(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices: inMatrices = [Numeric.identity(4).astype('f')]
        matrices = Numeric.array(inMatrices)
        assert len(matrices.shape)==3
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
        ownmat = self.getMatrices()
        out = []
        for m in ownmat: # loop over this node's own transformation matrices
            for im in matrices: #loop over node's incoming matrices
                out.append( Numeric.dot(m, im) )
        return out




class ApplyTransfToCoords:
    """ applies matrices to coords and outputs transformed coords """

    def __init__(self, coords, matrices):
        pass

    def getMatrices(self):
        pass

    def set(self, coords=None, matrices=None):
        if coords is None: return
        else: self.coords = Numeric.array(coords).astype('f')
        if matrices is None:
            self.matrices = [Numeric.identity(4).astype('f')] 
        else:
            #assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4
            self.matrices = matrices

    
    def compute(self):
        newCoords=[]
        if self.coords is not None:
            one = Numeric.ones( (self.coords.shape[0], 1), \
                                self.coords.dtype.char )
            c = Numeric.concatenate( (self.coords, one), 1 )


            for m in range(len(self.matrices)):
                newCoords.append(Numeric.dot(c, \
                                   Numeric.transpose(self.matrices[m]))[:, :3])
            return Numeric.concatenate(newCoords)
        
            
    def __call__(self):
        return self.compute()
        


class PDBtoMatrix:
    """ inputs PDB file, parses MTRIXn records and returns a list of (4x4)
    matrices. MTRIXn is the default PDB standard, however not everybody seems
    to follow the standard, thus an optional keyword can be passed that
    describes the matrix records in this non-standard PDB file."""

    def __init__(self):
        pass


    def getMatrices(self, mol=None, keyword='MTRIX'):
        if mol is None:
            return

        matrices = []
        next = 0

        lines = mol.data[0].parser.allLines
        arr = Numeric.identity(4).astype('f')
    
        for l in lines:
            
            spl = string.split(l)
            if spl[0][:-1] != keyword: continue
            index = int(spl[0][-1:])-1

            arr[index][0] = float(spl[2])
            arr[index][1] = float(spl[3])
            arr[index][2] = float(spl[4])

            if index == 2:
                matrices.append(arr)
                arr = Numeric.identity(4).astype('f')
                
        return matrices



class SymTranspose:

    """ SymTranspose transposes all incomming matrices. """


    def __call__(self, inMatrices=None, applyIndex=None):
        """outMatrices <- SymTranspose(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        if not inMatrices:
            inMatrices = [Numeric.identity(4).astype('f')]

        matrices = Numeric.array(inMatrices)
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4

        out = []
        for im in matrices: #loop over node's incoming matrices
            out.append( Numeric.transpose(im) )
        return out

class SymInverse:

    """ SymInverse inverse all incomming matrices. """


    def __call__(self, inMatrices=None, applyIndex=None):
        """outMatrices <- SymInverse(inMatrices, applyIndex=None)
        inMatrices: list of 4x4 matrices
        outMatrices: list of 4x4 matrices
        """

        import numpy.oldnumeric.linear_algebra as LinearAlgebra 

        if not inMatrices:
            inMatrices = [Numeric.identity(4).astype('f')]

        matrices = Numeric.array(inMatrices)
        assert matrices.shape[-2] == 4 and matrices.shape[-1] == 4

        out = []
        for im in matrices: #loop over node's incoming matrices
            out.append( LinearAlgebra.inverse(im) )
        return out


class DistanceBetweenTwoPoints:

    """Compute the distance between two (x,y,z) points"""


    def __call__(self, point1, point2):
        """point1, point2
both must be (x,y,z) coordinates"""

        x1, y1, z1 = point1
        x2, y2, z2 = point2
        dist = math.sqrt( math.pow((x2-x1),2) + math.pow((y2-y1),2) + \
                          math.pow((z2-z1),2) )
        return dist
        

