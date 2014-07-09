## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

import numpy.oldnumeric as Numeric

def ClosestAtom():
    """ask for 2 molecules, compute for each atom
the distance to the closest atom in the other
molecule. After execution, each atom has a new
attribute 'closest' holding the distance"""

    # it would be better to ask for the attribute's name also
    from Pmv.guiTools import MoleculeChooser
    p = MoleculeChooser(self, 'extended', 'Choose 2 molecules')
    mols = p.go(modal=1)
    mol1Atoms = mols[0].allAtoms
    mol2Atoms = mols[1].allAtoms

    def distanceToClosestPoint(point, setOfPoints):
        """computes the shortest distance between point and setOfPoints"""
        diff = Numeric.array(point) - Numeric.array(setOfPoints)
        diff = diff*diff
        len = Numeric.sqrt(Numeric.sum(diff,1))
        return min(len)

    for a in mol1Atoms:
        a.closest = distanceToClosestPoint( a.coords, mol2Atoms.coords)

    for a in mol2Atoms:
        a.closest = distanceToClosestPoint( a.coords, mol1Atoms.coords)
