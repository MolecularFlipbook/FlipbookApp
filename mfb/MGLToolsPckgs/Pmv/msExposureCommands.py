########################################################################
#
# Copyright: Sargis Dallakyan (sargis@scripps.edu), 
#            Michel Sanner (sanner@scripps.edu)
#            The Scripps Research Institute (TSRI)
#            Molecular Graphics Lab
#            La Jolla, CA 92037, USA
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/msExposureCommands.py,v 1.2 2008/10/01 19:11:27 sargis Exp $
#
# $Id: msExposureCommands.py,v 1.2 2008/10/01 19:11:27 sargis Exp $
#
from Pmv.mvCommand import MVCommand
import mslib
import numpy
import math
import Pmw
from ViewerFramework.VFCommand import CommandGUI

class ComputeExposure(MVCommand):
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('computeSESAndSASArea'):
            self.vf.loadCommand('msmsCommands', ['computeSESAndSASArea',], topCommand=0)

    def __call__(self, nodes, **kw):
        """None <- computeExposure(nodes, **kw)
    Computes percentage of Solvent Excluded Surface (SES) or Solvent Accessible Surface (SAS) area for nodes, where
    nodes is a list of Chains, Residues or Atoms depending on the name of this class. The results are stored in
    ses_ratio or sas_ratio attributes in the list items, depending on the name of this class. For instance,
    computeAtomSESExposure(atoms) compute percentage of Solvent Excluded Surface for atoms and stores it in atom.ses_ratio.    
        """
        if len(nodes) == 0:
            print "Input list is empty"
            return
        nodes=self.vf.expandNodes(nodes)
        if not hasattr(nodes[0], 'ses_area'):
            self.vf.computeSESAndSASArea(nodes[0].top)
        return apply( self.doitWrapper, (nodes,), kw )
        
class ComputeAtomSESExposure(ComputeExposure):
    def doit(self, atoms):
        for atom in atoms:
            surfaceArea = 4*math.pi*atom.radius*atom.radius
            if atom.ses_area > 0.0:
                atom.ses_ratio = (atom.ses_area * 100) / surfaceArea
            else:
                atom.ses_ratio = 0.0

class ComputeAtomSASExposure(ComputeExposure):
    def doit(self, atoms):
        for atom in atoms:
            surfaceArea = 4*math.pi*(atom.radius+1.5)*(atom.radius+1.5)
            if atom.sas_area > 0.0:
                atom.sas_ratio = (atom.sas_area * 100) / surfaceArea
            else:
                atom.sas_ratio = 0.0
        
class ComputeResidueSESExposure(ComputeExposure):
    def doit(self, residues):
        for r in residues:
          coords = r.atoms.coords
          rad = map(lambda x: x.radius, r.atoms)
          m = mslib.MSMS(coords=coords, radii = rad) 
          m.compute()
          m.compute_ses_area()
          if r.ses_area > 0.0:
              r.ses_ratio = (r.ses_area * 100) / m.sesr.fst.a_ses_area
          else:
              r.ses_ratio = 0.0

class ComputeResidueSASExposure(ComputeExposure):
    def doit(self, residues):
        for r in residues:
          coords = r.atoms.coords
          rad = map(lambda x: x.radius, r.atoms)
          m = mslib.MSMS(coords=coords, radii = rad) 
          m.compute()
          m.compute_ses_area()
          if r.ses_area > 0.0:
              r.sas_ratio = (r.sas_area * 100) / m.sesr.fst.a_sas_area
          else:
              r.sas_ratio = 0.0

class ComputeChainSESExposure(ComputeExposure):
    def doit(self, chains):
        for chain in chains:
          coords = chain.residues.atoms.coords
          rad = map(lambda x: x.radius, chain.residuse.atoms)
          m = mslib.MSMS(coords=coords, radii = rad) 
          m.compute()
          m.compute_ses_area()
          if chain.ses_area > 0.0:
              chain.ses_ratio = (chain.ses_area * 100) / m.sesr.fst.a_sas_area
          else:
              chain.ses_ratio = 0.0

class ComputeChainSASExposure(ComputeExposure):
    def doit(self, chains):
        for chain in chains:
          coords = chain.residues.atoms.coords
          rad = map(lambda x: x.radius, chain.residuse.atoms)
          m = mslib.MSMS(coords=coords, radii = rad) 
          m.compute()
          m.compute_ses_area()
          if chain.ses_area > 0.0:
              chain.sas_ratio = (chain.sas_area * 100) / m.sesr.fst.a_sas_area
          else:
              chain.sas_ratio = 0.0

commandList = [{'name':'computeAtomSESExposure','cmd':ComputeAtomSESExposure(), 'gui':None},
               {'name':'computeAtomSASExposure','cmd':ComputeAtomSASExposure(), 'gui':None},
               {'name':'computeResidueSESExposure','cmd':ComputeResidueSESExposure(), 'gui':None},
               {'name':'computeResidueSASExposure','cmd':ComputeResidueSASExposure(), 'gui':None},
               {'name':'computeChainSESExposure','cmd':ComputeChainSESExposure(), 'gui':None},
               {'name':'computeChainSASExposure','cmd':ComputeChainSASExposure(), 'gui':None},
               
               ]
               
def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])        