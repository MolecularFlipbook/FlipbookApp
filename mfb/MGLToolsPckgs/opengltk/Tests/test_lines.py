import sys
from test_cube import TestBase
from opengltk.OpenGL import GL, GLU, GLUT

class TestLines(TestBase):
    
    def drawOneLine(self, x1, y1, x2, y2):
        GL.glBegin( GL.GL_LINES)
        try:
            GL.glVertex2f( x1, y1)
            GL.glVertex2f( x2, y2)
        finally:
            GL.glEnd()

    def display(self):
        GL.glClear( GL.GL_COLOR_BUFFER_BIT)

        # select white for all lines
        GL.glColor3f( 1.0, 1.0, 1.0)

        # in 1st row, 3 lines, each with a different stipple
        GL.glEnable( GL.GL_LINE_STIPPLE)

        GL.glLineStipple( 1, 0x0101)  #  dotted  
        self.drawOneLine( 50.0, 125.0, 150.0, 125.0)
        GL.glLineStipple( 1, 0x00FF)  #  dashed 
        self.drawOneLine( 150.0, 125.0, 250.0, 125.0);
        GL.glLineStipple( 1, 0x1C47)  #  dash/dot/dash
        self.drawOneLine( 250.0, 125.0, 350.0, 125.0)

        # in 2nd row, 3 wide lines, each with different stipple 
        GL.glLineWidth( 5.0)
        GL.glLineStipple( 1, 0x0101)  #  dotted 
        self.drawOneLine( 50.0, 100.0, 150.0, 100.0)
        GL.glLineStipple( 1, 0x00FF)  #  dashed
        self.drawOneLine( 150.0, 100.0, 250.0, 100.0)
        GL.glLineStipple( 1, 0x1C47)  #  dash/dot/dash
        self.drawOneLine( 250.0, 100.0, 350.0, 100.0)
        GL.glLineWidth( 1.0)

        # in 3rd row, 6 lines, with dash/dot/dash stipple  
        # as part of a single connected line strip        
        GL.glLineStipple( 1, 0x1C47)  # dash/dot/dash
        GL.glBegin( GL.GL_LINE_STRIP)
        try:
            for i in range( 0, 7):
                GL.glVertex2f( 50.0 + (i * 50.0), 75.0)
        finally:
            GL.glEnd()

        # in 4th row, 6 independent lines with same stipple  */
        for i in range( 0, 6):
            self.drawOneLine( 50.0 + (i * 50.0), 50.0, 50.0 + ((i+1) * 50.0), 50.0)

        # in 5th row, 1 line, with dash/dot/dash stipple 
        # and a stipple repeat factor of 5               
        GL.glLineStipple( 5, 0x1C47)  #  dash/dot/dash 
        self.drawOneLine( 50.0, 25.0, 350.0, 25.0)

        GL.glDisable( GL.GL_LINE_STIPPLE)
        GL.glFlush()

    def reshape(self, w, h):
        GL.glViewport( 0, 0, w, h)
        GL.glMatrixMode( GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluOrtho2D( 0.0, w, 0.0, h)

    def test_Lines(self):
        self.doloop( 'Lines', GL.GL_FLAT, self.display, self.reshape, self.keyboard)

    def test_002(self):
        print "test002"
        


if __name__ == '__main__':

    test_cases = ['TestLines']
    unittest.main(argv=([__name__, '-v'])+test_cases )



