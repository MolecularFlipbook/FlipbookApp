import sys
import time
import httplib
import urllib
import xml.dom.minidom
import os
import shutil
import subprocess
import copy
import urlparse
import pickle

from mglutil.web.services import AppService_client

class OpalCache:
    def getServices(self, opal_url):
        services = []

        if opal_url.find("/opal2") != -1:
            service_list_url = opal_url + "/opalServices.xml"
            opener = urllib.FancyURLopener({})
            socket = opener.open(service_list_url)
            text = socket.read()
            feed = xml.dom.minidom.parseString(text)

            for entry in feed.getElementsByTagName('entry'):
                link = entry.getElementsByTagName('link')[0]
                service = link.getAttribute('href')
                services.append(str(service))
        else:
            print "ERROR: No opal2 contained in URL"

        return services

    def getFileName(self, url):
        hostname = url.split('http://')[1].split('/')[0]
        hostname = hostname.replace(':', '+')
        servicename = os.path.basename(url)
        filename = os.path.join(hostname, servicename)

        return filename
    
    def getBinaryLocation(self, url, dir):
        (bl, x2, x3) = self.getCache(url, dir)
        return bl

    def getParams(self, url, dir):
        (x1, params, x3) = self.getCache(url, dir)
        return params

    def getSeparator(self, url, dir):
        (x1, x2, separator) = self.getCache(url, dir)
        return separator

    def getServicesFromCache(self, url, dir, disable_inactives=True):
        hostname = url.split('http://')[1].split('/')[0]
        hostname = hostname.replace(':', '+')
        hostcd = os.path.join(dir, hostname)
        inactivedir = os.path.join(os.path.join(dir, "inactives"), hostname)
        files = []
        inactives = []

        try:
            files = os.listdir(hostcd)
            inactives = os.listdir(inactivedir)
            actives = set(files) - set(inactives)
        except:
            print "ERROR: Cache directory for " + url + " does not exist!"
            print "       Are you connected to the internet???"
            return []

        if disable_inactives:
            services = map(lambda x: url + '/services/' + x, actives)
        else:
            services = map(lambda x: url + '/services/' + x, files)

        return services

    def getCache(self, url, dir):
        file = os.path.join(dir, self.getFileName(url))
        params = pickle.load(open(file))
        
        return params

    def isCacheValid(self, url, dir, days=30):
        fn = self.getFileName(url)
        cachedir = os.path.join(dir, os.path.dirname(fn))
        filename = os.path.join(dir, fn)

        if not(os.path.exists(cachedir)) or not(os.path.exists(filename)):
            return False

        if (time.time() - os.path.getmtime(filename) > days * 86400):
            print "*** [WARNING]: Cache for " + url + " is older than " + days + " days!"
            return False
        
        return True
        

    def writeCache(self, url, dir, days=30):
        fn = self.getFileName(url)
        cachedir = os.path.join(dir, os.path.dirname(fn))

        if not(os.path.exists(cachedir)):
            os.mkdir(cachedir)

        filename = os.path.join(dir, fn)

        if not(self.isCacheValid(url, dir, days)):
            print "[INFO]: Writing cache for " + url + " in " + filename

            appLocator = AppService_client.AppServiceLocator()
            appServicePort = appLocator.getAppServicePort(url)
            req = AppService_client.getAppMetadataRequest()
            metadata = appServicePort.getAppMetadata(req)

            appLocator = AppService_client.AppServiceLocator()
            appServicePort = appLocator.getAppServicePort(url)
#            req = AppService_client.getAppConfigRequest()
#            metadata2 = appServicePort.getAppConfig(req)
#            executable = metadata2._binaryLocation

            try:
                req = AppService_client.getAppConfigRequest()
                metadata2 = appServicePort.getAppConfig(req)
                executable = metadata2._binaryLocation
            except:
                executable = 'NA'
                pass

            separator = None
            params = {}
            
            try:
                rawlist = metadata._types._flags._flag
                order = 0

                for i in rawlist:
                    myhash = {}
                    myhash = {'type': 'boolean'}
                    myhash['config_type'] = 'FLAG'
                    myhash['tag'] = str(i._tag)
                    myhash['default'] = 'True' if str(i._default)=='True' else 'False'
                    myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
                    myhash['order'] = order
                    params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
                    order = order + 1
            except AttributeError:
                pass
            try:
                rawlist = metadata._types._taggedParams._param
                separator = metadata._types._taggedParams._separator
                order = 0
            
                for i in rawlist:
                    myhash = {}
                    myhash['config_type'] = 'TAGGED'
                    if i._value:
                        myhash['type'] = 'selection'
                        myhash['values'] = [str(z) for z in i._value]
                    else:
                        myhash['type'] = str(i._paramType)
                        if(str(i._paramType)=="FILE"):
                            myhash['ioType'] = str(i._ioType)
                    myhash['description'] = str(i._textDesc) if i._textDesc else 'No Description'
                    myhash['default'] = str(i._default) if i._default else None
                    myhash['tag'] = str(i._tag)
                    myhash['separator'] = separator
                    myhash['order'] = order
                    params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
                    order = order + 1
            except AttributeError:
                pass
            try:
                rawlist = metadata._types._untaggedParams._param
                order = 0

                for i in rawlist:
                    myhash = {}
                    myhash['config_type'] = 'UNTAGGED'
                    myhash['type'] = str(i._paramType)
                    if(str(i._paramType)=="FILE"):
                        myhash['ioType'] = str(i._ioType)
                    myhash['description'] = str(i._textDesc)
                    myhash['default'] = str(i._default) if i._default else None
                    myhash['tag'] = str(i._tag)
                    myhash['order'] = order
                    params[str(i._id).replace('-','_')] = copy.deepcopy(myhash)
                    order = order + 1
            except AttributeError:
                pass

            lock = filename + '.lock'

            if os.path.exists(lock) and time.time() - os.path.getmtime(lock) > 100:
                os.remove(lock)
            
            if not(os.path.exists(lock)):
                open(lock, 'w').close() 
                pickle.dump((executable, params, separator), open(filename, "wb"))
                os.remove(lock)



        
        
