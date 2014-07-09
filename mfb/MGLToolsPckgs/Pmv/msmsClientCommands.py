#$Header: /opt/cvs/python/packages/share1.5/Pmv/msmsClientCommands.py,v 1.3 2009/11/03 17:42:20 annao Exp $
#
#$Id: msmsClientCommands.py,v 1.3 2009/11/03 17:42:20 annao Exp $
#
# Authors: M. Sanner and S. Dallakyan

import socket
import subprocess
import numpy
import struct
from mglutil.util.packageFilePath import getBinary, which
import types, os
import Tkinter, Pmw
from math import sqrt

import numpy.oldnumeric as Numeric
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom, AtomSet
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
import Pmv

try:
    msmsBinary = getBinary('msms','binaries')
except:
    msmsBinary = None

if not msmsBinary: #msms not found in binaries
    msmsBinary = which('msms')

if not msmsBinary:
    print "Could not find msms binaries. Please set the path to msms executable in ",__file__

class MSMSClient:    
    def __init__(self, coords=None, radii=None, **kw):
        
        self.coords = coords
        self.radii = radii        
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 2000
        #find a free port
        result = soc.connect_ex(('', port))
        while not result:
            port += 1
            result = soc.connect_ex(('', port))
            soc.close()
        self.port = port
        proc = subprocess.Popen([msmsBinary, "-socketPort", str(port)], stdout=subprocess.PIPE)
        if proc.returncode:
            result = None
            while not result:
                port += 1
                result = soc.connect_ex(('', port))
                soc.close()
            self.port = port
            proc = subprocess.Popen([msmsBinary, "-socketPort", str(port)], stdout=subprocess.PIPE)
        #print "msms server started on port "+str(port)
        self.proc = proc
     
    def compute(self, probe_radius, density, **kw):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print  probe_radius, density, kw
        connected = False
        for i in range(1000):#this is done to make sure msms is ready to accept a client.     
            try:
                soc.connect(('', self.port))
                connected = True
                #print "msms client connected on port "+str(self.port)
                break;
            except Exception, inst:
                pass
                #print inst
        print connected
        if not connected: 
            raise RuntimeError("Unable to connect to msms on port "+str(self.port))
        soc.settimeout(None) 
        lenCoord = len(self.coords)
        soc.send(struct.pack('ffiii', probe_radius, density, 0, 1, lenCoord))

        for i in range(lenCoord):
            x, y, z = self.coords[i]
            soc.send( struct.pack('ffffi', x, y, z, self.radii[i], 1))  
        msg = ''
        while 1:
            d = soc.recv(1)
            if d[0]=='\n':
                break
            msg += d
        print msg
        # e.g. "tahiti: MSMS SERVICE started on tahiti"
        cmd = ''
        while 1:
            d = soc.recv(1)
            if d and d[0]=='\n':
                break
            cmd += d        
        #cmd can be one of the following strings
        # MSMS END this tring should be received after the calculation ocmpleted
        #          successfuly and the data was sent back
        # MSMS RS  This string indicates that next the reduced surface will be sent
        # MSMS RCF This string indicates that nexttbhe triangulated surface will be sent
        print cmd        
        isize = struct.calcsize('i')
        fsize = struct.calcsize('f')
        
        d = soc.recv(isize)
        nbf = struct.unpack('i', d)[0]
        
        d = soc.recv(isize)
        nbv = struct.unpack('i', d)[0]
        
        soc.setblocking(1) # to avoid recv to return with partial data
        

        # get the faces
        d = soc.recv(nbf*5*isize)
        while len(d) != nbf*5*isize:
            d += soc.recv(nbf*5*isize-len(d))
            
        faces = struct.unpack('%di'%(nbf*5), d)
        faces = numpy.array(faces)
        faces.shape = (-1,5)
        
        # get the vertices
        d = soc.recv(nbv*6*fsize)
        while len(d) != nbv*6*isize:
            d += soc.recv(nbv*6*isize-len(d))
        vn = struct.unpack('%df'%(6*nbv), d)
        vf = numpy.array(vn)
        vf.shape = (-1,6)
        
        d = soc.recv(nbv*isize)
        indices = struct.unpack('%di'%nbv, d)     
        #self.vf = vf
        self.faces = faces
        self.indices = indices
        self.vfloat =  numpy.zeros((len(self.indices), 6), dtype=numpy.float)
        self.vint =  numpy.zeros((len(self.indices), 3), dtype=numpy.int)

        for index, atomIndex in enumerate(self.indices):
            self.vfloat[index] = [vf[index][3], vf[index][4], vf[index][5],
                                  vf[index][0], vf[index][1], vf[index][2]]
            self.vint[index] = [0, self.indices[index], 0]

        if hasattr(self.proc, 'terminate'): #New in Python 2.6.
            self.proc.terminate()
            
    def getTriangles(self, atomindices, **kw):
        firstTime = True
        indices = range(len(self.faces))
        faces = self.faces.copy()
        for index, item in enumerate(self.indices):
            if item in atomindices: continue
            #else
            for i, face in enumerate(faces[indices]):
                if (face[0] == index) or (face[1] == index) or (face[2] == index):
                    if i in indices:
                        indices.remove(i)    
        return self.vfloat, self.vint, faces.take(indices, axis=0)



class ComputeMSMS(MVCommand, MVAtomICOM):
    """The computeMSMS command will compute a triangulated solvent excluded surface for the current selection.\n
    Package : Pmv\n
    Module  : msmsCommands\n
    Class   : ComputeMSMS\n
    Command name : computeMSMS\n
    \nSynopsis :\n
    None <--- mv.computeMSMS(nodes, surfName=None, pRadius=1.5,
                           density=1.0, perMol=True,
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

    def checkDependencies(self, vf=None):
        import mslib


    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('assignAtomsRadii'):
            self.vf.loadCommand('editCommands', ['assignAtomsRadii',],
                                topCommand=0)

    def onAddObjectToViewer(self, obj):
        """
        """
        if not self.vf.hasGui: return
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
                 density=3.0, perMol=True, display=True, hdset='None',
                 hdensity=6.0, **kw):
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
    display  --- flag when set to 1 the displayMSMS will be executed with
                 the surfName else not.\n
    hdset    --- Atom set (or name) for which high density triangualtion will
                 be generated
    hdensity --- vertex density for high density
"""
        nodes=self.vf.expandNodes(nodes)
        kw['surfName'] = surfName
        kw['pRadius'] = pRadius
        kw['density'] = density
        kw['perMol'] = perMol
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
        if type(val['surfName']) is types.TupleType:
            surfName = val['surfName'][0]
        else:
            surfName = val['surfName']


        del val['surfName']
        
        apply(self.doitWrapper, (self.vf.getSelection(), surfName), val)


    def doit(self, nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
             perMol=True, display=True, hdset=None, hdensity=6.0):
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
        display  --- flag when set to True the displayMSMS will be executed with
                    the surfName else not.\n
        hdset    --- Atom set for which high density triangualtion 
                     will be generated
        hdensity --- vertex density for high density
        """
        from Pmv.msmsClientCommands import MSMSClient as MSMS
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
            atmSets = map(lambda x: x.allAtoms, molecules)
        else:
            molecules, atmSets = self.vf.getNodesByMolecule(nodes, Atom)

        for mol, atms in map(None, molecules, atmSets):
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
                if self.cmdForms.has_key('default'):
                    self.updateForm(surfName)

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


    def buildFormDescr(self, formName='default'):
        if formName == 'default':
            idf = InputFormDescr(title ="MSMS Parameters Panel:")
            mols = self.vf.getSelection().top.uniq()
            sNames = []
            for mol in mols:
                sNames += mol.geomContainer.msms.keys()

            defaultValues = self.getLastUsedValues()

            if not sNames:
                sNames = ['MSMS-MOL']
                idf.append({'widgetType':Pmw.ComboBox,
                            'name':'surfName',
                            'required':1,
                            'tooltip': "Please type-in a new name or chose \
one from the list below\n '_' are not accepted.",
                            'wcfg':{'labelpos':'nw',
                                    'label_text':'Surface Name: ',
                                    'entryfield_validate':self.entryValidate,
                                    'entryfield_value':'MSMS-MOL',
                                    'scrolledlist_items':[],
                                    },
                            'gridcfg':{'sticky':'we'}})
            else:
                idf.append({'widgetType':Pmw.ComboBox,
                            'name':'surfName',
                            'required':1,
                            'tooltip': "Please type-in a new name or chose \
one from the list below\n '_' are not accepted.",
                            'defaultValue': defaultValues['surfName'],
                            'wcfg':{'labelpos':'nw',
                                    'label_text':'Surface Name: ',
                                    'entryfield_validate':self.entryValidate,
                                    'scrolledlist_items':sNames,
                                },
                        'gridcfg':{'sticky':'we'}})
            
            names = ['None']+self.vf.sets.keys()
            names.sort()
#            idf.append({'widgetType':Pmw.ComboBox,
#                        'name':'hdset',
#                        'required':0,
#                        'tooltip': """Choose a set defining the part of the surface
#that should be triangualte at high density""",
#                        'defaultValue': str(defaultValues['hdset']),
#                        'wcfg':{'labelpos':'nw',
#                                'label_text':'High density surface set: ',
#                                'scrolledlist_items':names,
#                                },
#                        'gridcfg':{'sticky':'we'}})
#            idf.append({'name':'perMol',
#                        'tooltip':"""When checked surfaces will be computed using all atoms (seelcted or not) of
#each molecule.  If unchecked, the unselected atoms are ignored during the
#calculation.""",
#                        'widgetType':Tkinter.Checkbutton,
#                        'defaultValue': defaultValues['perMol'],
#                        'wcfg':{'text':'Per Molecule',
#                                'variable':Tkinter.IntVar(),
#                                'command':self.perMol_cb},
#                        'gridcfg':{'sticky':'we'}
#                        })
#            
#            idf.append({'name':'saveSel',
#                        'widgetType':Tkinter.Button,
#                        'tooltip':"""This button allows the user to save the current selection as a set.
#The name of the msms surface will be used as the name of the set""",
#                        'wcfg':{'text':'Save Current Selection As Set',
#                                'state':'disabled',
#                                'command':self.saveSel_cb},
#                        'gridcfg':{'sticky':'we'}})
            
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
                         'labCfg':{'text':'Probe Radius'},
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

#            idf.append({'name':'hdensity',
#                    'widgetType':ThumbWheel,
#                    'tooltip':"""Vertex density use for triangulating the high density part of the surface.
#Right click on the widget to type a value manually""",
#
#                    'gridcfg':{'sticky':'we'},
#                    'wcfg':{'oneTurn':2, 
#                        'type':'float',
#                        'value': defaultValues['hdensity'],
#                        'increment':0.1,
#                        'precision':1,
#                        'continuous':False,
#                        'wheelPad':2,'width':145,'height':18,
#                         'labCfg':{'text':'High Density '},
#                        }
#                    })


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
        cbb = ebn['surfName']['widget']
        typein = cbb.get()
        sel = cbb.getcurselection()
        if typein in sel: return
        sNames = []
        mols = self.vf.getSelection().top.uniq()
        for mol in mols:
            sNames += mol.geomContainer.msms.keys()
        if not typein in sNames:
            return 
        else:
            cbb.setlist(sNames)
            cbb.selectitem(typein)

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
ComputeMSMSGUI.addMenuCommand('menuRoot', 'Compute','Molecular Surface using MSMS Binaries',
                                 cascadeName='Molecular Surface')


commandList = [
    {'name':'computeMSMSBin','cmd':ComputeMSMS(), 'gui':ComputeMSMSGUI},
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

        
