from NetworkEditor.items import NetworkNode


def importMolKitLib(net):
    try:
        from MolKit.VisionInterface.MolKitNodes import molkitlib
        net.editor.addLibraryInstance(
            molkitlib, 'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
    except:
        import traceback
        traceback.print_exc()
        warnings.warn(
            'Warning! Could not import molitlib from MolKit.VisionInterface')



class RotationFile(NetworkNode):
    """This node reads a list of rotations matrices and outputs it as a list of
9-floats"""
    
    def __init__(self, name='Rotation File', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

	# show the entry widget by default
        self.inNodeWidgetVisibleByDefault = True


	fileTypes=[('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'read file', 'width':16,
            'labelCfg':{'text':'file:'},
            }

	self.inputPortsDescr.append(datatype='string', name='filename')

        op = self.outputPortsDescr
        op.append(datatype='float(0,9)', name='rotations')

        code = """def doit(self, filename):
    if filename and len(filename):    
	f = open(filename)
    	data = f.readlines()
    	f.close()

    	rots = []
    	for line in data:
        	rots.append( map(float, line.split()) )
    
    self.outputData(rotations=rots)
"""
        self.setFunction(code)

	
class ReadLog(NetworkNode):
    """Read an F2Dock log file and out put a list of scores, translations,
rotations

Input:
    filename: string, F2Dock out.txt file
    
Output:
    results: list of floats providing [score, tx, ty, tz, rotIndex, fine rot, conf ind, RMSD] for each docking solution
"""
    
    def __init__(self, name='ReadLog', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.inputPortsDescr.append(datatype='string', name='filename')

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node', 'width':16,
            'initialValue':'', 'labelCfg':{'text':'Log File: '}
            }

        self.outputPortsDescr.append(datatype='list', name='results')

        code = """def doit(self,filename):
    f = open(filename)
    data = f.readlines()
    f.close()
    results = []
    for line in data[9:-27]:
        w = line.split()
        results.append( [float(w[0]),float(w[1]),float(w[2]),float(w[3]),
                         int(w[4]),int(w[5]),int(w[6]),float(w[7])] )

    self.outputData(results=results)
"""
        self.setFunction(code)


import numpy


class BrowseLog(NetworkNode):
    """Takes a log file, a rotation file and a lignad molecule and allows to apply docking transformations to the ligand.

Input:
    logfile: list of floats providing [score, tx, ty, tz, rotIndex, fine rot, conf ind, RMSD] for each docking solution
    rotations: 
Output:
    results: list of floats providing [score, tx, ty, tz, rotIndex, fine rot, conf ind, RMSD] for each docking solution
"""
    
    def beforeAddingToNetwork(self, net):
        # import molkitlib
        importMolKitLib(net)


    def __init__(self, name='ReadLog', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.inNodeWidgetsVisibleByDefault = True

        self.mat = numpy.zeros( (4,4), 'f')

        ip = self.inputPortsDescr
        ip.append(datatype='list', name='dockingResults')
        ip.append(datatype='float(0,9)', name='rotations')
        ip.append(datatype='Molecule', name='molecule')
        ip.append(datatype='int', name='solutionNum')
        ip.append(datatype='float(3)', name='initialConf')

        op = self.outputPortsDescr
        op.append(datatype='float', name='score')
        op.append(datatype='float', name='RMSD')

        self.widgetDescr['solutionNum'] = {
            'class':'NEThumbWheel', 'master':'node',
            'width':60, 'height':18, 'oneTurn':10,
            'lockType':1, 'min':1, 'type':'int', 'wheelPad':2,
            'initialValue':0,
            'labelCfg':{'text':'solution number:'},
            }

        code = """def doit(self, dockingResults, rotations, molecule, solutionNum, initialConf):
    solution = dockingResults[solutionNum]
    score, tx, ty, tz, ri, fri, confi, rmsd = solution

    t1 = numpy.identity(4)
    t1[:3,3] = initialConf

    negt1 = numpy.identity(4)
    for i in range(len(initialConf)):
    	negt1[i,3] = initialConf[i] * -1
	
    t2 = numpy.identity(4)
    t2[:3,3] = [tx, ty, tz]

    rot = numpy.identity(4)
    r = numpy.array(rotations[ri])
    r.shape = (3,3)
    rot[0:3,0:3] = r

    self.mat =  numpy.dot(t2, numpy.dot(t1, numpy.dot(rot,negt1)))   
    
    geom = molecule.geomContainer.geoms['master']
    geom.SetTransformation(self.mat, transpose=True)
    self.outputData(score=score, RMSD=rmsd)
"""
        self.setFunction(code)
        
from Vision.VPE import NodeLibrary
F2Docklib = NodeLibrary('F2Dock', '#663366')

F2Docklib.addNode(RotationFile, 'RotFile', 'Rotations')
F2Docklib.addNode(ReadLog, 'ReadLog', 'Input')
F2Docklib.addNode(BrowseLog, 'BrowseLog', 'Mapper')

