#############################################################################
#
# Author: Ludovic Autin
#
# Copyright: Ludovic Autin TSRI 2010
#
#
#############################################################################

from Pmv.hostappInterface.epmvAdaptor import epmvAdaptor
from Pmv.hostappInterface.blender import blenderHelper
#import Pmv.hostappInterface.pdb_blender as blenderHelper
import Blender

class blenderAdaptor(epmvAdaptor):
    
    def __init__(self,mv=None,debug=0):
        epmvAdaptor.__init__(self,mv,host='blender',debug=debug)
        self.soft = 'blender'
        self.helper = blenderHelper
        #scene and object helper function
        self._getCurrentScene = blenderHelper.getCurrentScene
        self._addObjToGeom = blenderHelper.addObjToGeom
        self._host_update = blenderHelper.update
        self._parseObjectName = blenderHelper.parseObjectName
        self._getObjectName = blenderHelper.getObjectName
        self._getObject = blenderHelper.getObject
        self._addObjectToScene = blenderHelper.addObjectToScene
        self._toggleDisplay = blenderHelper.toggleDisplay
        self._newEmpty = blenderHelper.newEmpty
        self._deleteObject = blenderHelper.deleteObject 
        #camera and lighting
        self._addCameraToScene = blenderHelper.addCameraToScene
        self._addLampToScene = blenderHelper.addLampToScene
        #display helper function
        self._editLines = blenderHelper.editLines
        self._createBaseSphere = blenderHelper.createBaseSphere
        self._instancesAtomsSphere = blenderHelper.instancesAtomsSphere
        self._Tube = blenderHelper.Tube
        self._createsNmesh = blenderHelper.createsNmesh
        self._PointCloudObject = blenderHelper.PointCloudObject
        #modify/update geom helper function
        self._updateSphereMesh = blenderHelper.updateSphereMesh
        self._updateSphereObj = blenderHelper.updateSphereObj
        self._updateSphereObjs = blenderHelper.updateSphereObjs
        self._updateTubeMesh = blenderHelper.updateTubeMesh
        self._updateTubeObj = blenderHelper.updateTubeObj
        self._updateMesh = blenderHelper.updateMesh
        #color helper function
        self._changeColor = blenderHelper.changeColor
        self._checkChangeMaterial = blenderHelper.checkChangeMaterial
        self._changeSticksColor = blenderHelper.changeSticksColor
        self._checkChangeStickMaterial = blenderHelper.checkChangeStickMaterial
        #define the general function
        self._progressBar = Blender.Window.DrawProgressBar
                
    def _resetProgressBar(self,max):
        pass

    def _makeRibbon(self,name,coords,shape=None,spline=None,parent=None):
        sc=self._getCurrentScene()
        if shape is None :
            shape = sc.objects.new(self.helper.bezCircle(0.3,name+"Circle"))
        if spline is None :
            obSpline,spline = self.helper.spline(name,coords,extrude_obj=shape,scene=sc)
        if parent is not None :
            parent.makeParent([obSpline])
        return obSpline
        
        