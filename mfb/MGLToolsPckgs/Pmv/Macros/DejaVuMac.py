#
# WARNING: a comment is required after the function prototype
#
def sideBySideStereo():
    """switch the PMV main camera to side by side stereo mode (crosseyed)"""
    self.GUI.VIEWER.cameras[0].Set(stereoMode='SIDE_BY_SIDE')


def mono():
    """switch the PMV main camera to side mono mode"""
    self.GUI.VIEWER.cameras[0].Set(stereoMode='MONO')

    
def transformRoot():
    """Bind trackball to the root object.
The mouse transforms the whole scene move"""
    vi = self.GUI.VIEWER
    vi.TransformRootOnly(yesno=1)
    vi.SetCurrentObject(vi.rootObject)


def selectObject():
    """Bind trackball to a user specified object.
Only geometries related to this object move, scaling
is disabled"""
    from Pmv.guiTools import MoleculeChooser
    mol = MoleculeChooser(self).go(modal=0, blocking=1)
    vi = self.GUI.VIEWER
    vi.TransformRootOnly(yesno=0)
    obj = mol.geomContainer.geoms['master']
    vi.SetCurrentObject(obj)
    vi.BindTrackballToObject(obj)
    vi.currentTransfMode = 'Object'


def continuousMotion():
    """Toggle continuous motion on and off"""
    pass

def showHideDejaVuGUI():
    """show and hide the original DejaVu GUI."""
    if self.GUI.VIEWER.GUI.shown:
        self.GUI.VIEWER.GUI.withdraw()
    else:
        self.GUI.VIEWER.GUI.deiconify()
        


def inheritMaterial(object=None):
    """set material inheritence flag for all objects
in the sub-tree below the current object"""

    if object is None: object=self.GUI.VIEWER.currentObject
    for c in object.children:
        c.inheritMaterial = 1
        inheritMaterial(c)
        c.RedoDisplayList()

