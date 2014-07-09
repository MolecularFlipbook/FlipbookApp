## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: November 2006 Authors: 
# Authors: Sophie COON, Ruth HUEY, Michel F. SANNER, Guillaume Vareille
#
#    vareille@scripps.edu
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/labelCommands.py,v 1.77.2.1 2012/05/18 18:45:52 annao Exp $
#
# $Id: labelCommands.py,v 1.77.2.1 2012/05/18 18:45:52 annao Exp $
#

"""
This Module implements commands to label the current selection different ways.
For example:
    by properties  of the current selection
"""
import warnings
import types,  string, Tkinter
import numpy.oldnumeric as Numeric
import Pmw

from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser
from mglutil.util.colorUtil import ToHEX, TkColor

from ViewerFramework.VFCommand import CommandGUI
from mglutil.gui.InputForm.Tk.gui import InputFormDescr, evalString

from mglutil.gui.BasicWidgets.Tk.customizedWidgets import LoadOrSaveText,FunctionButton
from Pmv.mvCommand import MVCommand, MVAtomICOM

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Molecule, Atom, AtomSet, MoleculeSet
from MolKit.protein import Protein, Residue, Chain, ResidueSet, ChainSet, ProteinSet

from DejaVu.glfLabels import GlfLabels
   

class LabelByProperties(MVCommand, MVAtomICOM):
    """selector.selection,property,textcolor,font,location,only,negate,funcItems Command to label the current selection items according to different properties of the selection level (Actually of the first item in the current selection.) Color can be specified as 'red','green','blue','white' or 'yellow'. Other values can be entered as a RGB tuple.One font can selected per label level: Atom,Residue,Chain,Molecule.Labels can be centered on first atom of selection level item, last atom of item or on the center of the item which is found by averaging the coordinates of all the atoms in the item. (eg all atoms in a residue if labelling at the Residue Level)
   \nPackage : Pmv
   \nModule  : labelCommands
   \nClass   : LabelByProperties
   \nCommand : labelByProperty
   \nSynopsis:\n
        None<-labelByProperty(nodes, prop, textcolor, font, location,only, negate, funcItems, format, kw)
   \nRequired Arguments:\n
        nodes --- TreeNodeSet holding the current selection
   \nOptional Arguments:\n    
        prop --- attribute to use for label (default 'name')
        \ntextcolor --- colorname or RGB tuple (default 'white')
        \nfont --- font understood by DejaVu (default 'Helvetica12')
        \nlocation --- 'First', 'Center', 'Last' atom in node (default 'Center')
        \nonly --- show this label only 
        \nnegate --- Boolean flag to toggle visibility of label 
        \nformat --- format string for label
"""

    def __init__(self, func=None):
        #print "LabelByProperties.__init__"#, self
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.negateKw
        self.flag = self.flag | self.objArgOnly

        self.colorDict={'red':(1,0,0), 'green':(0,1,0), 'blue':(0,0,1),
                        'yellow':(1,1,0), 'cyan':(0,1,1),
                        'white':(1,1,1), 'fushia':(1.,0.,0.5),
                        'purple':(1.,0.,1.), 'orange':(1.,0.6,0.)}
        
        self.lastGeomOwnGuiShown = None


    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        if len(atoms)==0: return None
        geomName = string.split(geom.name,'_')[0]
        prop = []
        if propIndex is not None:
            if not isinstance(atoms[0], Atom):
                 for x in atoms:
                     a = x.findType(Atom)[0]
                     d = getattr(a, propName)
                     prop.append(d[propIndex])
            else:
                for a in atoms:
                    d = getattr(a, propName)
                    prop.append(d[propIndex])

        else:
            if not isinstance(atoms[0], Atom):
                for x in atoms:
                    a = x.findType(Atom)[0]
                    prop.append( getattr(a, propName) )
            else:
                for a in atoms:
                    prop.append( getattr(a, propName) )
        return prop


    def onAddCmdToViewer(self):
        #if self.vf.hasGui:
        self.properties = []
        self.colorIndex = 0
        self.molDict = {'Molecule':Molecule,
                        'Atom':Atom, 'Residue':Residue, 'Chain':Chain}
        self.nameDict = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}
        self.leveloption={}
        for name in ['Atom', 'Residue', 'Molecule', 'Chain']:
            col = self.vf.ICmdCaller.levelColors[name]
            bg = TkColor((col[0]/1.5,col[1]/1.5,col[2]/1.5))
            ag = TkColor(col)
            self.leveloption[name]={'bg':bg,'activebackground':ag,
                                    'borderwidth':3}


    def onAddObjectToViewer(self, obj):
        #print "LabelByProperties.onAddObjectToViewer", self.name
        #if not self.vf.hasGui:
        #    return
        #from DejaVu.Labels import Labels
        geomC = obj.geomContainer
        classNames = ['Atom','Residue','Chain','Protein']
        self.level = self.nameDict[self.vf.selectionLevel]
        #for item in classNames:
        for i in range(len(classNames)):
            item = classNames[i]
            #geomName = eval("'%sLabels'" %item)
            geomName = '%sLabels'%item
            for atm in obj.allAtoms:
                atm.colors[geomName] = (1.0, 1.0, 1.0)
                atm.opacities[geomName] = 1.0
            if not geomC.atoms.has_key(geomName):
                # DON'T KNOW HOW TO REPLACE THIS EVAL
                geomC.atoms[geomName]=eval("%sSet()" %item)
                geomC.atomPropToVertices[geomName] = self.atomPropToVertices

            if not geomC.geoms.has_key(geomName):
                j = i + 1
                g = GlfLabels(geomName, fontStyle='solid3d',
                      #inheritMaterial=0,
                      fontTranslation=(0,0,3.), # so the label is less hidden by the structure
                      fontScales=(j*.3,j*.3, .1), # different size for atom, res, chain, mol
                      visible=0,
                      pickable=0,
                     )
                geomC.addGeom(g, parent=geomC.masterGeom,redo=0)
                g.applyStrokes()
            else:
                g = None
                if self.vf.hasGui:
                    g = geomC.VIEWER.FindObjectByName(geomC.masterGeom.fullName+'|'+geomName)
            if g not in self.managedGeometries:
                self.managedGeometries.append(g)


    def update_cb(self, tag, force=False):
        #print "in update_cb with tag=", tag
        if tag!=self.level or force:
            self.level = tag
        #if self.molDict[tag]  != self.vf.ICmdCaller.level.value:
            #self.vf.setIcomLevel(self.molDict[tag])
            self.selection=self.vf.getSelection().uniq().findType(self.molDict[tag]).uniq()
            self.selection.sort()
            if tag == 'Atom':
                if self.selection[0].chargeSet:
                    self.selection[0].charge = self.selection[0].__getattr__('charge')
            self.updateChooser()

            if    self.lastGeomOwnGuiShown is not None \
              and self.lastGeomOwnGuiShown.ownGui.winfo_ismapped() == 1:
                self.labelsSettings_cb()


    def updateChooser(self):
        if not hasattr(self, 'properties'): self.properties = []
        oldProp = self.properties
        self.properties = filter(lambda x: isinstance(x[1], types.IntType) \
                                 or isinstance(x[1], types.FloatType) or \
                                 type(x[1]) is types.StringType,
                                 self.selection[0].__dict__.items())
        # Filter out the private members starting by __.
        self.properties = filter(lambda x: x[0][:2]!='__', self.properties)
        if not self.cmdForms.has_key('default'): return
        descr = self.cmdForms['default'].descr
        if oldProp != self.properties:
            # If the list of properties changed then need to update the listchooser
            widget = descr.entryByName['properties']['widget']
            propertyNames = map(lambda x: (x[0],None), self.properties)
            propertyNames.sort()
            widget.setlist(propertyNames)


    def buildFormDescr(self, formName='default'):
        if formName == 'default': 
            # create the form descriptor
            formTitle = "Label" + self.vf.ICmdCaller.level.value.__name__ +\
                        " by properties"
            idf = InputFormDescr(title = formTitle)
            #val = self.nameDict[self.vf.ICmdCaller.level.value]
            val = self.level
            idf.append({'name':'display',
                        'widgetType':Pmw.RadioSelect,
                        'listtext':['label','label only', 'unlabel'],
                        'defaultValue':'label',
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'we','columnspan':3}})

            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':'________________________________________________________',
                                },
                        'gridcfg':{'columnspan':3}})

            idf.append({'widgetType':Pmw.RadioSelect,
                        'name':'level',
                        'listtext':['Atom','Residue','Chain','Molecule'],
                        'listoption':self.leveloption,#listoption,
                        'defaultValue':val,
                        'wcfg':{'label_text':'Change the PCOM level:',
                                'labelpos':'nw',
                                'command':self.update_cb,
                                },
                        'gridcfg':{'sticky':'we','columnspan':3}})

            if len(self.properties)>0:
                propertyNames = map(lambda x: (x[0], None), self.properties)
                propertyNames.sort()

            idf.append({'name':'properties',
                        'widgetType':ListChooser,
                        'defaultValue':'name',
                        'wcfg':{'entries': propertyNames,
                                'title':'Choose one or more properties:',
                                'lbwcfg':{'exportselection':0},
                                'mode':'multiple','withComment':0},
                        'gridcfg':{'sticky':'we', 'rowspan':4, 'padx':5}})

            self.textColor = (1.,1.,1.)
            idf.append({'widgetType':Tkinter.Button,
                        'name':'textcolor',
                        'wcfg':{'text':'Choose Label Color:',
                                'command':self.chooseColor_cb, 
                                'bg':'white', 'activebackground':'white',
                                'borderwidth':4,
                                },
                        'gridcfg':{'sticky':'w','row':3, 'column':1}})

            idf.append({'name':'Labels settings',
                        'widgetType':Tkinter.Button,
                        'wcfg':{'text': 'Labels settings',
                                'command':self.labelsSettings_cb
                                },
                        'gridcfg':{'row':4,'column':1, 'sticky':'we'}})

            location = ['First','Center' ,'Last']
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'location',
                        'defaultValue':'Center',
                        'wcfg':{'label_text':'Label location: ',
                                'labelpos':'nw',
                                'scrolledlist_items': location},
                        'gridcfg':{'sticky':'w','row':5,'column':1}})
            formats = ['%d','%4.2f','%f','None']
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'format',
                        'defaultValue' : 'None',
                        'wcfg':{'label_text':'Label format: ',
                                'labelpos':'nw',
                                'scrolledlist_items': formats},
                        'gridcfg':{'sticky':'w','row':6,'column':1}})

            return idf

        elif formName=='chooser':
            idf = InputFormDescr(title = 'Label Color')

            idf.append({'widgetType':ColorChooser,
                        'name':'colors',
                        'wcfg':{'commands':self.configureButton,
                                'exitFunction':self.dismiss_cb},
                        'gridcfg':{'sticky':'wens', 'columnspan':3,
                                   }
                        })
            return idf


    def getRelatedLabelsGeom(self):
        molecules, nodeSets = self.vf.getNodesByMolecule(self.selection)
        for mol, nodes in map(None, molecules, nodeSets):
            break
        nodes.sort()
        geomName = nodes[0].__class__.__name__+'Labels'
        labelsGeom = mol.geomContainer.geoms[geomName]
        return labelsGeom


    def labelsSettings_cb(self):
        #print "labelsSettings_cb", self.lastGeomOwnGuiShown
        if self.lastGeomOwnGuiShown is not None:
            self.lastGeomOwnGuiShown.hideOwnGui()
        labelsGeom = self.getRelatedLabelsGeom()
        labelsGeom.showOwnGui()
        self.lastGeomOwnGuiShown = labelsGeom


    def dismiss_cb(self):
        self.cmdForms['chooser'].withdraw()
        self.cmdForms['default'].grabFocus()


    def configureButton(self, col):
        f = self.cmdForms['default']
        bg = ToHEX(col)
        but = f.descr.entryByName['textcolor']['widget']
        but.configure(bg=bg, activebackground=bg)
        self.textColor = col


    def chooseColor_cb(self):
        form = self.showForm('chooser', modal=0, blocking=0)
        self.cmdForms['default'].releaseFocus()
        form.grabFocus()


    def getLastUsedValues(self, formName='default', **kw):
        """Return dictionary of last used values
"""
        values = self.lastUsedValues[formName].copy()
        if values.has_key("font"): values.pop('font')
        return values


    def guiCallback(self):

        self.selection = self.vf.getSelection().copy()
        if len(self.selection) == 0 : return
        ##FIX THIS WHEN MolKit gets straightened out:
        self.level = self.nameDict[self.vf.selectionLevel]
        if isinstance(self.selection, MoleculeSet):
            self.selection = ProteinSet(self.selection)
            itemName = self.selection[0].__class__.__name__
        self.updateChooser()

        # Update the level if the form exists already.
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr
            levelwid = descr.entryByName['level']['widget']
            oldlevel =levelwid.getcurselection()
            #if oldlevel != self.nameDict[self.vf.ICmdCaller.level.value]:
            #    levelwid.invoke(self.nameDict[self.vf.ICmdCaller.level.value])
            if oldlevel != self.level:
                levelwid.invoke(self.level)

        val = self.showForm('default', modal=0, blocking=1)
        if self.cmdForms.has_key('chooser'):
            self.cmdForms['chooser'].withdraw()

        if not val: return
        val['textcolor'] = self.textColor

        lLabelsGeom = self.getRelatedLabelsGeom()
        lLabelsState = lLabelsGeom.getSubClassState()
        lLabelsState.pop('labels') # appart from the labels themselves we want everything
        val['font'] = lLabelsState

        if not val['location']: val['location'] = 'center'
        else: val['location'] = val['location'][0]

        if not val['format'] or val['format'] == ('None',):
            val['format'] = None
        else: val['format'] = val['format'][0]

        if val['display']=='label':
            val['only']= 0
            val['negate'] = 0
            del val['display']
        elif val['display']=='label only':
            val['only']= 1
            val['negate'] = 0
            del val['display']
        elif val['display']== 'unlabel':
            val['negate'] = 1
            val['only'] = 0
            del val['display']
        val['redraw'] = 1
        if val.has_key('level'): del val['level']
        
        if self.lastGeomOwnGuiShown is not None:
            self.lastGeomOwnGuiShown.hideOwnGui()
        
        #apply(self.doitWrapper, (self.vf.getSelection(),), val)
        apply(self.doitWrapper, (self.selection,), val)


    def __call__(self, nodes, properties=['name',], textcolor='white',
                 font='arial1.glf', location='Center', only=False,
                 negate=False, format=None, **kw):
        """None<-labelByProperty(nodes, prop, textcolor, font, location,only, negate, funcItems, format, kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nprop --- attribute to use for label (default 'name')
           \ntextcolor --- colorname or RGB tuple (default 'white')
           \nfont --- font understood by DejaVu (default 'arial1.glf')
           \nlocation --- 'First', 'Center', 'Last' atom in node (default 'Center')
           \nonly --- show this label only 
           \nnegate --- Boolean flag to toggle visibility of label 
           \nformat --- format string for label
"""
        #print "__call__"
        kw['properties']=properties
        kw['textcolor']=textcolor
        kw['font']=font
        kw['location']=location
        kw['only']=only
        kw['negate']=negate
        kw['format']=format
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        self.vf.expandNodes(nodes)
        if not kw.has_key('redraw'):
            kw['redraw']=1
        apply(self.doitWrapper, (nodes,), kw)


    def doit(self, nodes, properties=['name',], textcolor='white',
             font={}, location='Center', only=False, negate=False,
             format=None):

        ###################################################################
        def drawLabels(mol, nodes, materials, properties,
                       font, location, only, negate, format):
            geomName = nodes[0].__class__.__name__+'Labels'

            # find the geoemtry to use, for atoms, label, chains or protein
            labelGeom = mol.geomContainer.geoms[geomName]

            # save parameters for session file
            labelGeom.params = {
                'font': font,
                'textcolor': materials,
                'properties': properties,
                'location': location,
                'format': str(format),
                }
            
            set = mol.geomContainer.atoms[geomName]
            ####if negate, remove current atms from displayed set
            ##if negate:
                ##set = set - nodes
            ##if only, replace displayed set with current atms 
            ##else:
                ##if only:
                    ##set = nodes
                ##else: 
                    ##set = nodes.union(set)
            ##3/11
            ##if negate and a previous set, 
            ##remove current atms from displayed set
            if negate:
                if len(set):
                    set = set - nodes
            ##if only or there were no labels, label current atms 
            elif only or not len(set):
                set = nodes
            ##not negate, not only and some previous labels, 
            ##  label union of old + new
            else:
                set = nodes.union(set)

            ##now, update the geometries:
            # draw atoms with bonds and without bonds
            if len(set)==0:
                labelGeom.Set(vertices=[], labels=[], tagModified=False)
                mol.geomContainer.atoms[geomName] = set
                return

            # 1st lines need to store the wole set in the
            # mol.geomContainer.atoms['lines'] because of the picking.
            mol.geomContainer.atoms[geomName] = set
            propLabels = [""]*len(set)
            for property in properties:
                if type(property) is types.StringType:
                    try:
                        #newPropLabels = eval('set.%s'%property)
                        newPropLabels = getattr(set, property)
                    except KeyError:
                        msg= "all nodes do not have such the property: %s"%property
                        self.warningMsg(msg)
                        newPropLabels =list("_"*len(set))

                else: 
                    continue

                assert len(newPropLabels) == len(propLabels)
                for i in range(len(newPropLabels)):
                    item = newPropLabels[i]
                    if format:
                        try:
                            item = format%newPropLabels[i]
                        except:
                            item = str(newPropLabels[i])
                        ###print item
                    else:
                        item = str(newPropLabels[i])
                    if propLabels[i] =="" :
                        propLabels[i] = propLabels[i]+item
                    else:
                        propLabels[i] = propLabels[i]+";"+item
            propLabels=tuple(propLabels)
            propCenters=[]    
            for item in set:
                z = item.findType(Atom)
                if location=='First':
                    z=z[0]
                    zcoords = Numeric.array(z.coords)
                    zcoords = zcoords+0.2
                    zcoords = zcoords.tolist()
                    propCenters.append(zcoords)
                elif location=='Center':
                    n = int(len(z)/2.)
                    z=z[n]                     
                    zcoords = Numeric.array(z.coords)
                    zcoords = zcoords+0.2                    
                    #zcoords = Numeric.sum(zcoords)/(len(zcoords)*1.0)
                    zcoords = zcoords.tolist()
                    propCenters.append(zcoords)
                if location=='Last':
                    z=z[-1]
                    zcoords = Numeric.array(z.coords)
                    zcoords = zcoords+0.2
                    zcoords = zcoords.tolist()
                    propCenters.append(zcoords)
            propCenters = tuple(propCenters)
            colors = (materials,)

            if isinstance(font, dict):
                apply( GlfLabels.Set, (labelGeom, 1, 0), font)
            else:
                labelGeom.Set(font=font, redo=0)
            labelGeom.Set(labels=propLabels,
                          vertices=propCenters,
                          materials=colors, 
                          visible=1,
                          tagModified=False,
                          inheritMaterial=False,
                         )
        ###################################################################


        #if len(nodes) == 0: return
        if (type(textcolor) is types.TupleType or type(textcolor) is types.ListType)\
           and len(textcolor)==3:
            materials = textcolor

        elif self.colorDict.has_key(textcolor):
            materials = self.colorDict[textcolor]
        elif len(textcolor)>0 and textcolor[0]=='(':
            textlist=string.split(textcolor[1:-1],',')
            try:
                materials = (float(textlist[0]),
                         float(textlist[1]),
                         float(textlist[2]))
            except ValueError:
                warnings.warn("Invalid number entered: %s" %textcolor)
            except IndexError:
                warnings.warn("IndexError for %s" %textcolor)
        molecules, nodeSets = self.vf.getNodesByMolecule(nodes)

        for mol, nodes in map(None, molecules, nodeSets):
            nodes.sort()
            drawLabels(mol, nodes, materials, 
                       properties , font, location, only, negate, format)

LabelByPropertiesGUI = CommandGUI()
LabelByPropertiesGUI.addMenuCommand('menuRoot', 'Display', 'by Properties',
                                     cascadeName= 'Label', index=4)

class LabelByExpression(LabelByProperties):
    """Command to label the current selection items according to different expressions of the selection level (Actually of the first item in the current selection.) Color can be specified as 'red','green','blue','white' or 'yellow'. Other values can be entered as a RGB tuple.One font can selected per label level: Atom,Residue,Chain,Molecule.Labels can be centered on first atom of selection level item, last atom of item or on the center of the item which is found by averaging the coordinates of all the atoms in the item. (eg all atoms in a residue if labelling at the Residue Level)
   \nPackage : Pmv
   \nModule  : labelCommands
   \nClass   : LabelByExpression
   \nCommand : labelByExpression
   \nSynopsis:\n     
        None <--- labelByExpression(nodes,function='lambda x: x.full_name()',
                 lambdaFunc = 1, textcolor='white', font='arial1.glf',
                 location='Center', only=0, negate=0, format=None, **kw)
   \nRequired Arguments:\n     
        nodes --- TreeNode, TreeNodeSet or string representing a TreeNode
                    or a TreeNodeSet holding the current selection.
   \nOptional Arguments:\n      
        function  --- function definition or lambda function returning a
                    list of strings that will used to label the selection.
        \nlambdaFunc --- Boolean flag when set to True the function is a lambda function
                    otherwise it is a regular function.
        \ntextcolor --- string representing the color of the label can also be
                    a rgb tuple (r,g,b).
        \nfont  ---  Font of the label
        \nlocation  --- Can be one of Center, First or Last specifies the location
                    of the label.
        \nformat --- Default is None string format of the label can be %4.2f
        \nonly --- Boolean flag when set to True only the selection is labeled when set
                    to 0 label are added to the existing labels.
        \nnegate --- Boolean flag when set to True the selection is unlabeled
        """
    # comments for map function definition window
    mapLabel = """Define a function or a lambda function to be applied
on each node of the current selection: """

    # code example for map function definition window
    mapText = '\
#def foo(node):\n\
#\t#property <- foo(node)\n\
#\t#property    : string that will be used for labelling\n\
#\t#node        : node from the current selection\n\
#\t#foo will then be applied to each node from the current selection.\n\
#\treturn str(node.full_name())\n\
#OR\n\
#lambda x: str(x.full_name())\n'

    # comments for function to operate on selection
    funcLabel = """Define a function to be applied to
the current selection:"""
    
    # code example for function to operate on selection
    funcText ='\
#def foo(selection):\n\
#\t#values <- foo(node)\n\
#\t#values   : list of string used for labelling\n\
#\t#selection: current selection.\n\
#\tvalues = []\n\
#\t#loop on the current selection\n\
#\tfor i in xrange(len(selection)):\n\
#\t\t#build a list of values to label the current selection.\n\
#\t\tif not hasattr(selection[i], "number"):\n\
#\t\t\tvalues.append("-")\n\
#\t\telse:\n\
#\t\t\tif selection[i].number > 20:\n\
#\t\t\t\tvalues.append(selection[i].number*2)\n\
#\t\t\telse:\n\
#\t\t\t\tvalues.append(selection[i].number)\n\
#\t# this list of values is then returned.\n\
#\treturn values\n'

    def updateInfo_cb(self, value):
        if not self.cmdForms.has_key('default'): return
        widget = self.cmdForms['default'].descr.entryByName['function']['widget']
        changed = 0
        if value == 'lambda function':
            if self.textLabel != self.mapLabel:
                self.textLabel = self.mapLabel
                self.textContent = self.mapText
                changed = 1
        elif value == 'function':
            if self.textLabel != self.funcLabel:
                self.textLabel = self.funcLabel
                self.textContent = self.funcText
                changed = 1
        if changed:
            widget.text.configure(label_text = self.textLabel)
            widget.text.settext(self.textContent)


    def update_cb(self, tag):
        if tag!=self.level:
            self.level = tag
        #if self.molDict[tag]  != self.vf.ICmdCaller.level.value:
        #    self.vf.setIcomLevel(self.molDict[tag])
            self.selection = self.vf.getSelection().uniq().findType(self.molDict[tag]).uniq()
            self.selection.sort()

            
    def buildFormDescr(self, formName='default'):
        if formName == 'default':
            # Create the form descriptor:
            formTitle = "Label by expression"
            idf = InputFormDescr(title = formTitle)

            idf.append({'name':'display',
                        'widgetType':Pmw.RadioSelect,
                        'listtext':['label','label only', 'unlabel'],
                        'defaultValue':'label',
                        'wcfg':{'orient':'horizontal',
                                'buttontype':'radiobutton'},
                        'gridcfg':{'sticky': 'we','columnspan':3}})

            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':'________________________________________________________',
                                },
                        'gridcfg':{'columnspan':3}})
            #val = self.nameDict[self.vf.ICmdCaller.level.value]
            val = self.level
            idf.append({'widgetType':Pmw.RadioSelect,
                        'name':'level',
                        'listtext':['Atom','Residue','Chain','Molecule'],
                        'defaultValue':val,'listoption':self.leveloption,#listoption,
                        'wcfg':{'label_text':'Select the property level:',
                                'labelpos':'nw',
                                'command':self.update_cb,
                                },
                        'gridcfg':{'sticky':'we','columnspan':3}})
            
            idf.append({'name':'functiontype',
                        'widgetType':Pmw.RadioSelect,
                        'listtext':['lambda function', 'function'],
                        'defaultValue':'lambda function',
                        'wcfg':{'label_text':'Choose Expression type:',
                                'labelpos':'nw','orient':'horizontal',
                                'buttontype':'radiobutton',
                                'command':self.updateInfo_cb,
                                },
                        'gridcfg':{'sticky': 'we'}})

            self.textContent = self.mapText
            self.textLabel = self.mapLabel
            idf.append({'name':'function',
                        'widgetType':LoadOrSaveText,
                        'defaultValue': self.textContent,
                        'wcfg':{'textwcfg':{'labelpos':'nw',
                                            'label_text': self.textLabel,
                                            'usehullsize':1,
                                            'hull_width':500,
                                            'hull_height':280,
                                            'text_wrap':'none'},
                                },
                        'gridcfg':{'sticky': 'we','rowspan':4, 'padx':5}})

            idf.append({'widgetType':Tkinter.Label,
                        'wcfg':{'text':""},
                        'gridcfg':{'row':-1}})

            self.textColor = (1.,1.,1.)
            idf.append({'widgetType':Tkinter.Button,
                        'name':'textcolor',
                        'wcfg':{'text':'Choose Label Color:',
                                'command':self.chooseColor_cb,'borderwidth':4,
                                'bg':'white', 'activebackground':'white',
                                },
                        'gridcfg':{'sticky':'w','row':4,'column':1}})

            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'font',
                        'defaultValue':GlfLabels.fontList[0],
                        'wcfg':{'label_text':'   Label font:',
                                'labelpos':'nw',
                                'scrolledlist_items': GlfLabels.fontList},
                        'gridcfg':{'sticky':'we','row':5,'column':1 }})

            location = ['First','Center' ,'Last']
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'location',
                        'defaultValue':'Center',
                        'wcfg':{'label_text':'Label location: ',
                                'labelpos':'nw',
                                'scrolledlist_items': location},
                        'gridcfg':{'sticky':'w','row':6,'column':1}})
            formats = ['%d','%4.2f','%f', 'None']
            idf.append({'widgetType':Pmw.ComboBox,
                        'name':'format',
                        'defaultValue': 'None',
                        'wcfg':{'label_text':'Label format: ',
                                'labelpos':'nw',
                                'scrolledlist_items': formats},
                        'gridcfg':{'sticky':'w','row':7,'column':1}})

            return idf

        elif formName=='chooser':
            idf = InputFormDescr(title = 'Choose Color')

            idf.append({'widgetType':ColorChooser,
                        'name':'colors',
                        'wcfg':{'commands':self.configureButton,
                                'exitFunction':self.dismiss_cb},
                        'gridcfg':{'sticky':'wens', 'columnspan':3}
                        })
            return idf


    def guiCallback(self):
        self.selection = self.vf.getSelection()
        if len(self.selection) == 0 : return
        self.level = self.nameDict[self.vf.selectionLevel]
        val = self.showForm('default')
        if self.cmdForms.has_key('chooser'):
            self.cmdForms['chooser'].withdraw()

        # Update the level if the form exists already.
        if self.cmdForms.has_key('default'):
            descr = self.cmdForms['default'].descr
            levelwid = descr.entryByName['level']['widget']
            oldlevel = levelwid.getcurselection()
            #if oldlevel != self.nameDict[self.vf.ICmdCaller.level.value]:
                #levelwid.invoke(self.nameDict[self.vf.ICmdCaller.level.value])
            if oldlevel != self.level:
                levelwid.invoke(self.level)


        if not val: return
        val['textcolor'] = self.textColor

        if not val['font']: val['font'] = 'arial1.glf'
        else: val['font'] = val['font'][0]

        if not val['location']: val['location'] = 'center'
        else: val['location'] = val['location'][0]

        if not val['format'] or val['format'] == ('None',):
            val['format'] = None
        else: val['format'] = val['format'][0]

        if val['functiontype'] == 'lambda function':
            val['lambdaFunc'] = 1
            del val['functiontype']

        elif val['functiontype'] == 'function':
            val['lambdaFunc'] = 0
            del val['functiontype']

        if val['display']=='label':
            val['only']= 0
            val['negate'] = 0
            del val['display']

        elif val['display']=='label only':
            val['only']= 1
            val['negate'] = 0
            del val['display']
        elif val['display']== 'unlabel':
            val['negate'] = 1
            val['only'] = 0
            del val['display']
        if val.has_key('level'): del val['level']
        val['redraw'] = 1
        apply(self.doitWrapper, (self.selection,), val)
        #apply(self.doitWrapper, (self.vf.getSelection(),), val)


    def __call__(self, nodes,  function='lambda x: x.full_name()',
                 lambdaFunc=True, textcolor='white', font='arial1.glf',
                 location='Center', only=False, negate=False, format=None, **kw):
        """None <--- labelByExpression(nodes,function='lambda x: x.full_name()',
                 lambdaFunc = 1, textcolor='white', font='arial1.glf',
                 location='Center', only=0, negate=0, format=None, **kw)
        \nnodes  --- TreeNode, TreeNodeSet or string representing a TreeNode
                    or a TreeNodeSet holding the current selection.
        \nfunction  --- function definition or lambda function returning a
                    list of strings that will used to label the selection.
        \nlambdaFunc --- Boolean flag when set to True the function is a lambda function
                    otherwise it is a regular function.
        \ntextcolor --- string representing the color of the label can also be
                    a rgb tuple (r,g,b).
        \nfont --- Font of the label
        \nlocation  --- Can be one of Center, First or Last specifies the location
                    of the label.
        \nformat --- Default is None string format of the label can be %4.2f
        \nonly --- Boolean flag when set to True only the selection is labeled when set
                    to 0 label are added to the existing labels.
        \nnegate --- Boolean flag when set to True the selection is unlabeled
        """
        
        kw['function'] = function
        kw['lambdaFunc'] = lambdaFunc
        kw['textcolor']=textcolor
        kw['font']=font
        kw['location']=location
        kw['only']=only
        kw['negate']=negate
        kw['format']=format
        kw['redraw'] = 1
        if type(nodes) is types.StringType:
            self.nodeLogString = "'"+nodes+"'"
        self.vf.expandNodes(nodes)
        apply(self.doitWrapper, (nodes,), kw)
        

    def doit(self, nodes, function='lambda x: x.full_name()', lambdaFunc=True,
             textcolor='white', font='arial1.glf', location='Center',
             only=False, negate=False, format=None):
        
        ##################################################################
        def drawLabels(mol, nodes, materials, function, lambdaFunc,
                       font, location, only, negate, format):
            #font = 'glut'+ font
            geomName = nodes[0].__class__.__name__+'Labels'
            labelGeom = mol.geomContainer.geoms[geomName]
            set = mol.geomContainer.atoms[geomName]
            if negate:
                if len(set):
                    set = set - nodes
            ##if only or there were no labels, label current atms 
            elif only or not len(set):
                set = nodes
            ##not negate, not only and some previous labels, 
            ##  label union of old + new
            else:
                set = nodes.union(set)

            ##now, update the geometries:
            # draw atoms with bonds and without bonds
            if len(set)==0:
                labelGeom.Set(vertices=[], labels=[], tagModified=False)
                mol.geomContainer.atoms[geomName] = set
                return

            # 1st lines need to store the wole set in the
            # mol.geomContainer.atoms['lines'] because of the picking.
            mol.geomContainer.atoms[geomName] = set
            propLabels = [""]*len(set)
            try:
                func = evalString(function)
            except:
                self.warningMsg("Error occured while evaluating the expression")
                return
            if lambdaFunc == 1:
                try:
                    newPropLabels = map(func, set)
                except KeyError:
                    msg= "all nodes do not have such a property"
                    self.warningMsg(msg)
                    newPropLabels =list("?"*len(nodes))

            else:
                try:
                    newPropLabels = func(nodes)
                except KeyError:
                    msg= "all nodes do not have such a property"
                    self.warningMsg(msg)
                    newPropLabels =list("?"*len(nodes))

            assert len(newPropLabels) == len(propLabels)
            for i in range(len(newPropLabels)):
                item = newPropLabels[i]
                if format:
                    try:
                        item = format%newPropLabels[i]
                    except:
                        item = str(newPropLabels[i])
                else:
                    item = str(newPropLabels[i])
                if propLabels[i] =="" :
                    propLabels[i] = propLabels[i]+item
                else:
                    propLabels[i] = propLabels[i]+";"+item
            propLabels=tuple(propLabels)

            propCenters=[]    
            for item in set:
                z = item.findType(Atom)
                if location=='First':
                    z=z[0]
                    zcoords = Numeric.array(z.coords)
                    zcoords = zcoords+0.2
                    zcoords = zcoords.tolist()
                    propCenters.append(zcoords)
                elif location=='Center':
                    n = int(len(z)/2.)
                    z=z[n]
                    zcoords = Numeric.array(z.coords)
                    zcoords = zcoords+0.2
                    #zcoords = Numeric.sum(zcoords)/(len(zcoords)*1.0)
                    zcoords = zcoords.tolist()
                    propCenters.append(zcoords)
                if location=='Last':
                    z=z[-1]
                    zcoords = Numeric.array(z.coords)
                    zcoords = zcoords+0.2
                    zcoords = zcoords.tolist()
                    propCenters.append(zcoords)
            propCenters = tuple(propCenters)
            colors = (materials,)
            labelGeom.Set(labels = propLabels,
                          vertices = propCenters,
                          materials = colors, font = font, visible = 1,
                          tagModified=False)
        ###################################################################

        if len(nodes) == 0: return

        if (type(textcolor) is types.TupleType or type(textcolor) is types.ListType)\
           and len(textcolor)==3:
            materials = textcolor
        elif self.colorDict.has_key(textcolor):
            materials = self.colorDict[textcolor]
        elif len(textcolor)>0 and textcolor[0]=='(':
            textlist=string.split(textcolor[1:-1],',')
            try:
                materials = (float(textlist[0]),
                         float(textlist[1]),
                         float(textlist[2]))
            except ValueError:
                warnings.warn("Invalid number entered: %s" %textcolor)
            except IndexError:
                warnings.warn("IndexError for %s" %textcolor)

        molecules, nodeSets = self.vf.getNodesByMolecule(nodes)

        for mol, nodes in map(None, molecules, nodeSets):
            nodes.sort()
            drawLabels(mol, nodes, materials, function , lambdaFunc, font,
                       location, only, negate, format)

LabelByExpressionGUI = CommandGUI()
LabelByExpressionGUI.addMenuCommand('menuRoot', 'Display', 'by Expression',
                                     cascadeName= 'Label', index=5)

class LabelAtoms(LabelByProperties):

        def guiCallback(self):
            selection = self.vf.getSelection()
            if len(selection) == 0 : return
            selection = selection.findType(Atom).copy()
            val = {}
            val['properties'] = ["name"]
            val['negate'] = not self.GUI.menu[4]['variable'].get()            
            self.doitWrapper( *(selection,), **val)    


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Atom)
            self.doitWrapper( *(nodes,), **kw)


LabelAtomsGUI = CommandGUI()
LabelAtomsGUI.addMenuCommand('menuRoot', 'Display', 'Atoms',
                                cascadeName= 'Label', menuEntryType='checkbutton', index=0)

class LabelResidues(LabelByProperties):
        def guiCallback(self):
            selection = self.vf.getSelection()
            if len(selection) == 0 : return
            selection = selection.findType(Residue).copy()
            val = {}
            val['properties'] = ["name"]
            val['negate'] = not self.GUI.menu[4]['variable'].get()
            self.doitWrapper( *(selection,), **val)


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Residue)
            self.doitWrapper( *(nodes,), **kw)

                   
LabelResiduesGUI = CommandGUI()
LabelResiduesGUI.addMenuCommand('menuRoot', 'Display', 'Residues',
                                cascadeName= 'Label', menuEntryType='checkbutton', index=0)

class LabelChains(LabelByProperties):
        def guiCallback(self):
            selection = self.vf.getSelection()
            if len(selection) == 0 : return
            selection = selection.findType(Chain).copy()
            val = {}
            val['properties'] = ["name"]
            val['negate'] = not self.GUI.menu[4]['variable'].get()
            self.doitWrapper( *(selection,), **val)    


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Chain)
            self.doitWrapper( *(nodes,), **kw)

                   
LabelChainsGUI = CommandGUI()
LabelChainsGUI.addMenuCommand('menuRoot', 'Display', 'Chains',
                             cascadeName= 'Label', menuEntryType='checkbutton', index=0)
           
class LabelMolecules(LabelByProperties):
        def guiCallback(self):
            selection = self.vf.getSelection()
            if len(selection) == 0 : return
            selection = selection.findType(Molecule).copy()
            val = {}
            val['properties'] = ["name"]
            val['negate'] = not self.GUI.menu[4]['variable'].get()
            self.doitWrapper( *(selection,), **val)    


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Molecule)
            self.doitWrapper( *(nodes,), **kw)
                   
LabelMoleculesGUI = CommandGUI()
LabelMoleculesGUI.addMenuCommand('menuRoot', 'Display', 'Molecules',
                                cascadeName= 'Label', menuEntryType='checkbutton', index=0)

class LabelAtomsFull(LabelByExpression):

##         def guiCallback(self):
##             selection = self.vf.getSelection().copy()
##             if len(selection) == 0 : return
##             selection = selection.findType(Atom)
##             val = {}
##             val['properties'] = ["name"]
##             val['negate'] = not self.GUI.menu[4]['variable'].get()            
##             self.doitWrapper( *(selection,), **val)    


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Atom)
            self.doitWrapper( *(nodes,), **kw)


LabelAtomsFullGUI = CommandGUI()
LabelAtomsFullGUI.addMenuCommand('menuRoot', 'Display', 'Atoms Full',
                                 cascadeName= 'Label',
                                 menuEntryType='checkbutton')

class LabelResiduesFull(LabelByExpression):
##         def guiCallback(self):
##             selection = self.vf.getSelection()
##             if len(selection) == 0 : return
##             selection = selection.findType(Residue).copy()
##             val = {}
##             val['properties'] = ["name"]
##             val['negate'] = not self.GUI.menu[4]['variable'].get()
##             self.doitWrapper( *(selection,), **val)    


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Residue)
            self.doitWrapper( *(nodes,), **kw)

                   
LabelResiduesFullGUI = CommandGUI()
LabelResiduesFullGUI.addMenuCommand('menuRoot', 'Display', 'Residues Full',
                                cascadeName= 'Label', menuEntryType='checkbutton')

class LabelChainsFull(LabelByExpression):
##         def guiCallback(self):
##             selection = self.vf.getSelection()
##             if len(selection) == 0 : return
##             selection = selection.findType(Chain).copy()
##             val = {}
##             val['properties'] = ["name"]
##             val['negate'] = not self.GUI.menu[4]['variable'].get()
##             self.doitWrapper( *(selection,), **val)    


        def __call__(self, nodes, **kw):
            nodes = self.vf.expandNodes(nodes)
            nodes = nodes.findType(Chain)
            self.doitWrapper( *(nodes,), **kw)

                   
LabelChainsFullGUI = CommandGUI()
LabelChainsFullGUI.addMenuCommand('menuRoot', 'Display', 'Chains Full',
                             cascadeName= 'Label', menuEntryType='checkbutton')

commandList = [
    {'name':'labelAtoms','cmd': LabelAtoms(), 'gui': LabelAtomsGUI},
    {'name':'labelResidues','cmd': LabelResidues(), 'gui': LabelResiduesGUI},
    {'name':'labelChains','cmd': LabelChains(), 'gui': LabelChainsGUI},
    {'name':'labelMolecules','cmd': LabelMolecules(),'gui': LabelMoleculesGUI},
    {'name':'labelAtomsFull','cmd': LabelAtomsFull(), 'gui': None},
    {'name':'labelResiduesFull','cmd': LabelResiduesFull(), 'gui': None},
    {'name':'labelChainsFull','cmd': LabelChainsFull(), 'gui': None},
    {'name':'labelByProperty','cmd': LabelByProperties(),
     'gui': LabelByPropertiesGUI},
    {'name':'labelByExpression','cmd': LabelByExpression(),
     'gui': LabelByExpressionGUI},    
    ]


def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
