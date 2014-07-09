# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 23:49:50 2010

@author: -
"""
#
#1wpe.pdb +membrane
#=>9207 atoms
#Time stat:
##reading 1crn 327atms
#loadPDB 0.0902199745178
##           compute                           update                  render S/A
##CPK                                                                  0:00:04
#surf        0.19288110733
#cpk         0.130399942398
#ss          0.20935177803
#lines       0.0323891639709
#bs          0.359109163284
#cms         0.101706027985

##reading 1crn 327atms
#loadPDB 0.0902199745178
##           compute                           update                  render S/A
##CPK                                                                  0:00:04
#surf        0.19288110733
#cpk         0.130399942398
#ss          0.20935177803
#lines       0.0323891639709
#bs          0.359109163284
#cms         0.101706027985

#general import
import sys,os
from time import time
#get the current software
if __name__ == "__main__":
	soft = os.path.basename(sys.argv[0]).lower()
else : 
    soft = __name__

#time to start epmv  1279092203.67
#time to start epmv  1279092405.16

plugin=False
re={}
if not plugin : 
    #define the python path
    import math
    MGL_ROOT="/Library/MGLTools/1.5.6.csv/"#os.environ['MGL_ROOT']
    sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
    sys.path.append(MGL_ROOT+'lib/python2.5/site-packages/PIL')
    sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
    #start epmv
    t1=time()
    from Pmv.hostappInterface.epmvAdaptor import epmv_start
    epmv = epmv_start(soft,debug=1)
    print "time to start epmv ",time()-1
else :
    #get epmv and mv (adaptor and molecular viewer)
    if sotf == 'c4d':
        import c4d
        epmv = c4d.mv.values()[0]#[dname]
import Pmv
dataDir = Pmv.__path__[0]+'/Tests/Data/'
self = epmv.mv
from Pmv import hostappInterface
plgDir = hostappInterface.__path__[0]
from Pmv.hostappInterface import comput_util as util

epmv.doCamera = False
epmv.doLight = False

listemol=["1AY3.pdb","fx.pdb",
"1HS1.pdb","hpi1s.mol2",
"1bsr.pdb","hsg1.C.map",
"1crn.pdb"]
#1AY3.pdb 117 atms
#1crn.pdb 327 atoms
#1bsr.pdb 2038
#need to sort 0-25.000



#most of pdb are <25.000
#2wu2 25.000
#3kfu 50.000
#2C7C groel/groes 57946 ats
#cpk : time  6.920814991
#
#0.2f/s
#3n6r 100.000
#2aff 250.000
#2wwv 500.000
#1htq 1.000.000 
#2ku2 1.290.000 

#1vri 150720      Bacteriophage phi-29 connector array. This file is one of three representing the entire carpet. This file, 1vri, includes the upper 5 monomers the other two files, 1ywe and 1vrj, contain the lower 5 and right 3 monomers respectively
#lines 23fps
#cpk 2fps (14sec to build anmd 14 sec to color) low res
#msms segmentation fault
#3k1q 101798      Backbone model of an aquareovirus virion by cryo-electron microscopy and bioinformatics
#3i55 99287   	 Co-crystal structure of mycalamide a bound to the large ribosomal subunit
from time import time
def timeFunction(function,arg):
    t1=time()
    function(arg)
    print "time ", time()-t1

def doit(mv,mol,R):
    from time import time
    self = mv
    #read the molecule and store some usefull information
    result={}
    t1=time()
    self.readMolecule(mol)
    result["loadPDB"] = time()-t1
    
    mol = self.Mols[0]
    mname = mol.name
    sc = epmv._getCurrentScene()
    masterParent = mol.geomContainer.masterGeom.obj
    
    #display
    t1=time()
    self.displayLines(mname)
    result["lines"] = time()-t1
    
    t1=time()
    self.displayCPK(mname)
    result["cpk"] = time()-t1
    
    t1=time()
    self.displaySticksAndBalls(mname,sticksBallsLicorice='Sticks and Balls',
                               cquality=0, bquality=0, cradius=0.2, only=False, 
                               bRad=0.3, negate=False, bScale=0.0)
    result["bs"] = time()-t1
    
    t1=time()
    self.computeMSMS(mname,surfName='MSMS-MOL')
    result["surf"] = time()-t1
    
    t1=time()
    #self.computeSecondaryStructure(mname, molModes={mname:'From Pross'}, log=0)
    #self.displayExtrudedSS(mname, negate=False, only=False, molModes={mname:'From Pross'}, log=0)
    self.displayExtrudedSS(mname)
    result["ss"] = time()-t1
    
    t1=time()
    name='CoarseMS_'+mname
    parent=masterParent 
    geom=epmv.coarseMolSurface(mol,[32,32,32],
                               isovalue=7.1,resolution=-0.3,
                               name=name)
    mol.geomContainer.geoms[name]=geom
    obj=epmv._createsNmesh(name,geom.getVertices(),None,
                           geom.getFaces(),smooth=True)
    epmv._addObjToGeom(obj,geom)
    epmv._addObjectToScene(sc,obj[0],parent=parent)
    result["cms"] = time()-t1
    R[mname] = result
    return R
    
def displayR(result):
    for molname in result.keys():
        for ds in result[molname].keys():
            print ds, " ", result[molname][ds]
            sys.stderr.write(ds+" "+str(result[molname][ds])+'\n')

re=doit(self,dataDir+listemol[6],re)
displayR(re)


#self.colorResiduesUsingShapely(mname, [name])
#g=mol.geomContainer.geoms[name]

#t1=time()
#self.colorByAtomType("pymolpept",['sticks','balls'])
#result["lines"] = time()

#t1=time()
#self.colorAtomsUsingDG("pymolpept",['cpk'])
#t1=time()

#self.computeMSMS("pymolpept",surfName='MSMS-MOL',pRadius=0.8)
#t1=time()
#self.colorByResidueType("pymolpept",['MSMS-MOL'])
#t1=time()
#self.colorBySecondaryStructure("pymolpept",['secondarystructure'])
