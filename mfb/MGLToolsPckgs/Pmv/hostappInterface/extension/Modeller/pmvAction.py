# -*- coding: utf-8 -*-
"""
Created on Fri Jun  4 20:02:15 2010

@author: Ludovic Autin
"""

from modeller.optimizers.actions import action
from Pmv.moleculeViewer import EditAtomsEvent
import modeller
import Pmv.hostappInterface as epmv

def setupMDL(env,name):
    from modeller.scripts import complete_pdb
    mdl = complete_pdb(env, name)
    mdl.patch_ss()
    name = name.split(".pdb")[0]+"m.pdb"
    mdl.write(file=name)
    return name,mdl

def setupENV():
    #setup Modeller
    env = modeller.environ()
    MPATH=epmv.__path__[0]+'/extension/Modeller/'
    env.io.atom_files_directory = [MPATH]
    env.edat.dynamic_sphere = True
    env.libs.topology.read(file='$(LIB)/top_heav.lib')
    env.libs.parameters.read(file='$(LIB)/par.lib')
    return env

def minimizeMDL(mol,maxit=1000,store=True):
    mdl = mol.mdl
    atmsel = modeller.selection(mdl)
    # Generate the restraints:
    mdl.restraints.make(atmsel, restraint_type='stereo', spline_on_site=False)
    #mdl.restraints.write(file=mpath+mname+'.rsr')
    mpdf = atmsel.energy()
    print "before optmimise"
    # Create optimizer objects and set defaults for all further optimizations
    cg = modeller.optimizers.conjugate_gradients(output='REPORT')
    mol.pmvaction.last = 10000
    print "optimise"
    mol.pmvaction.store = store#self.pd.GetBool(self.pd.CHECKBOXS['store']['id'])
    cg.optimize(atmsel, max_iterations=maxit, actions=mol.pmvaction)#actions.trace(5, trcfil))
    del cg
    return True

def dynamicMDL(mol,temp=300,maxit=1000,store=True):
    mdl = mol.mdl
    # Select all atoms:
    atmsel = modeller.selection(mdl)
    # Generate the restraints:
    mdl.restraints.make(atmsel, restraint_type='stereo', spline_on_site=False)
    #mdl.restraints.write(file=mpath+mname+'.rsr')
    mpdf = atmsel.energy()
    print "before optmimise"
    md = modeller.optimizers.molecular_dynamics(output='REPORT')
    mol.pmvaction.last = 10000
    mol.pmvaction.store = store
    print "optimise"
    md.optimize(atmsel, temperature=temp, max_iterations=int(maxit),actions=mol.pmvaction)
    del md
    return True

class pmvAction(action):
    #self.['__call__', '__class__', '__delattr__', '__dict__', 
    #'__doc__', '__getattribute__', '__hash__', '__init__', '__module__',
    #'__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
    #'__str__', '__weakref__', 'first', 'last', 'skip']
    def __init__(self,skip, first, last,iconf=1,pmvModel=None,mv=None):
        action.__init__(self,skip, first, last)
        self.idConf=iconf
        self.pmvModel=pmvModel
        self.epmv = mv
        self.mv = mv.mv
        #if storing mode, we create a conf every x step
        self.store = False
        self.cg=None
        self.realtime=False
        self.mdstep = 2
        self.temp = 300
        self.redraw = True
        self.sObject = "cpk" #object type used for update coordinates. e.g. lines,cpk,bones
        self.rtType = "mini"
        
    def updatePmvCoord(self,conf,model):
        self.pmvModel.allAtoms.setConformation(conf)
        #shold use map()
        for i,atom in enumerate(self.pmvModel.allAtoms):
            #modeller fix molecule and add atoms....crap
            if i < len(model.atoms):
                atom._coords[conf]=[model.atoms[i].x,model.atoms[i].y,model.atoms[i].z]
        self.pmvModel.allAtoms.setConformation(conf)
        
    def updateModellerCoord(self,conf,model):
        self.pmvModel.allAtoms.setConformation(conf)
        for i,atom in enumerate(self.pmvModel.allAtoms):
            if i < len(model.atoms):
                model.atoms[i].x,model.atoms[i].y,model.atoms[i].z = atom._coords[conf]

    def updateModellerCoordXYZ(self,xyz,model):
        for i,coord in enumerate(xyz):
            if i < len(model.atoms):
                model.atoms[i].x,model.atoms[i].y,model.atoms[i].z = coord

    def resetOptimizer(self):
        if self.cg is not None :
            del self.cg
        self.cg = None
        self.modellerOptimizeInit()
        
    def modellerOptimizeInit(self):
        import modeller
        mname,mol=self.pmvModel.name,self.pmvModel      
        mdl = mol.mdl
        # Select all atoms:
        self.atmsel = modeller.selection(mdl)
        # Generate the restraints:
        mdl.restraints.make(self.atmsel, restraint_type='stereo', spline_on_site=False)
        #mdl.restraints.write(file=mpath+mname+'.rsr')
        self.mpdf = self.atmsel.energy()
        print "before optmimise"
        # Create optimizer objects and set defaults for all further optimizations
        if self.rtType == "mini" :
            self.cg = modeller.optimizers.conjugate_gradients(output='REPORT')
        elif self.rtType == "md" :
            self.cg = modeller.optimizers.molecular_dynamics(output='REPORT')
        self.last = 10000
        print "optimise"
        
    def modellerOptimize(self,maxit,temp=300):
        if self.cg is None :
            self.modellerOptimizeInit()
        if self.rtType == "mini" :
            self.cg.optimize(self.atmsel, max_iterations=maxit,actions=self)#actions.trace(5, trcfil))
        elif self.rtType == "md" :
            self.cg.optimize(self.atmsel, temperature=temp, max_iterations=int(maxit),actions=self)
        
        #self.updatePmvCoord(self.idConf,self.pmvModel.mdl)#update lines ?
        #del cg
        return True

    def __call__(self,opt):
        #opt is the optimizer object either cg, md etc...
        #opt.atmsel give acces to the current data model 
        #opt.current_e give acces to the current energy    
        indices,model = opt.atmsel.get_atom_indices()
        self.updatePmvCoord(self.idConf,model)
        event = EditAtomsEvent('coords', self.pmvModel.allAtoms)
        self.mv.dispatchEvent(event)
        #should we update other geom? at least one chain to test
        self.epmv.helper.updatePoly(self.pmvModel.name+":"+self.pmvModel.chains[0].name+"_cloud",
                                    vertices=self.pmvModel.chains[0].residues.atoms.coords)
        #try tu update viewer ?
        if self.redraw:
            if self.mv.hasGui :
                self.mv.GUI.VIEWER.Redraw()
            self.epmv.helper.update()
        if self.store :
            #add a conformation for modeller
            self.pmvModel.allAtoms.addConformation(self.pmvModel.allAtoms.coords[:])
            self.idConf = len(self.pmvModel.allAtoms[0]._coords)-1
        #i could get input coord here?
        #no once i am in the md / optimized loop cant control the display
        #how improve performance ? hcekc on higher perorfmat computer