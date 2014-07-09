from numpy import copy
from DejaVu.scenarioInterface.animations import ColorObjectMAA, PartialFadeMAA,\
     RedrawMAA, expandGeoms, getObjectFromString
from DejaVu.scenarioInterface import getActor
from Scenario2.keyframes import KF
from Scenario2.multipleActorsActions import MultipleActorsActions

colorCmds = {"color by atom types": ["colorByAtomType", "Atm"],
             "color by molecule":["colorByMolecules", "Mol"], 
             "color by DG": ["colorAtomsUsingDG", "DG "],
             "color by second.struct.":["colorBySecondaryStructure", "SSt"],
             "color by residue:RasmolAmino": ["colorByResidueType", "RAS"],
             "color by residue:Shapely": ["colorResiduesUsingShapely", "SHA"],
             "choose color": ["color", "col"]}
# the values in the colorCmds dictionary are from pmv.commands.keys()

class PmvColorObjectMAA(ColorObjectMAA):
    """ Create an MAA for different coloring schemes:
        - colorByAtomType
        - colorByMolecules
        - colorAtomsUsingDG
        - colorBySecondaryStructure
        - colorByResidueType
        - colorResiduesUsingShapely
        - color (choose color)
    """

    def __init__(self, object, objectName=None, name=None, nbFrames=None,
                 kfpos=[0,30], pmv = None, colortype = "color by atom types",
                 color = [(0.0, 0.0, 1.0)], nodes = None, easeInOut='none',
                 objectFromString = None, startFlag="after previous", saveAtomProp=False):
        
        """ Create an MAA to color a Pmv object.
        maa <- PmvColorObjectMAA(object, objectName=None, name=None, nbFrames=None,
                 kfpos=[0,30], pmv = None, colortype = "color by atom types",
                 color = [(0.0, 0.0, 1.0)], nodes = None,
                 objectFromString = None, startFlag='after previous')
        arguments:
         - object -  a geometry object (or list of objects) to color;
         - objectName - the object's name. If it is not specified, the class constructor
                      will try to use 'fullName' attribute of the object.
         - name   - the MAA name;
         - nodes - specifies a subset of atoms;
         - pmv is an instance of Pmv;
         - colortype - one of the available coloring schemes;
         - color - specifies (r,g, b) tuple if colortype is 'choose color';
         - either a total number of frames (nbFrames) or a list of keyframe positions
           (kfpos) can be specified;
         - objectFromString is a string  that yields the specified oject(s) when evaluated;
         - startFlag - flag used in a sequence animator for computing time position of the maa.
         
    """

        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object

        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.actors = []
        self.endFrame = 0
        self.gui = None
        self.redrawActor = None
        if not pmv:
            print "application Pmv is not specified"
            return
        vi = pmv.GUI.VIEWER
        if colortype not in colorCmds.keys():
            print "unsupported color scheme %s" % colortype
            return
        
        self.cmd = pmv.commands[colorCmds[colortype][0]]
        self.shortName = colorCmds[colortype][1]
        self.color = color
        self.pmv = pmv
        if nodes is None:
            nodes = pmv.getSelection()
        self.nodes = nodes
        geoms = self.cmd.getAvailableGeoms(nodes)
        #print "available geoms", geoms
        molnames = map(lambda x: x.name , pmv.Mols)
        
        for object in objects:
            #print "object:", object
            oname = object.name
            if oname != "root" and oname not in geoms and oname not in molnames:
                import tkMessageBox
                tkMessageBox.showwarning("Pmv AniMol warning:", "Cannot create %s animation for %s -\nobject is not available for Pmv color command."%(colortype, object.name))
                #print "object %s cannot be colored with %s" % (object.name, colortype)
                ind = objects.index(object)
                objects.pop(ind)
        if not len(objects):
            return
        
        vi.stopAutoRedraw()
        
        geomsToColor = []
        molecules = []
        for object in objects:
            if object.name == "root":
                geomsToColor = geoms # "all"
                molecules = self.cmd.getNodes(nodes)[0]
                break
            elif object.name in molnames:
                geomsToColor = geoms
                molecules = [pmv.getMolFromName(object.name),]
                break
            else:
                geomsToColor.append(object.name)
                if hasattr(object, "mol"):
                    molecules.append(object.mol)
        #Get initial color .If the object is a geometry container, get colors for each child geometry.
        initColors = self.initColors = self.getObjectsColors(geomsToColor, molecules)
        
        #print "nodes" , nodes
        #print "color type:", colortype
        #print "objects:", objects
        #print "geoms to color:", geomsToColor
        #print "calling command", self.cmd
        editorKw = {}
        # call command and get current value
        if colortype == "choose color":
            self.cmd(nodes, color, geomsToColor, log = 0)
            editorKw = {'choosecolor': True}
        else:
            self.cmd(nodes, geomsToColor, log = 0)
        #finalColors = self.finalColors = self.getObjectsColors(objects, nodes)
        finalColors = self.finalColors = self.getObjectsColors(geomsToColor, molecules)
        geoms = finalColors.keys()
        self.geomsToColor = geomsToColor
        self.molecules = molecules
        #print "geoms:", geoms
        self.atomSets = {}
        if len(geoms): 
        
            ColorObjectMAA.__init__(self, geoms, initColors=initColors,
                                    finalColors=finalColors,
                                    objectName=objectName, name=name,
                                    nbFrames=nbFrames, kfpos=kfpos,
                                    colortype = colortype,
                                    objectFromString=objectFromString,
                                    startFlag=startFlag, easeInOut=easeInOut)
            for object in objects:
                # object is probably a geom container, so we need to add a 'visible' actor for it:  
                visibleactor = getActor(object, 'visible')
                if not self.findActor(visibleactor):
                    self.origValues[visibleactor.name] =  visibleactor.getValueFromObject()
                    kf1 = KF(kfpos[0], 1)
                    visibleactor.actions.addKeyframe(kf1)
                    self.AddActions( visibleactor, visibleactor.actions )

        
            if saveAtomProp:
                try:
                    self.saveGeomAtomProp()
                except: pass
        #return to the orig state
        pmv.undo()
        
        vi.startAutoRedraw()
        self.editorKw = editorKw


    def saveGeomAtomProp(self):
        self.atomSets = {}
        allobj = self.objects
        from MolKit.molecule import Atom
        from copy import copy
        for obj in allobj:
            if hasattr(obj, "mol"):
                mol = obj.mol
                set = mol.geomContainer.atoms.get(obj.name, None)
                if set is not None and len(set):
                    #print "saving aset for:" , obj.fullName
                    aset = set.findType(Atom).copy()
                    self.atomSets[obj.fullName] = {'atomset': set.full_name(0)}
                    
                    #self.atomSets[obj.fullName] = {'atomset': set}
                    #if aset.colors.has_key(obj.name):
                    #    self.atomSets[obj.fullName]['colors']=copy(aset.colors[obj.name])
                    #elif aset.colors.has_key(obj.parent.name):
                    #    self.atomSets[obj.fullName]['colors']=copy(aset.colors[obj.parent.name])


    def getObjectsColors(self, geomsToColor, molecules):
        colors = {}
        for mol in molecules:
            allGeoms = []
            geomC = mol.geomContainer
            for gName in geomsToColor:
                if not geomC.geoms.has_key(gName): continue
                geom = geomC.geoms[gName]
                allGeoms.append(gName)
                if len(geom.children):
                    childrenNames = map(lambda x: x.name, geom.children)
                    allGeoms = allGeoms + childrenNames
                for name in allGeoms:
                    if geomC.atoms.has_key(name) and len(geomC.atoms[name])==0: continue 
                    col = geomC.getGeomColor(name)
                    if col is not None:
                        g = geomC.geoms[name]
                        colors[g] = col
            
        return colors


    def setGeomAtomProp(self):
        if not len(self.atomSets) : return
        from MolKit.molecule import Atom
        prop = 'colors'
        for actor in self.actors:
            if actor.name.find(prop) > 0:
                obj = actor.object
                if self.atomSets.has_key(obj.fullName):
                    #setstr = self.atomSets[obj.fullName]['atomset']
                    g = obj.mol.geomContainer
                    aset = g.atoms[obj.name].findType(Atom)
                    asetstr = aset.full_name(0)
                    #if len(asetstr) != len(setstr):
                    #    return
                    atList = []
                    func = g.geomPickToAtoms.get(obj.name)
                    if func:
                        atList = func(obj, range(len(obj.vertexSet.vertices)))
                    else:
                        allAtoms = g.atoms[obj.name]
                        if hasattr(obj, "vertexSet") and len(allAtoms) == len(obj.vertexSet):
                            atList = allAtoms
                    if not len(atList): return
                    col = actor.getLastKeyFrame().getValue()
                    oname = None
                    if aset.colors.has_key(obj.name):
                        oname = obj.name
                    elif aset.colors.has_key(obj.parent.name):
                        oname = obj.parent.name
                    if not oname : return
                    if len(col) == 1:
                        for a in atList:
                            a.colors[oname] = tuple(col[0])
                    else:
                        for i, a in enumerate(atList):
                            a.colors[oname] = tuple(col[i])
                    from MolKit.stringSelector import StringSelector
                    selector = StringSelector()
                    #nset, msg = selector.select(atList, setstr)
                    nset, msg = selector.select(atList, asetstr)
                    #if g.atoms[obj.name].elementType == Atom:
                        #obj.mol.geomContainer.atoms[obj.name] = nset
                    


    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from Pmv.scenarioInterface.animations import PmvColorObjectMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = PmvColorObjectMAA(object, objectName='%s', name='%s', kfpos=%s, pmv=pmv, colortype='%s', """ % (varname, self.objectName, self.name, self.kfpos, self.colortype)
        lines += """ nodes=%s""" %(self.cmd._strArg(self.nodes)[0], )
        import numpy
        if type(self.color) == numpy.ndarray:
            lines += """color=%s, """ % self.color.tolist()
        else:
            lines += """color=%s, """ % self.color
        lines += """ objectFromString="%s", startFlag='%s', saveAtomProp=False)\n""" % (self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('Pmv AniMol warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines

    
    def configure(self, **kw):
        """
        set kfpos, direction and easeInOut and rebuild MAA
        """
        if kw.has_key('color'):
            if self.colortype == "choose color":
                vi = self.pmv.GUI.VIEWER
                vi.stopAutoRedraw()
                self.cmd(self.nodes, kw['color'], self.geomsToColor, log = 0)
                finalColors = self.finalColors = self.getObjectsColors(self.geomsToColor,
                                                                       self.molecules)
                self.pmv.undo()
                vi.startAutoRedraw()
                self.color = kw['color']
            kw.pop('color')
        if not kw.has_key('colortype'):
            kw['colortype'] = self.colortype
        ColorObjectMAA.configure(self, **kw)

    def run(self, forward=True):
        ColorObjectMAA.run(self, forward)
        try:
            self.setGeomAtomProp()
        except:
            pass
            #print "FAILED to setGeomAtomProp"


    def setValuesAt(self, frame, pos=0):
        ColorObjectMAA.setValuesAt(self, frame, pos)
        if frame == pos + self.lastPosition:
            try:
                self.setGeomAtomProp()
            except:
                pass



from MolKit.molecule import Atom

class  PartialFadeMolGeomsMAA(PartialFadeMAA):

    """
    build a MAA to fade in parts of a molecule for geometry objects where the
    atom centers correspond to the geometry vertices (cpk, sticks, balls,
    bonded, etc)
    
    [maa] <- PartialFadeMolGeomsMAA(object, nodes=None, pmv=None,
                            objectName=None, name=name, 
                            nbFrames=None, kfpos=[0,30], easeInOut='none',
                            destValue=1.0, fade='in', startFlag='after previous')

    - object  is a DejaVu geometry object or a list of objects
    - nodes specifies a subset of atoms
    - pmv is an instance of Pmv
    - destValues is the opacity desired at the end of the fade in
    - fade can be 'in' or 'out'. for 'in' the MAA fades nodes in to a level of
      opacity destValue. For 'out' it fades them out to opacity destValue
    - either a total number of frames (nbFrames) or a list of keyframe positions
      (kfpos) can be specified;
    - startFlag - flag used in a sequence animator for computing time position of the maa.       
    
    For each molecule a vector of an MAA is generated that will force the
    geom's visibility to True and interpolate th per-vertex array of opacities
    from a starting vetor to a final vector. Only entries in this vector
    corresponding to the atoms to be faded in will have interpolated value.
    Other displayed atoms will retain their current opacity

    NOTE: the atoms specified by nodes have to be displayed for the specified
    geoemtries BEFORE this function is called
    """

    def __init__(self, object, nodes=None, pmv=None, objectName=None, name=None, 
                 kfpos=[0,30], easeInOut='none', destValue=None, fade='in',
                 objectFromString = None, startFlag="after previous"):

        
        if not hasattr(object, "__len__"):
            objects = [object]
        else:
            objects = object
        geometries = expandGeoms(objects)
        self.actors = []
        self.endFrame = 0
        self.gui = None
        self.redrawActor = None
        self.editorClass = None
        if not pmv:
            print "application Pmv is not specified"
            return
        self.pmv = pmv
        if not len(geometries):
            return
        vi = pmv.GUI.VIEWER

        
        if fade=='in':
            if destValue is None:
                destValue = 0.6
        else:
            if destValue is None:
                destValue = 0.4
        if name is None:
            if objectName:
                name = "partial fade %s, %s, %3.1f"% (
                    fade, objectName, destValue)
        
        if objectFromString is None:
            objectFromString = getObjectFromString(objects)
        self.actors = []
        
        self.easeInOut = easeInOut
        self.destValue = destValue
        self.fade = fade
        self.nodes = nodes
        #print "geometries", geometries, "nodes", nodes
        #self.objects = geometries
        allobjects = self.getOpacityValues(geometries, nodes, destValue, fade)
        self.objects = allobjects

        if len(allobjects):
            PartialFadeMAA.__init__(self, allobjects, self.initOpac, self.finalOpac, name=name,
                                    objectName=objectName,
                                    kfpos=kfpos, easeInOut=easeInOut,
                                    objectFromString=objectFromString,
                                    startFlag=startFlag)
        from Pmv.scenarioInterface.animationGUI import SESpOpSet_MAAEditor
        self.editorClass = SESpOpSet_MAAEditor
        self.editorKw = {'pmv': pmv}
        self.editorArgs = []

        if not len(self.actors):
            RedrawMAA.__init__(self, vi, name)
                #print "cannot create PartialFadeMAA for object:", object.name, self.actors



    def getOpacityValues(self, objects, nodes=None, destValue=None, fade=None):
        if nodes != None:
            self.nodes = nodes            
        if destValue != None:
            self.destValue = destValue
        if fade != None:
            self.fade = fade

        allobjects = []
        self.initOpac = initOpac = {}
        self.finalOpac = finalOpac = {}
        #if self.nodes:
        #    print "lennodes:", len(self.nodes)
        #print "objects ", objects
        for geom in objects:
            try:
                molecules, atmSets = self.pmv.getNodesByMolecule(self.nodes, Atom)
                # for each molecule
                geomName = geom.name
                for mol, atms in zip(molecules, atmSets):
                    if not mol.geomContainer.geoms.has_key(geomName):
                        continue
                    if geom.mol != mol:
                        continue
                    # get the set of atoms in mol currently displayed as CPK
                    atset = mol.geomContainer.atoms[geomName]
                    # build initial and final vector of opacities
                    _initOpac = geom.materials[1028].prop[1][:,3].copy()
                    _finalOpac = _initOpac.copy()
                    if len(_finalOpac) == 1:
                        import numpy
                        _finalOpac = numpy.ones(len(atset), 'f')*_initOpac[0]

                    atIndex = {} # provides atom index in atset
                    for i, at in enumerate(atset):
                        atIndex[at] = i

                    # set initial opacity and final opacity for all atoms to fade in 
                    if self.fade=='in':
                        for at in atms:
                            i = atIndex[at]
                            _initOpac[ i ] = 0.0
                            _finalOpac[ i ] = self.destValue
                    else:
                         for at in atms:
                            i = atIndex[at]
                            _finalOpac[ i ] = self.destValue
                    allobjects.append(geom)
                    initOpac[geom] = _initOpac
                    finalOpac[geom] = _finalOpac
            except:
                if self.fade=='in':
                    initOpac[geom] = [0.0]
                else:
                    initOpac[geom] = geom.materials[1028].prop[1][:,3]
                allobjects.append(geom)
                finalOpac[geom] = self.destValue

        return allobjects


    def configure(self, **kw):
        """set nodes, destValue, fade parameters and rebuild MAA."""
        
        nodes = None
        if kw.has_key('nodes'):
            nodes = kw.pop('nodes')
        destValue = None
        if kw.has_key('destValue'):
            destValue = kw.pop('destValue')
        fade = None
        if kw.has_key('fade'):
            fade = kw.pop('fade')
        allobjects = self.getOpacityValues(self.objects, nodes, destValue, fade)
        self.objects = allobjects
        PartialFadeMAA.configure(self, **kw)
        self.name = "partial fade %s, %s, %3.1f"% (
                    self.fade, self.objectName, destValue)
        

    def getSourceCode(self, varname, indent=0):
        """
        Return python code creating this object
        """
        if not self.objectFromString:
            return ""
        tabs = " "*indent
        lines = tabs + """import tkMessageBox\n"""
        lines += tabs + """from Pmv.scenarioInterface.animations import PartialFadeMolGeomsMAA\n"""
        lines += tabs + """object = %s\n"""%(self.objectFromString)
        newtabs = tabs + 4*" "
        lines += tabs + """try:\n"""
        lines += newtabs + """%s = PartialFadeMolGeomsMAA(object, objectName='%s', name='%s', kfpos=%s, pmv=pmv, fade='%s', destValue=%.2f, """ % (varname, self.objectName, self.name, self.kfpos, self.fade, self.destValue)
        if not hasattr(self.pmv, "color"):
            self.pmv.loadModule("colorCommands", "Pmv")
        lines += """ nodes=%s""" %(self.pmv.color._strArg(self.nodes)[0], )
        lines += """easeInOut='%s', """ % self.easeInOut     
        lines += """ objectFromString="%s", startFlag='%s')\n""" % (self.objectFromString, self.startFlag)
        lines += newtabs + """assert len(%s.actors) > 0 \n""" % (varname,)
        lines += tabs + """except:\n"""
        lines += newtabs + """if showwarning: tkMessageBox.showwarning('Pmv AniMol warning', 'Could not create MAA %s')\n""" % self.name
        lines += newtabs + """print sys.exc_info()[1]\n"""
        return lines


