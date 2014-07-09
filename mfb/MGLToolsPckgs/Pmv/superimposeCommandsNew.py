## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Authors:
# Sophie I. COON, William LINDSTROM, Michel F. SANNER, Brian NORLEDGE
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/superimposeCommandsNew.py,v 1.15.4.1 2010/12/30 21:56:18 rhuey Exp $
#
# $Id: superimposeCommandsNew.py,v 1.15.4.1 2010/12/30 21:56:18 rhuey Exp $
#

import numpy.oldnumeric as Numeric, os, Tkinter, Pmw

from Pmv.stringSelectorGUI import StringSelectorGUI
from Pmv.mvCommand import MVCommand, MVAtomICOM
from Pmv.guiTools import MoleculeChooser

from ViewerFramework.VFCommand import CommandGUI

from MolKit.molecule import Molecule, Atom, AtomSet
from MolKit.protein import Protein, Residue, Chain, ProteinSet, ResidueSet, ChainSet

from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolylines import IndexedPolylines
from mglutil.alignmentEditor import AlignmentEditor


from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
from mglutil.math.rigidFit import RigidfitBodyAligner
from SimpleDialog import SimpleDialog

from MolKit.tree import TreeNode, TreeNodeSet
from Pmv.moleculeViewer import EditAtomsEvent 
from types import ListType, TupleType, StringType, IntType, FloatType, LongType


class SuperimposeCommand(MVCommand):
    """ superimpose two equal-length AtomSets """

    def onAddCmdToViewer(self):
        self.rigidfitAligner = RigidfitBodyAligner()
        
    def doit(self, refAtoms, mobAtoms, updateGeom=True, showRMSD=True):
        """
        The SuperImposeAtomsCommand takes two set of Atoms of the same length
        compute the rotation and translation matrices to superimpose the
        mobAtoms onto the refAtoms using rigidFit module and then transform the
        corresponding geometry.

        updateGeom = True : transform the masterGeom of mobAtoms.
        showRMSD   = True : print and return RMSD 
        """

        if refAtoms is None or mobAtoms is None: return
        assert isinstance(refAtoms, TreeNodeSet)
        assert isinstance(mobAtoms, TreeNodeSet)

        refAtoms = refAtoms.findType(Atom)
        mobAtoms = mobAtoms.findType(Atom)
        # validate the inputs
        if len(refAtoms) !=len(mobAtoms):
            print "The two atomSet are not of equal length"
            return
        if len(refAtoms) < 3 :
            print "At least three atoms are needed for superimposition"
            return
        
        refCoords = refAtoms.coords
        mobCoords = mobAtoms.coords
        
        rigidfitAligner = RigidfitBodyAligner()
        rigidfitAligner.setRefCoords(refCoords)                
        rigidfitAligner.rigidFit(mobCoords)

        if updateGeom:
            rotMat =  Numeric.identity(4).astype('d')
            rotMat[:3,:3] = rigidfitAligner.rotationMatrix               
            transMat = Numeric.array(rigidfitAligner.translationMatrix)
            rotMat[3,:3] = transMat
            #print rotMat  # the matrix
            mGeom = mobAtoms[0].top.geomContainer.masterGeom        
            mGeom.SetRotation(Numeric.reshape(rotMat, (16,)).astype('f'))
            mGeom.viewer.Redraw()

        if showRMSD:
            rmsd=rigidfitAligner.rmsdAfterSuperimposition(mobCoords)
            print "RMSD = ", rmsd
            return rmsd
        else:
            return
            

    def __call__(self, refAtoms, mobAtoms, updateGeom=True, showRMSD=True,**kw):
        """
        None <- superimposeAtoms(refAtoms, mobAtoms,updateGeom=True, showRMSD=True, **kw)
        """
        if type(refAtoms) is StringType:
            self.nodeLogString = "'" + refAtoms +"'"
        refAtoms = self.vf.expandNodes(refAtoms)
        if type(mobAtoms) is StringType:
            self.nodeLogString = "'" + mobAtoms +"'"
        mobAtoms = self.vf.expandNodes(mobAtoms)

        if not mobAtoms or not refAtoms: return        
        if not kw.has_key('redraw'): kw['redraw'] = 1
        res=apply(self.doitWrapper, (refAtoms, mobAtoms, updateGeom, showRMSD), kw)
        return res
        

class TransformAtomsCommand(MVCommand):
    """ This command transforms an AtomSet object by a given matrix, without changing the coords
"""
        
    def doit(self, mat, mobAtoms):
        """
        mat:  tranformation matrix, in (4,4) Numeric array
        mobAtoms: AtomSet where the matrix is applied to """

        # fixme: need checking for mat (matrix) and mobAtoms
        sh=mat.shape
        if sh!=(4,4) and sh !=(16,):
            print "Need a 4x4 matrix or flatted (16,) list"
            return
        
        mGeom = mobAtoms[0].top.geomContainer.masterGeom 

        if sh ==(4,4):
            mGeom.SetRotation(Numeric.reshape(mat, (16,)).astype('f'))
        else:
            mGeom.SetRotation( mat )
            
        mGeom.viewer.Redraw()    
        return
        

    def __call__(self, mat, nodes, **kw):
        """
        None <- transformAtoms(mat, nodes, **kw)
        """
        
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return

        if not kw.has_key('redraw'): kw['redraw'] = 1
        apply(self.doitWrapper, (mat, nodes), kw)


        

class FreezeAtomsCommand(MVCommand):
    """ Freeze the Atoms, store the coordinates as shown in masterGeom  """

    def doit(self,mobAtoms):
        """
mobAtoms: AtomSet that is being frozen.
Assuming the AtomSet are from same molecule
        """

        # fixme: need checking for mat (matrix) and mobAtoms
        geomContainer = mobAtoms[0].top.geomContainer
        mGeom = geomContainer.masterGeom
        mat = mGeom.rotation
        mat = Numeric.reshape(mat, (4,4))

        # update coords
        mobAtoms = mobAtoms.findType(Atom)
        coords = mobAtoms.coords
        hCoords = Numeric.concatenate((coords,Numeric.ones((len(coords),1),\
                                                            'd')), 1)
        tCoords = Numeric.dot(hCoords, mat)[:,:3]
        tCoords = tCoords.tolist()
        mobAtoms.updateCoords(tCoords, 0) # overwritten the original coords
        
        # reset the rotation matrix of masterGeom
        identity = Numeric.identity(4,'f').ravel()
        mGeom.SetRotation(Numeric.identity(4,'f').ravel() ) 

        event = EditAtomsEvent('coords', mobAtoms)
        self.vf.dispatchEvent(event)
        
        mGeom.viewer.Redraw()
        
        return
        

    def __call__(self, nodes, **kw):
        """
        None <- transformAtoms(mat, nodes, **kw)
        """
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return

        if not kw.has_key('redraw'): kw['redraw'] = 1
        apply(self.doitWrapper, (nodes, ), kw)




class SuperimposeAtomsCommand(MVCommand):

    def onAddCmdToViewer(self):
        self.rigidfitAligner = RigidfitBodyAligner()
        
    def doit(self, refAtoms, mobAtoms):
        """
        The SuperImposeAtomsCommand takes two set of Atoms of the same length
        compute the rotation and translation matrices to superimpose the
        mobAtoms onto the refAtoms using rigidFit module and then transform the
        corresponding geometry.
        """

        refCoords = refAtoms.coords
        mobCoords = mobAtoms.coords
        
        self.rigidfitAligner.setRefCoords(refCoords)

        # Nothing can be done if the two sets of coords are not of the same
        # size
        if not len(refCoords) == len(mobCoords):
            print " ERROR: Cannot perform the superimposition because the 2 \
            mv.lsets of Atoms are not of the same length"
            return

        # Get the rotation and the translation ysing mglutil.math.rigidFit
        self.rigidfitAligner.rigidFit(mobCoords)
        #rotation, translation= rigidFit.rigid_fit( refCoords, inCoords)
        rotMat =  Numeric.identity(4).astype('d')
        rotMat[:3,:3] = self.rigidfitAligner.rotationMatrix
               
        transMat = Numeric.array(self.rigidfitAligner.translationMatrix)
        
        # transform the geometry representing the atoms only if a gui has been
        # created:
        #if not self.vf.hasGui:
        #    return

        # build the geometry name:
        mobMol = mobAtoms.top.uniq()[0]
        mob = mobMol.geomContainer.masterGeom
        #gName = 'root|'+ mobMol[0].name
        if not self.vf.hasGui:
            vi = self.vf.GUI.VIEWER
            oldCurrent = vi.currentObject
            vi.SetCurrentObject(mob)
        
            # transform only the given geometry.
            if vi.redirectTransformToRoot == 1:
                old = vi.redirectTransformToRoot
                vi.TransformRootOnly(0)
            else:
                old = 0

        
        # apply the rotation to the masterGeom of the inMol
        mob.SetRotation(Numeric.reshape(rotMat, (16,)))
        # apply the translation to the masterGeom of the inMol
        mob.SetTranslation(transMat)


##         refMol = refAtoms.top.uniq()[0]
##         refmg = refMol.geomContainer.masterGeom
        
##         refmg = refAtoms.top.uniq()[0].geomContainer.masterGeom
##         mat = refmg.GetMatrix(refmg)
##         tmat = Numeric.transpose(mat)
        
##         rot, trans, scale = refmg.Decompose4x4(Numeric.reshape(tmat, (16,)))
##         rot_1 = refmg.rotation
##         trans_1 = refmg.translation
##         print 'rot',rot
##         print 'trans',trans
##         print 'rot_1',rot_1
##         print 'trans_1',trans_1
        
##         mobPivot = list(mob.pivot)
##         mobPivot.append(1.)
##         transfo = Numeric.identity(4).astype('d')
##         transfo[:3,:3] = rotMat[:3,:3]
##         transfo[3, :3] = transMat
##         hc = Numeric.array(mobPivot)
##         tPivot = Numeric.dot(hc, transfo)
##         print tPivot[:3]
##         mob.SetPivot(tPivot[:3])
        
        #self.vf.centerOnNodes(refMol)
        #mob.ConcatRotationRelative(Numeric.reshape(rot, (16,)))
        #mob.ConcatTranslation(trans_1)
        
        if not self.vf.hasGui:
            if old == 1:
                vi.TransformRootOnly(1)
            vi.SetCurrentObject(oldCurrent)

        # Not sure to put that here ?
        # Need to concatenate with the transformation of the reference molecule
        # to have the two molecule aligned:
        # - Get the transformatiom matrix of the ref molecule and decompose it
        
##         refmg = refAtoms.top.uniq()[0].geomContainer.masterGeom
##         mat = refmg.GetMatrix(refmg)
##         tmat = Numeric.transpose(mat)
        
##         rot, trans, scale = refmg.Decompose4x4(Numeric.reshape(tmat, (16,)))
        
##         self.vf.transformObject('rot', gName, rot)
##         self.vf.transformObject('tra', gName, trans)
##         #self.vf.transformObject('sca', gName, scale)
        

    def __call__(self, refAtoms, mobAtoms, **kw):
        """
        None <- superimposeAtoms(refAtoms, mobAtoms, **kw)
        """
        if not kw.has_key('redraw'): kw['redraw'] = 1
        apply(self.doitWrapper, (refAtoms, mobAtoms), kw)
        

#class SuperimposeAtomsGUICommand(MVCommand, MVAtomICOM):
class SuperimposeAtomsGUICommand(SuperimposeCommand, MVAtomICOM):
    """
    
    The SuperimposeAtomsGUICommand provides a GUI interface to the
    SuperimposeAtomsCommand. This commands allows the user to create two sets
    of atoms one reference and mobile of the same length by picking,
    by string or using the alignment editor.
    These two sets are then fed to the SuperimposeAtoms command.
    
    - For now Only two 2 sets of Atoms belonging to a ref molecule and
      a mobile molecule can be superimposed simultaneously.

    - The command provides two way of defining those two sets of atoms:
      * By picking nodes 
      * By string:
      * Using the alignment editor
    """
    # The superimposeAtomsGC provides an GU interface to allow the user to create two sets of atoms
    # which will be used to do a pairwise superimposition.
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.refAtomList = []
        self.inAtomList = []
        #self.superImposedPairs = {}
        self.newPairs = {}
        self.pair = []
        self.mobMol = None
        self.refMol = None
        self.refNodes = {}
        self.mobNodes = {}
        self.filters = {'CA Atoms':lambda x: x.name == 'CA',
                        'Backbone Atoms': lambda x: x.name in ['CA', 'C',
                                                               'N', 'O',
                                                               'CA@A','C@A',
                                                               'N@A','O@A'],
                        'Heavy Atoms': lambda x: not x.element == 'H',
                        'All Atoms': None}
        self.defaultFilter = 'Backbone Atoms'


##     def doit(self, refAtoms, mobAtoms, updateGeom=True, showRMSD=True):
##         """same as in SuperimposeCommand """
##         SuperimposeCommand.doit(self, refAtoms, mobAtoms, updateGeom=True, showRMSD=True)
        

    def onAddCmdToViewer(self):
        # Check first is any of the command that superimpose depends on are
        # already loaded.
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand = 0)
        if not self.vf.commands.has_key('superimposeAtoms'):
            self.vf.loadCommand('superImposeCommands', 'superimposeAtoms',
                                'Pmv', topCommand = 0)
            
        if not self.vf.commands.has_key('startContinuousPicking'):
            self.vf.loadCommand('dejaVuCommands','startContinuousPicking',
                                'ViewerFramework', topCommand = 0)

        if not self.vf.commands.has_key('stopContinuousPicking'):
            self.vf.loadCommand('dejaVuCommands','stopContinuousPicking',
                                'ViewerFramework', topCommand = 0)
        if not self.vf.commands.has_key('labelByExpression'):
            self.vf.loadCommand('labelCommands', 'labelByExpression', 'Pmv',
                                topCommand = 0)

        self.sphere1 = Spheres(name='elt1', radii=0.5, 
                               materials = ( (0.,1.,0.),), protected=True)
        self.sphere2 = Spheres(name = 'elt2', radii=0.5, 
                               materials = ( (1.,1.,0.),), protected=True)


    def onRemoveObjectFromViewer(self,obj):
        if hasattr(self.vf,'alignment'):
            self.vf.alnEditor.deleteSequence(obj.name)
            self.vf.alnEditor.redraw()
        if obj.name == self.refMol:
            self.refMol=None
        if obj.name == self.mobMol:
            self.mobMol=None


    ##########################################################################
    ####   BY PICKING...
    ##########################################################################
    def initICOM(self, modifier):
        # set the callback of continuousPicking to label the picked node
        # 1- get a handle on the cbManager
        cbManager  = self.vf.startContinuousPicking.cbManager
        # 2- Save the existing callbacks
        #self.oldCallBacks = cbManager.callbacks
        # 3- Set to the new callback
        cbManager.SetCallback(CallBackFunction(self.labelByName))
        
        self.vf.startContinuousPicking()
        self.supcb = 0

    def labelByName(self, pick):
        # Continuous labeling.
        if pick is None: return
        atom = self.vf.findPickedAtoms(pick)
        if atom:
            level = self.vf.ICmdCaller.level.value
            self.vf.ICmdCaller.level.AddCallback(self.unlabelLevel)
            if level == Molecule : level = Protein
            self.node = atom.findType(level)
            funcItems = map(lambda x: x.full_name(), self.node)
            self.vf.labelByExpression(self.node,
                                      font = 'arial1.glf',
                                      location = 'First', 
                                      textcolor = 'red', only = 0,
                                      lambdaFunc = 1,negate=0,
                                      function = 'lambda x: str(x.full_name())\n\n',
                                      topCommand=0)
            
    def unlabelLevel(self, newLevel, oldLevel):
        if not hasattr(self, 'node'): return

        if oldLevel == Molecule: oldLevel = Protein
        # need to be at the former level for all the former picked stuff
        # so take it all.
        node = self.vf.getSelection()
        nodes = node.findType(oldLevel)
        # Careful in labelByProperty fix a bug if no label should not break! 
        self.vf.labelByExpression(nodes, negate=1, log=0)
        
    def stopICOM(self):
        # Destroy the inputForm
        #self.cmdForms['superimpose'].root.destroy()
        # Set the form to None.
        #del self.cmdForms['superimpose']

        # Set back the continuousPicking to unsolicitedPick
        cbManager  = self.vf.startContinuousPicking.cbManager
        if not len(self.oldCallBacks) == 0:
            cbManager.SetCallback(self.oldCallBacks[0])
            if len(self.oldCallBacks)>1:
                for cb in self.oldCallBacks[1:]:
                    cbManager.AddCallBack(cb)

        # Remove the unlabel callback bound to the self.vf.ICmdCaller.level
        if self.unlabelLevel in  self.vf.ICmdCaller.level.callbacks:
            self.vf.ICmdCaller.level.RemoveCallback(self.unlabelLevel)

        # Unlabel whatever is labeled
        level = self.vf.ICmdCaller.level.value
        
        nodes = self.vf.getSelection().findType(level)
        if not nodes is None or len(nodes)!=0:
            self.vf.labelByExpression(nodes, negate=1, log=0)

        # Stop the continuous picking.
        self.vf.stopContinuousPicking()

        self.sphere1.Set(vertices=[])
        self.sphere2.Set(vertices=[])
##         self.visualFeedBack(vertices =[])

    ##########################################################################
    ####  
    ##########################################################################
    def createNodesSets(self, refnodes=None, mobnodes=None):
        # Set the reference molecule and the mobile molecule....
        # 1- set the reference molecule and the mobile 
        from MolKit.protein import ProteinSet
        if refnodes:
            refMols = refnodes.top.uniq()
            if refMols == self.vf.Mols:
                self.warningMsg("Reference and mobile molecules should be selected.")
                return
            if len(refMols) > 1:
                self.warningMsg("Can have one and only one reference molecule.")
                return
            self.refMol = refMols[0]

        if mobnodes:
            mobMols = mobnodes.top.uniq()
            if refMols == self.vf.Mols:
                self.warningMsg("Reference and mobile molecules should be selected.")
                return
            if len(mobMols) > 1:
                self.warningMsg("Can have one and only one mobile molecule.")
                return
            if mobMols[0] == self.refMol:
                self.warningMsg("The mobile molecule must be different from the ref molecule")
                return
            self.mobMol = mobMols[0]

        # 2- Create the entries for the refNodes listChooser
        ebn = self.cmdForms['addPairs'].descr.entryByName
        if refnodes:
            reflc = ebn['refnodes']['widget']
            for rn in refnodes:
                if not rn.top == self.refMol: continue
                self.refNodes[rn.full_name()] = rn
                reflc.add((rn.full_name(), None))
            
        # Create the entries for  the mobNodes listChooser
        if mobnodes:
            moblc = ebn['mobnodes']['widget']
            for mn in mobnodes:
                if not mn.top == self.mobMol: continue
                self.mobNodes[mn.full_name()] = mn
                moblc.add((mn.full_name(), None))

    
    def createPairs(self, refnames, mobnames, slice, choice):
        # This is where the atom pairs are created
        # Get the ref atom set
        refAtms = AtomSet([])
        mobAtms = AtomSet([])
        for name in refnames:
            refnod = self.refNodes[name]
            atms = refnod.findType(Atom)
            refAtms = refAtms + atms

        for name in mobnames:
            mobnod = self.mobNodes[name]
            atms = mobnod.findType(Atom)
            mobAtms = mobAtms + atms
        # Now apply the filters to the sets
        if choice:
            refFiltAtms = refAtms.get(self.filters[choice])
            mobFiltAtms = mobAtms.get(self.filters[choice])
        if not len(refFiltAtms) == len(mobFiltAtms):
            #print 'slicing', slice
            self.warningMsg("the two sets of atoms needs to be of the same length")
            return
        ebn = self.cmdForms['pairs'].descr.entryByName
        lc = ebn['newpairs']['widget']
        for refatm, mobatm in map(None, refFiltAtms, mobFiltAtms):
            #self.pairs.append((refatm, mobatm))
            pairName = refatm.full_name() + '---' + mobatm.full_name()
            self.newPairs[pairName]=(refatm,mobatm)
            lc.add((pairName, None))
        

    ##########################################################################
    ####   GUI CALLBACKS
    ##########################################################################
    def pick_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        cbVar = int(ebn['pick']['variable'].get())
        if cbVar:
            self.vf.setICOM(self, modifier="Shift_L", topCommand=0)
        else:
            self.stopICOM()

    def string_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        cbVar = ebn['string']['variable']
        #print cbVar.get()
        if cbVar.get():
            # if pushed show the form
            val = self.showForm('editString', modal=1, blocking=0, force=1)
            cbVar.set(0)
        if val:
            if not val['srefNodes'] and not val['smobNodes']: return
            refnodes = val['srefNodes']
            if refnodes:
                refnodes.sort()
            mobnodes = val['smobNodes']
            if mobnodes: mobnodes.sort()
            self.createNodesSets(refnodes,mobnodes)
        
    def setDefault(self, text):
        pass
##         self.defaultFilter = text
##         if hasattr(self, 'pair') and len(self.pair) == 2:
##             filter = self.filters[text]
##             set1 = self.pair[0]
##             set2 = self.pair[1]
            
##             if filter:
##                 set1 = set1.get(filter)
##                 set2 = set2.get(filter)
##             if (set1 and set2) and (len(set1) == len(set2)):
##                 self.updateChooser(set1, set2)):

    def delete_cb(self):
        ebn = self.cmdForms['pairs'].descr.entryByName
        lc = ebn['newpairs']['widget']
        lc.clear()
        self.newPairs ={}
        return


    def dismiss_cb(self):
        if self.cmdForms.has_key('pairs'):self.cmdForms['pairs'].withdraw()
        if self.cmdForms.has_key('addPairs'):
            self.cmdForms['addPairs'].withdraw()
        if self.cmdForms.has_key('editString'):
            self.cmdForms['addPairs'].withdraw()
        # Dismiss all the forms ???
##         for v in self.cmdForms.values():
##             v.withdraw()

    def continuous_cb(self):
        # Sets the continuous flag to the right value ????
        pass

    def reset_cb(self):
        # Reset the superposition put back the mob molecule to the right place..
        pass
    def superimpose_cb(self):
        refAtoms = AtomSet()
        mobAtoms = AtomSet()
        for pair in self.newPairs.values():
            refAtoms.append(pair[0])
            mobAtoms.append(pair[1])
            
        apply( self.doitWrapper, (refAtoms,mobAtoms),  {} )
        

    def add_cb(self):
        val = self.showForm('addPairs', modal=1, blocking=0, force=1,
                            okCfg={'text':'Create Pairs'})
        # need to get all the nodes... from each listchooser
        if not val: return
        # Need this for the order of the nodes in the pairs...
        ebn = self.cmdForms['addPairs'].descr.entryByName
        reflc = ebn['refnodes']['widget']
        refnames = map(lambda x: x[0], reflc.entries)
        moblc = ebn['mobnodes']['widget']
        mobnames = map(lambda x: x[0], moblc.entries)
        self.createPairs(refnames, mobnames, val['slice'][0], val['choice'][0])
        
    def refremove_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        lc = ebn['refnodes']['widget']
        sel = lc.get()
        if sel:
            lc.remove(sel[0])
            if sel[0] in self.refNodes:
                del self.refNodes[sel[0]]

    def mobremove_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        lc = ebn['mobnodes']['widget']
        sel = lc.get()
        if sel:
            lc.remove(sel[0])
            if sel[0] in self.refNodes:
                del self.mobNodes[sel[0]]
                
    def refmoveup_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        lc = ebn['refnodes']['widget']
        sel = lc.get()
        if not sel: return
        sel = sel[0]
        selIndex = lc.entries.index((sel,None))
        if selIndex == 0: return
        lc.remove(sel)
        lc.insert(selIndex-1, sel)
        lc.select(sel)

    def mobmoveup_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        lc = ebn['mobnodes']['widget']
        sel = lc.get()
        if not sel: return
        sel = sel[0]
        selIndex = lc.entries.index((sel,None))
        if selIndex == 0: return
        lc.remove(sel)
        lc.insert(selIndex-1, sel)
        lc.select(sel)

    def refmovedown_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        lc = ebn['refnodes']['widget']
        sel = lc.get()
        if not sel: return
        sel = sel[0]
        selIndex = lc.entries.index((sel,None))
        if selIndex == len(lc.entries)-1: return
        lc.remove(sel)
        lc.insert(selIndex+1, sel)
        lc.select(sel)

    def mobmovedown_cb(self):
        ebn = self.cmdForms['addPairs'].descr.entryByName
        lc = ebn['mobnodes']['widget']
        sel = lc.get()
        if not sel: return
        sel = sel[0]
        selIndex = lc.entries.index((sel,None))
        if selIndex == len(lc.entries)-1: return
        lc.remove(sel)
        lc.insert(selIndex+1, sel)
        lc.select(sel)


    def guiCallback(self):
        #form = self.showForm('pairs', modal=0, blocking=0)
        val = self.showForm('pairs', modal=0, blocking=0)        

        
    def buildFormDescr(self, formName):
        if formName=='addPairs':
            # CREATE PAIRS GROUP
            idf = InputFormDescr(title="Superimpose")
            idf.append({'name':"mode",
                        'widgetType':Pmw.Group,
                        'container':{'mode':'w.interior()'},
                        'wcfg':{'tag_text':"Create Reference Nodes and Mobile Nodes Lists"},
                        'gridcfg':{'sticky':'wnse'}
                        })
            idf.append({'widgetType':Tkinter.Label,
                        'parent':'mode',
                        'wcfg':{'text':'By String'},
                        'gridcfg':{'sticky':'we'}}
                       )
            idf.append({'widgetType':Tkinter.Checkbutton,
                        'name':'string',
                        'parent':'mode',
                        #'tooltip':'Use the string selector to create refnode-mobnodes pairs',
                        'wcfg':{'text':'on/off','command':self.string_cb},
                        'gridcfg':{'sticky':'we','row':-1}})

            idf.append({'widgetType':Tkinter.Label,
                        'parent':'mode',
                        'wcfg':{'text':'By Picking'},
                        'gridcfg':{'sticky':'we', 'row':-1}}
                       )

            idf.append({'widgetType':Tkinter.Checkbutton,
                        'name':'pick',
                        'tooltip':'Use the picking event to create refnode-mobnodes pairs',
                        'parent':'mode',
                        'wcfg':{'text':'on/off','command':self.pick_cb},
                        'gridcfg':{'sticky':'we','row':-1}})
            
            
            ###############################################################
            ## EDIT REF/MOB NODES
            ###############################################################
            idf.append({'name':"editnodes",
                        'widgetType':Pmw.Group,
                        'container':{'editnodes':'w.interior()'},
                        'wcfg':{'tag_text':"Edit Reference Nodes and Mobile Nodes Lists:"},
                        'gridcfg':{'sticky':'wnse'}
                        })

            idf.append({'name':'refremove',
                        'parent':'editnodes',
                        'widgetType':Tkinter.Button,
                        'tooltip':""" Remove the selected entry from the
commands to be applied to the object when loaded in the application""",
                        'wcfg':{'text':'REMOVE','width':10,
                               'command':self.refremove_cb},
                        'gridcfg':{'sticky':'we', 'row':0, 'column':0}})

            idf.append({'name':'refoneup',
                        'parent':'editnodes',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""Move the selected entry up one entry""",
                        'wcfg':{'text':'Move up','width':10,
                                'command':self.refmoveup_cb},
                        'gridcfg':{'sticky':'we', 'row':1, 'column':0}})

            idf.append({'name':'refonedown',
                        'parent':'editnodes',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""Move the selected entry down one entry""",
                        'wcfg':{'text':'Move down','width':10,
                                'command':self.refmovedown_cb},
                        'gridcfg':{'sticky':'we', 'row':2, 'column':0}})


            
            # RefNodes listchooser
            idf.append({'widgetType':ListChooser,
                        'name':'refnodes',
                        'parent':'editnodes',
                        'tooltip':"""list of the reference nodes""",
                        'wcfg':{'entries':[],
                                'mode':'single',
                                'lbwcfg':{'exportselection':0},
                                'title':'Reference Nodes'},
                        'gridcfg':{'sticky':'we', 
                                   'row':0, 'column':1,'rowspan':3}})


            # MobNodes listchooser
            idf.append({'widgetType':ListChooser,
                        'name':'mobnodes',
                        'parent':'editnodes',
                        'tooltip':"""list of the mobile nodes""",
                        'wcfg':{'entries':[],
                                'mode':'single',
                                'lbwcfg':{'exportselection':0},
                                'title':'Mobile Nodes'},
                        'gridcfg':{'sticky':'we', 
                                   'row':0, 'column':2, 'rowspan':3}})

            
            idf.append({'name':'mobremove',
                        'parent':'editnodes',
                        'widgetType':Tkinter.Button,
                        'tooltip':""" Remove the selected mobile node""",
                        'wcfg':{'text':'REMOVE','width':10,
                               'command':self.mobremove_cb},
                        'gridcfg':{'sticky':'we','row':0, 'column':3}})

            idf.append({'name':'moboneup',
                        'parent':'editnodes',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""Move the selected entry up one entry""",
                        'wcfg':{'text':'Move up','width':10,
                                'command':self.mobmoveup_cb},
                        'gridcfg':{'sticky':'we','row':1, 'column':3}})

            idf.append({'name':'mobonedown',
                        'parent':'editnodes',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""Move the selected entry down one entry""",
                        'wcfg':{'text':'Move down','width':10,
                                'command':self.mobmovedown_cb},
                        'gridcfg':{'sticky':'we','row':2, 'column':3}})

            ###############################################################
            ## FILTERS
            ###############################################################
            
            idf.append({'name':"filter",
                        'widgetType':Pmw.Group,
                        'container':{'filters':'w.interior()'},
                        'wcfg':{'tag_text':"Apply Filters To The Ref/Mob nodes lists:"},
                        'gridcfg':{'sticky':'wnse'}
                        })
                                         
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'choice',
                        'parent':'filters',
                        'tooltip':"""This filter allows the user to choose
which atom to consider from the ref node or mob nodes sets to create the atom pairs""",
                        'defaultValue':self.defaultFilter,
                        'wcfg':{ 'scrolledlist_items': self.filters.keys(),
                                'selectioncommand':self.setDefault},
                        'gridcfg':{'sticky':'w'}})

            
            # If sets not of the same length:
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'slice',
                        'parent':'filters',
                        'defaultValue':'Beginning',
                        'tooltip':"""When the two sets of atoms are not of
the same length the user can chose what subset of the longest set to take,
beginning, the end or half and half""",
                        'wcfg':{'scrolledlist_items':['Beginning',
                                               'End',
                                               'Half/Half'],
                         },
                        'gridcfg':{'sticky':'w', 'row':-1}})


            return idf
            
        elif formName == 'pairs':
            idf = InputFormDescr(title="Pairwise Superimposition")


            # EDIT PAIRS GROUP
            idf.append({'name':"edit",
                        'widgetType':Pmw.Group,
                        'container':{'edit':'w.interior()'},
                        'wcfg':{'tag_text':"Edit Atom Pairs"},
                        'gridcfg':{'sticky':'wnse'}
                        })
                                         
            
            entries = map(lambda x: (x, None), self.newPairs.keys())
            idf.append({'widgetType':ListChooser,
                        'name':'newpairs',
                        'parent':'edit',
                        'wcfg':{'mode':'extended',
                                'entries':entries,
                                'lbwcfg':{'exportselection':1},
                                'title':'Reference Atoms    --    Mobile Atoms'},
                        'gridcfg':{'sticky':'wens', 'columnspan':2}})
            

            idf.append({'widgetType':Tkinter.Button,
                        'name': 'delete',
                        'parent':'edit',
                        'wcfg':{'width':15,'text': 'Add Pairs',
                                'command':self.add_cb},
                        'gridcfg':{'sticky':'we'}})

            idf.append({'widgetType':Tkinter.Button,
                        'name': 'delete',
                        'parent':'edit',
                        'wcfg':{'width':15,'text': 'Delete Pairs',
                                'command':self.delete_cb},
                        'gridcfg':{'sticky':'we', 'row':-1}})
            
            idf.append({'name':"superimpose",
                        'widgetType':Pmw.Group,
                        'container':{'superimpose':'w.interior()'},
                        'wcfg':{'tag_text':"Superimposation parameters"},
                        'gridcfg':{'sticky':'wnse'}
                        })
            # Continuous Superimposition
            idf.append({'widgetType':Tkinter.Checkbutton,
                        'name':'continuous',
                        'parent':'superimpose',
                        'wcfg':{'variable':Tkinter.IntVar(),
                                'text':'Continuous',
                                'command':self.continuous_cb,
                                'padx':10,'pady':10},
                        'gridcfg':{'sticky':'w'}})

                                         
            # Reset & SuperImpose button.
            idf.append({'widgetType':Tkinter.Button,
                        'name':'final',
                        'parent':'superimpose',
                        'wcfg':{'width':15,'text':'Superimpose',
                                'command':self.superimpose_cb},
                        'gridcfg':{'sticky':'we', 'row':-1}})

            idf.append({'widgetType':Tkinter.Button,
                        'parent':'superimpose',
                        'name':'reset',
                        'wcfg':{'text':'Reset', 'command':self.reset_cb},
                        'gridcfg':{'sticky':'we', 'row':-1}})


            idf.append({'widgetType':Tkinter.Button,
                        'name': 'dismiss',
                        'wcfg':{'text': 'DISMISS',
                                'command':self.dismiss_cb},
                        'gridcfg':{'sticky':'we', 'columnspan':2}})
            

            return idf

        elif formName == 'editString':

            idf = InputFormDescr(title = 'Get Nodes From String')
            
            idf.append({'name':"refgroup",
                        'widgetType':Pmw.Group,
                        'container':{'refgroup':'w.interior()'},
                        'wcfg':{'tag_text':"Reference Nodes:"},
                        'gridcfg':{'sticky':'wnse'}
                        })

            idf.append({'name':"mobgroup",
                        'widgetType':Pmw.Group,
                        'container':{'mobgroup':'w.interior()'},
                        'wcfg':{'tag_text':"Mobile Nodes:"},
                        'gridcfg':{'sticky':'wnse', 'row':-1}
                        })


            idf.append({ 'widgetType':StringSelectorGUI,
                         'parent':'refgroup',
                         'name':'srefNodes',
                         #'defaultValue':self.vf.Mols[0].name+", , , ",
                         'tooltip':'Please select the reference nodes set. By default the ref nodes will be the first molecule loaded in the viewer',
                         'wcfg':{ 'molSet': self.vf.Mols,
                                  'vf': self.vf,
                                  'all':1,
                                  'crColor':(1.,0.,0.),
                                  'forceEmpty':1,
                                  },
                         'gridcfg':{'sticky':'we' }})

            idf.append({ 'widgetType':StringSelectorGUI,
                         'parent':'mobgroup',
                         #'defaultValue':self.vf.Mols[1].name+", , , ",
                         'tooltip':'Please select the mobile nodes set. By default the mobile nodes will be the second molecule loaded in the viewer',
                         'name':'smobNodes',
                         'wcfg':{ 'molSet': self.vf.Mols,
                                  'vf': self.vf,
                                  'all':1,
                                  'crColor':(0.,0.,1.),'forceEmpty':1,
                                  },
                         'gridcfg':{'row':-1, 'sticky':'we' }})
            return idf

SuperimposeAtomsCommandGUI = CommandGUI()
## SuperimposeAtomsGUICommandGUI.addMenuCommand('menuRoot', 'Compute',
##                                              'superimpose Atom Pairs',
##                                              cascadeName = "Superimpose")
SuperimposeAtomsCommandGUI.addMenuCommand('menuRoot', 'Compute',
                                             'Superimpose Atom Pairs')


commandList = [
    {'name':'superimposeAtoms', 'cmd':SuperimposeAtomsCommand(),
     'gui':None},
##     {'name':'superimposeAtomsGC2', 'cmd':SuperimposeAtomsGUICommand(),
##      'gui':SuperimposeAtomsCommandGUI},
    {'name':'superimposeGUI', 'cmd':SuperimposeAtomsGUICommand(),
     'gui':SuperimposeAtomsCommandGUI},
    
    {'name':'superimpose', 'cmd':SuperimposeCommand(),
     'gui':None}, 

    {'name':'transformAtoms', 'cmd':TransformAtomsCommand(),
     'gui':None},
    {'name':'freezeAtoms', 'cmd':FreezeAtomsCommand(),
     'gui':None},

    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

