from ViewerFramework.VFCommand import Command, CommandGUI
from DejaVu.Spheres import Spheres
from DejaVu.Arrows import Arrows
from MolKit.molecule import Atom
import numpy.oldnumeric as Numeric
import math
#from Pmv.moleculeViewer import EditAtomsEvent
#from DejaVu.Transformable import translateEvent

class Handler(Command):
    def create(self,target,geom=None,imd=None,forceType="steered"):
        self.target = target.findType(Atom) #should be an atom selection
        self.imd = imd
        if self.imd is not None :
            self.slot = self.imd.slot
        else : self.slot = 0
        self.initial_position = self.getTargetCenter()
        self.previousForce = [0.,0.,0.] 
        self.scale_force = 0.5 #scale before display and send to MD
        self.sphere_radius = 4.
        if geom is None :
            #by default the handler is a sphere
            self.geom = Spheres('handler', inheritMaterial=False, 
                                   centers=[[0.,0.,0.],],radii=[2.], visible=1)
            if self.vf.hasGui : self.vf.GUI.VIEWER.AddObject(self.geom)
        else :
            self.geom = geom
            #if self.vf.hasGui : self.geom.SetTranslation(Numeric.array(self.initial_position))
            #else : self.geom.setLocation(self.initial_position[0],self.initial_position[1],self.initial_position[2])
        if self.vf.hasGui : self.prepareQuickKeys()
        self.N_forces = len(self.target)
        self.atoms_list = self.target.number #need to check this 
        self.forces_list = Numeric.zeros((self.N_forces,3),'f')
        self.arrow = None

        self.isinited = True
        self.handler_pattern = None
        self.mol_pattern = None
        #preaper the arrow that will represent the force
        if self.vf.hasGui : self.prepareArrow()
        self.forceType = forceType
        #self.vf.registerListener(translateEvent, self.getForces)
        #self.vf.GUI.VIEWER.registerListener(translateEvent, self.getForces)

    def getTargetCenter(self):
	self.target.setConformation(self.slot)
	coords = Numeric.array(self.target.coords)#self.allAtoms.coords
	center = sum(coords)/(len(coords)*1.0)
	center = list(center)
	for i in range(3):
	    center[i] = round(center[i], 4)
	self.target.setConformation(0)
	self.N_forces = len(coords)
	return center

    def prepareArrow(self):
        force = Numeric.array(self.forces_list)
        self.target.setConformation(1)
        point = Numeric.array(self.target.coords)
        self.target.setConformation(0)
        vertices=[]
        faces =[]
        indice=0
        for i in range(self.N_forces):
            vertices.append(point[i])
            vertices.append(point[i]+force[i])
            faces.append([indice,indice+1])
            indice = indice+2
        vertices = Numeric.array(vertices,'f').tolist()
        self.arrow = Arrows('pyarrow', vertices = vertices,faces=faces)
        self.vf.GUI.VIEWER.AddObject(self.arrow)

    def updateArrow(self):
     if self.forceType != "move":
        force = Numeric.array(self.forces_list)
        self.target.setConformation(1)
        point = Numeric.array(self.target.coords)
        self.target.setConformation(0)		
        vertices=[]
        faces =[]
        indice=0
        for i in range(self.N_forces):
            vertices.append(point[i])
            vertices.append(point[i]+force[i])
            faces.append([indice,indice+1])
            indice = indice+2
        vertices = Numeric.array(vertices,'f').tolist()			
        self.arrow.Set(vertices = vertices,faces=faces)

    def prepareQuickKeys(self):
        import Tkinter
        from mglutil.util.callback import CallBackFunction
        #prepare the QuickKeys one for the root, one for the handler
        self.vf.GUI.VIEWER.GUI.showHideQuickKeysVar.set(1)
        xform = 'Object'
        root=self.vf.GUI.VIEWER.rootObject
        cbroot = CallBackFunction( self.vf.GUI.VIEWER.GUI.quickKey_cb, xform, root, 1 )
        cbhandler = CallBackFunction( self.vf.GUI.VIEWER.GUI.quickKey_cb, xform, self.geom, 0 )
        label = "Xform Scene"
        labelHandler = "Xform Handler"
        # create a button and add it to the Quick Keys panel
        button = Tkinter.Button(self.vf.GUI.VIEWER.GUI.QuickKeysFrame, text=label, command=cbroot)
        button.pack(side='top', expand=1, fill='y')
        # create a button and add it to the Quick Keys panel
        button = Tkinter.Button(self.vf.GUI.VIEWER.GUI.QuickKeysFrame, text=labelHandler, command=cbhandler)
        button.pack(side='top', expand=1, fill='y')

    def getHandlerPos(self):
        if self.vf.hasGui :
            if hasattr(self.vf,"art"):
                from numpy import matrix
                #the inverse matrix for molecule pattern
                m1 = self.mol_pattern.mat_transfo
                M1 = matrix(m1.reshape(4,4))
                #get the pattern transfor
                m2 = self.handler_pattern.mat_transfo
                M2 = matrix(m2.reshape(4,4))
                transfo = M2*M1.I
                pos = Numeric.array(transfo[3,:3])
            else :
                pos = self.geom.translation
        else : pos = self.geom.getLocation()
        return pos

    def findNeighbor(self,pos):
        #loop or pmvcommands
        self.vf.selectInSphere(pos, self.sphere_radius, [self.imd.mol.name], log=0)
        node=self.vf.selection
        if node != None : 
            self.target = node.findType(Atom)
            self.N_forces = len(self.target)
            self.atoms_list = self.target.number #need to check this 
            self.forces_list = Numeric.zeros((self.N_forces,3),'f')
            return Numeric.array(self.getTargetCenter())
        else :
            return None

    def getPush(self,target=True):
        pos = self.getHandlerPos()
        if target : targetpos = Numeric.array(self.getTargetCenter())
        else :
            targetpos = self.findNeighbor(pos[0].tolist())
            if targetpos == None : return Numeric.array([0.,0.,0.])
        force =  - Numeric.array(pos[0]) +  targetpos
        d=math.sqrt(Numeric.sum(force*force))
        return force*1/(d*d)
        #else : return Numeric.array([0.,0.,0.])

    def getSteered(self):
        pos = self.getHandlerPos()
        force =  Numeric.array(pos) -  Numeric.array(self.getTargetCenter())    
        #d=math.sqrt(Numeric.sum(force[0]*force[0]))
        #if d > 30. : return Numeric.zeros(3)
        #else : 
        return force

    def getCoord(self):
        pos = self.getHandlerPos()
        mol = self.target.top
        mol.allAtoms.setConformation(self.slot)
        coords = mol.allAtoms.coords[:]
        mol.allAtoms.setConformation(0)
        force =  Numeric.array(coords) + (Numeric.array(pos) -  Numeric.array(self.getTargetCenter()))#Numeric.array([1.0,0.,0.])
        self.N_forces = len(coords)
        return force

    def getForces(self,event):
        if event == None : obj=self.geom
        else : obj = event.objects
        if obj != self.geom : return 0
        if self.forceType == "steered": force = self.getSteered()
        elif self.forceType == "pushtarget": force = self.getPush(target=True)
        elif self.forceType == "push": force = self.getPush(target=False)
        elif self.forceType == "move": force = self.getCoord()
        if self.forceType != "move":
           for i in range(self.N_forces):
                self.forces_list[i] = force*self.scale_force
        else : self.forces_list = force
        self.previousForce = force

commandList = [
    {'name':'handler', 'cmd':Handler(),
     'gui': None},
    ]

def initModule(viewer):
    for dict in commandList:
#        print 'dict',dict
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
