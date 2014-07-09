# Author: Wes Goodman
# Module for launching Opal jobs within Vision
import sys
import traceback
import time
import httplib
import urllib
import os
import shutil
import subprocess
import tempfile
import urlparse


from mglutil.web.services.AppService_client import AppServiceLocator, \
      launchJobRequest, getOutputsRequest, queryStatusRequest, destroyRequest
from mglutil.web.services.AppService_types import ns0

from ZSI.TC import String
from ZSI import *

from time import strftime
from datetime import datetime

from NetworkEditor.items import FunctionNode

class OpalWSNode(FunctionNode):

    def getNodeSourceCodeForWidgetValue(self, networkName, portIndex,
                                        indent="", ignoreOriginal=False,
                                        full=0, nodeName=None):
        lines = FunctionNode.getNodeSourceCodeForWidgetValue(
            self, networkName, portIndex, indent=indent,
            ignoreOriginal=ignoreOriginal, full=full, nodeName=nodeName)

        line = lines[0]
        nsindent = len(line.split(indent)) - 1
        sindent = ''

        for i in range(0, nsindent):
            sindent += indent
        for i in range(0, len(lines)):
            lines[i] = indent + lines[i]

        if nodeName == None:
            nodeName = self.getUniqueNodeName()

        hn = nodeName[nodeName.find('_')+1:nodeName.rfind('_')].replace('_', '.')
        sn = nodeName.split('_')[0]
        mmsg = '[WARNING] Opal web service option <' + \
            self.inputPortsDescr[portIndex]['name'] + \
            '> no longer exists for ' + sn + ' on ' + hn
        mmsg = "\'" + mmsg + "\'"
        lines.insert(0, sindent + 'try:\n')
        lines.append(sindent + 'except KeyError:\n')
        lines.append(sindent + indent + 'print ' + mmsg + '\n')
        lines.append(sindent + indent + 'pass\n')
        
        return lines


class OpalUtil(object):
    """
    OpalUtil: Static class containing generic utility wrappers for exectuting Opal Web Service calls
    """
    def __init__(self, opalNode):
        """
          initialize OpalUtil object
        """

        self.opalNode = opalNode
        self.jobID = None
        #add link to OpalObject

    def onStoppingExecution(self):
        #kill running job
        #TODO kill local running job
        if (self.jobID != None):
            #ok let's kill the running job
            print "Killing job: " + self.jobID
            appLocator = AppServiceLocator()
            appServicePort = appLocator.getAppServicePort(self.opalNode.url)
            destroyReq = destroyRequest(self.jobID)
            resp = appServicePort.destroy(destroyReq)

          

    def launchJob(self,url,flags,taggedparams,untaggedparams,meta,localRun=False,executable=''):
        """
          launchJob description:
          @input:
            -url: for application endpoint
            -flags: list of flag ids for the application
            -taggedparams: list of tuples: [(tag_id,value),...]
            -untaggedparams: list of tuples: [(tag_id,value),...]
            -meta: getAppMetadata output object
          @output:
            -returns tuple: (job code, status message, output url)
        """

        #print "launchJob"
        # build two hashes: flaghash, taggedhash from xml
        #  Index on id, value will be tag    
        flaghash = self.buildHash(meta,'flags')
        taggedhash = self.buildHash(meta,'taggedParams')
        separator = meta._types._taggedParams._separator

        if ( separator == None ):
            separator=' '
        # map from flag ids to flag tags
        flagtags = map(lambda x: flaghash[x],flags)
        command = ' '.join(flagtags)
        inputFiles = []

        for (tagid,val) in taggedparams:
            #let's create the tagged params part of the command line 
            taggedobject = self.getTaggedParam(meta,tagid)
            if (taggedobject._paramType=='FILE') and (taggedobject._ioType=='INPUT'):
                inputFiles.append(val)
                command += ' '+taggedobject._tag+separator+os.path.basename(val)
            else:
                #this is not an input file handle normally
                command += ' '+taggedobject._tag+separator+val
        for (tagid,val) in untaggedparams:
            #now let's see the untagged part of the command line
            #match id to ioType
            #  if input, determine if file or string
            #  if output, just put the string
            untaggedobject = self.getUntaggedParam(meta,tagid)
            if (untaggedobject._paramType=='FILE') and (untaggedobject._ioType=='INPUT'):
                inputFiles.append(val)
                command += ' '+os.path.basename(val)
            else:
                command += ' '+val

        print "The node " + self.opalNode.__class__.__name__ + " is going to execute the command: " + command
        #common code
        if (localRun==False):
            #print "Local run is: " + str(localRun) + " running remotely"
            results = self.executeWebJob(url, command, inputFiles, None)
        else :
            results = self.executeLocal(url, command, inputFiles, executable)
        return results


    def launchJobCachedParams(self,url,flags,taggedparams,untaggedparams,params,localRun=False,executable=''):
        """
          launchJob description:
          @input:
            -url: for application endpoint
            -flags: list of flag ids for the application
            -taggedparams: list of tuples: [(tag_id,value),...]
            -untaggedparams: list of tuples: [(tag_id,value),...]
            -meta: getAppMetadata output object
          @output:
            -returns tuple: (job code, status message, output url)
        """

        flaghash = {}
        taggedhash = {}
        untagged_count = 0
        tagged_count = 0
        flag_count = 0
        untagged_order = {}
        tagged_order = {}
        flag_order = {}

        for k, v in params.iteritems():
            if v['config_type'] == 'FLAG':
                flaghash[k] = v['tag']
                flag_count = flag_count + 1
            elif v['config_type'] == 'TAGGED':
                taggedhash[k] = v['tag']
                tagged_count = tagged_count + 1
                separator = v['separator']
            elif v['config_type'] == 'UNTAGGED':
                untagged_count = untagged_count + 1

        try:        
            if separator == None:
                separator = ' '
        except:
            separtor = ' '


        #if separator == None:
         #   separator = ' '

        # map from flag ids to flag tags
        # flagtags = map(lambda x: flaghash[x],flags)
        # command = ' '.join(flagtags)

        command = ' '

        for tagid in flags:
            order = params[tagid]['order']
            flag_order[order] = tagid
        for i in range(flag_count):
            try:
                tagid = flag_order[i]
                if tagid:
                    command += ' ' + params[tagid]['tag']
            except:
                pass
            

        inputFiles = []

        for (tagid, val) in taggedparams:
            order = params[tagid]['order']
            tagged_order[order] = (tagid, val)
        for i in range(tagged_count):
            try:
                (tagid, val) = tagged_order[i]
                if params[tagid]['type'] == 'FILE' and params[tagid]['ioType'] == 'INPUT':
                    inputFiles.append(val)
                    command += ' ' + params[tagid]['tag'] + separator + os.path.basename(val)
                else:
                    #this is not an input file handle normally
                    command += ' ' + params[tagid]['tag'] + separator + val
            except:
                pass

        for (tagid, val) in untaggedparams:
            order = params[tagid]['order']
            untagged_order[order] = (tagid, val)
        for i in range(untagged_count):
            try:
                (tagid, val) = untagged_order[i]
                if params[tagid]['type'] == 'FILE' and params[tagid]['ioType'] == 'INPUT':
                    inputFiles.append(val)
                    command += ' ' + os.path.basename(val)
                else:
                    #this is not an input file handle normally
                    command += ' ' + val                
            except:
                pass
        
        print "The node " + self.opalNode.__class__.__name__ + " is going to execute the command: " + command
        #common code
        if (localRun==False):
            #print "Local run is: " + str(localRun) + " running remotely"
            results = self.executeWebJob(url, command, inputFiles, None)
        else :
            results = self.executeLocal(url, command, inputFiles, executable)
        return results

    def getUntaggedParam(self,meta,tagid):
        """
        getUntaggedParam description:
        @input:
          -meta: application's metadata
          -tagid: id for parameter
        @output:
          -returns param object
        """
        untaggedlist = meta._types._untaggedParams._param
        for i in untaggedlist:
            if(i._id==tagid):
                return i
        return "NOT AN UNTAGGED PARAM"


    def getTaggedParam(self,meta,tagid):
        """
        getTaggedParam description:
        @input:
          -meta: application's metadata
          -tagid: id for parameter
        @output:
          -returns param object
        """
        taggedlist = meta._types._taggedParams._param
        for i in taggedlist:
            if(i._id==tagid):
                return i
        return "NOT AN UNTAGGED PARAM"


    def buildHash(self,meta,tagtype):
        """
        buildHash description:
        @input:
          -meta: application's metadata
          -id: an ID to use to know where to start building the hash
        @output:
          -returns hash[param_id] = param_tag
        """
        if(tagtype=='flags'):
            mylist = meta._types._flags._flag
        elif(tagtype=='taggedParams'):
            mylist = meta._types._taggedParams._param
        myhash = {}
        for i in mylist:
            myhash[str(i._id)] = str(i._tag)
        return myhash


    def launchBasicJob(self,url,commandline,inFilesPath,numProcs=None,localRun=False,executable=''):
        """
        launchBasicJob description:
        @input:
          -url: for application endpoint
          -inFilesPath: list of input files, an array of strings containing the paths
        """
        #print "launchBasicJob"
        #this should be moved in the constructor...

        print "The node " + self.opalNode.__class__.__name__ + " is going to execute the command: " + commandline
        if (localRun==False):
            results = self.executeWebJob(url, commandline, inFilesPath, numProcs)
        else :
            #local execution do not support number of cpu
            results = self.executeLocal(url, commandline, inFilesPath, executable)
        return results


    def executeWebJob(self, url, commandline, inFilesPath, numProcs):
        """ 
            executeWebJob description:
            it execute a job through OpalInterface
            @input:
                -url: the url where to reach the Opal service
                -commandline the command line to use for the execution
                -inputFiles an array of input file to upload, it should contains an array of string with the path to the file
                -numProcs the number of processors to use
        """

        inputFiles = []

        if inFilesPath != None:
            for i in inFilesPath:
                inputFile = ns0.InputFileType_Def('inputFile')
                inputFile._name = os.path.basename(i)
                if self.isOpal2(url):
                    #use attachment this is opal2 server

                    if os.name == 'dos' or os.name == 'nt': 
                        inputFile._attachment = open(i, "rb")
                    else:
                        inputFile._attachment = open(i, "r")
                else:
                    #it's not a opal2 server don't user attachment
                    infile = open(i, "r")
                    inputFile._contents = infile.read()
                    infile.close()
                inputFiles.append(inputFile)

        appLocator = AppServiceLocator()
        appServicePort = appLocator.getAppServicePort(url)

        req = launchJobRequest()
        req._argList = commandline
        req._inputFile = inputFiles
        req._numProcs = numProcs

        if inputFiles != []:
            print "Uploading input files..."

        resp_s = -1

        while resp_s == -1:
            try:
                resp = appServicePort.launchJob(req)
                resp_s = 0
            except FaultException, inst:
                estr = inst.fault.AsSOAP()
                estr = estr.split("<message>")[1].split("</message>")[0]
                t = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cte = time.mktime(datetime.now().timetuple())
                ete = cte + 60 * 60 + 10
                
                print "WARNING: " + t + " Opal FaultException from server: " + estr
                print "         will try again in about an hour" 
                while time.mktime(datetime.now().timetuple()) < ete:
                    if self.opalNode._vpe is not None:
                        self.opalNode._vpe.updateGuiCycle()
                        net = self.opalNode._node.network
                        if net.execStatus == 'stop':
                        #if self.opalNode._vpe.buttonBar.toolbarButtonDict['stop'].state == "disabled":
                            self.onStoppingExecution()
                            return None
                    time.sleep(0.5)
                pass
            except: # no internet
                s = -1
                while s == -1:
                    try:
                        urllib.urlopen(url)
                        s = 0
                    except IOError:
                        t = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        cte = time.mktime(datetime.now().timetuple())
                        ete = cte + 60
                        print "WARNING: " + t + " cannot connect to " + url
                        print "         Are you connected to the internet?"
                        print "         Will try again in about a minute"
                        while time.mktime(datetime.now().timetuple()) < ete:
                            if self.opalNode._vpe is not None:
                                self.opalNode._vpe.updateGuiCycle()
                                net = self.opalNode._node.network
                                if net.execStatus == 'stop':
                                #if self.opalNode._vpe.buttonBar.toolbarButtonDict['stop'].state == "disabled":
                                    #stop running job and return
                                    self.onStoppingExecution()
                                    return None
                            time.sleep(0.5)
                pass           
            pass

        if inputFiles != []:
            print "Done uploading input files."

        self.jobID = resp._jobID
        print "Job outputs URL: " + resp._status._baseURL # urlparse.urljoin(url, '/' + self.jobID)
        status = resp._status._code

        while(status!=4 and status!=8):
            try:
                status = appServicePort.queryStatus(queryStatusRequest(self.jobID))._code
            except FaultException, inst:
                estr = inst.fault.AsSOAP()
                estr = estr.split("<message>")[1].split("</message>")[0]
                t = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cte = time.mktime(datetime.now().timetuple())
                ete = cte + 60 * 60 + 10
                
                print "WARNING: " + t + " Opal FaultException from server: " + estr
                print "         will try again in about an hour" 
                while time.mktime(datetime.now().timetuple()) < ete:
                    if self.opalNode._vpe is not None:
                        self.opalNode._vpe.updateGuiCycle()
                        net = self.opalNode._node.network
                        if net.execStatus == 'stop':
                        #if self.opalNode._vpe.buttonBar.toolbarButtonDict['stop'].state == "disabled":
                            self.onStoppingExecution()
                            return None
                    time.sleep(0.5)
                pass
            except:
                status = -2
                try:
                    urllib.urlopen(url)
                except IOError:
                    status = -1
                    t = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    cte = time.mktime(datetime.now().timetuple())
                    ete = cte + 60
                    print "WARNING: " + t + " cannot connect to " + url
                    print "         Are you connected to the internet?"
                    print "         Will try again in about a minute"
                    while time.mktime(datetime.now().timetuple()) < ete:
                        if self.opalNode._vpe is not None:
                            self.opalNode._vpe.updateGuiCycle()
                            net = self.opalNode._node.network
                            if net.execStatus == 'stop':
                            #if self.opalNode._vpe.buttonBar.toolbarButtonDict['stop'].state == "disabled":
                                self.onStoppingExecution()
                                return None
                        time.sleep(0.5)

                    pass

                if status == -1:
                    pass

            if self.opalNode._vpe is not None:
                self.opalNode._vpe.updateGuiCycle()
                net = self.opalNode._node.network
                if net.execStatus == 'stop':                
                #if self.opalNode._vpe.buttonBar.toolbarButtonDict['stop'].state == "disabled":
                    #stop running job and return
                    self.onStoppingExecution()
                    return None

        if(status==8):
            #Job completed successfully
            resp = appServicePort.getOutputs(getOutputsRequest(self.jobID))
            outurls = [str(resp._stdOut),str(resp._stdErr)]
            if(resp._outputFile!=None):
                for i in resp._outputFile:
                    outurls.append(str(i._url))
        else:
            #Job died or something else went wrong
            resp = appServicePort.getOutputs(getOutputsRequest(self.jobID))
            outurls = [str(resp._stdOut),str(resp._stdErr)]

        return tuple(outurls)

    def isOpal2(self, url):
        """ it returns true if this service points to a opal2 server
            false in the other cases
        """
        if url.find("/opal2/") != -1:
            return True
        else:
            return False

    def executeLocal(self, url, command, inputFiles, executable):
        """
            executeLocal description:
            this functions is used to exectute a job on the local machine
            @input:
                -url: the url where to reach the Opal service
                -commandline the command line to use for the execution
                -inputFiles an array of input file to upload to the server (array of strings path)
                -numProcs the number of processors to use
        """
        #print "executeLocal"
        #setting up workind dir and input files
        #workingDir = os.tempnam()
        workingDir = tempfile.mkdtemp()
        print "Job output files directory is: " + workingDir
        #workingDir = workingDir + '/app' + str(int(time.time()*100 ))
        #os.mkdir(workingDir)
        if inputFiles != None:
            for i in inputFiles:
                shutil.copy(i,workingDir)
        #setting up input and error file
        output = open(workingDir + os.sep + 'stdout.txt', 'w')
        error = open(workingDir + os.sep + 'stderr.txt', 'w')
        #working directory
        cwd = os.getcwd()
        os.chdir(workingDir)
        #environmental variables
        pythonpath = os.getenv('PYTHONPATH')
        pythonhome = os.getenv('PYTHONHOME')
        pathorig = os.getenv('PATH')
        if ( pathorig.partition(':')[0].find('MGL') ): # there is the MGL python let's remove it
            os.putenv('PATH',pathorig.partition(':')[2])
        os.unsetenv('PYTHONPATH')
        os.unsetenv('PYTHONHOME')
        cmdExec=executable + ' ' + command
        #print 'going to exectute: ' + cmdExec + ' with input files: ' + str(inputFiles)
        p = subprocess.Popen(cmdExec.split(), stdout=output, stderr=error)
        while p.poll() == None:
            if self.opalNode._vpe is not None:
                self.opalNode._vpe.updateGuiCycle()
            time.sleep(0.5)
        #job finished cleaning up 
        #files
        output.close()
        error.close()
        #evironment variables
        if pythonpath != None:
            os.putenv('PYTHONPATH', pythonpath)
        if pythonhome != None:
            os.putenv('PYTHONHOME', pythonhome)
        os.putenv('PATH', pathorig)
        #going back to previous working dir
        os.chdir(cwd)
        outputFiles=[]
        for i in os.listdir(workingDir):
            #outputFiles.append('file://' + workingDir + '/' + i)
            outputFiles.append(workingDir +  os.sep + i)
        return outputFiles



