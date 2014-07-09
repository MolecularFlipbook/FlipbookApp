## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Nov 2001 Authors: Michel Sanner, Daniel Stoffler
#
#    sanner@scripps.edu
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler and TSRI
#
#########################################################################

import Tkinter
import numpy.oldnumeric as Numeric
import Image, ImageTk
import types
import math

from NetworkEditor.items import NetworkNode
from Vision import UserLibBuild


class ImageFromArray(NetworkNode):
    """based on the Image.open function. Reads an image file
Input:  filename (string)
Output: Image"""
    
    def __init__(self, name='Image from array', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        code = """def doit(self, array, width, height, normalize, linkRGB): 
    lennar = len(array)
    if lennar != width * height:
        import warnings
        print ("Image from array: width * height must be equal to len(array)")
        return
    if hasattr(array[0], '__len__') is False or len(array[0]) == 1:
        lenarray = 1
    elif len(array[0]) == 3:
        lenarray = 3
    elif len(array[0]) == 4:
        lenarray = 4
        
    nar = Numeric.array(array)
    narOriginalShape = nar.shape
    nar.shape = (width*height*lenarray,)

    if isinstance(nar[0], types.FloatType):

        if normalize == 1:
            nar.shape = narOriginalShape
            if lenarray == 1:
                mininar = min(nar)
                maxinar = max(nar)
                ecartnar = maxinar - mininar
                if ecartnar > 0:
                    for i in range(lennar):
                        nar[i] = (nar[i] - mininar) / ecartnar
            else:
                narChannel = range(lennar)
                mininar = [0,0,0,0]
                maxinar = [0,0,0,0]
                for j in range(lenarray):
                    for i in range(lennar):
                        narChannel[i] = nar[i][j]
                    mininar[j] = min(narChannel)
                    maxinar[j] = max(narChannel)

                if linkRGB == 1:
                    mininarGlobal = min(mininar[0], mininar[1], mininar[2])
                    mininar[0] = mininarGlobal
                    mininar[1] = mininarGlobal
                    mininar[2] = mininarGlobal
                    maxinarGlobal = max(maxinar[0], maxinar[1], maxinar[2])
                    maxinar[0] = maxinarGlobal
                    maxinar[1] = maxinarGlobal
                    maxinar[2] = maxinarGlobal

                for j in range(lenarray):
                    ecartnar = maxinar[j] - mininar[j]
                    if ecartnar > 0:
                        for i in range(lennar):
                            nar[i][j] = (nar[i][j] - mininar[j]) / ecartnar

        nar.shape = (width*height*lenarray,)
        for i in range(len(nar)):
            nar[i] = int(math.floor( 255.999 * nar[i] ))
    nar = nar.astype(Numeric.UnsignedInt8)
    
    import Image
    if lenarray == 1:
        im = Image.fromstring('L', (width, height), nar.tostring()) 
    elif lenarray == 3:
        im = Image.fromstring('RGB', (width, height), nar.tostring()) 
    elif lenarray == 4:
        im = Image.fromstring('RGBA', (width, height), nar.tostring()) 
    if im:
        self.outputData(image=im)
"""

        self.setFunction(code)

        self.inputPortsDescr.append(datatype='list', name='array')
        self.inputPortsDescr.append(datatype='int', name='width')
        self.inputPortsDescr.append(datatype='int', name='height')
        self.inputPortsDescr.append(datatype='boolean', name='normalize')
        self.inputPortsDescr.append(datatype='boolean', name='linkRGB')
        self.outputPortsDescr.append(datatype='image', name='image')

        self.widgetDescr['normalize'] = {
            'class':'NECheckButton',
            'master':'node',
            'initialValue':False,
            'labelGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'normalize floats'},
            }

        self.widgetDescr['linkRGB'] = {
            'class':'NECheckButton',
            'master':'node',
            'initialValue':True,
            'labelGridCfg':{'sticky':'we'},
            'labelCfg':{'text':'link RGB normalization'},
            }



class ReadImage(NetworkNode):
    """based on the Image.open function. Reads an image file
Input:  filename (string)
Output: Image"""
    
    def __init__(self, name='Read Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
        self.inNodeWidgetsVisibleByDefault = True

        #self.readOnly = 1
        code = """def doit(self, filename):
    if filename:
        import Image
        im = Image.open(filename)
        if im:
            self.outputData(image=im)\n"""

        self.setFunction(code)

        fileTypes = [('all', '*'), ('jpeg', '*.jpg'), ('tiff', '*.tif'),
                     ('png', '*.png'), ('bmp', '*.bmp')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'read image', 'width':10,
                    'labelCfg':{'text':'image file:'} }

        self.inputPortsDescr.append(datatype='str', name='filename')
        self.outputPortsDescr.append(datatype='image', name='image')


class SaveImage(NetworkNode):
    """saves an image."""
    
    def __init__(self, name='Save Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
        #self.readOnly = 1
        code = """def doit(self, image, filename):
    if filename:
        image.save(filename)\n"""

        self.setFunction(code)

        fileTypes = [('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node',
            'filetypes':fileTypes, 'title':'save image', 'width':10,
            'labelCfg':{'text':'image file:'} }

        self.inputPortsDescr.append(datatype='image', name='image')
        self.inputPortsDescr.append(datatype='str', name='filename')


class GetFrontBuffer(NetworkNode):
    """Extract front buffer image of camera 0 of DejaVu Viewer"""
    
    def getFrontBuffer(self, width, height):
        from opengltk.OpenGL import GL
        #import bufarray
        #bar = bufarray.Bufarray(3*width*height, bufarray.ubyteCtype)
        #GL.glReadPixels( 0, 0, width, height, GL.GL_RGB, bar)

        bar = GL.glReadPixels( 0, 0, width, height, GL.GL_RGB, GL_GL_UBYTE)
        im = Image.fromstring('RGB', (width,height), bar)
        #FIXME we have to destroy bar .. but how ?

        # for some reason refount is 2
        #import sys
        #print sys.getrefcount(bar)
        del bar
        return im.transpose(Image.FLIP_TOP_BOTTOM)


    def __init__(self, name='Front Buffer', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='viewer', name='viewer')
        ip.append(datatype='int', required=False, name='cameraNum')

	self.outputPortsDescr.append(datatype='image', name='image')
        

        code = """def doit(self, viewer, cameraNum):
    if cameraNum is None:
        cameraNum=0
    camera = viewer.cameras[cameraNum]
    camera.Activate()
    #width = divmod(camera.width, 4)[0]*4
    #height = divmod(camera.height, 4)[0]*4
    self.outputData(image = camera.GrabFrontBuffer() )
"""

        self.setFunction(code)

    def beforeAddingToNetwork(self, net):
        try:
            ed = net.getEditor()
            from DejaVu.VisionInterface.DejaVuNodes import vizlib
            ed.addLibraryInstance(vizlib,
                                  'DejaVu.VisionInterface.DejaVuNodes',
                                  'vizlib')
        except:
            import traceback
            traceback.print_exc()
            print 'Warning! Could not import vizlib from DejaVu/VisionInterface'


class GetZBuffer(NetworkNode):
    """Extract front buffer image of camera 0 of DejaVu Viewer"""
    
    def getZBuffer(self, width, height):
        from opengltk.OpenGL import GL
        depthString = GL.glReadPixels( 0, 0, width, height,
                                       GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT)
        import struct
        zval = Numeric.array(struct.unpack('%df'%width*height, depthString))
        zmax = max(zval)
        zmin = min(zval)
        zval1 = 255 * ((zval-zmin) / (zmax-zmin))
        ds = zval1.astype('c').tostring()
        depthImage = Image.fromstring('P', (width, height), ds)

        return depthImage.transpose(Image.FLIP_TOP_BOTTOM)


    def __init__(self, name='Z Buffer', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='viewer', name='viewer')
        ip.append(datatype='int', required=False, name='cameraNum')

	self.outputPortsDescr.append(datatype='image', name='image')

        code = """def doit(self, viewer, cameraNum):
    if cameraNum is None:
        cameraNum=0
    camera = viewer.cameras[cameraNum]
    camera.Activate()
    #width = divmod(camera.width, 4)[0]*4
    #height = divmod(camera.height, 4)[0]*4
    self.outputData(image = camera.GrabZBuffer() )
"""

        self.setFunction(code)

    def beforeAddingToNetwork(self, net):
        try:
            ed = net.getEditor()
            from DejaVu.VisionInterface.DejaVuNodes import vizlib
            ed.addLibraryInstance(vizlib,
                                  'DejaVu.VisionInterface.DejaVuNodes',
                                  'vizlib')
        except:
            import traceback
            traceback.print_exc()
            print 'Warning! Could not import vizlib from DejaVu/VisionInterface'


class ToRGB(NetworkNode):
    """converts an Image to RGB"""

    def __init__(self, name='To RGB', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.inputPortsDescr.append(datatype='image', name='image')

        self.outputPortsDescr.append(datatype='image', name='RGBimage')
        
        code = """def doit(self, image):
    if image.mode!='RGB':
        image.draft('RGB', image.size)
        image = image.convert('RGB')
    self.outputData(RGBimage=image)\n"""

        self.setFunction(code)


class ResizeImage(NetworkNode):
    """Resize image using scaling factor supplied by dial. The filter argument
    can be NEAREST, BILINEAR, or BICUBIC. If omitted, it defaults to NEAREST.
    """
    
    def __init__(self, name='Resize', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
        self.inNodeWidgetsVisibleByDefault = True

        code = """def doit(self, image, scale, filter):
    import Image
    w,h = image.size
    if filter is not None and filter != '':
        op = eval('Image.'+filter)
        result = image.resize( (w*scale, h*scale), op )
    else:
        result = image.resize( (w*scale, h*scale) )
    
    self.outputData( scaledImage=result )\n"""

        if code: self.setFunction(code)

        self.widgetDescr['scale'] = {
            'class': 'NEThumbWheel', 'master':'node', 'width':75, 'height':28,
            'type': 'float', 'oneTurn': 1.0, 'min':0.01,
            'initialValue':1.0, 
            'labelCfg':{'text':'Scale'},
            }

        filters = ['NEAREST','BILINEAR','BICUBIC' ]
        self.widgetDescr['filter'] = {
            'class':'NEComboBox', 
            'choices':filters,
            'fixedChoices':True,
            'initialValue':'NEAREST',
            'entryfield_entry_width':12,
            'labelCfg':{'text':'filter'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        
        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image')
        ip.append(datatype='float', name='scale')
        ip.append(datatype='string', name='filter')

        op = self.outputPortsDescr
        op.append(datatype='image', name='scaledImage')


class ImageFilter(NetworkNode):
    """Apply different filters to an image"""

    def __init__(self, name='Filter Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        filters = ['BLUR', 'CONTOUR', 'DETAIL', 'EDGE_ENHANCE',
                   'EDGE_ENHANCE_MORE', 'EMBOSS', 'FIND_EDGES',
                   'SMOOTH', 'SMOOTH_MORE', 'SHARPEN' ]

        self.widgetDescr['filter'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':filters,
            'fixedChoices':True,
            'entryfield_entry_width':14,
            'labelCfg':{'text':'filter:'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image')
        ip.append(datatype='None', name='filter')

        self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image, filter):
    import ImageFilter
    if filter is not '' and image:
        op = eval('ImageFilter.'+filter)
        self.outputData(image= image.filter(op))\n"""

        self.setFunction(code)


class ImageInvert(NetworkNode):
    """Inverts an image."""

    def __init__(self, name='Invert Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.inputPortsDescr.append(datatype='image', name='image')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image):
    import ImageChops
    self.outputData(image = ImageChops.invert(image))\n"""

        self.setFunction(code)


class ImageMultiply(NetworkNode):
    """Superimposes two images on top of each other. If you multiply an
image with a solid black image, the result is black. If you multiply with
a solid white image, the image is unaffected."""
    
    def __init__(self, name='Multiply Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image1')
        ip.append(datatype='image', name='image2')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image1, image2):
    import ImageChops
    self.outputData(image = ImageChops.multiply(image1, image2))\n"""

        self.setFunction(code)


class ImageSplit(NetworkNode):
    """Apply different filters to an image"""

    def __init__(self, name='Split Image', **kw):
        apply( NetworkNode.__init__, (self,), kw)

        self.inputPortsDescr.append(datatype='image', name='image')

        op = self.outputPortsDescr
        op.append(datatype='None', name='r')
	op.append(datatype='None', name='g')
	op.append(datatype='None', name='b')
        
        code = """def doit(self, image):
    r,g,b = image.split()
    self.outputData(r=r, g=g, b=b)\n"""

        self.setFunction(code)


class AlphaMask(NetworkNode):
    """
    Build a mask for an image based ona  threshold value.
    The mask will have 0 values for evry pixel with intensity below the
    threshold value. THis mask can be used as the third input of a composite
    node for instance to blend 2 images only where the mask is not 0.
    """

    def __init__(self, name='Alpha Mask', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['threshold'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'labelCfg':{'text':'threshold'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image')
        ip.append(datatype='image', name='threshold')

	self.outputPortsDescr.append(datatype='None', name='mask')

        code = """def doit(self, image, threshold):
    l = lambda x,cutOff=threshold: (x > cutOff)*255
    mask = image.point( l )
    self.outputData(mask=mask)\n"""

        self.setFunction(code)


class ImagePaste(NetworkNode):
    """Apply different filters to an image"""

    def __init__(self, name='Invert Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image1')
        ip.append(datatype='image', name='image2')
        ip.append(datatype='None', name='mask')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image1, image2, mask):
    image1.paste(image2, None, mask)
    self.outputData(image=image1)\n"""

        self.setFunction(code)
        

class ShowImage(NetworkNode):
    """Display an image file as a Tkinter.Photoimage in  a canvas.

Double-click the on the node icon to show/hide the canvas.

Input:  Image"""
    
    def __init__(self, name='Show Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        #self.readOnly = 1
        self.top = None       # will be created after adding to network
        self.imCanvas = None  # will be created after adding to network
        self.canvasImage = None

        self.isWithdrawn = None  # flag to toggle show/hide canvas
        # double-click on node to show/hide canvas
        self.mouseAction['<Double-Button-1>'] = self.show_hide
        
        code = """def doit(self, image):
    if image:
        if self.canvasImage: self.imCanvas.delete(self.canvasImage)
        import ImageTk
        self.imtk = ImageTk.PhotoImage(image, master=self.top)
        self.canvasImage = self.imCanvas.create_image(
                        0, 0, image=self.imtk, anchor='nw')
        self.imCanvas.configure(width=self.imtk.width(),
                              height=self.imtk.height())
        self.imCanvas.pack()\n"""

        self.setFunction(code)

        self.inputPortsDescr.append(datatype='image', name='image')


    def afterRemovingFromNetwork(self):
        NetworkNode.afterRemovingFromNetwork(self)
        if self.top:
            self.top.destroy()


    def afterAddingToNetwork(self):
        self.top = Tkinter.Toplevel()
        self.imCanvas = Tkinter.Canvas(self.top)
        self.top.protocol('WM_DELETE_WINDOW', self.show_hide)
        self.isWithdrawn = 0


    def show_hide(self, event=None):
        if self.isWithdrawn:
            self.top.deiconify()
            self.isWithdrawn = 0
        else:
            self.top.withdraw()
            self.isWithdrawn = 1


class ImageBlend(NetworkNode):
    """Creates a new image by interpolating between the given images,
using a constant alpha. Both images must have the same size and mode.
If alpha is 0.0, a copy of the first image is returned. If alpha is 1.0,
a copy of the second image is returned. There are no restrictions on the
alpha value. If necessary, the result is clipped to fit into the allowed
output range."""

    def __init__(self, name='Invert Image', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['alpha'] = {
            'class': 'NEDial', 'master':'node', 'size':50,
            'type':'float', 'min':0,
            'lockMin':1, 'lockBMin':1, 'lockType':1, 'max':1.0,
            'lockMax':1, 'lockBMax':1, 'oneTurn':0.1,
            'initialValue':0.5,
            'labelCfg':{'text':'alpha'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        
        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image1')
        ip.append(datatype='image', name='image2')
        ip.append(datatype='float', name='alpha')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image1, image2, alpha):
    import Image
    result = Image.blend(image1, image2, alpha)
    self.outputData(image=result)\n"""

        self.setFunction(code)
    
 
class ImageRotate(NetworkNode):
    """Returns a copy of an image rotated the given number of degrees counter
clockwise around its centre. The filter argument can be NEAREST, BILINEAR,
or BICUBIC. If omitted, it defaults to NEAREST. """

    def __init__(self, name='Rotate', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['angle'] = {
            'class': 'NEThumbWheel', 'master':'node', 'width':75, 'height':28,
            'type':'float','initialValue':0.0,
            'labelCfg':{'text':'angle'},
            }

        filters = ['NEAREST','BILINEAR','BICUBIC' ]
        self.widgetDescr['filter'] = {
            'class':'NEComboBox', 
            'choices':filters,
            'fixedChoices':True,
            'initialValue':'NEAREST',
            'entryfield_entry_width':12,
            'labelCfg':{'text':'filter'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        
        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image')
        ip.append(datatype='float', name='angle')
        ip.append(datatype='string', name='filter')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image, angle, filter):
    if filter is not None and filter != '':
        import Image
        op = eval('Image.'+filter)
        result = image.rotate(angle, op)
    else:
        result = image.rotate(angle)
    self.outputData(image=result)\n"""

        self.setFunction(code)
        

class ImageTranspose(NetworkNode):
    """Returns a flipped or rotated copy of an image.  Method can be one of
    the following: FLIP_LEFT_RIGHT, FLIP_TOP_BOTTOM, ROTATE_90, ROTATE_180,
    or ROTATE_270."""

    def __init__(self, name='Transpose', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        methods = ['FLIP_LEFT_RIGHT','FLIP_TOP_BOTTOM','ROTATE_90',
                   'ROTATE_180', 'ROTATE_270']
        self.widgetDescr['method'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':methods,
            'fixedChoices':True,
            'entryfield_entry_width':14,
            'labelCfg':{'text':'methods:'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image')
        ip.append(datatype='string', name='method')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image, method):
    if method is not None and method != '':
        import Image
        op = eval('Image.'+method)
        result = image.transpose(op)
    else:
        result = image
    self.outputData(image=result)\n"""

        self.setFunction(code)


class ImageComposite(NetworkNode):
    """Creates a new image by interpolating between the given images, using
the mask as alpha. The mask can be either 1, L, or RGBA. All images must have
the same size."""

    def __init__(self, name='Composite', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image1')
        ip.append(datatype='image', name='image2')
        ip.append(datatype='image', name='mask')

	self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, image1, image2, mask):
    import Image
    result = Image.composite(image1, image2, mask)
    self.outputData(image=result)\n"""

        self.setFunction(code)


class ImageStat(NetworkNode):
    """This node calculates global statistics for an image, or a region of an
image. If a mask is included, only the  regions covered by that mask are
included in the statistics."""

    def __init__(self, name='Image Stat', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        stats = ['extrema','count','sum','sum2','mean','median','rms','var',
                 'stddev']

        self.widgetDescr['stat'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':stats,
            'fixedChoices':True,
            'entryfield_entry_width':7,
            'labelCfg':{'text':'methods:'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='image', name='image')
        #ip.append(datatype='image', required=False, name='mask')
        ip.append(datatype='string', required=False, name='stat')

	self.outputPortsDescr.append(datatype='None', name='stats')
        
        code = """def doit(self, image, stat):
    if stat is not None and stat != '':
        import ImageStat
        data = ImageStat.Stat(image)
        result = eval('data.'+stat)
        self.outputData(stats=result)\n"""

        self.setFunction(code)

 

try:
    import pymedia.video.vcodec as vcodec
    

    class RecordMPEGmovie(NetworkNode):
        """
        Create an MPEG movie from a sequence of images

        Input:
            image: image to be added to the movie (PIL Image)
            movieFileName: filename of the mpeg movie (string)
            op.append(datatype='boolean',
                      balloon='sends "True" when iterate starts to iterate',
                      name='begin')
            op.append(datatype='boolean',
                      balloon='output "True" when loop is over', name='end')

        Output:
            movieFileName: name of the created movie (string)
            nbFrames: number of recorded frames
        """

        def initMPEG(self, filename, width, height, codec):
            """
            initialize MPEG capture

            bool <- initMPEG(filename, width, height):

            filename is hte name of the MPEG file
            width is the width of a frame in pixel
            height is the height of a frame in pixel
            """
            self.videoOutputFile = open( filename, 'wb' )
            assert self.videoOutputFile, 'ERROR, failed to open file: '+filename

            if width is None:
                width = self.width
            w = self.videoFrameWidth = width - width%2

            if height is None:
                height = self.height
            h = self.videoFrameHeight = height - height%2

            if codec=='mpeg2':
                params= { 'type': 0, 'gop_size': 12, 'frame_rate_base': 125,
                          'max_b_frames': 0, 'width': w, 'height': h,
                          'frame_rate': 2997,'deinterlace': 0,
                          'bitrate': 9800000,
                          'id': vcodec.getCodecID( 'mpeg2video' )
                          }
            else: # default is mpeg1
                params= { 'type': 0, 'gop_size': 12, 'frame_rate_base': 125,
                          'max_b_frames': 0, 'width': w, 'height': h,
                          'frame_rate': 2997,'deinterlace': 0,
                          'bitrate': 2700000,
                          'id': vcodec.getCodecID( 'mpeg1video' )
                          }
            self.encoder = vcodec.Encoder( params )
            self.nbFrames = 0


        def __init__(self, name='Record MPEG movie', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw)
            self.inNodeWidgetsVisibleByDefault = True

            fileTypes = [('all', '*'), ('mpg', '*.mpg'), ('mpeg', '*.mpeg')]

            ip = self.inputPortsDescr
            ip.append(datatype='image',
                      balloon='PIL image to be added to the movie',
                      name='image')
            ip.append(datatype='str',
                      balloon='name og hte file in whichthe MPEG is saved',
                      name='movieFileName')
            ip.append(datatype='boolean',
                      balloon='expects True on the first Frame',
                      name='begin')
            ip.append(datatype='boolean',
                      balloon='expects True on the last Frame',
                      name='end')
            ip.append(datatype='string',
                      balloon='can be mpeg1 or mpeg2',
                      name='codec')

            self.widgetDescr['movieFileName'] = {
                'class':'NEEntryWithFileSaver', 'master':'node',
                'initialValue':'movie.mpeg',
                'filetypes':fileTypes, 'title':'Browse file name', 'width':10,
                'labelCfg':{'text':'MPEG file name:'} }

            self.widgetDescr['codec'] = {
                'class':'NEComboBox', 'master':'node',
                'choices':['mpeg1', 'mpeg2'],
                'initialValue':'mpeg1',
                'fixedChoices':True,
                'entryfield_entry_width':7,
                'labelCfg':{'text':'codec:'},
            }

            op = self.outputPortsDescr
            op.append(datatype='string', name='movieFileName')
            op.append(datatype='int', name='nbFrames')

            code = """def doit(self, image, filename, start, end, codec):

        if start: # open the MPEG file
            width, height = image.size
            status = self.initMPEG(filename, width, height, codec)
            if not status:
                return 'Stop'
                
        # add the image as a frame
        if hasattr(self, 'videoOutputFile'):
        
            bmpFrame = vcodec.VFrame(
                vcodec.formats.PIX_FMT_RGB24, image.size,
                (image.tostring(), None, None))
            yuvFrame = bmpFrame.convert(vcodec.formats.PIX_FMT_YUV420P)
            self.videoOutputFile.write(self.encoder.encode(yuvFrame).data)
            self.nbFrames += 1

            if end: # close the MPEG file
                self.videoOutputFile.close()
                del self.videoOutputFile
            self.outputData(movieFileName=filename, nbFrames=self.nbFrames)\n"""
                
            self.setFunction(code)

    class PlayMPEG(NetworkNode):

        def __init__(self, name='PlayMPEG', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw)
            self.inNodeWidgetsVisibleByDefault = True

            code = """def doit(self, movieFileName, MPEGplayerPgm):
    import os, sys
    if os.name == 'nt':
        cmd='''\"C:\Program Files\Windows Media Player\wmplayer.exe\" /prefetch:1 %s'''%movieFileName
    elif os.name == 'posix' and sys.platform=='darwin':
        cmd = '''/Applications/VLC.app/Contents/MacOS/VLC %s &'''%movieFileName
    else:
        cmd = "%s %s"%(MPEGplayerPgm, movieFileName)
    os.system(cmd)\n"""
            self.configure(function=code)

            ip = self.inputPortsDescr
            ip.append( {'name': 'movieFileName', 'datatype': 'string'})
            ip.append( {'name': 'MPEGplayerPgm', 'datatype': 'string'})
            
            self.widgetDescr['movieFileName'] = {
                'initialValue': '',
                'labelGridCfg': {'column': 0, 'row': 0},
                'master': 'node',
                'widgetGridCfg': {'labelSide': 'left'},#, 'column': 1, 'row': 0},
                'labelCfg': {'text': 'movie File'},
                'class': 'NEEntryWithFileBrowser'}

            self.widgetDescr['MPEGplayerPgm'] = {
                'initialValue': 'default',
                'labelGridCfg': {'column': 0, 'row': 0},
                'master': 'node',
                'widgetGridCfg': {'labelSide': 'left'},#, 'column': 1, 'row': 1},
                'labelCfg': {'text': 'MPEG player pgm'},
                'class': 'NEEntryWithFileBrowser'}


except ImportError:
    print 'Failed to import pymedia.video.vcodec'
    
from Vision.VPE import NodeLibrary
imagelib = NodeLibrary('Imaging', '#995699')

imagelib.addNode(ImageFromArray, 'Image from array', 'Input')
imagelib.addNode(ReadImage, 'Read Image', 'Input')
imagelib.addNode(GetFrontBuffer, 'Grab Image', 'Input')
#imagelib.addNode(GetZBuffer, 'RecordMPEGmovie', 'Input')

imagelib.addNode(ShowImage, 'Show Image', 'Output')
imagelib.addNode(ImageStat, 'Image Stat', 'Output')
imagelib.addNode(SaveImage, 'Save Image', 'Output')

try:
    import pymedia.video.vcodec as vcodec
    imagelib.addNode(RecordMPEGmovie, 'Record MPEG movie', 'Output')
    imagelib.addNode(PlayMPEG, 'Play MPEG', 'Output')
except ImportError:
    pass

imagelib.addNode(ToRGB, 'ToRGB', 'Filter')
imagelib.addNode(ImageFilter, 'Filter Image', 'Filter')
imagelib.addNode(ImageInvert, 'Invert Image', 'Filter')
imagelib.addNode(ImageSplit, 'Split Image', 'Filter')
imagelib.addNode(AlphaMask, 'Build Mask', 'Filter')
imagelib.addNode(ImagePaste, 'Paste Images', 'Filter')

imagelib.addNode(ResizeImage, 'Scale', 'Mapper')
imagelib.addNode(ImageBlend, 'Blend', 'Mapper')
imagelib.addNode(ImageMultiply, 'Multiply', 'Mapper')
imagelib.addNode(ImageComposite, 'Composite', 'Mapper')
imagelib.addNode(ImageRotate, 'Rotate', 'Mapper')
imagelib.addNode(ImageTranspose, 'Transpose', 'Mapper')


UserLibBuild.addTypes(imagelib, 'Vision.PILTypes')

try:
    UserLibBuild.addTypes(imagelib, 'DejaVu.VisionInterface.DejaVuTypes')
except:
    pass

