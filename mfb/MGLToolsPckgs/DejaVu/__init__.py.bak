########################################################################
#
# Date: 2000 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/DejaVu/__init__.py,v 1.69.2.1 2012/10/31 22:25:01 mgltools Exp $
#
# $Id: __init__.py,v 1.69.2.1 2012/10/31 22:25:01 mgltools Exp $
#

import os
import sys
import warnings


# makes this directory the viewer package
## <<<<<<< __init__.py
## try:
##   import OpenGL
##   if not OpenGL._numeric:
##       import sys
##       print 'FATAL ERROR: DejaVu requires the OpenGL Package to be compiled \
##  with the the NUMERIC option turned on'
##       sys.exit(1)
      
## except:
##     import sys
##     print 'FATAL ERROR: OpenGL Package not found'
##     sys.exit(1)

## def loadTogl(master):
##     # simulate the setting of TCLLIPATH

##     import os, sys
##     # Togl is expected to be in sys.exec_prefix/lib

##     # build path to directory containing Togl
##     pth = os.path.join(sys.exec_prefix, 'lib')
##     ToglPath = os.path.join(sys.exec_prefix, pth)

##     # get TCL interpreter auto_path variable
##     tclpath = master.tk.globalgetvar('auto_path')

##     # ToglPath not already in there, add it
##     from string import split
##     if ToglPath not in split(tclpath):
##         tclpath = ToglPath + ' ' + tclpath
##         master.tk.globalsetvar('auto_path', tclpath )

##     # load Togl extension into TCL interpreter
##     master.tk.call('package', 'require', 'Togl')
#=======
##  try:
##    from bufarray import bufarray_Numeric
##  except ImportError:
##    raise RuntimeError('FATAL ERROR: bufarray_Numeric not found')
  
## import bufarray_array

## from bufarray import bufarray_array

try:
  from opengltk import OpenGL
except ImportError:
    print 'FATAL ERROR: opengltk.OpenGL Package not found'
    raise RuntimeError('FATAL ERROR: opengltk.OpenGL Package not found')

from Tkinter import _default_root, Tk

def loadTogl(master):
    # simulate the setting of TCLLIPATH

    import sys, os
    from os import path
    # Togl is expected to be 

    # build path to directory containing Togl
    from opengltk.OpenGL import Tk
    ToglPath = path.dirname(path.abspath(Tk.__file__))
    # get TCL interpreter auto_path variable
    tclpath = master.tk.globalgetvar('auto_path')

    # ToglPath not already in there, add it
    from string import split
    if ToglPath not in tclpath:
        tclpath = (ToglPath,) + tclpath
        master.tk.globalsetvar('auto_path', tclpath )
    # load Togl extension into TCL interpreter

    if os.name == 'nt':
        toglVersion = master.tk.call('package', 'require', 'Togl','1.7')  
    else:
        toglVersion = master.tk.call('package', 'require', 'Togl','2.0')

    return toglVersion

dejavurcText = """########################################################################
#
# Date: Decembre 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    DejaVu Resource File
#
#########################################################################
# To customize DejaVu, you can modify the _dejavurc file:
# unix: ~/.mgltools/[version number]/DejaVu/_dejavurc
# windows: \Documents and Settings\(user name)\.mgltools\(version numer)\DejaVu\_dejavurc
# DejaVu will generate it automatically if it doesn't exist.
# Do not modify the original source file DejaVu/__init__.py
##################################################################

preventIntelBug_BlackTriangles = None # True, False or None (will evaluate GL_VENDOR)
preventIntelBug_WhiteTriangles = None # True, False or None (will evaluate GL_VENDOR)
defaultSpinningMode = 0 # 0 - None , 1 - Spin , 2 - Bounce , 3 - Oscillate
allowedAntiAliasInMotion = 0 # 0,2,3,4,8,15,24,66
#enableStereo = False # True, False
defaultAntiAlias = None # None,0,2,3,4,8,15,24,66, None will decide if the graphic card is good enough
enableSelectionContour = True # True, False
selectionContourSize = 0 # 0 (= disabled), 1,2,3 .....
selectionContourColor = (0., 1., 1., .7) # (1., 0., 1., .7)
selectionPatternSize = 6 # 0 .... 50 (0 = disabled)
enableVertexArrayVBO = False
enableVertexArrayNonVBO = False
enableVertexArray = enableVertexArrayVBO or enableVertexArrayNonVBO
def functionName0(level=1):
    # i.e. this func => level 0 (useless)
    # calling function => level 1
    # one function up => level 2
    assert level > 0 , level
    lsf = sys._getframe(level)
    functionname = lsf.f_code.co_name
    from os import sep
    filename = lsf.f_code.co_filename.split(sep)[-1]
    linenumber = lsf.f_lineno
    if True: #filename == 'MaterialEditor.py':
        print functionname, filename, linenumber
"""

def ensureDejaVuResourceFile():
    """verify or generate _dejavurc file
"""
    #print "ensureDejaVuResourceFile"
    
    #import pdb;pdb.set_trace()
    
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    rcFolder = getResourceFolderWithVersion()
    if rcFolder is None:
        return
    rcFolder += os.sep + 'DejaVu'
    if not os.path.isdir(rcFolder):
        try:
            os.mkdir(rcFolder)
        except:
            txt = "Cannot create the Resource Folder %s" %rcFolder
            warnings.warn(txt)
            return None

    rcFile = rcFolder + os.sep + '_dejavurc'
    if os.path.isfile(rcFile) is False:
        try:
            f = open(rcFile, "w")
            map( lambda x, f=f: f.write(x), dejavurcText )
            f.close()
        except:
            txt = "can not create _dejavurc"
            warnings.warn(txt)
            return None

    return rcFile



# after this we can access variables in _dejavurc with
# from DejaVu import preventIntelBug_BlackTriangles
rcFile = ensureDejaVuResourceFile()
if rcFile is None:
    exec( dejavurcText )
else:
    execfile( rcFile )

from Viewer import Viewer
from viewerConst import *

CRITICAL_DEPENDENCIES = ['opengltk', 'numpy', 'mglutil','geomutils']
NONCRITICAL_DEPENDENCIES = ['PIL', 'numarray', 'Pmw', 'gle', 'UTpackages', 'NetworkEditor', 'symserv', 'Vision', 'Volume', 'QSlimLib', 'bhtree','pyglf', 'pymedia','Scenario2', 'SimPy', 'mslib', 'pytz', 'Pmv', 'bpy', 'BPyMesh', 'MolKit']

