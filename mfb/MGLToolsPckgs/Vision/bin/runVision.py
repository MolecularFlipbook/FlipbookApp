# $Header: /opt/cvs/python/packages/share1.5/Vision/bin/runVision.py,v 1.48 2008/07/30 18:33:40 vareille Exp $
# $Id: runVision.py,v 1.48 2008/07/30 18:33:40 vareille Exp $

# vision can be launched from a python shell like this:
#import Vision; Vision.runVision()

import sys
import Vision

if '__IP' in dir(): # ipython
    Vision.runVision(sys.argv, ownInterpreter = False)
else:
    Vision.runVision(sys.argv, ownInterpreter = True)

