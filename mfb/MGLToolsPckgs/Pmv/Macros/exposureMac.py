## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

def sesExposurePercent():
    """Compute the percentage of solvent exposed surface for each amino acide.
After running this macro, each residue has the 2 following members:
ses_area: total surface area for this residue
ses_ratio: percentage of residue surface exposed to solvent
The ratio is the percentage of SES area exposed to the solvent in each
residue, where 100 is the surface of that particular residue when all other
atoms are ignored
    """

    import mslib
    import numpy.oldnumeric as Numeric
    from Pmv.guiTools import MoleculeChooser

    mol = MoleculeChooser(self).go(modal=0, blocking=1)
    allrads = mol.defaultRadii()
    allResidues = mol.chains.residues
    allAtoms = mol.allAtoms

    # compute the surface
    srf = mslib.MSMS(coords=allAtoms.coords, radii = allrads)
    srf.compute()
    srf.compute_ses_area()

    # get surface areas per atom
    ses_areas = []
    for i in xrange(srf.nbat):
        atm = srf.get_atm(i)
        ses_areas.append( atm.get_ses_area(0) )

    # get surface areas to each atom
    allAtoms.ses_area = ses_areas

    # sum up ses areas over resdiues
    for r in allResidues:
        r.ses_area = Numeric.sum( r.atoms.ses_area )

    # compute the surface for each residue independantly
    # compute the % of ses
    srfList = []
    for r in allResidues:
      coords = r.atoms.coords
      rad = map(lambda x: x.radius, r.atoms)
      m = mslib.MSMS(coords=coords, radii = rad) 
      m.compute()
      m.compute_ses_area()
      srfList.append(m)
      if r.ses_area > 0.0:
          r.ses_ratio = (r.ses_area * 100) / m.sesr.fst.a_ses_area
      else:
          r.ses_ratio = 0.0

