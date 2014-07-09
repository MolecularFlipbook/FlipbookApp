# -*- coding: utf-8 -*-
"""
Created on Tue Jul 20 23:03:07 2010

@author: Ludovic Autin
@copyright: Ludovic Autin TSRI 2010
"""

#replace "template" by the name of your software
from Pmv.hostappInterface.epmvAdaptor import epmvAdaptor
import Pmv.hostappInterface.Template.helperTemplate as templateHelper

class templateAdaptor(epmvAdaptor):
    """
    the derived class for embedding pmv in the specific hostApplication "Template"
    define the hostAppli helper function to apply according Pmv event
    """
    
    def __init__(self,mv=None,debug=0):        
        epmvAdaptor.__init__(self,mv,host='template',debug=debug)
        self.soft = 'template'
        self.helper = templateHelper
        #scene and object helper function
        self._getCurrentScene = templateHelper.getCurrentScene
        self._addObjToGeom = templateHelper.addObjToGeom
        self._host_update = templateHelper.update
        self._getObjectName = templateHelper.getObjectName
        self._parseObjectName = templateHelper.parseObjectName
        self._getObject = templateHelper.getObject
        self._addObjectToScene = templateHelper.addObjectToScene
        self._toggleDisplay = templateHelper.toggleDisplay
        self._newEmpty = templateHelper.newEmpty 
        self._deleteObject = templateHelper.deleteObject
        #camera and lighting
        self._addCameraToScene = templateHelper.addCameraToScene
        self._addLampToScene = templateHelper.addLampToScene        
        #display helper function
        self._editLines = templateHelper.editLines
        self._createBaseSphere = templateHelper.createBaseSphere
        self._instancesAtomsSphere = templateHelper.instancesAtomsSphere
        self._Tube = templateHelper.Tube
        self._createsNmesh = templateHelper.createsNmesh
        self._PointCloudObject = templateHelper.PointCloudObject
        #modify/update geom helper function
        self._updateSphereMesh = templateHelper.updateSphereMesh
        self._updateSphereObj = templateHelper.updateSphereObj
        self._updateSphereObjs = None#templateHelper.updateSphereObjs
        self._updateTubeMesh = templateHelper.updateTubeMesh
        self._updateTubeObj = templateHelper.updateTubeObj
        self._updateMesh = templateHelper.updateMesh
        #color helper function
        self._changeColor = templateHelper.changeColor
        self._checkChangeMaterial = templateHelper.checkChangeMaterial
        self._changeSticksColor = templateHelper.changeSticksColor
        self._checkChangeStickMaterial = templateHelper.checkChangeStickMaterial
        #define the general function
        self.use_progressBar = False

    def _resetProgressBar(self,max):
        return
        
    def _progressBar(self,progress,label):
        return
        
    def _makeRibbon(self,name,coords,shape=None,spline=None,parent=None):
        sc=self._getCurrentScene()
        if shape is None :
            # create full circle at origin on the x-y plane
            #return obj (Circle) and makenurbeCircle but not the CircleShape
            shape = "CircleShape"
        if spline is None :
            obSpline,spline = self.helper.spline(name,coords,extrude_obj=shape,scene=sc)
        return obSpline
