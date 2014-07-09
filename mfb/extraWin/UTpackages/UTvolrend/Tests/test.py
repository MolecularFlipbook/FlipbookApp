## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by 

#!/usr/bin/env python
try:
    import numpy.oldnumeric as Numeric
    from numpy.oldnumeric import *
except:
    print("This test requires the Numeric extension")
    import sys
    sys.exit()
#from RandomArray import *
import string, sys
try:
    from opengltk.OpenGL.GL import *
    from opengltk.OpenGL.GLUT import *
    from opengltk.OpenGL.GLU import *
except:
    print("Error: Could not import opengltk ")
from struct import unpack
#from Volume import VolumeLibrary
from UTpackages.UTvolrend import UTVolumeLibrary
from mglutil.regression import testplus
import sys
print(("VOLLIB:", UTVolumeLibrary.__file__))
class TestVolumeLibrary:

    def __init__(self):
        
        self.rotMatrix = [1.,0.,0.,0.,
                          0.,1.,0.,0.,
                          0.,0.,1.,0.,
                          0.,0.,0.,1.]
        self.transMatrix = [1.,0.,0.,0.,
                            0.,1.,0.,0.,
                            0.,0.,1.,0.,
                            0.,0.,0.,1.]
        self.W= 640
        self.H= 480
        self.halted = 0

        self.whichbutton=0
        self.mousex =0
        self.mousey =0
        self.cdx = 0
        self.cdy = 0
        self.state = 'ROTATE'
        
        #volume renderer
        self.vol = UTVolumeLibrary.VolumeRenderer()
	self.data =None
	self.byte_map=None
	self.indexCM =0
        
    def Display(self,*args):

        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT| GL_DEPTH_BUFFER_BIT)
        #Set up the modelview matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslated(0.0, 0.0, -4.0)
        glMultMatrixd(self.transMatrix)
        glMultMatrixd(self.rotMatrix)

        #the volume is rendered 
        #volumeRenderer.renderVolume();
        self.vol.renderVolume()

        glutSwapBuffers()


    def halt(self):
        pass


    def setup_viewport(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, 1.0, 0.0, 1.0, 0.0, 1.0)

    def reshape(self,w, h):

        glViewport(0, 0, w, h)
        self.setup_viewport()

    #Callback function for the mouse button */
    def MouseButton(self,button, mstate, x, y):
        #sets the initial positions for mousex and mousey */
        if (mstate == GLUT_DOWN):
            self.mousex = x
            self.mousey = y
            self.whichbutton = button
            self.cdx = 0
            self.cdy = 0

    #Callback function for the mouse motion */
    def MouseMove(self,x, y):


        dx = x-self.mousex
        dy = y-self.mousey
        if self.state == 'ROTATE':
            self.Rotate(dx, dy)

        elif self.state ==  'TRANSLATE':
            if (self.whichbutton == GLUT_LEFT_BUTTON):
                self.Translate(dx, -dy,0)
            else:
                self.Translate(0,0,-dy)
        else:
            pass
        self.mousex = x
        self.mousey = y
        glutPostRedisplay()

    def Keyboard(self,key, x, y):

        print(('--> keyboard( %s <%c>, %i, %i)' % (key, chr( key), x, y)))
	chkey = chr(key)
        if (chkey == 'R') or (chkey=='r'):
            self.state = 'ROTATE'

        elif (chkey == 't') or (chkey=='T'):
            self.state = 'TRANSLATE'

        elif (chkey == 'q') or (chkey == 'Q'):
            sys.exit()
	elif (chkey == 'z') or (chkey == 'Z'):
		#self.rotateCM = 1
		self.StartRotateCM()
	elif (chkey == 'a') or (chkey == 'A'):
		#self.rotateCM = 0
		self.StopRotateCM()
        else:
            pass


    def StopRotateCM(self):
	    
        if hasattr(self, 'tmpCM'):
	    self.byte_map[:] = self.tmpCM[:]
	    del self.tmpCM
	    self.indexCM =0
	self.vol.uploadColorMap(self.byte_map)
	    
    def StartRotateCM(self):
	    
        if not hasattr(self, 'tmpCM'):
	    self.tmpCM= Numeric.zeros((256,4),Numeric.UnsignedInt8)
	    self.tmpCM[:] = self.byte_map[:]

	for i in range(10):
	    if 10 <= self.indexCM < 255 :
		#print "self.indexCM",self.indexCM
		self.byte_map[self.indexCM] = (255,0,0,255)
		#print "self.indexCM -10",self.indexCM -10
		self.byte_map[self.indexCM -10]=self.tmpCM[self.indexCM -10]
		self.indexCM =self.indexCM +1
	    elif self.indexCM <10 :
	        self.byte_map[self.indexCM] = (255,0,0,255)
		self.indexCM =self.indexCM +1
	    else:
	        print("End of color map")
	self.vol.uploadColorMap(self.byte_map)

	    
    def Rotate(self,dx, dy):
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glRotated((float(dy)), 1.0, 0.0, 0.0)
        glRotated((float(dx)), 0.0, 1.0, 0.0)
        glMultMatrixd(self.rotMatrix)
        self.rotMatrix=glGetDoublev(GL_MODELVIEW_MATRIX)
        #self.rotMatrix.shape = (16,)
        glPopMatrix()

    def Translate(self,dx,dy, dz):
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glTranslated((float(dx))/100.0, (float(dy))/100.0, (float(dz))/10.0)
        glMultMatrixd(self.transMatrix)
        self.transMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.transMatrix.shape = (16,)
        glPopMatrix()


    def RegisterCallbacks(self):

        #glutSetDisplayFuncCallback(self.Display)
	#glutDisplayFunc()
	
	#glutSetIdleFuncCallback(self.Idle)
	#glutIdleFunc()

	glutDisplayFunc(self.Display)
	glutIdleFunc(self.Idle)
	
        #glutSetMouseFuncCallback(self.MouseButton)
        #glutMouseFunc()
	
        #glutSetMotionFuncCallback(self.MouseMove)
        #glutMotionFunc()
	
        #glutSetKeyboardFuncCallback(self.Keyboard)
        #glutKeyboardFunc()
        try:
            glutMouseFunc(self.MouseButton)
        except:
            print("Could not use glutMouseFunc")
	glutMotionFunc(self.MouseMove)
	glutKeyboardFunc(self.Keyboard)

    def InitProjection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective( 30.0,
                        self.W / self.H,
                        0.01,
                        20.0
                        )

    def InitModelMatrix(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        #initialize rotMatrix an d transMatrix to the identity */
        self.rotMatrix=glGetDoublev(GL_MODELVIEW_MATRIX)
        #self.rotMatrix.shape = (16,)
        self.transMatrix=glGetDoublev(GL_MODELVIEW_MATRIX)
        #self.transMatrix.shape = (16,)


    def InitLighting(self):

        lightdir = [-1.0, 1.0, 1.0, 0.0]
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, lightdir)
        glEnable(GL_NORMALIZE)


    def Idle(self):
        self.Rotate(self.cdx, self.cdy)
        glutPostRedisplay()


    def init(self):

        self.InitProjection()
        self.InitModelMatrix()
        self.InitLighting()
        self.InitState()
        self.InitVolumeRenderer()
	self.LoadData()
        self.InitData()

    def BeginGraphics(self):

        print("Init")
        glutInit('foo')
	print("InitWindowSize")
        glutInitWindowSize(640,480)
	print("InitWindowPosition")
        glutInitWindowPosition(100,100)
	print("InitDisplayMode")
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
	print("CreateWindow")
        win = glutCreateWindow('test')
	print("SetWindow")
        glutSetWindow(win)
	print("init")
        self.init()

        self.RegisterCallbacks()

        glutMainLoop()


    def InitVolumeRenderer(self):
        if not self.vol.initRenderer():
            print("Warning, there was an error initializing the volume renderer\n")

    def LoadData(self):
        #load colormap from file
	import os
        
	myfile = open("ct_head.rawiv", "rb" )
        print(("myfile: ", myfile))
        if not myfile:
            print("Error: could not open file: ct_head.rawiv")
        else:
            #the header
            header=myfile.read(68)
            # unpack header following rawiv format,big endian
            h = unpack('>6f5I6f',header)
            width=int(h[8])
            height=int(h[9])
            depth =int(h[10])

            # load the data
            l = myfile.read(width*height*depth)
            self.data = Numeric.fromstring(l, Numeric.UnsignedInt8,
                                           (width*height*depth) )
            self.size = (width, height, depth)
            print(("size: ", self.size))
            #self.data = Numeric.reshape(self.data,(width,height,depth))
            myfile.close()
        
  	myfile = open("colormap.map", "rb" )
        if not myfile:
            print("Error: Could not open file: colormap.map")
        else:
            l = myfile.read(256*4)
            self.byte_map =Numeric.fromstring(l,
                                              Numeric.UnsignedInt8, (256*4)) 
            self.byte_map = Numeric.reshape(self.byte_map,(256,4))
            myfile.close()

    def InitState(self):

        glClearColor(0.2, 0.2, 0.2, 1.0)
        glColor4d(1.0, 1.0, 1.0, 1.0)
        glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

    def InitData(self):
        nx, ny, nz = self.size
	print("uploadColorMappedData..")
        status = self.vol.uploadColorMappedData(self.data, nx, ny, nz)
	print(("status:", status))
	print("done..")
        self.vol.uploadColorMap(self.byte_map)

def test_Library():
    v = TestVolumeLibrary()
    v.BeginGraphics()


print("Use the mouse buttons to control.")
print(" Hit 't' or 'T' to do translation.")
print(" Hit 'r' or 'R' to do rotation.")
print("Hit q  key to quit.")

	
##  harness = testplus.TestHarness( __name__,
##                                  funs = testplus.testcollect( globals()),
##                                  )
	

if __name__ == '__main__':
    harness = testplus.TestHarness( __name__,
				    funs = testplus.testcollect( globals()),
				    )
	
    print(harness)
    sys.exit( len( harness))
	

