## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Sophie COON, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/extrusionCommands.py,v 1.45.2.1 2012/06/20 20:58:59 sanner Exp $
#
# $Id: extrusionCommands.py,v 1.45.2.1 2012/06/20 20:58:59 sanner Exp $
#
import Tkinter, numpy.oldnumeric as Numeric,Pmw
import types, string
from tkColorChooser import askcolor
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI

from MolKit.molecule import Atom, AtomSet
from MolKit.protein import Protein, Residue, Chain, ResidueSet, ProteinSet
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import SliderWidget, \
     ExtendedSliderWidget
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from Pmv.extruder import Sheet2D
from Pmv.displayCommands import DisplayCommand
from DejaVu.Spheres import Spheres


class ComputeSheet2DCommand(MVCommand):
    """The ComputeSheet2DCommand class implements methods to compute the sheet2D for each chain of the contained in the current selection. Need to specify two control atoms.
    \nPackage : Pmv
    \nModule  : extrusionCommands
    \nClass   : ComputeSheet2DCommand
    \nCommand name : computeSheet2D
    \nSynopsis:\n
        None <- ComputeSheet2D(nodes, buildIsHelix=1, nbrib=2,
                               nbchords=4, width=1.5, offset=1.2, **kw)
    \nRequired Arguments:\n   
        nodes --- any set for MolKit nodes describing molecular components
     \nOptional Arguments:\n    
        ctlAtmsName --- tuple of two atom name specifying the two control atoms
                      the second atom is used to limit the torsion of the sheet
                      2D.
        \nbuildIsHelix --- flag when set to 1 specifies that an helix is defined.
        \nnbrib --- integer specifying the number of ribbon of the sheet2D.
        \nnbchords --- integer specifying the number of points per residues
        \nwidth  --- float specifying the width of the sheet2D
        \noffset --- float specifying the offset of ?

    \nRequired Packages:\n
      MolKit, DejaVu, mglutil, OpenGL, Tkinter, Pmw, types, ViewerFramework
    \nRequired Commands:\n
      ExtrusionCommands.ComputeSheet2D, 
    \nKnown bugs:\n
      None
    \nExamples:\n
      mol = mv.Mols[0]
      \nmv.extrudeCATrace(mv.getSelection())
    
    """
    def __init__(self):
        MVCommand.__init__(self)

    def __call__(self, nodes, sheet2DName, ctlAtmName, torsAtmName,
                 buildIsHelix=False, nbrib=2, nbchords=4, width=1.5, offset=1.2,
                 **kw):
        """None <- ComputeSheet2D(nodes, sheet2DName, ctlAtmName, torsAtmName,
                               buildIsHelix=0, nbrib=2, nbchords=4,
                               width=1.5, offset=1.2, **kw)
        \nnodes  --- any set for MolKit nodes describing molecular components
        \nctlAtmName --- tuple of two atom name specifying the two control atoms
                      the second atom is used to limit the torsion of the sheet
                      2D.
        \nbuildIsHelix ---- Boolean flag when set to True specifies that an helix is defined.
        \nnbrib --- integer specifying the number of ribbon of the sheet2D.
        \nnbchords --- integer specifying the number of points per residues
        \nwidth  --- float specifying the width of the sheet2D
        \noffset --- float specifying the offset of ?
        """
        kw['buildIsHelix'] = buildIsHelix
        kw['nbrib'] = nbrib
        kw['nbchords'] = nbchords
        kw['width'] = width
        kw['offset'] = offset
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"

        nodes = self.vf.expandNodes(nodes)
        apply(self.doitWrapper, (nodes, sheet2DName, ctlAtmName, torsAtmName),
              kw)
        
    def getSheet2DRes(self, chain, ctlAtmName, torsAtmName, buildIsHelix=False):
        isHelix = []
        sheetCoords = []
        from MolKit.protein import ResidueSet
        sheet2DRes = ResidueSet()
        residues = chain.residues
        sheet2DResappend = sheet2DRes.append
        isHelixappend = isHelix.append
        for res in residues:
            hasAtm, rCoords = res.getAtmsAndCoords([ctlAtmName, torsAtmName])
            if hasAtm == 0:
                ## MS June 2012: the code below cause 2X2K.pdb and 2IVU.pdb
                ## to only show a short helical part. Instead of stopping
                ## we continue
                continue
##                 if len(sheet2DRes)== 0 or res.atoms[0].hetatm:
##                     # if the residue without CA and O is at the beginning
##                     # go on until you find the right residue
##                     # or res.atoms[0].hetatm added ti fix bug#779
##                     continue
##                 else:
##                     # Stop the sheet2D right there
##                     return  sheet2DRes, sheetCoords, isHelix
                ## end MS June 2012:
            else:
                sheet2DResappend(res)
                sheetCoords = sheetCoords + rCoords
                if buildIsHelix and hasattr(res, 'secondarystructure'):
                    sr = res.secondarystructure.structureType
                    isHelixappend(sr=='Helix')
                else:
                    isHelixappend(0)
                    
        return sheet2DRes, sheetCoords, isHelix


    def doit(self, nodes, sheet2DName, ctlAtmName, torsAtmName,
             buildIsHelix=False, nbrib=2, nbchords=8, width=1.5, offset=1.2):
        from MolKit.protein import Chain
        from types import StringType, IntType
        """ Function that will compute the sheet2D elements for a molecule.
        1- Get the residues with a CA and O and the coordinates of these
        atoms.
        """
        # Make sure that the given arguments are from the right type.
        if not type(sheet2DName) is StringType: return
        if not type(ctlAtmName) is StringType or not ctlAtmName: return
        if not type(torsAtmName) is StringType or not torsAtmName: return
        if not isinstance(nbchords, IntType): return
        if len(nodes)==0: return

        # Get the molecules having at least one node in the selection

        # loop over the chains of the molecules. We want to compute
        # the sheet2D for all the molecules not only the chain in the
        # current selection.
        chains = nodes.findType(Chain).uniq()
        for chain in chains:
            # Do not recompute the sheet2D if a entry with the same
            # sheet2DName exists in the dictionary and the sheet2D
            # has been computed with the same chords, ctlAtms...
            if not hasattr(chain, 'sheet2D'):
                chain.sheet2D = {}

            if not chain.sheet2D.has_key(sheet2DName):
                chain.sheet2D[sheet2DName] = Sheet2D()
            else:
                # If one of the parameter of the sheet2D is different then...
                pass

            sheet2DRes, sheetCoords, inHelix = self.getSheet2DRes(
                chain, ctlAtmName, torsAtmName, buildIsHelix)
            
            if sheetCoords is None or len(sheetCoords)<=2:
                chain.sheet2D[sheet2DName] = None
                continue

            s = chain.sheet2D[sheet2DName]
            s.compute(sheetCoords, inHelix, nbchords=nbchords,
                      nbrib=nbrib, width=width, offset=offset )
            s.resInSheet = sheet2DRes

    def buildFormDescr(self, formName):
        if formName == 'computesheet2D':
            
            idf = InputFormDescr(title ="Sheet 2D parameters :")
            idf.append( {'name':'sheet2DName',
                         'widgetType':Pmw.EntryField,
                         'tooltip':'Name of the sheet2D',
                         'wcfg':{'label_text':"Name of the sheet2D:",
                                 'labelpos':'w',
                                 'entry_width':15
                                 },
                         'gridcfg':{'sticky':'w', "columnspan":2}})
            idf.append( {'name':'ctlAtms',
                         'widgetType':Pmw.EntryField,
                         'tooltip':'Type the name of atom to use as control atom.\n\
                         (CA or C or O etc...)',
                         'wcfg':{'value':'CA',
                                 'label_text':"Name of the control atom:",
                                 'labelpos':'w',
                                 'entry_width':3
                                 },
                         'gridcfg':{'sticky':'w'}})
            
            idf.append( {'name':'torsAtms',
                         'widgetType':Pmw.EntryField,
                         'tooltip':'Type the name of the atom to control the torsion of the sheet',
                         'wcfg':{'value':'O',
                                 'label_text':"Name of the control atom:",
                                 'labelpos':'w',
                                 'entry_width':3
                                 },
                         'gridcfg':{'sticky':'w', 'row':-1}})

            idf.append( {'name': 'nbchords',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'nb. Pts Per Residue:  ',
                                 'minval':4,'maxval':15, 'incr': 1, 'init':8,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })

            idf.append( {'name': 'width',
                         'widgetType':ExtendedSliderWidget,
                         'type':float,
                         'wcfg':{'label': 'width  ',
                                 'minval':0.5,'maxval':5., 'incr':0.1,
                                 'init':1.5,
                                 'labelsCursorFormat':'%4.1f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })

            idf.append( {'name': 'nbrib',
                         'widgetType':ExtendedSliderWidget,
                         'type':int,
                         'wcfg':{'label': 'Number of ribbons  ',
                                 'minval':2,'maxval':10, 'incr': 1, 'init':2,
                                 'labelsCursorFormat':'%d', 'sliderType':'int',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })
 
            idf.append( {'name': 'offset',
                         'widgetType':ExtendedSliderWidget,
                         'type':float,
                         'wcfg':{'label': 'width  ',
                                 'minval':0.5,'maxval':5.,
                                 'incr':0.1, 'init':1.2,
                                 'labelsCursorFormat':'%4.1f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })
            idf.append( {'name': 'offset',
                         'widgetType':ExtendedSliderWidget,
                         'type':float,
                         'wcfg':{'label': 'width  ',
                                 'minval':0.5,'maxval':5.,
                                 'incr':0.1, 'init':1.2,
                                 'labelsCursorFormat':'%4.1f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'columnspan':2,'sticky':'we'}
                         })

            
            return idf

    def guiCallback(self):
        val = self.showForm('computesheet2D')
        if val == {}:
            return
        val['buildIsHelix']=0
        sheet2DName = val['sheet2DName']
        del val['sheet2DName']
        ctlAtmName = val['ctlAtms']
        del val['ctlAtms']
        torsAtmName = val['torsAtms']
        del val['torsAtms']
        if self.vf.userpref['Expand Node Log String']['value'] == 0:
            self.nodeLogString = "self.getSelection()"

        apply(self.doitWrapper,(self.vf.getSelection(),sheet2DName ,
                                ctlAtmName, torsAtmName), val)

ComputeSheet2DGUI = CommandGUI()
ComputeSheet2DGUI.addMenuCommand('menuRoot', 'Compute', 'sheet2D')

class DisplayPath3DCommand(MVCommand):
    """This Command displays the computed sheet2D for each chain of the contained in the current selection.
    \nPackage : Pmv
    \nModule  : extrusionCommands
    \nClass   : DisplayPath3DCommand
    \nCommand name : displayPath3D
    \nSynopsis:\n
        None <- displayPath3D(self, nodes, negate=False, only=False, **kw)
    \nRequired Arguments:\n   
        nodes --- any set for MolKit nodes describing molecular components
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.flag = self.flag | self.objArgOnly
    
    def onAddCmdToViewer(self):
        #if self.vf.hasGui and \
        #   not self.vf.commands.has_key('computeSheet2D'):
        self.vf.loadCommand("extrusionCommands",
                            ["computeSheet2D",], "Pmv",
                            topCommand = 0)

    def onAddObjectToViewer(self,obj):
        for c in obj.chains:
            c.residues.rindex = range(len(c.residues))

    def createGeometries(self, obj):
        from DejaVu.Geom import Geom
        geomC = obj.geomContainer
        c =  Geom('path',  shape=(0,0), protected=True)
        c.replace = 'force'
        geomC.addGeom(c, parent=geomC.masterGeom)
        for a in obj.allAtoms:
            a.colors['path']=(1.,1.,1.)
            a.opacities['path']=1.0

        for chain in obj.chains:
            if not hasattr(chain, 'sheet2D') or chain.sheet2D is None: 
                continue
            # HACK TO DEBUG SECONDARYSTRUCTURE
            if not chain.sheet2D.has_key('ssSheet2D') or \
               chain.sheet2D['ssSheet2D'] is None:
                continue

            # Create a geometry per sheet2D
            name = 'path'+ chain.id
            g = Spheres( name, quality = 10, radii = 0.15, protected=True)
            g.replace = 'force'
            geomC.addGeom( g, parent=c)
            self.managedGeometries.append(g)
            # FIXME to update this geom we would have to implement
            # self.updateGeom specifically for this command

            geomC.atoms[name] = ResidueSet()
            g.chain = chain
            geomC.atomPropToVertices[name] = self.atomPropToVertices
            geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
            geomC.geomPickToBonds[name] = None


    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert a picked vertex into an atom"""

        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet
        chain = geom.chain
        l = []
        for vi in vertInd:
            resInd = self.getResInd( vi, chain )
            l.append(chain.residues[resInd].atoms[0])
        return AtomSet( AtomSet( l ) )

    def atomPropToVertices(self, geom, residues, propName, propIndex=None):
        """Function called to compute the array of colors"""
        if residues is None or len(residues)==0 : return None
        residues.sort()
        if not propIndex is None:
            propIndex = geom.name
        # chords = residues[0].parent.sheet2D.chords
        chords = residues[0].parent.sheet2D['ssSheet2D'].chords
        col = [residues[0].atoms[0].colors['path'],]*(chords/2+1)
        for r in residues[1:-1]:
            col = col + ([r.atoms[0].colors['path'],]*chords)

        col = col + [residues[-1].atoms[0].colors['path'],]*(chords+chords/2)
        # here need to compute the number of colors corresponding to the
        # number of vertices. 
        return col


    def getResInd(self, vi, chain):
        assert vi < len(chain.sheet2D['ssSheet2D'].path)
        #assert vi < len(chain.sheet2D.path)
        chords = chain.sheet2D['ssSheet2D'].chords
        lengthPath = chain.sheet2D['ssSheet2D'].path.shape[0]
        #chords = chain.sheet2D.chords
        #lengthPath = chain.sheet2D.path.shape[0]
        if vi < (chords/2 + 1 ):
            # first residue
            resIndex = 0
        elif vi > ((lengthPath-1)-\
                        (chords + chords/2)):
            # last residue
            resIndex = len(chain.residues)-1
        else:
            # all the other nbchords
            resIndex = (vi-(2+ chords/2))/chords + 1

        return resIndex

    def getResPts(self, residueindex, chain):
        """ return the index of the first and the last point in the
        Sheet2D.path for the residue whose index is specified"""
        # a residue is represented in the path3D by chords points.
        # first residue represented by nbchords/2 + 1
        # last residue represented by nbchords+nbchords/2
        # all other by nbchords.
        #chords = chain.sheet2D.chords
        chords = chain.sheet2D['ssSheet2D'].chords
        #lengthPath = chain.sheet2D.path.shape[0]
        lengthPath = chain.sheet2D['ssSheet2D'].path.shape[0]
        if residueindex == 0:
            fromPts = 0
            toPts = chords/2 + 2

        elif residueindex == len(chain.residues)-1:
            fromPts = (residueindex-1) * chords + chords/2 +1
            toPts = lengthPath-1

        else:
            fromPts = (residueindex-1) * chords + chords/2 +1
            toPts = fromPts + chords +1

        return fromPts,toPts

    def drawResidues(self,chain, res, only, negate):
        mol = chain.parent
        name = 'path'+chain.id
        set = mol.geomContainer.atoms[name]
        if negate :
            set =  set - res
            ##if only, replace displayed set with current atms 
        else:
            if only:
                set = res
            else:
                set = res.union(set)
        if len(set)==0:
            mol.geomContainer.geoms[name].Set(visible=0, tagModified=False)
            mol.geomContainer.atoms[name] = set
            return
        set.sort()
        g = mol.geomContainer.geoms[name]
        mol.geomContainer.atoms[name] = set
        resVert = []
        lastres = chain.residues[-1].rindex
        #p = chain.sheet2D.path
        p = chain.sheet2D['ssSheet2D'].path
        for res in set:
            fromPts, toPts = self.getResPts(res.rindex,
                                            chain)
            if res.rindex == lastres:
                resVert = resVert + (p[fromPts:].tolist())
            else:
                resVert = resVert + (p[fromPts:toPts-1].tolist())
                
        g.Set(vertices = resVert, tagModified=False)

    def __call__(self, nodes, negate=False, only=False, **kw):
        """
        None <- displayPath3D(self, nodes, negate=False, only=False, **kw)
        
        """
        kw['negate'] = negate
        kw['only'] = only
        kw['redraw'] = True
        nodes = self.vf.expandNodes(nodes)
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply(self.doitWrapper, (nodes,), kw)

        
    def doit(self, nodes, negate=False, only=False):
        #################################################################
            
        molecules, residueSets = self.vf.getNodesByMolecule(nodes, Residue)
        for mol,residues in map(None, molecules, residueSets):
            for chain in mol.chains:
                if not hasattr(chain, 'sheet2D'):
                    chain.sheet2D = {}
##                 if not hasattr(mol, 'hasSheet2D') or not mol.hasSheet2D:
##                     # compute a sheet2D need to put buildIsHelix = 0 here.
##                     self.vf.ComputeSheet2D(mol, nbchords = 10,
##                                            buildIsHelix = 0,
##                                            topCommand=0,log=0)
                if not chain.sheet2D.has_key('ssSheet2D'):
                    self.vf.computeSheet2D(chain, 'ssSheet2D',
                                               'CA','O', buildIsHelix=1,
                                               nbchords=8,
                                               topCommand=0,log=0)

                #if chain.sheet2D is None : continue
                if chain.sheet2D['ssSheet2D'] is None : continue

            self.createGeometries(mol)    
            self.drawResidues(chain, residues, only, negate)


    def buildFormDescr(self, formName):
        if formName == 'display':
            idf =  InputFormDescr(title = self.name)
            idf.append({'name':'display',
                        'widgetType':Pmw.RadioSelect,
                        'listtext':['display','display only', 'undisplay'],
                        'defaultValue':'display',
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'we'}})
            return idf

    def guiCallback(self):
        val = self.showForm('display')

        if val:
            if val['display']=='display':
                val['only']= 0
                val['negate'] = 0
                del val['display']
            elif val['display']=='display only':
                val['only']= 1
                val['negate'] = 0
                del val['display']
            elif val['display']== 'undisplay':
                val['negate'] = 1
                val['only'] = 0
                del val['display']
                
            val['redraw'] = 1
            apply( self.doitWrapper, (self.vf.getSelection(),), val )

DisplayPathGUI = CommandGUI()
DisplayPathGUI.addMenuCommand('menuRoot', 'Display', 'Path3D',
                               index = 0)


class Nucleic_Acids_properties(MVCommand):
    """The Nucleic_Acids_properties class implements methods for setting
    Nucleic Acids colors and scaling factor.
    \nPackage : Pmv
    \nModule  : extrusionCommands
    \nClass   : Nucleic_Acids_properties
    \nCommand name : Nucleic_Acids_properties
    """
    def __init__(self):
        "Constructor for Nucleic_Acids_properties"
        MVCommand.__init__(self)
        self.color_A =  [1,0,0]
        self.color_C = [1,1,0]
        self.color_U = [1,0.5,0]
        self.color_G = [0,0,1]
        self.color_T = [0,1,0]
        self.scale_purine = self.scale_pyrimidine = 1.3
        self.height_purine = self.height_pyrimidine = 0.4
        self.color_backbone = 1


    def __call__(self, color_A=[1,0,0], color_G=[0,0,1], color_T=[0,1,0],
                 color_C=[1,1,0], color_U=[1,0.5,0],
                 scale_purine = 1.3, scale_pyrimidine = 1.3, 
                 height_purine = 0.4, height_pyrimidine = 0.4, 
                 color_backbone = 1,  **kw):
        """None <- Nucleic_Acids_properties(color_A =  [1,0,0], 
                 color_G = [0,0,1], color_T = [0,1,0],
                 color_C = [1,1,0], color_U = [1,0.5,0],
                 scale_purine = 1.3, scale_pyrimidine = 1.3, 
                 height_purine = 0.4, height_pyrimidine = 0.4, 
                 color_backbone = 1)
        """

        kw['color_A'] = color_A
        kw['color_G'] = color_G
        kw['color_T'] = color_T
        kw['color_U'] = color_U
        kw['scale_purine'] = scale_purine
        kw['scale_pyrimidine'] = scale_pyrimidine
        kw['height_purine'] = height_purine
        kw['height_pyrimidine'] = height_pyrimidine
        kw['color_backbone'] = color_backbone
        self.doitWrapper( ** kw )
        

    def doit(self, color_A=[1,0,0], color_G=[0,0,1], color_T=[0,1,0],
             color_C=[1,1,0], color_U=[1,0.5,0], 
             scale_purine = 1.3, scale_pyrimidine = 1.3, 
             height_purine = 0.4, height_pyrimidine = 0.4, 
             color_backbone = 1):

        self.color_A = color_A
        self.color_C = color_C
        self.color_U = color_U
        self.color_G = color_G
        self.color_T = color_T
        self.scale_purine = scale_purine
        self.scale_pyrimidine = scale_pyrimidine
        self.height_purine = height_purine
        self.height_pyrimidine = height_pyrimidine

        self.color_backbone = color_backbone

        
    def buildFormDescr(self, formName):
        if formName == 'Display':
            idf = InputFormDescr(
                title = "Set Nucleic Acids colors and scaling factor")
            idf.append( {'name':'Purines',
                         'widgetType':Pmw.Group,
                         'container':{'Purines':'w.interior()'},
                         'wcfg':{'tag_text':'Purines'},
                         'gridcfg':{'sticky':'wens'}
                         })
            self.A_rgb = (255*self.color_A[0], 255*self.color_A[1], 
                          255*self.color_A[2])
            self.hex_color_A = "#%02x%02x%02x" % (self.A_rgb)
            idf.append( {'name':'colorA',
                         'widgetType':Tkinter.Button,
                         'tooltip':'Click to change the color',
                         'parent':'Purines',                         
                         'wcfg':{'text':'Adenine',
                                 'command':self.set_color_A,
                                 'font':'Helvetica 12 bold',
                                 'bg':self.hex_color_A,
                                 'width':8,
                                 'relief':'ridge'
                                 },
                         'gridcfg':{'sticky':'w', 'row':0,'column':0}})

            self.G_rgb = (255*self.color_G[0], 255*self.color_G[1], 
                          255*self.color_G[2])
            self.hex_color_G = "#%02x%02x%02x" % (self.G_rgb)
            idf.append( {'name':'colorG',
                         'widgetType':Tkinter.Button,
                         'tooltip':'Click to change the color',
                         'parent':'Purines',
                         'wcfg':{'text':'Guanine',
                                 'command':self.set_color_G,
                                 'font':'Helvetica 12 bold',
                                 'bg':self.hex_color_G,
                                 'width':8,
                                 'relief':'ridge'
                                 },
                         'gridcfg':{'sticky':'w', 'row':1,'column':0}})

            idf.append( {'name': 'height_purine',
                         'widgetType':ExtendedSliderWidget,
                         'parent':'Purines',
                         'wcfg':{'label': "Height",
                                 'minval':0.01,'maxval':1, 'incr': 0.01,
                                 'init':0.4,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'row':0,'column':1,'sticky':'we'}
                         })

            idf.append( {'name': 'scale_purine',
                         'widgetType':ExtendedSliderWidget,
                         'parent':'Purines',
                         'wcfg':{'label': " Scale",
                                 'minval':0.5,'maxval':2, 'incr': 0.01,
                                 'init':1.3,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'row':1,'column':1,'sticky':'we'}
                         })

            idf.append( {'name':'Pyrimidines',
                         'widgetType':Pmw.Group,
                         'container':{'Pyrimidines':'w.interior()'},
                         'wcfg':{'tag_text':'Pyrimidines',},
                         'gridcfg':{'sticky':'wens'}
                         })

            self.T_rgb = (255*self.color_T[0], 255*self.color_T[1], 
                          255*self.color_T[2])
            self.hex_color_T = "#%02x%02x%02x" % (self.T_rgb)
            idf.append( {'name':'colorT',
                         'widgetType':Tkinter.Button,
                         'tooltip':'Click to change the color',
                         'parent':'Pyrimidines',            
                         'wcfg':{'text':'Thymine',
                                 'command':self.set_color_T,
                                 'font':'Helvetica 12 bold',
                                 'bg':self.hex_color_T,
                                 'width':8,
                                 'relief':'ridge'
                                 },
                         'gridcfg':{'sticky':'w', 'row':2,'column':0}})

            self.C_rgb = (255*self.color_C[0], 255*self.color_C[1], 
                          255*self.color_C[2])
            self.hex_color_C = "#%02x%02x%02x" % (self.C_rgb)
            idf.append( {'name':'colorC',
                         'widgetType':Tkinter.Button,
                         'tooltip':'Click to change the color',
                         'parent':'Pyrimidines',
                         'wcfg':{'text':'Cytosine',
                                 'command':self.set_color_C,
                                 'font':'Helvetica 12 bold',
                                 'bg':self.hex_color_C,
                                 'width':8,
                                 'relief':'ridge'
                                 },
                         'gridcfg':{'sticky':'w', 'row':3,'column':0}})
            self.U_rgb = (255*self.color_U[0], 255*self.color_U[1], 
                          255*self.color_U[2])
            self.hex_color_U = "#%02x%02x%02x" % (self.U_rgb)
            idf.append( {'name':'colorU',
                         'widgetType':Tkinter.Button,
                         'tooltip':'Click to change the color',
                         'parent':'Pyrimidines',
                         'wcfg':{'text':'Uracil',
                                 'command':self.set_color_U,
                                 'font':'Helvetica 12 bold',
                                 'bg':self.hex_color_U,
                                 'width':8,
                                 'relief':'ridge'
                                 },
                         'gridcfg':{'sticky':'w', 'row':4,'column':0}})


            idf.append( {'name': 'height_pyrimidine',
                         'widgetType':ExtendedSliderWidget,
                         'parent':'Pyrimidines',
                         'type':int,
                         'wcfg':{'label': "Height",
                                 'minval':0.01,'maxval':1, 'incr':0.01,
                                 'init':0.4,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'row':3,'column':1,'sticky':'we'}
                         })

            idf.append( {'name': 'scale_pyrimidine',
                         'widgetType':ExtendedSliderWidget,
                         'parent':'Pyrimidines',
                         'type':int,
                         'wcfg':{'label': " Scale",
                                 'minval':0.5,'maxval':2, 'incr': 0.01,
                                 'init':1.3,
                                 'labelsCursorFormat':'%1.2f',
                                 'sliderType':'float',
                                 'entrywcfg':{'width':4},
                                 'entrypackcfg':{'side':'right'}},
                         'gridcfg':{'row':4,'column':1,'sticky':'we'}
                         })

            idf.append( {'name':'color_backbone',
                         'widgetType':Tkinter.Checkbutton,
                         'defaultValue':1,                                    
                         'wcfg':{'text':'Color ribbon using these colors',
                                 'variable': Tkinter.IntVar()
                                 },
                         'gridcfg':{'sticky':'ew', 'row':5,'column':0}})
 
            self.idf = idf
            return idf


    def guiCallback(self):
        val = self.showForm('Display')
        if val:
            color_A = [self.A_rgb[0]/255.,self.A_rgb[1]/255.,self.A_rgb[2]/255.]
            color_G = [self.G_rgb[0]/255.,self.G_rgb[1]/255.,self.G_rgb[2]/255.] 
            color_T = [self.T_rgb[0]/255.,self.T_rgb[1]/255.,self.T_rgb[2]/255.]
            color_C = [self.C_rgb[0]/255.,self.C_rgb[1]/255.,self.C_rgb[2]/255.]
            color_U = [self.U_rgb[0]/255.,self.U_rgb[1]/255.,self.U_rgb[2]/255.]
            idf =  self.idf.entryByName
            scale_purine = idf['scale_purine']['widget'].get()
            scale_pyrimidine = idf['scale_pyrimidine']['widget'].get()
            height_purine = idf['height_purine']['widget'].get()
            height_pyrimidine = idf['height_pyrimidine']['widget'].get()
            color_backbone = val['color_backbone']

            self.doitWrapper( color_A, color_G, color_T, color_C, color_U,
                              scale_purine, scale_pyrimidine, 
                              height_purine, height_pyrimidine, 
                              color_backbone)
        else:
            return {}

        
    def set_color_A(self):
        rgb, hex = askcolor(self.hex_color_A)
        if hex:
            self.A_rgb = rgb
            self.idf.entryByName['colorA']['widget'].config(bg=hex)

    def set_color_G(self):
        rgb, hex = askcolor(self.hex_color_G)
        if hex:
            self.G_rgb = rgb
            self.idf.entryByName['colorG']['widget'].config(bg=hex)

    def set_color_T(self):
        rgb, hex = askcolor(self.hex_color_T)
        if hex:
            self.T_rgb = rgb            
            self.idf.entryByName['colorT']['widget'].config(bg=hex)

    def set_color_C(self):
        rgb, hex = askcolor(self.hex_color_C)
        if hex:
            self.C_rgb = rgb            
            self.idf.entryByName['colorC']['widget'].config(bg=hex)

    def set_color_U(self):
        rgb, hex = askcolor(self.hex_color_U)
        if hex:
            self.U_rgb = rgb            
            self.idf.entryByName['colorU']['widget'].config(bg=hex)
        
commandList = [{'name': 'computeSheet2D','cmd': ComputeSheet2DCommand(),
                'gui':None},
               {'name': 'displayPath3D','cmd': DisplayPath3DCommand(),
                'gui':DisplayPathGUI},
               {'name': 'Nucleic_Acids_properties',
                'cmd': Nucleic_Acids_properties(), 'gui':None}
               ]

def initModule(viewer):
    """ initializes commands for secondary structure and extrusion.  Also
    imports the commands for Secondary Structure specific coloring, and
    initializes these commands also. """
    for dict in commandList:
	viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
