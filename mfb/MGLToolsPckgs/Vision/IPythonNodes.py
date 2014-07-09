from NetworkEditor.items import NetworkNode
from Vision.StandardNodes import RunFunction
from idlelib.EditorWindow import EditorWindow
from IPython.kernel import client
import Tkinter, Image, ImageTk, types, inspect, warnings

def importImageLib(net):
    try:
        from Vision.PILNodes import imagelib
        net.editor.addLibraryInstance(imagelib, 'Vision.PILNodes', 'imagelib')
    except:
        warnings.warn(
            'Warning! Could not import imagelib from Vision.PILNodes.py', stacklevel=2)


def computeLine(yrange):
    # size, bounds, MyF, maxIterationsPerPoint, distanceWhenUnbounded are
    # globals that need to be defined before calling computeLine
    #
    # width is the image width
    # bounds are the global bounds of the region of the complex plane

    #define our function to iterate with
    def MyF( x, c = 0.4 + 0.3j):
        return x*x + c

    width = float(size[0])
    height = float(size[1]) 
    dx = bounds[2]-bounds[0]
    dy = (bounds[3] - bounds[1])

    lines = []
    for y in yrange:
        line = []
        for x in range( int(width) ):

            #Calculate the (x,y) in the plane from the (x,y) in the BMP
            thisX = bounds[0] + (x/width)*dx
            thisY = (y/height)*dy
            thisY += bounds[1]

            #Create a complex # representation of this point
            thisPoint = complex(thisX, thisY)

            #Iterate the function until it grows unbounded
            nxt = MyF( thisPoint )
            numIters = 0
            while 1:
                dif = nxt-thisPoint
                if abs(nxt - thisPoint) > distanceWhenUnbounded:
                    break;
                if numIters >= maxIterationsPerPoint:
                    break;
                nxt = MyF(nxt)
                numIters = numIters+1

            #Convert the number of iterations to a color value
            colorFac = 255.0*float(numIters)/float(maxIterationsPerPoint)

            line.append( ( int(colorFac*0.8 + 32),
                           int(24+0.1*colorFac),
                           int(0.5*colorFac) ) )
        lines.append(line)

    return yrange, lines

class FractalDemo(NetworkNode):
    """
    This nodes demonstrates computing a fractal in parallel
    """
    
    def beforeAddingToNetwork(self, net):
        # import imagelib
        importImageLib(net)

    def __init__(self, name='FractalDemo', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype=None, name='mec')

        self.nbProc = None
        self.image = None # will be the PIL image
        self.display = None # will be the Tkinter.Label displaying the image
        self.size = (400, 400) # image size
        self.linesPerCall = 20

        self.widgetDescr['linesPerCall'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':10,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'linesPerCall:'},
            }
        self.inputPortsDescr.append(datatype='int', name='linesPerCall')
        
        self.widgetDescr['imageSize'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':400, 'min':200, 
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Image Size:'},
            }
        self.inputPortsDescr.append(datatype='int', name='imageSize')

        self.outputPortsDescr.append(datatype='image', name='image')
        
        code = """def doit(self, mec, linesPerCall, imageSize):

    self.nbProc = len(mec.get_ids())

    self.size = (imageSize,imageSize)
    # define globals in engines
    mec.execute("bounds = (-0.6, -0.6, 0.4, 0.4 )")
    mec.execute("maxIterationsPerPoint=64")
    mec.execute("distanceWhenUnbounded=3.")
    mec.execute("size=%s"%str(self.size))

    # push the computeLine function to the engines
    #function = computeLine
    #mec.push_function(dict(function.__name__=function.__name__))

    # push the function to iterate
    #function = MyF
    #mec.push_function(dict(function.__name__=function.__name__))

    im = Image.new('RGBA', self.size)
    # make it a photo image and display it
    photo = ImageTk.PhotoImage(im)
    self.display.configure(image=photo)
    self.display.image = im 

    # now farm out the computation of lines in batches of self.nbProc
    pix = im.load()
    
    nbBlocs = self.size[1]/(self.nbProc*linesPerCall)

    for bloc in range(nbBlocs):
        lineIndices = []
        for proc in range(self.nbProc):
            off = bloc*linesPerCall + proc*nbBlocs*linesPerCall
            lineIndices.append( range(off, off + linesPerCall) )

        #print 'AAAAA', lineIndices
        result = mec.map(computeLine, lineIndices)

        for res in result:
            for i,y in enumerate(res[0]):
                linePixels = res[1][i]
                for x, v in enumerate(linePixels):
                    pix[x, y] = v

        photo = ImageTk.PhotoImage(im)
        self.display.configure(image=photo)
        self.root.update()

    self.photo = photo

    self.outputData(image=im)
"""

        self.setFunction(code)


    def afterAddingToNetwork(self):
        # create a label with a photo image to display result
        import Tkinter
        root = self.root = Tkinter.Toplevel()
        # create an image
        self.image = im = Image.new('RGBA', self.size)
        # make it a photo image and display it
        photo = ImageTk.PhotoImage(im)
        label = self.display = Tkinter.Label(root, image=photo)
        label.image = im # keep a reference!
        label.pack()



class IPmecBase(NetworkNode):
    """
    Base class for creating IPmec nodes
"""
    def __init__(self, name='MEC', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

    def afterAddingToNetwork(self):
        NetworkNode.afterAddingToNetwork(self)
        top = Tkinter.Toplevel()
        top.withdraw()
        ed = EditorWindow(root=top)
        ed.top.withdraw()
        self.top = ed.top
        self.editorDialogue = ed
        b=Tkinter.Button(master=ed.status_bar,
                         text='Apply', command=self.applyCmd)
        b.pack(side='left')


    def applyCmd(self, event=None):
        self.mecCode = self.editorDialogue.io.text.get("1.0", 'end')
        for line in self.mecCode.split('\n'):
            if len(line):
                print self.mec.execute(line)

    def pass_cb(self, event=None):
        pass

    def show(self, event=None):
        # reset source code
        self.editorDialogue.io.text.delete("1.0", "end")
        self.editorDialogue.io.text.insert("1.0", self.mecCode)
        self.top.deiconify()

    def hide(self, event=None):
        self.top.withdraw()


class IPmec(IPmecBase):
    """A node for connecting to a running MultiEngineController object

inputs:
    furl: foolscap URL or the controller, empty string will pick up default engine
    cmds: python code to executed in all engines. typically imports of needed things
    
outputs:
    mec: a MEC instance
"""
    def afterAddingToNetwork(self):
        IPmecBase.afterAddingToNetwork(self)

        # look for an existin furl and set its value as the default
        from IPython.genutils import get_security_dir
        import os
        d = get_security_dir()
        filename = os.path.join( d, "ipcontroller-mec.furl") 
        if os.path.exists( filename ):
            f = open(filename)
            data = f.readlines()
            f.close()
        self.inputPorts[0].widget.set(data[0], 0)


    def __init__(self, name='MEC', **kw):
        kw['name'] = name
        apply( IPmecBase.__init__, (self,), kw )
        self.mec = None
        self.mecCode = ""
        self.targets = 'all'

        self.widgetDescr['furl'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'furl:'},
            'initialValue':''}

        self.widgetDescr['codeEditor'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':0, 'labelCfg':{'text':'code editor'},
            }

	self.widgetDescr['engineSelector'] = {
            'class':'NEMultiCheckButtons', 'lockedOnPort':True,
            'valueList':None, #'callback':self.myCallback,
            'sfcfg':{'hull_width':10,'hull_height':4},
            'labelCfg':{'text':'Select working engines'} }

        self.inputPortsDescr.append(datatype='string', name='furl')
        self.inputPortsDescr.append(datatype='int', name='codeEditor')
        self.inputPortsDescr.append(datatype='None', name='engineSelector')
        
        self.outputPortsDescr.append(datatype=None, name='mec')

        code = """def doit(self, furl, codeEditor, engineSelection):

    print 'engineSelection:', engineSelection

    if self.inputPorts[1].hasNewValidData():
        if codeEditor:
            self.show()
        else:
            self.hide()

    if self.inputPorts[0].hasNewValidData():
        if furl=='':
            furl = None
        self.mec = client.MultiEngineClient(furl)
        procs = self.mec.get_ids()
        values = []
        for p in procs:
           values.append( (str(p), {'value':1}) )
        self.inputPorts[2].widget.widget.rebuild(values)
        nbProc = len(procs)
        self.rename('mec_%dproc'%nbProc)
        self.applyCmd()
    
    self.targets = []
    procs = self.mec.get_ids()
    i = 0
    for n,v in engineSelection:
        if v:
            self.targets.append(procs[i])
        i+=1
    self.mec.targets = self.targets
    self.outputData(mec=self.mec)
"""
        self.setFunction(code)


class IPLocalMEC2(IPmecBase):
    """
    This will create a controller with 2 engines on the local host
    and connect to it.

    inputs:
        cmds: python code to executed in all engines. 
              typically imports of needed things
    outputs:
        mec: a MEC instance
"""

    def beforeRemovingFromNetwork(self):
        if self.mec is not None:
            self.mec.kill(True)

    def afterAddingToNetwork(self):
        IPmecBase.afterAddingToNetwork(self)
        self.startController(self.nbEngines)

    def startController(self, nbEngines):
        import sys, os

        # get Python executable
        p = sys.executable

        # build path to ipcluster-script.py
        ipcl = os.path.join(os.path.split(p)[0], 'Scripts', 'ipcluster-script.py')

        # create a .bat file (else I don;t know how to start in batch)
        import tempfile
        f, fname = tempfile.mkstemp(suffix='.bat',text=True)
        os.write(f, '"%s" "%s" local -xy -n %d\n'%(p, ipcl,nbEngines))
        os.close(f)

        # start bat file in batch
        os.system('start '+fname)

        #import time
        #time.sleep(10)
        # connect to the MEC
        
        
    def __init__(self, name='MEC2local', **kw):
        kw['name'] = name
        apply( IPmecBase.__init__, (self,), kw )
        self.nbEngines = 2
        self.mec = None
        self.mecCode = ""

        self.widgetDescr['codeEditor'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':0, 'labelCfg':{'text':'code editor'},
            }

        self.inputPortsDescr.append(datatype='int', name='codeEditor')
        
        self.outputPortsDescr.append(datatype=None, name='mec')

        code = """def doit(self, codeEditor):
    
    if self.mec is None:
        # find the fulr of the controller
        import user, os
        furlFile = os.path.join(user.home, "_ipython", "security", "ipcontroller-mec.furl")
        f = open(furlFile)
        data = f.readlines()
        f.close()

        self.furl = data[0]
        from IPython.kernel import client
        self.mec = client.MultiEngineClient(self.furl)

    if self.inputPorts[0].hasNewValidData():
        if codeEditor:
            self.show()
        else:
            self.hide()

        self.applyCmd()
        
    self.outputData(mec=self.mec)
"""
        self.setFunction(code)


class IPLocalMEC3(IPLocalMEC2):
    def __init__(self, name='MEC3local', **kw):
        kw['name'] = name
        apply( IPLocalMEC2.__init__, (self,), kw )
        self.nbEngines = 3

class IPLocalMEC4(IPLocalMEC2):
    def __init__(self, name='MEC3local', **kw):
        kw['name'] = name
        apply( IPLocalMEC2.__init__, (self,), kw )
        self.nbEngines = 4

class IPLocalMEC5(IPLocalMEC2):
    def __init__(self, name='MEC3local', **kw):
        kw['name'] = name
        apply( IPLocalMEC2.__init__, (self,), kw )
        self.nbEngines = 5

class IPLocalMEC6(IPLocalMEC2):
    def __init__(self, name='MEC3local', **kw):
        kw['name'] = name
        apply( IPLocalMEC2.__init__, (self,), kw )
        self.nbEngines = 6

class IPLocalMEC7(IPLocalMEC2):
    def __init__(self, name='MEC3local', **kw):
        kw['name'] = name
        apply( IPLocalMEC2.__init__, (self,), kw )
        self.nbEngines = 7

class IPLocalMEC8(IPLocalMEC2):
    def __init__(self, name='MEC3local', **kw):
        kw['name'] = name
        apply( IPLocalMEC2.__init__, (self,), kw )
        self.nbEngines = 8


class IPScatter(NetworkNode):
    """A node for distributing data to engines of a MEC

inputs:
    data: vector of data to be scattered
    varname: name of the variable holding the partial vectors onm the engines
    mec: MEC instance
    
outputs:
    mec: a MEC instance
"""
    def __init__(self, name='Scatter', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['varname'] = {
            'class': 'NEEntry', 'width':10,
            'initialValue':'v0',
            'master':'node',
            'labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'variable name'},
            }
        self.inputPortsDescr.append(datatype='list', name='data')
        self.inputPortsDescr.append(datatype='string', name='varname')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=None, name='mec')
        self.outputPortsDescr.append(datatype='string', name='varname')
        
        code = """def doit(self, data, varname, mec):
    print mec.scatter(varname, data)
    self.outputData(varname=varname, mec=mec)
"""
                
        self.setFunction(code)



class IPGather(NetworkNode):
    """A node for retrieving data from engines

inputs:
    varname: name of the variable holding the partial vectors onm the engines
    mec: MEC instance
    
outputs:
    data: gathered data
"""
    def __init__(self, name='Gather', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['varname'] = {
            'class': 'NEEntry', 'width':10,
            'initialValue':'v0',
            'master':'node',
            'labelGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'variable name'},
            }
        self.inputPortsDescr.append(datatype='string', name='varname')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=list, name='data')
        
        code = """def doit(self, varname, mec):
    data = mec.gather(varname)
    self.outputData(data=data)
"""
                
        self.setFunction(code)
   

class IPPull(NetworkNode):
    """A node for fetching data from engines of a MEC

inputs:
    varname: name of the variable holding the partial vectors onm the engines
    mec: MEC instance
    
outputs:
    data: a single list of all data from all engines
    dataPerEngine: a list of data from each engine
"""
    def __init__(self, name='Pull', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype='string', name='varname')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=None, name='data')
        self.outputPortsDescr.append(datatype='list', name='dataPerEngine')

        code = """def doit(self, varname, mec):
    vall = []
    vperengine = []
    for engine in mec.get_ids():
        v = mec.pull(varname, [engine])
        vall.extend(v)
        vperengine.append(v)
    self.outputData(data=vall, dataPerEngine=vperengine)
"""

        self.setFunction(code)

   

class IPPush(NetworkNode):
    """A node for sending python objects to the engines of a MEC

inputs:
    objects: objects to be sent to the MEC engines
    mec: MEC instance
    
outputs:
"""
    def __init__(self, name='Push', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype=None, name='object',
                                    singleConnection=False)
        self.inputPortsDescr.append(datatype=None, name='mec')

        code = """def doit(self, objects, mec):
    for obj in objects:
        print mec.push(obj)
"""

        self.setFunction(code)

   
## OBSOLETE now that PRunFunction is available
##
## class IPPushFunction(NetworkNode):
##     """A node for sending python functions to the engines of a MEC

## inputs:
##     function: function to be sent to the MEC engines
##     mec: MEC instance
    
## outputs:
## """
##     def __init__(self, name='Push Func', **kw):
##         kw['name'] = name
##         apply( NetworkNode.__init__, (self,), kw )

##         self.inputPortsDescr.append(datatype=None, name='function')
##         self.inputPortsDescr.append(datatype=None, name='mec')

##         code = """def doit(self, function, mec):
##     print mec.push_function(dict([(function.__name__,function)]))
## """

##         self.setFunction(code)


class IPRunFunction(RunFunction):
    """Node to run a function in parallel in MEC engines

inputs:
    mec: Multi Engine Controller
    scatter: index of the arguement to be scattered across engines
    command: name or instance of the function to execute
    importString: statements to execute before command definition
    
output:
    result: values returned by the function
"""
    def __init__(self, functionOrString=None, importString=None,
                 posArgsNames=[], namedArgs={},
                 name='PRunFunc', **kw):
            
        # we do this to pass the variables into kw
        if functionOrString is not None or kw.has_key('functionOrString') is False:
            kw['functionOrString'] = functionOrString
        elif kw.has_key('functionOrString') is True:
            functionOrString = kw['functionOrString']
        if importString is not None or kw.has_key('importString') is False:
            kw['importString'] = importString
        elif kw.has_key('importString') is True:
            importString = kw['importString']
        if len(posArgsNames)>0 or kw.has_key('posArgsNames') is False:
            kw['posArgsNames'] = posArgsNames
        elif kw.has_key('posArgsNames') is True:
            posArgsNames = kw['posArgsNames']
        if len(namedArgs)>0 or kw.has_key('namedArgs') is False:
            kw['namedArgs'] = namedArgs
        elif kw.has_key('namedArgs') is True:
            namedArgs = kw['namedArgs']
        if name is not None or kw.has_key('name') is False:
            kw['name'] = name
        elif kw.has_key('name') is True:
            name = kw['name']

        apply( RunFunction.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        ip = self.inputPortsDescr
        ip.append(datatype=None, name='mec')
        ip.append(datatype='int', name='scatter')

        code = """def doit(self, mec, scatter, command, importString, *args):
    functionOrString = command
    import types
    if type(functionOrString) == types.StringType:
        # we add __main__ to the scope of the local function
        # the folowing code is similar to: "from __main__ import *"
        # but it doesn't raise any warning, and its probably more local
        # and self and in1 are still known in the scope of the eval function

        #mod = __import__('__main__')
        #for modItemName in set(dir(mod)).difference(dir()):
        #    locals()[modItemName] = getattr(mod, modItemName)
        from mglutil.util.misc import importMainOrIPythonMain
        lMainDict = importMainOrIPythonMain()
        for modItemName in set(lMainDict).difference(dir()):
            locals()[modItemName] = lMainDict[modItemName]

        if importString != '':
            exec(importString)
            print mec.execute(importString)
            
        lfunctionOrString = functionOrString
        while type(lfunctionOrString) == types.StringType:
             try:
                 function = eval(lfunctionOrString)
             except NameError:
                 function = None
             lfunctionOrString = function
    else:
        function = functionOrString
        functionOrString = None

    if function is None:
        return

    if function is not self.function:
        try:
            lFunction = eval(self.name)
            self.function = lFunction
        except NameError:
            pass

#    if function is not self.function or \
#      self.constrkw.has_key('functionOrString') is True and \
#       (   self.constrkw['functionOrString'] != "\'"+functionOrString+"\'" \
#       and self.constrkw['functionOrString'] != functionOrString ):

    if function is not self.function:
        # remember current function
        self.function = function
        if hasattr(function, 'name'):
            self.rename('PRun '+function.name)
        elif hasattr(function, '__name__'):
            self.rename('PRun '+function.__name__)
        else:
            self.rename('PRun '+function.__class__.__name__)

        print 'L pushing function', self.funcname
        print mec.push_function({self.funcname:function})
        print 'pulling', mec.execute('print %s'%self.funcname)
        
        # remove all ports beyond the function and the importString input ports 
        for p in self.inputPorts[4:]:
            self.deletePort(p, updateSignature=False)

        # get arguments description
        from inspect import getargspec
        if hasattr(function, '__call__') and hasattr(function.__call__, 'im_func'): 
            args = getargspec(function.__call__.im_func)
        else:
            args = getargspec(function)

        if len(args[0])>0 and args[0][0] == 'self':
            args[0].pop(0) # get rid of self

        allNames = args[0]

        defaultValues = args[3]
        if defaultValues is None:
            defaultValues = []
        nbNamesArgs = len(defaultValues)
        if nbNamesArgs > 0:
            self.posArgsNames = args[0][:-nbNamesArgs]
        else:
            self.posArgsNames = args[0]
        d = {}
        for name, val in zip(args[0][-nbNamesArgs:], defaultValues):
            d[name] = val

        self.namedArgs = d

        # create widgets and ports for arguments
        if hasattr(function, 'params') and type(function.params) == types.DictType:
            argsDescription = function.params
        else:
            argsDescription = {}
        self.buildPortsForPositionalAndNamedArgs(self.posArgsNames, self.namedArgs,
                                                 argsDescription=argsDescription,
                                                 createPortNow=True)

        # create the constructor arguments such that when the node is restored
        # from file it will have all the info it needs
        if functionOrString is not None:
            if type(functionOrString) == types.StringType:
                self.constrkw['functionOrString'] = "\'"+functionOrString+"\'"
            else:
                self.constrkw['functionOrString'] = functionOrString
            if importString is not None:
                self.constrkw['importString'] ="\'"+ importString+"\'"
            else:
                self.constrkw['importString'] ="\'\'"
        elif hasattr(function, 'name'):
            # case of a Pmv command
            self.constrkw['command'] = 'masterNet.editor.vf.%s'%function.name
        elif hasattr(function, '__name__'):
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = function.__name__
        else:
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = function.__class__.__name__

        self.constrkw['posArgsNames'] = str(self.posArgsNames)
        self.constrkw['namedArgs'] = str(self.namedArgs)
        
    elif self.function is not None:
        # get all positional arguments
        sig = ""
        numArg = 0
        for pn in self.posArgsNames:
            if numArg==scatter:
                print 'L scattering', pn, locals()[pn]
                print mec.scatter(pn, locals()[pn])
                print 'pull ',mec.pull(pn)
            else:
                print 'pushing', pn, locals()[pn]
                print mec.push({pn:locals()[pn]})
                print 'pull', mec.pull(pn)

            sig += pn+', '
            numArg += 1

        # build named arguments
        for arg in self.namedArgs.keys():
            if numArg==scatter:
                print mec.scatter(arg, locals()[arg])
            else:
                #print mec.push(dict(arg=locals()[arg]))
                mec[arg] = locals()[arg]
            sig += arg+'=' + arg+ ', '
            numArg += 1

        # call function

        #print mec.push(dict(posargs=poargs))
        #print mec.push(dict(kw=kw))
        s =  'result = %s('%self.funcname + sig[:-2]+' )'
        print 'EXECUTING2', s
        print mec.execute(s)
        
##         try:
##             if hasattr(function,'__call__') and hasattr(function.__call__, 'im_func'):
##                 s = 'result = %s.__call__('%self.funcname + sig[:-2]+' )'
##                 print 'EXECUTING1', s
##                 print mec.execute( s )
##             else:
##                 s =  'result = %s('%self.funcname + sig[:-2]+' )'
##                 print 'EXECUTING2', s
##                 print mec.execute(s)
##         except Exception, e:
##             warnings.warn(e)
##             result = None
        result = mec.gather('result')
        self.outputData(result=result)
"""
        if code: self.setFunction(code)
        # change signature of compute function
        self.updateCode(port='ip', action='create', tagModified=False)



class IPmap(NetworkNode):
    """A node for mapping a function to a sequence of data in parallel

inputs:
    function: function to apply to the data
    data: data 
    mec: MEC instance
    
outputs:
    data: data resulting from the mapping operation

example: parallel_result = mec.map(lambda x:x**10, range(32))
"""
    def __init__(self, name='Map', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append(datatype=None, name='function')
        self.inputPortsDescr.append(datatype=None, name='data')
        self.inputPortsDescr.append(datatype=None, name='mec')

        self.outputPortsDescr.append(datatype=None, name='data')

        code = """def doit(self, function, data, mec):
    assert callable(function)
    result = mec.map(function, data)
    self.outputData(data=result)
"""

        self.setFunction(code)


from Vision.VPE import NodeLibrary
iplib = NodeLibrary('IPython', 'grey75')

iplib.addNode(IPmec, 'MEC', 'Objects')
iplib.addNode(IPLocalMEC2, 'MEC2local', 'Objects')
iplib.addNode(IPLocalMEC3, 'MEC3local', 'Objects')
iplib.addNode(IPLocalMEC4, 'MEC4local', 'Objects')
iplib.addNode(IPLocalMEC5, 'MEC5local', 'Objects')
iplib.addNode(IPLocalMEC6, 'MEC6local', 'Objects')
iplib.addNode(IPLocalMEC7, 'MEC7local', 'Objects')
iplib.addNode(IPLocalMEC8, 'MEC8local', 'Objects')
iplib.addNode(IPPull, 'Pull', 'Communication')
iplib.addNode(IPPush, 'Push', 'Communication')
#iplib.addNode(IPPushFunction, 'Push Func', 'Communication')
iplib.addNode(IPScatter, 'Scatter', 'Communication')
iplib.addNode(IPGather, 'Gather', 'Communication')
iplib.addNode(IPmap, 'PMap', 'Mapper')
iplib.addNode(IPRunFunction, 'PRunFunc', 'Mapper')
iplib.addNode(FractalDemo, 'Fractal Demo', 'Demo')

## TYPES to define
## MEC
## function

## TODO
# locking flag for mec
# 
try:
    from Vision import UserLibBuild
    UserLibBuild.addTypes(iplib, 'Vision.PILTypes')
except:
    pass
