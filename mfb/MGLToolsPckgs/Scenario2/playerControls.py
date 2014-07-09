from mglutil.gui.BasicWidgets.Tk.player import Player
from Scenario2.events import PlayerStartEvent, PlayerStopEvent
from Scenario2.director import MAADirector
import Tkinter, Pmw
import sys, os
import tkFileDialog
from time import strftime

class PlayerControls(Player):
    """Subclasses Player widget. Plays and records animations of the
    specified director object.
    PlayerControlsObject <- PlayerControls (director, kw)
    """
    def __init__(self, director, **kw):
##                         master=None, root=None,
##                         height=80,width=200,
##                         currentFrameIndex=0,
##                         startFrame=0, 
##                         endFrame=0,
##                         maxFrame=0,
##                         stepSize=1, 
##                         playMode=0,
##                         ##afterDelay=50,
##                         titleStr='Player',
##                         gotoStartfile = 'go_to_start.gif',
##                         gotoEndfile = 'go_to_end.gif',
##                         ff_revfile = 'ff_rev.gif',
##                         ff_fwdfile = 'ff_fwd.gif',
##                         stopfile = 'stop.gif',
##                         playfile = 'play_fwd.gif',
##                         playRevfile = 'play_rev.gif',
##                         chmodfile = 'chmod.gif',
##                         closefile = 'close.gif',
##                         iconpath = None,
##                         counter = 1,
##                         form2=1, gui=1,framerate=15., hasSlider=False):

        assert isinstance(director, MAADirector)
        self.director = director
        kw['gui'] = 1
        kw['form2'] = 1
        kw['startFrame'] = 0
        kw['maxFrame'] = kw['endFrame'] = director.endFrame
        kw['buttonMask'] = {'setanimB':False, 'closeB':False}
        kw['currentFrameIndex'] = -1
        Player.__init__(self, **kw)
        if self.hasSlider:
            slider = self.form.descr.entryByName['slider']['widget']
            sliderkw = {'from': self.startFrame-1, 'to': self.maxFrame+1}
            slider.configure(sliderkw)
            slider.set(self.currentFrameIndex)
        self.form.ent2.delete(0,'end')
        self.form.ent2.insert(0, 'start')
        self.recording = False
        if sys.platform == 'darwin':
            self.codecType = 'mpeg1video'
        else:
            self.codecType = 'mpeg2video'
        self.filename = 'movie.mpg'
        self.fileTypes = [("MPG", ".mpg")]
        self.cameraSize=Tkinter.StringVar()
        self.cameraSize.set("current")
        root = self.root
        screenw, screenh = root.winfo_screenwidth(), root.winfo_screenheight()
        res = [(320, 240), (640, 480), (1280, 720), (1920, 1080)]
        self.resolutions = {}
        for w,h in res:
            if w <= screenw and h <=screenh:
                self.resolutions["%dx%d"%(w,h)] = (w, h)
        nb = self.director._animNB
        if nb:
            self.vf=nb().pmv
        else:
            self.vf=None

        self.recordDialog = self.createRecordDialog()
        


    def createRecordDialog(self):
        self.balloon = Pmw.Balloon(self.master)
        dialog = Pmw.Dialog(
            self.master, buttons=['Record', 'Cancel'], defaultbutton='Record',
            title="Record Options")
        dialog.withdraw()
        # create a frame to hold group to force setting orient and rendering
        frame = Tkinter.Frame(dialog.interior())

        bn = Tkinter.Button(frame, text="Save As:", command = self.browseFile_cb,
                            width= 0, height=0)
        self.balloon.bind(bn, "Opens file browser")
        bn.grid(row=0, column=0,sticky='ew')
        
        filename = 'movie_'+strftime("%m-%d-%Y_%H:%M")+'.mpg'
        self.filenamew = fn = Pmw.EntryField(frame, command = self.getFileName_cb,
                                             entry_width = 35,
                                             value = filename)
        fn.grid( row=0, column = 1,sticky ='w') #columnspan=2)
        self.balloon.bind(fn, "type filename" )
        self.codecw = Pmw.RadioSelect(frame, labelpos='w', label_text="Codec:",
                                      selectmode='single', orient='horizontal',
                                      buttontype='radiobutton', command=self.setCodec_cb)
        for text in ['mpeg1video', 'mpeg2video']:
            self.codecw.add(text)

        self.codecw.grid( row=1, column=0, columnspan=2, sticky='ew')
        self.cameraSizeMenub = None
        if self.vf:
            listitems = self.resolutions.keys()
##             csize = Pmw.ComboBox(frame, labelpos = 'w',
##                                 label_text = 'Camera Size:',
##                                 #entryfield_validate = self.entryValidate,
##                                 entryfield_value="current",
##                                 scrolledlist_items=listitems, 
##                                 #fliparrow=1,
##                                  history=False,
##                                  selectioncommand=self.setCameraSize_cb)
            
##             csize.grid( row=2, column=0, columnspan=2, sticky='ew')
            self.cameraSizeMenub = mb= Tkinter.Menubutton(frame, text='Select camera size...',
                           underline=0, relief='raised')
            #mb('<Button-1>', toggleMenu, '+')
            mb.grid( row=2, column=0, columnspan=2, sticky='ew')
            mb.menu = Tkinter.Menu(mb)
            for s in self.resolutions.keys():
                mb.menu.add_radiobutton(label=s,
                                        var=self.cameraSize,
                                        value = s,
                                        command = self.setCameraSize_cb)
            mb.menu.add_radiobutton(label="current", var=self.cameraSize,
                                    value="current",
                                    command = self.setCameraSize_cb)
            mb['menu'] = mb.menu
            self.balloon.bind(mb, "Left-Click to select camera size")
        frame.pack( fill='x', expand=1)
        return dialog


    
    def browseFile_cb(self):
        """callback of the 'Save as' button of the record dialog. Opens a file browser."""
        
        fileDir = None
        if self.filename:
            if os.path.exists(self.filename):
                fileDir = os.path.dirname(os.path.realpath(self.filename))
            else:
                fileDir = os.getcwd()
        file = tkFileDialog.asksaveasfilename( filetypes=self.fileTypes,
                                               initialdir=fileDir,
                                               initialfile=None,
                                               title="Save file")
        if file:
            if self.filename != file:
                self.fileName = file
                self.filenamew.setentry(file)


    def getFileName_cb(self):
        """ Get file name from the record dialog's entry field."""
        name = self.filenamew.get()
        if name:
            self.filename = name


    def setCodec_cb(self, val):
        """callback of the radioselect widget of the record dialog """
        self.codecType = val

    def setCameraSize_cb(self, object=None):
        val=self.cameraSize.get()
        #print "setCameraSize:", val
        if self.cameraSizeMenub:
            self.cameraSizeMenub.configure(text = "Camera size: %s" % val)
        if val != "current":
            if not self.vf.GUI.isCameraFloating():
                self.vf.GUI.floatCamera()
            if object is not None:
                camera = object.currentCamera
            else:
                camera = self.vf.GUI.VIEWER.currentCamera
            w, h = self.resolutions[val]
            if camera.width != w or camera.height != h:
                camera.Set(width=w, height=h)
                camera.Redraw()
            camera.lift()
            


    def startRecording_cb(self, event=None):
        """Callback of the 'record' (red dot) check button """
        ifd = self.form.ifd
        cbVar = ifd.entryByName['recordB']['wcfg']['variable']
        entry = ifd.entryByName['recordB']['widget']
        recording = cbVar.get()
        self.recording = recording
        if recording:
            # activate and place the dialog just below the button that was clicked:
            self.codecw.invoke(self.codecType)
            if event:
                x = event.x_root
                y = event.y_root
                if y + self.master.winfo_height() > self.master.winfo_screenheight():
                    y = self.master.winfo_screenheight() - self.master.winfo_height()
                exitStatus = self.recordDialog.activate(geometry = '+%d+%d' % (x, y ))
            else:
                exitStatus = self.recordDialog.activate(geometry = '+%d+%d' % (100, 100 ))

            if exitStatus=='Cancel':
                self.recording = False
                ifd = self.form.ifd
                cbVar = ifd.entryByName['recordB']['wcfg']['variable']
                cbVar.set(0)
                return 
            for viActor in self.director.redrawActors.values():
                cam = viActor.object.currentCamera
                self.setCameraSize_cb(viActor.object)
                self.getFileName_cb()
                #cam.setVideoOutputFile('movie_'+cam.uniqID+'.mpg')
                cam.setVideoOutputFile(self.filename)
                cam.setVideoParameters(outCodec=self.codecType)
                cam.nbRecordedframes = 0
                self.Play_cb()
        #print 'Recording', self.recording, self.stop


    def stopRecording_cb(self, event=None):
        """Stops camera recording. """
        if not self.recording:
            return
        self.recording = False
        for viActor in self.director.redrawActors.values():
            cam = viActor.object.currentCamera
            cam.stop()
            print 'Recorded', cam.nbRecordedframes
        ifd = self.form.ifd
        cbVar = ifd.entryByName['recordB']['wcfg']['variable']
        cbVar.set(0)
        #print 'Recording', self.recording


    def play(self, framerate=None,event=None):
        """this method is called by Play_cb()-the callback of the 'play' buttons """

        self.director.stopViewersAutoRedraw()
        self.director.dispatchEvent(PlayerStartEvent(0))
        #print 'in play() Recording', self.recording, self.stop
##         for i, viActor in enumerate(self.director.redrawActors.values()):
##             cam = viActor.object.currentCamera
##             if self.recording:
##                 #cam.setVideoOutputFile('movie_'+cam.uniqID+'.mpg')
##                 from time import strftime
##                 cam.setVideoOutputFile('movie_'+strftime("%m-%d-%Y_%H:%M")+'.mpg')
##                 cam.setVideoParameters()
##                 # don;t set recording else viewer redraw will record frames
##                 # the frames are recorded explicitely in nextFrame()
##                 #cam.videoRecordingStatus = 'recording'
##                 cam.nbRecordedframes = 0

        Player.play(self, framerate, event)

        for i, viActor in enumerate(self.director.redrawActors.values()):
            cam = viActor.object.currentCamera
            if self.recording:
                self.stopRecording_cb()

        self.director.dispatchEvent(PlayerStopEvent(-1))        
        self.director.startViewersAutoRedraw()

        if self.currentFrameIndex == self.maxFrame:
            #self.director.afterAnimationCb()
            self.GoToEnd_cb()
        elif self.currentFrameIndex == self.startFrame:
            self.GoToStart_cb()
        

    def nextFrame(self, id):
        """Overrides Player.nextFrame() method.
        Actually displays the next frame and upades the slider widget of the player
        """
        try:
            # id can be a string 'start' or 'end'
            id = int(id)
        except:
            return

        if id == self.currentFrameIndex:
            return

        if self.hasCounter and self.gui:
            self.form.ent2.delete(0,'end')
            if id < 0:
                self.form.ent2.insert(0, 'start')
            else:
                self.form.ent2.insert(0, str(id))
            if self.hasSlider:
                self.form.ifd.entryByName['slider']['widget'].set(id)
        self.currentFrameIndex = id
        if  id < 0: return
        self.director.setValuesAt(id)
        self.currentFrameIndex = id
        self.director.viewerRedraw()
        if self.recording:
            for i, viActor in enumerate(self.director.redrawActors.values()):
                cam = viActor.object.currentCamera
                cam.recordFrame(force=True)
            
        
    def update(self):
        """call in response to addMaaEvents inplemented in gui.Tk.sequenceAnimator.py """
        #print "update" 
        self.startFrame = 0
        self.maxFrame = self.endFrame = self.targetFrame = self.director.endFrame-1
        if self.hasSlider:
            sliderWidget = self.form.ifd.entryByName['slider']['widget']
            sliderWidget.configure(to=self.maxFrame+1)


    def GoToStart_cb(self, event=None):
        """Callback of '|<<'  button . Sets the player to 'start' frame."""
        #print "GoToStart_cb", self.startFrame, self.currentFrameIndex
        self.currentFrameIndex = self.startFrame-1
        self.oneDirection = 0

        if self.hasCounter and self.gui:
            self.form.ent2.delete(0,'end')
            self.form.ent2.insert(0, 'start')
            if self.hasSlider:
                self.form.ifd.entryByName['slider']['widget'].set(self.startFrame-1)


    def GoToEnd_cb(self, event=None):
        """Callback of '>>|' button. Sets the player to 'end' frame. """
        #print 'GoToEnd'
        id = self.currentFrameIndex = self.maxFrame+1
        self.oneDirection = 0

        if self.hasCounter and self.gui:
            self.form.ent2.delete(0,'end')
            self.form.ent2.insert(0, 'end')
            if self.hasSlider:
                self.form.ifd.entryByName['slider']['widget'].set(id)

        
