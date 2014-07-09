#################################################################
# CADD - A computer aided drug design using Vision
#
##################################################################
# $Header: /opt/cvs/CADD/__init__.py,v 1.4 2011/05/03 17:58:07 nadya Exp $
# $Id: __init__.py,v 1.4 2011/05/03 17:58:07 nadya Exp $

import time
import sys
import getopt
import os
import user
import warnings
import stat
from string import split

from mglutil.util.packageFilePath import setResourceFolder, getResourceFolder 

__version__ = '0.1';
__revision__ = '1';

# add new type and associated directory in workflows/
WFTypes = {
    ' MD analysis'       : 'MDanalysis',
    ' Virtual Screening' : 'virtualScreening',
    ' Visualization'     : 'visualization',
    ' Docking'           : 'docking',
    'User Workflows'     : 'user'
}

def createRoot():
    """ create a root and hide it
"""
    from Tkinter import Tk
    root = Tk()
    root.withdraw()
    return root


def createCADD(root=None, interactive=True):
    """
"""
    from CADD.VPECADD import VisualProgramingEnvironmentCADD
    ed = VisualProgramingEnvironmentCADD(master=root, name='CADD',
                                     withShell= not interactive)
    return ed


def createSplash():
    """
"""
    iconsDir = os.path.join( __path__[0], 'Icons')
    image_dir = os.path.join( iconsDir, 'Images')

    # insert release date here
    version = ' ' + __version__

    copyright = """(c) 1999-2008 Molecular Simulation Laboratory, The Scripps Research Institute
    ALL RIGHTS RESERVED """
    authors = """Authors: Michel F. Sanner, Daniel Stoffler, Guillaume Vareille"""
    icon = os.path.join( iconsDir, 'cadd.png')
    third_party = """"""

    text = 'Python executable   : '+sys.executable+'\n'
    text += 'CADD script               : '+__file__+'\n'
    text += 'MGLTool packages  : '+'\n'
    
    from user import home
    updates_rc_dir = home + os.path.sep + ".mgltools" + os.sep + 'update'
    latest_tested_rc = updates_rc_dir + os.sep + 'latest_tested'
    latest_rc = updates_rc_dir + os.sep + 'latest' #may or may not be tested
    
    if os.path.exists(latest_tested_rc):
        p = open(latest_tested_rc).read()
        sys.path.insert(0, p)
        text += '    tested  : ' + p +'\n'
    
    if os.path.exists(latest_rc):
        p = open(latest_rc).read()
        sys.path.insert(0, p)
        text += '    nightly : ' + p +'\n'
    
    text += version + ': ' + 'ADD PATH HERE'
    path_data = text

    from mglutil.splashregister.splashscreen import SplashScreen
    from mglutil.splashregister.about import About
    about = About(image_dir=image_dir, third_party=third_party,
                  path_data=path_data,
                  title='CADD', version=version, revision=__revision__, 
                  copyright=copyright, authors=authors, icon=icon)
    splash =  SplashScreen(about, noSplash=False)

    return splash, about


def launchVisionToRunNetworkAsApplication(splash=True):
    root = createRoot()
    if splash:
        splash, about = createSplash()
        lSplashVisibleTimeStart = time.clock()  
    ed = createCADD(root, interactive=True)
    ed.sourceFile(resourceFile='_caddrc')
    masterNet = ed.currentNetwork
    masterNet.isApplication = True
    if splash:
        lSplashVisibleTimeEnd = time.clock()
        while lSplashVisibleTimeEnd - lSplashVisibleTimeStart < 2:
            lSplashVisibleTimeEnd = time.clock()
        splash.finish()
    return masterNet


def mainLoopVisionToRunNetworkAsApplication(ed):
    #ed.master.mainloop()
    sys.stdin = sys.__stdin__
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    import code
    mod = __import__('__main__')
    try: # hack to really exit code.interact 
        code.interact( 'CADD Interactive Shell', local=mod.__dict__)
    except:
        pass


##################################################################
# Define a bunch of useful methods
##################################################################
def net():
    return ed.currentNetwork


def nodes():
    return ed.currentNetwork.nodes


def run():
    return ed.currentNetwork.run()


def runCADD(*argv, **kw):
    """The main function for running CADD
listOfDemandedOuts = runCADD('--noSplash',
                               '--runAndExit',
                               'Network0_net.py',
                               ins=[('myeval', 'command', 4),],
                               outs=[('myeval', 'result'),]
                               )
ins: list of tuples, each tuple being (node name, input port name, value)
     the input ports must have a widget.
outs: list of tuples, each tuple being (node name, output port name)
listOfDemandedOuts: list of values in the output ports listed in outs
"""

    ##################################################################
    # Parse options
    ##################################################################

    if type(argv) is tuple:
        if len(argv) == 0:
            argv = None
        elif len(argv) == 1:
            argv = argv[0]
            if type(argv) is not list:
                argv = [argv]
        else:
            argv = list(argv)
    if kw.has_key("ownInterpreter"):
        ownInterpreter = kw["ownInterpreter"]
    else:
        if argv is None:
            argv = ['CADD/bin/runCADD.py']
            ownInterpreter = False
        elif argv[0].endswith('runCADD.py') is False:
            argv.insert(0,'CADD/bin/runCADD.py')
            ownInterpreter = False
        else:
            ownInterpreter = True

    help_msg = """usage: %s <options> <filenames>

    Files filenames ending in "net.py" will be laoded as networks in vision.
    Other files will be executed as Python scripts in which "ed" refers
    to the VisualProgrammingEnvironment instance.
    
            -h or --help : print this message
            -s or --noSplash : doesn't show the CADD splash screen (works only if registered)
            -t or --noTerminal : vision provides its own shell (under menu 'Edit') 
                           instead of the terminal
            --resourceFolder foldername  : stores resource file under .name (defaults to .mgltools)    
            -p or --ipython : create an ipython shell instead of a python shell        
            -r or --run  : run the networks on the command line
            -e or --runAndExit : run the networks and exit

            port values can be passed on the command line (but not to macros):
                             Network_net.py nodeName:portName:value

""" % sys.argv[0]

    try:
        optlist, args = getopt.getopt(argv[1:], 'hirestp', [
            'help', 'interactive', 'noTerminal', 'noSplash', 'resourceFolder=', 'run', 'runAndExit','ipython'] )
    except:
        print "Unknown option!"
        print help_msg
        return

    interactive = 1
    noSplash = False
    runNetwork = False
    once = False
    ipython = False
    for opt in optlist:
        if opt[0] in ('-h', '--help'):
            print help_msg
            return
        elif opt[0] in ('-i', '--interactive'):
            warnings.warn('-i (interactive) is default mode, use --noTerminal to disable it',
                          stacklevel=3)
        elif opt[0] in ('-t', '--noTerminal'):
            interactive = 0
        elif opt[0] in ('-s', '--noSplash',):
            noSplash = True
        elif opt[0] in ('--resourceFolder',):
            setResourceFolder(opt[1])
        elif opt[0] in ('-r', '--run'):
            runNetwork = True
        elif opt[0] in ('-e', '--runAndExit'):
            runNetwork = True
            once = True
        elif opt[0] in ('-p', '--ipython'):
            ipython = True

    from Support.path import path_text, release_path
    print 'Run CADD from ', __path__[0]
    
    if globals().has_key('ed') is False:
        root = createRoot()
        #root.withdraw()
        ##################################################################
        # Splash Screen
        ##################################################################
        if noSplash is False:
            splash, about = createSplash()
            lSplashVisibleTimeStart = time.clock()

        ##################################################################
        # Start CADD
        ##################################################################
        ed = createCADD(root, interactive)
        globals()['ed'] = ed

        ##################################################################
        # Workaround: currently, Vision would crash on some Windows2000 and SGI
        # when running multi-threaded. We turn MT off for those platforms
        ##################################################################
        if os.name == 'nt' or sys.platform == 'irix646':
            ed.configure(withThreads=0)

        ##################################################################
        # Source Resource File (if available)
        ##################################################################
        if getResourceFolder() is None:
            ed.loadLibModule('Vision.StandardNodes')
        else:
            ed.sourceFile(resourceFile='_caddrc')
            # complete vpe menu with additionnal fastLibs
            if hasattr(ed, 'updateFastLibs'):
                ed.updateFastLibs()

        ##################################################################
        # Make sure splash is visible long enough before removing it
        ##################################################################
        if noSplash is False:
            lSplashVisibleTimeEnd = time.clock()
            while lSplashVisibleTimeEnd - lSplashVisibleTimeStart < 2:
                lSplashVisibleTimeEnd = time.clock()
            splash.finish()

        ##################################################################
        # Make vision visible 
        #(before the network loads, so the additional windows will load on top)
        ##################################################################
        if once is False:
            root.deiconify()

    else:
        ed = globals()['ed']
        root = ed.master
        root.master.master.deiconify()

    ##################################################################
    # Load network(s) if specified at startup
    ##################################################################
    lResults = []
    if len(args):
        ed.root.update() # make sure the canvas is shown b4 loading any network
        lArgIndex = 0
        while lArgIndex < len(args):
            if args[lArgIndex][-6:]=='net.py':
                ed.loadNetwork(args[lArgIndex], ins=kw.get('ins'))
                lNodePortValues = []
                lArgIndex += 1
                while lArgIndex < len(args) and args[lArgIndex][-3:]!='.py':
                    lNodePortValues.append(args[lArgIndex])
                    lArgIndex += 1
                ed.currentNetwork.setNodePortValues(lNodePortValues)
                if runNetwork:
                    ed.softrunCurrentNet_cb()
            elif args[lArgIndex][-3:]=='.py':
                execfile(netName)
                lArgIndex += 1
            else:
                lArgIndex += 1

        # lets obtain the asked outs values   
        outs=kw.get('outs')
        if outs is not None:
            for lOut in outs:
                lOutFound = False
                for lNodes in ed.currentNetwork.nodes:
                    if lNodes.name == lOut[0]:
                        if lOutFound is True:
                            warnings.warn("found several nodes %s"%lOut[0] )
                        lOuputPort = lNodes.outputPortByName.get(lOut[1])
                        if lOuputPort is None:
                            warnings.warn("node %s doesn't have port %s"%(lOut[0],lOut[1]) )
                        else:
                           lResults.append(lOuputPort.data)
                        lOutFound = True
                if lOutFound is False:
                    warnings.warn("can't find node %s"%lOut[0] )

    if once is True:
        ed.root.quit()
        ed.root.destroy()
        globals().pop('ed')
        return lResults
    ##################################################################
    # Set the Python Shell
    ##################################################################
    elif ownInterpreter is True:
        if interactive:
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            mod = __import__('__main__')
            if ipython is True:
                try:
                    # create IPython shell
                    from IPython.Shell import _select_shell
                    sh = _select_shell([])(argv=[], user_ns=mod.__dict__)
                    sh.mainloop()
                except:
                    import code
                    try: # hack to really exit code.interact 
                        code.interact( 'CADD Interactive Shell', local=mod.__dict__)
                    except:
                        pass
            else:
                import code
                try: # hack to really exit code.interact 
                    code.interact( 'CADD Interactive Shell', local=mod.__dict__)
                except:
                    pass

        else:
            ed.master.mainloop()
    else:
        return lResults

packageContainsVFCommands = 1
CRITICAL_DEPENDENCIES = ['NetworkEditor', 'mglutil', 'Support', 'Pmw', 'numpy']
NONCRITICAL_DEPENDENCIES = ['magick', 'PIL', 'opengltk', 'DejaVu', 'grail', 'MolKit', 'symserv','Volume', 'Pmv', 'matplotlib', 'pytz', 'AutoDockTools', 'IPython', 'pymedia']
