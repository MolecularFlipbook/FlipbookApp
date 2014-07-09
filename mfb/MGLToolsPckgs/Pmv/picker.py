#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/picker.py,v 1.4 2004/12/17 19:21:23 sanner Exp $
#
# $Id: picker.py,v 1.4 2004/12/17 19:21:23 sanner Exp $
#

##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from ViewerFramework.picker import Picker
import Tkinter, Pmw
from MolKit.molecule import AtomSet, BondSet

class AtomPicker(Picker):
    """
This objects can be used to prompt the user for selecting a set of atoms
or starting a picker that will call a callback function after a user-
defined number of atoms have been selected
"""

    def removeAlreadySelected(self, objects):
        """remove for objects the ones already in self.objects"""
        return objects - self.objects


    def getObjects(self, pick):
        """to be implemented by sub-class"""
        atoms = self.vf.findPickedAtoms(pick)
        return atoms

    def clear(self):
        """clear AtomSet of selected objects"""
        self.objects = AtomSet([])


    def updateGUI(self, atom):
        name = atom.full_name()
        self.ifd.entryByName['Atom']['widget'].setentry(name)


    def buildInputFormDescr(self):
        """to be implemented by sub-class"""
        
	ifd=InputFormDescr()
        ifd.title = "atom picker"
        ifd.append({'widgetType':Tkinter.Label,
                         'name':'event',
                         'wcfg':{'text':'last atom: '},
                         'gridcfg':{'sticky':Tkinter.W} })
        ifd.append({'widgetType':Pmw.EntryField,
                         'name':'Atom',
                         'wcfg':{'labelpos':'w',
                                 'label_text':'Atom: ', 'validate':None},
                         'gridcfg':{'sticky':'we'}})
        if self.numberOfObjects==None:
            ifd.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Done'},
                             'command': self.stop})

        return ifd


class BondPicker(Picker):


    def go(self, modal=0, level='parts'):
        Picker.go( self, modal, level)

        
    def removeAlreadySelected(self, objects):
        """remove for objects the ones already in self.objects"""
        return objects - self.objects


    def clear(self):
        """clear BondSet of selected objects"""
        self.objects = BondSet([])

        
    def getObjects(self, pick):
        """to be implemented by sub-class"""
        bonds = self.vf.findPickedBonds(pick)
        return bonds


    def updateGUI(self, bond):
        name = bond.atom1.full_name()
        self.ifd.entryByName['Atom1']['widget'].setentry(name)
        name = bond.atom2.full_name()
        self.ifd.entryByName['Atom2']['widget'].setentry(name)
        name = str(bond.bondOrder)
        self.ifd.entryByName['BondOrder']['widget'].setentry(name)


    def buildInputFormDescr(self):
        """to be implemented by sub-class"""

	ifd=InputFormDescr()
        ifd.title = "bond picker"
        ifd.append({'widgetType':Tkinter.Label,
                    'name':'event',
                    'wcfg':{'text':'event: '+self.event},
                    'gridcfg':{'sticky':Tkinter.W} })
        
        ifd.append({'widgetType':Pmw.EntryField,
                    'name':'Atom1',
                    'wcfg':{'labelpos':'w',
                            'label_text':'Atom 1: ',
                            'validate':None},
                    'gridcfg':{'sticky':'we'}})
        ifd.append({'widgetType':Pmw.EntryField,
                    'name':'Atom2',
                    'wcfg':{'labelpos':'w',
                            'label_text':'Atom 2: ',
                            'validate':None},
                    'gridcfg':{'sticky':'we'}})
        ifd.append({'widgetType':Pmw.EntryField,
                    'name':'BondOrder',
                    'wcfg':{'labelpos':'w',
                            'label_text':'BondOrder: ',
                            'validate':None},
                    'gridcfg':{'sticky':'we'}})

        if self.numberOfObjects==None:
            ifd.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Done'},
                             'command': self.stop})

        return ifd


from DejaVu.IndexedPolygons import IndexedPolygons

class MsmsPicker(Picker):

    def getObjects(self, pick):
        """to be implemented by sub-class"""
        result = []
        for o in pick.hits.keys():
            if isinstance(o, IndexedPolygons):
                if hasattr(o, 'mol'):
                    if hasattr(o,'userName'):
                        result.append(o)
        return result

    
    def updateGUI(self, geom):
        name = geom.userName
        self.ifd.entryByName['Surface']['widget'].setentry(name)


    def buildInputFormDescr(self):
        """to be implemented by sub-class"""
        
	ifd=InputFormDescr()
        ifd.title = "MSMSsel picker"
        ifd.append({'widgetType':Tkinter.Label,
                         'name':'event',
                         'wcfg':{'text':'event: '+self.event},
                         'gridcfg':{'sticky':Tkinter.W} })
        ifd.append({'widgetType':Pmw.EntryField,
                         'name':'Surface',
                         'wcfg':{'labelpos':'w',
                                 'label_text':'Surface name: ',
                                 'validate':None},
                         'gridcfg':{'sticky':'we'}})
        if self.numberOfObjects==None:
            ifd.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Done'},
                             'command': self.stop})
        return ifd


class NewMsmsPicker(MsmsPicker):

    def getObjects(self, pick):
        """to be implemented by sub-class"""
        for o in pick.hits.keys():
            if o:
                if isinstance(o, IndexedPolygons):
                    if hasattr(o, 'mol'):
                        if hasattr(o,'userName'):
                            return o
                        if hasattr(o, 'name'):
                            if o.name=='msms':
                                result.append(o)
            return result
        else:
            if self.ifd.entryByName.has_key('AllObjects'):
                widget = self.ifd.entryByName['AllObjects']['widget']
                if len(widget.lb.curselection()):
                    return widget.entries(int(widget.lb.curselection()[0]))
            return None


    def allChoices(self):
        choices = []
        for mol in self.vf.Mols:
            geoms = mol.geomContainer.geoms
            for geomname in geoms.keys():
                if hasattr(geoms[geomname], 'userName') or \
                   (geomname=='msms' and geoms[geomname].vertexSet):
                    choices.append(mol.geomContainer.geoms[geomname])
        return choices


    def updateGUI(self, geom):
        if geom.name=='msms':
            name = 'msms'
        else:
            name = geom.userName
        self.ifd.entryByName['Surface']['widget'].setentry(name)


    def buildInputFormDescr(self):
        """to be implemented by sub-class"""
        
	ifd=InputFormDescr()
        ifd.title = "MSMSsel picker"
        ifd.append({'widgetType':Tkinter.Label,
                         'name':'event',
                         'wcfg':{'text':'event: '+self.event},
                         'gridcfg':{'sticky':Tkinter.W} })
        ifd.append({'widgetType':Pmw.EntryField,
                         'name':'Surface',
                         'wcfg':{'labelpos':'w',
                                 'label_text':'Surface name: ',
                                 'validate':None},
                         'gridcfg':{'sticky':'we'}})
        ifd.append({'widgetType':Tkinter.Button,
                         'name':'Cancel',
                         'wcfg':{'text':'Cancel',
                                'command':self.Cancel
                                }
                         })

        if self.numberOfObjects==None:
            ifd.append({'widgetType':Tkinter.Button,
                             'wcfg':{'text':'Done'},
                             'command': self.stop})
        return ifd

    def Cancel(self, event=None):
        self.form.destroy()






