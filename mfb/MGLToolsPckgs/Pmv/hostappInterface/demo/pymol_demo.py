#general import
import sys,os

#get the current software
if __name__ == "__main__":
	soft = os.path.basename(sys.argv[0]).lower()
else : 
    soft = __name__

from Pmv import hostappInterface
plgDir = hostappInterface.__path__[0]
from Pmv.hostappInterface import comput_util as util
demodir = plgDir+'/demo/'

pdbname = '1TIMtr'
ext = ".pdb"
mext = '.dx'

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
obj=epmv._createsNmesh(name,geom.getVertices(),None,
                       geom.getFaces(),smooth=True)
epmv._addObjToGeom(obj,geom)
epmv._addObjectToScene(sc,obj[0],parent=parent)
self.colorResiduesUsingShapely(pdbname, [name])
g=mol.geomContainer.geoms[name]

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
armature,bones=epmv.helper.armature(name,atoms,scn=sc,root=masterParent)
#attach the bones to ss
listeObject=[]
#maya have name issue!
for name,g in mol.geomContainer.geoms.items():
    if name[:4] in ['Heli', 'Shee', 'Coil', 'Turn', 'Stra']:
        if soft == 'maya':
            g.obj=g.obj[1:]
        listeObject.append(g.obj)
epmv.helper.bindGeom2Bones(listeObject,bones)
#what about the ik chain?
#for i in range(len(bones)):
#    if i%10 == 0:
#        sc.SetSelection(bones[i],c4d.SELECTION_NEW)
#        c4d.CallCommand(epmv.helper.CREATEIKCHAIN)
#        cmds.ikHandle
# in blender it is automatic

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
self.isoC(grid,name=mname+"Pos",isovalue=2.5)
self.isoC(grid,name=mname+"Neg",isovalue=-2.5)

#color it
g1 = grid.geomContainer['IsoSurf'][mname+"Pos"]
isoP = epmv._getObject(g1.obj)
g2 = grid.geomContainer['IsoSurf'][mname+"Neg"]
isoN = epmv._getObject(g2.obj)
#Attention : not done in maya 
epmv.helper.changeObjColorMat(isoN,(0.,0.,1.))
epmv.helper.changeObjColorMat(isoP,(1.,0.,0.))

##MOVE THE OBJECT on a GRID 4*3
#center = mol.getCenter()
#radius = util.computeRadius(mol,center)
#ch=mol.chains[0]
#chname = ch.full_name()
#if soft == 'maya' : 
#    #in maya the caracter ':' is not allow 
#    #moreover begining a name by a nymber is also forbidden
#    chname = chname.replace(":","_")
#    line = None
#else : line = mol.geomContainer.geoms[chname+'_line'][0]
##define the geom to be translated
##problem the name with maya ? have to replace :/_
#lgeom=[[],[],[]]
#lgeom[0].append(epmv._getObject(mol.name+"_cloudds")) 
#lgeom[0].append(line)
#lgeom[0].append(epmv._getObject(mol.geomContainer.masterGeom.chains_obj[ch.name+"_balls"]))
#lgeom[0].append(epmv._getObject(mol.geomContainer.masterGeom.chains_obj[ch.name+"_cpk"]))
#
#lgeom[1].append(epmv._getObject('spline'+mol.name)) #spline
#lgeom[1].append(epmv._getObject('armature'+mol.name)) #bones armature
#lgeom[1].append(epmv._getObject(mol.geomContainer.masterGeom.chains_obj[ch.name+"_ss"])) #cartoon
#lgeom[1].append(ruban) #ribbon : simple backbone trace
#
#msms = mol.geomContainer.geoms['MSMS-MOL'].obj
#lgeom[2].append("iso") #isoContour #2geoms
#lgeom[2].append(metaballs) #Metaballs
#lgeom[2].append(obj[0]) #CMS
#lgeom[2].append(epmv._getObject(msms)) #MSMS
#
#
##let rotate the master if needed
##masterParent
##H 355.51
##P -232
##B 13.
#
#print lgeom
##move it according the grid rules :
#sc = 3.
#x = [center[0] - (sc*radius),center[0] - (radius),center[0] + (radius),center[0] + (sc*radius)]
#y = [center[1] + (sc/2*radius),center[1],center[1]-(sc/2*radius)]
#z = center[2]
#
#def position(lgeom,x,y,z,mname):
#    for i in range(3):
#        for j in range(4):
#            print i,j
#            obj = lgeom[i][j]
#            #print obj
#            if obj == "iso":
#                coord= [x[j],y[i],z]
#                g1 = grid.geomContainer['IsoSurf'][mname+"Pos"]
#                isoP = epmv._getObject(g1.obj)
#                g2 = grid.geomContainer['IsoSurf'][mname+"Neg"]
#                isoN = epmv._getObject(g2.obj)
#                epmv.helper.translateObj(isoP,coord,use_parent=False)
#                epmv.helper.translateObj(isoN,coord,use_parent=False)
#            elif obj != "" and obj != None:
#                coord= [x[j],y[i],z]
#                print obj
#                epmv.helper.translateObj(obj,coord,use_parent=False)
#position(lgeom,x,y,z,mname)