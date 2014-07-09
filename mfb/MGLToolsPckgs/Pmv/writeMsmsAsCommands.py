#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/writeMsmsAsCommands.py,v 1.6 2006/12/27 18:27:00 sargis Exp $
# 
# $Id: writeMsmsAsCommands.py,v 1.6 2006/12/27 18:27:00 sargis Exp $
#
#

import types
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom
from opengltk.OpenGL import GL
from geomutils.geomalgorithms import  TriangleNormals
from ViewerFramework.VFCommand import CommandGUI
from Pmv.mvCommand import MVCommand

class WriteSTL(MVCommand):
    
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('msmsMol'):
            self.vf.loadCommand('msmsCommands', 'msmsMol', 'Pmv',
                                topCommand=0) 

    def writeSTLCATrace(self, mol, filename):
        """Write ca trace of the selected molecules in the STL format"""

	if not hasattr(mol.geomContainer, 'catrace'): #ca trace not computed
	    self.vf.buildCATrace.guiCallback()

        # get the extrude catrace object for that molecule
        caExtrude = mol.geomContainer.geoms['catrace'].extrusion

	# get the vertices and faces
	vertices = caExtrude.vertices
        faces = caExtrude.faces
        f = Numeric.concatenate((faces[:,-2:], faces[:,:1]), 1)
        F = Numeric.concatenate((faces[:,:3], f), 0)
        #n = GL.glTriangleNormals(vertices, F, 'PER_VERTEX')
        n = TriangleNormals(vertices, F, 'PER_VERTEX')


	# compute the face normals
        
        fn = caExtrude.glQuadNormals(self,vertices, faces)
	#fn = GL.glTriangleNormals(vf[:,:3], fa[:,:3])

	f = open(filename, 'w')
	f.write("solid NoName\n")
	for i in range(len(F)):
	    face = F[i]
	    f.write(" facet normal %f %f %f\n" % tuple(fn[i]))
	    f.write("  outer loop\n")
            for f in face:
                f.write("   vertex %f %f %f\n" % tuple(vf[f][:3]))
            f.write("  endloop\n")
	    f.write(" endfacet\n")
	f.write("end solid\n")
	f.close()

    def writeSTLsurface(self, mol, filename):
        """Write the MSMS surface corresponding to all selected molecules
	in the STL format"""

	if not hasattr(mol.geomContainer, 'msms'): #surface not computed
	    self.vf.msmsMol.guiCallback()

        # get the msms surface object for that molecule
        srf = mol.geomContainer.msms

	# get the vertices and faces
	vf, vi, fa = srf.getTriangles()

	# compute the face normals
	#fn = GL.glTriangleNormals(vf[:,:3], fa[:,:3])
        fn = TriangleNormals(vf[:,:3], fa[:,:3])
	f = open(filename, 'w')
	f.write("solid NoName\n")
	for i in range(len(fa)):
	    face = fa[i]
	    f.write(" facet normal %f %f %f\n" % tuple(fn[i]))
	    f.write("  outer loop\n")
	    f.write("   vertex %f %f %f\n" % tuple(vf[face[0]][:3]))
	    f.write("   vertex %f %f %f\n" % tuple(vf[face[1]][:3]))
	    f.write("   vertex %f %f %f\n" % tuple(vf[face[2]][:3]))
	    f.write("  endloop\n")
	    f.write(" endfacet\n")
	f.write("end solid\n")
	f.close()


    def doit(self, nodes, filename):
        self.log(nodes, filename)
#        oldcursor = self.vf.GUI.setCursor('watch')

        if type(nodes)==types.StringType:
            nodes = self.vf.Mols.NodesFromName(nodes)
        
        assert isinstance(nodes,TreeNode) or isinstance(nodes,TreeNodeSet)
        if isinstance(nodes,TreeNode):
            nodes = TreeNodeSet([nodes])

        if len(nodes)==0: return
        atoms = nodes.findType( Atom )
        molecules = atoms.top.uniq()

        for mol in molecules:
	    self.writeSTLsurface(mol, '%s.%s.stl'%(filename, mol.name))

#        self.vf.GUI.setCursor(oldcursor)


    def __call__(self, atoms, filename):
	"""Write STL file ( molecules, filename )"""
        self.doit(atoms, filename)


    def guiCallback(self):
        newfile = self.vf.askFileSave(types = [('STL files', '*.stl'),],
                                 title = 'Select STL files:')
        print 'filename: ', newfile
        if newfile != None:
            self.doit(self.vf.getSelection(), newfile)

writeSTLGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                    'menuButtonName':'File',
                    'menuEntryLabel':'Write STL'}

WriteSTLGUI = CommandGUI()
WriteSTLGUI.addMenuCommand('menuRoot', 'File', 'Write STL')

class WriteColoredM(MVCommand):

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('msmsMol'):
            self.vf.loadCommand('msmsCommands', 'msmsMol', 'Pmv',
                                topCommand = 0) 

    def writeCMsurface(self, mol, filename):
        """Write the MSMS surface corresponding to all selected molecules
	in the .m format with rbg color for each vertex"""

	if not hasattr(mol.geomContainer, 'msms'): #surface not computed
	    self.vf.msmsMol.guiCallback()

        # get the msms surface object for that molecule
        srf = mol.geomContainer.msms

	# get the vertices and faces
	vf, vi, fa = srf.getTriangles()

        # get the colors
        col = mol.geomContainer.geoms['msms'].materials[1028].prop[0]
        assert len(col) == len(vf)

	f = open(filename, 'w')
	for i in xrange(len(vf)):
            f.write("vertex %d %f %f %f %f %f %f\n" % (i+1, vf[i][0],vf[i][1],vf[i][2],col[i][0],col[i][1],col[i][2]) )

	for i in xrange(len(fa)):
	    face = fa[i]
	    f.write("face %d %d %d %d\n" % (i+1, fa[i][0]+1, fa[i][1]+1, fa[i][2]+1))
	f.close()


    def doit(self, nodes, filename):
        self.log(nodes, filename)

        if type(nodes)==types.StringType:
            nodes = self.vf.Mols.NodesFromName(nodes)
        
        assert isinstance(nodes,TreeNode) or isinstance(nodes,TreeNodeSet)
        if isinstance(nodes,TreeNode):
            nodes = TreeNodeSet([nodes])

        if len(nodes)==0: return
        atoms = nodes.findType( Atom )
        molecules = atoms.top.uniq()

        for mol in molecules:
	    self.writeCMsurface(mol, '%s.%s.m'%(filename, mol.name))


    def __call__(self, nodes, filename, **kw):
	"""None <- writeCM(self, nodes, filename, **kw)
        Write colored .m files
        nodes   : current selection, or string representing nodes
        filename: filename
        """
        apply(self.doitWrapper, (nodes, filename), kw)

    def guiCallback(self):
        newfile = self.vf.askFileSave(types = [('.m Files', '*.m'),],
                                      title = "Select .m file:")
        if newfile != None:
            apply(self.doitWrapper, (self.vf.getSelection(), newfile), {})

writeColoredMGuiDescr  = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                          'menuButtonName':'File',
                          'menuEntryLabel':'Write ColoredM'}

WriteColoredMGUI = CommandGUI()
WriteColoredMGUI.addMenuCommand('menuRoot', 'File', 'Write ColoredM')

commandList = [
    #{'name':'writeSTL', 'cmd':WriteSTL(), 'gui':WriteSTLGUI },
    {'name':'writeCM', 'cmd':WriteColoredM(), 'gui':WriteColoredMGUI },
    ]

def initModule(viewer):

    for dict in commandList:
        viewer.addCommand( dict['cmd'], dict['name'], dict['gui'])
