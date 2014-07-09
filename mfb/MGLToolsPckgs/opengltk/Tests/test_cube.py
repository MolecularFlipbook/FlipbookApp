
import sys
import unittest
try:
    from opengltk.OpenGL import GL, GLU, GLUT
except:
    print "could not import OpenGL"
#print "GL imported from: ", GL.__file__

class TestBase(unittest.TestCase):
    def keyboard(self, key, x, y):
        if 'e' == chr( key):
            raise RuntimeError
        elif 'q' == chr( key):
            sys.exit()

    def exitloop(self, x):
        print "exiting.."
        sys.exit()


    def doloop(self, name, shademodel, cbdisplay, cbreshape, cbkeyboard):
        GLUT.glutInit( sys.argv)
        GLUT.glutInitDisplayMode( GLUT.GLUT_SINGLE | GLUT.GLUT_RGB)
        GLUT.glutInitWindowSize( 500, 500)
        GLUT.glutInitWindowPosition( 100, 100)
        GLUT.glutCreateWindow( name)
        GL.glClearColor( 0.0, 0.0, 0.0, 0.0)
        GL.glShadeModel( GL.GL_FLAT)

        GLUT.glutDisplayFunc( cbdisplay)
        GLUT.glutReshapeFunc( cbreshape)
        GLUT.glutKeyboardFunc( cbkeyboard)
        GLUT.glutTimerFunc(1000, self.exitloop, 0)
        GLUT.glutMainLoop()


class TestCube(TestBase):


    def display(self):
           GL.glClear( GL.GL_COLOR_BUFFER_BIT)
           GL.glColor3f( 1.0, 1.0, 1.0)
           GL.glLoadIdentity()             # clear the matrix 
           # viewing transformation 
           GLU.gluLookAt( 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
           GL.glScalef( 1.0, 2.0, 1.0)      # modeling transformation 
           GLUT.glutWireCube( 1.0)
           GL.glFlush()

    def reshape(self,  w, h):
           GL.glViewport( 0, 0, w, h)
           GL.glMatrixMode( GL.GL_PROJECTION)
           GL.glLoadIdentity()
           GL.glFrustum( -1.0, 1.0, -1.0, 1.0, 1.5, 20.0)
           GL.glMatrixMode( GL.GL_MODELVIEW)



    def setUp(self):
        from opengltk.OpenGL import GL, GLU, GLUT
        print "GL imported from: ", GL.__file__

    def test_Cube(self):
        self.doloop( 'cube', GL.GL_FLAT, self.display, self.reshape, self.keyboard)


if __name__ == '__main__':
    test_cases = ['TestCube']
    unittest.main(argv=([__name__, '-v'])+test_cases )

