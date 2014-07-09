## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################################
#
# Author: Ruth HUEY, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/editCommands.py,v 1.127.2.2 2012/06/20 21:37:28 sanner Exp $
#
# $Id: editCommands.py,v 1.127.2.2 2012/06/20 21:37:28 sanner Exp $
#

from PyBabel.addh import AddHydrogens
from PyBabel.aromatic import Aromatic
from PyBabel.atomTypes import AtomHybridization
from PyBabel.cycle import RingFinder
from PyBabel.bo import BondOrder
from PyBabel.gasteiger import Gasteiger

from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
from tkMessageBox import *
from SimpleDialog import SimpleDialog


from Pmv.mvCommand import MVCommand, MVAtomICOM, MVBondICOM
from Pmv.measureCommands import MeasureAtomCommand

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Bond, Molecule, MoleculeSet
from MolKit.molecule import BondSet
from MolKit.protein import Protein, ProteinSet, Chain, Residue, ResidueSet
from MolKit.pdbParser import PdbParser, PdbqParser, PdbqsParser

from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.Points import CrossSet

from Pmv.stringSelectorGUI import StringSelectorGUI

import types, Tkinter, Pmw, math, os
import numpy.oldnumeric as Numeric
from string import letters, strip, find

def check_edit_geoms(VFGUI):
    edit_geoms_list = VFGUI.VIEWER.findGeomsByName('edit_geoms')
    if edit_geoms_list==[]:
        edit_geoms = Geom("edit_geoms", shape=(0,0), protected=True)
        VFGUI.VIEWER.AddObject(edit_geoms, parent=VFGUI.miscGeom)
        edit_geoms_list = [edit_geoms] 
    return edit_geoms_list[0]
        

from MolKit.protein import Residue, ResidueSet
from MolKit.molecule import Atom, AtomSet

class DeleteWaterCommand(MVCommand):
    """This class provides a command to remove water molecules.
    It will delete all atoms belonging to resides with names 'HOH' or 'WAT'
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:DeleteWaterCommand
    \nCommand:deleteWater
    \nSynopsis:\n
        None <--- removeWater(nodes, **kw)
    \nRequired Arguments:\n   
        nodes --- TreeNodeSet for which to remove waters
    \nexample:\n
      >>> RemoveWaterCommand()\n
      >>> RemoveWaterCommand(molecule)\n
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        self.vf._deletedLevels = []
        #if self.vf.hasGui and not self.vf.commands.has_key('deleteMol'):
        if not self.vf.commands.has_key('deleteAtomSet'):
            self.vf.loadCommand("deleteCommands", "deleteAtomSet", "Pmv",
                                topCommand=0)

    def doit(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        nodes = nodes.findType( Residue ).uniq()
        nodes = ResidueSet([r for r in nodes if r.type=='WAT' or r.type=='HOH'])
        atoms = nodes.findType( Atom )
        self.vf.deleteAtomSet( atoms )
        

    def __call__(self, nodes, **kw):
        """None<---deleteWater(nodes, **kw)
        \nnodes --- TreeNodeSet from which to delete waters"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        try:
            nodes = self.vf.expandNodes(nodes)
        except:
            raise IOError
        apply ( self.doitWrapper, (nodes,), kw )


    def guiCallback(self):
        sel = self.vf.getSelection()
        if len(sel):
            self.doitWrapper(sel, log=1, redraw=0)

        
deleteWaterCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                              'menuButtonName':'Edit',
                              'menuEntryLabel':'delete water'
                              }

DeleteWaterCommandGUI = CommandGUI()
DeleteWaterCommandGUI.addMenuCommand('menuRoot', 'Edit', 'Delete Water')



class TypeAtomsCommand(MVCommand):
    """This class uses the AtomHybridization class to assign atom types.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:TypeAtomsCommand
    \nCommand:typeAtoms
    \nSynopsis:\n
        None <--- typeAtoms(nodes, **kw)
    \nRequired Arguments:\n   
        nodes --- TreeNodeSet holding the current selection
    \nexample:\n
      >>> atype = AtomHybridization()\n
      >>> atype.assignHybridization(atoms)\n
      atoms has to be a list of atom objects\n
      Atom:\n
      a .element : atom's chemical element symbol (string)\n
      a .coords : 3-sequence of floats\n
      a .bonds : list of Bond objects\n
      Bond:\n
      b .atom1 : instance of Atom\n
      b .atom2 : instance of Atom\n
      After completion each atom has the following additional members:\n
      babel_type: string\n
      babel_atomic_number: int\n
      babel_organic\n
reimplementation of Babel1.6 in Python by Michel Sanner April 2000
Original code by W. Patrick Walters and Matthew T. Stahl\n

    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def doit(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: 
            return 'ERROR'
        mols = nodes.top.uniq()
        for mol in mols:
            #if hasattr(mol.allAtoms[0], 'babel_type'):
                #continue
#            try:
#                mol.allAtoms.babel_type
#            except:
            babel = AtomHybridization()
            babel.assignHybridization(mol.allAtoms)


    def __call__(self, nodes, **kw):
        """None<---typeAtoms(nodes, **kw)
        \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        try:
            nodes = self.vf.expandNodes(nodes)
        except:
            raise IOError
        apply ( self.doitWrapper, (nodes,), kw )


    def guiCallback(self):
        sel = self.vf.getSelection()
        if len(sel):
            self.doitWrapper(sel, log=1, redraw=0)

        
typeAtomsCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuEntryLabel':'Type',
                            'menuCascadeName': 'Atoms'}


TypeAtomsCommandGUI = CommandGUI()
TypeAtomsCommandGUI.addMenuCommand('menuRoot', 'Edit', 'Type',
                                   cascadeName='Atoms')#, index=1)


class EditAtomTypeGUICommand(MVCommand, MVAtomICOM):
    """This class provides the GUI to EditAtom Type which allows the user 
to change assigned atom types.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:EditAtomTypeGUICommand
    \nCommand:editAtomTypeGC
    \nSynopsis:\n
        None<---editAtomTypeGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet 
    """


    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.atmTypeDict={}
        self.atmTypeDict['B']=['B', 'Bac', 'Box']
        self.atmTypeDict['C']=['C', 'C1','C2','C3','Cac', 'Cbl', 'Car', 'C-',\
            'C+', 'Cx', 'Cany']
        self.atmTypeDict['H']=['H', 'HC', 'H-','HO','H+', 'HN']
        self.atmTypeDict['N']=['Ng+', 'Npl','Nam', 'N1','N2','N3', 'N4',\
            'Naz', 'Nox', 'Ntr', 'NC', 'N2+', 'Nar', 'Nany', 'N3+']
        self.atmTypeDict['O']=['O', 'O-','O2','O3','Oes', 'OCO2', \
            'Oco2', 'Oany']
        self.atmTypeDict['P']=['P', 'P3', 'P3+', 'Pac', 'Pox']
        self.atmTypeDict['S']=['S', 'S2', 'S3', 'S3+', 'Sac', 'So',\
            'So2', 'Sox', 'Sany']


    def onAddCmdToViewer(self):
        self.spheres = Spheres(name='editAtomTypeSphere', shape=(0,3),
                               radii=0.2, #inheritMaterial=0,
                               pickable=0, quality=15, 
                               materials=((1.,1.,0.),), protected=True) 
        if self.vf.hasGui:
            edit_geoms = check_edit_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.spheres, parent=edit_geoms)

        if not hasattr(self.vf, 'editAtomType'):
            self.vf.loadCommand('editCommands', 'editAtomType','Pmv',
                                topCommand=0)


    def __call__(self, nodes, **kw):
        """None<---editAtomTypeGC(nodes, **kw)
        \nnodes --- TreeNodeSet """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        ats = self.vf.expandNodes(nodes)
        if not len(ats): return 'ERROR'
        ats = ats.findType(Atom)
        apply ( self.doitWrapper, (ats,), kw )


    def doit(self, ats):
        for atom in ats:
            self.spheres.Set(vertices=(atom.coords,))
            self.vf.GUI.VIEWER.Redraw()
            if not hasattr(atom,'babel_type'):
                #msg = 'atom has no babel_type: calling typeAtoms'
                #self.warningMsg(msg)
                #typeAtoms does whole molecule
                self.vf.typeAtoms(atom, topCommand=0)
            if atom.element not in self.atmTypeDict.keys():
                msg = 'No alternative atom types available for this element'
                self.warningMsg(msg)
                continue
            else:
                bVals = self.atmTypeDict[atom.element]
            initialValue = (atom.babel_type,None)
            entries = []
            for item in bVals:
                entries.append((item, None))
            ifd = self.ifd = InputFormDescr(title='Select New AtomType')
            ifd.append({'name': 'typesList',
                    'title':'Choose New Type',
                    'widgetType':'ListChooser',
                    'entries': entries,
                    'defaultValue':initialValue,
                    'mode': 'single',
                    'gridcfg':{'row':0,'column':0},
                    'lbwcfg':{'height':5}})
            vals = self.vf.getUserInput(ifd)
            if vals is not None and len(vals)>0 and len(vals['typesList'])>0:
                self.vf.editAtomType(atom, vals['typesList'][0],topCommand=0)
            else:
                return 'ERROR'
        self.spheres.Set(vertices=[])
        self.vf.GUI.VIEWER.Redraw()


    def startICOM(self):
        self.vf.setIcomLevel(Atom)


    def stopICOM(self):
        self.spheres.Set(vertices=[])
        self.vf.GUI.VIEWER.Redraw()
        self.vf.ICmdCaller.commands.value["Shift_L"] = self.save
        self.save = None


    #def setupUndoBefore(self, ats, btype=None):
        #ustr = ''
        #for at in ats:
            ##typeAtoms types everything so can't undo it
            #if hasattr(at, 'babel_type'):
                #ustr=ustr + '"at=self.expandNodes('+'\''+at.full_name()+'\''+')[0];at.babel_type=\''+ at.babel_type+'\';"'
                #self.undoCmds = "exec("+ustr+")"
                


    def guiCallback(self):
        showinfo("Picking level is set to editAtomType", 
                 "Please pick on atom to change the type.")
        self.save = self.vf.ICmdCaller.commands.value["Shift_L"]
        self.vf.setICOM(self, modifier="Shift_L", topCommand=0)
        

editAtomTypeGUICommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuCascadeName':'Atoms',
                            'menuEntryLabel':'Edit Type'}


EditAtomTypeGUICommandGUI = CommandGUI()
EditAtomTypeGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 'Edit Type',
                   cascadeName='Atoms')#, index=1)



class EditAtomTypeCommand(MVCommand):
    """This class allows the user to change assigned atom types. 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:EditAtomTypeCommand
    \nCommand:editAtomType
    \nSynopsis:\n
        None <- editAtomType(ats, btype, **kw)\n
    \nRequired Arguments:\n   
        at ---  atom\n 
        btype --- babel_type\n
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        

    def __call__(self, ats, btype, **kw):
        """None <- editAtomType(ats, btype, **kw)
        \nat --- atom 
        \nbtype --- babel_type"""
        if type(ats) is types.StringType:
            self.nodeLogString = "'"+ats+"'"
        ats = self.vf.expandNodes(ats)
        if not len(ats): return 'ERROR'
        at = ats.findType(Atom)[0]
        apply ( self.doitWrapper, (at, btype,), kw )


    def doit(self, at, btype):
        at.babel_type = btype


    def setupUndoBefore(self, at, btype):
        ustr = ''
        #typeAtoms types everything so can't undo it
        if hasattr(at, 'babel_type'):
            ustr = ustr + '"at=self.expandNodes('+'\''+at.full_name()+'\''+')[0];at.babel_type=\''+ at.babel_type+'\';"'
            self.undoCmds = "exec("+ustr+")"
                


class EditAtomChargeGUICommand(MVCommand, MVAtomICOM):
    """This class provides the GUI to EditAtomCharge which allows the user 
to change atom charge.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:EditAtomTypeGUICommand
    \nCommand:editAtomTypeGC
    \nSynopsis:\n
         None<---editAtomChargeGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet 


    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.objArgOnly
        

    def onAddCmdToViewer(self):
        self.spheres = Spheres(name='editAtomChargeSphere', shape=(0,3),
                               radii=0.2, #inheritMaterial=0,
                               pickable=0, quality=15, 
                               materials=((1.,1.,0.),), protected=True) 
        if self.vf.hasGui:
            edit_geoms = check_edit_geoms(self.vf.GUI)
            self.vf.GUI.VIEWER.AddObject(self.spheres, parent=edit_geoms)
            self.oldCharge = Tkinter.StringVar()


    def __call__(self, nodes, **kw):
        """None<---editAtomChargeGC(nodes, **kw)
        \nnodes --- TreeNodeSet """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        apply ( self.doitWrapper, (nodes,), kw )


    def doit(self, nodes,):
        ats = nodes.findType(Atom)
        res = ats[0].parent
        self.setUp(res)
        atom = nodes[0]
        self.spheres.Set(vertices=(atom.coords,))
        self.vf.GUI.VIEWER.Redraw()
        if not hasattr(atom,'charge'):
            msg = 'atom has no charge: calling XXXXX'
            print msg
            #self.warningMsg(msg)
        self.oldCharge.set(atom.charge)
        ifd = self.ifd = InputFormDescr(title='Enter New Charge')
        ifd.append({'name':'eCLab',
                'widgetType':Tkinter.Label,
                'text':'Enter new charge for:\n' + atom.full_name(),
                'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'eCEnt',
            'widgetType':Tkinter.Entry,
            'wcfg':{'textvariable':self.oldCharge},
            'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        vals = self.vf.getUserInput(ifd)
        if len(vals)>0:
            atom._charges[atom.chargeSet] = float(vals['eCEnt'])
            self.vf.labelByExpression(AtomSet([atom]),
                                      textcolor=(1.0, 1.0, 1.0), 
                                      negate=0, 
                                      format=None, 
                                      location='Center', 
                                      log=0, 
                                      font='arial1.glf',
                                      only=0,
                                      lambdaFunc=1, 
                                      function='lambda x: str(x.charge)')
            #also update something showing the sum on this residue
            self.vf.setIcomLevel(Residue, topCommand=0)
            res = atom.parent
            res.new_sum = round(Numeric.sum(res.atoms.charge),4)
            self.vf.labelByProperty(ResidueSet([res]), properties=("new_sum",), \
                        textcolor="yellow",  log=0, font="arial1.glf")
            self.vf.setIcomLevel(Atom, topCommand=0)
        else:
            return 'ERROR'
        self.spheres.Set(vertices=[])
        self.vf.GUI.VIEWER.Redraw()


    def checkStartOk(self):
        self.vf.setIcomLevel(Atom)
        sel = self.vf.getSelection()
        lenSel = len(sel)
        if lenSel:
            resSet = sel.findType(Residue).uniq()
            ats = resSet[0].atoms
            self.vf.setIcomLevel(Atom, topCommand=0)
            #make sure each atom has a charge
            chrgdAts = ats.get(lambda x: hasattr(x, 'charge'))
            if chrgdAts is None or len(chrgdAts)!=len(ats):
                self.warningMsg('not all atoms have charge')
                self.stopICOM()
                return 0
            else:
                return 1
        else:
            return 0


    def setUp(self, res):
        #print 'setUp with ', res.full_name()
        #label with the smaller error either the floor or ceiling
        chsum = Numeric.sum(res.atoms.charge)
        fl_sum = math.floor(chsum)
        ceil_sum = math.ceil(chsum)
        #always add err to end up with either fl_sum or ceil_sum
        errF = fl_sum - chsum
        #errF = chsum - fl_sum
        #errC = chsum - ceil_sum
        errC = ceil_sum - chsum
        absF = math.fabs(errF)
        absC = math.fabs(errC)
        #make which ever is the smaller adjustment
        if absC<absF:
            err = round(errC, 4)
        else:
            err = round(errF, 4)
        #print 'labelling with err = ', err
        res.err = err

        self.vf.setIcomLevel(Atom, topCommand=0)
        self.vf.labelByExpression(res.atoms,textcolor=(1.0, 1.0, 1.0), 
                                  negate=0, 
                                  format=None, 
                                  location='Center', 
                                  log=0, 
                                  font='arial1.glf', 
                                  only=0, 
                                  lambdaFunc=1, 
                                  function='lambda x: str(x.charge)')
        self.vf.setIcomLevel(Residue, topCommand=0)
        #res.new_sum = round(Numeric.sum(res.atoms.charge),4)
        #self.vf.labelByProperty(ResidueSet([res]), properties=("new_sum",), \
        self.vf.labelByProperty(ResidueSet([res]), properties=("err",), \
                        textcolor="yellow",  log=0, font="arial1.glf")
        self.vf.setIcomLevel(Atom, topCommand=0)


    def startICOM(self):
        self.vf.setIcomLevel(Atom)
        #ok = self.checkStartOk()
        #if ok: 
            #nodes = self.vf.getSelection()
            #res = nodes.findType(Residue).uniq()
            #if not len(res):
            #    return 'ERROR'
            #self.setUp(res[0])


    def stopICOM(self):
        self.spheres.Set(vertices=[])
        sel = self.vf.getSelection()
        selAts = sel.findType(Atom)
        self.vf.setIcomLevel(Residue, topCommand=0)
        self.vf.labelByProperty(selAts.parent.uniq(), log=0, negate=1)
        self.vf.setIcomLevel(Atom, topCommand=0)
        self.vf.labelByExpression(sel, lambdaFunc=1, function='lambda x:2',\
                        log=0, negate=1)
        self.vf.GUI.VIEWER.Redraw()


    def setupUndoBefore(self, ats):
        ustr = ''
        for at in ats:
            ##typeAtoms types everything so can't undo it
            #if hasattr(at, 'babel_type'):
            ustr=ustr + '"at=self.expandNodes('+'\''+at.full_name()+'\''+')[0];at._charges[at.chargeSet]=float(\''+ str(at.charge)+'\');res = at.parent; import numpy.oldnumeric as Numeric;from MolKit.protein import ResidueSet; res.new_sum = round(Numeric.sum(res.atoms.charge),4);self.labelByProperty(ResidueSet([res]), properties = (\'new_sum\',),textcolor = \'yellow\',font=\'arial1.glf\',log=0)"'
        self.undoCmds = "exec("+ustr+")"
        #NEED to redo labels here, too
                

    def guiCallback(self):
        if not len(self.vf.Mols):
            self.warningMsg('no molecules in viewer')
            return
        ok = self.checkStartOk()
        if ok: 
            #nodes = self.vf.getSelection()
            #res = nodes.findType(Residue).uniq()
            #set up list of residues with non-integral charges
            #self.setUp(res[0])
            #self.setUp(self.vf.getSelection())
            self.vf.setICOM(self, modifier="Shift_L", topCommand=0)
        

editAtomChargeGUICommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuCascadeName':'Atoms',
                            'menuEntryLabel':'Edit Charge'}


EditAtomChargeGUICommandGUI = CommandGUI()
EditAtomChargeGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 'Edit Charge',
                   cascadeName='Charges')#, index=1)
                


class TypeBondsCommand(MVCommand):
    """This class uses the BondOrder class to compute bond order.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:TypeBondsCommand
    \nCommand:typeBonds
    \nSynopsis:\n
        None<---typeBonds(nodes, withRings=0, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
        withRings: default is 0
Before a BondOrder object can be used, atoms must have been assigned
a type see (AtomHybridization in types.py).\n
Bond order can be calculated using 2 different methods depending on whether
rings have been identified previously or not. Babel decides to use the first
method for molecules with more than 200 atoms and the second one else.\n
example:\n

      >>> atype = AtomHybridization()\n
      >>> atype.assignHybridization(atoms)\n
      >>> bo = BondOrder()\n
      >>> bo.assignBondOrder( atoms, bonds )\n

      or\n

      >>> atype = AtomHybridization()\n
      >>> atype.assignHybridization(atoms)\n
      >>> rings = RingFinder()\n
      >>> rings.findRings(allAtoms, bonds)\n
      >>> bo = BondOrder()\n
      >>> bo.assignBondOrder( atoms, bonds, rings )\n

      atoms has to be a list of atom objects\n
      Atom:\n
      a .coords : 3-sequence of floats\n
      a .bonds : list of Bond objects\n
      babel_type: string\n
      babel_atomic_number: int\n

      Bond:\n
      b .atom1 : instance of Atom\n
      b .atom2 : instance of Atom\n

      after completion each bond has a 'bondOrder' attribute (integer)\n

reimplementation of Babel1.6 in Python by Michel Sanner April 2000
Original code by W. Patrick Walters and Matthew T. Stahl\n

    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def doit(self, nodes, withRings=False):
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'
        mols = nodes.top.uniq()
        for mol in mols:
            allAtoms = mol.allAtoms
            if hasattr(mol, 'rings'): continue
            try:
                allAtoms.babel_type
            except:
                babel = AtomHybridization()
                babel.assignHybridization(allAtoms)

            #allAtoms = nodes.findType(Atom)
            bonds = allAtoms.bonds[0]
            
            if withRings:
                rings = RingFinder()
                rings.findRings2(allAtoms, bonds)
            else:
                rings = None
            mol.rings = rings
            # create a new attribute to know which rings a bond belongs to maybe should be done in cycle.py
            if not mol.rings is None:
                mol.rings.bondRings = {}
                for ind in xrange(len(mol.rings.rings)):
                    r = mol.rings.rings[ind]
                    for b in r['bonds']:
                        if not mol.rings.bondRings.has_key(b):
                            mol.rings.bondRings[b] = [ind,]
                        else:
                            mol.rings.bondRings[b].append(ind)

            
            bo = BondOrder()
            bo.assignBondOrder(allAtoms, bonds, rings)
            allAtoms._bndtyped = 1

            if withRings:
                # do aromatic here
                arom = Aromatic(rings)
                arom.find_aromatic_atoms(allAtoms)



    def __call__(self, nodes, withRings=False, **kw):
        """None<---typeBonds(nodes, withRings=0, **kw)
        \nnodes --- TreeNodeSet holding the current selection
        \nwithRings --- default is 0"""

        kw['withRings'] = withRings
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        apply ( self.doitWrapper, (nodes,), kw )


    def guiCallback(self):
        #put in checkbutton here for w/ or w/out rings
        ifd = InputFormDescr(title="Type bonds:")
        ifd.append({'name': 'rings',
                    'text': 'With Rings',
                    'widgetType': Tkinter.Checkbutton,
                    'variable': Tkinter.IntVar(),
                    'gridcfg': {'sticky':'w'}})
        val = self.vf.getUserInput(ifd)
        sel = self.vf.getSelection()
        if val and len(sel):
            self.doitWrapper(sel, val['rings'],log=1,redraw=0)

        
typeBondsCommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuCascadeName':'Bonds',
                            'menuEntryLabel':'Type'}


TypeBondsCommandGUI = CommandGUI()
TypeBondsCommandGUI.addMenuCommand('menuRoot', 'Edit', 'Type' ,
                   cascadeName='Bonds')



class AddHydrogensGUICommand(MVCommand):
    """This GUICOMMAND class calls the AddHydrogenCommand class. 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:AddHydrogensGUICommand
    \nCommand:add_hGC
    \nSynopsis:\n
        None<---add_hGC(nodes, polarOnly=0, method='noBondOrder', renumber=1,**kw)\n
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection\n
        polarOnly --- default is 0\n
        method --- Hydrogen atoms can be added using 2 different methods, ex: method='withBondOrder', default is 'noBondOrder'\n
        renumber --- default is 1\n
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'add_h'):
            self.vf.loadCommand('editCommands', 'add_h','Pmv',
                                topCommand=0)


    def __call__(self, nodes, polarOnly=False, method='noBondOrder',
                 renumber=True, **kw):
        """None<---add_hGC(nodes, polarOnly=False, method='noBondOrder',
                          renumber=1,**kw)
           \nnodes ---    TreeNodeSet holding the current selection
           \npolarOnly --- default is False
           \nmethod ---    Hydrogen atoms can be added using 2 different methods,
                      ex: method='withBondOrder', default is 'noBondOrder'
           \nrenumber ---  Boolean flag when set to True the atoms are renumbered. (default is True)
           """
        #kw['topCommand'] = 0
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        apply(self.doitWrapper,(nodes,polarOnly,method,renumber,), kw)


    def doit(self, nodes, polarOnly, method, renumber):
        """ None <- add_h(nodes, polarOnly=0, method='noBondOrder',
        renumber=1)"""
        newHs = self.vf.add_h(nodes, polarOnly, method, renumber,topCommand=0)
        #it could be that there are no new hydrogens: then don't log + return
        if not len(newHs): return 'ERROR'

        molecules, ats = self.vf.getNodesByMolecule(newHs)
##         for mol, hSet in map(None, molecules, ats):
##             #to update display
##             done = 0
##             for name, g in mol.geomContainer.geoms.items():
##                 #if name in ['lines', 'cpk', 'balls', 'sticks']:
##                 if name=='lines':
##                     if g.visible:
##                         kw = self.vf.displayLines.getLastUsedValues()
##                         kw['topCommand']=0
##                         kw['redraw']=1
##                         apply(self.vf.displayLines, (hSet,), kw)

##                 if name=='cpk':
##                     if g.visible:
##                         kw = self.vf.displayCPK.getLastUsedValues()
##                         kw['topCommand']=0
##                         kw['redraw']=1
##                         apply(self.vf.displayCPK, (hSet,), kw)

##                 if not done and (name=='balls' or name=='sticks'):
##                     if g.visible:
##                         kw = self.vf.displaySticksAndBalls.getLastUsedValues()
##                         kw['topCommand']=0
##                         kw['redraw']=1
##                         apply(self.vf.displaySticksAndBalls, (hSet,), kw)
##                         done = 1


    def guiCallback(self):
        sel = self.vf.getSelection()
        if not len(sel):
            self.warningMsg("No Molecules in Viewer!")
            return
        # check for non-bonded atoms
        mols = sel.findType(Protein, uniq=1)
        nonbnded = AtomSet()
        for m in mols:
            if m == mols[0]:
                mnames = m.name
            else:
                mnames = ',' + m.name
            nbs = m.get_nonbonded_atoms()
            if len(nbs): nonbnded += nbs
        if len(nonbnded):
            msg = '  Try adding hydrogens anyway?\n Found non-bonded atoms in ' + mnames +":\n"
            d = Pmw.TextDialog(self.vf.GUI.ROOT, scrolledtext_labelpos = 'n',
                 title = 'Add hydrogens',
                 buttons =['No', 'Yes'] , defaultbutton = 0,
                 label_text = msg , text_width=30, text_height=20)
            d.withdraw()
            msg = ""
            for b in nonbnded:
                msg = msg + "       " + b.full_name() + "\n"
##             d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
##                 buttons=['No','Yes'], default=0, 
##                 title='Try adding hydrogens anyway?')
##             tryAnyway = d.go()
            d.insert('end', msg)
            tryAnyway = d.activate()
            if tryAnyway == "No":
                return "ERROR"
        ifd = InputFormDescr(title = "Add Hydrogens:")
        hydrogenChoice = Tkinter.IntVar()
        hydrogenChoice.set(0)
        methodChoice = Tkinter.StringVar()
        if os.path.splitext(sel.top[0].parser.filename)[1]=='.pdb':
            methodChoice.set('noBondOrder')
        else:
            methodChoice.set('withBondOrder')
        #if len(sel.findType(Atom))>200:
            #methodChoice.set('noBondOrder')
        #else:
            #methodChoice.set('withBondOrder')
        #methodChoice.set('noBondOrder')
        renumberChoice = Tkinter.IntVar()
        renumberChoice.set(1)
        ifd.append({'name': 'allHs',
                    'text': 'All Hydrogens',
                    'widgetType': Tkinter.Radiobutton,
                    'value':0,
                    'variable': hydrogenChoice,
                    'gridcfg': {'sticky':'w'}})
        ifd.append({'name': 'polarOnly',
                    'text': 'Polar Only',
                    'widgetType': Tkinter.Radiobutton,
                    'value':1,
                    'variable': hydrogenChoice,
                    'gridcfg': {'sticky':'w'}})
        ifd.append({'name':'methodLab',
                    'widgetType':Tkinter.Label,
                    'text':'Method',
                    'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name': 'noBondOrder',
                    'text': 'noBondOrder (for pdb files...)',
                    'widgetType': Tkinter.Radiobutton,
                    'value':'noBondOrder',
                    'variable': methodChoice,
                    'gridcfg': {'sticky':'w'}})
        ifd.append({'name': 'withBondOrder',
                    'text': 'withBondOrder (if you trust the bond order info)',
                    'widgetType': Tkinter.Radiobutton,
                    'value':'withBondOrder',
                    'variable': methodChoice,
                    'gridcfg': {'sticky':'w'}})
        ifd.append({'name':'renumberLab',
                    'widgetType':Tkinter.Label,
                    'text':'Renumber atoms to include new hydrogens',
                    'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name': 'yesRenumber',
                    'text': 'yes',
                    'widgetType': Tkinter.Radiobutton,
                    'value':1,
                    'variable': renumberChoice,
                    'gridcfg': {'sticky':'w'}})
        ifd.append({'name': 'noRenumber',
                    'text': 'no',
                    'widgetType': Tkinter.Radiobutton,
                    'value':0,
                    'variable': renumberChoice,
                    'gridcfg': {'sticky':'w'}})
        val = self.vf.getUserInput(ifd)
        if val:
            self.doitWrapper(sel, polarOnly=hydrogenChoice.get(),
                method=methodChoice.get(), renumber=renumberChoice.get(),
                redraw=1)


addHydrogensGUICommandGuiDescr = {'widgetType':'Menu','menuBarName':'menuRoot',
                                  'menuButtonName':'Edit',
                                  'menuCascadeName':'Hydrogens',
                                  'menuEntryLabel':'Add'}

AddHydrogensGUICommandGUI = CommandGUI()
AddHydrogensGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 'Add',
                                cascadeName='Hydrogens')




class AddHydrogensCommand(MVCommand):
    """This command adds hydrogen atoms to all atoms in all molecules that have at least one member (i.e atom, residue, chain, base-pair etc..) specified in the first argument.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:AddHydrogensCommand
    \nCommand:add_h
    \nSynopsis:\n 
        AtomSet<---add_h(nodes, polarOnly=0, method='noBondOrder,
                         renumber=1,**kw)\n
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection\n
        polarOnly --- default is 0\n
        method --- Hydrogen atoms can be added using 2 different methods, ex: method='withBondOrder', default is 'noBondOrder'\n
        renumber --- default is 1\n
Returns an atomSet containing the created H atoms\n
NOTE: This command adds hydrogens to all atoms in the molecule specified using the nodes argument.\n
The hydrogen atoms added to each molecule are also saved as a set called mol.name + '_addedH'\n
This class uses the AddHydrogens class from the PyBabel package.\n

Before this AddHydrogens object can be used, atoms must have been assigned
a type see (AtomHybridization in types.py).\n

Hydrogen atoms can be added using 2 different methods. The first one requires
bondOrders to have been calculated previousely.\n

example:\n

      >>> atype = AtomHybridization()\n
      >>> atype.assignHybridization(atoms)\n
      >>> addh = AddHydrogens()\n
      >>> hat = addh.addHydrogens(atoms)\n

      atoms has to be a list of atom objects\n
      Atom:\n
          a .coords : 3-sequence of floats\n
          a .bonds : list of Bond objects\n
          babel_type: string\n
          babel_atomic_number: int\n

      Bond:\n
          b .atom1 : instance of Atom\n
          b .atom2 : instance of Atom\n

      or\n
      >>> addh = AddHydrogens()\n
      >>> hat = addh.addHydrogens(atoms, method='withBondOrder')\n

      atoms has to be a list of atom objects as above and\n
      Bond:\n
          b .atom1 : instance of Atom\n
          b .atom2 : instance of Atom\n
          b .bondOrder : integer\n

      these calls return a list 'hat' containing a tuple for each Hydrogen
      atom to be added. This tuple provides:\n
          coordsH       : 3-float coordinates of the H atom\n
          atom          : the atom to which the H atom is to be connected\n
          atomic_number : the babel_atomic_number of the H atom\n
          type          : tyhe b:wabel_type of the H atom\n

reimplementation of Babel1.6 in Python by Michel Sanner April 2000
Original code by W. Patrick Walters and Matthew T. Stahl\n
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('typeBonds'):
            self.vf.loadCommand('editCommands', 'typeBonds','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key("saveSet"):
            self.vf.loadCommand("selectionCommands", "saveSet", "Pmv",
                                topCommand=0)
        if not self.vf.commands.has_key("selectSet"):
            self.vf.loadCommand("selectionCommands", "selectSet", "Pmv",
                                topCommand=0)
        if not self.vf.commands.has_key("fixHNames"):
            self.vf.loadCommand("editCommands", "fixHNames", "Pmv",
                                topCommand=0)
            

    def __call__(self, nodes, polarOnly=False, method='noBondOrder',
                 renumber=True, **kw):
        """
        AtomSet <- add_h(nodes, polarOnly=0, method='noBondOrder,
                         renumber=1,**kw)
        \nnodes --- TreeNodeSet holding the current selection
        \npolarOnly --- default is False
        \nmethod --- Hydrogen atoms can be added using 2 different methods,
        \nex --- method='withBondOrder', default is 'noBondOrder'
        \nrenumber --- default is True 
        \nReturns an atomSet containing the created H atoms
        \nNOTE: This command adds hydrogens to all atoms in the molecule
        specified using the nodes argument.
        \nThe hydrogen atoms added to each molecule are also saved as a set
        called mol.name + '_addedH'
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        return apply(self.doitWrapper,(nodes,polarOnly,method,renumber,), kw)


    def doit(self, nodes, polarOnly=False, method='noBondOrder',
             renumber=True):
        """ None <- add_h(nodes, polarOnly=False, method='noBondOrder', renumber=True)"""
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'

        mols = nodes.top.uniq()

        newHs = AtomSet([]) # list of created H atoms (will be returned)
        resList = {} # used to get a list of residues with added H atoms

        for mol in mols:
            # check if we need to assign babel atom types
            try:
                t = mol.allAtoms.babel_type
            except:
                babel = AtomHybridization()
                babel.assignHybridization(mol.allAtoms)

            # check if we need to assign bond orders
            if method=='withBondOrder':
                allBonds, noBonds = mol.allAtoms.bonds
                haveBO = 1
                for b in allBonds:
                    if b.bondOrder is None:
                        haveBO = 0
                        break

                if haveBO==0:
                    self.vf.typeBonds(mol, withRings=1, topCommand=0)

            # add hydrogen atoms to this molecule
            addh = AddHydrogens()
            hat = addh.addHydrogens(mol.allAtoms, method=method)
            # build lists of all H atoms bonded to the same heavy atom
            bondedAtomDict = {}  # key is heavy atom
            for a in hat:
                if bondedAtomDict.has_key(a[1]):
                    bondedAtomDict[a[1]].append(a)
                else:
                    bondedAtomDict[a[1]] = [a]

            # now create Atom object for hydrogens
            # and add the to the residues's atom list

            molNewHs = AtomSet([]) # list of created H atoms for this molecule
            heavyAtoms = AtomSet([]) # list of atoms that need new radii
            
            for heavyAtom, HatmsDscr in bondedAtomDict.items():
                # do not add H to Carbon atoms if polarOnly is specified
                if polarOnly:
                    if heavyAtom.element=='C': continue

                res = heavyAtom.parent
                resList[res] = 1
                # find where to insert H atom
                childIndex = res.children.index(heavyAtom)+1

                # loop over H atoms description to be added
                # start art the end because (go ask RUTH)
                l = len(HatmsDscr)
                for i in range(l-1,-1,-1):
                    a = HatmsDscr[i]
                    # build H atom's name
                    if len(heavyAtom.name)==1:
                        name = 'H' + heavyAtom.name
                    else:
                        name = 'H' + heavyAtom.name[1:]

                    # if more than 1 H atom, add H atom index
                    # for instance HD11, HD12, Hd13 (index is 1,2,3)
                    if l > 1:
                        name = name + str(i+1)
                    #this is needed to avoid bug #752 alternate position atoms
                    if '@' in name and '@' in a[1].name:
                        at_position  = name.find('@')
                        name = name[:at_position] + name[at_position+2:] + \
                               name[at_position:at_position+2]
                    # create the H atom object
                    atom = Atom(name, res, top=heavyAtom.top,
                                chemicalElement='H',
                                childIndex=childIndex, assignUniqIndex=0)

                    # set atoms attributes
                    atom._coords = [ a[0] ]
                    if hasattr(a[1], 'segID'): atom.segID = a[1].segID
                    atom.hetatm = heavyAtom.hetatm
                    atom.alternate = []
                    #atom.element = 'H'
                    atom.occupancy = 1.0
                    atom.conformation = 0
                    atom.temperatureFactor = 0.0
                    atom.babel_atomic_number = a[2]
                    atom.babel_type = a[3]
                    atom.babel_organic = 1
                    atom.radius = 1.2
                    
                    # create the Bond object bonding Hatom to heavyAtom
                    bond = Bond( a[1], atom, bondOrder=1)

                    # add the created atom the the list
                    newHs.append(atom)
                    molNewHs.append(atom)

                    # create the color entries for all geoemtries
                    # available for the heavyAtom
                    for key, value in heavyAtom.colors.items():
                        atom.colors[key]=(1.0, 1.0, 1.0)
                        atom.opacities[key]=1.0
                    # DO NOT set charges to 0.0
                    ##for key in heavyAtom._charges.keys():
                        ##atom._charges[key] = 0.0
                    heavyAtoms.append(heavyAtom)
                    
            if not len(newHs):
                # if there are no newHs, return empty AtomSet here
                return newHs

            # assign non united radii to heavy atoms
            mol.defaultRadii(atomSet=heavyAtoms, united=0 )

            # update the allAtoms set in the molecule
            mol.allAtoms = mol.findType(Atom)

            if renumber:
                fst = mol.allAtoms[0].number
                mol.allAtoms.number = range(fst, len(mol.allAtoms)+fst)


            # save the added atoms as a set
            if len(molNewHs) > 0:
                setName = mol.name + '_addedH'
                self.vf.saveSet( molNewHs, setName,
                                 'added by addh command', topCommand=0)

        for r in resList.keys():
            r.assignUniqIndex()

        # update self.vf.Mols.allAtoms
        self.vf.allAtoms = self.vf.Mols.allAtoms

        event = AddAtomsEvent(objects=newHs)
        self.vf.dispatchEvent(event)

        return newHs



class FixHydrogenAtomNamesGUICommand(MVCommand):
    """This class provides Graphical User Interface to FixHydrogenAtomsNameCommand
which is invoked by it with the current selection, if there is one.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:FixHydrogenAtomNamesGUICommand
    \nCommand:fixHNamesGC
    \nSynopsis:\n 
        None<---fixHNamesGC(nodes, **kw)
    \nRequired Arguments:\n       
        nodes --- TreeNodeSet holding the current selection
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'fixHNames'):
            self.vf.loadCommand('editCommands', 'fixHNames','Pmv',
                                topCommand=0)

    

    def doit(self, nodes):
        self.vf.fixHNames(nodes)


    def __call__(self, nodes, **kw):
        """None <- fixHNamesGC(nodes, **kw)
        \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        
        apply( self.doitWrapper, (nodes,), kw )


    def guiCallback(self):
        sel=self.vf.getSelection()
        if len(sel):
            self.doitWrapper(sel, topCommand=0)
        

fixHydrogenAtomNamesGUICommandGuiDescr = {'widgetType':'Menu',
                                          'menuBarName':'menuRoot',
                                          'menuButtonName':'Edit',
                                          'menuCascadeName':'Hydrogens',
                                          'menuEntryLabel':'Fix Pdb Names'}


FixHydrogenAtomNamesGUICommandGUI = CommandGUI()
FixHydrogenAtomNamesGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                    'Fix Pdb Names', cascadeName='Hydrogens')



class FixHydrogenAtomNamesCommand(MVCommand):
    """\nThis class checks hydrogen atom names and modifies them to conform to 'IUPAC-IUB' conventions 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:FixHydrogenAtomNamesCommand
    \nCommand:fixHNames
    \nSynopsis:\n
        None <- fixHNames(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection\n

    Hydrogen names have 4 spaces:'H _ _ _', (here referred to as 1-4).\n 
    'H' is always in space 1.\n
    Space 2 references the name of the atom to which H is bonded 
        using the following scheme: \n
    IF the name has 1 letter, space 2 is that letter. \n
    IF the name has more than 1 letter, space 2 is the second letter 
        in that name and space 3 the third letter if it exists. \n
(Please note that the second space in the bonded atom name is a 'remoteness'
indicator and the third used to number items equally remote.)\n

    In all cases, the LAST space (which could be space 3 or space 4 
depending on the bonded-atom's name) is used to number hydrogen atoms 
when more than one are bound to the same atom.\n

EXAMPLES:\n
        HN <- hydrogen bonded to atom named 'N'\n
        HA <- hydrogen bonded to atom named 'CA'\n
        HE <- hydrogen bonded to atom named 'NE'\n
        HH11 <- first hydrogen bonded to atom named 'NH1'\n
        HH12 <- second hydrogen bonded to atom named 'NH1'\n
        HD21 <- first hydrogen bonded to atom named 'CD2'\n
________________________________________________________________________\n
A final complexity results when these names are written in pdb files:\n
The name of the atom appears RIGHT-JUSTIFIED in the first two columns of
the 4 columns involved (13-16). Thus 'H' appears in column 14 for all hydrogen
atoms. This creates a problem for 4 character hydrogen names. They are 
accommodated by wrapping so that space 4 appears in column 13.\n

EXAMPLE:\n
        1HD2 <- first hydrogen bonded to atom named 'CD2' as represented 
in a pdb file.\n
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def doit(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'

        allAtoms = nodes.findType(Atom)
        allHs = allAtoms.get('H*')
        if allHs is None or len(allHs)==0: return 'ERROR'
        ct = 0
        for a in allHs:
            if not len(a.bonds): continue
            b=a.bonds[0]
            a2=b.atom1
            if a2==a: a2=b.atom2
            if a2.name=='N':
                hlist = a2.findHydrogens()
                if len(hlist) == 1:
                    if a.name!='HN':
                        #print 'fixing atom ', a.full_name()
                        a.name = 'HN'
                        ct = ct + 1
                else:
                    for i in range(len(hlist)):
                        if hlist[i].name[:2]!='HN' or len(hlist[i].name)<3:
                            #print 'fixing atom ', hlist[i].full_name()
                            ct = ct + 1
                            hlist[i].name = 'HN'+str(i+1)
            if len(a2.name)>1:
                remote=a2.name[1]
                if remote in letters:
                    if len(a.name)<2 or remote!=a.name[1]:
                        #print 'fixing remote atom', a.full_name()
                        ct = ct + 1
                        a.name = a.name[0]+a2.name[1]
                        if len(a.name)>2:
                            a.name=a.name+a.name[2:]
                else:
                    newname = a.name + remote
                    if len(a.name)>1:
                        newname=newname+a.name[1:]


    def __call__(self, nodes, **kw):
        """None <--- fixHNames(nodes, **kw)
           \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        apply ( self.doitWrapper, (nodes,), kw )
   


## class FixHydrogenAtomNamesGUICommand(MVCommand):
##     """
## This class provides Graphical User Interface to FixHydrogenAtomsNameCommand
## which is invoked by it with the current selection, if there is one.
##     """

##     def __init__(self, func=None):
##         MVCommand.__init__(self, func)
##         self.flag = self.flag | self.objArgOnly

##     def onAddCmdToViewer(self):
##         if not hasattr(self.vf, 'fixHNames'):
##             self.vf.loadCommand('editCommands', 'fixHNames','Pmv',
##                                 topCommand=0)

    

##     def doit(self, nodes):
##         self.vf.fixHNames(nodes)


##     def __call__(self, nodes, **kw):
##         """None<---fixHNamesGC(nodes, **kw)
##         \nnodes --- TreeNodeSet holding the current selection"""
        
##         if type(nodes) is types.StringType:
##             self.nodeLogString = "'"+nodes+"'"
##         apply( self.doitWrapper, (nodes,), kw )


##     def guiCallback(self):
##         sel=self.vf.getSelection()
##         if len(sel):
## ##             if self.vf.userpref['expandNodeLogString']['value'] == 0:
## ##                 # The GUI command doesn't log itself but the associated command
## ##                 # does so we need to set the nodeLogString of the Command
## ##                 self.vf.fixHNames.nodeLogString = "self.getSelection()"
##             self.doitWrapper(sel, topCommand=0)
        

## fixHydrogenAtomNamesGUICommandGuiDescr = {'widgetType':'Menu',
##                                           'menuBarName':'menuRoot',
##                                           'menuButtonName':'Edit',
##                                           'menuCascadeName':'Hydrogens',
##                                           'menuEntryLabel':'Fix Pdb Names'}


## FixHydrogenAtomNamesGUICommandGUI = CommandGUI()
## FixHydrogenAtomNamesGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
##                     'Fix Pdb Names', cascadeName='Hydrogens')



#class FixHydrogenAtomNamesCommand(MVCommand):
 #   """
#This class checks hydrogen atom names and modifies them to conform to
#IUPAC-IUB conventions: 

#Hydrogen names have 4 spaces:'H _ _ _', (here referred to as 1-4). 
#    'H' is always in space 1. 
#    Space 2 references the name of the atom to which H is bonded 
#        using the following scheme: 
#    IF the name has 1 letter, space 2 is that letter. 
#    IF the name has more than 1 letter, space 2 is the second letter 
#        in that name and space 3 the third letter if it exists. 
#(Please note that the second space in the bonded atom name is a 'remoteness'
#indicator and the third used to number items equally remote.)

#    In all cases, the LAST space (which could be space 3 or space 4 
#depending on the bonded-atom's name) is used to number hydrogen atoms 
#when more than one are bound to the same atom.

#EXAMPLES:
#        HN <- hydrogen bonded to atom named 'N'
#        HA <- hydrogen bonded to atom named 'CA'
#       HE <- hydrogen bonded to atom named 'NE'
#        HH11 <- first hydrogen bonded to atom named 'NH1'
#        HH12 <- second hydrogen bonded to atom named 'NH1'
#        HD21 <- first hydrogen bonded to atom named 'CD2'
#________________________________________________________________________
#A final complexity results when these names are written in pdb files:
#The name of the atom appears RIGHT-JUSTIFIED in the first two columns of
#the 4 columns involved (13-16). Thus 'H' appears in column 14 for all hydrogen
#atoms. This creates a problem for 4 character hydrogen names. They are 
#accommodated by wrapping so that space 4 appears in column 13.

#EXAMPLE:
#        1HD2 <- first hydrogen bonded to atom named 'CD2' as represented 
#in a pdb file.
#    """
#    def __init__(self, func=None):
#        MVCommand.__init__(self, func)
#        self.flag = self.flag | self.objArgOnly

#    def doit(self, nodes):
#        nodes = self.vf.expandNodes(nodes)
#        if not len(nodes): return 'ERROR'
#
#        allAtoms = nodes.findType(Atom)
#        allHs = allAtoms.get('H.*')
##        if allHs is None or len(allHs)==0: return 'ERROR'
#        ct = 0
#        for a in allHs:
#            if not len(a.bonds): continue
#           b=a.bonds[0]
#            a2=b.atom1
#            if a2==a: a2=b.atom2
#            if a2.name=='N':
#                hlist = a2.findHydrogens()
#                if len(hlist) == 1:
#                   if a.name!='HN':
#                        #print 'fixing atom ', a.full_name()
#                        a.name = 'HN'
#                        ct = ct + 1
#                else:
#                    for i in range(len(hlist)):
##                        if hlist[i].name[:2]!='HN' or len(hlist[i].name)<3:
#                            #print 'fixing atom ', hlist[i].full_name()
#                            ct = ct + 1
#                            hlist[i].name = 'HN'+str(i+1)
##            if len(a2.name)>1:
#                remote=a2.name[1]
##                if remote in letters:
#                    if remote!=a.name[1]:
#                        #print 'fixing remote atom', a.full_name()
#                        ct = ct + 1
#                        a.name = a.name[0]+a2.name[1]
#                        if len(a.name)>2:
#                            a.name=a.name+a.name[2:]
#                else:
#                    newname = a.name + remote
#                    if len(a.name)>1:
#                        newname=newname+a.name[1:]
##
#
#    def __call__(self, nodes, **kw):
#        """None <- fixHNames(nodes, **kw)
#           nodes: TreeNodeSet holding the current selection"""
#        if type(nodes) is types.StringType:
#              self.nodeLogString = "'"+nodes+"'"
#        apply ( self.doitWrapper, (nodes,), kw )
   


class SplitNodesGUICommand(MVCommand):
    """ This class presents GUI for SplitNodesCommand 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:SplitNodesGUICommand
    \nCommand:splitNodesGC
    \nSynopsis:\n
        None<---splitNodesGC(nodes, levelToSplit, top, renumber=1, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection\n
        levelToSplit --- splitting level\n
        top --- \n
        renumber --- default is 1\n
    """


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'splitNodes'):
            self.vf.loadCommand('editCommands', 'splitNodes','Pmv',
                                topCommand=0)
    


    def onAddCmdToViewer(self):
        import MolKit
        self.levelDict={}
        self.levelDict['Molecule']=MolKit.molecule.Molecule
        self.levelDict['Protein']=MolKit.protein.Protein
        self.levelDict['Chain']=MolKit.protein.Chain
        self.levelDict['Residue']=MolKit.protein.Residue
        self.levelStrings={}
        self.levelStrings[MolKit.molecule.Molecule]='Molecule'
        self.levelStrings[MolKit.protein.Protein]='Protein'
        self.levelStrings[MolKit.protein.Chain]='Chain'
        self.levelStrings[MolKit.protein.Residue]='Residue'


    def __call__(self, nodes, levelToSplit, top, renumber=1, **kw):
        """None<---splitNodesGC(nodes, levelToSplit, top, renumber=1, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nlevelToSplit --- splitting level
           \ntop ---
           \nrenumber --- default is 1"""
        if type(levelToSplit)==types.StringType:
            levelToSplit = self.levelDict[levelToSplit]
        kw['renumber'] = renumber
        apply(self.doitWrapper, (nodes, levelToSplit, top,), kw)


    def fixIDS(self, chains):
        idList = chains.id
        ifd = self.ifd = InputFormDescr(title="Set unique chain ids")
        ent_varDict = self.ent_varDict = {}
        self.nStrs = []
        self.entStrs = []
        self.chains = chains
        ifd.append({'name':'Lab1',
                    'widgetType':Tkinter.Label,
                    'text':'Current',
                    'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'Lab2',
                    'widgetType':Tkinter.Label,
                    'text':'New',
                    'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        for ch in chains:
            #fix the chain numbers here, also
            ch.number = self.vf.Mols.chains.index(ch)
            idList = chains.id
            ct = idList.count(ch.id)
            if ct!=1:
                for i in range(ct-1):
                    ind = idList.index(ch.id)
                    idList[ind] = ch.id+str(i)
        for i in range(len(chains)):
            chid = idList[i]
            ch = chains[i]
            nStr = chid+'_lab'
            self.nStrs.append(nStr)
            entStr = chid+'_ent'
            self.entStrs.append(entStr)
            newEntVar = ent_varDict[ch] = Tkinter.StringVar()
            newEntVar.set(ch.id)
            ifd.append({'name':nStr,
                    'widgetType':Tkinter.Label,
                    'text':ch.full_name(),
                    'gridcfg':{'sticky':'we'}})
            ifd.append({'name':entStr,
                'widgetType':Tkinter.Entry,
                'wcfg':{ 'textvariable': newEntVar, },
                'gridcfg':{'sticky':'we', 'row':-1, 'column':1}})
        vals = self.vf.getUserInput(self.ifd, modal=0, blocking=1)
        if vals :
            for i in range(len(chains)):
                #CHECK for changes in id/name
                ch = chains[i]
                ll = ch.id
                ln = (len(ch.name)+len(ch.id))/2.0

                wl = strip(vals[self.entStrs[i]])
                if len(wl) and ln!=1:
                    print 'changed chain ', ch.full_name(), ' to ',  
                    ch.id = wl[0]
                    ch.name = wl[0]
                    print  ch.full_name()


    def doit(self, nodes, levelToSplit, top, **kw):
        mol = apply(self.vf.splitNodes, (nodes, levelToSplit, top,),kw)
        # if levelToSplit is Molecule/Protein then mol is new mol
        # otherwise it is nodes.top with new levelToSplit items: chains or
        # residues....
        self.vf.select.updateSelectionIcons()
        #also need to fix name 
        #if at chain level, assign a number to the chain
        if levelToSplit==self.levelDict['Protein']:
            self.fixIDS(mol.chains)
            nobnds = mol.geomContainer.atoms['nobnds']
            mol.geomContainer.atoms['bonds'] = mol.allAtoms - nobnds
            self.vf.displayLines(nodes, negate=1)
            self.vf.displayLines(nodes, negate=0)
            

    def guiCallback(self):
        nodes=self.vf.getSelection()
        if len(nodes)==0: return 'ERROR'
        if nodes.__class__==nodes.top.__class__:
            msg= "unable to split selection at " +  nodes.__class__+ " level"
            self.warningMsg(msg)
            return

        #figure out what levels are available for splitting:
        top = nodes.top.uniq()
        assert len(top)==1, 'nodes to be split must be in same molecule'
        top = top[0]
        levelChoices=[]
        try:
            n = top.levels.index(nodes.elementType)
        except:
            msg='invalid selection'
            self.warningMsg(msg)
            return 
        levels = top.levels[:n]

        for item in levels:
            levelChoices.append(self.levelStrings[item])
        
        assert len(levelChoices)>0, 'molecule has no levels !?!'

        if len(levelChoices)==1:
            self.doitWrapper(nodes,self.levelDict[levelChoices[0]],top)
        else:
            renumberChoice = Tkinter.IntVar()
            renumberChoice.set(1)
            ifd = InputFormDescr(title='Choose Split Level')    
            ifd.append({'name':'level',
                    'widgetType': Tkinter.Radiobutton,
                    'listtext':levelChoices,
                    'gridcfg':{'sticky':Tkinter.W}})
            ifd.append({'name':'renumberLab',
                    'widgetType':Tkinter.Label,
                    'text':'Renumber atoms after split',
                    'gridcfg':{'sticky':Tkinter.W}})
            ifd.append({'name': 'yesRenumber',
                    'text': 'yes',
                    'widgetType': Tkinter.Radiobutton,
                    'value':1,
                    'variable': renumberChoice,
                    'gridcfg': {'sticky':'w'}})
            ifd.append({'name': 'noRenumber',
                    'text': 'no',
                    'widgetType': Tkinter.Radiobutton,
                    'value':0,
                    'variable': renumberChoice,
                    'gridcfg': {'sticky':'w'}})
            val = self.vf.getUserInput(ifd)
            if val is not None and len(val):
##                 if self.vf.userpref['expandNodeLogString']['value'] == 0:
##                     # The GUI command doesn't log itself but the associated
##                     # command does so we need to set the nodeLogString of the
##                     # Command
##                     self.vf.splitNodes.nodeLogString = "self.getSelection()"

                self.doitWrapper(nodes, self.levelDict[val['level']], top,\
                    renumber=renumberChoice.get(), log=1, redraw=1)
        
        
splitNodesGUICommandGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                             'menuButtonName':'Edit',
                             'menuCascadeName':'Misc',
                             'menuEntryLabel':'Split Selection'}


SplitNodesGUICommandGUI = CommandGUI()
SplitNodesGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 'Split Selection',
                    cascadeName='Misc')



class SplitNodesCommand(MVCommand):
    """This class allows the user to split current selection from unselected nodes. 
     \nPackage:Pmv
    \nModule :editCommands
    \nClass:SplitNodesCommand
    \nCommand:splitNodes
    \nSynopsis:\n
        mol<---splitNodes(nodes, levelToSplit, top, renumber=1, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection\n
        levelToSplit --- the splitting level\n
        top ---\n
        renumber --- default is 1\n
if levelToSplit is Molecule/Protein, the new molecule is returned
OTHERWISE the modified molecule is returned\n

The split is done at a level above nodes.  If more than one level above nodes exists, 
the user chooses the level at which to split. Result of split depends on the designated
splitting level: \n
    splits at the Protein/Molecule level result in a new Protein/Molecule\n 
splits at other levels result in adding new nodes to the Protein/Molecule: \n
eg. splitting at the chain level adds a new chain to the Protein, etc. etc.\n

    """

    def onAddCmdToViewer(self):
        import MolKit
        self.levelDict={}
        self.levelDict['Molecule']=MolKit.molecule.Molecule
        self.levelDict['Protein']=MolKit.protein.Protein
        self.levelDict['Chain']=MolKit.protein.Chain
        self.levelDict['Residue']=MolKit.protein.Residue
        self.levelStrings={}
        self.levelStrings[MolKit.molecule.Molecule]='Molecule'
        self.levelStrings[MolKit.protein.Protein]='Protein'
        self.levelStrings[MolKit.protein.Chain]='Chain'
        self.levelStrings[MolKit.protein.Residue]='Residue'


    def __call__(self, nodes, levelToSplit, top, renumber=True, **kw):
        """mol <- splitNodes(nodes, levelToSplit, top, renumber=1, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nlevelToSplit --- the splitting level
           \ntop ---
           \nrenumber --- default is 1
           \nif levelToSplit is Molecule/Protein, the new molecule is returned
           OTHERWISE the modified molecule is returned"""

        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        if type(levelToSplit)==types.StringType:
            levelToSplit = self.levelDict[levelToSplit]
        kw['renumber'] = renumber
        return apply(self.doitWrapper, (nodes, levelToSplit, top,), kw)


    def doit(self, nodes, levelToSplit, top, **kw):

        renumber = kw['renumber']
        
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'
        #FIX THIS: could be in >1 molecule
        assert len(nodes.top.uniq())==1, 'nodes to be split must be in same molecule'
        if nodes.__class__==nodes.top.__class__:
            msg= "unable to split selection at " +  nodes.__class__+ " level"
            self.warningMsg(msg)
            return 'ERROR'

        if levelToSplit==top.__class__:
            changeAtoms = nodes.findType(Atom)
            event = DeleteAtomsEvent(objects=changeAtoms)
            self.vf.dispatchEvent(event)

        parents=nodes.parent.uniq()

        #while parents.elementType!=levelToSplit and parents[0].parent!=None:
        while parents[0].__class__!=levelToSplit and \
              not parents[0].parent is None:
            parents=parents.parent.uniq()

        #returnVal = []
        #then need to split each parent with its children in nodes
        for parent in parents:
            children = nodes.__class__(filter(lambda x, parent=parent, nodes=nodes:\
                x in parent.findType(nodes.elementType), nodes))
            #newnode of class levelToSplit is returned with proper children:
            #if top, add to viewer else adopt it by correct parent
            #split returns a copy of parent so thisResult is really parentCOPY
            thisResult = parent.split(children)
            movedAtoms = thisResult.findType(Atom)
            #parentAtoms = parent.findType(Atom) 
            ##NB: bogusAtoms are atoms moving to new molecule, newtop
            #have to correct bonds here for both sets:
            #atSetList = [bogusAtoms, parentAtoms]
            #only have to correct bonds in one set
            for at in movedAtoms:
                for b in at.bonds:
                    at2 = b.atom1
                    if at2==at: at2 = b.atom2
                    if at2 not in movedAtoms:
                        #print 'removing bond:', b
                        b.atom1.bonds.remove(b)
                        b.atom2.bonds.remove(b)
                        del b

        if levelToSplit==top.__class__:
            # FIX THIS: should not get >2 as result
            # assert len(thisResult)==2, 'faulty split'
            # add new molecule to viewer
            # add new molecule to viewer
            newtop = self.vf.addMolecule(thisResult)
            newtop.allAtoms = newtop.chains.residues.atoms
            top.allAtoms = top.chains.residues.atoms
            #top.allAtoms = top.allAtoms - movedAtoms

            #NB: this fixes 'number' but not '_uniqIndex'
            if renumber:
                for m in [top, newtop]:
                    fst = m.allAtoms[0].number
                    m.allAtoms.number = range(fst, len(m.allAtoms)+fst)
            #have to rebuilt allAtoms

            #newAllAtoms = AtomSet([])
            #for item in self.vf.Mols:
                #newAllAtoms = newAllAtoms + item.allAtoms

            #self.vf.allAtoms = newAllAtoms
            self.vf.allAtoms = self.vf.Mols.chains.residues.atoms

            #thisResult is top, newtop
            #FIX THIS: need to duplicate/split the parser, also
            return thisResult
        else:
            #return top.setClass([top])
            return top



class MergeFieldsCommand(MVCommand):
    """This class allows the user to change the fields of one set by the values 
of another set.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:MergeFieldsCommand
    \nCommand:mergeFields
    \nSynopsis:\n
        None <- mergeFields(set1, set2, fieldList=[], negate=0, **kw)
    \nRequired Arguments:\n
        set1 --- field value of set1\n
        set2 --- field value of set1\n
    \nOptional Arguments:\n
        fieldList --- fields of type Int or Float in a list, default is []\n
        negate --- flag when set to 1 undisplay the current selection, default is 0\n
Fields that are of type Int or Float can be added or subtracted.
Specified fields of the items in the first set are incremented or decremented
by those of the second set.\n
    """


    def __call__(self, set1, set2, fieldList=[], negate=False, **kw):
        """None <- mergeFields(set1, set2, fieldList=[], negate=0, **kw)
           \nset1 --- field value of set1
           \nset2 --- field value of set1
           \nfieldList --- fields of type Int or Float in a list, default is []
           \nnegate --- flag when set to 1 undisplay the current selection, default is 0"""
        kw['negate'] = negate
        apply(self.doitWrapper, (set1, set2, fieldList,), kw)


    def doit(self,set1, set2, fieldList, **kw):

        if not len(set1): return 'ERROR'
        if not len(set2): return 'ERROR'

        negate = kw['negate']
        assert len(set1)<=len(set2),'second set must be equal or larger than first'
        #possibly truncate second set
        set2=set2[:len(set1)]

        topSets=[MoleculeSet,ProteinSet]
        if not (set1.__class__ in topSets and set2.__class__ in topSets):
            assert set1.__class__==set2.__class__, 'sets not of same class'

        for f in fieldList:
            exec('set1.'+f+'=Numeric.array(set1.'+f+')')
            exec('set2.'+f+'=Numeric.array(set2.'+f+')')

            if not negate:
                exec('set1.'+f+'=Numeric.add(set1.'+f+',set2.'+f+')')
            else:
                exec('set1.'+f+'=Numeric.subtract(set1.'+f+',set2.'+f+')')



    def guiCallback(self):
        import Pmv.selectionCommands
        set_entries=self.vf.sets.keys()
        if not len(set_entries):
            msg='No current sets'
            self.warningMsg(msg)
            return
        ifd=InputFormDescr(title='Select two sets')
        ifd.append({'name':'labelSet1',
            'widgetType':Tkinter.Label,
            'text':'Change Set1 values',
            'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name': 'set1List',
            'widgetType': Tkinter.Radiobutton,
            'listtext':set_entries,
            'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name':'labelSet2',
            'widgetType':Tkinter.Label,
            'text':'by values in Set2',
            'gridcfg':{'sticky':Tkinter.W, 'row':0, 'column':1}})
        ifd.append({'name': 'set2List',
            'widgetType': Tkinter.Radiobutton,
            'listtext':set_entries,
            'gridcfg':{'sticky':Tkinter.W, 'row':1, 'column':1}})

        vals = self.vf.getUserInput(ifd)
        if vals is not None and len(vals)>0:
            set1=self.vf.sets[vals['set1List']]
            set2=self.vf.sets[vals['set2List']]
        else:
            return

        entries1 = filter(lambda x: isinstance(x[1], types.IntType)\
                        or isinstance(x[1], types.FloatType),
                        set1[0].__dict__.items())
        entries1=map(lambda x: x[0], entries1)
        entries2 = filter(lambda x: isinstance(x[1], types.IntType)\
                        or isinstance(x[1], types.FloatType),
                        set2[0].__dict__.items())
        entries2=map(lambda x: x[0], entries2)

        entries = filter(lambda x,entries2=entries2:x in entries2, entries1)

        ifd=InputFormDescr(title='Select Property')
        ifd.append({'name': 'propList',
            'widgetType':Tkinter.Radiobutton,
            'listtext': entries,
            'title':'Select Property(s) to Merge',
            'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name':'negateB',
            'widgetType':Tkinter.Checkbutton,
            'defaultValue':0,
            'wcfg':{'text':'Subtract (when on)'},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        vals = self.vf.getUserInput(ifd)
        if vals is not None and len(vals)>0:
            fieldList = vals['propList']
            kw = {}
            kw['negate'] = int(vals['negateB'])
            kw['log'] =1
            kw['redraw'] =1
            
            apply(self.doitWrapper, (set1, set2, [vals['propList']],), kw)


mergeFieldsCommandGuiDescr = {'widgetType':'Menu','menuBarName':'menuRoot',
                              'menuButtonName':'Edit',
                              'menuEntryLabel':'Fields',
                              'menuCascadeName':'Misc'}

MergeFieldsCommandGUI = CommandGUI()
MergeFieldsCommandGUI.addMenuCommand('menuRoot', 'Edit', 'Fields',
                     cascadeName='Misc')



class MergeSetsCommand(MVCommand):
    """This class allows the user to merge two sets into one. 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:MergeSetsCommand
    \nCommand:mergeSets
    \nSynopsis:\n
        None <- mergeSets(set1, set2, **kw)
    \nRequired Arguments:\n
        set1 --- first set
        \nset2 --- second set
One by one items in the first set adopt children of items of the second set\n
    """


    def updateAllAtoms(self,mols,negate):
        if len(self.vf.Mols)>len(mols):
            restmols=self.vf.Mols-mols    
            allAtoms=restmols.allAtoms
        else:
            allAtoms=AtomSet([])
        classList=[Chain,Residue,Atom]
        for m in mols:
            if not(len(m.children)): 
                continue
            lnodes=m.setClass([m])
            for l in classList:
                if l in m.levels:
                    lnodes=lnodes.findType(l)
            m.allAtoms=lnodes
            allAtoms=allAtoms+m.allAtoms
        self.vf.allAtoms=allAtoms
        #print 'at end: self.vf.allAtoms= ', len(self.vf.allAtoms)


    def __call__(self, set1, set2, **kw):
        """removedItems <- mergeSets(set1, set2, **kw)
\nset1 --- first set
\nset2 --- second set

           """
        return apply(self.doitWrapper, (set1, set2,), kw)


    def doit(self,set1, set2, **kw):

        
        if not len(set1): return
        if not len(set2): return

        assert len(set1)>=len(set2),'len(set1) not >= len(set2)'

        negate = kw['negate']

        topSets=[MoleculeSet,ProteinSet]
        if not (set1.__class__ in topSets and set2.__class__ in topSets):
            assert set1.__class__==set2.__class__, 'sets not of same class'

        removedItems = set1.__class__([])

        top1=set1.top.uniq()[0]
        top2=set2.top.uniq()[0]
        if top1==top2:
            tops=MoleculeSet([top1])
        else:
            tops=MoleculeSet([top1,top2])

        if not negate: 
            if set2.__class__ != AtomSet and not len(set2.children): 
                msg='unable to merge currently merged set2'
                self.warningMsg(msg)
                return 'ERROR'
            self.vf.displayLines(set2,negate=1, log=0,redraw=1)
            
        else:
            if len(set2.children): 
                msg='trying to unmerge currently unmerged set2'
                self.warningMsg(msg)
                return 'ERROR'

        for i in range(len(set2)):
            item1=set1[i]
            item2=set2[i]
            #next part deals with trying to update the tree structure correctly
            if not negate:
                #if there are any children: deal with them:
                item2.childrenByName=item2.children.name
                if not item2.childrenByName is None:
                    for c in item2.children:
                        item1.adopt(c)
                    for cname in item2.children.name:
                        ind=item2.children.name.index(cname)
                        item2.remove(item2.children[ind])
                if item2==item2.top:
                    self.vf.deleteMol(item2)
                else:
                    item2.parent.remove(item2)
                    removedItems.append(item2)
            else:
                #if there are any children: deal with them:
                if not item2.childrenByName is None:
                    for c in item2.childrenByName:
                        child=None
                        for ch in item1.children:
                            if ch.name==c:
                                child=ch
                        if child is not None:
                            item2.adopt(child)
                    for c in item2.childrenByName:
                        child=None
                        for ch in item1.children:
                            if ch.name==c:
                                child=ch
                        if child is not None:
                            item1.remove(child)                    
                item2.parent.adopt(item2)
        self.updateAllAtoms(tops,negate)
        #lines should deal with this:
        #needs to update geomContainer.geoms correctly
        #FIX ME: THIS IS A HACK..because only would hide other molecules, etc
        #oldats=tops[0].geomContainer.atoms['lines']
        oldats=tops[0].geomContainer.atoms['bonded']
        
        newats=tops[0].allAtoms-oldats
        if not negate: 
            self.vf.displayLines(newats,log=0,redraw=1)
            ##self.vf.select.updateSelectionIcons()
        else:
            self.vf.displayLines(tops[0].allAtoms, only=1,log=0,redraw=1)
            self.vf.displayLines(set2,log=0,redraw=1)
            #self.vf.select.updateSelectionIcons()
        return removedItems


    def guiCallback(self):
        import Pmv.selectionCommands
        set_entries=self.vf.sets.keys()
        if not len(set_entries):
            msg='No current sets'
            self.warningMsg(msg)
            return
        if len(set_entries)<2:
            msg='Not enough current sets'
            self.warningMsg(msg)
            return
        ifd=InputFormDescr(title='Select two sets')
        ifd.append({'name':'labelSet1',
            'widgetType':Tkinter.Label,
            'text':'Add to Set1',
            'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name': 'set1List',
            'widgetType': Tkinter.Radiobutton,
            'listtext':set_entries,
            'gridcfg':{'sticky':Tkinter.W}})
        ifd.append({'name':'labelSet2',
            'widgetType':Tkinter.Label,
            'text':'children of nodes in Set2',
            'gridcfg':{'sticky':Tkinter.W, 'row':0, 'column':1}})
        ifd.append({'name': 'set2List',
            'widgetType': Tkinter.Radiobutton,
            'listtext':set_entries,
            'gridcfg':{'sticky':Tkinter.W, 'row':1, 'column':1}})
        ifd.append({'name':'negateB',
            'widgetType':Tkinter.Checkbutton,
            'defaultValue':0,
            'wcfg':{'text':'Negate'},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        vals = self.vf.getUserInput(ifd)
        if vals is not None and len(vals)>0:
            set1=self.vf.sets[vals['set1List']]
            set2=self.vf.sets[vals['set2List']]
            dict = {}
            dict['log'] = 1
            dict['redraw'] = 1
            dict['negate'] = int(vals['negateB'])
            apply(self.doitWrapper,(set1, set2,),dict)


mergeSetsCommandGuiDescr = {'widgetType':'Menu','menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuEntryLabel':'Sets',
                            'menuCascadeName':'Misc'}

MergeSetsCommandGUI = CommandGUI()
MergeSetsCommandGUI.addMenuCommand('menuRoot', 'Edit', 'Sets',
                   cascadeName='Misc')



class MergeNPHsGUICommand(MVCommand):
    """This class implements GUICommand for MergeNPHsCommand below
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:MergeNPHsGUICommand
    \nCommand:mergeNPHSGC
    \nSynopsis:\n
        None<---mergeNPHSGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    """ 

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'mergeNPHS'):
            self.vf.loadCommand('editCommands', 'mergeNPHS','Pmv',
                                topCommand=0)


    def __call__(self, nodes, **kw):
        """None <- mergeNPHSGC(nodes, **kw)
\nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, **kw):
        ats = nodes.findType(Atom)
        hs = ats.get(lambda x: x.element=='H')
        hs_with_bonds = hs.get(lambda x: len(x.bonds)>0)
        hs_with_no_bonds = hs.get(lambda x: len(x.bonds)==0)
        if hs_with_no_bonds:
            mols = hs_with_no_bonds.top.uniq()
            msg = ""
            for m in mols:
                msg += m.name + ','
            msg =  msg[:-1] + ' has ' + str(len(hs_with_no_bonds)) + ' hydrogen(s) with no bonds:'
            for at in hs_with_no_bonds:
                print 'adding ', at.full_name()
                msg += at.parent.parent.name + ':'+ at.parent.name +':'+ at.name + ','
                print 'EC:', msg
            self.warningMsg(msg[:-1])
        #npHs = ats.get(lambda x: x.element=='H' and
                       #(x.bonds[0].atom1.element=='C' or 
                        #x.bonds[0].atom2.element=='C'))
        npHs = hs_with_bonds.get(lambda x: x.bonds[0].atom1.element=='C' or x.bonds[0].atom2.element=='C')
        if npHs is not None and len(npHs)!=0:
            if kw.has_key('logBaseCmd'):
                kw['topCommand'] = kw['logBaseCmd']
            apply(self.vf.mergeNPHS,(npHs,),kw)
            self.vf.select.updateSelectionIcons()
        else:
            return 'ERROR'

        
    def guiCallback(self):
        sel=self.vf.getSelection()
        
        if len(sel):
            if self.vf.undoCmdStack == []:
                self.doitWrapper(sel, topCommand=0)
            else:
                text = """WARNING: This command cannot be undone.
                if you choose to continue the undo list will be reset.
        Do you want to continue?""" 
                idf = self.idf = InputFormDescr(title="WARNING")
                idf.append({'name': 'testLab',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':text},
                    'gridcfg':{'columnspan':3,'sticky':'w'}})
                idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'CONTINUE',
                        'command':CallBackFunction(self.cont_cb, sel)},
                    'gridcfg':{'sticky':'we'}})
                idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'CANCEL', 'command':self.cancel_cb},
                    'gridcfg':{'row':-1,'sticky':'we'}})
                self.form = self.vf.getUserInput(idf, modal=0, blocking=0)
                self.form.root.protocol('WM_DELETE_WINDOW',self.cancel_cb)


    def cont_cb(self, sel):
        self.vf.resetUndo()
        self.form.destroy()
        self.doitWrapper(sel, topCommand=0)


    def cancel_cb(self, event=None):
        self.form.destroy()
        

mergeNPHsGUICommandGuiDescr = {'widgetType':'Menu','menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuCascadeName':'Hydrogens',
                            'menuEntryLabel':'Merge Non-Polar Hs'}


MergeNPHsGUICommandGUI = CommandGUI()
MergeNPHsGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 'Merge Non-Polar',
                   cascadeName='Hydrogens')



class MergeNPHsCommand(MVCommand):
    """This class merges non-polar hydrogens and the carbons to which they are attached. There are three parts to the process:the charge(s) of non-polar hydrogens are added to those their carbons the bond between the npH and its carbon is removed from the carbon's bonds the hydrogen atoms are removed. 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:MergeNPHsCommand
    \nCommand:mergeNPHS
    \nSynopsis:\n
        None<---mergeNPHS(nodes, **kw)
    \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection
    """ 
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly



    def __call__(self, nodes, **kw):
        """None <- mergeNPHS(nodes, **kw)
\nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        return apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, **kw):
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'

        if nodes[0].__class__!=Atom:
            nodes = nodes.findType(Atom)
        allAtoms = nodes

        returnVal = []
        #process nodes by molecule
        molecules, atomSets = self.vf.getNodesByMolecule(allAtoms)
        for mol, atoms in zip(molecules, atomSets):
            # we do not delete the atom in mol.mergeNPH but call
            # self.vf.deleteAtomSet() instead so that Pmv updates properly
            npHSet = mol.mergeNPH(atoms, deleteAtoms=False)
            self.vf.deleteAtomSet(npHSet)

        return returnVal



class MergeLonePairsGUICommand(MVCommand):
    """ This class presents GUI for MergeLonePairsCommand
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:MergeLonePairsGUICommand
    \nCommand:mergeLPSGC
    \nSynopsis:\n
        None<---mergeLPSGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
     """ 

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'mergeLPS'):
            self.vf.loadCommand('editCommands', 'mergeLPS','Pmv',
                                topCommand=0)
    



    def __call__(self, nodes, **kw):
        """None <- mergeLPSGC(nodes, **kw)
\nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, **kw):
        ats = nodes.findType(Atom)
        lps = ats.get(lambda x:x.element=='Xx'\
                 and (x.name[0]=='L' or \
                 x.name[1]=='L'))
        if lps is not None and len(lps)!=0:
            if kw.has_key('logBaseCmd'):
                kw['topCommand'] = kw['logBaseCmd']
            apply(self.vf.mergeLPS, (lps,), kw)
            self.vf.select.updateSelectionIcons()
        else:
            return 'ERROR'

        
    def guiCallback(self):
        sel=self.vf.getSelection()
        if len(sel):
            if self.vf.undoCmdStack == []:
                self.doitWrapper(sel, topCommand=0)
            else:
                        
                text = """WARNING: This command cannot be undone.
                if you choose to continue the undo list will be reset.
        Do you want to continue?""" 
                idf = self.idf = InputFormDescr(title="WARNING")
                idf.append({'name': 'testLab',
                    'widgetType':Tkinter.Label,
                    'wcfg':{'text':text},
                    'gridcfg':{'columnspan':3,'sticky':'w'}})
                idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'CONTINUE',
                        'command':CallBackFunction(self.cont_cb, sel)},
                    'gridcfg':{'sticky':'we'}})
                idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text':'CANCEL', 'command':self.cancel_cb},
                    'gridcfg':{'row':-1,'sticky':'we'}})
                self.form = self.vf.getUserInput(idf, modal=0, blocking=0)
                self.form.root.protocol('WM_DELETE_WINDOW',self.cancel_cb)


    def cont_cb(self, sel):
        self.vf.resetUndo()
        self.form.destroy()
##         if self.vf.userpref['expandNodeLogString']['value'] == 0:
##             self.mergeLPS.nodeLogString = "self.getSelection()"
        self.doitWrapper(sel, topCommand=0)


    def cancel_cb(self, event=None):
        self.form.destroy()
        

mergeLonePairsCommandGuiDescr = {'widgetType':'Menu','menuBarName':'menuRoot',
                            'menuButtonName':'Edit',
                            'menuCascadeName':'Misc',
                            'menuEntryLabel':'Merge Lone Pairs'}


MergeLonePairsGUICommandGUI = CommandGUI()
MergeLonePairsGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                                           'Merge Lone Pairs',
                                           cascadeName='Misc')

        

class MergeLonePairsCommand(MVCommand):
    """This class merges lone-pairs and the sulfur atoms to which they are attached.There are three parts to the process:the charges of lone-pairs, if any, are added to those of the sulfurs the bond between the lone-pair and its sulfur is removed from the sulfur's bonds the lone-pair 'atoms' are deleted
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:MergeLonePairsCommand
    \nCommand:mergeLPS
    \nSynopsis:\n
        None<---mergeLPS(nodes, **kw)
    \nRequired Arguments:\n    
        nodes --- TreeNodeSet holding the current selection\n
    NB: the lone pairs are identified by these criteria:
    \nthe element field of the lone pair 'atom' is 'Xx' and its name has a 'L'
in the first or second position.
    """ 

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def __call__(self, nodes, **kw):
        """None<---mergeLPS(nodes, **kw)
\nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 'ERROR'
        return apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, **kw):
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'

        if nodes[0].__class__!=Atom:
            nodes = nodes.findType(Atom)

        allAtoms = nodes

        returnVal = []
        #process nodes by molecule
        molecules, atomSets= self.vf.getNodesByMolecule(allAtoms)
        allAtoms = AtomSet([])
        for i in range(len(molecules)):
            mol=molecules[i]
            ats=atomSets[i]
            lps=ats.get(lambda x:x.element=='Xx'\
                 and (x.name[0]=='L' or \
                 x.name[1]=='L'))
            if lps is not None and len(lps)!=0:
                Sset = AtomSet([])
                for LPatom in lps:
                    b = LPatom.bonds[0]
                    if b.atom1==LPatom: 
                        Sset.append(b.atom2)
                        if b in b.atom2.bonds:
                            b.atom2.bonds.remove(b)
                    else: 
                        Sset.append(b.atom1)
                        if b in b.atom1.bonds:
                            b.atom1.bonds.remove(b)
            else:
                #there is nothing to do, so just do next molecule
                continue
            #process each field in lps._charges.keys()
            #to get only the ones every lps has:
            chList = lps[0]._charges.keys()
            for at in lps:
                chs = at._charges.keys()
                for c in chList:
                    if c not in chs: chList.remove(c)
            if not len(chList): 
                 print 'no consistent chargeSet across sulfurs\ncharge on sulfurs unchanged'
                #self.warningMsg('no consistent chargeSet across sulfurs\ncharge on sulfurs unchanged')
            for chargeSet in chList:
                for lp in lps:
                    Satom = lp.bonds[0].atom1
                    if Satom==lp: Satom = lp.bonds[0].atom2
                    Satom._charges[chargeSet] = Satom.charge + lp.charge
        
            mol.allAtoms = mol.allAtoms - lps
            self.vf.allAtoms = self.vf.allAtoms - lps

            event = DeleteAtomsEvent(objects=lps)
            self.vf.dispatchEvent(event)

            for at in lps:
                at.parent.remove(at)
                del at
            returnVal.append(mol)

        #return a list of molecules which changed
        return returnVal



class ComputeGasteigerGUICommand(MVCommand):
    """Calls computeGasteiger which does work of computing gasteiger partial charges
for each atom and entering each atom's charge in its _charges dictionary.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:ComputeGasteigerGUICommand
    \nCommand:computeGasteigerGC
    \nSynopsis:\n 
        None<---computeGasteigerGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    """
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly



    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'computeGasteiger'):
            self.vf.loadCommand('editCommands', 'computeGasteiger','Pmv',
                                topCommand=0)
    

    def doit(self, nodes):
        self.vf.computeGasteiger(nodes)
        ats = nodes.findType(Atom)
        sum = round(Numeric.add.reduce(ats.charge),4)
        msg = 'Total gasteiger charge added = ' + str(sum)
        self.warningMsg(msg)
        self.msg = msg
        return sum


    def __call__(self, nodes, **kw):
        """None<---computeGasteigerGC(nodes, **kw)
           \nnodes --- TreeNodeSet holding the current selection"""

        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        if not len(nodes): return
        return apply(self.doitWrapper, (nodes,), kw )


    def guiCallback(self):
        sel=self.vf.getSelection()
        if len(sel):
            return self.doitWrapper(sel, topCommand=0)
        

computeGasteigerGUICommandGuiDescr = {'widgetType':'Menu',
                                      'menuBarName':'menuRoot',
                                      'menuButtonName':'Edit',
                                      'menuCascadeName':'Charges',
                                      'menuEntryLabel':'Compute Gasteiger'}


ComputeGasteigerGUICommandGUI = CommandGUI()
ComputeGasteigerGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                    'Compute Gasteiger', cascadeName='Charges')



class ComputeGasteigerCommand(MVCommand):
    """Does work of computing gasteiger partial charges for each atom and entering each atom's charge in its '_charges' dictionary as value for key 'gasteiger' (rounded to 4 decimal places).  Calls babel.assignHybridization(mol.allAtoms) for each molecule with atoms in nodes.Sets the current charge (its chargeSet field) of each atom to gasteiger.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:ComputeGasteigerCommand
    \nCommand:computeGasteiger
    \nSynopsis:\n
        None<---computeGasteiger(nodes, **kw)
    \nRequiured Arguments:\n
        nodes --- TreeNodeSet holding the current selection
     """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def setupUndoBefore(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        allAtoms = nodes.findType(Atom)
        chargeAts = AtomSet([])
        charges = []
        nochargeAts = AtomSet([])

        for at in allAtoms:
            #if hasattr(at, 'gast_charge'):
            if at._charges.has_key('gasteiger'):
                chargeAts.append(at)
                charges.append(at._charges['gasteiger'])
            else:
                nochargeAts.append(at)

        self.undoMenuString = self.name

        if len(chargeAts) and len(nochargeAts):
            ustr='"nodes=self.expandNodes('+'\''+chargeAts.full_name()+'\''+');nodes.addCharges(\'gasteiger\','+str(charges)+');nodes=self.expandNodes('+nochargeAts.full_name()+');nodes.delCharges(\'gasteiger\')"'
            self.undoCmds = "exec("+ustr+")"

        elif len(chargeAts):
            ustr = '"nodes=self.expandNodes('+'\''+chargeAts.full_name()+'\''+');nodes.addCharges(\'gasteiger,'+str(charges)+')"'
            self.undoCmds = "exec("+ustr+")"
        else:
            ustr='"nodes=self.expandNodes('+'\''+nochargeAts.full_name()+'\''+');nodes.delCharges(\'gasteiger\')"'
            self.undoCmds = "exec("+ustr+")"

    def __call__(self, nodes, **kw):
        """None <- computeGasteiger(nodes, **kw)
           \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return
        apply ( self.doitWrapper, (nodes,), kw )

    def doit(self, nodes ):
        #nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'

        mols = nodes.top.uniq()
        for mol in mols:
            babel_typed = filter(lambda x: hasattr(x,'babel_type'), mol.allAtoms)
            if len(babel_typed)==len(mol.allAtoms):
                continue
            babel = AtomHybridization()
            babel.assignHybridization(mol.allAtoms)

        allAtoms = nodes.findType(Atom)
        bonds = allAtoms.bonds[0]

        if not len(bonds):
            msg='must buildBonds before gasteiger charges can be computed'
            self.warningMsg(msg)
            return

        Gast = Gasteiger()
        Gast.compute(allAtoms)
        #at this point, allAtoms has field 'gast_charge' with 12 decimal places
        gastCharges = []
        for c in allAtoms.gast_charge:
            gastCharges.append(round(c,4))
        allAtoms.addCharges('gasteiger', gastCharges)
        del allAtoms.gast_charge
        #make gasteiger the current charge
        allAtoms.chargeSet = 'gasteiger'
        


class AddKollmanChargesGUICommand(MVCommand):
    """Kollman united atom charges are added to atoms in peptides by looking up each atom's parent and name in table in Pmv.qkollua.  Missing entries are assigned charge 0.0
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:AddKollmanChargesGUICommand
    \nCommand:addKollmanChargesGC
    \nSynopsis:\n
        totalCharge<---addKollmanChargesGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    """


    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'addKollmanCharges'):
            self.vf.loadCommand('editCommands', 'addKollmanCharges','Pmv',
                                topCommand=0)
    


    def __call__(self, nodes, **kw):
        """totalCharge <- addKollmanChargesGC(nodes, **kw)
\nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        kw['topCommand'] = 0
        return apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes,):
        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'
        self.vf.addKollmanCharges(nodes)
        ats = nodes.findType(Atom)
        sum = round(Numeric.add.reduce(ats.charge),4)
        msg = 'Total Kollman charge added = ' + str(sum)
        self.warningMsg(msg)
        self.msg = msg
        return sum


    def guiCallback(self):
        sel = self.vf.getSelection()
        if not len(sel): 
            self.warningMsg("No Molecules Present")
            return
##         if self.vf.userpref['expandNodeLogString']['value'] == 0:
##             self.vf.addKollmanCharges.nodeLogString = "self.getSelection()"

        return self.doitWrapper(sel, topCommand=0)


addKollmanChargesGUICommandGuiDescr = {'widgetType':'Menu',
                                      'menuBarName':'menuRoot',
                                      'menuButtonName':'Edit',
                                      'menuCascadeName':'Charges',
                                      'menuEntryLabel':'Add Kollman Charges'}


AddKollmanChargesGUICommandGUI = CommandGUI()
AddKollmanChargesGUICommandGUI.addMenuCommand('menuRoot', 'Edit',
                       'Add Kollman Charges ', cascadeName='Charges')



class AddKollmanChargesCommand(MVCommand):
    """Kollman united atom partial charges are added to atoms by looking up each atom's parent's type to get a dictionary of charges for specific atom names (from Pmv.qkollua).  Missing entries are assigned charge 0.0.  These partial charges are entered in each atom's '_charges' dictionary as value for key 'Kollman'. Sets the current charge (its chargeSet field) of each atom to 'Kollman'.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:AddKollmanChargesCommand
    \nCommand:addKollmanCharges
    \nSynopsis:\n
        totalCharge<---addKollmanCharges(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
        \ntotalCharge --- sum of partial charges on nodes.
"""

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def onAddCmdToViewer(self):
        import Pmv.qkollua
        self.q = Pmv.qkollua.q


    def __call__(self, nodes, **kw):
        """totalCharge<---addKollmanCharges(nodes, **kw)
\nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        return apply(self.doitWrapper, (nodes,), kw)


    def setupUndoBefore(self, nodes):
        nodes = self.vf.expandNodes(nodes)
        allAtoms = nodes.findType(Atom)
        chargeAts = AtomSet([])
        charges = []
        nochargeAts = AtomSet([])
        for at in allAtoms:
            #if hasattr(at, 'gast_charge'):
            if at._charges.has_key('Kollman'):
                chargeAts.append(at)
                charges.append(at._charges['Kollman'])
            else:
                nochargeAts.append(at)

        self.undoMenuString = self.name


        if len(chargeAts) and len(nochargeAts):
            ustr='"nodes=self.expandNodes('+'\''+chargeAts.full_name()+'\''+');nodes.addCharges(\'Kollman\','+str(charges)+');nodes=self.expandNodes('+nochargeAts.full_name()+');nodes.delCharges(\'Kollman\')"'
            self.undoCmds = "exec("+ustr+")"

        elif len(chargeAts):
            ustr = '"nodes=self.expandNodes('+'\''+chargeAts.full_name()+'\''+');nodes.addCharges(\'Kollman\','+str(charges)+')"'
            self.undoCmds = "exec("+ustr+")"
        else:
            ustr='"nodes=self.expandNodes('+'\''+nochargeAts.full_name()+'\''+');nodes.delCharges(\'Kollman\')"'
            self.undoCmds = "exec("+ustr+")"


    def doit(self, nodes):

        nodes = self.vf.expandNodes(nodes)
        if len(nodes)==0: return 'ERROR'

        self.vf.fixHNames(nodes, topCommand=0)

        allRes = nodes.findType(Residue).uniq()
        allAtoms = allRes.atoms
        allChains = allRes.parent.uniq()

        total = 0.0
        for a in allAtoms:
            if not self.q.has_key(a.parent.type):
                a._charges['Kollman'] = 0.0
            else:
                dict = self.q[a.parent.type]
                if dict.has_key(a.name):
                    a._charges['Kollman'] = dict[a.name]
                    total = total + a._charges['Kollman']
                else:
                    a._charges['Kollman'] = 0.0

        #fix histidines
        hisRes = allRes.get(lambda x:x.name[:3]=='HIS')
        if hisRes is not None and len(hisRes)!=0:
            for hres in hisRes:
                total = self.fixHisRes(hres, total)

        #fix cys's
        cysRes = allRes.get(lambda x:x.name[:3]=='CYS')
        if cysRes is not None and len(cysRes)!=0:
            for cres in cysRes:
                total = self.fixCysRes(cres, total)

        #check for termini:
        for ch in allChains:
            if ch.residues[0] in allRes:
                ##fix the charge on Hs 
                total = self.fixNterminus(ch.residues[0],total)
            if ch.residues[-1] in allRes:
                self.fixCterminus(ch.residues[-1], total)

        #make Kollman the current charge
        allAtoms.chargeSet = 'Kollman'

        return total
        

    def fixNterminus(self, nres, total):
        """newTotal<-fixNterminu(nres, total)
           \nnres is the N-terminal residue
           \ntotal is previous charge total on residueSet
           \nnewTotal is adjusted total after changes to nres.charges
        """
        nresSet =  nres.atoms.get('N')
        if nresSet is None or len(nresSet)==0:
            if self.q.has_key(nres.type):
                for at in nres.atoms:
                    try:
                        at._charges['Kollman'] = self.q[at.parent.type][at.name]
                    except:
                        at._charges['Kollman'] = 0.0
            else:
                print  nres.name, ' not in qkollua; charges set to 0.0'
                for at in nres.atoms:
                    at._charges['Kollman'] = 0.0
            return total
        Natom = nres.atoms.get('N')[0]
        caresSet = nres.atoms.get('CA')
        if caresSet is None or len(caresSet)==0:
            if self.q.has_key(nres.type):
                for at in nres.atoms:
                    at._charges['Kollman'] = self.q[at.parent.type][at.name]
            else:
                print  nres.name, ' not in qkollua; charges set to 0.0'
                for at in nres.atoms:
                    at._charges['Kollman'] = 0.0
            return total
        CAatom = nres.atoms.get('CA')
        if CAatom is not None and len(CAatom)!=0:
            CAatom = nres.atoms.get('CA')[0]
            hlist = Natom.findHydrogens()
            #5/5:assert len(hlist), 'polar hydrogens missing from n-terminus'
            if not len(hlist): 
                print 'polar hydrogens missing from n-terminus of chain ' + nres.parent.name
                #self.warningMsg('polar hydrogens missing from n-terminus')
            if nres.type == 'PRO':
                #divide .059 additional charge between CA + CD
                #FIX THIS what if no CD?
                #CDatom = nres.atoms.get('CD')[0]
                CDatom = nres.atoms.get('CD')
                if CDatom is not None and len(CDatom)!=0:
                    CDatom = CDatom[0]
                    CDatom._charges['Kollman'] = CDatom._charges['Kollman'] + .029
                else:
                    print 'WARNING: no CD atom in ', nres.name
                Natom._charges['Kollman'] = Natom._charges['Kollman'] + .274
                CAatom._charges['Kollman'] = CAatom._charges['Kollman'] + .030
                for ha in hlist:
                    ha._charges['Kollman'] = .333
            else:
                Natom._charges['Kollman'] = Natom._charges['Kollman'] + .257
                CAatom._charges['Kollman'] = CAatom._charges['Kollman'] + .055
                for ha in hlist:
                    ha._charges['Kollman'] = .312
            
            return total + 1
        else:
            print 'WARNING: no CA atom in ', nres.name
            return total


    def fixCterminus(self, cres, total):
        """newTotal<-fixCterminu(cres, total)
            \ncres is the C-terminal residue
            \ntotal is previous charge total on residueSet
            \nnewTotal is adjusted total after changes to cres.charges
        """
        OXYatomSet = cres.atoms.get('OXT')
        if OXYatomSet is not None and len(OXYatomSet)!=0:
            OXYatom = OXYatomSet[0]
            OXYatom._charges['Kollman'] = -.706
            #CAUTION!
            CAatom = cres.atoms.get('CA')
            if CAatom is not None and len(CAatom)!=0:
                CAatom = cres.atoms.get('CA')[0]
                CAatom._charges['Kollman'] = CAatom._charges['Kollman'] - .006
                #CAUTION!
                Catom = cres.atoms.get('C')
                if Catom is not None and len(Catom)!=0:
                    Catom = cres.atoms.get('C')[0]
                    Catom._charges['Kollman'] = Catom._charges['Kollman'] - .082
                    Oatom = cres.atoms.get('O')
                    if Oatom is not None and len(Oatom)!=0:
                        #CAUTION!
                        Oatom = cres.atoms.get('O')[0]
                        Oatom._charges['Kollman'] = Oatom._charges['Kollman'] - .206
                        return total - 1

            
        else: 
            #if there is no OXT don't change charges
            return total
            

    def fixHisRes(self, his, total):
        """newTotal<-fixHisRes(his, total)
           \nhis is a HISTIDINE residue
           \ntotal is previous charge total on residueSet
           \nnewTotal is adjusted total after changes to his.charges
        """
        hisAtomNames = his.atoms.name
        #oldcharge = Numeric.sum(his.atoms._charges['Kollman'])
        oldcharge = 0
        for at in his.atoms:
            oldcharge = oldcharge + at._charges['Kollman']
        assertStr = his.name + ' is lacking polar hydrogens'
        assert 'HD1' or 'HE2' in hisAtomNames, assertStr
        #get the appropriate dictionary
        if 'HD1' in hisAtomNames and 'HE2' in hisAtomNames:
            d = self.q['HIS+']
        elif 'HD1' in  hisAtomNames:
            d = self.q['HISD']
        elif 'HE2' in hisAtomNames:
            d = self.q['HIS']
        else:
            msgStr = his.full_name() + ' missing both hydrogens!'
            print msgStr
            #self.warningMsg(msgStr)
            return total

        #assign charges
        for a in his.atoms:
            if d.has_key(a.name):
                a._charges['Kollman'] = d[a.name]
            else:
                a._charges['Kollman'] = 0.0

        #correct total
        #newcharge = Numeric.sum(his.atoms._charges['Kollman'])
        newcharge = 0
        for at in his.atoms:
            newcharge = newcharge + at._charges['Kollman']
        total = total - oldcharge + newcharge
        return total


    def fixCysRes(self, cys, total):
        cysAtomNames = cys.atoms.name
        #oldcharge = Numeric.sum(cys.atoms._charges['Kollman'])
        oldcharge = 0
        for at in cys.atoms:
            oldcharge = oldcharge + at._charges['Kollman']
        #get the appropriate dictionary
        if 'HG' in cysAtomNames:
            d = self.q['CYSH']
        else:
            #cystine
            d = self.q['CYS']

        #assign charges
        for a in cys.atoms:
            if d.has_key(a.name):
                a._charges['Kollman'] = d[a.name]
            else:
                a._charges['Kollman'] = 0.0

        #correct total
        #newcharge = Numeric.sum(cys.atoms._charges['Kollman'])
        newcharge = 0
        for at in cys.atoms:
            newcharge = newcharge + at._charges['Kollman']
        total = total - oldcharge + newcharge
        return total



class AverageChargeErrorCommand(MVCommand):
    """Adjusts the charge on each atom in  residue with non-integral overall charge so that the sum of the charge on all the atoms in the residue is an integer.  Determines if initial sum is closer to the ceiling or the floor and then adds or subtracts the difference from this nearer value divided by the number of atoms to each atom.  The new chargeSet is called 'adjustedCharges'.
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:AverageChargeErrorCommand
    \nCommand:averageChargeError
    \nSynopsis:\n
        None<---averageChargeError(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly

    def guiCallback(self):
        sel = self.vf.getSelection()
        if len(sel):
            self.doitWrapper(sel, topCommand=0)
        else:
            self.warningMsg('No Molecules present!')


    def __call__(self, nodes, **kw):
        """None<---averageChargeError(nodes, **kw)
           \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        kw['topCommand'] = 0
        nodes = self.vf.expandNodes(nodes)
        if len(nodes): 
            apply(self.doitWrapper,(nodes,), kw)
        else: 
            return 'ERROR'

 
    def doit(self, nodes):
        totalCharge, resSet = self.vf.checkResCharges(nodes)
        if not len(resSet):
            self.warningMsg('no residues with non-integral charges found')
            return 'ERROR'
        if totalCharge==9999.9999:
            self.warningMsg('ERROR in checkResCharges')
            return 'ERROR'
        for res in resSet:
            self.averageCharge(res)
        tops = resSet.top.uniq()
        for t in tops:
            okAts = t.allAtoms.get(lambda x: not x._charges.has_key('adjustedCharge'))
            if okAts is not None and len(okAts)!=0:
                okAts.addCharges('adjustedCharges', okAts.charge)
        t.allAtoms.setCharges('adjustedCharges')


    def averageCharge(self, res):
        rats = res.atoms
        sum = Numeric.sum(Numeric.array(rats.charge))
        numRats = len(rats)
        fl_sum = math.floor(sum)
        ceil_sum = math.ceil(sum)
        errF = sum - fl_sum
        errC = ceil_sum - sum
        absF =math.fabs(errF)
        absC =math.fabs(errC)
        newCharges = []
        #make which ever is the smaller adjustment
        if absC<absF:
            delta = round(errC/numRats, 4)
            newCharges = []
            for a in rats:
                newCharges.append(a.charge + delta)
        else:
            delta = round(errF/numRats, 4)
            newCharges = []
            for a in rats:
                newCharges.append(a.charge - delta)
        #add these newCharges as a chargeSet
        #FIX THIS@@!!
        #NB THIS ONLY ADDS charge to ones with problems
        rats.addCharges('adjustedCharges', newCharges)
        rats.setCharges('adjustedCharges')
        chs = Numeric.sum(Numeric.array(rats.charge))
        #print 'chs=', chs,
        err = round(chs, 0) - chs
        res.err = round(err, 4)


#class SetTerminusChargeGUICommand(MVCommand):
#    """Allows user to set total charge on N terminus 
#    \nPackage:Pmv
#    \nModule :editCommands
#    \nClass:SetTerminusChargeGUICommand
#    \nCommand:setTerminusChargeGC
#    \nSynopsis:\n
#        None<---setTerminusChargeGC(nodes, **kw)
#    \nRequired Arguments:\n
#        nodes --- TreeNodeSet holding the current selection
#    """

#    
#    def __init__(self, func=None):
#        MVCommand.__init__(self, func)
#        self.flag = self.flag | self.objArgOnly


#    def onAddCmdToViewer(self):
#        if not self.vf.commands.has_key('labelByProperty'):
#            self.vf.loadCommand('labelCommands', 'labelByProperty','Pmv',
#                                topCommand=0)
#        if not self.vf.commands.has_key('labelByExpression'):
#            self.vf.loadCommand('labelCommands', 'labelByExpression','Pmv',
#                                topCommand=0)
#        if not hasattr(self.vf, 'checkResCharges'):
#            self.vf.loadCommand('editCommands', 'checkResCharges','Pmv',
#                                topCommand=0)
#    

#    def guiCallback(self):
#        sel = self.vf.getSelection()
#        if len(sel):
#            self.doitWrapper(sel, topCommand=0)
#        else:
#            self.warningMsg('No Molecules present!')


#    def __call__(self, nodes, netcharge=1.0, **kw):
#        """None<---setTerminusChargeGC(nodes, **kw)
#           \nnodes --- TreeNodeSet holding the current selection"""
#        if type(nodes) is types.StringType:
#            self.nodeLogString = "'"+nodes+"'"
#        kw['topCommand'] = 0
#        nodes = self.vf.expandNodes(nodes)
#        if len(nodes): 
#            apply(self.doitWrapper,(nodes, netcharge), kw)
#        else: 
#            return 'ERROR'


#    def doit(self, nodes, netcharge):
#        if totalCharge==9999.9999:
#            self.warningMsg('ERROR in checkResCharges')
#            return 'ERROR'
#        resNames = []
#        if len(resSet):
#            resSet.sort()
#        else:
#            self.warningMsg('no residues with non-integral charges found')
#            return 'ERROR'
#        for item in resSet:
#            resNames.append((item.full_name(), None))
#        #FIX THIS: have to change contents of listbox + labels
#        #if the molecule has changed....
#        ifd = self.ifd=InputFormDescr(title='Check Residue Charge Results:')
#        ifd.append({'name': 'numResErrsLabel',
#            'widgetType': Tkinter.Label,
#            'wcfg':{'text': str(len(resSet)) + ' Residues with non-integral charge:\n(double click to edit charges on a residue\nyellow number is amt to add\nfor closest integral charge)'},
#            'gridcfg':{'sticky': Tkinter.W+Tkinter.E}})
#        ifd.append({'name': 'resLC',
#            'widgetType':ListChooser,
#            'wcfg':{
#                'mode': 'single',
#                'entries': resNames,
#                'title': '',
#                'command': CallBackFunction(self.showErrResidue, resSet),
#                'lbwcfg':{'height':5, 
#                    'selectforeground': 'red',
#                    'exportselection': 0,
#                    'width': 30}},
#            'gridcfg':{'sticky':'news','row':2,'column':0} })
#        ifd.append({'name': 'chargeLabel',
#            'widgetType':Tkinter.Label,
#            'wcfg':{'text':'Net Charge on ResidueSet:  ' + str(totalCharge)},
#            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
#        ifd.append({'name':'averBut',
#            'widgetType':Tkinter.Button,
#            'wcfg': { 'text':'Spread Charge Deficit\nover all atoms in residue',
#                'command': CallBackFunction(self.averageCharge, resSet)},
#            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
#        #ifd.append({'name':'showBut',
#            #'widgetType':Tkinter.Button,
#            #'wcfg': { 'text':'Save Non-Integral Charge Residues As Set',
#                #'command': CallBackFunction(self.saveErrResidues, resSet)},
#            #'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
#        ifd.append({'widgetType':Tkinter.Button,
#            'wcfg':{'bd':6, 'text':'Dismiss',
#                    'command': CallBackFunction(self.Dismiss_cb, resSet)},
#            'gridcfg':{'sticky':'ew', 'columnspan':4}})
#        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
#        self.form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
#        eD = self.ifd.entryByName
#        eD['resLC']['widget'].lb.bind('<Double-Button-1>', \
#            CallBackFunction(self.editResCharges, resSet), add='+')
#        self.totalChLab = eD['chargeLabel']['widget']
#        #else:
#            #self.form.deiconify()
#            #self.form.lift()
#            ##vals = self.vf.getUserInput(ifd, modal=0, blocking=1, 
#            ##        scrolledFrame=1, width=300, height=220)


#    def Dismiss_cb(self, resSet, event=None):
#        self.form.destroy()
#        if len(resSet):
#            self.vf.setIcomLevel(Residue, topCommand=0)
#            self.vf.labelByProperty(resSet, log=0, negate=1)
#            self.vf.setIcomLevel(Atom, topCommand=0)
#            self.vf.labelByExpression(resSet.atoms, lambdaFunc=1, \
#                function='lambda x: 2', log=0, negate=1)
#            self.vf.GUI.VIEWER.Redraw()
#            

#    def updateTotalCharge(self, resSet, event=None):
#        #make sure form still exists before trying to do update
#        if not self.form.f.winfo_exists():
#            return
#        totalCharge = 0
#        tops = resSet.top.uniq()
#        for top in tops:
#            totalCharge = totalCharge + Numeric.sum(top.allAtoms.charge)
#        totalCharge = round(totalCharge, 4)
#        self.totalChLab.config({'text':'New Net Charge on ResidueSet:  ' + str(totalCharge)})
#        

#    def averageCharge(self, resSet, event=None):
#        self.vf.averageChargeError(resSet)
#        #print 'averaged charge error'
#        self.vf.setIcomLevel(Residue, topCommand=0)
#        self.vf.labelByProperty(resSet, properties=("err",), \
#                    textcolor="yellow",  log=0, font="arial1.glf")
#        self.vf.setIcomLevel(Atom, topCommand=0)
#        self.vf.labelByExpression(resSet.atoms, lambdaFunc=1, \
#                    function='lambda x:str(x.charge)',log=0,font="arial1.glf")
#        self.updateTotalCharge(resSet)
#        ##want charge on the whole molecule
#        #totalCharge = 0
#        #tops = resSet.top.uniq()
#        #for top in tops:
#            #totalCharge = totalCharge + Numeric.sum(top.allAtoms.charge)
#        #self.totalChLab.config({'text':'New Net Charge on ResidueSet:  ' + str(totalCharge)})
#        

#    def editResCharges(self, resSet, event=None):
#        lb = self.ifd.entryByName['resLC']['widget'].lb
#        if lb.curselection() == (): return
#        resName = lb.get(lb.curselection())
#        resNode = self.vf.Mols.NodesFromName(resName)[0]
#        #need to open a widget here to facilitate changing charges
#        self.vf.editAtomChargeGC.setUp(resNode)
#        self.vf.setICOM(self.vf.editAtomChargeGC, topCommand=0)
#        self.updateTotalCharge(resSet)


#    def showErrResidue(self, resSet, event=None):
#        lb = self.ifd.entryByName['resLC']['widget'].lb
#        if lb.curselection() == (): return
#        resName = lb.get(lb.curselection())
#        resNode = self.vf.Mols.NodesFromName(resName)[0]
#        oldSel = self.vf.getSelection()
#        self.vf.clearSelection(topCommand=0)
#        self.vf.setIcomLevel(Residue, topCommand=0)
#        self.vf.setICOM(self.vf.select, modifier=None, topCommand=0)
#        self.vf.labelByProperty(ResidueSet([resNode]), properties=("err",), textcolor="yellow",  log=0, font="arial1.glf")
#        self.vf.setIcomLevel(Atom, topCommand=0)
#        self.vf.labelByExpression(resNode.atoms, lambdaFunc=1, function='lambda x:str(x.charge)',  log=0, font="arial1.glf")
#        self.updateTotalCharge(resSet)


#    def saveErrResidues(self, resSet, event=None):
#        nameStr = resSet.full_name()
#        self.vf.saveSet(resSet, nameStr, topCommand=0)


#checkChargesGUICommandGuiDescr = {'widgetType':'Menu',
#                                  'menuBarName':'menuRoot',
#                                  'menuButtonName':'Edit',
#                                  'menuCascadeName':'Charges',
#                                  'menuEntryLabel':'Check Charges'}

#CheckChargesGUICommandGUI=CommandGUI()
#CheckChargesGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 
#        'Check Totals on Residues', cascadeName='Charges')




class CheckChargesGUICommand(MVCommand):
    """Allows user to call checkResCharges on each residue in selection
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:CheckChargesGUICommand
    \nCommand:checkChargesGC
    \nSynopsis:\n
        None<---checkChargesGC(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    """

    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('labelByProperty'):
            self.vf.loadCommand('labelCommands', 'labelByProperty','Pmv',
                                topCommand=0)
        if not self.vf.commands.has_key('labelByExpression'):
            self.vf.loadCommand('labelCommands', 'labelByExpression','Pmv',
                                topCommand=0)
        if not hasattr(self.vf, 'checkResCharges'):
            self.vf.loadCommand('editCommands', 'checkResCharges','Pmv',
                                topCommand=0)
    

    def guiCallback(self):
        sel = self.vf.getSelection()

        if len(sel):
            self.doitWrapper(sel, topCommand=0)
        else:
            self.warningMsg('No Molecules present!')


    def __call__(self, nodes, **kw):
        """None<---checkChargesGC(nodes, **kw)
           \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        kw['topCommand'] = 0
        nodes = self.vf.expandNodes(nodes)
        if len(nodes): 
            apply(self.doitWrapper,(nodes,), kw)
        else: 
            return 'ERROR'


    def doit(self, nodes):
        totalCharge, resSet = self.vf.checkResCharges(nodes)
        if totalCharge==9999.9999:
            self.warningMsg('ERROR in checkResCharges')
            return 'ERROR'
        resNames = []
        if len(resSet):
            resSet.sort()
        else:
            self.warningMsg('no residues with non-integral charges found')
            return 'ERROR'
        for item in resSet:
            resNames.append((item.full_name(), None))
        #FIX THIS: have to change contents of listbox + labels
        #if the molecule has changed....
        ifd = self.ifd=InputFormDescr(title='Check Residue Charge Results:')
        ifd.append({'name': 'numResErrsLabel',
            'widgetType': Tkinter.Label,
            'wcfg':{'text': str(len(resSet)) + ' Residues with non-integral charge:\n(double click to edit charges on a residue\nyellow number is amt to add\nfor closest integral charge)'},
            'gridcfg':{'sticky': Tkinter.W+Tkinter.E}})
        ifd.append({'name': 'resLC',
            'widgetType':ListChooser,
            'wcfg':{
                'mode': 'single',
                'entries': resNames,
                'title': '',
                'command': CallBackFunction(self.showErrResidue, resSet),
                'lbwcfg':{'height':5, 
                    'selectforeground': 'red',
                    'exportselection': 0,
                    'width': 30}},
            'gridcfg':{'sticky':'news','row':2,'column':0} })
        ifd.append({'name': 'chargeLabel',
            'widgetType':Tkinter.Label,
            'wcfg':{'text':'Net Charge on ResidueSet:  ' + str(totalCharge)},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        ifd.append({'name':'averBut',
            'widgetType':Tkinter.Button,
            'wcfg': { 'text':'Spread Charge Deficit\nover all atoms in residue',
                'command': CallBackFunction(self.averageCharge, resSet)},
            'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        #ifd.append({'name':'showBut',
            #'widgetType':Tkinter.Button,
            #'wcfg': { 'text':'Save Non-Integral Charge Residues As Set',
                #'command': CallBackFunction(self.saveErrResidues, resSet)},
            #'gridcfg':{'sticky':Tkinter.W+Tkinter.E}})
        ifd.append({'widgetType':Tkinter.Button,
            'wcfg':{'bd':6, 'text':'Dismiss',
                    'command': CallBackFunction(self.Dismiss_cb, resSet)},
            'gridcfg':{'sticky':'ew', 'columnspan':4}})
        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.form.root.protocol('WM_DELETE_WINDOW',self.Dismiss_cb)
        eD = self.ifd.entryByName
        eD['resLC']['widget'].lb.bind('<Double-Button-1>', \
            CallBackFunction(self.editResCharges, resSet), add='+')
        self.totalChLab = eD['chargeLabel']['widget']
        #else:
            #self.form.deiconify()
            #self.form.lift()
            ##vals = self.vf.getUserInput(ifd, modal=0, blocking=1, 
            ##        scrolledFrame=1, width=300, height=220)


    def Dismiss_cb(self, resSet, event=None):
        self.form.destroy()
        if len(resSet):
            self.vf.setIcomLevel(Residue, topCommand=0)
            self.vf.labelByProperty(resSet, log=0, negate=1)
            self.vf.setIcomLevel(Atom, topCommand=0)
            self.vf.labelByExpression(resSet.atoms, lambdaFunc=1, \
                function='lambda x: 2', log=0, negate=1)
            self.vf.GUI.VIEWER.Redraw()
            

    def updateTotalCharge(self, resSet, event=None):
        #make sure form still exists before trying to do update
        if not self.form.f.winfo_exists():
            return
        totalCharge = 0
        tops = resSet.top.uniq()
        for top in tops:
            totalCharge = totalCharge + Numeric.sum(top.allAtoms.charge)
        totalCharge = round(totalCharge, 4)
        self.totalChLab.config({'text':'New Net Charge on ResidueSet:  ' + str(totalCharge)})
        

    def averageCharge(self, resSet, event=None):
        self.vf.averageChargeError(resSet)
        #print 'averaged charge error'
        self.vf.setIcomLevel(Residue, topCommand=0)
        self.vf.labelByProperty(resSet, properties=("err",), \
                    textcolor="yellow",  log=0, font="arial1.glf")
        self.vf.setIcomLevel(Atom, topCommand=0)
        self.vf.labelByExpression(resSet.atoms, lambdaFunc=1, \
                    function='lambda x:str(x.charge)',log=0,font="arial1.glf")
        self.updateTotalCharge(resSet)
        ##want charge on the whole molecule
        #totalCharge = 0
        #tops = resSet.top.uniq()
        #for top in tops:
            #totalCharge = totalCharge + Numeric.sum(top.allAtoms.charge)
        #self.totalChLab.config({'text':'New Net Charge on ResidueSet:  ' + str(totalCharge)})
        

    def editResCharges(self, resSet, event=None):
        lb = self.ifd.entryByName['resLC']['widget'].lb
        if lb.curselection() == (): return
        resName = lb.get(lb.curselection())
        resNode = self.vf.Mols.NodesFromName(resName)[0]
        #need to open a widget here to facilitate changing charges
        self.vf.editAtomChargeGC.setUp(resNode)
        self.vf.setICOM(self.vf.editAtomChargeGC, modifier="Shift_L", topCommand=0)
        self.updateTotalCharge(resSet)


    def showErrResidue(self, resSet, event=None):
        lb = self.ifd.entryByName['resLC']['widget'].lb
        if lb.curselection() == (): return
        resName = lb.get(lb.curselection())
        resNode = self.vf.Mols.NodesFromName(resName)[0]
        oldSel = self.vf.getSelection()
        self.vf.clearSelection(topCommand=0)
        self.vf.setIcomLevel(Residue, topCommand=0)
        self.vf.setICOM(self.vf.select, modifier="Shift_L", topCommand=0)
        self.vf.labelByProperty(ResidueSet([resNode]), properties=("err",), textcolor="yellow",  log=0, font="arial1.glf")
        self.vf.setIcomLevel(Atom, topCommand=0)
        self.vf.labelByExpression(resNode.atoms, lambdaFunc=1, function='lambda x:str(x.charge)',  log=0, font="arial1.glf")
        self.updateTotalCharge(resSet)


    def saveErrResidues(self, resSet, event=None):
        nameStr = resSet.full_name()
        self.vf.saveSet(resSet, nameStr, topCommand=0)


checkChargesGUICommandGuiDescr = {'widgetType':'Menu',
                                  'menuBarName':'menuRoot',
                                  'menuButtonName':'Edit',
                                  'menuCascadeName':'Charges',
                                  'menuEntryLabel':'Check Charges'}

CheckChargesGUICommandGUI=CommandGUI()
CheckChargesGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 
        'Check Totals on Residues', cascadeName='Charges')



class SetChargeCommand(MVCommand):
    """allows user to set string used to index into _charges dictionary
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:SetChargeCommand
    \nCommand:setChargeSet
    \nSynopsis:\n
        None<---setChargeSet(nodes, key, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
        \nkey --- what charges (keyword of the _charges dictionary).
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)


    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            self.key = Tkinter.StringVar()


    def __call__(self, nodes, key, **kw):
        """None <--- setChargeSet(nodes, key, **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nkey --- what charges (keyword of the _charges dictionary).
           """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        #is this a good idea?
        #assert key in nodes._charges.keys()
        kw['redraw'] = 0
        if len(nodes): 
            nodes = nodes.findType(Atom)
            #check that the key is valid
            nodes_with_key = filter(lambda x: key in x._charges.keys(), nodes)
            if len(nodes_with_key)!=len(nodes):
                raise KeyError
            return apply(self.doitWrapper,(nodes, key), kw)
        else: return 'ERROR'


    def doit(self, nodes, key):
        nodes.chargeSet = key
        #should be nodes.setCharges(key)


    def guiCallback(self):
        z = self.vf.getSelection()
        if not len(z):
            return
        nodes = z.findType(Atom)
        # only displays the charges keys f
        keys = nodes._charges.keys()
        if not len(keys):
            print 'no charges to choose from'
            return
        self.key.set(keys[0])
        if len(keys)>1:
            currentCharge = self.key.get()
            ifd = self.ifd = InputFormDescr(title = 'Select charge')
            ifd.append({'name': 'chargeList',
                        'listtext': keys,
                        'widgetType': Tkinter.Radiobutton,
                        'groupedBy': 10,
                        'defaultValue': currentCharge,
                        'variable': self.key,
                        'gridcfg': {'sticky': Tkinter.W}})
            val = self.vf.getUserInput(ifd)
            if val is None or val=={} or not len(val):
                return 
        else:
            print 'using only available charge: ', keys[0]
        kw = {}
        kw['redraw'] = 0
##         if self.vf.userpref['expandNodeLogString']['value'] == 0:
##             self.nodeLogString = "self.getSelection()"

        apply(self.doitWrapper, (nodes, self.key.get()), kw)

setChargeGUICommandGuiDescr = {'widgetType':'Menu',
                                  'menuBarName':'menuRoot',
                                  'menuButtonName':'Edit',
                                  'menuCascadeName':'Charges',
                                  'menuEntryLabel':'Set Charge Field'}

SetChargeCommandGUI=CommandGUI()
SetChargeCommandGUI.addMenuCommand('menuRoot', 'Edit', 'Set Charge Field',
                        cascadeName='Charges')



class CheckResidueChargesCommand(MVCommand):
    """Allows user to check charges on each residue + whole molecule 
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:CheckResidueChargesCommand
    \nCommand:checkResCharges
    \nSynopsis:\n
        None <--- checkResCharges(nodes, **kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def __call__(self, nodes, **kw):
        """None <- checkResCharges(nodes, **kw)
           \nnodes --- TreeNodeSet holding the current selection"""
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if len(nodes): 
            #if there are nodes, there have to be Residues
            resSet = nodes.findType(Residue).uniq()
            return apply(self.doitWrapper,(resSet,), kw)
        else: 
            kw['log'] = 0
            self.warningMsg('no nodes specified')
            return 9999.9999, ResidueSet([])


    def doit(self, resSet):
        totalCharge = 0.0
        errResSet = ResidueSet([])
        for item in resSet:
            chs = Numeric.sum(item.atoms.charge)
            fl_sum = math.floor(chs)
            ceil_sum = math.ceil(chs)
            errF = chs - fl_sum
            errC = ceil_sum - chs
            absF = math.fabs(errF)
            absC = math.fabs(errC)
            #make which ever is the smaller adjustment
            if absC<absF:
                err = round(errC, 4)
            else:
                err = round(errF, 4)
            #print 'labelling with err = ', err
            item.err = err
            totalCharge = totalCharge + chs
            #err = round(chs, 0) - chs
            #item.err = err
            if err > .005 or err < -0.005:
                errResSet.append(item)
        return totalCharge, errResSet



class AssignAtomsRadiiCommand(MVCommand):
    """This commands adds radii to all the atoms loaded so far in the application. Only default radii for now
    \nPackage:Pmv
    \nModule :editCommands
    \nClass:AssignAtomsRadiiCommand
    \nCommand:assignAtomsRadii
    \nSynopsis:\n
    None <- mv.assignAtomsRadii(nodes, united=1, overwrite=1,**kw)\n
    \nRequired Arguments:\n
    nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
    \nunited   --- (default=1) flag to specify whether or not to consider
            hydrogen atoms. When hydrogen are there the atom radii
            is smaller. 

    overwrite ---(default=1) flag to specify whether or not to overwrite
            existing radii information.\n

    
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly


    def doit(self, nodes, united=True, overwrite=False):
        #nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        molecules = nodes.top.uniq()
        for mol in molecules:
            # Reassign the radii if overwrite is True
            if overwrite is True:
                mol.unitedRadii = united
                mol.defaultRadii(united=united, overwrite=overwrite)
            # Reassign the radii if different.
            elif mol.unitedRadii != united:
                mol.unitedRadii = united
                mol.defaultRadii(united=united, overwrite=overwrite)


    def onAddObjectToViewer(self, obj):
        obj.unitedRadii = None
        

    def __call__(self, nodes, united=True, overwrite=False, **kw):
        """ None <- mv.assignAtomsRadii(nodes, united=True, overwrite=False,**kw)
        \nRequired Arguments:\n
         nodes --- TreeNodeSet holding the current selection 

         \nOptional Arguments:\n
          united --- (default=True) Boolean flag to specify whether or not
                    to consider hydrogen atoms. When hydrogen are there the
                    atom radii is smaller.\n 

          overwrite --- (default=True) Boolean flag to specify whether or not to overwrite
                    existing radii information.\n

        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not len(nodes): return 
        kw['united'] = united
        kw['overwrite'] = overwrite
        apply(self.doitWrapper, (nodes, ), kw)

        
    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes: return
        idf = InputFormDescr(title="Assign Atoms Radii")
        idf.append({'widgetType':Tkinter.Checkbutton,
                    'name':'united',
                    'tooltip': "When united is set to 1 it means that the radii should be calculated without hydrogen atoms.",
                    'defaultValue':1,
                    'wcfg':{'text':'United Radii',
                            'variable':Tkinter.IntVar()},
                    'gridcfg':{'sticky':'w'}})
        idf.append({'widgetType':Tkinter.Checkbutton,
                    'name':'overwrite',
                    'tooltip': "When overwrite is off the existing radii information won't be overwritten.",
                    'defaultValue':0,
                    'wcfg':{'text':'Overwrite Radii','variable':Tkinter.IntVar()},
                    'gridcfg':{'sticky':'w'}})

        val = self.vf.getUserInput(idf)
        if val is None or val == {}: return
        apply(self.doitWrapper, (self.vf.getSelection(),), val)

assignAtomsRadiiGUICommandGuiDescr = {'widgetType':'Menu',
                                      'menuBarName':'menuRoot',
                                      'menuButtonName':'Edit',
                                      'menuCascadeName':'Atoms',
                                      'menuEntryLabel':'Assign Radii'}


AssignAtomsRadiiCommandGUI = CommandGUI()
AssignAtomsRadiiCommandGUI.addMenuCommand('menuRoot', 'Edit',
                   'Assign Radii', cascadeName = 'Atoms')


commandList=[
    {'name':'editAtomTypeGC','cmd':EditAtomTypeGUICommand(),
     'gui': EditAtomTypeGUICommandGUI},
    {'name':'editAtomChargeGC','cmd':EditAtomChargeGUICommand(),
     'gui': None},
    #{'name':'editAtomChargeGC','cmd':EditAtomChargeGUICommand(),
    # 'gui': EditAtomChargeGUICommandGUI},
    {'name':'typeAtoms','cmd':TypeAtomsCommand(),
     'gui': TypeAtomsCommandGUI},
    {'name':'deleteWater','cmd':DeleteWaterCommand(),
     'gui': DeleteWaterCommandGUI},
    {'name':'editAtomType','cmd':EditAtomTypeCommand(), 'gui':None},
    {'name':'assignAtomsRadii', 'cmd':AssignAtomsRadiiCommand(),
     'gui': AssignAtomsRadiiCommandGUI},

    {'name':'typeBonds','cmd':TypeBondsCommand(),
     'gui': TypeBondsCommandGUI},

    {'name':'addKollmanChargesGC','cmd':AddKollmanChargesGUICommand(),
     'gui': AddKollmanChargesGUICommandGUI},
    {'name':'addKollmanCharges','cmd':AddKollmanChargesCommand(),'gui': None},
    {'name':'computeGasteigerGC','cmd':ComputeGasteigerGUICommand(),
     'gui': ComputeGasteigerGUICommandGUI},
    {'name':'computeGasteiger','cmd':ComputeGasteigerCommand(), 'gui': None},
    {'name':'checkChargesGC','cmd':CheckChargesGUICommand(),
     'gui': CheckChargesGUICommandGUI},
    {'name':'checkResCharges','cmd':CheckResidueChargesCommand(),'gui': None},
    {'name':'averageChargeError','cmd':AverageChargeErrorCommand(),'gui': None},
    {'name':'setChargeSet','cmd':SetChargeCommand(),
     'gui': SetChargeCommandGUI},

    {'name':'add_hGC','cmd':AddHydrogensGUICommand(),
     'gui': AddHydrogensGUICommandGUI},
    {'name':'add_h','cmd':AddHydrogensCommand(), 'gui': None},
    {'name':'mergeNPHSGC','cmd':MergeNPHsGUICommand(),
     'gui': MergeNPHsGUICommandGUI},
    {'name':'mergeNPHS','cmd':MergeNPHsCommand(), 'gui': None},
    {'name':'fixHNamesGC','cmd':FixHydrogenAtomNamesGUICommand(),
     'gui': FixHydrogenAtomNamesGUICommandGUI},
    {'name':'fixHNames','cmd':FixHydrogenAtomNamesCommand(), 'gui': None},
    #{'name':'mergeFields','cmd':MergeFieldsCommand(),
     #'gui': MergeFieldsCommandGUI},
    #{'name':'mergeSets','cmd':MergeSetsCommand(),
     #'gui': MergeSetsCommandGUI},
    {'name':'mergeLPSGC','cmd':MergeLonePairsGUICommand(),
     'gui': MergeLonePairsGUICommandGUI},
    {'name':'mergeLPS','cmd':MergeLonePairsCommand(), 'gui': None},
    {'name':'splitNodesGC','cmd':SplitNodesGUICommand(),
     'gui': SplitNodesGUICommandGUI},
    {'name':'splitNodes','cmd':SplitNodesCommand(), 'gui': None},
    ]



def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
