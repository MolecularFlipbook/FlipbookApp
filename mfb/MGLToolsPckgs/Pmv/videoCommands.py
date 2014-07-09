
import weakref
from Pmv.mvCommand import MVCommand
from ViewerFramework.VFCommand import CommandGUI
from DejaVu.videoRecorder import Recorder

try:
    from DejaVu.Camera import RecordableCamera
    isrecordable = True
except:
    isrecordable = False

class VideoCommand(MVCommand):
    """This command uses DajaVu.Camera.RecordableCamera functionality to make mpg video."""

    def __init__(self):
        
        MVCommand.__init__(self)
        self.recorder = None
        self.gui = None
        self.camera = None


    def guiCallback(self):
        msg = "Camera does not support movie recording"
        if isrecordable:
            if not isinstance(self.vf.GUI.VIEWER.cameras[0], RecordableCamera):
                self.vf.warningMsg(msg)
                return
        else:
            self.vf.warningMsg(msg) 
            return
        self.camera = weakref.ref(self.vf.GUI.VIEWER.cameras[0])
        if self.recorder:
            self.recorder.buildForm()
        else:
            if not hasattr(self.camera, "videoRecorder"):
                self.camera().videoRecorder = None
            
            if self.camera().videoRecorder:
                self.recorder = self.camera().videoRecorder
            else:
                filename = "out.mpg"
                self.recorder = Recorder(self.vf.GUI.ROOT,
                                         filetypes=[("MPG", ".mpg")],
                                         fileName = filename, camera=self.camera())
                self.camera().videoRecorder = self.recorder
            self.gui = self.recorder.form


VideoCommandGUI = CommandGUI()
VideoCommandGUI.addMenuCommand('menuRoot', '3D Graphics','Video Recorder',
                               index = 6)
