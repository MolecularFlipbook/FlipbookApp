#to launhc in ipython:
# execfile("/local/MGL/MGLTools-1.5.5/MGLToolsPckgs/mglutil/hostappli/blenderPmvScript.py")
# from commandline :
# blender155 -P blenderPmvScript.py
# from blender :
# in a text editor windows, open blenderPmvScript.py and then type Alt+P or or click run Python Script in Text menu
#general import
import math
import sys

#Pmv import 
from ViewerFramework.VF import LogEvent
from mglutil.hostappli.pdb_blender import *
import mglutil.hostappli.pdb_blender as epmv


#Blender import 
import Blender
from Blender import *
from Blender import *
from Blender.Mathutils import *
from Blender import Object
from Blender import Material
from Blender import Window, Scene, Draw
from Blender.Window import DrawProgressBar
from Blender import Registry


self=epmv.start()
mv.readMolecule('MGL.pdb',log=1)

#self = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='pmv', withShell= 0,verbose=False, gui = False)
#self.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
#self.embedInto('blender',debug=0)
#self.armObj = None

self.browseCommands('PmvInterface.artCommands', commands=('initARViewer',),package='ARViewer')
self.initARViewer(log=0)

#use join=1 to join mesh in one unic object
#self.hostApp.driver.SetJoins(1)


#Place here your pmv command
#we provide severals exemples
exemple1=False
exemple2=False
exemple3=False
exemple4=False
exemple5=False
#exemple1
if exemple1:
    self.readMolecule('3gbi_rename.pdb',log=1)
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
		name='Coarse'+c.name
		#self.computeMSMS(c, log=1, perMol=0, display=True, surfName='MSMS'+c.name)
		g=coarseMolSurface(self,c,[32,32,32],isovalue=7.1,resolution=-0.3,name='Coarse'+c.name)
		g.fullName = 'Coarse'+c.name
		mol.geomContainer.geoms[name]=g
		bl_ob,mesh=createsNmesh(name,g.getVertices(),None,g.getFaces(),smooth=True)
		sc.link(bl_ob)
		mol.geomContainer.masterGeom.obj.makeParent([bl_ob,])
		g.mesh=mesh
		g.obj=bl_ob
		self.color(c, [cols[i]], ['Coarse'+c.name], log=1)
	else :
		print 'MSMS'+c.name
		self.computeMSMS(c, log=1, perMol=0, display=True, surfName='MSMS'+c.name)
		print i
		self.color(c, [colors[i]], ["MSMS"+c.name], log=1)

#exemple2
if exemple2 :
    self.readMolecule('1CRN.pdb',log=1)
    #self.displayExtrudedSS("1CRN", negate=False, only=False, log=1)
    #self.displayCPK("1CRN", log=1, cpkRad=0.0, scaleFactor=1.0, only=False, negate=False, quality=0)
    #self.displayCPK("1CRN", log=1, cpkRad=0.0, scaleFactor=1.0, only=False, negate=True, quality=0)
    self.computeMSMS("1CRN", log=1, perMol=0, display=True, surfName='MSMS')

#exemple3
if exemple3 :
	#server/client mode
	self.hostApp.setServer('localhost',50000)
	self.hostApp.start()

if exemple4:
   self.browseCommands('serverCommands', commands=None, log=0, removable=True, package='ViewerFramework')
   self.startServer()
   print self.socketComm.port
   #self.socketComm.sendToClients(msgcmd)
   
if exemple5:
   self.browseCommands('dashboardCommands', package='Pmv', log=0)
   








