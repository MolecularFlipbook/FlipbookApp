import os,sys
import numpy.oldnumeric as Numeric

class HostPmvCommand():
    def __init__(self,soft='blender'):
        self.initialised=True    
        self.gDict={'CPK':['"cpk"'],
                    'Lines':['"lines"'],
                    'SticksAndBalls':['"balls"','"sticks"'],
                    'ExtrudedSS':['"secondarystructure"'],
                    'MSMS' : ['"MSMS-MOL"']}
        self.joins=False
        self.colorProxyObject=True    
        self.only=False
        self.updateSS = False
        self.use_instances=False
        self.duplicatemol=False
        self.duplicatedMols={}
        self.soft=soft
        self.useTree = 'default'#None#'perRes' #or perAtom    
        self.useIK = False            
        self.rootObj='mol.geomContainer.masterGeom.obj'    
        self.chObj='mol.geomContainer.masterGeom.chains_obj'
        self.useEvent = False
        self.bicyl = False
        
    def init(self,mol):
        #import the required module, and get the current scene from the host        
        astr='import Pmv.hostappInterface.pdb_'+self.soft+' as util\n'
        astr+='import numpy,math\n'
        astr+='from MolKit.protein import Protein, ProteinSet, Residue, Chain, ResidueSet\n'
        astr+='from MolKit.molecule import Atom, AtomSet, BondSet, Molecule , MoleculeSet\n'
        #astr+='from Pmv.moleculeViewer import MoleculeViewer\n'
        astr+='from Pmv.pmvPalettes import *\n'
        astr+='from DejaVu.Shapes import Rectangle2D,Circle2D\n'
        astr+='sc=util.getCurrentScene()\n'
        #astr+='print self\n'
        if self.soft == 'c4d':            
            astr+='import c4d\n'
            astr+='import c4d.documents\n'
            astr+='import c4d.plugins\n'
            #astr+='print sc.get_document_name()\n'
            #astr+='print c4d.mv[sc.get_document_name()]\n'
            #astr+='self= c4d.mv[sc.get_document_name()]\n'                        
        if mol != "" :
            #astr+='print self.Mols\n'         
            astr+='mol=self.getMolFromName('+mol+')\n'
            #mol=mol.replace("'","")
            #astr+='if mol == None : mol=self.getMolFromName("'+mol+'_model1")\n'
        return astr

    def SetJoins(self,val):
        self.joins=val

    def parseMessageToFunc(self,message):
        #parse the incoming pmvCommand which start by self.
        #extract the function name, and the related arguments
        if message.find('self')==0 :
            argind=message.find('(')
            func=message[5:argind]
            arg =message[argind+1:-1]
            arg =arg.split(',')
            return func,arg
        else : return "",""

    def parseSelection(self,mol,arg):
        #parse the passed string selection to the pmv commands
        #mol : first arg parsed and filtered from the message
        #arg : all arg parsed from the messafe
        #return the correct string selection    "1crn:::CA,C,N"                                 
        selection=""
        mol=(mol.split(':')[0])+'"'
        for a in arg:
            ind=a.find('"')
            if ind == 0 : ind =  a[1:].find('"')                          
            selection=selection+a+","
            if ind != -1 : break
        #print "parsing ",selection[0:-2]+';"'
        selection=selection[0:-2]+';"'
        return selection   

    def getChainParentName(self,selection,mol):
        parent=""
        astr=""            
        if selection != mol : 
            astr='chain=select.findParentsOfType(Chain)[0]\n'            
            parent=self.chObj+'[chain.name]'
            parent='util.getObject('+self.chObj+'[chain.name])'
            #astr+='print chain.name,'+parent+'.get_name()\n'
        return parent,astr    

    def createMeshCommands(self,namestring,gstring="g",parent="",space="",proxy=False):
        #function to generate the spring commands which produce a 3d geometri from a pmv geometri
        #namestring : the name of the 3d geometri
        #gstring : the name of the variable instanciating the pmv geometri or the name of the pmv geometry
        #parent : the name of the variable instanciating the 3d parent in the scene
        #space: the tabulation to insert                                  
        astr=''
        if gstring != "g" : astr+=space+'g=mol.geomContainer.geoms['+gstring+']\n'
        astr+=space+'name='+namestring+'\n'
        if proxy : astr+=space+'obj=util.createsNmesh(name,g.getVertices(),None,g.getFaces(),smooth=True,proxyCol='+str(self.colorProxyObject)+')\n'
        else : astr+=space+'obj=util.createsNmesh(name,g.getVertices(),None,g.getFaces(),smooth=True)\n'
        astr+=space+'util.addObjToGeom(obj,g)\n'
        if parent =="" : astr+=space+'util.addObjectToScene(sc,obj[0],parent='+self.rootObj+')\n'
        elif parent == None  : astr+=space+'util.addObjectToScene(sc,obj[0])\n'
        else  : astr+=space+'util.addObjectToScene(sc,obj[0],parent='+parent+')\n'
        return astr
     
    def createSScommands(self,extrude=False):
        astr='for name,g in mol.geomContainer.geoms.items() :\n'
        astr+=' if name[:4] in [\'Heli\', \'Shee\', \'Coil\', \'Turn\', \'Stra\']:\n'
        astr+='  fullname=mol.name+":"+name[-1]+":"+name[:-1]\n'
        #astr+='  print g.name, len(g.getVertices()),fullname in self.sets.keys()\n'
        #astr+='  chain=mol.chains[mol.chains.name.index(name[-1])]\n'
        astr+='  if not hasattr(g,"obj") and display and fullname in self.sets.keys():\n'
        astr+='       parent=util.getObject(mol.geomContainer.masterGeom.chains_obj[name[-1]+"_ss"])\n'
        astr+=self.createMeshCommands('mol.name+"_"+name',parent='parent',space='       ')
        if extrude : #have to replace / redo the geometry
            astr+='  elif hasattr(g,"obj") : util.updateMesh(g,parent=util.getObject(mol.geomContainer.masterGeom.chains_obj[name[-1]+"_ss"]))\n'
        astr+='  if hasattr(g,"obj"):util.toggleDisplay(g.obj,display)\n'
        return astr

    def getSelectionCommand(self,selection):
        astr='select=self.select('+selection+',negate=False, only=True, xor=False, log=0, intersect=False)\n'
        astr+='sel=select.findType(Atom)\n'
        astr+='parentString=None\n'
        astr+='if hasattr(self,"selections"):\n'                                     
        astr+='    parentString=util.compareSel('+selection+',self.selections[mol.name])\n'
        #astr+='print "PS ",parentString\n'                    
        return astr    

    def createMessageCommand(self,func,arg,message):
        #print "createMessgaCommand"
        astr=""
        #astr+='print self\n'        
        mol=""
        sys.stderr.write('mess %s\n'%message)
        if self.useEvent : return astr
        if func=="setSelectionLevel" or func=="select" : return astr
        if len(arg) > 1 : mol=arg[0]
        selection=""
        #sys.stderr.write('mess %s\n'%message)
        sys.stderr.write('func %s\n'%func)
        sys.stderr.write('name %s\n'%mol)
        if ':' in mol : 
            mol=(mol.split(':')[0])+'"'
            selection=self.parseSelection(mol,arg)
        else : selection=mol
        if mol!="" :
            if mol[-1] not in ["'",'"'] : mol=mol+'"'
        sys.stderr.write('sel %s\n'%selection)        
        astr=self.init(mol)        
        #if func!="readMolecule" or func!="readFromWeb" : mol=mol.replace(".","_")
        if func=="readMolecule" or func=="readFromWeb" :
            if self.useEvent : return astr
            #DONT SUPPORT NMR MODEL ...But to avoid error will take only the first one
            #self.computeGasteiger("loop,1CRN", log=0) automatically ad charge..?
            mol=os.path.splitext(os.path.basename(mol))[0]
            mol=mol.replace("'","")
            sys.stderr.write('%s\n'%mol)
            if self.duplicatemol : #molecule already loaded,so the name is overwrite by pmv, add _ind
                print self.duplicatedMols.keys()
                if mol in self.duplicatedMols.keys() : self.duplicatedMols[mol]+=1
                else : self.duplicatedMols[mol]=1
                mol=mol+"_"+str(self.duplicatedMols[mol])
            mol=mol.replace(".","_")
            sys.stderr.write('%s\n'%mol)
            astr+='print self.Mols.name\n'                                    
            astr+='P=mol=self.getMolFromName("'+mol+'")\n'
            astr+='if mol == None : \n'
            #astr+='    print "WARNING RMN MODEL OR ELSE, THERE IS SERVERAL MODEL IN THE FILE\nWE LOAD ONLY LOAD THE 1st\n",self.Mols.name\n'            
            astr+='    P=mol=self.getMolFromName("'+mol+'_model1")\n'
            astr+='    mol.name="'+mol+'"\n'
            #mol=mol.replace("_","")
            sys.stderr.write('%s\n'%mol)
            #astr+='mol.name = mol.name.replace("_","")\n'
            astr+='self.buildBondsByDistance(mol,log=0)\n'
            astr+='center = mol.getCenter()\n'
            #create an empty/null object as the parent of all geom, and build the molecule hierarchy as empty for each Chain 
            astr+='master=util.newEmpty(mol.name,location=center)\n'
            astr+='mol.geomContainer.masterGeom.obj=master\n'
            astr+='util.addObjectToScene(sc,master)\n'
            astr+='mol.geomContainer.masterGeom.chains_obj={}\n'
            astr+='mol.geomContainer.masterGeom.res_obj={}\n'        
            astr+='cloud = util.PointCloudObject(mol.name+"_cloud",vertices=mol.allAtoms.coords)\n'
            astr+='util.addObjectToScene(sc,cloud,parent=master)\n'                    
            astr+='for ch in mol.chains:\n'
            astr+='    ch_center=util.getCenter(ch.residues.atoms.coords)\n'            
            astr+='    chobj=util.newEmpty(ch.full_name(),location=ch_center)\n'#,parentCenter=center)\n'            
            astr+='    mol.geomContainer.masterGeom.chains_obj[ch.name]=util.getObjectName(chobj)\n'
            astr+='    util.addObjectToScene(sc,chobj,parent=master,centerRoot=True)\n'
            astr+='    parent = chobj\n'
            astr+='    cloud = util.PointCloudObject(ch.full_name()+"_cloud",vertices=ch.residues.atoms.coords)\n'
            astr+='    util.addObjectToScene(sc,cloud,parent=chobj)\n'
            if self.useTree == 'perRes' :
                astr+='    for res in ch.residues :\n' 
                astr+='        res_obj = util.makeResHierarchy(res,parent,useIK='+str(self.useIK)+')\n'
                astr+='        mol.geomContainer.masterGeom.res_obj[res.name]=util.getObjectName(res_obj)\n'
            elif self.useTree == 'perAtom' : 
                astr+='    for res in ch.residues :\n' 
                astr+='        parent = util.makeAtomHierarchy(res,parent,useIK='+str(self.useIK)+')\n'
            else :
                astr+='    chobjcpk=util.newEmpty(ch.full_name()+"_cpk",location=ch_center)\n'            
                astr+='    mol.geomContainer.masterGeom.chains_obj[ch.name+"_cpk"]=util.getObjectName(chobjcpk)\n'
                astr+='    util.addObjectToScene(sc,chobjcpk,parent=chobj,centerRoot=True)\n'
                astr+='    chobjballs=util.newEmpty(ch.full_name()+"_bs",location=ch_center)\n'            
                astr+='    mol.geomContainer.masterGeom.chains_obj[ch.name+"_balls"]=util.getObjectName(chobjballs)\n'
                astr+='    util.addObjectToScene(sc,chobjballs,parent=chobj,centerRoot=True)\n'
            astr+='    chobjss=util.newEmpty(ch.full_name()+"_ss",location=ch_center)\n'            
            astr+='    mol.geomContainer.masterGeom.chains_obj[ch.name+"_ss"]=util.getObjectName(chobjss)\n'
            astr+='    util.addObjectToScene(sc,chobjss,parent=chobj,centerRoot=True)\n'            
            astr+='radius = util.computeRadius(P,center)\n'
            astr+='focal = 2. * math.atan((radius * 1.03)/100.) * (180.0 / 3.14159265358979323846)\n'
            astr+='center =center[0],center[1],(center[2]+focal*2.0)\n'
            astr+='util.addCameraToScene("cam_'+mol+'","ortho",focal,center,sc)\n'
            astr+='util.addLampToScene("lamp_'+mol+'",\'Area\',(1.,1.,1.),15.,0.8,1.5,False,center,sc)\n'
            astr+='util.addLampToScene("sun_'+mol+'",\'Sun\',(1.,1.,1.),15.,0.8,1.5,False,center,sc)\n'
        elif func=="deleteMol":
            astr+=""
        elif func=="coarseMolSurface" :
            #self.coarseMolSurface(bindGeom=True, gridSize=32, surfName='CoarseMolSurface', isovalue='fast approximation', immediate=False, padding=0.0, perMol=True, nodes="1CRN", resolution=-0.3, log=0)
            resolutions={"very smooth":-0.1, "medium smooth": -0.3, "smooth": -0.5}
            gname=''
            mol=''
            isovalue=7.2
            resolution=-0.3
            padding=0.0
            sys.stderr.write("ARGS %s\n" %(str(arg)))
            for a in arg :
                if a.split('=')[0].replace(' ','') == 'surfName'  or a.split('=')[0].replace(' ','') == 'name' : gname = a.split('=')[1]
                else : gname="'Coarse'"
                if a.split('=')[0].replace(' ','') == 'nodes'  : 
                    mol=a.split('=')[1].replace(')','')    
                    selection=mol
                if a.split('=')[0].replace(' ','') == 'resolution'  :
                    resolution = a.split('=')[1].replace(')','')
                    if resolution in resolutions.keys(): resolution=str(resolutions[resolution])
                if a.split('=')[0].replace(' ','') == 'padding'  : padding = a.split('=')[1].replace(')','')
                if a.split('=')[0].replace(' ','') == 'isovalue' : isovalue = a.split('=')[1].replace(')','')
                if a.split('=')[0].replace(' ','') == 'gridSize' : gridSize = a.split('=')[1].replace(')','')
            if isovalue == "'fast approximation'" : isovalue=str(self.piecewiseLinearInterpOnIsovalue(eval(resolution)))
            elif isovalue == "'precise value'" : isovalue='7.2'
            astr+='select=self.select('+selection+',negate=False, only=True, xor=False, log=0, intersect=False)\n'
            astr+='sel=select.findType(Atom)\n'
            astr+='name="'+gname+'"\n'
            parent,string=self.getChainParentName(selection,mol)            
            astr+='g=util.coarseMolSurface(self,mol,['+gridSize+','+gridSize+','+gridSize+'],isovalue='+isovalue+',resolution='+resolution+',padding='+padding+',name='+gname+')\n'
            #astr+='g.fullName = "CoarseMolSurface"\n'
            parent,string=self.getChainParentName(selection,mol)
            astr+=string        
            astr+=self.createMeshCommands('name',parent=parent,proxy=True)        
        elif func=="getIsosurface" or func=="setIsovalue" :
            if self.useEvent : return astr
            astr+='map=self.grids['+arg[0]+']\n'
            astr+='name=map.name\n'
            astr+='g = map.srf\n'
            astr+='mol = self.cmol\n'            
            astr+='if hasattr(g,"obj") : #already computed so need update\n'
            astr+='    #print "UPDATE MESH"\n'
            astr+='    util.updateMesh(g,parent='+self.rootObj+')\n'
            astr+='else :\n'
            astr+=self.createMeshCommands('name',parent=self.rootObj,space="    ",proxy=True)
        elif func=="computeMSMS" :
            if self.useEvent : return astr
            for a in arg :
                if a.split('=')[0].replace(' ','') == 'surfName' : 
                    gname = a.split('=')[1]#.replace(')','')
                    break
                else : gname="'MSMS-MOL'"
            astr+='select=self.select('+selection+',negate=False, only=True, xor=False, log=0, intersect=False)\n'
            astr+='sel=select.findType(Atom)\n'
            astr+='name="'+gname+'"\n'
            parent,string=self.getChainParentName(selection,mol)
            astr+=string        
            astr+='g = mol.geomContainer.geoms['+gname+']\n'
            astr+='if hasattr(g,"obj") : #already computed so need update\n'
            if parent == "" : parent=self.rootObj
            astr+='    #print "UPDATE MESH"\n'
            astr+='    util.updateMesh(g,parent='+parent+',proxyCol='+str(self.colorProxyObject)+',mol=mol)\n'
            astr+='else :\n'
            astr+=self.createMeshCommands('name',parent=parent,space="    ",proxy=True)
        elif func=="extrudeSecondaryStructure":
            if self.useEvent : return astr
            astr+='display=self.extrudeSecondaryStructure.lastUsedValues["default"]["display"]\n'        
            astr+=self.createSScommands(extrude=True)
        elif func[0:7]=="display" :
            display = True
            gType=func[7:]
            #astr+='mol=self.getMolFromName('+mol+')\n'
            for a in arg :
                if a.split('=')[0].replace(' ','') == 'negate' : display = eval(a.split('=')[1].replace(')',''))
                if a.split('=')[0].replace(' ','') == 'only' : self.only = eval(a.split('=')[1].replace(')',''))
            astr+='display='+str(not display)+'\n'
            #astr+='only='+str(self.only)+'\n'
            if gType=='ExtrudedSS' : 
                if self.useEvent : return astr
                astr+=self.createSScommands()
            elif gType=='CPK' :
                if self.useEvent : return astr                
                for a in arg :
                    if a.split('=')[0].replace(' ','') == 'quality' : quality = a.split('=')[1].replace(')','')
                astr+='options=self.displayCPK.lastUsedValues["default"]\n'
                astr+='needRedo=False\n'
                astr+='if options.has_key("redraw"):\n'
                astr+='    needRedo=True\n'
                astr+='g = mol.geomContainer.geoms['+self.gDict[gType][0]+']\n'            
                astr+='name='+selection+'+"_"+'+self.gDict[gType][0]+'\n'
                astr+='select=self.select('+selection+',negate=False, only=True, xor=False, log=0, intersect=False)\n'
                astr+='#print name,select\n'
                astr+='sel=select.findType(Atom)\n'
                astr+='if not hasattr(g,"obj") and display:\n' #if no mesh have to create it for evey atms
                astr+='    name='+mol+'+"_"+'+self.gDict[gType][0]+'\n'
                astr+='    mesh=util.createBaseSphere(name="base_cpk",quality=options["quality"],cpkRad=options["cpkRad"],scale=options["scaleFactor"],parent='+self.rootObj+')\n'
                astr+='    #sel=mol.findType(Atom)\n'
                astr+='    ob=util.instancesAtomsSphere(name,mol.allAtoms,mesh,sc,scale=options["scaleFactor"],Res=options["quality"],R=options["cpkRad"],join='+str(self.joins)+',geom=g)\n'                
                astr+='    util.addObjToGeom([ob,mesh],g)\n'
                if self.soft=='blender' : astr+='    util.addObjectToScene(sc,ob,parent='+self.rootObj+')\n'
                """
                astr+='    for o in ob:\n'
                astr+='        parent='+self.rootObj+'\n'
                #if self.soft=='c4d' : 
                astr+='        hierarchy=util.parseObjectName(o)\n'
                astr+='        if hierarchy != "" :\n'
                astr+='             #parent = util.getObject('+self.chObj+'[hierarchy[1]+"_cpk"])\n'
                if self.useTree == 'perRes' :
                    astr+='             parent = util.getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])\n'
                elif self.useTree == 'perAtom' :
                    astr+='             parent = util.getObject(o.get_name().split("_")[1])\n'
                else :
                    astr+='             parent = util.getObject('+self.chObj+'[hierarchy[1]+"_cpk"])\n'                
                astr+='        #print "PARENTING ",o,parent\n'
                astr+='        util.addObjectToScene(sc,o,parent=parent)\n'
                astr+='        util.toggleDisplay(o,False)\n' #True per default
                """
                astr+='    #sel=select.findType(Atom)\n'            
                #need display the selection use here the only option
                astr+='elif hasattr(g,"obj")  and display : \n'
                astr+='    #util.updateSphereMesh(g,quality=options["quality"],cpkRad=options["cpkRad"],scale=options["scaleFactor"])\n' 
                astr+='    util.updateSphereObj(g)\n'#if needRedo : 
                astr+='if hasattr(g,"obj"):\n'
                astr+='    atoms=sel#findType(Atom) already done\n'
                astr+='    for atms in atoms:\n'
                astr+='        nameo = "S"+"_"+atms.full_name()\n'
                astr+='        #print nameo\n'
                astr+='        o=util.getObject(nameo)\n'#Blender.Object.Get (nameo)\n'
                astr+='        if o != None :util.toggleDisplay(o,display)\n'        
            elif gType=='SticksAndBalls' :
                if self.useEvent : return astr
                for a in arg :
                    if a.split('=')[0].replace(' ','') == 'sticksBallsLicorice' : option = a.split('=')[1].replace(')','')
                    elif a.split('=')[0].replace(' ','') == 'bRad' :    bradius = a.split('=')[1].replace(')','')    
                    elif a.split('=')[0].replace(' ','') == 'cradius' : cradius = a.split('=')[1].replace(')','')    
                if option =='Licorice' or option =="'Licorice'" or option =='"Licorice"' : bradius=cradius
                #astr+='print self.displaySticksAndBalls.getArguments()\n'
                astr+='options=self.displaySticksAndBalls.lastUsedValues["default"]\n'
                astr+='needRedo=False\n'
                astr+='if options.has_key("redraw"):\n'
                astr+='    needRedo=True\n'
                astr+='gb = mol.geomContainer.geoms['+self.gDict[gType][0]+']\n'
                astr+='gs = mol.geomContainer.geoms['+self.gDict[gType][1]+']\n'
                astr+='select=self.select('+selection+',negate=False, only=True, xor=False, log=0, intersect=False)\n'
                astr+='sel=select.findType(Atom)\n'
                astr+='name='+mol+'+"_balls&sticks"\n'
                astr+='if not hasattr(gb,"obj") and  not hasattr(gs,"obj") :\n'
                #astr+='    gbsg=util.newEmpty(name)\n'
                #astr+='    util.addObjectToScene(sc,gbsg,parent=mol.geomContainer.masterGeom.obj)\n'
                astr+='    options = self.displaySticksAndBalls.lastUsedValues[\'default\']\n'
                astr+='    mol.allAtoms.ballRad = options[\'bRad\']\n'
                astr+='    mol.allAtoms.ballScale = options[\'bScale\']\n'
                astr+='    mol.allAtoms.cRad = options[\'cradius\']\n'
                astr+='    for atm in mol.allAtoms:\n'
                astr+='        atm.colors[\'sticks\'] = (1.0, 1.0, 1.0)\n'
                astr+='        atm.opacities[\'sticks\'] = 1.0\n'
                astr+='        atm.colors[\'balls\'] = (1.0, 1.0, 1.0)\n'
                astr+='        atm.opacities[\'balls\'] = 1.0\n'                
                if option !='Sticks only' or option !="'Sticks only'" or option !='"Sticks only"':
                    astr+='if not hasattr(gb,"obj") and display:\n'
                    astr+='    #name='+mol+'+"_"+'+self.gDict[gType][0]+'\n'
                    #astr+='    gbsg=util.getObject(name)\n'
                    astr+='    mesh=util.createBaseSphere(name="base_balls",quality=options["bquality"],cpkRad=options["bRad"],scale=options[\'bScale\'],radius=options[\'bRad\'],parent='+self.rootObj+')\n'
                    astr+='    #sel=mol.findType(Atom)\n'
                    astr+='    ob=util.instancesAtomsSphere(name,mol.allAtoms,mesh,sc,scale=options[\'bScale\'],R=options["bRad"],join='+str(self.joins)+',geom=gb)\n'
                    astr+='    util.addObjToGeom([ob,mesh],gb)\n'
                    astr+='    for o in ob:\n'
                    astr+='        parent='+self.rootObj+'\n'                    
                    astr+='        hierarchy=util.parseObjectName(o)\n'
                    astr+='        if hierarchy != "" :\n'
                    if self.useTree == 'perRes' :
                        astr+='             parent = util.getObject(mol.geomContainer.masterGeom.res_obj[hierarchy[2]])\n'
                    elif self.useTree == 'perAtom' :
                        astr+='             parent = util.getObject(o.get_name().split("_")[1])\n'
                    else :
                        astr+='             parent = util.getObject('+self.chObj+'[hierarchy[1]+"_balls"])\n'
                    astr+='        util.addObjectToScene(sc,o,parent=parent)\n'
                    astr+='        util.toggleDisplay(o,False)\n' #True per default
                    astr+='    #sel=select.findType(Atom)\n'            
                    astr+='elif hasattr(gb,"obj")  and display : \n'
                    astr+='    util.updateSphereMesh(gb,quality=options["bquality"],cpkRad=options["bRad"],scale=options[\'bScale\'],radius=options[\'bRad\'],)\n' 
                    astr+='    if needRedo : util.updateSphereObj(gb)\n'
                astr+='if not hasattr(gs,"obj") and display:\n'
                astr+='    #name='+mol+'+"_"+'+self.gDict[gType][1]+'\n'
                astr+='    #gbsg=util.getObject(name)\n'
                astr+='    set = mol.geomContainer.atoms["sticks"]\n'
                astr+='    cyl=None\n'
                if self.soft=='c4d' : #and self.use_instances :
                    astr+='    cyl=util.newEmpty("baseBond")\n'
                    astr+='    util.addObjectToScene(sc,cyl,parent='+self.rootObj+')\n'                
                    astr+='    cylinder=c4d.BaseObject(5170)\n'
                    astr+='    cylinder[5000]=options[\'cradius\']\n'
                    astr+='    cylinder[5005]= 1.\n' #lenght
                    astr+='    cylinder[5008]=    15\n' #subdivision
                    #astr+='    cylinder.set_render_mode(c4d.MODE_OFF)\n'
                    astr+='    cylinder.make_tag(c4d.Tphong)\n'                                                        
                    astr+='    util.addObjectToScene(sc,cylinder,parent=cyl)\n'
                    astr+='    gs.mesh=cyl\n'                        
                #tube are inserted in scene on the fly
                astr+='    stick=util.Tube(set,sel,gs.getVertices(),gs.getFaces(),sc, None, res=15, size=options[\'cradius\'], sc=1., join=0,instance=cyl,hiera = "'+self.useTree+'")\n'
                astr+='    util.addObjToGeom(stick,gs)\n'
                astr+='    #print "stick number ",len(stick)\n'                
                astr+='    for o in stick[0]:\n'
                #astr+='         util.addObjectToScene(sc,o,parent='+self.rootObj+')\n'
                astr+='         util.toggleDisplay(o,False)\n'                
                astr+='if hasattr(gs,"obj")  and display : \n'
                astr+='    util.updateTubeMesh(gs,cradius=options[\'cradius\'],quality=options["cquality"])\n' 
                astr+='    #util.updateTubeObj(gs)\n'#if needRedo : 
                #need display only the selection
                astr+='if hasattr(gb,"obj"):\n'
                astr+='    select=self.select('+selection+',negate=False, only=True, xor=False, log=0, intersect=False)\n'
                astr+='    sel=select.findType(Atom)\n'                
                astr+='    atoms=sel\n'
                astr+='    for atms in atoms:\n'
                astr+='        nameo = "B"+"_"+atms.full_name()\n'
                astr+='        #print nameo,display\n'
                astr+='        o=util.getObject(nameo)\n'
                astr+='        #print o\n'                
                astr+='        if o != None :\n'
                if option =='Sticks only' or option =="'Sticks only'" or option =='"Sticks only"': 
                    astr+='            display = False\n'
                else :  astr+='            display = display\n'
                astr+='            util.toggleDisplay(o,display=display)\n'
                astr+='if hasattr(gs,"obj"):\n'
                astr+='    atoms=sel\n'                
                astr+='    set = mol.geomContainer.atoms["sticks"]\n'
                astr+='    bonds, atnobnd = set.bonds\n'
                astr+='    #if len(set)==0 : \n'
                astr+='    for o in gs.obj:util.toggleDisplay(o,display=False)\n'
                astr+='    if len(set) > 0 :\n'
                astr+='      for bds in bonds:\n'
                astr+='        atm1=bds.atom1\n'
                astr+='        atm2=bds.atom2\n'
                #this is for the bylcylinder...need to make this an option..                
                astr+='        #if atm1 in atoms or atm2 in atoms :\n'                 
                astr+='        #namet="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)\n'
                astr+='        namet="T_"+atm1.full_name()+"_"+atm2.name\n' 
                astr+='        namet2="T_"+atm2.full_name()+"_"+atm1.name\n'
                astr+='        #print  namet\n'                    
                astr+='        o=util.getObject(namet)\n'
                astr+='        if o != None :\n'
                astr+='            util.updateTubeObj(o,atm1.coords,atm2.coords)\n'
                astr+='            util.toggleDisplay(o,display=True)\n'                
                astr+='        o=util.getObject(namet2)\n'
                astr+='        if o != None :\n'
                astr+='            #util.updateTubeObj(o,atm1.coords,atm2.coords)\n'
                astr+='            util.toggleDisplay(o,display=True)\n'
                if self.soft=='maya' : astr+='        util.updateTubeMesh(atm1,atm2,bicyl=True,cradius=options[\'cradius\'],quality=options["cquality"])\n'                
                else : astr+='        if needRedo : util.updateTubeObj(atm1,atm2,bicyl=True)\n'
            elif gType=='Lines' :
                pass            
            else :
                if self.useEvent : return astr
                if self.gDict[gType][0].find('MSMS') : 
                    for a in arg :
                        print a,a.split('=')[0].replace(' ',''),a.split('=')[0].replace(' ','') == 'surfName'                   
                        if a.split('=')[0].replace(' ','') == 'surfName' : 
                            print a.split('=')[1].replace(')','')
                            lgname = a.split('=')[1].replace(')','')
                            if lgname.find("[") != -1 :
                                message=message.replace(' ','')
                                indS=message.find('surfName=[')
                                end=message[indS+10:].find(']')
                                liste=message[indS+10:][:end]
                                lgname=liste.split(",")
                            break                            
                        else : lgname=self.gDict[gType][0]
                    if type(lgname) == str : lgname=[lgname]
                    if len(lgname) > 1 : lgname=[lgname]
                    print lgname
                    for gname in lgname:
                        print gname
                        if gname == "'all'" or gname == 'all' or gname == '"all"': gname=self.gDict[gType][0]                                    
                        #astr+='print '+gname+'\n'
                        astr+='gname='+gname+'\n'
                        if gname == "'all'" or gname == 'all' or gname == '"all"':
                        #undisplay the current msms display    
                            astr+='surfs=mol.geomContainer.msmsCurrentDisplay.keys()\n'
                            astr+='gname=surfs[0]\n'
                        astr+='g = mol.geomContainer.geoms[gname]\n'
                        astr+='if not hasattr(g,"obj") and display:\n'
                        astr+='        name=gname\n'
                        astr+=self.createMeshCommands('name',space="        ",proxy=True)
                        astr+='if hasattr(g,"obj"):util.toggleDisplay(g.obj,display=display)\n'
        elif func[0:5] == "color":
            if self.useEvent : return astr
            geoms=[]
            if func == "color":
                geoms=[]
                #print "color"
                #print message  
                indc=message.find(']')
                cp=message[indc+1:]
                indg =cp.find('[') #geom array begin
                indge=cp.find(']') #geom array end
                lGeom=cp[indg:indge+1]
                #print lGeom
                sys.stderr.write("parsed g arg %s\n" % lGeom)
                geoms=eval(lGeom)
            else :
                for i in range(len(arg)) :
                    if (arg[i].replace(' ',''))[0] == '[' : #first geom
                        g=""
                        g=(arg[i].replace(' ',''))
                        while True :
                            g=arg[i].replace(' ','')
                            g=g.replace('[','')
                            g=g.replace(']','')
                            geoms.append(eval(g))
                            if (arg[i].replace(' ',''))[-1] == ']' or i == len(arg) : break
                            i=i+1
            #print "parsed geoms ",geoms
            for g in geoms : 
                print 'geoms ',g
                if g=='"secondarystructure"' or g=='secondarystructure' or g=="'secondarystructure'" :
                    astr+='gss = mol.geomContainer.geoms["secondarystructure"]\n'
                    astr+='for name,g in mol.geomContainer.geoms.items() :\n'
                    astr+=' if name[:4] in [\'Heli\', \'Shee\', \'Coil\', \'Turn\', \'Stra\']:\n'        
                    astr+='        SS= g.SS\n'
                    astr+='        name=\'%s%s\'%(SS.name, SS.chain.id)\n'
                    astr+='        colors=mol.geomContainer.getGeomColor(name)\n'
                    astr+='        flag=mol.geomContainer.geoms[name].vertexArrayFlag\n'
                    astr+='        if hasattr(g,"obj"):\n'
                    astr+='            util.changeColor(g,colors,perVertex=flag)\n'        
                elif g=='"cpk"'or g=='cpk' or g=="'cpk'" or g=='"balls"'or g=='balls' or g=="'balls'": 
                    #have instance materials...so if colorbyResidue have to switch to residueMaterial
                    astr+='#print "function '+func[5:11]+'"\n'
                    astr+=self.getSelectionCommand(selection)
                    astr+='g = mol.geomContainer.geoms["'+g+'"]\n'
                    astr+='colors=mol.geomContainer.getGeomColor("'+g+'")\n'
                    astr+='prefix="S"\n'
                    astr+='name="cpk"\n'
                    astr+='if g.name == "balls" : \n'
                    astr+='    prefix="B"\n'
                    astr+='    name="balls&sticks"\n'
                    astr+='if hasattr(g,"obj"):\n'
                    astr+='        if isinstance(sel,Atom):\n'
                    astr+='            atoms = sel\n'
                    astr+='        else :\n'                                                                                
                    astr+='            atoms=sel.findType(Atom)\n'#mol.allAtoms#
                    astr+='        for atm in atoms:\n'
                    astr+='            nameo = prefix+"_"+atm.full_name()\n'
                    astr+='            o=util.getObject(nameo)\n'#Blender.Object.Get (nameo)\n'
                    astr+='            vcolors = [atm.colors["'+g+'"],] #(0,0,0)\n'
                    astr+='            #print vcolors\n'
                    astr+='            if len(atoms) == len(mol.allAtoms) :\n'
                    astr+='                util.checkChangeMaterial(o,"'+func[5:11]+'",atom=atm,parent=mol.name+"_"+name,color=vcolors[0])\n'
                    astr+='            else : util.checkChangeMaterial(o,"'+func[5:11]+'",atom=atm,parent=parentString,color=vcolors[0])\n'
                    astr+='            #changeColor(g.mesh[atoms[k].name[0]],vcolors,perObjectmat=o)\n'
                    astr+='            #changeColor(g.mesh[atoms[k].name[0]],vcolors,perObjectmat=o)\n'
                    astr+='            #k=k+1\n'
                    astr+='            #o.makeDisplayList()\n'
                elif g=='"sticks"'or g=='sticks' or g=="'sticks'" : 
                    astr+='g = mol.geomContainer.geoms["'+g+'"]\n'
                    astr+='colors=mol.geomContainer.getGeomColor("'+g+'")\n'
                    astr+=self.getSelectionCommand(selection)
                    astr+='if hasattr(g,"obj"):\n'
                    astr+='  atoms=sel\n'                    
                    astr+='  set = mol.geomContainer.atoms["sticks"]\n'
                    astr+='  if len(set) == len(mol.allAtoms) : p = mol.name+"_"+name\n' 
                    astr+='  else : p = parentString\n'
                    astr+='  bonds, atnobnd = set.bonds\n'
                    astr+='  if len(set)!=0 : \n'
                    astr+='    for bds in bonds:\n'
                    astr+='        atm1=bds.atom1\n'
                    astr+='        atm2=bds.atom2\n'
                    astr+='        if atm1 in atoms or atm2 in atoms :\n' 
                    astr+='            vcolors=[atm1.colors["sticks"],atm2.colors["sticks"]]\n'
                    if not self.bicyl :
                        astr+='            name="T_"+atm1.name+str(atm1.number)+"_"+atm2.name+str(atm2.number)\n'
                        astr+='            o=util.getObject(name)\n'
                        astr+='            if o != None : \n'
                        if self.soft=="c4d" : astr+='                util.checkChangeStickMaterial(o,"'+func[5:11]+'",atoms=[atm1,atm2],parent=parentString,color=vcolors[0])\n'
                        astr+='                util.changeSticksColor(o,vcolors,type="'+func[5:11]+'",bicyl=False)\n'
                    else :
                        astr+='            c0=numpy.array(atm1.coords)\n'
                        astr+='            c1=numpy.array(atm2.coords)\n'
                        astr+='            vect = c1 - c0\n'
                        astr+='            n1=atm1.full_name().split(":")\n'
                        astr+='            n2=atm2.full_name().split(":")\n'
                        astr+='            name1="T_"+n1[1]+"_"+n1[2]+"_"+n1[3]+"_"+atm2.name\n'
                        astr+='            name2="T_"+n2[1]+"_"+n2[2]+"_"+n2[3]+"_"+atm1.name\n'
                        astr+='            o=util.getObject(name1)\n'
                        astr+='            if o != None : \n'
                        astr+='                util.checkChangeMaterial(o,"'+func[5:11]+'",atom=atm1,parent=p,color=vcolors[0])\n'
                        astr+='            o=util.getObject(name2)\n'
                        astr+='            if o != None : \n'
                        astr+='                util.checkChangeMaterial(o,"'+func[5:11]+'",atom=atm2,parent=p,color=vcolors[1])\n'
                else :
                    astr+='g = mol.geomContainer.geoms["'+g+'"]\n'
                    #astr+='print g.name,'+g+',hasattr(g,"mesh")\n'                 
                    astr+='colors=mol.geomContainer.getGeomColor("'+g+'")\n'
                    astr+='flag=g.vertexArrayFlag\n'
                    astr+='if hasattr(g,"obj"):\n'
                    if self.soft=="c4d" : astr+='        util.changeColor(g,colors,perVertex=flag,proxyObject=g.color_obj)\n'
                    else : astr+='        util.changeColor(g,colors,perVertex=flag)\n'
        #astr+="util.update()\n"
        return astr

    def prepareToSend(self,message):
        astr='#cF\n#s%d\n' % len(message)
        astr=astr + message + '\n\0'
        return astr

    def stateObject(self,mol,geom,state):
        rid=[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        astr=self.init()
        #astr+='mol=self.getMolFromName("'+mol+'")\n'    
        astr+='geoms = mol.geomContainer.geoms\n'
        if geom == 'master' : #all geometry affect
            #in all the state keys, only several interested us
            astr+='for k in geoms.keys() :\n'
            astr+='    g=geoms[k]\n'
            astr+='    if hasattr(g,"mesh") and hasattr(g,"obj"):\n'
            #pivot?,scale,translation,rotation is the mesh transformation
            if sum(state['translation']) > 0.0 or (state['rotation']) != rid or (state['scale']) != [1.0,1.0,1.0]:
                astr+='       #transform mesh\n'
                sys.stderr.write('################BEFORE COMPOSE\n\n\n\n')
                astr+='       if not hasattr(g,"orimesh") : g.orimesh=g.mesh.__copy__()\n'
                astr+='       mat=Compose4x4(obj.rotation,obj.translation,obj.scale)\n'
                astr+='       #blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])\n'
                astr+='    #get vert original position and then apply the trans\n'
                astr+='       #g.mesh.verts= g.orimesh.verts\n'
                astr+='       #g.mesh.transform(blender_mat,recalc_normals=True)\n'
            #instanceMatricesFromFortran is object transformation
            if len(state['instanceMatricesFromFortran']) > 1 :
                astr+='       #create instance\n'
                astr+='       #verfify if its already done...\n'
                astr+='       done=True\n'
                """astr+='       if hasattr(g.obj,"drawMode") or  :\n'
                astr+='           sc.unlink(g.obj)\n'
                astr+='           g.obj=[]\n'
                astr+='           done=False\n'
                astr+='       elif len(g.obj) != len(obj.instanceMatricesFortran):\n'
                astr+='           for bobj in g.obj : sc.unlink(bobj)\n'
                astr+='           g.obj=[]\n'
                astr+='           done=False\n'
                astr+='       if not done :\n'
                astr+='        for i in range(len(obj.instanceMatricesFortran)):\n'
                astr+='            m=obj.instanceMatricesFortran[i].reshape(4,4)\n'
                astr+='            m=m.transpose()\n'
                astr+='            mat=m.tolist()\n'
                astr+='            blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])\n'
                astr+='            blendObj = Blender.Object.New("Mesh",g.name+"_"+str(i))\n'
                astr+='            blendObj.link(g.mesh)\n'
                astr+='            blendObj.setMatrix(blender_mat)\n'
                astr+='            g.obj.append(blendObj)\n'
                astr+='            sc.link(blendObj)\n'
                astr+='       else :\n'
                astr+='        for i in range(len(obj.instanceMatricesFortran)):\n'
                astr+='            m=obj.instanceMatricesFortran[i].reshape(4,4)\n'
                astr+='            m=m.transpose()\n'
                astr+='            mat=m.tolist()\n'
                astr+='            blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])\n'
                astr+='            g.obj[i].setMatrix(blender_mat)\n'    """        
            astr+='       pass\n'
        else :               #the specified geom is affected    
            #pivot,scale,translation,rotation is the mesh transformation    
            if sum(state['translation']) > 0.0 or (state['rotation']) != rid or (state['scale']) != [1.0,1.0,1.0]:
                astr+='if obj:\n'
                astr+='   if hasattr(obj,"mesh") and hasattr(obj,"obj"):\n'
                astr+='       #transform mesh\n'
                sys.stderr.write('################BEFORE COMPOSE\n\n\n\n')
                astr+='       if not hasattr(obj,"orimesh") : obj.orimesh=g.mesh.__copy__()\n'
                astr+='       mat=Compose4x4(obj.rotation,obj.translation,obj.scale)\n'
                astr+='       blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])\n'
                astr+='    #get vert original position and then apply the trans\n'
                astr+='       #obj.mesh.verts= obj.orimesh.verts\n'
                astr+='       #obj.mesh.transform(blender_mat,recalc_normals=True)\n'
            #instance
            if len(state['instanceMatricesFromFortran']) > 1 :
                astr+='if obj:\n'
                """astr+='   if hasattr(obj,"mesh") and hasattr(obj,"obj"):\n'
                astr+='       #create instance\n'
                astr+='       done=True\n'
                astr+='       if hasattr(g.obj,"drawMode") or  :\n'
                astr+='           sc.unlink(obj.obj)\n'
                astr+='           obj.obj=[]\n'
                astr+='           done=False\n'
                astr+='       elif len(obj.obj) != len(obj.instanceMatricesFortran):\n'
                astr+='           for bobj in obj.obj : sc.unlink(bobj)\n'
                astr+='           obj.obj=[]\n'
                astr+='           done=False\n'
                astr+='       if not done :\n'
                astr+='        for i in range(len(obj.instanceMatricesFortran)):\n'
                astr+='            m=obj.instanceMatricesFortran[i].reshape(4,4)\n'
                astr+='            m=m.transpose()\n'
                astr+='            mat=m.tolist()\n'
                astr+='            blender_mat=Matrix(mat[0],mat[1],mat[2],mat[3])\n'
                astr+='            blendObj = Blender.Object.New("Mesh",g.name+"_"+str(i))\n'
                astr+='            blendObj.link(obj.mesh)\n'
                astr+='            blendObj.setMatrix(blender_mat)\n'
                astr+='            obj.obj.append(blendObj)\n'
                astr+='            sc.objects.link(blendObj)\n'    """
        return astr

    def solveFindObject(self,string):
        #obj = self.GUI.VIEWER.FindObjectByName('root|1crn|AtomLabels')    
        arg=string.split("(")[1] #'root|1crn')
        name=arg[:-1].split("root|")[1]
        mol=name.split("|")[0]
        if mol == 'misc' : return "obj=None\n"
        else :
            sys.stderr.write("NAME %s\n" %(name))
            if len(name.split("|")) > 1: geom=name.split("|")[1]
            else :     
                mol=mol.replace("'","")
                geom='master'
            geom=geom.replace("'","")
            newCom='if "'+mol+'" in self.Mols.name : \n'
            newCom+='    mol=self.getMolFromName("'+mol+'")\n'
            newCom+='    if "'+geom+'" in mol.geomContainer.geoms.keys():\n'
            newCom+='     obj = mol.geomContainer.geoms["'+geom+'"]\n'
            newCom+='    else : obj=None\n'
            newCom+='else :\n'
            newCom+='    for mols in self.Mols:\n'
            newCom+='      if "'+geom+'" in mols.geomContainer.geoms.keys():\n'
            newCom+='          obj = mols.geomContainer.geoms["'+geom+'"]\n'
            newCom+='          break\n'
            newCom+='      else : obj=None\n'
            return newCom
          #else :
          #    return "obj=None\n"
        
    def parsePmvStates(self,states):
        #print "parsePmvStates"    
        sys.stderr.write("parse\n")
        sys.stderr.flush()        
        res=""""""
        i=0
        mol=""
        geom=""        
        array=states.split("\n")
        sys.stderr.write("nblines %d\n#######ARRAY############\n"%len(array))
        sys.stderr.write("%s"%states)
        while i < len(array) :
            lines=array[i]
            sys.stderr.write("line %d:\n%s\n"%(i,lines))
            if len(lines) > 0:
                #neeed to get the state for the masterGeom ie |root|1crn for instance..
                #first remove all gui viewer command
                #we need to think how handle the self.GUI.VIEWER.FindObjectByName command
                #obj = self.GUI.VIEWER.FindObjectByName('root|1crn|AtomLabels')    
                if lines.find("GUI") != (-1) :
                    sys.stderr.write('ok GUI command\n')
                    if lines.find("FindObjectByName") != (-1) :
                        sys.stderr.write('#FindObjectByName\n')
                        sys.stderr.write('%s\n'%self.solveFindObject(lines))
                        res+=self.solveFindObject(lines)
                    elif lines == 'if self.GUI.VIEWER.rootObject:' :
                        if array[i+1].find('pass') != (-1) : i=i+1
                        if array[i+3].find('pass') != (-1) : i=i+3
                        res+=""
                    else : res+=""
                elif lines.find("vision") != (-1) : res+=""
                else : 
                     if lines.find('coarseMolSurface') != (-1) or lines.find('deleteMol') != (-1): 
                        #print lines
                        func,arg=self.parseMessageToFunc(lines)
                        #print func
                        res+=self.createMessageCommand(func,arg,lines)    
                     elif lines[0:9] == '## Object' : 
                        #'## Object root|misc|setTorsionGeom|settorsionLine'
                        find=True
                        sys.stderr.write("ok OBJECT\n")
                        odescr=lines.split(" ")[2]
                        descr=odescr.split("root|")[1]
                        objs=descr.split('|')
                        if objs[0] == 'misc' : res+=lines+'\n'
                        else : 
                            mol=objs[0]
                            if len(objs) > 1 : geom=objs[1]
                            else : geom='master'
                            sys.stderr.write("%s %s\n" %(mol,geom))
                            res+=lines+'\n'
                            while lines[0:5] != 'state' and i < len(array): 
                                i=i+1
                                lines=array[i]
                                sys.stderr.write("line %d:\n%s\n"%(i,lines))
                                if lines[0:9] == '## Object' : 
                                        find=False
                                        break
                            if find == True :
                                state=eval(lines.split("=")[1])    
                                res+=lines+'\n'
                            while lines.find("FindObjectByName") == (-1) and i < len(array) :
                                i=i+1
                                lines=array[i]
                                sys.stderr.write("line %d:\n%s\n"%(i,lines))
                            res+=self.solveFindObject(lines)
                            while lines[0:7] != 'if obj:' and i < len(array) :
                                i=i+1
                                lines=array[i]
                                sys.stderr.write("line %d:\n%s\n"%(i,lines))
                            res+=lines+'\n'
                            while lines.find("apply(") == (-1) and i < len(array) :
                                i=i+1
                                lines=array[i]
                                sys.stderr.write("line %d:\n%s\n"%(i,lines))
                            res+=lines+'\n'
                            res+=self.stateObject(mol,geom,state)
                     else : res+=lines+'\n'
                i=i+1
        sys.stderr.write('%s\n'%res)
        return res

    def piecewiseLinearInterpOnIsovalue(self, x):
            """Piecewise linear interpretation on isovalue that is a function
            blobbyness.
            """
            X = [-3.0, -2.5, -2.0, -1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]
            Y = [0.6565, 0.8000, 1.0018, 1.3345, 1.5703, 1.8554, 2.2705, 2.9382, 4.1485, 7.1852, 26.5335]
            if x<X[0] or x>X[-1]:
                print "WARNING: Fast approximation :blobbyness is out of range [-3.0, -0.1]"
                return None
            i = 0
            while x > X[i]:
                i +=1
            x1 = X[i-1]
            x2 = X[i]
            dx = x2-x1
            y1 = Y[i-1]
            y2 = Y[i]
            dy = y2-y1
            return y1 + ((x-x1)/dx)*dy

            
