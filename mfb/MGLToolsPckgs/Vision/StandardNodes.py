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

import os
import warnings
import types
import numpy
import numpy.oldnumeric as Numeric
import Pmw, Tkinter
import string, types, re
from UserList import UserList
from NetworkEditor.items import NetworkNode, FunctionNode
from NetworkEditor.macros import MacroNode
import inspect

class Generic(NetworkNode):
    """A node prototype. The user needs to add input-, and output ports,
    and edit the compute function."""
    
    def __init__(self, name='Generic', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )


class ATEST(NetworkNode):
    """A node prototype. The user needs to add input-, and output ports,
    and edit the compute function."""
    
    def __init__(self, name='Generic', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='float(0)', name='singleFloat', required=False)
        ip.append(datatype='float(3)', name='float3', required=False)
        ip.append(datatype='float(>3)', name='floatmore3', required=False)
        ip.append(datatype='float(4,4)', name='float44', required=False)
        ip.append(datatype='float(>3 and <6)', name='float4or5', required=False)

        code = """def doit(self, singleFloat, float3, floatmore3, float44,
float4or5):
    print singleFloat, float3, floatmore3, float44, float4or5
"""
        self.setFunction(code)


class TestDefaultValues(NetworkNode):

    def __init__(self, name='ATEST', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='required')
        ip.append(datatype='None', required=False, name='optNodefault')
        ip.append(datatype='string', required=False, name='opt1', defaultValue='a')
        ip.append(datatype='float', required=False, name='opt2', defaultValue=3.14)

        code = """def doit(self, required, optNodefault, opt1, opt2):
    print 'required', required
    print 'optNodefault',optNodefault
    print 'opt1',opt1
    print 'opt2',opt2   
"""
        self.setFunction(code)

        

class HasNewData(NetworkNode):
    """ Node to evaluate if an input port gets new data

Input Ports
    in1: allows to pass a Python object and determine if it is new data.
Output Ports
    result: the input if new data
"""
    
    def __init__(self, name='HasNewData', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

	code = """def doit(self, in1):
    if self.inputPorts[0].hasNewValidData():
        self.outputData(result=in1)
    #else:
    #    return 'stop'
"""
            
	if code: self.setFunction(code)

	ip = self.inputPortsDescr
	ip.append(datatype='None', required=True, name='in1')

	self.outputPortsDescr.append(datatype='None', name='result')


class ListOf(NetworkNode):
    """Creates a list of Python objects from the ones sent into the node.
Each new object is added using a new uinput port. New input ports are
created on the fly when a connection is made to the first input port
called 'object'.

Input:
    object: connect to this port to create a new input port for a Python
            object to be added to the list
Output:
    datalist: list of Python objects
"""
    def __init__(self, name='LitsOf', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        # define a function that creates a new port each time a connection
        # to this port is made
        codeAfterConnect = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    op = conn.port1
    node = self.node
    newport = {'name':op.name, 'datatype':op.datatypeObject['name'],
               'afterDisconnect':self.node.codeAfterDisconnect,
               '_modified': True}
    ip = apply( node.addInputPort, (), newport )
    # create the connection to the new port
    newconn = self.network.connectNodes( op.node, node, op.name, ip.name )
    # delete the connection to the port
    self.network.deleteConnections([conn])
    # update the signature of the function
    self.node.updateCode(node)
    return newconn
"""
        # define a function to be bound to a newly created port (see above)
        # which will delete the port if the connection is deleted
        # to this port is created
        self.codeAfterDisconnect = """def afterDisconnect(self, p1, p2):
    # self refers to the port
    node = p2.node
    node.deletePort(p2)
"""
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='object', required=False,
                  balloon="connect data to be added to the list\nA new port will be created",
                  afterConnect=codeAfterConnect)
        
        op = self.outputPortsDescr
        op.append(datatype='list', name='datalist')

        code = """def doit(self, newport):
    vlist = []
    for p in self.inputPorts[1:]:
        vlist.append(p.getData())
    self.outputData(datalist=vlist)
"""
        self.setFunction(code)


class Zip(ListOf):
    """Zips together multiple lists of objects using the zip() Python function

New lists are added by connecting them to the the first port. Doing so will
create a new input ports on the fly.

Input:
    object: connect to this port to create a new input port for a Python
            object to be added to the list
    followed by any number of ports (one per list) created on the fly

Output:
    datalist: a single list whgere each element is a list contining 1 element
              fro each of the input lists
"""
    def __init__(self, name='zip', **kw):
        kw['name'] = name
        apply( ListOf.__init__, (self,), kw )

        code = """def doit(self, newport):
    lists = [ p.getData() for p in self.inputPorts[1:] ]
    if len(lists):
        self.outputData(datalist=apply(zip, tuple(lists) ) )
"""
        self.setFunction(code)


class Random(NetworkNode):
    """generate a random number, adds offset and multiplies by scale
    
Input:
    offset: offset to be added (float) defaults to -0.5
    scale: scaling factor (float) defaults to 2.0

Output:
    randomNumber: float between [off, (off+1)*scale] default [-1., 1.]
"""
    def __init__(self, name='Random', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='float', name='offset', required=False, defaultValue=.5)
        ip.append(datatype='float', name='scale', required=False, defaultValue=2.)

        self.widgetDescr['offset'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':-0.5, 'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'offset:'},
            }
        self.widgetDescr['scale'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'float', 'wheelPad':1,
            'initialValue':2.0, 'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'offset:'},
            }

        op = self.outputPortsDescr
        op.append(datatype='float', name='randomNumber')

        code = """def doit(self, offset, scale):
    from random import random
    self.outputData(randomNumber=(random()+offset)*scale)
"""
        self.setFunction(code)


class SelectOnExtension(NetworkNode):
    """The .. descrinbe here    
Input:
    a: kitof file names
    b: extension (no .)

Output:
    mnatching: list fo filename withmathcing extension.
"""
    def __init__(self, name='SelectOnExtendion', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        op = self.outputPortsDescr
        op.append(datatype='list', name='matching')

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='filenames')
        ip.append(datatype='string', name='extension')

        self.inNodeWidgetsVisibleByDefault = True
       
        self.widgetDescr['extension'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'extension'}}
            
        code = """def doit(self, filenames, extension):
    result = filter( lambda x, extension=extension: x.endswith(extension), filenames )
    self.outputData(matching=result)
"""
        self.setFunction(code)



class ExclusiveOR(NetworkNode):
    """The Xor node outputs the value from the input port that has new data
    
Input:
    a: first input 
    b: second input

Output:
    value: the value provided on either a or b. If both ports provide new data
           the value of the first port is output.
"""
    def __init__(self, name='ExclusiveOR', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        op = self.outputPortsDescr
        op.append(datatype='None', name='value')

        ip = self.inputPortsDescr
        ip.append(datatype='None', name='a', required=False)
        ip.append(datatype='None', name='b', required=False)
        
        code = """def doit(self, a, b):
    new_a = self.inputPorts[0].hasNewValidData()
    new_b = self.inputPorts[1].hasNewValidData()

    print new_a, a, new_b, b
#    if new_a and new_b:
#        print 'ERROR: both input ports of ExclusiveOR node have new value'
#        return 'stop'
    if new_a:
        self.outputData(value=a)
    else:
        self.outputData(value=b)
"""
        self.setFunction(code)


class Select(ListOf):
    """Takes multiple input ports and outputs values from the ports presenting
new data

New input ports are added by connecting output ports to the the first port.
Doing so will create a new input ports on the fly.

Input:
    object: connect to this port to create a new input port for a Python
            object to be added to the list
    followed by any number of ports (one per list) created on the fly

Output:
    datalist: a single list whgere each element is a list contining 1 element
              fro each of the input lists
"""
    def __init__(self, name='select', **kw):
        kw['name'] = name
        apply( ListOf.__init__, (self,), kw )

        code = """def doit(self, newport):
    values = []
    for p in self.inputPorts[1:]:
        if p.hasNewValidData():
            values.append( p.getData() )
    if len(values):
        self.outputData(datalist=values)
"""
        self.setFunction(code)

    

class DelayBuffer(NetworkNode):
    """A node that receives data and buffers it a user specified number of executions.  This canbe used to delay data in a a network.

Input Ports
    value:  next value to be added to the queue
    delay:  number of executions between the time data enters and is output
    
Output Ports
    value:  first value from the queue
"""
    def __init__(self, name='DelayBuffer', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['delay'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':1,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Qlen:'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='None', name='value',
                  balloon='valueto be appended to the queue')
        ip.append(datatype='int', name='delay')
        
        op = self.outputPortsDescr
        op.append(datatype='None', name='value')

        self.queue = []
        
        code = """def doit(self, value, delay):
    self.queue.append(value)
    if len(self.queue)<=delay:
        self.outputPorts[0].data = None
    else:
        val = self.queue[0]
        self.queue = self.queue[1:]
        self.outputData(value=val)
"""
        self.setFunction(code)


class FilenameOps(NetworkNode):
    """A node to manipulate filename

 Input Ports
    filename: this is a string representing a filename potentially with a path
    extList:  a space separated list of file extension with or without the
              extension separator symbol used to create filenames with these
              extensions
    withPath: when True the filenames with new extensions will be generated
              with the leading path
    
Output Ports
    dirname:   name of the file's directory. Will be an empty string if there is
               no path in front of the filename
    filename:  the name of the file including its extension
    basename:  file name stripped of its extension
    extension: the file name extension starting with the extension separator
    newfilenames: a list of filename using the basename and the list of
                 provided extensions
"""
    def __init__(self, name='FilenameOps', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='filename',
                  balloon='filename to be decomposed')

        self.widgetDescr['extList'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'extension list:'},
            'initialValue':''}

        ip.append(datatype='string', name='extList', required=False,
                  balloon='a list of extension used to create new filename')
        
	self.widgetDescr['withPath'] = {
            'class':'NECheckButton', 'master':'node', 'initialValue':1,
            'labelCfg':{'text':'with path'},
            }
        ip.append(datatype='boolean', name='withPath', required=False,
                  balloon='When True new filenames are generated with path',
                  defaultValue=True)
       
        op = self.outputPortsDescr
        op.append(datatype='string', name='dirname')
        op.append(datatype='string', name='filename')
        op.append(datatype='string', name='basename')
        op.append(datatype='string', name='extension')
        op.append(datatype='string', name='newfilenames')

        code = """def doit(self, filename, extList, withPath):

    import os.path

    # remove path and split into bname and ext
    name = os.path.basename(filename)
    bname, ext = os.path.splitext(name)

    # get the path
    dirname = os.path.dirname(filename)

    # if filenames with different extensions are requested build them
    if extList:
        nfnames = []

        # handke withPath variable
        if withPath:
            lname = os.path.join(dirname, bname)
        else:
            lname = bname

        # build list of names
        for e in extList.split():
            if e[0]==os.path.extsep:
                nfnames.append( lname + e )
            else:
                nfnames.append( lname + os.path.extsep + e )            
    else:
        nfnames = []

    # output all
    self.outputData(
        dirname = dirname,
        filename = name,
        basename = bname,
        extension = ext,
        newfilenames = nfnames
        )
"""
        self.setFunction(code)



class Filename(NetworkNode):
    """A node to generate filenames with an integer value
 Input Ports
    format: a string use to create the filename is 'frame%08d.png'
    number: number to be printed using format
    
Output Ports
    filenamee: the resulting filename
"""
    def __init__(self, name='Entry', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['format'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'format:'},
            'initialValue':'file%08d.png'}

        ip = self.inputPortsDescr
        ip.append(datatype='string', balloon='format string used to create a filename', name='format')
        ip.append(datatype='int', name='number')
        
        op = self.outputPortsDescr
        op.append(datatype='string', name='filename')

        code = """def doit(self, format, number):
    self.outputData(filename=format%number)
"""
        self.setFunction(code)

    
class NumberedFilename(NetworkNode):
    """A node to generate filenames with a trailling 0-padded integer value

 Input Ports
    directory: path to the folder containing the files
    baseName: name of each file withoutthe number
    padding:  number of digits in the file number
    suffix:   file extension
    number:   number of the file for which the name willbe created

 Output Ports
    filenamee: the resulting filename i.e. mydir/frame0002.png
"""
    def __init__(self, name='numberedName', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['directory'] = {
            'class':'NEEntryWithDirectoryBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'lockedOnPort':True, 
            'labelCfg':{'text':'directory: '}
            }

        self.widgetDescr['baseName'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'baseName:'},
            'initialValue':'file'}

        self.widgetDescr['padding'] = {
            'class':'NEThumbWheel','master':'node', 'lockedOnPort':True,
            'width':75, 'height':21, 'oneTurn':10, 'type':'int', 'wheelPad':2,
            'initialValue':0, 'min':0,
            'labelCfg':{'text':'padding'} }

        self.widgetDescr['suffix'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'suffix:'},
            'initialValue':'.png'}

        ip = self.inputPortsDescr
        ip.append(datatype='string', balloon='path to the folder containing the files', name='directory')
        ip.append(datatype='string', balloon='base string used to create a filename', name='baseName')
        ip.append(datatype='int', name='padding')
        ip.append(datatype='string', name='suffix')
        ip.append(datatype='int', name='number')

        op = self.outputPortsDescr
        op.append(datatype='string', name='filename')

        code = """def doit(self, directory, baseName, padding, suffix, number):
    import os.path
    format = baseName + '%'
    if padding != 0:
        format += '0' + str(padding)
    if suffix:
        format += 'd' + suffix
    else:
        format += 'd'
    #print "format", format
    if directory:
        name =  os.path.join(directory,format%number)
    else:
        name = format%number
    self.outputData(filename=name)
"""
        self.setFunction(code)



class Filelist(NetworkNode):
    """
    Generate a list of file names matching a string with wildcards

    Input Ports
        directory: root directory from where the search for files matching
                   the matchstring will be searched (Optional)
                   
        matchstring: a string containing wildcards. Wildcards are the same
                     as the ones used nunix shells:
                       e.g.  * : any number of nay character
                             ? : any 1 character
                             [abc] : either a b or c in this position
                             
    Output Ports
        filenames: a list of file names matching matchstring in directory

   
   Note: matchstring can contain path elements that contain wildcards.
         for instance */*.py ill match all .py file in the all current
         sub-directories
"""
    def __init__(self, name='Entry', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['directory'] = {
            'class':'NEEntryWithDirectoryBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'lockedOnPort':True, 
            'labelCfg':{'text':'directory: '}
            }

        self.widgetDescr['match_str'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'match string:'},
            'initialValue':'*'}


        ip = self.inputPortsDescr
        ip.append(datatype='string',
                  balloon='directory where to apply match string',
                  name='directory')

        ip.append(datatype='string',
                  balloon='string used to select filenames', name='match_str')
        
        op = self.outputPortsDescr
        op.append(datatype='list', name='filelist')

        code = """def doit(self, directory, match_str ):
    import glob, os
    if directory is not None:
        cwd = os.getcwd()
        os.chdir(directory)
    try:
        values = glob.glob(match_str)
        filenames = [ os.path.join(directory, x) for x in values ]
        self.outputData(filelist=filenames)
    finally:
        if directory is not None:
            os.chdir(cwd)
"""
        self.setFunction(code)


    
class EntryNE(NetworkNode):
    """A Tkinter Entry widget.
Double-clicking on the node opens the entry widget.

Input Ports
    button: (bound to checkbutton widget)

Output Ports
    value: a integer describing the status of the checkbutton (1 on, 0 off)
"""

    def __init__(self, name='Entry', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['entry'] = {
            'class':'NEEntry', 'master':'node', 'width':14,
            'labelCfg':{'text':''}, 'lockedOnPort':True }

        self.inputPortsDescr.append(datatype='string', name='entry')
        
        self.outputPortsDescr.append(datatype='string', name='string')

        code = """def doit(self, entry):
    if len(str(entry))!=0:
        self.outputData(string=entry)
"""

        self.setFunction(code)


class FileBrowserNE(NetworkNode):
    """A Tkinter Filebrowser. Double-clicking into the entry opens the
filebrowser."""

    def __init__(self, name='File Browser', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        #self.readOnly = 1                                                                   
        code = """def doit(self, filename):                                                  
    if filename:                                                                             
        self.outputData(filename=filename, AbsPath_filename=os.path.abspath(filename))       
"""

        self.setFunction(code)

        # show the entry widget by default                                                   
        self.inNodeWidgetVisibleByDefault = True

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'lockedOnPort':True,
            'labelCfg':{'text':'Filename: '}
            }

        self.inputPortsDescr.append(datatype='string', name='filename')

        self.outputPortsDescr.append(datatype='string', name='filename')
        self.outputPortsDescr.append(datatype='string', name='AbsPath_filename')
    

class DirBrowserNE(NetworkNode):
    """
    Directory browser. Double-clicking in the button to the right of the entry
    opens a file browser. the path returned are relative to the current
    directory.
"""
    
    def __init__(self, name='File Browser', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        #self.readOnly = 1
        code = """def doit(self, directory):
    import os
    if directory:
        self.outputData(directory=directory, AbsPath_directory=os.path.abspath(directory))
"""

        self.setFunction(code)

        # show the entry widget by default
        self.inNodeWidgetVisibleByDefault = True

        self.widgetDescr['directory'] = {
            'class':'NEEntryWithDirectoryBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'lockedOnPort':True, 
            'labelCfg':{'text':'directory: '}
            }

        self.inputPortsDescr.append(datatype='string', name='directory')

        self.outputPortsDescr.append(datatype='string', name='directory')
        self.outputPortsDescr.append(datatype='string', name='AbsPath_directory')

class MakeZipFileNE(NetworkNode):
    """
    Create a zip file from a directory

    Input: 

        input_directory: directory from which the zip file will be created.
        
        output_directory: directory to place resulting zip file.  

        output_name: name of the resulting zip file, without the .zip extension and directory path.

    Output:                                                                        

        zipfile: path to zip file
                                            
"""
    
    def __init__(self, name='File Browser', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        #self.readOnly = 1
        code = """def doit(self, input_directory, output_directory, output_name):
   
    from Vision.make_zip_file import make_zip_file
   
    zipname_abs = make_zip_file(input_directory, output_directory, output_name)

    self.outputData(zipfile=zipname_abs)
"""

        self.setFunction(code)

        # show the entry widget by default
        self.inNodeWidgetVisibleByDefault = True

        self.inputPortsDescr.append(datatype='string', name='input_directory')
        self.inputPortsDescr.append(datatype='string', required=False, name='output_directory')
        self.inputPortsDescr.append(datatype='string', required=False, name='output_name')

        self.outputPortsDescr.append(datatype='string', name='zipfile')


class ThumbWheelNE(NetworkNode):
    """A thumbwheel widget.
Double-clicking on the node opens a thumbwheel widget. Right-clicking on the
thumbwheel opens an options panel with various parameters such as set minimum
and maximum, increment, sensitivity, output as int or float and more.

Input Ports
    thumbwheel: (bound to thumbwheel widget)
    mini: dials minimum value (optional)
    maxi: dials maximum value (optional)

Output Ports
    value: value is of type int or float, depending on the thumbwheel  settings
"""

    def __init__(self, name='Thumbwheel', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.model = None
        self.resolution = 0
        self.inNodeWidgetsVisibleByDefault = True
        
        self.widgetDescr['thumbwheel'] = {
            'class':'NEThumbWheel','master':'node', 'lockedOnPort':True,
            'width':75, 'height':21, 'oneTurn':10, 'type':'float', 'wheelPad':2,
            'initialValue':0.0,
            'labelCfg':{'text':''} }

	self.inputPortsDescr.append(datatype='float', name='thumbwheel')
	self.inputPortsDescr.append(datatype='float', name='mini',
                                    required=False)
	self.inputPortsDescr.append(datatype='float', name='maxi',
                                    required=False)
        
        self.outputPortsDescr.append(datatype='float', name='value')

        code = """def doit(self, thumbwheel, mini, maxi):
    if thumbwheel is not None:
        w = self.inputPorts[0].widget
        if w:
            if mini is not None and self.inputPorts[1].hasNewValidData():
                w.configure(min=mini)
            if maxi is not None and self.inputPorts[2].hasNewValidData():
                w.configure(max=maxi)
        self.outputData(value=thumbwheel)
"""

        self.setFunction(code)


#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        # run this node so the value is output
#        self.run()
#        self.inputPorts[0].widget.configure = self.configure_NEThumbWheel
#        self.inputPorts[0].widget.widget.setType = self.setType_ThumbWheel
#        
#
#    def configure_NEThumbWheel(self, rebuild=True, **kw):
#        """specialized configure method for ThumbWheel widget"""
#        # overwrite the tw widget's configure method to set the outputPort
#        # data type when the dial is configured
#        w = self.inputPorts[0].widget
#        from NetworkEditor.widgets import NEThumbWheel
#        apply( NEThumbWheel.configure, (w, rebuild), kw)
#        dtype = kw.pop('type', None)
#
#        if dtype:
#            self.updateDataType(dtype)
#            
#
#    def setType_ThumbWheel(self, dtype):
#        """specialized setTyp method for mglutil ThumbWheel object"""
#        # overwrite the tw's setType method to catch type changes through
#        # the optionsPanel
#        from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
#        tw = self.inputPorts[0].widget.widget
#        apply( ThumbWheel.setType, (tw, dtype), {})
#        if type(dtype) == types.TypeType:
#            dtype = dtype.__name__
#
#        self.updateDataType(dtype)
#        self.inputPorts[1].setDataType(dtype, makeOriginal= True)
#        self.inputPorts[2].setDataType(dtype, makeOriginal= True)
#
#
#    def updateDataType(self, dtype):
#        port = self.outputPorts[0]
#        port.setDataType(dtype, tagModified=False)
#        if port.data is not None:
#            if type(dtype) == types.TypeType:
#                port.data = dtype(port.data)                
#            else:
#                port.data = eval("%s(port.data)"%dtype)



class ThumbWheelIntNE(ThumbWheelNE):
    """A thumbwheel widget providing an integer.
Double-clicking on the node opens a thumbwheel widget. Right-clicking on the
thumbwheel opens an options panel with various parameters such as set minimum
and maximum, increment, sensitivity, output as int or float and more.

Input Ports
    thumbwheel: (bound to thumbwheel widget)
    mini: dials minimum value (optional)
    maxi: dials maximum value (optional)

Output Ports
    value: value is of type int or float, depending on the thumbwheel  settings
"""

    def __init__(self, name='Thumbwheel', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.model = None
        self.resolution = 0
        self.inNodeWidgetsVisibleByDefault = True
        
        self.widgetDescr['thumbwheel'] = {
            'class':'NEThumbWheel','master':'node', 'lockedOnPort':True,
            'width':75, 'height':21, 'oneTurn':10, 'type':'int', 'wheelPad':2,
            'initialValue':0.0,
            'labelCfg':{'text':''} }

        self.inputPortsDescr.append(datatype='int', name='thumbwheel')
        self.inputPortsDescr.append(datatype='int', name='mini',
                                            required=False)
        self.inputPortsDescr.append(datatype='int', name='maxi',
                                            required=False)
        
        self.outputPortsDescr.append(datatype='int', name='value')

        code = """def doit(self, thumbwheel, mini, maxi):
    if thumbwheel is not None:
        w = self.inputPorts[0].widget
        if w:
            if mini is not None and self.inputPorts[1].hasNewValidData():
                w.configure(min=mini)
            if maxi is not None and self.inputPorts[2].hasNewValidData():
                w.configure(max=maxi)
        self.outputData(value=thumbwheel)
"""

        self.setFunction(code)



class DialNE(NetworkNode):
    """A dial widget. Double-clicking on the node opens a dial widget.
Right-clicking on the dial widget opens an options panel with various
parameters such as set minimum and maximum, increment, sensitivity, output
as int or float and more.

Input Ports
    dial: (bound to dial widget)
    mini: dials minimum value (optional)
    maxi: dials maximum value (optional)

Output Ports
    value: value is of type int or float, depending on the dial settings
"""

    def __init__(self, name='Dial', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['dial'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':1, 'type':'float', 'lockedOnPort':True,
            'initialValue':0.0,
            'labelCfg':{'text':''}}
        
        self.inputPortsDescr.append(datatype='float', name='dial')
        self.inputPortsDescr.append(datatype='float', name='mini',
                                            required=False)
        self.inputPortsDescr.append(datatype='float', name='maxi',
                                            required=False)
        
        self.outputPortsDescr.append(datatype='float', name='value')

        code = """def doit(self, dial, mini, maxi):
    if dial is not None:
        w = self.inputPorts[0].widget
        if w:
            if mini is not None and self.inputPorts[1].hasNewValidData():
                w.configure(min=mini)
            if maxi is not None and self.inputPorts[2].hasNewValidData():
                w.configure(max=maxi)
        self.outputData(value=dial)
"""

        self.setFunction(code)

#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        # run this node so the value is output
#        self.run()
#        self.inputPorts[0].widget.configure = self.configure_NEDial
#        self.inputPorts[0].widget.widget.setType = self.setType_Dial
#        
#
#    def configure_NEDial(self, rebuild=True, **kw):
#        """specialized configure method for Dial widget"""
#        # overwrite the dial widget's configure method to set the outputPort
#        # data type when the dial is configured
#        w = self.inputPorts[0].widget
#        from NetworkEditor.widgets import NEDial
#        apply( NEDial.configure, (w, rebuild), kw)
#        dtype = kw.pop('type', None)
#
#        if dtype:
#            self.updateDataType(dtype)
#            
#
#    def setType_Dial(self, dtype):
#        """specialized setTyp method for mglutil Dial object"""
#        # overwrite the Dial's setType method to catch type changes through
#        # the optionsPanel
#        from mglutil.gui.BasicWidgets.Tk.Dial import Dial
#        dial = self.inputPorts[0].widget.widget
#        apply( Dial.setType, (dial, dtype), {})
#        if type(dtype) == types.TypeType:
#            dtype = dtype.__name__
#
#        self.updateDataType(dtype)
#        self.inputPorts[1].setDataType(dtype, makeOriginal= True)
#        self.inputPorts[2].setDataType(dtype, makeOriginal= True)
#
#    def updateDataType(self, dtype):
#        port = self.outputPorts[0]
#        port.setDataType(dtype, tagModified=False)
#        if port.data is not None:
#            if type(dtype) == types.TypeType:
#                port.data = dtype(port.data)                
#            else:
#                port.data = eval("%s(port.data)"%dtype)



class DialIntNE(DialNE):
    """A dial widget providing an integer.
Double-clicking on the node opens a dial widget.
Right-clicking on the dial widget opens an options panel with various
parameters such as set minimum and maximum, increment, sensitivity, output
as int or float and more.

Input Ports
    dial: (bound to dial widget)
    mini: dials minimum value (optional)
    maxi: dials maximum value (optional)
    
Output Ports
    value: value is of type int or float, depending on the dial settings
"""

    def __init__(self, name='Dial', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['dial'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10, 'type':'int', 'lockedOnPort':True,
            'initialValue':0.0,
            'labelCfg':{'text':''}}
        
        self.inputPortsDescr.append(datatype='int', name='dial')
        self.inputPortsDescr.append(datatype='int', name='mini',
                                            required=False)
        self.inputPortsDescr.append(datatype='int', name='maxi',
                                            required=False)
        
        self.outputPortsDescr.append(datatype='int', name='value')

        code = """def doit(self, dial, mini, maxi):
    if dial is not None:
        w = self.inputPorts[0].widget
        if w:
            if mini is not None and self.inputPorts[1].hasNewValidData():
                w.configure(min=mini)
            if maxi is not None and self.inputPorts[2].hasNewValidData():
                w.configure(max=maxi)
        self.outputData(value=dial)
"""

        self.setFunction(code)



#class ShowHideGUI(NetworkNode):
#    """A Tkinter Checkbutton widget to show or hide the Vision GUI.
#
#**********************************************************
#DEPRECATED !!! node 'Show/Hide GUI' is DEPRECATED !!!
#use the menu 'Options' of the user panel instead
#**********************************************************
#
#We recommend this node is used to move its widget to a user-created panel.
#
#If the checkbutton is unchecked, the GUI is hidden. If the checkbutton was
#not moved to a user-created panel, the only way to show the Vision GUI again
#is to type 'ed.showGUI()' in your Python shell (without the quotes).
#
#Note: if the button is unchecked and the node is saved, we will execute this
#node upon restoring the network, to hide the GUI.
#
#Input Ports
#    button: (bound to checkbutton widget)
#"""
#
#    def __init__(self, name='Show/Hide GUI', **kw):
#        kw['name'] = name
#        apply( NetworkNode.__init__, (self,), kw )
#
#        self.model = None
#        self.resolution = 0
#        self.inNodeWidgetsVisibleByDefault = True
# 
#	self.widgetDescr['button'] = {
#            'class':'NECheckButton', 'master':'node',
#            'initialValue':1,
#            'labelCfg':{'text':'show/Hide GUI'},
#            }
#
#        self.inputPortsDescr.append(datatype='int', name='button')
#        
#        code = """def doit(self, button):
#    if button:
#        self.editor.showGUI()
#    else:
#        self.editor.hideGUI()
#"""
#
#        self.setFunction(code)
#
#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        # run this node so the value is output
#        self.run()
#
#
#    def getNodeDefinitionSourceCode(self, networkName, indent="",
#                                    ignoreOriginal=False):
#        """extend base class method to overwrite the setting of widget value:
#        if the widget is set to 0, we want to execute this node, which means
#        we want to hide the network editor."""
#        lines = []
#        txt = NetworkNode.getNodeDefinitionSourceCode(
#            self, networkName, indent, ignoreOriginal)
#
#        for t in txt:
#            newtxt = t.replace("inputPorts[0].widget.set(0,0)\n",
#                             "inputPorts[0].widget.set(0,1)\n")
#            lines.append(newtxt)
#        return lines
  
    
class ShowHideParamPanel(NetworkNode):
    """A Tkinter Checkbutton widget to show or hide a node's ParamPanel.

One or more nodes can be connected. If the checkbutton is checked, the
parameter panels of all connected nodes are shown (if available), if the
checkbutton is unchecked, the parameter panels of all connected nodes are
hidden.

Disconnecting a node with a shown panel hides this panel.

Input Ports
    nodes:  any outputport of a Vision node
    button: (bound to checkbutton widget)
"""

    def __init__(self, name='Show/Hide Panel', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.model = None
        self.resolution = 0
        self.inNodeWidgetsVisibleByDefault = True
 
	self.widgetDescr['button'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':1,
            'labelCfg':{'text':'ParamPanel'},
            }

        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    node = c.port1.node
    node.paramPanel.hide()
"""

        codeAfterConnect = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    self.node.run()
"""

        # Note: required=False since all we need is the connection to find out
        # which node is connected, we don't need the actual data
        self.inputPortsDescr.append(name='nodes', datatype='None',
                                    singleConnection='auto',
                                    required=False,
                                    beforeDisconnect=codeBeforeDisconnect,
                                    afterConnect=codeAfterConnect)
         
        self.inputPortsDescr.append(datatype='int', name='button')
        
        code = """def doit(self, nodes, button):

    conn = self.inputPorts[0].connections
    if len(conn) == 0:
        return

    for c in conn:
        node = c.port1.node
        if button:
            node.paramPanel.show()
        else:
            node.paramPanel.hide()
"""

        self.setFunction(code)



class CheckButtonNE(NetworkNode):
    """A Tkinter Checkbutton widget.
Double-clicking on the node opens the checkbutton widget.

Input Ports
    button: (bound to checkbutton widget)

Output Ports
    value: a integer describing the status of the checkbutton (1 on, 0 off)
"""

    def __init__(self, name='Checkbutton', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.model = None
        self.resolution = 0
        self.inNodeWidgetsVisibleByDefault = True
 
	self.widgetDescr['button'] = {
            'class':'NECheckButton', 'master':'node',
            'intialValue':0, 'lockedOnPort':True,
            'labelCfg':{'text':'check'},
            }

        self.inputPortsDescr.append(datatype='int', name='button')
        
        self.outputPortsDescr.append(datatype='int', name='value')
        self.outputPortsDescr.append(datatype='boolean', name='value_bool')

        code = """def doit(self, button):
    self.outputData(value=button, value_bool=button)
"""

        self.setFunction(code)

#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        # run this node so the value is output
#        self.run()


class ButtonNE(NetworkNode):
    """A Tkinter Button widget.
Double-clicking on the node opens the Button widget.

Input Ports
    button: (bound to checkbutton widget)

Output Ports
    value: a integer describing the status of the checkbutton (1 on, 0 off)
"""

    def __init__(self, name='Checkbutton', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.model = None
        self.resolution = 0
        self.inNodeWidgetsVisibleByDefault = True
 
	self.widgetDescr['button'] = {
            'class':'NEButton', 'master':'node', 'lockedOnPort':True,
            'labelCfg':{'text':'press me'},
            }

        self.inputPortsDescr.append(datatype='int', name='button')
        
        self.outputPortsDescr.append(datatype='int', name='value')

        code = """def doit(self, button):
    self.outputData(value=1)
"""

        self.setFunction(code)


class SaveLines(NetworkNode):
    """Saves list of strings to a file using Python's writelines().
Double-clicking on the node opens a text entry widget to type the file name.
In addition, double-clicking in the text entry opens a file browser window.

Input Ports
    data: list of strings to be saved
    filename: name of the file to be saved

Output Ports
    filename: string of the filename
"""

    def __init__(self, name='Save Lines', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        #self.readOnly = 1
        code = """def doit(self, data, filename):
    if filename and len(filename) and data and len(data):

        f = open(filename, 'w')
        f.writelines(data)
        f.close()
        import os
        self.outputData(filename=os.path.abspath(filename))
"""

        self.setFunction(code)

        fileTypes=[('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node',
            'filetypes':fileTypes, 'title':'save file', 'width':16,
            'labelCfg':{'text':'file:'} }

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='data')
        ip.append(datatype='string', name='filename')

        self.outputPortsDescr.append(datatype='string', name='filename')



class TextEditor(NetworkNode):
    """Allows user to edit a file using a text editor on the local computer.
Input Ports
    filename: name of the file to be edited
Ouput Ports
    filename: string of the filename
"""
    def __init__(self, name='Text editor', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        if os.name == 'nt' or os.name == 'dos':
           texteditor = 'notepad.exe'
        elif os.name == 'posix':
           if os.uname()[0] == 'Darwin':
              texteditor = '/Applications/TextEdit.app/Contents/MacOS/TextEdit'       
           else:
              texteditor = 'emacs'
        else:
            texteditor = ''

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'lockedOnPort':True, 
            'labelCfg':{'text':'filename: '}}

        self.widgetDescr['texteditor'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':texteditor, 'lockedOnPort':True, 
            'labelCfg':{'text':'text editor: '}}

        self.inputPortsDescr.append(datatype='string', name='filename')
        self.inputPortsDescr.append(datatype='string', name='texteditor')
        self.outputPortsDescr.append(datatype='string', name='filename')

        code = """def doit(self, filename, texteditor):
    if filename != '' and texteditor != '':
        self.outputData(filename=filename)
        if os.name == 'posix':
            os.system(texteditor + ' ' + filename + ' &')
        else:
            os.system(texteditor + ' ' + filename)
"""
        self.setFunction(code)



class OpenFile(NetworkNode):
    """Opens a file using OS specific application (open_prog) that defaults to 'explorer' on Windows, 
'open' on Mac OS X and 'gnome-open' on Linux/Unix. 
Input Ports
    filename: name of the file to be open
Ouput Ports
    filename: string of the filename
"""
    def __init__(self, name='Open', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        
        if os.name == 'nt' or os.name == 'dos':
            open_prog = 'explorer'
        elif os.name == 'posix':
           if os.uname()[0] == 'Darwin':
               open_prog = 'open'
           else:
               open_prog = 'gnome-open'
        else:
            open_prog = ''

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'labelCfg':{'text':'filename:'}}

        self.widgetDescr['open_prog'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':open_prog, 'lockedOnPort':False, 
            'labelCfg':{'text':'open program: '}}

        self.inputPortsDescr.append(datatype='string', name='filename')
        self.inputPortsDescr.append(datatype='string', name='open_prog')
        self.outputPortsDescr.append(datatype='string', name='filename')

        code = """def doit(self, filename, open_prog):
    if filename != '' and open_prog != '':
        if os.name == 'nt' or os.name == 'dos':
            if filename.find(":") == -1:
                filename = os.path.normpath(filename)

        self.outputData(filename=filename)
        os.system(open_prog + ' ' + filename)
"""
        self.setFunction(code)



class Pass(NetworkNode):
    """Pass data.

Input Ports
    in1: any type of data

Output Ports
    out: same as in1

Notes
    The data is output 'as is', no processing is performed.
"""

    def __init__(self, name='Pass', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, in1):
    if in1 is not None:
        self.outputData(out1=in1)
"""
            
        if code: self.setFunction(code)

        # connecting to a pass node sets the output port datatype
        afterConnectCode = """def afterConnect(self, conn):
    self.node.outputPorts[0].configure(datatype=conn.port2.datatypeObject['name'])
"""
        # disconnecting to a pass node resets the output port datatype to None
        afterDisconnectCode = """def afterDisconnect(self, port1, port2):
   self.node.outputPorts[0].configure(datatype='None')
"""
        
        self.inputPortsDescr.append(name='in1', datatype='None',
                                    afterConnect=afterConnectCode,
                                    afterDisconnect=afterDisconnectCode,
                                    )
        
	self.outputPortsDescr.append(datatype='None', name='out1')


class Map(NetworkNode):
    """Applies function typed by user to object comming in

Input Ports
    dataList: any type of sequence data
    functions: function to be mapped to data in dataList
    
Output Ports
    out: list of results
"""

    def __init__(self, name='Map', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, dataList, function):
    if function is not None \
      and dataList is not None \
      and len(dataList) > 0:
        func = eval(function)
        self.outputData(out=map(func, dataList))\n
"""
            
        if code: self.setFunction(code)

        self.widgetDescr['function'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'function:'}}

	ip = self.inputPortsDescr
        ip.append(datatype='None', name='dataList')
	ip.append(datatype='string', name='function')

	self.outputPortsDescr.append(datatype='None', name='out')


class Counter(NetworkNode):
    """Works same as the Pass node but in addition every time this node runs,
its internal counter increments by 1. The counter can be reset through a button
bound to the node.

Input Ports
    in1: any type of data
    reset: reset the counter, bound to a button

Output Ports
    out1: same as in1
    counts: # of counts

Notes
    The data is output on out1 'as is', no processing is performed.
"""

    def __init__(self, name='Counter', **kw):
        kw['name'] = name
        self.counter = 0 # increments every time the node runs
        
        apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, in1, reset):
    self.counter = self.counter + 1
    self.outputData(out1=in1, counts=self.counter)
"""
            
        if code: self.setFunction(code)

        self.widgetDescr['reset'] = {
            'class':'NEButton', 'master':'node',
            'command':self.reset,
            'text':'Reset',
            'labelCfg':{'text':'hello'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='None', required=False, name='in1')
	ip.append(datatype='int', required=False, name='reset')

	op = self.outputPortsDescr
        op.append(datatype='None', name='out1')
	op.append(datatype='int', name='counts')


    def reset(self):
        # reset counter
        self.counter = -1 # node will run once, thus counter will be 0
        # run to output 0 as new counter
        self.inputPorts[1].widget.scheduleNode()
        

class ReadTable(NetworkNode):
    """Parse a file that is expected to provide a table of numbers.
Lines starting with # are comments and are ignored.

Input Ports
    filename: filename of the file to parse
    datatype: data type can be 'int', 'float' or 'string'
              (bound to a multiradio check button)
    sep: separator character
    
Output Ports
    data: the resulting 2D table
"""

    def __init__(self, name='NumericTable', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
##          self.mode = None # can be 'list' or 'instance'
        self.numData = None
        
        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'title':'browse files',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'file:'}, 'width':10,
            }

        self.widgetDescr['numOfTopLinesToJump'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'numOfTopLinesToJump:'},
            }

        self.widgetDescr['numOfBottomLinesToJump'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'numOfBottomLinesToJump:'},
            }

        self.widgetDescr['sep'] = {
            'class':'NEEntry', 'master':'node',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'sep:'}, 'width':10,
            }

        self.widgetDescr['datatype'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['int', 'float', 'str'],
            'fixedChoices':True,
            'initialValue':'str',
            'entryfield_entry_width':7,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'type:'}}

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='filename')
        ip.append(datatype='int', name='numOfTopLinesToJump')
        ip.append(datatype='int', name='numOfBottomLinesToJump')
        ip.append(datatype='string', name='sep')
        ip.append(datatype='string', name='datatype')

        self.outputPortsDescr.append(datatype='None', name='data')

        code = """def doit(self, filename, numOfTopLinesToJump,
numOfBottomLinesToJump, sep, datatype):
    if not filename:
        return

    if self.inputPorts[0].hasNewValidData() or self.inputPorts[3].hasNewValidData() \
       or self.inputPorts[4].hasNewValidData():
        f = open(filename)
        data = f.readlines()
        f.close()

        # numOfTopLinesToJump numOfBottomLinesToJump
        if numOfBottomLinesToJump > 0:
            data = data[numOfTopLinesToJump:-numOfBottomLinesToJump]
        else:
            data = data[numOfTopLinesToJump:]

        # get rid of comments
        self.data = data = filter(lambda x: x[0]!='#', data)
        
        # split the columns
        dtype = eval(datatype)
        if sep == '':
            sep = None

        numdata = []
        for d in data:
            numdata.append( map( dtype, d.split(sep) ) )

        result = self.numData = numpy.array(numdata)

    else:
        data = self.numData

        # numOfTopLinesToJump numOfBottomLinesToJump
        if numOfBottomLinesToJump > 0:
            result = data[numOfTopLinesToJump:-numOfBottomLinesToJump]
        else:
            result = data[numOfTopLinesToJump:]

    self.outputData(data=result)
"""
            
        if code: self.setFunction(code)


class StdDev(NetworkNode):
    """compute standard deviation for a list of values
    stddev = sqrt( [ n*sum(x^2) - sum(x)^2 ] / n*(n-1) )

Input Ports
    values: list of values

Output Ports
    result: standard deviation
"""
    
    def __init__(self, name='stddev', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='values')

        op = self.outputPortsDescr
        op.append(datatype='float', name='stddev')

        code = """def doit(self, values):
    sum = sum2 = 0.
    n = len(values)
    
    for value in values:
        sum += value
        sum2 += value*value
    from math import sqrt
    stddev = sqrt((n*sum2-sum*sum)/(n*(n-1)))
    self.outputData(stddev=stddev)
"""
        if code:
            self.setFunction(code)


class Operator1(NetworkNode):
    """apply unary operator to incomming value.

Input Ports
    data: any python object or list of python objects
    operation: unary operator available in operator module
    applyToElements: default=False. Should only be true if data is a sequence.
               When true the operator is applied to each element rather than
               the sequence

Output Ports
    result: result of applying operator to data
"""
    
    def __init__(self, name='Op1', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
        self.inNodeWidgetsVisibleByDefault = True

        code = """def doit(self, data, operation, applyToElements):
    if not operation:
        return
    if applyToElements is None:
        applyToElements = False
    import operator
    op = getattr(operator, operation)
    if not applyToElements:
        result = apply( op, (data,) )
        tp = self.network.getTypeManager().getTypeFromClass(result.__class__)
        self.outputPorts[0].setDataType(tp, tagModified=False)
    else:
        result = map( op, data )
        self.outputPorts[0].setDataType('list', tagModified=False)
    if result is not None:
        self.outputData(result=result)
"""
        if code: self.setFunction(code)

        self.widgetDescr['operation'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['not_', 'truth', 'abs', 'inv', 'neg', 'pos'],
            'fixedChoices':True,
            'initialValue':'abs',
            'entryfield_entry_width':5,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'operation'},
            'selectioncommand':self.rename,
            }

	self.widgetDescr['applyToElements'] = {
            'class':'NECheckButton', 'master':'node',
            'labelGridCfg':{'sticky':'w', 'columnspan':2},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'apply to elements'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='None', balloon='Data to be operated on',
                  name='data')
        ip.append(datatype='None', balloon='operation to be applied',
                  name='operation')
        ip.append(datatype='int', name='applyToElements')
        
        self.outputPortsDescr.append(datatype='None', name='result')



class Operator2(NetworkNode):
    """apply binary operator to incomming values.

Input Ports
    data1: any python object or list of python objects
    data2: any python object or list of python objects
    operation: unary operator available in operator module
    applyToElements: default=False. Should only be true if data is a sequence.
               When true the operator is applied to each element rather than
               the sequence

Output Ports
    result: result of applying operator to data
"""
    
    def __init__(self, name='Op2', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
        self.inNodeWidgetsVisibleByDefault = True

        code = """def doit(self, data1, data2, operation, applyToElements):
    if not operation:
        return

    ed = self.getEditor()
        
    haslen1 = haslen2 = True
    try:
       len(data1)
    except TypeError:
       haslen1 = False
    try:
       len(data2)
    except TypeError:
       haslen2 = False
       
    if applyToElements is None:
        applyToElements = False
    import operator
    op = getattr(operator, operation)

    if not applyToElements:
        result = apply( op, (data1, data2) )
        if result is None and operation == 'delitem':
            result = data1
        try:
            if hasattr(data1, str(result[0].__class__)):
                tp = self.network.getTypeManager().getTypeFromClass(result[0].__class__)
            else:
                tp = None
        except TypeError:
            if hasattr(data1, str(result.__class__)):
                tp = self.network.getTypeManager().getTypeFromClass(result.__class__)
            else:
                tp = None
        if tp is not None:
            self.outputPorts[0].setDataType(tp, tagModified=False)
                
    else: # apply operation to pairs of elements in sequence
        if not haslen1 and not haslen2:
            result = op(data1, data2)
            if result is None and operation == 'delitem':
                result = data1
            tp = self.network.getTypeManager().getTypeFromClass(result.__class__)
            self.outputPorts[0].setDataType(tp, tagModified=False)
        else:
            # if data1 is not a list, make one
            if not haslen1 and len(data2)>0:
                data1 = [data1]*len(data2)
            # if data2 is not a list, make one
            if not haslen2 and len(data1)>0:
                data2 = [data2]*len(data1)
            result = map( op, data1, data2 )
            if result is None and operation == 'delitem':
                result = data1            
            self.outputPorts[0].setDataType('list', tagModified=False)
    if result is not None:
        self.outputData(result=result)
"""
        if code: self.setFunction(code)

        self.widgetDescr['operation'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'is_', 'is_not',
                       'add', 'and', 'div', 'floordiv', 'lshift', 'mod',
                       'mul', 'or', 'pow', 'rshift', 'sub', 'truediv',
                       'xor', 'concat', 'contains', 'countOf', 'delitem',
                       'getitem', 'indexOf', 'repeat'],
            'fixedChoices':True,
            'entryfield_entry_width':8,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'operator'},
            'selectioncommand':self.rename,
            }

	self.widgetDescr['applyToElements'] = {
            'class':'NECheckButton', 'master':'node',
            'labelGridCfg':{'sticky':'w', 'columnspan':2},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'apply to elements'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='None', balloon='Data to be operated on',
                  name='data1')
        ip.append(datatype='None', balloon='Data to be operated on',
                  name='data2')
        ip.append(datatype='None', balloon='operation to be applied',
                  name='operation')
        ip.append(datatype='int', name='applyToElements')
        
        self.outputPortsDescr.append(name='result', datatype='None')
        

class Operator3(NetworkNode):
    """apply ternary operator to incomming values.

Input Ports
    data1: any python object or list of python objects
    data2: any python object or list of python objects
    data3: any python object or list of python objects
    operation: unary operator available in operator module
    applyToElements: default=False. Should only be true if data is a sequence.
               When true the operator is applied to each element rather than
               the sequence

Output Ports
    result: result of applying operator to data
"""

    def __init__(self, name='Op3', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)
        self.inNodeWidgetsVisibleByDefault = True
        
        code = """def doit(self, data, operation, from_, to_, applyToElements):
    ed = self.getEditor()
    if not operation:
        return
    if applyToElements is None:
        applyToElements = False
    import operator
    op = getattr(operator, operation)
    if not applyToElements:
        result = apply( op, (data, from_ , to_) )
        tp = self.network.getTypeManager().getTypeFromClass(result.__class__)
        self.outputPorts[0].setDataType(tp, tagModified=False)
    else:
        result = []
        for d in data:
           result.append( op( d, from_, to_ ))
    if result is not None:
        self.outputData(result=result)
"""
        if code: self.setFunction(code)

        self.widgetDescr['operation'] = {
            'class':'NEComboBox', 'master':'node',
            'entryfield_entry_width':8,
            'labelpos':None,
            'choices':['delslice', 'getslice', 'setitem'],
            'fixedChoices':True,
            'initialValue':'setitem',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2, 'pady':2},
            'labelCfg':{'text':'operator'},
            'selectioncommand':self.rename,
            }

        self.widgetDescr['from_'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'from:'},
            }

        self.widgetDescr['to_'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':80, 'height':20, 'type':'int', 'wheelPad':1,
            'initialValue':0.0,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'to:'},
            }

	self.widgetDescr['applyToElements'] = {
            'class':'NECheckButton', 'master':'node',
            'labelGridCfg':{'sticky':'w', 'columnspan':2},
            'widgetGridCfg':{'sticky':'w'},
            'labelCfg':{'text':'apply to elements'},
            }
                                               
        ip = self.inputPortsDescr
        ip.append(datatype='None', balloon='Data to be operated on',
                  name='data')
        ip.append(datatype='None', balloon='operation to be applied',
                  name='operation')
        ip.append(datatype='None', balloon='Data to be operated on',
                  name='from_')
        ip.append(datatype='None', balloon='Data to be operated on',
                  name='to_')
        ip.append(datatype='int', name='applyToElements')
        
        self.outputPortsDescr.append(name='result', datatype='None')


class Duplicate(NetworkNode):
    """Duplicate a Python object a user specified number of times into a list

Input Ports
    object: python object to be duplicated
    number: number of times the object should be duplicated

Output Ports
    dupObjects: list of duplicated objects
"""
    
    def __init__(self, name='BinaryOp', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        self.widgetDescr['number'] = {
            'class':'NEThumbWheel','master':'node',
            'width':75, 'height':21, 'oneTurn':10, 'type':'int', 'wheelPad':2,
            'initialValue':10, 'labelCfg':{'text':''}
            }
 	self.inputPortsDescr.append(datatype='None', name='object')
 	self.inputPortsDescr.append(datatype='int', name='number')
        
        self.outputPortsDescr.append(datatype='list', name='dupObjects')

       
        code = """def doit(self, object, number):
        self.outputData(dupObjects = [object]*number)
"""
        self.setFunction(code)



class Cast(NetworkNode):
    """Turn an incomming object into some other type.
The cast method of the newtype will be called with the incomming data.
If successful, the result will be output.

Input Ports
    data: any python object or list of python objects
    newtype: (bound to a combo box widget)
         name of a registered type as obtained from the editor's typeManager

Output Ports
    result: the new object
"""
    
    def __init__(self, name='Cast', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw)

        code = """def doit(self, data, newtype):
    ed = self.getEditor()
    newTypeInstance = self.network.getTypeManager().get(newtype, None)
    newdata = None
    from NetworkEditor.datatypes import AnyArrayType
    if isinstance(newTypeInstance, AnyArrayType):
        isAlreadyValid, newdata = newTypeInstance.validate(data)
    else:
        isAlreadyValid = newTypeInstance.validate(data)
        newdata = data
    if isAlreadyValid is False:
        if newTypeInstance:
            if self.name.startswith('Cast'):
                self.rename('Cast to '+ newTypeInstance.__class__.__name__)
            if self.inputPorts[0].singleConnection:
                try:
                    len(data) > -1
                    ans = map( newTypeInstance.cast, data)
                    if len(ans) == 2:
                        ok = min( map(lambda x: x[0], ans))
                        newdata = map( lambda x: x[1], ans)
                    else:
                        ok = min( map(lambda x: x[0][0], ans))
                        newdata = map( lambda x: x[0][1], ans)
                except:
                    ok, newdata = newTypeInstance.cast(data)
            else:
                ans = map( newTypeInstance.cast, data)
                ok = min( map(lambda x: x[0], ans))
                newdata = map( lambda x: x[1], ans)
    if isAlreadyValid or ok:
        op = self.outputPorts[0]
        op.setDataType(newTypeInstance, tagModified=False)
        if ed is not None:
            op.deleteIcon()
            op.createIcon()
        self.outputData(result=newdata)
"""
        if code: self.setFunction(code)

        self.widgetDescr['newtype'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':[''],
            #'autoList':True, # params are created when the node runs
            'entryfield_entry_width':14,
            'labelCfg':{'text':'type'}
            }

        ip = self.inputPortsDescr
        ip.append(datatype='None', balloon='Data to be coerced', name='data')
        ip.append(datatype='None', balloon='target data type', name='newtype')

        self.outputPortsDescr.append(name='result', datatype='None')


    def afterAddingToNetwork(self):
        allTypes = self.network.getTypeManager().portTypeInstances.keys()
        allTypes.sort()
        self.inputPorts[1].widget.setlist(allTypes)


class GetAttr(NetworkNode):
    """Get Python object attributes.
Double-clicking in the node opens a combo box widget. This widget displays all
available attributes of the object. If a list of objects is provided it is
assumed that they all have the same attributes and the list of attributes of
the first object is the list is used to populate the combobox.
The attribute can either be chosen by selecting it in the combo box or by
directly typing it into the combo box if it's name is known. When typed, the
attribute can contain '.' to access attributes of children objects (e.g.
'child.name' will retrieve the name attribute in the object child which itself
is an attribute of the object.

Input Ports
    objects: a list of Python objects
    attribute: (bound to a combo box widget)
               a string describing an attribute to be extracted for each
               object in the list. This string also supports recursive
               attribute retrieval using the '.' character. For example:
               a.b.c will retieve c from b which was found in a. Only c
               will be output.
Output Ports
    attrs: a list of attributes

Notes
    If one of the object is missing a required attribute an exception is
    raised.
"""

    def __init__(self, name='getattr', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        code ="""def doit(self, objects, attr):

##          ORIGINAL CODE FROM BEFORE AUG 18 2003
##          if attr is not None and len(attr):
##              self.rename('Get '+attr)
##          else:
##              self.rename('Getattr')

##          if self.inputPorts[0].singleConnection:
##              attrs = string.split(attr, '.')
##              result = reduce( getattr, [objects]+attrs )
##              self.outputData(attrs=result)
##          else:
##              if objects:
##                  allAttrs = dir(objects[0])
##                  if self.inputPorts[1].widget:
##                      self.inputPorts[1].widget.setlist(allAttrs)

##              results = []
##              for obj in objects:
##      #            if attr is None or attr=='':
##                  if attr=='':
##                      continue
##                  attrs = string.split(attr, '.')
##                  result = reduce( getattr, [obj]+attrs )
##                  if type(result) == types.ListType:
##                      results.extend( result )
##                  else:
##                      results.append( result )
##              self.outputData(attrs=results)


        if objects is None:
            return

        # rename node if we have an attr
        if self.name.startswith('getattr'):
            if attr is not None and len(attr):
                self.rename('getattr: '+attr)
            else:
                self.rename('getattr')

        # populate combobox with attrs 
        allAttrs = dir(objects[0])
        if self.inputPorts[1].widget: # could have been unbound by user
            #self.inputPorts[1].widget.setlist(allAttrs)
            self.inputPorts[1].widget.configure(choices=allAttrs)
                
        if attr:
            if self.inputPorts[0].singleConnection:
                attrs = string.split(attr, '.')
                result = reduce( getattr, [objects]+attrs )
                self.outputData(attrs=result)
            else:
                if objects:
                    allAttrs = dir(objects[0])
                    if self.inputPorts[1].widget:
                        #self.inputPorts[1].widget.setlist(allAttrs)
                        self.inputPorts[1].widget.configure(choices=allAttrs)

                results = []
                for obj in objects:
        #            if attr is None or attr=='':
                    if attr=='':
                        continue
                    attrs = string.split(attr, '.')
                    result = reduce( getattr, [obj]+attrs )
                    if type(result) == types.ListType:
                        results.extend( result )
                    else:
                        results.append( result )
                self.outputData(attrs=results)
"""
        
        if code: self.setFunction(code)

        self.widgetDescr['attr'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':[''],
            'entryfield_entry_width':14,
            'labelCfg':{'text':'attr:'}
            }

        ip = self.inputPortsDescr
        ip.append(datatype='None', singleConnection=False, name='objects')
        ip.append(datatype='string', name='attr')

        self.outputPortsDescr.append(datatype='list', name='attrs')


##  class GetAttrList(NetworkNode):
##      """Returns a list with the names of all available attributes of a Python
##  object. If a list of objects is passed to the node, the attributes of the
##  first object are chosen.
##  An additional Multi-Checkbutton param. panel allows to specify the
##  types of attributes to be output.

##  Input Ports
##      objects: a list of Python objects
##      buttonPanel: (bound to the Multi-Checkbutton widget). This widget allows
##                   to filter the attribute types to be output

##  Output Ports
##      attrs: a list of attributes
##  """

##      def __init__(self, valueList=None, constrkw={}, name='getattr List', **kw):
##          kw['name'] = name
        
##          apply( NetworkNode.__init__, (self,), kw)
##          self.mode = None # this is used by the Checkbutton Panel

##          self.widgetDescr['buttonPanel'] = {'class':'NEMultiCheckButtons',
##                           'valueList':valueList, 'callback':self.myCallback,
##                           'labelCfg':{'text':''} }
        
##          self.inputPortsDescr.append({'name':'objects', 'balloon': None,
##                                       'datatype':'None'})

##          self.inputPortsDescr.append({'name':'buttonPanel',
##                                       'datatype':'None'})


##          self.outputPortsDescr.append({'balloon':None, 'name':'attrs',
##              'datatype':'list'})


##          code = """def doit(self, objects, buttonPanel):
##      object = objects[0]
##      attrDict = {}
##      buttonTypeDict = {}
##      buttonStatusDict = {}
##      resultList = []
    
##      # first, we build a dict storing att name and type
##      for name in dir(object): 
##          if name[:2] == '__': # get rid of attrs that start with __
##              continue
##          att = eval('object.'+name)    
##          attrDict[name] = type(att).__name__

##      # now we build the values for the Multi-Checkbutton panel    
##      widget = self.inputPorts[1].widget
##      tkwidget = widget.tkwidget
##      typeList = attrDict.values()
##      for entry in typeList: 
##          # we use a dict to get rid of duplicate entries
##          buttonTypeDict[entry] = None
##      valueList = buttonTypeDict.keys()
##      valueList.sort()
 
##      # now try to (re)build the Multi-Checkbutton widget if necessary
##      if self.inputPorts[0].hasNewValidData():
##          tkwidget.rebuild(valueList)

##      # now we build a dict storing the current panel configuration
##      for bName, bValue in tkwidget.get():
##          buttonStatusDict[bName] = bValue
        
##      # now we build the output    
##      for name in attrDict.keys():
##          if buttonStatusDict.has_key(attrDict[name]):
##              if buttonStatusDict[attrDict[name]] == 1:
##                  resultList.append(name)
##      resultList.sort()
##      self.outputData(attrs=resultList)
##"""
            
##          if code: self.setFunction(code)


##      def myCallback(self, event=None):
##          self.paramPanel.run()


class SetAttr(NetworkNode):
    """Set one attribute on a Python object.
Double-clicking on the node opens a text entry panel to type the name of the
new attribute.
    
Input Ports
    object: a Python object
    values: value to be set as the new attribute
    name: (bound to entry widget)
          a string describing the name of the attribute

Output Ports
    object: the Python object with the new attribute
"""
    
    def __init__(self, name='Setattr', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        code = """def doit(self, object, value, name):
    setattr( object, name, value )
    self.outputData(object=object)
"""

        if code: self.setFunction(code)

        self.widgetDescr['name'] = {
            'class':'NEEntry', 'master':'node',
            'width':16, 'labelCfg':{'text':'attr name:'}}
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='object')
        ip.append(datatype='None', name='value')
        ip.append(datatype='string', name='name')

        self.outputPortsDescr.append(datatype='None', name='object')


class CallMethod(NetworkNode):
    """Invoke a user specified method on all incoming objects.
Double-clicking on the node opens a text entry widget to specifty the method
(see example below).

The string has to start with the method name followed by a blank followed
by any number of blank separated argument names. Arguments names starting with
the % character will be used as positional arguments. Other names will be used
while calling the method. Each argument creates a new input port and the
values passed to these ports will be passed to the method.

Input Ports
    objects: a list of Python objects
    signature: (bound to a text entry widget)
               provides a string describing the method's name and signature.
    and dynamically created input ports

Output Ports
    objects: a list of Python objects
    results: a list of returned values for calling the method on each object
    
Example
    The following string typed into the text entry widget:

        Set %arg1 %arg2 foo bar

    would create 4 additional input ports (the 4 right
    most ports) called arg1, arg2, name and help.
    For each object g of input port 0 (objects) the method 'Set'
    will be called using the following syntax:

    g.Set( in1, in2, foo=in3, bar=in4)

    where in1 through in4 are the values presented on the ports arg1,
    arg2, foo and bar respectively.
"""

    def createPortsFromDescr(self, words):
        # a list of positional argument inputPort names is built
        # a list of named argument inputPort names is built
        ed = self.getEditor()

        self.posArgNames = []
        self.posArgNamesDict = {} # used for fast lookup
        self.namedArgNames = []
        self.newCode = """def doit(self, objects, signature"""
        
        if len(words[0])==0:
            return
        self.method = words[0]

        match = self.allowedFirstChar.match(self.method)
        if not match:
            return
        i = 1

        # find positional arguments
        for arg in words[1:]:
            if arg[0]=='%':
                if len(arg)==1:
                   arg = '%in',i
                l = string.find(arg[1:], '[')
                if l == -1:
                    shortName = arg[1:]
                else:
                    shortName = arg[1:l+1]
                self.posArgNames.append((arg[1:], shortName))
                self.posArgNamesDict[shortName] = arg[1:]
                i = i + 1
            else:
                break

        for arg in words[i:]:
            if arg[0]=='%':
                raise RuntimeError('Positional argument specified '+\
                'after named argument!')
            # ??? looking for indices ???
            l = string.find(arg, '[')
            if l == -1:
                shortName = arg
            else:
                shortName = arg[:l]
            self.namedArgNames.append((arg, shortName))

        # Find first port that is wrong and delete all the ones beyond
        lastOK = 0
        newportnames = self.posArgNames + self.namedArgNames
        #print newportnames
        for p in self.inputPorts[2:]:
	    if lastOK == len(newportnames):
		break
            if p.required and not self.posArgNamesDict.has_key(p.name):
                break
            if not p.required and self.posArgNamesDict.has_key(p.name):
                break
           
            if p.name == newportnames[lastOK][1]:
                #print 'KEEPING', p.name, p.number
                self.newCode = self.newCode + """, %s"""%p.name
                lastOK = lastOK + 1
            else:
                break
	if lastOK == len(self.inputPorts): # nothing changed
	    return
        pl = self.inputPorts[2+lastOK:][:]
        pl.reverse()
        for p in pl:
            #print 'REMOVING', p.name, p.number
            self.deletePort(p)
        # create all inputPorts behind lastOK
        #portTypes = ed.typeManager.portTypeInstances.keys()
        for name in newportnames[lastOK:]:
            if self.posArgNamesDict.has_key(name[1]):
                ipdescr = {'name':name[1]}
            else:
                ipdescr = {'name':name[1], 'required':False}
            ip = apply( self.addInputPort, (), ipdescr )
            #print 'CREATING', ip.name, ip.number
            self.newCode = self.newCode + """, %s"""%name[1]

            # make sure dynamic input ports get saved to file
            if len(self.inputPorts) > 2:
                ip._modified = True

        self.newCode = self.newCode + """):\n"""

        codeNoSig = self.sourceCode[string.find(self.sourceCode,'\n')+1:]
        self.newCode = self.newCode + codeNoSig
        
        # check this out DUDE ! self modifying code
        self.setFunction(self.newCode, tagModified=1)


    def __init__(self, name='CallMethod', sourceCode=None, originalClass=None,
                 **kw):

        kw['name'] = name
        kw['sourceCode'] = sourceCode
        kw['originalClass'] = originalClass
        apply( NetworkNode.__init__, (self,), kw )

        self.method = ''
        self.oldSignature = '' # used to compare old a new user input
        # test that first character is either '_' or alphabetic
        self.allowedFirstChar = re.compile('_|[a-zA-Z]')
                        
        code = """def doit(self, objects, signature):
    if signature and signature != self.oldSignature:
        self.oldSignature = signature
        words = signature.split()
        for word in words:
            if word[0] == '%':
                match = self.allowedFirstChar.match(word[1:])
            else:
                match = self.allowedFirstChar.match(word)
            if not match:
                return

        self.createPortsFromDescr( words )

    results = []
    
    if self.inputPorts[0].singleConnection:
        if not hasattr(objects, self.method):
            return
        else:
            #self.rename(objects.fullName+' '+self.oldSignature)
            method = eval('objects.'+self.method)
            posArgs = []
            namedArgs = {}
            #print 'POS',self.posArgNames
            for arg in self.posArgNames:
                posArgs.append(eval(arg[0]))
            #print 'NAMED',self.namedArgNames
            for arg in self.namedArgNames:
                namedArgs[arg[1]] = eval(arg[0])
            results = [apply( method, posArgs, namedArgs )]

    elif objects:
        from mglutil.util.misc import isInstance
        for g in objects:
            #import types
            #if not type(g)==types.InstanceType:
            if isInstance(g) is False:
                continue
            if not hasattr(g, self.method):
                continue
            #method = getattr(g, self.method)
            method = eval('g.'+self.method)
            posArgs = []
            namedArgs = {}
            #print 'POS',self.posArgNames
            for arg in self.posArgNames:
                posArgs.append(eval(arg[0]))
            #print 'NAMED',self.namedArgNames
            for arg in self.namedArgNames:
                namedArgs[arg[1]] = eval(arg[0])

            results.append( apply( method, posArgs, namedArgs ) )

    self.outputData(objects=objects, results=results)
"""


        if code: self.setFunction(code)

        self.widgetDescr['signature'] = {
            'class':'NEEntry', 'master':'node',
            'width':16, 'callback':self.myCallback,
            'labelCfg':{'text':'signature:'}
            }
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', required=False, name='objects')
        ip.append(datatype='string', balloon='None', required=False,
                  name='signature')

        op = self.outputPortsDescr
        op.append(datatype='None', name='objects')
        op.append(datatype='None', name='results')


    def myCallback(self, event=None):
        # ok this is the deal: we want to call the doit method of this node,
        # even though some of the dynamically added inputports might have no
        # data, and could be required, which would prevent the node from run
        # and therefore not calling the doit method.
        args = [self,None,]
        args.append( self.inputPorts[1].getData() )
        for i in range(2,len(self.inputPorts)):
            args.append(None)
        apply( self.dynamicComputeFunction, tuple(args) )
        
        

class Builtin(NetworkNode):
    """Call a Python builtin function
Double clicking on the node opens a text entry widget to type the function
to be applied.

Input Ports
    values: tuple of positional arguments
    func: (bound to text entry widget)
    
Output Ports
    result: the result of the applying the callable to the arguments
"""
    
    def __init__(self, name='Builtin', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

	code = """def doit(self, values, func ):
    if len(func) == 0:
        return
    else:
        f = eval(func)
        if self.inputPorts[0].singleConnection:
            res = f(values)
        else:
            res = map(f, values)
        self.outputData(result=res)
"""
            
	if code: self.setFunction(code)

        self.widgetDescr['func'] = {
            'class':'NEEntry', 'master':'node', 'width':16,
            'labelCfg':{'text':'function:'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='None', name='values')
	ip.append(datatype='string', name='func')
        
	self.outputPortsDescr.append(datatype='None', name='result')



class Eval(NetworkNode):
    """Call the Python Eval builtin function.
Double clicking on the node opens a text entry widget to type the string
to be evaluated.

Input Ports
    command: (bound to text entry widget)
    in1: allows to pass a Python object that can be used in the statement
         that gets evaluated.
Output Ports
    result: the result of the eval function    

Notes

    NEW: Not just input ports' names (in1),
         now ANY PYTHON OBJECT from the __main__ scope
         can be evaluated with this node !!!

    eval(source[, globals[, locals]]) -> value
    Evaluates the source in the context of globals and locals.
    The source may be a string representing a Python expression
    or a code object as returned by compile().
    The globals and locals are dictionaries, defaulting to the current
    globals and locals.  If only globals is given, locals defaults to it.
"""
    
    def __init__(self, name='eval', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        code = """def doit(self, command, importString, in1):
    if len(command) == 0:
        return
    else:
        if self.name.startswith('eval'):
            if len(command)>15:
                self.displayName('eval: '+command[:15]+'...')
            else:
                self.displayName('eval: '+command)

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

        result = eval(command)
        self.outputData(result=result)
"""
            
        if code:
            self.setFunction(code)

        self.widgetDescr['command'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'statement:'}}

        self.widgetDescr['importString'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'import'}}

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='command')
        ip.append(datatype='string', required=False, name='importString', defaultValue='')
        ip.append(datatype='None', required=False, name='in1')

        self.outputPortsDescr.append(datatype='None', name='result')



class Assign(NetworkNode):
    """ creates/assigns a variable in the __main__ scope.
this variable is then accessible from the python shell.

Input Ports
    variable: name of the variable to be created/assigned in the main scope
    in1: Python object to assign to the variable
"""
    def __init__(self, name='assign', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['variable'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'variable:'}}

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='variable')
        ip.append(datatype='None', required=True, name='in1')

        code = """def doit(self, variable, in1):
    if len(variable) == 0:
        return
    else:
        if self.name.startswith('assign'):
            if len(variable)>15:
                self.rename('assign: '+variable[:15]+'...')
            else:
                self.rename('assign: '+variable)

        #mod = __import__('__main__')
        #setattr(mod, variable, in1)
        from mglutil.util.misc import importMainOrIPythonMain
        importMainOrIPythonMain()[variable] = in1
"""
        if code: self.setFunction(code)



class Accumulate(NetworkNode):
    """Node that accumulates in a list, values during iteration.
If the input port 'begin' receives 'True', the node resets its internal
list. Data is appended to this internal list. If the 3rd input port 'output'
receives a 'True', the node outputs the internal list of data.

Input Ports
    data:  data to be appended
    begin: if True, reset internal list
    output: output the final list
    
Output Ports
    listOfValues: list build during iteration
"""

    def __init__(self, name='accum', **kw):

        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.isSchedulingNode = True # this node is not scheduled in the net.py/

        self.accumList = [] # internal list to accumulate data
        
	code = """def doit(self, data, begin, output):
    #print 'ACCUM', data, begin, output, self.accumList
    if begin is True:
        self.accumList = []
    if data is not None and self.inputPorts[0].hasNewValidData():
        self.accumList.append(data)
    if output is True:
        self.outputData(listOfValues=self.accumList)
        self.scheduleChildren()
"""
            
        if code: self.setFunction(code)

        ip = self.inputPortsDescr
        ip.append(datatype='None', name='data')
	ip.append(datatype='boolean', name='begin')
        ip.append(datatype='boolean', name='output')

        op = self.outputPortsDescr
	op.append(datatype='list', name='listOfValues')



class Iterate(NetworkNode):
    """Loop over a given list.
This node iterates over every item in a list and outputs one at a time until
the end of the list is reached. Additional data is output to use this node
together with an accumulate node. See port description below.

Input Ports
    listToLoopOver: the list of values 
    stopOnFailure: acheck button
    
Output Ports
    oneItem: one item of the list
    iter:    the current index into the list of items to iterate over
    begin:   at the begin of an iteration, output True
    end:     at the end of an iteration, output True
    maxIter: the lenght of the list to loop over
"""


    def __init__(self, name='iterate', **kw):

        kw['name'] = name
        kw['progbar'] = 1 # add a progress bar to the node
        apply( NetworkNode.__init__, (self,), kw )
        self.isSchedulingNode = True # this node is not scheduled in the net.py/
                                  # method widthFirstChildren()
        self.readOnly = 1
        
	code = """def doit(self, listToLoopOver, stopOnFailure):
    iter = 0
    length = len(listToLoopOver)

    net = self.network
    p = self.getOutputPortByName('oneItem')
    roots = map( lambda x: x.node, p.children )
    p = self.getOutputPortByName('iter')
    roots.extend( map( lambda x: x.node, p.children ))

    allNodes = net.getAllNodes(roots)
    #print 'iterate', roots, allNodes
    
    if length>0:
        t = type(listToLoopOver[0])
        if t in [int, float, str]:
            if t==str:
               t = 'string'
            else:
               t = t.__name__
        elif isinstance(listToLoopOver[0],types.InstanceType):
            t = listToLoopOver[0].__class__.__name__

        self.outputPorts[0].setDataType(t, tagModified=False)

        self.outputData(maxIter=length)
        if length > 1:
            for lItemIndex in range(length):
                item = listToLoopOver[lItemIndex]
                if net.canvas is not None:
                    net.canvas.update()
                # check if stop execution button wwas pressed
                stop = self.network.checkExecStatus()
                #print 'Iterate LOOP', item, stop
                if stop:
                    break
                self.outputData(oneItem=item, iter=iter,
                                begin=(lItemIndex == 0),
                                end=( lItemIndex == (length-1) )
                                )
                if net.canvas is not None:
                    self.setProgressBar(float(iter)/length)
                self.forceExecution = 1
                # this is needed for iterate inside macros to fire children of
                # macro nodes when macronetwork isnot current network
                self.network.forceExecution = 1
                if len(allNodes):
                    #print 'ITERATE: running', stopOnFailure, allNodes
                    allOK = net.runNodes(allNodes, resetList=False)
                if stopOnFailure and not allOK:
                    break
                iter = iter + 1
            if net.canvas is not None:
                self.setProgressBar(1.0)
        else:
            self.outputData(oneItem=listToLoopOver[0], iter=0, begin=True, end=True)
            self.scheduleChildren()
"""
            
        if code: self.setFunction(code)

        ip = self.inputPortsDescr
        ip.append(datatype='vector', name='listToLoopOver')
        ip.append(datatype='boolean', name='stopOnFailure')

        self.widgetDescr['stopOnFailure'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':0, 'labelCfg':{'text':'stopOnFailure'},
            }
        
        op = self.outputPortsDescr
	op.append(datatype='None', name='oneItem')
        op.append(datatype='int', balloon='0-based iteration index',
                  name='iter')
	op.append(datatype='boolean',
                  balloon='sends "True" when iterate starts to iterate',
                  name='begin')
	op.append(datatype='boolean',
                  balloon='output "True" when loop is over', name='end')
	op.append(datatype='int', balloon='number of iteration to be done',
                  name='maxIter')


class While(NetworkNode):
    """While condition is true schedule children

Input Ports
    condition: expressin to be tested. values from input ports are refered to as val1, val2, etc...
    val1: first value
    val2: second value
    val3: third value

Output Ports
    run: port used to trigger children nodes
"""


    def __init__(self, name='while', **kw):

        kw['name'] = name
        #kw['progbar'] = 1 # add a progress bar to the node
        apply( NetworkNode.__init__, (self,), kw )
        self.isSchedulingNode = True # this node is not scheduled in the net.py/
                                  # method widthFirstChildren()
        self.readOnly = 0
        self.accumulate = []  # list used for accumulation
        
	code = """def doit(self, condition, val1, val2, val3):
    iter = 0
    net = self.network
    p = self.getOutputPortByName('run')
    roots = map( lambda x: x.node, p.children )
    allNodes = net.getAllNodes(roots)
    if self in allNodes:
        allNodes.remove(self)
    
    while True:
        # get a dict of {'portname':values}
        d = self.refreshInputPortData()
        # set the function arguments to the current values
        for k,v in d.items():
            # if it is a string we want the set the variable to the string
            # rather than evaluating the string
            if type(v) is types.StringType:
                exec('%s=str(%s)'%(k,v))
            else: # we assign the value (NOT SURE THIS WORKS WITH OBJECTS!)
                exec('%s=%s'%(k,str(v)))
        if net.canvas is not None:
            net.canvas.update()
        stop = self.network.checkExecStatus()
        if stop:
            break
        if not eval(condition):
            break
        self.outputData(run=1)
        self.forceExecution = 1
        # this is needed for iterate inside macros to fire children of
        # macro nodes when macronetwork isnot current network
        self.network.forceExecution = 1

        if len(allNodes):
            net.runNodes(allNodes, resetList=False)

        iter = iter + 1
"""
            
        if code: self.setFunction(code)

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='condition')
        ip.append(datatype='None', required=False, name='val1')
        ip.append(datatype='None', required=False, name='val2')
        ip.append(datatype='None', required=False, name='val3')

        self.widgetDescr['condition'] = {
            'class':'NEEntry', 'master':'node', 'width':16,
            'initialValue':'val1==0',
            'labelCfg':{'text':'condition:'}
            }
        
        op = self.outputPortsDescr
	op.append(datatype='int', name='run')



## class Counter(NetworkNode):
##     """
## """
    
##     def __init__(self, name='counter', **kw):
##         kw['name'] = name
##         apply( NetworkNode.__init__, (self,), kw )
##         self.value = None
        
## 	code = """def doit(self, initial, increment):
##     if self.inputPorts[0].hasNewValidData():
##         self.value = initial
##     if increment is not None:
##         self.value += increment
##     self.outputData(value=self.value)
## """
## 	if code: self.setFunction(code)

## 	self.inputPortsDescr.append(datatype='None', name='initial')
## 	self.inputPortsDescr.append({'name':'increment', 'datatype':'None',
##                                      'required':False})

## 	self.outputPortsDescr.append(datatype='None', name='value')



class PrintFormatedString(NetworkNode):
    """Print arguments into a string using a format string

Input Ports
    format:    format string using python print formating syntax.
               if format is None the format will be infere based on the
               argument type
    args:      connecting to this port creates a new input port for a Python
               object to be used as an argument to be printed

Output Ports
    formatedstring:  the result of printing the arguments int oa  astring
"""


    def __init__(self, name='print formated string', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        # define a function that adds creates a new port each time a connection
        # to this port is made
        codeAfterConnect = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    op = conn.port1
    node = self.node
    newport = {'name':op.name, 'datatype':op.datatypeObject['name'],
               'afterDisconnect':self.node.codeAfterDisconnect,
               '_modified': True}
    ip = apply( node.addInputPort, (), newport )
    # create the connection to the new port
    newconn = self.network.connectNodes( op.node, node, op.name, ip.name )
    # delete the connection to the port
    self.network.deleteConnections([conn])
    # update the signature of the function
    self.node.updateCode(node)
    return newconn
"""
        # define a function that adds creates a new port each time a connection
        # to this port is created
        self.codeAfterDisconnect = """def afterDisconnect(self, p1, p2):
    # self refers to the port
    node = p2.node
    node.deletePort(p2)
"""

        ip = self.inputPortsDescr
        ip.append(name='format', datatype='string', required=False)
        ip.append(name='args', datatype='None', required=False,
                  balloon="connect data to add args\nA new port will be created",
                  afterConnect=codeAfterConnect)

        op = self.outputPortsDescr
        op.append(datatype='string', name='formatedstring')

	code = """def doit(self, format, arguments):
    vlist = []
    for p in self.inputPorts[2:]:
        vlist.append(p.getData())
    if format: #(i.e. not None or '')
        result = format%tuple(vlist)
    else:
        result = ''
        for w in vlist:
           result += str(w) + ' '
    self.outputData(formatedstring=result)
"""
        self.setFunction(code)
            
	if code: self.setFunction(code)


class PopUpMessage(NetworkNode):
    """Print and pop up message in python shell.

Input Ports
    in1: Any kind of data

Output Ports
    None
"""
    
    def __init__(self, name='print', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

	code = """def doit(self, in1):
    print in1

    try:
      self.editor.vf.GUI.pyshell.top.deiconify()
    
    except AttributeError:
      return
"""
            
	if code: self.setFunction(code)

	self.inputPortsDescr.append(name='in1', datatype='None')


class Print(NetworkNode):
    """Print to stdout.

Input Ports
    in1: Any kind of data

Output Ports
    None
"""
    
    def __init__(self, name='print', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

	code = """def doit(self, in1):
    print in1
"""
            
	if code: self.setFunction(code)

	self.inputPortsDescr.append(name='in1', datatype='None')


class Len(NetworkNode):
    """Outputs lenght of data.

Input Ports
    in1: any kind of data

Output Ports
    length: an integer of the lenght of the data on in1
"""

    def __init__(self, name='len', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

	code = """def doit(self, in1):
    self.outputData(length = len(in1))
"""
	if code: self.setFunction(code)

	self.inputPortsDescr.append(datatype='None', name='in1')

        self.outputPortsDescr.append(datatype='int', name='length')


class AsType(NetworkNode):
    """cast Numric array to another type

Input Ports
    inArray: Numeric array or list of data
    dtype: (bound to combo box widget)
            Type of the data elements of the output array

Output Ports
    outArray: Numeric array
"""

    def __init__(self, name='AsType', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.dtypes= [
            'Character', 'Complex', 'Complex0', 'Complex16', 'Complex32',
            'Complex64', 'Complex8', 'Float', 'Float0', 'Float16', 'Float32',
            'Float64', 'Float8', 'Int', 'Int0', 'Int16', 'Int32', 'Int8',
            'uint', 'UInt16', 'UInt32', 'UInt8', 'UnsignedInt16',
            'UnsignedInt32', 'UnsignedInt8', 'unsignedinteger'
            ]

        self.widgetDescr['dtype'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.dtypes,
            'fixedChoices':True,
            'entryfield_entry_width':14,
            'initialValue':'Float16',
            'labelCfg':{'text':'operator'}
            }

	ip = self.inputPortsDescr
        ip.append(datatype='None', name='inArrayList')
	ip.append(datatype='string', name='dtype')

	self.outputPortsDescr.append(name='outArray')

	code = """def doit(self, data, dtype):
    if isinstance(data, Numeric.ArrayType):
        self.outputData(outArray=data.astype(getattr(Numeric,dtype)))
    else:
        d = Numeric.array(data)
        self.outputData(outArray=d.astype(getattr(Numeric,dtype)))
"""
            
	if code: self.setFunction(code)


class UnaryFuncs(NetworkNode):
    """Apply unary functions such as sin, cos, tan, exp, log, sqrt etc.
Double-clicking on the node opens a combo box widget to select the unary
function.

Input Ports
    inArrayList: list of data to be processed by unary function
    operator: (bound to combo box widget)
              a choice of unary functions such as sin, cos, tan, ect.

Output Ports
    outArrayList: a list of processed data
"""

    def __init__(self, name='Array Funcs1', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.operations= ['arccos ', 'arccosh', 'arcsin', 'arcsinh', 'arctan',
                          'actanh', 'cos', 'cosh', 'exp', 'log', 'log10',
                          'normalize', 'sin', 'sinh', 'sqrt', 'tan', 'tanh']

        self.widgetDescr['operator'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.operations,
            'fixedChoices':True,
            'entryfield_entry_width':8,
            'labelCfg':{'text':'operator'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='None', name='inArrayList')
	ip.append(datatype='string', name='operator')

	self.outputPortsDescr.append(name='outArrayList')

	code = """def doit(self, data, operator):
    result = []
    if operator=='':
        return
    data = Numeric.array(data)
    if operator=='normalize':
        norm = 1./Numeric.sqrt(Numeric.add.reduce(data*data, 1))
        norm.shape = norm.shape+(1,)
        result = data * norm
    else:
        op = getattr(Numeric, operator)
        result = op(Numeric.array(data))

    if len(result):
       self.outputData(outArrayList=result)
"""
            
	if code: self.setFunction(code)


class BinaryFuncs(NetworkNode):
    """Apply binary functions such as add, subtract, multiply, divide, etc.
Double-clicking on the node opens a combo box widget to select the binary
function.

Input Ports
    inArrayList1: first list of data to be processed by binary function
    inArrayList2: second list of data to be processed by binary function
    operator: (bound to combo box widget)
              a choice of binary functions such as add, subtract etc

Output Ports
    outArrayList: a list of processed data
"""
    
    def __init__(self, name='ArrayFuncs2', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.operations= ['add', 'subtract', 'multiply', 'divide',
                          'remainder', 'power']

        self.widgetDescr['operator'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':self.operations,
            'fixedChoices':True,
            'entryfield_entry_width':8,
            'labelCfg':{'text':'operator'},
            }

	ip = self.inputPortsDescr
        ip.append(datatype='None', name='inArrayList1')
        ip.append(datatype='None', name='inArrayList2')
        ip.append(datatype='string', name='operator')

	self.outputPortsDescr.append(name='outArrayList')

	code = """def doit(self, inArrayList1, inArrayList2, operator):
    if operator=='': return
    op = getattr(Numeric, operator)
    result = op(Numeric.array(inArrayList1), Numeric.array(inArrayList2) )
    self.outputData(outArrayList=result)
"""
            
	if code: self.setFunction(code)
        
##  class method
##       self.operations = ['add', 'subtract', 'multiply', 'divide',
##               'remainder', 'power', 'arccos', 'arccosh', 'arcsin',
##               'arcsinh', 'arctan', 'arctanh', 'cos', 'cosh', 'exp',
##               'log', 'log10', 'sin', 'sinh', 'sqrt', 'tan', 'tanh',
##               'maximum', 'minimum',
##          conjugate, equal, not_equal, greater, greater_equal, less,
##         less_equal, logical_and, logical_or, logical_xor, logical_not,
##          boolean_and, boolean_or, boolean_xor, boolean_not
        
##          kw['name'] = name
##          apply( NetworkNode.__init__, (self,), kw )

##  	code = """def doit(self, in1):
##      print in1
##  """
##  	if code: self.setFunction(code)


class Vector3DNE(NetworkNode):
    """A 3-D vector widget.
Double-clicking on the node opens the widget. The widget displays a vector
which can be moved within a sphere to generate a 3D vector. Right-clicking on
the widget opens an options panel.

Input Ports
    vector3D: (bound to vector3D widget)

Output Ports
    value: a list of [x, y z] floats
"""

    def __init__(self, name='Vector3D', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.model = None
        self.resolution = 0
 
 	self.widgetDescr['vector3D'] = {
            'class':'NEVectorGUI', 'master':'node',
            'size':100, 'continuous':1, 'vector':[1.,0,0],
            'labelCfg':{'text':''},
             }       

        self.inputPortsDescr.append(datatype='list', name='vector3D')
        
        self.outputPortsDescr.append(datatype='list', name='value')

        code = """def doit(self, vector3D):
    if vector3D:
        self.outputData(value=vector3D)
"""

        self.setFunction(code)


class MultiCheckbuttonsNE(NetworkNode):
    """A Tkinter Multi-Checkbutton widget. Checkbuttons are dynamically added
to the param. panel. The node inputs a list describing the buttons (see below).
Creating buttons or changing them does not trigger the node to run.

Buttons are added to a scrolled canvas, the user can jump to a button by
typing its name or by using the scrollbar.

This node adds additional options to the param. panel menu such as 'check all',
'uncheck all', 'toggle selection' and selection using regular expressions.

Syntax to create checkbuttons:
  Example1: ['apple','banana','orange'] creates 3 buttons

  Example2: [ ('apple',), ('banana', {'value':1},) ]
  this example creates an unchecked button 'apple' and a checked button
  'banana'.
  'value' is used to define the button status: 0=unchecked, 1=checked

  Example3: [<A List Of Objects>]
  the node tries to extract the names of the objects to build the panel
  please note that in this case the node actually outputs the objects selected
  in the param. panel.

Input Ports:
    valueList: a list of values to build the param. panel (see Examples above)
    buttonPanel: (bound to the param. panel)

Output Ports:
    onValues: either a list of the names of the currently checked buttons
              or a list of objects corresponding to the currently checked
              buttons
    offValues: same as onValues, but for the unchecked buttons.
  """

    def __init__(self, valueList=None, name='Multi Checkbuttons', **kw):
        kw['name'] = name
         
        self.mode = None # can be 'list' or 'instance'
        self.objectList = None # stores the valueList if values are of type
                               # instance
        
        apply( NetworkNode.__init__, (self,), kw )

         
	self.widgetDescr['buttonPanel'] = {
            'class':'NEMultiCheckButtons', 'lockedOnPort':True,
            'valueList':valueList, 'callback':self.myCallback,
            'labelCfg':{'text':''} }

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='valueList')
        ip.append(datatype='None', name='buttonPanel', required=False)

        op = self.outputPortsDescr
        op.append(datatype='list', name='onButtons')
        op.append(datatype='list', name='offButtons')
        op.append(datatype='list', name='allValues')

        code = """def doit(self, valueList, buttonPanel):

    widget = self.inputPorts[1].widget

    outputClass = list
    from mglutil.util.misc import isInstance
    #if type(valueList) == types.InstanceType:
    if isInstance(valueList) is True:
        if isinstance(valueList, UserList):
            outputClass = valueList.__class__
        elif isinstance(valueList, Numeric.ArrayType):
            outputClass = Numeric.array

    if type(valueList[0]) in [types.ListType, types.StringType,
                              types.TupleType]:
        self.mode = 'list'
        self.objectList = None # clear the data

    elif type(valueList[0]) in [types.IntType, types.FloatType]:
        self.mode = 'instance'
        self.objectList = valueList
        newValueList = []
        for val in valueList:
            newValueList.append(str(val))
        valueList = newValueList

    #elif type(valueList[0]) == types.InstanceType:
    elif isInstance(valueList[0]) is True:
        self.mode = 'instance'
        self.objectList = valueList
        newValueList = []
        for val in valueList:
            if hasattr(val, 'name'):
                newValueList.append(val.name)
            else:
                newValueList.append(repr(val))
        valueList = newValueList

    # only rebuild widget if we receive a new valueList
    if self.inputPorts[0].hasNewValidData():
        widget.widget.rebuild(valueList)

        # FIXME: add type to outputPort type

    onV = []
    offV = []

    panelData = widget.widget.get()

    if self.mode == 'list':
        for value in panelData:
            if value[1] != 0:
                onV.append(value[0])
            else:
                offV.append(value[0])

    elif self.mode == 'instance':
        for i in range(len(panelData)):
            if panelData[i][1] != 0:
                onV.append(self.objectList[i])
            else:
                offV.append(self.objectList[i])


    self.outputData(onButtons=outputClass(onV))    
    self.outputData(offButtons=outputClass(offV))    
    self.outputData(allValues=panelData)
"""

        self.setFunction(code)


    def myCallback(self, event=None):
        self.paramPanel.run()

#### NOTE: This node is no longer necessary, a combobox could do the same trick
##  class MultiRadiobuttonsNE(NetworkNode):
##      """A Tkinter Multi-Radiobutton widget. Radiobuttons are dynamically added
##  to the param. panel. The node inputs a list describing the buttons (see below).
##  Creating buttons or changing them does not trigger the node to run.

##  Buttons are added to a scrolled canvas, the user can jump to a button by
##  typing its name or by using the scrollbar.

##  Syntax to create radiobuttons:
##    Example1: ['apple','banana','orange'] creates 3 buttons

##    Example2: [ ('apple',), ('banana', {'value':1},) ]
##    this example creates an unchecked button 'apple' and a checked button
##    'banana'.
##    'value' is used to define the button status: 0=unchecked, 1=checked

##    Example3: [<A List Of Objects>]
##    the node tries to extract the names of the objects to build the panel
##    please note that in this case the node actually outputs the object selected
##    in the param. panel.

##  Input Ports:
##      valueList: a list of values to build the param. panel (see Examples above)
##      buttonPanel: (bound to the param. panel)

##  Output Ports:
##      onValue:  either the name of the currently checked button
##                or the object corresponding to the currently checked
##                button, as string (not as list)
##      offValues: same as onValues, but for the unchecked buttons, as list.
##    """
    
##      def __init__(self, valueList=None, name='Multi Radiobuttons', **kw):
##          kw['name'] = name
         
##          self.mode = None # can be 'list' or 'instance'
##          self.objectList = None # stores the valueList if values are of type
##                                 # instance
        
##          apply( NetworkNode.__init__, (self,), kw )

##  	self.widgetDescr['buttonPanel'] = {'class':'NEMultiRadioButtons',
##              'valueList':valueList, 'callback':self.myCallback,
##              'label':{'text':''} }

##          self.inputPortsDescr.append({'name':'valueList',
##                                       'datatype':'list'})

##          self.inputPortsDescr.append({'name':'buttonPanel',
##                                       'datatype':'None'})

         
##          self.outputPortsDescr.append({'name':'onButton',
##                                         'datatype':'None'})

##          self.outputPortsDescr.append({'name':'offButtons',
##                                         'datatype':'list'})

##          self.outputPortsDescr.append({'name':'allValues',
##                                         'datatype':'list'})


##          code = """def doit(self, valueList, buttonPanel):

##      if len(valueList)==0:
##          return
##      widget = self.inputPorts[1].widget

##      outputClass = list
##      if type(valueList) == types.InstanceType:
##          if isinstance(valueList, UserList):
##              outputClass = valueList.__class__
##          elif isinstance(valueList, Numeric.ArrayType):
##              outputClass = Numeric.array

##      if type(valueList[0]) in [types.ListType, types.StringType,
##                                types.TupleType]:
##          self.mode = 'list'
##          self.objectList = None # clear the data

##      elif type(valueList[0]) in [types.IntType, types.FloatType]:
##          self.mode = 'instance'
##          self.objectList = valueList
##          newValueList = []
##          for val in valueList:
##              newValueList.append(str(val))
##          valueList = newValueList

##      elif type(valueList[0]) == types.InstanceType:
##          self.mode = 'instance'
##          self.objectList = valueList
##          newValueList = []
##          for val in valueList:
##              if hasattr(val, 'name'):
##                  newValueList.append(val.name)
##              else:
##                  newValueList.append(repr(val))
##          valueList = newValueList
                
##      # only rebuild widget if we receive a new valueList
##      if self.inputPorts[0].hasNewValidData():
##          widget.tkwidget.rebuild(valueList)

##          # FIXME: add type to outputPort type

##      offV = []
##      panelData = widget.tkwidget.get()
    
##      if self.mode == 'list':
##          onOutputClass = str
##          for i in range(len(panelData)):
##              value = panelData[i]
##              if value[1] == i:
##                  onV = value[0]
##              else:
##                  offV.append(value[0])
        
##      elif self.mode == 'instance':
##          onOutputClass = outputClass
##          for i in range(len(panelData)):
##              if panelData[i][1] == i:
##                  onV = [self.objectList[i]]
##              else:
##                  offV.append(self.objectList[i])
        

##      self.outputData(onButton=onOutputClass(onV))    
##      self.outputData(offButtons=outputClass(offV))    
##      self.outputData(allValues=panelData)
##"""

##          self.setFunction(code)


##      def myCallback(self, event=None):
##          self.paramPanel.run()


class ScrolledTextNE(NetworkNode):
    """A Pmw ScrolledText widget.
The ScrolledText widget is bound to this node's parameter panel which is
displayed by right-clicking on the node and choosing 'show param. panel.

Input Ports
    scrolltext: (bound to scrolledText widget)
                a scrolled text window to type multi-line text

Output Ports
    string: A string representation of the text typed in the widget
"""

    def __init__(self, name='ScrolledText', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['scrolltext'] = {
            'class':'NEScrolledText', 'hull_width':400, 'hull_height':300,
            'text_padx':4,'text_pady':4,
            'labelCfg':{'text':''} }

        self.inputPortsDescr.append(datatype='None', name='scrolltext')
        
        self.outputPortsDescr.append(datatype='string', name='string')

        code = """def doit(self, scrolltext):
    if len(scrolltext)!=0:
        self.outputData(string=scrolltext)
"""

        self.setFunction(code)


class ReadFile(NetworkNode):
    """Read a file using Python's realines() command.
A file browser widget allowing specifying the file to be read.
A check button allows to display the file content and select a contiguous
subset of lines to be output When no lines are selected all lines are output.

Input Ports
    filename: name of the file to be opened
    selectLines: display/undisplay line selection window
    selectedLines: string description of the lines selected. IT can be a range
                   expression for a contiguous set of lines (e.g. range(0,10)
                   for the 10 first lies of the file) or an explicit list of
                   indices (e.g. [2,4,6,8,10]). The value of this widget can
                   be set by hand, or by selecting lines in the window
                   displaying the values and clicking on output lines.
    
Output Ports
    data: a list of lines from the file
"""

    def __init__(self, name='Read Lines', **kw):
        kw['name'] = name
        self.inNodeWidgetsVisibleByDefault = True
        self.text = ''
        apply( NetworkNode.__init__, (self,), kw )
        #self.readOnly = 1
        self.selectedLines = [] # list of indices of selected lines
        self.lastSelectedLinesStr=''
        
        code = """def doit(self, filename, selectLines, selectedLines):

    st = self.lineSelector
    if filename and len(filename):
        self.text = data = open(filename).readlines()
        st.clear()
        all = ''
        for line in self.text:
           all += line
        st.settext(all)
        st.clipboard_clear()

    if selectedLines:
        for ln in self.selectedLines:
            st.tag_delete(Tkinter.SEL, '%d.0'%(ln+1), '%d.0'%(ln+2))
        self.selectedLines = eval(selectedLines)
        for ln in self.selectedLines:
            st.tag_add(Tkinter.SEL, '%d.0'%(ln+1), '%d.0'%(ln+2))
            st.clipboard_append(self.text[ln])
        self.lastSelectedLinesStr=str(selectedLines)
        self.sel = st.component('text').selection_get()
    else:
        st.tag_add(Tkinter.SEL, '1.0', 'end')
        self.selectedLines = range(len(self.text))
        st.clipboard_append(all)
        self.lastSelectedLinesStr='range(0,len(self.text))'

    if self.inputPorts[1].hasNewValidData():
        if selectLines:
            self.lineSelectorMaster.deiconify()
        else:
            self.lineSelectorMaster.withdraw()

    self.outputSelection()
"""

        self.setFunction(code)

        fileTypes=[('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'read file', 'width':16,
            'labelCfg':{'text':'file:'},
            }

        self.inputPortsDescr.append(datatype='string', name='filename')

        self.widgetDescr['selectLines'] = {
            'class':'NECheckButton', 'master':'node',
            'initialValue':0, 'lockedOnPort':True,
            'labelCfg':{'text':'SelectLines'},
            }

        self.inputPortsDescr.append(datatype='boolean', name='selectLines')

        self.inputPortsDescr.append(datatype='string', name='selectedLines')
        self.widgetDescr['selectedLines'] = {
            'class':'NEEntry', 'master':'ParamPanel',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'selected lines:'}, 'width':10,
            }
        self.outputPortsDescr.append(datatype='list', name='data')


    def afterAddingToNetwork(self):
        fixedFont = Pmw.logicalfont('Fixed')
        st = self.lineSelectorMaster = Tkinter.Toplevel()
        self.lineSelector = Pmw.ScrolledText(
            st,
            usehullsize = 1,
            hull_width = 400,
            hull_height = 300,
            text_wrap='none',
            text_font = fixedFont,
            )
        #self.lineSelector.component('text').selection_handle(self.select)
        self.lineSelector.component('text').bind("<ButtonPress-1>", self.press)
        self.lineSelector.component('text').bind("<ButtonRelease-1>", self.release)
        
        self.lineSelector.grid(sticky='nsew', 
                               column=0, row=0, columnspan=3)

        Tkinter.Button(st, text="select regular expression:",
                       command=self.selectFromRE).grid(column=0, row=1)
        self.revar = Tkinter.StringVar()
        self.reentryTk = Tkinter.Entry(st, textvariable=self.revar)
        self.reentryTk.grid(column=1, row=1)

        
        Tkinter.Button(st, text="output lines",
                       command=self.outputSelection).grid(column=2, row=1)

        st.protocol("WM_DELETE_WINDOW", self.inputPorts[1].widget.widget.invoke)
        st.withdraw()

    def press(self, event=None):
        t = self.lineSelector.component('text')
        self.pressIndex = t.index('current')
        
    def release(self, event=None):
        t = self.lineSelector.component('text')
        index = t.index('current')
        if index==self.press:
            return
        else:
            fromInd = int(self.pressIndex.split('.')[0])
            toInd = int(index.split('.')[0])
            self.selectedlines = range(fromInd-1, toInd)
            t.tag_add(Tkinter.SEL, str(fromInd)+'.0', str(toInd)+'.end')
            self.lastSelectedLinesStr = 'range(%d,%d)'%(fromInd-1, toInd)
        self.pressIndex = None
                
    def outputSelection(self):
        data = self.lineSelector.component('text').selection_get().split('\n')
        if len(data[-1])==0:
            data = data[:-1]
        self.outputData(data=data)
        self.inputPorts[2].widget.set(self.lastSelectedLinesStr, run=0)
        
    def selectFromRE(self):
        pattern = re.compile(self.revar.get())
        st = self.lineSelector
        st.clear()
        st.clipboard_clear()
        selectedLines = []
        for i, line in enumerate(self.text):
            if pattern.match(line):
                st.insert('end', line)
                st.tag_add(Tkinter.SEL, "%d.0"%(i+1), "%d.0"%(i+2))
                st.clipboard_append(line)
                selectedLines.append(i)
            else:
                st.insert('end', line)
        self.lastSelectedLinesStr = str(selectedLines)
        self.selectedLines = selectedLines


class ExtractColumns(NetworkNode):
    """
    extract the specified columns from a list of lines contaning the same
    number of words.
    Multiple columns as well as colum ranges can be specified.
    Data casting can be specified using comma separated formating characters
    where 'i' represents an integer, 'f' a float and 's' a string.

    Input Ports
      data:    A list of strings. Each strin is a line that has to contain
               the same number of words when split using the specified separator
      columns: columns selector string (see example below)
      sep:     separator character, use 'None' for default split behavior (i.e.
               splitting on space.
      cast:    string allowing to specify hot to cast data into intergers,
               floats or strings. If ommitted all columns remain strings.
               A single format character (e.g. 'i') converts all values to
               this type (in this example integers).
               A comma seprated list of format characters (e.g. 'i,s,f,f')
               of the same length as the number of columns will cast each
               column according to the specified format.

Output Ports
    result: selected columns for each line

example:
  columns: [1:3], 5, [12:-1] will output columns 1,2,5,12,... up to the last column
  cast: i,s,f,f    casts the 4 columns to integer, string and float float
"""

    def __init__(self, name='Extract columns', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        #self.readOnly = 1
        code = """def doit(self, data, columns, sep, cast):
        result = []
        cols = columns.split(',')
        if sep=='None' or sep=='': sep=None
        castarrayfunc = []
        if len(cast)>1:
            castarray = cast.split(',')
            assert len(cols)==len(castarray)
            for castop in castarray:
                if castop == 'i': castarrayfunc.append(int)
                elif castop == 'f': castarrayfunc.append(float)
                else: castarrayfunc.append(str)
        elif len(cast)==1:
            castop=cast[0]
            if castop == 'i': castarrayfunc=(int,)*len(cols)
            elif castop == 'f': castarrayfunc=(float,)*len(cols)
            elif castop == 's': castarrayfunc=(str,)*len(cols)
            else:
                raise ValueError, csatop, 'bad format string, i=int, f=float, s=string expected'

        else:
            castarrayfunc=(cast[0],)*len(cols)

        for line in data:
            newline = []
            words = line.split(sep)
            for i,col in enumerate(cols):
                fcast = castarrayfunc[i]
                if col[0]=='[':
                    a,b = map(int, col[1:-1].split(':'))
                    newline.extend(map(fcast, words.__getslice__(a, b)))
                else:
                    newline.append(fcast(words.__getitem__(int(col))))
            if len(newline)==1:
                result.append(newline[0])
            else:
                result.append(newline)
 
        self.outputData(result=result)
"""

        self.setFunction(code)

        self.inputPortsDescr.append(datatype='list', name='data')
        self.inputPortsDescr.append(datatype='string', name='columns')
        self.inputPortsDescr.append(datatype='string', name='sep',
                                    required=False)
        self.inputPortsDescr.append(datatype='string', name='cast',
                                    required=False)

        self.widgetDescr['columns'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'columns:'},
            'initialValue':'[0:-1]'}

        self.widgetDescr['sep'] = {
            'class':'NEEntry', 'master':'node',
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'sep:'}, 'width':10,
            }

        self.widgetDescr['cast'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'columns:'},
            'initialValue':''}
##             'class':'NEComboBox', 'master':'node',
##             'choices':['int', 'float', 'string'],
##             'fixedChoices':True,
##             'initialValue':'str',
##             'entryfield_entry_width':7,
##             'labelGridCfg':{'sticky':'w'},
##             'widgetGridCfg':{'sticky':'w', 'columnspan':2},
##             'labelCfg':{'text':'type:'}}

        self.outputPortsDescr.append(datatype='list', name='result')





class ReadField(NetworkNode):
    """Reads a field (list, tuple or Numeric array) using pickle.Pickler
Double-clicking on the node opens a text entry widget to type the file name.
In addition, double-clicking in the text entry opens a file browser window.

Input Ports
    filename: name of the file to be opened

Output Ports
    array: an array of data
"""

    def __init__(self, name='Read Field', **kw):
        import pickle
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        #self.readOnly = 1
        code = """def doit(self, filename):
    if filename and len(filename):
        import pickle
        f = open(filename, 'r')
        p = pickle.Unpickler(f)
        field = p.load()
        f.close()

        if field is not None:
            self.outputData(array=field)
"""

        self.setFunction(code)

        fileTypes=[('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'read field', 'width':16,
            'labelCfg':{'text':'file:'},
            }

        self.inputPortsDescr.append(datatype='string', name='filename')

        self.outputPortsDescr.append(datatype='None', name='array')


class SaveField(NetworkNode):
    """Saves a field (list, tuple or Numeric array) using pickle.Pickler
Double-clicking on the node opens a text entry widget to type the file name.
In addition, double-clicking in the text entry opens a file browser window.

Input Ports
    field: array to be saved
    filename: name of the file to be saved

Output Ports
    None
"""

    def __init__(self, name='Save Field', **kw):
        import pickle
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        fileTypes=[('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node',
            'filetypes':fileTypes, 'title':'save field', 'width':16,
            'labelCfg':{'text':'file:'},
            }


        ip = self.inputPortsDescr
        ip.append(datatype='None', name='field')
        ip.append(datatype='string', name='filename')

        #self.readOnly = 1
        code = """def doit(self, field, filename):
    if filename and len(filename) and field:

        import pickle
        import numpy.oldnumeric as Numeric
        field = Numeric.array(field)
        f = open(filename, 'w')
        p = pickle.Pickler(f)
        p.dump(field)
        f.close()
"""

        self.setFunction(code)



class ChangeBackground(NetworkNode):
    """Change the background color of the editor canvas.

Input Ports
    color: The color can be either:
               a string describing a Tkinter color: i.e. 'gray85' or 'red'
               or a hexadecimal color description: i.e. '#2233344'
           or:
               a list with RGB or RGBV values: i.e. [0.0, 255.0, 0.0]

Output Ports
    None
"""
   
    def __init__(self, name='Change Background', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['color'] = {
            'class':'NEEntry', 'master':'node', 'width':16,
            'initialValue':'gray85',
            'labelCfg':{'text':'color:'},
            }

	self.inputPortsDescr.append(datatype='None', name='color')

	code = """def doit(self, color):
    ed = self.getEditor()
    if type(color) in [types.ListType, Numeric.ArrayType, types.TupleType]:
        assert len(color) == 3 or len(color) == 4
        color = list(color)
        if Numeric.minimum.reduce(color) <= 1:
            color = Numeric.multiply(color, 255)
        colorStr = '#%02x%02x%02x'%(color[0],color[1],color[2])

    elif type(color) in [types.StringType]:
        colorStr = color

    else: # wrong type
        raise ValueError

    ed.currentNetwork.scrolledCanvas.interior().configure(background=colorStr)
"""
            
	if code: self.setFunction(code)



class SliceData(NetworkNode):
    """Slices data. The slicing is specified in the entry widget. The node
handles lists (of ints, floats, arrays, strings) or Numeric arrays.
    
Input Ports
    data: the data to be sliced
    slice: (bound to entry widget)
          a string describing the slicing to be performed on the data

Output Ports
    data: the sliced data
"""

##      def _findType(self, data):
##          # recursive method to find type of data
##          for d in data:
##              if self.recStop: # we break out of the recursive method
##                  return
##              if type(d) == types.ListType:
##                  self._findType(d)
##              else:
##                  self.dType = type(d)
##                  self.recStop=1
        
        
    def __init__(self, name='Slice Data', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.recStop = 0 # this is used to break out of the recursice function
        self.dType = None # the dataType

        code = """def doit(self, data, _slice):
    result = eval('data'+_slice)
    if result is not None:
        self.outputData(data=result)
"""

        if code: self.setFunction(code)

        self.widgetDescr['_slice'] = {
            'class':'NEEntry', 'master':'node', 'width':10,
            'initialValue':'[:]',
            'labelCfg':{'text':'expression:'}}
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='data')
        ip.append(datatype='None', name='_slice')

        self.outputPortsDescr.append(datatype='None', name='data')


class Index(NetworkNode):
    """Extract an element out of a sequence (i.e. indexing)
    
Input Ports
    data:  the data to be indexed
    index: the index a whicstarting index (included, defaults to 0)

Output Ports
    data: data element of out incoming sequence
"""
        
    def __init__(self, name='Index', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        code = """def doit(self, data, index):
    lendata = len(data)
    maxPositiveIndex = lendata - 1
    minNegativeIndex = -lendata
    w = self.inputPortByName['index'].widget
    if w is not None and hasattr(w, 'widget'):
        w.widget.configure(min=minNegativeIndex, max=maxPositiveIndex)
        
    if index < minNegativeIndex:
        index = minNegativeIndex
    elif index > maxPositiveIndex:
        index = maxPositiveIndex
    val = data[index]

    if hasattr(val, '__class__'):
        tp = self.network.getTypeManager().getTypeFromClass(val.__class__)
        self.outputPortByName['data'].setDataType(tp, tagModified=False)
        
    self.outputData(data=val)
"""
        if code: self.setFunction(code)

        self.widgetDescr['index'] = {
            'class':'NEDial', 'size':40, 'type':'int', 'initialValue':0,
            'labelCfg':{'text':'index:'}, 'oneTurn':10,
            'master':'node'
            }
        ip = self.inputPortsDescr
        ip.append(datatype='None',
                  balloon='data sequence from which to extract an element',
                  name='data')
        ip.append(datatype='int',
                  balloon="""index value. 0 is the first element
Negative values index from end.
Defaults to 0.""",
                  name='index')

        self.outputPortsDescr.append(datatype='None', name='data')



class Split(NetworkNode):
    """Split a list or a tuple into several output ports (up to 10)
the output ports are re-created each times it runs (but the connected output ports
are not removed)
    
Input Ports
    data:  the list or a tuple to be splitted

Output Ports
    0: 1st element of incoming sequence
    1: 2nd element of incoming sequence
    2: 3rd element of incoming sequence
    ...
"""
        
    def __init__(self, name='Split', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='None',
                  balloon='list or a tuple to be splitted',
                  name='data')

        code = """def doit(self, data):
    # we remove all the not connected output ports
    lOutputPorts = self.outputPorts[:]
    for port in lOutputPorts:
        if len(port.connections) == 0:
            self.deletePort(port)

    # we add all the missing output ports
    if data is not None and len(data) > 0:
        for lValueIndex in range(len(data)):
            lPortName = str(lValueIndex)
            for p in self.outputPorts:
                if p.name == lPortName:
                    break
            else: # we didn't break
                self.addOutputPort(name=lPortName)
            lPort = self.getOutputPortByName(lPortName)
            lPort.outputData(data[lValueIndex])
"""
        if code: self.setFunction(code)




class Slice(NetworkNode):
    """Slice sequence data using Python conventions [From, to[.
Outputs data[ [from [: [to [: [step]]]]]]
    
Input Ports
    data: the data to be sliced
    from: starting index (included, defaults to 0)
    to:   ending index (excluded)
    step: step size (defaults to 1)

Output Ports
    data: data slice
"""
        
    def __init__(self, name='Slice', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        code = """def doit(self, data, fromInd, toInd, step):

    if fromInd is None:
        fromInd = 0
    if toInd is None:
        toInd = len(data)
    if step is None:
        step = 1

    result = data[ slice( fromInd, toInd, step)]

    if result is not None:
        import numpy.oldnumeric as Numeric
        if isinstance(result, Numeric.ArrayType):
            self.outputPorts[0].setDataType('NumericArray', tagModified=False)
            self.outputData(data=result)
        else:
            self.outputPorts[0].setDataType(self.inputPorts[0].datatypeObject,
            tagModified=False)
            self.outputData(data=data.__class__(result))
"""
            
        if code: self.setFunction(code)

        self.widgetDescr['fromInd'] = {
            'class':'NEDial', 'size':50, 'type':'int', 'initialValue':0,
            'labelCfg':{'text':'from:'}, 'oneTurn':10,
            }
        
        self.widgetDescr['toInd'] = {
            'class':'NEDial', 'size':50, 'type':'int', 'initialValue':0,
            'labelCfg':{'text':'to:'}, 'oneTurn':10,
            }
        
        self.widgetDescr['step'] = {
            'class':'NEDial', 'size':50, 'type':'int', 'initialValue':1,
            'labelCfg':{'text':'step:'}, 'oneTurn':10,
            }

        ip = self.inputPortsDescr
        ip.append(datatype='None', balloon='data to be sliced', name='data')
        ip.append(datatype='int', balloon="""slice start index.
Data at this index is included.
Negative values index from end.
Defaults to 0.""", required=False, name='fromInd')
        ip.append(datatype='int', balloon="""slice end index.
Data at this index is excluded.
Negative values index from end.
Defaults to length of data.""", required=False, name='toInd')
        ip.append(datatype='int', balloon="""slicing step.
Data at this index is included.
Negative values index from end.
Defaults to 0.""", required=False, name='step')

        self.outputPortsDescr.append(datatype='None', name='data')



class Range(NetworkNode):
    """create a sequence of integers
    Outputs range( from, to, step)
    
Input Ports
    from: starting index (included, defaults to 0)
    to:   ending index (excluded)
    step: step size (defaults to 1)

Output Ports
    data: range of integers
"""
        
    def __init__(self, name='Range', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        code = """def doit(self, fromInd, toInd, step):

    if fromInd is None:
        fromInd = 0

    if toInd is None:
        toInd = 0

    if step is None or step==0:
        step = 1
        
    result = range( fromInd, toInd, step)

    if result is not None:
        self.outputData(data=result)
"""
            
        if code: self.setFunction(code)

        self.widgetDescr['fromInd'] = {
            'class':'NEThumbWheel', 'width':60, 'height':20, 'type':'int',
            'initialValue':0, 'oneTurn':10, 'master':'node',
            'showLabel':1, 'wheelPad':1,
            'labelCfg':{'text':'from:'},
            }
        
        self.widgetDescr['toInd'] = {
            'class':'NEThumbWheel', 'width':60, 'height':20, 'type':'int',
            'initialValue':0, 'oneTurn':10, 'master':'node',
            'showLabel':1, 'wheelPad':1,
            'labelCfg':{'text':'  to:'},
            }
        
        self.widgetDescr['step'] = {
            'class':'NEThumbWheel', 'width':60, 'height':20, 'type':'int',
            'initialValue':1, 'oneTurn':10, 'master':'node',
            'showLabel':1, 'wheelPad':1,
            'labelCfg':{'text':'step:'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='int', balloon="""slice start index.
Data at this index is included.
Negative values index from end.
Defaults to 0.""", name='fromInd')
        ip.append(datatype='int', balloon="""slice end index.
Data at this index is excluded.
Negative values index from end.
Defaults to length of data.""", name='toInd')
        ip.append(datatype='int', balloon="""slicing step.
Data at this index is included.
Negative values index from end.
Defaults to 0.""", name='step')

        self.outputPortsDescr.append(datatype='list', name='data')



class ComboBoxNE(NetworkNode):
    """Provides a combobox to choose a single value from a user-specified list.
Optionally, the user can also pass a list of names. This list must have the
same size as the valueList. These names are then used to build the combobox
chooser. Else, we use repr() of the items in the valueList.
    Outputs the selected value
    
Input Ports
    valueList: list of values
    nameList: list of strings describing names (optional, must be of same size
              as valueList)
    selection: (bound to combobox widget)

Output Ports
    selection: the user-specified selection
"""

    def __init__(self, name='ComboBox', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.objectList = None # stores the valueList 
        self.nameList = None   # stores the optional nameList
        self.firstRun = True

        self.widgetDescr['selection'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':[''],
            'fixedChoices':True,
            'initialValue':'',
            'entryfield_entry_width':12,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':''},
            }

        if isinstance(self, ScrolledListNE):
             self.widgetDescr['selection']['dropdown'] = False

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='valueList')
        ip.append(datatype='list', required=False, name='nameList')
        ip.append(datatype='None', required=False, name='selection')

        op = self.outputPortsDescr
        op.append(datatype='None', name='selection')

        code = """def doit(self, valueList, nameList, selection):
    widget = self.inputPorts[2].widget

    # do we run the first time, and have been restored from a network? (then
    # we have both valueList and selection specified)
    if valueList and selection and self.firstRun is True:
        self.firstRun = False
        self.objectList = valueList
        self.nameList = nameList
        data = self.getData(selection, nameList)
        if data is not None:
            self.outputData(selection=data)
        return

    # only rebuild widget if we receive a new valueList
    if self.inputPorts[0].hasNewValidData() or self.inputPorts[1].hasNewValidData():
        if valueList != self.objectList or self.nameList != nameList:
            self.objectList = valueList
            self.nameList = nameList
            if nameList:
                vList = nameList
            else:
                vList = []
                for data in valueList:
                    if type(data) == types.StringType:
                        vList.append(data)
                    else:
                        vList.append(repr(data))
            if widget is not None:
                widget.setlist(vList)
                widget.configure(choices=vList)
                widget.widget.setentry('')
            return

    if selection:
        data = self.getData(selection, nameList)
        if data is not None:
            self.outputData(selection=data)
"""
            
        if code: self.setFunction(code)


    def getData(self, selection, nameList=None):
        #print "ComboBoxNE.getData", selection, nameList
        data = None
        widget = self.inputPorts[2].widget
        if widget is not None and hasattr(widget,'widget'):
            index = int(widget.widget.curselection()[0])
            data = self.objectList[index]
        else:
            if nameList is not None and len(nameList):
                for i in range(len(nameList)):
                    if nameList[i] == selection:
                        data = self.objectList[i]
                        break
            else:
                for i in range(len(self.objectList)):
                    if type(self.objectList[i]) == types.StringType and self.objectList[i] == selection:
                        data = self.objectList[i]
                        break
                    elif repr(self.objectList[i]) == selection:
                        data = self.objectList[i]
                        break

        return data



class ScrolledListNE(ComboBoxNE):
    pass



class IfNode(NetworkNode):
    """
    This node outputs theincomming data on its first or second output port
    if a user specified condition is True or False repectively.

    Input:
        value: the value to be output on th first or the second port
        condition: a condition to be evaluated to decide on which port to output
                   value
        param[123]: variables that can be used in 'condition'

    Output:
        _if: outputs value if the condition is True and schedules the children
             nodes under this output port
             
        _else: outputs value if the condition is False and schedules the
               children nodes under this output port
             
    NOTE: this node is scheduling. It will be in charge of triggering the
          execution of the subtree under one of its input potrs
    """


    def __init__(self, name='if else', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inNodeWidgetsVisibleByDefault = True

        self.isSchedulingNode = True # this node is not scheduled in the net.py/
                                  # method widthFirstChildren()

        self.widgetDescr['condition'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'cond:'},
            'initialValue':''}
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='value')
        ip.append(datatype='string', name='condition')
        ip.append(datatype='None', name='param1', required=False)
        ip.append(datatype='None', name='param2', required=False)
        ip.append(datatype='None', name='param3', required=False)

        op = self.outputPortsDescr
        op.append(datatype='None', name='_if')
        op.append(datatype='None', name='_else')
        
        code = """def doit(self, value, condition, param1, param2, param3):
    import os

    if condition is None or condition == '':
        return

    if eval(condition, locals()):#{'param1':param1, 'param2':param2, 'param3':param3} )
        self.outputData(_if=value)
        self.scheduleChildren(portList=[self.getOutputPortByName('_if')])
    else:
        self.outputData(_else=value)    
        self.scheduleChildren(portList=[self.getOutputPortByName('_else')])
"""
        self.setFunction(code)


class IfElseNode(NetworkNode):
    """if the user-specified condition is true, the value from the first input
port is output, else the value from the second port is output.

The condition can be typed into the condition entry widget in the node.
The condition can also be either a boolean or an integer (e.g. if the widget is
unbound and a checkbutton is bound to the condition port. 
"""


    def __init__(self, name='if else', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['condition'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'cond:'},
            'initialValue':''}
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='if_')
        ip.append(datatype='None', name='else_')
        ip.append(datatype='None', name='condition')

        op = self.outputPortsDescr
        op.append(datatype='None', name='result')
        
        code = """def doit(self, if_, else_, condition):

    if condition is None or condition == '':
        return

    if eval(str(condition)):
        self.outputData(result=if_)
    else:
        self.outputData(result=else_)    
"""
        self.setFunction(code)


class IsTrue(NetworkNode):
    """This node allows to test a condition involving some input data.
A boolean will be output on a port if the condition is true and another
port if the condition is false.

The condition can be typed into the condition entry widget in the node.
The data used in the condition refered to by the port name 'data',
i.e. 'data==3.14' is a valide condition
"""


    def __init__(self, name='if', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.isSchedulingNode = True # this node is not scheduled in the net.py/
                                  # method widthFirstChildren()

        self.widgetDescr['condition'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'cond:'},
            'initialValue':''}
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='data')
        ip.append(datatype='string', name='condition')

        op = self.outputPortsDescr
        op.append(datatype='boolean', name='true')
        op.append(datatype='boolean', name='false')
        
        code = """def doit(self, data, condition):

    if condition is None or condition == '':
        return

    # code copied from iterate
    net = self.network
    p = self.getOutputPortByName('true')
    rootsTrue = map( lambda x: x.node, p.children )

    p = self.getOutputPortByName('false')
    rootsFalse =  map( lambda x: x.node, p.children )

    if eval(str(condition)):
        allNodes = net.getAllNodes(rootsTrue)
        self.outputData(true=True)
    else:
        allNodes = net.getAllNodes(rootsFalse)
        self.outputData(false=True)    

    self.network.forceExecution = 1
    if len(allNodes):
        #print 'ITERATE: running', allNodes
        net.runNodes(allNodes, resetList=False)
"""
        self.setFunction(code)

class IsTrue_Stop(NetworkNode):
    """This node allows to test a condition involving some input data.
The input will be output on a port if the condition is true, else the
node return 'stop' to stop the rest of the network.

The condition can be typed into the condition entry widget in the node.
The data used in the condition refered to by the port name 'data',
i.e. 'data==3.14' is a valide condition
"""


    def __init__(self, name='if', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.widgetDescr['condition'] = {
            'class':'NEEntry', 'master':'node', 'labelCfg':{'text':'cond:'},
            'initialValue':''}
        
        ip = self.inputPortsDescr
        ip.append(datatype='None', name='data')
        ip.append(datatype='string', name='condition')

        op = self.outputPortsDescr
        op.append(datatype='None', name='data')
        
        code = """def doit(self, data, condition):

    if condition is None or condition == '':
        return

    if eval(str(condition)):
        self.outputData(data=data)
    else:
        return 'stop'
"""
        self.setFunction(code)


class RegressionTestMacro(MacroNode):
    """This node is used to test saving/restoring a macro node that came from
    a node library. Please do not user or modify this node.
    This node is not and shall not be exposed in stdlib."""
    
    def __init__(self, constrkw={}, name='NodeLibraryMacro', **kw):
        kw['name'] = name
        apply( MacroNode.__init__, (self,), kw)

    def beforeAddingToNetwork(self, net):
        MacroNode.beforeAddingToNetwork(self, net)
        ## loading libraries ##
        from Vision.StandardNodes import stdlib
        net.editor.addLibraryInstance(stdlib,"Vision.StandardNodes", "stdlib")


    def afterAddingToNetwork(self):
        from NetworkEditor.macros import MacroNode
        MacroNode.afterAddingToNetwork(self)
        ## loading libraries ##
        from Vision.StandardNodes import stdlib
        ## building macro network ##
        node0 = self
        node1 = node0.macroNetwork.ipNode
        node1.move(39, 16)
        node2 = node0.macroNetwork.opNode
        node2.move(27, 268)
        from Vision.StandardNodes import Pass
        node3 = Pass(constrkw = {}, name='Pass1', library=stdlib)
        node0.macroNetwork.addNode(node3,151,103)
        from Vision.StandardNodes import Pass
        node4 = Pass(constrkw = {}, name='Pass2', library=stdlib)
        node0.macroNetwork.addNode(node4,151,171)
        from Vision.StandardNodes import DialNE
        node5 = DialNE(constrkw = {}, name='Dial', library=stdlib)
        node0.macroNetwork.addNode(node5,377,78)

        ## saving connections for network macro0 ##
        node0.macroNetwork.connectNodes(
            node1, node3, "new", "in1", blocking=True)
        node0.macroNetwork.connectNodes(
            node3, node4, "out1", "in1", blocking=True)
        node0.macroNetwork.connectNodes(
            node4, node2, "out1", "new", blocking=True)
        node0.macroNetwork.connectNodes(
            node5, node2, "value", "new", blocking=True)

        node2.inputPorts[2].configure(singleConnection=True)
        node0.shrink()
        ## reset modifications ##
        node0.resetTags()
        node0.buildOriginalList()


class RunFunction(FunctionNode):
    """
    This node allow running a function that is defined in the __main__ scope

    input:
        function: name of the function to be executed
        import: allows importing into __main__ scope

    output:
        result: output the value returned by the function

    This node allows typing the name of a function in the 'function' field.
    If the function is found in the __main__ scope of the Python interpreter
    input ports will be created for all arguments. If arguments have default
    values of standard types such as float, int, or string a widget will be
    assigned to the input port and placed in the node's parameter panel.
    The function can be imported into the __main__ scope by typing an import
    statement in the 'import field'.

    example:
       1) in the python shell type:
          >>> def foo(x):
          ...     return 2*x
       in the Node type 'foo' in the 'function' entry field and execute the node
       A new port will be created at the top of the node for specifying x.
       Connecting a Dial widget to this port will allow specifying x and the
       'result' output port will display foo(x) which is 2*x

       2) in a file func.py define a function bar
         func.py
         def bar(x, y=2):
            return x*y

         in the node type 'from func import bar' in the import entry field and
         'bar' in the function entry field. When the node executed 2 new input
         ports are create, one for x which appears at the top of the node and
         one for y which is bound to a dial widget placed in the node's
         parameter panel.
         when a value of x is given or the dial specifying the value of y is
         modified, the 'result' output port will output bar(x,y) = x*y
    """
    def __init__(self, functionOrString=None, importString=None,
                 posArgsNames=[], namedArgs={},
                 name='runFunction', **kw):

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

        apply( FunctionNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        ip = self.inputPortsDescr

        self.widgetDescr['command'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'function'}}
            
        self.widgetDescr['importString'] = {
            'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'import'}}
            
        ip.insert(0,{'name':'command', 'required':True, 'datatype':'None',
                  'beforeDisconnect':FunctionNode.codeBeforeDisconnect})

        ip.insert(1,{'name':'importString', 'required':False, 'datatype':'string',
                  'beforeDisconnect':FunctionNode.codeBeforeDisconnect,
                  'defaultValue':''})

        code = """def doit(self, command, importString, *args):
    functionOrString = command
    import types
    if type(functionOrString) == types.StringType:
        # we add __main__ to the scope of the local function
        # the following code is similar to: "from __main__ import *"
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

#    if function is not self.function \
#      or \
#       ( self.constrkw.has_key('functionOrString') is True \
#        and \
#         self.constrkw['functionOrString'] != "\'"+functionOrString+"\'" \
#        and \
#         self.constrkw['functionOrString'] != functionOrString ):

    if function is not self.function:

        # remember current function
        self.function = function
        if hasattr(function, 'name'):
            self.rename('Run '+function.name)
        elif hasattr(function, '__name__'):
            self.rename('Run '+function.__name__)
        else:
            self.rename('Run '+function.__class__.__name__)
        
        # remove all ports beyond the function and the importString input ports 
        for p in self.inputPorts[2:]:
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
        if functionOrString is not None \
          and type(functionOrString) == types.StringType:
            from mglutil.util.misc import suppressMultipleQuotes
            self.constrkw['functionOrString'] = "\'"+suppressMultipleQuotes(functionOrString)+"\'"
            if importString is not None:
                self.constrkw['importString'] = "\'"+suppressMultipleQuotes(importString)+"\'"
        elif hasattr(function, 'name'):
            # case of a Pmv command
            self.constrkw['command'] = 'masterNet.editor.vf.%s'%function.name
        elif hasattr(function, '__name__'):
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = function.__name__
        else:
            # a function is not savable, so we are trying to save something
            self.constrkw['functionOrString'] = function.__class__.__name__
        if (importString is None or importString == '') \
          and self.constrkw.has_key('importString') is True:
            del self.constrkw['importString']
        if len(self.posArgsNames) > 0:
            self.constrkw['posArgsNames'] = self.posArgsNames # was str() 
        elif self.constrkw.has_key('posArgsNames') is True:
            del self.constrkw['posArgsNames']
        if len(self.namedArgs) > 0:
            self.constrkw['namedArgs'] = self.namedArgs # was str()
        elif self.constrkw.has_key('namedArgs') is True:
            del self.constrkw['namedArgs']

    elif self.function is not None:
        # get all positional arguments
        posargs = []
        for pn in self.posArgsNames:
            posargs.append(locals()[pn])
        # build named arguments
        kw = {}
        for arg in self.namedArgs.keys():
            kw[arg] = locals()[arg]
        # call function
        try:
            if hasattr(function,'__call__') and hasattr(function.__call__, 'im_func'):
                result = apply( self.function.__call__, posargs, kw )
            else:
                result = apply( self.function, posargs, kw )
        except Exception, e:
            from warnings import warn
            warn(e)
            result = None
        self.outputData(result=result)
"""
        if code: self.setFunction(code)
        # change signature of compute function
        self.updateCode(port='ip', action='create', tagModified=False)



from Vision.VPE import NodeLibrary
stdlib = NodeLibrary('Standard', '#66AA66')

#stdlib.addNode(ATEST, 'ATEST', 'Input')
stdlib.addNode(Generic, 'Generic', 'Input')
stdlib.addNode(ReadTable, 'ReadTable', 'Input')
stdlib.addNode(ThumbWheelNE, 'ThumbWheel', 'Input')
stdlib.addNode(ThumbWheelIntNE, 'ThumbWheelInt', 'Input')
stdlib.addNode(DialNE, 'Dial', 'Input')
stdlib.addNode(DialIntNE, 'DialInt', 'Input')
#stdlib.addNode(DialFloatNE, 'DialFloat', 'Input')
stdlib.addNode(Vector3DNE, 'Vector3D', 'Input')
stdlib.addNode(CheckButtonNE, 'Checkbutton', 'Input')
stdlib.addNode(ButtonNE, 'Button', 'Input')
stdlib.addNode(EntryNE, 'Entry', 'Input')
stdlib.addNode(ScrolledTextNE, 'ScrolledText', 'Input')
stdlib.addNode(FileBrowserNE,'File Browser','Input')
stdlib.addNode(DirBrowserNE,'Directory Browser','Input')
stdlib.addNode(MakeZipFileNE,'Make Zip File','Input')
stdlib.addNode(ReadFile,'Read Lines','Input')
stdlib.addNode(ExtractColumns,'Extract Cols.','Filter')
stdlib.addNode(ReadField,'Read Field','Input')
stdlib.addNode(MultiCheckbuttonsNE,'Multi Checkbuttons','Input')
#stdlib.addNode(MultiRadiobuttonsNE,'Multi Radiobuttons','Input')
stdlib.addNode(Filename, 'Filename', 'Input')
stdlib.addNode(NumberedFilename, 'NumberedName', 'Input')
stdlib.addNode(FilenameOps, 'FilenameOps', 'Input')
stdlib.addNode(Filelist, 'Filelist', 'Input')
stdlib.addNode(ComboBoxNE, 'ComboBox', 'Input')
stdlib.addNode(ScrolledListNE, 'ScrolledList', 'Input')
stdlib.addNode(Random, 'Random', 'Input')

stdlib.addNode(OpenFile,'Open file','Output')
stdlib.addNode(PopUpMessage, 'PopUpMsg', 'Output')
stdlib.addNode(Print, 'print', 'Output')
stdlib.addNode(PrintFormatedString, 'PrintFS', 'Output')
stdlib.addNode(SaveLines,'Save Lines','Output')
stdlib.addNode(TextEditor,'Text Editor','Output')
stdlib.addNode(SaveField,'Save Field','Output')

stdlib.addNode(UnaryFuncs, 'Array Ufunc1', 'Numpy')
stdlib.addNode(BinaryFuncs, 'Array Ufunc2', 'Numpy')
stdlib.addNode( AsType, 'As Type', 'Numpy')

stdlib.addNode(CallMethod, 'call method', 'Python')
stdlib.addNode(Eval, 'eval', 'Input')
stdlib.addNode(Assign, 'assign', 'Output')
stdlib.addNode(Len, 'len', 'Python')
stdlib.addNode(Iterate, 'iterate', 'Python')
stdlib.addNode(While, 'while', 'Python')
stdlib.addNode(Accumulate, 'accum', 'Python')
stdlib.addNode(GetAttr,'getattr','Python')
#stdlib.addNode(GetAttrList,'getattr List','Python')
stdlib.addNode(SetAttr, 'setattr', 'Python')
stdlib.addNode(Builtin, 'builtin', 'Python')
stdlib.addNode(Map, 'map', 'Python')
stdlib.addNode(Range, 'range', 'Python')
stdlib.addNode(Zip, 'zip' , 'Python')

stdlib.addNode(IfElseNode, 'if else', 'Logic')
stdlib.addNode(IfNode, 'if', 'Logic')
stdlib.addNode(IsTrue, 'isTrue', 'Test')
stdlib.addNode(IsTrue_Stop, 'isTrue_Stop', 'Logic')
stdlib.addNode(ExclusiveOR, 'ExclusiveOR', 'Logic')
stdlib.addNode(SelectOnExtension, 'SelectOnExtension', 'Filter')

stdlib.addNode(Pass, 'Pass' , 'Filter')
stdlib.addNode(SliceData, 'Slice Data' , 'Filter')
stdlib.addNode(Slice, 'Slice' , 'Filter')
stdlib.addNode(Index, 'Index' , 'Filter')
stdlib.addNode(Split, 'Split' , 'Filter')
stdlib.addNode(Cast, 'Cast' , 'Filter')
stdlib.addNode(StdDev, 'stddev' , 'Filter')
stdlib.addNode(Operator1, 'Op1' , 'Filter')
stdlib.addNode(Operator2, 'Op2' , 'Filter')
stdlib.addNode(Operator3, 'Op3' , 'Filter')
stdlib.addNode(Duplicate, 'duplicate' , 'Filter')
stdlib.addNode(ListOf, 'listOf' , 'Filter')
stdlib.addNode(Select, 'select' , 'Filter')
stdlib.addNode(DelayBuffer, 'DelayBuffer' , 'Filter')

stdlib.addNode(ChangeBackground, 'Change Background', 'Vision')
stdlib.addNode(Counter, 'Counter', 'Vision')
#stdlib.addNode(ShowHideGUI, 'Show/Hide GUI', 'deprecated')
stdlib.addNode(HasNewData, 'HasNewData', 'Vision')
stdlib.addNode(ShowHideParamPanel, 'Show/Hide Panel', 'Vision')
#stdlib.addNode(TestDefaultValues, 'Atest', 'Vision')
stdlib.addNode(RunFunction, 'Run function', 'Python')

#def lala(a,b,c=3): print "abc",a,b,c
#stdlib.addNode(FunctionNode, 'lala', 'Python', kw={'functionOrString':lala})


#from Vision.cmdlWrapper import wrapperGenerator
#directory = os.path.dirname(__file__) + os.sep + 'Tests'
#for file in os.listdir(directory):
#    if file[-3:]=='dsc':
#        wg = wrapperGenerator(os.path.join(directory, file))
#        code = wg.codeGen()
#        #print "code", code, wg.descr['nodename']
#        exec(code)
#        stdlib.addNode(FunctionNode, 'MSMS', 'CmdLine',
#                       kw={'functionOrString':eval(wg.descr['nodename'])})

