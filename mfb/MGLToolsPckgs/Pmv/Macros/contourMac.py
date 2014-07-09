## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

import Image
import ImageFilter
from opengltk.OpenGL import GL
import math
import numpy.oldnumeric as Numeric

class Outline:

    def __init__(self, camera):
        self.camera = camera

    def getDepthString(self):
        depthString = GL.glReadPixels( 0, 0, self.w, self.h,
                                       GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT)
        return depthString
    
    def getFrontBuffer(self):
        s = GL.glReadPixels( 0, 0, self.w, self.h, GL.GL_RGB,
                             GL.GL_UNSIGNED_BYTE, 3*self.w*self.h)
        im = Image.fromstring('RGB', (self.w,self.h), s) 
        return im

        
    def go(self, cutOff = 10, bw=1):
        self.w = divmod(self.camera.width, 4)[0]*4
        self.h = divmod(self.camera.height, 4)[0]*4
        self.cutOff = cutOff
        self.imOrig = self.getFrontBuffer()
        depthString = self.getDepthString()

        # convert to numeric array 

        # quick and dirty way .. use 3rd byte
        #self.depth = Numeric.array(depthString, 'c')[2::4].astype(Numeric.Int8)
        import struct
        zval = Numeric.array(struct.unpack('%df'%self.w*self.h, depthString))
        zmax = max(zval)
        zmin = min(zval)
        zval1 = 255 * ((zval-zmin) / (zmax-zmin))
        ds = zval1.astype('c').tostring()
        self.depthImage = Image.fromstring('P', (self.w,self.h), ds)

        # detect edges in depth image
        self.depthImage.draft("RGB", self.depthImage.size)
        self.depthImageRGB = self.depthImage.convert("RGB")
        self.depthedges = self.depthImageRGB.filter(ImageFilter.FIND_EDGES)

        # select regions contour (where pixel is not black)
        l = lambda i, cutOff=self.cutOff: (i > cutOff)*255
        self.mask = self.depthedges.split()[0].point( l )

        # make contour black or grey scale
        if bw: l = lambda i, cutOff=self.cutOff: (i<=cutOff)*255 and 255
        else: l = lambda i, cutOff=self.cutOff: (i<=cutOff)*255 and 255-i
        self.contour = self.depthedges.point( l )

        # composite original and contour
        self.imOrig.paste(self.contour, None, self.mask)
        self.finalImage = self.imOrig.transpose(Image.FLIP_TOP_BOTTOM)
        return self.finalImage


    def save(self, image, filename):
        import os
        if os.path.splitext(filename)[1] == '': filename = filename+'.ppm'
        image.save(filename)

        
    def _derivatives(self, x, y):
        if x==0 or x==self.w: return 0.
        if y==0 or y==self.h: return 0.
        A = self.dsq[x-1][y-1]
        B = self.dsq[x][y-1]
        C = self.dsq[x+1][y-1]
        D = self.dsq[x-1][y]
        E = self.dsq[x+1][y]
        F = self.dsq[x-1][y+1]
        G = self.dsq[x][y+1]
        H = self.dsq[x+1][y+1]
        first = ( math.fabs( A+2*B+C-F-2*G-H ) +
                  math.fabs( C+2*E+H-A-2*D-F ) ) / 8.
        second = math.fabs( 8*self.dsq[x][y]-A-B-C-D-E-F-G-H ) / 3.
        return first, second


    def derivatives(self):
        # make array of numbers
        depthString = self.getDepthString()
        self.depth = Numeric.array(depthString, 'c')[2::4].astype(Numeric.Int8)
        self.dsq = Numeric.reshape(self.depth, (self.w, self.h))
        self.fstD = Numeric.zeros((self.w, self.h), Numeric.Int8)
        self.sndD = Numeric.zeros((self.w, self.h), Numeric.Int8)
        self.deriv = Numeric.zeros((self.w, self.h), Numeric.Int8)

        for i in range(1, self.w-1):
            for j in range(1, self.h-1):
                a, b = self._derivatives(i,j)
                self.fstD[i][j] = a
                self.sndD[i][j] = b
                self.deriv[i][j] = max(a, b)
                
#        self.deriv = Numeric.choose( Numeric.greater(self.fstD,self.sndD),
#                                     (self.fstD,self.sndD) )

        self.fstDim = Image.fromstring('P', (self.w,self.h),
                                       self.fstD.tostring())

        self.sndDim = Image.fromstring('P', (self.w,self.h),
                                       self.sndD.tostring())
        
        self.derivim = Image.fromstring('P', (self.w,self.h),
                                        self.deriv.tostring() )

    def fill(self, cutOff):
        self.dsqs = Numeric.array(self.deriv)
        cut= cutOff*8
        for x in range(1, self.w-1):
            for y in range(1, self.h-1):
                if self.dsq[x][y]>0.: continue
                A = self.dsq[x-1][y-1]
                B = self.dsq[x][y-1]
                C = self.dsq[x+1][y-1]
                D = self.dsq[x-1][y]
                E = self.dsq[x+1][y]
                F = self.dsq[x-1][y+1]
                G = self.dsq[x][y+1]
                H = self.dsq[x+1][y+1]
                sum = A+B+C+D+E+F+G+H
                self.dsqs[x][y] = sum/8.
                
    def composeDerivatives(self, maskCutOff=5, bw=0):

        self.derivim.draft("RGB", self.derivim.size)
        self.derivimRGB = self.derivim.convert("RGB")

        # select regions fstD where pixel is not black
        l = lambda i, cut=maskCutOff: (i > cut)*255
        self.maskD = self.derivimRGB.split()[0].point( l )

        # make contour black or grey scale
        if bw: l = lambda i, cutOff=0: (i<=cutOff)*255 and 255
        else: l = lambda i,cutOff=0: (i<=cutOff)*255 and 255-i
        self.contourD = self.derivim.point( l )

        self.imOrig = self.getFrontBuffer()

        # composite original and contour
        self.imOrig.paste(self.contourD, None, self.maskD)
        self.finalImageD = self.imOrig.transpose(Image.FLIP_TOP_BOTTOM)
        return self.finalImageD


from PIL import ImageTk
import Tkinter
class imageViewer:
    def __init__(self, master=None, title='Image Viewer'):
        self.master = master
        if not master:
            self.master = Tkinter.Toplevel()
        #self.image = ImageTk.PhotoImage(image)
        self.lab = Tkinter.Label(self.master, bg="black", bd=0)
        self.lab.pack()

    def show(self, image):
        self.image = ImageTk.PhotoImage(image, master=self.master)
        self.lab.configure(image=self.image)
        self.lab.pack()
    

ivi = imageViewer()
outline = None

def getOutlinedImage():
    """Apply David Goodsell's alogrithm to generate dark outlines"""
    global outline
    vi = self.GUI.VIEWER
    vi.cameras[0].Set(color=(.7,.7,.7))
    vi.Redraw()
    outline = Outline(vi.cameras[0])
    im = outline.go()
    ivi.show(im)

def saveFinalImage():
    """save the resulting file in a file in the .ppm format"""
    file = self.askFileSave(types=[('PPM files', '.ppm')])
    outline.save(outline.finalImage, file)

