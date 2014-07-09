## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Nov 2001 Authors: Michel Sanner, Daniel Stoffler
#
#    sanner@scripps.edu
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler and TSRI
#
#########################################################################

import os
import warnings

from NetworkEditor.items import NetworkNode
from Vision import UserLibBuild

from MolKit.molecule import MoleculeSet
from MolKit.tree import TreeNodeSet
from ViewerFramework.VFCommand import Command
from Pmv.moleculeViewer import MoleculeViewer
from mglutil.util.relpath import relpath
from Vision.StandardNodes import RunFunction
from ViewerFramework.VF import LogEvent

def importMolKitLib(net):
    try:
        from MolKit.VisionInterface.MolKitNodes import molkitlib
        net.editor.addLibraryInstance(
            molkitlib, 'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
    except:
        warnings.warn(
            'Warning! Could not import molkitlib from MolKit.VisionInterface')


def importSymLib(net):
    try:
        from symserv.VisionInterface.SymservNodes import symlib
        net.editor.addLibraryInstance(
            symlib, 'symserv.VisionInterface.SymservNodes', 'symlib')
    except:
        warnings.warn(
            'Warning! Could not import molitlib from symserv.VisionInterface.SymservNodes.py')


def importVizLib(net):
    try:
        from DejaVu.VisionInterface.DejaVuNodes import vizlib
        net.editor.addLibraryInstance(
            vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
    except:
        warnings.warn(
            'Warning! Could not import vizlib from DejaVu/VisionInterface')


def importVolLib(net):
    try:
        from Volume.VisionInterface.VolumeNodes import vollib
        net.editor.addLibraryInstance(
            vollib, 'Volume.VisionInterface.VolumeNodes', 'vollib')
    except:
        warnings.warn(
            'Warning! Could not import vollib from Volume/VisionInterface')
            

class PmvLogEvents(NetworkNode):
    """
    captures Pmv log events and outputs the log string
    """
    def __init__(self, name='log events', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype='PmvInstance', name='pmv')

	self.outputPortsDescr.append(datatype='string', name='log')

        code = """def doit(self, pmv):
    if pmv and not self.hasRun:
        pmv.registerListener(LogEvent, self.handleLogEvent)
        self.hasRun = True
"""
        self.setFunction(code)
        self.hasRun = False
        
    def handleLogEvent(self, event):
        self.outputData(log= event.logstr)
        self.scheduleChildren()

from DejaVu.VisionInterface.DejaVuNodes import Viewer
class PmvViewer(Viewer):

    def beforeAddingToNetwork(self, net):
        Viewer.beforeAddingToNetwork(self, net)
        # loading library vizlib
        importVizLib(net)


    #def deleteGeometries(self, connection):
    #    pass


    def beforeRemovingFromNetwork(self):
        self.vi.RemovePickingCallback(self.handlePick)
        Viewer.beforeRemovingFromNetwork(self)
        pass



class PmvNode(NetworkNode):
    """
    Node representing Pmv in a Vision network. Provides access to commands and molecules

    Input Ports:
        cmd: name of the Pmv command to be output on the PmvCmd output port
        molecules: molecule(s) name. Wild cards such as * and . can be used.
                   for instance:
                     'abc*' will select all molecule whose name starts with
                     the string 'abc' followed by any number of any characters
                     '1AY3_model[1-5]' selects 1AY3_model1 through 1AY3_model5

    OutPut Ports:
        PmvInstance:  a handle to the Pmv application
        PmvCommand: a Pmv command object that can be turned into a Vision
                    node using the Run Command node.
        molecules: a single molecule or a moleculeSet
        selection: Pmv's current selection
    """
    def __init__(self, vf=None, name='PMV', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        #self.readOnly = 1

        self.vf = vf

        self.widgetDescr['cmdName'] = {
            'class': 'NEComboBox', 'master':'node',
            'choices':[''],
            'autoList':True, # only save the current selected choice
            'entryfield_entry_width':14,
            'labelCfg':{'text':'cmd:'},
            }

        self.widgetDescr['molecules'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':[''],
            'autoList':True,
            'entryfield_entry_width':16,
            'labelCfg':{'text':'molecules:'},
            }

        self.inputPortsDescr.append(datatype='string', required=False, name='cmdName')
        self.inputPortsDescr.append(datatype='string', name='molecules')

        self.outputPortsDescr.append(datatype='PmvInstance', name='PMV')
        self.outputPortsDescr.append(datatype='PmvCmd', name='cmd')
        self.outputPortsDescr.append(datatype='MoleculeSet', name='molecules')
        self.outputPortsDescr.append(datatype='TreeNodeSet', name='selection')

        code = """def doit(self, cmdName, molecules):
    allCommandNames = self.vf.commands.keys()
    allCommandNames.sort()
    self.inputPortByName['cmdName'].widget.configure(choices=allCommandNames)
    if cmdName and cmdName in allCommandNames:
        obj = self.vf.commands[cmdName]
        if obj:
            self.outputData(cmd=obj )

    allMoleculeNames = map(lambda x: x.name, self.vf.Mols)
    w = self.inputPortByName['molecules'].widget
    if w:
        w.configure(choices=allMoleculeNames)

    obj = self.vf.Mols.get(molecules)
    if obj:
        self.outputData(molecules=obj)
    else:
        w.widget.setentry('')
        self.outputData(molecules=None)
        
##     if molecule not in allMoleculeNames:
##         w.widget.setentry('')
##         self.outputData(molecule=None)
##     else:
##         obj = self.vf.Mols.get(molecule)
##         if obj:
##             self.outputData(molecule=obj)

    if hasattr(self.vf, 'select'):
        # output PMV's current selection
        self.outputData(selection=self.vf.getSelection())

    self.outputData(PMV=self.vf)
"""
        if code:
            self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        # loading library molkitlib
        importMolKitLib(net)


    def afterAddingToNetwork(self):
        NetworkNode.afterAddingToNetwork(self)
        # run this node so the value is output
        self.run(force=1)


class PmvVolume(NetworkNode):

    def beforeAddingToNetwork(self, net):
        NetworkNode.beforeAddingToNetwork(self, net)
        # loading library vizlib
        importVolLib(net)


    def __init__(self,  grid=None, name='volume', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        #self.readOnly = 1

        self.grid = grid

	code = """def doit(self):
    self.outputData(grid=self.grid)
"""
        if code:
            self.setFunction(code)

        self.outputPortsDescr.append(datatype='Grid3D', name='grid')


class PmvMolecule(NetworkNode):


    def __init__(self, molecule=None, name='Molecule', **kw):
        self.mol = molecule
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        code = """def doit(self):
    self.outputData(Molecule=self.mol)
"""
        if code: self.setFunction(code)
        self.outputPortsDescr.append(datatype='Molecule', name='Molecule')


    def beforeAddingToNetwork(self, net):
        # loading library molkitlib
        importMolKitLib(net)


    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):

        """subclass baseclass method to add lines to load the molecule in
        Pmv if it is not loaded yet"""

        lines = []
        if self.network.filename is not None:
            lNetworkDir = os.path.dirname(os.path.abspath(self.network.filename))
            lFileName = relpath(lNetworkDir, os.path.abspath(self.mol.parser.filename))
        elif hasattr(self.network, 'macroNode') \
          and self.network.macroNode.network.filename is not None:
            lNetworkDir = os.path.dirname(os.path.abspath(self.network.macroNode.network.filename))
            lFileName = relpath(lNetworkDir, os.path.abspath(self.mol.parser.filename))
        else:
            lFileName = self.mol.parser.filename

        # we save the name of the file in a path relatives to the network
        s00 = 'import os\n'
        s01 = 'from mglutil.util.relpath import rel2abs\n'
        lFileNameUnix = lFileName.replace('\\', '/')
        s02 = "lRelFileName = '%s'\n"%lFileNameUnix
        # we prepare the readding with an absolut path
        s03 = 'lNetworkDir = os.path.dirname(os.path.abspath(%s.filename))\n'%networkName
        s04 = 'lAbsFileName = rel2abs(lRelFileName, lNetworkDir)\n'
        
        s1 = 'mol = %s.editor.vf.loadMoleculeIfNeeded(lAbsFileName)\n'%networkName
        s2 = 'assert mol\n'
        lines.append(indent+s00)
        lines.append(indent+s01)
        lines.append(indent+s02)
        lines.append(indent+s03)
        lines.append(indent+s04)
        lines.append(indent+s1)
        lines.append(indent+s2)
        lines.extend(NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent, ignoreOriginal) )
        return lines



class PmvSetNode(NetworkNode):
    """Handle to a Pmv Set.
Output: MolKit TreeNodeSet containing a set of either molecules, chains,
        residues, or atoms that exists in Pmv"""

    def __init__(self, set=None, selString=None, name='Pmv Set', **kw):
        self.set = set
        self.selString = selString
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.outputPortsDescr.append(datatype='Molecule', name='PmvSet')
        self.outputPortsDescr.append(datatype='string', name='selection')

	code = """def doit(self):
    self.outputData(PmvSet=self.set, selection=self.selString)\n"""

        if code: self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        # loading library molkitlib
        importMolKitLib(net)


    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):

        """subclass baseclass method to add lines to load the molecule in
        Pmv if it is not loaded yet"""

        if self.network.filename is not None:
            lNetworkDir = os.path.dirname(os.path.abspath(self.network.filename))
        elif hasattr(self.network, 'macroNode') \
          and self.network.macroNode.network.filename is not None:
            lNetworkDir = os.path.dirname(os.path.abspath(self.network.macroNode.network.filename))
        else:
            lNetworkDir = None
            assert False, "my guess is we don't go here"

        lines = []
        molecules = []
        for mol in self.set.top.uniq().data:
            # we save the name of the file in a path relatives to the network
            if lNetworkDir is not None:
                lFileName = relpath(lNetworkDir, os.path.abspath(mol.parser.filename))
            else:
                lFileName = mol.parser.filename
            molecules.append(lFileName)

        # we prepare the readding with an absolut path
        s0 = 'import os\n'
        s1 = 'from mglutil.util.relpath import rel2abs\n'
        s2 = 'lNetworkDir = os.path.dirname(os.path.abspath(%s.filename))\n'%networkName
        s3 = 'mols = %s\n'%molecules
        s4 = 'for m in mols:\n'
        s5 = '    lAbsFileName = rel2abs(m, lNetworkDir)\n'
        s6 = '    mol = %s.editor.vf.loadMoleculeIfNeeded(lAbsFileName)\n'%networkName
        s7 = '    assert mol\n'
        s8 = 'selString = "%s"\n'%self.selString
        s9 = '%s.editor.vf.loadModule("selectionCommands")\n'%networkName
        s10 = '%s.editor.vf.createSetIfNeeded(selString, "%s")\n'%(networkName, self.name)
        s11 = 'from Pmv.selectionCommands import sets__\n'
        lines.append(indent+s0)
        lines.append(indent+s1)
        lines.append(indent+s2)
        lines.append(indent+s3)
        lines.append(indent+s4)
        lines.append(indent+s5)
        lines.append(indent+s6)
        lines.append(indent+s7)
        lines.append(indent+s8)
        lines.append(indent+s9)
        lines.append(indent+s10)
        lines.append(indent+s11)

        lines.extend(NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent, ignoreOriginal) )
        return lines

 
class PmvChooseCommand(NetworkNode):

    def __init__(self, name='cmd chooser', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['cmdName'] = {
            'class': 'NEComboBox', 'master':'node',
            'choices':[''],
            'autoList':True, # only save the current selected choice
            'entryfield_entry_width':14,
            'labelCfg':{'text':'cmd:'},
            }

        self.inputPortsDescr.append(datatype='PmvInstance', name='viewer')
        self.inputPortsDescr.append(datatype='string', required=False, name='cmdName')
	self.outputPortsDescr.append(datatype='PmvCmd', name='cmd')

        code = """def doit(self, viewer, cmdName):
    if viewer:
        allNames = viewer.commands.keys()
        allNames.sort()
        self.inputPortByName['cmdName'].widget.configure(choices=allNames)
    if cmdName and cmdName in allNames:
        obj = viewer.commands[cmdName]
        if obj:
            self.outputData(cmd=obj )\n"""

        self.setFunction(code)


class PmvCommand(NetworkNode):

    def __init__(self, pmvCmd, name='pmv cmd', **kw):
        self.cmd = pmvCmd
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['log'] = {
            'class':'NECheckButton',
            'initialValue':1,
            'labelCfg':{'text':'log'},
            }
            
        self.widgetDescr['redraw'] = {
            'class':NECheckButton,
            'initialValue':1,
            'labelCfg':{'text':'redraw'},
            }
            
        self.widgetDescr['topCommand'] = {
            'class':NECheckButton,
            'initialValue':1,
            'labelCfg':{'text':'topCommand'},
            }

        self.widgetDescr['setupUndo'] = {
            'class':'NECheckButton',
            'initialValue':0,
            'labelCfg':{'text':'setupUndo'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='int', name='log')
        ip.append(datatype='int', name='redraw')
        ip.append(datatype='int', name='topCommand')
        ip.append(datatype='int', name='setupUndo')


class PmvRunCommand(RunFunction):

    def Run_Command():
        pass
    passFunc = Run_Command


    def __init__(self, command=None, posArgsNames=[], namedArgs={},
                 name='run command', **kw):

        lNamedArgs = {'log':True, 'redraw':True, 'topCommand':True, 'setupUndo':True}
        if len(namedArgs) > 0:
            lNamedArgs.update(lNamedArgs)
        elif kw.has_key('namedArgs') is True:
            kw['namedArgs'].update(lNamedArgs)
        else:
            namedArgs = lNamedArgs

        # we do this to pass the variables into kw
        if command is not None or kw.has_key('functionOrString') is False:
            kw['functionOrString'] = command
        elif kw.has_key('functionOrString') is True:
            command = kw['functionOrString']
        if len(posArgsNames)>0 or kw.has_key('posArgsNames') is False:
            kw['posArgsNames'] = posArgsNames
        elif kw.has_key('posArgsNames') is True:
            posArgsNames = kw['posArgsNames']
        if len(namedArgs)>0 or kw.has_key('namedArgs') is False:
            kw['namedArgs'] = namedArgs
        elif kw.has_key('namedArgs') is True:
            namedArgs = kw['namedArgs']
        if name is not None or kw.has_key('name') is False:
            kw['name'] = name
        elif kw.has_key('name') is True:
            name = kw['name']

        apply( RunFunction.__init__, (self,), kw )
        self.widgetDescr['importString']['master'] ='ParamPanel'


    def afterAddingToNetwork(self):
        RunFunction.afterAddingToNetwork(self)
        self.inputPortByName['command'].unbindWidget()



try:
    from mslib import MSMS
    msmsFound=1
except: #ImportError
    msmsFound=0
    warnings.warn("could not find MSMS library")

class GetMSMSGeom(NetworkNode):
    """Get a handle to an MSMS surface geometry for a molecule loaded in PMV

Input:
    molecule: the molecule for which we want a handle to a surface
    surfaceName: the name of the surface we want
Output:
    msmsGeom: an IndexedPolygons geometry corresponding to an MSMS surface
              calculated in PMV
"""
    def __init__(self, constrkw = {},  name='Get MSMS Geom', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['surfaceName'] = {
            'initialValue': 'MSMS-MOL', 'fixedChoices': 0,
            'choices': ['MSMS-MOL'], 'labelGridCfg': {},
            'master': 'node', 'widgetGridCfg': {},
            'labelCfg': {'text': 'surface:'}, 'class': 'NEComboBox',
            }
        
        self.inputPortsDescr.append(name='molecule', datatype='Molecule')
        self.inputPortsDescr.append(name='surfaceName', datatype='string', defaultValue='MSMS-MOL')

        self.outputPortsDescr.append(name='msmsGeom', datatype='geom')

        code = """def doit(self, molecule, surfaceName):
    if molecule:
        allNames = molecule.geomContainer.msms.keys()
        self.inputPorts[1].widget.configure(choices=allNames)
    srf = molecule.geomContainer.geoms.get(surfaceName, None)
    self.outputData(msmsGeom=srf)
"""
        self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        # import vizlib
        importVizLib(net)
        # import molkitlib
        importMolKitLib(net)


class PmvSetCPKRadii(NetworkNode):
    """Set the radius of the atoms currently selected in PMV"""
    
    def __init__(self, name='Set radius', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype='PmvInstance',
                       balloon='Pmv instance holding the selection of atoms ',
                                    name='Pmv')
        self.inputPortsDescr.append(datatype='float', name='radius')

        code = """def doit(self, Pmv, radius):
    sel = Pmv.getSelection()
    from MolKit.molecule import Atom
    atsel = sel.findType(Atom)
    for a in atsel:
        a.radius = radius
    Pmv.displayCPK(atsel)\n"""

        self.setFunction(code)

import numpy.oldnumeric as Numeric

class PmvSetInstanceMatrices(NetworkNode):
    """Apply (4x4) transformation matrices to all geometries associated with
a given molecule currently displayed in PMV.
Input:
      molecule:    a PMV molecule
      matrices: (4x4) transformation matrices
"""
    
    def __init__(self, name='Set Instances', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype='Molecule', name='molecule')
        self.inputPortsDescr.append(datatype='instancemat(0)',
                                    name='matrices', required=False,
                                    defaultValue=[Numeric.identity(4,'f')])

        code = """def doit(self, molecule, matrices):
    if molecule:
        assert hasattr(molecule, 'geomContainer')   

        geom = molecule.geomContainer.geoms['master']
        geom.Set(instanceMatrices=matrices)
        
        geom.viewer.Redraw()\n"""
        
        self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        # loading library molkitlib
        importMolKitLib(net)
        # loading library symlib
        importSymLib(net)


class PmvGetSelection(NetworkNode):
    """Returns the current selection as a TreeNodeSet.
Note: when the selection changes in Pmv, this node has to re-run by the user.

Input:
        Pmv:   an instance of Pmv

Output:
        nodes: the current Pmv selection
"""
    
    def __init__(self, name='Pmv Selection', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype='PmvInstance',
                      balloon='Pmv instance holding the selection of atoms',
                                    name='Pmv')

        self.outputPortsDescr.append(datatype='TreeNodeSet', name='nodes')

        code = """def doit(self, Pmv):
        if not Pmv:
            return

        # selection command loaded?
        if not hasattr(Pmv, 'select'):
            return

        # output PMV's current selection

        self.outputData(nodes=Pmv.getSelection())
"""
        
        self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        # loading library molkitlib
        importMolKitLib(net)


class PmvMoleculeChooser(NetworkNode):
    """Provides a list of molecules currently loaded in PMV in a ComboBox
and lets the user select one.

Input:
        Pmv:   an instance of Pmv

Output:
        nodes: Molecule
"""
    
    def __init__(self, name='Pmv Mol. Chooser', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['molecule'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':[''],
            'autoList':True,
            'entryfield_entry_width':16,
            'labelCfg':{'text':'molecules:'},
            }
        
        self.inputPortsDescr.append(
                      datatype='PmvInstance',
                      balloon='Pmv instance holding the selection of atoms',
                      name='Pmv')
        self.inputPortsDescr.append(datatype='string', name='molecule')
        self.outputPortsDescr.append(datatype='Molecule', name='molecule')

        code = """def doit(self, Pmv, molecule):
    assert Pmv is not None

    allNames = map(lambda x: x.name, Pmv.Mols)
    w = self.inputPortByName['molecule'].widget
    if w:
        w.configure(choices=allNames)
    if molecule not in allNames:
        w.widget.setentry('')
        self.outputData(molecule=None)
    else:
        obj = Pmv.Mols.get(molecule)
        if obj:
            self.outputData(molecule=obj)
"""
        
        self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        # loading library molkitlib
        importMolKitLib(net)


from Vision.VPE import NodeLibrary
pmvlib = NodeLibrary('Pmv', '#7A7AFF')

pmvlib.addNode(PmvChooseCommand, 'Choose Cmd', 'Filter',)

pmvlib.addNode(PmvSetCPKRadii, 'Set CPK radii', 'Mapper',)
pmvlib.addNode(PmvSetInstanceMatrices, 'Set Instances', 'Mapper',)

pmvlib.addNode(PmvRunCommand, 'Run Command', 'Output',)
pmvlib.addNode(PmvGetSelection, 'Get Selection', 'Input',)
pmvlib.addNode(PmvMoleculeChooser, 'Choose Molecule', 'Input',)
pmvlib.addNode(PmvLogEvents, 'Pmv Log String', 'Output',)

if msmsFound==1:
    pmvlib.addNode(GetMSMSGeom, 'Get MSMS Geom', 'Filter')



UserLibBuild.addTypes(pmvlib, 'Pmv.VisionInterface.PmvTypes')

try:
    UserLibBuild.addTypes(pmvlib, 'DejaVu.VisionInterface.DejaVuTypes')
except:
    pass

try:
    UserLibBuild.addTypes(pmvlib, 'MolKit.VisionInterface.MolKitTypes')
except:
    pass
