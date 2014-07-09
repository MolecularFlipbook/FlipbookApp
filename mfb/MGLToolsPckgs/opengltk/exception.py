#
# copyright_notice
#

'''opengltk exception processing
'''

__all__ = ()


from extent import _gllib
from extent._glulib import gluErrorString

class GLerror( StandardError):
    def __init__( self, *errs):
        self.errs = errs
        apply( StandardError.__init__, [self] + map( gluErrorString, errs))


##errmap = {
##    _gllib.GL_NO_ERROR: lambda x: SystemError( gluErrorString( x)),
##    _gllib.GL_INVALID_ENUM: lambda x: ValueError( gluErrorString( x)),
###    _gllib.GL_INVALID_OPERATION: lambda x: ValueError( gluErrorString( x)),
##    _gllib.GL_INVALID_VALUE: lambda x: ValueError( gluErrorString( x)),
##    _gllib.GL_OUT_OF_MEMORY: lambda x: MemoryError( gluErrorString( x)),
##    }

##  from utilplus import customvalue
##  opengltk_exception_maxerrs = customvalue.get( 'opengltk_exception_maxerrs', 10)
opengltk_exception_maxerrs = 10

def processglerror( errcode):
    '''callback from C function opengltk_processerror()
    '''
    errs = [errcode]
    othererr = _gllib.glGetError()
    while othererr and othererr != _gllib.GL_INVALID_OPERATION: # glGetError pb
        errs.append( othererr)
        if opengltk_exception_maxerrs < len( errs):
            raise SystemError( 'opengltk_exception_maxerrs reached',
                               map( gluErrorString, errs))
        othererr = _gllib.glGetError()

    raise apply( GLerror, errs)


class GLwarning( RuntimeWarning):
    pass

def gluErrorCallback( errorCode):
    '''default callback for glu error functions
    '''
    import warnings
    warnings.warn( gluErrorString( errorCode), GLwarning)
    

class Glxerror( RuntimeError):
    def __init__( self, code):
        self.code = code
        RuntimeError.__init__( self, code)
    def __repr__( self):
        return `self.code`
    def __str__( self):
        from opengltk.extent import glxlib
        return {
            glxlib.GLX_NO_EXTENSION: 'dpy does not support the GLX extension',
            glxlib.GLX_BAD_SCREEN: 'the screen of vis does not correspond'
                ' to a screen',
            glxlib.GLX_BAD_ATTRIBUTE: 'attrib is not a valid GLX attribute',
            glxlib.GLX_BAD_VISUAL: 'vis does nott support GLX and an attribute'
                ' other than GLX_USE_GL is requested',
            }[ self.code]

