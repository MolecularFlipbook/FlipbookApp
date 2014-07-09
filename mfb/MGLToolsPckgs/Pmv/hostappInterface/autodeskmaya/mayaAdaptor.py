#############################################################################
#
# Author: Ludovic Autin
#
# Copyright: Ludovic Autin TSRI 2010
#
#
#############################################################################

from Pmv.hostappInterface.epmvAdaptor import epmvAdaptor
import Pmv.hostappInterface.autodeskmaya.helperMaya as mayaHelper
import maya

class mayaAdaptor(epmvAdaptor):
    
    def __init__(self,mv=None,debug=0):
        epmvAdaptor.__init__(self,mv,host='maya',debug=debug)
        self.soft = 'maya'
        self.helper = mayaHelper
        #scene and object helper function
        self._getCurrentScene = mayaHelper.getCurrentScene
        self._addObjToGeom = mayaHelper.addObjToGeom
        self._host_update = mayaHelper.update
        self._getObjectName = mayaHelper.getObjectName
        self._parseObjectName = mayaHelper.parseObjectName
        self._getObject = mayaHelper.getObject
        self._addObjectToScene = mayaHelper.addObjectToScene
        self._toggleDisplay = mayaHelper.toggleDisplay
        self._newEmpty = mayaHelper.newEmpty 
        self._deleteObject = mayaHelper.deleteObject
        #camera and lighting
        self._addCameraToScene = mayaHelper.addCameraToScene
        self._addLampToScene = mayaHelper.addLampToScene        
        #display helper function
        self._editLines = mayaHelper.editLines
        self._createBaseSphere = mayaHelper.createBaseSphere
        self._instancesAtomsSphere = mayaHelper.instancesAtomsSphere
        self._Tube = mayaHelper.Tube
        self._createsNmesh = mayaHelper.createsNmesh
        self._PointCloudObject = mayaHelper.PointCloudObject
        #modify/update geom helper function
        self._updateSphereMesh = mayaHelper.updateSphereMesh
        self._updateSphereObj = mayaHelper.updateSphereObj
        self._updateSphereObjs = None#mayaHelper.updateSphereObjs
        self._updateTubeMesh = mayaHelper.updateTubeMesh
        self._updateTubeObj = mayaHelper.updateOneSctick
        self._updateMesh = mayaHelper.updateMesh
        #color helper function
        self._changeColor = mayaHelper.changeColor
        self._checkChangeMaterial = mayaHelper.checkChangeMaterial
        self._changeSticksColor = mayaHelper.changeSticksColor
        self._checkChangeStickMaterial = mayaHelper.checkChangeStickMaterial
        if not hasattr(maya,'pb') : 
            maya.pb = None    
        #define the general function
        self.use_progressBar = False

    def _resetProgressBar(self,max):
		maya.cmds.progressBar(maya.pb, edit=True, maxValue=max,progress=0)
		
    def _progressBar(self,progress,label):
		#maxValue = 100	
		#did not work	
		#maya.cmds.progressBar(maya.pb, edit=True, progress=progress*100)
		maya.cmds.progressBar(maya.pb, edit=True, step=1)

    def _makeRibbon(self,name,coords,shape=None,spline=None,parent=None):
        sc=self._getCurrentScene()
        if shape is None :
            # create full circle at origin on the x-y plane
            obj,circle = maya.cmds.circle(n="Circle", nr=(1, 0, 0), c=(0, 0, 0),r=0.3 ) 
            #return obj (Circle) and makenurbeCircle but not the CircleShape
            shape = "CircleShape"
        if spline is None :
            obSpline,spline,extruded = self.helper.spline(name,coords,extrude_obj=shape,scene=sc)
        #if parent is not None :
        #    parent.makeParent([obSpline])
        return obSpline,extruded
