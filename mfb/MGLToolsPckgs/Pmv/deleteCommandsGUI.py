# $Header: /opt/cvs/python/packages/share1.5/Pmv/deleteCommandsGUI.py,v 1.2.4.2 2011/06/06 17:19:58 sanner Exp $
# Author: Sargis Dallakyan  TSRI 2009

from ViewerFramework.VFCommand import CommandGUI, CommandProxy

class DeleteMoleculeProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.deleteCommands import DeleteMolecule
            command = DeleteMolecule()
            loaded = self.vf.addCommand(command, 'deleteMol', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
            
DeleteMoleculeGUI = CommandGUI()
DeleteMoleculeGUI.addMenuCommand('menuRoot', 'Edit', 'Delete Molecule', 
        cascadeName = 'Delete')


class DeleteAllMoleculesProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.deleteCommands import DeleteAllMolecules
            command = DeleteAllMolecules()
            loaded = self.vf.addCommand(command, 'deleteAllMolecules', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
            
DeleteAllMoleculesGUI = CommandGUI()
DeleteAllMoleculesGUI.addMenuCommand('menuRoot', 'Edit', 'Delete All Molecules', 
        cascadeName = 'Delete')


class DeleteCurrentSelectionProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.deleteCommands import DeleteCurrentSelection
            command = DeleteCurrentSelection()
            loaded = self.vf.addCommand(command, 'Delete Selected Atom', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    

DeleteCurrentSelectionGUI = CommandGUI()
DeleteCurrentSelectionGUI.addMenuCommand('menuRoot', 'Edit',
                                         'Delete Selected Atoms',
                                         cascadeName='Delete')


class DeleteHydrogensProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.deleteCommands import DeleteHydrogens
            command = DeleteHydrogens()
            loaded = self.vf.addCommand(command, 'deleteHydrogens', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    

DeleteHydrogensGUI = CommandGUI()
DeleteHydrogensGUI.addMenuCommand('menuRoot', 'Edit', 'Delete Hydrogens',
        cascadeName='Delete')

def initGUI(viewer):
    viewer.addCommandProxy(DeleteMoleculeProxy(viewer, DeleteMoleculeGUI))
    viewer.addCommandProxy(DeleteAllMoleculesProxy(viewer, DeleteAllMoleculesGUI))
    viewer.addCommandProxy(DeleteAtomSetProxy(viewer, DeleteAtomSetGUI))
    viewer.addCommandProxy(DeleteHydrogensProxy(viewer, DeleteHydrogensGUI))
    
