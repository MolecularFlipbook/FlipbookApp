path = __path__[0]
import os, sys, string

def findExecModule(modname):
    
    """return (platform-dependent) path to executable module"""
    assert modname
    mod = __import__('binaries')
    #pth = mod.__path__[0]
    pth = mod.path
    if sys.platform == 'win32':
        modname = modname + '.exe'
    pth = os.path.join( pth, modname)
    
    if os.path.exists(pth):
        return pth
    else:
        print 'ERROR! Module %s not found in %s'%(modname, path)
        return None
__MGLTOOLSVersion__ = '1-4alpha3'
CRITICAL_DEPENDENCIES = ['mglutil']
NONCRITICAL_DEPENDENCIES = ['DejaVu',]
