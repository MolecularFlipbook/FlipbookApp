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
## $Header: /opt/cvs/python/packages/share1.5/Pmv/hostappInterface/cinema4d/test/test_arvideo.py,v 1.1 2010/08/23 18:24:54 autin Exp $
## $Id: test_arvideo.py,v 1.1 2010/08/23 18:24:54 autin Exp $
##  
##
##
## This is a short test of the video
## it will display the video stream in a Tkinter windows 
##
import sys
#should use epmv and arviewer....like in chimera and probably in blender...

MGL_ROOT="/Library/MGLTools/1.5.6.csv/"
#sys.path[-1] = '/Library/Python/2.6/site-packages/PIL'

sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
sys.path.append(MGL_ROOT+'lib/python2.5/')
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
#sys.path.append(MGL_ROOT+'/lib/python2.5/site-packages/PIL')


from numpy import oldnumeric as Numeric
from PyARTK import video,arparamlib,arlib,utils
import Image
#import Tkinter
#import ImageTk
import c4d

class video_tk:
  """ video example: display the video image in a Tkinter windows """

  def __init__(self,texture):

    # initialize the video feed
    self.videoApp = video.VideoForARTK(width=640,height=480)
    self.videoApp.init_video_device()
    self.videoApp.start()
    self.width = self.videoApp.cam.width
    self.height = self.videoApp.cam.height

    if self.videoApp.cam.pixelsize == 3:
      self.pixel_format = 'RGB'
    else:
      self.pixel_format = 'RGBA'

    # init Tkinter Display
    #self.tk=Tkinter.Tk()
    #self.tk.protocol("WM_DELETE_WINDOW", self.exit_cb)
    self.photo = texture
    self.photo[1000] = '/tmp/tmp.png'
    #self.photo = c4d.BaseBitmap()#ImageTk.PhotoImage(self.pixel_format,(self.width,self.height))
    #self.photo.init(int(self.width),int(self.height),32)
    #label= Tkinter.Label(self.tk,text="videoCamera",image=self.photo,
    #                     width=self.width,height=self.height)
    #label.pack()
    
    self.run_now= True
    #self.mainloop()
    
  def arrayToBmp(self,array):
    for i in xrange(self.width):
        for j in range(self.height):
            rgba = array[i][j]
            px = c4d.Vector(int(rgba[0]),int(rgba[1]),int(rgba[2])) #int
            self.photo[i,j] = px
            
  def exit_cb(self):
    self.run_now =  False
    self.videoApp.stop()
    self.videoApp.arVideoClose()
    #self.tk.destroy()


  def mainloop(self):
    try :
        while self.run_now :
            self.doitonce()
    except :#Tkinter.TclError:
      self.videoApp.stop()
      self.videoApp.arVideoClose()
      pass
        
  def doitonce(self):
    self.videoApp.lock.acquire()
    import Image
    if sys.platform == 'darwin':
          im_array = utils.convert_ARGB_RGBA(self.videoApp.cam.im_array)
    else:
          im_array = self.videoApp.cam.im_array
    print len(im_array)      
    #im = Image.fromstring(self.pixel_format,(self.width,self.height),im_array.tostring())
    #im = im_array.reshape(self.width,self.height,self.videoApp.cam.pixelsize)
    #self.arrayToBmp(im)
    print "ImageFromString"
    im = Image.fromstring(self.pixel_format,(self.width,self.height),im_array.tostring())
    self.videoApp.lock.release()
    print "save"
    im.save('/tmp/tmp.png')
    #self.photo[1000] = '/tmp/tmp.png'
    print "up texture"
    #c4d.call_command(1023410)
    #self.videoApp.lock.release()
    # update Tk label
    #self.photo.paste(im)
    #self.tk.update()
    return True


if __name__ == '__main__':
  vid = video_tk()
#bmp = BaseBitmap()     # allocate an object of this type
#bmp.init(100, 100, 24) # initialize the bitmap
#bmp[1,2] = Vector(255, 0, 0)
