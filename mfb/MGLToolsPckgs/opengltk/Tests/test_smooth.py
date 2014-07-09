import sys
from test_cube import TestBase
from opengltk.OpenGL import GL, GLU, GLUT

class TestSmooth(TestBase):
   def triangle(self):
      GL.glBegin( GL.GL_TRIANGLES)
      try:
          GL.glColor3f( 1.0, 0.0, 0.0)
          GL.glVertex2f( 5.0, 5.0)
          GL.glColor3f( 0.0, 1.0, 0.0)
          GL.glVertex2f( 25.0, 5.0)
          GL.glColor3f( 0.0, 0.0, 1.0)
          GL.glVertex2f( 5.0, 25.0)
      finally:
          GL.glEnd()

   def display(self):
      GL.glClear(GL.GL_COLOR_BUFFER_BIT)
      self.triangle()
      GL.glFlush()


   def reshape(self, w, h):
      GL.glViewport( 0, 0, w, h)
      GL.glMatrixMode(GL.GL_PROJECTION)
      GL.glLoadIdentity()
      if(w <= h):
         GLU.gluOrtho2D( 0.0, 30.0, 0.0, 30.0 * h/w)
      else:
         GLU.gluOrtho2D( 0.0, 30.0 * w/h, 0.0, 30.0)
      GL.glMatrixMode( GL.GL_MODELVIEW)

   def setUp(self):
       from opengltk.OpenGL import GL,  GLU, GLUT
       print "GL imported from: ", GL.__file__

   def test_Smooth(self):   
       self.doloop( 'Smooth', GL.GL_SMOOTH, self.display, self.reshape, self.keyboard)


if __name__ == '__main__':
   test_cases = ['TestSmooth']
   unittest.main(argv=([__name__, '-v'])+test_cases )

