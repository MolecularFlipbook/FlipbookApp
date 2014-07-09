# specify mglroot here
import sys, os
path = os.path.join(mglroot, "MGLToolsPckgs")
sys.path.insert(0,path)

from os import getenv
if getenv('MGLPYTHONPATH'):
    sys.path.insert(0, getenv('MGLPYTHONPATH')) 

from Support.path import setSysPath
setSysPath(path)
#sys.path.insert(0,os.path.abspath('.'))
