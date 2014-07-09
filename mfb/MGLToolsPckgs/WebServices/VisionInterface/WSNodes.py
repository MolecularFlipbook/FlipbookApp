# $Header: /opt/cvs/WebServices/VisionInterface/WSNodes.py,v 1.64.2.11 2011/08/04 20:56:37 jren Exp $
#
# $Id: WSNodes.py,v 1.64.2.11 2011/08/04 20:56:37 jren Exp $

import os, os.path, time, urllib, tkMessageBox, webbrowser
import xml.dom.minidom
import shutil
from NetworkEditor.items import NetworkNode, FunctionNode
from Vision import UserLibBuild
from urlparse import urlparse
from WebServices.OpalCache import OpalCache
from mglutil.util.packageFilePath import getResourceFolderWithVersion
from urlparse import urlparse

from time import strftime
from datetime import datetime

def Get_Opal_WS(url):
    """
Retruns the list of available Opal Web Services
output - list of Opal Web Services
"""
    if not url:
        tkMessageBox.showerror("Error!","No URL was provided")
        return
    services = []
    if  url.find("/opal2") != -1:
        #this is opal2 let's use the registry
        url = url + "/opalServices.xml"
        opener = urllib.FancyURLopener({}) 
        socket = opener.open(url)
        text = socket.read()
        feed = xml.dom.minidom.parseString(text)
        for entry in feed.getElementsByTagName('entry'):
            #getting the link element
            link = entry.getElementsByTagName('link')[0]
            service = link.getAttribute('href')
            services.append(str(service))
    else:
        #this is opal1
        url = url + '/servlet/AxisServlet'
        #print "url", url
        opener = urllib.FancyURLopener({}) 
        servlet = opener.open(url)
        text = servlet.read()
        text = text.split('<ul>')
        text = text[1:]
        for line in text[:-1]:
            #print "Line: " + line
            tmp_text = line.split(url)
            #print "tmp_text: " + str(tmp_text)
            port = tmp_text[-1].split('?wsdl')
            #print "port: " + str(port)
            wsdl_url = port[0].split('href="')[-1]   + "?wsdl"
            #print "wsdl_url: " + str(wsdl_url)
            if ( isOpalService(wsdl_url) ):
                #print "adding a service: " + str(wsdl_url)
                services.append(wsdl_url[:-5])
            #else: do nothing just skeep it
    return services

def isOpalService(wsdl_url):
    """
Given a wsdl_url which point to a wsdl it return true 
if the wsdl pointed by the url is a Opal Service
    """
    filehandle = urllib.urlopen(wsdl_url)
    string = filehandle.read()
    if ( string.find("wsdl:service name=\"AppService\"") != -1 ):
        return True
    else:
        return False


def isVersionValid(version):
    """this function check that the input string version 
    is a valid version number, which means that it should 
    be in the form of 
        <number>.<number>.<number>.<number>.etc.
    """
    import math
    numbers = version.split(".")
    decimalCounter = 0
    returnValue = 0
    for i in reversed(numbers):
        try:
            number = int(i)
        except:
            return 0
        #we count under the base 100 because sometime
        #version number are bigger than 10
        returnValue = returnValue + number * math.pow(100,decimalCounter)
        decimalCounter = decimalCounter + 1
    return int(returnValue)


def addOpalServerAsCategory(host, replace=True):
    """
Adds Category named `host` to Web Services Libary. 
replace=True: If the Nodes in `host` Category already exist, this function updates them.
"""
    if replace is False and wslib.libraryDescr.has_key(host):
        # this category is already loaded
        return

    oc = OpalCache()
    mglrd =  getResourceFolderWithVersion()
    mglwsdir = os.path.join(mglrd, "ws")
    inactivedir = os.path.join(mglwsdir, "inactives")
    hn = urlparse(host).hostname
    port = urlparse(host).port

    if port != None:
        hn = hn + '+' + str(port)

    inactivehostdir = os.path.join(inactivedir, hn)
    host_cache_dir = os.path.join(mglwsdir, hn)

    if not os.path.exists(mglwsdir):
        os.mkdir(mglwsdir)

    if not os.path.exists(inactivedir):
        os.mkdir(inactivedir)

    if not os.path.exists(inactivehostdir):
        os.mkdir(inactivehostdir)

    try:
        services = Get_Opal_WS(host) # get list of opal services on host 
        active_services = []
        cached_services = []

        for s in services:
            sn = os.path.basename(s)
            active_services.append(sn)

        # old inactive services that are now active

        old_inactives = os.listdir(inactivehostdir)
        now_actives = set(old_inactives) & set(active_services)

        for s in now_actives:
            os.remove(os.path.join(inactivehostdir, s))

        if os.path.exists(host_cache_dir):
            cached_services = os.listdir(host_cache_dir)

        inactive_services = set(cached_services) - set(active_services)

        for s in inactive_services:
            iaf = os.path.join(inactivehostdir, s)

            if not os.path.exists(iaf):
                shutil.copy(os.path.join(host_cache_dir, s), iaf)

        new_inactives = os.listdir(inactivehostdir)

        for s in new_inactives:
            print "*** [WARNING]: " + host + '/services/' + s + " IS NO LONGER AVAILBLE ON THE SERVER!"
    except: # no internet connection?
        print "WARNING: Loading services for " + host + " from cache"
        services = oc.getServicesFromCache(host, mglwsdir)

    for s in services:
        try:
            if not(os.path.exists(mglwsdir)):
                os.mkdir(mglwsdir)
            oc.writeCache(s, mglwsdir)
        except:
            pass

    if not services:
        print "No Opal web service is found on ", host
        return
    #print "services ", services
    #short_name = host.split('http://')[-1]
    #short_name = short_name.split('.')
    #short_name = short_name[0] + "." + short_name[1]

    for service in services:
        serviceNameOriginal = service.split('/')[-1]
        serviceName = serviceNameOriginal.replace('.','_')
        serverName = urlparse(service)[1]
        serverName = serverName.replace('.','_')
        serverName = serverName.split(':')[0]
        serviceOpalWrap = serviceName + "_" + serverName
        #print serviceOpalWrap
        if wslib.libraryDescr.has_key(host):
            for node in wslib.libraryDescr[host]['nodes']:
                if node.name == serviceOpalWrap:
                    wslib.deleteNodeFromCategoryFrame(host, FunctionNode, nodeName=serviceOpalWrap)
        from WebServices.OpalWrapper import OpalWrapper
        wrapper = OpalWrapper()

        try:
            wrap = wrapper.generate(service) #generate the python wrapper class for the service
        except:
            wrap = wrapper.generate(service, False)

        if wrap is not None:
            #mod = __import__('__main__')
            #for modItemName in set(dir(mod)).difference(dir()):
            #    locals()[modItemName] = getattr(mod, modItemName)
            from mglutil.util.misc import importMainOrIPythonMain
            lMainDict = importMainOrIPythonMain()
            for modItemName in set(lMainDict).difference(dir()):
                locals()[modItemName] = lMainDict[modItemName]

            exec(wrap)
            #print "wrap: ", wrap
            lServiceOpalClass = eval(serviceOpalWrap)
            lServiceOpalClass.sourceCodeWrap = wrap
            # sourceCodeWrap is the source of the Python class wrapping this service
            # An instance of this object will be available in the __main__ scope
            # The source code can be obtained from an instance of this service in a Vision
            # network as follows:  node.function.sourceCodeWrap
            # ALternatively one can type <servicename>.sourceCodeWrap in the Python shell
            # e.g. print Pdb2pqrOpalService_ws_nbcr_net.sourceCodeWrap
            
            #checking the service name if it contains the version or not
            versionStr = serviceNameOriginal.split("_")[-1]
            versionInt = isVersionValid(versionStr)
            if ( versionInt > 0 ):
                #ok we have a version in the serviceName
                #let's update it in the lServiceOpalClass
                serviceNameNoVersion = serviceNameOriginal.rstrip("_" + versionStr)
                serviceNameNoVersion.replace('.','_')
                #print "Setting service " + serviceNameNoVersion + " with version " + str( versionInt)
                lServiceOpalClass.serviceName = serviceNameNoVersion
            else:
                #we don't have a version, let's just use the serviceName 
                #as it is...
                #print "Setting service with no version " + serviceName
                lServiceOpalClass.serviceName = serviceName
            lServiceOpalClass.version = versionInt
            lServiceOpalClass.serviceOriginalName = serviceNameOriginal.replace('.','_')
            
            #setattr(mod, serviceOpalWrap, lServiceOpalClass)
            lMainDict[serviceOpalWrap] = lServiceOpalClass

            # the python wrapper class is callable
            # here we create a Vision FunctionNode to add this Python object
            # to the Vision library
            from WebServices.OpalUtil import OpalWSNode
            wslib.addNode(OpalWSNode, serviceOpalWrap, host, 
                          kw={'functionOrString':serviceOpalWrap,
                              'host':host
                             }
                         )



class GetWSNode(NetworkNode):
    """Drug and drop 'Load WS' node into a network to load web services.
Input Port: host (bound to ComboBox widget)
Change to host as needed to load additional web services.
"""
    def __init__(self, name='WS_List', host=None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True
        self.widgetDescr['host'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['http://ws.nbcr.net/opal2',
                       'http://kryptonite.ucsd.edu/opal2',
                       #'http://nbcrdemo.ucsd.edu:8080/opal',
                       'http://krusty.ucsd.edu:8081/opal2', 
                       ],
            'initialValue':'http://ws.nbcr.net/opal2',
            'entryfield_entry_width':30,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Host:'},
            }                   
        self.inputPortsDescr.append( {'name':'host', 'datatype':'string'} )
        code = """def doit(self, host):   
    addOpalServerAsCategory(host)            
"""
        if code:
            self.setFunction(code)


class OpalServiceNode(NetworkNode):
    """A generic Opal Web Service Node that extends NetworkEditor.items.NetworkNode 
and impliments common functionalty among Opal Web Service Nodes.
    http://nbcr.net/services/opal
    """
    def __init__(self, service=None, **kw):
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True
        from mglutil.web.services.AppService_client import AppServiceLocator, launchJobRequest, \
getOutputsRequest, queryStatusRequest
        from mglutil.web.services.AppService_types import ns0
        self.appLocator = AppServiceLocator()
        self.req = launchJobRequest()        
        self.inputFile = ns0.InputFileType_Def('inputFile')   

        self.widgetDescr['outputURL'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'labelCfg':{'text':'output URL'},
            }    
        self.inputPortsDescr.append(datatype='boolean', name='outputURL')            
        self.outputPortsDescr.append(datatype='string', name='URL')    
        if service:   
            self.constrkw['service'] = `service`
            self.service = service
            self.host =  self.service[:7+self.service[7:].find('/')] #to get rid of part after http://ws.nbcr.net:8080
            
    def runws(self):
        """
        Runs Opal Web Service on a given port:
            Returns resp if succeeded or
            prints obID and resp._baseURL message if failed, and returns ""
        """
        appServicePort = self.appLocator.getAppServicePort(self.service)
        try:
            self.resp = appServicePort.launchJob(self.req)
            jobID = self.resp._jobID
            self.resp = appServicePort.queryStatus(queryStatusRequest(jobID))
        except Exception, inst:
            from ZSI import FaultException
            if isinstance(inst, FaultException):
                tmp_str = inst.fault.AsSOAP()
                tmp_str = tmp_str.split('<message>')
                tmp_str = tmp_str[1].split('</message>')
                if len(tmp_str[0]) > 500:
                    print tmp_str[0]
                    tmp_str[0] = tmp_str[0][0:500] + '...'
                tkMessageBox.showerror("ERROR: ",tmp_str[0])
                self.resp = None
                return

        while self.resp._code != 8:
            time.sleep(1)
            self.resp = appServicePort.queryStatus(queryStatusRequest(jobID))
            if self.resp._code == 4:
                print "jobID:",jobID, 'failed on', self.resp._baseURL
                opener = urllib.FancyURLopener({}) 
                errorMsg = opener.open(self.resp._baseURL+"/std.err").read()
                tkMessageBox.showerror("Error!",errorMsg)
                webbrowser.open(self.host + '/' + jobID)
                return ""
        self.outurl = self.host + '/' + jobID
        self.resp = appServicePort.getOutputs(getOutputsRequest(jobID))

                        
class pdb2pqrNode(OpalServiceNode):
    """Web Service for pdb2pqr 
Input Ports
either
    input_file: string that holds the path to the input file supported by Babel
or
    input_mol: MolKit.Molecule instance
    
    options: command line options (bound to Entry widget)

Output Ports
    output_file_url: URL of the output file
"""
    def __init__(self, name='pdb2pqr', service=None, **kw):
        kw['name']=name
        OpalServiceNode.__init__(self, service=service, **kw )        
        self.inputPortsDescr.append(datatype='string', name='input_file')
        self.inputPortsDescr.append(datatype='Molecule', name='input_mol')
        
        self.widgetDescr['options'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'options:'},
            'labelGridCfg':{'sticky':'e'},
             'width':10,
             }
        self.inputPortsDescr.append( {'name':'options', 'datatype':'string',
                                     'required':False})
        
        self.widgetDescr['ff'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['amber', 'charmm', 'parse' ],
            'fixedChoices':True,
            'initialValue':'amber',
            'entryfield_entry_width':7,
            'labelCfg':{'text':'forcefield:'},
            }
        self.inputPortsDescr.append(datatype='string', name='ff')
                            
        self.outputPortsDescr.append(datatype='string', name='output_file_url')
        code = """def doit(self, outputURL, input_file, input_mol, options, ff ):    
    if input_mol:
        self.inputPorts[1].required = False
        input_file_base = os.path.basename(input_mol.parser.filename)
        self.inputFile._name = input_file_base
        sampleFileString = ''
        for line in input_mol.parser.allLines:
            sampleFileString += line
    else:
        self.inputPorts[2].required = False
        input_file_base = os.path.basename(input_file)
        self.inputFile._name = input_file_base
        sampleFile = open(input_file, 'r')
        sampleFileString = sampleFile.read()
        sampleFile.close()

    options = options + ' --ff='+ff + ' ' + input_file_base + ' ' + input_file_base +'.pqr'
    self.req._argList = options
    inputFiles = []
    self.inputFile._contents = sampleFileString
    inputFiles.append(self.inputFile)
    self.req._inputFile = inputFiles
    self.runws()
    output_file_url = None
    if self.resp:
        for files in self.resp._outputFile:
            if files._url[-4:] == input_file_base +'.pqr':
                output_file_url = files._url
        if not output_file_url:
            self.outputData(URL = self.outurl)
            return
        print outputURL, self.outurl
        if not outputURL:
            import urllib
            opener = urllib.FancyURLopener({})
            in_file = opener.open(output_file_url)
            self.outputData(URL = self.outurl, output_file_url = in_file.read())
        else:
            self.outputData(URL = self.outurl, output_file_url=output_file_url)
"""     
        if code:
            self.setFunction(code)
        
        codeAfterConnect_input_mol = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    self.node.getInputPortByName('input_file').required = False
"""    
        self.inputPortsDescr[2]['afterConnect']= codeAfterConnect_input_mol

        codeAfterConnect_input_file = """def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    self.node.getInputPortByName('input_mol').required = False
"""    
        self.inputPortsDescr[1]['afterConnect']= codeAfterConnect_input_file   


from WebServices import checkURL

class DownloadNode(NetworkNode):
    """Downloads remote files from the URL.
Input Ports
    url: URL for the remote file
Output Ports
    output: string containing the contents of the remote file
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        
        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }
        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )

        self.outputPortsDescr.append(datatype='string', name='output')
        
        code = """def doit(self, url):
    import time
    from time import strftime

    opener = urllib.FancyURLopener({})
    try:
        infile = opener.open(url)
    except IOError:
        s = -1
        while s == -1:
            try:
                urllib.urlopen(url)
                infile = opener.open(url)
                s = 0
            except IOError:
                t = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cte = time.mktime(datetime.now().timetuple())
                ete = cte + 30
                print "WARNING: " + t + " cannot connect to " + url
                print "         Are you connected to the internet?"
                print "         Will try again in about 30 seconds"
                while time.mktime(datetime.now().timetuple()) < ete:
                    if self.opalNode._vpe is not None:
                        self.opalNode._vpe.updateGuiCycle()
                        if net.execStatus == 'stop':
                            self.onStoppingExecution()
                            return None
                    time.sleep(30)
        pass

    self.outputData(output=infile.read())

"""
        if code:
            self.setFunction(code)

class DownloadToFileNode(NetworkNode):
    """Downloads the URL file to local machine.
Input Ports
    url: URL for the remote file
    filename: file name to save the remote file.  Default is the remote file name.
    overwrite: if checked - ovewrite existing file with the same name.  
               if not checked - give the file a unique file name.
Output Ports
    output: local file path
"""
    def __init__(self, name='DownloadToFile', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        
        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'width':16, 'labelCfg':{'text':'URL'},
                    }
        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'lockedOnPort':False,
            'labelCfg':{'text':'Filename: '}
            }

        self.widgetDescr['overwrite'] = {
            'class':'NECheckButton', 'master':'node', 'initialValue':1,
            'labelGridCfg':{'sticky':'w', 'columnspan':1},
            'widgetGridCfg':{'sticky':'w'}, 
            'labelCfg':{'text':'Overwrite'},
            }
        
        self.inputPortsDescr.append( {'name':'url', 'datatype':'string', 'required':'True'} )
        self.inputPortsDescr.append( {'name':'filename', 'datatype':'string', 'required':'False'} )
        self.inputPortsDescr.append( {'name':'overwrite', 'datatype':'int'} )

        self.outputPortsDescr.append(datatype='string', name='filename')
        
        code = """def doit(self, url, filename, overwrite):
    import tempfile
    import time
    from time import strftime

    if filename == None or filename == "":
        filename = os.path.basename(url)
        
    filename = os.path.abspath(filename)     

    if overwrite == 0 and os.path.exists(filename):
        fdir = os.path.dirname(filename)
        filename = tempfile.mktemp(prefix=filename+'.', dir=fdir)

    opener = urllib.FancyURLopener({})


    try:
        infile = opener.open(url)
    except IOError:
        s = -1
        while s == -1:
            try:
                urllib.urlopen(url)
                infile = opener.open(url)
                s = 0
            except IOError:
                t = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cte = time.mktime(datetime.now().timetuple())
                ete = cte + 30
                print "WARNING: " + t + " cannot connect to " + url
                print "         Are you connected to the internet?"
                print "         Will try again in about 30 seconds"
                while time.mktime(datetime.now().timetuple()) < ete:
                    if self.opalNode._vpe is not None:
                        self.opalNode._vpe.updateGuiCycle()
                        if net.execStatus == 'stop':
                            self.onStoppingExecution()
                            return None
                    time.sleep(30)
        pass

    f = open(filename, 'w')
    f.write(infile.read())
    f.close()
    self.outputData(filename=filename)
"""
        if code:
            self.setFunction(code)

class DownloadSaveDirNode(NetworkNode):
    """Downloads and saves all files from the URL directory.
Input Ports
    url: URL for the remote directory
    path: Path to downloaded directory on local machine.
    cutdirs: Number of directories to cut for wget.  Equivalent to the --cut-dirs option.
Output Ports
    output: Local path to download remote directory to.
"""
    def __init__(self, name='DownloadSaveDir', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }

        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )
        self.inputPortsDescr.append( {'name':'path', 'datatype':'string'} )
        self.inputPortsDescr.append( {'name':'cutdirs', 'datatype':'string', 'required':False} )

        self.outputPortsDescr.append(datatype='string', name='output')
        
        code = """def doit(self, url, path, cutdirs):   
            from binaries import findExecModule

            if os.name == 'dos' or os.name == 'nt':
                wget = findExecModule('wget')
                wget = '\"' + wget + '\"'
            elif os.uname()[0] == "Darwin":
                wget = findExecModule('wget')
            else:
                wget = "wget"

            opener = urllib.FancyURLopener({})

            if not os.path.exists(path):
                  os.mkdir(path)

            if os.name == 'dos' or os.name == 'nt':
                  sep = '&&'
            else:
                  sep = ';'

            url.strip('''/''')

            if cutdirs == None:
                  num_dirs = 1
            else:
                  num_dirs = cutdirs

            ddct = time.ctime(os.path.getmtime(path))

            dflc = wget + ' --spider -r -l inf --no-remove-listing --no-parent --no-host-directories -nH --cut-dirs=''' + str(num_dirs) + ' ' + url
            os.system(dflc + ' >& /tmp/spider.pig')


            download_cmd = 'cd ' + path + ' ' + sep + ' ' +  wget + ' -r -l inf --no-remove-listing --no-parent --no-host-directories -nH --cut-dirs=''' + str(num_dirs) + ' ' + url
            print download_cmd
            os.system(download_cmd)

            ddnct = time.ctime(os.path.getmtime(path))

            if ddct != ddnct:
                self.outputData(output = path)
            
            pass
#            self.outputData(output=path)
"""
        if code:
            self.setFunction(code)

class GetMainURLNode(NetworkNode):
    """Get the directory URL of a remote file URL
Input Ports
    url: URL for the remote file
Output Ports
    newurl: string containing the directory URL of a remote file URL
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }

        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )

        self.outputPortsDescr.append(datatype='string', name='newurl')
        
        code = """def doit(self, url):   
            filename = url.split('/')[len(url.split('/'))-1]
            nurl = url.strip(filename) 
            pass
            self.outputData(newurl=nurl)
"""
        if code:
            self.setFunction(code)

class GetMainURLFromListNode(NetworkNode):
    """Get the Opal output main URL from a list of Opal result URLs
Input Ports
    url: list of Opal output URLs for one particular job
Output Ports
    newurl: string containing the directory URL of a remote file URL
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }

        self.inputPortsDescr.append( {'name':'urls', 'datatype':'list'} )

        self.outputPortsDescr.append(datatype='string', name='newurl')
        
        code = """def doit(self, urls):   
            url = urls[0]
            filename = url.split('/')[len(url.split('/'))-1]
            nurl = url.strip(filename) 
            pass
            self.outputData(newurl=nurl)
"""
        if code:
            self.setFunction(code)

class GetURLFromListNode(NetworkNode):
    """Get the first URL that matches the extension in the URL list.
Input Ports
    urllist: list of urls
    ext: extension
Output Ports
    url: the first url that matches the extension in urllist
"""
    def __init__(self, name='GetURLFromList', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['ext'] = {'class':'NEEntry', 'master':'node',
            'width':8,
            'labelCfg':{'text':'extension'},
                    }

        self.inputPortsDescr.append( {'name':'urllist', 'datatype':'list'} )
        self.inputPortsDescr.append( {'name':'ext', 'datatype':'string'} )

        self.outputPortsDescr.append(datatype='string', name='url')
        
        code = """def doit(self, urllist, ext):   
            ext = '.' + ext
            found = False

            for i in urllist:
                if i.endswith(ext):
                    url = i
                    found = True
                    break

            if found == False:
                print "ERROR: No matching URL found in the list"
                url = ""

            pass
            self.outputData(url=url)
"""
        if code:
            self.setFunction(code)

class IsURLNode(NetworkNode):
    """Returns true if input is an URL and false otherwise.
Input Ports
    url_str: a string
Output Ports
    is_url: true if input if an URL and false otherwise.
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }

        self.inputPortsDescr.append( {'name':'url_str', 'datatype':'string'} )

        self.outputPortsDescr.append(datatype='boolean', name='is_url')
        
        code = """def doit(self, url_str):   
            from urlparse import urlparse
            scheme = urlparse(url_str)[0]
     
            pass

            if scheme == "http" or scheme == "ftp" or url_str.find('www.') != -1 or url_str.find('.edu') != -1 or url_str.find('.com') != -1 or url_str.find('.org') != -1:
                  self.outputData(is_url=1)
            else:
                  self.outputData(is_url=0)
"""
        if code:
            self.setFunction(code)

class ReplaceURLNode(NetworkNode):
    """Replace filename in the URL with a new filename
Input Ports
    url: URL for the remote file
    filename: new filename for the URL
Output Ports
    newurl: string containing URL with old file name replaced with the new filename
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }

        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )
        self.inputPortsDescr.append( {'name':'newfilename', 'datatype':'string'} )

        self.outputPortsDescr.append(datatype='string', name='newurl')
        
        code = """def doit(self, url, newfilename):   
            oldfilename = url.split('/')[len(url.split('/'))-1]
            nurl = url.strip(oldfilename) + newfilename
            pass
            self.outputData(newurl=nurl)
"""
        if code:
            self.setFunction(code)

class WebBrowserNode(NetworkNode):
    """Opens a URL with default Web Browser.
Input Ports
    url: URL
"""
    def __init__(self, name='Download', host = None, **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        
        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'URL'},
                    }
        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )
        
        code = """def doit(self, url):   
            url = self.getInputPortByName('url').data
            webbrowser.open(url)
"""
        if code:
            self.setFunction(code)

from Vision.VPE import NodeLibrary
wslib = NodeLibrary('Web Services', '#d7fdf9')
wslib.addNode(GetWSNode, 'Load WS', 'Generic')
wslib.addNode(DownloadNode, 'Download', 'Generic')
wslib.addNode(DownloadSaveDirNode, 'DownloadSaveDir', 'Generic')
wslib.addNode(DownloadToFileNode, 'DownloadToFile', 'Generic')
wslib.addNode(GetMainURLNode, 'GetMainURL', 'Generic')
wslib.addNode(GetMainURLFromListNode, 'GetMainURLFromList', 'Generic')
wslib.addNode(GetURLFromListNode, 'GetURLFromList', 'Generic')
wslib.addNode(IsURLNode, 'IsURL', 'Generic')
wslib.addNode(ReplaceURLNode, 'ReplaceURL', 'Generic')
wslib.addNode(WebBrowserNode, 'WebBrowser', 'Generic')
#addOpalServerAsCategory('http://ws.nbcr.net/opal2')
#addOpalServerAsCategory('http://krusty.ucsd.edu:8081/opal2')
#addOpalServerAsCategory('http://kryptonite.ucsd.edu/opal2')

try:
    UserLibBuild.addTypes(wslib, 'MolKit.VisionInterface.MolKitTypes')
except:
    pass
