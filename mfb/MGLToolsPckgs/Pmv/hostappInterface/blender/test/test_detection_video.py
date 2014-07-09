##
## Copyright (C)2007 The Scripps Research Institute 
##
## Authors: Alexandre Gillet <gillet@scripps.edu>
##  
## All rights reserved.
##  
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##  
##   * Redistributions of source code must retain the above copyright notice,
##     this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright notice,
##     this list of conditions and the following disclaimer in the documentation 
##     and/or other materials provided with the distribution.
##   * Neither the name of the Scripps Research Institute nor the names of its
##     contributors may be used to endorse or promote products derived from this 
##     software without specific prior written permission.
##  
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, 
## BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
## FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##  
## For further information please contact:
##  Alexandre Gillet
##  <gillet@scripps.edu>
##  The Scripps Research Institute
##  10550 N Torrey Pines Rd 
##  La Jolla Ca 92037 USA
##  
##  
## $Header: /opt/cvs/python/packages/share1.5/Pmv/hostappInterface/blender/test/test_detection_video.py,v 1.2 2010/06/24 17:24:12 autin Exp $
## $Id: test_detection_video.py,v 1.2 2010/06/24 17:24:12 autin Exp $
##  
##
##
## This is a short test of the video
## it will display the video stream in a Tkinter windows 
##
# execfile("/local/MGL/MGLTools-1.5.5/MGLToolsPckgs/mglutil/hostappli/test_detection_video.py")
#general import
import sys,os
#get the current software
if __name__ == "__main__":
	soft = os.path.basename(sys.argv[0]).lower()
else : 
    soft = __name__

plugin=False

if not plugin : 
    #define the python path
    import math
    MGL_ROOT="/Library/MGLTools/1.5.6.csv/"#os.environ['MGL_ROOT']
    sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
    sys.path.append(MGL_ROOT+'lib/python2.5/site-packages/PIL')
    sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
    #start epmv
    from Pmv.hostappInterface.epmvAdaptor import epmv_start
    epmv = epmv_start(soft,debug=1)
else :
    #get epmv and mv (adaptor and molecular viewer)
    if sotf == 'c4d':
        import c4d
        epmv = c4d.mv.values()[0]#[dname]
self = epmv.mv
#from Pmv import hostappInterface
#plgDir = hostappInterface.__path__[0]
#from Pmv.hostappInterface import comput_util as util

import sys,os
MGL_ROOT=os.environ['MGL_ROOT']
sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
sys.path.append(MGL_ROOT+'lib/python2.5/site-packages/PIL')
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
import numpy
from numpy import oldnumeric as Numeric
import PyARTK
from PyARTK import video,arparamlib,arlib,utils,glutils
import Image
import Tkinter
import ImageTk
import Blender
from Blender import *
from Blender import Window, Scene, Draw
import time

global debug
debug = True

class video_tk:
  """ video example: display the video image in a Tkinter windows """

  def __init__(self,tk=True,trackedObj=None):
    import sys,os
    import numpy
    from numpy import oldnumeric as Numeric
    import PyARTK
    from PyARTK import video,arparamlib,arlib,utils,glutils
    import Image
    import Tkinter
    import ImageTk
    self.matrix=None
    self.trackedObj=trackedObj
	
    self.data_path = os.path.join(PyARTK.__path__[0],'Tests','data')
    camera_param = os.path.join(self.data_path,"LogitechPro4000.dat")
    patt_name = os.path.join(self.data_path,"kanjiPatt")

    # initialize the video feed
    self.videoApp = video.VideoForARTK(width=640,height=480)
    self.videoApp.init_video_device()
    self.videoApp.start()
    self.width = self.videoApp.cam.width
    self.height = self.videoApp.cam.height

    if self.videoApp.cam.pixelsize == 3:
      self.pixel_format = 'RGB'
      self.depth = 24
    else:
      self.pixel_format = 'RGBA'
      self.depth = 32
    # pattern data
    self.thresh = 100
    self.patt_width = 80.0
    self.patt_center = Numeric.array([0.0,0.0],'d')
    self.patt_trans = Numeric.zeros((3,4),'d')
    self.patt_prev  = Numeric.zeros((3,4),'d')

    # initialise tracking
    self.mode =1 # 1:Continuous mode: Using arGetTransMatCont
                     # 0: One shot mode: Using arGetTransMat.
    # create ARParam structure
    self.wparam = arparamlib.ARParam()
    self.cparam = arparamlib.ARParam()
    # set the initial camera parameters
    status = arparamlib.arParamLoad(camera_param, 1, self.wparam,0)
    if status < 0 :
            raise RuntimeError("Camera parameter load error !!")
            return
    status = arparamlib.arParamChangeSize( self.wparam,
                                               self.width,
                                               self.height,
                                               self.cparam)
    if status < 0 :
            raise RuntimeError("arParamChangeSize failed !!")
            return
    status = arlib.arInitCparam(self.cparam)
    if status < 0 :
            raise RuntimeError("arInitCparam  failed !!")
            return
        
    if debug:
            print "-- Camera Parameter --"
            arparamlib.arParamDisp(self.cparam)
    near=0.1
    far=5000.0
    #projection matrix depending on video camera
    self.m_projection = Numeric.zeros((16,),'d')
    glutils.arglCameraFrustumRH(self.cparam,near,far,self.m_projection)
    if debug:
            print "-- Camera Projection Matrix --"
	    print self.m_projection
    

    # load pattern data 
    id = arlib.arLoadPatt(patt_name)
    if id == -1:
            print " pattern load error "
            sys.exit(0)
    else: self.patt_id = id

    # init Tkinter Display
    self.tk=None
    if tk :
       self.tk=Tkinter.Tk()
       self.tk.protocol("WM_DELETE_WINDOW", self.exit_cb)
       self.photo = ImageTk.PhotoImage(self.pixel_format,(self.width,self.height))
       label= Tkinter.Label(self.tk,text="videoCamera",image=self.photo,
                         width=self.width,height=self.height)
       label.pack()
    else :
	self.photo=Blender.Image.New("videoCamera", self.width, self.height, self.depth)
	self.photo.setFilename(self.data_path+'/tmp.png')
	self.photo.pack()
    self.run_now= True
    #self.mainloop()

  def exit_cb(self):
    self.run_now =  False
    self.videoApp.stop()
    self.videoApp.arVideoClose()
    if self.tk != None : self.tk.destroy()
    
  def mainloop(self):
        import sys,os
        import numpy
        from numpy import oldnumeric as Numeric
        import PyARTK
        from PyARTK import video,arparamlib,arlib,utils,glutils
        import Image
        import Tkinter
        import ImageTk
        from Blender import Mathutils
    #try:
     
        self.videoApp.lock.acquire()        # detect the markers in the video frame
        if sys.platform == 'darwin':
          im_array = utils.convert_ARGB_RGBA(self.videoApp.cam.im_array)
        else:
          im_array = self.videoApp.cam.im_array

        marker_info  = arlib.arDetectMarker(im_array,self.thresh)
        marker_num = len(marker_info)
        
        # check for object visibility
        k = -1;
        for j in range(marker_num):
            if( self.patt_id == marker_info[j].id ):
                if( k == -1 ):k = j
                elif( marker_info[k].cf < marker_info[j].cf ): k = j
        
        
        if( k > -1 ):
            conf = marker_info[k].cf
	    sys.stdout.write("-- Detected Marker --")
	    sys.stderr.write("-- Detected Marker --")
            print "-- Detected Marker --"
            print " Marker id = %d conf= %d\n "%(marker_info[k].id,int(conf*100.0))
	    sys.stderr.write(" Marker id = %d conf= %d\n "%(marker_info[k].id,int(conf*100.0)))
            # get the transformation between the marker and the real camera */
            if(self.mode == 0):
                arlib.arGetTransMat(marker_info[k], self.patt_center,
                                    self.patt_width, self.patt_trans)
            else:
                arlib.arGetTransMatCont(marker_info[k], self.patt_prev,
                                        self.patt_center, self.patt_width,
                                        self.patt_trans)
                # save as for averaging
                self.patt_prev = Numeric.array(self.patt_trans,copy=1)
      
        m_modelview = Numeric.zeros(16,'d')
        scale = 1.0
        glutils.arglCameraView(self.patt_trans,m_modelview,scale)
        print "-- Model View Matrix arglCameraView --"
        for i in range(4):
            i = i *4
            print "%.2f %.2f %.2f %.2f"%(m_modelview[i],
                                         m_modelview[i+1],
                                         m_modelview[i+2],
                                         m_modelview[i+3])
        print ''
        print "-- Model View Matrix arglCameraViewRH --"     
        m_modelview_rh = Numeric.zeros(16,'d')
        glutils.arglCameraViewRH(self.patt_trans,m_modelview_rh,scale)
        for i in range(4):
            i = i *4
            print "%.2f %.2f %.2f %.2f"%(m_modelview_rh[i],
                                         m_modelview_rh[i+1],
                                         m_modelview_rh[i+2],
                                         m_modelview_rh[i+3])
	    sys.stderr.write("%.2f %.2f %.2f %.2f"%(m_modelview_rh[i],
                                         m_modelview_rh[i+1],
                                         m_modelview_rh[i+2],
                                         m_modelview_rh[i+3]))
	    sys.stdout.write("%.2f %.2f %.2f %.2f"%(m_modelview_rh[i],
                                         m_modelview_rh[i+1],
                                         m_modelview_rh[i+2],
                                         m_modelview_rh[i+3]))
	self.matrix=m_modelview
        if self.tk != None : 
            im = Image.fromstring(self.pixel_format,(self.width,self.height),im_array.tostring())
            self.videoApp.lock.release()
            #update Tk label
            self.photo.paste(im)
            self.tk.update()
	else :
	    im = Image.fromstring(self.pixel_format,(self.width,self.height),im_array.tostring())
	    self.videoApp.lock.release()
	    im.save(self.data_path+'/tmp.png')
	    #data=im.getdata()
	    #for y in range(self.height-1):
	    #    ind=(self.height-1)+y
	    #    for x in range(self.width-1):
	    #        r,g,b=data[x+ind]
	    #        self.photo.setPixelI(x, y, (int(r), int(g), int(b), 255)) 
	    self.photo.reload()

	if self.trackedObj != None :
		#self.matrix[14]=self.matrix[14]/10.0
		mat=self.matrix.reshape(4,4)
		self.trackedObj.setMatrix(Mathutils.Matrix(mat[0],mat[1],mat[2],mat[3]))

	sys.stderr.write('i am in the loop\n')
	sys.stderr.flush()
	sys.stdout.flush()
	#Blender.Redraw()
	#Window.RedrawAll()
	#Draw.Redraw(1)
	#ime.sleep(5)
    #except :#kinter.TclError:
    #  self.videoApp.stop()
    #  self.videoApp.arVideoClose()
    #  pass
  
def mainloop(vid,lock):
    count = 0	
    while 1:  
	#lock.acquire()
        exec('print "exec mainloop"\nvid.mainloop()\n')
	count = count + 1
	#lock.reease()
  
import Blender
import bpy
from Blender import *
from Blender.Mathutils import *
from Blender import Object
from Blender import Material
from Blender import Mathutils

#if __name__ == '__main__':
sc=Blender.Scene.GetCurrent()
sphere=Mesh.Primitives.UVsphere(10,10,50.)
mesho=sc.objects.new(sphere,'Mesh')
#import sys
#pmvstderr=open('pmvstderr','w')
#sys.stderr=pmvstderr
from Blender import Camera
cam = Camera.New('persp')
ob = sc.objects.new(cam)
sc.setCurrentCamera(ob)
import math
ob.RotX=math.pi
vid = video_tk(tk=False,trackedObj=mesho)
import thread 
lock=thread.allocate_lock()
t=thread.start_new_thread(mainloop,(vid,lock))
#print "thread start"
 #i=0
 #while i < 1000:
    #print vid.matrix
 #   print i
 #   i=i+1
 
#run test_detection_video
#im_array = vid.videoApp.cam.im_array
#import Image as I
#im = I.fromstring(vid.pixel_format,(vid.width,vid.height),im_array.tostring())
#data=list(im.getdata())
#for y in range(vid.height-1):
#    ind=(vid.height-1)+y
#    for x in range(vid.width-1):#
#	r,g,b=data[x+ind]
#	vid.photo.setPixelI(x, y, (int(r), int(g), int(b), 255)) 


