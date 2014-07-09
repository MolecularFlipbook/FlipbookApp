# Eric Kim
# script to communicate between PyRosetta and PyMol
# run rosetta libraries and this script inside PyMol command-line window
# PyRosetta and PyMol must be built with matching Python versions
# March 2009
# (c) Copyright Rosetta Commons Member Institutions.
# (c) This file is part of the Rosetta software suite and is made available under license.
# (c) The Rosetta software is developed by the contributing members of the Rosetta Commons.
# (c) For more information, see http://www.rosettacommons.org. Questions about this can be
# (c) addressed to University of Washington UW TechTransfer, email: license@u.washington.edu.

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
from mglutil import hostappli

####################blender specific###################
import Pmv.hostappInterface.pdb_blender as epmv
import Blender
from Blender import Window, Scene, Draw
self=epmv.start(debug=1)
sc=Blender.Scene.GetCurrent()
#########################################################

plugDir=hostappli.__path__[0]

with_pmv = True
rConf=1
pmv_state = 1
nDecoys=5
def pmv_show(pose,self):
  from Pmv.moleculeViewer import EditAtomsEvent
  global pmv_state
  import time
  #if not with_pmv: return
  model = self.getMolFromName("test")
  model.allAtoms.setConformation(1)
  coord = {}
  print pose.n_residue(),len(model.chains.residues)
  for resi in range(1, pose.n_residue()+1):
    res = pose.residue(resi)
    resn = pose.pdb_info().number(resi)
    #print resi,res.natoms(),len(model.chains.residues[resi-1].atoms)
    k=0
    for atomi in range(1, res.natoms()+1):
      name = res.atom_name(atomi).strip()
      if name != 'NV' :
	     a=model.chains.residues[resi-1].atoms[k]     
	     pmv_name=a.name
	     k = k + 1		 
	     if name != pmv_name : 
	        if name[1:] != pmv_name[:-1]:
	            print name,pmv_name
	        else : 
	            coord[(resn, pmv_name)] = res.atom(atomi).xyz()
	            cood=res.atom(atomi).xyz()
	            a._coords[1]=[cood.x,cood.y,cood.z]
					
	     else : 
	         coord[(resn, name)] = res.atom(atomi).xyz()
	         cood=res.atom(atomi).xyz()
	         a._coords[1]=[cood.x,cood.y,cood.z]  #return coord
  event = EditAtomsEvent('coords', model.allAtoms)
  self.dispatchEvent(event)
  #modEvent = ModificationEvent('edit','coords', mol.allAtoms)
  #mol.geomContainer.updateGeoms(modEvent)
  #PMV
  #self.GUI.VIEWER.Redraw()
  #time.sleep(.1)
  #Blender
  epmv.insertKeys(model.geomContainer.geoms['cpk'],1)
  epmv.getCurrentScene().update()
  Draw.Redraw()
  Draw.Redraw(1)
  Blender.Redraw()

def pmv_load(f):
  if not with_pmv: return
  mol=self.getMolFromName("test")
  if mol is None : 
     self.readMolecule(f)
     mol=self.Mols[0]
  for i in range(nDecoys):
      mol.allAtoms.addConformation(mol.allAtoms.coords[:])
  #mol.name="tset"
  print mol.name  
  #self.displaySticksAndBalls("test",log=1)
  self.displayCPK("test:::",log=1)
  self.colorAtomsUsingDG("test",log=1)
  #cmd.show("cartoon", "decoy")


from rosetta import *
rosetta.init()

pose = Pose(plugDir+"/data/test_fragments.pdb")
dump_pdb(pose, plugDir+"/data/test.pdb")
pmv_load(plugDir+"/data/test.pdb")
pmv_show(pose,self)

scorefxn = core.scoring.ScoreFunction()
scorefxn.set_weight(core.scoring.fa_atr, 1.0)
scorefxn.set_weight(core.scoring.fa_rep, 1.0)
scorefxn.set_weight(core.scoring.hbond_sr_bb, 1.0)
scorefxn.set_weight(core.scoring.hbond_lr_bb, 1.0)
scorefxn.set_weight(core.scoring.hbond_bb_sc, 1.0)
scorefxn.set_weight(core.scoring.hbond_sc, 1.0)

#switch = SwitchResidueTypeSetMover("centroid")
#switch.apply(pose)
#scorefxn = create_score_function("score3")

import random, math, time

def perturb(new_pose,pose):
  import random, math, time
  res = random.randrange(1,11)
  if random.randrange(0,2)==0:
    new_pose.set_phi(res, pose.phi(res)+random.gauss(0, 25))
  else:
    new_pose.set_psi(res, pose.psi(res)+random.gauss(0, 25))

from rosetta.core.fragment import *
fragset = core.fragment.ConstantLengthFragSet(3)
fragset.read_fragment_file(plugDir+"/data/test3_fragments")
movemap = core.kinematics.MoveMap()
movemap.set_bb(True)
mover_3mer = ClassicFragmentMover(fragset,movemap)
log = open("log", 'w')

def fold(pose,self,scorefxn,perturb,mover_3mer,pmv_show):
  import random, math, time   
  kt = 1
  print "ok Fold"
  low_pose = Pose()
  low_score = scorefxn(pose)
  new_pose = Pose()
  maxit = 1000
  start_time = time.time()
  stat = {"E":0,"A":0,"R":0}
  for it in range(0, maxit):
    print "in the loop"
    if it==maxit/2: pose.assign(low_pose)

    score = scorefxn(pose)
    new_pose.assign(pose)

    if it<maxit/2: mover_3mer.apply(new_pose)
    else: perturb(new_pose,pose)

    new_score = scorefxn(new_pose)
    delE =  new_score-score

    if delE<0:
      score = new_score
      pose.assign(new_pose)
      action = "E"
    else:
      if random.random()<math.exp(-delE/kt):
        score = new_score
        pose.assign(new_pose)
        action = "A"
      else: action = "R"

    if score<low_score:
      low_score = score
      low_pose.assign(pose)

    print it,"\t",score,"\t",low_score,"\t",action
    #log.write(str(score)+"\t"+str(low_score)+"\t"+str(action)+"\n")
    stat[action] += 1
    if action<>"R": pmv_show(pose,self)

  duration = time.time()-start_time
  print "took ",duration,"s\t",duration/float(maxit),"s/it"
  #print "E:",stat["E"]/float(maxit),"\t","A:",stat["A"]/float(maxit),"\t","R:",stat["R"]/float(maxit)
  print low_score
  pmv_show(low_pose,self)
  return low_pose

def angle(a):
  return math.fmod(a,180)

"""
for i in range(0, 1):
  pose2 = Pose()
  pose2.assign(pose)
  low_pose = fold(pose2)
  print i,
  for i in range(1,11):
    log.write(str(angle(low_pose.phi(i)))+"\t"+str(angle(low_pose.psi(i)))+"\n")

import threading

def run(self):
  thread = threading.Thread(target=fold, args=(pose,self,scorefxn,perturb,mover_3mer,pmv_show))
  thread.setDaemon(1)
  thread.start()
"""

import time
time.sleep(1.)
#fold(pose,self)
#import thread
#thread.start_new(fold, (pose,self))
#run(self)
fold(pose,self,scorefxn,perturb,mover_3mer,pmv_show)
