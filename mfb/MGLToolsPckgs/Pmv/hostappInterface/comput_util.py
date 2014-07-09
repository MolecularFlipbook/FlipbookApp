## Automatically adapted for numpy.oldnumeric Apr 10, 2008 by
##
## Copyright (C) The Scripps Research Institute 2006
##
## Authors: Alexandre Gillet <gillet@scripps.edu>
##
## $Header: /opt/cvs/python/packages/share1.5/Pmv/hostappInterface/comput_util.py,v 1.22 2010/11/30 07:23:01 autin Exp $
## $Id: comput_util.py,v 1.22 2010/11/30 07:23:01 autin Exp $
##
##
## utils function use for computation during pattern detection


import numpy.oldnumeric as Numeric
from MolKit.pdbWriter import PdbWriter
#from MolKit.chargeCalculator import KollmanChargeCalculator,GasteigerChargeCalculator

from PyAutoDock.MolecularSystem import MolecularSystem
from PyAutoDock.AutoDockScorer import AutoDock305Scorer, AutoDock4Scorer
#from PyAutoDock.AutoDockScorer import AutoDockTermWeights305, AutoDockTermWeights4
#from PyAutoDock.trilinterp_scorer import TrilinterpScorer,TrilinterpScorer_AD3
from PyAutoDock.scorer import WeightedMultiTerm
from PyAutoDock.electrostatics import Electrostatics
from PyAutoDock.vanDerWaals import VanDerWaals,HydrogenBonding
#from PyAutoDock.vanDerWaals import HydrogenBonding
from PyAutoDock.desolvation import Desolvation

#import warnings

from MolKit.molecule import Atom

#######################MATH FUNCTION##########################################################
def transformedCoordinatesWithMatrice(mol,matrice):
    """ for a nodeset, this function returns transformed coordinates.
    This function will use the pickedInstance attribute if found.

    @type  mol: MolKit node
    @param mol: the molecule to be transfromed
    @type  matrice: 4x4array
    @param matrice: the matrix to apply to the molecule node

    @rtype:   array
    @return:  the transformed list of 3d points from the molecule atom coordinates
    """
    vt = []
    #transfo = matrice#Numeric.transpose(Numeric.reshape(pat.mat_transfo,(4,4)))
    scaleFactor = 1.#pat.scaleFactor
    #for node in nodes:
        #find all atoms and their coordinates
    coords = mol.allAtoms.coords# nodes.findType(Atom).coords
        #g = nodes[0].top.geomContainer.geoms['master']

#        M1 = g.GetMatrix(g.LastParentBeforeRoot())
        # apply the AR transfo matrix
    M = matrice#Numeric.dot(transfo,M1)
    for pt in coords:
            ptx = (M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3]) /scaleFactor
            pty = (M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3]) /scaleFactor
            ptz = (M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3]) /scaleFactor
            vt.append( (ptx, pty, ptz) )
    return vt

def rotatePoint(pt,m,ax):
      x=pt[0]
      y=pt[1]
      z=pt[2]
      u=ax[0]
      v=ax[1]
      w=ax[2]
      ux=u*x
      uy=u*y
      uz=u*z
      vx=v*x
      vy=v*y
      vz=v*z
      wx=w*x
      wy=w*y
      wz=w*z
      sa=sin(ax[3])
      ca=cos(ax[3])
      pt[0]=(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
      pt[1]=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
      pt[2]=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
      return pt

def matrixToEuler(mat):
    """
    code from 'http://www.euclideanspace.com/maths/geometry/rotations/conversions/'

    notes : this conversion uses conventions as described on page:
    'http://www.euclideanspace.com/maths/geometry/rotations/euler/index.htm'
    Coordinate System: right hand
    Positive angle: right hand
    Order of euler angles: heading first, then attitude, then bank
    matrix row column ordering:
    [m00 m01 m02]
    [m10 m11 m12]
    [m20 m21 m22]
    @type  mat: 4x4array
    @param mat: the matrix to convert in euler angle (heading,attitude,bank)

    @rtype:   3d array
    @return:  the computed euler angle from the matrice

     """
    #Assuming the angles are in radians.
    #3,3 matrix m[0:3,0:3]
    #return heading,attitude,bank Y,Z,X
    import math
    if (mat[1][0] > 0.998) : # singularity at north pole
        heading = math.atan2(mat[0][2],mat[2][2])
        attitude = math.pi/2.
        bank = 0
        return (heading,attitude,bank)
    if (mat[1][0] < -0.998) : # singularity at south pole
        heading = math.atan2(mat[0][2],mat[2][2])
        attitude = -math.pi/2.
        bank = 0
        return (heading,attitude,bank)
    heading = math.atan2(-mat[2][0],mat[0][0])
    bank = math.atan2(-mat[1][2],mat[1][1])
    attitude = math.asin(mat[1][0])
    if mat[0][0] < 0 :
	if (attitude < 0.) and (math.degrees(attitude) > -90.):
		attitude = -math.pi-attitude
	elif (attitude > 0.) and (math.degrees(attitude) < 90.):
		attitude = math.pi-attitude
    return (heading,attitude,bank)

def eulerToMatrix(euler): #double heading, double attitude, double bank
    """
    code from 'http://www.euclideanspace.com/maths/geometry/rotations/conversions/'.
    this conversion uses NASA standard aeroplane conventions as described on page:
    'http://www.euclideanspace.com/maths/geometry/rotations/euler/index.htm'

    Coordinate System: right hand

    Positive angle: right hand

    Order of euler angles: heading first, then attitude, then bank

    matrix row column ordering:

    [m00 m01 m02]

    [m10 m11 m12]

    [m20 m21 m22]

    @type euler:   3d array
    @param euler:  the euler angle to convert in matrice

    @rtype: 4x4array
    @return: the matrix computed from the euler angle

    """
    # Assuming the angles are in radians.
    import math
    heading=euler[0]
    attitude=euler[1]
    bank=euler[2]
    m=[[ 1.,  0.,  0.,  0.],
       [ 0.,  1.,  0.,  0.],
       [ 0.,  0.,  1.,  0.],
       [ 0.,  0.,  0.,  1.]]
    ch = math.cos(heading)
    sh = math.sin(heading)
    ca = math.cos(attitude)
    sa = math.sin(attitude)
    cb = math.cos(bank)
    sb = math.sin(bank)
    m[0][0] = ch * ca
    m[0][1] = sh*sb - ch*sa*cb
    m[0][2] = ch*sa*sb + sh*cb
    m[1][0] = sa
    m[1][1] = ca*cb
    m[1][2] = -ca*sb
    m[2][0] = -sh*ca
    m[2][1] = sh*sa*cb + ch*sb
    m[2][2] = -sh*sa*sb + ch*cb
    return m

rotY90n = Numeric.array([[ 0.,  0.,  1.,  0.],
                        [ 0.,  1., 0.,  0.],
                        [ 1.,  0., 0.,  0.],
                        [ 0.,  0.,  0.,  1.]],'f')


def ApplyMatrix(coords,mat):
    """
    Apply the 4x4 transformation matrix to the given list of 3d points

    @type  coords: array
    @param coords: the list of point to transform.
    @type  mat: 4x4array
    @param mat: the matrix to apply to the 3d points

    @rtype:   array
    @return:  the transformed list of 3d points
    """

    #4x4matrix"
    coords = Numeric.array(coords)
    one = Numeric.ones( (coords.shape[0], 1), coords.dtype.char )
    c = Numeric.concatenate( (coords, one), 1 )
    return Numeric.dot(c, Numeric.transpose(mat))[:, :3]


def Decompose4x4(matrix):
    """
    Takes a matrix in shape (16,) in OpenGL form (sequential values go
    down columns) and decomposes it into its rotation (shape (16,)),
    translation (shape (3,)), and scale (shape (3,))

    @type  matrix: 4x4array
    @param matrix: the matrix to decompose

    @rtype:   list of array
    @return:  the decomposition of the matrix ie : rotation,translation,scale
    """
    m = matrix
    transl = Numeric.array((m[12], m[13], m[14]), 'f')
    scale0 = Numeric.sqrt(m[0]*m[0]+m[4]*m[4]+m[8]*m[8])
    scale1 = Numeric.sqrt(m[1]*m[1]+m[5]*m[5]+m[9]*m[9])
    scale2 = Numeric.sqrt(m[2]*m[2]+m[6]*m[6]+m[10]*m[10])
    scale = Numeric.array((scale0,scale1,scale2)).astype('f')
    mat = Numeric.reshape(m, (4,4))
    rot = Numeric.identity(4).astype('f')
    rot[:3,:3] = mat[:3,:3].astype('f')
    rot[:,0] = (rot[:,0]/scale0).astype('f')
    rot[:,1] = (rot[:,1]/scale1).astype('f')
    rot[:,2] = (rot[:,2]/scale2).astype('f')
    rot.shape = (16,)
    #rot1 = rot.astype('f')
    return rot, transl, scale


def rotatePoint(pt,m,ax):
    """
    rotate a point (x,y,z) arount an axis by alha degree.

    @type  pt: point
    @param pt: the point to rotate
    @type  m: array
    @param m: translation offset to apply after the rotation
    @type  ax: vector4D
    @param ax: axise of rotation (ax[0:3]) and the angle of rotation (ax[3])

    @rtype:   point
    @return:  the new rotated point
    """

    x=pt[0]
    y=pt[1]
    z=pt[2]
    u=ax[0]
    v=ax[1]
    w=ax[2]
    ux=u*x
    uy=u*y
    uz=u*z
    vx=v*x
    vy=v*y
    vz=v*z
    wx=w*x
    wy=w*y
    wz=w*z
    sa=sin(ax[3])
    ca=cos(ax[3])
    pt[0]=(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
    pt[1]=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
    pt[2]=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
    return pt

def norm(A):
    """Return vector norm"""
    return Numeric.sqrt(sum(A*A))

def dist(A,B):
    """Return distnce between point A and point B"""
    return Numeric.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)

def normsq(A):
    """Return square of vector norm"""
    return abs(sum(A*A))

def normalize(A):
    """Normalize the Vector A"""
    if (norm(A)==0.0) : return A
    else :return A/norm(A)

def getCenter(coords):
    """
    Get the center from a 3d array of coordinate x,y,z.

    @type  coords: liste/array
    @param coords: the coordinates

    @rtype:   list/array
    @return:  the center of mass of the coordinates
    """
    coords = Numeric.array(coords)#self.allAtoms.coords
    center = sum(coords)/(len(coords)*1.0)
    center = list(center)
    for i in range(3):
        center[i] = round(center[i], 4)
    #print "center =", self.center
    return center

def computeRadius(protein,center=None):
    """
    Get the radius of gyration of a protein.

    @type  protein: MolKit Protein
    @param protein: the molecule
    @type  center: list/array
    @param center: the center of the molecule

    @rtype:   float
    @return:  the radius of the molecule
    """

    if center == None : center = protein.getCenter()
    rs = 0.
    for atom in protein.allAtoms:
        r = dist(center,atom._coords[0])
        if r > rs:
            rs = r
    return rs

def convertColor(col,toint=True):
    """
    This function will convert a color array [r,g,b] from range 1-255 
    to range 0.-1 (vice/versa)
    
    @type  col: array
    @param col: the color [r,g,b]
    @type  toint: boolean
    @param toint: way of the convertion, if true convert to 1-255, if false
    convert to range 0-1
   
    @rtype:   array
    @return:  the converted color [0-1.,0-1.,0-1.] or [1-255,1-255,1-255]
    """

    if toint and max(col)<=1.0: col = map( lambda x: x*255, col)
    elif not toint and max(col)>1.0: col = map( lambda x: x/255., col)
    return col

DGatomIds=['ASPOD1','ASPOD2','GLUOE1','GLUOE2', 'SERHG',
                        'THRHG1','TYROH','TYRHH',
                        'LYSNZ','LYSHZ1','LYSHZ2','LYSHZ3','ARGNE','ARGNH1','ARGNH2',
                        'ARGHH11','ARGHH12','ARGHH21','ARGHH22','ARGHE','GLNHE21',
                        'GLNHE22','GLNHE2',
                        'ASNHD2','ASNHD21', 'ASNHD22','HISHD1','HISHE2' ,
                        'CYSHG', 'HN']

def lookupDGFunc(atom):
    assert isinstance(atom, Atom)
    if atom.name in ['HN']:
        atom.atomId = atom.name
    else:
        atom.atomId=atom.parent.type+atom.name
    if atom.atomId not in DGatomIds: 
        atom.atomId=atom.element
    return atom.atomId.upper()

def norm(A):
    "Return vector norm"
    return Numeric.sqrt(sum(A*A))

def dist(A,B):
    return Numeric.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)

def normsq(A):
    "Return square of vector norm"
    return abs(sum(A*A))

def normalize(A):
    "Normalize the Vector"
    if (norm(A)==0.0) : return A
    else :return A/norm(A)

def changeR(txt):
    from Pmv.pmvPalettes import RasmolAminoSortedKeys
    from MolKit.protein import ResidueSetSelector
    #problem this residue not in r_keyD
    rname = txt[0:3]
    rnum = txt[3:]
    if rname not in RasmolAminoSortedKeys :#ResidueSetSelector.r_keyD.keys() :
        print rname
        rname=rname.replace(" ","")
        if len(rname) == 1 : 
            return rname+rnum
        return rname[1]+rnum
    else :
        rname=rname.replace(" ","")
        r1n=ResidueSetSelector.r_keyD[rname]
        return r1n+rnum

def patchRasmolAminoColor():
    from Pmv.pmvPalettes import RasmolAmino,RasmolAminoSortedKeys
    RasmolAminocorrected=RasmolAmino.copy()
    for res in RasmolAminoSortedKeys:
        name=res.strip()
        if name in ['A', 'C', 'G', 'T', 'U']:
            name = 'D'+name
            RasmolAminocorrected[name]= RasmolAmino[res]
            del RasmolAminocorrected[res]    
    return RasmolAminocorrected
    
#######################ENERGY CLASS & FUNCTION##########################################################
class EnergyHandler:
    """ object to manage the different energies calculation between set of atoms """

    def __init__(self,viewer):

        self.viewer = viewer
        # list the energies instance to manage
        self.data = {} # keys name, values: energie classs instance
        self.current_scorer = None
        self.realTime = True

    def add(self,atomset1,atomset2,score_type='c_ad3Score',**kw):
        """ a pairs of atoms to get energies between them
        should be receptor ligan
        """
        # make name from molecule name of each atom set instance
        n1 = atomset1.top.uniq()[0].name
        n2 = atomset2.top.uniq()[0].name
        n = n1+'-'+n2+'-'+score_type

        if self.viewer.hasGui : self.viewer.infoBox.Set(visible=True)
        # we test if energy scorer already been setup
        if self.data.has_key(n):
            self.current_scorer = self.data[n]
            return self.data[n]

        # we create a energy scorer for pairs of atoms
        if score_type == 'PairWise':
            nrg = PairWiseEnergyScorer(atomset1,atomset2)
        elif score_type == 'Trilinterp':
            nrg = TrilinterpEnergyScorer(atomset1,atomset2,stem=kw.get('stem'),atomtypes=kw.get('atomtypes'))
        elif score_type == 'TrilinterpAD3':
            nrg = TrilinterpEnergyScorerAD3(atomset1,atomset2,stem=kw.get('stem'),atomtypes=kw.get('atomtypes'))
        elif score_type == 'PyPairWise':
            nrg = PyPairWiseEnergyScorer(atomset1,atomset2)
        elif score_type == 'ad3Score':
            nrg = PyADCalcAD3Energies(atomset1,atomset2)
        elif score_type == 'ad4Score':
            nrg = PyADCalcAD4Energies(atomset1,atomset2)
        elif score_type == 'c_ad3Score':
            nrg = cADCalcAD3Energies(atomset1,atomset2)
        elif score_type == 'c_ad4Score':
            nrg = cADCalcAD4Energies(atomset1,atomset2)
        self.data[n]=nrg

        self.current_scorer = nrg

        if self.viewer.hasGui:
            self.viewer.GUI.nrg_pairs_combobox.setlist(self.data.keys())
            self.viewer.GUI.nrg_pairs_combobox.setentry(self.data.keys()[0])


        return nrg

    def reset(self):
        """ delete all the atoms pairs """
        self.current_scorer = None
        if self.viewer.hasGui:
            self.viewer.GUI.nrg_pairs_combobox.setlist(self.data.keys())

        ## ATTENTION the following code do create a segmentation fault
        ## FIX ME   AG 04/2007
##         # free up allocate memory for each nengy scorer
##         for scorer in self.data.values():
##             scorer.free_memory()
##             del(scorer)
##         self.data.clear()

    def compute_energies(self):
        """ retrieve the score for each pairs """
        sc = self.current_scorer
        if sc is None: return
        #if sc.mol1 in self.viewer.mol_detected.keys() and sc.mol2 in self.viewer.mol_detected.keys():
        score,estat,hbond,vdw,ds = sc.doit()
        from Pmv.moleculeViewer import EditAtomsEvent
        #editAtom event ? just to check ?
        #event = EditAtomsEvent('coords', sc.mol2.allAtoms)
        #self.viewer.dispatchEvent(event)

        if self.viewer.hasGui:
            self.viewer.infoBox.update_entry(score=score,estat=estat,hbond=hbond,
                                             vdw=vdw,ds=ds)
        return True

    def save_conformations(self):
        for nrg in self.data.values():
            nrg.saveCoords()

cAD=True
try:
    from cAutoDock import scorer as c_scorer
    from memoryobject import memobject
except:
    cAD = False
    memobject = None
    c_scorer = None

class EnergyScorer:
    """ Base class for energie scorer """

    def __init__(self,atomset1,atomset2,func=None):

        self.atomset1 =atomset1
        self.atomset2 =atomset2

        # save molecule instance of parent molecule
        self.mol1 =  self.atomset1.top.uniq()[0]
        self.mol2 =  self.atomset2.top.uniq()[0]
        # dictionnary to save the state of each molecule when the
        # energie is calculated, will allow to retrieve the conformation
        # use for the energie calculation
        # keys are score,values is a list a 2 set of coords (mol1,mol2)
        self.confcoords = {}
        self.ms = ms = MolecularSystem()
        self.cutoff = 1.0
        self.score  = 0.0


    def doit(self):

        self.update_coords()
        score,estat,hbond,vdw,ds= self.get_score()
        self.score = score
        self.saveCoords(score)
        self.atomset1.setConformation(0)
        self.atomset2.setConformation(0)
        return (score,estat,hbond,vdw,ds)

    def update_coords(self):
        """ methods to update the coordinate of the atoms set """
        pass

    def get_score(self):
        """ method to get the score """
        score = estat =  hbond = vdw = ds =  1000.
        return (score,estat,hbond,vdw,ds)


    def saveCoords(self,score):
        """methods to store each conformation coordinate.
         the score is use as the key of a dictionnary to store the different conformation.
         save the coords of the molecules to be use later to write out
         a pdb file
         We only save up 2 ten conformations per molecule. When 10 is reach we delete the one with the
         highest energie
         """
        score_int= int(score*100)
        # check number of conf save
        if len(self.confcoords.keys()) >= 50:
            # find highest energies
            val =max(self.confcoords.keys())
            del(self.confcoords[val])

        # add new conformation
        coords = [self.atomset1.coords[:],self.atomset2.coords[:]]
        self.confcoords[score_int] = coords

    def writeCoords(self,score=None,filename1=None,filename2=None,
                    sort=True, transformed=False,
                    pdbRec=['ATOM', 'HETATM', 'CONECT'],
                    bondOrigin='all', ssOrigin=None):
        """ write the coords of the molecules in pdb file
        pdb is file will have the molecule name follow by number of conformation
        """
        writer = PdbWriter()
        if score is None:
            score = min( self.confcoords.keys())
        if not self.confcoords.has_key(float(score)): return

        c1 = self.confcoords[score][0]
        c2 = self.confcoords[score][1]

        if filename1 is None:
            filename1 = self.mol1.name + '_1.pdb'
        prev_conf = self.setCoords(self.atomset1,c1)

        writer.write(filename1, self.atomset1, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)

        self.atomset1.setConformation(prev_conf)

        if filename2 is None:
            filename2 = self.mol2.name + '_1.pdb'

        prev_conf = self.setCoords(self.atomset2,c2)
        writer.write(filename2, self.atomset2, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)
        self.atomset2.setConformation(prev_conf)

    def setCoords(self,atomset,coords):
        """ set the coords to a molecule """
        mol = atomset.top.uniq()[0]
        prev_conf = atomset.conformation[0]
        # number of conformations available
        confNum = len(atomset[0]._coords)
        if hasattr(mol, 'nrgCoordsIndex'):
            # uses the same conformation to store the transformed data
            atomset.updateCoords(coords,
                                 mol.nrgCoordsIndex)
        else:
            # add new conformation to be written to file
            atomset.addConformation(coords)
            mol.nrgCoordsIndex = confNum
        atomset.setConformation( mol.nrgCoordsIndex )
        return prev_conf

    def free_memory(self):
        """ Method to free memory allocate by scorer
        Should be implemented """

        pass




class TrilinterpEnergyScorer(EnergyScorer):
    """ Scorer using the trilinterp method, base on autogrid
    """

    def __init__(self,atomset1,atomset2,stem, atomtypes):
        """
        based on AD4 scoring function:
        stem (string) and atomtypes list (list of string)2 specify filenames for maps
        value_outside_grid is energy penalty for pts outside box
        atoms_to_ignore are assigned 0.0 energy: specifically
        added to avoid huge energies from atoms bonded to flexible residues
        """

        EnergyScorer.__init__(self,atomset1,atomset2)
        self.l = self.ms.add_entities(self.atomset2)
        #eg: stem = 'hsg1', atomtypes= ['C','A','HD','N','S']
        scorer = self.scorer = TrilinterpScorer(stem, atomtypes,readMaps=True)
        self.scorer.set_molecular_system(self.ms)
	self.prop='Trilinterp'
        self.scorer.prop = self.prop
        self.grid_obj = None

    def set_grid_obj(self,grid_obj):
        self.grid_obj = grid_obj

    def update_coords(self):
        """ update the coords """
        if hasattr(self.mol1,'cconformationIndex'):
            self.atomset1.setConformation(self.mol1.cconformationIndex)
        confNum = 0
        if hasattr(self.mol2,'cconformationIndex'):
            self.atomset2.setConformation(self.mol2.cconformationIndex)
            confNum = self.mol2.cconformationIndex

        # transform ligand coord with grid.mat_transfo_inv
        # put back the ligand in grid space
        #print "dans update coord nrg"
        #print  self.mol2.allAtoms.coords
        if hasattr(self.grid_obj,'mat_transfo_inv'):
            M = self.grid_obj.mat_transfo_inv
            vt = []
            for pt in self.mol2.allAtoms.coords:
                ptx = (M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3])
                pty = (M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3])
                ptz = (M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3])
                vt.append( (ptx, pty, ptz) )
            self.mol2.allAtoms.updateCoords(vt,ind=confNum)
            #print  vt

    def get_score(self):
        # labels atoms
        score_array,terms_dic = self.scorer.get_score_array()
        self.scorer.labels_atoms_w_nrg(score_array)

	self.score =score= min(Numeric.add.reduce(score_array),100.)
	#self.score =score= min(self.scorer.get_score(),100.)
	terms_score = terms_dic
        estat = min(round(Numeric.add.reduce(terms_score[0]),2),1000.)
        hbond = 0.#min(round(terms_score['m'],2),1000.)
        vdw   = min(round(Numeric.add.reduce(terms_score[1]),2),1000.)
        ds    = min(round(Numeric.add.reduce(terms_score[2]),2),1000.) #problem with ds

        #ds=ds-ds
	#self.score = self.score -ds

        return (score,estat,hbond,vdw,ds)

class TrilinterpEnergyScorerAD3(EnergyScorer):
    """ Scorer using the trilinterp method, base on autogrid
    """

    def __init__(self,atomset1,atomset2,stem, atomtypes):
        """
        based on AD4 scoring function:
        stem (string) and atomtypes list (list of string)2 specify filenames for maps
        value_outside_grid is energy penalty for pts outside box
        atoms_to_ignore are assigned 0.0 energy: specifically
        added to avoid huge energies from atoms bonded to flexible residues
        """

        EnergyScorer.__init__(self,atomset1,atomset2)
        self.l = self.ms.add_entities(self.atomset2)
        #eg: stem = 'hsg1', atomtypes= ['C','A','HD','N','S']
        scorer = self.scorer = TrilinterpScorer_AD3(stem, atomtypes)
        self.scorer.set_molecular_system(self.ms)
        self.prop = 'Trilinterp'
        self.grid_obj = None

    def set_grid_obj(self,grid_obj):
        self.grid_obj = grid_obj

    def update_coords(self):
        """ update the coords """
        if hasattr(self.mol1,'cconformationIndex'):
            self.atomset1.setConformation(self.mol1.cconformationIndex)
        confNum = 0
        if hasattr(self.mol2,'cconformationIndex'):
            self.atomset2.setConformation(self.mol2.cconformationIndex)
            confNum = self.mol2.cconformationIndex

        # transform ligand coord with grid.mat_transfo_inv
        # put back the ligand in grid space
        #print "dans update coord nrg"
        #print  self.mol2.allAtoms.coords
        if hasattr(self.grid_obj,'mat_transfo_inv'):
            M = self.grid_obj.mat_transfo_inv
            vt = []
            for pt in self.mol2.allAtoms.coords:
                ptx = (M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3])
                pty = (M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3])
                ptz = (M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3])
                vt.append( (ptx, pty, ptz) )
            self.mol2.allAtoms.updateCoords(vt,ind=confNum)
            #print  vt

    def get_score(self):
        score = self.scorer.get_score()
        estat = 0.0
        hbond = 0.0
        vdw   = 0.0
        ds    = 0.0

        return (score,estat,hbond,vdw,ds)

class PairWiseEnergyScorer(EnergyScorer):
    """For each atom in one AtomSet, determine the electrostatics eneregy vs all the atoms in a second
    AtomSet using the C implementation of the autodock scorer.
    When using the autodock3 scorer, the receptor need to be loaded as a pdbqs file, the ligand as pdbqt.
    """


    def __init__(self,atomset1,atomset2,scorer_ad_type='305'):


        EnergyScorer.__init__(self,atomset1,atomset2)
        self.prop = 'ad305_energy'
        self.ms = ms = c_scorer.MolecularSystem()
        self.receptor= self.pyMolToCAtomVect(atomset1)
        self.ligand  = self.pyMolToCAtomVect(atomset2)

        self.r = ms.add_entities(self.receptor)
        self.l = ms.add_entities(self.ligand)

        ms.build_bonds( self.r )
        ms.build_bonds( self.l )
        # Notice: keep references to the terms !
        # or they will be garbage collected.
        self.scorer_ad_type = scorer_ad_type
        if self.scorer_ad_type == '305':
            self.ESTAT_WEIGHT_AUTODOCK = 0.1146 # electrostatics
            self.HBOND_WEIGHT_AUTODOCK = 0.0656 # hydrogen bonding
            self.VDW_WEIGHT_AUTODOCK   = 0.1485 # van der waals
            self.DESOLV_WEIGHT_AUTODOCK= 0.1711 # desolvation


        ## !!! Make sure that all the terms are save and not free after init is done
        ## use self.
        self.estat = c_scorer.Electrostatics(ms)
        self.hbond = c_scorer.HydrogenBonding(ms)
        self.vdw   = c_scorer.VanDerWaals(ms)
        self.ds    = c_scorer.Desolvation(ms)
        self.scorer = c_scorer.WeightedMultiTerm(ms)
        self.scorer.add_term(self.estat, self.ESTAT_WEIGHT_AUTODOCK)
        self.scorer.add_term(self.hbond, self.HBOND_WEIGHT_AUTODOCK)
        self.scorer.add_term(self.vdw,   self.VDW_WEIGHT_AUTODOCK)
        self.scorer.add_term(self.ds,    self.DESOLV_WEIGHT_AUTODOCK)
        # shared memory, used by C++ functions
        self.proteinLen = len(atomset1)
        self.ligLen = len(atomset2)
        self.msLen =  self.proteinLen + self.ligLen
        self.sharedMem = memobject.allocate_shared_mem([self.msLen, 3],
                                                       'SharedMemory', memobject.FLOAT)
        self.sharedMemPtr = memobject.return_share_mem_ptr('SharedMemory')[0]
        #print "Shared memory allocated.."


    def update_coords(self):
        """ update the coordinate of atomset """

        # use conformation set by dectected patterns
        if hasattr(self.mol1,'cconformationIndex'):
            self.atomset1.setConformation(self.mol1.cconformationIndex)
        if hasattr(self.mol2,'cconformationIndex'):
            self.atomset2.setConformation(self.mol2.cconformationIndex)
        # get the coords
        R_coords  = self.atomset1.coords
        L_coords =  self.atomset2.coords

        self.sharedMem[:] = Numeric.array(R_coords+L_coords, 'f')[:]

        c_scorer.updateCoords(self.proteinLen, self.msLen, self.ms,self.sharedMemPtr)

    def get_score(self):
        """ return the score """

        mini = self.ms.check_distance_cutoff(0, 1, self.cutoff)

        # when number return should not do get_score ( proteins too close)
        # flag = (mini==1.0 and mini==2.0)
        flag =  (mini == mini)

        # for each of the terms and the score, we cap their max value to 100
        # so if anything is greater than 100 we assign 100
        # If their is bad contact score = 1000.

        if flag: # if any distance < cutoff : no scoring
            #self.score = min(9999999.9, 9999.9/mini)
            self.score = 1000.
            estat =  hbond = vdw = ds =  1000.
        else:
            self.score = min(self.scorer.get_score(),100.)

            estat = min(round(self.estat.get_score() * self.ESTAT_WEIGHT_AUTODOCK,2),1000.)
            hbond = min(round(self.hbond.get_score() * self.HBOND_WEIGHT_AUTODOCK,2),1000.)
            vdw   = min(round(self.vdw.get_score()   * self.VDW_WEIGHT_AUTODOCK,2),1000.)
            ds    = min(round(self.ds.get_score()    * self.DESOLV_WEIGHT_AUTODOCK,2),1000.)
            #print "--",estat,hbond,vdw,ds

        return (self.score,estat,hbond,vdw,ds)



    def pyMolToCAtomVect( self,mol):
        """convert Protein or AtomSet to AtomVector
        """
        try :
            from cAutoDock.scorer import AtomVector, Atom, Coords
        except :
            pass
        className = mol.__class__.__name__
        if className == 'Protein':
            pyAtoms = mol.getAtoms()
        elif className == 'AtomSet':
            pyAtoms = mol
        else:
            return None
        pyAtomVect = AtomVector()
        for atm in pyAtoms:
            a=Atom()
            a.set_name(atm.name)
            a.set_element(atm.autodock_element)# aromatic type 'A', vs 'C'
            coords=atm.coords
            a.set_coords( Coords(coords[0],coords[1],coords[2]))
            a.set_charge( atm.charge)
            try:
                a.set_atvol( atm.AtVol)
            except:
                pass
            try:
                 a.set_atsolpar( atm.AtSolPar)
            except:
                pass
            a.set_bond_ord_rad( atm.bondOrderRadius)
            a.set_charge( atm.charge)
            pyAtomVect.append(a)
        return pyAtomVect

    def free_memory(self):
        # free the shared memory
        memobject.free_shared_mem("SharedMemory")




from AutoDockTools.pyAutoDockCommands import pep_aromList

class PyADCalcAD3Energies(EnergyScorer):
    """For each atom in one AtomSet, determine the autodock3 energy vs all the atoms in a second
    AtomSet
    """

    def __init__(self,atomset1,atomset2):
        """ """
        EnergyScorer.__init__(self,atomset1,atomset2)
        self.weight = None
        self.weightLabel = None

        self.scorer = AutoDock305Scorer()
        self.prop = self.scorer.prop

        bothAts = atomset1 + atomset2
        for a in bothAts:
            if a.parent.type + '_' + a.name in pep_aromList:
                a.autodock_element=='A'
                a.AtSolPar = .1027
            elif a.autodock_element=='A':
                a.AtSolPar = .1027
            elif a.autodock_element=='C':
                a.AtSolPar = .6844
            else:
                a.AtSolPar = 0.0


        self.r = self.ms.add_entities(atomset1)
        self.l = self.ms.add_entities(atomset2)
        self.scorer.set_molecular_system(self.ms)

    def update_coords(self):
        """ update the coords """
        if hasattr(self.mol1,'cconformationIndex'):
            self.atomset1.setConformation(self.mol1.cconformationIndex)
        if hasattr(self.mol2,'cconformationIndex'):
            self.atomset2.setConformation(self.mol2.cconformationIndex)

        for ind in (self.r,self.l):
            # clear distance matrix
            self.ms.clear_dist_mat(ind)

    def get_score(self):

        score = self.scorer.get_score()
        terms_score = []
        for t,w in self.scorer.terms:
            terms_score.append(w*t.get_score())

        estat = min(round(terms_score[0]),1000.)
        hbond = min(round(terms_score[1]),1000.)
        vdw   = min(round(terms_score[2]),1000.)
        ds    = min(round(terms_score[3]),1000.)

        # labels atoms
        score_array = self.scorer.get_score_array()
        self.scorer.labels_atoms_w_nrg(score_array)

        return (score,estat,hbond,vdw,ds)

class PyADCalcAD4Energies(EnergyScorer):
    """For each atom in one AtomSet, determine the autodock4 energy vs all the atoms
    in a second AtomSet
    """

    def __init__(self,atomset1,atomset2):
        """ """
        EnergyScorer.__init__(self,atomset1,atomset2)
        self.weight = None
        self.weightLabel = None

        self.scorer = AutoDock4Scorer()
        self.prop = self.scorer.prop

        self.r = self.ms.add_entities(atomset1)
        self.l = self.ms.add_entities(atomset2)
        self.scorer.set_molecular_system(self.ms)

    def update_coords(self):
        """ update the coords """
        if hasattr(self.mol1,'cconformationIndex'):
            self.atomset1.setConformation(self.mol1.cconformationIndex)
        if hasattr(self.mol2,'cconformationIndex'):
            self.atomset2.setConformation(self.mol2.cconformationIndex)

        for ind in (self.r,self.l):
            # clear distance matrix
            self.ms.clear_dist_mat(ind)

    def get_score(self):
        score = self.scorer.get_score()
        terms_score = []
        for t,w in self.scorer.terms:
            terms_score.append(w*t.get_score())

        estat = min(round(terms_score[0]),1000.)
        hbond = min(round(terms_score[1]),1000.)
        vdw   = min(round(terms_score[2]),1000.)
        ds    = min(round(terms_score[3]),1000.)
        self.scores = [estat,hbond,vdw,ds]
        # labels atoms
        score_array = self.scorer.get_score_array()
        self.scorer.labels_atoms_w_nrg(score_array)

        return (score,estat,hbond,vdw,ds)
if cAD:
    from cAutoDock.AutoDockScorer import AutoDock305Scorer as c_AutoDock305Scorer
    from cAutoDock.scorer import MolecularSystem as c_MolecularSystem
    from cAutoDock.scorer import updateCoords as c_updateCoords

    class cADCalcAD3Energies(EnergyScorer):
        """For each atom in one AtomSet, determine the electrostatics eneregy vs all the atoms in a second
        AtomSet using the C implementation of the autodock scorer.
        When using the autodock3 scorer, the receptor need to be loaded as a pdbqs file, the ligand as pdbqt.
        """


        def __init__(self,atomset1,atomset2):


            EnergyScorer.__init__(self,atomset1,atomset2)
            self.weight = None
            self.weightLabel = None

            bothAts = atomset1 + atomset2
    ##         for a in bothAts:
    ##             if a.parent.type + '_' + a.name in pep_aromList:
    ##                 a.autodock_element=='A'
    ##                 a.AtSolPar = .1027
    ##             elif a.autodock_element=='A':
    ##                 a.AtSolPar = .1027
    ##             elif a.autodock_element=='C':
    ##                 a.AtSolPar = .6844
    ##             else:
    ##                 a.AtSolPar = 0.0

            self.ms = c_MolecularSystem()
            self.receptor= self.pyMolToCAtomVect(atomset1)
            self.ligand  = self.pyMolToCAtomVect(atomset2)
            self.r = self.ms.add_entities(self.receptor)
            self.l = self.ms.add_entities(self.ligand)
            self.ms.build_bonds( self.r )
            self.ms.build_bonds( self.l )

            self.scorer = c_AutoDock305Scorer(ms=self.ms,
                                              pyatomset1=atomset1,
                                              pyatomset2=atomset2)
            self.prop = self.scorer.prop

            # shared memory, used by C++ functions
            self.proteinLen = len(atomset1)
            self.ligLen = len(atomset2)
            self.msLen =  self.proteinLen + self.ligLen
            self.sharedMem = memobject.allocate_shared_mem([self.msLen, 3],
                                                           'SharedMemory', memobject.FLOAT)
            self.sharedMemPtr = memobject.return_share_mem_ptr('SharedMemory')[0]
            #print "Shared memory allocated.."


        def update_coords(self):
            """ update the coordinate of atomset """
            # use conformation set by dectected patterns
            if hasattr(self.mol1,'cconformationIndex'):
                self.atomset1.setConformation(self.mol1.cconformationIndex)
            if hasattr(self.mol2,'cconformationIndex'):
                self.atomset2.setConformation(self.mol2.cconformationIndex)
                #confNum = self.mol2.cconformationIndex
            # get the coords

            #if hasattr(self.mol1,'mat_transfo_inv'):
            #    M = self.mol1.mat_transfo_inv
            #    vt = []
            #    for pt in self.mol2.allAtoms.coords:
            #        ptx = (M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3])#+self.mol1.getCenter()[0]
            #        pty = (M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3])#+self.mol1.getCenter()[1]
            #        ptz = (M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3])#+self.mol1.getCenter()[2]
            #        vt.append( (ptx, pty, ptz) )
            #    self.mol2.allAtoms.updateCoords(vt,ind=confNum)#confNum
            #
            R_coords  = self.atomset1.coords
            L_coords =  self.atomset2.coords

            self.sharedMem[:] = Numeric.array(R_coords+L_coords, 'f')[:]

            c_updateCoords(self.proteinLen, self.msLen, self.ms,self.sharedMemPtr)

        def get_score(self):
            """ return the score """

            mini = self.ms.check_distance_cutoff(0, 1, self.cutoff)

            # when number return should not do get_score ( proteins too close)
            # flag = (mini==1.0 and mini==2.0)
            flag =  (mini == mini)

            # for each of the terms and the score, we cap their max value to 100
            # so if anything is greater than 100 we assign 100
            # If their is bad contact score = 1000.

            if flag: # if any distance < cutoff : no scoring
                #self.score = min(9999999.9, 9999.9/mini)
                self.score = 1000.
                estat =  hbond = vdw = ds =  1000.
                self.scores = [1000.,1000.,1000.,1000.]
            else:
                self.score = min(self.scorer.get_score(),100.)


                terms_score = self.scorer.get_score_per_term()
                estat = min(round(terms_score[0],2),1000.)
                hbond = min(round(terms_score[1],2),1000.)
                vdw   = min(round(terms_score[2],2),1000.)
                ds    = 0.#min(round(terms_score[3],2),1000.) #problem with ds
                #print "--",estat,hbond,vdw,ds
                self.scores = [estat,hbond,vdw,ds]
            # labels atoms
            score_array = self.scorer.get_score_array()
            self.scorer.labels_atoms_w_nrg(score_array)
            #ds=ds-ds
    	    #self.score = self.score -ds
            return (self.score,estat,hbond,vdw,ds)



        def pyMolToCAtomVect( self,mol):
            """convert Protein or AtomSet to AtomVector
            """
            from cAutoDock.scorer import AtomVector, Atom, Coords
            className = mol.__class__.__name__
            if className == 'Protein':
                pyAtoms = mol.getAtoms()
            elif className == 'AtomSet':
                pyAtoms = mol
            else:
                return None
            pyAtomVect = AtomVector()
            for atm in pyAtoms:
                a=Atom()
                a.set_name(atm.name)
                a.set_element(atm.autodock_element)# aromatic type 'A', vs 'C'
                coords=atm.coords
                a.set_coords( Coords(coords[0],coords[1],coords[2]))
                a.set_charge( atm.charge)
                try:
                    a.set_atvol( atm.AtVol)
                except:
                    pass
                try:
                     a.set_atsolpar( atm.AtSolPar)
                except:
                    pass
                a.set_bond_ord_rad( atm.bondOrderRadius)
                a.set_charge( atm.charge)
                pyAtomVect.append(a)
            return pyAtomVect

        def free_memory(self):
            # free the shared memory
            memobject.free_shared_mem("SharedMemory")









#############################################################################################################


class PyPairWiseEnergyScorer(EnergyScorer):
    """For each atom in one AtomSet, determine the electrostatics energy vs all the atoms in a second
    AtomSet
    """

    def __init__(self,atomset1,atomset2,scorer_ad_type='305'):

        EnergyScorer.__init__(self,atomset1,atomset2)
        self.r = self.ms.add_entities(self.atomset1)
        self.l = self.ms.add_entities(self.atomset2)


        self.scorer = WeightedMultiTerm()
        self.scorer.set_molecular_system(self.ms)

        self.scorer_ad_type = scorer_ad_type
        if self.scorer_ad_type == '305':
            self.ESTAT_WEIGHT_AUTODOCK = 0.1146 # electrostatics
            self.HBOND_WEIGHT_AUTODOCK = 0.0656 # hydrogen bonding
            self.VDW_WEIGHT_AUTODOCK   = 0.1485 # van der waals
            self.DESOLV_WEIGHT_AUTODOCK= 0.1711 # desolvation

        # different terms to be use for score
        self.estat= Electrostatics(self.ms)
        self.scorer.add_term(self.estat, self.ESTAT_WEIGHT_AUTODOCK)

        self.hbond=HydrogenBonding(self.ms)
        self.scorer.add_term(self.hBond, self.HBOND_WEIGHT_AUTODOCK)

        self.vdw = VanDerWaals(self.ms)
        self.scorer.add_term(self.vdw, self.VDW_WEIGHT_AUTODOCK)

        self.ds= Desolvation(self.ms)
        self.scorer.add_term(self.ds,self.DESOLV_WEIGHT_AUTODOCK)


    def update_coords(self):
        """ update the coords """
        if hasattr(self.mol1,'cconformationIndex'):
            self.atomset1.setConformation(self.mol1.cconformationIndex)
        if hasattr(self.mol2,'cconformationIndex'):
            self.atomset2.setConformation(self.mol2.cconformationIndex)

        for ind in (self.r,self.l):
            # clear distance matrix
            self.ms.clear_dist_mat(ind)

    def get_score(self):

        score = self.scorer.get_score()
        estat = min(round(self.estat.get_score() * self.ESTAT_WEIGHT_AUTODOCK,2),1000.)
        hbond = min(round(self.hbond.get_score() * self.HBOND_WEIGHT_AUTODOCK,2),1000.)
        vdw   = min(round(self.vdw.get_score()   * self.VDW_WEIGHT_AUTODOCK,2),1000.)
        ds    = min(round(self.ds.get_score()    * self.DESOLV_WEIGHT_AUTODOCK,2),1000.)

        return (score,estat,hbond,vdw,ds)

#"""
#class PatternDistanceMatrix:
#    # Object to store information about distance between a
#    # set of patterns
#
#
#    def __init__(self,patternList):
#        self.patterns = patternList # list of patterns object
#        self.vertices = [] # list of vertice of center of pattern
#        self.centers = []  # list of center between two marker
#        self.dist = []     # distance between 2 markers
#        self.dist_str = [] # distance between 2 markers as string, so we
#                           # can pass it to display
#
#    def clear_matrix(self):
#        # delete all values store
#        self.vertices = []
#        self.centers = []
#        self.dist = []
#        self.dist_str = []
#
#    def compute(self):
#        # compute the distance between patterns
#        We only compute half of the distance matrix as the rest is not needed
#
#        self.clear_matrix()
#        index = 0
#        for pat in self.patterns[index:]:
#            if not pat.isdetected: continue
#            x = pat.gl_para[12]
#            y = pat.gl_para[13]
#            z = pat.gl_para[14]
#            v = (x,y,z)
#            for pat1 in self.patterns[index+1:]:
#                if not pat1.isdetected: continue
#                x1= pat1.gl_para[12]
#                y1= pat1.gl_para[13]
#                z1= pat1.gl_para[14]
#                v1= (x1,y1,z1)
#                # calculate distance
#                d = util.measure_distance(Numeric.array(v),Numeric.array(v1))
#                # calculate center between 2 patterns
#                c = util.get_center(Numeric.array(v),Numeric.array(v1))
#
#                self.dist.append(d)
#                self.dist_str.append('%4.1f'%(d/10.)) # we want the values in centimeters
#                                                      # 1 unit  = 10 mm
#
#                self.vertices.append(v)
#                self.vertices.append(v1)
#                self.centers.append(c.tolist())
#            index +=1
#
#    def getall(self):
#        # return vertices,centers,dist,dist_str
#        return  self.vertices,self.centers,self.dist,self.dist_str
#
#### Functions used to create Event
#
#def test_display_dist(arviewer):
#    # test function to determine if we need to run the event function
#    if arviewer.display_pat_distance: return True
#
#def display_distance(arviewer):
#    # event function to display the distance between patterns
#    vertices,centers,dist,dist_str = arviewer.patternMgr.distance_matrix.getall()
#    arviewer.set_dist_geoms(vertices,centers,dist_str)
#
#
#
#def measure_atoms_dist(arviewer):
#    # calculate and set to display the distance between atoms selected
#    #Computes the distance between atom1, atom2, atom3.All coordinates are Cartesian; result is in mm
#
#    #print "-- measure_atoms_dist --"
#    detected_mols = [] # name list
#    if len(arviewer.atoms_selected) < 2: return # we need at least 2 atoms selected to measure a distance
#    vertices = []
#    labelStr = []
#    atm_dist_label = []
#    centers = []
#
#    for i in range(len(arviewer.atoms_selected) -1):
#
#        at1 = arviewer.atoms_selected[i]
#        at2 = arviewer.atoms_selected[i+1]
#        # set correct conformation to get coordinate of atom
#        # check if pattern is detected
#        conf1=0
#        conf2=0
#        #if at1.top not in arviewer.mol_detected: continue
#        #if at2.top not in arviewer.mol_detected: continue
#
#        if hasattr(at1,'pat') :
#            pat1 = at1.pat[0]
#	    if pat1 not in arviewer.current_context.patterns.keys(): continue
#	    pat1 = arviewer.current_context.patterns[at1.pat[0]]
#	    if not pat1.isdetected : continue
#            #conf1 = arviewer.current_context.patterns[pat1].confNum
#	    conf1 = pat1.confNum
#        if hasattr(at2,'pat') :
#            pat2 = at2.pat[0]
#            if pat2 not in arviewer.current_context.patterns.keys(): continue
#	    pat2 = arviewer.current_context.patterns[at2.pat[0]]
#	    if not pat2.isdetected : continue
#            #conf1 = arviewer.current_context.patterns[pat1].confNum
#	    conf2 = pat2.confNum
#        # check if atomset belong to a molecule that is part of
#        # detected pattern
#        #if at1.top not in arviewer.mol_detected: continue
#        #if at2.top not in arviewer.mol_detected: continue
#
#        #conf = arviewer.current_context.patterns[pat1].confNum
#        at1.setConformation(conf1)
#        c1 = Numeric.array(at1[0].coords)
#        at1.setConformation(0)
#
#        #conf = arviewer.current_context.patterns[pat2].confNum
#        at2.setConformation(conf2)
#        c2 = Numeric.array(at2[0].coords)
#        at2.setConformation(0)
#
#        d = util.measure_distance(c1,c2)#Numeric.array
#        c = util.get_center(c1,c2)
#        #print "%s - %s :%f"%(atom1.full_name(),atom2.full_name(),distance)
#        d = d /10.0 # arviewer.current_context.patterns[pat2].scaleFactor # scale factor 1A -> 10mm
#        #print d
#        #print c1.tolist()
#        vertices.append(c1.tolist())
#        vertices.append(c2.tolist())
#        #print "Distance:%3.f"%d
#        atm_dist_label.append('%3.1f'%d)
#        centers.append(c.tolist())
#
#        labelStr.append(at1[0].name)
#        labelStr.append(at2[0].name)
#
#	#if arviewer.patternMgr.mirror : arviewer.set_dist_geoms_mirror(vertices,centers,atm_dist_label)
#        #else : arviewer.set_dist_geoms(vertices,centers,atm_dist_label)
#	arviewer.set_dist_geoms(vertices,centers,atm_dist_label)
#
#def test_measure_dist(arviewer):
#    for i in range(len(arviewer.atoms_selected) -1):
#        at1 = arviewer.atoms_selected[i]
#        at2 = arviewer.atoms_selected[i+1]
#	if at1.top[0] not in arviewer.mol_detected: return False
#	if at2.top[0] not in arviewer.mol_detected: return False
#        if hasattr(at1,'pat') :
#            pat1 = at1.pat[0]
#            if pat1 not in arviewer.current_context.patterns.keys(): return False
#	    pat1 = arviewer.current_context.patterns[at1.pat[0]]
#	    if not pat1.isdetected : return False
#        if hasattr(at2,'pat') :
#            pat2 = at2.pat[0]
#            if pat2 not in arviewer.current_context.patterns.keys(): return False
#	    pat1 = arviewer.current_context.patterns[at1.pat[0]]
#	    if not pat1.isdetected : return False
#   	return True
#
#
#def measure_dist(arviewer):
#    # calculate and set to display the distance between atoms selected
#    #Computes the distance between atom1, atom2, atom3.All coordinates are Cartesian; result is in mm#
#
#    #print "-- measure_atoms_dist --"
#    detected_mols = [] # name list
#    if len(arviewer.atoms_selected) < 2: return # we need at least 2 atoms selected to measure a distance
#    vertices = []
#    labelStr = []
#    atm_dist_label = []
#    centers = []
#
#    mtr=arviewer.current_context.glcamera.rootObjectTransformation
#    M=Numeric.reshape(mtr,(4,4))
#    rot,tr,sc=arviewer.current_context.glcamera.Decompose4x4(mtr)
#    p=arviewer.current_context.patterns.values()
#
#    for i in range(len(arviewer.atoms_selected) -1):
#
#        at1 = arviewer.atoms_selected[i]
#        at2 = arviewer.atoms_selected[i+1]
#	#print at1
#	#print at2
#        # set correct conformation to get coordinate of atom
#        # check if pattern is detected
#        conf1=0
#        conf2=0
#        #if at1.top not in arviewer.mol_detected: continue
#        #if at2.top not in arviewer.mol_detected: continue
#
#        if at1.top[0] not in arviewer.mol_detected:
#	    continue
#            g=at1.top[0].geomContainer.masterGeom
#            #c1 = Numeric.array(at1[0].coords)
#            c1 = g.ApplyParentsTransform(Numeric.array([at1[0].coords,]))
#            one = Numeric.ones( (c1.shape[0], 1), c1.dtype.char )
#            c = Numeric.concatenate( (c1, one), 1 )
#            #M=Numeric.reshape(mtr,(4,4))
#            c1=Numeric.dot(c, M)[:, :3]
#            c1=c1[0]
#	    #print c1
#        else :
#            pat1 = arviewer.current_context.patterns[at1.pat[0]]
#	    if not pat1.isdetected : continue
#            #pat1 = p[0]
#            #print pat1.name
#            conf1 = pat1.confNum
#            #at1.setConformation(conf1)
#            vt = util.transformedCoordinatesWithInstances(at1,pat1)
#            c1=Numeric.array(vt)
#            #c1 = Numeric.array(at1[0].coords)
#            #at1.setConformation(0)
#            one = Numeric.ones( (c1.shape[0], 1), c1.dtype.char )
#            c = Numeric.concatenate( (c1, one), 1 )
#            M=Numeric.reshape(mtr,(4,4))
#            c1=Numeric.dot(c, M)[:, :3]
#            c1=c1[0]
#            #c1=c1+tr
#	    #print c1
#        if at2.top[0] not in arviewer.mol_detected:
#	    continue
#            g=at2.top[0].geomContainer.masterGeom
#            #c1 = Numeric.array(at1[0].coords)
#            c2 = g.ApplyParentsTransform(Numeric.array([at2[0].coords,]))
#            one = Numeric.ones( (c2.shape[0], 1), c2.dtype.char )
#            c = Numeric.concatenate( (c2, one), 1 )
#            #M=Numeric.reshape(mtr,(4,4))
#            c2=Numeric.dot(c, M)[:, :3]
#            c2=c2[0]
#	    #print c2
#        else :
#            #pat2 = p[0]
#	    pat2 = arviewer.current_context.patterns[at2.pat[0]]
#	    if not pat2.isdetected : continue
#	    #print pat2.name
#            conf2 = pat2.confNum
#            #at2.setConformation(conf2)
#	    vt = util.transformedCoordinatesWithInstances(at2,pat2)
#            c2=Numeric.array(vt)
#            #c2 = Numeric.array(at2[0].coords)
#            #at2.setConformation(0)
#            one = Numeric.ones( (c2.shape[0], 1), c2.dtype.char )
#            c = Numeric.concatenate( (c2, one), 1 )
#            M=Numeric.reshape(mtr,(4,4))
#            c2=Numeric.dot(c, M)[:, :3]
#            c2=c2[0]
#            #c2=c2+tr
#
#        # check if atomset belong to a molecule that is part of
#        # detected pattern
#        #f at1.top[0] not in arviewer.mol_detected: continue
#        #f at2.top[0] not in arviewer.mol_detected: continue
#
#
#        d = util.measure_distance(c1,c2)#Numeric.array
#        c = util.get_center(c1,c2)
#        #print "%s - %s :%f"%(atom1.full_name(),atom2.full_name(),distance)
#        d = d /10.0 # arviewer.current_context.patterns[pat2].scaleFactor # scale factor 1A -> 10mm
#        #print d
#        #print c1.tolist()
#        vertices.append(c1.tolist())
#        vertices.append(c2.tolist())
#        #print "Distance:%3.f"%d
#        atm_dist_label.append('%3.1f'%d)
#        centers.append(c.tolist())
#
#        labelStr.append(at1[0].name)
#        labelStr.append(at2[0].name)
#
#    arviewer.set_dist_geoms(vertices,centers,atm_dist_label)
#
#def measure_dist2(arviewer):
#    # calculate and set to display the distance between atoms selected
#    #Computes the distance between atom1, atom2, atom3.All coordinates are Cartesian; result is in mm
#
#    #print "-- measure_atoms_dist --"
#    detected_mols = [] # name list
#    if len(arviewer.atoms_selected) < 2: return # we need at least 2 atoms selected to measure a distance
#    vertices = []
#    labelStr = []
#    atm_dist_label = []
#    centers = []
#    mtr=arviewer.current_context.glcamera.rootObjectTransformation
#    M=Numeric.reshape(mtr,(4,4))
#    rot,tr,sc=arviewer.current_context.glcamera.Decompose4x4(mtr)
#    p=arviewer.current_context.patterns.values()
#    for i in range(len(arviewer.atoms_selected) -1):
#
#        at1 = arviewer.atoms_selected[i]
#        at2 = arviewer.atoms_selected[i+1]
#	#print at1
#	#print at2
#        # set correct conformation to get coordinate of atom
#        # check if pattern is detected
#        conf1=0
#        conf2=0
#
#        if at1.top[0] not in arviewer.mol_detected:
#            g=at1.top[0].geomContainer.masterGeom
#            #c1 = Numeric.array(at1[0].coords)
#            c1 = g.ApplyParentsTransform(Numeric.array([at1[0].coords,]))
#            one = Numeric.ones( (c1.shape[0], 1), c1.dtype.char )
#            c = Numeric.concatenate( (c1, one), 1 )
#            #M=Numeric.reshape(mtr,(4,4))
#            c1=Numeric.dot(c, M)[:, :3]
#            c1=c1[0]
#	   # print c1
#        else :
#            pat1 = arviewer.current_context.patterns[at1.pat[0]]
#            #pat1 = p[0]
#            print pat1.name
#            #f pat1 not in arviewer.current_context.patterns.keys(): continue
#            conf1 = pat1.confNum
#            #vt=util.transformedCoord(at1,pat1)
#            vt = util.transformedCoordinatesWithInstances(at1,pat1)
#            c1=Numeric.array(vt[0])
#            #at1.setConformation(conf1)
#            #c1 = Numeric.array(at1[0].coords)
#            #at1.setConformation(0)
#            #one = Numeric.ones( (c1.shape[0], 1), c1.dtype.char )
#            #c = Numeric.concatenate( (c1, one), 1 )
#            #M=Numeric.reshape(mtr,(4,4))
#            #c1=Numeric.dot(c, M)[:, :3]
#            #c1=c1[0]
#            #c1=c1-tr
#	    #print c1
#        if at2.top[0] not in arviewer.mol_detected:
#            g=at2.top[0].geomContainer.masterGeom
#            #c1 = Numeric.array(at1[0].coords)
#            c2 = g.ApplyParentsTransform(Numeric.array([at2[0].coords,]))
#            one = Numeric.ones( (c2.shape[0], 1), c2.dtype.char )
#            c = Numeric.concatenate( (c2, one), 1 )
#            #M=Numeric.reshape(mtr,(4,4))
#            c2=Numeric.dot(c, M)[:, :3]
#            c2=c2[0]
#	    #print c2
#        else :
#            #pat2 = p[0]
#	    pat2 = arviewer.current_context.patterns[at2.pat[0]]
#	    #print pat2.name
#            #f pat1 not in arviewer.current_context.patterns.keys(): continue
#            conf2 = pat2.confNum
#            vt = util.transformedCoordinatesWithInstances(at2,pat2)
#            c2=Numeric.array(vt[0])
#	   # print c2
#            #at2.setConformation(conf2)
#            #c2 = Numeric.array(at2[0].coords)
#            #at2.setConformation(0)
#            #one = Numeric.ones( (c2.shape[0], 1), c2.dtype.char )
#            #c = Numeric.concatenate( (c2, one), 1 )
#            #M=Numeric.reshape(mtr,(4,4))
#            #c2=Numeric.dot(c, M)[:, :3]
#            #c2=c2[0]
#            #c2=c2-tr
#
#        # check if atomset belong to a molecule that is part of
#        # detected pattern
#        #f at1.top[0] not in arviewer.mol_detected: continue
#        #f at2.top[0] not in arviewer.mol_detected: continue
#
#
#        d = util.measure_distance(c1,c2)#Numeric.array
#        c = util.get_center(c1,c2)
#        #print "%s - %s :%f"%(atom1.full_name(),atom2.full_name(),distance)
#        d = d /10.0 # arviewer.current_context.patterns[pat2].scaleFactor # scale factor 1A -> 10mm
#        #print d
#        #print c1.tolist()
#        vertices.append(c1.tolist())
#        vertices.append(c2.tolist())
#       # print "Distance:%3.f"%d
#        atm_dist_label.append('%3.1f'%d)
#        centers.append(c.tolist())
#
#        labelStr.append(at1[0].name)
#        labelStr.append(at2[0].name)
#
#    arviewer.set_dist_geoms(vertices,centers,atm_dist_label)
#"""


################
import math
from math import sqrt, cos, sin, acos,atan2,asin
import numpy as N
import numpy

Q_EPSILON = 0.0000000001
X = 0
Y = 1
Z = 2
W = 3

def q_make( x, y, z, angle):
    """q_make:  make a quaternion given an axis and an angle (in radians)
    notes:
        - rotation is counter-clockwise when rotation axis vector is
    pointing at you
        - if angle or vector are 0, the identity quaternion is returned.

    double x, y, z  :    axis of rotation
    double angle    :    angle of rotation about axis in radians
    """
    length=0
    cosA=0
    sinA=0
    destQuat = [0.0,0.0,0.0,0.0]
    #/* normalize vector */
    length = sqrt( x*x + y*y + z*z )

    #/* if zero vector passed in, just return identity quaternion   */
    if ( length < Q_EPSILON ) :
        destQuat[X] = 0
        destQuat[Y] = 0
        destQuat[Z] = 0
        destQuat[W] = 1
        return

    x /= length
    y /= length
    z /= length

    cosA = cos(angle / 2.0)
    sinA = sin(angle / 2.0)

    destQuat[W] = cosA
    destQuat[X] = sinA * x
    destQuat[Y] = sinA * y
    destQuat[Z] = sinA * z
    return destQuat


def q_from_col_matrix(srcMatrix) :
   """#/*****************************************************************************
# * q_from_col_matrix- Convert 4x4 column-major rotation matrix
# *                to unit quaternion.
# *****************************************************************************/
"""
   trace=0
   s=0
   i=0
   j=0
   k=0
   next = [Y, Z, X]
   destQuat = [0.0,0.0,0.0,0.0]

   trace = srcMatrix[X][X] + srcMatrix[Y][Y] + srcMatrix[Z][Z]

   if (trace > 0.0) :
      s = sqrt(trace + 1.0)
      destQuat[W] = s * 0.5
      s = 0.5 / s
      destQuat[X] = (srcMatrix[Z][Y] - srcMatrix[Y][Z]) * s
      destQuat[Y] = (srcMatrix[X][Z] - srcMatrix[Z][X]) * s
      destQuat[Z] = (srcMatrix[Y][X] - srcMatrix[X][Y]) * s
   else :
      i = X
      if (srcMatrix[Y][Y] > srcMatrix[X][X]):
         i = Y
      if (srcMatrix[Z][Z] > srcMatrix[i][i]):
         i = Z
      j = next[i]
      k = next[j]

      s = sqrt( (srcMatrix[i][i] - (srcMatrix[j][j]+srcMatrix[k][k])) + 1.0 )
      destQuat[i] = s * 0.5
      s = 0.5 / s

      destQuat[W] = (srcMatrix[k][j] - srcMatrix[j][k]) * s
      destQuat[j] = (srcMatrix[j][i] + srcMatrix[i][j]) * s
      destQuat[k] = (srcMatrix[k][i] + srcMatrix[i][k]) * s
   return destQuat

def q_from_row_matrix(srcMatrix):
   """#/*****************************************************************************
# *
#   q_from_row_matrix: Convert 4x4 row-major rotation matrix to unit quaternion
# *
# *****************************************************************************/
"""
   trace=0
   s=0
   i=0
   j=0
   k=0
   next = [Y, Z, X]
   destQuat = [0.0,0.0,0.0,0.0]

   trace = srcMatrix[X][X] + srcMatrix[Y][Y]+ srcMatrix[Z][Z];

   if (trace > 0.0):
      s = sqrt(trace + 1.0)
      destQuat[W] = s * 0.5
      s = 0.5 / s
      destQuat[X] = (srcMatrix[Y][Z] - srcMatrix[Z][Y]) * s
      destQuat[Y] = (srcMatrix[Z][X] - srcMatrix[X][Z]) * s
      destQuat[Z] = (srcMatrix[X][Y] - srcMatrix[Y][X]) * s
   else :
      i = X
      if (srcMatrix[Y][Y] > srcMatrix[X][X]):
         i = Y
      if (srcMatrix[Z][Z] > srcMatrix[i][i]):
         i = Z
      j = next[i]
      k = next[j]

      s = sqrt( (srcMatrix[i][i] - (srcMatrix[j][j]+srcMatrix[k][k])) + 1.0 )
      destQuat[i] = s * 0.5

      s = 0.5 / s

      destQuat[W] = (srcMatrix[j][k] - srcMatrix[k][j]) * s
      destQuat[j] = (srcMatrix[i][j] + srcMatrix[j][i]) * s
      destQuat[k] = (srcMatrix[i][k] + srcMatrix[k][i]) * s
   return destQuat


def quat_to_ogl_matrix(srcQuat):
	print "quat"
	#For unit srcQuat, just set s = 2.0, or set xs = srcQuat[X] + srcQuat[X], etc.
	s = 2.0 / ( srcQuat[X] * srcQuat[X] + srcQuat[Y] * srcQuat[Y] + srcQuat[Z] * srcQuat[Z] + srcQuat[W] * srcQuat[W] )
	xs = srcQuat[X] * s
	ys = srcQuat[Y] * s
	zs = srcQuat[Z] * s
	wx = srcQuat[W] * xs
	wy = srcQuat[W] * ys
	wz = srcQuat[W] * zs
	xx = srcQuat[X] * xs
	xy = srcQuat[X] * ys
	xz = srcQuat[X] * zs
	yy = srcQuat[Y] * ys
	yz = srcQuat[Y] * zs
	zz = srcQuat[Z] * zs
	#set up 4x4 matrix
	matrix=[]
	matrix.append(1.0 - ( yy + zz ))
	matrix.append(xy + wz)
	matrix.append(xz - wy)
	matrix.append(0.0)
	matrix.append(xy - wz)
	matrix.append(1.0 - ( xx + zz ))
	matrix.append(yz + wx)
	matrix.append(0.0)
	matrix.append(xz + wy)
	matrix.append(yz - wx)
	matrix.append(1.0 - ( xx + yy ))
	matrix.append(0.0)
	matrix.append(0.0)
	matrix.append(0.0)
	matrix.append(0.0)
	matrix.append(1.0)
	return matrix

def quat_to_matrix(srcQuat):
	#print "quat"
	#For unit srcQuat, just set s = 2.0, or set xs = srcQuat[X] + srcQuat[X], etc.
	#s = 2.0 / ( srcQuat[X] * srcQuat[X] + srcQuat[Y] * srcQuat[Y] + srcQuat[Z] * srcQuat[Z] + srcQuat[W] * srcQuat[W] )
	#xs = srcQuat[X] * s
	#ys = srcQuat[Y] * s
	#zs = srcQuat[Z] * s
	#wx = srcQuat[W] * xs
	##wy = srcQuat[W] * ys
	#wz = srcQuat[W] * zs
	#xx = srcQuat[X] * xs
	#xy = srcQuat[X] * ys
	#xz = srcQuat[X] * zs
	#yy = srcQuat[Y] * ys
	#yz = srcQuat[Y] * zs
	#zz = srcQuat[Z] * zs
	#set up 4x4 matrix
	matrix=[]

	matrix.append(1.0 - 2*(srcQuat[Y] * srcQuat[Y]) - 2*(srcQuat[Z] * srcQuat[Z]))
	matrix.append(2*(srcQuat[X] * srcQuat[Y])-2*(srcQuat[Z] * srcQuat[W]))
	matrix.append(2*(srcQuat[X] * srcQuat[Z])+2*(srcQuat[Y] * srcQuat[W]))
	matrix.append(0.0)

	matrix.append(2*(srcQuat[X] * srcQuat[Y])+2*(srcQuat[Z] * srcQuat[W]))
	matrix.append(1.0 - 2*(srcQuat[X] * srcQuat[X]) - 2*(srcQuat[Z] * srcQuat[Z]))
	matrix.append(2*(srcQuat[Y] * srcQuat[Z])-2*(srcQuat[X] * srcQuat[W]))
	matrix.append(0.0)

	matrix.append(2*(srcQuat[X] * srcQuat[Z])-2*(srcQuat[Y] * srcQuat[W]))
	matrix.append(2*(srcQuat[Y] * srcQuat[Z])+2*(srcQuat[X] * srcQuat[W]))
	matrix.append(1.0 - 2*(srcQuat[X] * srcQuat[X]) - 2*(srcQuat[Y] * srcQuat[Y]))
	matrix.append(0.0)

	matrix.append(0.0)
	matrix.append(0.0)
	matrix.append(0.0)
	matrix.append(1.0)

	return matrix

def quat_invert(q) :
	qres = [0.0,0.0,0.0,0.0]
	qNorm = 0.0;
	qNorm = 1.0 / (q[X]*q[X] + q[Y]*q[Y] + q[Z]*q[Z] + q[W]*q[W])
	qres[X] = -q[X] * qNorm
	qres[Y] = -q[Y] * qNorm
	qres[Z] = -q[Z] * qNorm
	qres[W] =  q[W] * qNorm
	return qres


def quat_sum(q1,q2) :
	qres = [0.0,0.0,0.0,0.0]
	qres[W] = q1[W]+q2[W]
	qres[X] = q1[X]+q2[X]
	qres[Y] = q1[Y]+q2[Y]
	qres[Z] = q1[Z]+q2[Z]
	return qres


def quat_mult(q1,q2) :
	qres = [0.0,0.0,0.0,0.0]
	qres[W] = q1[W]*q2[W] - q1[X]*q2[X] - 	q1[Y]*q2[Y] - q1[Z]*q2[Z]
	qres[X] = q1[W]*q2[X] + q1[X]*q2[W] + 	q1[Y]*q2[Z] - q1[Z]*q2[Y]
	qres[Y] = q1[W]*q2[Y] + q1[Y]*q2[W] + 	q1[Z]*q2[X] - q1[X]*q2[Z]
	qres[Z] = q1[W]*q2[Z] + q1[Z]*q2[W] + 	q1[X]*q2[Y] - q1[Y]*q2[X]
	return qres

def quat_normalize(q) :
	qres = [0.0,0.0,0.0,0.0]
	normalizeFactor = 0.0;
	normalizeFactor = 1.0 / sqrt( q[X]*q[X] + q[Y]*q[Y] + q[Z]*q[Z] + q[W]*q[W])
	qres[X] = q[X] * normalizeFactor
	qres[Y] = q[Y] * normalizeFactor
	qres[Z] = q[Z] * normalizeFactor
	qres[W] = q[W] * normalizeFactor
	return qres

def quat_diff(q1,q2) :
	quat_inv = quat_invert(q1)
	quat_diff = quat_mult(q2,quat_inv)
	quat_norm = quat_normalize(quat_diff)
	return quat_norm

# -*- coding: utf-8 -*-
# transformations.py
# http://www.lfd.uci.edu/~gohlke/code/transformations.py.html
# Copyright (c) 2006, Christoph Gohlke
# Copyright (c) 2006-2010, The Regents of the University of California
# All rights reserved.

def unit_vector(data, axis=None, out=None):
    """Return ndarray normalized by length, i.e. eucledian norm, along axis.

    >>> v0 = numpy.random.random(3)
    >>> v1 = unit_vector(v0)
    >>> numpy.allclose(v1, v0 / numpy.linalg.norm(v0))
    True
    >>> v0 = numpy.random.rand(5, 4, 3)
    >>> v1 = unit_vector(v0, axis=-1)
    >>> v2 = v0 / numpy.expand_dims(numpy.sqrt(numpy.sum(v0*v0, axis=2)), 2)
    >>> numpy.allclose(v1, v2)
    True
    >>> v1 = unit_vector(v0, axis=1)
    >>> v2 = v0 / numpy.expand_dims(numpy.sqrt(numpy.sum(v0*v0, axis=1)), 1)
    >>> numpy.allclose(v1, v2)
    True
    >>> v1 = numpy.empty((5, 4, 3), dtype=numpy.float64)
    >>> unit_vector(v0, axis=1, out=v1)
    >>> numpy.allclose(v1, v2)
    True
    >>> list(unit_vector([]))
    []
    >>> list(unit_vector([1.0]))
    [1.0]

    """
    if out is None:
        data = numpy.array(data, dtype=numpy.float64, copy=True)
        if data.ndim == 1:
            data /= math.sqrt(numpy.dot(data, data))
            return data
    else:
        if out is not data:
            out[:] = numpy.array(data, copy=False)
        data = out
    length = numpy.atleast_1d(numpy.sum(data*data, axis))
    numpy.sqrt(length, length)
    if axis is not None:
        length = numpy.expand_dims(length, axis)
    data /= length
    if out is None:
        return data

def swithQuat(quat,inv=False):
    if inv:
        return [quat[1],quat[2],quat[3],quat[0]]
    else :
        return [quat[3],quat[0],quat[1],quat[2]]


def quaternion_slerp(quat0, quat1, fraction, spin=0, shortestpath=True):
    """Return spherical linear interpolation between two quaternions.

    >>> q0 = random_quaternion()
    >>> q1 = random_quaternion()
    >>> q = quaternion_slerp(q0, q1, 0.0)
    >>> numpy.allclose(q, q0)
    True
    >>> q = quaternion_slerp(q0, q1, 1.0, 1)
    >>> numpy.allclose(q, q1)
    True
    >>> q = quaternion_slerp(q0, q1, 0.5)
    >>> angle = math.acos(numpy.dot(q0, q))
    >>> numpy.allclose(2.0, math.acos(numpy.dot(q0, q1)) / angle) or \
        numpy.allclose(2.0, math.acos(-numpy.dot(q0, q1)) / angle)
    True

    """
    q0 = unit_vector(swithQuat(quat0)[:4])
    q1 = unit_vector(swithQuat(quat1)[:4])
    if fraction == 0.0:
        return q0
    elif fraction == 1.0:
        return q1
    d = numpy.dot(q0, q1)
    if abs(abs(d) - 1.0) < _EPS:
        return q0
    if shortestpath and d < 0.0:
        # invert rotation
        d = -d
        q1 *= -1.0
    angle = math.acos(d) + spin * math.pi
    if abs(angle) < _EPS:
        return q0
    isin = 1.0 / math.sin(angle)
    q0 *= math.sin((1.0 - fraction) * angle) * isin
    q1 *= math.sin(fraction * angle) * isin
    q0 += q1
    return swithQuat(q0,inv=True)

def quat_to_axis_angle(q) :
	axis_angle = [0.0,0.0,0.0,0.0]
	length = sqrt( q[X]*q[X] + q[Y]*q[Y] + q[Z]*q[Z])
	if (length < Q_EPSILON)  :
		axis_angle[2] = 1.0
	else :
		#According to an article by Sobiet Void (robin@cybervision.com) on Game Developer's
		#Network, the following conversion is appropriate.
		axis_angle[X] = q[X] / length;
		axis_angle[Y] = q[Y] / length;
		axis_angle[Z] = q[Z] / length;
		axis_angle[W] = 2 * acos(q[W]);
	return axis_angle

def rotatePoint(pt,m,ax):
				x=pt[0]
				y=pt[1]
				z=pt[2]
				u=ax[0]
				v=ax[1]
				w=ax[2]
				ux=u*x
				uy=u*y
				uz=u*z
				vx=v*x
				vy=v*y
				vz=v*z
				wx=w*x
				wy=w*y
				wz=w*z
				sa=sin(ax[3])
				ca=cos(ax[3])
				pt[0]=(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
				pt[1]=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
				pt[2]=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
				return pt


def euler_to_quat(yaw, pitch, roll):
	half_yaw=float(yaw)/2.0
	half_pitch=float(pitch)/2.0
	half_roll=float(roll)/2.0
	cosYaw = cos(half_yaw);
	sinYaw = sin(half_yaw);
	cosPitch = cos(half_pitch);
	sinPitch = sin(half_pitch);
	cosRoll = cos(half_roll);
	sinRoll = sin(half_roll);
	destQuat=[]
	destQuat.append(cosRoll * cosPitch * sinYaw - sinRoll * sinPitch * cosYaw)
	destQuat.append(cosRoll * sinPitch * cosYaw + sinRoll * cosPitch * sinYaw)
	destQuat.append(sinRoll * cosPitch * cosYaw - cosRoll * sinPitch * sinYaw)
	destQuat.append(cosRoll * cosPitch * cosYaw + sinRoll * sinPitch * sinYaw)
	return destQuat

def quat_to_euler(q):
	euler=[0.,0.,0.]#heading-pitch Y, attitude-yaw-Z,bank-roll-tilts-X // Y-azimuth, X-elevation, Z-tilt. // Y Z X
	sqw=q[3]*q[3]
	sqx=q[0]*q[0]
	sqy=q[1]*q[1]
	sqz=q[2]*q[2]
	unit=sqx + sqy + sqz + sqw
	test=q[0]*q[1]+q[2]*q[3]
	if (test > 0.499) : # singularity at north pole
		euler[0]=2 * atan2(q[0],q[3])
		euler[1]=math.pi/2
		euler[2]=0
		return euler
	if (test < -0.499) :# singularity at south pole
		euler[0]=2 * atan2(q[0],q[3])
		euler[1]=-1*math.pi/2
		euler[2]=0
		return euler

	euler[0]=atan2(2*q[1]*q[3]-2*q[0]*q[2],1 - 2*sqy - 2*sqz)
	euler[1]=asin(2*test)
	euler[2]=atan2(2*q[0]*q[3]-2*q[1]*q[2],1 - 2*sqx - 2*sqz)
	return euler

def dot(A,B):
	return((A[0] * B[0]) + (A[1] * B[1]) + (A[2] * B[2]));

def angle(A,B):
	"""give radians angle between vector A and B"""
	normA=N.sqrt(N.sum(A*A))
	normB=N.sqrt(N.sum(B*B))
	return acos(dot(A/normA,B/normB))

def dist(A,B):
  return sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)

def norm(A):
        "Return vector norm"
        return sqrt(sum(A*A))

def normsq(A):
        "Return square of vector norm"
        return abs(sum(A*A))

def normalize(A):
        "Normalize the Vector"
        if (norm(A)==0.0) : return A
	else :return A/norm(A)

def mini_array(array):
	count=0
	mini=9999
	mini_array=N.array([0.,0.,0.])
        for i in xrange(len(array)):
		norm=N.sqrt(N.sum(array[i]*array[i]))
		if N.sum(array[i]) != 0.0 :
			if norm < mini :
				mini_array=array[i]
				mini=norm
	return mini_array


def spAvg(array):
	count=0
	avg=N.array([0.,0.,0.])
        for i in xrange(len(array)):
		if N.sum(array[i]) != 0.0 :
			avg+=array[i]
			count=count+1
	if count !=0 : avg*=1.0/count
	return avg

def spAverage(cube):
	count=0
	avg=N.array([0.,0.,0.])
	lavg=[]
	for c in cube:
	        for x in xrange(len(c)):
        	    for y in xrange(len(c[0])):
               		for z in xrange(len(c[0][0])):
				if N.sum(c[x,y,z]) != 0.0 :
					avg+=c[x,y,z]
					count=count+1
		if count !=0 : avg*=1.0/count
		lavg.append(avg.copy())
		avg=N.array([0.,0.,0.])
		count=0
	return N.array(lavg)

def stddev(values):
    sum = sum2 = 0.
    n = len(values)
    for value in values:
        sum += value
        sum2 += value*value
    from math import sqrt
    stddev = sqrt((n*sum2-sum*sum)/(n*(n-1)))
    return stddev
    
# epsilon for testing whether a number is close to zero
_EPS = numpy.finfo(float).eps * 4.0

# axis sequences for Euler angles
_NEXT_AXIS = [1, 2, 0, 1]

# map axes strings to/from tuples of inner axis, parity, repetition, frame
_AXES2TUPLE = {
    'sxyz': (0, 0, 0, 0), 'sxyx': (0, 0, 1, 0), 'sxzy': (0, 1, 0, 0),
    'sxzx': (0, 1, 1, 0), 'syzx': (1, 0, 0, 0), 'syzy': (1, 0, 1, 0),
    'syxz': (1, 1, 0, 0), 'syxy': (1, 1, 1, 0), 'szxy': (2, 0, 0, 0),
    'szxz': (2, 0, 1, 0), 'szyx': (2, 1, 0, 0), 'szyz': (2, 1, 1, 0),
    'rzyx': (0, 0, 0, 1), 'rxyx': (0, 0, 1, 1), 'ryzx': (0, 1, 0, 1),
    'rxzx': (0, 1, 1, 1), 'rxzy': (1, 0, 0, 1), 'ryzy': (1, 0, 1, 1),
    'rzxy': (1, 1, 0, 1), 'ryxy': (1, 1, 1, 1), 'ryxz': (2, 0, 0, 1),
    'rzxz': (2, 0, 1, 1), 'rxyz': (2, 1, 0, 1), 'rzyz': (2, 1, 1, 1)}

_TUPLE2AXES = dict((v, k) for k, v in _AXES2TUPLE.items())

################################################################################
import sys,os
import glob
plateform=sys.platform

def listDir(dir):
    return glob.glob(dir+"/*")

def findDirectory(dirname,where):
    result=None
    #print where
    if dirname in os.listdir(where):
        print "founded"
        result=os.path.join(where,dirname)
    else :
        for dir in listDir(where):
            if os.path.isdir(dir):
                result = findDirectory(dirname,dir)
                if result != None:
                    break
    return result




