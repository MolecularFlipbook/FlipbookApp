##############################################
# pmvClient.py  (c) 2009 by Ludovic Autin    #
#                                            #
# Description:                               #
#											 #
#											 #
##############################################
# from menu Py4D->Script
# or execfile('/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/mglutil/hostappli/c4dPmvScript.py')
import math
from Pmv.moleculeViewer import MoleculeViewer
import mglutil.hostappli.pdb_c4d as c4dutil

import c4d
from c4d import gui
from c4d import plugins
from c4d import documents

scene = doc = documents.get_active_document()

self = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='toto', withShell= 0,verbose=False, gui = False)
from Pmv.displayCommands import BindGeomToMolecularFragment
self.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
self.embedInto('c4d',debug=0)
#driver options
self.hostApp.driver.use_instances=True
#self.hostApp.driver.joins

exemple1=False
exemple2=True
exemple3=False
exemple4=False
#Place here your pmv command
#exemple1
if exemple1 :
    self.readMolecule('/Users/ludo/Work/goods/3gbi_rename.pdb',log=1)
    P=self.Mols[0]			#Protein    instance
    R=P.chains[0].residues		#Residue Set
    backbone = P.allAtoms
    meshes=[]
    mol=P
    sym=False
    coarse=True
    colors=[(1.0, 0.0, 0.0),
		(1.0, 0.0, 0.0),
		(1.0, 0.0, 0.0),
		(1.0, 1.0, 0.0),
		(0.0, 0.0, 1.0),
		(0.0, 0.0, 1.0),
		(0.0, 0.0, 1.0),
		]
    for i,c in enumerate(P.chains) :
		if coarse :
				print "coarseMS"		
				name="CoarseMS"+c.name
				g=c4dutil.coarseMolSurface(self,c,[32,32,32],isovalue=7.1,resolution=-0.3,name=name)
				print name
				mol.geomContainer.geoms[name]=g
				print "nmesh"
				c4dobj=c4dutil.createsNmesh(name,g.getVertices(),None,g.getFaces(),smooth=True)
				c4dobj.set_name(name)
				c4dobj.calc_vertexmap(c4dobj)
				g.obj=c4dobj
				print c4dobj
				c4dutil.addObjectToScene(doc,c4dobj)
				self.color(c, [colors[i]], [name], log=1)
		else :
				print 'MSMS'+c.name
				self.computeMSMS(c, log=1, perMol=0, display=True, surfName='MSMS'+c.name)
				print i
				self.color(c, [colors[i]], ["MSMS"+c.name], log=1)
    if sym:	  
       #Ok now create the instance object
       from symserv.utils import readInstancesMatsFromFile
       mats = readInstancesMatsFromFile('/Users/ludo/Work/goods/test.imat')	
       #geom = molecule.geomContainer.geoms['master']
       #geom.Set(instanceMatrices=matrices) 
       for i in range(len(mats)):
           #for i in range(2):
           #print i
           m=mats[i].transpose()
           mat=m.tolist()
           #print Matrix(mat[0],mat[1],mat[2],mat[3])
           #blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])
           #obparent = Blender.Object.New("Empty","Mesh_"+str(i))
           #for k,c in enumerate(P.chains) :   
                      #ob = Blender.Object.New("Mesh",str(i)+"chain_"+str(k))
                      #g=mol.geomContainer.geoms["MSMS"+c.name]
                      #ob.link(g.mesh)
                      #obparent.makeParent([ob])
                      #sc.link(ob)
                      #obparent.setMatrix(blender_mat)
           #sc.link(obparent)

#exemple2
if exemple2 :
    self.readMolecule('/Users/ludo/blenderKTF/1CRN.pdb',log=1)
    P=mol=self.getMolFromName('1CRN')			#Protein    instance
    R=P.chains[0].residues		#Residue Set
    backbone = P.allAtoms
    meshes=[]
    #self.computeSecondaryStructure(mol,topCommand=0,log=0)	
    #self.extrudeSecondaryStructure(mol,topCommand=0,log=0,display=0)
    self.displayCPK("1CRN", log=1, cpkRad=1.48333333333, quality=0, only=False, negate=False, scaleFactor=1.0)
    self.displayExtrudedSS("1CRN", negate=False, only=False,log=0)
    sheet=mol.chains[0].sheet2D['ssSheet2D']
    sheet.chords=1
    sheet.compute(sheet.coords, sheet.isHelix, nbrib=sheet.nrib, nbchords=sheet.chords, offset=sheet.offset)
    print sheet
	#smooth = Ribbon.ribbon2D(sheet.nrib, sheet.width, sheet.chords, sheet.offset, len(sheet.coords), sheet.coords,sheet.isHelix, 0.5)
    shap=c4d.BaseObject(c4d.Onull)
    shap.set_name('BaseShape')
    c4dutil.addObjectToScene(doc,shap)
    shape2d,array =c4dutil.createShapes2D()#doc=doc,parent=shap)
    for k,o in enumerate(array) :c4dutil.addObjectToScene(doc,o,parent=shap)
	   #one=c4dutil.morph2dObject('sh1',shape2d['coil'],shape2d['helix'])
    #for o in shape2d.values() : c4dutil.addObjectToScene(doc,o,parent=shap)
    #points=atoms=mol.allAtoms.get("CA").coords
    #L,sh=c4dutil.c4dSpecialRibon('LOFT',points)
    #c4dutil.addObjectToScene(doc,L)
    #for o in sh : c4dutil.addObjectToScene(doc,o,parent=L)
    atoms=mol.allAtoms.get("CA")
    spline=c4dutil.spline('spline',atoms.coords)
    c4dutil.addObjectToScene(doc,spline,parent=mol.geomContainer.masterGeom.obj)
    #self.displayExtrudedSS("1CRN", negate=False, only=False,log=0)
    loft=c4dutil.loftnurbs('loft')
    c4dutil.addObjectToScene(doc,loft)
    prev=[0.,0.,0.]
    #for i,at in enumerate(mol.allAtoms.get("CA")):
    sh=c4dutil.c4dSecondaryLoftsSp('ssSheet2D',atoms)
    for k,o in enumerate(sh) :c4dutil.addObjectToScene(doc,o,parent=loft)
		
    """		
    for ss in mol.chains[0].secondarystructureset:
        #points=ss.exElt.path3D#[1:-1]#ss.sheet2D.path
		#colors=ss.exElt.colors #color RGB for each point???
		        #start=ss.start.getPrevious()
        #if start :  points.append(start.get('CA').coords[0])
        points=[]
        for r in ss.children : points.append(r.get('CA').coords[0])
        #print ss.exElt.shape
        shape=c4dutil.SSShapes[ss.name[:4]]
        print shape
        if len(points)==1:points.insert(0,prev)
        #sh=c4dutil.c4dSpecialRibon(ss.name,points,dshape=ss.name[:4],shape2dlist=shape2d)
        sh=c4dutil.c4dSecondaryLofts(ss.name,ss.exElt.matrix,dshape=shape)
        for i,o in enumerate(sh) : #clean-up
		    #if i % 2 != 0 : 
		    #    del o
		    #    continue
		    c4dutil.addObjectToScene(doc,o,parent=loft)
        prev=points[-1]
    self.displayCPK("1CRN:::CA", log=1)
    #print atoms
    armature=c4dutil.Armature('armature',atoms,doc=doc,root=mol.geomContainer.masterGeom.obj)
    #print armature"""


			
#self.colorBySecondaryStructure("1CRN", ['secondarystructure'], log=1)
    #self.displayCPK("1CRN", log=1)
    #self.colorByAtomType("1CRN", ['cpk'], log=1)
    #self.displayCPK("1CRN", log=1, cpkRad=0.0, scaleFactor=1.0, only=False, negate=False, quality=0)
    #self.displaySticksAndBalls("1CRN", log=1, cquality=0, sticksBallsLicorice='Licorice', bquality=0, cradius=0.2, only=False, bRad=0.3, negate=False, bScale=0.0)
#exemple3
if exemple3 :
	#server/client mode
	self.hostApp.setServer('localhost',50000)
	self.hostApp.start()
if exemple4 :
    self.readMolecule('/Users/ludo/blenderKTF/loop.pdb',log=1)
    P=mol=self.getMolFromName('loop')			#Protein    instance
    R=P.chains[0].residues		#Residue Set
    backbone = P.allAtoms
    meshes=[]
    #self.displayExtrudedSS("1CRN", negate=False, only=False, log=1)
    #self.colorBySecondaryStructure("1CRN", ['secondarystructure'], log=1)
    atoms=mol.allAtoms.get("CA")
    self.displayCPK("loop:::CA", log=1)
    print atoms
    armature=c4dutil.Armature('armature',atoms,doc=doc,root=mol.geomContainer.masterGeom.obj)
    print armature
    #armature can be attached using the skin tools/object and the skin attribute
	#on mesh...so convert, then connect (cf join), then apply skin
    #self.displayExtrudedSS("1CRN", negate=False, only=False, log=1)
    #self.colorBySecondaryStructure("1CRN", ['secondarystructure'], log=1)



PolygonColorsObject(name,vertColors)
