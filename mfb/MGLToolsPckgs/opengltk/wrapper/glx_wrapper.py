## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by 

#
# copyright_notice
#

"""glx wrappers
"""

import numpy.oldnumeric as Numeric
from opengltk.extent import _glxlib


def glXChooseVisual( dpy, screen, attribpairs):
    """
    dpy - Display*
    screen - int
    attribpairs - seq( (attribute, value))
    """
    from types import IntType
    larray = Numeric.zeros( 2 * len( attribpairs) + 1, Numeric.Int32)
    idx = 0
    for assg in attribpairs:
        if isinstance( assg, IntType):
            larray[ idx] = assg
        else:
            larray[ idx] = assg[ 0]
            idx += 1
            larray[ idx] = assg[ 1]
        idx += 1

    return _glxlib.glXChooseVisual( dpy, screen, larray)


def glXGetConfig( dpy, vis, attrib):
    """
    dpy - Display*
    vis - XVisualInfo*
    attrib - int
return - int
    """
    value = Numeric.zeros( 1, Numeric.Int32)
    res = _glxlib.glXGetConfig( dpy, vis, attrib, value)
    if res:
        from exception import Glxerror
        raise Glxerror( res)
    return value[ 0]


def glXQueryExtension( dpy):
    """
    dpy - Display*
return - bool, int, int: support, errorBase, eventBase
"""
    errorBase = Numeric.zeros( 1, Numeric.Int32)
    eventBase = Numeric.zeros( 1, Numeric.Int32)
    res = _glxlib.glXQueryExtension( dpy, errorBase, eventBase)
    return res, errorBase[ 0], eventBase[ 0]


def glXQueryVersion( dpy):
    """
    dpy - Display*
return - bool, int, int: support, major, minor
"""
    major = Numeric.zeros( 1, Numeric.Int32)
    minor = Numeric.zeros( 1, Numeric.Int32)
    res = _glxlib.glXQueryVersion( dpy, major, minor)
    return res, major[ 0], minor[ 0]


def XOpenDisplay( name=None):
    if name is None:
        from os import environ
        name = environ[ 'DISPLAY']
    return _glxlib.XOpenDisplay( name)

__all__ = [
    'glXChooseVisual',
    'glXGetConfig',
    'glXQueryExtension',
    'glXQueryVersion',
    'XOpenDisplay',
    ]

