#execfile("/Users/ludo/Work/c4dscript/c4d_script.py")
import sys
#sys.path.append('/Library/Python/2.6/site-packages')
#sys.path.append('/Library/Python/2.6/site-packages/PIL')
#sys.path.append("/Library/MGLTools/1.5.6/MGLToolsPckgs")
#sys.path.append('/Users/ludo/Work/c4dscript')

import math
from Pmv.moleculeViewer import MoleculeViewer
from ViewerFramework.VF import LogEvent
from pdb_c4d import *

#from Pmv.displayCommands import BindGeomToMolecularFragment
from ViewerFramework.clientsCommands import Pmv_client

from c4d import plugins
from c4d import documents

import c4d

scene = doc = documents.get_active_document()

self = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='toto', withShell= 0,verbose=False, gui = False)
self.abclogfiles=open('abclog','w')
self.pmvstderr=open('pmvstderr','w')
sys.stderr=self.pmvstderr
self.addCommand(Pmv_client(), 'client', None)
#self.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
self.client.setDriver('c4d')
self.registerListener(LogEvent, self.client.handleLogEvent)
self.armObj = None
self.browseCommands('fileCommands', package="Pmv", topCommand=0)

com=True
cpk=False
coarse=False
sym=False

if coarse :
	self.readMolecule('/Users/ludo/Work/goods/3gbi_rename.pdb',log=1)
	P=self.Mols[0]			#Protein    instance
	R=P.chains[0].residues		#Residue Set
	backbone = P.allAtoms
	meshes=[]
        mol=P
	colors=[(1.0, 0.0, 0.0),
		(1.0, 0.0, 0.0),
		(1.0, 0.0, 0.0),
		(1.0, 1.0, 0.0),
		(0.0, 0.0, 1.0),
		(0.0, 0.0, 1.0),
		(0.0, 0.0, 1.0),
		]
	for i,c in enumerate(P.chains) :
		self.computeMSMS(c, log=1, perMol=0, display=True, surfName='MSMS'+c.name)
		#g=coarseMolSurface(self,c,[32,32,32],isovalue=7.2,resolution=-0.1,)
		#self.colorByAtomType("1CRN", ['CoarseMolSurface'], log=0)
		#self.color("1CRN", [(0.0, 0.0, 1.0)], ['CoarseMolSurface'], log=0)
		#name="CoarseMolSurface"+c.name
		#name="MSMS"+c.name
		#bl_ob,mesh=createsNmesh(name,g.getVertices(),None,g.getFaces(),smooth=True)
		#sc.link(bl_ob)
		#meshes.append(mesh)
		#g.mesh=mesh
		#g.obj=bl_ob
		#self.color(c, [colors[i]], ["MSMS"+c.name], log=1)

if sym:
	#Ok now create the instance object
	from symserv.utils import readInstancesMatsFromFile
	mats = readInstancesMatsFromFile('/local/ludo/Desktop/goods/test.imat')	
	#geom = molecule.geomContainer.geoms['master']
	#geom.Set(instanceMatrices=matrices)   
	for i in range(len(mats)):
	  #for i in range(2):
	  #print i
	  m=mats[i].transpose()
	  mat=m.tolist()
	  #print Matrix(mat[0],mat[1],mat[2],mat[3])
	  blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])
	  obparent = Blender.Object.New("Empty","Mesh_"+str(i))
  	  for k,c in enumerate(P.chains) :   
	   ob = Blender.Object.New("Mesh",str(i)+"chain_"+str(k))
	   g=mol.geomContainer.geoms["MSMS"+c.name]
	   ob.link(g.mesh)
	   obparent.makeParent([ob])
	   sc.link(ob)
	  obparent.setMatrix(blender_mat)
	sc.link(obparent)
	  #print ob
if com :
	#server/client mode
	self.embeded=True
	self.client.setServer('localhost',50000)
	self.client.start()

