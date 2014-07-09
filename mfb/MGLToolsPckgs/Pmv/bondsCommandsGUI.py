# $Header: /opt/cvs/python/packages/share1.5/Pmv/bondsCommandsGUI.py,v 1.3 2009/08/13 20:21:23 sargis Exp $
from ViewerFramework.VFCommand import CommandGUI, CommandProxy

class BuildBondsByDistanceProxy(CommandProxy):
    def __init__(self, vf, gui):
        CommandProxy.__init__(self, vf, gui)
        from Pmv.bondsCommands import BuildBondsByDistance
        command = BuildBondsByDistance()
        self.vf.addCommand(command, 'buildBondsByDistance', self.gui)
                
BuildBondsByDistanceGUI = CommandGUI()
BuildBondsByDistanceGUI.addMenuCommand('menuRoot', 'Edit',
                   'Build By Distance', cascadeName='Bonds')

class AddBondsGUICommandProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.bondsCommands import AddBondsGUICommand
            command = AddBondsGUICommand()
            loaded = self.vf.addCommand(command, 'addBondsGC', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)            
AddBondsGUICommandGUI=CommandGUI()
AddBondsGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 'Add',
    cascadeName='Bonds')

class RemoveBondsGUICommandProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.bondsCommands import RemoveBondsGUICommand
            command = RemoveBondsGUICommand()
            loaded = self.vf.addCommand(command, 'removeBondsGC', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)            
            
RemoveBondsGUICommandGUI=CommandGUI()
RemoveBondsGUICommandGUI.addMenuCommand('menuRoot', 'Edit', 
        'Remove Bonds', cascadeName='Bonds')

def initGUI(viewer):
    viewer.addCommandProxy(BuildBondsByDistanceProxy(viewer, BuildBondsByDistanceGUI))
    viewer.addCommandProxy(AddBondsGUICommandProxy(viewer, AddBondsGUICommandGUI))
    viewer.addCommandProxy(RemoveBondsGUICommandProxy(viewer, RemoveBondsGUICommandGUI))
