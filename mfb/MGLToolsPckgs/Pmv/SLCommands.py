## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/SLCommands.py,v 1.33 2009/10/16 23:18:01 annao Exp $
#
# $Id: SLCommands.py,v 1.33 2009/10/16 23:18:01 annao Exp $
#

import Tkinter, numpy.oldnumeric as Numeric, Pmw
from DejaVu.IndexedPolygons import IndexedPolygons
from ViewerFramework.VFCommand import CommandGUI
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from Pmv.mvCommand import MVCommand
from DejaVu.GleObjects import GleObject
try:
    from SpatialLogic import geometrylib
    initCommand = True
except:
    print "WARNING: Spatial Logic module not found"
    initCommand = False

from opengltk.OpenGL import GL
from time import time
import thread
from string import split, find ,replace
import types
from os import path
from math import sqrt
from MolKit.molecule import AtomSet, Atom
from Pmv.displayCommands import DisplayCommand
import string

BHTree_CUT = 40.0
def triangle_normal(p1, p2, p3):
    """computes a normal for a triangle"""
    v1 = [0.0, 0.0, 0.0]
    v2 = [0.0, 0.0, 0.0]
    for i in range(3):
        v1[i] = p2[i]-p1[i]   #vector (p1,p2)
        #v2[i] = p3[i]-p2[i]   #vector (p2,p3)
        v2[i] = p3[i]-p1[i]   #vector (p1,p3)
    v = [0.0, 0.0, 0.0]
    v[0] = v1[1]*v2[2] - v1[2]*v2[1]  #v3 = v1^v2
    v[1] = v1[2]*v2[0] - v1[0]*v2[2]
    v[2] = v1[0]*v2[1] - v1[1]*v2[0]
    norm = sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if (norm>1.0e-8): 
        for i in range(3): v[i] = v[i] /norm
    else:
        for i in range(3): v[i] = 0.0
    return v

OPS = ("union", "join", "difference", "intersect")

class SLGeom:
    """An interface class based on Spatial Geometry library (geometrylib.so)"""
    def __init__(self):
        geometrylib.Initialize_Geometry_Module(geometrylib.Default_Geometry_Module())
        
    def readFile0(self, filename):
        """ opens a brp(boundary representations) file, returns the data """
        f_ptr = open(filename)
        lines = f_ptr.readlines()
        f_ptr.close()
        return lines
            
    def indexedFromFile0(self, brp):
        """Reads data from .brp(boundary representations) file , returns
        an array of vertices and a list of faces."""
        
        vertDict = {}
        faceList = []
        findex = []
        mode = None
        vnumber = 0
        for s in brp:
            sp = split(s)

            if len(sp)<1: continue
            if sp[0] == 'POLYGON':
                mode = 'face'
                continue
            if sp[0] == 'PT':
                vertices = [float(sp[1]), float(sp[2]), float(sp[3])] 
                vstring = '%12.6f %12.6f %12.6f'%tuple(vertices)

                if not vertDict.has_key(vstring):
                    vertDict[vstring]=(vnumber)
                    findex.append(vnumber)
                    vnumber = vnumber + 1
                    continue
                else:
                    findex.append(vertDict[vstring])
                    continue
            if sp[0] == 'TX' or sp[0] == 'N':
                continue
            else:
                if mode == 'face':
                    faceList.append(findex)
                    findex = []
                    mode = None

        vertArray = Numeric.zeros( (len(vertDict),3) ).astype('f')
        #normArray = Numeric.zeros( (len(vertDict),3) ).astype('f')

        for i in range(len(vertDict)):
            s = split(vertDict.keys()[i])
            index = vertDict.values()[i]
            vertArray[index] = ([ float(s[0]), float(s[1]), float(s[2]) ])
            #normArray[index] = vertDict.values()[i][1]

        return vertArray, faceList #, normArray

    def readBrepFile(self, filename):

        """ opens a brp file, returns the data """
        f_ptr = open(filename)
        lines = f_ptr.readlines()
        f_ptr.close()
##          i=0
##          sp = split(brp[i])
##          while (len(sp) < 1):
##              i = i+1
##              sp = split(brp[i])
##          if sp[1] != "ASCII":
##              print "file is not ASCII text"
##              return
##          if sp[2] != "BREP":
##              print "file is not BREP"
##              return
        vertList = []
        faceList = []
        for s in lines:
            sp = split(s)

            if len(sp)<1: continue
            if sp[0] == 'POLYGON':
                faceList.append(int(sp[-1]))
                continue
            if sp[0] == 'PT':
                vertList.append([float(sp[1]), float(sp[2]), float(sp[3])])
        return vertList, faceList #, normArray

    def writeBspt(self, bspt_set, filename, ascii = 0):
        """ writes a Bspt in a file"""
        # if ascii == 1 - Bspt is written in a text file.
        fid = geometrylib.New_FileID()
        from os import path
        if path.splitext(filename)[-1] != ".bsp":
            name = filename+".bsp"
        else :
            name = filename
        #name = split(filename, ".")[0]+".bsp"
        fid.file_name = name
        fid.ascii = ascii
        fid.fp = geometrylib.Open_File( "test", fid.file_name, "w" )
        #geometrylib.Write_Set(bspt_set, fid)
        bspt_set = geometrylib.Discard_Set_Shps(bspt_set)
        status = geometrylib.write_Set(bspt_set, fid)
        #print "write status: ", status        
        return status

    def readBspt(self, filename):
        """ reads a Bspt from a file"""
        if not path.isfile(filename):
            print "File %s does not exist." % (filename,)
            return
        t1 = time()
        fid = geometrylib.New_FileID()
        fid.fp = geometrylib.Open_File( "test", filename, "r" ) 
        fid = geometrylib.Read_FileID( fid.fp ) 
        set = geometrylib.Read_Set(fid)
        set = geometrylib.Form_Set_Shps( set )
        t2 = time()
        #print "time to read %s : %.2f"% (filename, (t2-t1))
        #print "set: ", set
        return set

    def buildBrepSet0(self, points, indeces,  solid=1):
        pts = []
        for p in points:
            pts.append(geometrylib.Assign_Point(p[0], p[1], p[2]))
            
        #no vertex normals 
        null_normal = None
        colors = None
        has_texture_coords = 0
        has_vertex_normals = 0
        has_vertex_colors  = 0
        material = geometrylib.Default_Material()
        brep_set = geometrylib.New_BrepSet()
        sh = indeces.shape
        for i in range(sh[0]):
            brep_face = geometrylib.New_BrepFace(material, has_texture_coords, 
                                        has_vertex_normals, has_vertex_colors)
            #print "face No: ", i
            for j in range(sh[1]):
                brep_face = geometrylib.Add_BrepFace_Vertex(brep_face,
                                        pts[indeces[i][j]],
                                        0., 0., #has no texture coords
                                        null_normal,#has no vertex normals
                                        colors)
                #print points[indeces[i][j]],
            #print ''
            brep_set = geometrylib.Add_BrepFace(brep_set, brep_face, 1)
        geometrylib.Make_BrepSet_Solid(brep_set, solid)
        return brep_set

    def buildBrepSet(self, points, indeces, normals = None, solid=1):
        """create Brep set"""
        has_normals = 0
        if normals:
            has_normals = 1 
        brep_set = geometrylib.CreateBrepSet(points,indeces, has_normals, normals)
        geometrylib.Make_BrepSet_Solid(brep_set, solid)
        return brep_set

    def Brep_To_Bspt(self, brep_set, expense = 0.5, exponent = None):
        """create a Set object of BSPT_SET type from Brep_Set"""
        parameters = geometrylib.New_BrepToBsptParams()
        if exponent:
            parameters.exponent = exponent
        bspt_set = geometrylib.BrepSet_to_BsptSet(brep_set, expense,
                                          parameters, None )
        set = geometrylib.New_Set( geometrylib.BSPT_SET, bspt_set )
        return set

    def buildBsptSet(self, points, indeces, normals = None,  expense = 0.5,
                     solid=1):
        """create a Set object of BSPT_SET type"""
        has_normals = 0
        if normals:
            has_normals = 1 
        brep_set = geometrylib.CreateBrepSet(points,indeces, has_normals, normals)
        geometrylib.Make_BrepSet_Solid(brep_set, solid)
        parameters = geometrylib.New_BrepToBsptParams()
        bspt_set = geometrylib.BrepSet_to_BsptSet(brep_set, expense,
                                          parameters, None )
        set = geometrylib.New_Set( geometrylib.BSPT_SET, bspt_set )
        return set
    
    def operateBsptSets(self, set1, set2, operation, expense = 0.5, copy = "duplicate"):
        """operates with two sets of BSPT_SET type.
        - operation can be one of the following:
        'union', 'join', 'difference', 'intersect' .
        - copy can be None , 'duplicate' or 'copy' (for duplicating
        or copying given operands)"""
        
        #ops = ("union", "join", "difference", "intersect")
        if operation not in OPS:
            print "wrong operation name: ", operation
            print OPS
            return None
        copy_func = None
        if copy:
            if copy == "duplicate":
                copy_func = geometrylib.Duplicate_Set
            elif copy == "copy":
                copy_func = geometrylib.Copy_Set
        if operation == "union":
            if copy:
                set = geometrylib.Union_Sets(copy_func(set1),
                                      copy_func(set2), None)
            else:
                set = geometrylib.Union_Sets(set1, set2, None)
        elif operation == "join":
            if copy:
                set = geometrylib.Join_Sets(copy_func(set1),
                                      copy_func(set2), None)
            else:
                set = geometrylib.Join_Sets(set1, set2, None)
        elif operation == "difference":
            if copy:
                set = geometrylib.Difference_Sets(copy_func(set1),
                                      copy_func(set2), None)
            else:
                set = geometrylib.Difference_Sets(set1, set2, None)
        elif operation == "intersect":
            if copy:
                set = geometrylib.Intersect_Sets(copy_func(set1),
                                      copy_func(set2), None)
            else:
                set = geometrylib.Intersect_Sets(set1, set2, None)
##          rset = geometrylib.Convert_Set(set, geometrylib.BREP_SET, expense)
##          size = geometrylib.Size_of_BrepSet(rset)
##          nvert = size.vertices
##          nface = size.faces
##          print nvert , nface 
        return set
    
    def convert_to_Brep(self, set, expense = 0.5, duplicate = 0):
        """Converts Bsp tree set to Brep set (boundary representation)"""
        
        if set.type != geometrylib.BSPT_SET:
            raise TypeError, "Set is not BSPT_Set type"
        if duplicate:
            return geometrylib.Convert_Set(geometrylib.Duplicate_Set(set), geometrylib.BREP_SET, expense)
        else:
            return geometrylib.Convert_Set(set, geometrylib.BREP_SET, expense)
    
    def discardSet(self, set):
        geometrylib.discard_Set(set)
    
    def getBoundaries(self, set, has_vnormals = 0, has_fnormals = 0):
        """returns arrays of vertices, faces, normals """
        
        if set.type != geometrylib.BREP_SET:
            raise TypeError, "Set is not BREP_Set type"
        size = geometrylib.Size_of_BrepSet(set)
        nvert = size.vertices
        nface = size.faces
        import numpy.oldnumeric as Numeric
        verts = Numeric.zeros((nvert,3), 'f') #all vertices
        faces = Numeric.zeros(nface, 'i') #number of vertices per each face
        if has_vnormals:
            vnorms = Numeric.zeros((nvert,3), 'f')
        else:
            vnorms = None
        if has_fnormals:
            fnorms = Numeric.zeros((nface,3), 'f')
        else:
            fnorms = None
        
        geometrylib.BrepSet_out(set, verts, faces, vnorms, fnorms) # verts, faces, norms
        # must be contiguous Num. arrays.
        #print "in getBoundaries: brepsize: ", size, "nvert: ", nvert , "nface:", nface 
        return verts, faces, vnorms, fnorms


    
    def indexedFromArr_old(self, verts, faces, vnorms = None, fnorms = None):
        """returns indexed arrays of vertices, faces, normals ."""
        
        if not len(verts):
            print "vertices array length = 0"
            return None, None, None, None
        vertDict = {}
        faceList = []
        findex = []
        vertList = []
        vnormList = []
        fnormList = []
        vnumber = 0
        fcount = 0
        vcount = 0
        count = 0
        for v in verts:
            vstring = '%12.6f %12.6f %12.6f'%tuple(v)
            if not vertDict.has_key(vstring):
                vertDict[vstring]=(vnumber)
                findex.append(vnumber)
                vertList.append(v)
                if vnorms:
                    vnormList.append(vnorms[count])
                vnumber = vnumber + 1
            else:
                findex.append(vertDict[vstring])
            vcount = vcount+1
            count = count + 1
            if vcount == faces[fcount]:
                faceList.append(findex)
                if fnorms:
                    fnormList.append(fnorms[fcount])
                findex = []
                vcount = 0
                fcount = fcount + 1
        import numpy.oldnumeric as Numeric
        vertArray = Numeric.array(vertList)
        if len(vnormList):
            vnormArray = Numeric.array(vnormList)
        else:
            vnormArray = None
        if len(fnormList):
            fnormArray = Numeric.array(fnormList)
        else:
            fnormArray = None
        return vertArray, faceList, vnormArray, fnormArray

    def indexedFromArr(self, verts, faces, vnorms = None, fnorms = None):
        """returns indexed arrays of vertices, faces, normals ."""
        
        if not len(verts):
            print "vertices array length = 0"
            return None, None, None, None
        # Not all the faces may have the same number of vertices ->
        # find the maximum number of vertices in the face array.
        import numpy.oldnumeric as Numeric
        maxvertnum = Numeric.maximum.reduce(faces)
        faceArray = (Numeric.ones((len(faces), maxvertnum)) *[-1]).astype("f") 
        vertDict = {}
        vertList = []
        vnormList = []
        fnormList = []
        vnumber = 0
        fcount = 0
        vcount = 0
        count = 0
        
        for v in verts:
            #vstring = '%12.6f %12.6f %12.6f'%tuple(v)
            vstring = '%.12f#%.12f#%.12f'%tuple(v)
            if not vertDict.has_key(vstring):
                vertDict[vstring]=(vnumber)
                faceArray[fcount][vcount] = vnumber
                vertList.append(v)
                if vnorms:
                    vnormList.append(vnorms[count])
                vnumber = vnumber + 1
            else:
                faceArray[fcount][vcount] = vertDict[vstring]
            vcount = vcount+1
            count = count + 1
            if vcount == faces[fcount]:
                if fnorms:
                    fnormList.append(fnorms[fcount])
                vcount = 0
                fcount = fcount + 1
        import numpy.oldnumeric as Numeric
        vertArray = Numeric.array(vertList)
        if len(vnormList):
            vnormArray = Numeric.array(vnormList)
        else:
            vnormArray = None
        if len(fnormList):
            fnormArray = Numeric.array(fnormList)
        else:
            fnormArray = None
        return vertArray, faceArray, vnormArray, fnormArray


sl = None

class SLCommand(MVCommand):
    """Command that performs Bsp tree operations such as 'union',
    'difference', 'intersect'."""

    def __init__(self):
        MVCommand.__init__(self)
        self.obj_dict = {} #keys - full names of the Viewer objects
        #values - {'copy_obj': IndexedPolygon(new instance from
        #                                     asIndexedPolygons()),
        #         'v_f': tuple of num_of_verts, num_of_faces of original
        #                object}.
        self.setdict = {}  #keys - as above;
                           #values - built Bsp trees for objects.
        self.cl_atoms = {}
        self.isDisplayed = 0
        self.currOptn = Tkinter.StringVar()
        self.currOptn.set("union")
        self.recomputeBSPT1 = Tkinter.IntVar()
        self.recomputeBSPT1.set(0)
        self.recomputeBSPT2 = Tkinter.IntVar()
        self.recomputeBSPT2.set(0)
        self.bindToMol = Tkinter.IntVar()
        self.bindToMol.set(0)
        self.newobj_name = Tkinter.StringVar()
        #self.sl = None

    def checkDependencies(self, vf):
        try:
            from SpatialLogic import geometrylib
        except:
            print "WARNING: Spatial Logic module not found"

    def buildFormDescr(self, formName):
        if formName == "sl":
            idf = self.idf = InputFormDescr(title = "Geometry operations")
            self.updateObjectDict()
            entries = self.sort_entries(self.allnames_dict)
            idf.append({'name': 'object1',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'labelpos': 'n',
                                'label_text':'Choose object 1',
                                'scrolledlist_items': entries},
                        'gridcfg':{'sticky':'we', 'column': 0,
                                   'columnspan':2},
                        })
            idf.append({'name': 'object2',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'labelpos': 'n',
                                'label_text':'Choose object 2',
                                'scrolledlist_items': entries},
                        'gridcfg':{'sticky':'we', 'row': -1, 'column': 2,
                                   'columnspan':2},
                        })


##              idf.append({'widgetType':Tkinter.Label,
##                          'wcfg': {'text':'Recompute Bspt for objects:'},
##                          'gridcfg':{'sticky':'we', 'columnspan':4,
##                                     'pady': 5}
            
##                          })
            idf.append({'widgetType':Tkinter.Checkbutton,
                        #'name': name,
                        'tooltip': "Recompute Bspt of selected object1 every\ntime a set operation takes place.",
                        'wcfg':{'text': "Recompute Bspt obj1",
                                #'width':5,
                                'variable':self.recomputeBSPT1,
                                'onvalue': 1, 'offvalue': 0},
                        'gridcfg':{'sticky': 'we', 'column': 0,
                                   'columnspan':2}
                        })
            idf.append({'widgetType':Tkinter.Checkbutton,
                        #'name': name,
                        'tooltip': "Recompute Bspt of selected object2 every\ntime a set operation takes place.",
                        'wcfg':{'text': "Recompute Bspt obj2",
                                #'width':5,
                                'variable':self.recomputeBSPT2,
                                'onvalue': 1, 'offvalue': 0},
                        'gridcfg':{'sticky': 'we', 'column': 2, 'row': -1,
                                   'columnspan':2}
                        })
            idf.append({'widgetType':Tkinter.Label,
                        'wcfg': {'text':'Select operation type:'},
                        'gridcfg':{'sticky':'we', 'columnspan':4,
                                   'pady': 5}
                        })
            
            #ops = ["union", "join", "difference", "intersect"]
            tips = ["A single solid object is created from the two objects.\n The goemetry of the overlapping area is eliminated.",
                    "Similar to union, exept that faces of the 2nd object \noverlapping the 1st are retained.",
                    "Subtraction: 1st object is left, minus its \noverlapping region with the 2nd object.",
                    "Preserves the overlapping region only, \neliminating all the rest of both objects."]
            i = 0
            for name in OPS:
                idf.append({'widgetType':Tkinter.Checkbutton,
                            'name': name,
                            'tooltip':tips[i],
                            'wcfg':{'text': name,
                                    #'width':5,
                                    'variable':self.currOptn,
                                    'onvalue': name, 'offvalue':None},
                            'gridcfg':{'sticky': 'we', 'column': i, 'row': 4}
                            })
                i = i+1
            self.newobj_name.set('')
            idf.append({'widgetType' : Pmw.EntryField,
                        'wcfg': {'labelpos':'w',
                                 'label_text' : "New object name(optional):",
                                 'entry_textvariable': self.newobj_name},
                        'gridcfg':{'sticky': 'we', 'column':0,
                                   'columnspan':4, 'pady': 5}
                        })
            idf.append({'widgetType':Tkinter.Checkbutton,
                            'wcfg':{'text': "bind new object to molecule",
                                    #'width':5,
                                    'variable':self.bindToMol ,
                                    'onvalue': 1, 'offvalue': 0},
                            'gridcfg':{'sticky': 'we','columnspan':4}
                            })
            idf.append({'widgetType':Tkinter.Button,
                    'wcfg': {'text': 'Operate',
                             'relief' : Tkinter.RAISED,
                             'borderwidth' : 3,
                             'command':self.operate_cb},
                    'gridcfg':{'sticky':'we', 'columnspan':2},
                    })

            idf.append({'widgetType':Tkinter.Button,
                    'wcfg':{'text': 'Dismiss',
                            'relief' : Tkinter.RAISED,
                            'borderwidth' : 3,
                            'command':self.dismiss_cb},
                    'gridcfg':{'sticky':'we', 'row':-1, 'columnspan':2},
                    })
            
            return idf

    def sort_entries(self, name_dict):
        keys = name_dict.keys()
        vals = name_dict.values()
        vals_sorted = map(None, vals, range(len(vals)))
        vals_sorted.sort()
        keys_sorted = []
        for v in vals_sorted:
            keys_sorted.append(keys[v[1]])
        return keys_sorted
            
    def guiCallback(self):
        if self.isDisplayed:
            self.idf.form.lift()
            return
        self.isDisplayed=1
        val = self.showForm('sl', force = 1, modal = 0)
        #print val

    def updateObjectDict(self):
        """Updates a list of objects on which set operations canbe performed.
        Called with every callback of the command."""
        vi = self.vf.GUI.VIEWER

        allobj = {}
        allnames_dict = {}
        # get a dictionary of all objects in the viewer
        for o in vi.rootObject.AllObjects():
            if o.asIndexedPolygons(run=0):
                v = hasattr(o, 'vertexSet')
                f = hasattr(o, 'faceSet')
                indict = 0
                v_f = ()
                if v and f:
                    v_f = (len(o.vertexSet), len(o.faceSet))
                    if v_f[0] >0 and v_f[1] > 0:
                        allobj[o.fullName] = {'obj':o, 'v_f':v_f}
                        indict = 1
                elif v:
                    v_f = (len(o.vertexSet),)
                    if v_f[0] >0:
                        allobj[o.fullName] = {'obj':o, 'v_f':v_f}
                        indict = 1
                if indict:
                    short_name = o.name
                    entry = short_name + '(' + \
                            replace(o.fullName, short_name, '')+ ')'
                    allnames_dict[entry] = o.fullName
        #check if objects had been added/removed to the viewer since
        #last callback of the command:
        allobj_names = allobj.keys()
        slobj_names = self.obj_dict.keys()
        for name in slobj_names:
            if name in allobj_names:
                #check if the object has changed(number of vertices and faces)
                if allobj[name]['v_f'] != self.obj_dict[name]['v_f']:
                    if self.obj_dict[name].has_key('copy_obj'):
                        del(self.obj_dict[name]['copy_obj'])
                    self.obj_dict[name]['v_f'] = allobj[name]['v_f']
                    self.obj_dict[name]['obj'] = allobj[name]['obj']
                    if name in self.setdict.keys():
                        del(self.setdict[name])
                allobj_names.remove(name)
            else:
                del(self.obj_dict[name])
                if name in self.setdict.keys():
                    del(self.setdict[name])
        for name in allobj_names:
            self.obj_dict[name] = {'v_f': allobj[name]['v_f'],
                                   'obj':allobj[name]['obj']}
        self.allnames_dict = allnames_dict        

    def operate_cb(self):

        name1 = self.idf.entryByName['object1']['widget'].get()
        name2 = self.idf.entryByName['object2']['widget'].get()
        if not name1 or not name2:
            print "object(s) not selected "
            return
        opname = self.currOptn.get()
        if not opname:
            print "Operation type is not selected."
            return
        newobj_name = self.newobj_name.get()
        bindToMol = self.bindToMol.get()
        apply(self.doitWrapper, (self.allnames_dict[name1],
                                 self.allnames_dict[name2],
                                 opname, newobj_name, bindToMol), {})
        self.dismiss_cb()
        self.vf.GUI.VIEWER.Redraw()

    def __call__(self, name1, name2, operation, newobj_name = '', bindToMol = 0, **kw):
        """ None <- SL(name1, name2, operation, newobj_name = '', bindToMol=0)
        name1, name2 - names of two objects (full names, eg: 1crn|msms);
        operation - can be one of the following:
        'union', 'join', 'intersect', 'difference';
        newobj_name - name of new object(optional);
        bindToMol - 1 for binding new object to molecule,
                    0 if no binding is needed.
        """
        
        self.updateObjectDict()
        names = self.obj_dict.keys()
        if name1 not in names:
            print "%s is not a valid operand" % (name1,)
            return
        if name2 not in names:
            print "%s is not a valid operand" % (name2,)
            return
        #ops = ("union", "join", "difference", "intersect")
        if operation not in OPS:
            print "%s in not a valid operation" % operation
            return
        apply(self.doitWrapper, (name1, name2, operation, newobj_name, bindToMol), kw)
        
        
    def doit(self, name1, name2, opname, res_name, bindToMol):
        if not res_name:
            res_name = split(name1,"|")[-1] + '-' + \
                       split(name2, "|")[-1] + '-' + opname
        if res_name in self.setdict.keys():
            print "%s object exists." % (res_name)
            return
        global sl
        if not sl:
            sl = SLGeom()
##          thread.start_new_thread( self.doSetOperation,(name1, name2, opname,
##                                                        res_name))
        self.doSetOperation(name1, name2, opname, res_name,bindToMol) 

    def doSetOperation(self, name1, name2, opname, res_name, bindToMol):
        """ Performs Bspt set operations. """
        ex = 0.5
        expon = 1.0
        bspt_set1 = None
        bspt_set2 = None
        if name1 in self.setdict.keys():
            #check if we need to recompute the Bspt for the object
            if self.recomputeBSPT1.get():
                if hasattr(self.obj_dict[name1]['obj'], "SLnewobj"):
                    # this object had  been created by SL :
                    # do not recompute
                    bspt_set1 = self.setdict[name1]
                else:
                    #remove the computed Bspt from self.setdict
                    # remove a copy of the object from
                    # self.obj_dict so that the function could use
                    # updated arrays of vertices and faces.
                    del(self.setdict[name1])
                    if self.obj_dict[name1].has_key('copy_obj'):
                        del(self.obj_dict[name1]['copy_obj'])
            else:
                bspt_set1 = self.setdict[name1]
                if not geometrylib.Size_of_Set(bspt_set1):
                    bspt_set1 = None
        if not bspt_set1:
            if self.obj_dict[name1].has_key('copy_obj'):
                object1 = self.obj_dict[name1]['copy_obj']
            else:
##                  if isinstance(self.obj_dict[name1]['obj'], GleObject):
##                      object1 = self.obj_dict[name1]['obj']
##                  else:    
                object1 = self.obj_dict[name1]['obj'].asIndexedPolygons(run=1, removeDupVerts=0)
                self.obj_dict[name1]['copy_obj'] = object1
            v1 = object1.vertexSet.vertices.array
            #print "object1: ", object1
##              if isinstance(object1, GleObject):
##                  f1 = self.triangulate_strips(object1.faceSet.faces.array)
##              else:
            f1 = object1.faceSet.faces.array
            #print "obj1, verts: ", len(v1), "faces: ", len(f1)
            brep_set1 = sl.buildBrepSet(v1,f1)
            t1 = time()
            bspt_set1 = sl.Brep_To_Bspt(brep_set1, expense = ex,
                                        exponent = expon)
            t2 = time()
            print "time to build bspt_set1(%s) is %.5f " % (name1, (t2-t1))
        if name2 in self.setdict.keys():
            if self.recomputeBSPT2.get():
                if hasattr(self.obj_dict[name2]['obj'], "SLnewobj"):
                    bspt_set2 = self.setdict[name2]
                else:
                    del(self.setdict[name2])
                    if self.obj_dict[name2].has_key('copy_obj'):
                        del(self.obj_dict[name2]['copy_obj'])
            else:
                bspt_set2 = self.setdict[name2]
                if not geometrylib.Size_of_Set(bspt_set2):
                    bspt_set2 = None
        if not bspt_set2:
            if self.obj_dict[name2].has_key('copy_obj'):
                object2 = self.obj_dict[name2]['copy_obj']
            else:
                object2 = self.obj_dict[name2]['obj'].asIndexedPolygons(run=1, removeDupVerts=0)
                self.obj_dict[name2]['copy_obj'] = object2
            #print "object2: ", object2
            v2 = object2.vertexSet.vertices.array
##              if isinstance(object2, GleObject):
##                  f2 = self.triangulate_strips(object2.faceSet.faces.array)
##              else:
            f2 = object2.faceSet.faces.array
            brep_set2 = sl.buildBrepSet(v2,f2)
            t1 = time()
            bspt_set2 = sl.Brep_To_Bspt(brep_set2, expense = ex,
                                        exponent = expon)
            t2 = time()
            print "time to build bspt_set2(%s) is %.5f " % (name2, (t2-t1))
        rset = sl.operateBsptSets(bspt_set1, bspt_set2, opname,
                                      expense=ex, copy = "duplicate")
        
        brep_set= sl.convert_to_Brep(rset, expense=ex, duplicate=1)
        verts, faces , vnorms,fnorms = sl.getBoundaries(brep_set,
                                                        has_vnormals = 0,
                                                        has_fnormals = 1)
        vs,fs,vns,fns = sl.indexedFromArr(verts, faces, fnorms=fnorms)
        #sl.discardSet(brep_set)
        #brep_set = None
        if find(res_name, "_"):   #name should not contain "_"
            res_name = replace(res_name, "_", "-")
##          if vs:
##              length = map( len, fs) 
##              mlength = max(length)
##              for i in range(len(fs)):
##                  d = mlength-len(fs[i])
##                  if d:
##                      for j in range(d):
##                          fs[i].append(-1)
            vi = self.vf.GUI.VIEWER
            mol= None
            res_fullname = 'root|'+res_name
            if bindToMol:
                from Pmv.guiTools import MoleculeChooser
                mol = MoleculeChooser(self.vf).go()
                if mol:
                    #mol_geom = self.vf.Mols.NodesFromName( molname )[0].geomContainer.masterGeom
                    mol_geom = mol.geomContainer.masterGeom
                    res_fullname = mol_geom.fullName+'|'+res_name
                        
            #find if an object with the same name already  exists:
            obj_fullnames = self.obj_dict.keys()
            objnames = map(lambda x: split(x, '|')[-1], obj_fullnames) 
            overwrite = False
            if res_name in objnames:
                ind = objnames.index(res_name)
                if res_fullname in obj_fullnames:
                    ipg = self.obj_dict[res_fullname]['obj']
                    if hasattr(ipg, "SLnewobj"): # the object is a result
                                                 # of SL operation 
                        if ipg.SLnewobj:
                            overwrite = True # will overwrite the object's
                                             # vertices and faces arrays
##                  if not overwrite:
##                      ipg = self.obj_dict[ obj_fullnames[ind] ]['obj']
##                      if isinstance(ipg, IndexedPolygons):
##                          #ask the user :
##                          root = Tkinter.Toplevel()
##                          root.withdraw()
##                          from SimpleDialog import SimpleDialog
##                          ans = SimpleDialog(root, text="Object %s exists. Overwrite it?"% (obj_fullnames[ind],),
##                                             buttons=["Yes", "No"],
##                                             default=0,
##                                             title="overwrite dialog").go()
##                          root.destroy()
##                          if ans == 0:
##                              overwrite = True
            if overwrite:
                ipg.Set(vertices = vs, faces = fs,fnormals = fns,
                        freshape = True, tagModified=False)
                if mol:
                    cl_atoms = self.vf.bindGeomToMolecularFragment(
                        ipg, mol.name,log=0)
                                               #addToViewer=False, log=0)
                    if cl_atoms:
                        #self.vf.bindGeomToMolecule.data[res_name]['fns']=fns
                        self.vf.bindGeomToMolecularFragment.data[ipg.fullName]['fns']=fns
            else:    
                ipg = IndexedPolygons(res_name, vertices = vs,
                                      faces = fs, #fnormals=fns,
                                      #materials=col2, 
                                      visible=1, inheritMaterial=0, protected=True,)
                if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':                
                    ipg.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
                if mol:
                    cl_atoms = self.vf.bindGeomToMolecularFragment(
                        ipg, mol.name, log=0)
                    if cl_atoms:
                        #self.vf.bindGeomToMolecule.data[res_name]['fns']=fns
                        self.vf.bindGeomToMolecularFragment.data[ipg.fullName]['fns']=fns
                    else:
                        vi.AddObject(ipg)
                else:
                    vi.AddObject(ipg)
                ipg.Set(frontPolyMode=GL.GL_FILL, shading=GL.GL_FLAT)
                ipg.Set(fnormals = fns, tagModified=False)

            self.setdict[ipg.fullName] = rset
            ipg.SLnewobj = True
            print "size of bspt_set1:", geometrylib.Size_of_Set(bspt_set1)    
            print "size of bspt_set2:", geometrylib.Size_of_Set(bspt_set2)
            print "size of rset:", geometrylib.Size_of_Set(rset)
        else:
            print "Number of vertices of the resultant object is 0."
        if name1 not in self.setdict.keys():
            self.setdict[name1] = bspt_set1
        if name2 not in self.setdict.keys():
            self.setdict[name2] = bspt_set2
        #self.dismiss_cb()

    def timeBspt(self, expon = 1.0):
        object = self.vf.GUI.VIEWER.currentObject
        name = object.fullName
        if not isinstance(object, IndexedPolygons):
            print "object %s is not IndexedPolygons instance" % (name,)
            return
        v = object.vertexSet.vertices.array
        if isinstance(object, GleObject):
            f = self.triangulate_strips(object.faceSet.faces.array)
        else:
            f = object.faceSet.faces.array
        n = object.normals
##          if not self.sl:
##              self.sl = SLGeom()
        global sl
        if not sl:
            sl = SLGeom()
        t1 = time()
        #brep_set = sl.buildBrepSet(v,f,normals = n)
        brep_set = sl.buildBrepSet(v,f)
        #brep_set = sl.buildBrepSet0(v,f)
        t2 = time()
        print "time to build brep_set for %s is %.2f " % (name, (t2-t1))
        t1 = time()
        bspt_set = sl.Brep_To_Bspt(brep_set, exponent = expon)
        t2 = time()
        print "time to build bspt_set is %.2f " % (t2-t1)
        if name not in self.setdict.keys():
                self.setdict[name] = bspt_set

    def rm_neg_inds(self, arr):
        """From every face of the given face array removes
        entries that == -1 """
        fl = arr.tolist()
        for face in fl:
            while(face[-1] < 0):
                face.pop(-1)
        return fl
        
    
    def triangulate_strips(self, faces):
        """Triangulate surfaces built with triangle strips."""
        
        size = faces.shape
        # number of triangles in each face (containing triangle strip
        # vertices) from faces array. 
        ntr = size[1]-2
        # new length of triangles array
        nfaces = size[0]*ntr
        new_faces = Numeric.zeros((nfaces, 3), 'i')
        i = 0
        for f in faces:
            for n in range(ntr):
                if (n/2)*2 == n:
                    new_faces[i] = [f[n], f[n+1], f[n+2]]
                else:
                    new_faces[i] = [f[n+2], f[n+1], f[n]]
                i = i + 1
        return new_faces

    def dismiss_cb(self):
          """Withdraws the GUI."""
          self.cmdForms['sl'].withdraw()
          self.isDisplayed=0
        
SLGUI = CommandGUI()
SLGUI.addMenuCommand('menuRoot', 'SL','Operate objects', index=1)

class SaveBsptCommand(MVCommand):
    """Command to save a Bspt set in a file."""
    def __init__(self):
        MVCommand.__init__(self)
        self.isDisplayed=0
        #self.sl = SLGeom()

    def checkDependencies(self, vf):
        try:
            from SpatialLogic import geometrylib
        except:
            print "WARNING: Spatial Logic module not found"

    def guiCallback(self):
        if not hasattr(self.vf, "SL"):
            return
        else :
            if not len(self.vf.SL.setdict):
                return
        if self.isDisplayed:
            self.idf.form.lift()
            return
        self.isDisplayed=1
        val = self.showForm('saveBspt', force = 1, modal = 0)

    def buildFormDescr(self, formName):
        if formName == "saveBspt":
            entries = self.vf.SL.setdict.keys()
            idf = self.idf = InputFormDescr(title = "Save Bspt in file")
            idf.append({'widgetType': Pmw.ScrolledListBox,
                        'name':'BsptList',
                        'wcfg' : {'items':entries,
                                  'labelpos': 'n',
                                  'label_text': "Select a BSPT"},
                        'gridcfg':{'sticky':'we', 'columnspan': 2}
                         })
            idf.append({'widgetType': Tkinter.Button,
                        'wcfg': {'text': 'OK',
                                 'relief' : Tkinter.RAISED,
                                 'borderwidth' : 2,
                                 'command':self.select_cb},
                        'gridcfg':{'sticky':'we',},
                        })
            
            idf.append({'widgetType':Tkinter.Button,
                        'wcfg':{'text': 'Cancel',
                                'relief' : Tkinter.RAISED,
                                'borderwidth' : 3,
                                'command':self.cancel_cb},
                        'gridcfg':{'sticky':'we', 'row':-1},
                        })

            return idf
        
    def select_cb(self):
        selection = \
                self.idf.entryByName['BsptList']['widget'].getcurselection()
        if selection:
            savefile = self.vf.askFileSave(types=[('BSPT file', '*.bsp')],
                                           title = "Save as .bsp")
            if savefile :
                apply(self.doitWrapper, (savefile, selection[0]), {})

            self.cmdForms['saveBspt'].withdraw()
            self.isDisplayed=0

    def cancel_cb(self):
        self.cmdForms['saveBspt'].withdraw()
        self.isDisplayed=0 

    def doit(self, savefile, selection):
        global sl
        if not sl:
            sl = SLGeom()
        status = sl.writeBspt(self.vf.SL.setdict[selection], savefile)
        print "write status:", status
        return
    
    def __call__(self, savefile, selection, **kw):
        """None <- SaveBspt(savefile, selection):
    savefile - name of file with .bsp extension;
    selection - name of Bspt set """
        
        if not hasattr(self.vf, "SL"):
            print "Warning: SLCommand is not loaded"
            return
        if not path.isfile(savefile):
            print "Warning: file %s does not exist" % (savefile,)
            return
        if not selection in self.vf.SL.setdict.keys():
            print "Wrong selection: %s" % (selection,)
            print "list of avalable Bspt(s):"
            print self.vf.SL.setdict.keys()
            return
        apply(self.doitWrapper, (savefile, selection), kw)
        

SaveBsptGUI = CommandGUI()
SaveBsptGUI.addMenuCommand('menuRoot', 'SL','Save Bspt', index = 2)        

class RestoreBsptCommand(MVCommand):
    """Command to build a geometric object out of previously built and
    saved in a file Bspt set. Adds the new object to the viewer.
    The object can be linked to a molecule."""

    def checkDependencies(self, vf):
        from bhtree import bhtreelib
        try:
            from SpatialLogic import geometrylib
        except:
            print "WARNING: SpatialLogic module not found."
                
        
    def __init__(self):
        MVCommand.__init__(self)
        self.isDisplayed=0

    def guiCallback(self):
        if not hasattr(self.vf, "SL"):
            self.warningMsg("This command requires 'SLCommands' module. Load the module.")
            return
        file = self.vf.askFileOpen(types=[('BSPT file', '*.bsp')],
                                   title = "Read .bsp")
        if file:
            root = Tkinter.Toplevel()
            root.withdraw()
            from SimpleDialog import SimpleDialog
            ans = SimpleDialog(root, text="Bind object to molecule?",
                               buttons=["Yes", "No", "Cancel"],
                               default=0,
                               title="new data dialog").go()
            root.destroy()
            mol = None
            if ans == 0:
                from Pmv.guiTools import MoleculeChooser
                ans = MoleculeChooser(self.vf).go()
                if ans:
                    mol = ans.name 
            apply(self.doitWrapper, (file, mol), {})
            
    def doit(self, file, molname=None):
        global sl
        if not sl:
            sl = SLGeom()
        bspt_set = sl.readBspt(file)
        brep_set= sl.convert_to_Brep(bspt_set, expense=0.5, duplicate=1)
        verts, faces , vnorms,fnorms = sl.getBoundaries(brep_set,
                                                        has_vnormals = 0,
                                                        has_fnormals = 1)
        vs,fs,vns,fns = sl.indexedFromArr(verts, faces, fnorms=fnorms)
        #sl.discardSet(brep_set)
        #brep_set = None
        name = path.splitext(path.basename(file))[0]
        if find(name, "_"):   #name should not contain "_"
            name = replace(name, "_", "-")
        if vs:
##              length = map( len, fs) 
##              mlength = max(length)
##              for i in range(len(fs)):
##                  d = mlength-len(fs[i])
##                  if d:
##                      for j in range(d):
##                          fs[i].append(-1)
            ipg = IndexedPolygons(name, vertices = vs,
                                  faces = fs, 
                                  visible=1, inheritMaterial=0, protected=True,)
            if self.vf.userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':                
                ipg.Set( inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
            vi = self.vf.GUI.VIEWER
            cl_atoms = None
            if molname:
                cl_atoms = self.vf.bindGeomToMolecularFragment(ipg, molname)
                
            else:
                vi.AddObject(ipg)
            ipg.Set(frontPolyMode=GL.GL_FILL, shading=GL.GL_FLAT)
            ipg.Set(fnormals = fns, tagModified=False)
            vi.Redraw()
            if molname and cl_atoms:
               self.vf.bindGeomToMolecularFragment.data[name]['fns']=fns 
            self.vf.SL.setdict[ipg.fullName] = bspt_set
        else:
            print "vertices array length of converted brep set is 0"

    def __call__(self, file, molname=None, **kw):
        """ None <- RestoreBspt(file)
        file - a .bsp file"""
        if not hasattr(self.vf, "SL"):
            print "SLCommand is not loaded"
            return
        if not path.isfile(file):
            print "file %s does not exist" % (file,)
            return
        apply(self.doitWrapper, (file, molname), kw)
        
RestoreBsptGUI = CommandGUI()
RestoreBsptGUI.addMenuCommand('menuRoot', 'SL','Restore Bspt', index = 3)
        

if initCommand:                          
    commandList = [
        {'name':'SL', 'cmd':SLCommand(),'gui': SLGUI},
        {'name':'SaveBspt', 'cmd':SaveBsptCommand(),'gui': SaveBsptGUI},
        {'name':'RestoreBspt', 'cmd':RestoreBsptCommand(), 'gui': RestoreBsptGUI},]
else:
    commandList = []
               

def initModule(viewer):
    if initCommand:
        for dict in commandList:
            viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

