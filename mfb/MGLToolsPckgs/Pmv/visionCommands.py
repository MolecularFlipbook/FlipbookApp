#########################################################################
#
# Date: Aug 2001 Authors: Michel Sanner, Daniel Stoffler
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
# Revision: Guillaume Vareille
#
#########################################################################
#
#$Header: /opt/cvs/python/packages/share1.5/Pmv/visionCommands.py,v 1.56 2009/04/24 20:03:55 vareille Exp $
#
#$Id: visionCommands.py,v 1.56 2009/04/24 20:03:55 vareille Exp $
#
#
import Tkinter
import sys

from mglutil.gui.InputForm.Tk.gui import InputFormDescr, InputForm
from Pmv.mvCommand import MVCommand, MVCommandGUI
from Pmv.VisionInterface.PmvNodes import PmvNode, PmvMolecule, PmvViewer, \
     PmvSetNode
#from Pmv.selectionCommands import sets__
from Vision.VPE import VisualProgramingEnvironment, NodeLibrary
from ViewerFramework.VFCommand import CommandGUI # this adds ok/cancel to form
from mglutil.util.packageFilePath import getResourceFolder 


class VisionCommand(MVCommand):

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.root = None
        self.lib = None # will point to pmvlib
        self.ed = None # VisualProgrammingEnvironment object


    def onExitFromViewer(self):
        if self.ed is None:
            return
        if len(self.ed.networks):
            self.vf.log("##")
            self.vf.log("## Saving Vision networks")
            self.vf.log("##")
            self.vf.log("self.browseCommands('visionCommands', commands=('vision',))")
            # no need to call the vision command because it has ben called
            # and loged int he Pmv session already
            #self.vf.log("self.vision()")
            self.vf.log("from NetworkEditor.net import Network")
            self.vf.log("self.vision.ed.deleteNetwork(self.vision.ed.networks['Network 0'])")
            self.vf.log("pmv = self")
            self.vf.log("self = pmv.vision.ed")

        from NetworkEditor.macros import MacroNetwork
        for netname, net in self.ed.networks.items():
            if isinstance(net, MacroNetwork):
                continue

            # do not create any code if no nodes are present in this net
            if len(net.nodes) == 0:
                continue

            self.vf.log("##")
            self.vf.log("## Networks %s"%netname)
            self.vf.log("##")

            if net._modified:
                self.vf.log("masterNet = Network('%s')"%netname)
                self.vf.log("self.addNetwork(masterNet)")
                self.vf.log("masterNet.buildIcons()")
                self.vf.log("self.setNetwork(masterNet)")
                netsrc = net.getNetworkCreationSourceCode()
                for line in netsrc:
                    self.vf.log(line)
            else:
                if net.filename:
                    self.vf.log("self.loadNetwork('%s')"%net.filename)
                else:
                    print 'WARNING: visionCommand: onExit: network %s has no filename'%netname
            self.vf.log("##")
            self.vf.log("## Networks %s End"%netname)
            self.vf.log("##\n\n")
            self.root.withdraw()

        self.vf.log("self = pmv")
        self.vf.log("##")
        self.vf.log("## Vision networks are saved")
        self.vf.log("##")
        self.exit_cb()

        
    def exit_cb(self):
        """the original exit_cb() in simpleNE.py destroys the root, which
        we cannot do here. Hence, we need to re-implement the exit_cb() here
        """
        #################
        # PART I: this is the exit_cb() from Vision/VPE.py:
        #################
    
        # we add attributes to node libraries. Upon exit, we clear these
        # attributes:
        for lib in self.ed.libraries.values():
            self.ed.deleteLibrary(lib.name)

        
        #################
        # PART II: this is the exit_cb() from NetworkEditor/simpleNE.py:
        #################
        from NetworkEditor.macros import MacroNetwork
        for net in self.ed.networks.values():
            if not isinstance(net, MacroNetwork):
                self.ed.deleteNetwork(net)
        self.root = None

            
    def onAddCmdToViewer(self):
        pass

    def interactiveExit_cb(self, event=None):
        from tkMessageBox import askyesno
        msg = askyesno("Quit","Are you sure you want to quit PMV?",parent = self.root)
        if msg == True:
            self.exit_cb()
            self.vf.GUI.quit_cb()        

                    
    def doit(self):
        if self.root is None:
            self.root = Tkinter.Toplevel()
            self.root.withdraw()

# the vision font must be decided in vision or _visionrc, not here anymore
#            if 'changeFont' in self.vf.commands.keys():
#                currentFont = self.vf.changeFont.getCurrentFont()
#                self.ed = VisualProgramingEnvironment(
#                    master=self.root, font=currentFont, withShell=0)
#            else:
            self.ed = VisualProgramingEnvironment(master=self.root,
                                                  withShell=0)

            self.root.protocol("WM_DELETE_WINDOW", self.hide)

            if getResourceFolder() is None:
                self.ed.loadLibModule('Vision.StandardNodes')
            else:
                self.ed.sourceFile(resourceFile='_visionrc')
                self.ed.updateFastLibs()

            filemenu = self.ed.menuButtons['File'].menu
            filemenu.entryconfig(filemenu.index('Quit'),command = self.hide)
            # let Vision know which PMV instance runs it
            self.ed.vf = self.vf

            # add handle to Pmv library instance
            from Pmv.VisionInterface.PmvNodes import pmvlib
            self.lib = pmvlib

            # initialize the API between PMV and Vision
            self.vf.visionAPI.setEditor(self.ed)
            self.vf.visionAPI.setLibrary(self.lib)

            # add Pmv library to Vision
            self.ed.addLibraryInstance(pmvlib, 'Pmv.VisionInterface.PmvNodes',
                                       'pmvlib')

            # add Standard library to Vision
            from Vision.StandardNodes import stdlib
            self.ed.addLibraryInstance(stdlib, 'Vision.StandardNodes',
                                       'stdlib')
            
            # add MolKit library to Vision if needed
            if len(self.vf.Mols):
                from MolKit.VisionInterface.MolKitNodes import molkitlib
                self.ed.addLibraryInstance(
                    molkitlib, 'MolKit.VisionInterface.MolKitNodes', 'molkitlib')

            # add molecule nodes to Pmv library if molecules were loaded in
            # Pmv before Vision was started
            for obj, name, kw in self.vf.visionAPI.objects:
                self.vf.visionAPI.addNodeToLibrary(obj, name, kw)

            # is ARTK running? if so, we need to add the library and nodes
            if hasattr(self.vf, 'art') and self.vf.art.visionAPI is not None:
                visionAPI = self.vf.art.visionAPI
                visionAPI.setEditor(self.ed)
                from ARViewer.VisionInterface.ARNodes import artlib
                visionAPI.setLibrary(artlib)
                visionAPI.ed.addLibraryInstance(
                    artlib, 'ARTK.VisionInterface.ARNodes', 'artlib')
                # add nodes to ARTK library 
                for obj, name, kw in visionAPI.objects:
                    visionAPI.addNodeToLibrary(obj, name, kw)

                # and add link to ARViewer
                self.ed.art = self.vf.art

        elif self.vf.GUI.toolbarCheckbuttons['Vision']['Variable'].get() == 0 and self.root:
            self.root.withdraw()
        elif self.vf.GUI.toolbarCheckbuttons['Vision']['Variable'].get() == 1 and self.root:
            self.root.deiconify()

        ##################################################################
        # FIXME:
        # Workaround: currently, Vision would crash on some Windows2000 and SGI
        # when running multi-threaded. We turn MT off by default
        ##################################################################
        #if sys.platform == 'win32' or sys.platform == 'irix646':
        self.ed.configure(withThreads=0)

    def show(self, event=None):
        if self.root is None:
            self.doitWrapper()
        self.root.deiconify()
        self.vf.GUI.toolbarCheckbuttons['Vision']['Variable'].set(1)
        

    def hide(self, event=None):
        if self.root:
            self.root.withdraw()
        self.vf.GUI.toolbarCheckbuttons['Vision']['Variable'].set(0)

    
    def guiCallback(self):
        self.doitWrapper()


    def __call__(self, **kw):
        """None <- vision(**kw) starts the visual programming environment"""
        apply( self.doitWrapper, (), kw )


        
VisionCommandGUI = MVCommandGUI()
msg = 'show/Hide the visual programming environment Vision'
from moleculeViewer import ICONPATH
VisionCommandGUI.addToolBar('Vision', icon1='vision.png', balloonhelp=msg,
                            icon_dir=ICONPATH, index=5)



commandList = [
    {'name':'vision', 'cmd':VisionCommand(), 'gui':VisionCommandGUI},
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])



