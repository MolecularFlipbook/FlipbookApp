# $Header: /opt/cvs/CADD/bin/runCADD.py,v 1.2 2011/01/18 00:56:07 nadya Exp $
# $Id: runCADD.py,v 1.2 2011/01/18 00:56:07 nadya Exp $

# vision can be launched from a python shell like this:
#import Vision; Vision.runVision()

import sys
import CADD

if '__IP' in dir(): # ipython
    CADD.runCADD(sys.argv, ownInterpreter = False)
else:
    CADD.runCADD(sys.argv, ownInterpreter = True)

