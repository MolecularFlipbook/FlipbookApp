# $Header: /opt/cvs/python/packages/share1.5/Pmv/fileCommandsGUI.py,v 1.9.2.1 2011/04/08 21:17:29 sargis Exp $
from ViewerFramework.VFCommand import CommandGUI, CommandProxy

class PDBWriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import PDBWriter
            command = PDBWriter()
            loaded = self.vf.addCommand(command, 'writePDB', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)            
PDBWriterGUI = CommandGUI()
PDBWriterGUI.addMenuCommand('menuRoot', 'File', 'Write PDB',
                            cascadeName='Save', index=3, separatorAbove=1)

class PDBQWriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import PDBQWriter
            command = PDBQWriter()
            loaded = self.vf.addCommand(command, 'writePDBQ', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)            
PDBQWriterGUI = CommandGUI()
PDBQWriterGUI.addMenuCommand('menuRoot', 'File', 'Write PDBQ',
                             cascadeName='Save', index=4)

class PDBQSWriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import PDBQSWriter
            command = PDBQSWriter()
            loaded = self.vf.addCommand(command, 'writePDBQ', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)            
PDBQSWriterGUI = CommandGUI()
PDBQSWriterGUI.addMenuCommand('menuRoot', 'File', 'Write PDBQS',
                             cascadeName='Save', index=5)

class PDBQTWriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import PDBQTWriter
            command = PDBQTWriter()
            loaded = self.vf.addCommand(command, 'writePDBQT', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)            
PDBQTWriterGUI = CommandGUI()
PDBQTWriterGUI.addMenuCommand('menuRoot', 'File', 'Write PDBQT',
                             cascadeName='Save', index=6)

class SaveMMCIFProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import SaveMMCIF
            command = SaveMMCIF()
            loaded = self.vf.addCommand(command, 'SaveMMCIF', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)                
SaveMMCIFGUI = CommandGUI()
SaveMMCIFGUI.addMenuCommand('menuRoot', 'File', 'Write MMCIF',
                            cascadeName='Save', index=7)

class PQRWriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import PQRWriter
            command = PQRWriter()
            loaded = self.vf.addCommand(command, 'writePQR', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)                            
PQRWriterGUI = CommandGUI()
PQRWriterGUI.addMenuCommand('menuRoot', 'File', 'Write PQR',
                            cascadeName='Save', index=8)

class MoleculeReaderProxy(CommandProxy):
    def __init__(self, vf, gui):
        from Pmv.fileCommands import MoleculeReader
        command = MoleculeReader()
        vf.addCommand(command, 'readMolecule', gui)
        CommandProxy.__init__(self, vf, gui)
        
MoleculeReaderGUI = CommandGUI()
MoleculeReaderGUI.addMenuCommand('menuRoot', 'File', 'Read Molecule', index = 0)

class fetchCommandProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import fetch
            command = fetch()
            loaded = self.vf.addCommand(command, 'fetch', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)                            
fetchGUI = CommandGUI()
fetchGUI.addMenuCommand('menuRoot', 'File', 'Fetch From Web', index=0,
                        cascadeName='Import')


class VRML2WriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import VRML2Writer
            command = VRML2Writer()
            loaded = self.vf.addCommand(command, 'writeVRML2', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)
VRML2WriterGUI = CommandGUI()
VRML2WriterGUI.addMenuCommand('menuRoot', 'File', 'Write VRML 2.0',
                              cascadeName='Save', cascadeAfter='Read Molecule',
                              separatorAboveCascade=1)

class STLWriterProxy(CommandProxy):
    def guiCallback(self, **kw):
        if self.command:
            self.command.guiCallback(**kw)
        else:
            from Pmv.fileCommands import STLWriter
            command = STLWriter()
            loaded = self.vf.addCommand(command, 'writeSTL', self.gui)
            if loaded:
                command = loaded
            self.command = command
            self.command.guiCallback(**kw)
STLWriterGUI = CommandGUI()
STLWriterGUI.addMenuCommand('menuRoot', 'File', 'Write STL',
                            cascadeName='Save', index=11,separatorBelow=1)

class ReadSourceMoleculeProxy(CommandProxy):
    def __init__(self, vf, gui):
        from Pmv.fileCommands import ReadSourceMolecule
        command =ReadSourceMolecule()
        vf.addCommand(command, 'readSourceMolecule', gui)
        CommandProxy.__init__(self, vf, gui)
                    
ReadSourceMoleculeGUI = CommandGUI()    
ReadSourceMoleculeGUI.addToolBar('Read Molecule or Python Script', icon1='fileopen.gif', 
                             type='ToolBarButton', balloonhelp='Read Molecule or Python Script', index=0)
            
def initGUI(viewer):
    viewer.addCommandProxy(fetchCommandProxy(viewer, fetchGUI))
    viewer.addCommandProxy(PDBWriterProxy(viewer, PDBWriterGUI))
    viewer.addCommandProxy(PDBQWriterProxy(viewer, PDBQWriterGUI))
    viewer.addCommandProxy(PDBQTWriterProxy(viewer, PDBQTWriterGUI))
    viewer.addCommandProxy(PDBQSWriterProxy(viewer, PDBQSWriterGUI))
    viewer.addCommandProxy(SaveMMCIFProxy(viewer, SaveMMCIFGUI))
    viewer.addCommandProxy(PQRWriterProxy(viewer, PQRWriterGUI))
    viewer.addCommandProxy(MoleculeReaderProxy(viewer, MoleculeReaderGUI))
    viewer.addCommandProxy(VRML2WriterProxy(viewer, VRML2WriterGUI))
    viewer.addCommandProxy(STLWriterProxy(viewer, STLWriterGUI))
    viewer.addCommandProxy(ReadSourceMoleculeProxy(viewer, ReadSourceMoleculeGUI))    
    
