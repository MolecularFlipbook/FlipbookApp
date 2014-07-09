#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/ViewerFramework/serverCommands.py,v 1.19 2010/09/04 01:04:22 sanner Exp $
#
# $Id: serverCommands.py,v 1.19 2010/09/04 01:04:22 sanner Exp $
#

"""
This module implements classes to start a server and to connect to a server.
"""
from ViewerFramework.VFCommand import Command, CommandGUI
try:
    import ViewerFramework.imdCommands as imd
    imdFound = True
except ImportError:
    imdFound = False

from mglutil.popen2Threads import SysCmdInThread
from mglutil.gui.InputForm.Tk.gui import InputForm, InputFormDescr
import Tkinter

import sys, os
if os.name == 'nt': #sys.platform=='win32':
    mswin = True
else:
    mswin = False

class StartServer(Command):
    """ This class implements methods to start a server"""

    def checkDependencies(self, vf):
        import thread

    def doit(self):
        import thread
        com = self.vf.socketComm
        if com.port:
            print 'WARNING: server already running on port', com.port
            return
        self.vf.socketComm.startServer()
        thread.start_new(com.acceptClients, (self.vf.clients_cb,))

        self.vf.GUI.ROOT.after(300, self.vf.sendViewerState)

        # create a threadsafe command queue
        from Queue import Queue
        self.vf.cmdQueue = Queue(-1) # infinite size
        self.vf.GUI.ROOT.after(10, self.vf.runClientCommands)


class WebDrivenTutorial(Command):
    """start a web browser that can send commands over a socket to Viewerframework
    We use Karrigell-2.0.3 as a light webserver. The source of Karrigell
    need to be install in the python path.
    When a server is started a webbrowser is started and display a url which
    should point to a file in the web server root dir.
    The commands take 2 keywords argument which specify the path to Karrigell
    package, and the file to open in the webbrowser.
    If not specify, we search the python path to find karrigell package, and give
    the top level of the karigell folder as the file to open as a url.
    """

    def onExitFromViewer(self):
        """ method which will be call when the Viewer is closed"""

        # we need to stop the Karigell webserver
        if hasattr(self,'cmd'):
            if not mswin:
                import os,signal
                print 'killing process Karrigell'
                pid = self.cmd.com.pid
                os.kill(pid,signal.SIGKILL)
                #self.cmd.com.kill(signal.SIGKILL)
            else:
                pass

    def doit(self,**kw):
        import webbrowser

        karrigell_path = kw['karrigell_path']
        file = kw['file']
        if karrigell_path is None:
            server_root = self.findKarrigell()
            if server_root is None:
                self.warningMsg("Karrigell package not install, Webserver not started.")
            else:
                karrigell_path = server_root

        # Karrigell folder should be in python path, we expect version-2.0.3
        import os
        # we create a absolute path as windows need it to under path
        karrigell_start = os.path.realpath(os.path.join(karrigell_path,'Karrigell.py'))
        karrigell_init  = os.path.realpath(os.path.join(karrigell_path,'Karrigell.ini'))

        status = False
        port = 8080
        status,port = self.startKarrigell(port,karrigell_start,karrigell_init)
        if status:
            print 'Karrigell started, listenning on port %d'%port
        else:
            print 'Karrigell could not be started'
            return

        # web page have to be in the server_root directory which
        # is by default karrigell_path
        if file is None:
            file = ''

        url2open = 'http://localhost:%d/'%port+file
        webbrowser.open_new(url2open)


    def startKarrigell(self,port,karrigell_start,karrigell_init):
        """ start the webserver Karrigell on the port specify in input
        return False for failure , True for sucess
        """
        if hasattr(self,'cmd'):
            del(self.cmd)
        print "Trying to start Karrigell on port %d"%port
        self.cmd =  SysCmdInThread("python -u %s -P %d %s "%(karrigell_start,
                                                             port,karrigell_init),
                                   hasGui=False)
        self.cmd.start()
        status = self.checkKarrigellStatus()
        if not status:
            # print try to start on another port
            port = port + 1
            if port > 8180:
                self.warningMsg("Could not start Karrigell server, no port available")
                return False,0
            else:
                status,port =self.startKarrigell(port,karrigell_start,karrigell_init)
        return status,port

    def checkKarrigellStatus(self):
        # check the status of Karrigell
        # did the  webserver started, if so we get the port back
        #while not self.cmd.output.empty():
        while(1):
            if not self.cmd.output.empty():
                data = self.cmd.output.get(False)
                # server fail to start
                if 'Address already in use' in data:
                    return False
                # server start success 
                if 'running on port' in data:
                    return True 
        return False

    def findKarrigell(self):
        """ method which search the path to the Karrigel directory in the
        python path"""
        import sys,os
        karrigell_path =None
        for d in sys.path:
            dirname = os.path.join(d,'Karrigell-2.0.3')
            if os.path.exists(dirname):
                karrigell_path = dirname
        return karrigell_path


    def guiCallback(self):
        kw ={}
        server_root = self.findKarrigell()
        if server_root is None: return
        file = self.vf.askFileOpen(types=[('all', '*')],
                                   idir=server_root,
                                   title='Select a web page or folder')
        if file is not None:
            import string
            webpage = string.split(file,'Karrigell-2.0.3')[1]
            kw['karrigell_path']=server_root
            kw['file'] = webpage
            apply(self.doitWrapper,(),kw)

    def __call__(self,karrigell_path=None,file=None,**kw):
        """ None<-web_tutorial( karrigell_path=None,file=None,**kw)
        karrigell_path = path to server_root of Karrigell webserver
        file = file or folder to show as url, should be in the webserver_root
        """
        kw['karrigell_path'] = karrigell_path
        kw['file'] = file
        apply(self.doitWrapper,(),kw)


class StartWebControlServer(Command):
    """ This class implements methods to start a communication pipe to
receive commands from a web browser"""

    def checkDependencies(self, vf):
        import thread

    def doit(self):
        import thread
        com = self.vf.webControl
        if com.port:
            print 'WARNING: server already running on port', com.port
            return
        com.startServer()
        thread.start_new(com.acceptClients, (self.clients_cb,))

        # print port number to a file in file pmv_server.pid in the directory where the
        # python process was started, if the package Karigell does not exist, otherwise
        # save pmv_server.pid in Karrigell folder.
        import os,sys
        karrigell_path =None
        for d in sys.path:
            dirname = os.path.join(d,'Karrigell-2.0.3')
            if os.path.exists(dirname):
                karrigell_path = dirname
        if not karrigell_path:
            filename = 'pmv_server.pid'
        else:
            filename = os.path.join(karrigell_path,'pmv_server.pid')
        f = open(filename,'w')
        f.write('%d'%com.port)
        f.close()

        from Queue import Queue
        self.cmdQueue = Queue(-1) # infinite size

        # start checking for messages from the web controler
        self.vf.GUI.ROOT.after(10, self.checkForCommands)


    def checkForCommands(self, event=None):
        """periodically check for new commands
        cmd should be a string where the Viewerframework command is separate by ||
        from a tuple representing the args separated by || from a dictonnary
        which represent the keyword arguments of commands
        example:
        'colorByAtomType||'+ '(self.vf.getSelection(), ('lines',))|| {}'
        colorByAtmoType: cmd to run
        (self.vf.getSelection(), ('lines',)): arguments to pass to cmd
        {}: keyword argument to pass to cmd
        """
        if not self.cmdQueue.empty():
            cmd = self.cmdQueue.get(False) # do not block if queue empty
            if cmd:
                #print 'got', cmd
                w = cmd.split('||')
                if self.vf.commands.has_key(w[0]):
                    # cmd should be a string where the Viewerframework command is separate by |
                    # from a tuple representing the args separated by | from a dictonnary
                    # which represent the keyword arguments of commands
                    # example:
                    # "colorByAtomType|"+ "(self.vf.getSelection(), ('lines',))| {}"
                    # colorByAtmoType: cmd to run
                    # (self.vf.getSelection(), ('lines',)): arguments to pass to cmd
                    # {}: keyword argument to pass to cmd

                    args = eval(w[1])
                    kw = eval(w[2])
                    apply( self.vf.commands[w[0]], args,kw )

        self.vf.GUI.ROOT.after(10, self.checkForCommands)


    def clients_cb(self, client, data):
        """get called every time a web page sends a message
The message is sent using Karrigell's Python in Html
"""
        # put it in a thread safe queue
        self.cmdQueue.put(data)


class ConnectToServer(Command):
    """ This class implements method to connect to a server."""

    def checkDependencies(self, vf):
        import thread

    def doit(self):
        import thread

        idf = InputFormDescr("Viewerframework server connection!")
        idf.append({'widgetType':Tkinter.Entry,
                    'name': 'host','defaultValue':'localhost',
                    'wcfg':{'label':'Host name or IP'}, 
                    'gridcfg':{'sticky':Tkinter.E}
                   })
        idf.append({'widgetType':Tkinter.Entry,
                    'name': 'port','defaultValue':'50000',
                    'wcfg':{'label':"Server's Port"}, 
                    'gridcfg':{'sticky':Tkinter.E}
                    })
        self.idf = idf
        val = self.vf.getUserInput(idf)
        self.vf.socketComm.connectToServer(val['host'], int(val['port']),
                                           self.vf.server_cb)

        # create a threadsafe command queue
        from Queue import Queue
        self.vf.cmdQueue = Queue(-1) # infinite size
        self.vf.GUI.ROOT.after(10, self.vf.runServerCommands)

if imdFound:
    class ConnectToImdServer(Command):
        """ This class implements method to connect to a imd server."""

        def checkDependencies(self, vf):
            import thread

        def setup(self,hostname,port,molname,atmslist="",htype="steered"):
            self.host = hostname
            self.port = port
            self.molname = molname
            self.atmslist = atmslist
            self.htype = htype

        def doit(self,gui=True):
            import thread
            if self.vf.hasGui and gui:        
                idf = InputFormDescr("Viewerframework imd server connection!")
                idf.append({'widgetType':Tkinter.Entry,
                        'name': 'host','defaultValue':'localhost',
                        'wcfg':{'label':'Host name or IP'}, 
                        'gridcfg':{'sticky':Tkinter.E}
                       })
                idf.append({'widgetType':Tkinter.Entry,
                        'name': 'port','defaultValue':'2030',
                        'wcfg':{'label':"Server's Port"}, 
                        'gridcfg':{'sticky':Tkinter.E}
                        })

                idf.append({'widgetType':Tkinter.Entry,
                        'name': 'molname','defaultValue':'',
                        'wcfg':{'label':"molecule name"}, 
                        'gridcfg':{'sticky':Tkinter.E}
                        })
                idf.append({'widgetType':Tkinter.Entry,
                        'name': 'handler','defaultValue':'',
                        'wcfg':{'label':"handler atoms"}, 
                        'gridcfg':{'sticky':Tkinter.E}
                        })
                idf.append({'widgetType':Tkinter.Entry,
                        'name': 'htype','defaultValue':'',
                        'wcfg':{'label':"handler type"}, 
                        'gridcfg':{'sticky':Tkinter.E}
                        })

                self.idf = idf
                val = self.vf.getUserInput(idf)
                mol = self.vf.getMolFromName(val['molname'])
                host = val['host']
                port = val['port']
                atmslist = val['handler'] #exple 
                htype = val["htype"]
                if len(htype) ==0 : htype = "steered"
            else :
                mol = self.vf.getMolFromName(self.molname)
                host = self.host
                port = self.port
                atmslist = self.atmslist
                htype = self.htype
            if type(mol) is list :
                slot =[] 
                for m in mol :
                    m.allAtoms.addConformation(m.allAtoms.coords[:])
                    slot.append( len(m.allAtoms[0]._coords) - 1)
            else :
                mol.allAtoms.addConformation(mol.allAtoms.coords[:])
                slot = len(mol.allAtoms[0]._coords) - 1
            self.vf.browseCommands('imdCommands',package='ViewerFramework', topCommand=0)
            #if two molecule
            if type(mol) is list :
                N=0
                for m in mol :
                    N+=len(m.allAtoms.coords)
                self.vf.imd.mindy = True
                #setup the file ? pdb, parameters, psf
                self.vf.imd.pdbFile = "/local/MGL/MGLTools-1.5.6/MGLToolsPckgs/ARDemo/mindy/two_alanin.pdb"
                self.vf.imd.psfFile = "/local/MGL/MGLTools-1.5.6/MGLToolsPckgs/ARDemo/mindy/two_alanin.psf"
                self.vf.imd.paraFile = "/local/MGL/MGLTools-1.5.6/MGLToolsPckgs/ARDemo/mindy/alanin.params"
                self.vf.imd.fixedAtoms = []
                self.vf.imd.init(host, 0,0, int(port), 1 , 0,N )
            else :
                self.vf.imd.init(host, 0,0, int(port), 1 , 0,len(mol.allAtoms) )
            if not self.vf.imd.mindy :        
                self.vf.imd.imd_pause()
            else :
                self.vf.imd.mol = mol
                self.vf.imd.slot = slot
                #self.vf.imd.gui = True
                #set coord at time 0
                #get all coordinate, and the total count
                #i will first translate mol2
    #            m2 = self.vf.imd.mol[0]
    #            vt = []
    #            M=[0.,0,0]
    #            #vt=util.ApplyMatrix(Numeric.array(self.mol2.allAtoms.coords),M)
    #            for pt in m2.allAtoms.coords:
    #                ptx = pt[0]+M[0]
    #                pty = pt[1]+M[1]
    #                ptz = pt[2]+M[2]
    #                vt.append( (ptx, pty, ptz) )
    #                
    #            m2.allAtoms.updateCoords(vt,ind=0)
                coords=[]
                N=0
                for m in self.vf.imd.mol:
                    if hasattr(self.vf,'art'):
                        self.vf.art.doimd = True
                        from ARViewer import util
                        import numpy.oldnumeric as Numeric
                        M = m.pat.mat_transfo
                        vt=util.ApplyMatrix(Numeric.array(m.allAtoms.coords),M,transpose=False)
                    else :
                        vt=m.allAtoms.coords[:]
                    N+=len(m.allAtoms.coords)
                    coords.extend(vt)
                self.vf.imd.N = N
                print "sendFcoords"
                self.vf.imd.imd_send_fcoords(self.vf.imd.N,coords)
            self.vf.browseCommands('handlerCommand',package='ViewerFramework', topCommand=0)
            self.vf.handler.isinited = False
            if len(atmslist) :
               atms = self.vf.select(atmslist)
               self.vf.handler.create(atms,forceType=htype)
            if self.vf.hasGui and self.vf.imd.gui :
                if not self.vf.imd.mindy : 
                    self.vf.imd.start()
                print "after"
                self.vf.GUI.ROOT.after(1, self.vf.updateIMD)

# add StartServer Command
StartServerGUI = CommandGUI()
StartServerGUI.addMenuCommand('menuRoot', 'File', 'start server',
                              cascadeName='server',
                              cascadeBefore='Exit')

# add StartWebControlServer Command
StartWebControlServerGUI = CommandGUI()
StartWebControlServerGUI.addMenuCommand(
    'menuRoot', 'File', 'start web controller', cascadeName='server')

# add ConnectToServer Command
ConnectToServerGUI = CommandGUI()
ConnectToServerGUI.addMenuCommand(
    'menuRoot', 'File', 'connect to server', cascadeName='server')

# add ConnectToImdServer Command
if imdFound:
    ConnectToImdServerGUI = CommandGUI()
    ConnectToImdServerGUI.addMenuCommand(
        'menuRoot', 'File', 'connect to imd server', cascadeName='server')


# add WebDrivenTutorial Command
WebDrivenTutorialGUI = CommandGUI()
WebDrivenTutorialGUI.addMenuCommand(
    'menuRoot', 'File', 'web tutorial')

commandList = [
    {'name':'startServer', 'cmd':StartServer(),
     'gui': StartServerGUI},
    {'name':'connectToServer', 'cmd':ConnectToServer(),
     'gui': ConnectToServerGUI},
    {'name':'StartWebControlServer', 'cmd':StartWebControlServer(),
     'gui': StartWebControlServerGUI},
    {'name':'web tutorial', 'cmd':WebDrivenTutorial(),
     'gui': WebDrivenTutorialGUI},
    ]

if imdFound:
    commandList.append(
        {'name':'connectToImdServer', 'cmd':ConnectToImdServer(),
         'gui': ConnectToImdServerGUI})

def initModule(viewer):
    for dict in commandList:
#        print 'dict',dict
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
