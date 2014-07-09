# adapted to PMV and Blender by L.AUTIN
#stable version 3/31/2010

#for embeded version:
#c4d execfile("/Library/MGLTools/1.5.6/MGLToolsPckgs/mglutil/hostappli/PyRosetta-PMV.py")
#blender ar ipython run PyRosetta-PMV.py
#for regular version of pmv comment line 21
#import mglutil.hostappli.pdb_c4d as epmv

import sys,os
MGL_ROOT=os.environ['MGL_ROOT']
sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
sys.path.append(MGL_ROOT+'lib/python2.5/site-packages/PIL')
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')

from Pmv.moleculeViewer import EditAtomsEvent
import time


####################blender specific###################
import Pmv.hostappInterface.pdb_blender as epmv
import Blender
from Blender import Window, Scene, Draw
self=epmv.start(debug=1)
sc=Blender.Scene.GetCurrent()
#########################################################

import ViewerFramework.imdCommands as imd
from Pmv.moleculeViewer import EditAtomsEvent

self.readMolecule("/local/MGL/MGLTools-1.5.6/MGLToolsPckgs/ARDemo/hiv/1hvr.pdb",log=1)
#self.displayCPK('1hvr',log=1)
self.connectToImdServer.setup("localhost",2030,"1hvr")
self.connectToImdServer.doit(gui=False)

self.imd.start()

"""
from socket import *
import numpy
import time
ffreq = 10
port = 2030#1025#3000#2030
IMDmsg = 0
pause  = 0
hostname = "localhost"
mode=0 #client
wait=0 #// Connection configuration
self.browseCommands('imdCommands',package='ViewerFramework', topCommand=0)
self.imd.init(hostname, mode,wait, port, IMDmsg , 0 )
self.imd.imd_pause()
self.readMolecule("/local/tools/NAMD_2.7b2_Linux-x86/test/alanin/alanin.pdb",log=1)
#self.readMolecule("/local/tools/NAMD_2.7b2_Linux-x86/test/bpti_imd/bpti.pdb",log=1) #882atoms
#self.displayCPK('alanin',log=1)
mol = self.Mols[0]
mol.allAtoms.addConformation(mol.allAtoms.coords[:])
slot = len(mol.allAtoms[0]._coords) - 1
self.imd.mol = mol
self.imd.slot = slot
#create a handler
handlerObj=epmv.Sphere('handler',1.5,16)
self.browseCommands('handlerCommand',package='ViewerFramework', topCommand=0)
atms=mol.allAtoms[5:8]
#self.select(atms)
self.handler.create(atms,geom=handlerObj)
#self.handler.isinited = False
#print self.handler.N_forces, self.handler.atoms_list, self.handler.forces_list
#i=0
#self.imd.imd_pause()
self.imd.start() #need the updateEvent in VF ?

#self.GUI.ROOT.after(10, self.updateIMD)
while 1:
    imdheader = self.imd.imd_recv_header(self.imd.sock)
    vmd_length = imdheader.length
    imdtype = imdheader.imdtype
    #print "TYPE ",imdtype
    if imdtype == imd.IMD_ENERGIES:
        #print "energie"
        ene=imd.IMDEnergies()
        test=self.imd.imd_recv_energies(ene)
        #print ene.tstep,ene.Etot,ene.Epot,ene.Evdw,ene.Epot,ene.Eelec,ene.Eangle
    if imdtype == imd.IMD_MDCOMM:
        #print "mdcom",vmd_length
        vmd_atoms=numpy.zeros(vmd_length,'i')
        vmd_forces=numpy.zeros((vmd_length,3),'f')
        test=self.imd.imd_recv_mdcomm(vmd_length,vmd_atoms,vmd_forces)
    if imdtype == imd.IMD_FCOORDS: #with NAMD how to get the coord??
        #print "fcoord",vmd_length
        self.imd.imd_pause()
        vmd_coords=numpy.zeros((vmd_length,3),'f')
        test=self.imd.imd_recv_fcoords(vmd_length,vmd_coords)
        #update the mol coordinate,and create event
        mol.allAtoms.updateCoords(vmd_coords, slot)
        #mol.allAtoms.setConformation(slot)
        event = EditAtomsEvent('coords', mol.allAtoms)
        self.dispatchEvent(event)
        epmv.insertKeys(mol.geomContainer.geoms['cpk'],1)
        epmv.getCurrentScene().update()
        Draw.Draw()
        Draw.Redraw(1)
        Blender.Redraw()
        self.imd.imd_pause()
    if (i % ffreq) == 0 :
        handlerObj.setLocation(float(i)/10.,0.,0.)
        print handlerObj.getLocation()
        self.handler.getForces(None)
        #IIMD_send_forces       ( &N_forces, (const int* ) atoms_list, 
	#		       (const float *) forces_list );
        #print self.handler.N_forces, self.handler.atoms_list, self.handler.forces_list
        self.imd.imd_send_mdcomm(self.handler.N_forces, self.handler.atoms_list, self.handler.forces_list)
    i=i+1"""
