# -*- coding: utf-8 -*-
"""
Created on Tue Jul 20 23:03:07 2010

@author: Ludovic Autin
@copyright: Ludovic Autin TSRI 2010

Library of helper function to permit the communication and synchronisation
between a hostapplication and a pmv cession.
Replace Template by the name of the software.
fill the different function using the hostApp API
"""
#Python import
import numpy
import numpy.oldnumeric as Numeric
import sys, os, os.path, struct, math, string
from math import *    
from types import StringType, ListType

#PMV import
import MolKit
from MolKit.molecule import Atom, AtomSet, BondSet, Molecule , MoleculeSet
from MolKit.protein import Protein, ProteinSet, Residue, Chain, ResidueSet,ResidueSetSelector
from MolKit.stringSelector import CompoundStringSelector
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom
from MolKit.protein import Residue

from Pmv.moleculeViewer import MoleculeViewer
from Pmv.displayCommands import BindGeomToMolecularFragment
from Pmv.trajectoryCommands import PlayTrajectoryCommand

#Pmv Color Palette
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import DavidGoodsell, DavidGoodsellSortedKeys
from Pmv.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
from Pmv.pmvPalettes import Shapely
from Pmv.pmvPalettes import SecondaryStructureType    

from Pmv.hostappInterface import Template as epmvTemplate

#host software import
#exple with maya :
#import maya
#from maya import cmds
#import maya.OpenMaya as om

#GLOBAL VARIABLE
VERBOSE=0
DEBUG=1

plugDir=epmvTemplate.__path__[0]

ResidueSelector=ResidueSetSelector()

SSShapes = SSColor = { 'Heli':(238,0,127),
           'Shee':(243,241,14),
           'Coil':(255,255,255),
           'Turn':(60,26,100),
           'Stra':(255,255,0)}


def start(debug=0):
    """
    Return a molecular viewer instance embeded into the host 'template'.
    The function also add usefull command to the molecular viewer that are not
    call automatically

    @type  debug: number
    @param debug: debug mode.
    @rtype:   MoleculeViewer
    @return:  an instance of pmv.
    """
     
    if VERBOSE : print "start PMV - debug ",debug
    mv = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,
                        title='pmv', withShell= 0,verbose=False, gui = False)
    mv.addCommand(BindGeomToMolecularFragment(), 
                  'bindGeomToMolecularFragment', None)
    mv.browseCommands('trajectoryCommands',commands=['openTrajectory'],
                      log=0,package='Pmv')
    mv.addCommand(PlayTrajectoryCommand(),'playTrajectory',None)
    mv.embedInto('maya',debug=debug)
    mv.userpref['Read molecules as']['value']='conformations'
    DEBUG=debug        
    return mv

def update():
    """
    Update the host viewport, ui or gl draw
    This function can't be call in a thread.
    """
    pass
    
def checkName(name):
    """
    Check the name of the molecule/filename to avoid invalid caracter for the 
    host. ie maya didnt support object name starting with number. If a invalid 
    caracter is found, the caracter is removed.

    @type  name: string
    @param name: name of the molecule.
    @rtype:   string
    @return:  corrected name of the molecule.
    """    
    invalid=[] 
    for i in range(9):
        invalid.append(str(i))       
    if name[0] in invalid:
        name= name[1:]    
    return name    

def splitName(name):
    """
    Split the given object name to retrieve the molecular informatio ie molname, 
    chain name, residu name, and atom name

    @type  name: string
    @param name: name of the object.
    @rtype:   string list
    @return:  array of : [indice,molname,chainname,residuename,residuenumber,atomname]
    """    
    #sticks name.. which is "T_"+chname+"_"+Resname+"_"+atomname+"_"+atm2.name\n'
    if name[0] == "T" : 
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

def getObjectName(o):
    """
    Return the name of an host object

    @type  o: hostObject
    @param o: an host object
    @rtype:   string
    @return:  the name of the host object
    """    
    name=""
    return name

def parseObjectName(o):
    """
    Parse a molecular object name to retrieve the molecule hierarchy.
    ie if its cpk/bs return B_MOL:CHAIN:RESIDUE:ATOMS as a list 

    @type  o: hostObject
    @param o: an host object
    @rtype:   string | list of string
    @return:  the molecule hierarchy MOL:CHAIN:RESIDUE:ATOMS or ''
    """
    
    name = getObjectName(o)
    #print "parse ",name
    tmp=name.split("_")
    if len(tmp) == 1 : #no "_" so not cpk (S_) or ball (B_) stick (T_) or Mesh (Mesh_)
        return ""
    else :
        if tmp[0] == "S" or tmp[0] == "B" : #balls or cpk
            hiearchy=tmp[1:] #B_MOL:CHAIN:RESIDUE:ATOMS        
            return hiearchy
    return ""
    
def getCurrentScene():
    """
    Return the current/active working document or scene

    @rtype:   scene
    @return:  the active scene
    """
    pass
    
def getObject(name):
    """
    retrieve an object from his name. 

    @type  name: string
    @param name: request name of an host object
    
    @rtype:   hostObject
    @return:  the object with the requested name or None
    """
    return None
    
def newEmpty(name,location=None,parentCenter=None,**kw):
    """
    Create a new Null Object

    @type  name: string
    @param name: name of the empty
    @type  location: list
    @param location: position of the null object
    @type  parentCenter: list
    @param parentCenter: position of the parent object
    
    @type kw: dictionary
    @param kw: you can add your own keyword
   
    @rtype:   hostObject
    @return:  the null object
    """
    empty=None#
    if location != None :
        if parentCenter != None : 
            location = location - parentCenter
        #set the position of the object to location       
    return empty

def newInstance(name,object,location=None,hostmatrice=None,matrice=None):
    """
    Create a new Instance from another Object

    @type  name: string
    @param name: name of the instance
    @type  object: hostObject
    @param object: the object to herit from   
    @type  location: list/Vector
    @param location: position of the null object
    @type  hostmatrice: list/Matrix 
    @param hostmatrice: transformation matrix in host format
    @type  matrice: list/Matrix
    @param matrice: transformation matrix in epmv/numpy format
   
    @rtype:   hostObject
    @return:  the instance object
    """
    #instance = None#
    #instance parent = object  
    #instance name = name
    if location != None :
        #set the position of instance with location
        pass
    #set the instance matrice
    setObjectMatrix(object,matrice=matrice,hostmatrice=hostmatrice)
    return instance
#alias
setInstance = newInstance

def setObjectMatrix(object,matrice,hostmatrice=None):
    """
    set a matrix to an hostObject

    @type  object: hostObject
    @param object: the object who receive the transformation 
    @type  hostmatrice: list/Matrix 
    @param hostmatrice: transformation matrix in host format
    @type  matrice: list/Matrix
    @param matrice: transformation matrix in epmv/numpy format
    """

    if hostmatrice !=None :
        #set the instance matrice
        pass
    if matrice != None:
        #convert the matrice in host format
        #set the instance matrice
        pass

def concatObjectMatrix(object,matrice,hostmatrice=None):
    """
    apply a matrix to an hostObject

    @type  object: hostObject
    @param object: the object who receive the transformation
    @type  hostmatrice: list/Matrix 
    @param hostmatrice: transformation matrix in host format
    @type  matrice: list/Matrix
    @param matrice: transformation matrix in epmv/numpy format
    """
    #get current transformation
    if hostmatrice !=None :
        #compute the new matrix: matrice*current
        #set the new matrice
        pass
    if matrice != None:
        #convert the matrice in host format
        #compute the new matrix: matrice*current
        #set the new matrice
        pass

def getPosUntilRoot(object):
    """
    Go through the hierarchy of the object until reaching the top level, 
    increment the position to get the transformation due to parents. 

    @type  object: hostObject
    @param object: the object   

   
    @rtype:   list
    @return:  the cumulative translation along the parenting hierarchy   
    """
    
    stop = False
    #get the first parent
    pos=[0,0,0]
    while not stop :
        #get the parent position, and add it to pos
        #get the parent of the previous parent
        parent=None
        if parent is None :
            stop = True
    return pos                                            
    
def addObjectToScene(doc,object,parent=None,centerRoot=True,rePos=None):
    """
    Insert/add an object to the current document under the specified parent, and
    at the specified location


    @type  doc: hostScene
    @param doc: the scene where to insert the object   
    @type  object: hostObject
    @param object: the object to insert
    @type  parent: hostObject
    @param parent: the parent of the object to insert under  
    @type  centerRoot: boolean
    @param centerRoot: if the object have to be recentered according the top-level  
    @type  rePos: list
    @param rePos: the location of the object in the scene 
    """
    #get the object name
    name=""
    #if the object is not already in the scene
    if getObject(name) == None:
        if parent != None : 
            if type(parent) == str : parent = getObject(parent)
            #if parent exist, insert the object under it
            pass
            if centerRoot :
                #get the current position of the object
                currentPos = []
                if rePos != None : 
                    parentPos = rePos          
                else :
                    parentPos = getPosUntilRoot(obj)#parent.GetPos()
                #set the new position of the object
                pass
        else :    
            #insert the object
            pass


def AddObject(object,parent=None,centerRoot=True,rePos=None):
    """
    Insert/add an object to the current document under the specified parent, and
    at the specified location. This function is an alias for addObjectToScene to
    permit to some script to work either in dejavu and the host

    @type  object: hostObject
    @param object: the object to insert
    @type  parent: hostObject
    @param parent: the parent of the object to insert under  
    @type  centerRoot: boolean
    @param centerRoot: if the object have to be recentered according the top-level  
    @type  rePos: list
    @param rePos: the location of the object in the scene 
    """

    doc = getCurrentScene()
    addObjectToScene(doc,object,parent=parent,centerRoot=centerRoot,rePos=rePos)
    
def addObjToGeom(object,geom):
    """
    Store/bind an hostobject to a Pmv/DejaVu geometry.
    ie mol.geoms['cpk'].obj

    @type  object: hostObject
    @param object: the object to bind/store
    @type  geom: DejaVu object
    @param geom: the dejavu geometry to be bind to 
    """    
    if type(obj) == list or type(obj) == tuple:
        if len(obj) > 2: geom.obj=obj        
        elif len(obj) == 1: geom.obj=obj[0]
        elif len(obj) == 2:    
            geom.mesh=obj[1]
            geom.obj=obj[0]
    else : geom.obj=obj


def makeHierarchy(listObj,listName, makeTagIK=False):
    """
    deprecated / in developpemt
    """
    pass
    
def addCameraToScene(name,Type,focal,center,scene):
    """
    Add a camera object to the scene

    @type  name: string
    @param name: name of the camera
    @type  Type: cameraType
    @param Type: perspective, orthogonale etc...
    @type  focal: float
    @param focal: the focal of the camera
    @type  center: list
    @param center: the position of the camera
    @type  scene: host scene
    @param scene: the scene
    
    """    
     
    cam = None
    #cam.SetPos(center)
    #cam perspective or parrallel
    #cam focal = float(focal)  #
    #most of the time we apply a rotation to get the same result as in PMV
    #cam rotZ = pi/2.
    addObjectToScene(scene,cam,centerRoot=False)    

def addLampToScene(name,Type,rgb,dist,energy,soft,shadow,center,scene):
    """
    Add a light to the scene

    @type  name: string
    @param name: name of the instance
    @type  Type: light hostType/int etc..
    @param Type: the light type : spot,sun,omni,etc..
    @type  rgb: list of int 0-255
    @param rgb: color of the light in rgb
    @type  dist: float
    @param dist: light distance of attenuation
    @type  energy: float
    @param energy: intensity of the light
    @type  soft: bool
    @param soft: soft light
    @type  shadow: boolean
    @param shadow: does the light produce shadow
    @type  scene: host scene
    @param scene: the scene
    """    
    dicType={'Area':0,'Sun':3}
    lamp = None#c4d.BaseObject(LIGHT)
    #lamp name (name)
    #lamp position (center)
    #lamp color (float(rgb[0]), float(rgb[1]), float(rgb[2]))#color
    #lamp energy  float(energy) #intensity
    #lamp type dicType[Type] #type
    if shadow : 
        #lampe shadow 
        pass
    addObjectToScene(scene,lamp,centerRoot=False)    
    """
    lampe.setDist(dist)
    lampe.setSoftness(soft)
    """

def reparent(obj,parent):
    """
    Change the object parent using the specified parent objects

    @type  obj: hostObject
    @param obj: the object to be reparented
    @type  parent: hostObject
    @param parent: the new parent object
    """    
    pass

def translateObj(object,position,use_parent=True):
    """
    Translation : Move the object to the vector position 

    @type  object: hostObject
    @param object: the object   
    @type  position: liste/array
    @param position: the new object position px,py,pz  
    @type  use_parent: boolean
    @param use_parent: if the parent position is used
    """
    pass

def scaleObj(object,sc):
    """
    Scale : scale the object by the vector scale 

    @type  object: hostObject
    @param object: the object   
    @type  sc: float or liste/array
    @param sc: the scale vector s,s,s or sx,sy,sz  
    """
    pass
    
def rotateObj(object,rotation):
    """
    Translation : Move the object to the vector position 
    This method could take either, a matrice, a euler array, a quaternion...

    @type  object: hostObject
    @param object: the object   
    @type  rotation: liste/array - matrice
    @param rotation: the new object rotation  
    """
    pass
 

    
def toggleDisplay(object,display):
    """
    Toggle on/off the display/visibility/rendermode of an hostObject in the host viewport

    @type  object: hostObject
    @param object: the object   
    @type  display: boolean
    @param display: if the object is displayed
    """    

def findatmParentHierarchie(atm,indice,hiera):
    """
    Get the parent of an atm object cpk or ball&sctick according the hierarchy type. 

    @type  atm: MolKit Atom
    @param atm: the atom
    @type  indice: string
    @param indice: type of object "S" or "B"
    @type  hiera: string
    @param hiera: the hierarchy type "default",'perRes' or 'perAtom'

    @rtype:   hostObject
    @return:  the direct parent object 
    """    
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
    
def ObjectsSelection(listeObjects,typeSel="new"):
    """
    Modify the current object selection.
    
    @type  listeObjects: list
    @param listeObjects: list of object to joins
    @type  typeSel: string
    @param listeObjects: type of modification: new,add,...

    """    
    dic={"add":c4d.SELECTION_ADD,"new":c4d.SELECTION_NEW}
    sc = getCurrentScene()
    #Put here the code to add/set an object to the current slection
    #[sc.SetSelection(x,dic[typeSel]) for x in listeObjects]

def JoinsObjects(listeObjects):
    """
    Merge the given liste of object in one unique geometry.
    
    @type  listeObjects: list
    @param listeObjects: list of object to joins
    """    
    sc = getCurrentScene()
    #put here the code to add the liste of object to the selection
#    sc.SetSelection(listeObjects[0],c4d.SELECTION_NEW)
#    for i in range(1,len(listeObjects)):
#        sc.SetSelection(listeObjects[i],c4d.SELECTION_ADD)
    #then call the command/function that joins the object selected
#    c4d.CallCommand(CONNECT)
    


#####################MATERIALS FUNCTION########################
def addMaterial(name,color):
    """
    Add a material in the current document 

    @type  name: string
    @param name: the material name
    @type  color: array
    @param color: the material color (r,g,b)

    @rtype:   hostMaterial
    @return:  the new material 
    """    
    doc = getCurrentScene()
    # look if the material already exist
    __mat = None#doc.SearchMaterial(name) put your code here
    if VERBOSE : print name,color	  
    if __mat != None :
        return __mat	  		
    else :
        #create the hostmaterial
        __mat = None
        # set the default color
        #__mat color  (float(color[0]),float(color[1]),float(color[2]))
        #__mat[900]  name  name
        # insert the material into the current document
        return __mat

def assignMaterial (mat, object):
    """
    Assign the provided material to the object 

    @type  mat: mat
    @param mat: the material
    @type  object: hostApp object
    @param object: the object
    """    

    #verify if the mat exist, if the string.
    #apply it to the object
    pass

def createDejaVuColorMat():
    """
    Create a Material for all DejaVu defined colors

    @rtype:   list
    @return:  the list of the new colors material 
    """    
    Mat=[]
    from DejaVu.colors import *
    for col in cnames:
        Mat.append(addMaterial(col,eval(col)))
    return Mat

def colorMaterial(mat,col):
    """
    Color a given material using the given color (r,g,b).

    @type  mat: hostMaterial
    @param mat: the material to change
    @type  col: array
    @param col: the color (r,g,b)
    """ 
    #put your code here
    #get the materiel if mat is a string for instance
    #or verify if the material exist in the current document
    #then change his color channel using 'col'
    pass

def retrieveColorMat(color):
    """
    Retrieve a material in the current document from his color (r,g,b), if his 
    color correpond to a DejaVu color

    @type  color: array
    @param color: the material color (r,g,b)

    @rtype:   hostMaterial
    @return:  the material of color color
    """    
    
    doc = getCurrentScene()
    from DejaVu.colors import *
    for col in cnames:
        if color ==	eval(col) :
            mat = None #search the material of name col
            return mat	
    return None


def create_SS_materials(doc=None):
    """
    Create/get the material for each type of secondary structure 
    ie sheet, helix, loop etc..

    @type  doc: hostScene
    @param doc: the document where to insert the new materials

    @rtype:   list hostMaterial
    @return:  the new materials
    """    

    SS_materials={}
    if doc == None : doc = getCurrentScene()
    # for each secondary structure type create a material
    for i,ss in enumerate(SecondaryStructureType.keys()):
        mat = None #search if the material already exist using the name ss[0:4] 
        if mat == None :
            mat=addMaterial(ss[0:4],SecondaryStructureType[ss]) #create the material
        SS_materials[ss[0:4]]=mat                      
    return SS_materials 

def create_Residus_materials(doc=None):
    """
    Create/get the material for each type of residues 
    ie ALA,CYS,GLU etc..

    @type  doc: hostScene
    @param doc: the document where to insert the new materials

    @rtype:   list hostMaterial
    @return:  the new materials
    """    
    import random
    Residus_materials={}
    if doc == None : doc = getCurrentScene()
    for i,res in enumerate(ResidueSelector.r_keyD.keys()):
        random.seed(i)
        mat=None #search if the material already exist using the residu name
        if mat == None :
            mat=addMaterial(res,(random.random(),random.random(),random.random()))
        Residus_materials[res]=mat
    #make a material for hetatm
    mat=None #search if the material already exist using the residu name
    if mat == None :
          mat=addMaterial('hetatm',(random.random(),random.random(),random.random()))
    Residus_materials["hetatm"]=mat
    return Residus_materials 

def create_Atoms_materials(doc=None):
    """
    Create/get the material for each type of atoms 
    ie C,N,O,H etc..

    @type  doc: hostScene
    @param doc: the document where to insert the new materials

    @rtype:   list hostMaterial
    @return:  the new materials
    """    
    Atoms_materials={}
    if doc == None : doc = getCurrentScene()
    for i,atms in enumerate(AtomElements.keys()):
        mat=None #search if the material already exist using the residu name
        if mat == None :
            mat=addMaterial(atms,(AtomElements[atms]))
        Atoms_materials[atms]=mat
    for i,atms in enumerate(DavidGoodsell.keys()):
        mat=None #search if the material already exist using the residu name
        if mat == None :
            mat=addMaterial(atms,(DavidGoodsell[atms]))
        Atoms_materials[atms]=mat
    return Atoms_materials

def getMaterials():
    """
    Create all material required for displaying a molecule

    @rtype:   dictionary hostMaterial
    @return:  the new materials
    """    

    Material={}
    Material["atoms"]=create_Atoms_materials()
    Material["residus"]=create_Residus_materials()
    Material["ss"]=create_SS_materials()
    Material["sticks"]=create_sticks_materials()
    #Material["loft"]=create_loft_material()
    return Material   

def getMaterialListe():
    """
    Create all material required for displaying a molecule, and make a liste 
    of theirs names
    @rtype:   list hostMaterial name
    @return:  the liste of materials name
    """    
    
    Material=getMaterials()
    matlist=[]
    matlist.extend(Material["atoms"].keys())
    matlist.extend(Material["residus"].keys())
    matlist.extend(Material["ss"].keys())
    matlist.extend(Material["sticks"].keys())            
    return matlist

def makeLabels(mol,selection):
    #"TODO"
    pass


def updateRTSpline(spline,selectedPoint,distance = 2.0,DistanceBumping = 1.85):
    """
    Update a spline by constraint from a steered point by Graham Jonhson
    
    @type  spline: hostSpline
    @param spline: the curve to update
    @type  selectedPoint: int
    @param selectedPoint: the indice of the steered point along the curve
    @type  distance: float
    @param distance: distance limit of steering effet
    @type  DistanceBumping: float
    @param DistanceBumping: radius of effect
    
    """    
    #get the total number of point of the curve
    nb_points = spline.GetPointCount()
    #update upstream
    for j in xrange(selectedPoint,nb_points-1):
        #get point j and j+1
        leaderB = spline.GetPointAll(j)
        myPos = spline.GetPointAll(j+1)
        #compute the distance
        deltaB = myPos-leaderB
        #deduce the new position
        newPosB = leaderB + deltaB*distance/deltaB.len()
        newPosA = c4d.Vector(0.,0.,0.)
        k = j        
        while k >=0 :
            #do it recursively
            leaderA = spline.GetPointAll(k)
            deltaA = myPos-leaderA;
            if ( deltaA.len() <= DistanceBumping and deltaA.len() >0):
                        newPosA = ((DistanceBumping-deltaA.len())*deltaA/deltaA.len());
            newPos = newPosB + newPosA
            spline.SetPoint(j+1,newPos)
            k=k-1
    jC = selectedPoint;
    #update dowstream
    while jC >0 :
        leaderBC = spline.GetPointAll(jC);
        myPosC = spline.GetPointAll(jC-1);              
        deltaC = myPosC-leaderBC;
        newPosBC = leaderBC + deltaC*distance/deltaC.len();
        newPosAC = c4d.Vector(0.,0.0,0.)
        k = jC
        while k < nb_points :
            leaderAC = spline.GetPointAll(k)
            deltaAC = myPosC-leaderAC;
            if ( deltaAC.len() <= DistanceBumping and deltaAC.len() >0.):
                        newPosAC = ((DistanceBumping-deltaAC.len())*deltaAC/deltaAC.len());
            newPosC = newPosBC + newPosAC
            spline.SetPoint(jC-1,newPosC)
            k=k+1
        jC=jC-1

def updateMolAtomCoord(mol,index=-1):
    """
    Update the molecule atoms coordinate according the cpk or balls position in the
    hostapp. A prerequise is that the cpk and/or the balls&stick representation
    have to be done at least once.

    @type  mol: MolKit Molecule
    @param mol: the molecule to update
    @type  index: int
    @param index: the molecule conformation index to update
    
    """
#    Note
#        balls and cpk should be linked to have always same position
#        let balls be dependant on cpk => contraints? or update
#        the idea : spline/dynamic move link to cpl whihc control balls
#        this should be the actual coordinate of the ligand
#        what about the rc...

    vt = []
    sph = mol.geomContainer.geoms['cpk'].obj
    for name in sph:
        o = getObject(name)
        #get the object o position, use the hostApp api 
        pos=(0.,0.,0.)#o.GetMg().off
        vt.append(pos)
	if index == -1 : index = 0	
    mol.allAtoms.updateCoords(vt,ind=index)

def updateCoordFromObj(mv,sel,debug=True):
    """
    Make the synchronisation between hostObject position and the molecule 
    coordinate they represent. The synchronisation permit for instance the 
    computation of energy, or the manipulation of string.

    @type  mv: MolecularViewer
    @param mv: the embeded molecular viewer
    @type  sel: hostObject list
    @param sel: selection of host object serving to update the molecule coordinate
    @type  debug: boolean
    @param debug: debug mode
    
    """    
    for s in sel :
        #get the object s name
        name = ''
        #get the type of object
        #replace the string by the actual class of object, and s by the type of s
        if s == 'spline':#Type == spline :
            #print "ok Spline"
            #get the slected point from the curve
            selectedPoint = 0
            #update the curve according this point
            updateRTSpline(s,selectedPoint)
        elif  s=='Null' :#Type == Null :
            #print "ok null"
            #parse the object name to get the molecule and chain name
            #molname or molname:chainname or molname:chain_ss ...
            hi = parseName(name)
            #print "parsed ",hi
            molname = hi[0]
            chname = hi[1]
            if hasattr(mv,'energy'): #ok need to compute energy
                #first update obj position: need mat_transfo_inv attributes at the mollevel
                #compute matrix inverse of actual position (should be the receptor...)
                if hasattr(mv.energy,'amber'): 
                    #first update obj position: need mat_transfo_inv attributes at the mollevel
                    #this is in developpement and probably not working
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
                    #mv.energy is a scoring handler based on AutoDock scoring function    
                    rec = mv.energy.current_scorer.mol1
                    lig = mv.energy.current_scorer.mol2
                    if rec.name == molname or lig.name == molname:
                        updateMolAtomCoord(rec,rec.cconformationIndex)
                        updateMolAtomCoord(lig,lig.cconformationIndex)
                    if hasattr(mv,'art'):
                        #are we in a Augmented Reality context
                        if not mv.art.frame_counter % mv.art.nrg_calcul_rate:
                            get_nrg_score(mv.energy)
                    else :
                        get_nrg_score(mv.energy)

def Circle(name, rad=1.):
    """
    Create a hostobject of type 2d circle.
    
    @type  name: string
    @param name: name of the circle
    @type  rad: float
    @param rad: the radius of the cylinder (default = 1.)
    
    @rtype:   hostObject
    @return:  the created circle
    """    
    #put the apropriate code here
    circle=None
    #set name and rad for the circle
    return circle

def Cylinder(name,radius=1.,length=1.,res=16, pos = [0.,0.,0.]):
    """
    Create a hostobject of type cylinder.
    
    @type  name: string
    @param name: name of the cylinder
    @type  radius: float
    @param radius: the radius of the cylinder
    @type  length: float
    @param length: the length of the cylinder
    @type  res: float
    @param res: the resolution/quality of the cylinder
    @type  pos: array
    @param pos: the position of the cylinder
    
    @rtype:   hostObject
    @return:  the created cylinder
    """    

    baseCyl = None #use the hostAPI
#    baseCyl radius = radius
#    baseCyl length = length
#    baseCyl resolution = res
    return baseCyl
		
def Sphere(name,radius=1.0,res=0, pos = [0.,0.,0.]):
    """
    Create a hostobject of type sphere.
    
    @type  name: string
    @param name: name of the sphere
    @type  radius: float
    @param radius: the radius of the sphere
    @type  res: float
    @param res: the resolution/quality of the sphere
    @type  pos: array
    @param pos: the position of the cylinder
    
    @rtype:   hostObject
    @return:  the created sphere
    """    

    QualitySph={"0":6,"1":4,"2":5,"3":6,"4":8,"5":16} 
    baseSphere = None#c4d.BaseObject(c4d.Osphere)
#    baseSphere radius = radius
#    baseSphere resolution = QualitySph[str(res)]
#    baseSphere position = position
    return baseSphere
    
def box(name,center=[0.,0.,0.],size=[1.,1.,1.],cornerPoints=None,visible=1):
    """
    Create a hostobject of type cube.
    
    @type  name: string
    @param name: name of the box
    @type  center: array
    @param center: the center of the box
    @type  size: array
    @param size: the size in x y z direction
    @type  cornerPoints: array list
    @param cornerPoints: the upper-left and bottom right corner point coordinates
    @type  visible: booelan
    @param visible: visibility of the cube after creation (deprecated)
    
    @rtype:   hostObject
    @return:  the created box
    """    
    #put your code
    box=None
    #set the name 'name'
    #if corner is provided compute the cube dimension in x,y,z, and the center
    if cornerPoints != None :
        for i in range(3):
            size[i] = cornerPoints[1][i]-cornerPoints[0][i]
        center=(numpy.array(cornerPoints[0])+numpy.array(cornerPoints[1]))/2.
    #position the cube to center
    #set the dimension to size
    #return the box
    return box


def updateSphereMesh(geom,quality=0,cpkRad=0.8,scale=0.,radius=0):
    """
    Update the atom sphere representation object according scale, 
    quality and radius factor.
    
    @type  geom: DejaVu Geom
    @param geom: the DejaVu geom representing the atom (cpk or balls)
    @type  cpkRad: float
    @param cpkRad: the vdw radius offset value
    @type  radius: float
    @param radius: deprecated / not used
    @type  quality: float
    @param quality: deprecated / not used
    @type  scale: float
    @param scale: the cdw radius scale factor
    """    
    
    AtmRadi = {"A":1.7,"N":"1.54","C":"1.85","O":"1.39","S":"1.85","H":"1.2","P" : "1.7"}
    #print geom.mesh
    for name in geom.mesh.keys() : 
        #get the scale factor
        scaleFactor=float(cpkRad)+float(AtmRadi[name])*float(scale)
        if float(cpkRad) > 0. :
            scaleFactor = float(cpkRad)*float(scale)
        #get the equivalent hostObject, ie baseMesh for each type of Atom (NCAO)
        mesh=geom.mesh[name]
        #scale the hostObject
        scaleObj(mesh,scaleFactor)
        #optionally update the mesh redraw / send an update event
        
def createBaseSphere(name="BaseMesh",quality=0,cpkRad=0.,scale=0.,
                     radius=None,mat=None,parent=None):
    """
    Foreach atom type C,A,N,O etc. create an empty object is created and use as a parent
    for a mesh/primitive geometry representing the atom. The list of the empty 
    objects is return.

    @type  name: string
    @param name: name of the baseObject
    @type  cpkRad: float
    @param cpkRad: the vdw radius offset value
    @type  radius: float
    @param radius: deprecated / not used
    @type  quality: float
    @param quality: quality of the sphere (segmentation level)
    @type  scale: float
    @param scale: the cdw radius scale factor
    @type  mat: Material list
    @param mat: the material dictionary to used for each atom
    @type  parent: hostObject
    @param parent: the baseObject parent
    
    @rtype:   Null hostObject list
    @return:  the list of empty object parenting the actual atom mesh by type
    """    
    
    QualitySph={"0":6,"1":4,"2":5,"3":6,"4":8,"5":16} 
    #AtmRadi = {"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2"}
    AtmRadi = {"A":1.7,"N":1.54,"C":1.85,"P":1.7,"O":1.39,"S":1.85,"H":1.2}
    iMe={}
    baseparent=newEmpty(name)
    addObjectToScene(getCurrentScene(),baseparent,parent=parent)
    baseShape = newEmpty(name+"_shape")
    addObjectToScene(getCurrentScene(),baseShape,parent=baseparent)
    baseSphere = Sphere(name+"_sphere",radius=1.0,res=QualitySph[str(quality)])
    addObjectToScene(getCurrentScene(),baseSphere,parent=baseShape)
    if mat == None : mat=create_Atoms_materials()
    for atn in AtmRadi.keys():
        atparent=newEmpty(name+"_"+atn)
        scaleFactor=float(cpkRad)+float(AtmRadi[atn])*float(scale)
        rad=AtmRadi[atn]
        #iMe[atn]=c4d.BaseObject(c4d.Osphere)
        iMe[atn] = newInstance(atn+"_"+name,baseShape) 
        #scale the instance acording scaleFactor
        scaleObj(iMe[atn],scaleFactor)        
        addObjectToScene(getCurrentScene(),atparent,parent=baseparent)
        addObjectToScene(getCurrentScene(),iMe[atn],parent=atparent)
        iMe[atn]=atparent
    return iMe
        
def updateObjectPos(object,position):
    """
    update an object position relative to his parent position
    alias for translateObj(object,position,use_parent=True)
    """   
    if len(position) == 1 : c = position[0]
    else : c = position
    #print "upadteObj"
    translateObj(object,position)
    
def updateSphereObj(obj,coord):
    """
    alias for updateObjectPos
    """
    updateObjectPos(obj,coord)

def updateSphereObjs(g):
    """
    update all hostObject (Spheres/Empty) associated to a DejaVu Geom

    @type  g: DejaVu Geom
    @param g: the related DejaVu geometry  
    """
   
    if not hasattr(g,'obj') : return
    newcoords=g.getVertices()
    #print "upadteObjSpheres"
    for i,o in enumerate(g.obj):
        #get the new coordinate/position
        c=newcoords[i]
        #apply it using the parent
        updateSphereObj(o,c)

def instancesSphere(name,centers,radii,meshsphere,colors,scene,parent=None):
    """
    Create instance Sphere object from the Sphere/Mesh geometry provided. The 
    instance are located according the centers list and are scaled according
    the radii list. 
    @type  name: string
    @param name: base name for instances
    @type  centers: liste/array vector
    @param centers: list of position coordinate of the sphere instances
    @type  radii: list/array float
    @param radii: the scale to apply to each instance
    @type  meshsphere: hostApp mesh
    @param meshsphere: the original mesh that will be instanciated
    @type  colors: rgb array
    @param colors: rgb color list to apply to each instance
    @type  scene: Mayadocument
    @param scene: the current document
    @type  parent: hostObject
    @param parent: the parent for the instance
    
    @rtype:   hostObject list
    @return:  the list of instance object sphere
    """    

    sphs=[]
    mat = None
    if len(colors) == 1:
        mat = retrieveColorMat(colors[0])
        if mat == None:		
            mat = addMaterial('mat_'+name,colors[0])
    for i in range(len(centers)):
        sphs.append(None) #append a instance object
        #sphs[i][1001]=meshsphere #set the mesh for the instance
        #sphs[i].SetName(name+str(i))        #set the name for the instance
        #sphs[i].SetPos(c4dv(centers[i]))    #set the position for the instance
        #sphs[i][905]=radii[i]               #set the scale for the instance
        #set the colors for the instance
        addObjectToScene(scene,sphs[i],parent=parent)
    return sphs
    
def instancesAtomsSphere(name,x,iMe,doc,mat=None,scale=1.0,
                         geom=None,dialog=None,pb=False,**kw):

    """
    Create instance Sphere object for every atom provided 
    from the Sphere/Mesh geometry provided. The 
    instance are located according the centers list and are scaled according
    the radii list. 
    @type  name: string
    @param name: base name for instances
    @type  x: MolKit node
    @param x: molecule instance
    @type  iMe: dictionary
    @param iMe: the dictionary of original mesh for every type of Atom
    @type  doc: document
    @param doc: the current document
    @type  mat: liste/array Materials
    @param mat: list of material for every type of Atom
    @type  scale: float
    @param scale: the scale to apply to each instance
    @type  geom: DejaVu.Geom
    @param geom: use geom vertices coordinate to place the instances
    @type  dialog: hostApp ui
    @param dialog: if dialog used for progress bar display
    @type  pb: hostApp widget
    @param pb: progress bar object
    @type  kw: dictionary
    @param kw: any additional arguments
   
    @rtype:   hostObject list
    @return:  the list of instance object sphere
    """    

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
		#print "finded",parent        
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
			spher.append( None ) #instance HotApp object
            #sphs[i][1001]=meshsphere #set the mesh for the instance
            #sphs[i].SetName(name+str(i))        #set the name for the instance
            #sphs[i].SetPos(c4dv(centers[i]))    #set the position for the instance
            #sphs[i][905]=scale               #set the scale for the instance
            #set the colors for the instance
			addObjectToScene(getCurrentScene(),spher[j],parent=cp)
			toggleDisplay(spher[j],False)
			k=k+1
			if pb :
				progressBar(j/len(coords)," cpk ")
                update()
		sphers.extend(spher)
    if pb :
        resetProgressBar(0)
    return sphers
        

def getStickProperties(coord1,coord2):
    """
    From two point return the length, and the orientation from one to another
    @type  coord1: vector
    @param coord1: first point
    @type  coord2: vector
    @param coord2: second point

    @rtype:   tupple
    @return:  length, orientation, and intermediate point
    """
    x1 = float(coord1[0])
    y1 = float(coord1[1])
    z1 = float(coord1[2])
    x2 = float(coord2[0])
    y2 = float(coord2[1])
    z2 = float(coord2[2])
    length = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
    wsz = atan2((y1-y2), (x1-x2))
    wz = acos((z1-z2)/length)
    return length,wsz,wz,[float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2]


def instancesCylinder(name,points,faces,radii,mesh,colors,scene,parent=None):
    """
    Create instance Cylinder object from the Cylinder/Mesh geometry provided. The 
    instance are located according the points list and are conected according 
    the face list. 
    
    @type  name: string
    @param name: base name for instances
    @type  points: liste/array vector
    @param points: list of position coordinate of the sphere instances
    @type  faces: liste/array int
    @param faces: list of index of connected point
    @type  radii: list/array float
    @param radii: the scale to apply to each instance
    @type  mesh: hostApp mesh
    @param mesh: the original mesh that will be instanciated
    @type  colors: rgb array
    @param colors: rgb color list to apply to each instance
    @type  scene: document
    @param scene: the current document
    @type  parent: hostObject
    @param parent: the parent for the instance
    
    @rtype:   hostObject list
    @return:  the list of instance object cylinder
    """    

    cyls=[]
    mat = None
    if len(colors) == 1:
        mat = retrieveColorMat(colors[0])
        if mat == None:		
            mat = addMaterial('mat_'+name,colors[0])
    for i in range(len(faces)):
        length,wsz,wz,pts=getStickProperties(points[faces[i][0]],points[faces[i][1]])
        #add code from hostAPI for 
        #creating an instance object named 'name'
        cyls.append(None)
        #from the polygon object 'mesh'
        #apply the trnasformation from the stick properties (matrice or rotation)
        #apply the scale 'radii'
        if mat == None : mat = addMaterial("matcyl"+str(i),colors[i])
        assignMaterial(mat,cyls[i])#mat[bl.retrieveColorName(sphColors[i])]
        addObjectToScene(scene,cyls[i],parent=parent)
    return cyls

    
def updateTubeMesh(geom,cradius=1.0,quality=0):
    """
    update the orgininal mesh used for the sticks, which should be a cylinder 
    
    @type  geom: DejaVu.Geom
    @param geom: the stick geom
    @type  cradius: float
    @param cradius: the scale to apply to each instance
    @type  quality: int
    @param quality: the quality/resolution 
    """    

    #get the mesh object should be the cylinder
    #but also can be a instance object.
    mesh=geom.mesh#should be the cylinder
    #print mesh.GetName()        
    #mesh[5000]=cradius
    cradius = cradius*1/0.2
    #scale only x and z , so just scale the radius not the length of the stick
    #the length depend of the atoms
    scaleObj(mesh,[float(cradius),1.,float(cradius)])
    #you can update the mesh

def updateTubeObj(atm1,atm2,bicyl=False):
    """
    update one tube object representing an atoms bonds stick.
    
    @type  atm1: MolKit.Atom
    @param atm1: the first atom
    @type  atm2: MolKit.Atom
    @param atm2: the second atom
    @type  bicyl: boolean
    @param bicyl: is the stick represented by 1 or 2 cylinders
    """    

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
    """
    update one tube object from new coordinate.
    
    @type  o: hostApp object
    @param o: the cylinder
    @type  coord1: Point array
    @param coord1: the first point
    @type  coord2: Point array
    @param coord2: the second point
    """    

    length,wsz,wz,pts=getStickProperties(coord1,coord2)
    #apply the trnasformation from the stick properties (length and rotation)
    #you can update according the parent position
    parentPos = getPosUntilRoot(o)#parent.GetPos()
    #currentPos = o.GetPos()
    #o.SetPos(currentPos - parentPos)                

def biStick(atm1,atm2,hiera,instance):
    """
    create 2 cylinder reprensenting the bond between the two given atoms.
    
    @type  atm1: MolKit.Atom
    @param atm1: the first atom
    @type  atm2: MolKit.Atom
    @param atm2: the second atom
    @type  hiera: string
    @param hiera: the type of hierarchi to apply the created cylinder
    @type  instance: hostApp object
    @param instance: the mesh to share between all cylinder 
    
    @rtype:   hostObject list
    @return:  the two instance object cylinder
    """    

    mol=atm1.getParentOfType(Protein)
    stick=[]
    c0=numpy.array(atm1.coords)
    c1=numpy.array(atm2.coords)
    vect = c1 - c0
    n1=atm1.full_name().split(":")
    n2=atm2.full_name().split(":")
    name1="T_"+n1[1]+"_"+n1[2]+"_"+n1[3]+"_"+atm2.name
    name2="T_"+n2[1]+"_"+n2[2]+"_"+n2[3]+"_"+atm1.name	
    #create the first cylinder named 'name1'
    stick.append(None) #instance of 'instance' object
    #apply the trnasformation from the stick properties (length and rotation)
    length,wsz,wz,pts=getStickProperties(c0,(c0+(vect/2.)))
    #apply the material
    mat=getCurrentScene().SearchMaterial(atm1.name[0])
    if mat == None :
        mat = addMaterial(atm1.name[0],[0.,0.,0.]) 	
    assignMaterial(mat,stick[0])

    #create the second cylinder named 'name2'
    stick.append(None) #instance of 'instance' object
    #apply the trnasformation from the stick properties (length and rotation)
    length,wsz,wz,pts=getStickProperties((c0+(vect/2.)),c1)
    #apply the material
    mat=getCurrentScene().SearchMaterial(atm2.name[0])
    if mat == None :
        mat = addMaterial(atm2.name[0],[0.,0.,0.])
    assignMaterial(mat,stick[1])

    parent = findatmParentHierarchie(atm1,'B',hiera)
    addObjectToScene(getCurrentScene(),stick[0],parent=parent)
    addObjectToScene(getCurrentScene(),stick[1],parent=parent)	
    return stick
	
def Tube(set,atms,points,faces,doc,mat=None,res=32,size=0.25,sc=1.,join=0,
         instance=None,hiera = 'perRes',bicyl=False,pb=False):
    """
    This is the function to build atoms covalent bonds as uni or bi-cylinders
    for a set of given atoms. The bonds are made by PMV using distance rules.
    
    @type  set: MolKit.Atom
    @param set: set of atoms, ie mol.geomContainer.atoms["sticks"]
    @type  atms: MolKit.Atom
    @param atms: selection of atoms ie atoms.get("CA"), or self.select('mol:::CA,C')
    @type  points: 3d points array
    @param points: the starting and ending point position of each bonds from DejaVu
    @type  doc: hostApp Scene
    @param doc: the current working documents/scene
    @type  mat: hostApp Material
    @param mat: optional predefined material to apply
    @type  res: float
    @param res: resolution of cylinder (ie subdivision level)
    @type  size: float
    @param size: use for initially scale the cylinder
    @type  sc: float
    @param sc: scale value deprecated, keep it to default
    @type  join: boolean
    @param join: if all the cylinder have to be joined in one unic mesh/object
    @type  instance: hostApp object
    @param instance: the mesh to share between all cylinder 
    @type  hiera: string
    @param hiera: the type of hierarchi to apply the created cylinder
    @type  bicyl: float
    @param bicyl: set of atoms, ie mol.geomContainer.atoms["sticks"]
    @type  pb: boolean
    @param pb: do we use the native hostApp statut bar if any to display the progress
   
    @rtype:   hostObject list
    @return:  the list of bond cylinder instance
    """    
             
    sticks=[]
    #get the list of bonds
    bonds, atnobnd = set.bonds
    if instance == None:
        #if no instance provide, build it
        mol = atms[0].top
        instance=newEmpty("baseBond") 
        addObjectToScene(doc,instance,parent=mol.geomContainer.masterGeom.obj)		
        cyl=Cylinder('baseBondShape',radius=size,length=1.,res=res)
        addObjectToScene(doc,cyl,parent=instance)
    #for everybond create an instance of the baseshape
    for i,bond in enumerate(bonds):
        if bicyl :
            sticks.extend(biStick(bond.atom1,bond.atom2,hiera,instance))
        else :
            #have to make one cylinder / bonds
            #and put the gradiant mat on it
            pass
        if pb :
            progressBar(i/len(bonds)," sticks ")
    if pb :
        resetProgressBar(0)
    return [sticks,instance]	


# You can add math convertion utility function such vector, matrice convertion
#between hostApp and numpy/pmv python...

def hostAppVector(points):
    """
    This will return a 3d point in the hostApp API appropriate format. 
    This function can also be used when theire is LeftHand / RightHand 
    conflict
    
    @type  points: array
    @param points: the point to convert

    @rtype:   hostObject Vector
    @return:  the converted point
    """    
    return hostApp.Vector(float(points[0]),float(points[1]),float(points[2]))

def pythonVector(points):
    """
    This will return a 3d point in a python list format
    This function can also be used when theire is LeftHand / RightHand 
    conflict
    
    @type  points: hostObject Vectorarray
    @param points: the hostObject point

    @rtype:   list
    @return:  the converted point
    """    
    
    return [v.x,v.y,v.z]
#same for matrice
def hostAppMat2numpy(hostmat):
    """
    This will return a matrice in a numpy.array format
    This function can also be used when theire is LeftHand / RightHand 
    conflict.
    ie a numpy matrice is a regular 4x4 matrice (3x3rot+trans)
    
    @type  hostmat: hostObject Matrice
    @param hostmat: the hostObject matrice to converted

    @rtype:   numpy.array
    @return:  the converted matrice
    """    
    import numpy
    from numpy import matrix
    from Pmv.hostappInterface import comput_util as C
    #place your code here
    M=matrix()
    IM=M.I
    return M,IM
    
def matrix2hostAppMat(mat,transpose = True):
    """
    This will return a matrice in the hostApp format
    This function can also be used when theire is LeftHand / RightHand 
    conflict.
    
    @type  mat: 4x4 array
    @param mat: the matrice to converted

    @rtype:   hostObject Matrice
    @return:  the converted matrice
    """
    
    from Pmv.hostappInterface import comput_util as C
    #do we need to transpose
    if transpose :
	    mat = Numeric.array(mat).transpose().reshape(16,)
    else :
	    mat = Numeric.array(mat).reshape(16,)
    r,t,s = C.Decompose4x4(mat)  	
    	#Order of euler angles: heading first, then attitude/pan, then bank
    axis = C.ApplyMatrix(Numeric.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]),r.reshape(4,4))
    #put your code here
    mx=None
    return mx

 
def spline(name, points,close=0,type=1,scene=None,parent=None):
    """
    This will return a hostApp spline/curve object according the given list
    of point.
    
    @type  name: string
    @param name: name for the object
    @type  points: liste/array vector
    @param points: list of position coordinate of the curve point
    @type  close: bool/int
    @param close: is the curve is closed
    @type  type: int/string
    @param type: ususally describe type of curve, ie : bezier, linear, cubic, etc...
    @type  scene: hostApp scene
    @param scene: the current scene
    @type  parent: hostObject
    @param parent: the parent for the curve

    @rtype:   hostObject
    @return:  the created spline
    """
    #create the spline
    spline=None
    #define type, close, name
    #set the points
    for i,p in enumerate(points):
        #set every i point
        pass 
    #add the object to the scene
    if scene != None :
        addObjectToScene(scene,spline,parent=parent)
    return spline,None

def update_spline(name,new_points):
    """
    This will update the hostApp spline/curve (name) object according the new list of 
    coordinates.
    
    @type  name: string
    @param name: name of the spline to be updated
    @type  new_points: liste/array vector
    @param new_points: list of new position coordinate to update the curve

    @rtype:   booelean
    @return:  if the spline has been retrieved and updated or not
    """
    spline=getObject(name)
    if spline is None : return False
    #resize/update the spline points
    #spline.ResizeObject(int(len(new_points))) Paste your code here
    for i,p in enumerate(new_points):
        #spline.SetPoint(i, c4dv(p)) Paste your code here
        pass
    return True

#dev function to produce lines display as spline
#def makeLines(name,points,faces,parent=None):
#    rootLine = newEmpty(name)
#    addObjectToScene(getCurrentScene(),rootLine,parent=parent)
#    spline=c4d.BaseObject(c4d.Ospline)
#    spline.SetName(name+'mainchain')
#    spline.ResizeObject(int(len(points)))
#    cd4vertices = map(c4dv,points)
#    map(polygon.SetPoint,range(len(points)),cd4vertices)    
#    addObjectToScene(getCurrentScene(),spline,parent=rootLine)
#    spline=c4d.BaseObject(c4d.Ospline)
#    spline.SetName(name+'sidechain')
#    spline.ResizeObject(int(len(points)))
#    for i,p in enumerate(points):
#        spline.SetPoint(i, c4dv(p))
#    addObjectToScene(getCurrentScene(),spline,parent=rootLine)    

def editLines(molecules,atomSets):
    """
    This function help creating and updating a polygon representing the atom bond 
    using lines (edges of the polygon).
    
    @type  molecules: MolKit.Protein
    @param molecules: the molecule to display as lines
    @type  atomSets: MolKit.AtomSet
    @param atomSets: the atomset to use (ie selection)
    """
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
                mol.geomContainer.geoms[ch.full_name()+'_line'] = lines
            else : #need to update
                updateLines(lines, chains=ch)
				
def updateLines(lines, chains=None):
    """
    This function update a polygon representing the atom bond 
    using lines (edges of the polygon).
    
    @type  lines: hostApp obj
    @param lines: the lines polygon to update
    @type  chains: MolKit.Chain
    @param chains: the atoms reference used to update
    """

    #lines = getObject(name)	
	#if lines == None or chains == None:
	    #print lines,chains	
    parent = getObject(chains.full_name())	
	    #print parent		
    bonds, atnobnd = chains.residues.atoms.bonds
    indices = map(lambda x: (x.atom1._bndIndex_,
								x.atom2._bndIndex_), bonds)
    updatePoly(lines,vertices=chains.residues.atoms.coords,faces=indices)
		
def PointCloudObject(name,**kw):
    """
    This function create a polygon representing the atom as point (vertex of the polygon).
    
    @type  name: string
    @param name: name of the pointCloud
    @type  kw: dictionary
    @param kw: dictionary of arg options, ie :
        'vertices' array of coordinates ;
        'faces'    int array of faces ;
        'parent'   hostAp parent object

    @rtype:   hostApp obj
    @return:  the polygon object
    """
    #get the coordinates for the vertices
    coords=kw['vertices']
    #get the number of face if any
    nface = 0	
    if kw.has_key("faces"):
        nface = len(kw['faces'])
    #create the polygon of name 'name'
    obj= None
    host_vertices = map(hostAppVector,coords)
    #example of settin up the polygon using map, if the polygon have a setpoint 
    #method for instance
    map(obj.SetPoint,range(len(coords)),host_vertices)    
    #else you can just make a for loop
    addObjectToScene(getCurrentScene(),obj,parent=parent)    
    return obj

##POLYGON MESH FUNCTION : update, create, instanciate etc....

#def c4df(face,g,polygon):
#    A = int(face[0])
#    B = int(face[1])
#    if len(face)==2 :
#        C = B
#        D = B
#        poly=c4d.CPolygon(A, B, C)
#    elif len(face)==3 : 
#        C = int(face[2])
#        D = C
#        poly=c4d.CPolygon(A, B, C)
#    elif len(face)==4 : 
#        C = int(face[2])
#        D = int(face[3])
#        poly=c4d.CPolygon(A, B, C, D)
#    polygon.SetPolygon(id=g, polygon=poly)
#    return [A,B,C,D]
#
def polygons(name,smooth=False,color=[0.5,0.5,0.5], material=None, **kw):
    """
    This function create a polygons according given data.
    
    @type  name: string
    @param name: name of the pointCloud
    @type  smooth: boolean
    @param smooth: smooth the mesh
    @type  color: array
    @param color: r,g,b value to color the mesh
    @type  material: hostApp obj
    @param material: material to apply to the mesh    
    @type  kw: dictionary
    @param kw: dictionary of arg options, follow the DejaVu.Geom keywords,  ie :
        'vertices' array of coordinates ;
        'faces'    int array of faces ;
        'normals'  array of vertex normals ;
        'parent'   hostAp parent object ;
        'frontPolyMode';
        'shading';
    @rtype:   hostApp obj
    @return:  the polygon object
    """

    vertices = kw["vertices"]
    faces = kw["faces"]
    normals = kw["normals"]
    frontPolyMode='fill'
    if kw.has_key("frontPolyMode"):	  
        frontPolyMode = kw["frontPolyMode"]
    if kw.has_key("shading") :  
        shading=kw["shading"]#'flat'
    if frontPolyMode == "line" : #wire mode look for material wire
        material = None#getCurrentScene().SearchMaterial("wire") Put your code here
        if material == None:
            material = addMaterial("wire",(0.5,0.5,0.5))
    #create the polygon according provided vertices and faces
    polygon = None #ex : c4d.PolygonObject(len(vertices), len(faces))
    #example of settin up the polygon using map, if the polygon have a setpoint 
    #method for instance
    host_vertices = map(hostAppVector,vertices)
    map(polygon.SetPoint,range(len(vertices)),host_vertices)
    #set the faces, you can use either a loop or a map function
    #here is the for loop checking the size of the face 
    #ie , 2, 3 or 4 vertices/faces
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
        #set the faces accroding the vertices indices A,B,C,D exple :
        #expl : polygon.SetPolygon(id=g, polygon=c4d.CPolygon( A, B, C, D ))    
    if material == None :
        material = addMaterial(name,color[0])
    assignMaterial(material,polygon)
    return polygon

        
def createsNmesh(name,vertices,vnormals,faces,smooth=False,material=None,proxyCol=False,color=[[1,0,0],]):
    """
    This is the main function that create a polygonal mesh corresponding to 
    DejaVu.IndexedPolygon such as MSMS or secondary structure.
    
    @type  name: string
    @param name: name of the pointCloud
    @type  vertices: array
    @param vertices: list of x,y,z vertices points
    @type  vnormals: array
    @param vnormals: list of x,y,z vertex normals vector
    @type  faces: array
    @param faces: list of i,j,k indice of vertex by face
    @type  smooth: boolean
    @param smooth: smooth the mesh
    @type  material: hostApp obj
    @param material: material to apply to the mesh    
    @type  proxyCol: booelan
    @param proxyCol: do we need a special object for color by vertex (ie C4D)
    @type  color: array
    @param color: r,g,b value to color the mesh

    @rtype:   hostApp obj
    @return:  the polygon object
    """
      
    PDBgeometry = polygons(name, vertices=vertices,normals=vnormals,faces=faces,material=material,color=color,smooth=smooth,proxyCol=proxyCol)
    return [PDBgeometry]

def instancePolygon(name, matrices=None, mesh=None,parent=None):
    """
    This function generate an instance object from the given mesh for every 
    transformations matrices given. ie equivalent to 
    SetInstance method of DejaVu.Geom.
    
    @type  name: string
    @param name: name of the pointCloud
    @type  matrices: array list
    @param matrices: list of transformations matrice to apply
    @type  mesh: hostApp polygon
    @param mesh: the mesh to instanciate
    @type  parent: hostApp obj
    @param parent: the instance parent object
 
    @rtype:   hostApp obj
    @return:  the list of instance object or None
    """     
      
    if matrices == None : return None
    if mesh == None : return None
    instance = []	  
    #print len(matrices)#4,4 mats
    for mat in matrices:
        obj = None #create an instance of mesh mesh
        instance.append(obj)
        mx = matrix2hostAppMat(mat)
        #apply the matrice of transformation i
        #add the object to the scene under the given 'parent' object
        AddObject(instance[-1],parent=parent)
    return instance
	  	
def updatePoly(polygon,faces=None,vertices=None):
    """
    This function update a given polygon mesh according the given new vertices and faces.
    
    
    @type  polygon: hostApp mesh || string
    @param polygon: the polygon or the name of the polygon to be update
    @type  faces: array
    @param faces: list of i,j,k indice of vertex by face
    @type  vertices: array
    @param vertices: list of x,y,z vertices points
    
    @rtype:   None
    @return:  None if no data provided
    """     
    
    if type(polygon) == str:
        polygon = getObject(polygon)
    if polygon == None : return		
    #put your code here...
    
    if vertices != None:
        for k,v in enumerate(vertices) :
            hostv = hostAppVector(v)
            #set the point k at position hostv
            #exple : polygon.SetPoint(k, c4dv(v))
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
            #set the faces accroding the vertices indices A,B,C,D exple :
            #polygon.SetPolygon(id=g, polygon=c4d.CPolygon( A, B, C, D ))

def updateMesh(g,proxyCol=False,parent=None,mol=None):
    """
    This function update the polygon mesh assoicated to the DejaVu.Geom obj 
    according the data extracted from the DejaVu.Geom.
    
    @type  g: DejaVu.Geom
    @param g: the dejavu geometry that have been modified
    @type  proxyCol: booelan
    @param proxyCol: do we need a special object for color by vertex (ie C4D)
    @type  parent: hostApp obj
    @param parent: the instance parent object (Deprecated)
    @type  mol: MolKit.Protein
    @param mol: Deprecated
    """
    #get the polygon obj
    obj=g.obj
    #get the new vertices and faces
    vertices=g.getVertices()
    faces=g.getFaces()    
    updatePoly(obj,faces=faces,vertices=vertices)

##COLOR METHODS
def changeMaterialSchemColor(typeMat):
    """
    This function will change the materials colors according the type of 
    coloring methods apply. ie ByAtom, or following the david goodsell rules.
    
    @type  typeMat: string
    @param typeMat: the coloring method. can be :  "ByAtom", "AtomsU","ByResi","Residu" or "BySeco".
    """     
    
    if typeMat == "ByAtom":
        for atms in AtomElements.keys() : colorMaterial(atms,AtomElements[atms])
    elif typeMat == "AtomsU" :
        for atms in DavidGoodsell.keys() :colorMaterial(atms,DavidGoodsell[atms])
    elif typeMat == "ByResi":
        for res in RasmolAmino.keys(): colorMaterial(res,RasmolAmino[res])
    elif typeMat == "Residu":
        for res in Shapely.keys(): colorMaterial(res,Shapely[res])
    elif typeMat == "BySeco":
        for ss in SecondaryStructureType.keys(): colorMaterial(ss[0:4],SecondaryStructureType[ss])
    else : pass

def checkChangeMaterial(o,typeMat,atom=None,parent=None,color=None):
    """
    This function will check if a change of materials and colors is need according the type of 
    coloring methods apply. 
    
    @type  o: hostApp object
    @param o: the object to check, ie usually an atom's sphere
    @type  typeMat: string
    @param typeMat: the coloring method. can be :  "ByAtom", "AtomsU","ByResi","Residu" or "BySeco".
    @type  atom: MolKit.Atom
    @param atom: the linked atom, ie o is a Sphere representing CPK of this atom
    @type  parent: hostApp obj
    @param parent: use the general material exemple mat_molname_cpk
    @type  color: array
    @param color: the new color [r,g,b] Deprecated

    """
    #get the current document, and all active materials
    doc= getCurrentScene()
    Material=getMaterials()
    matliste=getMaterialListe()
    ss="Helix"
    ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']
    #if an atom is provided get the secondary strcture type
    if atom != None :
        res=atom.getParentOfType(Residue)
        if hasattr(res,"secondarystructure") : ss=res.secondarystructure.name
    #split the name to get molecular data
    names=splitName(o.GetName())

    #get the current material of o
    mat = None #put your code
    matname=mat.name #put your code here
    objectname = o.name #put your code here
    
    #change the material color ie AtomType to DavidGoodcelle coloring method
    changeMaterialSchemColor(typeMat)
    #check according the type if we need to change the material assign to o
    if typeMat == "" or typeMat == "ByProp" : #color by color
        if parent != None : requiredMatname = 'mat'+parent            #exemple mat_molname_cpk
        else : requiredMatname = 'mat'+objectname                     #exemple mat_coil1a_molname
        if typeMat == "ByProp": requiredMatname = 'mat'+objectname    #exemple mat_coil1a_molname
        if matname != requiredMatname : 
            #check if requiredMatname exist in the current document
            rMat=None #put your code here, ex:doc.SearchMaterial(requiredMatname)
            if rMat is None : rMat=addMaterial(requiredMatname,color)
            else : colorMaterial(rMat,color)
            #assign the new material
            assignMaterial (rMat, o)
        else : colorMaterial(requiredMatname,color)               
    if typeMat == "ByAtom" :
        if matname not in AtmRadi.keys() :                #switch to atom materials
            assignMaterial(Material["atoms"][names[5][0]], o)
    if typeMat == "AtomsU" :
        #if matname not in AtmRadi.keys() :               #switch to atom materials
        assignMaterial(Material["atoms"][lookupDGFunc(atom)],o)
    elif typeMat == "ByResi" :
        if matname not in ResidueSelector.r_keyD.keys() : #switch to residues materials
            if names[3] not in ResidueSelector.r_keyD.keys(): names[3]='hetatm'            
            assignMaterial(Material["residus"][names[3]],o)
    elif typeMat == "BySeco" :
        if matname not in ssk : #switch to ss materials
            assignMaterial(Material["ss"][ss[0:4]],o)

def checkChangeStickMaterial(o,typeMat,atoms,parent=None,color=None):
    """
    This function will check if a change of materials and colors is need according the type of 
    coloring methods apply. 
    
    @type  o: hostApp object
    @param o: the object to check, ie one stick/bond
    @type  typeMat: string
    @param typeMat: the coloring method. can be :  "ByAtom", "AtomsU","ByResi","Residu" or "BySeco".
    @type  atoms: MolKit.Atom list
    @param atoms: the linked atoms, ie o is a bond linking these two atoms
    @type  parent: hostApp obj
    @param parent: use the general material exemple mat_molname_cpk
    @type  color: array
    @param color: the new color [r,g,b] Deprecated

    """
    doc=getCurrentScene()
    Material=getMaterials()
    ss="Helix"
    ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']                
    res=atoms[0].getParentOfType(Residue)
    if hasattr(res,"secondarystructure") : ss=res.secondarystructure.name
    names=["T","noname","noname",res.name[0:3],res.name[:3],atoms[0].name[0]]        

    #get the current material of o
    mat = None #put your code
    matname=mat.name #put your code here
    objectname = o.name #put your code here

    if typeMat == "" or typeMat == "ByProp": #color by color
        if parent != None : requiredMatname = 'mat'+parent         #exemple mat_molname_cpk
        else : requiredMatname = 'mat'+o.GetName()                 #exemple mat_coil1a_molname
        if typeMat == "ByProp": requiredMatname = 'mat'+objectname #exemple mat_coil1a_molname
        if matname != requiredMatname : 
            #check if requiredMatname exist in the current document
            rMat=None #put your code here, ex:doc.SearchMaterial(requiredMatname)
            if rMat is None : rMat=addMaterial(requiredMatname,color)
            else : colorMaterial(rMat,color)
            assignMaterial(rMat,o)
        else : colorMaterial(requiredMatname,color)                        
    if typeMat == "ByAtom" or typeMat == "AtomsU" :
        if matname not in Material["sticks"].keys() : #switch to atom materials
                assignMaterial(Material["sticks"][atoms[0].name[0]+atoms[1].name[0]])
    elif typeMat == "ByResi" :
        if matname not in ResidueSelector.r_keyD.keys() : #switch to residues materials
                #print matname, names[3],Material["residus"]            
                assignMaterial(Material["residus"][names[3]])
    elif typeMat == "BySeco" :
        if matname not in ssk : #switch to ss materials
                assignMaterial(Material["ss"][ss[0:4]])

##NOTE : checkChangeMaterial and checkChangeStickMaterial should/could be merge 
## in one unic function....especially since checkChangeStickMaterial is deprecated
    
def changeColor(geom,colors,perVertex=False,proxyObject=None,doc=None,pb=False):
    """
    This function will change the color of a given object (usually a mesh).
    
    @type  geom: DejaVu.Geom or hostApp object
    @param geom: the geom that have been modified, or the hostApp obj directly
    @type  colors: array
    @param colors: list of new colors [[r,g,b],[r,g,b],...]
    @type  perVertex: boolean
    @param perVertex: is the colors list apply to the vertex list
    @type  proxyObject: hostApp obj
    @param proxyObject: special object use when host didnt support color by vertex (ie C4D)
    @type  doc: hostApp scene
    @param doc: the current document
    @type  pb: boolean
    @param pb: do we use the host statut bar to display the progress
    """

    if doc == None : doc = getCurrentScene()
    if hasattr(geom,'obj'): obj=geom.obj
    else : obj=geom
    
    #verfify perVertex flag
    unic=False
    ncolor=colors[0]    
    if len(colors)==1 :
        unic=True
        #ncolor have to be in the hostApp color format, choose range 1-255 or 0-1
        #using the convert function
        ncolor = convertColor(colors[0],toint=False)
    if proxyObject  :
        #put your code here that handle the color per vertex when not supported 
        #by the host
        pass
    else :    
        #put your code here to change the color per vertex of the given mesh
        #if only one color (ie ncolor) provided, apply the same color to every vertex
        #and apply also the color to the material
        #you can use the progress bar here
        if pb and (k%70) == 0:
            progress = float(k) / (len( mesh.faces ))
            print progress, 'color mesh'
    if unic :
        mat = None #get the object materials
        matname = "" #get the material name
        colorMaterial(matname,ncolor)   
     
def changeSticksColor(geom,colors,type=None,indice=0,perVertex=False,proxyObject=None,doc=None):
    """
    This function will change the color of a given sticks/bonds. need 2 colors 
    per stick as there is two atoms. This function can get complexe depending on the nature of
    the stick :
    
        - mesh : color per vertex 
        - cylinder : gradiant material
        - bicylinder : two material
    
    @type  geom: DejaVu.Geom or hostApp object
    @param geom: the geom that have been modified, or the hostApp obj directly
    @type  colors: array
    @param colors: list of new colors [[r,g,b],[r,g,b],...]
    @type  type: int | string
    @param type: type of sticks, mesh, cylinder, bicylinder
    @type  indice: int
    @param indice: do we use the host statut bar to display the progress
    @type  perVertex: boolean
    @param perVertex: is the colors list apply to the vertex list
    @type  proxyObject: hostApp obj
    @param proxyObject: special object use when host didnt support color by vertex (ie C4D)
    @type  doc: hostApp scene
    @param doc: the current document
    """

    if hasattr(geom,'obj'):obj=geom.obj[indice]
    else : obj=geom

    unic=False
    if len(colors)==1 :
        unic=True
        ncolor = convertColor(colors[0],toint=False)

    mat = None #get the object materials
    matname = "" #get the material name
    #put your code here, look at other helper for example

def changeObjColorMat(obj,color):
    """
    This function will change the color of a given object's material.
    
    @type  obj: hostApp object
    @param obj: the hostApp obj to be colored
    @type  color: array
    @param color: the new colors [r,g,b]
    """

    doc = getCurrentScene()
    mat = None #get the object materials
    matname = "" #get the material name
    rMat=None #check if the material still exist in the scene
    colorMaterial(rMat,color)


def getCornerPointCube(obj):
    """
    This function return the lowerleft/upperright corner point of the given cube/parallelpiped
    
    @type  obj: hostApp object
    @param obj: the hostApp obj to be colored

    @rtype:   array
    @return:  the two corner points.
    """
    size = 0            #get object size
    center = [0.,0.,0.] #get object position
    cornerPoints=[]
    #lowCorner
    lc = [center[0] - size[0]/2.,
          center[1]- size[1]/2.,
          center[2] - size[2]/2.]
    uc = [center[0] + size[0]/2.,
          center[1]+ size[1]/2.,
          center[2] + size[2]/2.]
    cornerPoints=[[lc[2],lc[1],lc[0]],[uc[2],uc[1],uc[0]]]
    return cornerPoints

def makeEditable(object,copy=True):
    """
    This function return an editable version of the given polygon mesh.
    Use oit only if the hostApp requir it
    
    @type  object: hostApp object mesh
    @param object: the hostApp obj to be decompose
    @type  copy: boolean
    @param copy: do we want to work on a copy of the mesh
    
    @rtype:   hostApp object mesh
    @return:  triangulated polygon mesh
    """
    #put the host code here
    return object
        
def triangulate(poly):
    """
    This function return the triangulated given polygon mesh
    
    @type  poly: hostApp object mesh
    @param poly: the hostApp obj to be decompose
    @rtype:   hostApp object mesh
    @return:  triangulated polygon mesh
    """
    #put the host code here
    return poly

def getFace(hostFace):
    """
    This function convert the hostApp polygon face format to a list
    
    @type  hostFace: hostApp face 
    @param hostFace: the hostApp face object
    @rtype:   list
    @return:  the face as list
    """
    #return [c4dface.a,c4dface.b,c4dface.c,c4dface.d]
    return hostFace

def getVertice(hostVertice):
    """
    This function convert the hostApp polygon vertice format to a list
    
    @type  hostVertice: hostApp vertice/point 
    @param hostVertice: the hostApp vertice object
    @rtype:   list
    @return:  the point/vertice as list
    """
    return hostVertice
    
def DecomposeMesh(poly,edit=True,copy=True,tri=True):
    """
    This function return the vertex coordinates, the face liste, and the normal of
    the given hostapp polygon mesh
    
    @type  poly: hostApp object mesh
    @param poly: the hostApp obj to be decompose
    @type  edit: boolean
    @param edit: make it editable
    @type  copy: boolean
    @param copy: create a copy
    @type  tri: boolean
    @param tri: triangulate before decompose

    @rtype:   list
    @return:  faces,vertices,vnormals of the mesh
    """
    
    #make it editable
    if edit :
        poly = makeEditable(poly,copy=copy)
    #triangulate
    if tri:
        poly = triangulate(poly)
    #get infos
    hostfaces = [] #poly.GetAllPolygons()
    faces = [getFace(f) for f in hostfaces]
    hostvertices = [] #poly.GetAllPoints()
    vertices = [getVertice(v) for v in hostvertices]
    hostvnormals = []#get the normal poly.CreatePhongNormals()
    vnormals=vertices[:]
    for i,f in enumerate(faces):
        #one face : 4 vertices
        for j in range(len(f)):
            vnormals[j] = getVertice(c4dvnormals[(i*4)+j])
    #remove the copy if its exist? or keep it ?
#    if edit and copy :
#        doc.SetActiveObject(poly)
#        c4d.CallCommand(100004787) #delete the obj       
    return faces,vertices,vnormals

def armature(basename, x,scn=None,root=None):
    """
    This function return the list of joins object, and their epmty parent. The joins are build
    according the AtomSet x
    
    @type  basename: string
    @param basename: name of the bones parent object
    @type  x: MolKit.AtomSet
    @param x: make it editable
    @type  scn: hostApp scene
    @param scn: the scene
    @type  root: hostApp object
    @param root: the parent

    @rtype:   list
    @return:  parent, bones
    """
    if scn is None :
        scn = getCurrentScene()
    bones=[]
    mol = x[0].top
    center = mol.getCenter()
    #create the main armature object, either an empty or an armature object if supported
    parent=None
    #for each atom position from the atomset, create a join
    for j in range(len(x)):    
        at=x[j]
        atN=at.name
        fullname = at.full_name()
        atC=at._coords[0]
        rad=at.vdwRadius
        #create the join and append it to the list
        # the bone will have name = fullname
        bone = None
        bones.append(bone)
        # the bone position is always relative to the preivous one
        relativePos=Numeric.array(atC)
        if j>0 :
            patC=Numeric.array((x[j-1]._coords[0]))   
            for i in range(3):relativePos[i]=(atC[i]-patC[i])
        else : #the first atom
            #relative should be against the master
            center=Numeric.array(center)
            for i in range(3):relativePos[i]=(atC[i]-center[i])
        #set the bone position relativePos
        #make the appropriate parenting ie bone.parent, or using the general parenting
    return parent,bones

def bindGeom2Bones(listeObject,bones):
    """
    Make a skinning. Namely bind the given bones to the given list of geometry.
    This function will joins the list of geomtry in one geometry
    
    @type  listeObjects: list
    @param listeObjects: list of object to joins
    @type  bones: list
    @param bones: list of joins
    """    
    
    if len(listeObject) >1:
        JoinsObjects(listeObject)
    else :
        ObjectsSelection(listeObject,"new")
    #2- add the joins to the selection
    ObjectsSelection(bones,"add")
    #3- bind the bones / geoms
    #put the code to bind here
#    add_armature(armObj,obj)



#To DO : extension helper and special object helper

##################################################################################
#def setupAmber(mv,name,mol,prmtopfile, type,add_Conf=True,debug = False):
#    if not hasattr(mv,'setup_Amber94'):
#        mv.browseCommands('amberCommands', package='Pmv')
#    from Pmv import amberCommands
#    amberCommands.Amber94Config = {}
#    amberCommands.CurrentAmber94 = {}
#
#    from Pmv.hostappInterface import comput_util as C
#    mv.energy = C.EnergyHandler(mv)
#    mv.energy.amber = True
#    mv.energy.mol = mol
#    mol.prname = prmtopfile
#    mv.energy.name=name	
#    def doit():
#        c1 = mv.minimize_Amber94
#        c1(name, dfpred=10.0, callback_freq='10', callback=1, drms=1e-06, maxIter=10, log=0)
#    mv.energy.doit=doit
#    if add_Conf:
#            confNum = 1
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
#    mv.setup_Amber94(mol.name+":",name,prmtopfile,indice=mol.cconformationIndex)
#    mv.minimize_Amber94(name, dfpred=10.0, callback_freq='10', callback=1, drms=1e-06, maxIter=100., log=0)	
#	
#def cAD3Energies(mv,mols,atomset1,atomset2,add_Conf=False,debug = False):
#    from Pmv.hostappInterface import comput_util as C
#    mv.energy = C.EnergyHandler(mv)
#    mv.energy.add(atomset1,atomset2)#type=c_ad3Score by default
#    #mv.energy.add(atomset1,atomset2,type = "ad4Score")
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
#    if debug :
#        s1=c4d.BaseObject(c4d.Osphere)
#        s1.SetName("sphere_rec")
#        s1[PRIM_SPHERE_RAD]=2.
#        s2=c4d.BaseObject(c4d.Osphere)
#        s2.SetName("sphere_lig")
#        s2[PRIM_SPHERE_RAD]=2.
#        addObjectToScene(getCurrentScene(),s1)
#        addObjectToScene(getCurrentScene(),s2)        
#        #label
#        label = newEmpty("label")
#        label.MakeTag(LOOKATCAM)
#        addObjectToScene(getCurrentScene(),label)
#        text1 =  c4d.BaseObject(TEXT)
#        text1.SetName("score")
#        text1[2111] = "score : 0.00"
#        text1[2115] = 5.
#        text1[904,1000] = 3.14
#        text1[903,1001] = 4.
#        text2 =  c4d.BaseObject(TEXT)
#        text2.SetName("el")
#        text2[2111] = "el : 0.00"
#        text2[2115] = 5.0
#        text2[904,1000] = 3.14
#        text3 =  c4d.BaseObject(TEXT)
#        text3.SetName("hb")
#        text3[2111] = "hb : 0.00"
#        text3[2115] = 5.0
#        text3[904,1000] = 3.14
#        text3[903,1001] = -4.
#        text4 =  c4d.BaseObject(TEXT)
#        text4.SetName("vw")
#        text4[2111] = "vw : 0.00"
#        text4[2115] = 5.0
#        text4[904,1000] = 3.14
#        text4[903,1001] = -8.
#        text5 =  c4d.BaseObject(TEXT)
#        text5.SetName("so")
#        text5[2111] = "so : 0.00"
#        text5[2115] = 5.0
#        text5[904,1000] = 3.14
#        text5[903,1001] = -12.
#        addObjectToScene(getCurrentScene(),text1,parent=label)
#        addObjectToScene(getCurrentScene(),text2,parent=label)
#        addObjectToScene(getCurrentScene(),text3,parent=label)
#        addObjectToScene(getCurrentScene(),text4,parent=label)
#        addObjectToScene(getCurrentScene(),text5,parent=label)       
#    #return energy
#
#def get_nrg_score(energy,display=True):
#    #print "get_nrg_score"
#    status = energy.compute_energies()
#    #print status
#    if status is None: return
#    #print energy.current_scorer
#    #print energy.current_scorer.score
#    vf = energy.viewer
#    text = getObject("score")
#    if text != None :
#        text[2111] = "score :"+str(energy.current_scorer.score)[0:5]
#        for i,term in enumerate(['el','hb','vw','so']):
#            labelT = getObject(term)
#            labelT[2111] = term+" : "+str(energy.current_scorer.scores[i])[0:5]
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
##################################################################################
#def c4dMat2numpy(c4dmat,center=None):
#    """a c4d matrice is 
#    v1 	X-Axis
#    v2 	Y-Axis
#    v3 	Z-Axis
#    off 	Position
#    a numpy matrice is a regular 4x4 matrice (3x3rot+trans)
#    """
#    import numpy
#    import c4d
#    #print "ok convertMAtrix"
#    from numpy import matrix
#    from Pmv.hostappInterface import comput_util as C
#    #m = numpy.identity(4).astype('f') 
#    #M=matrix(m)
#    euler = c4d.tools.matrix_to_hpb(c4dmat) #heading,att,bank need to inverse y/z left/righ hand problem
#    #print "euler",euler
#    matr = numpy.array(C.eulerToMatrix([euler.x,euler.z,euler.y]))
#    #M[0:3,0:3]=matr
#    trans = c4dmat.off
#    #matr[3]= [trans.x,trans.z,trans.y,1.]
#    matr[:3,3] = [trans.x,trans.z,trans.y]
#    if center != None :
#        matr[3][0] =  matr[3][0] - center[0]
#        matr[3][1] =  matr[3][1] - center[1]
#        matr[3][2] =  matr[3][2] - center[2]
#    M = matrix(matr)
#    #print M
#    IM = M.I
#    return numpy.array(M),numpy.array(IM)
#    
#def matrix2c4dMat(mat,transpose = True):
#	import c4d
#	from Pmv.hostappInterface import comput_util as C
#    #why do I transpose ?? => fortran matrix ..
#	if transpose :
#	    mat = Numeric.array(mat).transpose().reshape(16,)
#	else :
#	    mat = Numeric.array(mat).reshape(16,)
#	r,t,s = C.Decompose4x4(mat)  	
#	#Order of euler angles: heading first, then attitude/pan, then bank
#	axis = C.ApplyMatrix(Numeric.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]),r.reshape(4,4))
#	#r = numpy.identity(4).astype('f')
#	#M = matrix(matr)
#	#euler = C.matrixToEuler(mat[0:3,0:3])
#	#mx=c4d.tools.hpb_to_matrix(c4d.Vector(euler[0],euler[1]+(3.14/2),euler[2]), c4d.tools.ROT_HPB)
#	v_1 = c4dv(r.reshape(4,4)[2,:3])
#	v_2 = c4dv(r.reshape(4,4)[1,:3])
#	v_3 = c4dv(r.reshape(4,4)[0,:3])
#	offset = c4dv(t)
#	mx = c4d.Matrix(offset,v_1, v_2, v_3)
#	#mx.off = offset
#	return mx
#
#def updateLigCoord(mol):
#    from Pmv.hostappInterface import comput_util as C
#    #fake update...reset coord to origin
#    mol.allAtoms.setConformation(0)
#    #get the transformation
#    name = mol.geomContainer.masterGeom.chains_obj[mol.chains[0].name]
#    mx = getObject(name).get_ml()
#    mat,imat = c4dMat2numpy(mx)
#    vt = C.transformedCoordinatesWithMatrice(mol,mat)
#    mol.allAtoms.updateCoords(vt,ind=mol.cconformationIndex)
#    #coords = mol.allAtoms.coords        
#    #mol.allAtoms.updateCoords(coords,ind=mol.cconformationIndex)
#    mol.allAtoms.setConformation(0)
#
#def updateMolAtomCoord(mol,index=-1):
#    #just need that cpk or the balls have been computed once..
#    #balls and cpk should be linked to have always same position
#    # let balls be dependant on cpk => contraints? or update
#    # the idea : spline/dynamic move link to cpl whihc control balls
#    # this should be the actual coordinate of the ligand
#    # what about the rc...
#    vt = []
#    sph = mol.geomContainer.geoms['cpk'].obj
#    for name in sph:
#        o = getObject(name)
#        pos=o.GetMg().off
#        vt.append([pos.x,pos.z,pos.y])
#	if index == -1 : index = 0	
#    mol.allAtoms.updateCoords(vt,ind=index)
#    
###############################AR METHODS#######################################
#def ARstep(mv):
#    #from Pmv.hostappInterface import comput_util as C
#    mv.art.beforeRedraw()
#    #up(self,dialog)
#    for arcontext in mv.art.arcontext :
#        for pat in arcontext.patterns.values():
#            if pat.isdetected:
#                #print pat
#                geoms_2_display = pat.geoms
#                transfo_mat = pat.mat_transfo[:]
#                #print transfo_mat[12:15]
#                for geom in geoms_2_display :
#                        if hasattr(pat,'offset') : offset = pat.offset[:]
#                        else : offset =[0.,0.,0.]
#                        transfo_mat[12] = (transfo_mat[12]+offset[0])* mv.art.scaleDevice
#                        transfo_mat[13] = (transfo_mat[13]+offset[1])* mv.art.scaleDevice
#                        transfo_mat[14] = (transfo_mat[14]+offset[2])* mv.art.scaleDevice
#                        mat = transfo_mat.reshape(4,4)
#                        model = geom.obj
#                        #print obj.GetName()
#                        #r,t,s = C.Decompose4x4(Numeric.array(mat).reshape(16,))
#                        #print t
#                        #newPos = c4dv(t)
#                        #model.SetPos(newPos)
#                        #model.Message(c4d.MSG_UPDATE)
#                        setObjectMatrix(model,mat)
#                        #updateAppli()
# 
#def ARstepM(mv):
#    #from Pmv.hostappInterface import comput_util as C
#    from mglutil.math import rotax
#    mv.art.beforeRedraw()
#    #up(self,dialog)
#    for arcontext in mv.art.arcontext :
#        for pat in arcontext.patterns.values():
#            if pat.isdetected:
#                #print pat
#                geoms_2_display = pat.geoms
#                m = pat.moveMat[:]
#                #print transfo_mat[12:15]
#                for geom in geoms_2_display :
#                        #if hasattr(pat,'offset') : offset = pat.offset[:]
#                        #else : offset =[0.,0.,0.]
#                        #apply the scale/interpolate
#                        #transfo_mat[12:15]*= mv.art.scaleDevice
##                        r,t,s=C.Decompose4x4(m.reshape(16,))
##                        Mat =  Numeric.identity(4, 'f')
##                        Mat[:3,:3]=(r.reshape(4,4)).astype(Numeric.Float32)[:3,:3]
##                        q = C.q_from_col_matrix(Mat)
##                        if mv.art.scaleDevice < 1.0:
##                            quat = C.quaternion_slerp([0.,0.,0.,1.], q, 
##                                                       mv.art.scaleDevice, 
##                                                       spin=0, 
##                                                       shortestpath=False)
##                        else :
##                            quat = q
##                        mtrans=t*mv.art.scaleDevice
##                        newMat=Numeric.array(C.quat_to_matrix(quat)).reshape(4,4)
##                        newMat[3][0] = mtrans[0]
##                        newMat[3][1] = mtrans[1]
##                        newMat[3][2] = mtrans[2]
#                        newMat=rotax.interpolate3DTransform([m.reshape(4,4)], [1], 
#                                                            mv.art.scaleDevice)
#                        #rotax.interpolate3DTransform1([m], [0], mv.art.scaleDevice)
#                        #transfo_mat[12] = (transfo_mat[12]+offset[0])* mv.art.scaleDevice
#                        #transfo_mat[13] = (transfo_mat[13]+offset[1])* mv.art.scaleDevice
#                        #transfo_mat[14] = (transfo_mat[14]+offset[2])* mv.art.scaleDevice
#                        #mat = transfo_mat.reshape(4,4)
#                        model = geom.obj
#                        #print obj.GetName()
#                        #r,t,s = C.Decompose4x4(Numeric.array(mat).reshape(16,))
#                        #print t
#                        #newPos = c4dv(t)
#                        #model.SetPos(newPos)
#                        #model.Message(c4d.MSG_UPDATE)
#                        #need to concat
#                        concatObjectMatrix(model,newMat)
#                        #updateAppli()
# 
#def ARloop(mv,ar=True,im=None,ims=None,max=1000):
#    count = 0	
#    while count < max:
#        #print count
#        if im is not None:
#            updateImage(mv,im,scale=ims)
#        if ar : 
#            ARstep(mv)
#        update()
#        count = count + 1
#
#def AR(mv,v=None,ar=True):#,im=None,ims=None,max=1000):
#    count = 0	
#    while 1:
#        #print count
#        if v is not None:
#            #updateBmp(mv,bmp,scale=None,show=False,viewport=v)
#            updateImage(mv,viewport=v)
#        if ar : 
#            ARstepM(mv)
#        #update()
#        count = count + 1
#
#
#Y=range(480)*640
#Y.sort()
#
#X=range(640)*480
#
#
##import StringIO
##im = Image.open(StringIO.StringIO(buffer))
##helper.updateImage(self,viewport=Right,order=[1, 2, 3, 1])
#def updateImage(mv,viewport=None,order=[1, 2, 3, 1]):
#    import Image
#    cam = mv.art.arcontext[0].cam
#    mv.art.arcontext[0].cam.lock.acquire()
#    #array = Numeric.array(cam.im_array[:])    
#    #n=int(len(array)/(cam.width*cam.height))
#    im = Image.fromstring('RGBA',(mv.art.video.width,mv.art.video.height),
#                           cam.im_array.tostring())
#    #cam.lock.release()
#    rgba = im.split()
#    new = Image.merge("RGBA", (rgba[order[0]],rgba[order[1]],rgba[order[2]],rgba[order[3]]))
#    new.save("/tmp/arpmv.jpg")
#    if viewport is not None : 
#        viewport[c4d.symbols.BASEDRAW_DATA_PICTURE] = "/tmp/arpmv.jpg"
#    cam.lock.release()
#    
#def updateBmp(mv,bmp,scale=None,order=[3, 2, 2, 1],show=True,viewport=None):
#    #cam.lock.acquire()
#    #dialog.keyModel.Set(imarray=cam.im_array.copy())
#    #cam.lock.release()
#    #import Image
#    cam = mv.art.arcontext[0].cam
#    mv.art.arcontext[0].cam.lock.acquire()
#    array = Numeric.array(cam.im_array[:])
#    mv.art.arcontext[0].cam.lock.release()
#    n=int(len(array)/(cam.width*cam.height))
#    array.shape = (-1,4)
#    map( lambda x,y,v,bmp=bmp: bmp.SetPixel(x, y, v[1], v[2], v[3]),X, Y, array)
#
#    if scale != None :
#        bmp.Scale(scale,256,False,False)
#        if show : c4d.bitmaps.ShowBitmap(scale)
#        scale.Save(name="/tmp/arpmv.jpg", format=c4d.symbols.FILTER_JPG)
#    else :
#        if show : c4d.bitmaps.ShowBitmap(bmp) 
#        bmp.Save(name="/tmp/arpmv.jpg", format=c4d.symbols.FILTER_JPG)
#    if viewport is not None:
#        viewport[c4d.symbols.BASEDRAW_DATA_PICTURE] = "/tmp/arpmv.jpg"
#       
#    


##SPECIAL OBJECT

##def metaballs(name,atoms,scn=None,root=None):
##    if scn == None:
##        scn = getCurrentScene()
##    parent = c4d.BaseObject(c4d.Onull)
##    parent.SetName(name)
##    addObjectToScene(scn,parent,parent=root)
##    mol = atoms[0].top
##    #copy of the cpk ?
##    #create the metaball objects child of the null
##    meta=c4d.BaseObject(METABALLS)
##    addObjectToScene(scn,meta,parent=parent)
##    #change the metaball parameter
##    meta[1000]=9.0#Hull Value
##    meta[1001]=0.5#editor subdivision
##    meta[1002]=0.5#render subdivision    
##    #coloring ?
##    return meta,parent
##
##
##def loftnurbs(name,mat=None):
##    loft=c4d.BaseObject(LOFTNURBS)
##    loft[1008]=0 #adaptive UV false
##    loft.SetName(name)
##    loft.MakeTag(c4d.Tphong)
##    texture = loft.MakeTag(c4d.Ttexture)
##    texture[1004]=6 #UVW Mapping    
##    #create the dedicayed material
##    if mat == None : 
##            texture[1010] = create_loft_material(name='mat_'+name)
##    else : texture[1010] = mat
##    return loft
##
##def sweepnurbs(name,mat=None):
##    loft=c4d.BaseObject(SWEEPNURBS)
##    loft.SetName(name)
##    loft.MakeTag(c4d.Tphong)
##    texture = loft.MakeTag(c4d.Ttexture)
##    #create the dedicayed material
##    if mat == None : 
##            texture[1010] = create_loft_material(name='mat_'+name)
##    else : texture[1010] = mat
##    return loft
##
##def addShapeToNurb(loft,shape,position=-1):
##    list_shape=loft.get_childs()
##    shape.insert_after(list_shape[position])
##
###def createShapes2D()
###    sh=c4d.BaseObject(dshape)
##
##def createShapes2Dspline(doc=None,parent=None):
##    circle=c4d.BaseObject(CIRCLE)
##    circle[2012]=float(0.3)
##    circle[2300]=1
##    if doc : addObjectToScene(doc,circle,parent=parent )
##    rectangle=c4d.BaseObject(RECTANGLE)
##    rectangle[2060]=float(2.2)
##    rectangle[2061]=float(0.7)
##    rectangle[2300]=1
##    if doc : addObjectToScene(doc,rectangle,parent=parent )
##    fourside=c4d.BaseObject(FOURSIDE)
##    fourside[2121]=float(2.5)
##    fourside[2122]=float(0.9)
##    fourside[2300]=1
##    if doc : addObjectToScene(doc,fourside,parent=parent )
##    shape2D={}
##    pts=[[0,0,0],[0,1,0],[0,1,1],[0,0,1]]
##    #helixshape
##    helixshape=fourside.get_real_spline()#spline('helix',pts,close=1,type=2)#AKIMA
##    helixshape.SetName('helix')
##    shape2D['Heli']=helixshape
##    #sheetshape
##    sheetshape=rectangle.get_real_spline()#spline('sheet',pts,close=1,type=0)#LINEAR
##    sheetshape.SetName('sheet')
##    shape2D['Shee']=sheetshape
##    #strandshape
##    strandshape=sheetshape.GetClone()
##    strandshape.SetName('strand')
##    shape2D['Stra']=strandshape
##    #coilshape
##    coilshape=circle.get_real_spline()#spline('coil',pts,close=1,type=4)#BEZIER
##    coilshape.SetName('coil')
##    shape2D['Coil']=coilshape
##    #turnshape
##    turnshape=coilshape.GetClone()
##    turnshape.SetName('turn')
##    shape2D['Turn']=turnshape
##    if doc : 
##        for o in shape2D.values() :
##            addObjectToScene(doc,o,parent=parent )    
##    return shape2D,[circle,rectangle,fourside,helixshape,sheetshape,strandshape,coilshape,turnshape]
##
##def createShapes2D(doc=None,parent=None):
##    if doc is None :
##        doc = getCurrentScene()    
##    shape2D={}
##    circle=c4d.BaseObject(CIRCLE)
##    circle[2012]=float(0.3)
##    circle[2300]=0
##    circle.SetName('Circle1')
##    circle2=circle.GetClone()
##    circle2.SetName('Circle2')
##    
##    coil=c4d.BaseObject(c4d.Onull)
##    coil.SetName('coil')    
##    turn=c4d.BaseObject(c4d.Onull)
##    turn.SetName('turn')
##    shape2D['Coil']=coil
##    shape2D['Turn']=turn        
##
##    addObjectToScene(doc,coil,parent=parent )
##    addObjectToScene(doc,circle,parent=coil )
##    addObjectToScene(doc,turn,parent=parent )
##    addObjectToScene(doc,circle2,parent=turn )
##
##    rectangle=c4d.BaseObject(RECTANGLE)
##    rectangle[2060]=float(2.2)
##    rectangle[2061]=float(0.7)
##    rectangle[2300]=0
##    rectangle.SetName('Rectangle1')
##    rectangle2=rectangle.GetClone()
##    rectangle2.SetName('Rectangle2')
##    
##    stra=c4d.BaseObject(c4d.Onull)
##    stra.SetName('stra')    
##    shee=c4d.BaseObject(c4d.Onull)
##    shee.SetName('shee')
##    shape2D['Stra']=stra
##    shape2D['Shee']=shee        
##
##    addObjectToScene(doc,stra,parent=parent )
##    addObjectToScene(doc,rectangle,parent=stra )
##    addObjectToScene(doc,shee,parent=parent )
##    addObjectToScene(doc,rectangle2,parent=shee )
##    
##    fourside=c4d.BaseObject(FOURSIDE)
##    fourside[2121]=float(2.5)
##    fourside[2122]=float(0.9)
##    fourside[2300]=0
##    heli=c4d.BaseObject(c4d.Onull)
##    heli.SetName('heli')    
##    shape2D['Heli']=heli    
##
##    addObjectToScene(doc,heli,parent=parent )
##    addObjectToScene(doc,fourside,parent=heli)
##    
##    return shape2D,[circle,rectangle,fourside]
##
##def getShapes2D():
##    shape2D={}
##    shape2D['Coil']=getObject('coil')
##    shape2D['Turn']=getObject('turn')
##    shape2D['Heli']=getObject('heli')
##    shape2D['Stra']=getObject('stra')        
##    return shape2D
##
##def morph2dObject(name,objsrc,target):
##    obj=objsrc.GetClone()
##    obj.SetName(name)
##    mixer=obj.MakeTag(POSEMIXER)
##    mixer[1001]=objsrc    #the default pose
##    #for i,sh in enumerate(shape2D) :
##    #    mixer[3002,1000+int(i)]=shape2D[sh]
##    mixer[3002,1000]=target#shape2D[sh] target 1
##    return obj
##   
##def c4dSpecialRibon(name,points,dshape=CIRCLE,shape2dlist=None,mat=None):
##    #if loft == None : loft=loftnurbs('loft',mat=mat)
##    shape=[]
##    pos=c4d.Vector(float(points[0][2]),float(points[0][1]),float(points[0][0]))
##    direction=c4d.Vector(float(points[0][2]-points[1][2]),float(points[0][1]-points[1][1]),float(points[0][0]-points[1][0]))
##    mx=getCoordinateMatrix(pos,direction)
##    if shape2dlist : shape.append(morph2dObject(dshape+str(0),shape2dlist[dshape],shape2dlist['Heli']))
##    else : 
##        shape.append(c4d.BaseObject(dshape))
##        if dshape == CIRCLE :
##            shape[0][2012]=float(0.3)
##            #shape[0][2300]=1
##        if dshape == RECTANGLE :
##            shape[0][2060]=float(0.3*4.)
##            shape[0][2061]=float(0.3*3.)
##            #shape[0][2300]=1
##        if dshape == FOURSIDE:
##            shape[0][2121]=float(0.3*4.)
##            shape[0][2122]=float(0.1)
##            #shape[0][2300]=0            
##    shape[0].SetMg(mx)
##    if len(points)==2: return shape
##    i=1
##    while i < (len(points)-1):
##        #print i
##        pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
##        direction=c4d.Vector(float(points[i-1][2]-points[i+1][2]),float(points[i-1][1]-points[i+1][1]),float(points[i-1][0]-points[i+1][0]))
##        mx=getCoordinateMatrix(pos,direction)
##        if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[dshape],shape2dlist['Heli']))
##        else : 
##            shape.append(c4d.BaseObject(dshape))    
##            if dshape == CIRCLE :
##                shape[i][2012]=float(0.3)
##                shape[i][2300]=2
##            if dshape == RECTANGLE :
##                shape[i][2060]=float(0.3*4.)
##                shape[i][2061]=float(0.3*3.)
##                shape[i][2300]=2
##            if dshape == FOURSIDE:
##                shape[i][2121]=float(0.3*4.)
##                shape[i][2122]=float(0.1)
##                shape[i][2300]=2            
##        shape[i].SetMg(mx)
##        i=i+1
##    pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
##    direction=c4d.Vector(float(points[i-1][2]-points[i][2]),float(points[i-1][1]-points[i][1]),float(points[i-1][0]-points[i][0]))
##    mx=getCoordinateMatrix(pos,direction)
##    if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[dshape],shape2dlist['Heli']))
##    else : 
##        shape.append(c4d.BaseObject(dshape))
##        if dshape == CIRCLE :
##            shape[i][2012]=float(0.3)
##            shape[i][2300]=2
##        if dshape == RECTANGLE :
##            shape[i][2060]=float(0.3*4.)
##            shape[i][2061]=float(0.3*3.)
##            shape[i][2300]=2        
##        if dshape == FOURSIDE:
##            shape[i][2121]=float(0.3*4.)
##            shape[i][2122]=float(0.1)
##            shape[i][2300]=2
##    shape[i].SetMg(mx)
##    return shape
##    
##def c4dSecondaryLofts(name,matrices,dshape=CIRCLE,mat=None):
##    #if loft == None : loft=loftnurbs('loft',mat=mat)
##    shape=[]            
##    i=0
##    while i < (len(matrices)):
##        #pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
##        #direction=c4d.Vector(float(points[i-1][2]-points[i+1][2]),float(points[i-1][1]-points[i+1][1]),float(points[i-1][0]-points[i+1][0]))
##        mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
##        #mx=getCoordinateMatrix(pos,direction)
##        shape.append(c4d.BaseObject(dshape))    
##        shape[i].SetMg(mx)
##        if dshape == CIRCLE :
##            shape[i][2012]=float(0.3)
##            shape[i][2300]=0
##        if dshape == RECTANGLE :
##            shape[i][2060]=float(2.2)
##            shape[i][2061]=float(0.7)
##            shape[i][2300]=0
##        if dshape == FOURSIDE:
##            shape[i][2121]=float(2.5)
##            shape[i][2122]=float(0.9)
##            shape[i][2300]=0            
##        i=i+1
##    return shape
##def instanceShape(ssname,shape2D):
##    #if shape2D=None : shape2D=createShapes2D()
##    shape=c4d.BaseObject(INSTANCE)
##    shape[1001]=shape2D[ssname[:4]]
##    shape.SetName(ssname[:4])
##    return shape
##    
##def makeShape(dshape,ssname):
##    shape=c4d.BaseObject(dshape)
##    if dshape == CIRCLE :
##                shape[2012]=float(0.3)
##                shape[2300]=0
##                shape.SetName(ssname[:4])                
##    if dshape == RECTANGLE :
##                shape[2060]=float(2.2)
##                shape[2061]=float(0.7)
##                shape[2300]=0
##                shape.SetName(ssname[:4])                    
##    if dshape == FOURSIDE:
##                shape[2121]=float(2.5)
##                shape[2122]=float(0.9)
##                shape[2300]=0
##                shape.SetName(ssname[:4])                
##    return shape
##    
##def c4dSecondaryLoftsSp(name,atoms,dshape=CIRCLE,mat=None,shape2dmorph=None,shapes2d=None,instance=False):
##    #print "ok build loft shape"
##    #if loft == None : loft=loftnurbs('loft',mat=mat)
##    shape=[]
##    prev=None    
##    ssSet=atoms[0].parent.parent.secondarystructureset
##    molname=atoms[0].full_name().split(":")[0]
##    chname=    atoms[0].full_name().split(":")[1]        
##    i=0
##    iK=0
##    #get The pmv-extruder    
##    sheet=atoms[0].parent.secondarystructure.sheet2D
##    matrices=sheet.matrixTransfo
##    if mat == None : mat = c4d.documents.GetActiveDocument().SearchMaterial('mat_loft'+molname+'_'+chname)
##    while i < (len(atoms)):
##        ssname=atoms[i].parent.secondarystructure.name
##        dshape=SSShapes[ssname[:4]]#ssname[:4]
##        #print ssname,dshape        
##        #pos=c4d.Vector(float(points[i][2]),float(points[i][1]),float(points[i][0]))
##        #direction=c4d.Vector(float(points[i-1][2]-points[i+1][2]),float(points[i-1][1]-points[i+1][1]),float(points[i-1][0]-points[i+1][0]))
##        mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
##        #mx=getCoordinateMatrix(pos,direction)
##        #iK=iK+1
##        if shape2dmorph :
##            shape.append(morph2dObject(dshape+str(i),shape2dmorph[dshape],shape2dmorph['Heli']))
##            shape[-1].SetMg(mx)
##        else :
##            #print str(prev),ssname         
##            if prev != None: #end of loop 
##                if ssname[:4] != prev[:4]:
##                    if not instance : shape.append(makeShape(SSShapes[prev[:4]],prev))
##                    else : shape.append(instanceShape(prev,shapes2d))                    
##                    shape[-1].SetMg(mx)
##            if not instance : shape.append(makeShape(dshape,ssname))
##            else : shape.append(instanceShape(ssname,shapes2d))
##            shape[-1].SetMg(mx)
##        prev=ssname
##        i=i+1
##    if mat != None:
##        prev=None
##        #i=(len(shape))
##        i=0
##        while i < (len(shape)):
##            ssname=shape[i].GetName()
##            #print ssname            
##            pos=1-((((i)*100.)/len(shape))/100.0)
##            if pos < 0 : pos = 0.
##            #print pos
##            #change the material knote according ss color / cf atom color...
##            #col=atoms[i].colors['secondarystructure']
##            col=c4dColor(SSColor[ssname])
##            nc=c4d.Vector(col[0],col[1],col[2])
##            ncp=c4d.Vector(0,0,0)            
##            if prev != None :
##                pcol=c4dColor(SSColor[prev])
##                ncp=c4d.Vector(pcol[0],pcol[1],pcol[2])        
##            #print col
##            #print ssname[:4]
##            #print prev
##            if ssname != prev : #new ss
##                grad=mat[8000][1007]    
##            #iK=iK+1
##                nK=grad.GetKnotCount()
##            #print "knot count ",nK,iK                
##                if iK >= nK :
##                    #print "insert ",pos,nK
##                    #print "grad.insert_knot(c4d.Vector("+str(col[0])+str(col[1])+str(col[2])+"), 1.0, "+str(pos)+",0.5)"
##                    if prev != None :
##                        grad.InsertKnot(ncp, 1.0, pos+0.01,0.5)
##                        iK=iK+1                                                
##                    grad.InsertKnot(nc, 1.0, pos-0.01,0.5)
##                    #grad.insert_knot(ncp, 1.0, pos+0.1,0.5)                    
##                    iK=iK+1                    
##                else :
##                    #print "set ",iK,pos    
##                    if prev != None :grad.SetKnot(iK-1,ncp,1.0,pos,0.5)                            
##                    grad.SetKnot(iK,nc,1.0,pos,0.5)
##                mat[8000][1007]=grad
##            prev=ssname
##            mat.Message(c4d.MSG_UPDATE)
##            i=i+1            
##    #mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
##    #if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[shape],shape2dlist['Heli']))
##    return shape
##
##def LoftOnSpline(name,chain,atoms,Spline=None,dshape=CIRCLE,mat=None,
##                 shape2dmorph=None,shapes2d=None,instance=False):
##    #print "ok build loft/spline"
##    molname = atoms[0].full_name().split(":")[0]
##    chname = atoms[0].full_name().split(":")[1]        
##    #we first need the spline
##    #if loft == None : loft=loftnurbs('loft',mat=mat)
##    shape=[]
##    prev=None
##    #mol = atoms[0].top	    
##    ssSet=chain.secondarystructureset#atoms[0].parent.parent.secondarystructureset
##    i=0
##    iK=0
##    #get The pmv-extruder    
##    sheet=chain.residues[0].secondarystructure.sheet2D
##    matrices=sheet.matrixTransfo
##    ca=atoms.get('CA')
##    o =atoms.get('O') 
##    if Spline is None :
##        parent=atoms[0].parent.parent.parent.geomContainer.masterGeom.chains_obj[chname]
##        Spline,ospline = spline(name+'spline',ca.coords)#
##        addObjectToScene(getCurrentScene(),Spline,parent=parent) 
##    #loftname = 'loft'+mol.name+'_'+ch.name 
##    #matloftname = 'mat_loft'+mol.name+'_'+ch.name
##    if mat == None : 
##        mat = c4d.documents.GetActiveDocument().SearchMaterial('mat_loft'+molname+'_'+chname)
##        if  mat is not None :
##            print "ok find mat"
##        #if mat == None :
##        #    mat = create_loft_material(name='mat_loft'+molname+'_'+chname)
##    print "CA",len(ca)
##    while i < (len(ca)):
##        pos= float(((i*1.) / len(ca)))
##        #print str(pos)+" %"  
##        #print atoms[i],atoms[i].parent,hasattr(atoms[i].parent,'secondarystructure')				      
##        if hasattr(ca[i].parent,'secondarystructure') : ssname=ca[i].parent.secondarystructure.name
##        else : ssname="Coil"
##        dshape=SSShapes[ssname[:4]]#ssname[:4]
##        #mx =getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
##        #have to place the shape on the spline    
##        if shape2dmorph :
##            shape.append(morph2dObject(dshape+str(i),shape2dmorph[dshape],shape2dmorph['Heli']))
##            path=shape[i].MakeTag(Follow_PATH)
##            path[1001] = Spline
##            path[1000] = 0#tangantial
##            path[1003] = pos
##            path[1007] = 2#1		axe	            
##            #shape[-1].SetMg(mx)
##        else :
##            #print str(prev),ssname         
##            #if prev != None: #end of loop 
##            #    if ssname[:4] != prev[:4]: #newSS need transition
##            #        if not instance : shape.append(makeShape(SSShapes[prev[:4]],prev))
##            #        else : shape.append(instanceShape(prev,shapes2d))                    
##            #        #shape[-1].SetMg(mx)
##            #        path=shape[-1].MakeTag(Follow_PATH)
##            #        path[1001] = Spline
##            #        path[1000] = 1    
##            #        path[1003] = pos                
##            if not instance : shape.append(makeShape(dshape,ssname))
##            else : shape.append(instanceShape(ssname,shapes2d))
##            path=shape[i].MakeTag(Follow_PATH)
##            path[1001] = Spline
##            path[1000] = 0  
##            path[1003] = pos                                           
##            path[1007] = 2#1
##            #shape[-1].SetMg(mx)        
##        if i >=1  : 
##            laenge,mx=getStickProperties(ca[i].coords,ca[i-1].coords)
##            #if i > len(o) : laenge,mx=getStickProperties(ca[i].coords,o[i-1].coords)
##            #else :laenge,mx=getStickProperties(ca[i].coords,o[i].coords)
##            shape[i].SetMg(mx)	
##        prev=ssname
##        i=i+1
##    laenge,mx=getStickProperties(ca[0].coords,ca[1].coords) 
##    #laenge,mx=getStickProperties(ca[0].coords,o[0].coords) 
##    shape[0].SetMg(mx)  		
##    if False :#(mat != None):
##        prev=None
##        #i=(len(shape))
##        i=0
##        while i < (len(shape)):
##            ssname=shape[i].GetName()
##            #print ssname            
##            pos=1-((((i)*100.)/len(shape))/100.0)
##            if pos < 0 : pos = 0.
##            #print pos
##            #change the material knote according ss color / cf atom color...
##            #col=atoms[i].colors['secondarystructure']
##            col=c4dColor(SSColor[ssname])
##            nc=c4d.Vector(col[0],col[1],col[2])
##            ncp=c4d.Vector(0,0,0)            
##            if prev != None :
##                pcol=c4dColor(SSColor[prev])
##                ncp=c4d.Vector(pcol[0],pcol[1],pcol[2])        
##            #print col
##            #print ssname[:4]
##            #print prev
##            if ssname != prev : #new ss
##                grad=mat[8000][1007]    
##            #iK=iK+1
##                nK=grad.GetKnotCount()
##            #print "knot count ",nK,iK                
##                if iK >= nK :
##                    #print "insert ",pos,nK
##                    #print "grad.insert_knot(c4d.Vector("+str(col[0])+str(col[1])+str(col[2])+"), 1.0, "+str(pos)+",0.5)"
##                    if prev != None :
##                        grad.InsertKnot(ncp, 1.0, pos+0.01,0.5)
##                        iK=iK+1                                                
##                    grad.InsertKnot(nc, 1.0, pos-0.01,0.5)
##                    #grad.insert_knot(ncp, 1.0, pos+0.1,0.5)                    
##                    iK=iK+1                    
##                else :
##                    #print "set ",iK,pos    
##                    if prev != None :grad.SetKnot(iK-1,ncp,1.0,pos,0.5)                            
##                    grad.SetKnot(iK,nc,1.0,pos,0.5)
##                mat[8000][1007]=grad
##            prev=ssname
##            mat.Message(c4d.MSG_UPDATE)
##            i=i+1            
##    #mx=getCoordinateMatrixBis(matrices[i][2],matrices[i][0],matrices[i][1])
##    #if shape2dlist : shape.append(morph2dObject(dshape+str(i),shape2dlist[shape],shape2dlist['Heli']))
##    return shape
##
##def update_2dsheet(shapes,builder,loft):
##    dicSS={'C':'Coil','T' : 'Turn', 'H':'Heli','E':'Stra','P':'Coil'}
##    shape2D=getShapes2D()
##    for i,ss in enumerate(builder):
##        if     shapes[i].GetName() != dicSS[ss]:
##            shapes[i][1001]=shape2D[dicSS[ss]]#ref object
##            shapes[i].SetName(dicSS[ss])    
##
##    texture = loft.GetTags()[0]
##    mat=texture[1010]
##    grad=mat[8000][1007]
##    grad.delete_all_knots()
##    mat[8000][1007]=grad
##
##    prev=None
##    i = 0
##    iK = 0    
##    while i < (len(shapes)):
##            ssname=shapes[i].GetName()
##            #print ssname            
##            pos=1-((((i)*100.)/len(shapes))/100.0)
##            if pos < 0 : pos = 0.
##            #print pos
##            #change the material knote according ss color / cf atom color...
##            #col=atoms[i].colors['secondarystructure']
##            col=c4dColor(SSColor[ssname])
##            nc=c4d.Vector(col[0],col[1],col[2])
##            ncp=c4d.Vector(0,0,0)            
##            if prev != None :
##                pcol=c4dColor(SSColor[prev])
##                ncp=c4d.Vector(pcol[0],pcol[1],pcol[2])        
##            #print col
##            #print ssname[:4]
##            #print prev
##            if ssname != prev : #new ss
##                grad=mat[8000][1007]    
##            #iK=iK+1
##                nK=grad.get_knot_count()
##            #print "knot count ",nK,iK                
##                if iK >= nK :
##                    #print "insert ",pos,nK
##                    #print "grad.insert_knot(c4d.Vector("+str(col[0])+str(col[1])+str(col[2])+"), 1.0, "+str(pos)+",0.5)"
##                    if prev != None :
##                        grad.insert_knot(ncp, 1.0, pos+0.01,0.5)
##                        iK=iK+1                                                
##                    grad.insert_knot(nc, 1.0, pos-0.01,0.5)
##                    #grad.insert_knot(ncp, 1.0, pos+0.1,0.5)                    
##                    iK=iK+1                    
##                else :
##                    #print "set ",iK,pos    
##                    if prev != None :grad.set_knot(iK-1,ncp,1.0,pos,0.5)                            
##                    grad.set_knot(iK,nc,1.0,pos,0.5)
##                mat[8000][1007]=grad
##            prev=ssname
##            mat.Message(c4d.MSG_UPDATE)
##            i=i+1            
## 
##
##
##    