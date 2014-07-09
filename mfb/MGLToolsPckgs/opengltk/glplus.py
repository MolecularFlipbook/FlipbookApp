#
# copyright_notice
#

"""OpenGL utilities
"""

from opengltk.OpenGL import GL

def DrawArrays( mode, count, first=0):
    """glDrawArrays with default args
    model - GLenum
    count - GLsizei
    first - GLint
    """
    GL.glDrawArrays( mode, first, count)


