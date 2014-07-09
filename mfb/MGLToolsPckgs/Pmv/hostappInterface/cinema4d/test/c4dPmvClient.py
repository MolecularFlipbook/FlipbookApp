##############################################
# pmvClient.py  (c) 2009 by Ludovic Autin    #
#                                            #
# Description:                               #
#											 #
#											 #
##############################################
from Pmv.moleculeViewer import MoleculeViewer
from mglutil.hostappli.pdb_c4d import *

import c4d
from c4d import documents

scene = doc = documents.get_active_document()

self = MoleculeViewer(logMode = 'overwrite', customizer=None, master=None,title='toto', withShell= 0,verbose=False, gui = False)
from Pmv.displayCommands import BindGeomToMolecularFragment
self.addCommand(BindGeomToMolecularFragment(), 'bindGeomToMolecularFragment', None)
self.embedInto('c4d',debug=1)
self.at_mat=create_Atoms_materials(doc)
self.hostApp.setServer('localhost',50000)
self.hostApp.start()
