import copy
import os
import OpalUtil

from mglutil.web.services import AppService_client
from mglutil.web.services.AppService_types import ns0
from urlparse import urlparse
from OpalCache import OpalCache
from mglutil.util.packageFilePath import getResourceFolderWithVersion

tab = "  "

class OpalWrapper(object):
  """docstring for OpalWrapper"""
  
  def __init__(self):
    pass

  def generate(self,url,conn=True):
    oc = OpalCache()

    if conn == True:
      if oc.isCacheValid(url, os.path.join(getResourceFolderWithVersion(), 'ws')):
        conn = False

    if conn == True:
      self.metadata = self.getAppMetadata(url)
    else:
      print "[INFO]: Generating Opal Wrapper for " + url + " from cache"

    self.url = url

    #setting up for local execution
    
    if conn == True:
      try:
        executable = self.getAppConfig(url)._binaryLocation
      except:
        executable = 'NA'
        pass
    else:
      dir = os.path.join(getResourceFolderWithVersion(), 'ws')
      executable = oc.getBinaryLocation(url, dir)
      params = oc.getParams(self.url, dir)
      self.params = oc.getParams(self.url, dir)

    # assuming the server is a unix
    executable = executable.rpartition("/")[2]

    if self.which(executable) == None:
        self.executable = ""
    else:
        self.executable = self.which(executable)

    if conn == True:
      classdec = self.buildClassDeclaration(self.metadata,self.url)

      if (self.metadata._types):
        initmethod = self.buildInitMethod(self.metadata, self.url)
        callmethod = self.buildCallMethod(self.metadata)
      else:
        initmethod = self.buildDefaultInitMethod(self.url)
        callmethod = self.buildDefaultCallMethod()
    else:
      classdec = self.buildClassDeclarationFromCache(self.url, params)

      if params:
        initmethod = self.buildInitMethodFromCache(params, self.url)
        callmethod = self.buildCallMethodFromCache(params)
      else:
        initmethod = self.buildDefaultInitMethodFromCache(self.url)
        callmethod = self.buildDefaultCallMethod()

    retclass = ""

    for i in classdec:
      retclass+=(str(i)+"\n")

    allmethods = []
    allmethods.extend(initmethod)
    allmethods.extend(callmethod)
    for i in allmethods:
      retclass+=(tab+str(i)+"\n")
    #add the onStoppingExecution before returning
    return retclass
  
  def getAppMetadata(self,url):
    """docstring for getAppMetadata"""
    appLocator = AppService_client.AppServiceLocator()
    appServicePort = appLocator.getAppServicePort(url)
    req = AppService_client.getAppMetadataRequest()
    metadata = appServicePort.getAppMetadata(req)
    return metadata

  def getAppConfig(self,url):
    """
        getAppConfig description: give the URL of the service it returns the appConfig of that service
    """
    appLocator = AppService_client.AppServiceLocator()
    appServicePort = appLocator.getAppServicePort(url)
    req = AppService_client.getAppConfigRequest()
    metadata = appServicePort.getAppConfig(req)
    return metadata

  def buildClassDeclaration(self,metadata,url):
    """docstring for buildClassDeclaration"""
    myclassname = url.split('/')[-1].replace('-','_')
    myclassname = myclassname.replace('.','_') 
    #LC 042308 added the server name to the generated classname 
    servername = urlparse(url)[1]
    servername = servername.replace('.','_')
    servername = servername.split(':')[0]
    myclassname = myclassname + "_" + servername
    myret = []
    myret.append('class %s:' % myclassname)
    params = {}
    try:
      rawlist = metadata._types._flags._flag
      for i in rawlist:
        myhash = {}
        myhash = {'type':'boolean'}
        myhash['default'] = 'True' if str(i._default)=='1' else 'False'
        myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
        params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
    except AttributeError:
      pass
    try:
      rawlist = metadata._types._taggedParams._param
      for i in rawlist:
        myhash = {}
        if i._value:
          myhash['type'] = 'selection'
          myhash['values'] = [str(z) for z in i._value]
        else:
          myhash['type'] = str(i._paramType)
        if(str(i._paramType)=="FILE"):
          myhash['ioType'] = str(i._ioType)
        myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
        myhash['default'] = str(i._default) if i._default else None
        params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
    except AttributeError:
      pass
    try:
      rawlist = metadata._types._untaggedParams._param
      for i in rawlist:
        myhash = {}
        myhash['type'] = str(i._paramType)
        if(str(i._paramType)=="FILE"):
          myhash['ioType'] = str(i._ioType)
        myhash['description'] = str(i._textDesc)
        myhash['default'] = str(i._default) if i._default else None
        params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
    except AttributeError:
      pass
    myret.append(tab+'params='+str(params))
    return myret

  def buildClassDeclarationFromCache(self, url, params):
    """docstring for buildClassDeclaration"""
    myclassname = url.split('/')[-1].replace('-','_')
    myclassname = myclassname.replace('.','_') 
    #LC 042308 added the server name to the generated classname 
    servername = urlparse(url)[1]
    servername = servername.replace('.','_')
    servername = servername.split(':')[0]
    myclassname = myclassname + "_" + servername
    myret = []
    myret.append('class %s:' % myclassname)
    oc = OpalCache()
    myret.append(tab+'params='+str(params))

    return myret
  
  def buildInitMethod(self,metadata,url):
    """docstring for buildInitMethod"""
    myret = []
    myret = ['def __init__(self):',\
            tab+'self.url=\''+url+'\'',\
            tab+'from mglutil.web.services.AppService_client import AppServiceLocator,getAppMetadataRequest',\
            tab+'appLocator = AppServiceLocator()',\
            tab+'appServicePort = appLocator.getAppServicePort(self.url)',\
            tab+'req = getAppMetadataRequest()',\
            tab+'self.metadata = appServicePort.getAppMetadata(req)'
    ]
    try:
      rawlist = metadata._types._flags._flag
      flaglist = [str(i._id) for i in rawlist]
    except AttributeError:
      flaglist = []
    try:
      rawlist = metadata._types._taggedParams._param
      taglist = [str(i._id) for i in rawlist]
    except AttributeError:
      taglist = []
    try:
      rawlist = metadata._types._untaggedParams._param
      untaglist = [str(i._id) for i in rawlist]
    except AttributeError:
      untaglist = []
    if flaglist:
      myret.append(tab+'self.flags='+str(flaglist))
    else:
      myret.append(tab+'self.flags=[]') 
    if taglist:
      myret.append(tab+'self.taggedparams='+str(taglist))
    else:
      myret.append(tab+'self.taggedparams=[]')
    if untaglist:
      myret.append(tab+'self.untaggedparams='+str(untaglist))
    else:
      myret.append(tab+'self.untaggedparams=[]')
    return myret

  def buildInitMethodFromCache(self, params, url):
    """docstring for buildInitMethod"""

    myret = []
    myret = ['def __init__(self):',\
            tab+'self.url=\''+url+'\'',\
#            tab+'from mglutil.web.services.AppService_client import AppServiceLocator,getAppMetadataRequest',\
#            tab+'appLocator = AppServiceLocator()',\
#            tab+'appServicePort = appLocator.getAppServicePort(self.url)',\
#            tab+'req = getAppMetadataRequest()',\
#            tab+'self.metadata = appServicePort.getAppMetadata(req)'
    ] 

    flaglist = []
    taglist = []
    untaglist = []

    for k, v in params.iteritems():
      if v['config_type'] == 'FLAG':
        flaglist.append(k)
      elif v['config_type'] == 'TAGGED':
        taglist.append(k)
      elif v['config_type'] == 'UNTAGGED':
        untaglist.append(k)
      else:
        print "ERROR: Invalid config_type"
 
    if flaglist:
      myret.append(tab+'self.flags='+str(flaglist))
    else:
      myret.append(tab+'self.flags=[]') 
    if taglist:
      myret.append(tab+'self.taggedparams='+str(taglist))
    else:
      myret.append(tab+'self.taggedparams=[]')
    if untaglist:
      myret.append(tab+'self.untaggedparams='+str(untaglist))
    else:
      myret.append(tab+'self.untaggedparams=[]')
 
    return myret
  
  def buildCallMethod(self,metadata):
    """docstring for buildCallMethod"""
    myret = []

    try:
      rawlist = metadata._types._flags._flag
      flaglist = [(str(i._id),True) if i._default else (str(i._id),False) for i in rawlist]
    except AttributeError:
      flaglist = []
    try:
      rawlist = metadata._types._taggedParams._param
      taglist = [(str(i._id),"'"+str(i._default)+"'") if i._default else (str(i._id),"''") for i in rawlist]
    except AttributeError:
      taglist = []
    try:
      rawlist = metadata._types._untaggedParams._param
      untaglist = [(str(i._id),"''") for i in rawlist]
    except AttributeError:
      untaglist = []
    myparams = []
    myparams.extend(flaglist)
    myparams.extend(taglist)
    myparams.extend(untaglist)
    myparams=map(lambda x: (x[0].replace('-','_'),x[1]),myparams)
    # add call function start to return array
    myret.append('def __call__(self,'+','.join('='.join((i[0],str(i[1]))) for i in myparams)+',localRun=False, execPath=' + repr(self.executable) + '):')
    # add variable assignment lines
    myret.extend([tab+'self._'+i[0]+'='+i[0] for i in myparams])
    # add boilerplate
    myret.extend([tab+'myflags=[]',\
                  tab+'mytaggedparams=[]',\
                  tab+'myuntaggedparams=[]',\
                  tab+'for i in self.flags:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'myflags.append(i)',\
                  tab+'for i in self.taggedparams:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'mytaggedparams.append((i,getattr(self,varname)))',\
                  tab+'for i in self.untaggedparams:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'myuntaggedparams.append((i,getattr(self,varname)))',\
                  tab+'from WebServices import OpalUtil',\
                  tab+'self.myOpalUtil = OpalUtil.OpalUtil(self)',\
                  tab+'outurls = self.myOpalUtil.launchJob(self.url,myflags,mytaggedparams,myuntaggedparams,self.metadata,localRun,execPath)',\
                  tab+'return outurls'])
    return myret

  def buildCallMethodFromCache(self, params):
    """docstring for buildCallMethod"""
    myret = []
    flaglist = []
    taglist = []
    untaglist = []

    for k, v in params.iteritems():
      if v['config_type'] == 'FLAG':
        if v['default'] == 'True':
          flaglist.append((k, True))
        else:
          flaglist.append((k, False))
      elif v['config_type'] == 'TAGGED':
        if v['default']:
          taglist.append((k, "'" + v['default'] + "'"))
        else:
          taglist.append((k, "''"))
      elif v['config_type'] == 'UNTAGGED':
        untaglist.append((k, "''"))
      else:
        print "ERROR: Invalid config_type"

    myparams = []
    myparams.extend(flaglist)
    myparams.extend(taglist)
    myparams.extend(untaglist)
    myparams=map(lambda x: (x[0].replace('-','_'),x[1]),myparams)
    # add call function start to return array
    myret.append('def __call__(self,'+','.join('='.join((i[0],str(i[1]))) for i in myparams)+',localRun=False, execPath=' + repr(self.executable) + '):')
    # add variable assignment lines
    myret.extend([tab+'self._'+i[0]+'='+i[0] for i in myparams])
    # add boilerplate
    myret.extend([tab+'myflags=[]',\
                  tab+'mytaggedparams=[]',\
                  tab+'myuntaggedparams=[]',\
                  tab+'for i in self.flags:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'myflags.append(i)',\
                  tab+'for i in self.taggedparams:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'mytaggedparams.append((i,getattr(self,varname)))',\
                  tab+'for i in self.untaggedparams:',\
                  tab+tab+'varname=\'_\' + i.replace(\'-\',\'_\')',\
                  tab+tab+'if getattr(self,varname):',\
                  tab+tab+tab+'myuntaggedparams.append((i,getattr(self,varname)))',\
                  tab+'from WebServices import OpalUtil',\
                  tab+'self.myOpalUtil = OpalUtil.OpalUtil(self)',\
                  tab+'outurls = self.myOpalUtil.launchJobCachedParams(self.url,myflags,mytaggedparams,myuntaggedparams,self.params,localRun,execPath)',\
                  tab+'return outurls'])
    return myret
  
  def buildDefaultInitMethod(self,url):
    """docstring for buildDefaultInit"""
    myret = ['def __init__(self):',\
            tab+'self.url=\''+url+'\'',\
            tab+'from mglutil.web.services.AppService_client import AppServiceLocator,getAppMetadataRequest',\
            tab+'appLocator = AppServiceLocator()',\
            tab+'appServicePort = appLocator.getAppServicePort(self.url)',\
            tab+'req = getAppMetadataRequest()',\
            tab+'self.metadata = appServicePort.getAppMetadata(req)'
    ]
    myret.append(tab+'self.commandline=\'\'')
    myret.append(tab+'self.inputfiles=[]')
    return myret

  def buildDefaultInitMethodFromCache(self,url):
    """docstring for buildDefaultInit"""
    myret = ['def __init__(self):',\
            tab+'self.url=\''+url+'\'',\
            tab+'from mglutil.web.services.AppService_client import AppServiceLocator,getAppMetadataRequest',\
#            tab+'appLocator = AppServiceLocator()',\
#            tab+'appServicePort = appLocator.getAppServicePort(self.url)',\
#            tab+'req = getAppMetadataRequest()',\
#            tab+'self.metadata = appServicePort.getAppMetadata(req)'
    ]
    myret.append(tab+'self.commandline=\'\'')
    myret.append(tab+'self.inputfiles=[]')
    return myret
  
  def buildDefaultCallMethod(self):
    """docstring for buildDefaultCallMethod"""
    myret = ["def __call__(self,commandline='',inputfiles=[], numProcs='1',localRun=False,execPath=" + repr(self.executable) + "):",\
              tab+'from WebServices import OpalUtil',\
              tab+'from string import atoi',\
              tab+'self.myOpalUtil = OpalUtil.OpalUtil(self)',\
              tab+'outurls = self.myOpalUtil.launchBasicJob(self.url,commandline,inputfiles,atoi(numProcs),localRun,execPath)',\
              tab+'return outurls']
    return myret

  def addOnStoppingExecution(self):
    """ this function adds the onStoppingExecution 
        to destroy running job when users terminate the 
        workflow
        TODO not used anymore
    """
    retstring = tab + "def onStoppingExecution(self):\n" +\
      tab+tab+ "print \"calling the onStopping execution\"\n" +\
      tab+tab+ "#self.myOpalUtil.onStoppingExecution()\n"
    return retstring

  def which (self, filename):
    """
        which definition: given an executable if found on the current path it return the full path to the executable
                        otherwise it returns ""
    """
    if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
      p = os.defpath
    else:
      p = os.environ['PATH']
    pathlist = p.split (os.pathsep)
    for path in pathlist:
      f = os.path.join(path, filename)
      if os.access(f, os.X_OK):
        return f
      #let's try harder to look for the command .bat .sh .exe 
      #expecially for windows
      fAlternative = f + '.exe'
      if os.access(fAlternative, os.X_OK):
        return fAlternative
      fAlternative = f + '.sh'
      if os.access(fAlternative, os.X_OK):
        return fAlternative
      fAlternative = f + '.bat'
      if os.access(fAlternative, os.X_OK):
        return fAlternative
    return ""


#wrap = OpalWrapper()
#print wrap.generate('http://ws.nbcr.net/opal2/services/pdb2pqr_1.4.0')

