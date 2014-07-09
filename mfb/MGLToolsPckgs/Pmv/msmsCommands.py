## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/msmsCommands.py,v 1.149.2.9 2011/10/12 23:38:42 sanner Exp $
# 
# $Id: msmsCommands.py,v 1.149.2.9 2011/10/12 23:38:42 sanner Exp $
#

import types, os
import Tkinter, Pmw
from math import sqrt
import numpy

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom
from MolKit.protein import Residue

from ViewerFramework.VFCommand import CommandGUI
##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     ExtendedSliderWidget, SaveButton, LoadButton
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel     
from mglutil.gui.BasicWidgets.Tk.Dial import Dial
from mglutil.util.misc import ensureFontCase

from DejaVu.IndexedPolygons import IndexedPolygons

from Pmv.displayCommands import DisplayCommand
from Pmv.mvCommand import MVCommand, MVAtomICOM
from Pmv.msmsParser import MSMSParser
from Pmv.guiTools import AugmentedMoleculeChooser, MoleculeChooser
from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent
from Pmv.deleteCommands import AfterDeleteAtomsEvent
import Pmv
if hasattr( Pmv, 'numOfSelectedVerticesToSelectTriangle') is False:
    Pmv.numOfSelectedVerticesToSelectTriangle = 1

    print "LALALALA"
    Pmv.vf.userpref.add('Sharp Color Boundaries for MSMS', 'yes', ('yes','no'),
                  doc="""specifie color boundaries for msms surface (blur or sharp)""",
                 )


class ReadMSMS(MVCommand):
    """Command reads .face and .vert file, creates the msms surface and links it to the selection if can\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : ReadMSMS\n
    Command name : readMSMS\n
    \nSynopsis :\n
    None--->mv.readMSMS(vertFilename,faceFilename,molName=None)\n
    \nRequired Arguments :\n
    vertFilename---name of the .vert file\n 
    faceFilename---name of the .face file\n    
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.msmsFromFile = {}
    
    ###
    ### WIDGETS CALLBACK FUNCTIONS
    ###
    
    def onAddObjectToViewer(self, obj):
        if self.cmdForms.has_key('readMSMS'):
            ebn = self.cmdForms['readMSMS'].descr.entryByName
            w = ebn['molName']['widget']
            molNames = list(w.get())
            molNames.append(obj.name)
            w.clear()
            w.setlist(molNames)
        
    # Need to ask for a .vert file, a .face file and a molecule if want
    # to bind a molecule to the surface

     
    def setEntry_cb(self, filename):
        import os
        file, ext = os.path.splitext(filename)
        ebn = self.cmdForms['readMSMS'].descr.entryByName
        vertEntry = ebn['vertfile']['widget']
        faceEntry = ebn['facefile']['widget']
        if ext == '.vert':
            vertEntry.setentry(filename)
            ffilename = '%s.face'%file
            if os.path.exists(ffilename):
                faceEntry.setentry(ffilename)
        elif ext == '.face':
            faceEntry.setentry(filename)
            vfilename = '%s.vert'%file
            if os.path.exists(vfilename):
                vertEntry.setentry(vfilename)
        else: return
        #entry.setentry(filename)

     
    def buildFormDescr(self, formName):
        if formName == 'readMSMS':
            idf = InputFormDescr(title="READ MSMS")
            idf.append({'name':'vertfile',
                        'required':1,
                        'widgetType':Pmw.EntryField,
                        'tooltip':"Please type in the path to the .vert file \
you wish to parse or click on the BROWSE button to open a file browser",
                        'wcfg':{'labelpos':'w',
                                'label_text':"Vertices Filename",
                                },
                        'gridcfg':{'sticky':'w'}})

            idf.append({'widgetType':LoadButton,
                        'name':'browseVert',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Load file describing msms vertices.',
                                'types':[('MSMS Vert','*.vert')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})
            idf.append({'name':'facefile',
                        'required':1,
                        'tooltip':"Please type in the path to the .face file \
you wish to parse or click on the BROWSE button to open a file browser",
                        'widgetType':Pmw.EntryField,
                        'wcfg':{'labelpos':'w',
                                'label_text':"Faces Filename",
                                },
                        'gridcfg':{'sticky':'w'}})

            idf.append({'widgetType':LoadButton,
                        'name':'browseVert',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Load file describing msms faces.',
                                'types':[('MSMS Face','*.face')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            molNames = ['None',]
            mols = self.vf.getSelection().top
            if mols:
                mols = mols.top.uniq()
                molNames = molNames + mols.name

            idf.append({'name':'molName',
                        'widgetType':Pmw.ScrolledListBox,
                        'tooltip':'Select a molecule to bind to the geometry \
representing this msms surface',
                        'defaultValue':molNames[0],
                        'wcfg':{'label_text':'Molecule Name: ',
                                'labelpos':'nw',
                                'items':molNames,
                                'listbox_selectmode':'single',
                                'listbox_exportselection':0,
                                'usehullsize': 1,
                                'hull_width':100,'hull_height':150,
                                'listbox_height':5,
                                },
                        'gridcfg':{'sticky': 'we'}})
                               
            return idf

    def guiCallback(self):
        val = self.showForm('readMSMS')
        if not val: return
        vertFilename = val['vertfile']
        kw={'redraw':1}
        faceFilename = val['facefile']
        if val['molName'][0] == 'None':
            kw['molName'] = None
        else:
            kw['molName'] = val['molName'][0]
        
        apply(self.doitWrapper, (vertFilename, faceFilename), kw)

    
    def doit(self, vertFilename, faceFilename, molName=None):
        
        vertFName = os.path.split(vertFilename)[1]
        faceFName = os.path.split(faceFilename)[1]
        vertName = os.path.splitext(vertFName)[0]
        faceName = os.path.splitext(faceFName)[0]
        assert vertName == faceName
        msmsParser = MSMSParser()
        self.msmsFromFile[vertName] = msmsParser
        msmsParser.parse(vertFilename, faceFilename)
        self.surf  = IndexedPolygons(vertName+'_msms', visible=1, 
                                pickableVertices=1, protected=True,)
        if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
            self.surf.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False, )
        #self.surf.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
        #self.surf.Set(frontPolyMode=GL.GL_FILL, redo=0)
        self.surf.Set(vertices=msmsParser.vertices, faces=msmsParser.faces,
                      vnormals=msmsParser.normals, tagModified=False)
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.AddObject(self.surf)
        if not molName is None:
                self.vf.bindGeomToMolecularFragment(self.surf, molName,
                                                topCommand=0)

                # highlight selection
                surf = self.surf
                bindcmd = self.vf.bindGeomToMolecularFragment
                selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                if lMolSelectedAtmsDict.has_key(surf.mol):
                    lSelectedAtoms = lMolSelectedAtmsDict[surf.mol]
                    if len(lSelectedAtoms) > 0:
                        lAtomVerticesDict = bindcmd.data[surf.fullName]['atomVertices']
                        highlight = [0] * len(surf.vertexSet.vertices)
                        for lSelectedAtom in lSelectedAtoms:
                            lVertexIndices = lAtomVerticesDict.get(lSelectedAtom, [])
                            for lVertexIndex in lVertexIndices:
                                highlight[lVertexIndex] = 1
                        surf.Set(highlight=highlight)


    def __call__(self, vertFilename, faceFilename, molName=None, **kw):
        """None--->mv.readMSMS(vertFilename,faceFilename,molName=None, **kw)
        """
        kw['molName'] = molName
        kw['redraw'] = 1
        apply(self.doitWrapper, (vertFilename, faceFilename), kw)
       
ReadMSMSGUI = CommandGUI()
ReadMSMSGUI.addMenuCommand('menuRoot', 'Compute', 'Read Molecular Surface',
                           cascadeName='Molecular Surface')

class SaveMSMS(MVCommand):
    """The SaveMSMS commands allows the user to save a chosen MSMS surface (tri-angulated solvant excluded surface) resulting from a calculation.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : SaveMSMS\n
    Command name : saveMSMS\n
    \nDescription:\n
    Two files will be created, one for
    vertices     (.vert) and one for faces (.face). 
    If the component number is 0, files called filename.vert and filename.face
    are created.
    For other components, the component number is inserted in the file name,
    for example for the component number 3 the files are called
    filename_3.vert and filename_3.face.

    The face file contains three header lines followed by one triangle per
    line. The first header line provides a comment and the filename of the
    sphere set.
    The second header line holds comments about the content of the third line.
    The third header line provides the number of triangles, the number of
    spheres in the set, the triangulation density and the probe sphere radius.
    The first three numbers are (1 based) vertex indices. The next field
    can be: 1 for a triangle in a toric reentrant face, 2 for a triangle in
    a spheric reentrant face and 3 for a triangle in a contact face.
    The last number on the line is the (1 based) face number in the
    analytical description of the solvent excluded surface. These values
    are written in the following format ''%6d %6d %6d %2d %6d''.

    The vertex file contains three header lines (similar to the header
    in the .face file) followed by one vertex per line and provides the
    coordinates (x,y,z) and the normals (nx,ny,nz) followed by the number of
    the face (in the analytical description of the solvent excluded surface)
    to which the vertex belongs.
    The vertices of the analytical surface have a value 0 in that field and
    the vertices lying on edges of this surface have nega tive values.
    The next field holds the (1 based) index of the closest sphere.
    The next field is 1 for vertices which belong to toric reentrant faces
    (including vertices of the analytical surface), 2 for vertices inside
    reentrant faces and 3 for vertices inside contact faces.
    Finally, if atom names were present in the input file, the name of the
    closest atom is written for each vertex. These values are written in
    the following format
    ''%9.3f %9.3f %9.3f %9.3f %9.3f %9.3f %7d %7d %2d %s''.\n

    \nSynopsis:\n
    None <- saveMSMS(filename, mol, surfacename, withHeader=1, component=0,
                     format='MS_TSES_ASCII', **kw)\n
    filename : name of the output file\n
    mol      : molecule associated with the surface\n
    surfacename : name of the surface to save\n
    withHeader  : flag to either write the headers or not\n
    component   : specifies which component of the surface to write out\n
    format      : specifies in which format to save the surface. 
                  It can be one of the following ,\n
                  'MS_TSES_ASCII' Triangulated surface in ASCII format\n
                  'MS_ASES_ASCII' Analytical surface in ASCII format. This is
                  actually a discrete representation of the analytical model.\n
                  'MS_TSES_ASCII_AVS' Triangulated surface in ASCII with
                  AVS header\n
                  'MS_ASES_ASCII_AVS'  Analytical surface in ASCII format
                  with AVS header\n

    """

    def onAddCmdToViewer(self):
        self.formats = ['MS_TSES_ASCII', 
                        'MS_ASES_ASCII', 
                        'MS_TSES_ASCII_AVS',
                        'MS_ASES_ASCII_AVS'
                        ]
        # MS_TSES_ASCII : Triangulated surface in ASCII format
        # MS_ASES_ASCII : Analytical surface in ASCII format, which is
        #                 a discrete representation of the analytical model
        # MS_TSES_ASCII_AVS : Triangulated surface in ASCII with AVS header
        # MS_ASES_ASCII_AVS : Analytical surface in ASCII format with AVS
        #                     header

    ### ##################################################################
    ### CALLBACK FUNCTIONS
    ### ##################################################################
    
    def setDial_cb(self, value):
        if not self.cmdForms.has_key('saveMSMS'): return
        # need to get the right surface....
        molName, srfName = value.split('/')
        mol = filter(lambda x: x.name == molName, self.vf.Mols)[0]
        srf = mol.geomContainer.msms[srfName][0]
        maxComponent = srf.rsr.nb-1
        dW = self.cmdForms['saveMSMS'].descr.entryByName['component']['widget']
        dW.configure(max=maxComponent)
        
    def setEntry_cb(self, filename):
        import os
        file = os.path.splitext(filename)[0]
        ebn = self.cmdForms['saveMSMS'].descr.entryByName
        entry = ebn['filename']['widget']
        entry.setentry(file)
        
    ### #################################################################
        
    def buildFormDescr(self, formName):
        if formName=='saveMSMS':
            molSrf = []
            for mol in self.vf.Mols:
                if not hasattr(mol.geomContainer, 'msms') \
                       or not mol.geomContainer.msms.keys():
                    continue
                for surf in mol.geomContainer.msms.keys():
                    molSrf.append(mol.name +'/'+surf)
            if not molSrf: return
            idf = InputFormDescr(title="Save MSMS")
            # Surface to wrire out
            idf.append({'name':'molsrf',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':"Please select the surface to save",
                        'wcfg':{'label_text':'Molecular Surfaces:',
                                'labelpos':'nw',
                                'scrolledlist_items':molSrf,
                                'selectioncommand':self.setDial_cb,
                                'history':0},
                        'defaultValue':molSrf[0],
                        'gridcfg':{'sticky':'we', 'columnspan':2}})
            # Component to write
            idf.append({'name':'component',
                        'widgetType':Dial,
                        'wcfg':{'labCfg':{'side':'left','text':'component'},
                                'type':'int','min':0,'size':50,
                                'max':0,'increment':1,
                                'showLabel':1,'lockMin':1,
                                'lockBMin':1,'lockBMax':1,
                                'lockMax':1,'lockPrecision':1,
                                'lockShowLabel':1, 'lockValue':1,
                                'lockType':1, 'lockContinuous':1,
                                'lockOneTurn':1,
                                },
                        'gridcfg':{'columnspan':2}})
            # Format to use
            tooltip="""Please select one of the following format:\n
MS_TSES_ASCII: Triangulated surface in ASCII format
MS_ASES_ASCII: Analytical surface in ASCII format, which is a discrete
representation of the analytical model.
MS_TSES_ASCII_AVS: Triangulated surface in ASCII with AVS header
MS_ASES_ASCII_AVS: Analytical surface in ASCII format with AVS header
"""
            idf.append({'name':'format',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':tooltip,
                        'defaultValue':self.formats[0],
                        'wcfg':{'label_text':'Format:',
                                'labelpos':'nw',
                                'scrolledlist_items':self.formats},
                        'gridcfg':{'sticky':'we', 'columnspan':2}})

            # Whether or not to write header.
            idf.append({'name':'withHeader',
                        'widgetType':Tkinter.Checkbutton,
                        'wcfg':{'text':'Write Header:',
                                'variable':Tkinter.IntVar()},
                        'gridcfg':{'sticky':'we'}
                        })
            
            # File to create
            idf.append({'name':'filename',
                        'widgetType':Pmw.EntryField,
                        'tooltip':'Enter the filename, a filename.face \
and filename.vert will be created.',
                        'wcfg':{'label_text':'Filename:',
                                'labelpos':'w'},
                        'gridcfg':{'sticky':'we'},
                        })

            idf.append({'widgetType':SaveButton,
                        'name':'filebrowse',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':'Save In File ...',
                                'types':[('MSMS Face','*.face'),
                                         ('MSMS Vert', '*.vert')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            return idf
            
    def guiCallback(self):
        # 1- the surface to save
        if self.cmdForms.has_key('saveMSMS'):
            w = self.cmdForms['saveMSMS'].descr.entryByName['molsrf']['widget']
            for mol in self.vf.Mols:
                if not hasattr(mol.geomContainer, 'msms') or \
                       not mol.geomContainer.msms.keys():
                    continue
                molsrf = []
                for surf in mol.geomContainer.msms.keys():
                    molsrf.append(mol.name +'/'+surf)
            w.setlist(molsrf)
            
        val = self.showForm('saveMSMS', force=1)
        kw = {}
        if not val: return
        if val.has_key('filename'):
            filename = val['filename']
        kw['format'] = val['format'][0]
        kw['component'] = val['component']
        kw['withHeader'] = val['withHeader']
        molsrf = val['molsrf'][0]
        molname, surfName = molsrf.split('/')
        apply(self.doitWrapper, (filename, molname, surfName), kw)

        
    def doit(self, filename, molName, surfName, withHeader=True, component=0,
             format="MS_TSES_ASCII"):
        mol = self.vf.getMolFromName(molName)
        if mol is None: return
        gc = mol.geomContainer
        if not gc.msms.has_key(surfName): return
        msmsSurf = gc.msms[surfName][0]
        msmsAtms = gc.msms[surfName]
        from mslib import msms
        if not format in self.formats:
            format = "MS_TSES_ASCII"
        format = getattr(msms, format)
        if component is None : component = 0
        elif not component in range( msmsSurf.rsr.nb ):
            self.warningMsg("%s is an invalid component"%component)
            return
        msmsSurf.write_triangulation(filename, no_header=not withHeader,
                                     component=component, format=format)


    def __call__(self, filename, molName, surfName, withHeader=True,
                 component=None, format="MS_TSES_ASCII", **kw):
        """None <--- mv.saveMSMS(filename, mol, surface, withHeader=True,component=None, format='MS_TSES_ASCII', **kw)\n
        \nRequired Arguments:\n
        filename --- path to the output file without an extension two files will be created filename.face and a filename.vert\n 
        mol      --- Protein associated to the surface\n
        surface  --- surface name\n

        \nOptional Arguments:\n
        withHeader --- True Boolean flag to specify whether or not to write the headers in the .face and the .vert files\n
        component  --- msms component to save by default None\n
        format     --- format in which the surface will be saved. It can be,\n        
        MS_TSES_ASCII: Triangulated surface in ASCII format.\n
        MS_ASES_ASCII: Analytical surface in ASCII format.This is a discrete representation of the analytical model.MS_TSES_ASCII_AVS: Triangulated surface in ASCII with AVS header\n
        MS_ASES_ASCII_AVS: Analytical surface in ASCII format with AVS header\n
        
        """
        if not molName or not filename or not surfName: return
        kw['withHeader'] = withHeader
        kw['component'] = component
        kw['format'] = format
        apply(self.doitWrapper, (filename, molName, surfName), kw)
        

SaveMSMSGUI = CommandGUI()
SaveMSMSGUI.addMenuCommand('menuRoot', 'Compute', 'Save Molecular Surface',
                           cascadeName='Molecular Surface')

class ComputeMSMS(MVCommand, MVAtomICOM):
    """The computeMSMS command will compute a triangulated solvent excluded surface for the current selection.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : ComputeMSMS\n
    Command name : computeMSMS\n
    \nSynopsis :\n
    None <--- mv.computeMSMS(nodes, surfName=None, pRadius=1.5,
                           density=1.0, perMol=True, noHetatm=False,
                           display=1)\n
    \nRequired Arguments :\n
        nodes --- current selection\n
    \nOptional Arguments:\n
    surfName --- name of the surfname which will be used as the key in
                mol.geomContainer.msms dictionary. If the surfName is
                already a key of the msms dictionary the surface is
                recreated. By default mol.name-MSMS\n
    pRadius  --- probe radius (1.5)\n
    density --- triangle density to represent the surface. (1.0)\n
    perMol  --- when this flag is True a surface is computed for each molecule
                having at least one node in the current selection
                else the surface is computed for the current selection.
                (True)\n
    noHetatm --- when this flag is True hetero atoms are ignored, unless
                 all atoms are HETATM\n
    display --- flag when set to 1 the displayMSMS will be executed to
                display the new msms surface.\n
                    
    """

    ###
    ###COMMAND METHODS
    ###
    def __init__(self, func=None):
        MVCommand.__init__(self)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.objArgOnly


    def checkDependencies(self, vf):
        import mslib


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('assignAtomsRadii'):
            self.vf.loadCommand('editCommands', ['assignAtomsRadii',],
                                topCommand=0)

    def onAddObjectToViewer(self, obj):
        """
        """
        #if not self.vf.hasGui: return
        geomC = obj.geomContainer
        geomC.nbSurf = 0
        geomC.msms = {}
        geomC.msmsAtoms = {} # AtomSets used for surfaces
        geomC.msmsCurrentDisplay = {} # Dictionary whose keys are 'surfaceNames'
                                      # and whose values are strings
                                      # to be used to undo either 'displayMSMS'
                                      # or 'displayBuriedTriangles', restoring
                                      # the geometry 'surfaceName' to its
                                      # previous state. This dictionary is 
                                      # necessary because these two different commands 
                                      # can effect changes to the same geometry,
                                      # thus making the undo dependent on the
                                      # command sequence....
                                      # 1. displayMSMS followed by displayMSMS is
                                      # simplest to undo: invoke the second displayMSMS 
                                      # cmd with negate flag on
                                      # 2. displayMSMS followed by displayBuriedTriangles
                                      # requires displayMSMS with
                                      # geomContainer.atoms['surfaceName']
                                      # 3. displayBuriedTriangles followed by displayMSMS 
                                      #  AND
                                      # 4. displayBuriedTriangles followed by displayBuriedTriangles
                                      # requires geom.Set(faces=currentFaces) 
                                      # NOTE: correctly updating msmsCurrentDisplay needs testing

    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        """Function called to map atomic properties to the vertices of the
        geometry"""
        if len(atoms)==0: return None

        geomC = geom.mol.geomContainer
        surfName = geom.userName
        surf = geomC.msms[surfName][0]
        surfNum = geomC.msms[surfName][1]
        # array of colors of all atoms for the msms.
        prop = []
        if propIndex is not None:
            for a in geomC.msmsAtoms[surfName].data:
                d = getattr(a, propName)
                prop.append( d[surfName] )
        else:
            for a in geomC.msmsAtoms[surfName].data:
                prop.append( getattr(a, propName) )
        # find indices of atoms with surface displayed
        atomIndices = []
        indName = '__surfIndex%d__'%surfNum
        for a in atoms.data:
            atomIndices.append(getattr(a, indName))
        # get the indices of closest atoms
        dum1, vi, dum2 = surf.getTriangles(atomIndices, keepOriginalIndices=1)
        # get lookup col using closest atom indicies
        mappedProp = Numeric.take(prop, vi[:, 1]-1).astype('f')
        if hasattr(geom,'apbs_colors'):
            colors = []
            for i in range(len(geom.apbs_dum1)):
                ch = geom.apbs_dum1[i] == dum1[0]
                if not 0 in ch:
                    tmp_prop = mappedProp[0]
                    mappedProp = mappedProp[1:]
                    dum1 = dum1[1:]
                    if    (tmp_prop[0] == [1.5]) \
                      and (tmp_prop[1] == [1.5]) \
                      and (tmp_prop[2] == [1.5]):
                        colors.append(geom.apbs_colors[i][:3])
                    else:
                        colors.append(tmp_prop)
                    if dum1 is None:
                        break
            mappedProp = colors            
        return mappedProp


    def pickedVerticesToBonds(self, geom, parts, vertex):
        return None


    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert picked vertices into atoms"""

        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet

        surfName = geom.userName
        geomC = geom.mol.geomContainer
        surfNum = geomC.msms[surfName][1]
        indName = '__surfIndex%d__'%surfNum
       
        #FIXME: building atomindices is done in DisplayMSMS
        # should re-use it
        mol = geom.mol
        atomindices = []
        indName = '__surfIndex%d__'%surfNum
        al = mol.geomContainer.atoms[surfName]
        for a in al:
            atomindices.append(getattr(a, indName))

        surf = geomC.msms[surfName][0]
        dum1, vi, dum2 = surf.getTriangles(atomindices, keepOriginalIndices=1)

        l = []
        allAt = geomC.msmsAtoms[surfName]
        for i in vertInd:
            l.append(allAt[vi[i][1]-1])
        return AtomSet( AtomSet( l ) )


    def __call__(self, nodes, surfName='MSMS-MOL', pRadius=1.5,
                 density=3.0, perMol=True, noHetatm=False, display=True,
                 hdset='None', hdensity=6.0, **kw):
        """None <- mv.computeMSMS(nodes, surfName='MSMSMOL', pRadius=1.5,density=1.0,perMol=True, display=1)\n
\nRequired Arguments :\n
    nodes ---  atomic fragment (string or objects)\n
\nOptional Arguments :\n
    surfName --- name of the surfname which will be used as the key in
                   mol.geomContainer.msms dictionary. If the surfName is
                   already a key of the msms dictionary the surface is
                   recomputed. (default MSMS-MOL)\n
    pRadius  --- probe radius (1.5)\n
    density  --- triangle density to represent the surface. (1.0)\n
    perMol   --- when this flag is True a surface is computed for each 
                 molecule having at least one node in the current selection
                 else the surface is computed for the current selection.
                 (True)\n
    noHetatm --- when this flag is True hetero atoms are ignored, unless
                 all atoms are HETATM.\n
    display  --- flag when set to 1 the displayMSMS will be executed with
                 the surfName else not.\n
    hdset    --- Atom set (or name) for which high density triangualtion will
                 be generated
    hdensity --- vertex density for high density
"""
        nodes = self.vf.expandNodes(nodes)
        kw['surfName'] = surfName
        kw['pRadius'] = pRadius
        kw['density'] = density
        kw['perMol'] = perMol
        kw['noHetatm'] = noHetatm
        kw['display'] = display
        kw['hdset'] = hdset
        kw['hdensity'] = hdensity
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply(self.doitWrapper, (nodes,), kw)
            

    def fixValues(self, val):
        if val['hdset'] is None:
            return val
        if val['hdset'] == 'None':
            val['hdset'] = None
            return val
        hdsetName = val['hdset'][0]
        if hdsetName=='None' or hdsetName=='':
            val['hdset'] = None
        return val

    
    def guiCallback(self):
        if self.cmdForms.has_key('default'):
            self.updateCBB()
        val = self.showForm('default')
        if not val: return

##         if type(val['surfName']) is types.TupleType:
##             surfName = val['surfName'][0]
##         else:
##             surfName = val['surfName']
        surfName = 'MSMS-MOL'

        val = self.fixValues(val)

        apply(self.doitWrapper, (self.vf.getSelection(), surfName), val)


    def doit(self, nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
             perMol=True, noHetatm=False, display=True, hdset=None,
             hdensity=6.0, **kw):
        """Required Arguments:\n        
        nodes   ---  current selection\n
        surfName --- name of the surfname which will be used as the key in
                    mol.geomContainer.msms dictionary.\n
        \nOptional Arguments:  \n      
        pRadius  --- probe radius (1.5)\n
        density  --- triangle density to represent the surface. (1.0)\n
        perMol   --- when this flag is True a surface is computed for each 
                    molecule having at least one node in the current selection
                    else the surface is computed for the current selection.
                    (True)\n
        noHetatm --- when this flag is True hetero atoms are ignored, unless
                 all atoms are HETATM.\n
        display  --- flag when set to True the displayMSMS will be executed with
                    the surfName else not.\n
        hdset    --- Atom set for which high density triangualtion 
                     will be generated
        hdensity --- vertex density for high density
        """
        from mslib import MSMS
        if nodes is None or not nodes:
            return
        # Check the validity of the input
        if not type(density) in [types.IntType, types.FloatType] or \
           density < 0: return 'ERROR'
        if not type(pRadius) in [types.IntType, types.FloatType] or \
           pRadius <0: return 'ERROR'

        if hdset=='None':
            hdset=None
        if hdset:
            if self.vf.sets.has_key(hdset[0]):
                hdset = self.vf.sets[hdset[0]].findType(Atom)
            else:
                self.warningMsg("set %s not found"%hdset)
            for a in hdset:
                a.highDensity = True

        # get the set of molecules and the set of atoms per molecule in the
        # current selection
        if perMol:
            molecules = nodes.top.uniq()
            atmSets = [x.allAtoms for x in molecules]
        else:
            molecules, atmSets = self.vf.getNodesByMolecule(nodes, Atom)

        for mol, atms in map(None, molecules, atmSets):
            if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
                self.vf.dashboard.resetColPercent(
                    mol, '_showMSMSStatus_%s'%surfName)
                
            if noHetatm:
                ats = [x for x in atms if not x.hetatm]
                if len(ats)==0:
                    ats = atms
                atms = AtomSet(ats)

            if not surfName:
                surfName = mol.name + '-MSMS'
            geomC = mol.geomContainer

            if not geomC.msms.has_key(surfName):
                # Create a new geometry
                # be stored.
                g = IndexedPolygons(surfName, pickableVertices=1, protected=True,)
                if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                    g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
                g.userName = surfName
                geomC.addGeom(g)
                self.managedGeometries.append(g)
                geomC.geomPickToAtoms[surfName] = self.pickedVerticesToAtoms
                geomC.geomPickToBonds[surfName] = None
                # This needs to be replaced by string to not have a direct
                # dependency between PMV and OPENGL...
                #g.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
                #g.Set(frontPolyMode=GL.GL_FILL, redo=0)
                # g.RenderMode('GL_FILL', face='GL_FRONT', redo=0)
                geomC.atomPropToVertices[surfName] = self.atomPropToVertices
                # Create the key for this msms for each a.colors dictionary.
                for a in mol.allAtoms:
                    a.colors[surfName] = (1.,1.,1.)
                    a.opacities[surfName] = 1.0
                # Created a new geometry needs to update the form if exists.
                #if self.cmdForms.has_key('default'):
                #    self.updateForm(surfName)

            # update the existing geometry
            geomC.msmsAtoms[surfName]=atms[:]
            geomC.atoms[surfName] = AtomSet([]) #atms

            i=0  # atom indices are 1-based in msms
            indName = '__surfIndex%d__'%geomC.nbSurf
            hd = []
            surf = []
            for a in atms:
                setattr(a, indName, i)
                i = i + 1
                surf.append(1)
                if hasattr(a, 'highDensity'):
                    hd.append(1)
                else:
                    hd.append(0)

            # get atm radii if necessary
            try:
                atmRadii = atms.radius
            except:
                atmRadii = self.vf.assignAtomsRadii(mol, united=0,
                                                    topCommand=0)
                atmRadii = atms.radius
              
            # build an MSMS object and compute the surface
            srf = MSMS(coords=atms.coords, radii=atmRadii, surfflags=surf,
                       hdflags=hd)
            srf.compute(probe_radius=pRadius, density=density,
                        hdensity=hdensity)

            # save computation parameters inside srf
            srf.probeRadius = pRadius
            srf.density = density
            srf.perMol = perMol
            srf.surfName = surfName
            srf.noHetatm = noHetatm
            srf.hdset = hdset
            srf.hdensity = hdensity
                
            if mol.geomContainer.msms.has_key(surfName):
                #print "freeing MSMSC %s"%surfName
                oldsrf = mol.geomContainer.msms[surfName][0]
                del oldsrf
                
            # save a pointer to the MSMS object
            mol.geomContainer.msms[surfName] = (srf, geomC.nbSurf)
            # Increment the nbSurf counter
            geomC.nbSurf += 1

        if hdset:
            for a in hdset:
                del a.highDensity

        if display:
            if not self.vf.commands.has_key('displayMSMS'):
                self.vf.loadCommand("msmsCommands", ['displayMSMS',],
                                    topCommand=0)
            if nodes.stringRepr is not None:
                geomC.msmsCurrentDisplay[surfName] = \
                    "self.displayMSMS('%s', surfName=['%s'], negate=0, only=0, nbVert=%d, topCommand=0)" %(nodes.stringRepr, surfName, Pmv.numOfSelectedVerticesToSelectTriangle) 
            else:
                geomC.msmsCurrentDisplay[surfName] = \
                    "self.displayMSMS('%s', surfName=['%s'], negate=0, only=0, nbVert=%d, topCommand=0)" %(nodes.full_name(), surfName, Pmv.numOfSelectedVerticesToSelectTriangle)            

            self.vf.displayMSMS(nodes, surfName=[surfName,], negate=0, only=1,
                                nbVert=Pmv.numOfSelectedVerticesToSelectTriangle, log=0)
        redraw = False
        if kw.has_key("redraw") : redraw=True
        event = EditGeomsEvent('msms_c', [nodes,[surfName, pRadius, density,
						perMol, display, hdset, hdensity]])
        self.vf.dispatchEvent(event)


    def buildFormDescr(self, formName='default'):
        if formName == 'default':
            idf = InputFormDescr(title ="MSMS Parameters Panel:")
            mols = self.vf.getSelection().top.uniq()
##             sNames = []
##             for mol in mols:
##                 sNames += mol.geomContainer.msms.keys()

            defaultValues = self.getLastUsedValues()
##             name = defaultValues['surfName'].replace('_', '-')
##             if name not in sNames:
##                 sNames.insert(0, name)
##             print 'VVVVVVVVVVV', defaultValues
##             if not sNames:
##                 sNames = ['MSMS-MOL']
##                 idf.append({'widgetType':Pmw.ComboBox,
##                             'name':'surfName',
##                             'required':1,
##                             'tooltip': "Please type-in a new name or chose \
## one from the list below\n '_' are not accepted.",
##                             'wcfg':{'labelpos':'nw',
##                                     'label_text':'Surface Name: ',
##                                     'entryfield_validate':self.entryValidate,
##                                     'entryfield_value':'MSMS-MOL',
##                                     'scrolledlist_items':[],
##                                     },
##                             'gridcfg':{'sticky':'we'}})
##             else:
##             idf.append({'widgetType':Pmw.ComboBox,
##                             'name':'surfName',
##                             'required':1,
##                             'tooltip': "Type-in a new name or chose \
## one from the list below\n '_' cannot be used.",
##                             'defaultValue': name,
##                             'wcfg':{'labelpos':'nw',
##                                     'label_text':'Surface Name: ',
##                                     'entryfield_validate':self.entryValidate,
##                                     'scrolledlist_items':sNames,
##                                     'entryfield_value':name,
##                                 },
##                         'gridcfg':{'sticky':'we'}})
            
            names = ['None']+self.vf.sets.keys()
            names.sort()
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'hdset',
                        'required':0,
                        'tooltip': """Choose a set defining the part of the surface
that should be triangualte at high density""",
                        'defaultValue': str(defaultValues['hdset']),
                        'wcfg':{'labelpos':'nw',
                                'label_text':'High density surface set: ',
                                'scrolledlist_items':names,
                                },
                        'gridcfg':{'sticky':'we'}})

##             idf.append({'name':'perMol',
##                         'tooltip':"""When checked surfaces will be computed using all atoms (selected or not) of
## each molecule.  If unchecked, the unselected atoms are ignored during the
## calculation.""",
##                         'widgetType':Tkinter.Checkbutton,
##                         'defaultValue': defaultValues['perMol'],
##                         'wcfg':{'text':'Per Molecule',
##                                 'variable':Tkinter.IntVar(),
##                                 'command':self.perMol_cb},
##                         'gridcfg':{'sticky':'we'}
##                         })
            

            idf.append({'name':'noHetatm',
                        'tooltip':"""When checked surfaces will be computed ignoring hetero atoms.""",
                        'widgetType':Tkinter.Checkbutton,
                        'defaultValue': defaultValues['noHetatm'],
                        'wcfg':{'text':'No Hetero Atoms',
                                'variable':Tkinter.IntVar(),
                                },#'command':self.noHetatm_cb},
                        'gridcfg':{'sticky':'we'}
                        })
            
            idf.append({'name':'saveSel',
                        'widgetType':Tkinter.Button,
                        'tooltip':"""This button allows the user to save the current selection as a set.
The name of the msms surface will be used as the name of the set""",
                        'wcfg':{'text':'Save Current Selection As Set',
                                'state':'disabled',
                                'command':self.saveSel_cb},
                        'gridcfg':{'sticky':'we'}})
            
            idf.append({'name':'pRadius',
                    'widgetType':ThumbWheel,
                    'tooltip':
                       """Right click on the widget to type a value manually""",
                    'gridcfg':{'sticky':'we'},
                    'wcfg':{'value':1.5, 'oneTurn':2, 
                        'type':'float',
                        'value': defaultValues['pRadius'],
                        'increment':0.1,
                        'precision':1,
                        'continuous':False,
                        'wheelPad':2,'width':145,'height':18,
                         'labCfg':{'text':'Probe Radius    '},
                        }
                    })
            
            idf.append({'name':'density',
                    'widgetType':ThumbWheel,
                    'tooltip':"""Vertex density use for triangulating the surface.
Right click on the widget to type a value manually""",
                    'gridcfg':{'sticky':'we'},
                    'wcfg':{'oneTurn':2, 
                        'type':'float',
                        'value': defaultValues['density'],
                        'increment':0.1,
                        'precision':1,
                        'continuous':False,
                        'wheelPad':2,'width':145,'height':18,
                         'labCfg':{'text':'Density         '},
                         
                        }
                    })

            idf.append({'name':'hdensity',
                    'widgetType':ThumbWheel,
                    'tooltip':"""Vertex density use for triangulating the high density part of the surface.
Right click on the widget to type a value manually""",

                    'gridcfg':{'sticky':'we'},
                    'wcfg':{'oneTurn':2, 
                        'type':'float',
                        'value': defaultValues['hdensity'],
                        'increment':0.1,
                        'precision':1,
                        'continuous':False,
                        'wheelPad':2,'width':145,'height':18,
                         'labCfg':{'text':'High Density    '},
                        }
                    })


            return idf

    ###
    ### HELPER METHODS
    ###
    def setTexCoords(self, mol, values):
        srf = mol.geomContainer.msms
        lookup = mol.geomContainer.texCoordsLookup["msms"]
        g = mol.geomContainer.geoms['msms']
        if g.texture:
            g.texture.auto=0
        if srf:
            vf, vi, f = srf.getTriangles()
            values.shape = (-1,1)
            assert len(values)==len(vf)
            i = 0
            for v in vf:
                lookup[str(v[0])+str(v[1])+str(v[2])] = values[i]
                i = i + 1
        self.updateTexCoords(mol)
        
                
    def updateTexCoords(self, mol):
        lookup = mol.geomContainer.texCoordsLookup["msms"]
        g = mol.geomContainer.geoms['msms']
        tx = map(lambda v, l=lookup: l[str(v[0])+str(v[1])+str(v[2])],
                 g.vertexSet.vertices.array)
        tx = Numeric.array(tx)
        tx.shape = (-1,1)
        g.Set( textureCoords=tx, tagModified=False )



    def updateForm(self, surfName):
        ebn = self.cmdForms['default'].descr.entryByName
        w = ebn['surfName']['widget']
        allitems = w.get()
        if not surfName in allitems:
            w.insert('end',surfName)

    ###
    ### GUI CALLBACKS
    ###
    def entryValidate(self, text):
        """
        Method to validate the name of the msms surface. This name
        will be used by other command to build Pmw widget so it can't
        contain an '_'.
        """
        if '_' in text:
            return Pmw.ERROR
        else:
            return Pmw.OK
        
        
    def updateCBB(self):
        defaultValues = self.getLastUsedValues()
        ebn = self.cmdForms['default'].descr.entryByName
##         cbb = ebn['surfName']['widget']
##         typein = cbb.get()
##         sel = cbb.getcurselection()
##         if typein in sel: return
##         sNames = []
##         mols = self.vf.getSelection().top.uniq()
##         for mol in mols:
##             sNames += mol.geomContainer.msms.keys()
##         if not typein in sNames:
##             return 
##         else:
##             cbb.setlist(sNames)
##             cbb.selectitem(typein)

        names = ['None']+self.vf.sets.keys()
        names.sort()
        cbb = ebn['hdset']['widget']
        cbb.setlist(names)
        if defaultValues['hdset'] is not None:
            cbb.selectitem(str(defaultValues['hdset'][0])) #str(None)->"None"

    def perMol_cb(self, event=None):
        if not self.cmdForms.has_key('default'):
            return
        ebn = self.cmdForms['default'].descr.entryByName
        perMol = ebn['perMol']['wcfg']['variable'].get()
        saveBut = ebn['saveSel']['widget']
        if perMol:
            saveBut.configure(state='disabled')
            ebn['saveSel']['wcfg']['state']='disabled'
        else:
            saveBut.configure(state='normal')
            ebn['saveSel']['wcfg']['state']='normal'

    def saveSel_cb(self, event=None):
        self.cmdForms['default'].releaseFocus()
        name=self.vf.saveSet.guiCallback()
        self.cmdForms['default'].grabFocus()
        cbb = self.cmdForms['default'].descr.entryByName['surfName']['widget']
        cbb.setentry(name)
                   
ComputeMSMSGUI = CommandGUI()
ComputeMSMSGUI.addMenuCommand('menuRoot', 'Compute','Compute Molecular Surface',
                                 cascadeName='Molecular Surface')


from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent

class DisplayMSMS(DisplayCommand):
    """The displayMSMS command allows the user to display/undisplay or display only the given MSMS surface corresponding to the current selection.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : DisplayMSMS\n
    Command name : displayMSMS\n
    \nRequired Arguments:\n
    nodes  --- TreeNodeSet holding the current selection\n
    \nOptional Arguments:\n
    only     --- flag when set to 1 only the current selection will be
              displayed\n
    negate   --- flag when set to 1 undisplay the current selection\n
    surfName --- name of the selection, default = 'all'\n
    nbVert  ---  Nb of vertices per triangle needed to select a triangle.\n
    
    """

    def onAddCmdToViewer(self):
        self.vf.registerListener(AfterDeleteAtomsEvent, self.handleDeleteAtoms)
        self.vf.registerListener(EditAtomsEvent, self.handleEditEvent)
        #self.vf.registerListener(AddAtomsEvent, self.updateGeom)



    def handleDeleteAtoms(self, event):
        """Function to update geometry objects created by this command
upon atom deletion.
\nevent --- instance of a VFEvent object
"""
        # split event.objects into atoms sets per molecule
        molecules, ats = self.vf.getNodesByMolecule(event.objects)

        # loop over molecules to update geometry objects
        for mol, atomSet in zip(molecules, ats):
            geomC = mol.geomContainer
            for srfName, srfc in geomC.msms.items():
                ats = geomC.atoms[srfName]
                srf = srfc[0]
                if len(ats & atomSet): #deleted atoms are in this surface
                    
                    newAts = ats-atomSet
                    kw = {}
                    kw['surfName'] = srfName
                    kw['pRadius'] = srf.probeRadius
                    kw['density'] = srf.density
                    kw['perMol'] = srf.perMol
                    kw['noHetatm'] = srf.noHetatm
                    kw['hdset'] = srf.hdset
                    kw['hdensity'] = srf.hdensity
                    kw['topCommand'] = 0
                    kw['display'] = 1
                    
                    del srf # free old C structure
                    #print 'recompute MSMS', len(newAts), kw
                    self.vf.computeMSMS( newAts, **kw)

    def handleEditEvent(self, event):
        from mslib import msms

        # build list of optional command arguments
        doitoptions = self.lastUsedValues['default']
        doitoptions['redraw']=1
        doitoptions['topCommand']=0

        molecules, atomSets = self.vf.getNodesByMolecule(event.objects, Atom)
        for mol, atoms in zip(molecules, atomSets):

            geomC = mol.geomContainer

            # loop over all surfaces
            for name in geomC.msms.keys():
                g = geomC.geoms[name]

                # get the atom indices
                surfc = geomC.msms[name][0]
                surfNum = geomC.msms[name][1]
                indName = '__surfIndex%d__'%surfNum
                atomindices = []
                coords = []
                for a in atoms:
                    atomindices.append(a.__dict__[indName])
                    coords.append( list(a.coords)+[a.radius] )
                        
                msms.MS_reset_atom_update_flag(surfc)
                i = msms.MS_updateSpheres(surfc, len(atoms), atomindices,
                                          coords)
                rs = surfc.rsr.fst
                # this would only be needed once initially
                msms.MS_tagCloseProbes(surfc, rs, 15.0)
                mode = 0
                density = surfc.density
                updateNum = 1
                i =msms.MS_update_surface(surfc, rs, mode, density, updateNum)
                if i==msms.MS_ERR:
                    print "ERROR while updating RS %d %s\n"%(updateNum, "Error")#msms.MS_err_msg) MS_err_msg not exposed
                    return
                #msms.MS_update_SES_area(surfc, rs.ses)
                vf, vi, f = surfc.getTriangles()
                col = mol.geomContainer.getGeomColor(name)

                g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6],
                       faces=f[:,:3], materials=col, inheritMaterial=False, 
                       tagModified=False )

                

    def setupUndoBefore(self, nodes, surfName='all', negate=False, only=False, nbVert=1):
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        for mol, atoms in map(None, molecules, atomSets):
            geomC = mol.geomContainer
            surfNames = geomC.msms.keys()
            if surfName == 'all':
                names = surfNames
            elif not type(surfName) in [types.ListType, types.TupleType]:
                if not surfName in surfNames:
                    continue
                else:
                    names = [surfName,]
            else:
                names = surfName
            for n in names: 
                # undo depends on whether current msms geometry resulted from
                # displayMSMS OR from displayBuriedTriangles
                # for each molecule, this is tracked in dictionary stored as
                # molecule.geomContainer.msmsCurrentDisplay[surfName]
                #possibly surface was previously computed but never displayed
                lastCmd = geomC.msmsCurrentDisplay.get(n, "")
                if lastCmd=="" or lastCmd.find('displayMSMS')>-1:
                    #no previous geometry OR the geometry resulted from displayMSMS 
                    not_negate =  not negate
                    if not geomC.atoms.has_key(n):
                        continue
                    ats = geomC.atoms[n]
                    if not len(ats):
                        continue
                    #FIX THIS SHOULD IT REALLY BE NOT-NEGATE???
                    old_atoms_name = self.vf.undo.saveUndoArg(ats)
                    undoCmd = "self.displayMSMS(%s, surfName=['%s'], negate=%d, only=%d, nbVert=%d, topCommand=0)" %(old_atoms_name, n, not_negate, only, nbVert)
                    #undoCmd = "self.displayMSMS('%s', surfName=['%s'], negate=%d, only=%d, nbVert=%d, topCommand=0)" %(old_atoms_name, n, not_negate, only, nbVert)
                    self.vf.undo.addEntry((undoCmd), (self.name))
                elif lastCmd.find('displayBuried')>-1:
                    #the geometry resulted from displayBuriedTriangles 
                    #get a handle to the IndexedPolygon geometry
                    g = geomC.geoms[n]
                    #save the current verts
                    old_vertices_name = self.vf.undo.saveUndoArg(g.getVertices())
                    #save the current faces
                    old_faces_name = self.vf.undo.saveUndoArg(g.getFaces())
                    #save the current vnormals
                    old_vnormals_name = self.vf.undo.saveUndoArg(g.getVNormals())
                    #save the current front_colors
                    front_colors = g.materials[GL.GL_FRONT].getState()
                    old_front_name = self.vf.undo.saveUndoArg(front_colors)
                    #save the current back_colors
                    back_colors = g.materials[GL.GL_BACK].getState()
                    old_back_name = self.vf.undo.saveUndoArg(back_colors)
                    undoCmd = "from opengltk.OpenGL import GL;g = self.expandNodes('%s')[0].geomContainer.geoms['%s'];g.Set(vertices=%s, faces=%s, vnormals=%s);apply(g.materials[GL.GL_FRONT].Set, (), %s);apply(g.materials[GL.GL_BACK].Set, (), %s)" %(mol.name, n, old_vertices_name, old_faces_name, old_vnormals_name, old_front_name, old_back_name)
                    geomC.msmsCurrentDisplay[n] = undoCmd
                    self.vf.undo.addEntry((undoCmd), (self.name))



    def doit(self, nodes, surfName='all', negate=False, only=False,
             nbVert=Pmv.numOfSelectedVerticesToSelectTriangle, **kw):
        #print "DisplayMSMS.doit", 
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        names = None

        rsetOn = AtomSet([])
        rsetOff = AtomSet([])

        for mol, atoms in zip(molecules, atomSets):
            geomC = mol.geomContainer
            surfNames = geomC.msms.keys()
            if surfName == 'all':
                names = surfNames

            elif not type(surfName) in [types.ListType, types.TupleType]:
                if not surfName in surfNames:
                    return
                else:
                    names = [surfName,]
            else:
                names = surfName
                
            for sName in names:
                # Make sure that the surface exists for this molecule.
                if not sName in surfNames: continue
                # first get the atoms for this molecule in set of atoms used
                # for that surface
                allAtms = geomC.msmsAtoms[sName]
                atm = allAtms.inter(atoms)

                # get the set of atoms with surface displayed
                lSet = geomC.atoms[sName]

                ##if negate, remove current atms from displayed set
                if negate:
                    setOff = atm
                    setOn = None
                    lSet = lSet - atm

                ##if only, replace displayed set with current atms 
                else:
                    if only:
                        setOff = lSet - atm
                        setOn = atm
                        lSet = atm
                    else:
                        lSet = atm + lSet
                        setOff = None
                        setOn = lSet

                if lSet is None:
                    print "skipping ", sName
                    continue
                if setOn: rsetOn += setOn
                if setOff: rsetOff += setOff
                
                geomC.atoms[sName]=lSet

                # get the msms surface object for that molecule
                srf = geomC.msms[sName][0]

                # get the atom indices
                surfNum = geomC.msms[sName][1]
                indName = '__surfIndex%d__'%surfNum
                atomindices = []
                for a in lSet:
                    atomindices.append(getattr(a, indName))

                g = geomC.geoms[sName]
                if lSet.stringRepr is not None:
                    geomC.msmsCurrentDisplay[sName] = "self.displayMSMS('%s', surfName=['%s'], negate=%d, only=%d, nbVert=%d, topCommand=0)" %(lSet.stringRepr, sName, negate, only, nbVert)
                else:
                    geomC.msmsCurrentDisplay[sName] = "self.displayMSMS('%s', surfName=['%s'], negate=%d, only=%d, nbVert=%d, topCommand=0)" %(lSet.full_name(), sName, negate, only, nbVert)
                if len(atomindices) == 0:
                    g.Set(visible=0, tagModified=False)
                else:
                    # get the triangles corresponding to these atoms
                    vf, vi, f = srf.getTriangles(atomindices, selnum=nbVert, keepOriginalIndices=1)
                    col = mol.geomContainer.getGeomColor(sName)
                    g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6],
                           faces=f[:,:3], materials=col, visible=1,
                           tagModified=False, inheritMaterial=False)
                
                    if g.transparent:
                        opac = mol.geomContainer.getGeomOpacity(sName)
                        g.Set( opacity=opac, redo=0, tagModified=False)

                    # update texture coordinate if needed
                    if g.texture and g.texture.enabled and g.texture.auto==0:
                        mol.geomContainer.updateTexCoords[sName](mol)

                    # highlight selection
                    #vi = self.vf.GUI.VIEWER
                    selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
                    lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                    atoms = lMolSelectedAtmsDict.get(mol, None)
                    if atoms is not None:
                        lAtomSet = mol.geomContainer.msmsAtoms[sName]
                        if len(lAtomSet) > 0:
                                lAtomSetDict = dict(zip(lAtomSet, range(len(lAtomSet))))
                                lAtomIndices = []
                                for i in range(len(atoms)):
                                    lIndex = lAtomSetDict.get(atoms[i], None)
                                    if lIndex is not None:
                                        lAtomIndices.append(lIndex)							
                                lSrfMsms = mol.geomContainer.msms[sName][0]
                                lvf, lvint, lTri = lSrfMsms.getTriangles(lAtomIndices, selnum=nbVert,
                                                                         keepOriginalIndices=1)
                                highlight = [0] * len(g.vertexSet.vertices)
                                for lThreeIndices in lTri:
                                    highlight[int(lThreeIndices[0])] = 1
                                    highlight[int(lThreeIndices[1])] = 1
                                    highlight[int(lThreeIndices[2])] = 1
                                g.Set(highlight=highlight)

        redraw = False
        if kw.has_key("redraw") : redraw=True
        if self.createEvents and len(rsetOn)+len(rsetOff):
            event = EditGeomsEvent('msms_ds',
                                   [nodes,[names, negate, only, nbVert]],
                                   setOn=rsetOn, setOff=rsetOff)
            self.vf.dispatchEvent(event)

        

    def buildFormDescr(self, formName='default'):
         if formName == 'default':
            idf = DisplayCommand.buildFormDescr(self, formName)
            surfNames = self.getSurfNames()
            idf.append({'name':'surfName',
                        'widgetType':Pmw.ScrolledListBox,
                        'tooltip':'surface to be display/undisplayed',
                        'wcfg':{'label_text':'Surface: ',
                                'labelpos':'nw',
                                'items':surfNames,
                                'listbox_selectmode':'extended',
                                'usehullsize': 1,
                                'hull_width':100,'hull_height':150,
                                'listbox_height':5,
                                },
                        'gridcfg':{'sticky': 'we'}})
            idf.append({'name':'nbVert',
                        'widgetType':Pmw.ComboBox,
                        'tooltip':'number of vertices in a triangle that \
have to belong\nto a selected atom, for that face to be shown',
                        'defaultValue':'1',
                        'wcfg':{'label_text':'nb. Vert Per face: ',
                                'labelpos':'w',
                                'scrolledlist_items': ['1', '2', '3']},
                        'gridcfg':{'sticky': 'we'}})
            
            return idf


    def getSurfNames(self):
        mols = self.vf.getSelection().top.uniq()
        surfNames = []
        for mol in mols:
            for name in mol.geomContainer.msms.keys():
                if not name in surfNames:
                    surfNames.append(name)
        return surfNames


    def guiCallback(self):
        # Update the comboBox with the name of the surfaces
        if self.cmdForms.has_key('default'):
            surfNames = self.getSurfNames()
            ebn = self.cmdForms['default'].descr.entryByName
            w = ebn['surfName']['widget']
            w.clear()
            w.setlist(surfNames)
            
        val = DisplayCommand.getFormValues(self)
        if val:
            val['nbVert'] = int(val['nbVert'][0])
            apply( self.doitWrapper, (self.vf.getSelection(),), val)


    def __call__(self, nodes, only=False, negate=False, surfName='all',
                 nbVert=1, **kw):
        """None <--- displayMSMS(nodes, only=False, negate=False, name='all', **kw)\n
        \nRequired Arguments:\n
        nodes  --- TreeNodeSet holding the current selection\n
        \nOptional Arguments:\n
        only   --- Boolean flag when set to True only the current selection will be displayed (default=False)\n
        negate --- Boolean flag when set to True undisplay the current selection (default=False)\n
        surfName   --- name of the selection, default = 'all'\n
        nbVert --- Nb of vertices per triangle needed to select a triangle\n
        """
        if not kw.has_key('redraw'): kw['redraw'] = 1
        kw['only'] = only
        kw['negate'] = negate
        kw['nbVert'] = nbVert
        kw['redraw'] = 1
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        if surfName is None: kw['surfName'] = 'all'
        else:
            kw['surfName'] = surfName
        apply( self.doitWrapper, (nodes,), kw )

DisplayMSMSGUI = CommandGUI()
DisplayMSMSGUI.addMenuCommand('menuRoot', 'Display', 'Molecular Surface')



from types import StringType

class UndisplayMSMS(DisplayCommand):
    """The undisplayMSMS command allows the user to undisplay displayedMSMS\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : UndisplayMSMS\n
    Command name : undisplayMSMS\n
    \nRequired Arguments:\n
    nodes  --- TreeNodeSet holding the current selection\n.
    """
    
    def onAddCmdToViewer(self):
        #if not self.vf.hasGui: return 
        if not self.vf.commands.has_key('displayMSMS'):
            self.vf.loadCommand('msmsCommands', ['displayMSMS'], 'Pmv',
                                topCommand=0)

    def __call__(self, nodes, **kw):
        """None <- undisplayMSMS(nodes, **kw)\n
           nodes ---TreeNodeSet holding the current selection
                   (mv.getSelection())"""
        kw['negate']= 1
        kw['redraw']=1
        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        apply(self.vf.displayMSMS, (nodes,),kw)



class ComputeMSMSApprox(ComputeMSMS):
    """Computes an approximative molecular surface for a selected set of atoms by molecule.\n 
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : ComputeMSMSApprox\n
    Command name : computeMSMSApprox\n
    \nDescription:\n
    This approximation is done by replacing each residue by a sphere. The center of the sphere is geometric center of the atoms in the  residue. The radius is set to include all atoms.\n
    \nSynopsis:\n
    None<---mv.computeMSMSapprox(nodes,surfName='MSMSMOL',pRadius=1.5,density=1.0,nbSphPerRes=1, perMol=True, display=1)\n
    \nRequired Arguments :\n
        nodes --- current selection\n
    \nOptional Arguments:\n
    surfName --- name of the surfname which will be used as the key in
                mol.geomContainer.msms dictionary. If the surfName is
                already a key of the msms dictionary the surface is
                recreated. By default MSMS-MOL\n
    pRadius  --- probe radius (1.5)\n
    density --- triangle density to represent the surface. (1.0)\n
    perMol  --- when this flag is True a surface is computed for each molecule
                having at least one node in the current selection
                else the surface is computed for the current selection.
                (True)\n
    display --- flag when set to 1 the displayMSMS will be executed to
                display the new msms surface.\n
                
    nbSphPerRes --- number of approximating spheres per residue,default=1, possible values 1 or 2\n

    """

    def computeResidueSpheres(self, residues, nbSphPerRes=1):
        """Compute the geometric centers and the radii of the spheres that
        will cover each residue"""
        centers = [] # list of centers of approximating spheres
        radii = [] # list of radii of approximating spheres
        atoms = [] # list of representative atoms for approximating spheres

        def getSphere(atoms):
            """get the center and radius of the sphere for a set of atoms"""
            coords = atoms.coords
            g = Numeric.sum(coords)/len(atoms)
            dist = Numeric.subtract(coords, g)
            dist = Numeric.sum(dist*dist, 1)
            maxd = max(dist)
            atom = atoms[list(dist).index(maxd)]
            return atoms[0], list( g ), sqrt(maxd)+atom.radius

        def getBBatoms(residue):
            bbat = []
            scat = []
            for a in residue.atoms:
                name = a.name.split("@")[0]
                if name=='N' or name=='C' or name=='CA' or name=='O' \
                   or name=='HN' or name=='HA':
                    bbat.append(a)
                else:
                    scat.append(a)
            return AtomSet(bbat), AtomSet(scat)
        
        if nbSphPerRes==2:
            for r in residues:
                if r.type=='GLY' or r.type=='ALA' or r.type=='PRO':
                    a, c, r = getSphere(r.atoms)
                    radii.append( r )
                    centers.append( c )
                    atoms.append( a )
                else:
                    bbatoms, scatoms = getBBatoms(r)
                    if len(bbatoms):
                        a, c, r = getSphere( bbatoms )
                        radii.append( r )
                        centers.append( c )
                        atoms.append( a )

                    if len(scatoms):
                        a, c, r = getSphere( scatoms )
                        radii.append( r )
                        centers.append( c )
                        atoms.append( a )
        else:
            for r in residues:
                a, c, r = getSphere(r.atoms)
                radii.append( r )
                centers.append( c )
                atoms.append( a )
                
        return AtomSet(atoms), centers, radii


    def doit(self, nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
             perMol=True, display=True, nbSphPerRes=1):
        from mslib import MSMS

        if perMol:
            molecules = nodes.top.uniq()
            resSets = map(lambda x: x.chains.residues, molecules)
        else:
            molecules, resSets = self.vf.getNodesByMolecule(nodes, Residue)
        
        for mol, res in map(None, molecules, resSets):

            # get radii if necessary
            try:
                res.atoms.radius
            except:
                #if not hasattr(res[0].atoms[0], 'radius'): 
                mol.defaultRadii()

            # get the centers and radii used for MSMS calculation
            atm, centers, radii = self.computeResidueSpheres(res,nbSphPerRes)

            geomC = mol.geomContainer
            if surfName is None:
                surfName = 'msmsApprox%d'%geomC.nbSurf

            if surfName in geomC.atoms.keys():
                # Update the old geom and all.
                geomC.msmsAtoms[surfName] = atm
                geomC.atoms[surfName] = atm 
                g = geomC.geoms[surfName]
            else:
                # Create a new geom and all 
                geomC.msmsAtoms[surfName] = atm # all atoms used to compute
                g = IndexedPolygons(surfName, pickableVertices=1, protected=True,)
                if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                    g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
                g.userName = surfName
                geomC.addGeom(g)
                self.managedGeometries.append(g)
                geomC.geomPickToAtoms[surfName] = self.pickedVerticesToAtoms
                geomC.geomPickToBonds[surfName] = None
                #g.Set(frontPolyMode='fill', redo=0)
                geomC.atomPropToVertices[surfName] = self.atomPropToVertices

            # Create the key for this msms for each a.colors dictionary.
            for a in mol.allAtoms:
                a.colors[surfName] = (1.,1.,1.)
                a.opacities[surfName] = 1.0

            i=0  # atom indices are 1-based
            indName = '__surfIndex%d__'%geomC.nbSurf
            for a in atm.data:
                a.__dict__[indName] = i
                i = i + 1

            # build an MSMS object and compute the surface
            srf = MSMS( coords=centers, radii=radii )
            srf.compute( probe_radius=pRadius, density=density )

            # save a pointer to the MSMS object
            mol.geomContainer.msms[surfName] = ( srf, geomC.nbSurf )
            geomC.nbSurf = geomC.nbSurf + 1

            # get the triangles and update the geometry of the surface for
            # that molecule
            vf,vi,f = srf.getTriangles()
            g = mol.geomContainer.geoms[surfName]

	    col = geomC.getGeomColor(surfName)
            g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6], faces=f[:,:3],
                   materials=col, inheritMaterial=False, tagModified=False )
            if display:
                if not self.vf.commands.has_key('displayMSMS'):
                    self.vf.loadCommand("msmsCommands", ['displayMSMS',],
                                    topCommand=0)
                self.vf.displayMSMS(atm, surfName=[surfName,],negate=0, only=0,
                                nbVert=1, topCommand=0)


    def __call__(self, nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
                 nbSphPerRes=1, perMol=True, display=True, **kw):
        """None<---mv.computeMSMSapprox(nodes,surfName='MSMSMOL',pRadius=1.5,density=1.0,nbSphPerRes=1, perMol=True, display=1)\n
           \nRequired Arguments:\n 
           nodes    ---  current selection\n
           \nOptional arguments:\n
           surfName --- name of the surfname which will be used as the key in mol.geomContainer.msms dictionary. If the surfName is already a key of the msms dictionary the surface is recomputed. (default MSMS-MOL)\n
           pRadius  --- probe radius (1.5)\n
           density  --- triangle density to represent the surface. (1.0)\n
           nbSphPerRes --- number of approximating spheres per residue,default=1, possible values 1 or 2\n
           perMol   --- when this flag is True a surface is computed for each molecule having at least one node in the current selection else the surface is computed for the current selection.(True)\n
           display  --- flag when set to 1 the displayMSMS will be executed with the surfName else not.\n
"""
        if not kw.has_key('redraw'): kw['redraw'] = 1
        kw['pRadius'] = pRadius
        kw['density'] = density
        kw['surfName'] = surfName
        kw['nbSphPerRes'] = nbSphPerRes
        kw['perMol'] = perMol
        kw['display'] = display
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.vf.expandNodes(nodes)
        apply( self.doitWrapper, (nodes,), kw)


    def guiCallback(self):
        val = self.showForm()
        if not val: return
        if type(val['surfName']) is types.TupleType:
            val['surfName'] = val['surfName'][0]
        val['redraw'] = 1
        apply( self.doitWrapper, (self.vf.getSelection(),), val)

ComputeMSMSApproxGUI = CommandGUI()
ComputeMSMSApproxGUI.addMenuCommand('menuRoot', 'Compute', 'Molecular Surface Approx',
                                    cascadeName='Molecular Surface')


 
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet
from opengltk.OpenGL import GL
import numpy.oldnumeric as Numeric

class MsmsNPR(MVCommand):
    """This command sets colors of MSMS surface to make it look NPR\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : MsmsNPR\n
    Command name : msmsNPR\n
    \nSynopsis:\n
    None <- msmsNPR(nodes)
    \nRequired Arguments :\n
    nodes --- current selection\n
    """


    def checkDependencies(self, vf):
        import mslib


    def setColors(self, mol):
	if not hasattr(mol.geomContainer, 'msms'): #surface not computed
	    return
        g = mol.geomContainer
        geom = g.geoms['msms']
	vf, vi, fa = g.msms.getTriangles()
        # FIXME won't work with instance matrices
        mat = geom.GetMatrix()[ :3, :3 ]
        nt = Numeric.dot( vf[:, 3:6], Numeric.transpose(mat) )
        norm = Numeric.sqrt( Numeric.add.reduce(nt*nt, 1))
        ci = nt[ : , 2] / norm
        from DejaVu import colorTool
        cmap = Numeric.ones( (255,4), 'f' )
        self.width=60
        self.vf.GUI.VIEWER.cameras[0].Set(color=(1.,1.,1.), tagModified=False)
        for i in range(self.width):
            v = i/self.width
            cmap[127-i] = (v,v,v,1.)
            cmap[127+i] = (v,v,v,1.)
        outlineCol = colorTool.Map(ci, cmap)
        origCol = geom.materials[1028].prop[0]
        if len(origCol)==1:
            origCol = Numeric.array( [list(origCol)]*len(outlineCol) )
        #geom.materials[1028].prop[4] = Numeric.array([128.])
        col = Numeric.array(outlineCol*origCol)
        #geom.materials[1028].prop[3] = col
        geom.materials[1028].prop[0] = col
##          geom.Set(materials = col)
##          from opengltk.OpenGL import GL
##          geom.frontPolyMode = GL.GL_FILL
        geom.normals = None
        geom.RedoDisplayList()


    def doit(self, nodes):
        from mslib import MSMS
        if not nodes: return 
        molecules = nodes.top.uniq()
        for mol in molecules:
	    self.setColors(mol)

    def __call__(self, nodes, **kw):
         """None <--- msmsNPR(nodes, **kw)\n
            \nRequired Arguments :\n
            nodes: TreeNodeSet holding the current selection\n"""
         if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
         kw['redraw']=True
         apply( self.doitWrapper, (nodes,), kw )

    def guiCallback(self):
        self.doitWrapper(self.vf.getSelection(), redraw=True)

msmsNPRGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                   'menuButtonName':'Compute',
                   'menuEntryLabel':'NPR MSMS For Selection'}

MsmsNPRGUI = CommandGUI()
MsmsNPRGUI.addMenuCommand('menuRoot', 'Compute', 'NPR MSMS For Selection',
                          cascadeName = 'Molecular Surface')



class IdentifyBuriedVertices(MVCommand):
    """This command enables finding out and tagging the vertices of a Solvent excluded surface that are buried by a set of atoms.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   :IdentifyBuriedVertices\n
    Command name :identifyBuriedVertices\n
    \nDescription:\n
    After running this command the vertices that are buried are tagged in
    the MSMS data structure with the buried flag (which is return by the
    ses.getTriangles() method. Each vertex of the triangulated ses also
    has a member called sesArea and sasArea that hold the surface area
    corresponding to each vertex of the triagulation.\n
    \nSynopsis:\n
    areas <- identifyBuriedVertices(surfaceName, surfaceMol, nodes)\n
    \nRequired Arguments:\n
      surfaceName ---  name of an MSMS surface computed using MSMS\n
      surfaceMol --- molecule for which the surface 'surfaceName' has been computed\n
      nodes --- string or objects that expand into a set of atoms\n
      """
    
    def checkDependencies(self, vf):
        """make sure the mslib package is available"""
        import mslib


    def doit(self, surfaceName, surfaceMol, nodes):
        """
        \nsurfaceName---name of an MSMS surface computed using MSMS
        \nsurfaceMol---molecule for which the surface 'surfaceName' has been
        computed
        \nnodes---string or objects that expand into a set of atoms which may bury
        parts of the MSMS surface

        \nReturn---a dictionary with 2 keys: 'ses' and 'sas'. The values are
        either lists of buried surface areas for all components considered.
        """
        
        # get the molecule surfaceMol
        surfaceMol = self.vf.expandNodes(surfaceMol)
        assert len(surfaceMol)==1

        surfaceMol = surfaceMol[0]
        assert isinstance(surfaceMol, Molecule)
        
        # get the msms surface object
        geomC = surfaceMol.geomContainer
        srf = geomC.msms[surfaceName][0]
            
        # get the atoms that might bury parts on that surface
        nodes = self.vf.expandNodes(nodes)
        nodes = nodes.findType( Atom )

        # make sure they all have radii
        try:
            rad = nodes.radius
        except AttributeError:
            molecules = nodes.top.uniq()
            for mol in molecules:
                mol.defaultRadii()
            rad = nodes.radius

        # identify buried vertices in all components
        srf.buriedVertices( nodes.coords, rad )

        # compute buried surface areas for all components and assign values
        # to triangulation vertices
        areas = srf.buriedSurfaceArea()
        return areas
        

    def selectMolecule_cb(self, event=None):
        
        moleculeName = self.ifd.entryByName['Molecule List']['widget'].get()[0]
        mol = self.vf.expandNodes(moleculeName)[0]
        geomC = mol.geomContainer
        w = self.ifd.entryByName['Surface List']['widget']
        w.clear()
        for n in geomC.msms.keys():
            w.insert('end', n, None)


    def OK_cb(self, event=None):
        """call back for OK button"""
        self.ifd.form.OK_cb(event)

    def buildFormDescr(self, formName):
        if formName == 'buriedSurf':
            ifd = self.ifd = InputFormDescr(title='Compute Buried surface')
            entries = map(lambda x: (x, None), self.vf.Mols.name)
        
            ifd.append({'name': 'Molecule List',
                        'widgetType':ListChooser,
                        'wcfg':{ 'title':'Choose a molecule (double click)',
                                 'entries': entries,
                                 'lbwcfg':{'exportselection':0,
                                           'width':25,'height':10},
                                 'command':self.selectMolecule_cb,
                                 'commandEvent':"<Double-Button-1>"
                                 },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
                        })
            
            ifd.append({'name': 'Surface List',
                        'widgetType':ListChooser,
                        'wcfg':{
                'title':'Choose a surface',
                'entries': [],
                'lbwcfg':{'exportselection':0,'width':25,'height':10},
                'command': self.OK_cb,
                'commandEvent':"<Double-Button-1>"
                },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W, 'row':0,
                                   'column':1}
                        })
            return ifd

    def guiCallback(self, event=None):

        nodes = self.vf.getSelection()
        if len(nodes)==0:
            self.warningMsg('You should first select the atoms that will bury parts of a surface')
            return
        
        val = self.showForm('buriedSurf')
        if len(val):
            molName = val['Molecule List']
            surfName = val['Surface List']
            if len(molName) and len(surfName):
                area = self.doitWrapper(surfName[0], molName[0], nodes)
                self.vf.message(str(area))
        

    def __call__(self, surfaceName, surfaceMol, nodes, **kw):
        """areas <- identifyBuriedVertices(surfaceName, surfaceMol, nodes,
                                           **kw)\n
        Compute the area of the SES and SAS surface buried by a set of atoms\n
        \nArguments:\n
        surfaceName--- name of an MSMS surface computed using MSMS\n
        surfaceMol--- molecule for which the surface 'surfaceName' has been computed\n 
        nodes--- string or objects that expand into a set of atoms\n
        Return---a dictionary with 2 keys: 'ses' and 'sas'. The values are either
        lists of buried surface areas for all components considered.\n
        """
        return apply( self.doitWrapper, (surfaceName, surfaceMol, nodes), kw )


identifyBuriedVerticesGuiDescr = {'widgetType':'Menu',
                                  'menuBarName':'menuRoot',
                                  'menuButtonName':'Compute',
                                  'menuEntryLabel':'Compute Buried Surface'}

IdentifyBuriedVerticesGUI = CommandGUI()
IdentifyBuriedVerticesGUI.addMenuCommand('menuRoot', 'Compute',
                                         'Compute Buried Surface',
                                         cascadeName='Molecular Surface')


class DisplayBuriedTriangles(DisplayCommand):
    """This Command display/Undisplay buried SES as computed with BuriedSurface command.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : DisplayBuriedTriangles\n
    Command name : displayBuriedTriangles\n    
    \nSynopsis :\n
    None <--- displayBuriedTriangles(nodes, surfaceName, negate=0)\n
    \nRequired Arguments:\n
    nodes --- set of nodes for which the buried vertices of the surface 'surfaceName' are to be 
    displayed. (string, TreeNode or TreeNodeSet)\n
    surfaceName --- name of an MSMS surface computed using msms. (string)\n
    \nOptional Arguments:\n
    cut---specifies how many vertices has to be buried (or not) for a triangle to be displayed.(1, 2 or 3)\n
    negate---specifies whether we want to display buried or exposed triangles\n
    """
    
    def __init__(self, func=None):
        
        DisplayCommand.__init__(self, func)
        self.flag = self.flag ^ self.objArgOnly

    def checkDependencies(self, vf):
        """make sure the mslib package is available"""
        import mslib
        

    def setupUndoBefore(self, nodes, surfaceName,  cut=1, negate=False, only=False, redraw=1):
        # The undo of this display command depends on which displayMSMS cmd
        # was used previously and results in displaying what faces were displayed previously
        nodes = self.vf.expandNodes(nodes)
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        for mol, atoms in map(None, molecules, atomSets):
            geomC = mol.geomContainer
            surfNames = geomC.msms.keys()
            if surfaceName == 'all':
                names = surfNames
            elif not type(surfaceName) in [types.ListType, types.TupleType]:
                if not surfaceName in surfNames:
                    continue
                else:
                    names = [surfaceName,]
            else:
                names = []
                #only get the surfaces which are in geomC.msms.keys()
                for n in surfaceName:
                    if n in surfNames:
                        names.append(n)
                #names = surfaceName
            for n in names: 
                # undo depends on whether current msms geometry resulted from
                # displayMSMS OR from displayBuriedTriangles
                # for each molecule, this is tracked in dictionary stored as
                # molecule.geomContainer.msmsCurrentDisplay[surfaceName]
                lastCmd = geomC.msmsCurrentDisplay.get(n, "")
                if lastCmd=="" or lastCmd.find('displayMSMS')>-1:
                    #the geometry resulted from displayMSMS 
                    ats = geomC.atoms[n]
                    old_nodes_name = self.vf.undo.saveUndoArg(ats)
                    undoCmd = "self.displayMSMS(%s, surfName=['%s'], negate=%d, only=%d, nbVert=%d, topCommand=0)" %(old_nodes_name, n, negate, only, cut)
                    self.vf.undo.addEntry((undoCmd), (self.name))
                else:
                    #the geometry resulted from displayBuriedTriangles 
                    #get a handle to the IndexedPolygon geometry
                    g = geomC.geoms[n]
                    #save the current verts
                    old_vertices_name = self.vf.undo.saveUndoArg(Numeric.array(g.getVertices()))
                    #save the current faces
                    old_faces_name = self.vf.undo.saveUndoArg(Numeric.array(g.getFaces()))
                    #save the current vnormals
                    old_vnormals_name = self.vf.undo.saveUndoArg(Numeric.array(g.getVNormals()))
                    #save the current front_colors
                    front_colors = g.materials[GL.GL_FRONT].getState()
                    old_front_name = self.vf.undo.saveUndoArg(front_colors)
                    #save the current back_colors
                    back_colors = g.materials[GL.GL_BACK].getState()
                    old_back_name = self.vf.undo.saveUndoArg(back_colors)
                    undoCmd = "from opengltk.OpenGL import GL;g = self.expandNodes('%s')[0].geomContainer.geoms['%s'];g.Set(vertices=%s, faces=%s, vnormals=%s);apply(g.materials[GL.GL_FRONT].Set, (), %s);apply(g.materials[GL.GL_BACK].Set, (), %s)" %(mol.name, n, old_vertices_name, old_faces_name, old_vnormals_name, old_front_name, old_back_name)
                    #undoCmd = "self.expandNodes('%s')[0].geomContainer.geoms['%s'].Set(vertices=%s, faces=%s, vnormals=%s)" %(mol.name, n, old_vertices_name, old_faces_name, old_vnormals_name)
                    geomC.msmsCurrentDisplay[n] = undoCmd
                    self.vf.undo.addEntry((undoCmd), (self.name))



    def doit(self, nodes, surfaceName, cut=1, negate=False, only=False, **kw):
        """
        nodes--- nodes for which the buried surface is to be displayed.
        surfaceName--- name of an MSMS surface computed using MSMS.
        cut-- triangles with this number of buried vertices will be displayed
        """

        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        for mol, atoms in map(None, molecules, atomSets):
            geomC = mol.geomContainer
            surfNames = geomC.msms.keys()
            if not type(surfaceName) in [types.ListType, types.TupleType]:
                if not surfaceName in surfNames:
                    continue
                    #return
                else:
                    names = [surfaceName,]
            else:
                names = surfaceName
            
            for sName in names:
                # Make sure that the surface exists for this molecule.
                if not sName in surfNames: continue
                # first get the atoms for this molecule in set of atoms used
                # for that surface
                allAtms = geomC.msmsAtoms[sName]
                atm = allAtms.inter(atoms)

                # get the set of atoms with surface displayed
                set = geomC.atoms[sName]

                ##if negate, remove current atms from displayed set
                if negate: set = set - atm

                #if only, replace displayed set with current atms 
                else:
                    if only: set = atm
                    else: set = atm.union(set)

                geomC.atoms[sName] = set
                surfNum = geomC.msms[surfaceName][1]
                indName = '__surfIndex%d__'%surfNum
                atomindices = []
                #for a in atoms:
                for a in set:
                    atomindices.append(getattr(a, indName))

                # get the msms surface object for that molecule
                srf = geomC.msms[sName][0]
                g = geomC.geoms[sName]
                from opengltk.OpenGL import GL
                g.Set(culling=GL.GL_NONE)
                if len(atomindices) == 0:
                    g.Set(visible=0, tagModified=False)
                else:
                    # get the triangles corresponding to these atoms
                    vf, vi, f = srf.getBuriedSurfaceTriangles(atomindices, selnum=cut, negate=negate)
                    col = mol.geomContainer.getGeomColor(sName)
                    g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6],
                           faces=f[:,:3], materials=col, visible=1,
                           tagModified=False, inheritMaterial=False)
                    if set.stringRepr is not None:
                        geomC.msmsCurrentDisplay[surfaceName] = "mv.displayBuriedTriangles(%s, surfaceName=['%s'], cut=%d, negate=%d, tagModified=False"%(set.stringRepr, surfaceName, cut,negate)
                    else:
                        geomC.msmsCurrentDisplay[surfaceName] = "mv.displayBuriedTriangles(%s, surfaceName=['%s'], cut=%d, negate=%d, tagModified=False"%(set.full_name(), surfaceName, cut,negate)
                    #geomC.msmsCurrentDisplay[surfaceName] = "mv.displayBuriedTriangles(surfaceName=['%s'],'%s', cut=%d, negate=%d, tagModified=False"%(surfaceName, surfaceMol.name, cut,negate)
                    if g.transparent:
                        opac = geomC.getGeomOpacity(sName)
                        g.Set( opacity=opac, redo=0, tagModified=False)

                    # update texture coordinate if needed
                    if g.texture and g.texture.enabled and g.texture.auto==0:
                        geomC.updateTexCoords[sName](mol)
                


    def selectMolecule_cb(self, event=None):
        ifd = self.cmdForms['displayBuried'].descr
        moleculeName = ifd.entryByName['Molecule List']['widget'].get()[0]
        mol = self.vf.expandNodes(moleculeName)[0]
        geomC = mol.geomContainer
        w = ifd.entryByName['Surface List']['widget']
        w.clear()
        for n in geomC.msms.keys():
            w.insert('end', n, None)


    def OK_cb(self, event=None):
        """call back for OK button"""
        ifd = self.cmdForms['displayBuried'].descr
        ifd.form.OK_cb(event)

    def buildFormDescr(self, formName):
        if formName == 'displayBuried':
            ifd = InputFormDescr(title='Select Buried surface')
            entries = map(lambda x: (x, None), self.vf.Mols.name)
            ifd.append({'name': 'Molecule List',
                        'widgetType':ListChooser,
                        'wcfg':{ 'title':'Choose a molecule (double click)',
                                 'entries': entries,
                                 'lbwcfg':{'exportselection':0,
                                           'width':25,'height':10},
                                 'command':self.selectMolecule_cb,
                                 'commandEvent':"<Double-Button-1>"
                                 },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
                        })

            ifd.append({'name': 'Surface List',
                        'widgetType':ListChooser,
                        'wcfg':{'title':'Choose a surface',
                            'entries': [],
                            'lbwcfg':{'exportselection':0,'width':25,'height':10},
                            'command': self.OK_cb,
                            'commandEvent':"<Double-Button-1>"
                            },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W, 'row':0,
                                   'column':1}
                        })

            ifd.append( {'name': 'cut',
                         'widgetType':ExtendedSliderWidget,
                         'wcfg':{'label': 'Nb. vertices/triangles',
                                 'minval':1,'maxval':3,'incr':1,'init':3,
                                 'sliderType':'int',
                                 'labelsCursorFormat':'%1d',
                                 },
                         'gridcfg':{'sticky':'we', 'row':1, 'column':0},
                         })

            ifd.append({'name':'negate',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text':'display exposed surface',
                            'variable':Tkinter.IntVar()},
                    'gridcfg':{'sticky':'w', 'row':1, 'column':1}})

            ifd.append({'name':'only',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text':'display only for these atoms',
                            'variable':Tkinter.IntVar()},
                    'gridcfg':{'sticky':'w', 'row':-1, 'column':2}})
            return ifd


    def guiCallback(self, event=None):
        #chooser =  self.cmdForms['displayBuried'].descr.entryByName['Molecule List']['widget']
        #if self.vf.Mols.name != map(lambda x: x[0], widget.entries)
        nodes = self.vf.getSelection()
        val = self.showForm('displayBuried', force=1)

        if len(val):
            molName = val['Molecule List']
            surfName = val['Surface List']
            if len(molName) and len(surfName):
                self.doitWrapper(nodes, surfName[0],
                                 #FIXME this should be an int
                                 int(val['cut']),
                                 val['negate'], val['only'], redraw=1)

        
    def __call__(self, nodes, surfaceName, cut=1, negate=False, only=False, **kw):
        """None <- displayBuriedTriangles(nodes, surfaceName, negate=0, only=False, redraw=0)\n
        \nRequired Arguments:\n
         nodes--- nodes for which the buried surface is to be displayed.
         surfaceName-- name of an MSMS surface computed using msms.(string)\n
         \nOptional Arguments:\n
         cut--- specifies how many vertices has to be buried (or not) for a triangle to be displayed.(1, 2 or 3)\n
         negate-- specifies whether we want to display buried or exposed triangles\n
         only-- specifies whether we want to display only triangles for these nodes\n"""
        
        if not kw.has_key('negate'): kw['negate'] = negate
        if not kw.has_key('only'): kw['only'] = only
        if not kw.has_key('cut'): kw['cut'] = cut
        if not kw.has_key('redraw'): kw['redraw'] = 1
        return apply( self.doitWrapper, (nodes, surfaceName), kw )


displayBuriedTrianglesGuiDescr = {'widgetType':'Menu',
                                  'menuBarName':'menuRoot',
                                  'menuButtonName':'Display',
                                  'menuEntryLabel':'Buried Surface'}

DisplayBuriedTrianglesGUI = CommandGUI()
DisplayBuriedTrianglesGUI.addMenuCommand('menuRoot', 'Display', 'Buried Surface')



class DisplayIntermolecularBuriedTriangles(DisplayCommand):
    """This Command display/Undisplay buried SES between two molecules.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : DisplayIntermolecularBuriedTriangles\n
    Command name : displayIntermolecularBuriedTriangles\n    
    \nSynopsis :\n
    None <--- displayIntermolecularBuriedTriangles(nodes1, surfaceName1,nodes2, surfaceName2, negate=0)\n
    \nRequired Arguments:\n
    nodes1 --- first set of nodes for which the buried vertices of the surface 'surfaceName1' are to be 
    displayed. (string, TreeNode or TreeNodeSet)\n
    surfaceName1 --- name of an MSMS surface computed using msms. (string)\n
    nodes2 --- first set of nodes for which the buried vertices of the surface 'surfaceName2' are to be 
    displayed. (string, TreeNode or TreeNodeSet)\n
    surfaceName2 --- name of an MSMS surface computed using msms. (string)\n
    \nOptional Arguments:\n
    cut---specifies how many vertices has to be buried (or not) for a triangle to be displayed.(1, 2 or 3)\n
    negate---specifies whether we want to display buried or exposed triangles\n
    """
    
    def __init__(self, func=None):
        
        DisplayCommand.__init__(self, func)
        self.flag = self.flag ^ self.objArgOnly

    def checkDependencies(self, vf):
        """make sure the mslib package is available"""
        import mslib
        

    def setupUndoBefore(self, nodes1, surfaceName1,nodes2, surfaceName2,  cut, negate, only, **kw):
        # The undo of this display command depends on which displayMSMS cmd
        # was used previously and results in displaying what faces were displayed previously
        undoCmd = "from opengltk.OpenGL import GL;"
        for nodes, surfaceName in [(nodes1, surfaceName1), (nodes2, surfaceName2)]:
            nodes = self.vf.expandNodes(nodes)
            molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
            for mol, atoms in map(None, molecules, atomSets):
                geomC = mol.geomContainer
                surfNames = geomC.msms.keys()
                if len(surfNames)==0:
                    surfNames = [surfaceName,]

                if surfaceName == 'all':
                    names = surfNames
                elif not type(surfaceName) in [types.ListType, types.TupleType]:
                    if not surfaceName in surfNames:
                        continue
                    else:
                        names = [surfaceName,]
                else:
                    names = []
                    #only get the surfaces which are in geomC.msms.keys()
                    for n in surfaceName:
                        if n in surfNames:
                            names.append(n)
                    #names = surfaceName
                for n in names: 
                    # undo depends on whether current msms geometry resulted from
                    # displayMSMS OR from displayBuriedTriangles
                    # for each molecule, this is tracked in dictionary stored as
                    # molecule.geomContainer.msmsCurrentDisplay[surfaceName]
                    if not hasattr(geomC, 'msmsCurrentDisplay'):
                        lastCmd == ""
                    else:
                        lastCmd = geomC.msmsCurrentDisplay.get(n, "")
                    if lastCmd=="" or lastCmd.find('displayMSMS')==-1:
                        #the geometry resulted from displayMSMS 
                        if n in geomC.atoms.keys():
                            ats = geomC.atoms[n]
                        else:
                            ats = atoms
                        old_nodes_name = self.vf.undo.saveUndoArg(ats)
                        undoCmd += "self.displayMSMS(%s, surfName=['%s'], negate=%d, only=%d, nbVert=%d, topCommand=0);" %(old_nodes_name, n, negate, only, cut)
                        #self.vf.undo.addEntry((undoCmd), (self.name))
                    else:
                        #the geometry resulted from displayBuriedTriangles 
                        #get a handle to the IndexedPolygon geometry
                        g = geomC.geoms[n]
                        #save the current verts
                        old_vertices_name = self.vf.undo.saveUndoArg(Numeric.array(g.getVertices()))
                        #save the current faces
                        old_faces_name = self.vf.undo.saveUndoArg(Numeric.array(g.getFaces()))
                        #save the current vnormals
                        old_vnormals_name = self.vf.undo.saveUndoArg(Numeric.array(g.getVNormals()))
                        #save the current front_colors
                        front_colors = g.materials[GL.GL_FRONT].getState()
                        old_front_name = self.vf.undo.saveUndoArg(front_colors)
                        #save the current back_colors
                        back_colors = g.materials[GL.GL_BACK].getState()
                        old_back_name = self.vf.undo.saveUndoArg(back_colors)
                        undoCmd += "g = self.expandNodes('%s')[0].geomContainer.geoms['%s'];g.Set(vertices=%s, faces=%s, vnormals=%s);apply(g.materials[GL.GL_FRONT].Set, (), %s);apply(g.materials[GL.GL_BACK].Set, (), %s);" %(mol.name, n, old_vertices_name, old_faces_name, old_vnormals_name, old_front_name, old_back_name)
                        #undoCmd = "self.expandNodes('%s')[0].geomContainer.geoms['%s'].Set(vertices=%s, faces=%s, vnormals=%s)" %(mol.name, n, old_vertices_name, old_faces_name, old_vnormals_name)
                        geomC.msmsCurrentDisplay[n] = undoCmd
                        #self.vf.undo.addEntry((undoCmd), (self.name))
        if self.vf.hasGui:
            undoCmd = undoCmd + "self.GUI.VIEWER.Redraw()"
        self.vf.undo.addEntry((undoCmd), (self.name))



    def doit(self, nodes1, surfaceName1, nodes2, surfaceName2, cut=1, negate=False, only=False):
        """
        nodes1--- nodes for which the buried surface is to be displayed.
        surfaceName1--- name of an MSMS surface computed using MSMS.
        nodes2--- nodes for which the buried surface is to be displayed.
        surfaceName2--- name of an MSMS surface computed using MSMS.
        cut-- triangles with this number of buried vertices will be displayed
        """
        for nodes, surfaceName in [(nodes1, surfaceName1), (nodes2, surfaceName2)]:
            molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
            for mol, atoms in map(None, molecules, atomSets):
                geomC = mol.geomContainer
                #print "doit: processing ", mol.name
                surfNames = geomC.msms.keys()
                if nodes==nodes1:
                    others = nodes2
                else:
                    others = nodes1
                if len(surfNames)==0:
                    self.vf.computeMSMS(mol.name, surfaceName, topCommand=0)
                    surfNames = [surfaceName,]
                if not type(surfaceName) in [types.ListType, types.TupleType]:
                    if not surfaceName in surfNames:
                        continue
                        #return
                    else:
                        names = [surfaceName,]
                else:
                    names = surfaceName
                
                for sName in names:
                    # Check whether this surface exists for this molecule.
                    if not sName in surfNames: continue
                    self.vf.identifyBuriedVertices(sName, mol.name, others, topCommand=0)
                    self.vf.assignBuriedAreas(sName, mol.name, topCommand=0)
                    self.vf.displayBuriedTriangles(mol.name, sName, cut=cut, negate=negate, topCommand=0)

                


    def selectFirstMolecule_cb(self, event=None):
        ifd = self.cmdForms['displayBuried'].descr
        moleculeName1 = ifd.entryByName['First Molecule List']['widget'].get()[0]
        mol = self.vf.expandNodes(moleculeName1)[0]
        geomC = mol.geomContainer
        w = ifd.entryByName['First Surface List']['widget']
        w.clear()
        for n in geomC.msms.keys():
            w.insert('end', n, None)


    def selectSecondMolecule_cb(self, event=None):
        ifd = self.cmdForms['displayBuried'].descr
        moleculeName2 = ifd.entryByName['Second Molecule List']['widget'].get()[0]
        mol = self.vf.expandNodes(moleculeName2)[0]
        geomC = mol.geomContainer
        w = ifd.entryByName['Second Surface List']['widget']
        w.clear()
        for n in geomC.msms.keys():
            w.insert('end', n, None)


    def OK_cb(self, event=None):
        """call back for OK button"""
        print "in OK_cb"
        #ifd = self.cmdForms['displayBuried'].descr
        #ifd.form.OK_cb(event)


    def guiCallback(self, event=None):
        cutVar = Tkinter.StringVar()
        cutVar.set("number of buried vertices for display cutoff")
        cutDict = [ {'name':'cutLab',
                          'widgetType': Tkinter.Label,
                          'textvariable':cutVar,
                           'wcfg':{'font':(ensureFontCase('helvetica'),9,) }},
                        {'name':'cut',
                        'widgetType':Pmw.RadioSelect,
                        'tooltip':
                       """triangles with this number of 'buried' vertices will be displayed""",
                        'listtext':['1','2', '3'],
                        'defaultValue':'1',
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton'}}]

        vals = AugmentedMoleculeChooser(self.vf, mode='extended', title='Choose two molecules\nfor intermolecular buried surface', extra=['cut'], extraDict=cutDict, selectTitle= 'select two molecules').go()
        if not len(vals):
            return "ERROR"
        mols = vals[0]
        cut = vals[1]
        assert len(mols)>1
        mols, cut = AugmentedMoleculeChooser(self.vf, mode='extended', title='Choose two molecules\nfor intermolecular buried surface', extra=['cut'], extraDict=cutDict, selectTitle= 'select two molecules').go()
        cut = int(cut)
        assert cut in [1,2,3]
        firstMol = mols[0]
        gc = firstMol.geomContainer
        if len(gc.msms)==0:
            surfName1 = firstMol.name + "MSMS"
            self.vf.computeMSMS(firstMol, surfName=surfName1)
        elif len(gc.msms)>1:
            formName = firstMol.name + "SurfaceList"
            formTitle = "Choose " + firstMol.name + " msms surface"
            ifd = self.ifd = InputFormDescr(title=formTitle)
            entries = map(lambda x: (x, None), gc.msms.keys())
            ifd.append({'name': 'First Surface List',
                        'widgetType':ListChooser,
                        'wcfg':{ 'title':'Choose first msms surface (double click)',
                                 'entries': entries,
                                 'lbwcfg':{'exportselection':0,
                                           'width':25,'height':10},
                                 'command':self.OK_cb,
                                 'commandEvent':"<Double-Button-1>"
                                 },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
                        })
            val = self.vf.getUserInput(ifd)
            #val = self.showForm(formName, force=1)
            surfName1 = val['First Surface List']
        else:
            surfName1 = gc.msms.keys()[0]
        secondMol = mols[1]
        gc2 = secondMol.geomContainer
        if len(gc2.msms)==0:
            surfName2 = secondMol.name + "MSMS"
            self.vf.computeMSMS(secondMol, surfName=surfName2)
        elif len(gc2.msms)>1:
            formName = secondMol.name + "SurfaceList"
            formTitle = "Choose " + secondMol.name + " msms surface"
            ifd = self.ifd = InputFormDescr(title=formTitle)
            entries = map(lambda x: (x, None), gc2.msms.keys())
            ifd.append({'name': 'Second Surface List',
                        'widgetType':ListChooser,
                        'wcfg':{ 'title':'Choose second msms surface (double click)',
                                 'entries': entries,
                                 'lbwcfg':{'exportselection':0,
                                           'width':25,'height':10},
                                 'command':self.OK_cb,
                                 'commandEvent':"<Double-Button-1>"
                                 },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
                        })
            val = self.vf.getUserInput(ifd)
            surfName2 = val['Second Surface List']
        else:
            surfName2 = gc2.msms.keys()[0]
            
        if firstMol and surfName1 and secondMol and surfName2:
                self.doitWrapper(firstMol, surfName1, 
                                 secondMol, surfName2,
                                 cut=cut, negate=0, only=0, redraw=1)

        

    def __call__(self, nodes1, surfaceName1, nodes2, surfaceName2, cut=1, negate=False, only=False, **kw):
        """None <- displayIntermolecularBuriedTriangles(nodes1, surfaceName1, nodes2, surfaceName2, negate=0, only=False, **kw)\n
        nodes1--- nodes for which the buried surface is to be displayed.
        surfaceName1--- name of an MSMS surface computed using MSMS.
        nodes2--- nodes for which the buried surface is to be displayed.
        surfaceName2--- name of an MSMS surface computed using MSMS.
        cut-- triangles with this number of buried vertices will be displayed
        negate-- specifies whether we want to display buried or exposed triangles\n
        only-- specifies whether we want to display only triangles for these nodes\n

        """
        
        if not kw.has_key('negate'): kw['negate'] = negate
        if not kw.has_key('only'): kw['only'] = only
        if not kw.has_key('cut'): kw['cut'] = cut
        if not kw.has_key('redraw'): kw['redraw'] = 1
        if not kw.has_key('setupUndo'): kw['setupUndo'] = 1
        return apply( self.doitWrapper, (nodes1, surfaceName1, nodes2, surfaceName2), kw )


displayBuriedIntermolecularTrianglesGuiDescr = {'widgetType':'Menu',
                                  'menuBarName':'menuRoot',
                                  'menuButtonName':'Display',
                                  'menuEntryLabel':'Buried Surface'}

DisplayIntermolecularBuriedTrianglesGUI = CommandGUI()
DisplayIntermolecularBuriedTrianglesGUI.addMenuCommand('menuRoot', 'Display', 'Buried Intermolecular Surface')



class AssignBuriedAreas(MVCommand):
    """Command to sum the areas of the buried vertices for each atom.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : AssignBuriedAreas\n
    Command name : assignBuriedAreas\n
    \nDescription:\n
    This command assumes that a command to find buried vertices has been run
previousely\n
    \nSynopsis :\n
    None <- assignBuriedAreas(surfaceName, surfaceMol)\n
    \nRequired Arguments:\n
    surfaceName---name of an MSMS surface computed using msms. (string)\n
    surfaceMol---molecule for which the surface 'surfaceName' has been computed. (string, TreeNode or TreeNodeSet)\n
    \nOptional Arguments:\n
     attributes---buriedSES and buriedSAS.\n
"""

    def checkDependencies(self, vf):
        """make sure the mslib package is available"""
        import mslib


    def doit(self, surfaceName, surfaceMol):
        """\nsurfaceName---name of an MSMS surface computed using MSMS
        \nsurfaceMol: molecule for which the surface 'surfaceName' has been computed
        \nReturn: None
        \nafter the command is executed each atom and residue has a 2 attributes:
        buriedSES and buriedSAS.\n"""
        
        # get the molecule surfaceMol
        surfaceMol = self.vf.expandNodes(surfaceMol)
        assert len(surfaceMol)==1

        surfaceMol = surfaceMol[0]
        assert isinstance(surfaceMol, Molecule)
        
        # get the msms surface object
        geomC = surfaceMol.geomContainer
        srf = geomC.msms[surfaceName][0]

        # get the geometry of that surface
        g = geomC.geoms[surfaceName]
        
        # get all the vertices, and buried faces
        vf, vi, f = srf.getBuriedSurfaceTriangles(selnum=3)

        # get all buried vertices float and int
        ind = Numeric.nonzero(vi[:,2])
        bvf = Numeric.take(vf, ind )
        bvi = Numeric.take(vi, ind)[:,1]
        
        # loop over arrays and accumulate buried area values over atoms indices
        d = {}
        for atInd, vfloat in map(None, bvi, bvf):
            ii = int(atInd)
            if not d.has_key(ii):
                d[ii] = [0.0, 0.0]
            d[ii][0] = d[ii][0] + vfloat[6]
            d[ii][1] = d[ii][1] + vfloat[7]

        # now find the corresponding atoms and create their buriedSAS
        # and buriedSES members
        atoms = geomC.msmsAtoms[surfaceName]
        for a in atoms:
            a.buriedSAS = a.buriedSES = 0.0
            
        for atInd, values in d.items():
            a = atoms[int(atInd-1)]
            a.buriedSES = values[0]
            a.buriedSAS = values[1]

        residues = atoms.parent.uniq()
        for r in residues:
            r.buriedSES = Numeric.sum( r.atoms.buriedSES )
            r.buriedSAS = Numeric.sum( r.atoms.buriedSAS )


    def selectMolecule_cb(self, event=None):
        ifd = self.cmdForms['buriedSurfaces'].descr
        moleculeName = ifd.entryByName['Molecule List']['widget'].get()[0]
        mol = self.vf.expandNodes(moleculeName)[0]
        geomC = mol.geomContainer
        w = ifd.entryByName['Surface List']['widget']
        w.clear()
        for n in geomC.msms.keys():
            w.insert('end', n, None)


    def OK_cb(self, event=None):
        """call back for OK button"""
        self.cmdForms['buriedSurfaces'].OK_cb(event)


    def buildFormDescr(self, formName):
        if formName == 'buriedSurfaces':
            ifd = InputFormDescr(title='Compute Buried surface')
            entries = map(lambda x: (x, None), self.vf.Mols.name)
        
            ifd.append({'name': 'Molecule List',
                        'widgetType':ListChooser,
                        'wcfg':{ 'title':'Choose a molecule (double click)',
                                 'entries': entries,
                                 'lbwcfg':{'exportselection':0,
                                           'width':25,'height':10},
                                 'command':self.selectMolecule_cb,
                                 'commandEvent':"<Double-Button-1>"
                                 },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W}
                        })

            ifd.append({'name': 'Surface List',
                        'widgetType':ListChooser,
                        'wcfg':{'title':'Choose a surface',
                                'entries': [],
                                'lbwcfg':{'exportselection':0,
                                          'width':25,'height':10},
                                'command': self.OK_cb,
                                'commandEvent':"<Double-Button-1>"
                                },
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W, 'row':0,
                                   'column':1}
                        })
            return ifd

            
        
    def guiCallback(self, event=None):
        val = self.showForm('buriedSurfaces', force=1)
        if len(val):
            molName = val['Molecule List']
            surfName = val['Surface List']
            if len(molName) and len(surfName):
                self.doitWrapper(surfName[0], molName[0])
                

    def __call__(self, surfaceName, surfaceMol, **kw):
        """None <- assignBuriedAreas(surfaceName, surfaceMol, **kw)       
        \nAssign buried surface areas to atoms and residues.\n
        \nArguments:\n
        surfaceName--- name of an MSMS surface computed using msms. (string)\n
        surfaceMol--- molecule for which the surface 'surfaceName' has been computed. (string, TreeNode or TreeNodeSet)\n
        After the command is executed all atoms and residues have 2 new\n
        attributes--- buriedSES and buriedSAS.\n
        """

        return apply( self.doitWrapper, (surfaceName, surfaceMol), kw )


assignBuriedSurfaceGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                               'menuButtonName':'Compute',
                               'menuCascadeName':'Molecular Surface',
                               'menuEntryLabel':'Assign Buried Surface'}

AssignBuriedAreasGUI = CommandGUI()
AssignBuriedAreasGUI.addMenuCommand('menuRoot', 'Compute', 
                                    'Assign Buried Surface',
                                    cascadeName='Molecular Surface')


from Pmv.picker import MsmsPicker

##  class msmsColorByFaceType(MVCommand):
##      """Computes a molecular surface for a selected set of atoms with each
##      molecule"""


##      def guiCallback(self):
##          print 'Pick a surface'
##          p = MsmsPicker(self.vf, numberOfObjects=1, gui=0,
##                         callbacks=[self.doit])
        
##      def doit(self, surfaces):
##          print surfaces
##          for geom in surfaces:
##              print geom
##              mol = geom.mol
##              name = geom.userName
##              mssrf = mol.geomContainer.msms[name][0]
##              msgeom = mol.geomContainer.geoms[name]
##              col = mssrf.getColorByType(0)
##              msgeom.Set( materials = col , tagModified=False)
            
##  msmsColorByFaceTypeGUI = CommandGUI()
##  msmsColorByFaceTypeGUI.addMenuCommand('menuRoot', 'Color',
##                                        'MSMS By Face Type')
class ComputeSESAndSASArea(MVCommand):
    """Compute Solvent Excluded Surface and Solvent Accessible Surface Areas\n
    Package : Pmv\n
    Module  : exposureCommands\n
    Class   : ComputeSESAndSASArea\n
    Command name : computeSESAndSASArea\n
    \nSynopsis :\n
    None--->mv.computeSESAndSASArea(mol)\n    
    \nDescription:\n
    Computes Solvent Excluded Surface and Solvent Accessible Surface Areas. Stores numeric values per Atom,
    Residue, Chain, and Molecule in ses_area and sas_area attributes.
    """
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('computeMSMS'):
            self.vf.loadCommand('msmsCommands', ['ComputeMSMS',], topCommand=0)

    def guiCallback(self, event=None):
        mol = MoleculeChooser(self.vf).go(modal=0, blocking=1)
        if not mol: return
        self.doitWrapper(mol)
        dialog = Pmw.TextDialog(self.vf.GUI.ROOT, title='SES and SAS Areas', 
                                text_height=5, text_width=50, defaultbutton=0)
        txt = "Computed SES and SAS Areas for "+mol.name
        txt += "\n\nSolvent Excluded Surface Area: "+str(mol.ses_area)
        txt += "\nSolvent Accessible Surface Area: "+str(mol.sas_area)
        dialog.insert('end', txt)
        dialog.activate()
        
    def doit(self, mol):
        allrads = mol.defaultRadii()
        allChains = mol.chains
        allResidues = mol.chains.residues
        allAtoms = mol.allAtoms
        import mslib
        # compute the surface
        srf = mslib.MSMS(coords=allAtoms.coords, radii = allrads)
        srf.compute()
        srf.compute_ses_area()        
        # get surface areas per atom
        ses_areas = []
        sas_areas = []
        for i in xrange(srf.nbat):
            atm = srf.get_atm(i)
            ses_areas.append(atm.get_ses_area(0))
            sas_areas.append(atm.get_sas_area(0))
        # get surface areas to each atom
        allAtoms.ses_area = ses_areas
        allAtoms.sas_area = sas_areas
        # sum up ses areas over resdiues
        for r in allResidues:
            r.ses_area = numpy.sum(r.atoms.ses_area)        
            r.sas_area = numpy.sum(r.atoms.sas_area)

        mol.ses_area = 0
        mol.sas_area = 0            
        for chain in allChains:
            chain.ses_area = 0
            chain.sas_area = 0
            for residue in chain.residues:
                chain.ses_area += numpy.sum(residue.ses_area)
                chain.sas_area += numpy.sum(residue.sas_area)
            mol.ses_area += chain.ses_area 
            mol.sas_area += chain.sas_area 
            
    def __call__(self, molecule, **kw):
        """None <- computeSESAndSASArea(molecule, **kw)
    Computes Solvent Excluded Surface and Solvent Accessible Surface Areas. Stores numeric values per Atom,
    Residue, Chain, and Molecule in ses_area and sas_area attributes.               
        """
        nodes=self.vf.expandNodes(molecule)
        return apply( self.doitWrapper, (nodes), kw )
          
ComputeSESAndSASAreaGUI = CommandGUI()
ComputeSESAndSASAreaGUI.addMenuCommand('menuRoot', 'Compute', 'Solvent Excluded & Accessible Areas',
                                       cascadeName='Molecular Surface', separatorAbove=1)

commandList = [
    {'name':'readMSMS','cmd':ReadMSMS(), 'gui':ReadMSMSGUI},
    {'name':'computeMSMS','cmd':ComputeMSMS(), 'gui':ComputeMSMSGUI},
    {'name':'displayMSMS','cmd':DisplayMSMS(), 'gui':DisplayMSMSGUI},
    {'name':'undisplayMSMS','cmd':UndisplayMSMS(), 'gui':None},
    {'name':'saveMSMS','cmd':SaveMSMS(), 'gui':SaveMSMSGUI},
    {'name':'computeMSMSApprox','cmd':ComputeMSMSApprox(),
     'gui':ComputeMSMSApproxGUI},
##     {'name':'msmsNPR','cmd':MsmsNPR(), 'gui':MsmsNPRGUI},
##      {'name':'msmsColorByFaceType','cmd':msmsColorByFaceType(), 'gui':msmsColorByFaceTypeGUI},
    {'name':'identifyBuriedVertices','cmd':IdentifyBuriedVertices(),
     'gui':IdentifyBuriedVerticesGUI},
    {'name':'displayBuriedTriangles','cmd':DisplayBuriedTriangles(),
     'gui':DisplayBuriedTrianglesGUI},
    {'name':'displayIntermolecularBuriedTriangles',
     'cmd':DisplayIntermolecularBuriedTriangles(),
     'gui':DisplayIntermolecularBuriedTrianglesGUI},
    {'name':'assignBuriedAreas','cmd':AssignBuriedAreas(),
     'gui':AssignBuriedAreasGUI},
     {'name':'computeSESAndSASArea','cmd':ComputeSESAndSASArea(), 'gui':ComputeSESAndSASAreaGUI}
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
