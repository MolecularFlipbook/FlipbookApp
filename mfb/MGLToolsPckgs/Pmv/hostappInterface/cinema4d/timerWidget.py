# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 17:43:53 2010
from Pmv.hostappInterface.cinema4d import timerWidget
widg=timerWidget.QuestionTimer()
widg.Open(async=True, pluginid=25555589, width=120, height=200)
@author: -
"""
import c4d
from c4d import plugins
#from c4d import tools
from c4d import bitmaps
import os,sys
from c4d import gui

import time

class QuestionTimer(gui.SubDialog):
    #.epmv
    _time = 0.
    _cancel = False
    def initWidgetId(self):
        #minimize options
        #max_iterations=1000
        #md options
        #temperature=300, max_iterations=1000
        id=1005
        self.OPTIONS = {'yes':{"id": id, "name":"Yes",'width':150,"height":10,"action":self.Cancel},
                       'no':{"id": id+1, "name":"No",'width':150,"height":10,"action":self.Continue},
                       }
        id = id + len(self.OPTIONS)
        self.LABEL_ID = [{"id":id,"label":"Wanna Cancel?"},
                         {"id":id,"label":""},]
        
        return True

    def CreateLayout(self):
        #done on Open
        
        ID=0
        self.SetTitle("Cancel?")
        self.initWidgetId()
        #minimize otin/button
        self.GroupBegin(id=ID,flags=gui.BFH_SCALEFIT | gui.BFV_MASK,
                           cols=2, rows=10)
        self.GroupBorderSpace(10, 10, 5, 10)
        ID = ID +1
        self.AddStaticText(self.LABEL_ID[0]["id"],flags=gui.BFH_CENTER | gui.BFV_MASK)
        self.SetString(self.LABEL_ID[0]["id"],self.LABEL_ID[0]["label"])        
        self.AddStaticText(self.LABEL_ID[1]["id"],flags=gui.BFH_CENTER | gui.BFV_MASK)
        self.SetString(self.LABEL_ID[1]["id"],self.LABEL_ID[1]["label"])        

        for k in self.OPTIONS.keys():       
            self.AddButton(id=self.OPTIONS[k]["id"], flags=gui.BFH_CENTER | gui.BFV_MASK,
                            initw=self.OPTIONS[k]["width"],
                            inith=self.OPTIONS[k]["height"],
                            name=self.OPTIONS[k]["name"])
        return True

    def Cancel(self):
        self._cancel = True
        self.Close()
        
    def Continue(self):
        self._cancel = False
        self.Close()
                
#######EVENT COMMAND######################################################
    def Command(self, id, msg):
        c4d.gui.SetMousePointer(c4d.MOUSE_BUSY)
        for butn in self.OPTIONS.keys():
            if id == self.OPTIONS[butn]["id"]:
                self.OPTIONS[butn]["action"]()
        c4d.gui.SetMousePointer(c4d.MOUSE_NORMAL)
        return True