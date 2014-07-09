

__all__ = ["glGetMapdv",
    "glGetMapfv",
    "glGetMapiv",
    "glGetPixelMapfv",
    "glGetPixelMapuiv",
    "glGetPixelMapusv",
    "glGetPointerv",
    "glGetTexImage"]

from warnings import warn

from opengltk.extent import _gllib


class ToWrap( RuntimeWarning):
    pass


def glGetMapdv( target, query, v):
    """To Wrap: """
    #warn( desc, ToWrap)
    return _gllib.glGetMapdv( target, query, v)

def glGetMapfv( target, query, v):
    """To Wrap: """
    #warn( desc, ToWrap)
    return _gllib.glGetMapfv( target, query, v)

def glGetMapiv( target, query, v):
    """To Wrap: """
    #warn( desc, ToWrap)
    return _gllib.glGetMapiv( target, query, v)

def glGetPixelMapfv( map, values):
    """To Wrap: use glGet to get value sz to return"""
    #warn( desc, ToWrap)
    return _gllib.glGetPixelMapfv( map, values)

def glGetPixelMapuiv( map, values):
    """To Wrap: use glGet to get value sz to return"""
    #warn( desc, ToWrap)
    return _gllib.glGetPixelMapuiv( map, values)

def glGetPixelMapusv( map, values):
    """To Wrap: use glGet to get value sz to return"""
    #warn( desc, ToWrap)
    return _gllib.glGetPixelMapusv( map, values)

def glGetPointerv( pname, params):
    """To Wrap: convert cobject to appropriate Numeric array (need size...)"""
    #warn( desc, ToWrap)
    return _gllib.glGetPointerv( pname, params)

def glGetTexImage( target, level, format, type, pixels):
    """To Wrap: """
    #warn( desc, ToWrap)
    return _gllib.glGetTexImage( target, level, format, type, pixels)
