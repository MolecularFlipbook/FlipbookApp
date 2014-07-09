########################################################################
#
# Date: January 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#########################################################################
#
# $Header$
#
# $Id$
#

import os
import shutil
import sys
import warnings
import stat
from inspect import isclass


def addDirToSysPath(dirToAdd):
    fullpath = os.path.abspath(dirToAdd)
    found = False
    for p in sys.path:
        if fullpath == p:
            # do nothing if this one is already in sys.path
            return
    # else, append parent to sys.path
    sys.path.append(fullpath)


def userLibBuild(libInstance, callingFile, dependents={}):

    for dep, depversion in dependents.items():
        try:
            __import__(dep) # make sure all dependent packages are loadable
        except Exception, e:
            warnings.warn("""
In order to use the vision library %s,
you need to install: %s %s\n""" %(libInstance.name,dep, depversion))
            return False

    thisPath = os.path.split(callingFile)[0]
    libdir = os.path.split(thisPath)[-1]
    for dirItem in os.listdir(thisPath):
        subdir = os.path.join(thisPath, dirItem)
        if ( not os.path.isdir(subdir) ) or \
           ( len( dirItem.split(' ') ) > 1 ) or \
           ( len( dirItem.split('_') ) > 1 ):
                continue
        for subdirItem in os.listdir(subdir):
            if subdirItem.endswith('.py') and (subdirItem != '__init__.py'):
                filenameWithoutExt = os.path.splitext(subdirItem)[0]
                moduleName = libdir + '.' + dirItem + '.' + filenameWithoutExt
                if '__init__.py' not in os.listdir(subdir):
                    lCategory1Init = thisPath + os.sep + dirItem + os.sep + '__init__.py'
                    f = open(lCategory1Init, "w")
                    f.close()
                try:
                    mod = __import__(moduleName, globals(), locals(),[filenameWithoutExt])
                    try:            
                        reload(mod)
                    except RuntimeError, e:
                        #print "userLibBuild: unable to reload library %s\n" % moduleName, e
                        pass # this is just to hide a potential problem in reloading (matplotlib has this issue) 
                    for modItemName in dir(mod):
                        modItem = getattr(mod, modItemName)
                        from NetworkEditor.items import NetworkNode
                        if isclass(modItem) and issubclass(modItem, NetworkNode):
                            if modItem.__module__ == moduleName:
                                if hasattr(modItem, 'mRequiredTypes'):
                                    for lTypeName, lModuleName in modItem.mRequiredTypes.items():
                                        mad = __import__(lModuleName, globals(), locals(), [lTypeName])
                                        madItem = getattr(mad, lTypeName)
                                        libInstance.typesTable.append(madItem())
                                if hasattr(modItem, 'mRequiredSynonyms'):
                                    for lSynonym in modItem.mRequiredSynonyms:
                                        libInstance.synonymsTable.append(lSynonym)
                                libInstance.addNode(modItem, modItemName, dirItem)
                except Exception, e:
            		print "userLibBuild: unable to load library %s\n" % moduleName, e
                        return False

    return True


def ensureDefaultUserLibFile():
    ##################################################################
    # verify or generate the default user lib file
    ##################################################################
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    userResourceFolder = getResourceFolderWithVersion()
    if userResourceFolder is None:
        return
    userVisionDir = userResourceFolder + os.sep + 'Vision' + os.sep
    userLibsDir = userVisionDir + 'UserLibs' + os.sep
    defaultLibDir = userLibsDir + 'MyDefaultLib' + os.sep
    defaultLibInit = defaultLibDir + '__init__.py'
    libTypesFile = defaultLibDir + 'libTypes.py'
    if os.path.isfile(defaultLibInit) is False:
        try:
            if os.path.isdir(userResourceFolder) is False:
                os.mkdir(userResourceFolder)
            if os.path.isdir(userVisionDir) is False:
                os.mkdir(userVisionDir)
            if os.path.isdir(userLibsDir) is False:
                os.mkdir(userLibsDir)
            #userLibsInit = userLibsDir + '__init__.py'
            #if os.path.isfile(userLibsInit) is False:
            #    f = open(userLibsInit, "w")
            #    f.close()
            if os.path.isdir(defaultLibDir) is False:
                os.mkdir(defaultLibDir)
            category1Dir = defaultLibDir + 'Input' + os.sep
            if os.path.isdir(category1Dir) is False:
                os.mkdir(category1Dir)
            category1Init = category1Dir + '__init__.py'
            if os.path.isfile(category1Init) is False:
                f = open(category1Init, "w")
                f.close()
            category2Dir = defaultLibDir + 'Output' + os.sep
            if os.path.isdir(category2Dir) is False:
                os.mkdir(category2Dir)
            category2Init = category2Dir + '__init__.py'
            if os.path.isfile(category2Init) is False:
                f = open(category2Init, "w")
                f.close()
            category3Dir = defaultLibDir + 'Macro' + os.sep
            if os.path.isdir(category3Dir) is False:
                os.mkdir(category3Dir)
            category3Init = category3Dir + '__init__.py'
            if os.path.isfile(category3Init) is False:
                f = open(category3Init, "w")
                f.close()
            category4Dir = defaultLibDir + 'Other' + os.sep
            if os.path.isdir(category4Dir) is False:
                os.mkdir(category4Dir)
            category4Init = category4Dir + '__init__.py'
            if os.path.isfile(category4Init) is False:
                f = open(category4Init, "w")
                f.close()
            f = open(defaultLibInit, "w")
            txt = """########################################################################
#
# Date: Jan 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    Vision Library Loader
#
#########################################################################
#
# %s
# Vision will generate this file automatically if it can't find it
#

from os import sep, path
from Vision.VPE import NodeLibrary
from Vision.UserLibBuild import userLibBuild, addDirToSysPath, addTypes

dependents = {} # {'scipy':'0.6.0',} the numbers indicate the highest tested version of the needed packages
libraryColor = '#FF7700'

addDirToSysPath(path.dirname(__file__)+sep+'..')
fileSplit = __file__.split(sep)
if fileSplit[-1] == '__init__.pyc' or fileSplit[-1] == '__init__.py':
    libInstanceName = fileSplit[-2]
else:
    libInstanceName = path.splitext(fileSplit[-1])[0]
try:
    from Vision import ed
except:
    ed = None
if ed is not None and ed.libraries.has_key(libInstanceName):
    locals()[libInstanceName] = ed.libraries[libInstanceName]
else:
    locals()[libInstanceName] = NodeLibrary(libInstanceName, libraryColor, mode='readWrite')
success = userLibBuild(eval(libInstanceName), __file__, dependents=dependents)
if success is False:
    locals().pop(libInstanceName)
elif path.isfile(path.dirname(__file__)+sep+'libTypes.py'):
    addTypes(locals()[libInstanceName], libInstanceName + '.libTypes')

""" % defaultLibInit
            map( lambda x, f=f: f.write(x), txt )
            f.close()
            os.chmod(defaultLibInit, 0444) #make it read only

            f = open(libTypesFile, "w")
            txt = """########################################################################
#
# Date: Jan 2006 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    Vision Library Types
#
#########################################################################
#
# %s
# Vision will generate this file automatically if it can't find it
#

from NetworkEditor.datatypes import AnyArrayType

############################################################
# add new types to your library that the node ports can use. 
############################################################

#class ThingType(AnyArrayType):
#
#    from ThingPackage import Thing
#    def __init__(self, name='thing', color='#995699', shape='rect',
#                 klass=Thing):
#
#        AnyArrayType.__init__(self, name=name, color=color, shape=shape, 
#                              klass=klass)
#
## in NetworkEditor.datatypes, you should have a look at the class IntType

""" % libTypesFile
            map( lambda x, f=f: f.write(x), txt )
            f.close()

        except:
            txt = "Cannot write the init files %s and %s" %(defaultLibInit,libTypesFile)
            warnings.warn(txt)


def ensureVisionResourceFile():
    ##################################################################
    # verify or generate _visionrc file
    ##################################################################
    from Vision.nodeLibraries import libraries
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    
    visionrcDir = getResourceFolderWithVersion()
    if visionrcDir is None:
        return
    visionrcDir += os.sep + 'Vision'
    if os.path.isdir(visionrcDir) is False:
        try:
            os.mkdir(visionrcDir)
        except:
            txt = "can not create folder for _visionrc"
            warnings.warn(txt)
            return

    visionrcFile = visionrcDir + os.sep + '_visionrc'
    if os.path.isfile(visionrcFile) is False:
        try:
            from Vision import __path__ as lVisionPath
            shutil.copyfile(lVisionPath[0]+os.sep+'_visionrc', visionrcFile)
        except:
            txt = "can not create _visionrc"
            warnings.warn(txt)


def addTypes(libOrTypeManagerInstance, typesModuleName):
    mod = __import__(typesModuleName, globals(), locals(),[typesModuleName])
    for modItemName in dir(mod):
        modItem = getattr(mod, modItemName)
        from inspect import isclass
        if isclass(modItem):
            from NetworkEditor.datatypes import AnyArrayType, AnyType
            if issubclass(modItem, AnyType) or issubclass(modItem, AnyArrayType):
                libOrTypeManagerInstance.addType(modItem())


def saveFonts4visionFile(fontDict):
    ##################################################################
    # generate and overwrite _fonts4Vision file
    ##################################################################
    from Vision.nodeLibraries import libraries
    from mglutil.util.packageFilePath import getResourceFolderWithVersion
    
    visionrcDir = getResourceFolderWithVersion()
    if visionrcDir is None:
        return

    visionrcDir += os.sep + 'Vision'
    if os.path.isdir(visionrcDir) is False:
        return

    fonts4visionFile = visionrcDir + os.sep + '_fonts4vision'
    try:
        f = open(fonts4visionFile, "w")
        txt = """########################################################################
#
# Date: Feb 2008 Authors: Guillaume Vareille, Michel Sanner
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Guillaume Vareille, Michel Sanner and TSRI
#
#    _fonts4vision Resource File
#
########################################################################
# This file is optionnal and can be deleted,
# it is generated each time the fonts
# are modified via the Vision GUI
########################################################################

from mglutil.util.misc import ensureFontCase

self.setFont('Menus', (ensureFontCase('%s'),%s,'%s'))
self.setFont('LibTabs', (ensureFontCase('%s'),%s,'%s'))
self.setFont('Categories', (ensureFontCase('%s'),%s,'%s'))
self.setFont('LibNodes', (ensureFontCase('%s'),%s,'%s'))
self.setFont('NetTabs', (ensureFontCase('%s'),%s,'%s'))
self.setFont('Nodes', (ensureFontCase('%s'),%s,'%s'))
self.setFont('Root', (ensureFontCase('%s'),%s,'%s'))
"""%(
fontDict['Menus'][0],fontDict['Menus'][1],fontDict['Menus'][2],
fontDict['LibTabs'][0],fontDict['LibTabs'][1],fontDict['LibTabs'][2],
fontDict['Categories'][0],fontDict['Categories'][1],fontDict['Categories'][2],
fontDict['LibNodes'][0],fontDict['LibNodes'][1],fontDict['LibNodes'][2],
fontDict['NetTabs'][0],fontDict['NetTabs'][1],fontDict['NetTabs'][2],
fontDict['Nodes'][0],fontDict['Nodes'][1],fontDict['Nodes'][2],
fontDict['Root'][0],fontDict['Root'][1],fontDict['Root'][2],
)

        map( lambda x, f=f: f.write(x), txt )
        f.close()
    except:
        txt = "can not create _fonts4vision"
        warnings.warn(txt)


