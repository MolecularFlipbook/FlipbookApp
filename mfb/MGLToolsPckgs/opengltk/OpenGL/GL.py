#
# copyright_notice
#

"""GL module
"""
try :
    from opengltk.extent._gllib import *
    from opengltk.wrapper.gl_wrapper import *
except :
    GL_FRONT = None
    GL_ZERO = None
    GL_ONE = None
    GL_DST_COLOR = None
    GL_SRC_ALPHA = None
    GL_ONE_MINUS_DST_COLOR = None
    GL_ONE_MINUS_SRC_ALPHA = None
    GL_DST_ALPHA = None
    GL_ONE_MINUS_DST_ALPHA = None
    GL_SRC_ALPHA_SATURATE = None
    GL_SRC_COLOR = None
    GL_ONE_MINUS_SRC_COLOR = None
    GL_LIGHT0 = None
    GL_LIGHT1 = None
    GL_LIGHT2 = None
    GL_LIGHT3 = None
    GL_LIGHT4 = None
    GL_LIGHT5 = None
    GL_LIGHT6 = None
    GL_LIGHT7 = None
    GL_BACK = None
    GL_FILL=None
    GL_FLAT=None
    GL_NONE=None
    GL_SMOOTH = None
    GL_FRONT_AND_BACK = None
    GL_POINT = None
    GL_TRIANGLES = None
    GL_LINE_STRIP = None
    GL_LINE = None
    GL_LINES = None
    GL_QUADS= None
    GL_POLYGON = None
    