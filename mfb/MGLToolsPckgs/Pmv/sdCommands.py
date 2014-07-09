## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: July 2002 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
# revision: Guillaume Vareille
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/sdCommands.py,v 1.80 2009/09/09 18:09:53 sanner Exp $
#
# $Id: sdCommands.py,v 1.80 2009/09/09 18:09:53 sanner Exp $
#

import Pmv 
import Pmw
import Tkinter
import numpy.oldnumeric as Numeric ; N = Numeric
import string
import types
import os
import tkMessageBox
from DejaVu.IndexedPolygons import IndexedPolygons
from Pmv.displayCommands import DisplayCommand
from Pmv.mvCommand import MVCommand
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, CallBackFunction
from ViewerFramework.VFCommand import Command, ICOM, CommandGUI
from ViewerFramework.VF import ViewerFramework
from MolKit.molecule import Atom,AtomSet
from MolKit.protein import Residue
from opengltk.OpenGL import GL
from Pmv.colorCommands import ColorCommand
from DejaVu.colorMap import ColorMap
from DejaVu.ColormapGui import ColorMapGUI
from DejaVu.colorTool import RGBRamp
from DejaVu.Texture import Texture
from Pmv.guiTools import MoleculeChooser,CenterChooser
from Pmv.selectionCommands import MVSelectFromStringCommand
from mglutil.math import transformation,rotax,rmsd ; Transform = transformation.Transformation
from bhtree import bhtreelib
from mglutil.bhtfunctions import findNearestAtoms
from DejaVu.Geom import Geom
    
class MolIndexedPolygons(IndexedPolygons):

    """
    Package : Pmv
    Module  : sdCommands
    Class   : MolIndexedPolygons
    Command : None
    
    Description:
    The MolIndexedPolygons is a class derived from IndexedPolygons. It
    has an additional method, getTriangles, which is used to assign
    atoms to geometry vertices and vice versa when an externally
    generated geometry is assigned to a molecule. Assignment to a
    molecule occurs with the ReadMolIndexedPolygons command
    
    Keywords: geometry, harmony, surfdock
    """
    
    def __init__(self, name = None, check=1, redo=1, **kw):

        apply(IndexedPolygons.__init__, (self, name, check), kw)
        #atomIndices has for each atomIndex a list of vertexIndices:
        #the vertices for which this atom is the closest
        self.atomIndices = {}
        #vertexIndices has a value for each vertex which corresponds to
        #the __surfIndex__ value for the closest atom
        self.vertexIndices = {}

        
    def getTriangles(self, atomindices):
        """This emulates the MSMS getTriangles method.
        Needed for assigning vertices to atoms
        """
        # get the list of vertex indices which are associated with the
        # atom indices passed in
        vindexList = []
        for a in atomindices:
            vindexList.extend(self.atomIndices[a])
        vfloat = []
        vint = []
        tri = []
        for key in self.properties.keys():
            self.displayprops[key]= []
        #flag all vertices as _not_ in the list to be returned
        displayFlags = -1*Numeric.ones(len(self.vertexIndices))
        for x in range(len(vindexList)):
            vindex = vindexList[x]
            #get hold of the propereties for the displayed vertices and
            #stick in the vertice.properties index for coloring purposes
            for key in self.properties.keys():
                value = self.properties[key][vindex]
                self.displayprops[key].append(value)
            # flag the vertices being included as being returned
            # displayFlag gives its new position in the list
            # which can be used to update the triangles (below)
            displayFlags[vindex]=x
            # vfloat = (x,y,z,nx,ny,nz,sesA=0.0,sasA=0.0)
            thisfloat = []
            thisfloat.extend(self.vertices[vindex].tolist())
            thisfloat.extend(self.vnormals[vindex].tolist())
            thisfloat.extend([0.0,0.0])
            vfloat.append(thisfloat)
            # vint = (type=-1, closestAtomIndex, buried=0)
            thisint = [-1]
            thisint.append(self.vertexIndices[vindex])
            thisint.append(0)
            vint.append(thisint)
            #tri = triangles data (i,j,k,type=1,SESF_num=0)
        for face in self.triangles:
            #replace the vertex number with its position in the new list
            tri0 = displayFlags[face[0]]
            tri1 = displayFlags[face[1]]
            tri2 = displayFlags[face[2]]
            # if they are all being used, we need a triangle
            if tri0 != -1 and tri1 != -1 and tri2 != -1:
                thistri = [tri0,tri1,tri2]
                thistri.extend([1,0])
                tri.append(thistri)
        return N.array(vfloat,'f'),N.array(vint,'i'),N.array(tri,'i')                     


class ReadMolIndexedPolygons(MVCommand):
    """
    Package : Pmv
    Module  : sdCommands
    Class   : ReadMolIndexedPolygons
    Command : readMolIndexedPolygons
    
    Description:
    Class to read two files (defining vertices and faces) to generate
    a MolIndexedPolygons instance and assign it to a molecule. Polygon
    vertices are assigned to atoms in the molecule and vice versa. The
    first six columns of the vertices file contain vertex coordinates
    and surface normals. The remaining columns contain surface
    properties.
    
    Synopsis:
      None <- ReadMolIndexedPolygons(molName, vertfile, trifile, propertyList=[], name=None, **kw)
      molName        : name of the molecule to which the polygon belongs
      vertfile       : name of the file containing list of vertices and surface properties
      trifile        : file containing faces (i.e. vertex connectivity)
      atom_index     : file containing correspondence between surface points and atoms
                       (in the format output using cluster -d -a)
                       If absent, the correspondences will be calculated
      propertyList   : list of names to give the surface properties (columns 7+ of the vertex file)
      name           : name to give the geometry. Defaults to the vertex file name.
      
    Keywords: geometry, harmony
    """

    
    def __init__(self):
        MVCommand.__init__(self)


    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert a picked vertex into an atom"""
        
        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet


        surfName = geom.userName
        geomC = geom.mol.geomContainer
        surfNum = geomC.molindexedpolygons[surfName][1]
        
        
        #FIXME: bulding atomindices is done in DisplayMSMS
        #should re-use it
        mol = geom.mol
        atomindices = []
        al = mol.geomContainer.atoms[surfName]
        
        for a in al:
            atomindices.append(a.__surfIndex__)

        surf = geomC.molindexedpolygons[surfName][0]
        vf, vi, f = surf.getTriangles(atomindices)

        l = []
        allAt = mol.allAtoms
        for i in vertInd:
            l.append(allAt[vi[i][1]-1])
        return AtomSet( l )


    def pickedVerticesToBonds(self, geom, parts, vertex):
        return None


    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        """Function called to map atomic properties to the vertices of the
        geometry"""
        if len(atoms)==0: return None

        geomC = geom.mol.geomContainer
        surfName = geom.userName
        surf = geomC.molindexedpolygons[surfName][0]
        surfNum = geomC.molindexedpolygons[surfName][1]

        prop = []
        if propIndex is not None:
            for a in geom.mol.allAtoms:
                d = getattr(a, propName)
                prop.append( d[propIndex] )
        else:
            for a in geom.mol.allAtoms:
                prop.append( getattr(a, propName) )

        # find indices of atoms with surface displayed
        atomindices = []
        for a in atoms.data:
            atomindices.append(a.__surfIndex__)
        
        # get the indices of closest atoms
        vf, vi, f = surf.getTriangles(atomindices)

        # get lookup col using closest atom indicies
        mappedprop = Numeric.take(prop, vi[:, 1]-1).astype('f')

        return mappedprop


    def onAddObjectToViewer(self, obj):
        """
        Adds the Molindexedpolygons geometry to represent the molindexedpolygons surface
        of a molecule
        """
        #if not self.vf.hasGui: return
        geomC = obj.geomContainer
        geomC.nbMolindexedpolygons = 0
        geomC.molindexedpolygons = {}


    def doit(self, molName, vertfile, trifile, atom_index=None, propertyList=[], name=None, display=1):

        print "molName",molName
        print "vertfile",vertfile
        print "trifile",trifile
        print "atom_index",atom_index
        print "propertyList",propertyList
        print "name",name
        # first try to read the files:
        try:
            infile = open(vertfile,'r')
            vertdata = infile.readlines()
            infile.close()
        except:
            msg = "File '%s' does not exist" % vertfile
            self.vf.warningMsg(msg)
            return None
        if trifile:
            try:
                infile = open(trifile,'r')
                tridata = infile.readlines()
                infile.close()
            except:
                msg = "File '%s' does not exist" % trifile
                self.vf.warningMsg(msg)
                return None
        else:
            # try to find the appropriate triangulation file
            # can be
            # icosohedral ( subdivision level is (nvertices-2)/10. )
            # dual icosohedral ( subdivision level is (nvertices/20.) )
            # octahedral (nfaces = 4*subdivisionlevel*8) # not done
            # cubic # not done
            # tetrahedral # not done
            pname = os.path.split(vertfile)[0]
            datapath = Pmv.__path__[0]+'/data'
            nvertices= len(vertdata)
            if (nvertices-2)/10. == (nvertices-2)/10: # dual icosohedral?
                level = (nvertices-2)/10
                trifiles = (os.path.join(datapath,'ico.%d.tri' % level),
                            os.path.join(pname,'ico.%d.tri' % level))
                #print "Tesselation is simple icosohedral at %d subdivision level" % level
            elif nvertices/20. == nvertices/20: # icosohedral?
                level = (nvertices)/20
                trifiles = (os.path.join(datapath,'%d.poly.tri' % level),
                            os.path.join(pname,'%d.poly.tri' % level))
                #print "Tesselation is dual icosohedral at %d subdivision level" % level
            else: #undetermined
                msg = "Cannot establish subdivision level. Check %s" % vertfile
                self.vf.warningMsg(msg)
                return None
            #now try to read the trifile
            tridata=[]
            for trifile in trifiles:
                try:
                    infile = open(trifile)
                    tridata = infile.readlines()
                    infile.close()
                    #print "#2: Read tesselation from",trifile
                    break
                except:
                    continue
            if not tridata:
                msg = "Files %s and %s cannot be found" % trifiles
                self.vf.warningMsg(msg)
                return

        #then expand the molName to nodes
        mol = self.vf.expandNodes(molName)[0]
        atm = mol.allAtoms
        geomC = mol.geomContainer
        if name is None:
            name = string.replace(molName,'_','')
            name = "%ssurf%d" % (name,geomC.nbMolindexedpolygons)

        # get all the atoms for the molecule
        if name in geomC.atoms.keys():
            #update the old geometry
            geomC.molindexedpolygons[name]=atm
            geomC.atoms[name]=atm
            g = geomC.geoms[name]
        else:
            #create a new geometry
            g = MolIndexedPolygons(name,pickableVertices=1)#, protected=True)
            g.userName = name
            if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False)
            geomC.addGeom(g)
            self.managedGeometries.append(g)
            geomC.molindexedpolygons[name]=atm
            geomC.atoms[name]=atm
            geomC.geomPickToAtoms[name] = self.pickedVerticesToAtoms
            geomC.geomPickToBonds[name] = None
            geomC.VIEWER.AddObject( g, parent = geomC.masterGeom, redo=0)
            g.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
            geomC.atomPropToVertices[name] = self.atomPropToVertices

        # Create the key for this dockdata for each a.colors dictionary.
        for a in mol.allAtoms:
            a.colors[name] = (1.,1.,1.)
            a.opacities[name] = 1.0
        
        i = 1
        if not hasattr(atm[0], '__surfIndex__'):
            #only need to set up the __surfIndex__ once
            for a in atm.data:
                a.__surfIndex__ = i
                i=i+1
                
        # construct the surface and its properties from the data
        vertices = []
        vnormals = []
        triangles = []
        vertexNumber = 0
        g.properties = properties = {}
        g.displayprops = displayprops = {}
        #print propertyList
        for property in propertyList:
            properties[property]=[]
            displayprops[property]=[]
        for line in vertdata:
            numbers = string.split(line)
            vertices.append(([float(numbers[0]),
                              float(numbers[1]),
                              float(numbers[2])]))
            vnormals.append(([float(numbers[3]),
                              float(numbers[4]),
                              float(numbers[5])]))
            props = map(lambda x: float(x), numbers[6:])
            if len(propertyList):
                for x in range(len(propertyList)):
                    properties[propertyList[x]].append(props[x])
        g.vertices = Numeric.array(vertices,'f')
        # translate and scale the unit sphere representation of the output from tmap
        if vertfile.split(".")[-1] in ["exp","exp2"]:
            ats = mol.allAtoms
            cg = Numeric.average(mol.allAtoms.coords)
            rg = map(lambda x: (x-cg)*(x-cg), mol.allAtoms.coords)
            rg = Numeric.average(rg)
            rg = Numeric.sum(Numeric.average(rg))
            rg = Numeric.sqrt(rg)
            g.vertices = map(lambda x: x*rg + cg, g.vertices)
        g.vnormals = Numeric.array(vnormals,'f')
        for line in tridata:
            numbers = string.split(line)
            triangles.append([int(numbers[0])-1,
                              int(numbers[1])-1,
                              int(numbers[2])-1])
        g.triangles = triangles = Numeric.array(triangles,'i')

        # If the atomIndices file is _not_ given (or not found) get the atomIndices and vertexIndices from bhtree
        # g.vertexIndices:keys = vertexnumbers, vals = corresponding atom numbers (0-based )
        # g.atomIndices:  keys = atom numbers: vals - list of vertexNumbers (1-based)
        if atom_index:
            try:
                infile= open(atom_index)
                atom_index = infile.readlines()
                infile.close()
            except:
                atom_index = None
        if atom_index:
            g.vertexIndices = {}
            g.atomIndices = {}
            for a in range(1,len(mol.allAtoms)+1):
                g.atomIndices[a]=[]
            for rec in atom_index:
                fields = rec.split()
                a = int(fields[3])
                v = int(fields[4])-1
                g.vertexIndices[v]=a
                g.atomIndices[a].append(v)
        else:
            g.vertexIndices,g.atomIndices = findNearestAtoms(mol,vertices)
        
        #create the surface and put it in the geomContainer
        # save a pointer to the dockdata object
        mol.geomContainer.molindexedpolygons[name] = (g, geomC.nbMolindexedpolygons)
        geomC.nbMolindexedpolygons = geomC.nbMolindexedpolygons+1

        if len(vertices):
	    # print 'setting vertices:', vertices
            g.Set( vertices=vertices[:], vnormals=vnormals[:], faces=triangles[:],
                   visible=1 )
	    #print 'after setting vertices:', g.vertexSet.vertices.array

        if display:
            self.vf.displaySurface(mol, name=name, topCommand=0, setupUndo=1)


    def guiCallback(self):
        """ Doesn't handle property lists yet. These have to be done on the
        command line
        """
        # get the molecule for which this is being read
        mol = MoleculeChooser(self.vf).go()
        if not mol:
            return None
        molName = mol.name

        # get the vertex file
        fileTypes = [("vertex files","*vert*"),]
        fileBrowserTitle = "Read Vertex File"
        vertfile = self.vf.askFileOpen(types=fileTypes,
                                       title=fileBrowserTitle)
        if not vertfile:
            return
        #get the triangle file
        fileTypes = [("triangle files","*tri*"),]
        fileBrowserTitle = "Read Triangle File"
        trifile = self.vf.askFileOpen(types=fileTypes,
                                      title=fileBrowserTitle)
        if not trifile:
            return
        
        self.doitWrapper(molName,vertfile,trifile)
        

    def __call__(self, molName, vertfile, trifile, atom_file=None, propertyList=[], name=None, **kw):
        """None <- readMolIndexedPolygons(nodes, vertfile, trifile, atom_file, propertyList, name,**kw)
           nodes   : TreeNodeSet holding a molecule
           vertfile: vertices and normals
           trifile : one-based triangulation file
           atom_file: (optional) output of cluster assigning atoms to vertices
           propertyList: list of names of surface properties in the vertfile
           """
        if not kw.has_key('redraw'): kw['redraw'] = 1
        apply( self.doitWrapper, (molName, vertfile, trifile,
                                  atom_file, propertyList, name), kw)


class ColorMolIndexedPolygons(ColorCommand):
    """
    Package : Pmv
    Module  : sdCommands
    Class   : ColorMolIndexedPolygons
    Command : colorMolIndexedPolygons
    
    Description:
    The ColorMolIndexedPolygons class provides a mechanism for coloring
    a MolIndexedPolygons instance according to its surface properties
    (i.e. the properties listed in the vertex file used to generate
    the MolIndexedPolygons). This command only colors a surface
    according to _surface_ properties. To color according to
    properties of the molecule to which the MolIndexedPolygons belongs
    (such as atom type, chain ID etc.), use the general color commands.
    
    Synopsis:
      None <- colorMolIndexedPolygin(nodes, geomsToColor,property,colorMap=None,**kw):
      nodes       : any set of MolKit nodes describing molecular components
      geomsToColor: list of MolIndexedPolygons instances to color
      property    : surface property by which to color
      colorMap    : colorMap which will translate the property values into colors
                    (default is the rgb256 colorMap)
    
    Keywords: color, surfdock, harmony
    """

    def onAddCmdToViewer(self):
       if 'rgb256' not in self.vf.colorMaps.keys():
           ramp = RGBRamp(256)
           cmap = ColorMapGUI(name='rgb256', ramp=ramp, allowRename=False, modifyMinMax=True)
           self.vf.addColorMap(cmap)
           

    def getPropsGUI(self, nodes, geomsToColor, showUndisplay = 0):
        propsAvailable = []
        molInSel = nodes.top.uniq()
        for mol in molInSel:
            geomC = mol.geomContainer
            if hasattr(geomC,'molindexedpolygons'):
                for geom in geomsToColor:
                    if geom in geomC.geoms.keys():
                        for key in geomC.geoms[geom].properties.keys():
                            if key not in propsAvailable:
                                propsAvailable.append(key)
        idf = self.idf = InputFormDescr(title = self.name)
        idf.append({'widgetType':Pmw.RadioSelect,
                    'name':'Property',
                    'listtext':propsAvailable,
                    'defaultValue':propsAvailable[0],
                    'wcfg':{'labelpos':'n',
                            'label_text':'Select the property to color by:',
                            'orient':'vertical',
                            'buttontype':'radiobutton'},
                    'gridcfg':{'sticky':'we','columnspan':2}})

        val = self.vf.getUserInput (self.idf)
        if val:
            return val['Property']
        else:
            return None

    def getAvailableGeoms(self, nodes, showUndisplay = 0):
        """Method to build a dictionary containing all the molindexedpolygons
        geometries available in the scene."""

        if not nodes:
            return
        molInSel = nodes.top.uniq()
        geomsAvailable = []
        for mol in molInSel:
            geomC = mol.geomContainer
            childGeomsName = self.getChildrenGeomsName(mol)
            # We only put the one we are ineterested in in the list
            # of geomsAvailable 
            for geomName in geomC.molindexedpolygons.keys():
                if geomName in ['master','selectionSpheres']:
                    continue
                if geomC.atoms.has_key(geomName):
                    if geomName in childGeomsName:
                        continue
                    if showUndisplay == 0 and  \
                       geomC.atoms[geomName]==[]:
                        continue
                    if not geomName in geomsAvailable:
                        geomsAvailable.append(geomName)
                else:
                    if not geomC.geoms[geomName].children:
                        continue
                    else:
                        empty = filter(lambda x, geomC=geomC:
                                       geomC.atoms.has_key(x.name) and \
                                       geomC.atoms[x.name]==[],
                                       geomC.geoms[geomName].children)
                        if len(empty)==len(geomC.geoms[geomName].children)\
                           and showUndisplay == 0:
                            continue
                        if not geomName in geomsAvailable:
                            geomsAvailable.append(geomName)
        return geomsAvailable
        

    def doit(self,nodes,geomsToColor,property,colorMap=None,**kw):
        if 'rgb256' not in self.vf.colorMaps.keys():
            self.vf.colorMaps['rgb256'] = ColorMapGUI('rgb256', RGBRamp(256), 
                                     allowRename=False, modifyMinMax=True)
        if colorMap is None:
            if not hasattr(self,'colorMap'):
                self.colorMap = self.vf.colorMaps['rgb256']
        else:
            self.colorMap = colorMap
        if hasattr(self.colorMap,'gui') and (self.colorMap.gui is not None):
            self.colorMapGUI = self.colorMap.gui
        else:
            self.colorMapGUI = ColorMapGUI(allowRename=False, modifyMinMax=True)
            self.colorMap.gui = self.colorMapGUI
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)  
        geometries={}
        for mol, atm in map(None, molecules, atomSets):
            geomC = mol.geomContainer
            fmax = -9999.0
            fmin = 9999.0
            for g in geomC.geoms.values():
                if g.name not in geomsToColor or not hasattr(g,'properties'):
                    continue
                if property in g.properties.keys():
                    geometries[g.name]=g
                    if fmax < max(g.properties[property]):
                        fmax = max(g.properties[property])
                    if fmin > min(g.properties[property]):
                        fmin = min(g.properties[property])
            self.colorMap.configure(mini=fmin,maxi=fmax,geoms=geometries)
##             if hasattr(self,'colorMapGUI'):
##                 self.colorMapGUI.update(mini=fmin,maxi=fmax)
            # now go through again, this time setting the colors
            for g in geometries.values():
                prop = Numeric.array(g.displayprops[property]).astype('f')
                #get rid of any other coloring
                colors = self.colorMap.Map(prop)
                colors = N.array(colors).astype('f')
                g.Set(materials=colors,inheritMaterial=0)
##                  if min(prop)<0 or max(prop)>0:
##                      mini = min(prop)
##                      l = max(prop)-mini
##                      prop1 = (prop-mini) / l
##                      prop = prop1
##                  prop.shape = (-1,1)
##                  tex = Numeric.array(Numeric.array(self.colorMap.ramp)*255).astype('B')
##                  t=Texture()
##                  t.Set(enable=1, image=tex)
##                  g.Set(texture=t,textureCoords=colors)
            self.vf.GUI.VIEWER.cameras[0].update()
            self.vf.GUI.VIEWER.Redraw()

    def cleanup(self):
        """ The attribute deleted by this method of ColorCommand aren't created
        in this class, so skip this step.
        """
        pass
 

    def __call__(self, nodes, geomsToColor,property,colorMap=None,**kw):
        """ None <- colorHarmony(self, molName, property, **kw)
        molName :
        property:
        """
        #molsAvailable = self.getAvailableMols()
        #if nodes not in molsAvailable: return None
        apply(self.doitWrapper, (nodes, geomsToColor,property,colorMap), {'redraw':1})
        
    
    def guiCallback(self):
        # get the nodes to be colored
        nodes = self.vf.getSelection()
        if len(nodes)==0: return
        # get the molindexedpolygons geometries to be colored for these nodes
        val = self.showForm('geomsGUI', scrolledFrame = 1,
                            width= 500, height = 200, force=1)
        if val:
            geomsToColor = self.geomsToColor = val['geoms']
        else:
            geomsToColor = self.geomsToColor = None
            return 'ERROR'
        # get the property by which the geometries will be colored
        colorProp = self.getPropsGUI(nodes,geomsToColor)
        if colorProp is None:
            return
        # set up the colorMap
        if not hasattr(self,'colorMap'):
            self.colorMap = self.vf.colorMaps['rgb256']
        if not hasattr(self.colorMap,'gui'):
            self.colorMapGUI = ColorMapGUI(self.colorMap, allowRename=False, modifyMinMax=True)
            self.colorMapGUI.addCallback( self.colorMapEditor_cb )
        self.colorMapEditor_Args = (nodes,geomsToColor,colorProp,)
        # pass the arguments to doit
        apply(self.doitWrapper, self.colorMapEditor_Args+(self.colorMap,),
              {'redraw':1,'log':0,'setupUndo':0})

        
    def colorMapEditor_cb(self, colorMap):
        apply(self.doitWrapper, self.colorMapEditor_Args,
              {'redraw':1,'log':1})



class ReadDockdata(ReadMolIndexedPolygons):
    """
    Package : Pmv
    Module  : sdCommands
    Class   : ReadDockdata
    Command : readDockdata
    
    Description:
    The ReadDockdata class is a subclass of ReadMolIndexedPolygons for
    reading dockdata files as used by surfdock. The propertyList and
    trifile are predefined, so only the vertex file is needed.

    Synopsis:
      None <- readDockdata(molname,vertfile,**kw)
      molName        : name of the molecule to which the polygon belongs
      vertfile       : name of the dockdatafile
      name           : name to assign to the geometry. Defaults to
      vertfile
      
    Keywords: harmony,surfdock,geometry
    """

#    def __call__(self,molName,vertfile,atom_index=None,name=None, **kw):
#        if not kw.has_key('redraw'): kw['redraw'] = 1
#        if not name:
#            name = os.path.split(vertfile)[1]
#            name = name.replace('_','')
#
#        propertyList = ['Area','ShapeIndex','Curvedness',
#                        'Hydro1','Hydro2','Electro','Bval']
#        apply(self.doitWrapper, (molName,vertfile,atom_index,None,propertyList,name), kw)

    def __call__(self, molName, vertfile, trifile, atom_file=None,
                 propertyList=['Area','ShapeIndex','Curvedness',
                               'Hydro1','Hydro2','Electro','Bval'],
                 name=None, **kw):
        """None <- readMolIndexedPolygons(nodes, vertfile, trifile, atom_file, propertyList, name,**kw)
           nodes   : TreeNodeSet holding a molecule
           vertfile: vertices and normals
           trifile : one-based triangulation file
           atom_file: (optional) output of cluster assigning atoms to vertices
           propertyList: list of names of surface properties in the vertfile
           """
        if not kw.has_key('redraw'): kw['redraw'] = 1
        if not name:
            name = os.path.split(vertfile)[1]
            name = name.replace('_','')

        apply( self.doitWrapper,
               (molName, vertfile, trifile, atom_file, propertyList, name),
               kw )


    def guiCallback(self):
        """ 
        """
        # get the molecule for which this is being read
        mol = MoleculeChooser(self.vf).go()
        if not mol:
            return None
        molName = mol.name

        # get the dockdata file
        fileTypes = [("dockdata files","*dockdata*"),]
        fileBrowserTitle = "Read Dockdata File"
        vertfile = self.vf.askFileOpen(types=fileTypes,
                                       title=fileBrowserTitle)
        if not vertfile:
            return

        name = os.path.split(vertfile)[1]
        name = name.replace('_','')
        propertyList = ['Area','ShapeIndex','Curvedness',
                        'Hydro1','Hydro2','Electro','Bval']
        atom_index= None
        apply( self.doitWrapper, (molName,vertfile,atom_index,None,propertyList,name))

class ReadHarmony(ReadMolIndexedPolygons):
    """
    Package : Pmv
    Module  : sdCommands
    Class   : ReadHarmony
    Command : readHarmony
    
    Description:
    The ReadHarmony class is a subclass of ReadMolIndexedPolygons for
    reading files generated by the Harmony suite (usually having the
    suffix 'field'. The propertyList and trifile are known in advance
    for such files, so only the vertices are needed.

    Synopsis:
      None <- readHarmony(molname,vertfile,name,**kw)
      molName        : name of the molecule to which the polygon belongs
      vertfile       : name of the harmony (.field) file
      name           : name to assign to the geometry. Defaults to vertfile

    Keywords: harmony,surfdock,geometry
    """

    def __call__(self,molName, vertfile, atom_index=None, name=None, **kw):
        if not kw.has_key('redraw'): kw['redraw'] = 1
        if not name:
            name = os.path.split(vertfile)[1]
            name = name.replace('_','')
        
        propertyList=['Gaussian Curvature','Mean Curvature',
                      'Max Curvature','Min Curvature','Area']
        apply(self.doitWrapper, (molName,vertfile,atom_index, None,propertyList,name), kw)


    def guiCallback(self):
        """ 
        """
        # get the molecule for which this is being read
        mol = MoleculeChooser(self.vf).go()
        if not mol:
            return None
        molName = mol.name

        # get the dockdata file
        fileTypes = [("harmony files","*field*"),]
        fileBrowserTitle = "Read Harmony File"
        vertfile = self.vf.askFileOpen(types=fileTypes,
                                       title=fileBrowserTitle)
        if not vertfile:
            return

        name = os.path.split(vertfile)[1]
        name = name.replace('_','')
        propertyList = ['Gaussian Curvature','Mean Curvature',
                        'Max Curvature','Min Curvature','Area']
        atom_index=None
        apply( self.doitWrapper, (molName,vertfile,atom_index,None,propertyList,name))


class ReadBlur(ReadMolIndexedPolygons):
    """
    Package : Pmv
    Module  : sdCommands
    Class   : ReadBlur
    Command : readBlur
    
    Description:
    The ReadHarmony class is a subclass of ReadMolIndexedPolygons for
    reading files generated by the Gaussian Blur method. The triangulation
    file is taken from the vertices file (i.e. given MOL.dockdata, it looks
    for MOL.face). Properties are the same as for old harmony dockdata files,
    qith kmax and kmin added at the end

    Synopsis:
      None <- readBlur(molName,vertfile,atom_index,name,**kw)
      molName        : name of the molecule to which the polygon belongs
      vertfile       : name of the blur-generated dockdatafile
      atom_index     : (optional) file containing assignment of vertices to atoms
      name           : (optional) name to assign to the geometry.

    Keywords: blur,surfdock,geometry
    """

    def __call__(self,molName, vertfile, atom_index=None, name=None, **kw):
        if not kw.has_key('redraw'): kw['redraw'] = 1
        if not name:
            name = os.path.split(vertfile)[1]
            name = name.replace('_','')
        
        trifile = vertfile.replace("dockdata","face")
        try:
            f = open(trifile)
            f.close()
        except:
            raise(IOError("Cannot open %d for reading" % trifile))
        propertyList = ['Area','ShapeIndex','Curvedness',
                        'Hydro1','Hydro2','Electro','Bval',
                        'Kmin', 'Kmax']
        apply(self.doitWrapper, (molName,vertfile,trifile,atom_index,propertyList,name), kw)


    def guiCallback(self):
        """ 
        """
        # get the molecule for which this is being read
        mol = MoleculeChooser(self.vf).go()
        if not mol:
            return None
        molName = mol.name

        # get the dockdata file
        fileTypes = [("Blur Files","*dockdata*"),]
        fileBrowserTitle = "Read Gaussian Blur File"
        vertfile = self.vf.askFileOpen(types=fileTypes,
                                       title=fileBrowserTitle)
        if not vertfile:
            return
        trifile = vertfile.replace("dockdata","face")
        try:
            f = open(trifile)
            f.close()
        except:
            raise(IOError("Cannot open %d for reading" % trifile))
        name = os.path.split(vertfile)[1]
        name = name.replace('_','')
        propertyList = ['Area','ShapeIndex','Curvedness',
                        'Hydro1','Hydro2','Electro','Bval',
                        'Kmin', 'Kmax']
        atom_index=None
        apply( self.doitWrapper, (molName,vertfile,trifile,atom_index,propertyList,name))


class ReadMSMS(ReadMolIndexedPolygons):
    """ molName, vertfile,trifile,propertyList,name,normals """

    def __call__(self,molName, vertfile, trifile, atom_index=None, name=None, **kw):
        if not vertfile: vertfile = molName +'.vert'
        if not trifile: trifile = molName +'.tri'
        if not kw.has_key('redraw'): kw['redraw'] = 1
        if not name:
            name = '%sMSMS' % (molName)
        apply(self.doitWrapper, (molName,vertfile,trifile, atom_index), kw)


class DisplayMolIndexedPolygons(DisplayCommand):
    """
    Package : Pmv
    Module  : sdCommands
    Class   : DisplayMolIndexedPolygons
    Command : displayMolIndexedPolygons
    
    Description:
    The DisplayMolIndexedPolygons is used to display MolIndexedPolygons
    instances (or parts thereof) which are associated with the
    selected nodes
    
    Synopsis:
      None <- displayMolIndexPolygons(nodes,name,only,negate,**kw)
      nodes          : nodes for which polygons will be displayed
      name           : name of the polygon to be displayed
      only           : display polygon for these atoms _only_
                       (i.e. undisplay any other parts currently displayed)
      negate         : undisplay selected polygon for selected nodes

    Keywords: harmony,surfdock,display
    """
    
    def doit(self, nodes, name = 'all', only=0, negate=0, **kw):

        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        for mol, atm in map(None, molecules, atomSets):
            idf = InputFormDescr(title ="Display indexedpolygons for %s:"%mol.name)
            geomC = mol.geomContainer
            if name == 'ask':
                for surfName in geomC.molindexedpolygons.keys():
                    idf.append({'name':surfName,
                                'widgetType':Tkinter.Checkbutton,
                                'wcfg':{'text':surfName,
                                        'variable':Tkinter.IntVar()},
                                'gridcfg':{'sticky':'w'}})
                val = self.vf.getUserInput(idf)

            elif name in geomC.molindexedpolygons.keys():
                val = {}
                for surfName in geomC.molindexedpolygons.keys():
                    if surfName == name:
                        val[surfName]=1
                    else:
                        val[surfName]=0
                        
            elif name == 'all':
                val = {}
                for surfName in geomC.molindexedpolygons.keys():
                    val[surfName] = 1

            if not val:
                return None
            
            for surfName in geomC.molindexedpolygons.keys():
                if not val[surfName]: continue

                set = geomC.atoms[surfName]
                if negate: set = set -atm
                else:
                    if only: set = atm
                    else: set = atm.union(set)

                geomC.atoms[surfName] = set
            
                # get the surface object for that molecule
                srf = geomC.molindexedpolygons[surfName][0]

                # get the atom indices
                surfNum = geomC.molindexedpolygons[surfName][1]
                atomindices = []
                for a in set.data:
                    atomindices.append(a.__surfIndex__)

                g = geomC.geoms[surfName]
                if len(atomindices)==0:
                    g.Set(visible=0)
                else:
                    vf, vi, f = srf.getTriangles(atomindices)
                    col = mol.geomContainer.getGeomColor(surfName)
		    # ... g.set() is commented by Qing on 8/15/2005 ...
                    # g.Set( vertices = vf[:,:3], vnormals = vf[:,3:6],
                    #       faces = f[:,:3], materials=col, visible=1 )

    def __call__(self, nodes, name ='all', only=0, negate=0, **kw):
        """None <- displaySurface(nodes, only=0, negate=0, **kw)
           nodes  : TreeNodeSet holding the current selection
           only   : flag when set to 1 only the current selection will be
                    displayed
           negate : flag when set to 1 undisplay the current selection"""
        if not kw.has_key('redraw'): kw['redraw']=1
        kw['only'] = only
        kw['negate'] = negate
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"

        mols = self.vf.expandNodes(nodes)
        if name == None:
            for mol in mols:
                for name in mol.geomContainer.molindexedpolygons.keys():
                    kw['name']
                    apply( self.doitWrapper, (nodes, name), kw)
        else:
            apply( self.doitWrapper, (nodes,name), kw )


    def guiCallback(self):
        idf = InputFormDescr(title ="Display indexedpolygons :")
        idf.append({'name':'display',
                    'widgetType':Pmw.RadioSelect,
                    'listtext':['display','display only', 'undisplay'],
                    'defaultValue':'display',
                    'wcfg':{'orient':'horizontal',
                            'buttontype':'radiobutton'},
                    'gridcfg':{'sticky': 'we'}})
        val = self.vf.getUserInput(idf)
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
            val['name']='ask'
            if self.vf.userpref['Expand Node Log String']['value'] == 0:
                self.nodeLogString = "self.getSelection()"
            apply( self.doitWrapper, (self.vf.getSelection(),), val)
            
class UndisplayMolIndexedPolygons(DisplayMolIndexedPolygons):
    def __call__(self, nodes, name, **kw):
        """None <- undisplaySurface(nodes, **kw)
           nodes  : TreeNodeSet holding the current selection (mv.getSelection())
           """
        kw['negate']= 1
        apply(self.vf.displaySurface, (nodes,name),kw)


class ApplyTransformations(MVSelectFromStringCommand):
    """ Opens up the Transformation Control GUI which allows reading in and
    scanning through transformations. The molecule of interest is selected via
    the pull-down 'Molecule List...' menu. Selecting the directory and file of
    interest in the Qlist menus will cause that file to be read in (to update
    the list of files one must hit return in the Qlist directory entry field).

    The qlist files have the format 'score tx ty tz rx ry rz theta rank', where
    tx,ty,tz is the translation, rx,ry,rz the direction of the rotation axis,
    theta the angle of rotation (in degrees) and rank the rank in the docking.

    On reading in a file of transformations, the default center of rotation is
    the molecule's center of gravity. To change this, read in the quaternions
    with the Center Chooser Dialog button activated. The center of rotation
    can then be set to the current selection, or a type-in value. The center
    of rotation is remembered, so for a series of files the center need only
    be set on reading the first file, after which the toggle can be turned off.

    Transformations of interest can be added to and removed from the preferred
    list, which can be written out to a file. The rank column in such a file
    contains the transformation's position in the original list.

    All the data shown in the GUI are stored as attributes of the molecule.
    Thus, dockings for several molecules can be shown at once, and the GUI
    retrieves the information when a previous molecule is reselected.
    """
    def __init__(self):
        MVSelectFromStringCommand.__init__(self)
        self.refSetName = None
        self.mobSetName = None

    def onAddCmdToViewer(self):
        self.molCts={}
        self.vf.loadModule('fileCommands',topCommand=0)
        self.vf.loadModule('measureCommands',topCommand=0)


    def __call__(self,mol,index,**kw):
        """ None <- applyTransformations(self, molName, index, **kw)
        molName:
        index  :
        """
        if not kw.has_key('redraw'): kw['redraw']=1
        apply (self.doitWrapper, (mol,index), kw)
        

    def doit(self,mol,index):
        if not mol:
            return None
        # sort out the rmsd stuff
        refSetName = self.ifd[16]['widget'].get()
        mobSetName = self.ifd[17]['widget'].get()
        savedSets = self.vf.sets
        if refSetName and mobSetName:
            # make sure the sets exist.
            if (mobSetName in savedSets.keys() and refSetName
                in savedSets.keys()):
                #have the sets changed?
                if (refSetName != self.refSetName or
                    mobSetName != self.mobSetName):
                    refSet = savedSets[refSetName]
                    mobSet = savedSets[mobSetName]
                    refSet = self.vf.getNodesByMolecule(refSet,
                                                        Residue)[1][0]
                    mobSet = self.vf.getNodesByMolecule(mobSet,
                                                        Residue)[1][0]
                    refSet = refSet.uniq()
                    mobSet = mobSet.uniq()
                    refSet.sort()
                    mobSet.sort()
                    refXYZ = []
                    mobXYZ = []
                    # set up lists of coordinates for RMSD:
                    # only use backbone atoms (incl.Cb)
                    for x in range(len(refSet)):
                        refRes = refSet[x]
                        mobRes = mobSet[x]
                        for atname in ['C','CA','CB','N','O']:
                            if (atname in refRes.childByName.keys()
                                and atname in mobRes.childByName.keys()):
                                xyz = refRes.childByName[atname].coords[:]
                                if type(xyz)!=type([]):
                                    xyz=xyz.tolist()
                                refXYZ.append(xyz)
                                xyz = mobRes.childByName[atname].coords[:]
                                mobXYZ.append(xyz)
                    map(lambda x: x.append(1.),mobXYZ)
                    map(lambda x: x.append(1.),refXYZ)
                    self.mobXYZ = N.array(mobXYZ,'f')
                    self.refXYZ = N.array(refXYZ,'f')
                    self.refMol = refSet.top.uniq()[0]
                    self.mobMol = mobSet.top.uniq()[0]
                # get the reference molecule's matrix
                master = self.refMol.geomContainer.geoms['master']
                refMatrix = (master.rotation[:12].tolist() +
                             master.translation.tolist() + [1.])
                refMatrix = N.array(refMatrix,'f')
                refMatrix= N.reshape(refMatrix,(4,4))
            #if either of the GUI entries is not a set, delete it in the GUI
            #to provide a clue
        if mobSetName not in savedSets.keys():
            mobSetName = None
            self.ifd.entryByName['MobSet']['widget'].setentry('')
        if refSetName not in savedSets.keys():
            refSetName = None
            self.ifd.entryByName['RefSet']['widget'].setentry('')
        # loop through the list and display one after another
        validRange = range(len(mol.qlist['totaltransforms']))
        for val in index:
            # reset values > max to max
            if (val-1) > validRange[-1]:
                val = validRange[-1]+1
            # input value of <=0 implies original setting, so apply reset:
            if val==0:
                self.reset()
            # apply transformation in valid range
            else:
                mol.currentQ = val
                transform = mol.qlist['totaltransforms'][val-1]
                score = mol.qlist['energy'][val-1]
                clusterSize = mol.qlist['cluster'][val-1]
                score = "%s, %s" % (score,clusterSize)
                #update the GUI
                self.ifd[2]['widget'].setentry(val)
                self.ifd[3]['widget'].setentry(score)
                # transform the geometries first
                self.transformGeoms(mol,transform)
                if refSetName and mobSetName:
                    #get the mobile molecule's matrix
                    master = self.mobMol.geomContainer.geoms['master']
                    mobMatrix = (master.rotation[:12].tolist() +
                                 master.translation.tolist() + [1.])
                    mobMatrix = N.array(mobMatrix,'f')
                    mobMatrix= N.reshape(mobMatrix,(4,4))
                    #compute the transformed XYZ
                    refXYZ = N.dot(self.refXYZ,refMatrix)
                    mobXYZ = N.dot(self.mobXYZ,mobMatrix)
                    #compute the Rmsd
                    Rmsd = rmsd.RMSDCalculator(refXYZ).computeRMSD(mobXYZ)
                    temp = self.ifd[3]['widget'].get()
                    temp = "%s, %3.1f" % (temp,Rmsd)
                    self.ifd[3]['widget'].setentry(temp)
                # update the viewer
                self.vf.GUI.VIEWER.cameras[0].update()
                self.vf.GUI.VIEWER.Redraw()
        


    def reset(self):
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if mol:
            mol.currentQ=0
            transform  = Transform(trans=(0.,0.,0.),quaternion=[1.,0.,0.,0.])
            #reset the GUI, geometries and coordinates
            self.ifd[2]['widget'].setentry(mol.currentQ)
            self.ifd[3]['widget'].setentry('')
            self.transformGeoms(mol,transform)
            #update the viewer
            self.vf.GUI.VIEWER.cameras[0].update()
            self.vf.GUI.VIEWER.Redraw()
        return

        
    def transformMol(self,mol,transform):
        # initialize the second (transformable) coordinate set at the start.
        atoms = mol.allAtoms
        if len(atoms[0]._coords)==1:
            mol.allAtoms.addConformation(mol.allAtoms.coords)

        #perform the transformation on conf1
        atoms.setConformation(1)
        xyz = atoms.coords[:]
        xyz = transform.apply(xyz)
        atoms.updateCoords(xyz)
        #reset to conf zero before returning
        atoms.setConformation(0)


    def transformGeoms(self,mol,transform):
        # update the transformation to the master geometry
        geoms = mol.geomContainer.geoms
        geoms['master'].SetRotation(transform.getRotMatrix(shape=(16,),
                                                           transpose=1))
        geoms['master'].SetTranslation(transform.getTranslation((3,)))
        # update the measure commands
        self.vf.measureDistanceGC.update()

        
    def buildQlistMenu(self):
        # get the qlists in the directory in the qdir entryfield
        qdir = self.ifd[8]['widget'].get()
        if qdir != '':
            cmd = 'ls %s/*qlist*' % qdir
        else:
            cmd = 'ls ./*qlist*'
        try:
            inputlist = os.popen(cmd).readlines()
        except:
            msg = 'Problem in directory name'
            self.vf.warningMsg(msg)
        filelist = []
        for name in inputlist:
            filename = string.split(name)[0]
            filename = os.path.split(filename)[1]
            filelist.append(filename)
        filelist.sort()
        filelist = tuple(filelist)
        self.ifd[9]['widget'].setlist(filelist)
            

    def getMolVal(self, event=None):
        molWidget=self.ifd[0]['widget']
        for molStr in self.molVar.keys():
            #figure out which check button was just changed
            newVal=self.molVar[molStr].get()
            if newVal==self.oldmolVar[molStr]:
                continue
            else:
                self.oldmolVar[molStr] = newVal
                break
        # if a new molecule has been selected, put it in the entryfield
        curMol = molWidget.get()
        if newVal==1:
            self.increaseCts(self.molCts,molStr)
            if not molStr ==  curMol:
                molWidget.setentry(molStr)
        # or if the current molecule has been deselected, clear the entryfield
        else:
            if molStr == curMol:
                self.molCts[molStr]=0
                molWidget.setentry('')
        # set molVar to zero for all other molecules
        # is this necessary? Yes
        for mol in self.molVar.keys():
            if mol != molStr:
                self.molCts[mol]=0
                self.oldmolVar[mol]=0
                self.molVar[mol].set(0)
       # activate the transformation if a molecule is still selected
        if molWidget.get() != '':
            molWidget.invoke()
        #otherwise clear the form
        else:
            self.clearForm()

    def buildArgs(self,displayRange=[1]):
        args = []
        # widget zero (molecule name)
        if self.ifd[0]['widget'].get()=='':
            self.vf.warningMsg('Molecule "" does not exist')
            return None
        else:
            molName = self.ifd[0]['widget'].get()
            mol = self.vf.expandNodes(molName)[0]
            args.append(mol)
        # widget two (range) (passed from onIncrement or onChangeRange)
        args.append(displayRange)
        # widget eight (choice of origin)
        # args.append(self.ifd[10]['widget'].getcurselection())
        return args


    def clearForm(self):
        self.ifd[0]['widget'].delete(0,'end')
        self.ifd[2]['widget'].setentry('0')
        self.ifd[3]['widget'].setentry('')
        self.ifd[8]['widget'].setentry('')
        self.ifd[9]['widget'].setentry('')
        self.ifd[9]['widget'].setentry('')
        self.ifd[10]['widget'].setentry('')
        self.ifd[10]['widget'].setlist(())
        #move cursor back to Molecule entry
        self.ifd[0]['widget'].focus()
        ###SHOULD ALL THE VARIABLES BE ZEROED HERE???
        for key in self.molCts.keys():
            self.molCts[key]=0
        if hasattr(self, 'oldmolVar'):
            for item in self.oldmolVar.keys():
                self.oldmolVar[item] = 0
        if hasattr(self, 'molVar'):
            for item in self.molVar.keys():
                self.molVar[item].set(0)
        if self.form: self.form.lift()


    def guiCallback(self):
        if not hasattr(self, 'ifd'):
            ifd = self.ifd = InputFormDescr(title = 'Transformation Control')
            ifd.append({'widgetType':Pmw.EntryField,
                        'name':'Molecule',
                        'tooltip':'Select the molecule to be transformed',
                        'wcfg':{'command':self.onChangeMolecule,
                                'label_text':'Mobile Mol Name',
                                'labelpos':'w'},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':3} })
            ifd.append({'name': 'Mol List',
                        'tooltip':'Select the molecule to be transformed',
                        'widgetType':Tkinter.Menubutton,
                        'text': 'Molecule List ...',
                        'gridcfg':{'sticky':Tkinter.W,
                                   'row':-1,
                                   'columnspan':1} })
            ifd.append({'widgetType':Pmw.Counter,
                        'name':'TransformNumber',
                        'wcfg':{'datatype':self.onIncrement,
                                'entryfield_command':self.onChangeRange,
                                'entryfield_value':'0',
                                'autorepeat':0,
                                'labelpos':Tkinter.W+Tkinter.E,
                                'label_text':'Transform #'},
                        'gridcfg':{'sticky':Tkinter.W,
                                   'columnspan':2,}})
            ifd.append({'name':'Score',
                        'widgetType':Pmw.EntryField,
                        'wcfg':{'command':None,
                                'labelpos':'w',
                                'label_text':'Score, Cluster Size, (Rmsd)'},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'row':-1,
                                   'columnspan':2}})
            ifd.append({'name': 'Reset',
                        'tooltip':'Restores the current molecule to its original position',
                        'widgetType':Tkinter.Button,
                        'text': 'Reset',
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':2},
                        'command': self.reset})
            ifd.append({'name': 'ClearForm',
                        'widgetType':Tkinter.Button,
                        'text': 'Clear Form',
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'row':-1,
                                   'columnspan':2}, 
                        'command': self.clearForm})
            ifd.append({'widgetType':Tkinter.Checkbutton,
                        'name':'CenterChooser',
                        'defaultValue':0,
                        'text':'Choose Center',
                        'wcfg':{'variable':Tkinter.IntVar()},
                        'gridcfg':{'columnspan':2}})
            ifd.append({'widgetType':Tkinter.Button,
                        'name':'Dismiss',
                        'text':'Dismiss',
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.E+Tkinter.W,
                                   'row':-1,
                                   'columnspan':2},
                        'command': self.Dismiss_cb})
            ifd.append({'widgetType':Pmw.EntryField,
                        'name':'Qdir',
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':4},
                        'wcfg':{'command':self.onChangeQdir,
                                'label_text':'Qlist Directory',
                                'labelpos':'w'}})
            ifd.append({'widgetType':Pmw.ComboBox,
                        'name':'Qfile',
                        'wcfg':{'label_text':'Qlist Filename',
                                'labelpos':'w',
                                'selectioncommand':self.onChangeQlist,
                                'entryfield_command':self.onChangeQlist,
                                'scrolledlist_items':()},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':4}})
            ifd.append({'widgetType':Pmw.ComboBox,
                        'name':'Preferred',
                        'wcfg':{'label_text':'Preferred List',
                                'labelpos':'w',
                                'selectioncommand':self.selFromPref,
                                'entryfield_command':self.onChangeQlist,
                                'scrolledlist_items':()},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':2}})
            ifd.append({'widgetType':Tkinter.Button,
                        'name':'WriteList',
                        'text':'Write List',
                        'command':self.writeList,
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'row':-1,
                                   'columnspan':2}})
            ifd.append({'widgetType':Tkinter.Button,
                        'name':'Add',
                        'text':'Add to list',
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':2},
                        'command': self.addToList})
            ifd.append({'widgetType':Tkinter.Button,
                        'name':'Remove',
                        'text':'Remove from list',
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'row':-1,
                                   'columnspan':2},
                        'command': self.removeFromList})
            ifd.append({'widgetType':Tkinter.Button,
                        'name':'WritePDB',
                        'text':'WritePDB',
                        'command':self.writePdb,
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':2}})
            ifd.append({'widgetType':Tkinter.Button,
                        'name':'WritePDBQ',
                        'text':'WritePDBQ',
                        'command':self.writePdbq,
                        'wcfg':{'bd':6},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'row':-1,
                                   'columnspan':2}})
            ifd.append({'widgetType':Pmw.EntryField,
                        'name':'RefSet',
                        'wcfg':{'label_text':'Ref Set',
                                'labelpos':'w'},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'columnspan':2} })
            ifd.append({'widgetType':Pmw.EntryField,
                        'name':'MobSet',
                        'wcfg':{'label_text':'Mobile Set',
                                'labelpos':'w'},
                        'gridcfg':{'sticky':Tkinter.W+Tkinter.E,
                                   'row':-1,
                                   'columnspan':2} })
                        
            self.form = self.vf.getUserInput(self.ifd, modal = 0, blocking=0)
            self.ifd.entryByName['Mol List']['widget'].bind('<ButtonPress>',
                                                           self.buildMolMenus,add='+')
        else:
            self.form.deiconify()
            self.form.lift()
        return
    

    def selFromPref(self,entry):
        self.ifd[2]['widget'].setentry(entry)
        self.onChangeRange()
        self.ifd[10]['widget'].setentry(entry)

        
    def addToList(self):
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if not mol:
            return
        if not hasattr(mol,'preferredList'):
            mol.preferredList = []
        entries = self.getRange()
        for entry in entries:
            if entry not in mol.preferredList:
                mol.preferredList.append(entry)
            self.ifd[10]['widget'].setentry(entry)
        mol.preferredList.sort()
        self.ifd[10]['widget'].setlist(mol.preferredList)
        

    def removeFromList(self):
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if not mol:
            msg = 'Please select a molecule'
            self.vf.warningMsg(msg)
            return
        entries = self.getRange()
        if hasattr(mol,'preferredList'):
            for entry in entries:
                if entry in mol.preferredList:
                    mol.preferredList.remove(entry)
            self.ifd[10]['widget'].setlist(mol.preferredList)
            self.ifd[10]['widget'].setentry('')

            
    def writeList(self):
        """
        The preferred list is a device for remembering which docking transformations
        looked good. Favorable conformations can be added or removed from the list,
        which can be written out to a file for future reference. The `rank' record
        in the preferred list stores the conformations position in the original
        list.
        """

        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if not mol:
            msg = 'Please select a molecule'
            self.vf.warningMsg(msg)
            return
        if not hasattr(mol,'preferredList'):
            msg = 'The preferred list is empty'
            self.vf.warningMsg(msg)
            return
        if mol.preferredList ==[]:
            msg = 'The preferred list is empty'
            self.vf.warningMsg(msg)
            return
        fileTypes = [("Qlist","*qlist*"),("All","*.*"),]
        fileBrowserTitle = "Write Quaternion List"
        fileName = self.vf.askFileSave(types=fileTypes,
                                       title=fileBrowserTitle)
        if fileName:
            outfile = open(fileName,'w')
        else:
            return
        for x in mol.preferredList:
            outstring= "%s %s %s\n" % (mol.qlist['energy'][x-1],
                                       mol.qlist['rawtransforms'][x-1].output(),
                                       x)
            outfile.write(outstring)
        outfile.close()

    
    def writePdb(self):
        """ 
        The WritePDB and WritePDBQ buttons cause the coordinates to be updated by
        the current transformations applied to the geometries, and then written
        out. Since these transformations need not have arisen from the qlist, these
        commands are more generally useful: e.g. they can be used to write out the
        transformed coordinates resulting from the superimpose commands
        """
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if mol:
            #set to the transformed set of coordinates
            fileBrowserTitle='PDB files'
            fileName = self.vf.askFileSave(types=[("pdb","*.pdb"),],
                                           title=fileBrowserTitle)
            if fileName:
                masterG = mol.geomContainer.geoms['master']
                rot = masterG.rotation
                trans = masterG.translation
                rotM = Numeric.reshape(rot,(4,4))
                quat = rotax.mat_to_quat(rotM)
                transform = Transform(quaternion=quat,trans=trans)
                self.transformMol(mol,transform)
                mol.allAtoms.setConformation(1)
                self.vf.writePDB(mol, filename=fileName)
                #self.vf.writePDB(fileName,mol)
                mol.allAtoms.setConformation(0)


    def writePdbq(self):
        """ 
        The WritePDB and WritePDBQ buttons cause the coordinates to be updated by
        the current transformations applied to the geometries, and then written
        out. Since these transformations need not have arisen from the qlist, these
        commands are more generally useful: e.g. they can be used to write out the
        transformed coordinates resulting from the superimpose commands
        """
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if mol:
            #set to the transformed set of coordinates
            fileBrowserTitle='PDBQ files'
            fileName = self.vf.askFileSave(types=[("pdbq","*.pdbq"),],
                                           title=fileBrowserTitle)
            if fileName:
                masterG = mol.geomContainer.geoms['master']
                rot = masterG.rotation
                trans = masterG.translation
                rotM = Numeric.reshape(rot,(4,4))
                quat = rotax.mat_to_quat(rotM)
                transform = Transform(quaternion=quat,trans=trans)
                self.transformMol(mol,transform)
                mol.allAtoms.setConformation(1)
                self.vf.writePDBQ(mol, fileName)
                #self.vf.writePDBQ(fileName,mol)
                mol.allAtoms.setConformation(0)

        
    def onIncrement(self,text,factor,increment):
        try:
            value = int(text)
            value = value + (factor*increment)
            if value < 0:
                value = 0
            args = self.buildArgs([value])
            mol = args[0]
            #if not mol:
            #    return
            maxval = len(mol.qlist['totaltransforms'])
            if value > maxval:
                value = maxval
                args = self.buildArgs([value])
            apply(self.doitWrapper, tuple(args),{'redraw':1})
            self.ifd[10]['widget'].setentry('')
            return str(value)
        except:
            msg = 'Error in range:\n %s' % text
            self.vf.warningMsg(msg)
            return text


    def onChangeMolecule(self):
        #update the entry in the qlist fileName field
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if mol:
            if hasattr(mol,'qlist'):
                # update the widget entryfields
                self.ifd[2]['widget'].setentry(mol.currentQ)
                if mol.currentQ > 0:
                    score = mol.qlist['energy'][mol.currentQ]
                    clusterSize = mol.qlist['cluster'][mol.currentQ]
                    score = "%s, %s" % (score,clusterSize)
                else:
                    score = ""
                self.ifd[3]['widget'].setentry(score)
                self.ifd[9]['widget'].setentry(mol.qfile)
                self.ifd[8]['widget'].setentry(mol.qdir)
                self.lastDir=mol.qdir
            else:
                curdir = os.getcwd()
                curdir = string.replace(curdir,'/tmp_mnt','')
                self.ifd[2]['widget'].setentry(0)
                self.ifd[3]['widget'].setentry('')
                self.ifd[8]['widget'].setentry(curdir)
                self.ifd[9]['widget'].setentry('')
            if hasattr(mol,'preferredList'):
                self.ifd[10]['widget'].setlist(mol.preferredList)
            else:
                self.ifd[10]['widget'].setlist([])
            self.ifd[10]['widget'].setentry('')
            self.buildQlistMenu()
            #modify the molCts dictionary
            for key in self.molCts.keys():
                if key == molName:
                    self.molCts[key]=1
                else:
                    self.molCts[key]=0
        else:
            self.clearForm()

            
    def onChangeRange(self):
        displayRange = self.getRange()
        if displayRange:
            args = self.buildArgs(displayRange)
        else:
            return None
        if args:
            apply(self.doitWrapper, tuple(args), {'redraw':1})
            self.ifd[10]['widget'].setentry('')
        else:
            return None

    def getRange(self):
        str_range = self.ifd[2]['widget'].get()
        if not str_range:
            str_range='0'
            self.ifd[2]['widget'].setentry(str_range)
        list_range = string.split(str_range,',')
        int_range = []
        try:
            for item in list_range:
                if item:
                    if '-' in item:
                        item = string.split(item,'-')
                        if item[1]!='':
                            if int(item[1])<int(item[0]):
                                item = range(int(item[0]),int(item[1])-1,-1)
                            else:
                                item = range(int(item[0]),int(item[1])+1)
                        else:
                            item = [int(item[0])]
                        for x in item:
                            int_range.append(x)
                    else:
                        int_range.append(int(item))
            return int_range
        except:
            msg = 'Error in range:\n %s' % str_range
            self.vf.warningMsg(msg)
            return None
        


    def onChangeQdir(self):
        newdirName = self.ifd[8]['widget'].get()
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if hasattr(mol,'qdir'):
            if mol.qdir != newdirName:
                self.ifd[9]['widget'].setentry('')
        self.buildQlistMenu()

    def onChangeQlist(self,entry):
        #update the qlist
        newdirName = self.ifd[8]['widget'].get()
        newfileName = self.ifd[9]['widget'].get()
        molName = self.ifd[0]['widget'].get()
        mol = self.verifyMolName(molName)
        if mol:
            fullName = newdirName+'/'+newfileName
            if self.ifd[6]['wcfg']['variable'].get():
                center = 'ask'
            else:
                center = None
            self.vf.readTransformations(molName,fullName,center)
            self.ifd[8]['widget'].setentry(mol.qdir)
            self.ifd[9]['widget'].setentry(mol.qfile)
            self.ifd[10]['widget'].setlist(mol.preferredList)
            self.ifd[10]['widget'].setentry('')
            mol.qfile = newfileName
            mol.qdir = newdirName
            self.buildQlistMenu()
            self.reset()
        return None
    
    def verifyMolName(self,molName):
        if not molName:
            return None
        molName = string.split(molName,',')
        if len(molName) != 1:
            msg = 'You must select one molecule only'
            self.vf.warningMsg(msg)
            return None
        molName = molName[0]
        mol = self.vf.expandNodes(molName)
        if not mol:
            msg = "Molecule '%s' does not exist" % molName
            self.vf.warningMsg(msg)
            return None
        mol = mol[0]
        return mol

class ReadTransformations(MVCommand):
        """ This command is invoked everytime the Qlist Filename entryfield is
        invoked. If the Center Chooser checkbutton is on, the CenterChooser
        popup dialog will come up to allow the center of rotation to be
        defined before the transformation list is read in. If this is turned
        off, the center of rotation defaults to either the previous center (if
        readTransformations has been invoked previously for this molecule), or to
        the molecules center of gravity.
        readTransformations then reads in lines from the file, which have the
        format 'score tx ty tz rx ry rz theta rank'. These are converted into
        a list of raw transformations (needed for writing out the preferred
        list), and also a list of total transformations (which take into
        account the center of rotation)
        """

        def __call__(self,molName,fileName,center=None,**kw):
            mol = self.vf.expandNodes(molName)[0]
            if mol:
                if center == 'ask':
                    center = CenterChooser(self.vf).go()
                apply( self.doitWrapper, (mol,fileName,center), kw)


        def guiCallback(self):
            # get the molecule for which this is being read
            mol = MoleculeChooser(self.vf).go()
            if not mol:
                return None
            molName = mol.name

            # get the center for the rotations
            # (default center of mass)
            center = CenterChooser(self.vf).go()
            # get the transformations file
            fileTypes = [("Transformation lists","*qlist*"),]
            fileBrowserTitle = "Read Transformation File"
            fileName = self.vf.askFileOpen(types=fileTypes,
                                           title=fileBrowserTitle)
            if not fileName:
                return

            self.doitWrapper(mol,fileName,center=center)
 

            
        def doit(self,mol,fileName,center=None,**kw):
            #get the molecule to attach the qlist to the molecule
            if not mol:
                msg = "There is no molecule '%s'" % molName
                self.vf.warningMsg(msg)
                return None
            if hasattr(mol,'preferredList'):
                if mol.preferredList != []:
                    msg = 'Reading in new quaternions will destroy the preferred list.'
                    proceed = tkMessageBox.askokcancel('Read Quaternions',msg)
                    if not proceed:
                        return None
            try:
                file = open(fileName,'r')
            except:
                msg = 'File %s does not exist' % (fileName,)
                self.vf.warningMsg(msg)
                return
            mol.preferredList=[]
            qdata = file.readlines()
            file.close()
            qlist = {}
            qlist['energy']=[]
            qlist['totaltransforms']=[]
            qlist['rawtransforms']=[]
            qlist['cluster']=[]
            #sort out the center
            if not hasattr(mol,'centerR'):
                if not center: center = 'Center on Molecule'
            if center:
                if center == 'Center on Molecule':
                    ats = mol.allAtoms
                    mol.centerR = N.sum(ats.coords)/len(ats.coords)
                elif center == 'Center on Selection':
                    sel = self.vf.getSelection()
                    ats = self.vf.getNodesByMolecule(sel, Atom)[1]
                    coordsum =0.0
                    Ncoords = 0
                    for set in ats:
                        coordsum = coordsum + N.sum(set.coords)
                        Ncoords = Ncoords + len(set.coords)
                    mol.centerR = coordsum/Ncoords
                else:
                    mol.centerR = N.array(center)
            #set up the transforms to and from the center of rotation
            fromCenter = Transform(trans = -mol.centerR)
            toCenter = fromCenter.inverse()
            #build the transformations list
            for line in qdata:
                numbers = string.split(line)
                if len(numbers) < 9:
                    msg = 'Error in file'
                    self.vf.warningMsg(msg)
                    return None
                trans = N.array(map(lambda x: float(x), numbers[1:4]),'f')
                quat = N.array(map(lambda x: float(x), numbers[4:8]),'f')
                transl = Transform(trans = trans)
                rotate = Transform(quaternion = quat)
                RawTrans = transl*rotate
                Trans = transl*toCenter*rotate*fromCenter
                qlist['energy'].append(numbers[0])         # score
                qlist['totaltransforms'].append(Trans)     # transformation
                qlist['rawtransforms'].append(RawTrans)    # transform as read in
                qlist['cluster'].append(numbers[8])        # cluster rank
            #update the molecules property list
            mol.qlist = qlist
            mol.qfile = os.path.split(fileName)[1]
            mol.qdir = os.path.split(fileName)[0]
            mol.currentQ = 0
            self.lastDir = mol.qdir
            #if the applyTransformations GUI exists, update it
#            if hasattr(self.vf.applyTransformations,'ifd'):
#                applyT = self.vf.applyTransformations.ifd
#                applyT



class SelectVertex(Command, ICOM):
    """This command allows a user to pick a vertex.
    """
    
    def __init__(self, func=None):
        Command.__init__(self, func)
        ICOM.__init__(self)
	# self.objArgOnly = 1
	# self.negateKw = 1


    def setupUndoBefore(self, obj):
        root = self.vf.GUI.VIEWER.rootObject
        piv = tuple(root.pivot)
        self.addUndoCall( (root, piv), {}, self.vf.centerGeom.name )

        
    def doit(self, objects):
        # objects is pick.hist = {geom: [(vertexInd, intance),...]}
        vt = []
        print "\nobjects clicked by left button: \n", objects
        for geom, values in objects.items():
            # print "    geom: ", geom
            # print "    values: ", values
            for vert, instance in values:
	        # print properties
		Area       = geom.properties['Area'][vert]
		ShapeIndex = geom.properties['ShapeIndex'][vert]
		Curvedness = geom.properties['Curvedness'][vert]
		Hydro1     = geom.properties['Hydro1'][vert]
		Hydro2     = geom.properties['Hydro2'][vert]
		Electro    = geom.properties['Electro'][vert]
		Bval       = geom.properties['Bval'][vert]
		Kmin       = geom.properties['Kmin'][vert]
		Kmax       = geom.properties['Kmax'][vert]
                self.vf.message( '\n'+ geom.name + ' - Vertex (zero-based): %d'%( vert ) )
                self.vf.message( '    Area: %.3f, ShapeIndex: %.3f, Curvedness: %.3f\n    Hydro1: %.3f, Hydro2: %.3f, Electro: %.3f\n    Bval: %.3f, Kmin: %.3f, Kmax: %.3f'      
			       %( Area, ShapeIndex, Curvedness, 
			          Hydro1, Hydro2, Electro, 
				  Bval, Kmin, Kmax ) )
		# print original coordinates and normals
                pt = geom.vertices[vert]
		nm = geom.vnormals[vert]
                self.vf.message( '    Original coordinate: %.3f, %.3f, %.3f'%(pt[0], pt[1], pt[2]) )
                self.vf.message( '    Original normal: %.3f, %.3f, %.3f'%(nm[0], nm[1], nm[2]) )
		# print current coordinates and normals
                M = geom.GetMatrix(geom.LastParentBeforeRoot(), instance[1:])
                ptx = M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3]
                pty = M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3]
                ptz = M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3]
                vt.append( (ptx, pty, ptz) )
                nmx = M[0][0]*nm[0]+M[0][1]*nm[1]+M[0][2]*nm[2]+M[0][3]
                nmy = M[1][0]*nm[0]+M[1][1]*nm[1]+M[1][2]*nm[2]+M[1][3]
                nmz = M[2][0]*nm[0]+M[2][1]*nm[1]+M[2][2]*nm[2]+M[2][3]
                self.vf.message( '    Current coordinate: %.3f, %.3f, %.3f'%(ptx, pty, ptz) )
                self.vf.message( '    Current normal: %.3f, %.3f, %.3f'%(nmx, nmy, nmz) )
		# print (on python shell) instance and transformation matrix applied
                print "        instance: ", instance
                print "        transformation matrix M applied: \n", M
        g = [0,0,0]
        i = 0
        for v in vt:
            g[0] += v[0]
            g[1] += v[1]
            g[2] += v[2]
            i+=1
        g[0] = g[0]/i
        g[1] = g[1]/i
        g[2] = g[2]/i
        self.vf.centerGeom( 'root', g, topCommand=0, log=1, setupUndo=1)


    def __call__(self, nodes, **kw):
        # we do not want this command to log or undo itself
        kw['topCommand']=0
        kw['busyIdle']=1
        apply( self.doitWrapper, (nodes,), kw )




ReadTransformationsGUI = CommandGUI()
ReadTransformationsGUI.addMenuCommand('menuRoot', 'Surfdock', 'Read Transformation')
ApplyTransformationsGUI = CommandGUI()
ApplyTransformationsGUI.addMenuCommand('menuRoot', 'Surfdock', 'Apply Transformation')
ReadDockdataGUI = CommandGUI()
ReadDockdataGUI.addMenuCommand('menuRoot', 'Surfdock', 'Read Dockdata Surface')
ReadHarmonyGUI = CommandGUI()
ReadHarmonyGUI.addMenuCommand('menuRoot', 'Surfdock', 'Read Harmony Surface')
ReadBlurGUI = CommandGUI()
ReadBlurGUI.addMenuCommand('menuRoot', 'Surfdock', 'Read Blur Surface')
DisplayMolIndexedPolygonsGUI = CommandGUI()
DisplayMolIndexedPolygonsGUI.addMenuCommand('menuRoot', 'Display','Surfdock Surface')
ColorMolIndexedPolygonsGUI = CommandGUI()
ColorMolIndexedPolygonsGUI.addMenuCommand('menuRoot', 'Surfdock','Color Surface By Property')
SelectVertexGUI = CommandGUI()
SelectVertexGUI.addMenuCommand('menuRoot', 'Surfdock', 'Select A Vertex')

commandList = [
    {'name':'readTransformations','cmd':ReadTransformations(), 'gui':ReadTransformationsGUI},
    {'name':'applyTransformations','cmd':ApplyTransformations(), 'gui':ApplyTransformationsGUI},
    {'name':'readMolIndexedPolygons','cmd':ReadMolIndexedPolygons(), 'gui':None},
    {'name':'readDockdata','cmd':ReadDockdata(), 'gui':ReadDockdataGUI},
    {'name':'readHarmony','cmd':ReadHarmony(), 'gui':ReadHarmonyGUI},
    {'name':'readBlur','cmd':ReadBlur(), 'gui':ReadBlurGUI},
    {'name':'displaySurface','cmd':DisplayMolIndexedPolygons(), 'gui':DisplayMolIndexedPolygonsGUI},
    {'name':'colorSurface','cmd':ColorMolIndexedPolygons(), 'gui':ColorMolIndexedPolygonsGUI},
    {'name':'SelectVertex','cmd':SelectVertex(), 'gui':SelectVertexGUI}]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

