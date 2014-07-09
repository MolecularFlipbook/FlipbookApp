def AddBond():
    """Template written as an example for OTHER people to write their own"""
    from Pmv.picker import AtomPicker
    p = AtomPicker(self, numberOfObjects=2, gui=0)
    p.go(modal=1)
    atoms = p.getObjects()
    assert atoms[0].top == atoms[1].top
    from MolKit.molecule import Bond
    Bond(atoms[0], atoms[1])
    self.lines(atoms[0].top)
    self.GUI.VIEWER.Redraw()
    
def deleteBond():
    """ """
##  BondPicker does not seem to work !
##      from Pmv.picker import BondPicker
##      p = BondPicker(self, numberOfObjects=1, gui=0)
##      p.go(modal=1)
    from Pmv.picker import AtomPicker
    p = AtomPicker(self, numberOfObjects=2, gui=0)
    p.go(modal=1)
    atoms = p.getObjects()
    bond = None
    for b in atoms[0].bonds:
        if b.atom1==atoms[0]:
            if b.atom2==atoms[1]:
                bond = b
                break
            elif b.atom1==atoms[1]:
                bond = b
                break
    if bond is None:
        print 'WARNING: atoms %s %s are not bonded'%(atoms[0].full_name(),
                                                     atoms[1].full_name())
        return
    b.atom1.bonds.remove(b)
    b.atom2.bonds.remove(b)
    self.lines(atoms[0].top)
    self.GUI.VIEWER.Redraw()
   
