#!/usr/bin/python
#TODO
#instanciat object from instanceMatricesFortran
#symserv == cloner Object linear for helix, radial for symNFold
#how comunicate this woth pmv....like vision ... only need ever node name/log or matrice

#C4d module
import c4d
#import c4d.documents
#import c4d.plugins
#from c4d import plugins
#from c4d import tools
#from c4d.gui import *
#from c4d.plugins import *

#standardmodule
import numpy
import numpy.oldnumeric as Numeric
import sys, os, os.path, struct, math, string
import types
from math import *
from types import StringType, ListType


#TAG ID
POSEMIXER = 100001736
IK = 1019561
PYTAG = 1022749
Follow_PATH = 5699
LOOKATCAM = 1001001

#OBJECT ID
INSTANCE = 5126
BONE = 1019362
CYLINDER = 5170
CIRCLE = 5181
RECTANGLE = 5186
FOURSIDE = 5180
LOFTNURBS= 5107
TEXT = 5178
CLONER = 1018544
MOINSTANCE = 1018957
ATOMARRAY = 1001002


#PARAMS ID
PRIM_SPHERE_RAD = 1110

#MATERIAL ATTRIB
LAYER=1011123
GRADIANT=1011100

VERBOSE=0
DEBUG=1

#MGLTOOLS module
import MolKit
from MolKit.molecule import Atom, AtomSet, BondSet, Molecule , MoleculeSet
from MolKit.protein import Protein, ProteinSet, Residue, Chain, ResidueSet,ResidueSetSelector
from MolKit.stringSelector import CompoundStringSelector
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom
from MolKit.protein import Residue

#PMV module
from Pmv.moleculeViewer import MoleculeViewer
from Pmv.displayCommands import BindGeomToMolecularFragment
from Pmv.trajectoryCommands import PlayTrajectoryCommand
#Pmv Color Palette
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import DavidGoodsell, DavidGoodsellSortedKeys
from Pmv.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
from Pmv.pmvPalettes import Shapely
from Pmv.pmvPalettes import SecondaryStructureType

#computation
#from Pmv.amberCommands import Amber94Config, CurrentAmber94

from Pmv.hostappInterface import cinema4d as epmvc4d
plugDir=epmvc4d.__path__[0]


SSShapes={  'Heli':FOURSIDE,
           'Shee':RECTANGLE,
           'Coil':CIRCLE,
           'Turn':CIRCLE,
           'Stra':RECTANGLE
}

SSColor={ 'Heli':(238,0,127),
           'Shee':(243,241,14),
           'Coil':(255,255,255),
           'Turn':(60,26,100),
           'Stra':(255,255,0)}
#NOTES
#[900] <-> set_name
AtmRadi = {"A":"1.7","N":"1.54","C":"1.7","CA":"1.7","O":"1.52","S":"1.85","H":"1.2","P" : "1.04"}

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
            if atom.atomId not in AtmRadi.keys() : atom.atomId="A"
        return atom.atomId


ResidueSelector=ResidueSetSelector()

def start(debug=0):
    if VERBOSE : print "start ePMV - debug ",debug
    mv = MoleculeViewer(logMode = 'unique', customizer=None, master=None,title='pmv', withShell= 0,verbose=False, gui = False)
    mv.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
    mv.browseCommands('trajectoryCommands',commands=['openTrajectory'],log=0,package='Pmv')
    #mv.browseCommands('amberCommands',package='Pmv')
    mv.addCommand(PlayTrajectoryCommand(),'playTrajectory',None)
    mv.embedInto('c4d',debug=debug)
    mv.userpref['Read molecules as']['value']='conformations'
    DEBUG=debug	
    return mv

def reset_ePMV(mv, debug=0):
    #need to restore the logEvent sytem for the right session
    if VERBOSE : print "reset epmv debug",debug,mv
    mv.embedInto('c4d',debug=debug)


def compareSel(currentSel,molSelDic):
    for selname in molSelDic.keys():
        if VERBOSE : print "The compareSelection   ",currentSel,molSelDic[selname][3]
        #if currentSel[-1] == ';' : currentSel=currentSel[0:-1]
        if currentSel == molSelDic[selname] : return selname

def parseObjectName(o):
    if type(o) == str : name=o
    else : name=o.get_name()
    tmp=name.split("_")
    if len(tmp) == 1 : #no "_" so not cpk (S_) or ball (B_) stick (T_) or Mesh (Mesh_)
        return ""
    else :
        if tmp[0] == "S" or tmp[0] == "B" : #balls or cpk
            hiearchy=tmp[1].split(":") #B_MOL:CHAIN:RESIDUE:ATOMS        
            return hiearchy
    return ""

def parseName(o):
    if type(o) == str : name=o
    else : name=o.get_name()
    tmp=name.split("_")
    if len(tmp) == 1 : #molname
        hiearchy=name.split(":")
        if len(hiearchy) == 1 : return [name,""]
        else : return hiearchy
    else :
        hiearchy=tmp[1].split(":") #B_MOL:CHAIN:RESIDUE:ATOMS        
        return hiearchy

def get_editor_object_camera(doc):
    bd = doc.get_render_basedraw()
    cp = bd.get_scene_camera(doc)
    if cp is None: cp = bd.get_editor_camera()
    return cp

def getCurrentScene():
    return c4d.documents.get_active_document()

def update():
    getCurrentScene().message(c4d.MULTIMSG_UP)    
    #c4d.draw_views(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)
    c4d.draw_views(c4d.DA_NO_THREAD|c4d.DA_FORCEFULLREDRAW)
	
def getObjectName(o):
    return o.get_name()

def getObject(name):
    obj=None
    if type(name) != str : return name
    try :
        obj=getCurrentScene().find_object(name)
    except : 
        obj=None
    return obj

def newEmpty(name,location=None,parentCenter=None,display=0,visible=0):
    empty=c4d.BaseObject(c4d.Onull)
    empty.set_name(name)
    empty[1000] = display
    empty[1001] = 1.0
    if location != None :
        if parentCenter != None : 
            location = location - parentCenter
        empty.set_pos(c4d.Vector(float(location[2]),float(location[1]),float(location[0])))        
    return empty

def newInstance(name,object,location=None,c4dmatrice=None,matrice=None):
    instance = c4d.BaseObject(INSTANCE)
    instance[1001]=iMe[atN[0]]        
    instance.set_name(n+"_"+fullname)#.replace(":","_")
    if location != None :
        instance.set_pos(c4d.Vector(float(location[2]),float(location[1]),float(location[0])))
    if c4dmatrice !=None :
        #type of matre
        instance.set_mg(c4dmatrice)
    if matrice != None:
        mx = matrix2c4dMat(matrice)
        instance.set_mg(mx)
    return instance


def getPosUntilRoot(obj):
    stop = False
    parent = obj.get_up()
    pos=c4d.Vector(0.,0.,0.)
    while not stop :
        pos = pos + parent.get_pos()
        parent = parent.get_up()
        if parent is None :
            stop = True
    return pos                                            
    
def addObjectToScene(doc,obj,parent=None,centerRoot=True,rePos=None):
    #doc.start_undo()
    if parent != None : 
        if type(parent) == str : parent = getObject(parent)
        doc.insert_object(op=obj,parent=parent)
        if centerRoot :
            currentPos = obj.get_pos()         
            if rePos != None : 
                parentPos = c4d.Vector(float(rePos[2]),float(rePos[1]),float(rePos[0]))          
            else :
                parentPos = getPosUntilRoot(obj)#parent.get_pos()                            
            obj.set_pos(currentPos-parentPos)                
    else :    doc.insert_object(op=obj)
    #add undo support
    #doc.add_undo(c4d.UNDO_NEW, obj)    
    #doc.end_undo()
    
def AddObject(obj,parent=None,centerRoot=True,rePos=None):
    doc = getCurrentScene()
    #doc.start_undo()
    if parent != None : 
        if type(parent) == str : parent = getObject(parent)
        doc.insert_object(op=obj,parent=parent)
        if centerRoot :
            currentPos = obj.get_pos()         
            if rePos != None : 
                parentPos = c4d.Vector(float(rePos[2]),float(rePos[1]),float(rePos[0]))          
            else :
                parentPos = getPosUntilRoot(obj)#parent.get_pos()                            
            obj.set_pos(currentPos-parentPos)                
    else :    doc.insert_object(op=obj)
    #add undo support
    #doc.add_undo(c4d.UNDO_NEW, obj)    
    #doc.end_undo()
    
def addObjToGeom(obj,geom):
    if type(obj) == list or type(obj) == tuple:
        if len(obj) > 2: geom.obj=obj        
        elif len(obj) == 1: geom.obj=obj[0]
        elif len(obj) == 2:    
            geom.mesh=obj[1]
            geom.obj=obj[0]
    else : geom.obj=obj


def makeHierarchy(listObj,listName, makeTagIK=False):
    for i,name in enumerate(listName) :
        o = getObject(listObj[name])
        if makeTagIK :
            o.make_tag(IK)
        if i < len(listObj)-1 :
            child = getObject(listObj[listName[i+1]]) 
            child.insert_under(o)

def addIKTag(object):
    object.make_tag(IK)

def makeAtomHierarchy(res,parent,useIK=False):
    doc = getCurrentScene()
    backbone = res.backbone()
    sidechain = res.sidechain()                
    for i,atm in enumerate(backbone):
        rePos = None
        prev_atom = None        
        at_center =     atm.coords
        at_obj = newEmpty(atm.full_name(),location=at_center)
        bond_obj = newEmpty(atm.full_name()+"_bond")                                    
        if useIK :
            addIKTag(at_obj)
            addIKTag(bond_obj)            
        if i > 0 : prev_atom = backbone[i-1]        
        if prev_atom != None:
            if VERBOSE : print "hierarchy backbone ",atm.name, prev_atom.name
            rePos = prev_atom.coords
            oparent = getObject(prev_atom.full_name()+"_bond")
            if VERBOSE : print oparent.get_name()            
            addObjectToScene(doc,at_obj,parent=oparent,centerRoot=True,rePos=rePos)                                     
        else :
            if VERBOSE : print "first atom", atm.name
            addObjectToScene(doc,at_obj,parent=parent,centerRoot=True,rePos=rePos)
        addObjectToScene(doc,bond_obj,parent=at_obj,centerRoot=False)
        if atm.name == 'CA' :
            #add the sidechain child of CA
            side_obj = newEmpty(atm.full_name()+"_sidechain")
            addObjectToScene(doc,side_obj,parent=at_obj,centerRoot=False)                            
            for j,satm in enumerate(sidechain):
                sat_center = satm.coords
                sat_obj = newEmpty(satm.full_name(),location=sat_center)
                sbond_obj = newEmpty(satm.full_name()+"_sbond")
                addObjectToScene(doc,sat_obj,parent=side_obj,centerRoot=True,rePos=at_center)
                addObjectToScene(doc,sbond_obj,parent=side_obj,centerRoot=False)
    if useIK : 
        return bond_obj
    else :
        return parent    

def makeResHierarchy(res,parent,useIK=False):
    sc = getCurrentScene()
    res_center = res.atoms.get("CA").coords[0]#or averagePosition of the residues?
    res_obj = newEmpty(res.full_name(),location=res_center)
    bond_obj = newEmpty(res.full_name()+"_bond")
    rePos = None
    prev_res = res.getPrevious()
    if useIK :
        addIKTag(res_obj)
    if prev_res != None and useIK :
        rePos = prev_res.atoms.get("CA").coords[0]
        oparent = getObject(prev_res.full_name())            
        addObjectToScene(sc,res_obj,parent=oparent,centerRoot=True,rePos=rePos)
    else :
        addObjectToScene(sc,res_obj,parent=parent,centerRoot=True,rePos=rePos)
        addObjectToScene(sc,bond_obj,parent=res_obj,centerRoot=False)
    #mol.geomContainer.masterGeom.res_obj[res.name]=util.getObjectName(res_obj)
    return res_obj
    
def addCameraToScene(name,Type,focal,center,sc):
    pass
    """
    cam = Blender.Camera.New(Type,name)
    cam.setScale(focal*2.)
    obc = sc.objects.new(cam) # make a new object in this scene using the camera data\n'
    obc.setLocation (center[0],center[1],center[2])
    obc.RotZ=2*math.pi
    sc.objects.camera = obc
    """

def addLampToScene(name,Type,rgb,dist,energy,soft,shadow,center,sc):
    pass
    """
    lampe=Lamp.New(Type,name)
    lampe.R=rgb[0]
    lampe.G=rgb[1]
    lampe.B=rgb[2]
    lampe.setDist(dist)
    lampe.setEnergy(energy)
    lampe.setSoftness(soft)
    if shadow : lampe.setMode("Shadows")
    objet = sc.objects.new(lampe)
    objet.loc=(center[0],center[1],center[2])
    """

def setInstance(name,object,location=None,c4dmatrice=None,matrice=None):
    instance = c4d.BaseObject(INSTANCE)
    instance[1001]=object        
    instance.set_name(name)#.replace(":","_")
    if location != None :
        instance.set_pos(c4d.Vector(float(location[2]),float(location[1]),float(location[0])))
    if c4dmatrice !=None :
        #type of matre
        instance.set_mg(c4dmatrice)
    if matrice != None:
        mx = matrix2c4dMat(matrice)
        instance.set_ml(mx)
        p = instance.get_pos()
        instance.set_pos(c4d.Vector(p.y,p.z,p.x))
    return instance

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
      
def dist(A,B):
  return Numeric.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2+(A[2]-B[2])**2)
  
def norm(A):
    """Return vector norm"""
    return sqrt(sum(A*A))
def normsq(A):
    """Return square of vector norm"""
    return abs(sum(A*A))
def normalize(A):
    """Normalize the Vector"""
    if (norm(A)==0.0) : return A
    else :return A/norm(A)

def getCenter(coords):
    """sets self.center<-getCenter(self)"""
    coords = Numeric.array(coords)#self.allAtoms.coords
    center = sum(coords)/(len(coords)*1.0)
    center = list(center)
    for i in range(3):
        center[i] = round(center[i], 4)
    #print "center =", self.center
    return center
    
class pybObject():
    def __init__(self,obj,name,atms ):
        self.b_obj=obj
        self.name=name
        self.Atoms=atms
        
class Surface(pybObject):
    def __init__(self,obj,name,atms,srf ):
        pybObject.__init__(self, obj=obj,name=name,atms=atms)
        self.msmsAtoms=atms
        self.msmsSurf=srf
def toggleDisplay(obj,display):
    if display : obj.set_editor_mode(c4d.MODE_ON)
    else :     obj.set_editor_mode(c4d.MODE_OFF)            
    if display : obj.set_render_mode(c4d.MODE_ON)
    else :     obj.set_render_mode(c4d.MODE_OFF)            
    if display : obj[906]=1
    else :     obj[906]=0            

def findatmParentHierarchie(atm,indice,hiera):
    if indice == "S" : n='cpk'
    else : n='balls'
    mol=atm.getParentOfType(Protein)
    hierarchy=parseObjectName(indice+"_"+atm.full_name())
    if hiera == 'perRes' :
        parent = getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])
    elif hiera == 'perAtom' :
        if atm1.name in backbone : 
            parent = getObject(atm.full_name()+"_bond")
        else :
            parent = getObject(atm.full_name()+"_sbond")
    else :
        parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_"+n])           
    return parent

#####################MATERIALS FUNCTION########################
def addMaterial(name,color):
      import c4d
      import c4d.documents
      doc = c4d.documents.get_active_document()
      # create standard material
      __mat = doc.find_material(name)
      if VERBOSE : print name,color	  
      if __mat != None :
          return __mat	  		
      else :
          __mat = c4d.BaseMaterial(c4d.Mmaterial)
          # set the default color
          __mat[2100] = c4d.Vector(float(color[0]),float(color[1]),float(color[2]))
          __mat[900] = name
          # insert the material into the current document
          doc.insert_material(op=__mat)
          return __mat

def createDejaVuColorMat():
    Mat=[]
    from DejaVu.colors import *
    for col in cnames:
        Mat.append(addMaterial(col,eval(col)))
    return Mat

def retrieveColorMat(color):
    doc = c4d.documents.get_active_document()
    from DejaVu.colors import *
    for col in cnames:
        if color ==	eval(col) :
            return doc.find_material(col)		
    return None
			
def create_layers_material(name):
      import c4d
      import c4d.documents
      # create standard material
      __mat = c4d.BaseMaterial(c4d.Mmaterial)
      __mat[2100] = c4d.Vector(0.,0.,0.)
      __mat[900] = name
      __mat[8000]= c4d.BaseList2D(LAYER)

	             
def create_loft_material(doc=None,name='loft'):
      import c4d
      import c4d.documents
      if doc == None : doc= c4d.documents.get_active_document()
      #c4d.call_command(300000109,110)
      GradMat=doc.find_material('loft')
      if GradMat == None :
         #c4d.documents.load_file(plugDir+'/LoftGradientMaterial1.c4d')
         bd=c4d.documents.merge_document(doc,plugDir+'/LoftGradientMaterial1.c4d',loadflags=c4d.SCENEFILTER_MATERIALS|c4d.SCENEFILTER_MERGESCENE)   
         GradMat=doc.find_material('loft')
         #c4d.call_command(300000109,110)-> preset material n110 in the demo version
      #GradMat                          
      GradMat[2004]=0#refletion turn off
      GradMat[2003]=0#refletion turn off      
      GradMat[8000][1001]=2001 #type 2d-V
      mat=GradMat.get_clone()
      mat[900]=name
      grad=mat[8000][1007]
      grad.delete_all_knots()
      mat[8000][1007]=grad
      doc.insert_material(op=mat)                      
      return mat 

def create_sticks_materials(doc=None):
      import c4d
      import c4d.documents
      sticks_materials={}
      if doc == None : doc= c4d.documents.get_active_document()
      #c4d.call_command(300000109,110)
      GradMat=doc.find_material('loft')#'loft'
      if GradMat == None :
         #c4d.documents.load_file(plugDir+'/LoftGradientMaterial1.c4d')
         bd=c4d.documents.merge_document(doc,plugDir+'/LoftGradientMaterial1.c4d',loadflags=c4d.SCENEFILTER_MATERIALS|c4d.SCENEFILTER_MERGESCENE)   
         GradMat=doc.find_material('loft')
      GradMat[2004]=0#refletion turn off
      GradMat[2003]=0#refletion turn off      
      GradMat[8000][1001]=2001 #type 2d-V
      # create standard material
      i=0
      j=0
      atms=AtmRadi.keys()
      for i in range(len(atms)):
         for j in range(len(atms)):
           if (atms[i][0]+atms[j][0]) not in sticks_materials.keys():    
              mat=doc.find_material(atms[i][0]+atms[j][0])
              if mat == None :
                  mat=GradMat.get_clone()
                  mat[900]=atms[i][0]+atms[j][0]
                  doc.insert_material(op=mat)
              sticks_materials[atms[i][0]+atms[j][0]]=mat                                        
      return sticks_materials 
#material prset 57,70...110 is a gradient thus should be able to get it, and copy it t=c4d.call_command(300000109,110)

def create_SS_materials(doc=None):
      import c4d
      import c4d.documents
      SS_materials={}
      if doc == None : doc= c4d.documents.get_active_document()
      # create standard material
      for i,ss in enumerate(SecondaryStructureType.keys()):
           mat=doc.find_material(ss[0:4])
           if mat == None :
               mat=c4d.BaseMaterial(c4d.Mmaterial)
               colorMaterial(mat,SecondaryStructureType[ss])
               mat[900] = ss[0:4]
               doc.insert_material(op=mat)
           SS_materials[ss[0:4]]=mat                      
      return SS_materials 

def create_Residus_materials(doc=None):
      import c4d
      import c4d.documents
      import random
      Residus_materials={}
      if doc == None : doc= c4d.documents.get_active_document()
      # create standard material
      for i,res in enumerate(ResidueSelector.r_keyD.keys()):
           random.seed(i)
           mat=doc.find_material(res)
           if mat == None :
               mat=c4d.BaseMaterial(c4d.Mmaterial)
               mat[2100] = c4d.Vector(random.random(),random.random(),random.random())
               mat[900] = res
               doc.insert_material(op=mat)       
           Residus_materials[res]=mat
      mat=doc.find_material("hetatm")
      if mat == None :
          mat=c4d.BaseMaterial(c4d.Mmaterial)
          mat[2100] = c4d.Vector(random.random(),random.random(),random.random())
          mat[900] = "hetatm"
          doc.insert_material(op=mat)
      Residus_materials["hetatm"]=mat
      return Residus_materials 

def create_Atoms_materials(doc=None):
      import c4d
      import c4d.documents
      Atoms_materials={}
      if doc == None : doc= c4d.documents.get_active_document()
      for i,atms in enumerate(AtomElements.keys()):
           mat=doc.find_material(atms)
           if mat == None :
               mat=c4d.BaseMaterial(c4d.Mmaterial)
               col=(AtomElements[atms])
               mat[2100] = c4d.Vector(col[0],col[1],col[2])
               mat[900] = atms
               doc.insert_material(op=mat)
           Atoms_materials[atms]=mat
      for i,atms in enumerate(DavidGoodsell.keys()):
           mat=doc.find_material(atms)
           if mat == None :
               mat=c4d.BaseMaterial(c4d.Mmaterial)
               col=(DavidGoodsell[atms])
               mat[2100] = c4d.Vector(col[0],col[1],col[2])
               mat[900] = atms
               doc.insert_material(op=mat)
           Atoms_materials[atms]=mat
      return Atoms_materials

#Material={}
#Material["atoms"]=create_Atoms_materials()
#Material["residus"]=create_Atoms_materials()
#Material["ss"]=create_Atoms_materials()

def getMaterials():
   Material={}
   Material["atoms"]=create_Atoms_materials()
   Material["residus"]=create_Residus_materials()
   Material["ss"]=create_SS_materials()
   Material["sticks"]=create_sticks_materials()
   #Material["loft"]=create_loft_material()
   return Material   

def getMaterialListe():
   Material=getMaterials()
   matlist=[]
   matlist.extend(Material["atoms"].keys())
   matlist.extend(Material["residus"].keys())
   matlist.extend(Material["ss"].keys())
   matlist.extend(Material["sticks"].keys())            
   return matlist
   
def computeRadius(protein,center=None):
        if center == None : center = protein.getCenter()
        rs = 0.
        for atom in protein.allAtoms:    
            r = dist(center,atom._coords[0])
            if r > rs:
                rs = r
        return rs


def makeLabels(mol,selection,):
    pass
    #self.labelByProperty("1CRN:A:CYS3", textcolor='white', log=0, format=None,
    #                      only=False, location='Center', negate=False, 
    #font='arial1.glf', properties=['name'])
    

def updateRTSpline(spline,selectedPoint,distance = 2.0,DistanceBumping = 1.85):
    #from Graham code 
    #print "before loop"
    nb_points = spline.get_point_count()
    for j in xrange(selectedPoint,nb_points-1):
        leaderB = spline.get_point(j)
        myPos = spline.get_point(j+1)      
        deltaB = myPos-leaderB
        newPosB = leaderB + deltaB*distance/deltaB.len()
        newPosA = c4d.Vector(0.,0.,0.)
        k = j        
        while k >=0 :
            leaderA = spline.get_point(k)
            deltaA = myPos-leaderA;
            if ( deltaA.len() <= DistanceBumping and deltaA.len() >0):
                        newPosA = ((DistanceBumping-deltaA.len())*deltaA/deltaA.len());
            newPos = newPosB + newPosA
            spline.set_point(j+1,newPos)
            k=k-1
    jC = selectedPoint;
    while jC >0 :
        leaderBC = spline.get_point(jC);
        myPosC = spline.get_point(jC-1);              
        deltaC = myPosC-leaderBC;
        newPosBC = leaderBC + deltaC*distance/deltaC.len();
        newPosAC = c4d.Vector(0.,0.0,0.)
        k = jC
        while k < nb_points :
            leaderAC = spline.get_point(k)
            deltaAC = myPosC-leaderAC;
            if ( deltaAC.len() <= DistanceBumping and deltaAC.len() >0.):
                        newPosAC = ((DistanceBumping-deltaAC.len())*deltaAC/deltaAC.len());
            newPosC = newPosBC + newPosAC
            spline.set_point(jC-1,newPosC)
            k=k+1
        jC=jC-1

def updateCoordFromObj(mv,sel,debug=True):
    #get what is display
    #get position object and assign coord to atoms...(c4d conformation number...or just use some constraint like avoid collision...but seems that it will be slow)    
    #print mv.Mols
    #print mv.molDispl
    for s in sel :
        #print s.get_name()
        if s.get_type() == c4d.Ospline :
            #print "ok Spline"
            select = s.get_selected_points()#mode=P_BASESELECT)#GetPointSelection();
            #print nb_points
            selected = select.get_all(s.get_point_count()) # 0 uns | 1 selected
            #print selected
            #assume one point selected ?
            selectedPoint = selected.index(1)           
            updateRTSpline(s,selectedPoint)
        elif  s.get_type() == c4d.Onull :
            #print "ok null" 
            #molname or molname:chainname or molname:chain_ss ...
            hi = parseName(s.get_name())
            #print "parsed ",hi
            molname = hi[0]
            chname = hi[1]
            #mg = s.get_mg()
            #should work with chain level and local matrix
            #mg = ml = s.get_ml()
            #print molname
            #print mg
            #print ml
            if hasattr(mv,'energy'): #ok need to compute energy
                #first update obj position: need mat_transfo_inv attributes at the mollevel
                #compute matrix inverse of actual position (should be the receptor...)
                if hasattr(mv.energy,'amber'): 
                #first update obj position: need mat_transfo_inv attributes at the mollevel
                    mol = mv.energy.mol
                    if mol.name == molname :
                        if mv.minimize == True:								
                            amb = mv.Amber94Config[mv.energy.name][0]			
                            updateMolAtomCoord(mol,index=mol.cconformationIndex)
                            #mol.allAtoms.setConformation(mol.cconformationIndex)
                            #from Pmv import amberCommands
                            #amberCommands.Amber94Config = {}
                            #amberCommands.CurrentAmber94 = {}
							#amb_ins = Amber94(atoms, prmfile=filename)
                            mv.setup_Amber94(mol.name+":",mv.energy.name,mol.prname,indice=mol.cconformationIndex)
                            mv.minimize_Amber94(mv.energy.name, dfpred=10.0, callback_freq='10', callback=1, drms=1e-06, maxIter=100., log=0)
                            #mv.md_Amber94(mv.energy.name, 349, callback=1, filename='0', log=0, callback_freq=10)
                            #print "time"
                            #import time
                            #time.sleep(1.)
                            #mol.allAtoms.setConformation(0)
                            #mv.minimize = False
                else :						
                    rec = mv.energy.current_scorer.mol1
                    lig = mv.energy.current_scorer.mol2
                    if rec.name == molname or lig.name == molname:
                        updateMolAtomCoord(rec,rec.cconformationIndex)
                        updateMolAtomCoord(lig,lig.cconformationIndex)
#                if rec.name == molname:
#                    #if chname != "":
#                    #    name = rec.geomContainer.masterGeom.chains_obj[chname]
#                    #    o = getObject(name)
#                    #    mg = o.get_mg()
#                    mg = s.get_mg()
#                    mat,rec.mat_transfo_inv = c4dMat2numpy(mg)
#                if lig.name == molname:
#                    print molname,rec
#                    #need the 4x4 matrix
#                    if not hasattr(rec,'mat_transfo_inv') :
#                        #should be identity if nothing have move or not ?
#                        name = rec.geomContainer.masterGeom.obj#.chains_obj[mol.chains[0].name]
#                        o = getObject(name)
#                        mg = o.get_mg()
#                        mat,rec.mat_transfo_inv = c4dMat2numpy(mg,center = rec.getCenter())
#                    #mat,rec.mat_transfo_inv = c4dMat2numpy(mg)#
#                    #update posLigand / reset actually to test purpose
#                    updateLigCoord(lig)
#                    #debug using some spher
#                    #print rec.mat_transfo_inv
                    get_nrg_score(mv.energy)
					
#                if debug :
#                        matx = matrix2c4dMat(mat)
#                        imatx = matrix2c4dMat(rec.mat_transfo_inv)
#                        sr = getObject('sphere_rec')
#                        sr.set_mg(matx)
#                        sl = getObject('sphere_lig')
#                        sl.set_mg(imatx)
            #update atom coord for dedicated conformation  (add or setConf)
            #then compute some energie!


def Cylinder(name,radius=1.,length=1.,res=16, pos = [0.,0.,0.]):
    baseCyl = c4d.BaseObject(CYLINDER)
    baseCyl[5000] = radius
    baseCyl[5005] = length
    baseCyl[5008] = res
    baseCyl.make_tag(c4d.Tphong)
    #addObjectToScene(getCurrentScene(),baseCyl)
    return baseCyl
		
def Sphere(name,radius=1.0,res=0):
    QualitySph={"0":6,"1":4,"2":5,"3":6,"4":8,"5":16} 
    baseSphere = c4d.BaseObject(c4d.Osphere)
    baseSphere[PRIM_SPHERE_RAD] = radius
    baseSphere[1111]=QualitySph[str(res)]
    baseSphere.make_tag(c4d.Tphong)
    #addObjectToScene(getCurrentScene(),baseSphere)
    return baseSphere
					              
def updateSphereMesh(geom,quality=0,cpkRad=0.8,scale=0.,radius=0):
    AtmRadi = {"A":1.7,"N":"1.54","C":"1.85","O":"1.39","S":"1.85","H":"1.2","P" : "1.7"}
    #print geom.mesh
    for name in geom.mesh.keys() : 
        scaleFactor=float(cpkRad)+float(AtmRadi[name])*float(scale)
        if float(cpkRad) > 0. :
            scaleFactor = float(cpkRad)*float(scale)
        #print cpkRad,scale,scaleFactor
        #print geom.mesh[name],geom.mesh[name].get_name()
        mesh=geom.mesh[name].get_down()
        #print mesh.get_name()        
        #mesh[PRIM_SPHERE_RAD]=scaleFactor
        mesh[905]=c4d.Vector(float(scaleFactor),float(scaleFactor),float(scaleFactor))
        #mesh[name][905]=c4d.Vector(float(scaleFactor),float(scaleFactor),float(scaleFactor))
        mesh.message(c4d.MSG_UPDATE)
    #pass
        
def createBaseSphere(name="BaseMesh",quality=0,cpkRad=0.,scale=0.,radius=None,mat=None,parent=None):
    QualitySph={"0":6,"1":4,"2":5,"3":6,"4":8,"5":16} 
    #AtmRadi = {"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2"}
    AtmRadi = {"A":1.7,"N":1.54,"C":1.85,"P":1.7,"O":1.39,"S":1.85,"H":1.2}
    iMe={}
    baseparent=newEmpty(name)
    addObjectToScene(getCurrentScene(),baseparent,parent=parent)
    baseShape = newEmpty(name+"_shape")
    addObjectToScene(getCurrentScene(),baseShape,parent=baseparent)
    baseSphere = c4d.BaseObject(c4d.Osphere)
    baseSphere[PRIM_SPHERE_RAD] = 1.
    baseSphere[1111]=QualitySph[str(quality)]
    baseSphere.make_tag(c4d.Tphong)
    addObjectToScene(getCurrentScene(),baseSphere,parent=baseShape)
    if mat == None : mat=create_Atoms_materials()
    for atn in AtmRadi.keys():
        atparent=newEmpty(name+"_"+atn)
        scaleFactor=float(cpkRad)+float(AtmRadi[atn])*float(scale)
        rad=AtmRadi[atn]
        #iMe[atn]=c4d.BaseObject(c4d.Osphere)
        iMe[atn] = c4d.BaseObject(INSTANCE)
        iMe[atn][1001] = baseShape
        iMe[atn].set_name(atn)
        #iMe[atn].set_render_mode(c4d.MODE_OFF)
        #quality - > resolution
        #iMe[atn][1111]=QualitySph[str(quality)]       
        if radius == None : iMe[atn][905]=c4d.Vector(float(scaleFactor),float(scaleFactor),float(scaleFactor))#[PRIM_SPHERE_RAD] = scaleFactor#1.#float(rad)
        else : iMe[atn][905]=c4d.Vector(float(scaleFactor),float(scaleFactor),float(scaleFactor))#[PRIM_SPHERE_RAD] = scaleFactor#1.#float(radius)
        #iMe[atn][905]=c4d.Vector(float(scaleFactor),float(scaleFactor),float(scaleFactor))
        #iMe[atn].make_tag(c4d.Tphong)
        addObjectToScene(getCurrentScene(),atparent,parent=baseparent)
        addObjectToScene(getCurrentScene(),iMe[atn],parent=atparent)
        iMe[atn]=atparent
        #texture = iMe[atn].make_tag(c4d.Ttexture)
        #texture[1010] = mat[atn]
        
    return iMe
def updateSphereObj(obj,coord):
    updateObjectPos(obj,coord)
    
def updateSphereObjs(g):
    if not hasattr(g,'obj') : return
    newcoords=g.getVertices()
    #print "upadteObjSpheres"
    for i,o in enumerate(g.obj):
        c=newcoords[i]
        #o=getObject(nameo)
        newPos=c4d.Vector(float(c[2]),float(c[1]),float(c[0]))         
        parentPos = getPosUntilRoot(o)#parent.get_pos()
        o.set_pos(newPos-parentPos)            

def updateObjectPos(object,position):
    if len(position) == 1 : c = position[0]
    else : c = position
    #print "upadteObj"
    newPos=c4dv(c)
    parentPos = getPosUntilRoot(object)#parent.get_pos()
    object.set_pos(newPos-parentPos)

def clonesAtomsSphere(name,x,iMe,doc,mat=None,scale=1.0,Res=32,R=None,join=0):
    spher=[]
    k=0
    n='S'
    AtmRadi = {"A":1.7,"N":1.54,"C":1.7,"P":1.7,"O":1.52,"S":1.85,"H":1.2}
    
    if scale == 0.0 : scale = 1.0
    if mat == None : mat=create_Atoms_materials()
    if name.find('balls') != (-1) : n='B'
    for j in range(len(x)): spher.append(None)
    for j in range(len(x)):
        #at=res.atoms[j]
        at=x[j]
        atN=at.name
        #print atN
        fullname = at.full_name()
        #print fullname
        atC=at._coords[0]
        spher[j] = iMe[atN[0]].get_clone()
        spher[j].set_name(n+"_"+fullname)#.replace(":","_"))
        spher[j].set_pos(c4d.Vector(float(atC[2]),float(atC[1]),float(atC[0])))
        spher[j][905]=c4d.Vector(float(scale),float(scale),float(scale))
        #
        #print atN[0]
        #print mat[atN[0]]    
        texture = spher[j].make_tag(c4d.Ttexture)
        texture[1010] = mat[atN[0]]
        k=k+1
    return spher
    
def instancesSphere(name,centers,radii,meshsphere,colors,scene,parent=None):
    sphs=[]
    mat = None
    if len(colors) == 1:
        mat = retrieveColorMat(colors[0])
        if mat == None:		
            mat = addMaterial('mat_'+name,colors[0])
    for i in range(len(centers)):
        sphs.append(c4d.BaseObject(INSTANCE))
        sphs[i][1001]=meshsphere
        sphs[i].set_name(name+str(i))        
        sphs[i].set_pos(c4dv(centers[i]))
        #sphs[i].set_pos(c4d.Vector(float(centers[i][0]),float(centers[i][1]),float(centers[i][2])))
        sphs[i][905]=c4d.Vector(float(radii[i]),float(radii[i]),float(radii[i]))
        texture = sphs[i].make_tag(c4d.Ttexture)
        if mat == None : mat = addMaterial("matsp"+str(i),colors[i])
        texture[1010] = mat#mat[bl.retrieveColorName(sphColors[i])]
        addObjectToScene(scene,sphs[i],parent=parent)
    return sphs
    
def instancesAtomsSphere(name,x,iMe,doc,mat=None,scale=1.0,Res=32,
						R=None,join=0,geom=None,dialog=None,pb=None):
    sphers=[]
    k=0
    n='S'
    AtmRadi = {"A":1.7,"N":1.54,"C":1.7,"P":1.7,"O":1.52,"S":1.85,"H":1.2}
    if R == None : R = 0.
    if scale == 0.0 : scale = 1.0    
    if mat == None : mat=create_Atoms_materials()    
    if name.find('balls') != (-1) : n='B'
    
    if geom is not None:
        coords=geom.getVertices()
    else :
        coords=x.coords
    hiera = 'default'		
    mol = x[0].getParentOfType(Protein)		
    molname = name.split("_")[0]
    if VERBOSE : print "molname ", molname,mol
    Spline = getObject("spline"+molname)
    for c in mol.chains:
		spher=[]
		oneparent = True 
		atoms = c.residues.atoms
		parent=findatmParentHierarchie(atoms[0],n,hiera)	
		for j in xrange(len(atoms.coords)):
			#at=res.atoms[j]
			at=atoms[j]
			radius = at.radius
			scaleFactor=float(R)+float(radius)*float(scale)
			atN=at.name
			#print atN
			if atN[0] not in AtmRadi.keys(): atN="A"
			fullname = at.full_name()
			#print fullname
			atC=at.coords#at._coords[0]
			spher.append( c4d.BaseObject(INSTANCE) )
			spher[j][1001]=iMe[atN[0]]
			#spher[j][1001]=1        
			spher[j].set_name(n+"_"+fullname)#.replace(":","_")
			sc = iMe[atN[0]][905].x
			if sc != scaleFactor : 
				spher[j][905]=c4d.Vector(float((1/sc)*scale),float((1/sc)*scale),float((1/sc)*scale))
			#
			if atN in ["CA","N","C"] and Spline != None and n == 'S':
				pos= float(((j*1.) / Spline.get_point_count()))
				path=spher[j].make_tag(Follow_PATH)
				path[1001] = Spline
				path[1000] = 1
				path[1003] = pos
			else : spher[j].set_pos(c4dv(atC))
			texture = spher[j].make_tag(c4d.Ttexture)
			texture[1010] = mat[atN[0]]
			p = findatmParentHierarchie(at,n,hiera)
			if parent != p : 
			    cp = p
			    oneparent = False
			    parent = p
			else :
			    cp = parent							
			addObjectToScene(getCurrentScene(),spher[j],parent=cp)
			toggleDisplay(spher[j],False)
			k=k+1
			if dialog != None :
				dialog.bc[c4d.gui.BFM_STATUSBAR_PROGRESS] = j/len(coords)
				#dialog.bc[c4d.gui.BFM_STATUSBAR_PROGRESSFULLSIZE] = True
				dialog.set(dialog._progess,float(j/len(coords)))#dialog.bc)
				getCurrentScene().message(c4d.MULTIMSG_UP)       
				c4d.draw_views(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)	  
		sphers.extend(spher)
    return sphers
        
def spheresMesh(name,x,mat=None,scale=1.0,Res=32,R=None,join=0):
    if scale == 0.0 : scale =1.
    scale = scale *2.
    spher=[]
    if Res == 0 : Res = 10.
    else : Res = Res *5.
    k=0
    if mat == None : mat=create_Atoms_materials()
    #print len(x)
    for j in range(len(x)): spher.append(None)
    for j in range(len(x)):
        #at=res.atoms[j]
        at=x[j]
        atN=at.name
        #print atN
        fullname = at.full_name()
        #print fullname
        atC=at._coords[0]
        #if R !=None : rad=R
        #elif AtmRadi.has_key(atN[0]) : rad=AtmRadi[atN[0]]
        #else : rad=AtmRadi['H']
        #print  at.vdwRadius
        rad=at.vdwRadius
        #print rad
        spher[j] = c4d.BaseObject(c4d.Osphere)
        spher[j].set_name(fullname.replace(":","_"))
        spher[j][PRIM_SPHERE_RAD] = float(rad)*float(scale)
        spher[j].set_pos(c4d.Vector(float(atC[0]),float(atC[1]),float(atC[2])))
        spher[j].make_tag(c4d.Tphong)
        # create a texture tag on the PDBgeometry object
        #texture = spher[j].make_tag(c4d.Ttexture)
        #create the dedicayed material
        #print mat[atN[0]]
        #texture[1010] = mat[atN[0]]
        #spher.append(me)
    k=k+1
    return spher


def display_CPK(mol,sel,display,needRedraw=False,quality=0,cpkRad=0.0,scaleFactor=1.0,useTree="default",dialog=None):
    sc = getCurrentScene()
    g = mol.geomContainer.geoms['cpk']
    #print g
    #name=selection+"_cpk"
    #select=self.select(selection,negate=False, only=True, xor=False, log=0, 
    #                   intersect=False)
    #print name,select
    #sel=select.findType(Atom)
    if not hasattr(g,"obj"): #if no mesh have to create it for evey atms
        name=mol.name+"_cpk"
        #print name
        mesh=createBaseSphere(name="base_cpk",quality=quality,cpkRad=cpkRad,
                              scale=scaleFactor,parent=mol.geomContainer.masterGeom.obj)
        ob=instancesAtomsSphere(name,mol.allAtoms,mesh,sc,scale=scaleFactor,
                                Res=quality,join=0,dialog=dialog)
        addObjToGeom([ob,mesh],g)
        for i,o in enumerate(ob):
            if dialog != None :
                dialog.bc[c4d.gui.BFM_STATUSBAR_PROGRESS] = j/len(coords)
                #dialog.bc[c4d.gui.BFM_STATUSBAR_PROGRESSFULLSIZE] = True
                dialog.set(dialog._progess,float(i/len(ob)))#dialog.bc)
                getCurrentScene().message(c4d.MULTIMSG_UP)       
                c4d.draw_views(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)
            parent=mol.geomContainer.masterGeom.obj
            hierarchy=parseObjectName(o)
            if hierarchy != "" :
                if useTree == 'perRes' :
                    parent = getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])
                elif useTree == 'perAtom' :
                    parent = getObject(o.get_name().split("_")[1])
                else :
                    parent = getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_cpk"])                
            addObjectToScene(sc,o,parent=parent)
            toggleDisplay(o,False) #True per default
            
    #elif hasattr(g,"obj")  and display : 
        #updateSphereMesh(g,quality=quality,cpkRad=cpkRad,scale=scaleFactor) 
        #if needRedraw : updateSphereObj(g)
    #if hasattr(g,"obj"):
    else :
        updateSphereMesh(g,quality=quality,cpkRad=cpkRad,scale=scaleFactor)
        atoms=sel#findType(Atom) already done
        for atms in atoms:
            nameo = "S_"+atms.full_name()
            o=getObject(nameo)#Blender.Object.Get (nameo)
            if o != None :
                toggleDisplay(o,display)
                if needRedraw : updateObjectPos(o,atms.coords) 


def getStickProperties(coord1,coord2):
    x1 = float(coord1[0])
    y1 = float(coord1[1])
    z1 = float(coord1[2])
    x2 = float(coord2[0])
    y2 = float(coord2[1])
    z2 = float(coord2[2])
    laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
    wsz = atan2((y1-y2), (z1-z2))
    wz = acos((x1-x2)/laenge)
    offset=c4d.Vector(float(z1+z2)/2,float(y1+y2)/2,float(x1+x2)/2)
    v_2=c4d.Vector(float(z1-z2),float(y1-y2),float(x1-x2))
    v_2.normalize()
    v_1=c4d.Vector(float(1.),float(0.),float(2.))
    v_3=c4d.Vector.crossproduct(v_1,v_2)
    v_3.normalize()
    v_1=c4d.Vector.crossproduct(v_2,v_3)
    v_1.normalize()
    #from mglutil.math import rotax
    #pmx=rotax.rotVectToVect([1.,0.,0.], [float(z1-z2),float(y1-y2),float(x1-x2)], i=None)
    mx=c4d.Matrix(offset,v_1, v_2, v_3)
    #mx=c4d.Matrix(c4d.Vector(float(pmx[0][0]),float(pmx[0][1]),float(pmx[0][2]),float(pmx[0][3])),
    #print laenge
    return laenge,mx

def instancesCylinder(name,points,faces,radii,mesh,colors,scene,parent=None):
    cyls=[]
    mat = None
    if len(colors) == 1:
        mat = retrieveColorMat(colors[0])
        if mat == None:		
            mat = addMaterial('mat_'+name,colors[0])
    for i in range(len(faces)):
        laenge,mx=getStickProperties(points[faces[i][0]],points[faces[i][1]]) 	
        cyls.append(c4d.BaseObject(INSTANCE))
        cyls[i][1001]=mesh
        cyls[i].set_name(name+str(i))
        #orient and scale
        cyls[i].set_mg(mx)
        cyls[i][905]=c4d.Vector(float(radii[i]),float(radii[i]),float(radii[i]))
        cyls[i][905,1001]=float(laenge)
        texture = cyls[i].make_tag(c4d.Ttexture)
        if mat == None : mat = addMaterial("matcyl"+str(i),colors[i])
        texture[1010] = mat#mat[bl.retrieveColorName(sphColors[i])]
        addObjectToScene(scene,cyls[i],parent=parent)
    return cyls

    
def updateTubeMesh(geom,cradius=1.0,quality=0):
    #print geom.mesh
    mesh=geom.mesh.get_down()#should be the cylinder
    #print mesh.get_name()        
    #mesh[5000]=cradius
    cradius = cradius*1/0.2
    mesh[905]=c4d.Vector(float(cradius),1.,float(cradius))
    mesh.message(c4d.MSG_UPDATE)
    #pass

def updateTubeObjs(g,bicyl=False):
    #problem when ds slection....
    if not hasattr(g,'obj') : return
    newpoints=g.getVertices()
    newfaces=g.getFaces()
    #print "upadteObjSpheres"
    for i,o in enumerate(g.obj):
        laenge,mx=getStickProperties(newpoints[newfaces[i][0]],newpoints[newfaces[i][1]])
        o.set_ml(mx)
        o[905,1001]=float(laenge)
        parentPos = getPosUntilRoot(o)#parent.get_pos()
        currentPos = o.get_pos()
        o.set_pos(currentPos - parentPos)            

  
def updateTubeObj(atm1,atm2,bicyl=False):
    c0=numpy.array(atm1.coords)
    c1=numpy.array(atm2.coords)
    if bicyl :
        vect = c1 - c0	
        name1="T_"+atm1.full_name()+"_"+atm2.name
        name2="T_"+atm2.full_name()+"_"+atm1.name
        o=getObject(name1)
        updateOneSctick(o,c0,(c0+(vect/2.))) 	 		
        o=getObject(name2)
        updateOneSctick(o,(c0+(vect/2.)),c1) 	 		
    else :
        name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)
        o=getObject(name)
        updateOneSctick(o,c0,c1)
		        		
def updateOneSctick(o,coord1,coord2):
    laenge,mx=getStickProperties(coord1,coord2)
    o.set_ml(mx)
    o[905,1001]=float(laenge)
    parentPos = getPosUntilRoot(o)#parent.get_pos()
    currentPos = o.get_pos()
    o.set_pos(currentPos - parentPos)                

def biStick(atm1,atm2,hiera,instance):
    mol=atm1.getParentOfType(Protein)
    stick=[]
    c0=numpy.array(atm1.coords)
    c1=numpy.array(atm2.coords)
    vect = c1 - c0
    n1=atm1.full_name().split(":")
    n2=atm2.full_name().split(":")
    name1="T_"+n1[1]+"_"+n1[2]+"_"+n1[3]+"_"+atm2.name
    name2="T_"+n2[1]+"_"+n2[2]+"_"+n2[3]+"_"+atm1.name	
    #name1="T_"+atm1.full_name()+"_"+atm2.name
    #name2="T_"+atm2.full_name()+"_"+atm1.name
    laenge,mx=getStickProperties(c0,(c0+(vect/2.)))
    stick.append(c4d.BaseObject(INSTANCE))
    stick[0][1001]=instance
    stick[0].set_mg(mx)   
    stick[0][905,1001]=float(laenge)
    stick[0].set_name(name1)
    texture=stick[0].make_tag(c4d.Ttexture)	
    mat=getCurrentScene().find_material(atm1.name[0])
    if mat == None :
        mat = addMaterial(atm1.name[0],[0.,0.,0.]) 		
    texture[1010]=mat
    laenge,mx=getStickProperties((c0+(vect/2.)),c1)
    stick.append(c4d.BaseObject(INSTANCE))
    stick[1][1001]=instance
    stick[1].set_mg(mx)   
    stick[1][905,1001]=float(laenge)
    stick[1].set_name(name2)
    texture=stick[1].make_tag(c4d.Ttexture)
    mat=getCurrentScene().find_material(atm2.name[0])
    if mat == None :
        mat = addMaterial(atm2.name[0],[0.,0.,0.])
    texture[1010]=mat
	#parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
    parent = findatmParentHierarchie(atm1,'B',hiera)
    addObjectToScene(getCurrentScene(),stick[0],parent=parent)
    addObjectToScene(getCurrentScene(),stick[1],parent=parent)	
    return stick
	
def Tube(set,atms,points,faces,doc,mat=None,res=32,size=0.25,sc=1.,join=0,
         instance=None,hiera = 'perRes',bicyl=False,pb=False):
    sticks=[]
    bonds, atnobnd = set.bonds
    if instance == None:
        mol = atms[0].top
        instance=newEmpty("baseBond") 
        addObjectToScene(getCurrentScene(),instance,parent=mol.geomContainer.masterGeom.obj)			
        cyl=c4d.BaseObject(CYLINDER) 
        cyl[5000]=size
        cyl[5005]= 1.  #lenght
        cyl[5008]=	res  #subdivision
        cyl.make_tag(c4d.Tphong)										
        addObjectToScene(getCurrentScene(),cyl,parent=instance) 
    for i,bond in enumerate(bonds):
        if bicyl :
            sticks.extend(biStick(bond.atom1,bond.atom2,hiera,instance))
        else :
            pass
    return [sticks,instance]	
	
def oldTube(set,atms,points,faces,doc,mat=None,res=32,size=0.25,sc=1.,join=0,instance=None,hiera = 'perRes'):
 bonds, atnobnd = set.bonds
 backbone = ['N', 'CA', 'C', 'O']
 stick=[]
 tube=[]
 #size=size*2.
 #coord1=x[0].atms[x[0].atms.CApos()].xyz() #x.xyz()[i].split()
 #coord2=x[1].atms[x[1].atms.CApos()].xyz() #x.xyz()[i+1].split()
 #print len(points)
 #print len(faces)
 #print len(atms)
 atm1=bonds[0].atom1#[faces[0][0]]
 atm2=bonds[0].atom2#[faces[0][1]]
 #name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number) 
 name="T_"+atm1.full_name()+"_"+atm2.name
 mol=atm1.getParentOfType(Protein)
 laenge,mx=getStickProperties(points[faces[0][0]],points[faces[0][1]]) 
 if mat == None : mat=create_sticks_materials()
 if instance == None :
     stick.append(c4d.BaseObject(CYLINDER))#(res, size, laenge/sc) #1. CAtrace, 0.25 regular |sc=1 CATrace, 2 regular
     stick[0].set_mg(mx)
     stick[0][5005]=laenge/sc#size
     stick[0][5000]=size#radius
     stick[0][5008]=res#resolution
     stick[0][5006]=2#heght segment
 else :
     stick.append(c4d.BaseObject(INSTANCE))
     stick[0][1001]=instance
     stick[0].set_mg(mx)     
     stick[0][905,1001]=float(laenge)
 texture=stick[0].make_tag(c4d.Ttexture)
 #print  atms[faces[0][0]].name[0]+atms[faces[0][1]].name[0]
 name1=atms[faces[0][0]].name[0]
 name2=atms[faces[0][1]].name[0]
 if name1 not in AtmRadi.keys(): name1="A"
 if name2 not in AtmRadi.keys(): name2="A"
 texture[1010]=mat[name1+name2]              
 stick[0].set_name(name)
 #stick[0].set_pos(c4d.Vector(float(z1+z2)/2,float(y1+y2)/2,float(x1+x2)/2))
 #stick[0].set_rot(c4d.Vector(float(wz),float(0),float(wsz)))
 #stick[0][904,1000] = wz #RY/RH
 #stick[0][904,1002] = wsz #RZ/RB
 stick[0].make_tag(c4d.Tphong)
 hierarchy=parseObjectName("B_"+atm1.full_name())
 #parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
 if hiera == 'perRes' :
     parent = getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])
 elif hiera == 'perAtom' :
     if atm1.name in backbone : 
         parent = getObject(atm1.full_name()+"_bond")
     else :
         parent = getObject(atm1.full_name()+"_sbond")
 else :
     parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
 addObjectToScene(doc,stick[0],parent=parent)
 for i in range(1,len(faces)):
  atm1=bonds[i].atom1#[faces[i][0]]
  atm2=bonds[i].atom2#[faces[i][1]]
  #name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)
  name="T_"+atm1.full_name()+"_"+atm2.name
  laenge,mx=getStickProperties(points[faces[i][0]],points[faces[i][1]])
  if instance == None :
     stick.append(c4d.BaseObject(CYLINDER))#(res, size, laenge/sc) #1. CAtrace, 0.25 regular |sc=1 CATrace, 2 regular
     stick[i].set_ml(mx)
     stick[i][5005]=laenge/sc#radius
     stick[i][5000]=size#height/size
     stick[i][5008]=res#resolution rotation segment
     stick[i][5006]=2#heght segment     
  else :
     stick.append(c4d.BaseObject(INSTANCE))
     stick[i][1001]=instance
     stick[i].set_ml(mx)
     stick[i][905,1001]=float(laenge)
  texture=stick[i].make_tag(c4d.Ttexture)
  #print i,i+1
  name1=atms[faces[i][0]].name[0]
  name2=atms[faces[i][1]].name[0]
  if name1 not in AtmRadi.keys(): name1="A"
  if name2 not in AtmRadi.keys(): name2="A"

  if i < len(atms) :
     #print  name1+name2
     texture[1010]=mat[name1+name2]
  else :
     texture[1010]=mat[name1+name2]                                 
  stick[i].set_name(name)
  #stick[i].set_pos(c4d.Vector(float(z1+z2)/2,float(y1+y2)/2,float(x1+x2)/2))
  #stick[i].set_rot(c4d.Vector(float(wz),float(0.),float(wsz)))
  stick[i].set_ml(mx)
  stick[i].make_tag(c4d.Tphong)
  hierarchy=parseObjectName("B_"+atm1.full_name())
  #parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
  if hiera == 'perRes' :
     parent = getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])
  elif hiera == 'perAtom' :
     if atm1.name in backbone : 
         parent = getObject(atm1.full_name()+"_bond")
     else :
         parent = getObject(atm1.full_name()+"_sbond")
  else :
     parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])

  addObjectToScene(doc,stick[i],parent=parent)

 #if join==1 : 
 #    stick[0].join(stick[1:])
 #    for ind in range(1,len(stick)):
        #obj[0].join([obj[ind]])
#        scn.unlink(stick[ind])
    #obj[0].setName(name)
 return [stick]

 
def c4dv(points):
    return c4d.Vector(float(points[2]),float(points[1]),float(points[0]))
    #return c4d.Vector(float(points[0]),float(points[1]),float(points[2]))
	
def getCoordinateMatrix(pos,direction):
  offset=pos
  v_2=direction
  v_2.normalize()
  v_1=c4d.Vector(float(1.),float(0.),float(0.))
  v_3=c4d.Vector.crossproduct(v_1,v_2)
  v_3.normalize()
  v_1=c4d.Vector.crossproduct(v_2,v_3)
  v_1.normalize()
 #from mglutil.math import rotax
 #pmx=rotax.rotVectToVect([1.,0.,0.], [float(z1-z2),float(y1-y2),float(x1-x2)], i=None)
  return c4d.Matrix(offset,v_1, v_2, v_3)

def getCoordinateMatrixBis(pos,v1,v2):
  offset=c4dv(pos)
  v_2=c4dv(v2)
  v_1=c4dv(v1)
  v_3=c4d.Vector.crossproduct(v_1,v_2)
  v_3.normalize()
 #from mglutil.math import rotax
 #pmx=rotax.rotVectToVect([1.,0.,0.], [float(z1-z2),float(y1-y2),float(x1-x2)], i=None)
  return c4d.Matrix(offset,v_1, v_2, v_3)

def loftnurbs(name,mat=None):
    loft=c4d.BaseObject(LOFTNURBS)
    loft[1008]=0 #adaptive UV false
    loft.set_name(name)
    loft.make_tag(c4d.Tphong)
    texture = loft.make_tag(c4d.Ttexture)
    texture[1004]=6 #UVW Mapping    
    #create the dedicayed material
    if mat == None : 
            texture[1010] = create_loft_material(name='mat_'+name)
    else : texture[1010] = mat
    return loft

def addShapeToNurb(loft,shape,position=-1):
    list_shape=loft.get_childs()
    shape.insert_after(list_shape[position])

#def createShapes2D()
#    sh=c4d.BaseObject(dshape)

def spline(name, points,close=0,type=1):
    spline=c4d.BaseObject(c4d.Ospline)
    spline[1000]=type
    spline[1002]=close
    spline.set_name(name)
    spline.resize_object(int(len(points)))
    for i,p in enumerate(points):
        spline.set_point(i, c4dv(p))
    return spline

def update_spline(name,new_points):
    spline=getCurrentScene().find_object(name)
    if spline is None : return False
    spline.resize_object(int(len(new_points)))
    for i,p in enumerate(new_points):
        spline.set_point(i, c4dv(p))
    return True
    
def createShapes2Dspline(doc=None,parent=None):
    circle=c4d.BaseObject(CIRCLE)
    circle[2012]=float(0.3)
    circle[2300]=1
    if doc : addObjectToScene(doc,circle,parent=parent )
    rectangle=c4d.BaseObject(RECTANGLE)
    rectangle[2060]=float(2.2)
    rectangle[2061]=float(0.7)
    rectangle[2300]=1
    if doc : addObjectToScene(doc,rectangle,parent=parent )
    fourside=c4d.BaseObject(FOURSIDE)
    fourside[2121]=float(2.5)
    fourside[2122]=float(0.9)
    fourside[2300]=1
    if doc : addObjectToScene(doc,fourside,parent=parent )
    shape2D={}
    pts=[[0,0,0],[0,1,0],[0,1,1],[0,0,1]]
    #helixshape
    helixshape=fourside.get_real_spline()#spline('helix',pts,close=1,type=2)#AKIMA
    helixshape.set_name('helix')
    shape2D['Heli']=helixshape
    #sheetshape
    sheetshape=rectangle.get_real_spline()#spline('sheet',pts,close=1,type=0)#LINEAR
    sheetshape.set_name('sheet')
    shape2D['Shee']=sheetshape
    #strandshape
    strandshape=sheetshape.get_clone()
    strandshape.set_name('strand')
    shape2D['Stra']=strandshape
    #coilshape
    coilshape=circle.get_real_spline()#spline('coil',pts,close=1,type=4)#BEZIER
    coilshape.set_name('coil')
    shape2D['Coil']=coilshape
    #turnshape
    turnshape=coilshape.get_clone()
    turnshape.set_name('turn')
    shape2D['Turn']=turnshape
    if doc : 
        for o in shape2D.values() :
            addObjectToScene(doc,o,parent=parent )    
    return shape2D,[circle,rectangle,fourside,helixshape,sheetshape,strandshape,coilshape,turnshape]

def createShapes2D(doc=None,parent=None):
    if doc is None :
        doc = getCurrentScene()    
    shape2D={}
    circle=c4d.BaseObject(CIRCLE)
    circle[2012]=float(0.3)
    circle[2300]=0
    circle2=circle.get_clone()
    circle2.set_name('Circle')
    
    coil=c4d.BaseObject(c4d.Onull)
    coil.set_name('coil')    
    turn=c4d.BaseObject(c4d.Onull)
    turn.set_name('turn')
    shape2D['Coil']=coil
    shape2D['Turn']=turn        

    addObjectToScene(doc,coil,parent=parent )
    addObjectToScene(doc,circle,parent=coil )
    addObjectToScene(doc,turn,parent=parent )
    addObjectToScene(doc,circle2,parent=turn )

    rectangle=c4d.BaseObject(RECTANGLE)
    rectangle[2060]=float(2.2)
    rectangle[2061]=float(0.7)
    rectangle[2300]=0
    rectangle2=rectangle.get_clone()
    rectangle2.set_name('Rectangle')
    
    stra=c4d.BaseObject(c4d.Onull)
    stra.set_name('stra')    
    shee=c4d.BaseObject(c4d.Onull)
    shee.set_name('shee')
    shape2D['Stra']=stra
    shape2D['Shee']=shee        

    addObjectToScene(doc,stra,parent=parent )
    addObjectToScene(doc,rectangle,parent=stra )
    addObjectToScene(doc,shee,parent=parent )
    addObjectToScene(doc,rectangle2,parent=shee )
    
    fourside=c4d.BaseObject(FOURSIDE)
    fourside[2121]=float(2.5)
    fourside[2122]=float(0.9)
    fourside[2300]=0
    heli=c4d.BaseObject(c4d.Onull)
    heli.set_name('heli')    
    shape2D['Heli']=heli    

    addObjectToScene(doc,heli,parent=parent )
    addObjectToScene(doc,fourside,parent=heli)
    
    return shape2D,[circle,rectangle,fourside]

def getShapes2D():
    shape2D={}
    shape2D['Coil']=getObject('coil')
    shape2D['Turn']=getObject('turn')
    shape2D['Heli']=getObject('heli')
    shape2D['Stra']=getObject('stra')        
    return shape2D

def morph2dObject(name,objsrc,target):
    obj=objsrc.get_clone()
    obj.set_name(name)
    mixer=obj.make_tag(POSEMIXER)
    mixer[1001]=objsrc    #the default pose
    #for i,sh in enumerate(shape2D) :
    #    mixer[3002,1000+int(i)]=shape2D[sh]
    mixer[3002,1000]=target#shape2D[sh] target 1
    return obj
    
def c4dSpecialRibon(name,points,dshape=CIRCLE,shape2dlist=None,mat=None):
    #if loft == None : loft=loftnurbs('loft',mat=mat)
    shape=[]
    pos=c4d.Vector(float(points[0][2]),float(points[0][1]),float(points[0][0]))
    direction=c4d.Vector(float(points[0][2]-points[1][2]),float(points[0][1]-points[1][1]),float(points[0][0]-points[1][0]))
    mx=getCoordinateMatrix(pos,direction)
    if shape2dlist : shape.append(morph2dObject(dshape+str(0),shape2dlist[dshape],shape2dlist['Heli']))
    else : 
        shape.append(c4d.BaseObject(dshape))
        if dshape == CIRCLE :
            shape[0][2012]=float(0.3)
            #shape[0][2300]=1
        if dshape == RECTANGLE :
            shape[0][2060]=float(0.3*4.)
            shape[0][2061]=float(0.3*3.)
            #shape[0][2300]=1
        if dshape == FOURSIDE:
            shape[0][2121]=float(0.3*4.)
            shape[0][2122]=float(0.1)
            #shape[0][2300]=0            
    shape[0].set_mg(mx)
    if len(points)==2: return shape
    i=1
    while i < (len(points)-1):
        #print i
        pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
        direction=c4d.Vector(float(points[i-1][2]-points[i+1][2]),float(points[i-1][1]-points[i+1][1]),float(points[i-1][0]-points[i+1][0]))
        mx=getCoordinateMatrix(pos,direction)
        if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[dshape],shape2dlist['Heli']))
        else : 
            shape.append(c4d.BaseObject(dshape))    
            if dshape == CIRCLE :
                shape[i][2012]=float(0.3)
                shape[i][2300]=2
            if dshape == RECTANGLE :
                shape[i][2060]=float(0.3*4.)
                shape[i][2061]=float(0.3*3.)
                shape[i][2300]=2
            if dshape == FOURSIDE:
                shape[i][2121]=float(0.3*4.)
                shape[i][2122]=float(0.1)
                shape[i][2300]=2            
        shape[i].set_mg(mx)
        i=i+1
    pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
    direction=c4d.Vector(float(points[i-1][2]-points[i][2]),float(points[i-1][1]-points[i][1]),float(points[i-1][0]-points[i][0]))
    mx=getCoordinateMatrix(pos,direction)
    if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[dshape],shape2dlist['Heli']))
    else : 
        shape.append(c4d.BaseObject(dshape))
        if dshape == CIRCLE :
            shape[i][2012]=float(0.3)
            shape[i][2300]=2
        if dshape == RECTANGLE :
            shape[i][2060]=float(0.3*4.)
            shape[i][2061]=float(0.3*3.)
            shape[i][2300]=2        
        if dshape == FOURSIDE:
            shape[i][2121]=float(0.3*4.)
            shape[i][2122]=float(0.1)
            shape[i][2300]=2
    shape[i].set_mg(mx)
    return shape
    
def c4dSecondaryLofts(name,matrices,dshape=CIRCLE,mat=None):
    #if loft == None : loft=loftnurbs('loft',mat=mat)
    shape=[]            
    i=0
    while i < (len(matrices)):
        #pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
        #direction=c4d.Vector(float(points[i-1][2]-points[i+1][2]),float(points[i-1][1]-points[i+1][1]),float(points[i-1][0]-points[i+1][0]))
        mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
        #mx=getCoordinateMatrix(pos,direction)
        shape.append(c4d.BaseObject(dshape))    
        shape[i].set_mg(mx)
        if dshape == CIRCLE :
            shape[i][2012]=float(0.3)
            shape[i][2300]=0
        if dshape == RECTANGLE :
            shape[i][2060]=float(2.2)
            shape[i][2061]=float(0.7)
            shape[i][2300]=0
        if dshape == FOURSIDE:
            shape[i][2121]=float(2.5)
            shape[i][2122]=float(0.9)
            shape[i][2300]=0            
        i=i+1
    return shape

def instanceShape(ssname,shape2D):
    #if shape2D=None : shape2D=createShapes2D()
    shape=c4d.BaseObject(INSTANCE)
    shape[1001]=shape2D[ssname[:4]]
    shape.set_name(ssname[:4])
    return shape
    
def makeShape(dshape,ssname):
    shape=c4d.BaseObject(dshape)
    if dshape == CIRCLE :
                shape[2012]=float(0.3)
                shape[2300]=0
                shape.set_name(ssname[:4])                
    if dshape == RECTANGLE :
                shape[2060]=float(2.2)
                shape[2061]=float(0.7)
                shape[2300]=0
                shape.set_name(ssname[:4])                    
    if dshape == FOURSIDE:
                shape[2121]=float(2.5)
                shape[2122]=float(0.9)
                shape[2300]=0
                shape.set_name(ssname[:4])                
    return shape
    
def c4dSecondaryLoftsSp(name,atoms,dshape=CIRCLE,mat=None,shape2dmorph=None,shapes2d=None,instance=False):
    #print "ok build loft shape"
    #if loft == None : loft=loftnurbs('loft',mat=mat)
    shape=[]
    prev=None    
    ssSet=atoms[0].parent.parent.secondarystructureset
    molname=atoms[0].full_name().split(":")[0]
    chname=    atoms[0].full_name().split(":")[1]        
    i=0
    iK=0
    #get The pmv-extruder    
    sheet=atoms[0].parent.secondarystructure.sheet2D
    matrices=sheet.matrixTransfo
    if mat == None : mat = c4d.documents.get_active_document().find_material('mat_loft'+molname+'_'+chname)
    while i < (len(atoms)):
        ssname=atoms[i].parent.secondarystructure.name
        dshape=SSShapes[ssname[:4]]#ssname[:4]
        #print ssname,dshape        
        #pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
        #direction=c4d.Vector(float(points[i-1][2]-points[i+1][2]),float(points[i-1][1]-points[i+1][1]),float(points[i-1][0]-points[i+1][0]))
        mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
        #mx=getCoordinateMatrix(pos,direction)
        #iK=iK+1
        if shape2dmorph :
            shape.append(morph2dObject(dshape+str(i),shape2dmorph[dshape],shape2dmorph['Heli']))
            shape[-1].set_mg(mx)
        else :
            #print str(prev),ssname         
            if prev != None: #end of loop 
                if ssname[:4] != prev[:4]:
                    if not instance : shape.append(makeShape(SSShapes[prev[:4]],prev))
                    else : shape.append(instanceShape(prev,shapes2d))                    
                    shape[-1].set_mg(mx)
            if not instance : shape.append(makeShape(dshape,ssname))
            else : shape.append(instanceShape(ssname,shapes2d))
            shape[-1].set_mg(mx)
        prev=ssname
        i=i+1
    if mat != None:
        prev=None
        #i=(len(shape))
        i=0
        while i < (len(shape)):
            ssname=shape[i].get_name()
            #print ssname            
            pos=1-((((i)*100.)/len(shape))/100.0)
            if pos < 0 : pos = 0.
            #print pos
            #change the material knote according ss color / cf atom color...
            #col=atoms[i].colors['secondarystructure']
            col=c4dColor(SSColor[ssname])
            nc=c4d.Vector(col[0],col[1],col[2])
            ncp=c4d.Vector(0,0,0)            
            if prev != None :
                pcol=c4dColor(SSColor[prev])
                ncp=c4d.Vector(pcol[0],pcol[1],pcol[2])        
            #print col
            #print ssname[:4]
            #print prev
            if ssname != prev : #new ss
                grad=mat[8000][1007]    
            #iK=iK+1
                nK=grad.get_knot_count()
            #print "knot count ",nK,iK                
                if iK >= nK :
                    #print "insert ",pos,nK
                    #print "grad.insert_knot(c4d.Vector("+str(col[0])+str(col[1])+str(col[2])+"), 1.0, "+str(pos)+",0.5)"
                    if prev != None :
                        grad.insert_knot(ncp, 1.0, pos+0.01,0.5)
                        iK=iK+1                                                
                    grad.insert_knot(nc, 1.0, pos-0.01,0.5)
                    #grad.insert_knot(ncp, 1.0, pos+0.1,0.5)                    
                    iK=iK+1                    
                else :
                    #print "set ",iK,pos    
                    if prev != None :grad.set_knot(iK-1,ncp,1.0,pos,0.5)                            
                    grad.set_knot(iK,nc,1.0,pos,0.5)
                mat[8000][1007]=grad
            prev=ssname
            mat.message(c4d.MSG_UPDATE)
            i=i+1            
    #mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
    #if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[shape],shape2dlist['Heli']))
    return shape

def LoftOnSpline(name,chain,atoms,Spline=None,dshape=CIRCLE,mat=None,shape2dmorph=None,shapes2d=None,instance=False):
    #print "ok build loft/spline"
    molname = atoms[0].full_name().split(":")[0]
    chname = atoms[0].full_name().split(":")[1]        
    #we first need the spline
    #if loft == None : loft=loftnurbs('loft',mat=mat)
    shape=[]
    prev=None
    #mol = atoms[0].top	    
    ssSet=chain.secondarystructureset#atoms[0].parent.parent.secondarystructureset
    i=0
    iK=0
    #get The pmv-extruder    
    sheet=chain.residues[0].secondarystructure.sheet2D
    matrices=sheet.matrixTransfo
    ca=atoms.get('CA')
    o =atoms.get('O') 
    if Spline is None :
        parent=atoms[0].parent.parent.parent.geomContainer.masterGeom.chains_obj[chname]
        Spline = spline(name+'spline',ca.coords)#
        addObjectToScene(getCurrentScene(),Spline,parent=parent)        
    if mat == None : mat = c4d.documents.get_active_document().find_material('mat_loft'+molname+'_'+chname)
    while i < (len(ca)):
        pos= float(((i*1.) / len(ca)))
        #print str(pos)+" %"  
        #print atoms[i],atoms[i].parent,hasattr(atoms[i].parent,'secondarystructure')				      
        if hasattr(ca[i].parent,'secondarystructure') : ssname=ca[i].parent.secondarystructure.name
        else : ssname="Coil"
        dshape=SSShapes[ssname[:4]]#ssname[:4]
        #mx =getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
        #have to place the shape on the spline    
        if shape2dmorph :
            shape.append(morph2dObject(dshape+str(i),shape2dmorph[dshape],shape2dmorph['Heli']))
            path=shape[i].make_tag(Follow_PATH)
            path[1001] = Spline
            path[1000] = 0#tangantial
            path[1003] = pos
            path[1007] = 2#1		axe	            
            #shape[-1].set_mg(mx)
        else :
            #print str(prev),ssname         
            #if prev != None: #end of loop 
            #    if ssname[:4] != prev[:4]: #newSS need transition
            #        if not instance : shape.append(makeShape(SSShapes[prev[:4]],prev))
            #        else : shape.append(instanceShape(prev,shapes2d))                    
            #        #shape[-1].set_mg(mx)
            #        path=shape[-1].make_tag(Follow_PATH)
            #        path[1001] = Spline
            #        path[1000] = 1    
            #        path[1003] = pos                
            if not instance : shape.append(makeShape(dshape,ssname))
            else : shape.append(instanceShape(ssname,shapes2d))
            path=shape[i].make_tag(Follow_PATH)
            path[1001] = Spline
            path[1000] = 0  
            path[1003] = pos                                           
            path[1007] = 2#1
            #shape[-1].set_mg(mx)        
        if i >=1  : 
            laenge,mx=getStickProperties(ca[i].coords,ca[i-1].coords)
            #if i > len(o) : laenge,mx=getStickProperties(ca[i].coords,o[i-1].coords)
            #else :laenge,mx=getStickProperties(ca[i].coords,o[i].coords)
            shape[i].set_mg(mx)	
        prev=ssname
        i=i+1
    laenge,mx=getStickProperties(ca[0].coords,ca[1].coords) 
    #laenge,mx=getStickProperties(ca[0].coords,o[0].coords) 
    shape[0].set_mg(mx)  		
    if mat != None:
        prev=None
        #i=(len(shape))
        i=0
        while i < (len(shape)):
            ssname=shape[i].get_name()
            #print ssname            
            pos=1-((((i)*100.)/len(shape))/100.0)
            if pos < 0 : pos = 0.
            #print pos
            #change the material knote according ss color / cf atom color...
            #col=atoms[i].colors['secondarystructure']
            col=c4dColor(SSColor[ssname])
            nc=c4d.Vector(col[0],col[1],col[2])
            ncp=c4d.Vector(0,0,0)            
            if prev != None :
                pcol=c4dColor(SSColor[prev])
                ncp=c4d.Vector(pcol[0],pcol[1],pcol[2])        
            #print col
            #print ssname[:4]
            #print prev
            if ssname != prev : #new ss
                grad=mat[8000][1007]    
            #iK=iK+1
                nK=grad.get_knot_count()
            #print "knot count ",nK,iK                
                if iK >= nK :
                    #print "insert ",pos,nK
                    #print "grad.insert_knot(c4d.Vector("+str(col[0])+str(col[1])+str(col[2])+"), 1.0, "+str(pos)+",0.5)"
                    if prev != None :
                        grad.insert_knot(ncp, 1.0, pos+0.01,0.5)
                        iK=iK+1                                                
                    grad.insert_knot(nc, 1.0, pos-0.01,0.5)
                    #grad.insert_knot(ncp, 1.0, pos+0.1,0.5)                    
                    iK=iK+1                    
                else :
                    #print "set ",iK,pos    
                    if prev != None :grad.set_knot(iK-1,ncp,1.0,pos,0.5)                            
                    grad.set_knot(iK,nc,1.0,pos,0.5)
                mat[8000][1007]=grad
            prev=ssname
            mat.message(c4d.MSG_UPDATE)
            i=i+1            
    #mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
    #if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[shape],shape2dlist['Heli']))
    return shape

def update_2dsheet(shapes,builder,loft):
    dicSS={'C':'Coil','T' : 'Turn', 'H':'Heli','E':'Stra','P':'Coil'}
    shape2D=getShapes2D()
    for i,ss in enumerate(builder):
        if     shapes[i].get_name() != dicSS[ss]:
            shapes[i][1001]=shape2D[dicSS[ss]]#ref object
            shapes[i].set_name(dicSS[ss])    

    texture = loft.get_tags()[0]
    mat=texture[1010]
    grad=mat[8000][1007]
    grad.delete_all_knots()
    mat[8000][1007]=grad

    prev=None
    i = 0
    iK = 0    
    while i < (len(shapes)):
            ssname=shapes[i].get_name()
            #print ssname            
            pos=1-((((i)*100.)/len(shapes))/100.0)
            if pos < 0 : pos = 0.
            #print pos
            #change the material knote according ss color / cf atom color...
            #col=atoms[i].colors['secondarystructure']
            col=c4dColor(SSColor[ssname])
            nc=c4d.Vector(col[0],col[1],col[2])
            ncp=c4d.Vector(0,0,0)            
            if prev != None :
                pcol=c4dColor(SSColor[prev])
                ncp=c4d.Vector(pcol[0],pcol[1],pcol[2])        
            #print col
            #print ssname[:4]
            #print prev
            if ssname != prev : #new ss
                grad=mat[8000][1007]    
            #iK=iK+1
                nK=grad.get_knot_count()
            #print "knot count ",nK,iK                
                if iK >= nK :
                    #print "insert ",pos,nK
                    #print "grad.insert_knot(c4d.Vector("+str(col[0])+str(col[1])+str(col[2])+"), 1.0, "+str(pos)+",0.5)"
                    if prev != None :
                        grad.insert_knot(ncp, 1.0, pos+0.01,0.5)
                        iK=iK+1                                                
                    grad.insert_knot(nc, 1.0, pos-0.01,0.5)
                    #grad.insert_knot(ncp, 1.0, pos+0.1,0.5)                    
                    iK=iK+1                    
                else :
                    #print "set ",iK,pos    
                    if prev != None :grad.set_knot(iK-1,ncp,1.0,pos,0.5)                            
                    grad.set_knot(iK,nc,1.0,pos,0.5)
                mat[8000][1007]=grad
            prev=ssname
            mat.message(c4d.MSG_UPDATE)
            i=i+1            
 


    
def piecewiseLinearInterpOnIsovalue(x):
            """Piecewise linear interpretation on isovalue that is a function
            blobbyness.
            """
            import sys
            X = [-3.0, -2.5, -2.0, -1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]
            Y = [0.6565, 0.8000, 1.0018, 1.3345, 1.5703, 1.8554, 2.2705, 2.9382, 4.1485, 7.1852, 26.5335]
            if x<X[0] or x>X[-1]:
                print "WARNING: Fast approximation :blobbyness is out of range [-3.0, -0.1]"
                return None
            i = 0
            while x > X[i]:
                i +=1
            x1 = X[i-1]
            x2 = X[i]
            dx = x2-x1
            y1 = Y[i-1]
            y2 = Y[i]
            dy = y2-y1
            return y1 + ((x-x1)/dx)*dy
    
def coarseMolSurface(mv,molFrag,XYZd,isovalue=7.0,resolution=-0.3,padding=0.0,name='CoarseMolSurface'):
    """
    will create a DejaVu indexedPolygon of a coarse molecular surface, the function is build as the implemented node
    in vision.
    geom<-    coarseMolSurface()
    mv : the molecular viewer embeded
    molFrag : the molkit node used to build the surface
    XYZd    : the dimension of the grid (X,Y,Z)
    etc...
    """
    from MolKit.molecule import Atom
    atoms = molFrag.findType(Atom)
    coords = atoms.coords
    radii = atoms.vdwRadius
    from UTpackages.UTblur import blur
    import numpy.oldnumeric as Numeric
    volarr, origin, span = blur.generateBlurmap(coords, radii, XYZd,resolution, padding = padding)
    volarr.shape = (XYZd[0],XYZd[1],XYZd[2])
    volarr = Numeric.ascontiguousarray(Numeric.transpose(volarr), 'f')
    #print volarr
    
    weights =  Numeric.ones(len(radii), typecode = "f")
    h = {}
    from Volume.Grid3D import Grid3DF
    maskGrid = Grid3DF( volarr, origin, span , h)
    h['amin'], h['amax'],h['amean'],h['arms']= maskGrid.stats()
    #(self, grid3D, isovalue=None, calculatesignatures=None, verbosity=None)
    from UTpackages.UTisocontour import isocontour
    isocontour.setVerboseLevel(0)
    data = maskGrid.data
    
    origin = Numeric.array(maskGrid.origin).astype('f')
    stepsize = Numeric.array(maskGrid.stepSize).astype('f')
    # add 1 dimension for time steps amd 1 for multiple variables
    if data.dtype.char!=Numeric.Float32:
        #print 'converting from ', data.dtype.char
        data = data.astype('f')#Numeric.Float32)
    newgrid3D = Numeric.ascontiguousarray(Numeric.reshape( Numeric.transpose(data),(1, 1)+tuple(data.shape) ), data.dtype.char)
    ndata = isocontour.newDatasetRegFloat3D(newgrid3D, origin, stepsize)
    isoc = isocontour.getContour3d(ndata, 0, 0, isovalue,isocontour.NO_COLOR_VARIABLE)
    vert = Numeric.zeros((isoc.nvert,3)).astype('f')
    norm = Numeric.zeros((isoc.nvert,3)).astype('f')
    col = Numeric.zeros((isoc.nvert)).astype('f')
    tri = Numeric.zeros((isoc.ntri,3)).astype('i')
    isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)
    #print "###VERT###"
    #print vert
    #print "###norm###"
    #print norm
    #print "###tri###"
    #print tri
    if maskGrid.crystal:
            vert = maskGrid.crystal.toCartesian(vert)
                
    from DejaVu.IndexedGeom import IndexedGeom
    from DejaVu.IndexedPolygons import IndexedPolygons
    g=IndexedPolygons(name=name)

    inheritMaterial = None
    g.Set(vertices=vert, faces=tri, materials=None, 
              tagModified=False, 
              vnormals=norm, inheritMaterial=inheritMaterial )
    #g.fullName = name
    #print "bind"    
    mv.bindGeomToMolecularFragment(g, atoms, log=0)
    #print len(g.getVertices())
    #print g
    return g
        #GeometryNode.textureManagement(self, image=image, textureCoordinates=textureCoordinates)

def makeLines(name,points,faces,parent=None):
    rootLine = newEmpty(name)
    addObjectToScene(getCurrentScene(),rootLine,parent=parent)
    spline=c4d.BaseObject(c4d.Ospline)
    #spline[1000]=type
    #spline[1002]=close
    spline.set_name(name+'mainchain')
    spline.resize_object(int(len(points)))
    for i,p in enumerate(points):
        spline.set_point(i, c4dv(p))
    addObjectToScene(getCurrentScene(),spline,parent=rootLine)
    spline=c4d.BaseObject(c4d.Ospline)
    #spline[1000]=type
    #spline[1002]=close
    spline.set_name(name+'sidechain')
    spline.resize_object(int(len(points)))
    for i,p in enumerate(points):
        spline.set_point(i, c4dv(p))
    addObjectToScene(getCurrentScene(),spline,parent=rootLine)    

def updateLines(lines, chains=None):
	#lines = getObject(name)	
	#if lines == None or chains == None:
	    #print lines,chains	
	    parent = getObject(chains.full_name())	
	    #print parent		
	    bonds, atnobnd = chains.residues.atoms.bonds
	    indices = map(lambda x: (x.atom1._bndIndex_,
								x.atom2._bndIndex_), bonds)
	    updatePoly(lines,vertices=chains.residues.atoms.coords,faces=indices)
		
def editLines(molecules,atomSets):
    for mol, atms, in map(None, molecules, atomSets):
        #check if line exist
        for ch in mol.chains:
            parent = getObject(ch.full_name())
            lines = getObject(ch.full_name()+'_line')
            if lines == None :
                bonds, atnobnd = ch.residues.atoms.bonds
                indices = map(lambda x: (x.atom1._bndIndex_,
                                         x.atom2._bndIndex_), bonds)

                lines = createsNmesh(ch.full_name()+'_line',ch.residues.atoms.coords,
                                     None,indices)
                addObjectToScene(getCurrentScene(),lines[0]	,parent=parent)
            else : #need to update
                updateLines(lines, chains=ch)
				

def PointCloudObject(name,**kw):
    #print "cloud", len(coords)
    coords=kw['vertices']
    nface = 0	
    if kw.has_key("faces"):
        nface = len(kw['faces'])	
    obj= c4d.PolygonObject(len(coords), nface)
    obj.set_name(name)
    for k,v in enumerate(coords) :
        obj.set_point(k, c4dv(v))
    return obj

def PolygonColorsObject(name,vertColors):
      obj= c4d.PolygonObject(len(vertColors), len(vertColors)/2.)
      obj.set_name(name+'_color')
      for k,v in enumerate(vertColors) :   
          obj.set_point(k, c4dv(v))
      return obj

def updatePoly(polygon,faces=None,vertices=None):
    if type(polygon) == str:
        polygon = getObject(polygon)
    if polygon == None : return		
    if vertices != None:
        for k,v in enumerate(vertices) :
            polygon.set_point(k, c4dv(v))
    if faces != None:
        for g in range(len(faces)):
            A = int(faces[g][0])
            B = int(faces[g][1])
            if len(faces[g])==2 :
                C = B
                D = B
            elif len(faces[g])==3 : 
                C = int(faces[g][2])
                D = C
            elif len(faces[g])==4 : 
                C = int(faces[g][2])
                D = int(faces[g][3])
          #print A
            polygon.set_polygon(id=g, polygon=[ A, B, C, D ])
    polygon.message(c4d.MSG_UPDATE)

def redoPoly(poly,vertices,faces,proxyCol=False,colors=None,parent=None,mol=None):
    doc = getCurrentScene()
    doc.set_active_object(poly)
    name=poly.get_name()
    texture = poly.get_tags()[0]
    c4d.call_command(100004787) #delete the obj
    obj=createsNmesh(name,vertices,None,faces,smooth=False,material=texture[1010],proxyCol=proxyCol)
    addObjectToScene(doc,obj[0],parent=parent)
    if proxyCol and colors!=None:
        pObject=getObject(name+"_color")
        doc.set_active_object(pObject)
        c4d.call_command(100004787) #delete the obj    
        pObject=PolygonColorsObject(name,colors)
        addObjectToScene(doc,pObject,parent=parent)

def reCreatePoly(poly,vertices,faces,proxyCol=False,colors=None,parent=None,mol=None):
    doc = getCurrentScene()
    doc.set_active_object(poly)
    name=poly.get_name()
    texture = poly.get_tags()[0]
    c4d.call_command(100004787) #delete the obj
    obj=createsNmesh(name,vertices,None,faces,smooth=False,material=texture[1010],proxyCol=proxyCol)
    addObjectToScene(doc,obj[0],parent=parent)
    if proxyCol and colors!=None:
        pObject=getObject(name+"_color")
        doc.set_active_object(pObject)
        c4d.call_command(100004787) #delete the obj    
        pObject=PolygonColorsObject(name,colors)
        addObjectToScene(doc,pObject,parent=parent)
	
"""def UVWColorTag(obj,vertColors):
      uvw=obj.make_tag(c4d.Tuvw)
    
      obj= c4d.PolygonObject(len(vertColors), len(vertColors)/2.)
      obj.set_name(name+'_color')
      k=0
      for v in vertColors :
          print v      
          obj.set_point(k, c4d.Vector(float(v[0]), float(v[1]), float(v[2])))
          k=k+1
      return obj
"""

def updateMesh_bug(g):
    obj=g.obj
    oldN=obj.get_point_count()
    vertices=g.getVertices()
    faces=g.getFaces()    
    newN=len(vertices)  
    if newN != oldN : 
        obj.resize_object(newN,len(faces))
        k=0
        for v in vertices :
            #print v      
            obj.set_point(k, c4d.Vector(float(v[2]), float(v[1]), float(v[0])))
            k=k+1
        for g in range(len(faces)):
            A = int(faces[g][0])
            B = int(faces[g][1])
            C = int(faces[g][2])
            if len(faces[g])==3 : D = C
            elif len(faces[g])==4 : D = int(faces[g][3])
            #print A
            obj.set_polygon(id=g, polygon=[ A, B, C, D ])    
    obj.message(c4d.MSG_UPDATE)

def updateMesh(g,proxyCol=False,parent=None,mol=None):
    doc = getCurrentScene()
    doc.set_active_object(g.obj)
    name=g.obj.get_name()   
    texture = g.obj.get_tags()[0]
    c4d.call_command(100004787) #delete the obj
    vertices=g.getVertices()
    faces=g.getFaces()
    #if     proxyCol : o=PolygonColorsObject
    obj=createsNmesh(name,vertices,None,faces,smooth=False,material=texture[1010],proxyCol=proxyCol)
    addObjectToScene(doc,obj[0],parent=parent)
    #obj.message(c4d.MSG_UPDATE)
    g.obj=obj[0]
    if proxyCol :
        colors=mol.geomContainer.getGeomColor(g.name)
        if hasattr(g,'color_obj'):
            pObject=g.color_obj#getObject(name+"_color")
            doc.set_active_object(pObject)
            c4d.call_command(100004787) #delete the obj 
        pObject=PolygonColorsObject(name,colors)
        g.color_obj=pObject
        addObjectToScene(doc,pObject,parent=parent)
		
def polygons(name,proxyCol=False,smooth=False,color=None, material=None, **kw):
      vertices = kw["vertices"]
      faces = kw["faces"]
      normals = kw["normals"]
      frontPolyMode='fill'
      if kw.has_key("frontPolyMode"):	  
          frontPolyMode = kw["frontPolyMode"]
      if kw.has_key("shading") :  
          shading=kw["shading"]#'flat'
      if frontPolyMode == "line" : #wire mode
          material = getCurrentScene().find_material("wire")
          if material == None:
              material = addMaterial("wire",(0.5,0.5,0.5))		  		  	  	  	    	  
      polygon = c4d.PolygonObject(len(vertices), len(faces))
      polygon.set_name(name)      
      k=0
      for v in vertices :
          #print v      
          polygon.set_point(k, c4dv(v))
          #polygon.set_point(k, c4d.Vector(float(v[0]), float(v[1]), float(v[2])))
          k=k+1
      for g in range(len(faces)):
          A = int(faces[g][0])
          B = int(faces[g][1])
          if len(faces[g])==2 :
            C = B
            D = B
          elif len(faces[g])==3 : 
            C = int(faces[g][2])
            D = C
          elif len(faces[g])==4 : 
            C = int(faces[g][2])
            D = int(faces[g][3])
          #print A
          polygon.set_polygon(id=g, polygon=[ A, B, C, D ])    
      polygon.make_tag(c4d.Tphong) #shading ?
      # create a texture tag on the PDBgeometry object
      if not proxyCol : 
          texture = polygon.make_tag(c4d.Ttexture)
          #create the dedicayed material
          if material == None :
              if name[:4] in SSShapes.keys() : texture[1010] =    getCurrentScene().find_material(name[:4])        
              else : texture[1010] = addMaterial(name,color[0])
          else : texture[1010] = material
      return polygon

        
def createsNmesh(name,vertices,vnormals,faces,smooth=False,material=None,proxyCol=False,color=[[1,0,0],]):
      PDBgeometry = polygons(name, vertices=vertices,normals=vnormals,faces=faces,material=material,color=color,smooth=smooth,proxyCol=proxyCol)
      return [PDBgeometry]

def instancePolygon(name, matrices=None, mesh=None,parent=None):
      if matrices == None : return None
      if mesh == None : return None
      instance = []	  
      #print len(matrices)#4,4 mats
      for mat in matrices:
          instance.append(c4d.BaseObject(INSTANCE))
          instance[-1][1001]=mesh
          mx = matrix2c4dMat(mat)
          instance[-1].set_mg(mx)
          AddObject(instance[-1],parent=parent)
		  #instance[-1].make_tag(c4d.Ttexture)
      return instance
	  		    
def colorMaterial(mat,col):
    #mat input is a material name or a material object
    #color input is three rgb value array
    doc= c4d.documents.get_active_document()
    if type(mat)==str: mat = doc.find_material(mat)
    mat[2100] = c4d.Vector(col[0],col[1],col[2])

def changeMaterialSchemColor(typeMat):
     if typeMat == "ByAtom":
          for atms in AtomElements.keys() : colorMaterial(atms,AtomElements[atms])
     elif typeMat == "AtomsU" :
          for atms in DavidGoodsell.keys() :colorMaterial(atms,DavidGoodsell[atms])
              #if (atms == "P") or (atms == "A") or (atms == "CA"): colorMaterial(atms[0],AtomElements[atms])
              #else : 
              #colorMaterial(atms,DavidGoodsell[atms])
     elif typeMat == "ByResi":
          for res in RasmolAmino.keys(): colorMaterial(res,RasmolAmino[res])
     elif typeMat == "Residu":
          for res in Shapely.keys(): colorMaterial(res,Shapely[res])
     elif typeMat == "BySeco":
          for ss in SecondaryStructureType.keys(): colorMaterial(ss[0:4],SecondaryStructureType[ss])
     else : pass

def splitName(name):
    if name[0] == "T" : #sticks name.. which is "T_"+chname+"_"+Resname+"_"+atomname+"_"+atm2.name\n'
        tmp=name.split("_")
        return ["T","",tmp[1],tmp[2][0:3],tmp[2][3:],tmp[3]]
    else :
        tmp=name.split(":")
        indice=tmp[0].split("_")[0]
        molname=tmp[0].split("_")[1]
        chainname=tmp[1]
        residuename=tmp[2][0:3]
        residuenumber=tmp[2][3:]
        atomname=tmp[3]
        return [indice,molname,chainname,residuename,residuenumber,atomname]

def checkChangeMaterial(o,typeMat,atom=None,parent=None,color=None):
        #print typeMat
        #print "checkChangeMaterial"
        doc= c4d.documents.get_active_document()
        Material=getMaterials()
        matliste=getMaterialListe()
        ss="Helix"
        ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']        
        if atom != None :
            res=atom.getParentOfType(Residue)
            if hasattr(res,"secondarystructure") : ss=res.secondarystructure.name
        #mats=o.getMaterials()
        names=splitName(o.get_name())
        #print names        
        texture = o.get_tags()[0]
        #print texture
        matname=texture[1010][900]
        #print matname
        changeMaterialSchemColor(typeMat)
        if typeMat == "" or typeMat == "ByProp" : #color by color
            if parent != None : requiredMatname = 'mat'+parent#.get_name() #exemple mat_molname_cpk
            else : requiredMatname = 'mat'+o.get_name()#exemple mat_coil1a_molname
            if typeMat == "ByProp": requiredMatname = 'mat'+o.get_name()#exemple mat_coil1a_molname
            #print parent.name,o.name,requiredMatname
            if matname != requiredMatname : 
                #print requiredMatname
                rMat=doc.find_material(requiredMatname)                
                if rMat is None : rMat=addMaterial(requiredMatname,color)
                else : colorMaterial(rMat,color)
                texture[1010] = rMat#doc.find_material(requiredMatname)
            else : colorMaterial(requiredMatname,color)                
        if typeMat == "ByAtom" :
            if matname not in AtmRadi.keys() : #switch to atom materials
                    texture[1010]=Material["atoms"][names[5][0]]
        if typeMat == "AtomsU" :
            #if matname not in AtmRadi.keys() : #switch to atom materials
                    texture[1010]=Material["atoms"][lookupDGFunc(atom)]
        elif typeMat == "ByResi" :
            if matname not in ResidueSelector.r_keyD.keys() : #switch to residues materials
                    #print matname, names[3],Material["residus"]
                    if names[3] not in ResidueSelector.r_keyD.keys(): names[3]='hetatm'            
                    texture[1010]=Material["residus"][names[3]]
        elif typeMat == "BySeco" :
            if matname not in ssk : #switch to ss materials
                    texture[1010]=Material["ss"][ss[0:4]]

def checkChangeStickMaterial(o,typeMat,atoms,parent=None,color=None):
        #print typeMat
        #print "checkChangeMaterial"
        doc=getCurrentScene()
        Material=getMaterials()
        ss="Helix"
        ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']                
        res=atoms[0].getParentOfType(Residue)
        if hasattr(res,"secondarystructure") : ss=res.secondarystructure.name
        names=["T","noname","noname",res.name[0:3],res.name[:3],atoms[0].name[0]]        

        texture = o.get_tags()[1]
        #print texture
        matname=texture[1010][900]
        #print matname
        if typeMat == "" or typeMat == "ByProp": #color by color
            if parent != None : requiredMatname = 'mat'+parent#.get_name() #exemple mat_molname_cpk
            else : requiredMatname = 'mat'+o.get_name()#exemple mat_coil1a_molname
            if typeMat == "ByProp": requiredMatname = 'mat'+o.get_name()#exemple mat_coil1a_molname
            #print parent.name,o.name,requiredMatname
            if matname != requiredMatname : 
                #print requiredMatname
                rMat=doc.find_material(requiredMatname)                
                if rMat is None : rMat=addMaterial(requiredMatname,color)
                else : colorMaterial(rMat,color)
                texture[1010] = rMat#doc.find_material(requiredMatname)
            else : colorMaterial(requiredMatname,color)                        
        if typeMat == "ByAtom" or typeMat == "AtomsU" :
            if matname not in Material["sticks"].keys() : #switch to atom materials
                    texture[1010]=Material["sticks"][atoms[0].name[0]+atoms[1].name[0]]
        elif typeMat == "ByResi" :
            if matname not in ResidueSelector.r_keyD.keys() : #switch to residues materials
                    #print matname, names[3],Material["residus"]            
                    texture[1010]=Material["residus"][names[3]]
        elif typeMat == "BySeco" :
            if matname not in ssk : #switch to ss materials
                    texture[1010]=Material["ss"][ss[0:4]]
      
def blenderColor(col):
        #blender color rgb range[0-1]
        if max(col)<=1.0: col = map( lambda x: x*255, col)
        return col
        
def c4dColor(col):
        #c4d color rgb range[0-1]
        if max(col)>1.0: col = map( lambda x: x/255., col)
        return col
        
def changeColor(geom,colors,perVertex=False,proxyObject=None,doc=None,pb=False):
    #print 'changeColor',len(colors)
    if hasattr(geom,'obj'):obj=geom.obj
    else : obj=geom
    #verfify perVertex flag
    unic=False
    ncolor=colors[0]    
    if len(colors)==1 :
        unic=True
        #print unic
        ncolor = c4dColor(colors[0])
    if proxyObject != None :#and not unic: 
      #print "not unic"    
      if len(colors) != obj.get_point_count() and len(colors) == obj.get_polygon_count(): perVertex=False
      if len(colors) == obj.get_point_count() and len(colors) != obj.get_polygon_count(): perVertex=True
      i=0    
      for g in (obj.get_polygons()):#faces
        if not unic and not perVertex : ncolor = c4dColor(colors[i])
        else : ncolor = c4dColor(colors[0])        
        for j in g:#vertices
            if not unic and perVertex : ncolor = c4dColor(colors[j])
            #print ncolor            
            proxyObject.set_point(j, c4d.Vector(float(ncolor[0]), float(ncolor[1]), float(ncolor[2])))
            #now how update the material tag of the object using C++ plugin??
      proxyObject.message(c4d.MSG_UPDATE)
      #need to update but how: maybe number of selected object: if one create eerything/if two just update the values! in the doit function !
      if doc == None : doc = getCurrentScene()
      doc.set_active_object(obj)
      #doc.set_active_object(proxyObject,c4d.SELECTION_ADD)
      c4d.call_command(1023892)
    #elif proxyObject != None and unic :
    #    print "unic"    
    #    print proxyObject.get_tags()
    #    print ncolor
    #    texture = proxyObject.get_tags()[0] #should be the textureFlag
    #    texture[1010][2100] = c4d.Vector((ncolor[0]),(ncolor[1]),(ncolor[2]))
    else :    
        #print obj.get_tags()
        #print ncolor
        texture = obj.get_tags()[0] #should be the textureFlag
        texture[1010][2100] = c4d.Vector((ncolor[0]),(ncolor[1]),(ncolor[2]))
    
def changeSticksColor(geom,colors,type=None,indice=0,perVertex=False,proxyObject=None,doc=None):
    #need 2color per stick, will try material per selection.
    #defeine sel1/sel2 of each tube, and call material from listMAterial
    #print 'changeSticksColor',(colors)
    #verfify perVertex flag
    if hasattr(geom,'obj'):obj=geom.obj[indice]
    else : obj=geom
    #print colors
    unic=False
    #ncolor=colors[0]    
    if len(colors)==1 :
        unic=True
        #print unic
        ncolor = c4dColor(colors[0])
    texture = obj.get_tags()[1] #should be the textureFlag
    #print texture[1010],texture[1010][900]
    if texture[1010][8000] is None or texture[1010][900] in ResidueSelector.r_keyD.keys() or  texture[1010][900].find("selection") != -1 or  texture[1010][900] in SSShapes.keys() :
        ncolor=    c4dColor(colors[0])
        texture[1010][2100] = c4d.Vector((ncolor[0]),(ncolor[1]),(ncolor[2]))
    else :
        grad=texture[1010][8000][1007]# = c4d.Vector((ncolor[0]),(ncolor[1]),(ncolor[2]))
        ncolor = c4dColor(colors[0])
        #print ncolor,obj.get_name()
        grad.set_knot(0,c4d.Vector((ncolor[0]),(ncolor[1]),(ncolor[2])),1.0,0.5,0.5)
        ncolor = c4dColor(colors[1])
        #print ncolor
        grad.set_knot(1,c4d.Vector((ncolor[0]),(ncolor[1]),(ncolor[2])),1.0,0.5,0.5) #col,bright,pos,bias
        texture[1010][8000][1007]=grad    

    
def Armature(basename, x,doc=None,root=None):
    bones=[]
    if doc != None:
        parent = c4d.BaseObject(c4d.Onull)
        parent.set_name(basename)
        addObjectToScene(doc,parent,parent=root)
    for j in range(len(x)):    
        at=x[j]
        atN=at.name
        fullname = at.full_name()
        atC=at._coords[0]
        rad=at.vdwRadius
        bones.append(c4d.BaseObject(BONE))
        bones[j].set_name(fullname.replace(":","_"))
        relativePos=Numeric.array(atC)
        if j>0 :
            patC=Numeric.array((x[j-1]._coords[0]))        
            for i in range(3):relativePos[i]=(atC[i]-patC[i])
        bones[j].set_pos(c4d.Vector(float(relativePos[2]),float(relativePos[1]),float(relativePos[0])))
        if doc != None :
             if j==0 : addObjectToScene(doc,bones[j],parent=parent)
             else : addObjectToScene(doc,bones[j],parent=bones[j-1])
    return bones

def box(name,center=[0.,0.,0.],size=[1.,1.,1.],cornerPoints=None,visible=1):
    #import numpy
    box=c4d.BaseObject(c4d.Ocube)#Object.New('Mesh',name)
    box.set_name(name)
    if cornerPoints != None :
        for i in range(3):
            size[i] = cornerPoints[1][i]-cornerPoints[0][i]
	center=(numpy.array(cornerPoints[0])+numpy.array(cornerPoints[1]))/2.
    box.set_pos(c4dv(center))
    box[1100] = c4dv(size)
    #aMat=addMaterial("wire")
    texture = box.make_tag(c4d.Ttexture)
    mat = getCurrentScene().find_material("wire")
    if mat == None:
        texture[1010] = addMaterial("wire",(0.5,0.5,0.5))
        texture[1010][2003] = 1 #transparancy
        texture[1010][2401] = 0.80 #value
    else :
        texture[1010] = mat
    return box

    
#################################################################################
def setupAmber(mv,name,mol,prmtopfile, type,add_Conf=True,debug = False):
    if not hasattr(mv,'setup_Amber94'):
        mv.browseCommands('amberCommands', package='Pmv')
    from Pmv import amberCommands
    amberCommands.Amber94Config = {}
    amberCommands.CurrentAmber94 = {}

    from Pmv.hostappInterface import comput_util as C
    mv.energy = C.EnergyHandler(mv)
    mv.energy.amber = True
    mv.energy.mol = mol
    mol.prname = prmtopfile
    mv.energy.name=name	
    def doit():
        c1 = mv.minimize_Amber94
        c1(name, dfpred=10.0, callback_freq='10', callback=1, drms=1e-06, maxIter=10, log=0)
    mv.energy.doit=doit
    if add_Conf:
            confNum = 1
            # check number of conformations available
            current_confNum = len(mol.allAtoms[0]._coords) -1
            if  current_confNum < confNum:
                # we need to add conformation
                for i in range((confNum - current_confNum)):
                    mol.allAtoms.addConformation(mol.allAtoms.coords)
                    # uses the conformation to store the transformed data
                    #mol.allAtoms.updateCoords(vt,ind=confNum)
                    # add arconformationIndex to top instance ( molecule)
                    mol.cconformationIndex = confNum
    mv.setup_Amber94(mol.name+":",name,prmtopfile,indice=mol.cconformationIndex)
    mv.minimize_Amber94(name, dfpred=10.0, callback_freq='10', callback=1, drms=1e-06, maxIter=100., log=0)	
	
def cAD3Energies(mv,mols,atomset1,atomset2,add_Conf=False,debug = False):
    from Pmv.hostappInterface import comput_util as C
    mv.energy = C.EnergyHandler(mv)
    mv.energy.add(atomset1,atomset2)#type=c_ad3Score by default
    #mv.energy.add(atomset1,atomset2,type = "ad4Score")
    if add_Conf:
        confNum = 1
        for mol in mols:
            # check number of conformations available
            current_confNum = len(mol.allAtoms[0]._coords) -1
            if  current_confNum < confNum:
                # we need to add conformation
                for i in range((confNum - current_confNum)):
                    mol.allAtoms.addConformation(mol.allAtoms.coords)
                    # uses the conformation to store the transformed data
                    #mol.allAtoms.updateCoords(vt,ind=confNum)
                    # add arconformationIndex to top instance ( molecule)
                    mol.cconformationIndex = confNum
    if debug :
        s1=c4d.BaseObject(c4d.Osphere)
        s1.set_name("sphere_rec")
        s1[PRIM_SPHERE_RAD]=2.
        s2=c4d.BaseObject(c4d.Osphere)
        s2.set_name("sphere_lig")
        s2[PRIM_SPHERE_RAD]=2.
        addObjectToScene(getCurrentScene(),s1)
        addObjectToScene(getCurrentScene(),s2)        
        #label
        label = newEmpty("label")
        label.make_tag(LOOKATCAM)
        addObjectToScene(getCurrentScene(),label)
        text1 =  c4d.BaseObject(TEXT)
        text1.set_name("score")
        text1[2111] = "score : 0.00"
        text1[2115] = 5.
        text1[904,1000] = 3.14
        text1[903,1001] = 4.
        text2 =  c4d.BaseObject(TEXT)
        text2.set_name("el")
        text2[2111] = "el : 0.00"
        text2[2115] = 5.0
        text2[904,1000] = 3.14
        text3 =  c4d.BaseObject(TEXT)
        text3.set_name("hb")
        text3[2111] = "hb : 0.00"
        text3[2115] = 5.0
        text3[904,1000] = 3.14
        text3[903,1001] = -4.
        text4 =  c4d.BaseObject(TEXT)
        text4.set_name("vw")
        text4[2111] = "vw : 0.00"
        text4[2115] = 5.0
        text4[904,1000] = 3.14
        text4[903,1001] = -8.
        text5 =  c4d.BaseObject(TEXT)
        text5.set_name("so")
        text5[2111] = "so : 0.00"
        text5[2115] = 5.0
        text5[904,1000] = 3.14
        text5[903,1001] = -12.
        addObjectToScene(getCurrentScene(),text1,parent=label)
        addObjectToScene(getCurrentScene(),text2,parent=label)
        addObjectToScene(getCurrentScene(),text3,parent=label)
        addObjectToScene(getCurrentScene(),text4,parent=label)
        addObjectToScene(getCurrentScene(),text5,parent=label)       
    #return energy

def get_nrg_score(energy,display=True):
    #print "get_nrg_score"
    status = energy.compute_energies()
    #print status
    if status is None: return
    #print energy.current_scorer
    #print energy.current_scorer.score
    vf = energy.viewer
    text = getObject("score")
    if text != None :
        text[2111] = "score :"+str(energy.current_scorer.score)[0:5]
        for i,term in enumerate(['el','hb','vw','so']):
            labelT = getObject(term)
            labelT[2111] = term+" : "+str(energy.current_scorer.scores[i])[0:5]
    #should make multi label for multi terms    
    # change color of ligand with using scorer energy
    if display:
            # change selection level to Atom
            prev_select_level = vf.getSelLev()
            vf.setSelectionLevel(Atom,log=0)
            # 
            scorer = energy.current_scorer
            atomSet = vf.expandNodes(scorer.mol2.name).findType(Atom) # we pick the ligand
            property = scorer.prop
            if hasattr(atomSet,scorer.prop):
                mini = min(getattr(atomSet,scorer.prop))
                #geomsToColor = vf.getAvailableGeoms(scorer.mol2)
                vf.colorByProperty(atomSet,['cpk'],property,
                                        mini=-1.0, maxi=1.0,
                                        colormap='rgb256',log=1)
                # get the geometries of colormap to be display
                #if vf.colorMaps.has_key('rgb256'):
                    #cmg = vf.colorMaps['rgb256']
                    #from DejaVu.ColormapGui import ColorMapGUI
                    #if not isinstance(cmg,ColorMapGUI):
                    #    cmg.read(self.colormap_file)
                    #    self.vf.showCMGUI(cmap=cmg, topCommand=0)
                    #    cmg = self.vf.colorMaps['rgb256']
                    #    cmg.master.withdraw()
                        # create the color map legend
                    #    cmg.createCML()
                        
                    #cml = cmg.legend
                    #cml.Set(visible=True,unitsString='kcal/mol')
                    #if cml not in self.geom_without_pattern:
                    #    self.geom_without_pattern.append(cml)
#################################################################################
def c4dMat2numpy(c4dmat,center=None):
    """a c4d matrice is 
    v1 	X-Axis
    v2 	Y-Axis
    v3 	Z-Axis
    off 	Position
    a numpy matrice is a regular 4x4 matrice (3x3rot+trans)
    """
    import numpy
    import c4d
    #print "ok convertMAtrix"
    from numpy import matrix
    from Pmv.hostappInterface import comput_util as C
    #m = numpy.identity(4).astype('f') 
    #M=matrix(m)
    euler = c4d.tools.matrix_to_hpb(c4dmat) #heading,att,bank need to inverse y/z left/righ hand problem
    #print "euler",euler
    matr = numpy.array(C.eulerToMatrix([euler.x,euler.z,euler.y]))
    #M[0:3,0:3]=matr
    trans = c4dmat.off
    #matr[3]= [trans.x,trans.z,trans.y,1.]
    matr[:3,3] = [trans.x,trans.z,trans.y]
    if center != None :
        matr[3][0] =  matr[3][0] - center[0]
        matr[3][1] =  matr[3][1] - center[1]
        matr[3][2] =  matr[3][2] - center[2]
    M = matrix(matr)
    #print M
    IM = M.I
    return numpy.array(M),numpy.array(IM)
    
def matrix2c4dMat(mat):
	import c4d
	from Pmv.hostappInterface import comput_util as C
	r,t,s = C.Decompose4x4(Numeric.array(mat).transpose().reshape(16,))    	
	#Order of euler angles: heading first, then attitude/pan, then bank
	axis = C.ApplyMatrix(Numeric.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]),r.reshape(4,4))
	#M = matrix(matr)
	#euler = C.matrixToEuler(mat[0:3,0:3])
	#mx=c4d.tools.hpb_to_matrix(c4d.Vector(euler[0],euler[1]+(3.14/2),euler[2]), c4d.tools.ROT_HPB)
	v_1 = c4dv(r.reshape(4,4)[2,:3])
	v_2 = c4dv(r.reshape(4,4)[1,:3])
	v_3 = c4dv(r.reshape(4,4)[0,:3])
	offset = c4dv(t)
	mx = c4d.Matrix(offset,v_1, v_2, v_3)
	#mx.off = offset
	return mx

def updateLigCoord(mol):
    from Pmv.hostappInterface import comput_util as C
    #fake update...reset coord to origin
    mol.allAtoms.setConformation(0)
    #get the transformation
    name = mol.geomContainer.masterGeom.chains_obj[mol.chains[0].name]
    mx = getObject(name).get_ml()
    mat,imat = c4dMat2numpy(mx)
    vt = C.transformedCoordinatesWithMatrice(mol,mat)
    mol.allAtoms.updateCoords(vt,ind=mol.cconformationIndex)
    #coords = mol.allAtoms.coords        
    #mol.allAtoms.updateCoords(coords,ind=mol.cconformationIndex)
    mol.allAtoms.setConformation(0)

def updateMolAtomCoord(mol,index=-1):
    #just need that cpk or the balls have been computed once..
    #balls and cpk should be linked to have always same position
    # let balls be dependant on cpk => contraints? or update
    # the idea : spline/dynamic move link to cpl whihc control balls
    # this should be the actual coordinate of the ligand
    # what about the rc...
    vt = []
    sph = mol.geomContainer.geoms['cpk'].obj
    for name in sph:
        o = getObject(name)
        pos=o.get_mg().off
        vt.append([pos.x,pos.z,pos.y])
	if index == -1 : index = 0	
    mol.allAtoms.updateCoords(vt,ind=index)
    
