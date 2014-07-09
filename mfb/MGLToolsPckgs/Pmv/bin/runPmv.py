# $Header: /opt/cvs/python/packages/share1.5/Pmv/bin/runPmv.py,v 1.78 2008/07/30 18:33:40 vareille Exp $
# $Id: runPmv.py,v 1.78 2008/07/30 18:33:40 vareille Exp $

# pmv can be launched from a python shell like this:
#import Pmv; Pmv.runPmv()

import sys
import Pmv

if '__IP' in dir(): # ipython
    ownInterpreter = False
else:
    ownInterpreter = True 

if '__file__' in locals():
    Pmv.runPmv(sys.argv, ownInterpreter=ownInterpreter, PmvScriptPath=__file__)
else:
    Pmv.runPmv(sys.argv, ownInterpreter=ownInterpreter)
