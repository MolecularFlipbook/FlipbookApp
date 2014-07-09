#############################################################################
#
# Author: Ludovic Autin
#
# Copyright: Ludovic Autin TSRI 2010
#
#
#############################################################################

from Pmv.hostappInterface.epmvAdaptor import epmvAdaptor
from Pmv.hostappInterface.Chimera import chimeraHelper
#import Pmv.hostappInterface.pdb_blender as None #

class chimeraAdaptor(epmvAdaptor):
    
    def __init__(self,mv=None,debug=0):
        epmvAdaptor.__init__(self,mv,host='chimera',debug=debug)
        self.soft = 'chimera'
        self.helper = chimeraHelper
        #scene and object helper function
        self._getCurrentScene = chimeraHelper.getCurrentScene
        self._addObjToGeom = chimeraHelper.addObjToGeom
        self._host_update =  None#None #.update
        self._parseObjectName =  None#None #.parseObjectName
        self._getObjectName =  None#None #.getObjectName
        self._getObject =  None#None #.getObject
        self._addObjectToScene =  chimeraHelper.addObjectToScene
        self._toggleDisplay =  None#None #.toggleDisplay
        self._newEmpty =  chimeraHelper.newEmpty 
        #camera and lighting
        self._addCameraToScene =  None#None #.addCameraToScene
        self._addLampToScene =  None#None #.addLampToScene
        #display helper function
        self._editLines =  None#None #.editLines
        self._createBaseSphere =  None#None #.createBaseSphere
        self._instancesAtomsSphere = None #.instancesAtomsSphere
        self._Tube = None #.Tube
        self._createsNmesh = chimeraHelper.createsNmesh
        self._PointCloudObject = None #.PointCloudObject
        #modify/update geom helper function
        self._updateSphereMesh = None #.updateSphereMesh
        self._updateSphereObj = None #.updateSphereObj
        self._updateSphereObjs = None #.updateSphereObjs
        self._updateTubeMesh = None #.updateTubeMesh
        self._updateTubeObj = None #.updateTubeObj
        self._updateMesh = chimeraHelper.updateMesh
        #color helper function
        self._changeColor = None #.changeColor
        self._checkChangeMaterial = None #.checkChangeMaterial
        self._changeSticksColor = None #.changeSticksColor
        self._checkChangeStickMaterial = None #.checkChangeStickMaterial
        #define the general function
        self._progressBar = None#Blender.Window.DrawProgressBar
                
    def _resetProgressBar(self,max):
        pass

    def _makeRibbon(self,name,coords,shape=None,spline=None,parent=None):
        return None
        """sc=self._getCurrentScene()
        if shape is None :
            shape = sc.objects.new(self.helper.bezCircle(0.3,name+"Circle"))
        if spline is None :
            obSpline,spline = self.helper.spline(name,coords,extrude_obj=shape,scene=sc)
        if parent is not None :
            parent.makeParent([obSpline])
        return obSpline"""
        
        