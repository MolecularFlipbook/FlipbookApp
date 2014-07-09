#to launhc in ipython:
# execfile("/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/hostappInterface/demo/pymol_like_demo.py")
# from commandline :
# blender155 -P blenderPmvScript.py
# from blender :
# in a text editor windows, open blenderPmvScript.py and then type Alt+P or or click run Python Script in Text menu
#in maya: either exexfile the file or copy/paste all the code in the script editor
#TOD :
#C4D problem of position,display of line and curve (nurb and atoms?), problem rendering bones
#MAYA lines problem, modify point clouds to particle
#blender fix memory lick for metaballs and curve ??? still Don't know why
#its seems thats this problem didnt occur on mac ??

#general import
import sys,os
#get the current software
if __name__ == "__main__":
	soft = os.path.basename(sys.argv[0]).lower()
else : 
    soft = __name__

plugin=False

if not plugin : 
    #define the python path
    import math
    MGL_ROOT="/Library/MGLTools/1.5.6.csv/"#os.environ['MGL_ROOT']
    sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
    sys.path.append(MGL_ROOT+'lib/python2.5/site-packages/PIL')
    sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
    #start epmv
    from Pmv.hostappInterface.epmvAdaptor import epmv_start
    epmv = epmv_start(soft,debug=1)
else :
    #get epmv and mv (adaptor and molecular viewer)
    if sotf == 'c4d':
        import c4d
        epmv = c4d.mv.values()[0]#[dname]
self = epmv.mv
from Pmv import hostappInterface
plgDir = hostappInterface.__path__[0]
from Pmv.hostappInterface import comput_util as util
#epmv.doCamera = False
#epmv.doLight = False
pdbname = 'pymolpept'
pdbname = '1q21'
ext = ".pdb"
demodir = plgDir+'/demo/'
demodir="/Library/MGLTools/1.5.4/MGLToolsPckgs/ARDemo/hiv/"
pdbname = '1hvr'
mext = '.dx'
demodir = "/Library/MGLTools/1.5.4/MGLToolsPckgs/ARDemo/hsg1a/"
pdbname = "hsg1"
ext=".pdbqt"
mext = '.map'
#read the molecule and store some usefull information
self.readMolecule(demodir+pdbname+ext)
mol = self.Mols[0]
mname = mol.name
sc = epmv._getCurrentScene()
masterParent = mol.geomContainer.masterGeom.obj

#MAKE THE REGULAR REPRESNETATION
self.displayLines(pdbname)
self.displaySticksAndBalls(pdbname,sticksBallsLicorice='Sticks and Balls',
                           cquality=0, bquality=0, cradius=0.2, only=False, 
                           bRad=0.3, negate=False, bScale=0.0)
self.colorByAtomType(pdbname,['sticks','balls'])
self.displayCPK(pdbname)
self.colorAtomsUsingDG(pdbname,['cpk'])
self.computeMSMS(pdbname,surfName='MSMS-MOL')
#self.computeMSMS(pdbname,surfName='MSMS-MOL',pRadius=0.8)
self.colorByResidueType(pdbname,['MSMS-MOL'])
self.displayExtrudedSS(pdbname)
self.colorBySecondaryStructure(pdbname,['secondarystructure'])

#MAKE THE SPECIAL REPRESENTATION
#CMS 
name='CoarseMS_'+mname
parent=masterParent 
geom=epmv.coarseMolSurface(mol,[32,32,32],
                           isovalue=7.1,resolution=-0.3,
                           name=name)
mol.geomContainer.geoms[name]=geom
#force binding
#self.mv.bindGeomToMolecularFragment(g, atoms)
obj=epmv._createsNmesh(name,geom.getVertices(),None,
                       geom.getFaces(),smooth=True)
epmv._addObjToGeom(obj,geom)
epmv._addObjectToScene(sc,obj[0],parent=parent)
self.colorResiduesUsingShapely(pdbname, [name])
g=mol.geomContainer.geoms[name]
#if soft=='c4d':
#    import c4d
#    #special case for c4d wihch didnt handle the color per vertex
#    #use of the graham johnson c++ plugin for color by vertex
#    colors=mol.geomContainer.getGeomColor(name)
#    pObject=epmv._getObject(name+"_color")
#    if pObject is not None :
#        sc.SetActiveObject(pObject)
#        c4d.call_command(100004787) #delete the obj
#    pObject=epmv._getObject(name+"_color")
#    if pObject is not None :
#        sc.set_active_object(pObject)
#        c4d.call_command(100004787) #delete the obj
#    elif hasattr(g,'color_obj') :
#        pObject=g.color_obj#getObject(name+"_color")
#        sc.set_active_object(pObject)
#        c4d.call_command(100004787) #delete the obj
#        g.color_obj = None
#    pObject=epmv.helper.PolygonColorsObject(name,colors)
#    g.color_obj=pObject
#    epmv._addObjectToScene(sc,pObject,parent=parent)
#    sc.set_active_object(obj[0])
#    #call the  graham J. color per vertex C++ plugin
#    c4d.call_command(1023892)    

#make a spline 
name='spline'+mol.name
atoms = mol.allAtoms.get("CA")
atoms.sort()
obSpline,spline=epmv.helper.spline(name,atoms.coords,scene=sc,parent=masterParent)

#make a ribbon/ruban using soft loft modifier in c4d
#in order to make a ribbon we need a spline, a 2dshape to extrude
ruban = epmv._makeRibbon("ribbon"+mol.name,atoms.coords,parent=masterParent)
#Attention in Blender to render and see the spline need to extrude it

#make the armature
name='armature'+mol.name
#remember to modify c4dhelper Armature -> armature and doc->scn
armature=epmv.helper.armature(name,atoms,scn=sc,root=masterParent)

#make the metaballs
name='metaballs'+mol.name
atoms = mol.allAtoms #or a subselection of surface atoms according sas
#in maya it is just a particle system, the metaball option have to be set manually in the
#render attributes
metaballsModifyer,metaballs = epmv.helper.metaballs(name,atoms,scn=sc,root=masterParent)
#clone the cpk, make them child of the metaball object
#or do we use metaball tag ????
if soft == 'c4d':
    #again a litlle trick in C4d, seems easier to just clone the cpk, and make
    #them child of the metaball Objects
    #clone the cpk,
    mol = atoms[0].top
    cpkname = mol.geomContainer.masterGeom.chains_obj[mol.chains[0].name+"_cpk"]
    cpk = epmv._getObject(cpkname)
    cpk_copy = cpk.GetClone()
    cpk_copy.SetName("cpkMeta")
    #make them child of the metaball
    epmv._addObjectToScene(sc,cpk_copy,parent=metaballsModifyer)
    #cpk_copy
    #this can produce instability as all cpk sphere are cloned 
    #but share the same name

#make isocontour exple

self.readAny(demodir+pdbname+mext)
name = self.grids3D.keys()[-1]
print name
grid = self.grids3D[name]
self.cmol = mol  	
self.isoC.select(grid_name=name)
self.isoC(grid,name=mname+"Pos",isovalue=1.0)
self.isoC(grid,name=mname+"Neg",isovalue=-1.0)

#color it
g1 = grid.geomContainer['IsoSurf'][mname+"Pos"]
isoP = epmv._getObject(g1.obj)
g2 = grid.geomContainer['IsoSurf'][mname+"Neg"]
isoN = epmv._getObject(g2.obj)
#Attention : not done in maya 
epmv.helper.changeObjColorMat(isoN,(0.,0.,1.))
epmv.helper.changeObjColorMat(isoP,(1.,0.,0.))

#MOVE THE OBJECT on a GRID 4*3
center = mol.getCenter()
radius = util.computeRadius(mol,center)
ch=mol.chains[0]
chname = ch.full_name()
if soft == 'maya' : 
    #in maya the caracter ':' is not allow 
    #moreover begining a name by a nymber is also forbidden
    chname = chname.replace(":","_")
    line = None
else : line = mol.geomContainer.geoms[chname+'_line'][0]
#define the geom to be translated
#problem the name with maya ? have to replace :/_
lgeom=[[],[],[]]
lgeom[0].append(epmv._getObject(mol.name+"_cloudds")) 
lgeom[0].append(line)
lgeom[0].append(epmv._getObject(mol.geomContainer.masterGeom.chains_obj[ch.name+"_balls"]))
lgeom[0].append(epmv._getObject(mol.geomContainer.masterGeom.chains_obj[ch.name+"_cpk"]))

lgeom[1].append(epmv._getObject('spline'+mol.name)) #spline
lgeom[1].append(epmv._getObject('armature'+mol.name)) #bones armature
lgeom[1].append(epmv._getObject(mol.geomContainer.masterGeom.chains_obj[ch.name+"_ss"])) #cartoon
lgeom[1].append(ruban) #ribbon : simple backbone trace

msms = mol.geomContainer.geoms['MSMS-MOL'].obj
lgeom[2].append("iso") #isoContour #2geoms
lgeom[2].append(metaballs) #Metaballs
lgeom[2].append(obj[0]) #CMS
lgeom[2].append(epmv._getObject(msms)) #MSMS

print lgeom
#move it according the grid rules :
sc = 3.
x = [center[0] - (sc*radius),center[0] - (radius),center[0] + (radius),center[0] + (sc*radius)]
y = [center[1] + (sc/2*radius),center[1],center[1]-(sc/2*radius)]
z = center[2]

def position(lgeom,x,y,z,mname):
    for i in range(3):
        for j in range(4):
            print i,j
            obj = lgeom[i][j]
            #print obj
            if obj == "iso":
                coord= [x[j],y[i],z]
                g1 = grid.geomContainer['IsoSurf'][mname+"Pos"]
                isoP = epmv._getObject(g1.obj)
                g2 = grid.geomContainer['IsoSurf'][mname+"Neg"]
                isoN = epmv._getObject(g2.obj)
                epmv.helper.translateObj(isoP,coord,use_parent=False)
                epmv.helper.translateObj(isoN,coord,use_parent=False)
            elif obj != "" and obj != None:
                coord= [x[j],y[i],z]
                print obj
                epmv.helper.translateObj(obj,coord,use_parent=False)
#position(lgeom,x,y,z,mname)
