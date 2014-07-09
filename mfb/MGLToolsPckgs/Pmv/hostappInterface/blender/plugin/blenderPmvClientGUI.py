#!BPY

"""
Name: 'Python Molecular Viewer Server-Client'
Blender: 249.2
Group: 'System'
Tooltip: 'Molecular Viewer'
"""

__author__ = "ludovic autin"
__url__ = ["www.blender.org", "blenderartists.org", "www.python.org"]
__bpydoc__ = """\
ePMV v0.1beta 
Use Blender as a molecular viewer

Connect to a regular PMV server session, and controle blender-pmv throungh the regular
interface...

1-connect to pmv server
2-controle using the pmv interface
....
"""

# -------------------------------------------------------------------------- 
# ***** BEGIN GPL LICENSE BLOCK ***** 
# 
# This program is free software; you can redistribute it and/or 
# modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation; either version 2 
# of the License, or (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program; if not, write to the Free Software Foundation, 
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA. 
# 
# ***** END GPL LICENCE BLOCK ***** 
# -------------------------------------------------------------------------- 
# TODO Fix how client react to serverCommands	

#general import
import math
import sys

MGL_ROOT=   #'/Library/MGLTools/1.5.6.csv'
sys.path[0]=(MGL_ROOT+'/lib/python2.5/site-packages')
sys.path.append(MGL_ROOT+'/lib/python2.5/site-packages/PIL')
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')

#Pmv import 
from Pmv.moleculeViewer import MoleculeViewer
from ViewerFramework.VF import LogEvent
from mglutil.util.recentFiles import RecentFiles
from Pmv.hostappInterface.blender.blenderHelper import *
from Pmv.displayCommands import BindGeomToMolecularFragment
from Pmv.hostappInterface.blender.blenderAdaptor import blenderAdaptor
#from Pmv.hostappInterface.blender import blenderHelper
from Pmv.moleculeViewer import EditAtomsEvent
from Pmv.hostappInterface import lightGridCommands as lG

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

def update_Registry():
   d = {}
   d['self'] = self
   d['epmv'] = epmv
   #if self.Mols : 
   #    if hasattr(self.Mols[0].geomContainer.geoms['cpk'],'obj') : 
   #        d['obj'] = self.Mols[0].geomContainer.geoms['cpk'].obj
   Blender.Registry.SetKey('bmv', d, False)

sc=Blender.Scene.GetCurrent()

rdict = Registry.GetKey('bmv', False) # True to check on disk also
print rdict
if rdict and 'self' in rdict.keys() : 
    self = rdict['self']
    epmv = rdict['epmv']
    if VERBOSE : print "redo"
    #print self,self.Mols.name
    if self == None :
        if VERBOSE : print "self none"
        epmv = blenderAdaptor(debug=1)
        self = epmv.mv     
        #self.armObj = None
        #self.selections=selections
        update_Registry()
    else : 
        if VERBOSE : 
            print "ok in registry ",self,self.Mols.name
            print self.Mols[0].geomContainer.masterGeom.chains_obj
else :
    if VERBOSE : print "no registration"
    epmv = blenderAdaptor(debug=1)
    self = epmv.mv
    #self.armObj = None
    #self.selections=selections
    update_Registry()


#start as a server too?
#self.browseCommands('serverCommands', commands=None, log=0, removable=True, 
#                    package='ViewerFramework')
#self.startServer()
#print self.socketComm.port

stringName = Draw.Create("")
Shapepreset = Draw.Create(1)	
Geompreset = Draw.Create(1)	
host= Draw.Create('localhost')	
port= Draw.Create('50000')
mesh= Draw.Create('Mesh')
molname= Draw.Create('')

line = [None,None,None,None,None,None,None,None,None,None]
line[0] = 5
line[1] = 35
line[2] = 65
line[3] = 95
line[4] = 125
line[5] = 155
line[6] = 185
line[7] = 215
line[8] = 245
line[9] = 275

EV_BT_OK = 1
EV_BT_CANCEL = 2
EV_ME_MOL = 3
EV_TG_ARMATURE = 4
EV_BT_REFRESH = 5
EV_ME_GEO = 6
EV_TG_JOIN = 7
EV_TG_DEL = 8
EV_BT_HOST1 = 9
EV_BT_HOST2 = 10
EV_TX_SEND1 = 11
EV_BT_SEND = 12
EV_TX_SEND2 = 13
EV_ST_PDBNAME = 14

JOIN=0
ARMATURE = 0

gnameString = ["none","coarseMolSurface","MSMS-MOL","cpk","sticks","secstruc"]

mols=self.Mols.full_name().split(',')
tmp="Mols %t|"
for i in range(len(mols)) :
	tmp+=mols[i]+'%x'+str(i)+'|'
name = tmp[:-1]

def getName():
	mols=self.Mols.full_name().split(',')
	tmp="Mols %t|"
	for i in range(len(mols)) :
		tmp+=mols[i]+'%x'+str(i)+'|'
	name = tmp[:-1]
	return name

def applyArmature():
	print "applyArmature to:"
	molList=self.Mols.full_name().split(',')
	print molList[Shapepreset.val-1]
	molName=molList[Shapepreset.val-1]
	mol=self.getMolFromName(molName)
	print mol
	string=stringName.val
	if string != "" : 
	    select=self.select(string,negate=False, only=True, xor=False, log=0, intersect=False)
	else : 
	    select=mol
	sel=select.findType(Atom)
	state=string.split(":")	
	#print len(atoms)
	if len(state) < 4 or state[3] == 'CA' : 
		    atoms=sel.get("CA")
	elif len(state[3]) == 1 :
		    atoms=sel.get(state[3])
	else : 
		    print atoms.bonds
		    print atoms
		    print "didnt find the solution yet!"
		    #atoms=sel#.get(state[3])
		    atoms.sort()			
	armObj=armature("Armature_obj",atoms,sc)
	print """* select the model, then shift select the rig
* press "control + P", to parent the rig to the model
* choose "Armature" from the pop up
* choose "Create from Bone Heat" from the next pop up
* play with your new rigged model
"""
	"""gname=gnameString[Geompreset.val-1]
	print "skin :"
	print gname
	if gname == "secstruc" : 
		for n,g in mol.geomContainer.geoms.items():
			if n[:4] in ['Heli', 'Shee', 'Coil', 'Turn', 'Stra']:
				obj=mol.geomContainer.geoms[n].obj
				print obj
				add_armature(self.armObj,obj)
	elif gname == "none" : pass
	else : 
		obj=mol.geomContainer.geoms[gname].obj
		add_armature(self.armObj,obj)
		print obj
	"""
def draw_gui():
        global host,port,Shapepreset,Geompreset,mesh,molname,stringName
	mols=self.Mols.full_name().split(',')
	tmp="Mols %t|"
	for i in range(len(mols)) :
		tmp+=mols[i]+'%x'+str(i)+'|'
	name = tmp[:-1]
	#print name
	#Draw.Toggle("Armature", EV_TG_ARMATURE, 5, line[1], 60, 25,ARMATURE, "Armature")
	BGL.glRasterPos2i(5,line[8])
	Draw.Text("Options:")
	Draw.Toggle("Join geometry", EV_TG_JOIN, 5, line[7], 60, 25,JOIN, "Join")

	Draw.PushButton("Delete Mol", EV_TG_DEL, 5, line[6], 90, 25, "DeleteMol")
	Shapepreset=Draw.Menu(name,EV_ME_MOL, 100, line[6], 90, 25, Shapepreset.val,'ON')

	Draw.PushButton("Add Armature", EV_TG_ARMATURE, 5, line[5], 90, 25, "Armature")
	Shapepreset=Draw.Menu(name,EV_ME_MOL, 100, line[5], 90, 25, Shapepreset.val,'ON')

	#gname = "Geoms %t|none %x1|MSMS-MOL %x2	|cpk %x3|sticks %x4|secstruc %x5|coarseSurf %x6"
	#Geompreset=Draw.Menu(gname,EV_ME_GEO, 195, line[5], 90, 25, Geompreset.val,'ON')

	stringName = Draw.String("sel:", EV_ST_PDBNAME, 220, line[5], 235, 25,stringName.val, 100,"selection level")

	BGL.glRasterPos2i(5,line[4])
	Draw.Text("Send Mesh to Server:")
	mesh = Draw.String("Mesh: ", EV_TX_SEND1, 5, line[3], 90, 25,mesh.val, 32, "Mesh")
	#molname= Draw.String("Mol: ", EV_TX_SEND2, 100, line[3], 90, 25,molname.val, 32, "Mol")
	Shapepreset=Draw.Menu(name,EV_ME_MOL, 100, line[3], 90, 25, Shapepreset.val,'ON')
	Draw.PushButton("SendToServer", EV_BT_SEND, 195, line[3], 90, 25, "SendGeom")

	BGL.glRasterPos2i(5,line[2])
	Draw.Text("Server:")
	host = Draw.String("Host: ", EV_BT_HOST1, 5, line[1], 90, 25,host.val, 32, "Name")
	port = Draw.String("Port: ", EV_BT_HOST2, 100, line[1], 90, 25,port.val, 32, "Portid")

	Draw.PushButton("StartCom", EV_BT_OK, 5, line[0], 90, 25, "StartThread")
	Draw.PushButton("StopCom", EV_BT_CANCEL, 100, line[0], 90, 25, "StopThread")
	Draw.PushButton("Refresh", EV_BT_REFRESH, 195, line[0], 90, 25, "Refresh")

def event(event, val) :
    if event == Draw.ESCKEY or event == Draw.QKEY:
       stop = Draw.PupMenu("OK?%t|Stop the script %x1")
       if stop == 1:
              Draw.Exit()
    #elif event == Draw.REDRAW :
	#print "Redraw"
       	#getName()
	#Draw.Redraw(1)

def button_event(evt) :
	global name,SURF,VDW,BKBONE,ARMATURE,CAT,TUBE,BSTICK,SS,COLOR1,COLOR2,JOIN
	if evt==EV_BT_OK:
		self.hostApp.setServer(host.val,eval(port.val))
		self.hostApp.start()
	elif evt==EV_BT_HOST1 or evt==EV_BT_HOST2:
		self.hostApp.setServer(host.val,eval(port.val))
	elif evt==EV_BT_CANCEL:
		self.hostApp.stop()
	elif evt==EV_TG_ARMATURE:
		#ARMATURE = 1 - ARMATURE
		applyArmature()
	elif evt==EV_BT_REFRESH:
		name = getName()
		self.runServerCommands()
		#print name
		update_Registry()
		Draw.Redraw()
		Draw.Redraw(1)
	elif evt==EV_TG_JOIN:
		JOIN = 1 - JOIN
		self.hostApp.driver.SetJoins(JOIN)
	elif evt==EV_TG_DEL:
		molList=self.Mols.full_name().split(',')
		print molList[Shapepreset.val-1]
		molName=molList[Shapepreset.val-1]
		mol=self.getMolFromName(molName)
		#self.deleteMol(mol,log=1)
	elif evt==EV_BT_SEND:
		molList=self.Mols.full_name().split(',')
		print molList[Shapepreset.val-1]
		molName=molList[Shapepreset.val-1]
		me=Blender.Mesh.Get(mesh.val)
		print me
		#if molName != '' :
		#	print molName
		#	msg=prepareMesh2Pmv(me,molname=molName)
		#else :  msg=prepareMesh2Pmv(me)
		msg=prepareMesh2Pmv(me)
		self.socketComm.sendToClients(msg)

#print "draw.register"		
Draw.Register(draw_gui, event, button_event)
