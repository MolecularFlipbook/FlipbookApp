#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2010
#
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/seqViewerCommands.py,v 1.2 2010/09/13 23:32:51 sanner Exp $
# 
# $Id: seqViewerCommands.py,v 1.2 2010/09/13 23:32:51 sanner Exp $
#

import Pmw

from Pmv.mvCommand import MVCommand, MVCommandGUI
from MolKit.sequence import Sequence, Alignment

class LoadSequenceViewerCommand(MVCommand):
    """
    The LoadSequenceViewerCommand adds the Sequence Viewer widget
    of the GUI
    \nPackage : Pmv
    \nModule  : seqViewerCommands
    \nClass   : LoadSequenceViewerCommand
    \nName    : loadSequenceViewer
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        

    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            gui = self.vf.GUI

            self.balloon = Pmw.Balloon(self.vf.GUI.ROOT)

            # add a page for sequence viewer
            self.seqWidgetM = gui.VPane.add('Sequence', min=100, size=200)
            self.seqWidgetM.pack(anchor='n', expand=1, fill='both')

            from mglutil.gui.BasicWidgets.Tk.seqViewer import AlignmentEditor
            
            self.aled = AlignmentEditor(master=self.seqWidgetM)


    def onAddObjectToViewer(self, obj):
        """
        update list of molecules in sequence viewer
        """
        if self.vf.hasGui:
            seq = Sequence(obj.chains.residues.type, name=obj.name)
            self.aled.alignment.addSequence(seq)
            self.aled.redraw()

               
commandList = [
    {'name':'loadSequenceViewer', 'cmd':LoadSequenceViewerCommand(),
     'gui':None},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
