#!/usr/bin/python
#Loft,spline and Lines
#still a big problem with name ....
#cpk/b&s parenting too slow
#still some color issues / too slow!!! and dont work for sticks

import numpy
import numpy.oldnumeric as Numeric
import sys, os, os.path, struct, math, string
from math import *

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
    
from types import StringType, ListType

#Pmv Color Palette
from Pmv.pmvPalettes import AtomElements
from Pmv.pmvPalettes import DavidGoodsell, DavidGoodsellSortedKeys
from Pmv.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
from Pmv.pmvPalettes import Shapely
from Pmv.pmvPalettes import SecondaryStructureType    
from Pmv.pmvPalettes import DnaElements

from Pmv.hostappInterface import autodeskmaya as epmvmaya
from Pmv.hostappInterface import comput_util as util

import maya
from maya import cmds
import maya.OpenMaya as om


VERBOSE=0
DEBUG=1
#global PROGRESS_BAR 


#GLOBAL VARIABLE
plugDir=epmvmaya.__path__[0]
                        
RasmolAminocorrected=util.patchRasmolAminoColor()

#executeInMainThreadWithResult

def start(debug=0):
    if VERBOSE : print "start ePMV - debug ",debug
    mv = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='pmv', withShell= 0,verbose=False, gui = False)
    mv.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
    mv.browseCommands('trajectoryCommands',commands=['openTrajectory'],log=0,package='Pmv')
    mv.addCommand(PlayTrajectoryCommand(),'playTrajectory',None)
    mv.embedInto('maya',debug=debug)
    mv.userpref['Read molecules as']['value']='conformations'
    DEBUG=debug        
    return mv

def update():
    #how do I update the redraw
    cmds.refresh()
    
def checkName(name):
    invalid=[] 
    for i in range(9):
        invalid.append(str(i))       
    if name[0] in invalid:
        name= name[1:]    
    return name    

def compareSel(currentSel,molSelDic):
    for selname in molSelDic.keys():
        print "The compareSelection   ",currentSel,molSelDic[selname][3]
        #if currentSel[-1] == ';' : currentSel=currentSel[0:-1]
        if currentSel == molSelDic[selname] : return selname

def getObjectName(o):
    if type(o) == str : 
        name = o.replace(":","_").replace(" ","_").replace("'","")
    elif type(o) == unicode : name = o
    else : name=o[0]
    return name

def parseObjectName(o):
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
    #useless for maya
    pass
    
def getObject(name,doit=False):
    if name.find(":") != -1 :
        name=name.replace(":","_").replace(" ","_").replace("'","")
    if doit :
            name=cmds.ls(name)
            if len(name)==0:
                return None
            if len(name) == 1 :
                return name[0]
    return name

def deleteObject(obj):
    sc = getCurrentScene()
    try :
        print "del"
    except:
        print "problem deleting ", obj

#######Special for maya#######################
def getNode( name ):
    selectionList = om.MSelectionList() 
    selectionList.add( name ) 
    node = om.MObject() 
    selectionList.getDependNode( 0, node )
    return node

def getNodePlug( attrName, nodeObject ):
    """
    example:
    translatePlug = nameToNodePlug( "translateX", perspNode ) 
    print "Plug name: %s" % translatePlug.name() 
    print "Plug value %g" % translatePlug.asDouble()
    """
    depNodeFn = om.MFnDependencyNode( nodeObject ) 
    attrObject = depNodeFn.attribute( attrName ) 
    plug = om.MPlug( nodeObject, attrObject )
    return plug
################################################

def newEmpty(name,location=None):
    if name.find(":") != -1 : name=name.replace(":","_")
    empty=cmds.group( em=True, n=name)
    return empty

def newInstance(name,object,location=None,hostmatrice=None,matrice=None):
    #instance = None#
    #instance parent = object  
    #instance name = name
    cmds.instance(object,name=name)
    if location != None :
        #set the position of instance with location
        cmds.move(float(location[0]),float(location[1]),float(location[2]), name,
                                           absolute=True )
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
    #have to manipulate the DAG/upper transform node...
    #let just take the owner Transofrm node of the shape
    #we should be able to setAttr either 'matrix' or 'worldMatrix'
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

def addObjectToScene(doc,obj,parent=None,**kw):
    #its just namely put the object under a parent
    #return
    if obj == None : return    
    if parent is not None :
        obj=checkName(obj)
        parent=checkName(parent)    
        cmds.parent( obj, parent)
        
def addObjToGeom(obj,geom):
    if type(obj) == list or type(obj) == tuple:
        if len(obj) > 2: geom.obj=obj        
        elif len(obj) == 1: geom.obj=obj[0]
        elif len(obj) == 2:    
            geom.mesh=obj[1]
            geom.obj=obj[0]
    else : geom.obj=obj


def addCameraToScene(name,Type,focal,center,sc):
    # Create a camera and get the shape name.
    cameraName = cmds.camera(n=name)
    cameraShape = cameraName[1]
    
    # Set the focal length of the camera.
    cmds.camera(cameraShape, e=True, fl=focal)
    
    #change the location
    cmds.move(float(center[0]),float(center[1]),float(center[2]), cameraName[0], absolute=True )
    #should I rotate it 
    cmds.rotate( 0, '0', '360deg',cameraName[0] )
    # Change the film fit type.
    #cmds.camera( cameraShape, e=True, ff='overscan' )
     
def addLampToScene(name,Type,rgb,dist,energy,soft,shadow,center,sc):
    print Type
    light = cmds.pointLight(n=name)
    #cmds.pointLight(light,e=1,i=energy,rgb=rgb,ss=soft,drs=dist)
    cmds.pointLight(light,e=1,i=energy)
    cmds.pointLight(light,e=1,ss=soft)
#    cmds.pointLight(light,e=1,drs=dist)
    cmds.pointLight(light,e=1,rgb=rgb)    
    cmds.move(float(center[0]),float(center[1]),float(center[2]), light, absolute=True )
        
def toggleDisplay(ob,display):
    ob=checkName(ob)
    if display : 
        cmds.showHidden(ob)
    else :     
        cmds.hide(ob)

def translateObj(obj,position,use_parent=True):
    if len(position) == 1 : c = position[0]
    else : c = position
    #print "upadteObj"
    newPos=c#c=c4dv(c)
    o=getObject(obj)
    if use_parent : 
        parentPos = getPosUntilRoot(obj)#parent.get_pos()
        c = newPos - parentPos
        cmds.move(float(c[0]),float(c[1]),float(c[2]), o, absolute=True )
    else :
        cmds.move(float(c[0]),float(c[1]),float(c[2]), o, absolute=True )

def scaleObj(obj,sc):
    pass

def rotateObj(obj,rot):
    pass
    
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

def ObjectsSelection(listeObjects,typeSel="new"):
    """
    Modify the current object selection.
    
    @type  listeObjects: list
    @param listeObjects: list of object to joins
    @type  typeSel: string
    @param listeObjects: type of modification: new,add,...

    """    
    dic={"add":True,"new":False}
    sc = getCurrentScene()
    
    for obj in listeObjects:
        cmds.select(getObject(obj),add=dic[typeSel])

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
    cmds.select(getObject(listeObjects[0]))
    for i in range(1,len(listeObjects)):
        cmds.select(listeObjects[i],add=True)
    cmds.polyUnite()
    #no need to joins? but maybe better
    #then call the command/function that joins the object selected
#    c4d.CallCommand(CONNECT)
    

def b_matrix(array):
    return Mathutils.Matrix(array)

def b_toEuler(bmatrix):
    return bmatrix.toEuler()

AtmRadi = {"N":"1.54","C":"1.7","A":"1.7","CA":"1.7","O":"1.52","S":"1.85","H":"1.2"}

################COLOR CODE ####################################################################################################
def blenderColor(col):
    if max(col)<=1.0: col = map( lambda x: x*255, col)
    return col

def color_mesh_perVertex(mesh,colors):
    mcolors=om.MColorArray()
    iv=om.MIntArray()
    #mcolor=om.MColorArray(colors,len(colors))
    mesh.findPlug('displayColors').setBool(True)
    nv=mesh.numVertices()
    #print 'colors',colors
    #if len(colors) == 1 : 
    for i in range(nv) :
        if len(colors) == 1 : ncolor = colors[0]
        else :
            if i >= len(colors) : ncolor = [0.,0.,0.] #per face coloring... 
            else : ncolor = colors[i]    
        #print ncolor
        #if max(ncolor) < 1 : ncolor = map( lambda x: x*255, ncolor)
        col=om.MColor(float(ncolor[0]),float(ncolor[1]),float(ncolor[2]))
        #print ncolor
        mcolors.append(col)
        iv.append(int(i))
        #mesh.setVertexColor(col,int(i))
    mesh.setVertexColors(mcolors,iv)
    #else :            
    #    for i,c in enumerate(colors):
    #        if max(c)<=1.0: c = map( lambda x: x*255, c)
    #        mcolors.append(om.MColor(int(c[0]),int(c[1]),int(c[2])))
    #        iv.append(int(i))
    #    mesh.setVertexColors(mcolors,iv)
    #ob.updateSurface()
    
###################MATERIAL CODE FROM Rodrigo Araujo#####################################################################################
#see http://linil.wordpress.com/2008/01/31/python-maya-part-2/
def createMaterial( name, color, type ):
    name = name.replace(":","_")
    mat=cmds.ls(name, mat=True)
    if len(mat)==0: #create only if mat didnt exist already
        #shading group
        cmds.sets( renderable=True, noSurfaceShader=True, empty=True, name=name+"SG" )
        #material
        cmds.shadingNode( type, asShader=True, name=name )
        cmds.setAttr( name+".color", color[0], color[1], color[2], type="double3")
        cmds.connectAttr(name+".outColor", name+"SG.surfaceShader")

def addMaterial( name, color ):
    name = name.replace(":","_")
    name=checkName(name)
    mat=cmds.ls(name, mat=True)
    if len(mat)==0: #create only if mat didnt exist already
        #shading group
        cmds.sets( renderable=True, noSurfaceShader=True, empty=True, name=name+"SG" )
        #material
        # = name[1:]
        cmds.shadingNode( 'lambert', asShader=True, name=name )
        cmds.setAttr( name+".color", color[0], color[1], color[2], type="double3")
        cmds.connectAttr(name+".outColor", name+"SG.surfaceShader")
        mat = cmds.ls(name, mat=True)
    return mat

def assignMaterial (name, object):
    if type(name) is not list :
        name = name.replace(":","_")
        mat=cmds.ls(name, mat=True)
    else :
        mat = name
        name = str(name[0])
    if len(mat)==0:
        createMaterial (name, (1.,1.,1.), 'lambert')
    cmds.sets(object, edit=True, forceElement=name+"SG")

def assignNewMaterial( name, color, type, object):
    createMaterial (name, color, type)
    assignMaterial (name, object)

def colorMaterial(name, color):
    cmds.setAttr( name+".color", color[0], color[1], color[2], type="double3")

def retrieveColorMat(color): 
    from DejaVu.colors import *
    for col in cnames:
        if color ==	eval(col) :
            mat = cmds.ls(color, mat=True) #search the material of name col
            return mat	
    return None

###################SpecificMAterials#####################################################################################
def create_Atoms_materials():
    Atoms_materials={}
    for i,atms in enumerate(AtomElements.keys()):
        matname=cmds.ls(atms,mat=True)
        if len(matname) == 0 :
            createMaterial(atms, AtomElements[atms], 'lambert')
        Atoms_materials[atms]=cmds.ls(atms,mat=True)
    for i,atms in enumerate(DavidGoodsell.keys()):
        matname=cmds.ls(atms,mat=True)
        if len(matname) == 0 :
            createMaterial(atms, DavidGoodsell[atms], 'lambert')
        Atoms_materials[atms]=cmds.ls(atms,mat=True)
    return Atoms_materials
atoms_materials = create_Atoms_materials

def create_SS_materials():
    SS_materials={}
    for i,ss in enumerate(SecondaryStructureType.keys()):
        matname=cmds.ls(ss[0:4],mat=True)
        if len(matname) == 0 :
            createMaterial(ss[0:4], SecondaryStructureType[ss], 'lambert')
        SS_materials[ss[0:4]]=cmds.ls(ss[0:4],mat=True)
    return SS_materials
SS_materials = create_SS_materials

def create_Residus_materials(doc=None):
      Residus_materials={}
      for i,res in enumerate(RasmolAminocorrected.keys()):#ResidueSelector.r_keyD.keys()):
           matname=cmds.ls(res,mat=True)
           if len(matname) == 0 :
               createMaterial(res, RasmolAminocorrected[res], 'lambert')
           Residus_materials[res]=cmds.ls(res,mat=True)
      matname=cmds.ls("hetatm",mat=True)
      if len(matname) == 0 :
          createMaterial("hetatm", (0.,1.0,0.), 'lambert')
      Residus_materials["hetatm"]=cmds.ls(res,mat=True)
      return Residus_materials 
Residus_materials = create_Residus_materials

def getMaterials():
    Material={}
    Material["atoms"]=atoms_materials()
    Material["residus"]=Residus_materials()
    Material["ss"]=SS_materials()
    #Material["sticks"]=sticks_materials()
    #Material["loft"]=create_loft_material()
    return Material   

def getMaterialListe():
    #return unicode list of material
    #mat=getMaterials()
    matlist=cmds.ls(mat=True)#[]
    return matlist

#def create_sticks_materials():
###################COLOR METHOD##########################################################################################                                                                        
def splitName(name):
    if name[0] == "T" : #sticks name.. which is "T_"+chname+"_"+Resname+"_"+atomname+"_"+atm2.name\n'
        #name1="T_"+mol.name+"_"+n1[1]+"_"+n1[2]+"_"+n1[3]+"_"+atm2.name
        tmp=name.split("_")
        return ["T",tmp[1],tmp[2],tmp[3][0:1],tmp[3][1:],tmp[4]]
    else :    
        tmp=name.split("_")
        indice=tmp[0]#.split("_")[0]
        molname=tmp[1]#.split("_")[1]
        chainname=tmp[2]
        residuename=tmp[3][0:3]
        residuenumber=tmp[3][3:]
        atomname=tmp[4]
    return [indice,molname,chainname,residuename,residuenumber,atomname]

def changeMaterialSchemColor(typeMat):
    mat=getMaterials()
    if typeMat == "ByAtom":
        for atms in AtomElements.keys() : colorMaterial(atms,AtomElements[atms])
    elif typeMat == "AtomsU" :
        for atms in DavidGoodsell.keys() :colorMaterial(atms,DavidGoodsell[atms])
              #if (atms == "P") or (atms == "A") or (atms == "CA"): colorMaterial(atms[0],AtomElements[atms])
              #else : 
              #colorMaterial(atms,DavidGoodsell[atms])
    elif typeMat == "ByResi":
        for res in RasmolAminocorrected.keys(): colorMaterial(res,RasmolAminocorrected[res])
    elif typeMat == "Residu":
        for res in Shapely.keys(): colorMaterial(res,Shapely[res])
    elif typeMat == "BySeco":
        for ss in SecondaryStructureType.keys(): colorMaterial(ss[0:4],SecondaryStructureType[ss])
    else : pass

def checkChangeStickMaterial(o,type,**kw):
    pass

#ssk=['Heli', 'Shee', 'Coil', 'Turn', 'Stra']
def checkChangeMaterial(o,typeMat,atom=None,parent=None,color=None):
    #print o
    #print typeMat
    #print "checkChangeMaterial"
    matlist = getMaterialListe()
    ss="Helix"
    if atom != None :
        res=atom.getParentOfType(Residue)
        ch = atom.getParentOfType(Chain)
        mol = atom.getParentOfType(Protein)
        if hasattr(res,"secondarystructure") : ss=res.secondarystructure.name
    names=splitName(o)
    #how to get material of object?
    matname = cmds.listConnections(cmds.listHistory(o,f=1),type='lambert')
    changeMaterialSchemColor(typeMat)
    if typeMat == "" or typeMat == "ByProp": #color by color or by prop
        if parent != None : requiredMatname = 'mat'+parent#.name #exemple mat_molname_cpk
        else : requiredMatname = 'mat'+o#exemple mat_coil1a_molname
        if typeMat == "ByProp": requiredMatname = 'mat'+o
        if requiredMatname not in matlist: createMaterial(requiredMatname, color, 'lambert')
        else : colorMaterial(requiredMatname,color)
        assignMaterial(requiredMatname,o)
    elif typeMat == "ByAtom" :
        #would it be more efficient to just change the color and use one shade for every
        #object?
        #need to check if already Atom based
        assignMaterial(atom.name[0],o)
    elif typeMat =="AtomsU" :
        assignMaterial(util.lookupDGFunc(atom),o)
    elif typeMat == "ByResi" or typeMat == "Residu":
        rname = res.type.strip()
        if rname in ['A', 'C', 'G', 'T', 'U'] :
            rname = 'D'+rname            
        if matname not in RasmolAminocorrected.keys() : #switch to residues materials
            if rname not in RasmolAminocorrected.keys(): 
                rname='hetatm'
            assignMaterial(rname,o)
    elif typeMat == "BySeco" :
        assignMaterial(ss[0:4],o)
    elif typeMat == "ByChai" : #swith chain material
        #print matname,ch.material
        if matname is not ch.material :
            assignMaterial(ch.material,o)
            
def changeObjColorMat(obj,color):
    #obj should be the object name, in case of mesh
    #in case of spher/cylinder etc...atom name give the mat name
    #thus  matname should be 'mat_'+obj
    matname = "mat_"+str(obj)
    colorMaterial(matname,color)
        
def changeColor(geom,colors,perVertex=True,perObjectmat=None,pb=False):
    #if hasattr(geom,'obj'):obj=geom.obj
    #else : obj=geom
    if hasattr(geom,'mesh'):mesh=geom.mesh#NMesh.GetRaw(geom.mesh)#geom.mesh
    else : mesh=geom    
    color_mesh_perVertex(mesh,colors)

def changeSchemColor(schem,keys,colors):
    #schem is the type of material to change
    #keys is the names of the material
    #colors is the new colors
    #ie atoms [C,N,O],[(255,255,0),(0,255,255),(0,0,255)]
    for i,name in enumerate(keys) :
        if schem == "atom":     AtomElements[name] = colors[i]     
        elif schem == "residu": RasmolAminocorrected[name] = colors[i]
        elif schem == "ss":     SecondaryStructureType[name] = colors[i]          

def changeSticksColor(geom,colors,type=None):#1 or 2 colors
    if True : return
    if hasattr(geom,'mesh'):mesh=geom.mesh
    else : mesh=geom
    #if not hasattr(mesh,'vertexColors') : mesh=geom.getData(mesh=True)
    #print mesh,mesh.name
    mesh.findPlug('displayColors').setBool(True)
    unic=False
    ncolor=None
    mcolors=om.MColorArray()
    iv=om.MIntArray()
    if len(colors)==1 : 
        #print colors    
        unic=True
        ncolor = colors[0]#blenderColor(colors[0])
    nbV=mesh.numVertices()
    split=(nbV-2)/2
    a=range(0,split)
    b=range(split,(nbV-2))
    for i in range(nv) :
        if not unic : 
            if i in a or i == (nbV-2):    ncolor = colors[0]
            elif i in b or i == (nbV-1): ncolor = colors[1]
        else : ncolor = colors[0]
        col=om.MColor(float(ncolor[0]),float(ncolor[1]),float(ncolor[2]))
        mcolors.append(col)
        iv.append(int(i))
    mesh.setVertexColors(mcolors,iv)

###################Meshs and Objects#####################################################################################                                                                        
def createBaseSphere(name="BaseMesh",quality=0,cpkRad=0.,scale=1.,radius=None,mat=None,parent=None):
    #QualitySph={"0":[64,32],"1":[5,5],"2":[10,10],"3":[15,15],"4":[20,20]"5":[25,25]} 
    #AtmRadi = {"N":"1.54","C":"1.7","O":"1.52","S":"1.85","H":"1.2"}
    AtmRadi = {"A":1.7,"N":1.54,"C":1.7,"P":1.7,"O":1.52,"S":1.85,"H":1.2}
    iMe={}
    baseparent=cmds.ls(name)
    if len(baseparent)==0:    
        baseparent=newEmpty(name)
        addObjectToScene(getCurrentScene(),baseparent,parent=parent)
        toggleDisplay(baseparent,False)
    if mat == None : mat=atoms_materials()
    for atn in  AtmRadi.keys():
        atparent=cmds.ls("Atom_"+atn)
        if len(atparent)==0:
            atparent=newEmpty(name+"_"+atn)
            addObjectToScene(getCurrentScene(),atparent,parent=baseparent)
        scaleFactor=float(cpkRad)+float(AtmRadi[atn])*float(scale)
        iMe[atn]=cmds.ls("Atom_"+atn)
        if len(iMe[atn])==0:
            iMe[atn],node=cmds.sphere(name=name+"Atom_"+atn,r=1)#float(scaleFactor) ) #nurbsphere
            addObjectToScene(getCurrentScene(),iMe[atn],parent=atparent)
            #iMe[atn]=atparent
            assignMaterial(atn, iMe[atn])
            #cmds.sets (nodeName, e=True, fe='initialShadingGroup')
#        toggleDisplay(iMe[atn],False)
    return iMe

def updateSphereMesh(geom,quality=0.0,cpkRad=0.0,scale=1.0,radius=None):
    #compute the scale transformation matrix
    AtmRadi = {"A":1.7,"N":1.54,"C":1.7,"P":1.7,"O":1.52,"S":1.85,"H":1.2}
    #print geom.mesh
    for name in geom.mesh.values() : 
        #print "UPDATE ",name," + ",name[-1]
        #need to get the makeNurbSphere node-> radius attributes
        factor=float(cpkRad)+float(AtmRadi[name[-1]])*float(scale)
        #have to update the nurbTosurface...not the node...        
        cmds.sphere(name,e=1,r=factor)
        #cmds.scale(factor, factor, factor, name,absolute=True )

def updateSphereMesh_test(geom,quality=0.0,cpkRad=0.0,scale=1.0,radius=None):
    #compute the scale transformation matrix
    if not hasattr(geom,'obj') : return
    newcoords=geom.getVertices()
    AtmRadi = {"A":1.7,"N":1.54,"C":1.7,"P":1.7,"O":1.52,"S":1.85,"H":1.2}
    for i,name in enumerate(geom.obj):
        #print "UPDATE ",name," + ",name[0][-1]
        n=str(name[0]).split("_")
        if n[-1][0] not in AtmRadi.keys(): atN="A"
        else : atN=n[-1][0]
        factor=float(cpkRad)+float(AtmRadi[atN])*float(scale)
        #have to update the nurbTosurface...not the node...        
        cmds.scale(factor, factor, factor, name,absolute=True )
        c=newcoords[i]
        cmds.move(float(c[0]),float(c[1]),float(c[2]), name, absolute=True )


def updateSphereObj(obj,coords=None):
    if obj is None or coords is None: return
    cmds.move(float(coords[0]),float(coords[1]),float(coords[2]), obj, absolute=True )
    
def updateSphereObjs(g,coords=None):
    if not hasattr(g,'obj') : return
    if coords == None :
        newcoords=g.getVertices()
    else :
        newcoords=coords
    #print "upadteObjSpheres"
    #again map function ?
    for i,nameo in enumerate(g.obj):
        c=newcoords[i]
        o=getObject(nameo)
        cmds.move(float(c[0]),float(c[1]),float(c[2]), o, absolute=True )

def instancesSphere(name,centers,radii,meshsphere,colors,scene,parent=None):
    sphs=[]
    mat = None
    if len(colors) == 1:
        mat = retrieveColorMat(colors[0])
        if mat == None:		
            mat = addMaterial('mat_'+name,colors[0])
    for i in range(len(centers)):
        sphs.append(cmds.instance(meshsphere,name=name+str(i)))
        cmds.move(float(centers[i][0]),float(centers[i][1]),float(centers[i][2]),name+str(i))
        cmds.scale(float(radii[i]),float(radii[i]),float(radii[i]), name+str(i),absolute=True )
        if mat == None : mat = addMaterial("matsp"+str(i),colors[i])
        assignMaterial(mat,name+str(i))#mat[bl.retrieveColorName(sphColors[i])]
        addObjectToScene(scene,sphs[i],parent=parent)
    return sphs

def instancesAtomsSphere(name,x,iMe,doc,mat=None,scale=1.0,Res=32,
                        R=None,join=0,geom=None,pb=False):
    sphers=[]
    k=0
    n='S'
    nn = 'cpk'
    AtmRadi = {"A":1.7,"N":1.54,"C":1.7,"P":1.7,"O":1.52,"S":1.85,"H":1.2}    
    if scale == 0.0 : scale = 1.0    
    #if mat == None : mat=create_Atoms_materials()    
    if name.find('balls') != (-1) : 
        n='B'
        nn='balls'
    #print name
    if geom is not None:
        coords=geom.getVertices()
    else :
        coords=x.coords
    #import maya
        
    #if PROGRESS_BAR != None:
    hiera = 'default'        
    mol = x[0].getParentOfType(Protein)        
    #parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])  
    for c in mol.chains:
        spher=[]
        oneparent = True 
        atoms = c.residues.atoms
        if maya.pb != None  : 
            maya.cmds.progressBar(maya.pb, edit=True, maxValue=len(atoms.coords),progress=0)
        #parent=findatmParentHierarchie(atoms[0],n,hiera)    
        for j in xrange(len(atoms.coords)):
            at=atoms[j]
            atN=at.name
            #print atN
            if atN[0] not in AtmRadi.keys(): atN="A"
            fullname = at.full_name().replace(":","_").replace(" ","_").replace("'","")
            #print fullname
            atC=at.coords#at._coords[0]
            #is theyr another way to create the instance, maybe using openMaya..
            spher.append(cmds.instance(iMe[atN[0]],name=n+"_"+fullname))
            cmds.move(float(atC[0]),float(atC[1]),float(atC[2]), n+"_"+fullname,
                    absolute=True )            
            factor=float(R)+float(AtmRadi[atN[0]])*float(scale)
            #have to update the nurbTosurface...not the node...        
            cmds.scale(factor, factor, factor, n+"_"+fullname,absolute=True )
            hierarchy=at.full_name().split(":")
            #print hierarchy
            #print mol.geomContainer.masterGeom.chains_obj
            #print hierarchy[1]+"_"+nn
            parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_"+nn])
#            p = findatmParentHierarchie(at,n,hiera)
#            if parent != p : 
#                cp = p
#                oneparent = False
#                parent = p
#            else :
#                cp = parent    
            #the parenting is realy slow...
            addObjectToScene(getCurrentScene(),spher[j],parent=parent)
            toggleDisplay(spher[j],False)
            if maya.pb != None : 
                maya.cmds.progressBar(maya.pb, edit=True, step=1)#progress=j/len(atoms.coords)*100)        
        sphers.extend(spher)
    return spher

def getStickProperties(coord1,coord2):
    x1 = float(coord1[0])
    y1 = float(coord1[1])
    z1 = float(coord1[2])
    x2 = float(coord2[0])
    y2 = float(coord2[1])
    z2 = float(coord2[2])
    laenge = math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))
    wsz = atan2((y1-y2), (x1-x2))
    wz = acos((z1-z2)/laenge)
    return laenge,wsz,wz,[float(x1+x2)/2,(y1+y2)/2,(z1+z2)/2]

def oneStick(name,coord1,coord2,instance):
    laenge,wsz,wz,pos=getStickProperties(coord1,coord2)     
    tube=cmds.instance(instance,n=name)#c4d.BaseObject(INSTANCE)
    cmds.scale( 1, 1, laenge, name,absolute=True )
    cmds.move(float(pos[0]),float(pos[1]),float(pos[2]), name, absolute=True )
    cmds.setAttr(name+'.ry',float(degrees(wz)))
    cmds.setAttr(name+'.rz',float(degrees(wsz)))
    return tube

def biStick(atm1,atm2,hiera,instance):
    doc = getCurrentScene()
    mol=atm1.getParentOfType(Protein)
    stick=[]
    c0=numpy.array(atm1.coords)
    c1=numpy.array(atm2.coords)
    vect = c1 - c0

    n1=atm1.full_name().split(":")
    n2=atm2.full_name().split(":")
#    name1="T_"+n1[1]+"_"+n1[2]+"_"+n1[3]+"_"+atm2.name
#    name2="T_"+n2[1]+"_"+n2[2]+"_"+n2[3]+"_"+atm1.name
#    name1="T_"+atm1.full_name().replace(":","_")+"_"+atm2.name
#    name2="T_"+atm2.full_name().replace(":","_")+"_"+atm1.name

    name1="T_"+mol.name+"_"+n1[1]+"_"+util.changeR(n1[2])+"_"+n1[3]+"_"+atm2.name
    name2="T_"+mol.name+"_"+n2[1]+"_"+util.changeR(n2[2])+"_"+n2[3]+"_"+atm1.name	        

    tube1 = oneStick(name1.replace(" ","_").replace("'",""),c0,(c0+(vect/2.)),instance)
    hierarchy=atm1.full_name().split(":")
    parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
    addObjectToScene(doc,tube1[0],parent=parent)
    mat=cmds.ls(atm1.name[0], mat=True)
    if mat == None :
        mat = addMaterial(atm1.name[0],[0.,0.,0.])         
    assignMaterial(atm1.name[0],tube1[0])
    tube2 = oneStick(name2.replace(" ","_").replace("'",""),(c0+(vect/2.)),c1,instance)
    hierarchy=atm2.full_name().split(":")
    parent=getObject(mol.geomContainer.masterGeom.chains_obj[hierarchy[1]+"_balls"])
    addObjectToScene(doc,tube2[0],parent=parent)
    mat=cmds.ls(atm2.name[0], mat=True)
    if mat == None :
        mat = addMaterial(atm2.name[0],[0.,0.,0.])         
    assignMaterial(atm2.name[0],tube2[0])
    return [tube1[0],tube2[0]]

def Tube(set,atms,points,faces,doc,mat=None,res=32,size=0.25,sc=1.,join=0,
         instance=None,hiera = 'perRes',bicyl=True,pb=True):
    sticks=[]
    bonds, atnobnd = set.bonds
    mol=bonds[0].atom1.getParentOfType(Protein)
    #import maya
    if maya.pb != None and pb : 
        #print "reset PB"
        maya.cmds.progressBar(maya.pb, edit=True, maxValue=len(bonds),progress=0)    
    #if mat == None : createMaterial('sticks', (0.8,0.8,0.8), 'lambert')#mat=create_sticks_materials()    
    if instance == None :            
        instance,mesh=cmds.polyCylinder(name="baseBond",axis=[0.0,0.0,1.0],r=size, sx=15, sy=15, sz=5, h=1.)
        addObjectToScene(doc,instance,parent=mol.geomContainer.masterGeom.obj)
    for i,bond in enumerate(bonds):
        if bicyl:    
            sticks.extend(biStick(bond.atom1,bond.atom2,hiera,instance))
        else :
            pass
        if maya.pb != None and pb: 
            maya.cmds.progressBar(maya.pb, edit=True, step=1)#progress=i/(len(bonds))*100)        
    return [sticks],mesh    

def updateTubeObj(atm1,atm2,bicyl=False,cradius=None):
    mol=atm1.getParentOfType(Protein)
    c0=numpy.array(atm1.coords)
    c1=numpy.array(atm2.coords)
    if bicyl :
        vect = c1 - c0
        n1=atm1.full_name().split(":")
        n2=atm2.full_name().split(":")        
        name1="T_"+mol.name+"_"+n1[1]+"_"+util.changeR(n1[2])+"_"+n1[3]+"_"+atm2.name
        name2="T_"+mol.name+"_"+n2[1]+"_"+util.changeR(n2[2])+"_"+n2[3]+"_"+atm1.name	                
#        name1="T_"+atm1.full_name()+"_"+atm2.name
#        name2="T_"+atm2.full_name()+"_"+atm1.name
        o=getObject(name1)
        updateOneSctick(o,c0,(c0+(vect/2.)),cradius=cradius)              
        o=getObject(name2)
        updateOneSctick(o,(c0+(vect/2.)),c1,cradius=cradius)              
    else :
        name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)
        o=getObject(name)
        updateOneSctick(o,c0,c1)
                        
def updateOneSctick(o,coord1,coord2,cradius=1.):
    laenge,wsz,wz,pos=getStickProperties(coord1,coord2) 
    cmds.scale( cradius, cradius, laenge, o,absolute=True )
    cmds.move(float(pos[0]),float(pos[1]),float(pos[2]), o, absolute=True )
    cmds.setAttr(o+'.ry',float(degrees(wz)))
    cmds.setAttr(o+'.rz',float(degrees(wsz)))
        
def updateTubeMeshold(atm1,atm2,bicyl=False,cradius=1.0,quality=0):
    updateTubeObj(atm1,atm2,bicyl=bicyl,cradius=cradius)

def updateTubeMesh(geom,cradius=1.0,quality=0):
    maya.cmds.polyCylinder(geom.mesh,e=True,r=cradius)
    pass#updateTubeObj(atm1,atm2,bicyl=bicyl,cradius=cradius)

def updateTubeObjs(g):
    if not hasattr(g,'obj') : return
    newpoints=g.getVertices()
    newfaces=g.getFaces()
    #print "upadteObjTubes"
    for i,o in enumerate(g.obj):
        laenge,wsz,wz,pos=getStickProperties(points[f[0]],points[f[1]]) 
        cmds.scale( 1, 1, laenge, o,absolute=True )
        cmds.move(float(pos[0]),float(pos[1]),float(pos[2]), o, absolute=True )
        cmds.setAttr(o+'.ry',float(degrees(wz)))
        cmds.setAttr(o+'.rz',float(degrees(wsz)))

def PointCloudObject(name,**kw):
    #print "cloud", len(coords)
    coords=kw['vertices']
    nface = 0    
    if kw.has_key("faces"):
        nface = len(kw['faces'])
    obj = createsNmesh(name+'ds',coords,None,[])
    return obj[0]

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
#    c4d.CallCommand(BIND)

def armature(basename, x,scn=None,root=None):
    #bones are called joint in maya
    #they can be position relatively or globally
    bones=[]
    mol = x[0].top
    center = mol.getCenter()
    parent = newEmpty(basename)
    addObjectToScene(scn,parent,parent=root)
    for j in range(len(x)):    
        at=x[j]
        atN=at.name
        fullname = at.full_name()
        atC=at.coords
        rad=at.vdwRadius
        #bones.append(c4d.BaseObject(BONE))
        relativePos=Numeric.array(atC)
#        if j>0 :
#            patC=Numeric.array((x[j-1].coords))   
#            for i in range(3):relativePos[i]=(atC[i]-patC[i])
#        else : #the first atom
#            #relative should be against the master
#            center=Numeric.array(center)
#            for i in range(3):relativePos[i]=atC[i]#(atC[i]-center[i])*0.
        joint=cmds.joint(n=fullname.replace(":","_"), p=relativePos.tolist()) #named "joint1"
        bones.append(joint)
        if scn != None :
             if j==0 : addObjectToScene(scn,bones[j],parent=parent)
             else : addObjectToScene(scn,bones[j],parent=bones[j-1])
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
    cmds.bindSkin()
    #IK:cmds.ikHandle( sj='joint1', ee='joint5', p=2, w=.5 )


def particule(name, coord):
    part,partShape=cmds.particle(n=name,p=coord)
    return partShape,part

def metaballs(name,selection,scn=None,root=None):
    atoms=selection.findType(Atom)
    #no metaball native in mauya, need to use particle set to blobby surface
    #use of the point cloud polygon object as the emmiter
    # name is on the form 'metaballs'+mol.name
    if scn == None:
        scn = getCurrentScene()
    #molname = name.split("balls")[1]
    #emiter = molname+"_cloud"    
    return particule(name, atoms.coords)
    
def splinecmds(name,coords,type="",extrude_obj=None,scene=None,parent=None):
    #Type : "sBezier", "tBezier" or ""
    if scene is None :
        scene = getCurrentScene()    
    #parent=newEmpty(name)
    curve = cmds.curve(n=name,p=coords)
    #return the name only, but create a transform node with name : name
    #and create a curveShape named curveShape1
    objName=cmds.ls("curveShape1")
    cmds.rename(objName,name+"Shape")
    if parent is not None :
        cmds.parent( name, parent)
    return name,None

def spline(name,coords,type="",extrude_obj=None,scene=None,parent=None):
    #Type : 
    if scene is None :
        scene = getCurrentScene()    
    #parent=newEmpty(name)
    shape,curve = omCurve(name,coords)
    #return the name only, but create a transform node with name : name
    #and create a curveShape named curveShape1
    if parent is not None :
        cmds.parent( name, parent)
    if extrude_obj is not None:
        # extrude profile curve along path curve using "flat" method
        # The extrude type can be distance-0, flat-1, or tube-2
        extruded=cmds.extrude( extrude_obj, name, n=name+"_extruded", et=1 ,fpt=1,upn=1)
        #setAttr "extrudedSurfaceShape1.simplifyMode" 1;
        return name,shape,extruded
    return name,shape

def update_spline(name,coords):
    pass

def omCurve(name,coords,**kw):
    #default value
    deg = 3; #Curve Degree
    ncvs = len(coords); #Number of CVs
    if kw.has_key("deg"):
        deg = kw['deg']
    spans = ncvs - deg # Number of spans
    nknots = spans+2*deg-1 # Number of knots
    controlVertices = om.MPointArray()
    knotSequences = om.MDoubleArray()
    # point array of plane vertex local positions
    for c in coords:
        p = om.MPoint(om.MFloatPoint( float(c[0]),float(c[1]),float(c[2]) ))
        #print 'point:: %f, %f, %f' % (p.x, p.y, p.z)
        controlVertices.append(p)
    
    for i in range(nknots):
    		knotSequences.append(i)
        
    curveFn=om.MFnNurbsCurve()
    
    curve = curveFn.create(controlVertices,knotSequences, deg, 
                            om.MFnNurbsCurve.kOpen, False, False)
    
    objName=cmds.ls("curve1")[0]
    cmds.rename(objName,name)
    
    nodeName = curveFn.name() #curveShape
    cmds.rename(nodeName, name+"Shape")

    return curveFn, curve
    
    
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
    #for mol, atms, in map(None, molecules, atomSets):
    #didnt support yet the selection
    #return 
    for mol in molecules:
        #check if line exist
        for ch in mol.chains:
            parent = getObject(ch.full_name())
            lines = getObject(ch.full_name()+'_line',doit=True) #is the object exist..
            #print parent,lines
            if lines == None :
                bonds, atnobnd = ch.residues.atoms.bonds
                indices = map(lambda x: (x.atom1._bndIndex_,
                                         x.atom2._bndIndex_), bonds)

                lines = createsNmesh(ch.full_name()+'_line',ch.residues.atoms.coords,
                                     None,indices)
                addObjectToScene(getCurrentScene(),lines[0],parent=parent)
            else : #need to update
                updateLines(lines, chains=ch)

def mayaVec(v):
    return om.MFloatPoint( float(v[0]),float(v[1]),float(v[2]) )

def createsNmesh(name,vertices,normal,faces,color=None,smooth=False,material=None,proxyCol=False):
    outputMesh = om.MObject()
    #print outputMesh.name()
    #cmds.rename(outputMesh.name(), name)
    #test=cmds.createNode( 'transform', n='transform1' )
    name=name.replace(":","_")
    name=name.replace("-","_")
    name=name.replace("'","")
    name=name.replace('"',"")
    #print "NMesh ",name
    numFaces = 0
    if faces is not None :
        numFaces = len(faces)
    numVertices = len(vertices)
    # point array of plane vertex local positions
    points = om.MFloatPointArray()
    for v in vertices:
        points.append(mayaVec(v))
    #mayaVertices=map(mayaVec,vertices)
    #map(points.append,mayaVertices)
    # vertex connections per poly face in one array of indexs into point array given above
    faceConnects = om.MIntArray()
    for f in faces:
        for i in f : 
             faceConnects.append(int(i))
    # an array to hold the total number of vertices that each face has
    faceCounts = om.MIntArray()    
    """for g in range(len(faces)):
        A = int(faces[g][0])
        B = int(faces[g][1])
        faceConnects.append(A)
        faceConnects.append(B)
        #lenf=3
        if len(faces[g])==2 :
            C = B
            D = B
            #faceConnects.append(C)
        elif len(faces[g])==3 : 
            C = int(faces[g][2])
            D = C
            faceConnects.append(C)
        elif len(faces[g])==4 : 
            C = int(faces[g][2])
            D = int(faces[g][3])
            faceConnects.append(C)
            faceConnects.append(D)
            #lenf=4
    for c in range(0,numFaces,1):
        faceCounts.append(len(faces[g]))#len(faces[g])
    """
    for c in range(0,numFaces,1):
        faceCounts.append(int(len(f)))
    
    #create mesh object using arrays above and get name of new mesh
    meshFS = om.MFnMesh()
    newMesh = meshFS.create(numVertices, numFaces, points, faceCounts, faceConnects, outputMesh)
    #    meshFS.updateSurface()
    nodeName = meshFS.name()
    cmds.rename(nodeName, "mesh_"+name)
    #print 'Mesh node name is: %s' % nodeName
    objName=cmds.ls("polySurface1")[0]
    cmds.rename(objName,name)
    #newName should bydefault polySurface something
    #     assign new mesh to default shading group
    if color is not None :
        color_mesh_perVertex(meshFS,color)
    if material == None :
        if len(name.split("_")) == 1 : splitname = name
        else :
            splitname = name.split("_")[1]  
        #print name,name[:4],splitname,splitname[:4]
        if splitname[:4] in [x[0:4] for x in SecondaryStructureType.keys()] : 
            mats=SS_materials()
            assignMaterial(str(splitname[:4]),"mesh_"+name)
            meshFS.findPlug('displayColors').setBool(False)
        else :
            assignNewMaterial( "mat_"+name, (1,1,1),'lambert' ,"mesh_"+name)
    else :
        assignMaterial(material,"mesh_"+name)    
    return name,meshFS#,outputMesh


def updatePoly(meshnode,vertices=None,faces=None):#chains.residues.atoms.coords,indices
    if type(meshnode) is str:
        meshnode = getObject(meshnode,doit=True)
    if meshnode is None:
        return
    nv = meshnode.numVertices()
    nf = meshnode.numPolygons()
    if vertices is not None :
        numVertices = len(vertices)
        # point array of plane vertex local positions
        points = om.MFloatPointArray()
        for v in vertices:
            points.append(mayaVec(v))
    else :
        return
        #numVertices = nv
    if faces is not None :
        numFaces = len(faces)
    else :
        numFaces = nf
        faces = []
    faceConnects = om.MIntArray()
    for f in faces:
        for i in f : 
             faceConnects.append(int(i))
    # an array to hold the total number of vertices that each face has
    faceCounts = om.MIntArray()    
    for c in range(0,numFaces,1):
        faceCounts.append(int(len(f)))
    #newMesh = meshFS.create(numVertices, numFaces, points, faceCounts, faceConnects, outputMesh)
    result = meshnode.createInPlace(numVertices, numFaces, points, faceCounts, faceConnects)
    meshnode.updateSurface()    


def updateMesh(g,proxyCol=False,parent=None,mol=None):
    #print "updateMesh ",geom,geom.mesh
    vertices=g.getVertices()
    faces=g.getFaces()
    obj = g.obj
    meshnode = g.mesh
    #print mesh,obj    
    #meshobject = getNode(str(g.mesh))
    #meshnode=OpenMaya.MFnMesh(meshobject)
    updatePoly(meshnode,vertices=vertices,faces=faces)

def m2vec(v):
    return [v.z,v.y,v.x]
    
def vecp2m(v):
    #from http://www.rtrowbridge.com/blog/2009/02/maya-api-docs-demystified-for-python-users/
    doubleArray = om.MScriptUtil()
    doubleArray.createFromList( v, len(v) )
    doubleArrayPtr = doubleArray.asDoublePtr()
    vec = om.MVector( doubleArrayPtr )
    #print vec.x, vec.y, vec.z
    return vec

def vec2m(v):
     return om.MVector(v[0], v[1], v[2])
    
def matrixp2m(mat):
    #from http://www.rtrowbridge.com/blog/2009/02/python-api-mtransformationmatrixgetrotation-bug/
    getMatrix = om.MMatrix()
    matrixList = mat.reshape(16,)
    om.MScriptUtil().createMatrixFromList(matrixList, getMatrix)
    mTM = om.MTransformationMatrix( getMatrix )
    rotOrder = om.MTransformationMatrix().kXYZ
    return mTM

def m2matrix(mMat):
    return mMat

def updateCoordFromObj(mv,sIter,debug=True):
    #get what is display
    #get position object and assign coord to atoms...(c4d conformation number...or just use some constraint like avoid collision...but seems that it will be slow)    
    #print mv.Mols
    #print mv.molDispl
#    mdagPath = om.MDagPath()
#    mComponent = om.MObject()
#    spc = om.MSpace.kWorld
    #print mv.Mols
#    while not sIter.isDone():
#        # Get path and possibly a component
#        # How to get the name ?
#        sIter.getDagPath(mdagPath, mComponent)
#        print "while selection"
#        print mdagPath.fullPathName()
#        print mComponent
#        try:
#            transFn = om.MFnTransform(mdagPath)
#            print "trans ",transFn
#        except:
#            pass

#        #print s.GetName()
#        if s.GetType() == c4d.Ospline :
#            #print "ok Spline"
#            select = s.GetSelectedPoints()#mode=P_BASESELECT)#GetPointAllAllelection();
#            #print nb_points
#            selected = select.get_all(s.GetPointCount()) # 0 uns | 1 selected
#            #print selected
#            #assume one point selected ?
#            selectedPoint = selected.index(1)           
#            updateRTSpline(s,selectedPoint)
#        elif  s.GetType() == c4d.Onull :
            #print "ok null" 
            #molname or molname:chainname or molname:chain_ss ...
#            hi = parseName(s.GetName())
            #print "parsed ",hi
#            if len(hi) == 1:
#                hi=[hi[0],""]
#            molname = hi[0]
#            chname = hi[1]
            #mg = s.GetMg()
            #should work with chain level and local matrix
            #mg = ml = s.get_ml()
            #print molname
            #print mg
            #print ml
    if hasattr(mv,'energy') : #ok need to compute energy
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
                    #if rec.name == molname or lig.name == molname:
                    #updateMolAtomCoord(rec,rec.cconformationIndex)
                    updateMolAtomCoord(lig,lig.cconformationIndex)
                    if mv.energy.realTime:
                        
                        if hasattr(mv,'art'):
                            if not mv.art.frame_counter % mv.art.nrg_calcul_rate:
                                get_nrg_score(mv.energy)
                        else :
                            get_nrg_score(mv.energy)
#                if debug :
#                        matx = matrix2c4dMat(mat)
#                        imatx = matrix2c4dMat(rec.mat_transfo_inv)
#                        sr = getObject('sphere_rec')
#                        sr.SetMg(matx)
#                        sl = getObject('sphere_lig')
#                        sl.SetMg(imatx)
            #update atom coord for dedicated conformation  (add or setConf)
            #then compute some energie!

def updateMolAtomCoord(mol,index=-1):
    #just need that cpk or the balls have been computed once..
    #balls and cpk should be linked to have always same position
    # let balls be dependant on cpk => contraints? or update
    # the idea : spline/dynamic move link to cpl whihc control balls
    # this should be the actual coordinate of the ligand
    # what about the rc...
    sph = mol.geomContainer.geoms['cpk'].obj
    vt=map(lambda x:cmds.xform(x,q=1,ws=1,t=1),sph)
    if index == -1 : index = 0	
    mol.allAtoms.updateCoords(vt,ind=index)

def get_nrg_score(energy,display=True):
    #print "get_nrg_score"
    status = energy.compute_energies()
    #print status
    if status is None: return
    #print energy.current_scorer
    #print energy.current_scorer.score
    vf = energy.viewer
#    print "score :"+str(energy.current_scorer.score)[0:5]
#    for i,term in enumerate(['el','hb','vw','so']):
#        print term+" : "+str(energy.current_scorer.scores[i])[0:5]
    if hasattr(energy,'labels'):
        cmds.textCurves( energy.labels[0],e=1,t="score :"+str(energy.current_scorer.score)[0:5])
        for i,term in enumerate(['el','hb','vw','so']):
            labelT = energy.labels[i+1]
            cmds.textCurves( labelT,e=1,t=term+" : "+str(energy.current_scorer.scores[i])[0:5])
        #should make multi label for multi terms    
    # change color of ligand with using scorer energy
    if energy.display:
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

def DecomposeMesh(poly,edit=True,copy=True,tri=True):
    return None,None,None
