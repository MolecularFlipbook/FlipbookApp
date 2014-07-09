#execfile("/Library/MGLTools/1.5.6/MGLToolsPckgs/mglutil/hostappli/epmvMDtuto.py")
#run epmvMDtuto.py
import mglutil.hostappli.pdb_blender as epmv
#import mglutil.hostappli.pdb_c4d as epmv
from Blender import Window, Scene, Draw
import time
import Blender
#import c4d
from mglutil import hostappli
plugDir=hostappli.__path__[0]

#sc=Blender.Scene.GetCurrent()

self=epmv.start(debug=1)
self.readMolecule(plugDir+"/data/1BTA.pdb",log=1)
self.displayCPK("1BTA",log=1)

self.openTrajectory(plugDir+'/data/1BTA.xtc', log=0)
tname=self.Trajectories.keys()[0] #1BTA_md_noh2o.xtc
molname=self.Mols[0].name #1BTA_noh2o_model1
traj=self.Trajectories['1BTA.xtc']
mol=self.Mols[0]
self.playTrajectory('1BTA', '1BTA.xtc', log=0)
#traj.player.applyState(10)

#def states(i,traj,sc):
#    Window.WaitCursor(1)
#    traj.player.applyState(i)
#    sc.update()
#    Blender.Redraw()
#    Window.WaitCursor(0)

#states(1,traj,sc)
#for i in range(100):
#   Window.WaitCursor(1)
#   traj.player.applyState(i)
#   epmv.getCurrentScene().message(c4d.MULTIMSG_UP)
#   c4d.draw_views(c4d.DA_ONLY_ACTIVE_VIEW|c4d.DA_NO_THREAD|c4d.DA_NO_ANIMATION)	      

#   sc.update()
#   Blender.Redraw()
#   Window.WaitCursor(0)

