# import gamengine modules
from bge import logic
from bge import events
from bge import render

# import native python modules
import sys
import os
import urllib.parse
from urllib.request import FancyURLopener
from urllib.request import urlopen
import threading

#******************************************
# Goal:   Fetch PDB file locally or remotely
# Input:  PDB file, pdb full path, URL
# Output: PDB file written to pdbcache folder
# Return: None
#**********************************************
class Fetch(threading.Thread):
    def __init__(self, pdbid, pdbFullPath, remoteaddr):
        self.pdbid = pdbid
        self.url = remoteaddr
        self.pdbFullPath = pdbFullPath
        threading.Thread.__init__(self)

    def run(self):
        opener = FancyURLopener()
        try:
            remotefile = opener.open(self.url)
        except IOError:
            logic.logger.new("Unable to connect to internet", 'ERROR')
            return
        if remotefile.getcode() == 404:
            logic.logger.new("PDB file not found on pdb.org", 'ERROR')
            return
        elif remotefile.getcode() >= 500:
            logic.logger.new("PDB.org is currently unavailable", 'ERROR')
            return
        localfile = open(self.pdbFullPath, 'wb')
        localfile.write(remotefile.read())
        localfile.close()
        remotefile.close()
