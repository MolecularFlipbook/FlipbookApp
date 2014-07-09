## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################
#       ImageMagick for Vision
#
#   Vision: http://www.scripps.edu/~sanner/python/vision/
#   ImageMagick: http://www.imagemagick.org
#   PythonMagick: http://sourceforge.net/projects/pylab
#
#   Author: Natalie Rubin (nmrubin@sdsc.edu)
#   Based on the PIL nodes included with Vision
############################################################

from NetworkEditor.items import NetworkNode
from magick import *

### Convert list of imimages to a sequence ###
def toSeq(imgList):
    args = "image("
    for i in range(len(imgList)):
        args = args + "imgList[" + str(i) + "], "
    args = args + ")"
    result = eval(args)    
    return result


### Input/Output ###
class Read(NetworkNode):
    """Reads an image from a file.
    
    File Name: the file to be read. Double click for file browser."""

    def __init__(self, name='Read', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, filename):
        if filename and filename != 'File Name':
            result = image(filename)
            if result:
                self.outputData(outImage=result)\n"""

        self.setFunction(code)

        fileTypes = [('all', '*')]
        self.widgetDescr['filename'] = {
            'class': 'NEEntryWithFileBrowser',
            'master': 'node',
            'filetypes': fileTypes,
            'initialValue': 'File Name',
            'title': 'Read Image',
            'width': 10,}
        
        self.inputPortsDescr.append({
            'name': 'filename',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Write(NetworkNode):
    """Writes an image to a file. Please insure that if you are using the correct format if you are saving multiple images to one file.
    
    File Name: the file to be written to. Double click for file browser."""

    def __init__(self, name='Write', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, filename):
        img = toSeq(img)
        if filename and filename != 'File Name':
            img.write(filename)\n"""

        self.setFunction(code)

        fileTypes = [('all', '*')]
        self.widgetDescr['filename'] = {
            'class': 'NEEntryWithFileSaver',
            'master': 'node',
            'initialValue': 'File Name',
            'filetypes': fileTypes,
            'title': 'Write Image',
            'width': 10 }
        
        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'filename',
            'datatype': 'string'})

class toPIL(NetworkNode):
    """Converts an image to the PIL datatype for use with the included imagelib.

    Removes transparency information. Only works with RGB images. Flattens image sequences."""

    def __init__(self, name='toPIL', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        import Image, numpy.oldnumeric as Numeric

        if len(img) > 1:
            img = toSeq(img)
            img = flatten(img)
        else:
            img = img[0]

        Aim = img.toarray()
        Aim = Aim[:,:,0:3]
        Aim = Aim / 257
        h, w, c = Aim.shape
        Aim = Numeric.reshape(Aim, (1, w*h*c))
        Aim = Aim.astype(Numeric.UnsignedInt8)

        result = Image.fromstring('RGB', (image.width,image.height), Aim.tostring())
        
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'image'})

class TkDisplay(NetworkNode):
    """Uses Tkinter and PIL to display an image.

    Does not display transparent colors. Only works with RGB images. Flattens image sequences."""

    def __init__(self, name='TkDisplay', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        import Tkinter
        from PIL import ImageTk
        # This code from PILNodes.py written by Michel Sanner
        self.top = Tkinter.Toplevel()
        self.imCanvas = Tkinter.Canvas(self.top)
        self.canvasImage = None

        code = """def doit(self, img):
        import Image, Tkinter, ImageTk, Numeric

        if len(img) > 1:
            img = toSeq(img)
            img = flatten(img)
        else:
            img = img[0]
        
        Aim = img.toarray()
        Aim = Aim[:,:,0:3]
        Aim = Aim / 257
        h, w, c = Aim.shape
        Aim = Numeric.reshape(Aim, (1, w*h*c))
        Aim = Aim.astype(Numeric.UnsignedInt8)

        PILimage = Image.fromstring('RGB', (w,h), Aim.tostring())

        # This code from PILNodes.py written by Michel Sanner
        if PILimage:
            if self.canvasImage: self.imCanvas.delete(self.canvasImage)
            self.imtk = ImageTk.PhotoImage(PILimage, master=self.top)
            self.canvasImage = self.imCanvas.create_image(
                            self.imtk.width()+2, self.imtk.height()+2, image=self.imtk, anchor='se')
            self.imCanvas.configure(width=self.imtk.width()+2,
                                  height=self.imtk.height()+2)
            self.imCanvas.pack()\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})    

class Display(NetworkNode):
    """Uses ImageMagick to display an image"""

    def __init__(self, name='Display', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        img.display()\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})

class Animate(NetworkNode):
    """Animates an image sequence on the screen."""

    def __init__(self, name='Animate', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        img.animate()\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})



class Copy(NetworkNode):
    """Copies an image.

    Usage Example: Add the an image to a sequence twice"""

    def __init__(self, name='Copy', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = img.copy()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class toArray(NetworkNode):
    """Converts an image to a Numeric array."""

    def __init__(self, name='toArrray', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = img.toarray()
        self.outputData(out=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'out'})

class getPixels(NetworkNode):
    """Outpus an array of pixel data for the region specified.

    X: X coordinate of top left corner of region
    Y: Y coordinate of top left corner of region
    Rows: height of region
    Cols: length of region"""

    def __init__(self, name='getPixels', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, x, y, c, r):
        img = toSeq(img)
        x = int(x)
        y = int(y)
        r = int(r)
        c = int(c)
        result = img.getpixels(x,y,c,r)
        self.outputData(out=result)\n"""

        self.setFunction(code)

        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'X',
            'width': 10,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Y',
            'width': 10,}
        self.widgetDescr['c'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Columns',
            'width': 10,}
        self.widgetDescr['r'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Rows',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'c',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'out'})
        
### Memory error
##class Describe(NetworkNode):
##    """Outputs attributes to a file."""
##
##    def __init__(self, name='Describe', **kw):
##        kw['name'] = name
##        apply(NetworkNode.__init__, (self,), kw)
##
##        code = """def doit(self, img, filename, verb):
##        if filename and filename != 'File Name':
##            img.describe(verb, filename)\n"""
##
##        self.setFunction(code)
##
##        fileTypes = [('all', '*')]
##        self.widgetDescr['filename'] = {
##            'class': 'NEEntryWithFileSaver',
##            'master': 'node',
##            'initialValue': 'File Name',
##            'filetypes': fileTypes,
##            'title': 'Write Image',
##            'width': 10 }
##        self.widgetDescr['verb'] = {
##            'class': 'NECheckButton',
##            'initialValue': 0,
##            'text': 'Verbose',
##            'master': 'node',}
##        
##        self.inputPortsDescr.append({
##            'name': 'img',
##            'singleConnection':False,
##            'datatype': 'imimage'})
##        self.inputPortsDescr.append({
##            'name': 'filename',
##            'datatype': 'str'})
##        self.inputPortsDescr.append({
##            'name': 'verb',
##            'datatype': 'int'})

### Size ###
class Halve(NetworkNode):
    """Minifies an image to half its size."""

    def __init__(self, name='Halve', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = minify(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Double(NetworkNode):
    """Magnifies an image to twice its size."""

    def __init__(self, name='Double', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = magnify(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ResizeFactor(NetworkNode):
    """Resizes an image by a factor. Maintains aspect ratio.
    
    Factor: the factor by which to change the size (2.0 would double the size; 0.5 would halve it)"""

    def __init__(self, name='ResizeFactor', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, fact):
        img = toSeq(img)
        result = img.copy()
        if scale:
            op = eval('(-1,' + str(fact) + ')')
            result = imresize(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['fact'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Factor'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0.0,
            'max': None,
            'oneTurn': 1.0,
            'master': 'node',
            'size': 75,}            

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'fact',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ResizeWidth(NetworkNode):
    """Resizes an image to the given width. Maintains aspect ratio.

    Width: the new width"""

    def __init__(self, name='ResizeWidth', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width):
        img = toSeq(img)
        result = img.copy()
        if width:
            op = eval('(-1,' + width + ')')
            result = imresize(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ResizeHeight(NetworkNode):
    """Resizes an image to a given height. Maintains aspect ratio.

    Height: the new height"""

    def __init__(self, name='ResizeHeight', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, height):
        img = toSeq(img)
        result = img.copy()
        if height:
            op = eval('(' + height + ',-1)')
            result = imresize(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ResizeDim(NetworkNode):
    """Resizes an image to a given width and height. Does not (necessarily) maintain aspect ratio.

    Width: the new width
    Height: the new height"""

    def __init__(self, name='ResizeDim', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width, height):
        img = toSeq(img)
        result = img.copy()
        if width and height:
            op = eval('(' + height + ',' + width + ')')
            result = imresize(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Width',
            'width': 5}
        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Height',
            'width': 5}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class SampleWidth(NetworkNode):
    """Resamples an image to a given width. Maintains aspect ratio.

    Width: the new width"""

    def __init__(self, name='SampleWidth', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width):
        img = toSeq(img)
        result = img.copy()
        if width:
            op = eval('(-1,' + width + ')')
            result = sample(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class SampleHeight(NetworkNode):
    """Resamples an image to a given height. Maintains aspect ratio.

    Height: the new height"""

    def __init__(self, name='SampleHeight', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, height):
        img = toSeq(img)
        result = img.copy()
        if height:
            op = eval('(' + height + ',-1)')
            result = sample(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class SampleDim(NetworkNode):
    """Resamples an image to a given width and height. Does not (necessarily) maintain aspect ratio.

    Width: the new width
    Height: the new height"""

    def __init__(self, name='SampleDim', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width, height):
        img = toSeq(img)
        result = img.copy()
        if width and height:
            op = eval('(' + height + ',' + width + ')')
            result = sample(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Width',
            'width': 5}
        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Height',
            'width': 5}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ScaleWidth(NetworkNode):
    """Rescales an image to a given width. Maintains aspect ratio.

    Width: the new width"""

    def __init__(self, name='ScaleWidth', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width):
        img = toSeq(img)
        result = img.copy()
        if width:
            op = eval('(-1,' + width + ')')
            result = scale(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ScaleHeight(NetworkNode):
    """Rescales an image to a given height. Maintains aspect ratio.

    Height: the new height"""

    def __init__(self, name='ScaleHeight', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, height):
        img = toSeq(img)
        result = img.copy()
        if height:
            op = eval('(' + height + ',-1)')
            result = scale(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ScaleDim(NetworkNode):
    """Rescales an image to a given width and height. Does not (necessarily) maintain aspect ratio.

    Width: the new width
    Height: the new height"""

    def __init__(self, name='ScaleDim', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width, height):
        img = toSeq(img)
        result = img.copy()
        if width and height:
            op = eval('(' + height + ',' + width + ')')
            result = scale(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Width',
            'width': 5}
        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Height',
            'width': 5}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ThumbFactor(NetworkNode):
    """Resizes an image by a factor for a thumbnail. Maintains aspect ratio.
    
    Factor: the factor by which to change the size (2.0 would double the size; 0.5 would halve it)"""

    def __init__(self, name='ThumbFactor', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, fact):
        img = toSeq(img)
        result = img.copy()
        if scale:
            op = eval('(-1,' + str(fact) + ')')
            result = thumbnail(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['fact'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Factor'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0.0,
            'max': None,
            'oneTurn': 1.0,
            'master': 'node',
            'size': 75,}            

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'fact',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ThumbWidth(NetworkNode):
    """Resizes an image to the given width for a thumbnail. Maintains aspect ratio.

    Width: the new width"""

    def __init__(self, name='ThumbWidth', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width):
        img = toSeq(img)
        result = img.copy()
        if width:
            op = eval('(-1,' + width + ')')
            result = thumbnail(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ThumbHeight(NetworkNode):
    """Resizes an image to a given height for a thumbnail. Maintains aspect ratio.

    Height: the new height"""

    def __init__(self, name='ThumbHeight', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, height):
        img = toSeq(img)
        result = img.copy()
        if height:
            op = eval('(' + height + ',-1)')
            result = thumbnail(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ThumbDim(NetworkNode):
    """Resizes an image to a given width and height for a thumbnail. Does not (necessarily) maintain aspect ratio.

    Width: the new width
    Height: the new height"""

    def __init__(self, name='ThumbDim', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, width, height):
        img = toSeq(img)
        result = img.copy()
        if width and height:
            op = eval('(' + height + ',' + width + ')')
            result = thumbnail(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['width'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Width',
            'width': 5}
        self.widgetDescr['height'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Height',
            'width': 5}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'width',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'height',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})



### Transform ###
class Rotate(NetworkNode):
    """Rotates an image to a given degree.

    Degrees: the number of degrees to rotate the image"""

    def __init__(self, name='Rotate', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, deg):
        img = toSeq(img)
        result = img.copy()
        if deg:
            result = rotate(img, deg)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['deg'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Degrees'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': -360,
            'max': 360,
            'oneTurn': 360,
            'master': 'node',
            'size': 75,}
        
        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'deg',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Flip(NetworkNode):
    """Flips an image upside down"""

    def __init__(self, name='Flip', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = flip(image)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Flop(NetworkNode):
    """Mirrors an image"""

    def __init__(self, name='Flop', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = flop(image)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Chop(NetworkNode):
    """Remove rows and/or columns of pixels from an image.

    Leftmost: The leftmost column to be removed
    Columns: The number of columns to be removed
    Topmost: The topmost row to be removed
    Rows: The number of rows to be removed"""
    
    def __init__(self, name='Chop', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, l, c, t, r):
        img = toSeq(img)
        result = img.copy()
        if l and c and t and r:
            op = eval('(' + l + ',' + c + ',' + t + ',' + r + ')')
            result = chop(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['l'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Leftmost',
            'width': 10,}
        self.widgetDescr['c'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Columns',
            'width': 10,}
        self.widgetDescr['t'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Topmost',
            'width': 10,}
        self.widgetDescr['r'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Rows',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'l',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'c',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 't',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Crop(NetworkNode):
    """Keeps only specified rows and columns in an image.

    Leftmost: the leftmost pixel to be kept
    Columns: the number of columns to be kept
    Topmost: the topmost row to be kept
    Rows: the number of rows to be kept"""
    
    def __init__(self, name='Chop', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, w, h, x, y):
        img = toSeq(img)
        result = img.copy()
        if w and h and x and y:
            op = eval('(' + l + ',' + c + ',' + t + ',' + r + ')')
            result = crop(img, op)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['l'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Leftmost',
            'width': 10,}
        self.widgetDescr['c'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Columns',
            'width': 10,}
        self.widgetDescr['t'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Topmost',
            'width': 10,}
        self.widgetDescr['r'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Rows',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'l',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'c',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 't',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Roll(NetworkNode):
    """Rolls an image around itself.

    Columns: the number of columns to roll
    Rows: the number of rows to roll"""

    def __init__(self, name='Roll', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, c, r):
        img = toSeq(img)
        result = img.copy()
        if c and r:
            result = roll(img, (int(c), int(r)))
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['c'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Colums',
            'width': 10,}
        self.widgetDescr['r'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Rows',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'c',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Shave(NetworkNode):
    """Shaves image by deleting from all 4 sides.

    Columns: number of columns to delete from left and right
    Rows: number of rows to delete from top and bottom"""

    def __init__(self, name='Shave', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, c, r):
        img = toSeq(img)
        result = img.copy()
        if c and r:
            result = shave(img, (int(c), int(r)))
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['c'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Colums',
            'width': 10,}
        self.widgetDescr['r'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Rows',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'c',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Shear(NetworkNode):
    """Shear image by given angles.

    X Shear: angle measured from Y-axis
    Y Shear: angle measured from X-Axis
    Background: A color name (red) for the background"""

    def __init__(self, name='Shear', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, x, y, color):
        img = toSeq(img)
        x = int(x)
        y = int(y)
        result = shear(img, x, y, background=color)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'initialValue': 'X Shear',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'initialValue': 'Y Shear',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'initialValue': 'Background',
            'master': 'node',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Affine(NetworkNode):
    """Transforms an image as dictated by the affine sequence.

    Affine matrix:
    sx      rx    0
    ry      sy    0
    tx(0)  ty(0)  1"""

    def __init__(self, name='Affine', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, sx, rx, ry, sy, tx, ty):
        img = toSeq(img)
        result = affine(img, (int(sx), int(rx), int(ry), int(sy), int(tx), int(ty)))
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['sx'] = {
            'class': 'NEEntry',
            'initialValue': 'sx',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['rx'] = {
            'class': 'NEEntry',
            'initialValue': 'rx',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['ry'] = {
            'class': 'NEEntry',
            'initialValue': 'ry',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['sy'] = {
            'class': 'NEEntry',
            'initialValue': 'sy',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['tx'] = {
            'class': 'NEEntry',
            'initialValue': '0',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['ty'] = {
            'class': 'NEEntry',
            'initialValue': '0',
            'master': 'node',
            'width': 5,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'sx',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'rx',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'ry',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'sy',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'tx',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'ty',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
        
### Color ###
class Contrast(NetworkNode):
    """Enhance the intensity differences between light and dark in the image.

    Level: > 0 to increase contrast, < 0 to decrease contrast"""

    def __init__(self, name='Contrast', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, cont):
        img = toSeq(img)
        result = img.copy()
        if cont:
            result.contrast(cont)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['cont'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Contrast'}, 'labelSide':'left',
            'type': float,
            'initialValue': 10,
            'min': 0,
            'max': None,
            'oneTurn': 20,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'cont',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
        
class Colorize(NetworkNode):
    """Blends the color with each pixel of the image.

    Color: A color name ('red') or or RGB tuple ((255, 0, 0))
    Opacity: A initialValue from 0 to 1 defining the opacity of the color"""

    def __init__(self, name='Colorize', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, color, val):
        img = toSeq(img)
        result = img.copy()
        if type(eval(color)) == str:
            result = colorize(img, eval(color), val)
        else:
            r, g, b = eval(color)
            r = r * 257
            g = g * 257
            b = b * 257
            result = colorize(img, (r, g, b) , val)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Color',
            'width': 10,}
        self.widgetDescr['val'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Opacity'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.5,
            'min': 0,
            'max': 1,
            'oneTurn': .10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'val',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Quantize(NetworkNode):
    """Quantize an image to a given number of colors using dithering if specified

    Colors: number of colors
    Dither: check to use dithering"""

    def __init__(self, name='Quantize', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, colors, dither):
        img = toSeq(img)
        result = img.copy()
        result.quantize(int(colors), dither)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['colors'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Colors',
            'width': 10,}
        self.widgetDescr['dither'] = {
            'class': 'NECheckButton',
            'initialValue': 1,
            'text': 'Dither',
            'master': 'node',}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'colors',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'dither',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class CompressMap(NetworkNode):
    """Compress an image colormap by removing any duplicate or unused color entries."""

    def __init__(self, name='CompressMap', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = img.copy();
        result.compresscolormap()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
        
class Equalize(NetworkNode):
    """Apply a histogram equalization to the image."""

    def __init__(self, name='Equalize', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = img.copy()
        result.equalize()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Normalize(NetworkNode):
    """Enhances the contrast of a color image by adjusting the pixels color to span the entire range of colors available."""
    
    def __init__(self, name='Normalize', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = img.copy()
        result.normalize()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Modulate(NetworkNode):
    """Control the percent change in the brightness, saturation, and hue of the image (100 means no change)

    Brightness: light or dark
    Saturation: intensity
    Hue: shade"""

    def __init__(self, name='Modulate', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, b, s, h):
        img = toSeq(img)
        result = img.copy()
        result.modulate(b, s, h)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['b'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Brightness'}, 'labelSide':'left',
            'type': int,
            'initialValue': 100,
            'min': 0,
            'max': None,
            'oneTurn': 100,
            'master': 'node',
            'size': 75,}
        self.widgetDescr['s'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Saturation'}, 'labelSide':'left',
            'type': int,
            'initialValue': 100,
            'min': 0,
            'max': None,
            'oneTurn': 100,
            'master': 'node',
            'size': 75,}
        self.widgetDescr['h'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Hue'}, 'labelSide':'left',
            'type': int,
            'initialValue': 100,
            'min': 0,
            'max': None,
            'oneTurn': 100,
            'master': 'node',
            'size': 75,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'b',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 's',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'h',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Negate(NetworkNode):
    """Negates the colors in the image.

    Grayscale: if checked, only the grayscale values are negated"""

    def __init__(self, name='Negate', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, gray):
        img = toSeq(img)
        result = img.copy()
        result.negate(gray)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['gray'] = {
            'class': 'NECheckButton',
            'initialValue': 0,
            'text': 'Grayscale',
            'master': 'node',}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'gray',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Solarize(NetworkNode):
    """Apply a special effect similar to the effect achieved in a photo darkroom by selectively exposing areas of photo sensitive paper to light.

    Threshold: extent of solarization from 1 to %s"""

    def __init__(self, name='Solarize', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, thresh):
        img = toSeq(img)
        result = img.copy()
        result.solarize(thresh)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['thresh'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Threshold'}, 'labelSide':'left',
            'type': int,
            'initialValue': 50,
            'min': 1,
            'max': MaxRGB,
            'oneTurn': 1000,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'thresh',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Gamma(NetworkNode):
    """Specify individual gamma levels for the red, blue, and green channels.

    A value of 0 will reduce the influence of the channel.
    Typical values range from 0.8 to 2.3"""

    def __init__(self, name='Gamma', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, r, g, b):
        img = toSeq(img)
        result = img.copy()
        result.gamma(r, g, b)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['r'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Red'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['g'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Green'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['b'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Blue'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'g',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'b',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Level(NetworkNode):
    """Adjusts the levels of an image by scaling the colors falling between specificed white and black points to the full available quantum range.

    Black: the darkest color of the image. Colors darker than this are set to 0. (Measured as a percentage of the maximum value)
    White: the lightest color of the image. Colors lighter than this are set to the maximum value. (Measured as a percentage of the maximum value)
    Mid: the gamma correction to apply to the image"""

    def __init__(self, name='Level', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, b, w, m):
	img = toSeq(img)
        result = img.copy()
        result.level(b, m, w)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['b'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Black'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['w'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'White'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.999,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['m'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Mid'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': None,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'b',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'w',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'm',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class OrderedDither(NetworkNode):
    """Uses the ordered dithering technique of reducing color images to monochrome using positional information to retain as much information as possible."""

    def __init__(self, name='OrderedDither', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img): 
	img = toSeq(img)
        result = img.copy()
        result.ordered_dither()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Channel(NetworkNode):
    """Extract the specified channel from the image."""

    def __init__(self, name='Channel', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, chan): 
	img = toSeq(img)
        result = img.copy()
        result.channel(chan)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        chanTypes = [
            'Undefined',
            'Red',
            'Cyan',
            'Green',
            'Magenta',
            'Blue',
            'Yellow',
            'Opacity',
            'Black',
            'Matte']
            
        self.widgetDescr['chan'] = {
            'class': 'NEComboBox',
            'scrolledlist_items': chanTypes,
            'labelCfg':{'text':'Channel'}, 'labelSide':'left',
            'master': 'node',
            'hull_width': 2,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'chan',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class CycleColors(NetworkNode):
    """Cycle the colormap by the given amount."""

    def __init__(self, name='CycleColors', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, val): 
	img = toSeq(img)
        result = img.copy()
        result.cyclecolor(val)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['val'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Value'}, 'labelSide':'left',
            'type': 'int',
            'initialValue': 50,
            'min': None,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'val',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class LAT(NetworkNode):
    """ Perfom local adaptive thresholding

    Width: of area around pixel
    Height: of area around pixel
    Offset: threshold calculated from mean of pizels + offset"""

    def __init__(self, name='LAT', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, w, h, off):
        img = toSeq(img)
        result = lat(img, w, h, off)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)
        
        self.widgetDescr['w'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Width'}, 'labelSide':'left',
            'type': 'int',
            'initialValue': 5,
            'min': 0,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['h'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Height'}, 'labelSide':'left',
            'type': 'int',
            'initialValue': 5,
            'min': 0,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['off'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Offset'}, 'labelSide':'left',
            'type': 'int',
            'initialValue': 5,
            'min': 1,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'w',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'h',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'off',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Segment(NetworkNode):
    """Segments an image using fuzzy C-means technique to identify units of the histograms of the color components that are homogeneous.

    Colorspace
    Verbose: Print detailed information about the classes
    Cluster: Minimum number of pixels contained in a hexahedra before it can be considered valid (percentage)
    Smooth: Eliminates noise in the second derivative of the histogram"""

    def __init__(self, name='Segment', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, space, verb, cluster, smooth):
        img = toSeq(img)
        result = img.copy()
        result.segment(space, verb, cluster, smooth)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)
    
        spaceTypes = [
            'Undefined',
            'RGB',
            'Gray',
            'Transparent',
            'OHTA',
            'XYZ',
            'YCbCr',
            'YCC',
            'YIQ',
            'YPbPr',
            'YUV',
            'CMYK',
            'sRGB']
        self.widgetDescr['space'] = {
            'class': 'NEComboBox',
            'scrolledlist_items': spaceTypes,
            'labelCfg':{'text':'Color Space'}, 'labelSide':'left',
            'master': 'node',
            'hull_width': 2,}
        self.widgetDescr['verb'] = {
            'class': 'NECheckButton',
            'initialValue': 0,
            'text': 'Verbose',
            'master': 'node',}
        self.widgetDescr['cluster'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Cluster'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0.0,
            'max': 1.0,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['smooth'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Smooth'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'space',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'verb',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'cluster',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'smooth',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class LevelChannel(NetworkNode):
    """Adjusts the levels of an image by scaling the colors falling between specificed white and black points to the full available quantum range.

    Channel
    Black: the darkest color of the image. Colors darker than this are set to 0. (Measured as a percentage of the maximum value)
    White: the lightest color of the image. Colors lighter than this are set to the maximum value. (Measured as a percentage of the maximum value)
    Mid: the gamma correction to apply to the image"""

    def __init__(self, name='LevelChannel', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, chan, b, w, m):
	img = toSeq(img)
        result = img.copy()
        result.levelchannel(chan, b, m, w)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)


        chanTypes = [
            'Undefined',
            'Red',
            'Cyan',
            'Green',
            'Magenta',
            'Blue',
            'Yellow',
            'Opacity',
            'Black',
            'Matte']
        self.widgetDescr['chan'] = {
            'class': 'NEComboBox',
            'scrolledlist_items': chanTypes,
            'labelCfg':{'text':'Channel'}, 'labelSide':'left',
            'master': 'node',
            'hull_width': 2,}
        self.widgetDescr['b'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Black'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['w'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'White'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.999,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['m'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Mid'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': None,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'chan',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'b',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'w',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'm',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Threshold(NetworkNode):
    """Creates an image based on a threshold value.

    R, G, B, & O: percentage of MaxRGB"""

    def __init__(self, name='Threshold', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, r, g, b, o):
        img = toSeq(img)
        result = img.copy()
        result.threshold(r, g, b, o)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['r'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'R'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['g'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'G'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['b'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'B'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['o'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'O'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 0.999,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'g',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'b',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'o',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

### Blur/Noise ###
class Blur(NetworkNode):
    """Applies a Guassian blur to the image.

    Sigma: The standard deviation (in pixels)"""

    def __init__(self, name='Blur', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, sig):
	img = toSeq(img)
        result = img.copy()
        if sig:
            result = blur(img, sig)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['sig'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Sigma'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'sig',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Enhance(NetworkNode):
    """Improves the quality of a noisy image."""

    def __init__(self, name='Enhance', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
	img = toSeq(img)
        result = enhance(image)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class AddNoise(NetworkNode):
    """Adds random noise to the image.

    Noise Type: the type of noise (drop down list)"""

    def __init__(self, name='AddNoise', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, type): 
	img = toSeq(img)
        result = img.copy()
        if type:
            result = addnoise(img, type)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        noiseTypes = [
            'Uniform',
            'Gaussian',
            'Multiplicative',
            'Impulse',
            'Laplacian',
            'Poisson']

        self.widgetDescr['type'] = ({
            'class': 'NEComboBox',
            'master': 'node',
            'scrolledlist_items': noiseTypes,
            'labelCfg':{'text':'Noise Type'}, 'labelSide':'left',
            'hull_width': 2})

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'type',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Despeckle(NetworkNode):
    """Despeckles an image while preserving the edge"""

    def __init__(self, name='Despeckle', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img): 
	img = toSeq(img)
        result = despeckle(image)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class MotionBlur(NetworkNode):
    """Blurs the image with a Gaussian kernal.

    Sigma: the standard deviation
    Degrees: angle of movement from vertical"""

    def __init__(self, name='MotionBlur', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, sig, deg): 
	img = toSeq(img)
        result = img.copy()
        if sig and deg:
            result = motionblur(img, sig, deg)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['sig'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Sigma'}, 'labelSide':'left',
            'type': float,
            'initialValue': 4.0,
            'min': 0.0,
            'max': None,
            'oneTurn': 2,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.widgetDescr['deg'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Degrees'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': -360,
            'max': 360,
            'oneTurn': 360,
            'master': 'node',
            'size': 75,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'sig',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'deg',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ReduceNoise(NetworkNode):
    """Smooths the contours of an image while still preserving edge information."""

    def __init__(self, name='ReduceNoise', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img): 
	img = toSeq(img)
        result = reducenoise(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Sharpen(NetworkNode):
    """Sharpen a blurry image.

    Sigma: the standard deviation"""

    def __init__(self, name='Sharpen', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, sig): 
	img = toSeq(img)
        result = img.copy()
        if sig:
            result = sharpen(img, sig)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['sig'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Sigma'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'sig',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class UnsharpMask(NetworkNode):
    """Unsharpen an image using unsharp masking.

    Sigma: The standard deviation (in pixels)"""

    def __init__(self, name='UnsharpMask', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, sig):
	img = toSeq(img)
        result = blur(img, sig)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['sig'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Sigma'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'sig',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

### Effects ###
class Border(NetworkNode):
    """Applies a border to the image.

    Width: width of the sides
    Height: width of the top and bottom
    Color: A color name ('red') or or RGB tuple ((255, 0, 0))"""

    def __init__(self, name='Border', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, w, h, color): 
	img = toSeq(img)
        result = img.copy();
        if type(eval(color)) == str:
            result = border(img, w, h, bordercolor=eval(color))
        else:
            r, g, b = eval(color)
            r = r * 257
            g = g * 257
            b = b * 257
            result = border(img, w, h, bordercolor=(r, g, b))
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['w'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Width'}, 'labelSide':'left',
            'type': int,
            'initialValue': 1,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,
            'wheelpad': 10,}
        self.widgetDescr['h'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Height'}, 'labelSide':'left',
            'type': int,
            'initialValue': 1,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,
            'wheelpad': 100,}
        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Color',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'w',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'h',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Charcoal(NetworkNode):
    """Makes the image look like a charcoal sketch.

    Radius: The radius (in pixels)
    Sigma: The standard deviation (in pixels)"""

    def __init__(self, name='Charcoal', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, rad, sig): 
	img = toSeq(img)
        result = img.copy()
        if rad and sig:
            result = charcoal(img, rad, sig)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['rad'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Radius'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.0,
            'min': 0.0,
            'max': None,
            'oneTurn': 2.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.widgetDescr['sig'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Sigma'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1.0,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'rad',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'sig',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Edge(NetworkNode):
    """Finds the edges in an image.

    Radius: the radius of the convolution filter"""

    def __init__(self, name='Edge', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, rad): 
	img = toSeq(img)
        result = edge(img, rad)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['rad'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Radius'}, 'labelSide':'left',
            'type': float,
            'initialValue': 3,
            'min': 0,
            'max': None,
            'oneTurn': 2,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'rad',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Emboss(NetworkNode):
    """Gives the image a 3-D, embossed effect.

    Sigma: the standard deviation """

    def __init__(self, name='Emboss', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, sig): 
	img = toSeq(img)
        result = emboss(img, sig)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)
        
        self.widgetDescr['sig'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Sigma'}, 'labelSide':'left',
            'type': float,
            'initialValue': 1.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'sig',
            'singleConnection':False,
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class OilPaint(NetworkNode):
    """Simulates an oil painting.

    Radius: the radius from which to choose the color for each 'stroke'"""

    def __init__(self, name='OilPaint', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, rad): 
	img = toSeq(img)
        result = img.copy()
        if rad:
            result = oilpaint(img, rad)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['rad'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Radius'}, 'labelSide':'left',
            'type': float,
            'initialValue': 3,
            'min': 0.0,
            'max': None,
            'oneTurn': 2,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'rad',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
      
class Frame(NetworkNode):
    """Adds a 3-D border around the image.

    Width: size of vertical sides
    Height: size of horizontal sides
    Inner: width of the inner shadow
    Outer: width of the outer shadow
    Color: A color name ('red') or or RGB tuple ((255, 0, 0))
"""

    def __init__(self, name='Border', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, w, h, i, o, color): 
	img = toSeq(img)
        result = img.copy();
        if type(eval(color)) == str:
            result = frame(img, w, h, i, o, mattecolor=eval(color))
        else:
            r, g, b = eval(color)
            r = r * 257
            g = g * 257
            b = b * 257
            result = frame(img, w, h, i, o, mattecolor=(r,g,b))
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['w'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Width'}, 'labelSide':'left',
            'type': int,
            'initialValue': 1,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['h'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Height'}, 'labelSide':'left',
            'type': int,
            'initialValue': 1,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['i'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Inner'}, 'labelSide':'left',
            'type': int,
            'initialValue': 1,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['o'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Outer'}, 'labelSide':'left',
            'type': int,
            'initialValue': 1,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'master': 'node',
            'initialValue': 'Color',
            'width': 10,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'w',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'h',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'i',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'o',
            'datatype': 'string'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'string'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Implode(NetworkNode):
    """Implode image pixels by a given factor

    Factor: the factor by which to implode the pixels"""

    def __init__(self, name='Implode', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, fact): 
	img = toSeq(img)
        result = img.copy()
        if fact:
            result = implode(img, fact)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['fact'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Factor'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.5,
            'min': 0.0,
            'max': None,
            'oneTurn': 1.0,
            'master': 'node',
            'size': 75,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'fact',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class MedianFilter(NetworkNode):
    """Replace each pixel by the median in a set of neighboring pixels.

    Radius: defines the set of neighboring pixels"""

    def __init__(self, name='MedianFilter', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, rad): 
	img = toSeq(img)
        result = medianfilter(img, rad)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['rad'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Radius'}, 'labelSide':'left',
            'type': float,
            'initialValue': 0.0,
            'min': 0.0,
            'max': 1.0,
            'oneTurn': 1,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'rad',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Shade(NetworkNode):
    """Shines a distant light on image
    Azimuth: Degress off x axis
    Elevation: Pixels above z axis"""

    def __init__(self, name='Shade', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, az, el): 
	img = toSeq(img)
        result = img.copy()
        if az and el:
            result = shade(img, az, el)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['az'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Azimuth'}, 'labelSide':'left',
            'type': float,
            'initialValue': 30.0,
            'min': None,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['el'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Elevation'}, 'labelSide':'left',
            'type': float,
            'initialValue': 30.0,
            'min': None,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'az',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'el',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Spread(NetworkNode):
    """Create a special effect by randomly displacing each pixel in a block.

    Radius: defines the block"""

    def __init__(self, name='Spread', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, rad): 
	img = toSeq(img)
        result = img.copy()
        if rad:
            result = spread(img, rad)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['rad'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Radius'}, 'labelSide':'left',
            'type': float,
            'initialValue': 3.0,
            'min': 0.0,
            'max': None,
            'oneTurn': 5,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'rad',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Swirl(NetworkNode):
    """Swirl the pixels about the center of the image.

    Degrees: angle of the arc through which each pixel is moved"""

    def __init__(self, name='Swirl', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, deg): 
	img = toSeq(img)
        result = img.copy()
        if deg:
            result = swirl(img, deg)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['deg'] = {
            'class': 'NEDial',
            'labelCfg':{'text':'Degrees'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': -360,
            'max': 360,
            'oneTurn': 360,
            'master': 'node',
            'size': 75,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'deg',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Raise(NetworkNode):
    """Create a 3D button from the image.

    Width: size of the vertical button edges
    Height: size of the horizontal button edges
    Raise: raise (checked) or lower (unchecked)"""

    def __init__(self, name='Raise', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, w, h, r): 
	img = toSeq(img)
        result = img.copy()
        result.raise_(w, h, r)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['w'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Width'}, 'labelSide':'left',
            'type': int,
            'initialValue': 6,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['h'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Height'}, 'labelSide':'left',
            'type': int,
            'initialValue': 6,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['r'] = {
            'class': 'NECheckButton',
            'initialValue': 1,
            'text': 'Raised',
            'master': 'node',}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'w',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'h',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'r',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Wave(NetworkNode):
    """Shift pixels along a sine wave.

    Amplitude
    Wavelength"""

    def __init__(self, name='Wave', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, amp, length):
        img = toSeq(img)
        result = wave(img, amp, length)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['amp'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Amplitude'}, 'labelSide':'left',
            'type': float,
            'initialValue': 25.0,
            'min': None,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['length'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Wavelength'}, 'labelSide':'left',
            'type': float,
            'initialValue': 15.0,
            'min': None,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'amp',
            'datatype': 'float'})
        self.inputPortsDescr.append({
            'name': 'length',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Plasma(NetworkNode):
    """Initialize an image with plasma fractal values.

    X1: coordinate of the region to initialize
    Y1: coordinate of the region to initialize
    X2: coordinate of the region to initialize
    Y2: coordinate of the region to initialize
    Atten: ?
    Depth: ?"""

    def __init__(self, name='Plasma', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, x1, y1, x2, y2, atten, depth):
        img = toSeq(img)
        result = img.copy()
        result.plasma((int(x1),int(y2),int(x2),int(y2)), atten, depth)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)
        
        self.widgetDescr['x1'] = {
            'class': 'NEEntry',
            'initialValue': 'X1',
            'master': 'node',
            'width': 5,}        
        self.widgetDescr['y1'] = {
            'class': 'NEEntry',
            'initialValue': 'Y1',
            'master': 'node',
            'width': 5,}        
        self.widgetDescr['x2'] = {
            'class': 'NEEntry',
            'initialValue': 'X2',
            'master': 'node',
            'width': 5,}        
        self.widgetDescr['y2'] = {
            'class': 'NEEntry',
            'initialValue': 'Y2',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['atten'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Atten'}, 'labelSide':'left',
            'type': int,
            'initialValue': 20,
            'min': None,
            'max': None,
            'oneTurn': 100,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['depth'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Depth'}, 'labelSide':'left',
            'type': int,
            'initialValue': 5,
            'min': None,
            'max': None,
            'oneTurn': 100,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'x1',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'y1',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'x2',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'y2',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'atten',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'depth',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Convolve(NetworkNode):
    """Convolve the image with a kernel.

    Kernel: NxN array with N odd. A 3x3 would by inputted like this:
    [[a, b, c], [d, e, f], [g, h, i]]"""

    def __init__(self, name='Convolve', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, kernel):
        img = toSeq(img)
        result = img.copy()
        kernel = eval(kernel)
        if type(kernel) == list:
            result = convolve(img, kernel)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['kernel'] = {
            'class': 'NEEntry',
            'initialValue': 'Kernel',
            'master': 'node',
            'width': 15,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'kernel',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

### Draw ###

class Transparent(NetworkNode):
    """Changes opacity of any pixel that matches a given color.

    Target: A color name ('red') or or RGB tuple ((255, 0, 0))
    Opacity: A value from 0 to 255 defining the opacity of the color
    Fuzz: Level of tolerance when determining whether a pixel matches the target"""

    def __init__(self, name='Transparent', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, target, o, fuzz): 
	img = toSeq(img)
        result = img.copy()
        o = o * 257
        if type(eval(target)) == str:
            result.transparent(eval(target), o, fuzz=fuzz)
        else:
            r, g, b = eval(target)
            r = r * 257
            g = g * 257
            b = b * 257
            result.transparent((r,g,b), o, fuzz=fuzz)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['target'] = {
            'class': 'NEEntry',
            'initialValue': 'Target',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['o'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Opacity'}, 'labelSide':'left',
            'type': int,
            'initialValue': 255,
            'min': 0,
            'max': 255,
            'oneTurn': 200,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['fuzz'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Fuzz'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': 0,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'target',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'o',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'fuzz',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class FillOpaque(NetworkNode):
    """Changes color of any pixel that matches a given color.

    Target: A color name ('red') or or RGB tuple ((255, 0, 0))
    Fill: A color name ('red') or or RGB tuple ((255, 0, 0))
    Fuzz: Level of tolerance when determining whether a pixel matches the target"""

    def __init__(self, name='FillOpaque', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, target, color, fuzz): 
	img = toSeq(img)
        result = img.copy()
        if type(eval(color)) == tuple:
            r, g, b = eval(color)
            r = r * 257
            g = g * 257
            b = b * 257
            color = '(' + str(r) + ',' + str(g) + ',' + str(b) + ')'
        if type(eval(target)) == str:
            result.opaque(eval(target), eval(color), fuzz=fuzz)
        else:
            r, g, b = eval(target)
            r = r * 257
            g = g * 257
            b = b * 257
            result.opaque((r,g,b), eval(color), fuzz=fuzz)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['target'] = {
            'class': 'NEEntry',
            'initialValue': 'Target',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'initialValue': 'Fill',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['fuzz'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Fuzz'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': 0,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'target',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'fuzz',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Erase(NetworkNode):
    """Sets each pixel to the background color"""

    def __init__(self, name='Erase', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img): 
	img = toSeq(img)
        result = img.copy()
        result.set()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Set(NetworkNode):
    """Sets each pixel to a specified color.

    Color: A color name ('red') or or RGB tuple ((255, 0, 0))
    Opacity: A value from 0 to 255 defining the opacity of the color"""

    def __init__(self, name='Set', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, color, o): 
	img = toSeq(img)
        result = img.copy()
        o = o * 257
        if type(eval(color)) == str:
            result.set(eval(color), o)
        else:
            r, g, b = eval(color)
            r = r * 257
            g = g * 257
            b = b * 257
            result.set((r,g,b), o)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'initialValue': 'Color',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['o'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Opacity'}, 'labelSide':'left',
            'type': int,
            'initialValue': 255,
            'min': 0,
            'max': 255,
            'oneTurn': 200,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'o',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class SetOpacity(NetworkNode):
    """Attenuates the opacity channel of an image.

    Opacity: from 1 to 255"""

    def __init__(self, name='SetOpacity', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, o):
        img = toSeq(img)
        result = img.copy()
        o = o * 257
        result.setopacity(o)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['o'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Opacity'}, 'labelSide':'left',
            'type': int,
            'initialValue': 255,
            'min': 0,
            'max': 255,
            'oneTurn': 200,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'o',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ColorFloodFill(NetworkNode):
    """Change the color value of any pixel with the following conditions.

    Target: A color name ('red') or or RGB tuple ((255, 0, 0))
    Fill: A color name ('red') or or RGB tuple ((255, 0, 0))
    X: X coordinate of target pixel
    Y: Y coordinate of target pixel
    Fuzz: Level of tolerance when determining whether a pixel matches the target"""

    def __init__(self, name='ColorFloodFill', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img,  target, fill, x, y, fuzz):
        img = toSeq(img)
        x = int(x)
        y = int(y)
        result = img.copy()
        if type(eval(fill)) == tuple:
            r, g, b = eval(fill)
            r = r * 257
            g = g * 257
            b = b * 257
            fill = '(' + str(r) + ',' + str(g) + ',' + str(b) + ')'
        if type(eval(target)) == tuple:
            r, g, b = eval(target)
            r = r * 257
            g = g * 257
            b = b * 257
            target = '(' + str(r) + ',' + str(g) + ',' + str(b) + ')'
        result.colorfloodfill(eval(target), eval(fill), x, y, fuzz=fuzz)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['target'] = {
            'class': 'NEEntry',
            'initialValue': 'Target',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['fill'] = {
            'class': 'NEEntry',
            'initialValue': 'Fill',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'initialValue': 'X',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'initialValue': 'Y',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['fuzz'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Fuzz'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': 0,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'target',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'fill',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'fuzz',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class MatteFloodFill(NetworkNode):
    """Change the transparency value of any pixel with the following conditions.

    Target: A color name ('red') or or RGB tuple ((255, 0, 0))
    Opacity: A value from 0 to 255
    X: X coordinate of target pixel
    Y: Y coordinate of target pixel
    Fuzz: Level of tolerance when determining whether a pixel matches the target"""

    def __init__(self, name='ColorFloodFill', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img,  target, o, x, y, fuzz):
        img = toSeq(img)
        x = int(x)
        y = int(y)
        result = img.copy()
        if type(eval(target)) == tuple:
            r, g, b = eval(target)
            r = r * 257
            g = g * 257
            b = b * 257
            target = '(' + str(r) + ',' + str(g) + ',' + str(b) + ')'
        o = o*257
        result.mattefloodfill(eval(target), o, x, y, fuzz=fuzz)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['target'] = {
            'class': 'NEEntry',
            'initialValue': 'Target',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['o'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Opacity'}, 'labelSide':'left',
            'type': int,
            'initialValue': 255,
            'min': 0,
            'max': 255,
            'oneTurn': 200,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}
        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'initialValue': 'X',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'initialValue': 'Y',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['fuzz'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Fuzz'}, 'labelSide':'left',
            'type': int,
            'initialValue': 0,
            'min': 0,
            'max': None,
            'oneTurn': 50,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'target',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'o',
            'datatype': 'int'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'fuzz',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
        
### Font error ###
class Annotate(NetworkNode):
    """Annotate an image.

    Font: Name of the font (use the ImageMagick command convert -list type to see available fonts
    Size: size of the font
    Color: A color name ('red') or or RGB tuple ((255, 0, 0))
    X: x offset
    Y: y offset
    Text: Annotation"""

    def __init__(self, name='Annotate', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, fname, size, color, x, y, text): 
	img = toSeq(img)
        result = img.copy()
        x = int(x)
        y = int(y)
        size = int(size)
        if type(eval(color)) == tuple:
            r, g, b = eval(color)
            r = r * 257
            g = g * 257
            b = b * 257
            color = '(' + str(r) + ',' + str(g) + ',' + str(b) + ')'
        dc = newdc(font=fname, pointsize=size, fill=eval(color))
        result.annotate(dc, x, y, text)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['fname'] = {
            'class': 'NEEntry',
            'initialValue': 'Font',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['size'] = {
            'class': 'NEEntry',
            'initialValue': 'Size',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['color'] = {
            'class': 'NEEntry',
            'initialValue': 'Color',
            'master': 'node',
            'width': 10,}
        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'initialValue': 'X',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'initialValue': 'Y',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['text'] = {
            'class': 'NEEntry',
            'initialValue': 'Text',
            'master': 'node',
            'width': 15,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'fname',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'size',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'color',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'text',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Draw(NetworkNode):
    """Use an ImageMagick primitive to draw on an image.

    Primitive: the string that specifies what you're drawing"""

    def __init__(self, name='Draw', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, prim):
        img = toSeq(img)
        result = img.copy()
        result.draw(prim)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['prim'] = {
            'class': 'NEEntry',
            'initialValue': 'Primitive',
            'master': 'node',
            'width': 15,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'prim',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class ClipPath(NetworkNode):
    """Set the clipping mask for an image.

    Primitive: ImageMagick primitive"""

    def __init__(self, name='ClipPath', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, prim):
        img = toSeq(img)
        result = img.copy()
        result.clip_path(prim)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['prim'] = {
            'class': 'NEEntry',
            'initialValue': 'Primitive',
            'master': 'node',
            'width': 15,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'prim',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class SetPixels(NetworkNode):
    """Set raw data into image.

    X: offset
    Y: offset
    Z: offset"""

    def __init__(self, name='SetPixels', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, data, x, y, z):
        img = toSeq(img)
        result = img.copy()
        x = int(x)
        y = int(y)
        z = int(z)

        result.setpixels(data, x, y, z)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'initialValue': 'X',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'initialValue': 'Y',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['z'] = {
            'class': 'NEEntry',
            'initialValue': 'Z',
            'master': 'node',
            'width': 5,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'data'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'z',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

### Multiple Images ###
class CreateSeq(NetworkNode):
    """Creates a sequence of images from several individual images."""

    def __init__(self, name='CreateSeq', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        result = toSeq(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimageseq'})
        
class Average(NetworkNode):
    """Averages a set of images together. Each must have the same height and width."""

    def __init__(self, name='Average', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = average(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimageseq'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Diff(NetworkNode):
    """Measures the difference between colors at each pixel location of two images.

    Output Port 0 (e0): mean error for any single pixel
    Output Port 1 (e1): normalized mean quantization error -- range 0 to 1
    Output Port 2 (e2): normalize maximum quantization error"""

    def __init__(self, name='Diff', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, img2):
        img = toSeq(img)
        img2 = toSeq(img2)
        result = img.copy()
        result.diff(img2)
        self.outputData(e0=result.error, e1=result.mean_error, e2=result.max_error)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'img2',
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'e0',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'e1',
            'datatype': 'float'})
        self.outputPortsDescr.append({
            'name': 'e2',
            'datatype': 'float'})

class Map(NetworkNode):
    """Replaces the colors of the first image with the closest color from the second image."""

    def __init__(self, name='Map', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, img2, dither):
        img = toSeq(img)
        img2 = toSeq(img2)
        result = img.copy()
        result.map(img2, dither)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['dither'] = {
            'class': 'NECheckButton',
            'initialValue': 1,
            'text': 'Dither',
            'master': 'node',}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'img2',
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'dither',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Mosaic(NetworkNode):
    """Inlays an image sequence to from a single coherent picture"""

    def __init__(self, name='Mosaic', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = mosaic(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Morph(NetworkNode):
    """Morphs images into each other.

    Frames: Number of frames used for the morph between two images"""

    def __init__(self, name='Morph', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, frames):
        img = toSeq(img)
        result = morph(img, frames)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['frames'] = {
            'class': 'NEThumbWheel',
            'labelCfg':{'text':'Frames'}, 'labelSide':'left',
            'type': int,
            'initialValue': 5,
            'min': 0,
            'max': None,
            'oneTurn': 10,
            'label': 1,
            'master': 'node',
            'width': 75,
            'height': 30,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'frames',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Append(NetworkNode):
    """Appends an image list to each other to make one image.

    Stack: if checked, stack top to bottom, else stack left to right"""

    def __init__(self, name='Append', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, stack):
        img = toSeq(img)
        result = img.copy()
        if len(img) > 1:
            result = append(img, stack)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['stack'] = {
            'class': 'NECheckButton',
            'initialValue': 1,
            'text': 'Stack',
            'master': 'node',}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'stack',
            'datatype': 'int'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Flatten(NetworkNode):
    """Merge an image list into a single image."""

    def __init__(self, name='Flatten', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = flatten(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
        
class Stegano(NetworkNode):
    """Hide a digital watermark within the image."""

    def __init__(self, name='Watermark', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, mark):
        img = toSeq(img)
        result = stegano(img, mark)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'mark',
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Stereo(NetworkNode):
    """Combines a stereo pair of images to produce a single image. Both images must have the same length."""

    def __init__(self, name='Stereo', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img1, img2):
        img1 = toSeq(img1)
        img2 = toSeq(img2)
        result = img1.copy()
        if len(img1) == len(img2):
            result = stereo(img1, img2)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img1',
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'img2',
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Coalesce(NetworkNode):
    """Composite an image list of different sizes and offsets into a single image sequence.

    Crops images that are bigger than the first image."""

    def __init__(self, name='Coalesce', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = img.copy()
        if len(img) > 1:
            result = coalesce(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class Composite(NetworkNode):
    """Composite the second image over the first.

    X: Column offset
    Y: Row offset
    Method"""

    def __init__(self, name='Composite', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img1, img2, x, y, method):
        img1 = toSeq(img1)
        img2 = toSeq(img2)
        result = img1.copy()
        x = int(x)
        y = int(y)
        result.composite(img2, x, y, method)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        methodTypes = [
            "Undefined",
            "Over",
            "In",
            "Out",
            "Atop",
            "Xor",
            "Plus",
            "Minus",
            "Add",
            "Subtract",
            "Difference",
            "Multiply",
            "Bumpmap",
            "Copy",
            "CopyRed",
            "CopyGreen",
            "CopyBlue",
            "CopyOpacity",
            "Clear",
            "Dissolve",
            "Displace",
            "Modulate",
            "Threshold",
            "No",
            "Darken",
            "Lighten",
            "Hue",
            "Saturate",
            "Colorize",
            "Luminize",
            "Screen",
            "Overlay",
            "ReplaceMatte"]
        self.widgetDescr['method'] = {
            'class': 'NEComboBox',
            'scrolledlist_items': methodTypes,
            'labelCfg':{'text':'Method'}, 'labelSide':'left',
            'master': 'node',
            'hull_width': 2,}
        self.widgetDescr['x'] = {
            'class': 'NEEntry',
            'initialValue': 'X',
            'master': 'node',
            'width': 5,}
        self.widgetDescr['y'] = {
            'class': 'NEEntry',
            'initialValue': 'Y',
            'master': 'node',
            'width': 5,}

        self.inputPortsDescr.append({
            'name': 'img1',
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'img2',
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'x',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'y',
            'datatype': 'str'})
        self.inputPortsDescr.append({
            'name': 'method',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})
        
class Deconstruct(NetworkNode):
    """Compare each image with the next in a sequence and return the maximum bounding region of any pixel differences encountered"""

    def __init__(self, name='Deconstruct', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img):
        img = toSeq(img)
        result = deconstruct(img)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.outputPortsDescr.append({
            'name': 'img',
            'datatype': 'imimage'})

class DrawAffine(NetworkNode):
    """Composite the second image over the first as defined by the affine transformation.

    Affine: 2x2, 3x3, 2x3, 3x2 matrix or 4-6 sequence. A 2x2 matrix would be inputted as:
    [[a, b], [c, d]]"""

    def __init__(self, name="DrawAffine", **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img1, img2, affine):
        img1 = toSeq(img1)
        img2 = toSeq(img2)
        result = img1.copy()
        if affine and affine != 'Affine':
            affine = eval(affine)
            result.drawaffine(img2, affine)
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['affine'] = {
            'class': 'NEEntry',
            'initialValue': 'Affine',
            'master': 'node',
            'width': 15,}

        self.inputPortsDescr.append({
            'name': 'img1',
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'img2',
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'affine',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

class getImage(NetworkNode):
    """Gets an image from an image sequence.

    Index: starts from 0"""

    def __init__(self, name='getImage', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw)

        code = """def doit(self, img, index):
        img = toSeq(img)
        index = int(index)
        if index >= 0 and index < len(img):
            result = img[index]
        else:
            result = img.copy()
        self.outputData(outImage=result)\n"""

        self.setFunction(code)

        self.widgetDescr['index'] = {
            'class': 'NEEntry',
            'initialValue': 'Index',
            'master': 'node',
            'width': 5,}

        self.inputPortsDescr.append({
            'name': 'img',
            'singleConnection':False,
            'datatype': 'imimage'})
        self.inputPortsDescr.append({
            'name': 'index',
            'datatype': 'str'})
        self.outputPortsDescr.append({
            'name': 'outImage',
            'datatype': 'imimage'})

## Animate: see Animate under Input/Output ##

### Vision Code ###
from Vision.VPE import NodeLibrary
ImageMagick = NodeLibrary('ImageMagick', '#336699')

ImageMagick.addNode(Read, 'Read Image', 'Input/Output')
ImageMagick.addNode(Write, 'Write Image', 'Input/Output')
ImageMagick.addNode(toPIL, 'To PIL', 'Input/Output')
ImageMagick.addNode(TkDisplay, 'Tkinter Display', 'Input/Output')
ImageMagick.addNode(Display, 'Display', 'Input/Output')
ImageMagick.addNode(Animate, 'Animate', 'Input/Output')
ImageMagick.addNode(Copy, 'Copy', 'Input/Output')
ImageMagick.addNode(toArray, 'To Array', 'Input/Output')
ImageMagick.addNode(getPixels, 'Get Pixels', 'Input/Output')


### memory error
##ImageMagick.addNode(Describe, 'Describe', 'Input/Output')

ImageMagick.addNode(Halve, 'Halve', 'Size')
ImageMagick.addNode(Double, 'Double', 'Size')
ImageMagick.addNode(ResizeFactor, 'Resize by Factor', 'Size')
ImageMagick.addNode(ResizeWidth, 'Resize by Width', 'Size')
ImageMagick.addNode(ResizeHeight, 'Resize by Height', 'Size')
ImageMagick.addNode(ResizeDim, 'Resize to Dimensions', 'Size')
ImageMagick.addNode(SampleWidth, 'Sample by Width', 'Size')
ImageMagick.addNode(SampleHeight, 'Sample by Height', 'Size')
ImageMagick.addNode(SampleDim, 'Sample to Dimensions', 'Size')
ImageMagick.addNode(ScaleWidth, 'Scale by Width', 'Size')
ImageMagick.addNode(ScaleHeight, 'Scale by Height', 'Size')
ImageMagick.addNode(ScaleDim, 'Scale to Dimensions', 'Size')
ImageMagick.addNode(ResizeFactor, 'Thumbnail by Factor', 'Size')
ImageMagick.addNode(ResizeWidth, 'Thumbnail by Width', 'Size')
ImageMagick.addNode(ResizeHeight, 'Thumbnail by Height', 'Size')
ImageMagick.addNode(ResizeDim, 'Thumbnail to Dimensions', 'Size')

ImageMagick.addNode(Rotate, 'Rotate', 'Transform')
ImageMagick.addNode(Flip, 'Flip', 'Transform')
ImageMagick.addNode(Flop, 'Flop', 'Transform')
ImageMagick.addNode(Chop, 'Chop', 'Transform')
ImageMagick.addNode(Crop, 'Crop', 'Transform')
ImageMagick.addNode(Roll, 'Roll', 'Transform')
ImageMagick.addNode(Shave, 'Shave', 'Transform')
ImageMagick.addNode(Shear, 'Shear', 'Transform')
ImageMagick.addNode(Affine, 'Affine', 'Transform')

ImageMagick.addNode(Contrast, 'Contrast', 'Color')
ImageMagick.addNode(Colorize, 'Colorize', 'Color')
ImageMagick.addNode(Quantize, 'Quantize', 'Color')
ImageMagick.addNode(CompressMap, 'Compress Colormap', 'Color')
ImageMagick.addNode(Equalize, 'Equalize', 'Color')
ImageMagick.addNode(Normalize, 'Normalize', 'Color')
ImageMagick.addNode(Modulate, 'Modulate', 'Color')
ImageMagick.addNode(Negate, 'Negate', 'Color')
ImageMagick.addNode(Solarize, 'Solarize', 'Color')
ImageMagick.addNode(Gamma, 'Gamma Levels', 'Color')
ImageMagick.addNode(Level, 'Level', 'Color')
ImageMagick.addNode(OrderedDither, 'Ordered Dither', 'Color')
ImageMagick.addNode(Channel, 'Channel', 'Color')
ImageMagick.addNode(CycleColors, 'Cycle Colors', 'Color')
ImageMagick.addNode(LAT, 'LAT', 'Color')
ImageMagick.addNode(Segment, 'Segment', 'Color')
ImageMagick.addNode(LevelChannel, 'LevelChannel', 'Color')
ImageMagick.addNode(Threshold, 'Threshold', 'Color')

ImageMagick.addNode(Blur, 'Blur', 'Blur/Noise')
ImageMagick.addNode(Enhance, 'Enhance', 'Blur/Noise')
ImageMagick.addNode(AddNoise, 'Add Noise', 'Blur/Noise')
ImageMagick.addNode(Despeckle, 'Despeckle', 'Blur/Noise')
ImageMagick.addNode(MotionBlur, 'Motion Blur', 'Blur/Noise')
ImageMagick.addNode(ReduceNoise, 'Reduce Noise', 'Blur/Noise')
ImageMagick.addNode(Sharpen, 'Sharpen', 'Blur/Noise')
ImageMagick.addNode(UnsharpMask, 'UnsharpMask', 'Blur/Noise')

ImageMagick.addNode(Border, 'Border', 'Effects')
ImageMagick.addNode(Charcoal, 'Charcoal', 'Effects')
ImageMagick.addNode(Edge, 'Edge', 'Effects')
ImageMagick.addNode(Emboss, 'Emboss', 'Effects')
ImageMagick.addNode(OilPaint, 'Oil Paint', 'Effects')
ImageMagick.addNode(Frame, 'Frame', 'Effects')
ImageMagick.addNode(Implode, 'Implode', 'Effects')
ImageMagick.addNode(MedianFilter, 'Median Filter', 'Effects')
ImageMagick.addNode(Shade, 'Shade', 'Effects')
ImageMagick.addNode(Spread, 'Spread', 'Effects')
ImageMagick.addNode(Swirl, 'Swirl', 'Effects')
ImageMagick.addNode(Raise, 'Raise', 'Effects')
ImageMagick.addNode(Wave, 'Wave', 'Effects')
ImageMagick.addNode(Plasma, 'Plasma', 'Effects')
ImageMagick.addNode(Convolve, 'Convolve', 'Effects')

ImageMagick.addNode(Transparent, 'Transparent', 'Draw')
ImageMagick.addNode(FillOpaque, 'Fill Opaque', 'Draw')
ImageMagick.addNode(Erase, 'Erase', 'Draw')
ImageMagick.addNode(Set, 'Set', 'Draw')
ImageMagick.addNode(SetOpacity, 'Set Opacity', 'Draw')
ImageMagick.addNode(ColorFloodFill, 'Color Flood Fill', 'Draw')
ImageMagick.addNode(MatteFloodFill, 'Matte Flood Fill', 'Draw')
ImageMagick.addNode(Annotate, 'Annotate', 'Draw')
ImageMagick.addNode(Draw, 'Draw', 'Draw')
ImageMagick.addNode(ClipPath, 'Clip Path', 'Draw')
ImageMagick.addNode(SetPixels, 'Set Pixels', 'Draw')

ImageMagick.addNode(CreateSeq, 'Create Sequence', 'Multiple Images')
ImageMagick.addNode(Average, 'Average', 'Multiple Images')
ImageMagick.addNode(Diff, 'Difference', 'Multiple Images')
ImageMagick.addNode(Map, 'Map', 'Multiple Images')
ImageMagick.addNode(Mosaic, 'Mosaic', 'Multiple Images')
ImageMagick.addNode(Morph, 'Morph', 'Multiple Images')
ImageMagick.addNode(Append, 'Append', 'Multiple Images')
ImageMagick.addNode(Flatten, 'Flatten', 'Multiple Images')
ImageMagick.addNode(Animate, 'Animate', 'Multiple Images')
ImageMagick.addNode(Stegano, 'Watermark', 'Multiple Images')
ImageMagick.addNode(Stereo, 'Stereo', 'Multiple Images')
ImageMagick.addNode(Coalesce, 'Coalesce', 'Multiple Images')
ImageMagick.addNode(Composite, 'Composite', 'Multiple Images')
ImageMagick.addNode(Deconstruct, 'Deconstruct', 'Multiple Images')
ImageMagick.addNode(DrawAffine, 'Draw Affine', 'Multiple Images')
ImageMagick.addNode(getImage, 'Get Single Image', 'Multiple Images')

# Add "imimage" datatype
from NetworkEditor.datatypes import AnyArrayType
class IMImageType(AnyArrayType):

    from Image import Image
    def __init__(self, name='imimage', color='#07BAEE', shape='rect1',
                 klass=Image):

        AnyArrayType.__init__(self, name=name, color=color, shape=shape, 
                              klass=klass)

ImageMagick.typesTable = [IMImageType()]
