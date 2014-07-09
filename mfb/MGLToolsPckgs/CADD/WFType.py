########################################################################
########################################################################
# $Header: /opt/cvs/CADD/WFType.py,v 1.3 2011/02/11 22:02:29 nadya Exp $
# $Id: WFType.py,v 1.3 2011/02/11 22:02:29 nadya Exp $

import os
from CADD import __path__, WFTypes 

class NodeWFType:
    """ class used to describe a workflows type"""
    
    def __init__(self, name, dir ):

        self.name = None        # worfklow Type name
        self.dir = None         # directory of individual workflows
        self.wflist = {}        # available workflows list. Key - short name, value - file full path
        self.items = []

        if name not in WFTypes.keys():
            return None

        self.name = name
        self.dir =  dir + os.sep + WFTypes[name]
        if not os.path.isdir(self.dir):
            self.about = "Missing  %s/ directory.\nYour installation may be incomplete" % self.dir
            return None

        for item in os.listdir(self.dir):
            if item.endswith('.py') and (item != '__about__.py'):
                filenameNoExt = os.path.splitext(item)[0]
                filenameNoExt = filenameNoExt.split('_')[0]   # remove version and _net from the name
                self.wflist[filenameNoExt] = self.dir + os.sep + item
        self.items = self.wflist.items()
        try:
            f = file (self.dir + os.sep + '__about__.py', 'r')
            exec f.read()
            f.close()
            self.about = about
        except:
            self.about = "Missing %s/__about__.py file.\nYour installation may be incomplete" % self.dir


    def showWFlist(self):
        if self.items :
            self.items.sort()
        return self.items

    def showType(self):
        return self.about

