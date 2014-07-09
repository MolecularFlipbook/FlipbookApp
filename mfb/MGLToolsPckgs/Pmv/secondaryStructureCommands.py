#############################################################################
#
# Author: Sophie I. COON, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/secondaryStructureCommands.py,v 1.126.2.8 2012/03/21 23:23:15 annao Exp $
#
# $Id: secondaryStructureCommands.py,v 1.126.2.8 2012/03/21 23:23:15 annao Exp $
#


from Tkinter import Label, Checkbutton, Radiobutton, StringVar, IntVar
import Pmw
import types
from types import StringType, IntType
import numpy

from opengltk.OpenGL import GL
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Shapes import Shape2D, Triangle2D, Circle2D, Rectangle2D,\
     Square2D, Ellipse2D
from NucleicBases import Add_Nucleic_Bases
from ViewerFramework.VFCommand import CommandGUI
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ExtendedSliderWidget, ListChooser,\
     SliderWidget
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet
from MolKit.protein import Protein, Residue, Chain, ResidueSet, ProteinSet
from MolKit.protein import SecondaryStructure, SecondaryStructureSet, \
     Helix, Strand, Turn, Coil
from MolKit.moleculeParser import MoleculeParser

#from ViewerFramework.drawShape import DrawShape

from Pmv.mvCommand import MVCommand
from Pmv.extruder import Sheet2D, ExtrudeSSElt, ExtrudeNA
from Pmv.displayCommands import DisplayCommand
from Pmv.colorCommands import ColorFromPalette
from Pmv.colorPalette import ColorPalette, ColorPaletteNG
from Pmv.deleteCommands import AfterDeleteAtomsEvent
from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent
from MolKit.protein import Residue
from MolKit.PDBresidueNames import AAnames, Nucleotides

class ComputeSecondaryStructureCommand(MVCommand):
    """The computeSecondaryStructure command gets the information on the secondary structure of each molecule contained in the current selection.This information is then used to create object describing the various secondary structure elements.
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : ComputeSecondaryStructureCommand
    \nCommand name : computeSecondaryStructure
    \nDescription:\n 
    The SS element object belonging to a chain are then grouped into sets.
    A new level is added in the 4 level hierarchy...
    The information is taken from the file when available or using stride when
    available.This command can be used as an interactive command.
    \nSynopsis:\n
        None <--- ComputeSS(nodes, molMode={}, **kw)
    \nRequired Arguments:\n   
        nodes --- any set for MolKit nodes describing molecular components
    \nOptional Arguments:\n    
        \nmolmode --- dictionary key: molecule name, value : 'From File' or 'From Stride'.
    \nRequired Packages:\n
      MolKit, DejaVu, mglutil, OpenGL, Tkinter, Pmw, types, ViewerFramework
    \nKnown bugs:\n
      None
    \nExamples:\n
      mol = mv.Mols[0]
      \nmv.computeSecondaryStructure(mv.getSelection())
    """
    

    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly


    def onRemoveObjectFromViewer(self, obj):
        """
        Method to delete sets created by this command.
        This is done to prevent circular references and memory leaks.
        """
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'chains'): return
        import sys
        for c in obj.chains:
            if not hasattr(c, 'secondarystructureset') :
                continue
            if c.secondarystructureset is None:
                delattr(c.secondarystructureset)
            else:
                # Cleaning up all the circular references created in this
                # command
                while len(c.secondarystructureset)!=0:
                    if hasattr(c.secondarystructureset[0], 'exElt'):
                        delattr(c.secondarystructureset[0], 'exElt')
                    delattr(c.secondarystructureset[0], 'children')
                    delattr(c.secondarystructureset[0], 'residues')
                    delattr(c.secondarystructureset[0], 'start')
                    delattr(c.secondarystructureset[0], 'end')
                    delattr(c.secondarystructureset[0], 'parent')
                    delattr(c.secondarystructureset[0], 'chain')
                    delattr(c.secondarystructureset[0], 'top')
                    del(c.secondarystructureset[0])

    def onAddCmdToViewer(self):
        # Try to import stride and set the flag to 1 if succeeds and to 0 if
        # does not
        try:
            import stride
            self.haveStride = 1
        except:
            self.haveStride = 0

        # Load the dependent commands if not already loaded in the
        # application
        #if self.vf.hasGui and \
        if not self.vf.commands.has_key('saveSet'):
            self.vf.loadCommand("selectionCommands", "saveSet", "Pmv",
                                topCommand=0)

##         if self.vf.hasGui and not self.vf.commands.has_key('selectSet'):
##             self.vf.loadCommand("selectionCommands", "selectSet", "Pmv",
##                                 topCommand=0)

    def __call__(self, nodes, molModes=None, **kw):
        """None <--- computeSecondaryStructure(nodes, molModes = None, **kw)
        \nnodes --- TreeNodeSet holding the current selection.
        \nmoldMode --- dictionary {name of the protein: 'From File', 'From PROSS', or 'From Stride'},
                  'From File' to get the information from the file,
                  'From Pross' to use the pross code to assing SS
                  'From Stride' to use stride (requires stride to be installed).
        """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        #print nodes,molModes		
        if not nodes: return
        kw['molModes'] = molModes
        self.doitWrapper( *(nodes,), **kw)
        

    def doit(self, nodes, molModes=None):
        molecules, nodeSets = self.vf.getNodesByMolecule(nodes)
        if len(molecules)==0 : return
        # Loop over the molecules
        for mol in molecules:
            for c in mol.chains:
                c.ribbonType()

            # Determine what mode to use to get the information
            if molModes is None:
                if mol.hasSS:
                    # Information has already been computed then
                    # continue
                    continue
                else:
                    # Find out the possibilities and set the mode to
                    # one of them.
                    if mol.parser:                    
                        if mol.parser.hasSsDataInFile():
                            # File contains information the mode will be 'From
                            # File'
                            mode = 'From File'
                        else:
                            mode = 'From Pross'
                    elif self.haveStride:
                        # Stride is available on the platform
                        # but no info in the file then stride will be used
                        mode='From Stride'
                    else:
                        mode='From Pross'
            else:
                #print molModes
                # a mode to get the information has been specified
                # for the given molecules
                if molModes and not molModes.has_key(mol.name):
                    # if the mode has not been specified for a molecule
                    # print a message and continue
                    print 'No mode has been specified for %s'%mol.name
                    continue
                else:
                    # Set the mode to the given value.
                    mode = molModes[mol.name]

            # if this mode has already been used pass.
            if mode in mol.hasSS: continue

            # if secondarystructure have been computed once using another
            # mode need to clean up first
            elif mol.hasSS != []:
                self.clean(mol)

            # Then compute using the new given mode.
            #if mode is None:
            #    mol.secondaryStructureFromFile()

            if mode == 'From File':
                # If both modes available try file first if fails use stride
                # instead.
                #if not mol.parser.hasSsDataInFile():
                #    # GIVE FEEDBACK TO THE USER !!!!
                #    self.warningMsg("WARNING: "+mol.name + \
                #                    ".pdb does not contain Secondary \
                #                    Structure information.")
                #    continue
                #else:
                    mol.secondaryStructureFromFile()
                    #self.savesets(mol)

            elif mode == 'From Stride':
                if not self.haveStride:
                    self.warningMsg("WARNING: Stride is not available on \
                    this computer to compute the secondary structure of "+\
                                       mol.name+".pdb")
                    continue
                else:
                    mol.secondaryStructureFromStride()
                    #self.savesets(mol)

            elif mode == 'From Pross':
                mol.secondaryStructureFromPross()
                #self.savesets(mol)

            #self.savesets(mol)


    def savesets(self, mol):
        for c in mol.chains:
            if not hasattr(c, 'secondarystructureset'): continue
            for ss in c.secondarystructureset:
                name = "%s%s"%(ss.name, ss.chain.id)
                if ss.residues:  #Bugfix for  #1033
## MS calling the command slows this down a lot
## but the sets are needed to extrude, so we add sets 'by hand'
## side effect: no vision nodes for these sets
#                    self.vf.saveSet(ss.residues, mol.name+':'+name[-1]
#                                    +':'+name[:-1],
#                                    '%s-%s' %(ss.residues[0].name,
#                                              ss.residues[-1].name),
#                                    topCommand=0)
                    name = mol.name+':'+name[-1] +':'+name[:-1]
                    ss.residues.comments = '%s-%s'%(ss.residues[0].name,
                                                    ss.residues[-1].name)
                    self.vf.sets.add(name, ss.residues)

    
    def clean(self, mol):
        """
        This method is called when getting the secondary structure information
        using stride after having from file and vice versa. It is used to
        delete all the secondary structure objects and attributes created
        previously."""
        # Compute secondary structure creates the following:
        # - Secondary structure elements
        # - Save the secondary structure elements residues as a set
        # - new mol attribute hasSS which is a list
        #from Pmv.selectionCommands import sets__
        molName = mol.name
        mol.hasSS = []
        # Here need to check if the secondary structure element have
        # been extruded or not. If yes need to clean up that as well.
        if hasattr(mol, '_ExtrudeSecondaryStructureCommand__hasSSGeom')\
        and mol._ExtrudeSecondaryStructureCommand__hasSSGeom:
            self.vf.extrudeSecondaryStructure.clean(mol)

        for chain in mol.chains:
            # delete the secondarystructureset
            if not hasattr(chain, 'secondarystructureset'): continue
            for ss in chain.secondarystructureset:
                name = "%s%s"%(ss.name, ss.chain.id)
                setName = mol.name+':'+name[-1]+':'+name[:-1]
                if self.vf.sets.has_key(setName):
                    del self.vf.sets[setName]
                #del sets__[mol.name+':'+name[-1]+':'+name[:-1]]
            delattr(chain, 'secondarystructureset')
            
            # delete the secondarystructure attribute of the residues when
            # existing.
            resWithSS = filter(lambda x:hasattr(x, 'secondarystructure'),
                               chain.residues)
            resTest = map(lambda x:
                          delattr(x, 'secondarystructure'),
                          resWithSS)
            
        # call the onRemoveObjectFromViewer for the mol.
        self.vf.undoableDelete__ = False
        self.onRemoveObjectFromViewer(mol)
        del self.vf.undoableDelete__
        
        # Also need to clean up the sheet2D information.
        for c in mol.chains:
            if hasattr(c, 'sheet2D') and c.sheet2D.has_key('ssSheet2D'):
                del c.sheet2D['ssSheet2D']

        
    def buildFormDescr(self, formName):
        """
        Build a for that has a line for each molecule for which we will
        assign secondary structure. Each line contains 1 or more methods
        to assign secondary structure from the list(Pross, file, stride)
        """
        self.nodes = self.vf.getSelection()
        self.molModes = {} # this dictionary has molecules as keys and
                           # a method for assigning SS as value or None

        molecules = self.nodes.top.uniq()
        if len(molecules)==0: return 
        idf = InputFormDescr(title="Get SS Information:")

        haveStride = self.haveStride
        for mol in molecules:

            # check if there are amino acids in the selection
            aa = [x for x in mol.chains.residues if \
                  AAnames.has_key(x.type.strip().upper())]

            if len(aa)==0: # NO AA -> cannot use file, PROSS or STRIDE
                self.molModes[mol.name]=None
                continue
            
            # MS 09 2010. I do not think we have 2 level molecules anymore
            #if not Chain in mol.levels: continue

            haveInFile = mol.parser.hasSsDataInFile()
            molName = mol.name + ' : '

            # if stride is not found and no SS info in the file we use PROSS
            if not haveStride and not haveInFile:
                idf.append({
                    'widgetType':Label,
                    'wcfg':{'text':molName},
                    'gridcfg':{'sticky':'w'}})

                idf.append({'widgetType':Label, # label NOT button
                            'name':'From Pross',# since it is the only option
                            'wcfg':
                            {'text':'From Pross'},
                            'gridcfg':{'sticky':'w', 'row':-1}})
                # we put
                self.molModes[mol.name]='From Pross'

            # if stride is installed but no file info we have a choice of
            # stride or PROSS and PROSS is the default
            elif haveStride and not haveInFile:
                defaultValue = 'From Pross'
                idf.append({'name':mol.name,
                            'widgetType': Pmw.RadioSelect,
                            'groupedBy':1,
                            'listtext':['From Stride','From Pross'],
                            'defaultValue': defaultValue,
                            'wcfg':{'label_text':molName,
                                    'labelpos':'w'
                                    },
                            'gridcfg':{'sticky':'ew'}})

            # if no stride but file info we have a choice of Pross or file\
            # and file is the default
            elif not haveStride and haveInFile:
                defaultValue = 'From File'
                idf.append({'name':mol.name,
                            'widgetType': Pmw.RadioSelect,
                            'groupedBy':1,
                            'listtext':['From File','From Pross'],
                            'defaultValue': defaultValue,
                            'wcfg':{'label_text':molName,
                                    'labelpos':'w'
                                    },
                            'gridcfg':{'sticky':'ew'}})

            # stride is present, and file has SS info. 3 choices,
            # file is default
            else:
                #if 'From File' in mol.hasSS:
                #    defaultValue = 'From Stride'
                #else:
                defaultValue = 'From File'

                idf.append({'name':mol.name,
                            'widgetType': Pmw.RadioSelect,
                            'groupedBy':1,
                            'listtext':['From File', 'From Stride','From Pross'],
                            'defaultValue': defaultValue,
                            'wcfg':{'label_text':molName,
                                    'labelpos':'w'
                                    },
                            'gridcfg':{'sticky':'ew'}})
 
        return idf


    def guiCallback(self):
        val = self.showForm('getSSInfo', force=1)
        for key,value in val.items():
            self.molModes[key] = value
            del val[key]
        if self.molModes == {}: # happens if selection was empty
            return
        val['molModes'] = self.molModes
        apply(self.doitWrapper, (self.nodes,), val)


class ExtrudeSecondaryStructureCommand(MVCommand):
    """The ExtrudeCommand allows the user to represent the secondary structure elements by extruding 2D geometries along a 3D path.To execute this command use the entry 'extrude Secondary Structure' under the 'Compute' menu in the menu bar. 
   The panel that appears lets the user choose the 2D shapes for the extrusion. The entry 'default' in the listChooser lets do a traditional ribbon representation.nbchords represents the number of points in the path3D corresponding to one residue. The higher this parameter is the smoother the extruded geometries will look.gapBeg allows the user to introduce a gap of gapBeg points the extruded geometrie before each residues.gapEnd allows the user to introduce a gap of gapEnd points the extruded geometrie after each residues.The value of this two parameters depend on the value of the nbchords parameter and on each other's value.Once you clique OK on this panel another panel appears to let the user caracterize the chosen 2D geometry.Once the user chose all the parameters an ExtrudeSSElt object is created for each secondary structure element. The geometries associated to each secondary structure element are then updated with the new vertices and faces.Finally the displaySSCommand is executed.This command has the objArgsOnly flag.
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : ExtrudeSecondaryStructureCommand
    \nCommand name : extrudeSecondaryStructure
    \nSynopsis:\n
            None <--- extrudeSecondaryStructure(nodes, shape1=None, shape2=None,frontcap=1, endcap=True, arrow=True, nbchords=8, gapBeg=False,gapEnd=False, larrow=2, display=True,**kw)
    \nRequired Arguments:\n    
        nodes ---  TreeNodeSet holding the current selection(mv.getSelection())
    \nOptional Arguments:\n    
        shape1 &
        shape2 --- DejaVu.Shapes.Shape2D objects. shape1 will be used to
                  represent the helix and strand, shape2 to represent coils and
                  turns.
        \nfrontcap &
        endcap   --- Boolean flag when set to True a  cap will be added to the
                   geom either at the front or at the end
        \narrow  --- Boolean flag when set to True an arow will be added to the
                   geometry representing the strand.
        \nnbchords --- Nb of points per residues in the smooth array
        \ngapBeg&  
        gapEnd  --- defines gap at the beginning or the end of each residue.
        \nlarrow  --- lenth of the arrow if arrow boolean flag set to 1
        \ndisplay  --- Boolean flag when set to True the displaySecondaryStructure
                   is called automatically
    """

    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly


    def pickedVerticesToAtoms(self, geom, vertInd):
        """
        This function gets called when a picking or drag select event has
        happened. It gets called with a geometry and the list of vertex
        indices of that geometry that have been picked.
        This function is in charge of turning these indices into an AtomSet
        This function takes the following arguments:
        geom   : geometry picked, instance of a class derived from DejaVu.Geom
                 (IndexedPolygons, IndexedPolylines.....)
        vertInd: list of integer representing the indices of the picked
                 vertices in the given geometry geom. 
        """

        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet
        ss = geom.SS
        l = []
        for vi in vertInd:
            resInd = ss.exElt.getResIndexFromExtrudeVertex( vi )
            try:
                l.append(ss.children[int(resInd)].atoms.get('CA')[0])
            except:
                l.append(ss.children[int(resInd)].atoms[0])
        return AtomSet( AtomSet( l ) )


    def atomPropToVertices(self, geom, residues, propName, propIndex=None):
        """Function called to compute the array of properties"""
        if residues is None or len(residues)==0 : return None
        propVect = []
        if not propIndex is None:
            propIndex = 'secondarystructure'
        for r in residues:
            try:
                prop = getattr(r.atoms.get('CA')[0], propName)
            except  IndexError:
                prop = getattr(r.atoms[0], propName)
            if not propIndex is None:
                propVect.append(prop[propIndex])
            else:
                propVect.append(prop)
        geom.SS.exElt.setResProperties(propVect, propName, residues)
        properties = geom.SS.exElt.getExtrudeProperties( residues, propName )
        return properties


    def onAddObjectToViewer(self, obj):
        # private flag to specify whether or not the geometries for the SS
        # have been created.
        obj.__hasSSGeom = 0
        if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
            self.vf.dashboard.resetColPercent(obj, '_showRibbonStatus')


    def createGeometries(self, obj):
        if obj.__hasSSGeom :
            return
        from DejaVu.Geom import Geom
        geomC = obj.geomContainer

        if not geomC.geoms.has_key('secondarystructure'):
            
            t = Geom('secondarystructure', shape=(0,0), protected=True)
            geomC.addGeom( t, parent=geomC.masterGeom, redo=0 ) 
        else:
            t = geomC.geoms['secondarystructure']
        
        for a in obj.allAtoms:
            a.colors['secondarystructure']=(1.,1.,1.)
            a.opacities['secondarystructure']=1.

        for c in obj.chains:
            if not hasattr(c, 'secondarystructureset'):
                continue
            for ss in c.secondarystructureset:
                name = "%s%s"%(ss.name, ss.chain.id)
                g = IndexedPolygons(name, visible=0, pickableVertices=1, protected=True,)
                if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                    g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
                #g.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
                #g.Set(frontPolyMode=GL.GL_FILL,redo=0)

                g.SS = ss
                
                geomC.atomPropToVertices[name] = self.atomPropToVertices
                geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
                geomC.geomPickToBonds[name] = None
                geomC.addGeom(g, parent=t, redo=0 )
                self.managedGeometries.append(g)
                #geomC.addGeom(g,self,parent=t, redo=0 )
                geomC.atoms[name] = ResidueSet()
                
                
        obj.__hasSSGeom = 1

    def onAddCmdToViewer(self):
        self.vf.loadCommand("secondaryStructureCommands",
                            "computeSecondaryStructure", "Pmv",
                            topCommand = 0)

        self.vf.loadCommand("secondaryStructureCommands",
                            "displayExtrudedSS", "Pmv",
                            topCommand = 0)

        self.vf.loadCommand("extrusionCommands",
                            "computeSheet2D", "Pmv",
                            topCommand = 0)
            
        self.vf.loadCommand("extrusionCommands",
                            "Nucleic_Acids_properties", "Pmv",
                            topCommand = 0)
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('computeSecondaryStructure'):
##             self.vf.loadCommand("secondaryStructureCommands",
##                                 "computeSecondaryStructure", "Pmv",
##                                 topCommand = 0)
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('displayExtrudedSS'):
##             self.vf.loadCommand("secondaryStructureCommands",
##                                 "displayExtrudedSS", "Pmv",
##                                 topCommand = 0)
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('computeSheet2D'):
##             self.vf.loadCommand("extrusionCommands",
##                                 "ComputeSheet2D", "Pmv",
##                                 topCommand = 0)
                
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('Nucleic_Acids_properties'):
##             self.vf.loadCommand("extrusionCommands",
##                                 "Nucleic_Acids_properties", "Pmv",
##                                 topCommand = 0)

    def clean(self, obj):
        if not hasattr(obj, 'chains'): return
        for c in obj.chains:
            if hasattr(c, 'residuesInSS'):
                delattr(c, 'residuesInSS')

            if not hasattr(c, 'secondarystructureset'):
                continue
            for ss in c.secondarystructureset:
                # Have to remove specifically geoms.SS and geoms.mol
                # from the geomContainer and the viewer
                g = obj.geomContainer.geoms[ss.name+c.id]
                del(g.SS)
                del(g.mol)
                g.Set(visible=0, tagModified=False)
                g.protected = False
                if self.vf.hasGui:
                    self.vf.GUI.VIEWER.RemoveObject(g)
                del obj.geomContainer.geoms[ss.name+c.id]
                del obj.geomContainer.atoms[ss.name+c.id]
        obj.__hasSSGeom=0


    def onRemoveObjectFromViewer(self, obj):
        if self.vf.undoableDelete__: return
        if not hasattr(obj, 'chains'): return
        for c in obj.chains:
            if hasattr(c, 'residuesInSS'):
                delattr(c, 'residuesInSS')

            if not hasattr(c, 'secondarystructureset'):
                continue
            for ss in c.secondarystructureset:
                # Have to remove specifically geoms.SS and geoms.mol
                # from the geomContainer and the viewer
                g = obj.geomContainer.geoms[ss.name+c.id]
                del(g.SS)
                del(g.mol)
                g.Set(visible=0, tagModified=False)
                g.protected = False
                self.vf.GUI.VIEWER.RemoveObject(g)
                del obj.geomContainer.geoms[ss.name+c.id]
                del obj.geomContainer.atoms[ss.name+c.id]
        obj.__hasSSGeom=0

    def __call__(self, nodes, shape1=None, shape2=None, frontcap=True,
                 endcap=True, arrow=True, nbchords=8, gapBeg=0, gapEnd=0,
                 larrow=2, display=True, **kw):
        """None<---extrudeSecondaryStructure(nodes,shape1=None,shape2=None,frontcap=1,endcap=True,arrow=True, nbchords=8,gapBeg=False,gapEnd=False,larrow=2,display=True,**kw)
        \nRequired Arguments:\n
        nodes ---  TreeNodeSet holding the current selection
                   (mv.getSelection())
        \nOptional Arguments:\n
        shape1 &
        shape2 --- DejaVu.Shapes.Shape2D objects. shape1 will be used to
                  represent the helix and strand, shape2 to represent coils and
                  turns.
        \nfrontcap &
        endcap --- Boolean flag when set to True a  cap will be added to the
                   geom either at the front or at the end
        \narrow --- Boolean flag when set to True an arow will be added to the
                   geometry representing the strand.
        \nnbchords --- Nb of points per residues in the smooth array
        \ngapBeg&  
        gapEnd --- defines gap at the beginning or the end of each residue.
        \nlarrow  --- length of the arrow if arrow boolean flag set to 1
        \ndisplay --- Boolean flag when set to True the displaySecondaryStructure
                   is called automatically """

        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        kw['shape1'] = shape1
        kw['shape2'] = shape2
        kw['frontcap'] = frontcap
        kw['endcap'] = endcap
        kw['arrow'] = arrow
        kw['nbchords'] = nbchords
        kw['gapBeg'] = gapBeg
        kw['gapEnd'] = gapEnd
        kw['larrow'] = larrow
        kw['display'] = display
        #print "kw.has_key('only')=", kw.has_key('only')
        #print kw.get('only', 'no_value')
        apply(self.doitWrapper, (nodes,), kw)
        

    def doit(self, nodes, shape1=None, shape2=None, frontcap=True, endcap=True,
             arrow=True, nbchords=8, gapBeg=0, gapEnd=0, larrow = 2,
             display=True, updateNucleicAcidsPropertiesGUI=False, **kw):
        """ nodes, shape1, shape2=None, frontcap=True, endcap=True, arrow=True,
        nbchords=8, gapBeg=0, gapEnd=1, display=True"""
        #print "2: kw.has_key('only')=", kw.has_key('only'), ':', 
        #print kw.get('only', 'no_value')
        shape1o = shape1
        shape2o = shape2
        
        if not type(nbchords)==IntType:
            print "invalid parameter nbchords:", nbchords
            return 
        if gapEnd>len(nodes):
            print "invalid parameter gapEnd:", gapEnd
            return 
        if gapBeg>len(nodes):
            print "invalid parameter gapBeg:", gapBeg
            return 

        molecules, residueSets = self.vf.getNodesByMolecule(nodes, Residue)
        if len(molecules)==0: return
        if shape1 is None:
            shape1 = Rectangle2D(width=1.2, height=0.2, vertDup=1)
            shape2 = Circle2D(radius=0.1)

        # highlight selection
        selMols, selResidues = self.vf.getNodesByMolecule(self.vf.selection,
                                                          Residue)
        molSelectedResiduesDict = dict( zip( selMols, selResidues) )
        # Create a sheet2 object.
        for mol, residues in map(None, molecules, residueSets):
            if not mol.hasSS:
                # Compute the secondarystructure if not there
                self.vf.computeSecondaryStructure(mol, topCommand=0)
            if not hasattr(mol,'__hasSSGeom') or not mol.__hasSSGeom:
                # Need here to change
                self.createGeometries(mol)
            reswithss = residues.get(lambda x:
                                     hasattr(x, 'secondarystructure'))
            if reswithss is None:
                print 'no secondary structure in that selection'
                continue

            selectionSS = reswithss.secondarystructure.uniq()
            chains = residues.parent.uniq()

            # highlight selection
            if molSelectedResiduesDict.has_key(mol) and len(molSelectedResiduesDict[mol]) > 0:
                lHighlight = True
            else:
                lHighlight = False

            for i in range(len(chains)):
                chain = chains[i]
                chain.ssExtrusionParams = { # used to save session
                    'shape1' : shape1o,
                    'shape2' : shape2o,
                    'frontcap' : frontcap,
                    'endcap' : endcap,
                    'arrow' : arrow,
                    'nbchords' : nbchords,
                    'gapBeg' : gapBeg,
                    'gapEnd' : gapEnd,
                    'larrow' : larrow
                    }
                newsheet = 0
                if not hasattr(chain, 'sheet2D'):
                    chain.sheet2D = {}
                if not hasattr(chain,'secondarystructureset'):
                    print 'no secondary structure set for chain: %s !'%chain.id
                    chain.sheet2D['ssSheet2D'] = None
                    continue
                
                ssSet = chain.secondarystructureset
                
                # 1- Check if the sheet2D for a secondary structure has been
                # computed already.
                if chain.sheet2D.has_key('ssSheet2D'):
                    if chain.sheet2D['ssSheet2D'] is None:
                        newsheet = 0
                        continue
                    elif chain.sheet2D['ssSheet2D'].chords != nbchords:
                        rt = chain.ribbonType()
                        if rt=='NA':
                            ExtrudeNA(chain)
                            newsheet = 1
                        elif rt=='AA':
                            self.vf.computeSheet2D(chain, 'ssSheet2D',
                               'CA','O', buildIsHelix=1,
                               nbchords=nbchords,
                               topCommand=0,log=0)
                            newsheet = 1
                        else:
                            newsheet = 0
                    else:
                        newsheet = 0
                    
                elif not chain.sheet2D.has_key('ssSheet2D'):
                    rt = chain.ribbonType()
                    if rt=='NA':
                        ExtrudeNA(chain)
                        newsheet = 1
                    elif rt=='AA':
                        self.vf.computeSheet2D(chain, 'ssSheet2D',
                                               'CA', 'O',buildIsHelix=1,
                                               nbchords=nbchords,
                                               topCommand=0,log=0)
                        newsheet = 1
                    else:
                        newsheet = 0
                        
                if newsheet:
                    sd = chain.sheet2D['ssSheet2D']
                    # then create a pointer to the sheet2D for each secondary structures.
                    ssSet.sheet2D = sd
                    if sd is None : continue
                # Do the extrusion ONLY for the ss having a residue in the
                # selection
                removeSS =[]
                #from Pmv.selectionCommands import sets__
                for SS in ssSet:
                    # test here if all the residues of the sselt are
                    # in the residue set used
                    # to compute the sheet2D. if not remove the ss.
                    if SS.sheet2D is None:
                        continue
                    if filter(lambda x, rs = SS.sheet2D.resInSheet:
                              not x in rs, SS.residues):
                        print "WARNING: Removing %s from secondary structure set. One or more residues \
doesn't have CA and O"%SS.name
                        # remove the SS from the set and etc....
                        #delattr(SS.residues, 'secondarystructure')
                        #ssSet.remove(SS)
                        removeSS.append(SS)
                        name = "%s%s"%(SS.name, SS.chain.id)
                        setName = mol.name+':'+name[-1]+':'+name[:-1]
                        if self.vf.sets.has_key(setName):
                            del self.vf.sets[setName]
                        #del sets__[mol.name+':'+name[-1]+':'+name[:-1]]
                        g = mol.geomContainer.geoms[name]
                        g.protected = False
                        if self.vf.hasGui:self.vf.GUI.VIEWER.RemoveObject(g)
                        continue
                    name = "%s%s"%(SS.name, SS.chain.id)
                    
                    if not SS in selectionSS:
                        continue
                    if isinstance(SS, Strand):
                        arrowf = arrow
                    else:
                        arrowf = 0
                    if not shape2 is None:
                        if SS.__class__.__name__ in ['Strand', 'Helix']:
                            SS.exElt = ExtrudeSSElt(
                                SS, shape1, gapEnd , gapBeg, frontcap, endcap,
                                arrowf,larrow)
                        elif SS.__class__.__name__ in ['Coil', 'Turn']:
                            rt = chain.ribbonType()
                            if rt=='NA':
                                NAp = self.vf.Nucleic_Acids_properties
                                sc = max(NAp.scale_pyrimidine, NAp.scale_purine)
                                #shape2 = Circle2D(radius=sc/2.5)
                                shape3 = Circle2D(radius=sc/5.)
                                SS.exElt = ExtrudeSSElt(
                                    SS, shape3, gapEnd, gapBeg, frontcap,
                                    endcap, arrowf)
                            elif rt=='AA':
                                SS.exElt = ExtrudeSSElt(
                                    SS, shape2, gapEnd, gapBeg, frontcap,
                                    endcap, arrowf)

                    else:
                        SS.exElt = ExtrudeSSElt(SS, shape1, gapEnd , gapBeg,
                                                frontcap, endcap, arrowf,
                                                larrow)
                    resfaces, resfacesDict = SS.exElt.getExtrudeResidues(SS.residues)
                    g = mol.geomContainer.geoms[name]
##                     # MS triangulate faces
##                     trifaces = []
##                     for f in resfaces:
##                         trifaces.append( (f[0],f[1],f[3]) )
##                         if f[2]!=f[3]:
##                             trifaces.append( (f[1],f[2],f[3]) )

                    # highlight selection
                    g.resfacesDict = resfacesDict
                    highlight = []
                    if lHighlight is True:# and chain in residueSet :
                        highlight = [0]*len(SS.exElt.vertices)
                        for lResidue in molSelectedResiduesDict[mol]:
                            if resfacesDict.has_key(lResidue):
                                for lFace in resfacesDict[lResidue]:
                                    for lVertexIndex in lFace:
                                        highlight[int(lVertexIndex)] = 1

                    g.Set(vertices=SS.exElt.vertices,
                          highlight=highlight,
                          faces = resfaces,
##                          faces=trifaces,
                          vnormals=SS.exElt.vnormals, redo=0,
                          tagModified=False)

                    if chain.ribbonType()=='NA':
                        geom_bases = Add_Nucleic_Bases(
                            g, self.vf.Nucleic_Acids_properties)
                        if self.vf.hasGui:
                            self.vf.GUI.VIEWER.AddObject(geom_bases, parent=g)
                        else:
                            g.children.append(geom_bases)
                            geom_bases.parent = g
                            #geom_bases.fullName = g.fullName+'|'+geom_bases.name
                for SS in removeSS:
                    delattr(SS.residues, 'secondarystructure')
                    ssSet.remove(SS)

        if display:
            kw['topCommand'] = 0
            if kw.get('only', 0):
                kw['only'] = 1
            kw['setupUndo'] = 1
            #print "calling displayExtrudedSS with ", kw
            apply(self.vf.displayExtrudedSS,(nodes,),  kw)
#            gg = g.viewer.FindObjectByName('root|1dwb_0|secondarystructure|Coil1L')
#            print 'AFTER DISPLAY', gg
            #self.vf.displayExtrudedSS(nodes, setupUndo=1, topCommand=0)

        redraw = False
        if kw.has_key("redraw") : redraw=True
        event = EditGeomsEvent(
            'SSextrude', [nodes,[shape1, shape2, frontcap, endcap,
                                 arrow, nbchords, gapBeg, gapEnd, larrow,
                                 display, updateNucleicAcidsPropertiesGUI]])
        self.vf.dispatchEvent(event)

        
    def gapValidateFunction(self, gapVal,*validateArgs):
        """ Function to test if the value of the gap is correct. Its has
        to take for arguments the value of the entry you are testing
        and a list of arguments. Here the list has only one argument
        the value number of chords."""
        chordVal = validateArgs[0]
        if gapVal < int(chordVal.get()):
            return 1
        else:
            return 0

    def buildFormDescr(self, formName):
        if formName == 'geomChooser':
            nbchordEntryVar = StringVar()
            idf = InputFormDescr(title ="Choose a shape :")
        
            entries = [('default',None),('rectangle',None),
                       ('circle',None), ('ellipse',None),
                       ('square',None),('triangle',None),
                       #('other', None)
                       ]

            idf.append({'name':'shape',
                        'widgetType':ListChooser,
                        'defaultValue':'default',
                        'wcfg':{'entries': entries,
                                'title':'Choose a shape'}
                        })
            
            idf.append( {'name': 'nbchords',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'nb. Pts Per Residue:  ',
                                 'minval':4,'maxval':15, 'incr': 1, 'init':8,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'textvariable':nbchordEntryVar,
                                              'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })

            idf.append( {'name': 'gapBeg',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'validateFunc':self.gapValidateFunction,
                         'validateArgs':(nbchordEntryVar,'GapEnd'),
                         'wcfg':{'label': 'Gap Before Residue',
                                 'minval':0,'maxval':5, 'incr': 1, 'init':0,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })
            
            idf.append( {'name': 'gapEnd',
                         'widgetType':ExtendedSliderWidget,'type':int,
                         'validateFunc':self.gapValidateFunction,
                         'validateArgs':(nbchordEntryVar,'GapBeg'),
                         'wcfg':{'label': 'Gap After Residue',
                                 'minval':0,'maxval':5, 'incr': 1, 'init':0 ,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })
        else:
            initRadius = 0.1
            radiusWidgetDescr = {'name': 'radius',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Radius',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initRadius,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initWidth = 1.2
            widthWidgetDescr =  {'name': 'width',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Width',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initWidth,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initHeight = 0.2
            heightWidgetDescr = {'name': 'height',
                                 'widgetType':ExtendedSliderWidget,
                                 'wcfg':{'label': 'Height',
                                         'minval':0.05,'maxval':3.0 ,
                                         'init':initHeight,
                                         'labelsCursorFormat':'%1.2f',
                                         'sliderType':'float' ,
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                             }
            initLarrow = 2
            larrowWidgetDescr = {'name': 'larrow',
                                 'widgetType':ExtendedSliderWidget,
                                 'type':int,
                                 'wcfg':{'label':'length of the arrow:',
                                         'minval':0,'maxval':4, 'incr': 1,
                                         'init':initLarrow,
                                         'labelsCursorFormat':'%d',
                                         'sliderType':'int',
                                         'entrywcfg':{'width':4},
                                         'entrypackcfg':{'side':'right'}},
                                 'gridcfg':{'columnspan':2,'sticky':'we'}
                                 }
            initSide = 1.0
            sideWidgetDescr = {'name': 'sidelength',
                               'widgetType':ExtendedSliderWidget,
                               'wcfg':{'label': 'Length of side:',
                                       'minval':0.05,'maxval':3.0 ,
                                       'init':initSide,
                                       'labelsCursorFormat':'%1.2f',
                                       'sliderType':'float',
                                       'entrywcfg':{'width':4},
                                       'entrypackcfg':{'side':'right'}},
                               'gridcfg':{'columnspan':2,'sticky':'we'}
                               }
            
            frontCapWidgetDescr = {'name':'frontcap',
                                   'widgetType':Checkbutton,
                                   'defaultValue':1,
                                   'wcfg':{'text':'front cap',
                                           'variable': IntVar()},
                                   'gridcfg':{'sticky':'we'}}
            endCapWidgetDescr = {'name':'endcap',
                                 'widgetType':Checkbutton,
                                 'defaultValue':1,
                                 'wcfg':{'text':'end cap ',
                                         'variable': IntVar()},
                                 'gridcfg':{'sticky':'we','row':-1}}
            

            if formName == 'default':
                idf = InputFormDescr(title ="Options :")
                idf.append(radiusWidgetDescr)
                idf.append(widthWidgetDescr)
                idf.append(heightWidgetDescr)
                idf.append(larrowWidgetDescr)

            elif formName == 'rectangle':
                idf = InputFormDescr(title ="Rectangle size :")
                idf.append(widthWidgetDescr)
                initHeight = 0.4
                idf.append(heightWidgetDescr)
                larrowInit = 0
                idf.append(larrowWidgetDescr)

            elif formName == 'circle':
                idf = InputFormDescr(title="Circle size :")
                idf.append(radiusWidgetDescr)

            elif formName == 'ellipse':
                idf = InputFormDescr(title="Ellipse size")
                idf.append( {'name': 'grand',
                             'widgetType':ExtendedSliderWidget,
                             'wcfg':{'label': 'demiGrandAxis',
                                     'minval':0.05,'maxval':3.0 ,
                                     'init':0.5,
                                     'labelsCursorFormat':'%1.2f',
                                     'sliderType':'float',
                                     'entrywcfg':{'width':4},
                                     'entrypackcfg':{'side':'right'}},
                             'gridcfg':{'columnspan':2,'sticky':'we'}
                             })
                idf.append( {'name': 'small',
                             'widgetType':ExtendedSliderWidget,
                             'wcfg':{'label': 'demiSmallAxis',
                                     'minval':0.05,'maxval':3.0 ,
                                     'init':0.2,
                                     'labelsCursorFormat':'%1.2f',
                                     'sliderType':'float',
                                     'entrywcfg':{'width':4},
                                     'entrypackcfg':{'side':'right'}},
                             'gridcfg':{'columnspan':2,'sticky':'we'}
                             })
            elif formName == 'square':
                idf = InputFormDescr(title="Square size :")
                idf.append(sideWidgetDescr)
                initLarrow = 0
                idf.append(larrowWidgetDescr)

            elif formName == 'triangle':
                idf = InputFormDescr(title="Triangle size :")
                idf.append(sideWidgetDescr)
                
                
            # These widgets are present in everyInputForm.
            idf.append(frontCapWidgetDescr)
            idf.append(endCapWidgetDescr)

        return idf


    def guiCallback(self, do=True):
        nodes = self.vf.getSelection()
        gotNAParams = gotAAParams = False
        typeshape = None
        for chain in nodes.findType(Chain):
            ctype = chain.ribbonType()

            if ctype=='NA' and not gotNAParams:
                typeshape = self.vf.Nucleic_Acids_properties.guiCallback()
                if typeshape=={}: return # NA options was 'Cancel'
                gotNAParams = True
                val = {}
                
            elif ctype=='AA' and not gotAAParams:
                typeshape = self.showForm('geomChooser')
                if (typeshape=={} or typeshape['shape']==[]):
                    return # AA extrusion options were 'Cancel'
                gotAAParams = True

                nbchords = typeshape['nbchords']
                gapBeg =  typeshape['gapBeg']
                gapEnd = typeshape['gapEnd']

                if typeshape['shape'][0]=='default':
                    val = self.showForm('default')
                    if val:
                        val['shape1'] = Rectangle2D(val['width'],val['height'],
                                                    vertDup=1)
                        val['shape2'] = Circle2D(radius=val['radius'])
                        del val['width']
                        del val['height']
                        del val['radius']

                        val['frontcap'] = int(val['frontcap'])
                        val['endcap'] = int(val['endcap'])

                        if val['larrow']!=0:
                            val['arrow'] = 1
                        else:
                            val['arrow'] = 0

                elif typeshape['shape'][0]=='rectangle':
                    val = self.showForm('rectangle')
                    if val:
                        val['shape1'] = Rectangle2D(width=val['width'],
                                                    height=val['height'],
                                                    vertDup=1)
                        del val['height']
                        del val['width']
                        val['shape2'] = None
                        val['frontcap'] = int(val['frontcap'])
                        val['endcap'] = int(val['endcap'])
                        if val['larrow']!=0:
                            val['arrow'] = 1
                        else:
                            val['arrow'] = 0

                elif typeshape['shape'][0]=='circle':
                    val = self.showForm('circle')
                    if val:
                        val['shape1'] = Circle2D(radius=val['radius'])
                        del val['radius']
                        val['shape2'] = None

                        val['frontcap'] = int(val['frontcap'])
                        val['endcap'] = int(val['endcap'])
                        val['arrow'] = 0

                elif typeshape['shape'][0]=='ellipse':
                    val = self.showForm('ellipse')
                    if val:
                        val['shape1'] = Ellipse2D(demiGrandAxis= val['grand'],
                                                  demiSmallAxis=val['small'])
                        del val['grand']
                        del val['small']
                        val['shape2'] = None
                        val['frontcap'] = int(val['frontcap'])
                        val['endcap'] = int(val['endcap'])
                        val['arrow'] = 0

                elif typeshape['shape'][0]=='square':
                    val = self.showForm('square')
                    if val:
                        val['shape1'] = Square2D(side=val['sidelength'], vertDup=1)
                        del val['sidelength']
                        val['shape2'] = None
                        val['frontcap'] = int(val['frontcap'])
                        val['endcap'] = int(val['endcap'])
                        if val['larrow']!=0:
                            val['arrow'] = 1
                        else:
                            val['arrow'] = 0

                elif typeshape['shape'][0]=='triangle':
                    val = self.showForm('triangle')
                    if val:
                        val['shape1'] = Triangle2D(side=val['sidelength'], vertDup=1)
                        del val['sidelength']
                        val['shape2'] = None
                        val['frontcap'] = int(val['frontcap'])
                        val['endcap'] = int(val['endcap'])

                        val['arrow'] = 0

        ##              draw = DrawShape(self.vf.GUI.ROOT)
        ##              val = draw.go()
        ##              if not val[0] or not val[1]: return
        ##              if val:
        ##                  shape1 = Shape2D(val[0], val[1], val[2])
        ##                  shape2 = None
        ##                  arrow, cap1, cap2 = 1, val[3], val[4]
                #elif not gotNAParams: return

            if gotAAParams and gotNAParams:
                break

        if not do:  # what is that used for ?? MS
            return val

        if typeshape:
            if val.has_key('arrow') and not val['arrow']:
                val['larrow'] = 0
            else:
                val['larrow'] = int((val['larrow']*nbchords)/4.)
            val['gapBeg'] = gapBeg
            val['gapEnd'] = gapEnd
            val['nbchords'] = nbchords

        apply(self.doitWrapper, (self.vf.getSelection(),), val)



class ExtrudeSecondaryStructureCommandUnic(ExtrudeSecondaryStructureCommand):
    """The ExtrudeCommand allows the user to represent the secondary structure 
	elements by extruding 2D geometries along a 3D path.To execute this command use 
	the entry 'extrude Secondary Structure' under the 'Compute' menu in the menu bar. 
   The panel that appears lets the user choose the 2D shapes for the extrusion. 
   The entry 'default' in the listChooser lets do a traditional ribbon representation.
   nbchords represents the number of points in the path3D corresponding to one residue. 
   The higher this parameter is the smoother the extruded geometries will look.
   gapBeg allows the user to introduce a gap of gapBeg points the extruded geometrie before each residues.
   gapEnd allows the user to introduce a gap of gapEnd points the extruded geometrie after each residues.
   The value of this two parameters depend on the value of the nbchords parameter and on each other's value.
   Once you clique OK on this panel another panel appears to let the user caracterize the chosen 2D geometry.
   Once the user chose all the parameters an ExtrudeSSElt object is created for each secondary structure element. 
   A unic geometries for all secondary structure element are then updated with the new vertices and faces.
   Finally the displaySSCommand is executed.This command has the objArgsOnly flag.
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : ExtrudeSecondaryStructureCommand
    \nCommand name : extrudeSecondaryStructure
    \nSynopsis:\n
            None <--- extrudeSecondaryStructure(nodes, shape1=None, shape2=None,frontcap=1, endcap=True, arrow=True, nbchords=8, gapBeg=False,gapEnd=False, larrow=2, display=True,**kw)
    \nRequired Arguments:\n    
        nodes ---  TreeNodeSet holding the current selection(mv.getSelection())
    \nOptional Arguments:\n    
        shape1 &
        shape2 --- DejaVu.Shapes.Shape2D objects. shape1 will be used to
                  represent the helix and strand, shape2 to represent coils and
                  turns.
        \nfrontcap &
        endcap   --- Boolean flag when set to True a  cap will be added to the
                   geom either at the front or at the end
        \narrow  --- Boolean flag when set to True an arow will be added to the
                   geometry representing the strand.
        \nnbchords --- Nb of points per residues in the smooth array
        \ngapBeg&  
        gapEnd  --- defines gap at the beginning or the end of each residue.
        \nlarrow  --- lenth of the arrow if arrow boolean flag set to 1
        \ndisplay  --- Boolean flag when set to True the displaySecondaryStructure
                   is called automatically
    """

    def __init__(self):
        ExtrudeSecondaryStructureCommand.__init__(self)

    def createGeometries(self, obj):
        if hasattr(obj,'__hasSSGeom') :
            return
        from DejaVu.Geom import Geom
        geomC = obj.geomContainer
        if not geomC.geoms.has_key('SS'):
            
            t = Geom('SS', shape=(0,0), protected=True)
            geomC.addGeom( t, parent=geomC.masterGeom, redo=0 ) 
        else:
            t = geomC.geoms['SS']
        
        for a in obj.allAtoms:
            a.colors['SS']=(1.,1.,1.)
            a.opacities['SS']=1.
        for c in obj.chains:
            #if not hasattr(c, 'secondarystructureset'):
            #    continue
            #for ss in c.secondarystructureset:
                name = "SS%s"%(c.id)
                g = IndexedPolygons(name, visible=0, pickableVertices=1, protected=True,)
                if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                    g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
                g.Set(frontPolyMode=GL.GL_FILL)

                #g.SS = ss
                
                geomC.atomPropToVertices[name] = self.atomPropToVertices
                geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
                geomC.geomPickToBonds[name] = None
                geomC.addGeom(g, parent=t, redo=0 )
                self.managedGeometries.append(g)
                #geomC.addGeom(g,self,parent=t, redo=0 )
                geomC.atoms[name] = ResidueSet()
                atoms = c.findType(Atom)
                for a in atoms:
                    a.colors[name]=(1.,1.,1.)
                    a.opacities[name]=1.								
                for ss in c.secondarystructureset:
                    sname = "%s%s"%(ss.name, ss.chain.id)
                    geomC.atoms[sname] = ResidueSet()               
        obj.__hasSSGeom = 1

    def doit(self, nodes, shape1=None, shape2=None, frontcap=True, endcap=True,
             arrow=True, nbchords=8, gapBeg=0, gapEnd=0, larrow = 2,
             display=True, updateNucleicAcidsPropertiesGUI=False, **kw):
        """ nodes, shape1, shape2=None, frontcap=True, endcap=True, arrow=True,
        nbchords=8, gapBeg=0, gapEnd=1, display=True"""
        #print "2: kw.has_key('only')=", kw.has_key('only'), ':', 
        #print kw.get('only', 'no_value')

        if not type(nbchords)==IntType:
            print "invalid parameter nbchords:", nbchords
            return 
        if gapEnd>len(nodes):
            print "invalid parameter gapEnd:", gapEnd
            return 
        if gapBeg>len(nodes):
            print "invalid parameter gapBeg:", gapBeg
            return 

        molecules, residueSets=self.vf.getNodesByMolecule(nodes, Residue)
        if len(molecules)==0: return
        if shape1 is None:
            shape1 = Rectangle2D(width=1.2, height=0.2, vertDup=1)
            shape2 = Circle2D(radius=0.1)

        # highlight selection
        selMols, selResidues = self.vf.getNodesByMolecule(self.vf.selection, Residue)
        molSelectedResiduesDict = dict( zip( selMols, selResidues) )

        # Create a sheet2 object.
        for mol, residues in map(None, molecules, residueSets):
            if not mol.hasSS:
                # Compute the secondarystructure if not there
                self.vf.computeSecondaryStructure(mol, topCommand=0)
            if not hasattr(mol,'__hasSSGeom') or not mol.__hasSSGeom:
                # Need here to change
                self.createGeometries(mol)
            reswithss = residues.get(lambda x:
                                     hasattr(x, 'secondarystructure'))
            if reswithss is None:
                print 'no secondary structure in that selection'
                continue

            selectionSS = reswithss.secondarystructure.uniq()
            chains = residues.parent.uniq()

            # highlight selection
            if molSelectedResiduesDict.has_key(mol) and len(molSelectedResiduesDict[mol]) > 0:
                lHighlight = True
            else:
                lHighlight = False

            for i in range(len(chains)):
                chain = chains[i]
                newsheet = 0
                if not hasattr(chain, 'sheet2D'):
                    chain.sheet2D = {}
                
                if not hasattr(chain,'secondarystructureset'):
                    print 'no secondary structure set for chain: %s !'%chain.id
                    chain.sheet2D['ssSheet2D'] = None
                    continue
                
                ssSet = chain.secondarystructureset
                # 1- Check if the sheet2D for a secondary structure has been
                # computed already.
                if chain.sheet2D.has_key('ssSheet2D'):
                    if chain.sheet2D['ssSheet2D'] is None:
                        newsheet = 0
                        continue
                    elif chain.sheet2D['ssSheet2D'].chords != nbchords:
                        rt = chain.ribbonType()
                        if rt=='NA':
                            ExtrudeNA(chain)
                            newsheet = 1
                        elif rt=='AA':
                            self.vf.computeSheet2D(chain, 'ssSheet2D',
                               'CA','O', buildIsHelix=1,
                               nbchords=nbchords,
                               topCommand=0,log=0)
                            newsheet = 1
                        else:
                            newsheet = 0
                    else:
                        newsheet = 0
                    
                elif not chain.sheet2D.has_key('ssSheet2D'):
                    rt = chain.ribbonType()
                    if rt=='NA':
                        ExtrudeNA(chain)
                        newsheet = 1
                    elif rt=='AA':
                        self.vf.computeSheet2D(chain, 'ssSheet2D',
                                               'CA', 'O',buildIsHelix=1,
                                               nbchords=nbchords,
                                               topCommand=0,log=0)
                        newsheet = 1
                    else:
                        newsheet = 0
                if newsheet:
                    sd = chain.sheet2D['ssSheet2D']
                    # then create a pointer to the sheet2D for each secondary structures.
                    ssSet.sheet2D = sd
                    if sd is None : continue
                # Do the extrusion ONLY for the ss having a residue in the
                # selection
                removeSS =[]
                faces=[]
                vertices=[]	
                normals=[]							
                #from Pmv.selectionCommands import sets__
                name = "SS"+chain.id
                g = mol.geomContainer.geoms[name]
                for SS in ssSet:
                    # test here if all the residues of the sselt are
                    # in the residue set used
                    # to compute the sheet2D. if not remove the ss.
                    if SS.sheet2D is None:
                        continue
                    if filter(lambda x, rs = SS.sheet2D.resInSheet:
                              not x in rs, SS.residues):
                        print "WARNING: Removing %s from secondary structure set. One or more residues \
doesn't have CA and O"%SS.name
                        
                        # remove the SS from the set and etc....
                        #delattr(SS.residues, 'secondarystructure')
                        #ssSet.remove(SS)
                        removeSS.append(SS)
                        #name = "%s%s"%(SS.name, SS.chain.id)
                        #del self.vf.sets[mol.name+':'+name[-1]+':'+name[:-1]]
                        #del sets__[mol.name+':'+name[-1]+':'+name[:-1]]
                        #g = mol.geomContainer.geoms[name]
                        #g.protected = False
                        #if self.vf.hasGui:self.vf.GUI.VIEWER.RemoveObject(g)
                        continue
                    name = "%s%s"%(SS.name, SS.chain.id)
                    
                    if not SS in selectionSS:
                        continue
                    if isinstance(SS, Strand):
                        arrowf = arrow
                    else:
                        arrowf = 0
                    if not shape2 is None:
                        if SS.__class__.__name__ in ['Strand', 'Helix']:
                            SS.exElt = ExtrudeSSElt(SS,shape1,gapEnd ,
                                                    gapBeg, frontcap, endcap,
                                                    arrowf,larrow)
                        elif SS.__class__.__name__ in ['Coil', 'Turn']:
                            if chain.ribbonType()=='NA':
                                NAp = self.vf.Nucleic_Acids_properties
                                sc = max(NAp.scale_pyrimidine, NAp.scale_purine)
                                shape2 = Circle2D(radius=sc/2.5)                                    
                            SS.exElt = ExtrudeSSElt(SS,shape2, gapEnd,
                                                    gapBeg, frontcap, endcap,
                                                    arrowf)
                            
                    else:
                        SS.exElt = ExtrudeSSElt(SS, shape1, gapEnd , gapBeg,
                                                frontcap, endcap, arrowf,
                                                larrow)
                    resfaces, resfacesDict = SS.exElt.getExtrudeResidues(SS.residues)
                    #g = mol.geomContainer.geoms[name]
##                     # MS triangulate faces
##                     trifaces = []
##                     for f in resfaces:
##                         trifaces.append( (f[0],f[1],f[3]) )
##                         if f[2]!=f[3]:
##                             trifaces.append( (f[1],f[2],f[3]) )

                    # highlight selection
                    g.resfacesDict = resfacesDict
                    highlight = []
                    if lHighlight is True:# and chain in residueSet :
                        highlight = [0]*len(SS.exElt.vertices)
                        for lResidue in molSelectedResiduesDict[mol]:
                            if resfacesDict.has_key(lResidue):
                                for lFace in resfacesDict[lResidue]:
                                    for lVertexIndex in lFace:
                                        highlight[int(lVertexIndex)] = 1

                    faces.extend(numpy.array(resfaces)+len(vertices))
                    vertices.extend(SS.exElt.vertices)
                    normals.extend(SS.exElt.vnormals)										
                    if chain.ribbonType()=='NA':
                        geom_bases = Add_Nucleic_Bases(g, 
                                           self.vf.Nucleic_Acids_properties)
                        if self.vf.hasGui:
                            self.vf.GUI.VIEWER.AddObject(geom_bases, parent=g)
                        else:
                            g.children.append(geom_bases)
                            geom_bases.parent = g
                            #geom_bases.fullName = g.fullName+'|'+geom_bases.name
                g.Set(vertices=vertices, highlight=highlight,
                      faces=faces,  vnormals=normals, redo=0,
                      tagModified=False)                       

                for SS in removeSS:
                    delattr(SS.residues, 'secondarystructure')
                    ssSet.remove(SS)

                atoms = chain.findType(Atom)
                self.vf.bindGeomToMolecularFragment(g, atoms, log=0)

        if display:
            kw['topCommand'] = 0
            if kw.get('only', 0):
                kw['only'] = 1
            kw['setupUndo'] = 1
            #print "calling displayExtrudedSS with ", kw
            apply(self.vf.displayExtrudedSS,(nodes,),  kw)
            #self.vf.displayExtrudedSS(nodes, setupUndo=1, topCommand=0)



class DisplayExtrudedSSCommand(DisplayCommand):

    """ The DisplaySSCommand displays the geometries representing the secondary structure elements of the current selection.To execute this command use the 'Display Secondary Structure' entry under the 'Display' menu in the menu bar.
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : DisplayExtrudedSSCommand
    \nCommand name : displaySecondaryStructure
    \nSynopsis:\n
        None <- displaySecondaryStructure(nodes, only=False,
                   negate=False,**kw)
    \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
    \nOptional Arguments:\n
        only --- allows the user to display only the current selection when set to 1
        \nnegate --- allows to undisplay the current selection when set to 1.
    \nThis command is undoable.
    """
    def getNodes(self, nodes):
        """expand nodes argument into a list of residues sets and a list of
        molecules.
        this function is used to prevent the expansion operation to be done
        in both doit and setupUndoBefore
        The nodes.findType( Residue ) is the operation that is potentially
        expensive"""

        if not hasattr(self, 'expandedNodes____ResidueSets'):
            mol, res = self.vf.getNodesByMolecule(nodes, Residue)
            #if len(mol)==0: return None, None
            self.expandedNodes____ResidueSets = res
            self.expandedNodes____Molecules = mol

        return self.expandedNodes____Molecules, self.expandedNodes____ResidueSets

    def onAddCmdToViewer(self):
        self.vf.loadCommand("secondaryStructureCommands",
                            "computeSecondaryStructure", "Pmv",
                            topCommand = 0)
            
        self.vf.loadCommand("extrusionCommands",
                            "computeSheet2D", "Pmv",
                            topCommand = 0)

        self.vf.loadCommand("secondaryStructureCommands",
                            "extrudeSecondaryStructure","Pmv",
                            topCommand = 0)
        self.vf.registerListener(AfterDeleteAtomsEvent, self.handleAfterDeleteAtoms)

    def handleAfterDeleteAtoms(self, event):
        """Function to update geometry objects created by this command
upon atom deletion.
\nevent --- instance of a VFEvent object
"""
        # split event.objects into atoms sets per molecule
        molecules, ats = self.vf.getNodesByMolecule(event.objects)
        # loop over molecules to update geometry objects
        for mol, atomSet in zip(molecules, ats):
            #if no backbone atoms are deleted ss does not change
            if len(atomSet.get("backbone")) == 0:
                continue
            
            for atom in atomSet.get("CA"):
                atom.parent.hasCA = False
            for atom in atomSet.get("O"):
                atom.parent.hasO = False
            
            if not  mol.geomContainer.geoms.has_key('secondarystructure'): continue
            kw = mol.geomContainer.geoms['secondarystructure'].kw
            #cleanup SS atomset in geomcontainer             
            self.vf.computeSecondaryStructure.clean(mol)
            
            #this for molparser.hasSsDataInFile to trurn false
            while 'HELIX' in mol.parser.keys:
                mol.parser.keys.remove('HELIX')
            while 'SHEET' in mol.parser.keys:
                mol.parser.keys.remove('SHEET')
            while 'TURN' in mol.parser.keys:
                mol.parser.keys.remove('TURN')
                
            for chain in mol.chains:
                chain.ribbonType(noCache=True)
            
            #mol.hasSS = False
            mol.secondaryStructureFromPross()
            mol.__hasSSGeom=0

            self.vf.extrudeSecondaryStructure(mol, topCommand=0, log=0, display=0)
            self.doitWrapper(mol, topCommand=0, **kw)

        

    def setupUndoBefore(self, nodes, only=False, negate=False, **kw):
        if len(nodes)==0 : return
        #molecules = nodes.top.uniq()
        molecules, residueSets = self.getNodes(nodes)
        #for mol, res in map(None, molecules, residueSets):
        for mol in molecules:
            resWithSS = mol.findType(Residue).get(
                lambda x:hasattr(x,'secondarystructure'))
            if resWithSS is None:
                continue
            SSinMol = resWithSS.secondarystructure.uniq()
            #resWithSS = res.get(lambda x: hasattr(x,'secondarystructure'))
            #SSinSel = resWithSS.secondarystructure.uniq()
            #mol.geomContainer.atoms['secondarystructure']=resWithSS.atoms
            set = ResidueSet()
            if mol.geomContainer.geoms.has_key('SS'):
                for ch in mol.chains :
                    set = set + mol.geomContainer.atoms['SS'+ch.id].parent
                    if len(set)==0: # nothing is displayed	
                        self.addUndoCall( (mol,),
                                  {'negate':True, 'redraw':True},
                                  self.name )
                    else:
                        self.addUndoCall( (set,), {'only':True, 'redraw':True},
                                  self.name )								
            else :
                for ss in SSinMol:
                    set = set + mol.geomContainer.atoms[ss.name+ss.chain.id]
                    if len(set)==0: # nothing is displayed
                        self.addUndoCall( (mol,),
                                  {'negate':True, 'redraw':True},
                                  self.name )
                    else:
                        self.addUndoCall( (set,), {'only':True, 'redraw':True},
                                  self.name )


    def doit(self, nodes, only=False, negate=False,**kw ):
        """ displays the secondary structure for the selected treenodes """

        #print "in display with only=", only, " and negate=", negate
        ###############################################################
        def drawResidues(SS, res, only, negate,uniq=False):
            mol = SS.chain.parent
            name = '%s%s'%(SS.name, SS.chain.id)
            _set = mol.geomContainer.atoms[name]
            inres = filter(lambda x, res=res: not x in res, _set)
            if len(inres) == 0:
                # res and _set are the same
                if negate:
                    _set = ResidueSet()
                    setOff = res
                    setOn = None
                else:
                    _set = res
                    setOff = None
                    setOn = res
            else:
                # if negate, remove current res from displayed _set
                if negate :
                    setOff = res
                    setOn = None
                    _set = _set - res

                else: # if only, replace displayed _set with current res
                    if only:
                        setOff = _set - res
                        setOn = res
                        _set = res
                    else:
                        _set = res.union(_set)
                        setOff = None
                        setOn = _set

##             # if negate, remove current res from displayed _set
##             if negate :
##                 _set = _set - res

##             else: # if only, replace displayed _set with current res
##                 if only:
##                     _set = res
##                 else:
##                     _set = res.union(_set)
##             # now, update the geometries:
## 	    if len(_set)==0:
##                 mol.geomContainer.geoms[name].Set(visible=0, tagModified=False)
##                 mol.geomContainer.atoms[name] = ResidueSet()
##                 return

            #the rest is done only if there are some residues           
            
            mol.geomContainer.atoms[name] = _set
            #print _set
            if not hasattr(SS, 'exElt'):
                return setOn, setOff

            if isinstance(SS, Coil):
                gapBefore = SS.gapBefore
                gapAfter = SS.gapAfter
            else:
                gapBefore = gapAfter = False
                
            resfaces, resfacesDict = SS.exElt.getExtrudeResidues(
                _set, gapBefore, gapAfter)
            
##          # MS triangulate faces
##             trifaces = []
##             for f in resfaces:
##                 trifaces.append( (f[0],f[1],f[3]) )
##                 if f[2]!=f[3]:
##                     trifaces.append( (f[1],f[2],f[3]) )
##             g.Set(faces=trifaces, vnormals=SS.exElt.vnormals,
            if uniq:
                return setOn, setOff, resfaces, SS.exElt.vnormals, \
                       SS.exElt.vertices            
            g = mol.geomContainer.geoms[name]
            col = mol.geomContainer.getGeomColor(name)
            g.Set(faces=resfaces, vnormals=SS.exElt.vnormals,
                  visible=1, materials=col, inheritMaterial=False,
                  tagModified=False)
            if SS.chain.ribbonType()=='NA':
                faces = []
                colors = [] 
                for residue in _set:
                    faces.extend(residue._base_faces)
                    colors.extend(residue._coil_colors)
                    try:
                        atm = residue.atoms.get('CA')[0]
                    except:
                        atm = residue.atoms[0]
                    if len(residue._coil_colors) :
                        atm.colors["secondarystructure"] = residue._coil_colors[0]#??
                    else:
                        atm.colors["secondarystructure"] = residue._coil_colors
                g.children[0].Set(faces=faces)
                if colors:
                    g.Set(materials=colors, inheritMaterial=False)
                    
                if self.vf.Nucleic_Acids_properties.color_backbone:
                    g.Set(inheritMaterial=False)
                    
                else:
                    g.Set(inheritMaterial=True)
                mol.geomContainer.atoms['Bases'] = ResidueSet()
                #mol.geomContainer.atoms[name] = ResidueSet()

            return setOn, setOff

###############################################################

        molecules, residueSets = self.getNodes(nodes)
        setOn = ResidueSet([])
        setOff = ResidueSet([])
        for mol, residues in map(None, molecules, residueSets):
            if not mol.hasSS:
                self.vf.computeSecondaryStructure(mol,topCommand=0,log=0)
                self.vf.extrudeSecondaryStructure(
                    mol, topCommand=0, log=0, display=0)
            reswithss = residues.get(lambda x:
                                     hasattr(x,'secondarystructure'))
            if reswithss is None:
                print 'no secondary structure in that selection'
                continue
            
            SSInSel = reswithss.secondarystructure.uniq()
            chainsInSel = residues.parent.uniq()
            for c in mol.chains:
                if not hasattr(c, 'secondarystructureset'):
                    continue
                if not hasattr(c, 'sheet2D'):
                    print "The chain %s doesn't have a sheet2D computed"%c.name
                    continue
                elif (c.sheet2D.has_key('ssSheet2D') and \
                      c.sheet2D['ssSheet2D'] is None): continue
                if mol.geomContainer.geoms.has_key('SS') :
                    faces=[]
                    vertices=[]	
                    normals=[]							
                    name = "SS"+c.id
                    g = mol.geomContainer.geoms[name]
                SS, resInSS = self.getResiduesBySS(residues, c)
                for s in xrange(len(c.secondarystructureset)):
                    ss = c.secondarystructureset[s]
                    res = resInSS[s]
                    if ss in SSInSel and not hasattr(ss, 'exElt') \
                       and negate == 0:
                        self.vf.extrudeSecondaryStructure(res, display=0,
                                                          topCommand=0)

                    if mol.geomContainer.geoms.has_key('SS') :
                        son, sof, f, n, v = drawResidues(ss, res, only , negate ,uniq=True)
                        faces.extend(numpy.array(f)+len(v))
                        vertices.extend(v)
                        normals.extend(n)
                    else :
                        son, sof = drawResidues(ss, res, only , negate )

                    if son: setOn += son
                    if sof: setOff += sof

                if mol.geomContainer.geoms.has_key('SS') :
                    g.Set(visible=not negate)
                    
            kw["only"] = only
            kw["negate"] = negate
            mol.geomContainer.geoms['secondarystructure'].kw = kw      				
        redraw = False
        if kw.has_key("redraw") : redraw=True
        event = EditGeomsEvent('SSdisplay', [nodes,[only, negate,redraw]],
                               setOn=setOn, setOff=setOff)
        self.vf.dispatchEvent(event)

					
    def cleanup(self):
        """ Method called by afterDoit to clean up things eventhough the doit
        failes."""
        del self.expandedNodes____ResidueSets
        del self.expandedNodes____Molecules
                    
                     
    def __call__(self, nodes, only=False, negate=False,**kw):
        """None <- displaySecondaryStructure(nodes, only=False,
                   negate=False,**kw)
        \nRequired Arguments:\n
            \nnodes  ---  TreeNodeSet holding the current selection
        \nOptional Arguments:\n
            \nonly ---  flag when set to 1 only the current selection will be displayed as secondarystructures
            \nnegate ---  flag when set to 1 undisplay the current selection"""
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        if not kw.has_key('redraw'):kw['redraw']=1
        kw['only'] = only
        kw['negate'] = negate
        
        apply(self.doitWrapper, (nodes,),kw)

    def getResiduesBySS(self, residues, chain):
        resWithSS = residues.get(lambda x: hasattr(x, 'secondarystructure'))
        residuesInSS = []
        for ss in chain.secondarystructureset :
            res = resWithSS.get(lambda x, ss=ss:x.secondarystructure==ss)
            if res is None:
                res = ResidueSet()
            residuesInSS.append(res)
        return chain.secondarystructureset, residuesInSS


class UndisplayExtrudedSSCommand(DisplayCommand):
    """ UndisplaySSCommand is an interactive command to undisplay part of
    the molecule when represented as extruded secondary structure.
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : UndisplayExtrudedSSCommand
    \nCommand name : undisplaySecondaryStructure
    \nSynopsis:\n
         None <--- undisplaySecondaryStructure(nodes, **k)
    \nRequired Arguments:\n    
         nodes --- TreeNodeSet holding the current selection
    """
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('displayExtrudedSS'):
            self.vf.loadCommand('secondaryStructureCommands',
                                ['displayExtrudedSS'], 'Pmv',
                                topCommand=0)

        
    def __call__(self, nodes, **kw):
        """None <--- undisplaySecondaryStructure(nodes, **k)
        \nnodes --- TreeNodeSet holding the current selection
        """
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        kw['negate']= 1
        apply(self.vf.displayExtrudedSS, (nodes,), kw)



class RibbonCommand(MVCommand):
    """ The RibbonCommand is a shortcut to visualize a traditional Ribbon
    representation of the current selection. It first executes getSSCommand
    then the extrudeSSCommand with the default values for all the parameters.
    This command is undoable.
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : RibbonCommand
    \nCommand name : ribbon
    \nSynopsis:\n    
        None <- ribbon(nodes, only=False, negate=False, **kw)
    \nRequired Arguments:\n    
        nodes ---  TreeNodeSet holding the current selection
    \nOptional Arguments:\n   
        only --- flag when set to 1 only the current selection
                  will be displayed
        \nnegate --- flag when set to 1 undisplay the current selection
    """
    def __init__(self):
        MVCommand.__init__(self)
        self.flag = self.flag | self.objArgOnly
        self.flag = self.flag | self.negateKw
   

    def onAddCmdToViewer(self):
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('computeSecondaryStructure'):
##             self.vf.loadCommand("secondaryStructureCommands",
##                                 "computeSecondaryStructure", "Pmv",
##                                 topCommand = 0)
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('extrudeSecondaryStructure'):
##             self.vf.loadCommand("secondaryStructureCommands",
##                                 "extrudeSecondaryStructure", "Pmv",
##                                 topCommand = 0)
##         if self.vf.hasGui and \
##            not self.vf.commands.has_key('displayExtrudedSS'):
##             self.vf.loadCommand("secondaryStructureCommands",
##                                 "displayExtrudedSS", "Pmv",
##                                 topCommand = 0)
        self.vf.loadCommand("secondaryStructureCommands",
                            "computeSecondaryStructure", "Pmv",
                            topCommand = 0)

        self.vf.loadCommand("secondaryStructureCommands",
                            "extrudeSecondaryStructure", "Pmv",
                            topCommand = 0)

        self.vf.loadCommand("secondaryStructureCommands",
                            "displayExtrudedSS", "Pmv",
                            topCommand = 0)

    def guiCallback(self):
        self.doitWrapper(self.vf.getSelection(), redraw=1)


    def __call__(self, nodes, only=False, negate=False, **kw):
        """None <- ribbon(nodes, only=False, negate=False, **kw)
        \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
        \nOptional Arguments:\n
        only --- flag when set to 1 only the current selection
                  will be displayed
        \nnegate ---  flag when set to 1 undisplay the current selection
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        
        if not kw.has_key('redraw'): kw['redraw']=1
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        kw['only']=only
        kw['negate']=negate
        #print "in ribbon with only=", only
        apply(self.doitWrapper, (nodes,), kw)
        
        
    def doit(self, nodes, **kw):
        #print "in ribbon.doit with only=", kw['only']
        apply(self.vf.computeSecondaryStructure,(nodes,), {'topCommand':False})
        kw['topCommand'] = 0
        #kw['only'] = only
        #kw['negate'] = negate
        
        apply(self.vf.extrudeSecondaryStructure,(nodes,), kw)
        #self.vf.computeSecondaryStructure(nodes, topCommand=0)
        #self.vf.extrudeSecondaryStructure(nodes, topCommand=0)



class ColorBySSElementType(ColorFromPalette):
    """Command to color the given geometry by secondary structure
    element. (Rasmol color code)
    \nPackage : Pmv
    \nModule  : secondaryStructureCommands
    \nClass   : ColorBySSElementType
     """
    def onAddCmdToViewer(self):
        if self.vf.hasGui:
            paletteClass = ColorPalette
        else:
            paletteClass = ColorPaletteNG
            
        from Pmv.pmvPalettes import SecondaryStructureType
        c = 'Color palette for secondary structure element type:'
        self.palette = paletteClass(
            'SecondaryStructureType', SecondaryStructureType,
            info=c, lookupMember = 'structureType')

        if not self.vf.commands.has_key('color'):
            self.vf.loadCommand('colorCommands', 'color', 'Pmv',
                                topCommand=0)
        self.undoCmdsString= self.vf.color.name


    def getNodes(self, nodes, returnNodes=False):
        """expand nodes argument into a list of atoms and a list of
        molecules.
        this function is used to prevent the expansion operation to be done
        in both doit and setupUndoBefore
        The nodes.findType( Atom ) is the operation that is potentially
        expensive"""
        # Only get the atoms belonging to a residue with a secondary structure
        if not hasattr(self, 'expandedNodes____Atoms') or not self.expandedNodes____Atoms:
            nodes = self.vf.expandNodes(nodes)
            self.expandedNodes____Nodes = nodes
            res = nodes.findType(Residue).uniq()
            resWithSS = res.get(lambda x: hasattr(x,'secondarystructure'))
            if resWithSS is None or len(resWithSS)==0:
                self.expandedNodes____Atoms = AtomSet()
                self.expandedNodes____Molecules = ProteinSet()
            else:
                self.expandedNodes____Atoms = resWithSS.atoms
                self.expandedNodes____Molecules = resWithSS.top.uniq()
        if returnNodes:
            return self.expandedNodes____Molecules, \
                   self.expandedNodes____Atoms, self.expandedNodes____Nodes
        else:
            return self.expandedNodes____Molecules, self.expandedNodes____Atoms

    def getColors(self, nodes):
        res = nodes.findType(Residue)
        resWithSS = res.get(lambda x: hasattr(x, 'secondarystructure'))
        if resWithSS is None: return None, None
        return resWithSS, self.palette.lookup(resWithSS.secondarystructure)


    def doit(self, nodes, geomsToColor):
        # these commands do not require the color argument since colors are
        # gotten from a palette
        # we still can use the ColorCommand.setupUndoBefore but first we get
        # the colors. This also insures that the colors are not put inside the
        # log string for these commands
        molecules, atms = self.getNodes(nodes)
        if len(atms)==0: return
        resWithSS, colors = self.getColors(atms)
        if colors is None: return
        for g in geomsToColor:
            if len(colors)==1 or len(colors)!=len(atms):
                for a in atms:
                    a.colors[g] = tuple( colors[0] )
            else:
                for a, c in map(None, atms, colors):
                    a.colors[g] = tuple(c)

        updatedGeomsToColor = []
        for mol in molecules:
            for gName in geomsToColor:
                if not mol.geomContainer.geoms.has_key(gName): continue
                geom = mol.geomContainer.geoms[gName]
                if geom.children != []:
                    # get geom Name:
                    childrenNames = map(lambda x: x.name, geom.children)
                    updatedGeomsToColor = updatedGeomsToColor + childrenNames
                    for childGeom in geom.children:
                        childGeom.Set(inheritMaterial=0, redo=0, tagModified=False)
                else:
                    updatedGeomsToColor.append(gName)
                    geom.Set(inheritMaterial=0, redo=0, tagModified=False)

            mol.geomContainer.updateColors(updatedGeomsToColor)
        #geomEditEventss
        event = EditGeomsEvent("color", [nodes,[geomsToColor, colors, self.name[5:11]]])
        self.vf.dispatchEvent(event)

    def cleanup(self):
        if hasattr(self, 'expandedNodes____Molecules'):
            del self.expandedNodes____Molecules
        if  hasattr(self, 'expandedNodes____Atoms'):
            del self.expandedNodes____Atoms
        if  hasattr(self, 'expandedNodes____Nodes'):
            del self.expandedNodes____Nodes
        

colorBySecondaryStructureTypeGuiDescr = {'widgetType':'Menu',
                                         'menuBarName':'menuRoot',
                                         'menuButtonName':'Color',
                                         'menuEntryLabel':'By SS Element Type'}


ColorBySSElementTypeGUI = CommandGUI()
ColorBySSElementTypeGUI.addMenuCommand('menuRoot', 'Color',
                                       'by SS Element Type')

computeSSGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Compute',
                     'menuEntryLabel':'Compute Secondary Structure',
                     'separatorAbove':1}

computeSSGUI = CommandGUI()
computeSSGUI.addMenuCommand('menuRoot', 'Compute',
                            'Compute Secondary Structure',
                            cascadeName = 'Secondary structure')

extrudeSSGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Compute',
                     'menuEntryLabel':'Extrude Secondary Structure'}

ExtrudeSSGUI = CommandGUI()
ExtrudeSSGUI.addMenuCommand('menuRoot', 'Compute',
                            'Extrude Secondary Structure',
                            cascadeName = 'Secondary structure')

ExtrudeSSuGUI = CommandGUI()
ExtrudeSSuGUI.addMenuCommand('menuRoot', 'Compute',
                            'Extrude Secondary Structure Unic',
                            cascadeName = 'Secondary structure')

displaySSGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Display',
                     'menuEntryLabel':'Secondary Structure'}

DisplaySSGUI = CommandGUI()
DisplaySSGUI.addMenuCommand('menuRoot', 'Display',
                            'Secondary Structure')

ribbonGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                  'menuButtonName':'Compute',
                  'menuEntryLabel':'Ribbon'}

RibbonGUI = CommandGUI()
RibbonGUI.addMenuCommand('menuRoot', 'Compute','Ribbon',
                          cascadeName = 'Secondary structure')

commandList = [
    {'name': 'computeSecondaryStructure',
     'cmd': ComputeSecondaryStructureCommand(),
     'gui':computeSSGUI},
    {'name': 'extrudeSecondaryStructure',
     'cmd': ExtrudeSecondaryStructureCommand(),
     'gui':ExtrudeSSGUI},
    {'name': 'extrudeSecondaryStructureUnic',
     'cmd': ExtrudeSecondaryStructureCommandUnic(),
     'gui':ExtrudeSSuGUI},	 
    {'name': 'displayExtrudedSS',
     'cmd': DisplayExtrudedSSCommand(),
     'gui':DisplaySSGUI},
    {'name': 'colorBySecondaryStructure',
     'cmd': ColorBySSElementType(),
     'gui':ColorBySSElementTypeGUI},
    {'name': 'undisplayExtrudedSS', 'cmd': UndisplayExtrudedSSCommand(),
     'gui': None},
    {'name': 'ribbon', 'cmd':RibbonCommand(),
     'gui':RibbonGUI},
    ]

def initModule(viewer):
    """ initializes commands for secondary structure and extrusion.  Also
    imports the commands for Secondary Structure specific coloring, and
    initializes these commands also. """

    for dict in commandList:
	viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

