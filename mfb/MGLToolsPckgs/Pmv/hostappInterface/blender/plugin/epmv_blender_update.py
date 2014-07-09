# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 09:36:40 2010

@author: -
"""
import Blender
from Blender import Registry
#from mglutil.hostappli import pdb_blender as epmv
from Pmv.hostappInterface.blender.blenderAdaptor import blenderAdaptor
from Pmv.hostappInterface.blender.blenderHelper import epmv

def update_Registry():
   d = {}
   d['self'] = self
   #if self.Mols : 
   #    if hasattr(self.Mols[0].geomContainer.geoms['cpk'],'obj') : 
   #        d['obj'] = self.Mols[0].geomContainer.geoms['cpk'].obj
   Blender.Registry.SetKey('bmv', d, False)

sc=Blender.Scene.GetCurrent()
self=None
rdict = Registry.GetKey('bmv', False) # True to check on disk also
if rdict and 'self' in rdict.keys() : 
   self = rdict['self']
   print "redo"
   #print self,self.Mols.name
   if self == None :
	print "self none"
	self = epmv.start(debug=1)#MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='toto', withShell= 0,verbose=False, gui = False)
	#self.embedInto('blender',debug=1)
	self.armObj = None
	#self.recentFiles = RecentFiles(self, None)
	#self.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
	#self.browseCommands('trajectoryCommands',commands=['openTrajectory'],log=0,package='Pmv')
	#self.addCommand(PlayTrajectoryCommand(),'playTrajectory',None)
	self.selections=selections
        #self.color.geomsToColor=[]
	update_Registry()
   else : 
       print "ok in registry "#,self,self.Mols.name
       #print self.Mols[0].geomContainer.masterGeom.chains_obj
       #recoverObjToGeom(sc,self)

	   #but have to clean 
       """for mol in self.Mols :
           geoms=mol.geomContainer.geoms
           for geomN in mol.geomContainer.geoms.keys():
               geom = geoms[geomN]
               if hasattr(geom,'obj'):
                   a=geom.obj			   
                   del geom.obj
               if hasattr(geom,'mesh'):
                   b=geom.mesh
                   del geom.mesh"""			
       #print self.Mols[0].geomContainer.geoms['cpk'].obj
       #print self.Mols[0].geomContainer.geoms['cpk'].mesh
       #print 'rdic ',rdict['obj']
else :
	print "no registration"
	self = epmv.start(debug=1)#MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='toto', withShell= 0,verbose=False, gui = False)
	#self.embedInto('blender',debug=1)
	self.armObj = None
    #    self.recentFiles = RecentFiles(self, None)
        #self.color.geomsToColor=[]        
	#self.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
	#self.browseCommands('trajectoryCommands',commands=['openTrajectory'],log=0,package='Pmv')
	#self.addCommand(PlayTrajectoryCommand(),'playTrajectory',None)
	#self.selections=selections
	update_Registry()

#scn = epmv.getCurrentScene()
sel = sc.objects.selected
print sel
epmv.updateCoordFromObj(self,sel,display=True,debug=True)

