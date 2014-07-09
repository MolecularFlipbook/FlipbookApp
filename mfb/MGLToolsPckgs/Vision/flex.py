## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Nov. 2001  Author: Michel Sanner
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################

from NetworkEditor.items import NetworkNode
import numpy.oldnumeric as Numeric


class DistanceMatrix(NetworkNode):

    def __init__(self, name='DM', **kw):
        kw['name'] = name
	apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, in1):
	import numpy.oldnumeric as Numeric
	l = len(in1)
	dm = Numeric.zeros( (l,l), 'd')
	in1 = Numeric.array(in1).astype('d')
	for i in range(l):
	    dist = in1[i] - in1
	    dist = dist*dist
	    dm[i] = Numeric.sqrt(Numeric.sum(dist, 1))
	self.outputData(out1=dm)\n"""

	if code: self.setFunction(code)
	
	self.inputPortsDescr.append({'name': 'in1', 'datatype': 'None'})
	self.outputPortsDescr.append({'name': 'out1', 'datatype': 'None'})


class DDM(NetworkNode):

    def __init__(self, name='DDM', **kw):
        kw['name'] = name
	apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, in1, in2):
	import numpy.oldnumeric as Numeric
	result = in1-in2
        self.outputData(out1=result)\n"""
		
	if code: self.setFunction(code)
	
	self.inputPortsDescr.append({'name': 'in1', 'datatype': 'None'})
	self.inputPortsDescr.append({'name':'in2', 'datatype': 'None'})
	self.outputPortsDescr.append({'name':'out1', 'datatype': 'None'})
		


class Cluster(NetworkNode):

    def __init__(self, name='cluster', **kw):
        kw['name'] = name
	apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, in1, cut_off):
    import math
    mat = in1
    clusters = [[0],] # 1 cluster with first point
    l = mat.shape[0]
    for i1 in range(1, l):
        for c in clusters: # loop over excisting clusters
            inclus = 1
            for p in c:  # check distance to all points in cluster
                if math.fabs(mat[i1,p]) > cut_off:
                    inclus=0
                    break
            if inclus:   # all dist. below cut_off --> add to cluster
                c.append(i1)
                inclus = 1
                break
        if not inclus: # after trying all clusters we failed -> new cluster
            clusters.append([i1])
    # make it 1 based so indices match PMV residue indices
    #clusters1 = []
    #for e in clusters:
    #    clusters1.append( list ( Numeric.array(e) + 1 ) )
    self.outputData(out1=clusters)\n"""
		    
	if code: self.setFunction(code)

	self.widgetDescr['cut_off'] = {
	    'class': 'NEDial', 'master': 'node',  'size': 50,
	    'oneTurn': 4.0, 'type': float, 'showLabel': 1, 'precision': 2,
	    'labelCfg':{'text':'cut_off'}, 'labelSide':'left'}

	self.inputPortsDescr.append({'name':'in1', 'datatype':'None'})
	self.inputPortsDescr.append({'datatype':'None', 'name':'cut_off'})
	self.outputPortsDescr.append({'name':'out1', 'datatype': 'None'})


class ColorCluster(NetworkNode):

    def __init__(self, name='color cluster', **kw):
        kw['name'] = name
	apply( NetworkNode.__init__, (self,), kw)
	    
	code = """def doit(self, in1):
    from DejaVu.colorTool import RGBRamp, Map
    cols = Map(range(len(in1)), RGBRamp() )
    l = len(reduce(lambda x,y: x+y, in1))
    c = Numeric.zeros( (l,3), 'f' )
    i=0
    for e in in1:
	col = cols[i]
	for p in e:
	    c[p] = col
	i = i + 1
    self.outputData(out1=c)\n"""

	if code: self.setFunction(code)
	
	self.inputPortsDescr.append({'name':'in1', 'datatype': 'None'})
	self.outputPortsDescr.append({'name':'out1', 'datatype': 'None'})
	

class DefaultIndices(NetworkNode):

    def __init__(self, name='default indices', **kw):
        apply( NetworkNode.__init__, (self,), kw)
	
	code = """def doit(self, in1):
    self.outputData(out1=[range(in1[0])])\n"""
	if code: self.setFunction(code)
	
	self.inputPortsDescr.append({'name':'length', 'datatype':'int'})
	self.outputPortsDescr.append({'name':'out1', 'datatype':'None'})


from Vision.VPE import NodeLibrary

flexlib = NodeLibrary('Flex', '#AA66AA')
flexlib.addNode(DistanceMatrix, 'DM', 'Input')
flexlib.addNode(DDM, 'DDM', 'Input')
flexlib.addNode(Cluster, 'Cluster', 'Input')
flexlib.addNode(ColorCluster, 'Color Cluster', 'Input')
flexlib.addNode(DefaultIndices, 'indices', 'Input')

