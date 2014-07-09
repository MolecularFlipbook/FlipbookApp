#
# WARNING: a comment is required after the fucntion prototype
#
def computeSesArea():
    """Computes the SES and SAS areas for the subset of currently selected
    molecules"""
    # get selection
    selection = self.getSelection()
    # get the set of molecules from selection
    selection = selection.top.uniq()
    #
    for m in selection:
        if hasattr(m.geomContainer, 'msms'):
            for ms, num in m.geomContainer.msms.values():
                # loop over components of that MSMS surface
                for i in range(ms.rsr.nb):
                    ms.compute_ses_area()


def assignAtomicSurfaceArea():
    """Assign to each atom the SES and SAS surface are in the external component"""
    # get selection
    selection = self.getSelection()
    # get the set of molecules from selection
    from MolKit.molecule import Atom
    mols, atoms = self.getNodesByMolecule(selection, Atom)
    #
    for m,atomSet in map(None, mols, atoms):
        if hasattr(m.geomContainer, 'msms'):
            for a in atomSet:
                a.ses_area = {}
                a.sas_area = {}
            for name, (ms, msn) in m.geomContainer.msms.items():
                indName = '__surfIndex%d__'%msn
                for a in atomSet:
                    n = getattr(a, indName)
                    atm = ms.get_atm(n)
                    a.ses_area[name] = atm.get_ses_area(0)
                    a.sas_area[name] = atm.get_sas_area(0)

def computeAtomicSphereArea():
    """compute the surface area of each atom (only if radii are present)"""

    import math
    # get selection
    selection = self.getSelection()
    # get the set of molecules from selection
    from MolKit.molecule import Atom
    mols, atoms = self.getNodesByMolecule(selection, Atom)

    for m,atomSet in map(None, mols, atoms):
        if hasattr(m.geomContainer, 'msms'):
            ms = m.geomContainer.msms
            for a in atomSet:
                if hasattr(a, 'radius'):
                    a.atom_ses_area = 4*math.pi*a.radius*a.radius
                    rad = a.radius+ms.rp
                    a.atom_sas_area = 4*math.pi*rad*rad

def avgPercentageOfExposedSurface():
    """compute the average percentage of exposed surface area"""
    computeSesArea()
    assignAtomicSurfaceArea()
    computeAtomicSphereArea()

    # get selection
    selection = self.getSelection()
    # get the set of molecules from selection
    from MolKit.molecule import Atom
    mols, atoms = self.getNodesByMolecule(selection, Atom)
    sumSES = sumSAS = 0.0
    nbSES = nbSAS = 0
    for m,atomSet in map(None, mols, atoms):
        for a in atomSet:
            if hasattr(a, 'atom_ses_area'):
                if hasattr(a, 'ses_area'):
                    if a.ses_area>0.0:
                        a.percentSesArea = a.ses_area*100/a.atom_ses_area
                        sumSES = sumSES+a.percentSesArea
                        nbSES = nbSES + 1
                    else:
                        a.percentSesArea = 0.0
            if hasattr(a, 'atom_sas_area'):
                if hasattr(a, 'sas_area'):
                    if a.ses_area>0.0:
                        a.percentSasArea = a.sas_area*100/a.atom_sas_area
                        sumSAS = sumSAS+a.percentSasArea
                        nbSAS = nbSAS + 1
                    else:
                        a.percentSasArea = 0.0
        if nbSES>0:
            m.avgPercentSES = sumSES/nbSES
            m.avgPercentSAS = sumSAS/nbSAS
            print "average percentage of exposed surface for %s: SES %f SAS %f"%(m.name,m.avgPercentSES,m.avgPercentSAS)

def cavityVolume():
    """Report the numerical volume of the MSMS surface compute for molecule
    for the current selection
    """
    selection = self.getSelection()
    # get the set of molecules from selection
    from MolKit.molecule import Atom
    mols, atoms = self.getNodesByMolecule(selection, Atom)

    for m in mols:
        if hasattr( m.geomContainer, 'msms'):
            m.geomContainer.msms.compute_numeric_area_vol()
            vol = m.geomContainer.msms.sesr.fst.n_ses_volume
            print "molecule", m.name, 'Volume: ', vol
        else:
            print 'no surface found for', m.name

def numericalVolume():
    """Compute the numerical volume of an msmsSel surface for the current
    selection of atoms"""
    sel = self.getSelection()
    mol = sel.top.uniq()
    assert len(mol)==1
    mol = mol[0]
    num = len(mol.geomContainer.msms.keys())
    self.computeMSMS(self.getSelection(), 1.5, 3.0, "mysurf%d"%num)
    msmssrfhandle= mol.geomContainer.msms["mysurf%d"%num][0]
    msmssrfhandle.compute_numeric_area_vol()
    vol = msmssrfhandle.sesr.fst.n_ses_volume
    name = "mysurf%d_NVolume"%num
    print name, vol
    setattr(self, "mysurf%d_NVolume"%num, vol)
