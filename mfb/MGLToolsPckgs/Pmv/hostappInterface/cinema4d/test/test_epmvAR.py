##
## Copyright (C)2010 The Scripps Research Institute 
##
## Authors: Ludovic Autin <autin@scripps.edu>
##  
## All rights reserved.
##  
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##  
##   * Redistributions of source code must retain the above copyright notice,
##     this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright notice,
##     this list of conditions and the following disclaimer in the documentation 
##     and/or other materials provided with the distribution.
##   * Neither the name of the Scripps Research Institute nor the names of its
##     contributors may be used to endorse or promote products derived from this 
##     software without specific prior written permission.
##  
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, 
## BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
## FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##  
## For further information please contact:
##  Ludovic Autin
##  <autin@scripps.edu>
##  The Scripps Research Institute
##  10550 N Torrey Pines Rd 
##  La Jolla Ca 92037 USA
##  
##  
## $Header: /opt/cvs/python/packages/share1.5/Pmv/hostappInterface/cinema4d/test/test_epmvAR.py,v 1.1 2010/08/23 18:24:54 autin Exp $
## $Id: test_epmvAR.py,v 1.1 2010/08/23 18:24:54 autin Exp $
##  
##
##
##
#execfile("/Library/MGLTools/1.5.6.csv/MGLToolsPckgs/Pmv/hostappInterface/cinema4d_dev/test/test_epmvAR.py")
import sys

#MGL_ROOT="/Library/MGLTools/1.5.6.csv/"
#sys.path[-1] = '/Library/Python/2.6/site-packages/PIL'

#sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
#sys.path.append(MGL_ROOT+'lib/python2.5/')
#sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
#sys.path.append(MGL_ROOT+'/lib/python2.5/site-packages/PIL')

import c4d
doc = c4d.documents.GetActiveDocument()
if len(c4d.mv) != 0 :
    epmv = c4d.mv[doc.GetDocumentName()]
else :
    from Pmv.hostappInterface.epmvAdaptor import epmv_start
    epmv = epmv_start('c4d',debug=1)
    c4d.mv[doc.GetDocumentName()]=epmv
    
epmv.doCamera = False
epmv.doLight = False

self = epmv.mv
helper = epmv.helper
self.initARViewer(log=0)
self.art.AR.Set(usePlus=False,useCfg=False,usePatCfg=False)
self.art.set_average_mode(True)
self.art.disable_magic_lenses()
self.art.useScenePattern=False
self.art.use_current_camera = False
self.art.dual_display = False
self.art.useAR = True
self.art.use_gesture = False
#self.art.scaleDevice = 1.
self.art.init_video()
self.art.patternMgr.useGUI = False
self.art.scaleDevice = 1.

dir = "/Library/MGLTools/1.5.4/MGLToolsPckgs/ARDemo/hsg1a/"
rec = "hsg1.pdbqt"
self.readMolecule(dir+rec)
self.displayCPK("hsg1")
self.displayCPK("hsg1",negate = True)
self.computeMSMS("hsg1",surfName='MSMShsg1')
lig = "ind.pdbqt"
self.readMolecule(dir+lig)
self.displayCPK("ind")
#need to manually read the map
#self.computeMSMS(molname,surfName='MSMS-MOL')
#self.colorByResidueType(molname, ['MSMS-MOL'])
#######setup ARViewer###########################
################################
#self.art.patternMgr.add_patterns(['hiroPatt'])
#need to load the cube

patt5='patt17'#left
patt6='patt35'#front
patt7='patt36'#right
patt8='patt39'#back   
#['front', 'right','back','left','top','bot']
#why loadDevice didnt set the transfo_position correctly
#about the scaleFactor?
self.art.patternMgr.loadDevice(name='head',type='cube4',width=40.,
                               listPatt=['kanjiPatt','sampPatt1', 'sampPatt2','patt15' ],
                                trans=[0.,0.,-30.],scaleFactor=1.)
self.art.patternMgr.loadDevice(name='bott',type='cube4',
							listPatt=[patt6,patt7,patt8,patt5],width=40.,
							trans=[0.,0.,-30.],scaleFactor=1.)
#offset ?
self.art.patternMgr.groups['head'].offset = [60.,0.,0.]
self.art.patternMgr.groups['bott'].offset = [60.,0.,0.]

#self.loadPattern(['hiroPatt', 'kanjiPatt'], log=0)
#self.setWidth(['hiroPatt', 'kanjiPatt'], 40.0, log=0)

geom = self.Mols[0].geomContainer.masterGeom
self.setGeoms('head',[geom],log=0)#1oel
geom1 = self.Mols[1].geomContainer.masterGeom
self.setGeoms('bott',[geom1],log=0)#1oel

### NRG calculation setup
#at1 = "hsg1:A::;"
#at2 = "ind:::;"
#atomset1 = self.expandNodes(at1)
#atomset2 = self.expandNodes(at2)
#
#helper.cAD3Energies(self,self.Mols,atomset1,atomset2,add_Conf=True,debug=True)
#self.art.nrg_calcul_rate = 5
#need to add the tag on ind

#prepare the image 
bmp = c4d.bitmaps.BaseBitmap()
fn = "/tmp/tmp.jpg"
fn2 = "/Users/ludo/Desktop/ar_ball_Stick.jpg"
#bmp.InitWith(fn2)
bmp.Init(640,480,32)#RGB
bmpS = c4d.bitmaps.BaseBitmap()
bmpS.Init(320,240,32)#RGB

#self.art.start_video()
#helper.updateImage(self,bmp,scale=bmpS)
#helper.updateBmp(self,bmp,scale=bmpS)#,show=False,viewport=Right)
#helper.updateBmp(self,bmp,scale=None,show=False,viewport=Right)
#helper.ARstepM(self)
#helper.ARloop(self,ar=False,im=bmp,ims=bmpS,max=10)
#helper.ARloop(self,ar=True,im=None,ims=None,max=100)
#helper.ARloop(self,ar=True,im=bmp,bmpS=bmpS,max=100)
#helper.updateAppli()
#try to visualize the volume D*tan(FOV/2)

#C4d thread
#thr = helper.c4dThread(func=helper.ARstep,arg=self)
#thr.Start(back=True)
#do some other operations here
#thr.wait() #wait until the main method is done

#regular thread
import thread 
#lock=thread.allocate_lock()
#helper.AR(self,bmp=bmp,v=Right)
#t=thread.start_new_thread(helper.AR,(self,Right))
