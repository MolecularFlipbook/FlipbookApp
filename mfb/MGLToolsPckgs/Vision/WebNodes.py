## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

import types, numpy.oldnumeric as Numeric, re, urllib, string

from NetworkEditor.items import NetworkNode
from mglutil.web.HTMLParser import ParseHTML


def buildCGIWidget(node, form):
    for field in form.fieldOrder:
        inputString = ""
        argsString = ""
        name = field[0]
        dict = eval('form.'+field[1])

        if type(dict[name]) == types.DictType:
            dict = dict[name]

        if dict.has_key('value'):
            value = dict['value']
        else:
            value = None
        fieldType = field[1]

        if fieldType == 'input':
            if dict['type'] in ['submit', 'reset', 'password']:
                print 'INPUT OF TYPE '+dict['type']+\
                ' NOT SUPPORTED YET!' 
                continue

            elif dict['type'] in ['text', None]:
                node.widgetDescr[name] = {
                    'class':'NEEntry',
                    'initialValue':value,
                    'labelCfg':{'text':name,}, 'labelSide':'left', }
                node.inputPortsDescr.append( {'name':name} )
                inputString = inputString + name + ', '
                argsString = argsString + name + '=' + name + ', '

            elif dict['type'] == 'file':
                node.widgetDescr[name] = {
                    'class':'NEEntryWithFileBrowser', 'title':name,
                    'labelCfg':{'text':name, 'foreground':'blue',},
                    'labelSide':'left', }
                node.inputPortsDescr.append( {'name':name} )
                inputString = inputString + name + ', '
                argsString = argsString + name + '=' + name + ', '

        elif fieldType == 'hiddenInput':
            argsString = argsString+name+'=\"'+ value +'\", '


        elif fieldType == 'radiobutton':
            radioValues = []
            for val in dict[name]:
                radioValues.append(val[0])
            node.widgetDescr[name] = {
                'class':'NERadioButton',
                'valueList':radioValues}

            node.inputPortsDescr.append( {'name':name} )
            inputString = inputString + name + ', '
            argsString = argsString + name + '=' + name +', '

        elif fieldType == 'checkbutton':
            for checkbox in dict:
                cstatus = checkbox[1]
                cvalue = checkbox[0]
                node.widgetDescr[cvalue] = {
                    'class':'NECheckButton',
                    'initialValue':cvalue,
                    'labelCfg':{'text':cvalue},
                    'labelSide':'left',
                    'status':cstatus
                    }
                node.inputPortsDescr.append( {'name':name} )
                inputString = inputString + name + ', '
                argsString = argsString + name + '=' + name +', '

        elif fieldType == 'select':
            options = dict['options']
            node.widgetDescr[name] = {
            'class': 'NEComboBox',
            'choices':options,
            'labelCfg':{'text':name}, 'labelSide':'w'}
            node.inputPortsDescr.append( {'name':name} )
            inputString = inputString + name + ', '
            argsString = argsString + name + '=' + name + ', '

        elif fieldType == 'textarea':
            node.widgetDescr[name] = {
            'class': 'NEScrolledText', 'hull_width':200,
            'hull_height':100, 'title':name, 'button':None}
            node.inputPortsDescr.append( {'name':name} )
            inputString = inputString + name + ', '
            argsString = argsString + name + '=' + name + ', '
    


class WebBrowser(NetworkNode):

    def __init__(self, name='Web Browser', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append( {
            'name':'URL', 'datatype':'string', 'required':False,
            } )
        self.inputPortsDescr.append( {
            'name':'filename', 'datatype':'string', 'required':False,
            } )

        from grail.grailApp import getGrailApp
        self.browser = getGrailApp()

        self.clientObj = GoogleClient()

        code = """def doit(self, URL, filename):

        if self.inputPorts[0].hasNewValidData():
            self.browser.context.load(URL[0])
        elif self.inputPorts[1].hasNewValidData():
            import os
            self.browser.context.load('file:/'+filename[0])
\n"""

        self.setFunction(code)

        
    
class PublicHttpClient:

    def __init__(self, url):
        self.url = url
        self.arguments = {}


    def argCheck(self):
        return 1
    
    def run(self):
        if self.argCheck() == 0:
            return
        args = urllib.urlencode( self.arguments )
        f = urllib.urlopen(self.url, args)
        return f.read()


    def setArguments(self, **kw):
        for k,v in kw.items():
            if k not in self.arguments.keys():
                raise RuntimeError (k+' is not a valid argument')
            
            if type(v) in (types.FloatType, types.IntType,
                           types.LongType, types.StringType):
                self.arguments[k] = v
            else:
                pat = re.compile("[\[,\]\012]")
                arrayStr = re.sub(pat, '', str(Numeric.array(v).ravel()) )
                c = string.split(arrayStr)
                c = map( float, c )
                c = re.sub(pat, '', str(c) )
                self.arguments[k] = c

     
class ConsurfClient(PublicHttpClient):

    def __init__(self):
        self.urlBase = 'http://consurf.tau.ac.il/'
        self.cgi = 'cgi-bin/consurf/consurf.cgi'
        url = self.urlBase + self.cgi
        PublicHttpClient.__init__(self, url)

        self.arguments = {
            "pdb_ID":    '1crn',
            "chain":     'none',
            "ALGORITHM": 'Likelihood', # or "Parsimony"
            "ITERATIONS": '1',
            "ESCORE":     '0.001',
            "MAX_NUM_HOMOL": '50'
            }

    def getResultPage(self, result):
        # parses html returned by job submission and returns either the
        # path to the result page (i.e. results/1032307369/index.htm) or None
        lines = string.split(result)
        page = None
        for l in lines:
            if l[:18]=="/~consurf/results/":
                page = l[1:string.find(l,"index.htm")]
                break
        return page


    def checkForCompletion(self, page):
        # opens the result page and check every 30 seconds if the 
        # computation is done by checking is the page contains
        # "ConSurf finished calculation"
        url = self.urlBase + page + 'output.html'
        print 'checkForCompletion', url
        done = 0
        count = 0
        import time
        while 1:
            f = urllib.urlopen(url)
            result = f.read()
            f.close()
            count = count + 1
            print 'checkForCompletion COUNT: ', count
            done = string.find(result, "ConSurf finished calculation")
            if done != -1:
                break
            if string.find(result, "ERROR") != -1:
                print "ERROR ********************************************"
                print result
                break
            if count == 40:
                print "giving up after %d minutes"%(count*0.5,)
                break
            time.sleep(30)
        
        url = self.urlBase + page + 'pdb%s.gradesPE'%self.arguments['pdb_ID']
        return url


    def getConservationScores(self, url):
        f = urllib.urlopen(url)
        result = f.read()
        f.close()
        lines = string.split(result, '\n')
        scores = []
        i = 0 
        for l in lines:
            if l[-7:]=='VARIETY':
                break
            i = i + 1
        for l in lines[i+1:]:
            words = string.split(l)
	    if len(words) < 5: continue
            if words[2] == '-':
                continue
            col = string.find(words[2], ':')
            scores.append( ( words[2][:col], words[2][col+1],
                             float(words[3]), int(words[4]) ) )
        return scores


from NetworkEditor.items import NetworkNode

class ConsurfClientNode(NetworkNode):

    def readCache(self, cacheFile):
        try:
            f = open(cacheFile)
            data = f.readlines()
            f.close()
            data = map(string.split, data)
            cache = {}
            for k,v in data:
                cache[k] = v
        except IOError:
            cache = {}

        return cache


    def saveCache(self, cacheFile):
        try:
            f = open(cacheFile, 'w')
            map( lambda x, f=f: f.write("%s %s\n"%x), self.cache.items())
            f.close()
        except IOError:
            print 'Could not open cache file %s for saving'%cacheFile

            
    def getKey(self):
        args = self.clientObj.arguments
        key = args["pdb_ID"] + args["chain"] + args["ALGORITHM"] + \
              args["ITERATIONS"] + args["ESCORE"] + args["MAX_NUM_HOMOL"]
        return string.strip(key)


    def checkForCompletion(self, page):
        # opens the result page and check every 30 seconds if the 
        # computation is done by checking is the page contains
        # "ConSurf finished calculation"
        clientObj = self.clientObj
        if self.flashNodesWhenRun is None:
            self.flashNodesWhenRun = self.editor.flashNodesWhenRun
        self.editor.flashNodesWhenRun = 0 # to prevent from turning gray
        url = clientObj.urlBase + page + 'output.html'
        print 'checkForCompletion', url
        f = urllib.urlopen(url)
        result = f.read()
        f.close()
        print 'checkForCompletion'
        done = string.find(result, "ConSurf finished calculation")
        if done != -1:
            resultUrl = clientObj.urlBase + page + \
                        'pdb%s.gradesPE'%clientObj.arguments['pdb_ID']
            key = self.getKey()
            self.cache[key] = resultUrl
            self.saveCache(self.cacheFile)
            scores = clientObj.getConservationScores(resultUrl)

            self.outputData(Fscore=map(lambda x: x[2], scores))
            self.outputData(Iscore=map(lambda x: x[3], scores))
            self.outputData(resultPageURL=resultUrl)
            self.editor.flashNodesWhenRun = self.flashNodesWhenRun
            if self.editor.flashNodesWhenRun:
                col = self.getColor()
                if col=='#557700': # after successfull run of failed node
                    col = node.colorBeforeFail
                #else:
                #    self.dirty = 0
                self.setColor('gray85')

            # FIXME: should really schedule all children here
            self.schedule()
            return

        if string.find(result, "ERROR") != -1:
            print "ERROR ********************************************"
            print result
            return
        #if count == 40:
        #    print "giving up after %d minutes"%(count*0.5,)
        #    break
        self.editor.root.after( 30000, self.checkForCompletion, page )

    
    def __init__(self, name='Consurf Client', cacheFile='.consrf.cache',
                 **kw):
        kw['name'] = name
        self.runInBackground = 1
        self.cacheFile = cacheFile
        self.cache = self.readCache(cacheFile)
        apply( NetworkNode.__init__, (self,), kw )

        self.inputPortsDescr.append( {'name':'molecule',
                                      'datatype':'MoleculeSet'} )
        self.inputPortsDescr.append( {'name':'chain', 'required':False,
                                      'datatype':'string'} )
        self.inputPortsDescr.append( {'name':'algorithm', 'required':False,
                                      'datatype':'string'} )

        self.outputPortsDescr.append( {'name':'Fscore',
                                       'datatype':'list'} )
        self.outputPortsDescr.append( {'name':'Iscore',
                                       'datatype':'list'} )
        self.outputPortsDescr.append( {'name':'resultPageURL',
                                       'datatype':'string'} )

        self.clientObj = ConsurfClient()
        
        code = """def doit(self, molecule, chain, algorithm):
    self.flashNodesWhenRun = None
    mol = molecule[0]
    assert algorithm is None or algorithm[0] in ['Likelihood', 'Parsimony']
    if chain is None or chain[0] not in mol.chains.id:
        chain = molecule[0].chains[0].id
    if algorithm is None:
        algorithm = ['Likelihood']
    self.clientObj.setArguments( pdb_ID=mol.name,
            chain=chain[0], ALGORITHM=algorithm[0])
    key = self.getKey()
    if self.cache.has_key(key):
        resultUrl = self.cache[key]
        scores = self.clientObj.getConservationScores(resultUrl)

        self.outputData(Fscore=map(lambda x: x[2], scores))
        self.outputData(Iscore=map(lambda x: x[3], scores))
        self.outputData(resultPageURL=resultUrl)
    else:
        result = self.clientObj.run()
        resultPage = self.clientObj.getResultPage(result)
        self.checkForCompletion(resultPage)\n"""

        self.setFunction(code)
        

    def beforeAddingToNetwork(self, net):
        try:
            from MolKit.VisionInterface.MolKitNodes import molkitlib
            net.editor.addLibraryInstance(molkitlib,
                                          'MolKit.VisionInterface.MolKitNodes',
                                          'molkitlib')
        except:
            print 'Warning! Could not import molkitlib from MolKit/VisionInterface'


class GoogleClient(PublicHttpClient):

    def __init__(self):
        self.urlBase = 'http://www.google.com/'
        self.cgi = 'search'
        url = self.urlBase + self.cgi
        PublicHttpClient.__init__(self, url)

        self.arguments = {
            "q":  '',
            "hl": 'en',
            "ie": 'ISO-8859-1',
            }


class GoogleClientNode(NetworkNode):

    def __init__(self, name='Consurf Client', cacheFile='.consrf.cache',
                 **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )
        self.widgetDescr['searchString'] = {
            'class':'NEEntry', 'master':'node'
            }
        self.inputPortsDescr.append( {
            'name':'searchString', 'datatype':'string'} )
        self.outputPortsDescr.append( {
            'name':'html', 'datatype':'string'
            } )
        self.outputPortsDescr.append( {
            'name':'links', 'datatype':'list'
            } )

        self.clientObj = GoogleClient()

        code = """def doit(self, searchString):
        
        self.outputData(html=resultHtml)\n"""

        self.setFunction(code)


class CGIFormNode(NetworkNode):
    
    def __init__(self, name='CGIForm Node', CGIFormObj=None, **kw):
        kw['name'] = name

        self.CGIFormObj = CGIFormObj

        apply( NetworkNode.__init__, (self,), kw )

        if CGIFormObj is not None:
            buildCGIWidget(self, CGIFormObj)

        code = """def doit(self, *args):
                argsDict = {}
                for port, val in map(None, self.inputPorts, args):
                    argsDict[port.name] = val
                apply(self.CGIFormObj.setArguments, (), argsDict)
                result=self.CGIFormObj.run()
                if result:
                    self.outputData(html=[result])\n"""

        self.outputPortsDescr.append( {
            'name':'html', 'datatype':'list'
            } )

        self.setFunction(code)


    def getNodeDefinitionSourceCode(self, lib, nodeId, nodeUniqId, networkName,
                                    ):
        
        txt = '#create CGI Form object:\n'
        txt = txt + 'from mglutil.web.HTMLParser import CGIForm\n'
        txt = txt + 'obj='+self.CGIFormObj.getCreationSourceCode()

        self.constrkw['CGIFormObj']='obj' # temporarily add kw to generate
                                          # correct list of arguments
        src = NetworkNode.getNodeDefinitionSourceCode(self, lib, nodeId,
                                                    nodeUniqId, networkName)

        del self.constrkw['CGIFormObj']   # now we remove it

        for line in src[0]:
            txt = txt + line
        
        return [txt], nodeId, nodeUniqId


class GetCGIForms(NetworkNode):

    def __init__(self, name='GetCGIForms', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.widgetDescr['url'] = {'class':'NEEntry', 'master':'node',
            'labelCfg':{'text':'url:'}, 'labelSide':'left' }
        self.inputPortsDescr.append( {'name':'url', 'datatype':'string'} )

        self.outputPortsDescr.append( {'name':'forms', 'datatype':'list'} )

        self.parserObj = ParseHTML(mode='forms')
        
        code = """def doit(self, url):

        if url is None or url == '': return
        if(url[:7]) != 'http://': url = 'http://' + url

        forms = self.parserObj.doit(url)
        posx = 60
        posy = 60

        inputString = ""
        argsString = ""
        
        for form in forms:
            node = CGIFormNode(CGIFormObj=None, name=form.name)
            
            posX = self.posx + posx
            posY = self.posy + posy
            posx = posx + 20
            posy = posy + 25

            # this method is defined outside this node
            buildCGIWidget(node, form)

            self.editor.currentNetwork.addNode(node, posX, posY)
            #node.addOutputPort(name='html', datatype='list')
            node.CGIFormObj = form
            node.CGIFormObj.setURL(url)

        self.outputData(forms=forms)\n"""

        self.setFunction(code)


from Vision.VPE import NodeLibrary
weblib = NodeLibrary('Web', '#bb4040')

weblib.addNode(ConsurfClientNode, 'Consurf', 'Filter')
#weblib.addNode(WebBrowser, 'Web Browser', 'Output') # not supported any longr
weblib.addNode(GetCGIForms, 'Get CGI Forms', 'Filter')
#weblib.addNode(CGIFormNode, 'CGI Form Node', 'Output')


if __name__ == '__main__':
    print 'Creating client Object'
    server = ConsurfServer()
    print 'submitting job'
    server.setArguments( pdb_ID='2plv', chain='1', ALGORITHM="Likelihood")
    result = server.run()
    print 'get temporary result page'
    resultPage = server.getResultPage(result)
    print ' wait for completion'
    resultUrl = server.checkForCompletion(resultPage)
    print ' COMPLETED'
    scores = server.getConservationScores(resultUrl)
    print scores

    #c = GoogleClient()
    #c.setArguments(q='foo')
    #result = c.run()
    
