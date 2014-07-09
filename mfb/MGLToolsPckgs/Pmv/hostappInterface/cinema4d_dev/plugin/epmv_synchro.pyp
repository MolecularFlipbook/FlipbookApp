import c4d
from c4d import plugins
#from c4d import tools
from c4d import bitmaps
import os,sys

import Pmv.hostappInterface.cinema4d_dev as epmv
import os
#from Tkinter import *

# be sure to use a unique ID obtained from www.plugincafe.com
PLUGIN_ID = 1023745

class epmv_update(plugins.TagData):

    #optimize_method_control = True

    def __init__(self):
        #self.optimize_method_control = True
        print "__init__"
        
    def Init(self, node):
        """get Pmv"""
        print "init"        
        #doc = c4d.documents.get_active_document()
        return True

    def say_hi(self):
        print "hi there, everyone!"

    def Execute(self, tag, doc, op, bt, priority, flags):
        dname=doc.GetDocumentName()
        if hasattr(c4d,'mv'):
            if c4d.mv.has_key(dname) :
                self.epmv = c4d.mv[dname]
                self.mv = self.epmv.mv
            else : 
                self.epmv = None
                self.mv = None
            #print "rexectute", self.mv
        else : 
            self.epmv = None
            self.mv = None    
        sel = doc.GetSelection()
        if hasattr(self.mv,'art'):
            vp = doc.GetActiveBaseDraw() 
            self.epmv.helper.updateImage(self.mv,viewport = vp)
        if self.epmv.synchro_timeline :
            traj = self.epmv.gui.current_traj
            t=c4d.BaseTime()
            fps = doc.GetFps()
            #getCurrent time
            frame=doc.GetTime().GetFrame(fps)
            st,ft=self.epmv.synchro_ratio
            if (frame % ft) == 0:   
                step = frame * st
                self.epmv.helper.updateData(self.epmv,traj,step)
#                self.epmv.gui.updateViewer()
        else :
            self.epmv.helper.updateCoordFromObj(self.mv,sel,debug=True)
        #this update should recognise the displayed object and update consequently
        #like update bond geometry,loft ss, constraint the move ? calcul_energy?                
        return c4d.EXECUTIONRESULT_OK

if __name__ == "__main__":
    dir, file = os.path.split(__file__)
    icon = bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(dir,"res","pmv.tif"))
#    plugins.RegisterTagPlugin(id=PLUGIN_ID, name="epmvUpdate", obj=epmv_update,
#                         description="epmv_update", icon=icon,res=dir,
#                         info=c4d.plugins.TAG_MULTIPLE|c4d.plugins.TAG_EXPRESSION|c4d.plugins.TAG_VISIBLE)
    plugins.RegisterTagPlugin(id=PLUGIN_ID, str="epmvUpdate",
                              info=c4d.TAG_MULTIPLE|c4d.TAG_EXPRESSION|c4d.TAG_VISIBLE,
                              g=epmv_update, description="epmv_update", icon=icon)