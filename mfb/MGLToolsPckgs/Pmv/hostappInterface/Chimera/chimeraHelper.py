#!/usr/bin/python
#TODO
#stabilize curve and metaball...really unstable and produce segmentation fault
import numpy.oldnumeric as Numeric
import sys, os, os.path, struct, math, string

import copy
import gzip
import types
import popen2

from math import *
import numpy
from numpy import matrix

from Pmv.moleculeViewer import MoleculeViewer
from Pmv.displayCommands import BindGeomToMolecularFragment
from Pmv.trajectoryCommands import PlayTrajectoryCommand

import MolKit
from MolKit.molecule import Atom, AtomSet, BondSet, Molecule , MoleculeSet
from MolKit.protein import Protein, ProteinSet, Residue, Chain, ResidueSet, ResidueSetSelector
from MolKit.stringSelector import CompoundStringSelector
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom
from MolKit.protein import Residue

from types import StringType, ListType
from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI

#Pmv Color Palette
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import DavidGoodsell, DavidGoodsellSortedKeys
from Pmv.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
from Pmv.pmvPalettes import Shapely
from Pmv.pmvPalettes import SecondaryStructureType

#chimera import
import Matrix
import chimera
from chimera import openModels as om

#import psyco
#psyco.full()
#
#GL=Blender.BGL
#
#DGatomIds=['ASPOD1','ASPOD2','GLUOE1','GLUOE2', 'SERHG',
#                        'THRHG1','TYROH','TYRHH',
#                        'LYSNZ','LYSHZ1','LYSHZ2','LYSHZ3','ARGNE','ARGNH1','ARGNH2',
#                        'ARGHH11','ARGHH12','ARGHH21','ARGHH22','ARGHE','GLNHE21',
#                        'GLNHE22','GLNHE2',
#                        'ASNHD2','ASNHD21', 'ASNHD22','HISHD1','HISHE2' ,
#                        'CYSHG', 'HN']
#
#ResidueSelector=ResidueSetSelector()
#
#VERBOSE = 0
#
#def Compose4x4(rot,tr,sc):
#    import Blender
#    from Blender import Mathutils
#    import numpy.oldnumeric as Numeric
#    """ compose a blender matrix of shape (16,) from  a rotation (shape (16,)),
#    translation (shape (3,)), and scale (shape (3,)) """
#    translation=Mathutils.Vector(tr[0],tr[1],tr[2])
#    scale = Mathutils.Vector(sc[0],sc[1],sc[2])
#    mat=rot.reshape(4,4)
#    mat=mat.transpose()
#    mt=Mathutils.TranslationMatrix(translation)
#    mr=Mathutils.Matrix(mat[0],mat[1],mat[2],mat[3])
#    ms=Mathutils.ScaleMatrix(scale.length, 4, scale.normalize())
#    Transformation = mt*mr#*ms
#    return Transformation
#
#
#def start(debug=0):
#    mv = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='pmv', withShell= 0,verbose=False, gui = False)
#    mv.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
#    mv.browseCommands('trajectoryCommands',commands=['openTrajectory'],log=0,package='Pmv')
#    mv.addCommand(PlayTrajectoryCommand(),'playTrajectory',None)
#    mv.embedInto('blender',debug=debug)
#    return mv
#
#
#def compareSel(currentSel,molSelDic):
#    for selname in molSelDic.keys():
#        print currentSel,molSelDic[selname][3]
#        if currentSel[-1] == ';' : currentSel=currentSel[0:-1]
#        if currentSel == molSelDic[selname][3] : return selname
#
#def parseObjectName(o):
#    if type(o) == str : name=o
#    else : name=o.name
#    tmp=name.split("_")
#    if len(tmp) == 1 : #no "_" so not cpk (S_) or ball (B_) stick (T_) or Mesh (Mesh_)
#        return ""
#    else :
#        if tmp[0] == "S" or tmp[0] == "B" : #balls or cpk
#           if len(tmp) == 3 : #molname include '_'
#            hiearchy=name[2:].split(":")
#           else :           
#            hiearchy=tmp[1].split(":") #B_MOL:CHAIN:RESIDUE:ATOMS        
#           return hiearchy
#    return ""
#    
#def parseName(o):
#    if type(o) == str : name=o
#    else : name=o.getName()
#    tmp=name.split("_")
#    if len(tmp) == 1 : #molname
#        hiearchy=name.split(":")
#        if len(hiearchy) == 1 : return [name,""]
#        else : return hiearchy
#    else :
#        hiearchy=tmp[0].split(":") #B_MOL:CHAIN:RESIDUE:ATOMS        
#        return hiearchy
#
#
def getCurrentScene():
    return None#Blender.Scene.GetCurrent()
#
#def updateAppli():
#    Blender.Scene.GetCurrent().update()
#    Blender.Draw.Redraw()
#    Blender.Window.RedrawAll()
#    Blender.Window.QRedrawAll()  
#    Blender.Redraw()
#
#def update():
#    getCurrentScene().update()
#    Draw.Redraw()
#    Blender.Redraw()
#    
#def getObjectName(o):
#    return o.name
#    
def getObject(id=None):
    model = om.list(id = id)
    return model[0]

def readMol(molpath):
    model = om.open(molpath)
    return model[-1]
    
#def setInstance(name,obj, matrix):
#    mesh=obj.getData(False,True)
#    o = Blender.Object.New("Mesh",name)
#    o.link(mesh)
#    o.setMatrix(matrix)
#    return o
#
def setObjectMatrix(o,matrix):
    #o is a chimera model instance
    m=matrix.reshape(4,4)
    m=m.transpose()
    #chimera matrix are 3 by 4 matrices with the first 3 columns
    # being a rotation and the 4th column being a translation.
    cm = Matrix.chimera_xform(m[0:3])
    #xf = o.openState.xform
    #xf.premultiply(Matrix.chimera_xform(m))
    o.openState.xform = cm
    #o.openState.globalXform(cm)

def concatObjectMatrix(o,mat,local=False):
    #o is a chimera model instance
    #matrix is 4x4 transformation matrix
    if local :
        o.openState.localXform(matrixToXform(mat))
        #same as xf.premultiply
    else :
        m=matrix(mat.reshape(4,4))
        xf=matrix(numpy.array(o.openState.xform.getOpenGLMatrix()).reshape(4,4))
        newMat = m*xf
        o.openState.xform = matrixToXform(numpy.array(newMat))
        #o.openState.globalXform(cm)

def matrixToXform(matrix):
    m=numpy.array(matrix).reshape(4,4)
    m=m.transpose()
    #m[0][3]=m[3][0]
    #m[1][3]=m[3][1]
    #m[2][3]=m[3][2]
    #chimera matrix are 3 by 4 matrices with the first 3 columns
    # being a rotation and the 4th column being a translation.
    cm = Matrix.chimera_xform(m[0:3])
    return cm


def translateObj(obj,coord,use_parent=False):
    #make a matrix
    m=Numeric.identity(4,'f')
    m[3][0:3] = coord
    concatObjectMatrix(obj,m)
    #setObjectMatrix(obj,m)
    
def scaleObj(obj,sc):
    #make a matrix
    pass
    
def rotateObj(obj,rot):
    m=Numeric.identity(4,'f')
    m[0:3][0:3] = rot.reshape(4,4)[0:3][0:3]
    concatObjectMatrix(obj,m)
    #setObjectMatrix(obj,m)
    
def newEmpty(name,location=None,visible=0):
    return None

def addObjectToScene(sc,obj,parent=None,centerRoot=True,rePos=None):
    pass
    
#def AddObject(obj,parent=None,centerRoot=True,rePos=None):
#    #objects must first be linked to a scene before they can become parents of other objects.
#    sc = getCurrentScene()
#    if type(obj) == list or type(obj) == tuple: 
#        for o in obj : 
#            if o not in sc.objects : sc.link(o)
#    else : 
#        if obj not in sc.objects : sc.link(obj)
#    #try:
#    #    sc.link(obj)
#    #except :
#    print "OUOS"              
#    if parent != None: 
#        if type(obj) == list or type(obj) == tuple: parent.makeParent(obj)
#        else : parent.makeParent([obj,])
#
#def addCameraToScene(name,Type,focal,center,sc):
#    cam = Blender.Camera.New(Type,name)
#    cam.setScale(focal*2.)
#    cam.clipEnd=1000.    
#    obc = sc.objects.new(cam) # make a new object in this scene using the camera data\n'
#    obc.setLocation (center[0],center[1],center[2])
#    obc.RotZ=2*math.pi
#    obc.restrictSelect=True
#    sc.objects.camera = obc
#    #Window.CameraView()
#
#def addLampToScene(name,Type,rgb,dist,energy,soft,shadow,center,sc):
#    lampe=Lamp.New(Type,name)
#    lampe.R=rgb[0]
#    lampe.G=rgb[1]
#    lampe.B=rgb[2]
#    lampe.setDist(dist)
#    lampe.setEnergy(energy)
#    lampe.setSoftness(soft)
#    if shadow : lampe.setMode("Shadows")
#    obj = sc.objects.new(lampe)
#    obj.loc=(center[0],center[1],center[2])
#    obj.restrictSelect=True
#

def addObjToGeom(obj,geom):
    if type(obj) == list or type(obj) == tuple:
        if type(obj[0]) == list or type(obj[0]) == tuple:    
            #print obj[1]
            geom.obj=[]
            if type(obj[1]) == list or type(obj[1]) == tuple: 
                #geom.mesh=[]
                geom.mesh=obj[1][:]
                #for o in obj[1]:
                #    geom.mesh.append(o.name)
            elif type(obj[1]) == dict :
                geom.mesh={}                                                
                for me in obj[1].keys():
                    geom.mesh[me]=obj[1][me].name
            else :
                geom.mesh=obj[1].name
            geom.obj= obj[0][:]
            #for o in obj[0]:
            #    geom.obj.append(o.name)
        else :
            geom.mesh=obj[1]#.name
            geom.obj=obj[0]#.name    
        #geom.mesh=obj[1]
        #geom.obj=obj[0]
    else : geom.obj=obj#.name
#
#def addMaterial(name,col):
#    #need toc heck if mat already exist\
#    #mats = Material.Get()
#    #if name not in mats :
#    #    mat = Material.New(name)
#    #else :
#    try :
#        mat = Material.New(name)
#        mat.setRGBCol(col[0],col[1],col[2])
#    except :
#        mat = None
#    return mat
#
#def blenderColor(col):
#    if max(col)<= 1.0: col = map( lambda x: x*255, col)
#    return col
#
#def toggleDisplay(ob,display=True):
#    if type(ob) == str : obj=getObject(ob)
#    else : obj=ob
#    obj.restrictDisplay=not display
#    obj.restrictRender=not display
#    #obj.makeDisplayList()
#

#def b_matrix(array):
#    return Mathutils.Matrix(array)
#
#def b_toEuler(bmatrix):
#    return bmatrix.toEuler()
#
#def rotatePoint(pt,m,ax):
#      x=pt[0]
#      y=pt[1]
#      z=pt[2]
#      u=ax[0]
#      v=ax[1]
#      w=ax[2]
#      ux=u*x
#      uy=u*y
#      uz=u*z
#      vx=v*x
#      vy=v*y
#      vz=v*z
#      wx=w*x
#      wy=w*y
#      wz=w*z
#      sa=sin(ax[3])
#      ca=cos(ax[3])
#      pt[0]=(u*(ux+vy+wz)+(x*(v*v+w*w)-u*(vy+wz))*ca+(-wy+vz)*sa)+ m[0]
#      pt[1]=(v*(ux+vy+wz)+(y*(u*u+w*w)-v*(ux+wz))*ca+(wx-uz)*sa)+ m[1]
#      pt[2]=(w*(ux+vy+wz)+(z*(u*u+v*v)-w*(ux+vy))*ca+(-vx+uy)*sa)+ m[2]
#      return pt
#
#def Decompose4x4(matrix):
#    """ takes a matrix in shape (16,) in OpenGL form (sequential values go
#    down columns) and decomposes it into its rotation (shape (16,)),
#    translation (shape (3,)), and scale (shape (3,)) """
#    m = matrix
#    transl = Numeric.array((m[12], m[13], m[14]), 'f')
#    scale0 = Numeric.sqrt(m[0]*m[0]+m[4]*m[4]+m[8]*m[8])
#    scale1 = Numeric.sqrt(m[1]*m[1]+m[5]*m[5]+m[9]*m[9])
#    scale2 = Numeric.sqrt(m[2]*m[2]+m[6]*m[6]+m[10]*m[10])
#    scale = Numeric.array((scale0,scale1,scale2)).astype('f')
#    mat = Numeric.reshape(m, (4,4))
#    rot = Numeric.identity(4).astype('f')
#    rot[:3,:3] = mat[:3,:3].astype('f')
#    rot[:,0] = (rot[:,0]/scale0).astype('f')
#    rot[:,1] = (rot[:,1]/scale1).astype('f')
#    rot[:,2] = (rot[:,2]/scale2).astype('f')
#    rot.shape = (16,)
#    #rot1 = rot.astype('f')
#    return rot, transl, scale
#
#def Compose4x4BGL(rot,trans,scale):
#    import Blender 
#    import numpy.oldnumeric as Numeric
#    GL=Blender.BGL
#    """ compose a matrix of shape (16,) from  a rotation (shape (16,)),
#    translation (shape (3,)), and scale (shape (3,)) """
#    GL.glMatrixMode(GL.GL_MODELVIEW)
#    GL.glPushMatrix()
#    GL.glLoadIdentity()
#    GL.glTranslatef(float(trans[0]),float(trans[1]),float(trans[2]))
#    GL.glMultMatrixf(rot)
#    GL.glScalef(float(scale[0]),float(scale[1]),float(scale[2]))
#    m = Numeric.array(GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)).astype('f')
#    GL.glPopMatrix()
#    return Numeric.reshape(m,(16,))
#
#def norm(A):
#        "Return vector norm"
#        return Numeric.sqrt(sum(A*A))
#
#
#
#def dist(A,B):
#  return Numeric.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)
#
#def normsq(A):
#    "Return square of vector norm"
#    return abs(sum(A*A))
#
#def normalize(A):
#    "Normalize the Vector"
#    if (norm(A)==0.0) : return A
#    else :return A/norm(A)
#
#def getCenter(coords):
#    """sets self.center<-getCenter(self)"""
#    coords = Numeric.array(coords)#self.allAtoms.coords
#    center = sum(coords)/(len(coords)*1.0)
#    center = list(center)
#    for i in range(3):
#        center[i] = round(center[i], 4)
#    #print "center =", self.center
#    return center
#
#AtmRadi = {"N":"1.54","C":"1.7","CA":"1.7","O":"1.52","S":"1.85","H":"1.2","P" : "1.04"}
#matlist = str(Material.Get ())
#
##check and create atoms materials
##first remove keys CA
#for atms in AtomElements.keys():
#    if not ('[Material "'+atms+'"]' in matlist):
#        mat = Material.New(atms)
#        col=(AtomElements[atms])
#        mat.setRGBCol(col[0],col[1],col[2])
##DG colors
#for atms in DavidGoodsell.keys():
#    if not ('[Material "'+atms[0]+'"]' in matlist):
#        mat = Material.New(atms)
#        col=(DavidGoodsell[atms])
#        mat.setRGBCol(col[0],col[1],col[2])
#
#if not ('[Material "anyatom"]' in matlist):
#    mat = Material.New('anyatom')
#    mat.R = 0.8
#    mat.G = 1.0
#    mat.B = 1.0
#
#if not ('[Material "sticks"]' in matlist):
#    mat = Material.New('sticks')
#    mat.R = 0.8
#    mat.G = 0.8
#    mat.B = 0.8
#
##check and create amino acid materials
#for res in RasmolAmino.keys():
#    if not ('[Material "'+res+'"]' in matlist):
#        mat = Material.New(res)
#        col=(RasmolAmino[res])
#        mat.setRGBCol(col[0],col[1],col[2])
#
##create an additional mat for Hetatm Mol
#if not ('[Material "hetatm"]' in matlist):
#    mat = Material.New('hetatm')
#    mat.R = 0.0
#    mat.G = 1.0
#    mat.B = 0.0
#
#from DejaVu.colors import *
#for cn in cnames:
#    if not ('[Material "'+cn+'"]' in matlist):
#        mat = Material.New(cn)
#        col=eval(cn)
#        mat.setRGBCol(col[0],col[1],col[2])
#
#ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']
##check and create secondary structure materials
#SecondaryStructureType['Sheet']=SecondaryStructureType['Strand']
#for ss in SecondaryStructureType.keys():
#    if not ('[Material "'+ss[:4]+'"]' in matlist):
#        mat = Material.New(ss[:4])
#        col=(SecondaryStructureType[ss])
#        mat.setRGBCol(col[0],col[1],col[2])
#    
#def createDejaVuColorMat():
#    Mat=[]
#    from DejaVu.colors import *
#    for col in cnames:
#        Mat.append(addMaterial(col,eval(col)))
#    return Mat
#
#def retrieveColorMat(color):
#    from DejaVu.colors import *
#    for col in cnames:
#        if color ==	eval(col) :
#            return Material.Get(col)		
#    return None
#
#def computeRadius(protein,center=None):
#        if center == None : center = protein.getCenter()
#        rs = 0.
#        for atom in protein.allAtoms:    
#            r = dist(center,atom._coords[0])
#            if r > rs:
#                rs = r
#        return rs
#
#
#def lookupDGFunc(atom):
#        assert isinstance(atom, Atom)
#        if atom.name in ['HN']:
#            atom.atomId = atom.name
#        else:
#            atom.atomId=atom.parent.type+atom.name
#        if atom.atomId not in DGatomIds: 
#            atom.atomId=atom.element
#        return atom.atomId
#
#def Trace(x):
#    #x is a list of atoms,if CA-> CAtrace
#    #deprecated see Tube
#    stick=[]  
#    #coord1=x[0].atms[(x[0].atms.CApos())].xyz()
#    #coord2=x[1].atms[(x[1].atms.CApos())].xyz()
#    coord1=x[0]._coords[0]
#    coord2=x[1]._coords[0]
#    x1 = float(coord1[0])
#    y1 = float(coord1[1])
#    z1 = float(coord1[2])
#    x2 = float(coord2[0])
#    y2 = float(coord2[1])
#    z2 = float(coord2[2])
#    laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
#    wsz = math.atan2((y1-y2), (x1-x2))
#    wz = math.acos((z1-z2)/laenge)
#
#    me=Mesh.Primitives.Cylinder(32, 1., laenge)
#    #mat = Material.Get('sticks')
#    #me.materials=[mat]
#    OBJ=Object.New('Mesh')
#    stick.append(OBJ)
#    stick[0].link(me)
#    stick[0].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
#    stick[0].RotY = wz
#    stick[0].RotZ = wsz
#    #scn.link(stick[0])
#
#    for i in range(1,len(x)-1):
#     #coord1=x[i].atms[x[i].atms.CApos()].xyz() #x.xyz()[i].split()
#     #coord2=x[i+1].atms[x[i+1].atms.CApos()].xyz() #x.xyz()[i+1].split()
#     coord1=x[i]._coords[0] #x.xyz()[i].split()
#     coord2=x[i+1]._coords[0] #x.xyz()[i+1].split()
#     x1 = float(coord1[0])
#     y1 = float(coord1[1])
#     z1 = float(coord1[2])
#     x2 = float(coord2[0])
#     y2 = float(coord2[1])
#     z2 = float(coord2[2])
#     laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
#     wsz = math.atan2((y1-y2), (x1-x2))
#     wz = math.acos((z1-z2)/laenge)
#     me=Mesh.Primitives.Cylinder(32, 1., laenge)
#     #mat = Material.Get('sticks')
#     #me.materials=[mat]
#     OBJ=Object.New('Mesh')
#     stick.append(OBJ)
#     stick[i].link(me)
#     stick[i].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
#     stick[i].RotY = wz
#     stick[i].RotZ = wsz
#     #scn.link(stick[i])
#     #scn= Scene.GetCurrent()
#     #ob = scn.objects.new(stick)
#    return stick
#
#def bezFromVecs(vecs0,vecs1):
#                       '''
#                       Bezier triple from 3 vecs, shortcut functon
#                       '''
#                       dd=[0.,0.,0.]
#                       vecs=[0.,0.,0.]
#                       for i in range(3): dd[i]=vecs1[i]-vecs0[i]
#                       for i in range(3): vecs[i]=vecs1[i]+dd[i]
#                       #vecs2=vecs1+(vecs0*-1)
#                       bt= BezTriple.New(vecs0[0],vecs0[1],vecs0[2],vecs1[0],vecs1[1],vecs1[2],vecs[0],vecs[1],vecs[2])
#                       bt.handleTypes= (BezTriple.HandleTypes.AUTO, BezTriple.HandleTypes.AUTO)
#                       
#                       return bt
#def bezFromVecs2(vecs0,vecs1,vecs):
#                       '''
#                       Bezier triple from 3 vecs, shortcut functon
#                       '''
#                       #projection of v1 on v0->v2
#                       #
#                       B=Numeric.array([0.,0.,0.])
#                       H1=Numeric.array([0.,0.,0.])
#                       H2=Numeric.array([0.,0.,0.])
#                       for i in range(3): B[i]=vecs1[i]-vecs0[i]                      
#                       A=Numeric.array([0.,0.,0.])
#                       for i in range(3): A[i]=vecs[i]-vecs0[i]
#                       #Projection B on A
#                       scalar=(((A[0]*B[0])+(A[1]*B[1])+(A[2]*B[2]))/((A[0]*A[0])+(A[1]*A[1])+(A[2]*A[2])))
#                       C=scalar*A
#                       #vector C->A
#                       dep=A-C
#                       for i in range(3):
#                            vecs0[i]=(vecs0[i]+dep[i])
#                            vecs[i]=(vecs[i]+dep[i])
#                       for i in range(3): H1[i]=(vecs[i]-vecs1[i])
#                       for i in range(3): H2[i]=(-vecs[i]+vecs1[i])
#                       H1=normalize(H1.copy())*3.
#                       H2=normalize(H2.copy())*3.
#                       vecs0=Vector(vecs1[0]-H1[0],vecs1[1]-H1[1],vecs1[2]-H1[2])
#                       vecs=Vector(vecs1[0]-H2[0],vecs1[1]-H2[1],vecs1[2]-H2[2])
#                       #vecs2=vecs1+(vecs0*-1)
#                       bt= BezTriple.New(vecs0[0],vecs0[1],vecs0[2],vecs1[0],vecs1[1],vecs1[2],vecs[0],vecs[1],vecs[2])
#                       bt.handleTypes= (BezTriple.HandleTypes.FREE , BezTriple.HandleTypes.FREE )
#                       
#                       return bt
#
#def bez2FromVecs(vecs1):
#                       
#                       bt= BezTriple.New(vecs1[0],vecs1[1],vecs1[2])
#                       bt.handleTypes= (BezTriple.HandleTypes.AUTO  , BezTriple.HandleTypes.AUTO  )
#                       
#                       return bt
#                      
#def bezFromVecs1(vecs0,vecs1,vecs): #tYPE vECTOR
#                       '''
#                       Bezier triple from 3 vecs, shortcut functon
#                       '''
#                       #rotatePoint(pt,m,ax)
#                       A=Vector(0.,0.,0.)
#                       B=Vector(0.,0.,0.)
#                       H2=Vector(0.,0.,0.)
#                       A=vecs0-vecs1                     
#                       B=vecs-vecs1
#                       crP=A.cross(B)
#                       crP.normalize()
#                       A.normalize()
#                       B.normalize()
#                       #angleA,B: acos of the dot product of the two (normalised) vectors:
#                       dot=A.dot(B)
#                       angle=math.acos(dot)
#                       print angle
#                       print math.degrees(angle)
#                       newA=(math.radians(90)-angle/2)
#                       nA=rotatePoint(A*1.35,vecs1,[crP[0],crP[1],crP[2],-newA])
#                       nB=rotatePoint(B*1.35,vecs1,[crP[0],crP[1],crP[2],newA])
#                       vecs0=Vector(nA[0],nA[1],nA[2])
#                       vecs=Vector(nB[0],nB[1],nB[2])
#                       #vecs2=vecs1+(vecs0*-1)
#                       bt= BezTriple.New(vecs0[0],vecs0[1],vecs0[2],vecs1[0],vecs1[1],vecs1[2],vecs[0],vecs[1],vecs[2])
#                       bt.handleTypes= (BezTriple.HandleTypes.FREE , BezTriple.HandleTypes.FREE )
#                       
#                       return bt
#
#
#    
#def bezList2Curve(x,typeC):
#    '''
#    Take a list or vector triples and converts them into a bezier curve object
#    '''
#    # Create the curve data with one point
#    cu= Curve.New()
#    #coord0=x[0].atms[(x[0].atms.Cpos())-1].xyz()
#    #coord1=x[0].atms[(x[0].atms.Cpos())].xyz()
#    #need to check the type of x :atom list or coord list
#    if isinstance(x[0],Atom) :
#        coord1=Numeric.array(x[0]._coords[0])
#        coord2=Numeric.array(x[1]._coords[0])
#    else :
#        coord1=Numeric.array(x[0])
#        coord2=Numeric.array(x[1])    
#    print coord1
#    print coord2
#    coord0=coord1-(coord2-coord1)
#
#    if typeC == "tBezier" : cu.appendNurb(bezFromVecs(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]))) # We must add with a point to start with
#    elif typeC == "sBezier" : cu.appendNurb(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
#    else : cu.appendNurb(bezFromVecs1(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]),Vector(coord2[0],coord2[1],coord2[2]))) # We must add with a point to start with
#
#    cu_nurb= cu[0] # Get the first curve just added in the CurveData
#               
#               
#    i= 1 # skip first vec triple because it was used to init the curve
#    while i<(len(x)-1):
#        if isinstance(x[0],Atom) :
#            coord0=x[i-1]._coords[0]#atms[(x[i].atms.Cpos())-1].xyz()
#            coord1=x[i]._coords[0]#atms[(x[i].atms.Cpos())].xyz()
#            coord2=x[i+1]._coords[0]
#        else :
#            coord0=x[i-1]#atms[(x[i].atms.Cpos())-1].xyz()
#            coord1=x[i]#atms[(x[i].atms.Cpos())].xyz()
#            coord2=x[i+1]
#        bt_vec_tripleAv= Vector(coord0[0],coord0[1],coord0[2])
#        bt_vec_triple  = Vector(coord1[0],coord1[1],coord1[2])
#        bt_vec_tripleAp= Vector(coord2[0],coord2[1],coord2[2])
#        bt= bezFromVecs(bt_vec_tripleAv,bt_vec_triple)
#
#        if typeC == "tBezier" : cu_nurb.append(bt)
#        elif typeC == "sBezier" : cu_nurb.append(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
#        else : cu_nurb.append(bezFromVecs1(bt_vec_tripleAv,bt_vec_triple,bt_vec_tripleAp))
#        i+=1              
#
#    if isinstance(x[0],Atom) :
#        coord0=Numeric.array(x[len(x)-2]._coords[0])
#        coord1=Numeric.array(x[len(x)-1]._coords[0])
#    else :
#        coord0=Numeric.array(x[len(x)-2])
#        coord1=Numeric.array(x[len(x)-1])        
#    print coord1
#    print coord2
#    coord2=coord1+(coord1-coord0)
#
#    if typeC == "tBezier" : cu_nurb.append(bezFromVecs(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]))) # We must add with a point to start with
#    elif typeC == "sBezier" : cu_nurb.append(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
#    else : cu_nurb.append(bez2FromVecs(Vector(coord1[0],coord1[1],coord1[2])))
#    #else : cu_nurb.append(bezFromVecs1(Vector(coord0[0],coord0[1],coord0[2]),Vector(coord1[0],coord1[1],coord1[2]),Vector(coord2[0],coord2[1],coord2[2]))) # We must add with a point to start with
#                
#    return cu
#    
#def bezSquare(r,name):
#      kappa=4*((math.sqrt(2)-1)/3)
#      l = r * kappa
#      pt1=[0.,r,0.]
#      pt1h=[-l,r,0.]
#      pt2=[r,0.,0.]
#      pt2h=[r,l,0.]
#      pt3=[0.,-r,0.]
#      pt3h=[l,-r,0.]
#      pt4=[-r,0.,0.]
#      pt4h=[-r,-l,0.]
#      cu= Curve.New(name)
#      coord1=pt1
#      cu.appendNurb(bez2FromVecs(pt1))
#      cu_nurb=cu[0]
#      coord1=pt2
#      cu_nurb.append(bez2FromVecs(pt2))
#      coord1=pt3
#      cu_nurb.append(bez2FromVecs(pt3))
#      coord1=pt4
#      cu_nurb.append(bez2FromVecs(pt4))
#      cu_nurb.append(bez2FromVecs(pt1))
#      #scn= Scene.GetCurrent()
#      #ob = scn.objects.new(cu)
#      return cu
#
#
#def bezCircle(r,name):
#      kappa=4*((math.sqrt(2)-1)/3)
#      l = r * kappa
#      pt1=[0.,r,0.]
#      pt1h=[-l,r,0.]
#      pt2=[r,0.,0.]
#      pt2h=[r,l,0.]
#      pt3=[0.,-r,0.]
#      pt3h=[l,-r,0.]
#      pt4=[-r,0.,0.]
#      pt4h=[-r,-l,0.]
#      cu= Curve.New(name)
#      coord1=pt1
#      cu.appendNurb(bezFromVecs(pt1h,pt1))
#      cu_nurb=cu[0]
#      coord1=pt2
#      cu_nurb.append(bezFromVecs(pt2h,pt2))
#      coord1=pt3
#      cu_nurb.append(bezFromVecs(pt3h,pt3))
#      coord1=pt4
#      cu_nurb.append(bezFromVecs(pt4h,pt4))
#      cu_nurb.append(bezFromVecs(pt1h,pt1))
#      #scn= Scene.GetCurrent()
#      #ob = scn.objects.new(cu)
#      return cu
#
#def Centroid(f,P0) : 
#  for v in f.v: 
#    for n in [0,1,2] : 
#       P0[n]+=v.co[n]/len(f.v) 
#  return P0
#
#def mean(list):
#    """
#    Given a list or tuple, will return the mean.
#    Usage mean(list)
#    """
#    
#    sum = 0;
#    for item in list:
#        sum += item
#        
#    return(sum / len(list))
#
#def makeRuban(x,str_type,r,name,scene):
#    #the bezierCurve"tBezier"
#    cu=bezList2Curve(x,str_type)
#    #the circle
#    if name == "Circle" : ob1 = scene.objects.new(bezCircle(r,name))
#    if name == "Square" : ob1 = scene.objects.new(bezSquare(r,name))
#    #extrude
#    cu.setBevOb(ob1)
#    cu.setFlag(1)
#    #make the object
#    ob = scene.objects.new(cu)
#    return ob
#
#def spline(name,coords,type="",extrude_obj=None,scene=None,parent=None):
#    #Type : "sBezier", "tBezier" or ""
#    if scene is None :
#        scene = getCurrentScene()
#    cu=bezList2Curve(coords,type)
#    cu.name = name
#    if extrude_obj is not None :
#        cu.setBevOb(extrude_obj)
#    cu.setFlag(1)
#    ob = scene.objects.new(cu)
#    if parent is not None :
#        parent.makeParent([ob])
#    return ob,cu
#
#def createShapes2D(doc=None,parent=None):
#    if doc is None :
#        doc = getCurrentScene()    
#    shape2D={}
#    circle = doc.objects.new(bezCircle(0.3,'Circle'))
#    square = doc.objects.new(bezSquare(0.3,'Square'))
#    shape2D['Coil']=circle
#    shape2D['Stra']=square
#    return shape2D,[circle,square,None]
#    
#def findparent(name, bones):
#    atms=name.split('_')
#    print atms    
#    for names in bones.keys() : 
#        patms=names.split('_')
#        print patms
#        if atms[0] == patms[1] : 
#            print "ok"
#            return bones[names]
#    return bones["root"]
#
#def findconectedparent(atoms,bones):
#    pass#get the bonds
#    #for bond in atoms.bonds:
#    #        
#    #for names in bones.keys() : 
#
#
#            
#def atoms_armature(name,x,scn):
#    armObj = Object.New('Armature', name)
#    armData = Armature.New()
#    armData.makeEditable()
#    armData.autoIK=bool(1)
#    armData.vertexGroups=bool(1)
#    #N=nbones
#    bones= {}
#    first=True
#
#    eb = Armature.Editbone()
#    eb.roll = 10
#    bones["root"]=eb
#    armData.bones['bone0']=eb
#    #print x.bonds,len(x.bonds[0])
#    #x is the bond set for the selection given, it givent the interconection between atoms
#    for i in range(len(x)):
#        armData.makeEditable()
#        eb = Armature.Editbone()
#        eb.roll = 10
#        print "bone"+str(i)
#        bond=x.bonds[0][i]
#        coord1=x[0]._coords[0]
#        coord2=x[0]._coords[0]        
#        fullname=x[0].full_name()
#        eb.head = Vector(coord1[0],coord1[1],coord1[2])
#        eb.tail = Vector(coord2[0],coord2[1],coord2[2])
#        eb.headRadius=x[0].vdwRadius#0.5
#        eb.tailRadius=x[0].vdwRadius#0.5
#        eb.deformDist=0.6
#        if first : first=False
#        else : 
#            eb.options = [Armature.HINGE, Armature.CONNECTED]
#            parent=findconectedparent(x[0],bones)
#            eb.parent = parent
#        bones[fullname]=eb
#        #eb.parent = armData.bones["bone"+str(i-1)]
#        armData.bones['bone'+str(i+1)] = eb
#    armObj.link(armData)
#    armData.update()
#    scn.objects.link(armObj)
#    return armObj
#
#def bond_armature(name,x,scn):
#    armObj = Object.New('Armature', name)
#    armData = Armature.New()
#    armData.makeEditable()
#    armData.autoIK=bool(1)
#    armData.vertexGroups=bool(1)
#    #N=nbones
#    bones= {}
#    first=True
#
#    eb = Armature.Editbone()
#    eb.roll = 10
#    bones["root"]=eb
#    armData.bones['bone0']=eb
#    print x.bonds,len(x.bonds[0])
#    #x is the bond set for the selection given, it givent the interconection between atoms
#    for i in range(len(x.bonds[0])):
#        armData.makeEditable()
#        eb = Armature.Editbone()
#        eb.roll = 10
#        print "bone"+str(i)
#        bond=x.bonds[0][i]
#        coord1=bond.atom1._coords[0]
#        coord2=bond.atom2._coords[0]        
#        fullname=bond.atom1.full_name()+"_"+bond.atom2.full_name()
#        eb.head = Vector(coord1[0],coord1[1],coord1[2])
#        eb.tail = Vector(coord2[0],coord2[1],coord2[2])
#        eb.headRadius=bond.atom1.vdwRadius#0.5
#        eb.tailRadius=bond.atom2.vdwRadius#0.5
#        eb.deformDist=0.6
#        if first : first=False
#        else : 
#            eb.options = [Armature.HINGE, Armature.CONNECTED]
#            parent=findparent(fullname,bones)
#            eb.parent = parent
#        bones[fullname]=eb
#        #eb.parent = armData.bones["bone"+str(i-1)]
#        armData.bones['bone'+str(i+1)] = eb
#    armObj.link(armData)
#    armData.update()
#    scn.objects.link(armObj)
#    return armObj
#
#def armature(name,x,scn=None,root=None):
# if scn is None:
#    scn = getCurrentScene()
# armObj = Object.New('Armature', name)
# armData = Armature.New()
# armData.makeEditable()
# armData.autoIK=bool(1)
# armData.vertexGroups=bool(1)
# #N=nbones
# bones= []
# eb = Armature.Editbone()
# eb.roll = 10
# #eb.parent = arm.bones['Bone.003']
# #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
# #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
# coord1=x[0]._coords[0]
# coord2=x[1]._coords[0]        
# eb.head = Vector(coord1[0],coord1[1],coord1[2])
# eb.tail = Vector(coord2[0],coord2[1],coord2[2])
# eb.headRadius=x[0].vdwRadius#0.5
# eb.tailRadius=x[0].vdwRadius#0.5
# eb.deformDist=0.4
# #eb.weight=0.02
# #eb.options = [Armature.NO_DEFORM]
# bones.append(eb)
# armData.bones['bone0'] = bones[0]
#
# for i in range(1,len(x)-1):
#  print i
#  print i-1
#  armData.makeEditable()
#  eb = Armature.Editbone()
#  eb.roll = 10
#  print "bone"+str(i-1)
#  #coord1=x[i].atms[x[i].atms.CApos()].xyz() #x.xyz()[i].split()
#  #coord2=x[i+1].atms[x[i+1].atms.CApos()].xyz() #x.xyz()[i+1].split()
#  coord1=x[i]._coords[0] #x.xyz()[i].split()
#  coord2=x[i+1]._coords[0] #x.xyz()[i+1].split()
#  eb.head = Vector(coord1[0],coord1[1],coord1[2])
#  eb.tail = Vector(coord2[0],coord2[1],coord2[2])
#  eb.headRadius=x[i].vdwRadius#0.5
#  eb.tailRadius=x[i+1].vdwRadius
#  eb.deformDist=0.4
#
# #if ( (i % 2) == 1 ) : eb.options = [Armature.HINGE, Armature.CONNECTED]
# #if ( (i % 2) == 0 ) : eb.options = [Armature.HINGE, Armature.CONNECTED,Armature.NO_DEFORM]
#  eb.options = [Armature.HINGE, Armature.CONNECTED]
#  eb.parent = bones[i-1]
#  bones.append(eb)
#  #eb.parent = armData.bones["bone"+str(i-1)]
#  armData.bones['bone'+str(i)] = bones[i]
#
#  #for bone in armData.bones.values():
#  #   #print bone.matrix['ARMATURESPACE']
#  #   print bone.parent, bone.name
#  #   print bone.options, bone.name
#
# armObj.link(armData)
# armData.update()
# addObjectToScene(scn,armObj,parent=root)
# #scn.objects.link(armObj)
# return armObj
#
#def add_armature(armObj,obj):
#     print obj
#     mods = obj.modifiers
#     print mods
#     mod=mods.append(Modifier.Types.ARMATURE)
#     mod[Modifier.Settings.OBJECT] = armObj
#     print mod
#     obj.addVertexGroupsFromArmature(armObj)
#     print 'done'
#
#
#def metaballs(name,atoms,scn=None,root=None):
#    if scn == None:
#        scn = getCurrentScene()
#    metab = Blender.Metaball.New()
#    metab.name = name
#    for at in atoms:
#        atN=at.name
#        atC=at.coords
#        if atN[0] not in AtomElements.keys() : atN="A"
#        rad=AtmRadi[atN[0]]
#        me=metab.elements.add()
#        me.radius=float(rad)*3.  
#        #mat = Material.Get(atN[0])
#        me.co = Blender.Mathutils.Vector(atC[0], atC[1], atC[2])    
#        #me.materials=[mat]
#    ob_mb = scn.objects.new(metab)
#    root.makeParent([ob_mb,])
#    return None,ob_mb
#
#def box(name,center=[0.,0.,0.],size=[1.,1.,1.],cornerPoints=None,visible=1):
#     import numpy
#     me=Mesh.Primitives.Cube(1.0)
#     me.name = "mesh_"+name   
#     addMaterial(name,[1.,1.,0.])
#     bx=getCurrentScene().objects.new(me,name)
#     if cornerPoints != None :
#         for i in range(3):
#             size[i] = cornerPoints[1][i]-cornerPoints[0][i]
#         center=(numpy.array(cornerPoints[0])+numpy.array(cornerPoints[1]))/2.
#     bx.setLocation(float(center[0]),float(center[1]),float(center[2]))
#     bx.setSize(float(size[0]),float(size[1]),float(size[2]))
#     bx.setDrawType(2) #wire
#     return bx
#
#def Sphere(name,res=16.,radius=1.0,pos=None):
# 	me=Mesh.Primitives.UVsphere(res,res,radius)#diameter
# 	me.name = "mesh_"+name
# 	addMaterial(name,[1.,1.,0.])
#	mat = Material.Get(name)
#	me.materials=[mat]
#	OBJ=getCurrentScene().objects.new(me,name)
# 	if pos == None : pos = [0.,0.,0.]
#	OBJ.setLocation(float(pos[0]),float(pos[1]),float(pos[2]))   
#	return OBJ
#
#def Cylinder(name,radius=1.,length=1.,res=16,pos = None):
#    #import numpy
#    diameter = 2*radius
#    me=Mesh.Primitives.Cylinder(res, diameter, length)#
#    me.name = "mesh_"+name
#    #addMaterial(name,[1.,1.,0.])
#    cyl=getCurrentScene().objects.new(me,name)
#    if pos != None : cyl.setLocation(float(pos[0]),float(pos[1]),float(pos[2]))   
#    return cyl
#
#"""
#def createMeshSphere(**kwargs):
#        # default the values
#        radius = kwargs.get('radius',1.0)
#        diameter = radius *2.0
#        segments = kwargs.get('segments',8)
#        rings = kwargs.get('rings',8)
#        loc   = kwargs.get('location',[0,0,0])
#        useIco = kwargs.get('useIco',False)
#        useUV = kwargs.get('useUV',True)
#        subdivisions = kwargs.get('subdivisions',2)
#        if useIco:
#            sphere = Blender.Mesh.Primitives.Icosphere(subdivisions,diameter)
#        else:    
#            sphere = Blender.Mesh.Primitives.UVsphere(segments,rings,diameter)
#        #ob = self.scene.objects.new(item,name)    
#        #ob.setLocation(loc)
#        return sphere
#"""
#def oldTube(name,nTube,x,scn,armObj,res=32,size=0.25,sc=2.,join=0):
# print "size sel"
# print len(x)
# stick=[]
# tube=[]
# size=size*2.
# #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
# #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
# coord1=x[0]._coords[0]
# coord2=x[1]._coords[0]
# x1 = float(coord1[0])
# y1 = float(coord1[1])
# z1 = float(coord1[2])
# x2 = float(coord2[0])
# y2 = float(coord2[1])
# z2 = float(coord2[2])
# laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
# wsz = atan2((y1-y2), (x1-x2))
# wz = acos((z1-z2)/laenge)
# me=Mesh.Primitives.Cylinder(res, size, laenge/sc) #1. CAtrace, 0.25 regular |sc=1 CATrace, 2 regular
# mat = Material.Get('sticks')
# me.materials=[mat]
# tube.append(me)
# #OBJ=Object.New('Mesh')
# fullname = x[0].full_name()
# OBJ=Object.New('Mesh',"T_"+fullname)
# stick.append(OBJ)
# stick[0].link(me)
# stick[0].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
# stick[0].RotY = wz
# stick[0].RotZ = wsz
# if armObj != None : 
#     mods = stick[0].modifiers
#     mod=mods.append(Modifier.Types.ARMATURE)
#     mod[Modifier.Settings.OBJECT] = armObj
# scn.link(stick[0])
# for i in range(1,len(x)-1):
#  coord1=x[i]._coords[0] #x.xyz()[i].split()
#  coord2=x[i+1]._coords[0] #x.xyz()[i+1].split()
#  x1 = float(coord1[0])
#  y1 = float(coord1[1])
#  z1 = float(coord1[2])
#  x2 = float(coord2[0])
#  y2 = float(coord2[1])
#  z2 = float(coord2[2])
#  laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
#  wsz = atan2((y1-y2), (x1-x2))
#  wz = acos((z1-z2)/laenge)
#  me=Mesh.Primitives.Cylinder(res, size, laenge/sc)
#  mat = Material.Get('sticks')
#  me.materials=[mat]
#  tube.append(me)
#  fullname = x[i].full_name()
#  OBJ=Object.New('Mesh',"T_"+fullname)
#  #OBJ=Object.New('Mesh')
#  stick.append(OBJ)
#  stick[i].link(me)
#  stick[i].setLocation(float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2)
#  stick[i].RotY = wz
#  stick[i].RotZ = wsz
#  if armObj != None : 
#     mods = stick[i].modifiers
#     mod=mods.append(Modifier.Types.ARMATURE)
#     mod[Modifier.Settings.OBJECT] = armObj
#  scn.link(stick[i])
# if join==1 : 
#     stick[0].join(stick[1:])
#     for ind in range(1,len(stick)):
#        #obj[0].join([obj[ind]])
#        scn.unlink(stick[ind])
#    #obj[0].setName(name)
# return stick,tube
#
#def getStickProperties(coord1,coord2):
#    x1 = float(coord1[0])
#    y1 = float(coord1[1])
#    z1 = float(coord1[2])
#    x2 = float(coord2[0])
#    y2 = float(coord2[1])
#    z2 = float(coord2[2])
#    laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
#    wsz = atan2((y1-y2), (x1-x2))
#    wz = acos((z1-z2)/laenge)
#    return laenge,wsz,wz,[float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2]
#    
#
#def updateTubeMesh(geom,cradius=1.0,quality=0):
#    #print "updateTubeMesh"
#    mesh=NMesh.GetRaw("mesh_"+geom.mesh)
#    basemesh = NMesh.GetRaw("mesh_baseCyl")
#    #reset mesh
#    #mats=mesh.materials
#    mesh.verts=basemesh.verts[:]
#    mesh.faces=basemesh.faces[:]
#    #new sacle
#    #cradius = cradius*1/0.2 
#    Smatrix=ScaleMatrix(cradius, 4)
#    Smatrix[2][2] = 1.
#    mesh.transform(Smatrix)
#    #mesh.materials = mats
#    #update
#    mesh.update()
#    #print "done"
#
#def updateTubeObj(o,coord1,coord2):
#        laenge,wsz,wz,coord=getStickProperties(coord1,coord2)
#        o.SizeZ = laenge
#        translateObj(o,coord)
#        #o.setLocation(coord[0],coord[1],coord[2])
#        o.RotY = wz
#        o.RotZ = wsz
#
#def updateTubeObjs(g):
#    if not hasattr(g,'obj') : return
#    newpoints=g.getVertices()
#    newfaces=g.getFaces()
#    for i,o in enumerate(g.obj):
#        laenge,wsz,wz,coord=getStickProperties(points[faces[i][0]],points[faces[i][1]])
#        o.SizeZ = laenge
#        translateObj(o,coord)
#        #o.setLocation(coord[0],coord[1],coord[2])
#        o.RotY = wz
#        o.RotZ = wsz
#
#def instancesCylinder(name,points,faces,radii,mesh,colors,scene,parent=None):
#    cyls=[]
#    mat = None
#    if len(colors) == 1:
#        mat = addMaterial('mat_'+name,colors[0])
#    for i in xrange(len(faces)):
#        laenge,wsz,wz,coord=getStickProperties(points[faces[i][0]],points[faces[i][1]]) 	
#        cname=name+str(i)
#        mesh=Mesh.Get("mesh_"+mesh.getName().split("_")[1])    #"mesh_"+name
#        if mat == None : mat = addMaterial("matcyl"+str(i),colors[i])
#        me.materials=[mat]
#        obj=Object.New('Mesh',spname)
#        obj.link(mesh)
#        #obj=scene.objects.new(mesh,cname)
#        obj.setLocation(float(coord[0]),float(coord[1]),float(coord[2]))
#        obj.RotY = wz
#        obj.RotZ = wsz
#        obj.setSize(float(radii[i]),float(radii[i]),float(laenge))
#        cyls.append(obj)
#    AddObject(cyls,parent=parent)
#    return cyls
#
#def oneCylinder(name,coord1,coord2,instance,material=None):
#    laenge,wsz,wz,coord=getStickProperties(coord1,coord2)
#    if instance == None : 
#        obj = Cylinder(name)
#    else : 
#        obj=getCurrentScene().objects.new(instance,name)
#    translateObj(obj,coord)
#    #obj.setLocation(float(coord[0]),float(coord[1]),float(coord[2]))
#    obj.RotY = wz
#    obj.RotZ = wsz
#    scaleObj(obj,[1.,1.,float(laenge)])
#    #obj.setSize(1.,1.,float(laenge))
#    if material != None :
#        obj.setMaterials([material])
#        obj.colbits = 1<<0
#        #print obj,material
#    return obj
#
#def oneStick(atm1,atm2,hiera,instance,parent):
#    #mol=atm1.getParentOfType(Protein)
#    c0=numpy.array(atm1.coords)
#    c1=numpy.array(atm2.coords)
#    name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)
#    mat = Material.Get('sticks')
#    obj=oneCylinder(name,c0,c1,instance,material=mat)
#    if parent is not None : parent.makeParent([obj,])
#    toggleDisplay(obj,display=False)
#    return obj
#    
#def biStick(atm1,atm2,hiera,instance,parent):
#    #mol=atm1.getParentOfType(Protein)
#    c0=numpy.array(atm1.coords)
#    c1=numpy.array(atm2.coords)
#    vect = c1 - c0
##    name1="T_"+atm1.full_name()+"_"+atm2.name
##    name2="T_"+atm2.full_name()+"_"+atm1.name
#    n1=atm1.full_name().split(":")
#    n2=atm2.full_name().split(":")
#    name1="T_"+n1[1]+"_"+n1[2]+"_"+n1[3]+"_"+atm2.name
#    name2="T_"+n2[1]+"_"+n2[2]+"_"+n2[3]+"_"+atm1.name
#    
#    mat = Material.Get(atm1.name[0])
#    if mat == None :
#        mat = addMaterial(atm1.name[0],[0.,0.,0.])
#    obj1=oneCylinder(name1,c0,(c0+(vect/2.)),instance,material=mat)
#    
#    mat = Material.Get(atm2.name[0])
#    if mat == None :
#        mat = addMaterial(atm2.name[0],[0.,0.,0.])
#    obj2=oneCylinder(name2,(c0+(vect/2.)),c1,instance,material=mat)
#    if parent is not None : parent.makeParent([obj1,obj2])
#    toggleDisplay(obj1,display=False)
#    toggleDisplay(obj2,display=False)
#    return [obj1,obj2]
#
#def Tube(set,sel,points,faces,scn,armObj,res=32,size=0.25,sc=2.,join=0,
#         instance=None,hiera = 'perRes',bicyl=False,pb=False):
#    sticks=[]
#    bonds, atnobnd = sel.bonds
#    cyl=None
#    mol = bonds[0].atom1.top
#    if instance == None:
#        #create mesh_baseBond
#        baseCyl= Cylinder("baseCyl",radius=1.,length=1.,res=res)
#        toggleDisplay(baseCyl,display=False)
#        cyl = Cylinder("baseBond",radius=1.,length=1.,res=res)
#        toggleDisplay(cyl,display=False)
#        mol.geomContainer.masterGeom.obj.makeParent([cyl,])
#        instance = NMesh.GetRaw("mesh_baseBond")
#    for c in mol.chains:
#        stick=[]
#        bonds, atnobnd = c.residues.atoms.bonds
#        parent = findatmParentHierarchie(bonds[0].atom1,'B',hiera)
#        oneparent=True
#        for i,bond in enumerate(bonds):
#            p = findatmParentHierarchie(bond.atom1,'B',hiera)
#            if p != parent : 
#                cp = p
#                oneparent=False
#            else : cp = None
#            if bicyl :
#                stick.extend(biStick(bond.atom1,bond.atom2,hiera,instance,parent=cp))
#            else :
#                stick.append(oneStick(bond.atom1,bond.atom2,hiera,None,parent=cp))
#            if pb and (i%50) == 0:
#                progress = float(i) / len(bonds)
#                Window.DrawProgressBar(progress, 'creating bonds sticks')
#        if oneparent :
#            parent.makeParent(stick)
#        sticks.extend(stick)
#    return [sticks,cyl]
#    
#def Tubeold(set,sel,points,faces,scn,armObj,res=32,size=0.25,sc=2.,join=0,
#         instance=None,hiera = 'perRes',bicyl=False):
# bonds, atnobnd = set.bonds
# stick=[]
# tube=[]
# size=size*2.
# #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
# #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
# print len(points)
# print len(faces)
# coord1=points[faces[0][0]]
# coord2=points[faces[0][1]]
# atm1=bonds[0].atom1#[faces[0][0]]
# atm2=bonds[0].atom2#[faces[0][1]]
# name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)
# mol=atm1.getParentOfType(Protein)
# laenge,wsz,wz,coord=getStickProperties(points[faces[0][0]],points[faces[0][1]]) 
# me=Mesh.Primitives.Cylinder(res, size, 1.) #1. CAtrace, 0.25 regular |sc=1 CATrace, 2 regular
# mat = Material.Get('sticks')
# me.materials=[mat]
# tube.append(me)
# #OBJ=Object.New('Mesh')
# #fullname = x[0].full_name()
# OBJ=Object.New('Mesh',name)
# stick.append(OBJ)
# stick[0].link(me)
# stick[0].SizeZ = laenge
# stick[0].setLocation(coord[0],coord[1],coord[2])
# stick[0].RotY = wz
# stick[0].RotZ = wsz
# if armObj != None : 
#     mods = stick[0].modifiers
#     mod=mods.append(Modifier.Types.ARMATURE)
#     mod[Modifier.Settings.OBJECT] = armObj
# hierarchy=parseObjectName("B_"+atm1.full_name())
# parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
# addObjectToScene(scn,stick[0],parent=parent)
# #scn.link(stick[0])
# for i in range(1,len(faces)):
#  coord1=points[faces[i][0]]
#  coord2=points[faces[i][1]]
#  atm1=bonds[i].atom1#[faces[i][0]]
#  atm2=bonds[i].atom2#[faces[i][1]]
#  name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)
#  laenge,wsz,wz,coord=getStickProperties(points[faces[i][0]],points[faces[i][1]])
#  me=Mesh.Primitives.Cylinder(res, size, 1.)
#  mat = Material.Get('sticks')
#  me.materials=[mat]
#  tube.append(me)
#  print name
#  #fullname = x[i].full_name()
#  OBJ=Object.New('Mesh',name)
#  #OBJ=Object.New('Mesh')
#  stick.append(OBJ)
#  stick[i].link(me)
#  stick[i].SizeZ = laenge  
#  stick[i].setLocation(coord[0],coord[1],coord[2])
#  stick[i].RotY = wz
#  stick[i].RotZ = wsz
#  if armObj != None : 
#     mods = stick[i].modifiers
#     mod=mods.append(Modifier.Types.ARMATURE)
#     mod[Modifier.Settings.OBJECT] = armObj
#  hierarchy=parseObjectName("B_"+atm1.full_name())
#  parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
#  addObjectToScene(scn,stick[i],parent=parent) 
#  #scn.link(stick[i])
# if join==1 : 
#     stick[0].join(stick[1:])
#     for ind in range(1,len(stick)):
#        #obj[0].join([obj[ind]])
#        scn.unlink(stick[ind])
#    #obj[0].setName(name)
# return stick,tube
#
#AtmRadi = {"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2","P" : "1.04"}
#
#def createBaseTube(quality=0,radius=None):
#    #default the values.
#    #QualitySph={"0":[64,32],"1":[5,5],"2":[10,10],"3":[15,15],"4":[20,20]"5":[25,25]} 
#    segments=quality*5
#    rings=quality*5
#    if quality == 0 : 
#        segments = 25
#        rings = 25
#    iMe={}    
#    for atn in     AtmRadi.keys():
#        if radius==None : radius=AtmRadi[atn]
#        iMe[atn]=Mesh.Primitives.UVsphere(int(segments),int(rings),1)#float(radius)*2.)
#        mat = Material.Get(atn)
#        iMe[atn].materials=[mat]
#        Smatrix=ScaleMatrix(float(radius)*2., 4)
#        iMe[atn].transform(Smatrix)
#        #iMe[atn].smooth()
#        print atn,iMe[atn]
#    return iMe
#
#def updateSphereMesh(geom,quality=0.0,cpkRad=0.0,scale=1.0,radius=None):
#    #compute the scale transformation matrix
#    if not hasattr(geom,'mesh') : return
#    AtmRadi = {"A":1.7,"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2","P" : "1.04"}
#    """segments=quality*5
#    rings=quality*5
#    if quality == 0 : 
#        segments = 25
#        rings = 25"""
#    #names=NMesh.GetNames()
#    if VERBOSE:
#        print "upadteSpheres ",names
#        print geom.mesh
#    for name in geom.mesh.values() : 
#        #if name in names:
#            if VERBOSE: print "UPDATE ",name
#            basemesh =  NMesh.GetRaw("Mbasesphere")
#            mesh=NMesh.GetRaw(name)
#            mesh.verts=basemesh.verts[:]
#            mesh.faces=basemesh.faces[:]
#            factor=float(cpkRad)+float(AtmRadi[name[-1]])*float(scale)
#            #why *2 ?
#            Smatrix=ScaleMatrix(factor*2., 4)
#            mesh.transform(Smatrix)
#            mesh.update()
#
#
#def createBaseSphere(name="",quality=0,radius=None,cpkRad=0.0,scale=1.0,scene=None,parent=""):
#    #AtomElements.keys() ['A', 'C', 'H', 'CA', 'O', 'N', 'P', 'S']
#    AtmRadi = {"A":1.7,"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2","P" : "1.04"}
#    scene = getCurrentScene()
#    #default the values.
#    #QualitySph={"0":[64,32],"1":[5,5],"2":[10,10],"3":[15,15],"4":[20,20]"5":[25,25]} 
#    segments=quality*2
#    rings=quality*5
#    if quality == 0 : 
#        segments = 15#25
#        rings = 15#25
#    iMe={}
#    n=name.split("_")[1] #cpk or balls
#    basesphere=getObject("basesphere")
#    if basesphere is None : 
#        meshsphere=Mesh.Primitives.UVsphere(int(segments),int(rings),1.)
#        meshsphere.name="Mbasesphere"
#        for face in meshsphere.faces: face.smooth=1
#        basesphere=getCurrentScene().objects.new(meshsphere,"basesphere")
#        basesphere.restrictSelect=True
#        toggleDisplay(basesphere,display=False)
#    #radius = CPKradi+AtomRadi*scaleFactor
#    for atn in  AtmRadi.keys():
#        if scene is not None : iObj=[]
#        #print float(cpkRad),float(AtmRadi[atn]),float(scale)
#        rad=float(cpkRad)+float(AtmRadi[atn])*float(scale)
#        #if radius !=None : rad=radius
#        #iMe[atn]=getObject(n+'_mesh_'+atn) #this is the mesh
#        iMe[atn]= NMesh.GetRaw(n+'_mesh_'+atn)
#        if iMe[atn] is None :
#            iMe[atn]=Mesh.Primitives.UVsphere(int(segments),int(rings),1.)#float(rad)*2.)
#            for face in iMe[atn].faces: face.smooth=1
#            mat = Material.Get(atn)
#            iMe[atn].materials=[mat]
#            iMe[atn].name=n+'_mesh_'+atn
#            Smatrix=ScaleMatrix(float(rad)*2., 4)
#            iMe[atn].transform(Smatrix)
#            if scene != None : 
#                iObj.append(scene.objects.new(iMe[atn],n+"_"+atn))
#                toggleDisplay(iObj[-1],display=False)
#    cpk=getObject(name)
#    if scene !=  None and cpk is None : 
#        cpk = newEmpty(name)
#        addObjectToScene(scene,cpk)#, parent=parent)
#        toggleDisplay(cpk,display=False)
#        cpk.makeParent(iObj)
#    return iMe
#
#def updateSphereObj(obj,coord):
#    if VERBOSE : print "upadteObjSpheres"
#    c=coord
#    o=obj#getObject(nameo)
#    #o.setLocation(float(c[0]),float(c[1]),float(c[2]))
#    o.LocX = float(c[0])
#    o.LocY = float(c[1])
#    o.LocZ = float(c[2])
#   
#def updateSphereObjs(g):
#    if not hasattr(g,'obj') : return
#    newcoords=g.getVertices()
#    if VERBOSE : print "upadteObjSpheres"
#    print 'g.obj',g.obj
#    for i,nameo in enumerate(g.obj):
#        c=newcoords[i]
#        print 'name',str(nameo)
#        o=getObject(str(nameo))
#        print 'object',o
#        o.setLocation(float(c[0]),float(c[1]),float(c[2]))
#    
#def findatmParentHierarchie(atm,indice,hiera):
#    if indice == "S" : n='cpk'
#    else : n='balls'
#    mol=atm.getParentOfType(Protein)
#    hierarchy=parseObjectName(indice+"_"+atm.full_name())
#    if hiera == 'perRes' :
#        parent = getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])
#    elif hiera == 'perAtom' :
#        if atm1.name in backbone : 
#            parent = getObject(atm.full_name()+"_bond")
#        else :
#            parent = getObject(atm.full_name()+"_sbond")
#    else :
#        parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_"+n])           
#    return parent
#    
#    
#def instancesAtomsSphere(name,x,iMe,scn,mat=None, scale=1.0,Res=32,R=None,
#                         join=0,geom=None,pb=False):
#    if scn == None :
#        scn=getCurrentScene()
#    objs=[]
#    mol = x[0].getParentOfType(Protein)
#    n='S'
#    if name.find('balls') != (-1) : n='B'
#    if geom is not None : 
#        coords=geom.getVertices()
#    else : 
#        coords = x.coords
#    hiera = 'default'
#    #what about chain...
#    #parent=findatmParentHierarchie(x[0],n,hiera)
#    for c in mol.chains:
#        obj=[]
#        oneparent = True 
#        atoms = c.residues.atoms
#        parent=findatmParentHierarchie(atoms[0],n,hiera)
#        for j in xrange(len(atoms.coords)):
#            at=atoms[j]
#            atN=at.name
#            if atN[0] not in AtomElements.keys() : atN="A"
#            #print atN
#            #fullname = at.full_name()
#            atC=atoms.coords[j]#at._coords[0]
#            #print atC, fullname,at.full_name()
#            mesh=iMe[atN[0]]
#            if type(mesh) == str :
#                mesh=Mesh.Get(mesh)
#            OBJ=scn.objects.new(mesh,n+"_"+at.full_name())
#            #print "obj ",OBJ.name
#            translateObj(OBJ,atC)
#            #OBJ.setLocation(float(atC[0]),float(atC[1]),float(atC[2]))
#            #OBJ=Object.New('Mesh',"S_"+fullname)   
#            OBJ.setMaterials([Material.Get(atN[0])])
#            OBJ.colbits = 1<<0
#            p = findatmParentHierarchie(at,n,hiera)
#            if parent != p : 
#                p.makeParent([OBJ])
#                oneparent = False
#            toggleDisplay(OBJ,False)
#            obj.append(OBJ)
#            if pb and (j%50) == 0:
#                progress = float(j) / len(coords)
#                Window.DrawProgressBar(progress, 'creating '+name+' spheres')
#        if oneparent :
#            parent.makeParent(obj)
#        objs.extend(obj)
#    if join==1 : 
#        obj[0].join(obj[1:])
#        for ind in range(1,len(obj)):
#            scn.unlink(obj[ind])
#        obj[0].setName(name)
#    return  objs
#
#def instancesSphere(name,centers,radii,meshsphere,colors,scene,parent=None):
#    sphs=[]
#    k=0
#    n='S'
#    mat = None
#    if len(colors) == 1:
#        mat = addMaterial('mat_'+name,colors[0])
#    for j in xrange(len(centers)):
#        spname = name+str(j)
#        atC=centers[j]
#        #meshsphere is the object which is link to the mesh
#        mesh=Mesh.Get("mesh_"+meshsphere.getName().split("_")[1])    #"mesh_"+name     OR use shareFrom    
#        #mesh=Mesh.Get(mesh)
#        OBJ=Object.New('Mesh',spname)
#        OBJ.link(mesh)
#        #OBJ=scene.objects.new(mesh,spname)
#        OBJ.setLocation(float(atC[0]),float(atC[1]),float(atC[2]))
#        OBJ.setSize(float(radii[j]),float(radii[j]),float(radii[j]))
#        #OBJ=Object.New('Mesh',"S_"+fullname)   
#        if mat == None : mat = addMaterial("matsp"+str(j),colors[j])
#        OBJ.setMaterials([mat])
#        OBJ.colbits = 1<<0
#        sphs.append(OBJ)
#    AddObject(sphs,parent=parent)
#    return  sphs
#
#def clonesAtomsSphere(name,iMe,x,scn,armObj,scale,Res=32,R=None,join=0):
#    pass
#    
#def AtomMesh(name,typMes,x,scn,armObj,scale,Res=32,R=None,join=0):
# #pr=Group.New(name)
# if scale == 0.0 : scale =1.
# scale = scale *2.
# Rsph=[]
# Robj=[]
# #resGr=[]
# mod=[]
# spher=[]
# obj=[]
# if Res == 0 : Res = 10.
# else : Res = Res *5.
# if typMes == "Mb" : 
#    metab = Blender.Metaball.New()
# k=0
# for j in range(len(x)):
#    at=x[j]
#    atN=at.name
#    fullname = at.full_name()
#    print fullname
#    atC=at._coords[0]
#    if R !=None : rad=R
#    elif AtmRadi.has_key(atN[0]) : rad=AtmRadi[atN[0]]
#    else : rad=AtmRadi['H']
#    if typMes == "Cube" : me=Mesh.Primitives.Cube(float(rad)*scale) #Cylinder(verts, diameter, length)
#    elif typMes == "Sphere" : 
#        print "SPHERE"+str(j)
#        me=Mesh.Primitives.UVsphere(64,int(Res),float(rad)*scale)
#    elif typMes == "Empty2" : 
#        me=Mesh.Primitives.UVsphere(64,int(Res),0.1)
#    elif typMes == "Mb":
#       me=metab.elements.add()
#       me.radius=float(rad)*3     
#    elif typMes == "Empty" : 
#       me = Blender.Object.New('Empty', 'Empty-'+fullname)
#       #me.co = atC[0], atC[1], atC[2]
#       obj.append(me)
#       obj[k].setLocation(float(atC[0]),float(atC[1]),float(atC[2]))      
#       scn.link(obj[k])
#       if armObj != None : 
#             mods = obj[k].modifiers
#             mod=mods.append(Modifier.Types.ARMATURE)
#             mod[Modifier.Settings.OBJECT] = armObj
#    if AtmRadi.has_key(atN[0]) : mat = Material.Get(atN[0])
#    else : mat = Material.Get('H')
#    if typMes == "Mb" : 
#        me.co = Blender.Mathutils.Vector(atC[0], atC[1], atC[2])    
#        me.materials=[mat]
#    elif typMes != "Empty" : 
#        me.materials=[mat]
#    spher.append(me)
#    OBJ=Object.New('Mesh',typMes[0]+"_"+fullname)
#    #resG.objects.link(OBJ)
#    obj.append(OBJ)
#    obj[k].link(spher[k])
#    obj[k].setLocation(float(atC[0]),float(atC[1]),float(atC[2]))   
#    scn.link(obj[k])
#    if armObj != None : 
#        mods = obj[i].modifiers
#        mod=mods.append(Modifier.Types.ARMATURE)
#        mod[Modifier.Settings.OBJECT] = armObj
#    k=k+1
# if typMes == "Mb":
#   ob_mb = scn.objects.new(metab)
#   if armObj != None :
#    modi=ob_mb.modifiers
#    mo=modi.append(Modifier.Types.ARMATURE)
#    mo[Modifier.Settings.OBJECT] = armObj
#    obj=ob_mb
#    #scn.link(bball)
# #join the mesh..
# if typMes != "Mb" and typMes != "Empty"  and join==1 : 
#    print "JOIN"
#    obj[0].join(obj[1:])
#    for ind in range(1,len(obj)):
#        #obj[0].join([obj[ind]])
#        scn.unlink(obj[ind])
#    obj[0].setName(name)
# vdwObj=pybObject(mesh=spher,obj=obj,name=name,atms=x)
# return  vdwObj,obj,spher 
#
#
#def getGeomName(geom):
#    g = geom
#    name = "Pmv_"
#    while g != geom.viewer.rootObject:
#        # g.name can contain whitespaces which we have to get rid of
#        gname = string.split(g.name)
#        ggname = "" 
#        for i in gname:
#            ggname = ggname + i
#            name = name + string.strip(ggname)+"AT"+\
#        string.strip(str(g.instanceMatricesIndex))+ '_'
#        g = g.parent
#        name=string.replace(name,"-","_")
#    return name
#
#def updateLines(lines, chains=None):
#	#lines = getObject(name)	
#	#if lines == None or chains == None:
#	    #print lines,chains	
#	    parent = getObject(chains.full_name())	
#	    #print parent		
#	    bonds, atnobnd = chains.residues.atoms.bonds
#	    indices = map(lambda x: (x.atom1._bndIndex_,
#								x.atom2._bndIndex_), bonds)
#	    updatePoly(lines,vertices=chains.residues.atoms.coords,faces=indices)
#		
#def editLines(molecules,atomSets):
#    for mol, atms, in map(None, molecules, atomSets):
#        #check if line exist
#        for ch in mol.chains:
#            parent = getObject(ch.full_name())
#            lines = getObject(ch.full_name()+'_line')
#            if lines == None :
#                bonds, atnobnd = ch.residues.atoms.bonds
#                indices = map(lambda x: (x.atom1._bndIndex_,
#                                         x.atom2._bndIndex_), bonds)
#
#                lines = createsNmesh(ch.full_name()+'_line',ch.residues.atoms.coords,
#                                     None,indices)
#                addObjectToScene(getCurrentScene(),lines[0]	,parent=parent)
#                mol.geomContainer.geoms[ch.full_name()+'_line'] = lines
#                #addObjToGeom(lines,mol.geomContainer.geoms['lines'])
#            else : #need to update
#                updateLines(lines, chains=ch)
#
#def PointCloudObject(name,**kw):
#    #print "cloud", len(coords)
#    coords=kw['vertices']
#    me=bpy.data.meshes.new(name)
#    me.verts.extend(coords)
#    ob = Blender.Object.New("Mesh",name+"ds")
#    ob.link(me)
#    if kw.has_key('parent') : 
#        addObjectToScene(getCurrentScene(),ob,parent=kw['parent'])
#    return ob
#
#def updateCloudObject(name,coords):
#    #print "updateMesh ",geom,geom.mesh
#    #getDataFrom object or gerNRAW?
#    #mesh=NMesh.GetRaw(geom.mesh)
#    mesh=Mesh.Get(name)
#    #print mesh
#    #mesh=geom.mesh
#    #remove previous vertice and face
#    mats=mesh.materials
#    mesh.verts=None
#    mesh.faces.delete(1,range(len(mesh.faces)))
#    #add the new one
#    mesh.verts.extend(coords)            # add vertices to mesh
#    #set by default the smooth
#    mesh.materials=mats
#    mesh.update()
#
#
#def polygons(name,proxyCol=False,smooth=True,color=None,dejavu=False,
#             material=None, **kw):
#    vertices = kw["vertices"]
#    faces = kw["faces"]
#    if type(faces) not in [types.ListType, types.TupleType]:
#        faces = faces.tolist()
#    normals = kw["normals"]
#    frontPolyMode = 'fill'
#    if kw.has_key("frontPolyMode") : frontPolyMode = kw["frontPolyMode"]
#    shading = 'flat'
#    if kw.has_key("shading") : shading=kw["shading"]#'flat'
#    #vlist = []
#    polygon=bpy.data.meshes.new(name)
#    polygon.verts.extend(vertices)    	# add vertices to mesh
#    polygon.faces.extend(faces)     # add faces to the mesh (also adds edges)
#    #smooth face : the vertex normals are averaged to make this face look smooth
#    polygon.calcNormals()
#    if smooth:
#        for face in polygon.faces:
#            face.smooth=1
#    mat = Material.New("mat"+name[:4])
#    polygon.materials=[mat]
#    if color != None :
#        changeColor(polygon,color)
#    if frontPolyMode == "line" :
#        #drawtype,and mat ->wire
#        mat.setMode("Wire")    
#    if dejavu :
#        obpolygon = Blender.Object.New("Mesh","Mesh_"+name)
#        obpolygon.link(polygon)
#        if frontPolyMode == "line" :
#            obpolygon.setDrawType(2)
#        return obpolygon
#    else :
#        return polygon
#
def createsNmesh(name,vertices,vnormals,faces,color=[[1,0,0],],material=None,smooth=True,proxyCol=False):
    return None,None
#
#def updatePoly(obj,vertices=None,faces=None):
#    mesh=Mesh.Get("Mesh_"+obj.name)
#    mats=mesh.materials
#    mesh.verts=None
#    mesh.faces.delete(1,range(len(mesh.faces)))
#    #add the new one
#    mesh.verts.extend(vertices)            # add vertices to mesh
#    mesh.faces.extend(faces)          # add faces to the mesh (also adds edges)
#    #set by default the smooth
#    for face in mesh.faces: face.smooth=1
#    mesh.calcNormals()
#    mesh.materials=mats
#    mesh.update()
#    #geom.obj.makeDisplayList()
#
def updateMesh(geom,parent=None,proxyCol=None,mol=None):
    pass

#def splitName(name):
#    if name[0] == "T" : #sticks name.. which is "T_"+chname+"_"+Resname+"_"+atomname+"_"+atm2.name\n'
#        tmp=name.split("_")
#        return ["T","",tmp[1],tmp[2][0:3],tmp[2][3:],tmp[3]]
#    else :
#        tmp=name.split(":")
#        indice=tmp[0].split("_")[0]
#        molname=tmp[0].split("_")[1]
#        chainname=tmp[1]
#        residuename=tmp[2][0:3]
#        residuenumber=tmp[2][3:]
#        atomname=tmp[3]
#        return [indice,molname,chainname,residuename,residuenumber,atomname]
#
#def checkChangeStickMaterial(o,**kw):
#    pass
#    
##ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']
#def checkChangeMaterial(o,typeMat,atom=None,parent=None,color=None):
#        #print typeMat
#        #print "checkChangeMaterial"
#        matlist = Material.Get()
#        ss="Helix"
#        if atom != None :
#            res=atom.getParentOfType(Residue)
#            if hasattr(res,'secondarystructure') : ss=res.secondarystructure.name
#        mats=o.getMaterials()
#        if len(mats) == 0 :  matname=""
#        else : matname=mats[0].getName()
#        names=splitName(o.name)
#        changeMaterialSchemColor(typeMat)
#        if typeMat == "" :#material by colorname-> function from rgb give color name...
#            mat = retrieveColorMat(color)
#            if mat == None :  mat = addMaterial("newColor",color)
#            o.setMaterials([mat])
#        elif typeMat == "ByProp" : #color by color
#            if parent != None : requiredMatname = 'mat'+parent#.name #exemple mat_molname_cpk
#            else : requiredMatname = 'mat'+o.getName()#exemple mat_coil1a_molname
#            if typeMat == "ByProp": requiredMatname = 'mat'+o.getName()
#            #print parent.name,o.name,requiredMatname
#            if matname != requiredMatname : 
#                 #print requiredMatname
#                if requiredMatname not in matlist: addMaterial(requiredMatname,color)
#                else : colorMaterial(requiredMatname,color)
#                matlist = Material.Get()
#                if requiredMatname not in matlist: 
#                    mat = addMaterial(requiredMatname,color)
#                    o.setMaterials([mat])
#                else :
#                    o.setMaterials([Material.Get(requiredMatname)])
#            else : colorMaterial(requiredMatname,color)
#        elif typeMat == "ByAtom" :
#                        #changeMaterialSchemColor(typeMat)
#            if matname not in AtmRadi.keys() : #switch to atom materials
#                    o.setMaterials([Material.Get(names[5][0])])
#        elif typeMat =="AtomsU" :
#                        #changeMaterialSchemColor(typeMat)
#                        #if matname not in DavidGoodsell.keys() :
#            o.setMaterials([Material.Get(lookupDGFunc(atom))])
#        elif typeMat == "ByResi" or typeMat == "Residu":
#            if matname not in ResidueSelector.r_keyD.keys() : #switch to residues materials
#                    if names[3] not in ResidueSelector.r_keyD.keys(): names[3]='hetatm'
#                    o.setMaterials([Material.Get(names[3])])
#        elif typeMat == "BySeco" :
#            if matname not in ssk : #switch to ss materials
#                    o.setMaterials([Material.Get(ss[0:4])])
#
#
#def changeColor(geom,colors,perVertex=True,perObjectmat=None,pb=False):
#    #if hasattr(geom,'obj'):obj=geom.obj
#    #else : obj=geom
#    if hasattr(geom,'mesh'):mesh=Mesh.Get(geom.mesh)#NMesh.GetRaw(geom.mesh)#geom.mesh
#    else : mesh=geom    
#    #print mesh
#    mesh.vertexColors = 1  # enable vertex colors
#    #verfify perVertex flag
#    unic=False
#    ncolor=None
#    #print len(colors),len(mesh.verts),len(mesh.faces)
#    if len(colors) != len(mesh.verts) and len(colors) == len(mesh.faces): perVertex=False
#    elif len(colors) == len(mesh.verts) and len(colors) != len(mesh.faces): perVertex=True
#    else :
#        if (len(colors) - len(mesh.verts)) > (len(colors) - len(mesh.faces)) : 
#            perVertex=True
#        else :
#            perVertex=False
#    #print perVertex
#    if len(colors)==1 : 
#        #print colors    
#        unic=True
#        ncolor = colors[0]#blenderColor(colors[0])
#    for k,f in enumerate(mesh.faces):
#        if not unic and not perVertex : 
#            if f.index < len(colors):
#                ncolor = blenderColor(colors[f.index])
#        for i, v in enumerate(f):
#                col= f.col[i]
#                if not unic and perVertex : 
#                    if v.index < len(colors):
#                        ncolor = blenderColor(colors[v.index])
#                else : ncolor = blenderColor(colors[0])
#                col.r= int(ncolor[0])
#                col.g= int(ncolor[1])
#                col.b= int(ncolor[2])
#        if pb and (k%70) == 0:
#            progress = float(k) / (len( mesh.faces ))
#            Window.DrawProgressBar(progress, 'color mesh')
#    mesh.materials[0].setMode("VColPaint")
#    if unic :
#       mat = mesh.materials[0]
#       if perObjectmat != None : mat = perObjectmat.getMaterials()[0]
#       mat.setRGBCol([colors[0][0],colors[0][1],colors[0][2]])
#       #mat.R=ncolor[0]
#       #mat.G=ncolor[1]
#       #mat.B=ncolor[2]
#       #print mat.R,mat.G,mat.B
#    mesh.update()
#
#def changeMaterialSchemColor(typeMat):
#     if typeMat == "ByAtom":
#          for atms in AtomElements.keys() : colorMaterial(atms,AtomElements[atms])
#     elif typeMat == "AtomsU" :
#          for atms in DavidGoodsell.keys() :colorMaterial(atms,DavidGoodsell[atms])
#              #if (atms == "P") or (atms == "A") or (atms == "CA"): colorMaterial(atms[0],AtomElements[atms])
#              #else : 
#              #colorMaterial(atms,DavidGoodsell[atms])
#     elif typeMat == "ByResi":
#          for res in RasmolAmino.keys(): colorMaterial(res,RasmolAmino[res])
#     elif typeMat == "Residu":
#          for res in Shapely.keys(): colorMaterial(res,Shapely[res])
#     elif typeMat == "BySeco":
#          for ss in SecondaryStructureType.keys(): colorMaterial(ss[0:4],SecondaryStructureType[ss])
#     else : pass
#
#def colorMaterial(mat,color):
#    #mat input is a material name or a material object
#    #color input is three rgb value array
#    try :
#        mat = Material.Get(mat)
#        ncolors=color#blenderColor(color)
#        mat.setRGBCol([ncolors[0],ncolors[1],ncolors[2]])
#    except :
#        print "no mat "+mat
#
#def applyMaterial(obj,mat):
#    obj.setMaterials([mat])
#
#def changeObjColorMat(obj,color):
#    mats=obj.getMaterials()
#    if len(mats) == 0 : 
#        mat = retrieveColorMat(color)
#        if mat == None : 
#            mat = addMaterial("newColor",color)
#        obj.setMaterials([mat])
#    else :
#        colorMaterial(mats[0],color)
#    obj.colbits = 1<<0
#    
#def changeSchemColor(schem,keys,colors):
#    #schem is the type of material to change
#    #keys is the names of the material
#    #colors is the new colors
#    #ie atoms [C,N,O],[(255,255,0),(0,255,255),(0,0,255)]
#    for i,name in enumerate(keys) :
#        if schem == "atom":     AtomElements[name] = colors[i]     
#        elif schem == "residu": RasmolAmino[name] = colors[i]
#        elif schem == "ss":     SecondaryStructureType[name] = colors[i]          
#
#def changeVertexStickColor(geom,colors):
#    if hasattr(geom,'mesh'):mesh=geom.mesh
#    else : mesh=geom
#    if not hasattr(mesh,'vertexColors') : mesh=geom.getData(mesh=True)
#    #print mesh,mesh.name
#    mesh.vertexColors = 1  # enable vertex colors
#    unic=False
#    ncolor=None
#    if len(colors)==1 : 
#        #print colors    
#        unic=True
#        ncolor = blenderColor(colors[0])
#    nbV=len(mesh.verts)
#    split=(nbV-2)/2
#    a=range(0,split)
#    b=range(split,(nbV-2))
#    for f in mesh.faces:
#        for i, v in enumerate(f):
#            col= f.col[i]
#            #print col            
#            if not unic : 
#              if v.index in a or v.index == (nbV-2):    ncolor = blenderColor(colors[0])
#              elif     v.index in b or v.index == (nbV-1): ncolor = blenderColor(colors[1])
#            #print "vcol", ncolor
#            col.r= int(ncolor[0])
#            col.g= int(ncolor[1])
#            col.b= int(ncolor[2])
#    mesh.materials[0].setMode("VColPaint")
#    mesh.update()
#    if unic :
#        mesh.materials[0].R=int(ncolor[0])
#        mesh.materials[0].G=int(ncolor[1])
#        mesh.materials[0].B=int(ncolor[2])
#    
#
#def changeSticksColor(obj,colors,type=None,bicyl=False):#1 or 2 colors
#    #can't use the vertex-color for bicylor instance-unicyl
#    if not bicyl :
#        changeVertexStickColor(geom,colors)
#    else :  
#        pass    
#        
#def atomPropToVertices(obj,name,srf,atoms, propName, propIndex=None):#propIndex:surfName
#        """Function called to map atomic properties to the vertices of the
#        geometry"""
#        if len(atoms)==0: return None
#
#        geomC = obj
#        surfName = name
#        surf = srf
#        surfNum = 1
#        # array of colors of all atoms for the msms.
#        prop = []
#        if propIndex is not None:
#            for a in geomC.msmsAtoms.data:
#                d = getattr(a, propName)
#                prop.append( d[surfName] )
#        else:
#            for a in geomC.msmsAtoms.data:
#                prop.append( getattr(a, propName) )
#        # find indices of atoms with surface displayed
#        atomIndices = []
#        indName = '__surfIndex%d__'%surfNum
#        for a in atoms.data:
#            atomIndices.append(getattr(a, indName))
#        # get the indices of closest atoms
#        dum1, vi, dum2 = surf.getTriangles(atomIndices, keepOriginalIndices=1)
#        # get lookup col using closest atom indicies
#        mappedProp = Numeric.take(prop, vi[:, 1]-1).astype('f')
#        if hasattr(obj,'apbs_colors'):
#            colors = []
#            for i in range(len(geom.apbs_dum1)):
#                ch = geom.apbs_dum1[i] == dum1[0]
#                if not 0 in ch:
#                    tmp_prop = mappedProp[0]
#                    mappedProp = mappedProp[1:]
#                    dum1 = dum1[1:]
#                    if    (tmp_prop[0] == [1.5]) \
#                      and (tmp_prop[1] == [1.5]) \
#                      and (tmp_prop[2] == [1.5]):
#                        colors.append(geom.apbs_colors[i][:3])
#                    else:
#                        colors.append(tmp_prop)
#                    if dum1 is None:
#                        break
#            mappedProp = colors            
#        return mappedProp
#
#
#def coarseMolSurface(mv,molFrag,XYZd,isovalue=7.0,resolution=-0.3,padding=0.0,
#                     name='CoarseMolSurface',geom=None):
#    from MolKit.molecule import Atom
#    atoms = molFrag.findType(Atom)
#    coords = atoms.coords
#    radii = atoms.vdwRadius
#    from UTpackages.UTblur import blur
#    import numpy.oldnumeric as Numeric
#    volarr, origin, span = blur.generateBlurmap(coords, radii, XYZd,resolution, padding = 0.0)
#    volarr.shape = (XYZd[0],XYZd[1],XYZd[2])
#    volarr = Numeric.ascontiguousarray(Numeric.transpose(volarr), 'f')
#    #print volarr
#
#    weights =  Numeric.ones(len(radii), typecode = "f")
#    h = {}
#    from Volume.Grid3D import Grid3DF
#    maskGrid = Grid3DF( volarr, origin, span , h)
#    h['amin'], h['amax'],h['amean'],h['arms']= maskGrid.stats()
#    #(self, grid3D, isovalue=None, calculatesignatures=None, verbosity=None)
#    from UTpackages.UTisocontour import isocontour
#    isocontour.setVerboseLevel(0)
#
#    data = maskGrid.data
#
#    origin = Numeric.array(maskGrid.origin).astype('f')
#    stepsize = Numeric.array(maskGrid.stepSize).astype('f')
#    # add 1 dimension for time steps amd 1 for multiple variables
#    if data.dtype.char!=Numeric.Float32:
#        #print 'converting from ', data.dtype.char
#        data = data.astype('f')#Numeric.Float32)
#
#    newgrid3D = Numeric.ascontiguousarray(Numeric.reshape( Numeric.transpose(data),
#                                          (1, 1)+tuple(data.shape) ), data.dtype.char)
#           
#    ndata = isocontour.newDatasetRegFloat3D(newgrid3D, origin, stepsize)
#
# 
#    isoc = isocontour.getContour3d(ndata, 0, 0, isovalue,
#                                       isocontour.NO_COLOR_VARIABLE)
#    vert = Numeric.zeros((isoc.nvert,3)).astype('f')
#    norm = Numeric.zeros((isoc.nvert,3)).astype('f')
#    col = Numeric.zeros((isoc.nvert)).astype('f')
#    tri = Numeric.zeros((isoc.ntri,3)).astype('i')
#    isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)
#    #print vert
#
#    if maskGrid.crystal:
#        vert = maskGrid.crystal.toCartesian(vert)
#    
#    from DejaVu.IndexedGeom import IndexedGeom
#    from DejaVu.IndexedPolygons import IndexedPolygons
#    if geom == None : 
#        g=IndexedPolygons(name=name)
#    else :
#        g = geom
#    #print g
#    inheritMaterial = None
#    g.Set(vertices=vert, faces=tri, materials=None, 
#              tagModified=False, 
#              vnormals=norm, inheritMaterial=inheritMaterial )
#    mv.bindGeomToMolecularFragment(g, atoms, log=0)
#    #print len(g.getVertices())
#    return g
#        #GeometryNode.textureManagement(self, image=image, textureCoordinates=textureCoordinates)
#
#
#def msms(nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
#             perMol=True, display=True,  hdensity=6.0):
#        """Required Arguments:\n        
#        nodes   ---  current selection\n
#        surfName --- name of the surfname which will be used as the key in
#                    mol.geomContainer.msms dictionary.\n
#        \nOptional Arguments:  \n      
#        pRadius  --- probe radius (1.5)\n
#        density  --- triangle density to represent the surface. (1.0)\n
#        perMol   --- when this flag is True a surface is computed for each 
#                    molecule having at least one node in the current selection
#                    else the surface is computed for the current selection.
#                    (True)\n
#        display  --- flag when set to True the displayMSMS will be executed with
#                    the surfName else not.\n
#        hdset    --- Atom set for which high density triangualtion 
#                     will be generated
#        hdensity --- vertex density for high density
#        """
#        from mslib import MSMS
#        if nodes is None or not nodes:
#            return
#        # Check the validity of the input
#        if not type(density) in [types.IntType, types.FloatType] or \
#           density < 0: return 'ERROR'
#        if not type(pRadius) in [types.IntType, types.FloatType] or \
#           pRadius <0: return 'ERROR'
#              
#        # get the set of molecules and the set of atoms per molecule in the
#        # current selection
#        if perMol:
#            molecules = nodes.top.uniq()
#            atmSets = map(lambda x: x.allAtoms, molecules)
#         
#        #else:
#        #    molecules, atmSets = self.vf.getNodesByMolecule(nodes, Atom)
#
#        for mol, atms in map(None, molecules, atmSets):
#            if not surfName:
#                surfName = mol.name + '-MSMS'
#            # update the existing geometry
#        #print mol
#        for a in mol.allAtoms:
#                    a.colors[surfName] = (1.,1.,1.)
#                    a.opacities[surfName] = 1.0
#        i=0  # atom indices are 1-based in msms
#        indName = '__surfIndex%d__'% 1
#        hd = []
#        surf = []
#        atmRadii=[]
#        for a in atms:
#                setattr(a, indName, i)
#                i = i + 1
#                surf.append(1)
#                hd.append(0)
#                atmRadii.append(a.vdwRadius)
#            # build an MSMS object and compute the surface
#        srf = MSMS(coords=atms.coords, radii=atmRadii, surfflags=surf,
#                       hdflags=hd )
#        srf.compute(probe_radius=pRadius, density=density,
#                        hdensity=hdensity)
#        vf, vi, f = srf.getTriangles()
#        vertices=vf[:,:3]
#        vnormals=vf[:,3:6]
#        faces=f[:,:3]
#        ob,mesh=createsNmesh(surfName,vertices,vnormals,faces)
#        surface=Surface(mesh,ob,surfName,mol.allAtoms,srf)
#        return surface
#
#
#
#def prepareMesh2Pmv(mesh,molname=None):
#    #TODO Check triangulation states
#    #print "Dans PrepareMesh"
#    msg='\n'
#    msg+='from DejaVu.IndexedGeom import IndexedGeom\n'
#    msg+='from DejaVu.IndexedPolygons import IndexedPolygons\n'
#    msg+='import numpy.oldnumeric as Numeric\n'
#    msg+='g=IndexedPolygons(name="'+mesh.name+'")\n'
#    msg+='inheritMaterial = None\n'
#    
#    #mesh must be triangulate
#    #print "triangulate"
#    mesh.quadToTriangle()
#    #vertex and vnormal array
#    #print "vertex"
#    vnorm='vnorm=Numeric.array([\n'
#    vert='verts=Numeric.array([\n'
#    for v in mesh.verts :
#        vert+='['+str(v.co[0])+','+str(v.co[1])+','+str(v.co[2])+'],\n'
#        vnorm+='['+str(v.no[0])+','+str(v.no[1])+','+str(v.no[2])+'],\n'
#    vert+='])\n\n'
#    vnorm+='])\n\n'
#    msg+=vert
#    msg+=vnorm    
#    #print vert
#    #print "Face"
#    #faces array
#    faces='faces=Numeric.array([\n'
#    for f in mesh.faces :
#        ind=[]
#        for i, v in enumerate(f):
#            ind.append(v.index)
#            faces+=str(ind)+',\n'
#        faces+='])\n\n'
#    msg+=faces
#   # print faces
#    #set the dejavu geom
#    msg+='print verts\n'
#    msg+='print faces\n'
#    msg+='g.Set(vertices=verts, faces=faces, materials=None, tagModified=False,vnormals=vnorm, inheritMaterial=None)\n'
#    #if a molecule name is provided, call the bindGeomToMol command
#    if molname != None :
#        msg+='molFrag=self.getMolFromName("'+molname+'",log=0)\n'
#        msg+='from MolKit.molecule import Atom\n'
#        msg+='atoms = molFrag.findType(Atom)\n'
#        msg+='self.bindGeomToMolecularFragment(g, atoms, log=0)\n'
#    msg+='self.GUI.VIEWER.AddObject(g)\n'
#    return msg
#
#def recoverObjToGeom(scn,mv):
#    AtmRadi = {"A":1.7,"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2","P" : "1.04"} 
#    for mol in mv.Mols:
#        #just check cpk for now
#        cpk=[]
#        cpkmesh={}    
#        for atn in     AtmRadi.keys():
#            name='mesh_'+atn
#            o=getObject(name)
#            if o == mol.geomContainer.geoms['cpk'].mesh[atn] : print atn
#            else : mol.geomContainer.geoms['cpk'].mesh[atn]=o                    
#        for atm in mol.allAtoms:
#            nameo = "S"+"_"+atm.full_name()
#            cpk.append(getObject(nameo))
#            #print cpk[-1].name
#        for o,c in zip(mol.geomContainer.geoms['cpk'].obj,cpk):
#            if o == c :print "??",o, o.name
#            else : o=c
#
#        #mol.geomContainer.geoms['cpk'].obj=cpk[:]
#        #mol.geomContainer.geoms['cpk'].mesh=cpkmesh
#        
#########################################################################################
#def updateCoordFromObj(mv,sel,display=True,debug=True):
#    #get what is display
#    #get position object and assign coord to atoms...(c4d conformation number...or just use some constraint like avoid collision...but seems that it will be slow)    
#    #print mv.Mols
#    #print mv.molDispl
#    #print "update",sel
#    for s in sel :
#        #print s
#        #print s.getType()
#        #m =  s.getMatrix()
#        #print mat
#        #mat = numpy.array(m)
#        #print mat
#        hi = parseName(s.getName())
#        #print "parsed ",hi
#        molname = hi[0]
#        #chname = hi[1]
#        print "molname",molname
#        if hasattr(mv,'energy'): #ok need to compute energy
#            #first update obj position: need mat_transfo_inv attributes at the mollevel
#            #compute matrix inverse of actual position (should be the receptor...)
#            print "ok energy"
#            rec = mv.energy.current_scorer.mol1
#            lig = mv.energy.current_scorer.mol2
#            print rec.name, lig.name
#            print molname
#            if rec.name == molname or lig.name == molname:
#                print "update"
#                #updateMolAtomCoord(rec)
#                updateMolAtomCoord(lig)
#                get_nrg_score(mv.energy,display=display)
##               if debug :
##                        matx = matrix2c4dMat(mat)
##                        imatx = matrix2c4dMat(rec.mat_transfo_inv)
##                        sr = getObject('sphere_rec')
##                        sr.set_mg(matx)
##                        sl = getObject('sphere_lig')
##                        sl.set_mg(imatx)
#            #update atom coord for dedicated conformation  (add or setConf)
#            #then compute some energie!
#            
#
#def cAD3Energies(mv,mols,atomset1,atomset2,add_Conf=False,debug = False):
#    from mglutil.hostappli import comput_util as C
#    print "prepareSolver"
#    mv.energy = C.EnergyHandler(mv)
#    #mv.energy.add(atomset1,atomset2)#type=c_ad3Score by default
#    mv.energy.add(atomset1,atomset2,type = "ad4Score")
#    if add_Conf:
#        confNum = 1
#        for mol in mols:
#            # check number of conformations available
#            current_confNum = len(mol.allAtoms[0]._coords) -1
#            if  current_confNum < confNum:
#                # we need to add conformation
#                for i in range((confNum - current_confNum)):
#                    mol.allAtoms.addConformation(mol.allAtoms.coords)
#                    # uses the conformation to store the transformed data
#                    #mol.allAtoms.updateCoords(vt,ind=confNum)
#                    # add arconformationIndex to top instance ( molecule)
#                    mol.cconformationIndex = confNum
#    print "done"                
#    if debug :
#        pass
#        """s1=c4d.BaseObject(c4d.Osphere)
#        s1.set_name("sphere_rec")
#        s1[PRIM_SPHERE_RAD]=2.
#        s2=c4d.BaseObject(c4d.Osphere)
#        s2.set_name("sphere_lig")
#        s2[PRIM_SPHERE_RAD]=2.
#        addObjectToScene(getCurrentScene(),s1)
#        addObjectToScene(getCurrentScene(),s2)        
#        #label
#        label = newEmpty("label")
#        label.make_tag(LOOKATCAM)
#        addObjectToScene(getCurrentScene(),label)
#        text1 =  c4d.BaseObject(TEXT)
#        text1.set_name("score")
#        text1[2111] = "score : 0.00"
#        text1[2115] = 5.
#        text1[904,1000] = 3.14
#        text1[903,1001] = 4.
#        text2 =  c4d.BaseObject(TEXT)
#        text2.set_name("el")
#        text2[2111] = "el : 0.00"
#        text2[2115] = 5.0
#        text2[904,1000] = 3.14
#        text3 =  c4d.BaseObject(TEXT)
#        text3.set_name("hb")
#        text3[2111] = "hb : 0.00"
#        text3[2115] = 5.0
#        text3[904,1000] = 3.14
#        text3[903,1001] = -4.
#        text4 =  c4d.BaseObject(TEXT)
#        text4.set_name("vw")
#        text4[2111] = "vw : 0.00"
#        text4[2115] = 5.0
#        text4[904,1000] = 3.14
#        text4[903,1001] = -8.
#        text5 =  c4d.BaseObject(TEXT)
#        text5.set_name("so")
#        text5[2111] = "so : 0.00"
#        text5[2115] = 5.0
#        text5[904,1000] = 3.14
#        text5[903,1001] = -12.
#        addObjectToScene(getCurrentScene(),text1,parent=label)
#        addObjectToScene(getCurrentScene(),text2,parent=label)
#        addObjectToScene(getCurrentScene(),text3,parent=label)
#        addObjectToScene(getCurrentScene(),text4,parent=label)
#        addObjectToScene(getCurrentScene(),text5,parent=label)       
#    #return energy"""
#
#def get_nrg_score(energy,display=True):
#    #print "get_nrg_score"
#    status = energy.compute_energies()
#    #print status
#    if status is None: return
#    #print energy.current_scorer
#    #print energy.current_scorer.score
#    vf = energy.viewer
#    print "score :"+str(energy.current_scorer.score)[0:5]
#    #text = getObject("score")
#    #if text != None :
#    #    text[2111] = "score :"+str(energy.current_scorer.score)[0:5]
#    #    for i,term in enumerate(['el','hb','vw','so']):
#    #        labelT = getObject(term)
#    #        labelT[2111] = term+" : "+str(energy.current_scorer.scores[i])[0:5]
#    #should make multi label for multi terms    
#    # change color of ligand with using scorer energy
#    if display:
#            # change selection level to Atom
#            prev_select_level = vf.getSelLev()
#            vf.setSelectionLevel(Atom,log=0)
#            # 
#            scorer = energy.current_scorer
#            atomSet = vf.expandNodes(scorer.mol2.name).findType(Atom) # we pick the ligand
#            property = scorer.prop
#            if hasattr(atomSet,scorer.prop):
#                mini = min(getattr(atomSet,scorer.prop))
#                #geomsToColor = vf.getAvailableGeoms(scorer.mol2)
#                vf.colorByProperty(atomSet,['cpk'],property,
#                                        mini=-1.0, maxi=1.0,
#                                        colormap='rgb256',log=1)
#                # get the geometries of colormap to be display
#                #if vf.colorMaps.has_key('rgb256'):
#                    #cmg = vf.colorMaps['rgb256']
#                    #from DejaVu.ColormapGui import ColorMapGUI
#                    #if not isinstance(cmg,ColorMapGUI):
#                    #    cmg.read(self.colormap_file)
#                    #    self.vf.showCMGUI(cmap=cmg, topCommand=0)
#                    #    cmg = self.vf.colorMaps['rgb256']
#                    #    cmg.master.withdraw()
#                        # create the color map legend
#                    #    cmg.createCML()
#                        
#                    #cml = cmg.legend
#                    #cml.Set(visible=True,unitsString='kcal/mol')
#                    #if cml not in self.geom_without_pattern:
#                    #    self.geom_without_pattern.append(cml)
#                    
#def updateLigCoord(mol):
#    from mglutil.hostappli import comput_util as C
#    #fake update...reset coord to origin
#    mol.allAtoms.setConformation(0)
#    #get the transformation
#    name = mol.geomContainer.masterGeom.chains_obj[mol.chains[0].name]
#    m = getObject(name).getMatrix()#get_ml()
#    mat = numpy.array(m)
#    #mat,imat = c4dMat2numpy(mx)
#    vt = C.transformedCoordinatesWithMatrice(mol,mat)
#    mol.allAtoms.updateCoords(vt,ind=mol.cconformationIndex)
#    #coords = mol.allAtoms.coords        
#    #mol.allAtoms.updateCoords(coords,ind=mol.cconformationIndex)
#    mol.allAtoms.setConformation(0)
#
#def updateMolAtomCoord(mol):
#    #just need that cpk or the balls have been computed once..
#    #balls and cpk should be linked to have always same position
#    # let balls be dependant on cpk => contraints? or update
#    # the idea : spline/dynamic move link to cpl whihc control balls
#    # this should be the actual coordinate of the ligand
#    # what about the rc...
#    print "update", mol.name
#    vt = []
#    sph = mol.geomContainer.geoms['cpk'].obj
#    print len(sph),sph[0],getObject(sph[0]).getLocation("worldspace")
#    for name in sph:
#        o = getObject(name)
#        pos=o.getLocation("worldspace")#get_mg().off
#        vt.append([pos[0],pos[1],pos[2]])
#    mol.allAtoms.updateCoords(vt,ind=mol.cconformationIndex)
#                
#######ANIMATION FUNCTION########################
#def insertKeys(geoms,step=5):
#  curFrame=getCurrentScene().getRenderingContext().currentFrame()#Blender.Get('curframe')
#  for geom in geoms:
#    if not hasattr(geom,'obj'):return
#    obj=geom.obj
#    #print "#######################",curFrame
#    if type(obj) == list or type(obj) == tuple:
#        for o in obj:
#            if type(o) == str : o=getObject(o)
#            o.insertIpoKey(Blender.Object.LOCROT)
#    else :
#        if type(o) == str : o=getObject(o)
#        o.insertIpoKey(Blender.Object.LOCROT)
#  getCurrentScene().getRenderingContext().currentFrame(curFrame+step)
#
#
##############################AR METHODS#######################################
def ARstep(mv,concat=False,local=False):
    from mglutil.math import rotax
    #from Pmv.hostappInterface import comput_util as C
    mv.art.beforeRedraw()
    #up(self,dialog)
    for arcontext in mv.art.arcontext :
        for pat in arcontext.patterns.values():
            if pat.isdetected:
                #print pat
                geoms_2_display = pat.geoms
                if concat : 
                    m = pat.moveMat[:]
                    newMat=rotax.interpolate3DTransform([m.reshape(4,4)], [1], 
                                                            mv.art.scaleDevice)
                else :
#                    m = pat.moveMat[:]
#                    newMat=rotax.interpolate3DTransform([m.reshape(4,4)], [1], 
#                                                            mv.art.scaleDevice)                    
                    newMat= pat.mat_transfo[:]
#                    newMat[3,0:3] = pat.mat_transfo[12:15]
                #print transfo_mat[12:15]
                for geom in geoms_2_display :
                    mat = newMat.reshape(4,4)
                    if hasattr(geom,'mol') :
                        model = geom.mol.ch_model
                    elif hasattr(geom,'ch_vol'):
                        model = geom.ch_vol
                    elif hasattr(geom,'obj'):
                        model = geom.obj                       
                    else :
                        continue
#                    else :#geom == 'volume'
#                        #model = helper.getObject(id=0)
#                        from VolumeViewer import active_volume
#                        model = active_volume()
                    if concat : 
                        concatObjectMatrix(model,mat,local=local)
                    else :
                        setObjectMatrix(model,mat)
                        
    mv.art.afterRedraw()
#tracker = chimera.TrackChange.get()
#tracker.addModifier(model,MyReason)
def ARloop(mv,v=None,emdiag=None,ar=True,concat=False,local=False,max=1000):#,im=None,ims=None,max=1000):
    count = 0	
    while count < max:
        #print count
        if v is not None:
            #updateBmp(mv,bmp,scale=None,show=False,viewport=v)
            updateImage(mv,v)
        if ar : 
            ARstep(mv,concat=concat,local=local)
        if emdiag is not None:
            emdiag.realtime_cb()
            emdiag.update_metric_cb()            
        update()
        count = count + 1

def AR(mv,v=None,emdiag=None,ar=True,concat=False,local=False):#,im=None,ims=None,max=1000):
    count = 0	
    while 1:
        #print count
        if v is not None:
            #updateBmp(mv,bmp,scale=None,show=False,viewport=v)
            updateImage(mv,v)
        if ar : 
            ARstep(mv,concat=concat,local=local)
        if emdiag is not None:
            emdiag.realtime_cb()
            emdiag.update_metric_cb()            
        update()
        count = count + 1

def updateImage(mv,dialog,order=[3, 3, 1, 2]):#[1, 2, 3, 1]
    import Image
    cam = mv.art.arcontext[0].cam
    cam.lock.acquire()
    im = Image.fromstring('RGBA',(mv.art.video.width,mv.art.video.height),
                          cam.im_array.tostring())
    rgba = im.split()
    new = Image.merge("RGBA", (rgba[order[0]],rgba[order[1]],rgba[order[2]],rgba[order[3]]))
    #can maybe modify the video...
    im = new.resize((320,240),Image.BILINEAR)
    dialog.keyModel.Set(image=im)
    cam.lock.release()

def update():
    import chimera
    chimera.viewer.displayCB(None)
    chimera.update.checkForChanges()

