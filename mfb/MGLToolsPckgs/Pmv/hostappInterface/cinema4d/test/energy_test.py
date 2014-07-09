# -*- coding: utf-8 -*-
"""
Created on Sun Mar 21 08:43:55 2010

@author: -
"""
#import c4d
#self=c4d.mv.values()[0]

from Pmv.hostappInterface import pdb_c4d

## NRG calculation setup
at1 = "hsg1:A::;"
at2 = "ind:::;"
atomset1 = self.expandNodes(at1)
atomset2 = self.expandNodes(at2)

pdb_c4d.cAD3Energies(self,self.Mols,atomset1,atomset2,add_Conf=True,debug=True)

# we specify the pattern/group for which the molecules use the transfo matrix
#self.energy.add(atomset1,atomset2,score_type='c_ad3Score')
#self.art.energy.add(atomset1,atomset2,stem='hsg1b',atomtypes=['C','N','OA','HD','A','NA'],score_type='Trilinterp')
pdb_c4d.get_nrg_score(self.energy)

#write some conf to check
atomset1.setConformation(self.Mols[0].cconformationIndex)
self.writePDB(self.Mols[0],"/tmp/test_rec.pdb")
atomset2.setConformation(self.Mols[1].cconformationIndex)
self.writePDB(self.Mols[1],"/tmp/test_lig.pdb")

###########AMBER###################################
from c4d import threading

class MyThread(threading.Thread):
    def main(self):
        import c4d
        mv = c4d.mv.values()[0]
        mv.browseCommands('amberCommands', package='Pmv')
        mv.setup_Amber94("trp3h:",'mdtest5','/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/Tests/Data/trp3_h.prmtop')
        c = mv.md_Amber94
        c('mdtest5', 10000, callback=1, filename='0', log=0, callback_freq=10)	
thr = MyThread()#c,'mdtest5', 349, callback=1, filename='0', log=0, callback_freq=10)
thr.start(back=True)
#do some other operations here
thr.wait() #wait un	

self.browseCommands('amberCommands', package='Pmv')
#self.readMolecule('/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/Tests/Data/trp3h.pdb')
self.setup_Amber94("trp3h:",'a94test5','/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/Tests/Data/trp3_h.prmtop')
c1 = self.minimize_Amber94
c1('a94test5', dfpred=10.0, callback_freq='10', callback=1, drms=1e-06, maxIter=100, log=0)

self.browseCommands('amberCommands', package='Pmv')
self.setup_Amber94("trp3h:",'mdtest5','/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/Tests/Data/trp3_h.prmtop',indice=0)
c = self.md_Amber94
#call md_Amber94 command
#c('mdtest5', 349, callback=1, filename='0', log=0, callback_freq=10)
import thread
thread.start_new(c,('mdtest5', 349, callback=1, filename='0', log=0, callback_freq=10))
thr = MyThread()#c,'mdtest5', 349, callback=1, filename='0', log=0, callback_freq=10)
thr.start(back=True)
#do some other operations here
thr.wait() #wait un	

from Pmv.hostappInterface import pdb_c4d
mol = self.getMolFromName('trp3h')
pdb_c4d.setupAmber(self,'a94test5',mol,'/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/Tests/Data/trp3_h.prmtop','minimization')
self.minimize = False


############MMTK##################################
# Standard normal mode calculation.
#

from MMTK import *

from MMTK.Proteins import Protein
from MMTK.ForceFields import Amber94ForceField
from MMTK.NormalModes import NormalModes

from MMTK.Minimization import ConjugateGradientMinimizer
from MMTK.Trajectory import StandardLogOutput
from MMTK.Visualization import view


# Construct system
universe = InfiniteUniverse(Amber94ForceField())
universe.protein = Protein('bala1')

# Minimize
minimizer = ConjugateGradientMinimizer(universe,
                                       actions=[StandardLogOutput(50)])
minimizer(convergence = 1.e-3, steps = 10000)

# Calculate normal modes
modes = NormalModes(universe)

# Print frequencies
for mode in modes:
    print mode


# Show animation of the first non-trivial mode 
view(modes[6])