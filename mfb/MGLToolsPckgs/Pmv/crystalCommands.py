# $Header: /opt/cvs/python/packages/share1.5/Pmv/crystalCommands.py,v 1.4 2009/05/22 18:40:03 vareille Exp $
#
# $Id: crystalCommands.py,v 1.4 2009/05/22 18:40:03 vareille Exp $
#
"""
Displays Unit Cell and Packing when Crystal Info is available in input cif file.
"""
from symserv.spaceGroups import spaceGroups
import numpy
from mglutil.math.crystal import Crystal
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
import Pmw, Tkinter
import tkMessageBox
from DejaVu.Box import Box
from mglutil.util.callback import CallBackFunction
def instanceMatricesFromGroup(molecule):
    returnMatrices = [numpy.eye(4,4)]
    crystal = Crystal(molecule.cellLength, molecule.cellAngles)
    matrices = spaceGroups[molecule.spaceGroup]
    for matrix in matrices:
        tmpMatix = numpy.eye(4,4) 
        tmpMatix[:3, :3] = matrix[0]
        tmpMatix[:3, 3] = crystal.toCartesian(matrix[1])
        returnMatrices.append(tmpMatix)
    molecule.crystal = crystal
    return returnMatrices
        
class CrystalCommand(MVCommand):
    def guiCallback(self):
        molNames = []
        for mol in self.vf.Mols:
            if hasattr(mol, 'spaceGroup'):
                molNames.append(mol.name)
        if not molNames:
            tkMessageBox.showinfo("Crystal Info is Needed", "No Molecule in the Viewer has Crystal Info.")    
            return
        ifd = InputFormDescr(title='Crystal Info')   
        ifd.append({'name':'moleculeList',
        'widgetType':Pmw.ScrolledListBox,
        'tooltip':'Select a molecule with Crystal Info.',
        'wcfg':{'label_text':'Select Molecule: ',
            'labelpos':'nw',
            'items':molNames,
            'listbox_selectmode':'single',
            'listbox_exportselection':0,
            'usehullsize': 1,
            'hull_width':100,'hull_height':150,
            'listbox_height':5},
        'gridcfg':{'sticky':'nsew', 'row':1, 'column':0}})
        val = self.vf.getUserInput(ifd, modal=1, blocking=1)
        if val:
            molecule = self.vf.getMolFromName(val['moleculeList'][0])
            matrices = instanceMatricesFromGroup(molecule)
            geom = molecule.geomContainer.geoms['master']
            geom.Set(instanceMatrices=matrices)
            if not molecule.geomContainer.geoms.has_key('Unit Cell'):
                fractCoords=((1,1,0),(0,1,0),(0,0,0),(1,0,0),(1,1,1),(0,1,1),
                                                                (0,0,1),(1,0,1))
                coords = []
                coords = molecule.crystal.toCartesian(fractCoords)
                box=Box('Unit Cell', vertices=coords)
                self.vf.GUI.VIEWER.AddObject(box, parent=geom)
                molecule.geomContainer.geoms['Unit Cell'] = box
            ifd = InputFormDescr(title='Crystal Options')
            visible = molecule.geomContainer.geoms['Unit Cell'].visible
            if visible:
                showState = 'active'
            else:
                showState = 'normal'
            ifd.append({'name': 'Show Cell',
            'widgetType':Tkinter.Checkbutton,
            'text': 'Hide Unit Cell',
            'state':showState,
            'gridcfg':{'sticky':Tkinter.W},
            'command': CallBackFunction(self.showUnitCell, molecule)})

            ifd.append({'name': 'Show Packing',
            'widgetType':Tkinter.Checkbutton,
            'text': 'Hide Packing',
            'state':'active',
            'gridcfg':{'sticky':Tkinter.W},
            'command': CallBackFunction(self.showPacking, molecule)})
            
            val = self.vf.getUserInput(ifd, modal=0, blocking=1)
            if not val:
                geom.Set(instanceMatrices=[numpy.eye(4,4)])
                molecule.geomContainer.geoms['Unit Cell'].Set(visible=False)
            
    def showUnitCell(self, molecule):
        visible = not molecule.geomContainer.geoms['Unit Cell'].visible
        molecule.geomContainer.geoms['Unit Cell'].Set(visible=visible)

    def showPacking(self, molecule):
        geom = molecule.geomContainer.geoms['master']
        if len(geom.instanceMatricesFortran) >= 2:
            geom.Set(instanceMatrices=[numpy.eye(4,4)])
        else:
            matrices = instanceMatricesFromGroup(molecule)
            geom.Set(instanceMatrices=matrices)
            
        
        
CrystalCommandGUI = CommandGUI()
CrystalCommandGUI.addMenuCommand('menuRoot', 'Display', 'Crystal')

commandList  = [{'name':'crystalCommand','cmd':CrystalCommand(),'gui':CrystalCommandGUI}]
def initModule(viewer):
    for _dict in commandList:
        viewer.addCommand(_dict['cmd'],_dict['name'],_dict['gui'])