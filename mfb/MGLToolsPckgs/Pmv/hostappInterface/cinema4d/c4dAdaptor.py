#############################################################################
#
# Author: Ludovic Autin
#
# Copyright: Ludovic Autin TSRI 2010
#
#
#############################################################################

from Pmv.hostappInterface.epmvAdaptor import epmvAdaptor
from Pmv.hostappInterface.cinema4d import helperC4D

import c4d
from c4d import gui


class c4dAdaptor(epmvAdaptor):
    
    def __init__(self,mv=None,debug=0):
        epmvAdaptor.__init__(self,mv,host='c4d',debug=debug)
        self.soft = 'c4d'
        self.helper = helperC4D
        #scene and object helper function
        self._getCurrentScene = helperC4D.getCurrentScene
        self._addObjToGeom = helperC4D.addObjToGeom
        self._host_update = helperC4D.update
        self._getObjectName = helperC4D.getObjectName
        self._parseObjectName = helperC4D.parseObjectName
        self._getObject = helperC4D.getObject
        self._addObjectToScene = helperC4D.addObjectToScene
        self._toggleDisplay = helperC4D.toggleDisplay
        self._newEmpty = helperC4D.newEmpty
        self._deleteObject = helperC4D.deleteObject
        #camera and lighting
        self._addCameraToScene = helperC4D.addCameraToScene
        self._addLampToScene = helperC4D.addLampToScene        
        #display helper function
        self._editLines = helperC4D.editLines
        self._createBaseSphere = helperC4D.createBaseSphere
        self._instancesAtomsSphere = helperC4D.instancesAtomsSphere
        self._Tube = helperC4D.Tube
        self._createsNmesh = helperC4D.createsNmesh
        self._PointCloudObject = helperC4D.PointCloudObject
        #modify/update geom helper function
        self._updateSphereMesh = helperC4D.updateSphereMesh
        self._updateSphereObj = helperC4D.updateSphereObj
        self._updateTubeMesh = helperC4D.updateTubeMesh
        self._updateTubeObj = helperC4D.updateOneSctick
        self._updateMesh = helperC4D.updateMesh
        #color helper function
        self._changeColor = helperC4D.changeColor
        self._checkChangeMaterial = helperC4D.checkChangeMaterial
        self._changeSticksColor = helperC4D.changeSticksColor
        self._checkChangeStickMaterial = helperC4D.checkChangeStickMaterial
        self._PolygonColorsObject = helperC4D.PolygonColorsObject
        #define the general function
        self.use_progressBar = False
        self.colorProxyObject = True
        self._progressBar = helperC4D.progressBar
        self._resetProgressBar = helperC4D.resetProgressBar

#    def _progressBar(self,progress,label):
#        #the progessbar use the StatusSetBar
#        c4d.StatusSetText(label)
#        c4d.StatusSetBar(int(progress*100.))
#
#    def _resetProgressBar(self,value):
#        c4d.StatusClear()

    def _makeRibbon(self,name,coords,shape=None,spline=None,parent=None):
        sc=self._getCurrentScene()
        if shape is None :
            circle=self.helper.Circle(name+"circle",rad=0.3)
            self._addObjectToScene(sc,circle)
        if spline is None :
            spline = self.helper.spline(name,coords)
            self._addObjectToScene(sc,spline[0])
        nurb=self.helper.sweepnurbs(name)
        self._addObjectToScene(sc,nurb,parent=parent)
        self.helper.reparent(spline[0],nurb)
        self.helper.reparent(circle,nurb)
        return nurb
        