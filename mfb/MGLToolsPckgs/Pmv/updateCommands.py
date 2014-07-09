# This modules handels updates for MGLTools
# Author: Sargis Dallakyan (sargis at scripps.edu)
# $Header: /opt/cvs/python/packages/share1.5/Pmv/updateCommands.py,v 1.6 2007/06/21 19:38:37 sargis Exp $
# $Id: updateCommands.py,v 1.6 2007/06/21 19:38:37 sargis Exp $

from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
import sys, subprocess, os
from tkMessageBox import *

class Update(MVCommand):
    
    def guiCallback(self):
   
        try:
            from Support.update import Update
        except ImportError:
            print "Support package is needed to get updates"
            return
        
        update = Update()
        waitTk = update.gui()
        self.vf.GUI.ROOT.wait_variable(waitTk)
        if update.updates_dir != 'cancel':
            txt = "You need to restart " + self.vf.help_about.title + \
                  " for the changes to take effect. Would you like to restart "\
                  + self.vf.help_about.title + " now?"
            
            if askokcancel("Restart is needed", txt):                
                executable = sys.executable
                if os.name == 'nt':
                    executable = executable.replace("\\","""\\\\""")                  

                cmd = executable
                cmd += ' -c "import time,os;time.sleep(1);os.system(\''
                script = self.vf.help_about.path_data.split('script                : ')[1].split('\n')[0]
                if os.name == 'nt':
                    script = script.replace("\\","""\\\\""")                  
                script = r'\"'+script+r'\"'
                cmd += executable + " " + script + "')\""
                if os.name == 'nt':
                    #cmd = cmd.replace("\\","""\\\\""")                  
                    cmd = 'start ' + cmd.encode()
                else:
                    cmd += ' &'
                subprocess.Popen(cmd, shell=True)
                os._exit(0)
            
UpdateGUI = CommandGUI()
UpdateGUI.addMenuCommand('menuRoot', 'Help', 'Update',separatorAbove = 1)

commandList  = [{'name':'update','cmd':Update(),'gui':UpdateGUI}]
def initModule(viewer):
    for _dict in commandList:
        viewer.addCommand(_dict['cmd'],_dict['name'],_dict['gui'])
