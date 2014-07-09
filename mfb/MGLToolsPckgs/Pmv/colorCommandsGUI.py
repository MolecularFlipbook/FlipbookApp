# $Header: /opt/cvs/python/packages/share1.5/Pmv/colorCommandsGUI.py,v 1.3 2010/02/05 18:03:45 sargis Exp $
# Author: Sargis Dallakyan  TSRI 2009

from ViewerFramework.VFCommand import CommandGUI, CommandProxy

class ColorCommandProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorCommand
            command = ColorCommand()
            loaded = self.vf.addCommand(command, 'color', self.gui)
            if loaded:
                command = loaded            
            self.command = command
            self.command.guiCallback(**kw)    
ColorGUI = CommandGUI()
ColorGUI.addMenuCommand('menuRoot', 'Color', 'Choose Color')


class ColorByAtomTypeProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByAtomType
            command = ColorByAtomType()
            loaded = self.vf.addCommand(command, 'colorByAtomType', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
ColorByAtomTypeGUI = CommandGUI()
ColorByAtomTypeGUI.addMenuCommand('menuRoot', 'Color', 'by Atom Type')

class ColorByDGProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByDG
            command = ColorByDG()
            loaded = self.vf.addCommand(command, 'colorAtomsUsingDG', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
ColorByDGGUI= CommandGUI()
ColorByDGGUI.addMenuCommand('menuRoot', 'Color', 'by DG colors')


class ColorByResidueTypeProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByResidueType
            command = ColorByResidueType()
            loaded = self.vf.addCommand(command, 'colorByResidueType', self.gui)
            if loaded:
                command = loaded            
            self.command = command
            self.command.guiCallback(**kw)    
ColorByResidueTypeGUI = CommandGUI()
ColorByResidueTypeGUI.addMenuCommand('menuRoot', 'Color', 'RasmolAmino',
                     cascadeName = 'by Residue Type')

class ColorShapelyProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorShapelyColorCommand
            command = ColorShapely()
            loaded = self.vf.addCommand(command, 'colorResiduesUsingShapely', self.gui)
            if loaded:
                command = loaded            
            self.command = command
            self.command.guiCallback(**kw)    
ColorShapelyGUI = CommandGUI()
ColorShapelyGUI.addMenuCommand('menuRoot', 'Color', 'Shapely',
                     cascadeName = 'by Residue Type')


class ColorByChainProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByChain
            command = ColorByChain()
            loaded = self.vf.addCommand(command, 'colorByChains', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
            
ColorByChainGUI = CommandGUI()
ColorByChainGUI.addMenuCommand('menuRoot', 'Color', 'by Chain')

class ColorByMoleculeProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByMolecule
            command = ColorByMolecule()
            loaded= self.vf.addCommand(command, 'colorByMolecules', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
ColorByMoleculeGUI = CommandGUI()
ColorByMoleculeGUI.addMenuCommand('menuRoot', 'Color', 'by Molecules')


class ColorByInstanceProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByInstance
            command = ColorByInstance()
            loaded = self.vf.addCommand(command, 'colorByInstance', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
ColorByInstanceGUI = CommandGUI()
ColorByInstanceGUI.addMenuCommand('menuRoot', 'Color', 'by Instance')

class ColorByPropertiesProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByProperties
            command = ColorByProperties()
            loaded = self.vf.addCommand(command, 'colorByProperty', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
ColorByPropertiesGUI = CommandGUI()
ColorByPropertiesGUI.addMenuCommand('menuRoot', 'Color', 'by Properties')


class ColorByExpressionProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.colorCommands import ColorByExpression
            command = ColorByExpression()
            loaded = self.vf.addCommand(command, 'colorByExpression', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)    
            
ColorByExpressionGUI = CommandGUI()
ColorByExpressionGUI.addMenuCommand('menuRoot', 'Color', 'by Expression')

def initGUI(viewer):
    viewer.addCommandProxy(ColorCommandProxy(viewer, ColorGUI))
    viewer.addCommandProxy(ColorByAtomTypeProxy(viewer, ColorByAtomTypeGUI))
    viewer.addCommandProxy(ColorByResidueTypeProxy(viewer, ColorByResidueTypeGUI))
    viewer.addCommandProxy(ColorByDGProxy(viewer, ColorByDGGUI))
    viewer.addCommandProxy(ColorShapelyProxy(viewer, ColorShapelyGUI))
    viewer.addCommandProxy(ColorByChainProxy(viewer, ColorByChainGUI))
    viewer.addCommandProxy(ColorByMoleculeProxy(viewer, ColorByMoleculeGUI))
    viewer.addCommandProxy(ColorByInstanceProxy(viewer, ColorByInstanceGUI))
    viewer.addCommandProxy(ColorByPropertiesProxy(viewer, ColorByPropertiesGUI))
    #viewer.addCommandProxy(ColorByExpressionProxy(viewer, ColorByExpressionGUI))    
