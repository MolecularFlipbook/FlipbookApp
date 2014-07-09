##
## Author Michel Sanner Feb 2009
##
## Copyrights TSRI and M. Sanner
##

from Scenario2.events import AddMAAEvent, RemoveMAAEvent, CurrentFrameEvent,\
     PlayerStartEvent, PlayerStopEvent
from Scenario2.sequenceAnimator import SequenceAnimator

import Tkinter, Pmw, os
from mglutil.util.callback import CallBackFunction
from mglutil.util.packageFilePath import findFilePath

from Scenario2.playerControls import PlayerControls

class SequenceAnimatorGUI:
    """
    class displaying the list of MultipleActorActions stored in
    a clipboard object and allowing to play them in sequence and to rearrange
    their order.
    """

    def __init__(self, animator, master=None):
        """
        SequenceAnimatorGUI constructor
        
        SequenceAnimatorGUI <- SequenceAnimatorGUI(animator, master=None)

        animator is an instance of a SequenceAnimator object
        master is a Tk container object. If master is None a Tkinter.Toplevel
        object is created

        This object registers interest in AddMAAToClipBoardEvent and
        RemoveMAAFromClipBoardEvent events with the standard
        SequenceAnimator object
        """

        assert isinstance(animator, SequenceAnimator)
        
        self.animator = animator
        
        self.master = master

        self.pl = None # will be the PlayerControls object

        animator.registerListener(AddMAAEvent, self.addMaaEvent_cb)
        animator.registerListener(RemoveMAAEvent, self.removeMaaEvent_cb)
        animator.registerListener(CurrentFrameEvent, self.curFrameEvent_cb)
        animator.registerListener(PlayerStartEvent, self.playerStart_cb)
        animator.registerListener(PlayerStopEvent, self.playerStop_cb)
        self.createGUI()
        self.refreshGUI()


    def playerStart_cb(self, event=None):
        """This function is called when a PlayerStartEvent is created
        """
        # save current active MAA
        sel = self.MAAContainer.getcurselection()
        if len(sel):
            self._currentSel = self.maaList.index(sel[0])


    def playerStop_cb(self, event=None):
        """This function is called when a PlayerStopEvent is created
        """
        # restore current active MAA
        if hasattr(self, '_currentSel'):
            self.MAAContainer.select_set(self._currentSel)
            del self._currentSel
        

    def addMaaEvent_cb(self, event=None):
        """This function is called by the dispatchEvent() in addMAAat() method of MAADirector.
        It updates the MAA Chooser and the Player"""
        # update list of MAAs in list
        self.refreshGUI()
        # update frame counter in player controls obejct
        self.pl.update()

    def removeMaaEvent_cb(self, event=None):
        """This function is called by the dispatchEvent() in removeMAA() method of SequenceAnimator.
        It updates the MAA Chooser and the Player."""
        self.refreshGUI()
        self.selectionCommand_cb()
        self.pl.update()

    def curFrameEvent_cb(self, event=None):
        """
        call back for current frame change in sequence animator
        highlight the MAA contianing this frame
        """
        frame = event.frame
        lb = self.MAAContainer
        for n, val in enumerate(self.animator.maas):
            maa, firstFrame = val
            if frame<=firstFrame or frame>firstFrame+maa.lastPosition:
                # frame not in this maa
                lb.itemconfigure(n, selectbackground='') # default grey
                lb.select_clear(n)
            else:
                lb.itemconfigure(n, selectbackground='yellow') # default grey
                lb.select_set(n)
        self.pl.update()

                
    def createGUI(self):
        """
        Create a ScrolledFrame to hold MAA entries
        """
        if self.master is None:
            self.master = master = Tkinter.Toplevel()
            self.ownsMaster = True
        else:
            self.ownsMaster = False
        self.balloon = Pmw.Balloon(self.master)

        ##
        ## Action Container
        ##        
        parent =  Pmw.Group(self.master, tag_text='Actions')

        # create container
	w = self.MAAContainer = Pmw.ScrolledListBox(
            parent.interior(), #labelpos='nw', label_text='AnimationClips',
            listbox_height = 6,
            selectioncommand = self.selectionCommand_cb,
            #dblclickcommand=self.defCmd,
            usehullsize = 0,
            #hull_width = 300,
            #hull_height = 200,
            )
        ##
        ## Action manipulation group
        ##        
	#w.grid(sticky='nesw', column=0, row=0, rowspan=3)
        w.pack(fill='both', expand=1, side="left")
        w._listbox.config(exportselection = False)
        
        ICONDIR = findFilePath('icons', 'mglutil.gui.BasicWidgets.Tk')
        manipGroup =  Pmw.Group(parent.interior(),
                                 tag_text='Manipulate Actions')
        master = manipGroup.interior()
        self.gotoStartIcon = im = Tkinter.PhotoImage(
            file=os.path.join(ICONDIR, 'go_to_start.gif'), master=master)
        w = self.startActionb =  Tkinter.Button(
            master, image=im, command=self.gotoActionStart_cb)
        w.pack(side='left', anchor='n')
        self.balloon.bind(w, "goto action's start") 

        self.gotoEndIcon = im = Tkinter.PhotoImage(
            file=os.path.join(ICONDIR, 'go_to_end.gif'), master=master)
        w = self.endActionb =  Tkinter.Button(
            master, image=im, command=self.gotoActionEnd_cb)
        w.pack(side='left', anchor='n')
        self.balloon.bind(w, "goto action's end") 
        
        self.moveUpIcon = im = Tkinter.PhotoImage(
            file=os.path.join(ICONDIR, 'arrowup.gif'), master=master)
        w = self.upb =  Tkinter.Button(master, image=im, command=self.moveUp_cb)
        w.pack(side='left', anchor='n')
        self.balloon.bind(w, "Move selected action one position up") 
        
        self.moveDownIcon = im = Tkinter.PhotoImage(
            file=os.path.join(ICONDIR, 'arrowdown.gif'), master=master)
        w = self.downb =  Tkinter.Button(
            master, image=im, command=self.moveDown_cb)
        w.pack(side='top', anchor='n')
        self.balloon.bind(w, "Move selected action one position down")         
        
        self.deleteIcon = im = Tkinter.PhotoImage(
            file=os.path.join(ICONDIR, 'close.gif'), master=master)
        w = self.deleteb =  Tkinter.Button(
            master, image=im, command=self.delete_cb)
        w.pack(side='top', anchor='n')
        self.balloon.bind(w, "Delete selected action")         

        manipGroup.pack(side='top')

        ##
        ## Action Group
        ##
        self.actionGroup =  Pmw.Group(parent.interior(), tag_text='force')
        actionFrame = self.actionGroup.interior()
        self.forceOrientTk = Tkinter.IntVar()
        w = self.orientb =  Tkinter.Checkbutton(
            actionFrame, text='Orientation', variable=self.forceOrientTk,
            command=self.orient_cb)
        w.pack(side='top', fill='x', anchor='nw')
        w.configure(state='disabled')
        self.balloon.bind(w, "Force the original orientation on the first frame of this action")
        
        self.forceRenderingTk = Tkinter.IntVar()
        w = self.renderingb =  Tkinter.Checkbutton(
            actionFrame, text='Rendering', variable=self.forceRenderingTk,
            command=self.rendering_cb)
        w.pack(side='top', fill='x', anchor='nw')
        w.configure(state='disabled')
        self.balloon.bind(w, "Force the original rendering on the first frame of this action")    
        self.actionGroup.pack(side='top', anchor='n', fill='x')

        w = self.editb =  Tkinter.Button(parent.interior(), text='Edit ...',
                                         command=self.edit_cb)
        w.pack(side='top', fill='x', anchor='n')
        self.balloon.bind(w, "Edit selected clip")    


        ##
        ## Start Group
        ##
        startgroup =  Pmw.Group(parent.interior(), tag_text='Start')
        startframe = startgroup.interior()
        self.startW = sw = Pmw.RadioSelect(
            startframe, selectmode='single', orient='vertical',
            buttontype='radiobutton', command=self.setStartFlag_cb)

        for text in ['after previous', 'with previous']:
            sw.add(text)

        sw.pack(side='top', anchor='n', fill='x',
                padx=5, pady=5)

        self.balloon.bind(sw.button("after previous"),
                          "Start selected item after the previous one")
        self.balloon.bind(sw.button("with previous"),
                          "Start selected item with the previous one")

        #sw.setvalue('after previous')
        self.offsetw = offw = Pmw.Counter(
            startframe, labelpos = 'w', label_text = 'Offset:',
            entry_width = 6, entryfield_value = 0,
            entryfield_command = self.setOffset_cb,
            datatype = self.setOffset_cb,
            entryfield_validate = {'validator' : 'integer' } )

        self.balloon.bind(offw,
                          "positive or negative offset from starting position")

        offw.pack(side='top', anchor='n', fill='x')

        parent.pack(fill='both', expand=1, padx=5, pady=5)
        startgroup.pack(side='top')
        

        #self.frameCounter = Tkinter.Label(master, text='Frame 000000')
        #self.frameCounter.pack(side='top')
        frame = Tkinter.Frame(self.master)               
        self.pl = PlayerControls( self.animator, root=frame, #root=self.master,
                                  form2=1, hasSlider=True)
        frame.pack(side='top')


        self.selectionCommand_cb() # called to configure the buttons


    def gotoActionEnd_cb(self, event=None):
        """
        callback for got to end button
        """
        curSel = self.MAAContainer.getcurselection()
        if len(curSel)==0:
            return
        index = self.maaList.index(curSel[0])
        maa, pos = self.animator.maas[index]
        #print 'Going to frame', pos + maa.lastPosition
        director = self.pl.director
        director.setValuesAt(pos + maa.lastPosition)
        director.viewerRedraw()
        self.MAAContainer.select_set(index)


    def gotoActionStart_cb(self, event=None):
        """
        callback for got to start button
        """
        curSel = self.MAAContainer.getcurselection()
        if len(curSel)==0:
            return
        index = self.maaList.index(curSel[0])
        maa, pos = self.animator.maas[index]
        #print 'Going to frame', pos
        director = self.pl.director
        director.setValuesAt(pos)
        director.viewerRedraw()
        self.MAAContainer.select_set(index)
        
        
    def refreshGUI(self):
        """Updates the entries of the MAA Chooser."""
        #self.maaList = ["%05d: "%i+ a.name for a,i in self.animator.maas]

        # save current selection
        curSel = self.MAAContainer.getcurselection()
        if len(curSel):
            indexSel = self.maaList.index(curSel[0])
        
        self.maaList = maas = []
        for i, (a,pos) in enumerate(self.animator.maas):
            if a.startFlag == 'with previous' and i != 0:
                maas.append("    %05d-%05d: "%(pos, pos+a.lastPosition) + a.name)
            else:
                maas.append("%05d-%05d: "%(pos, pos+a.lastPosition)+ a.name)

        self.MAAContainer.setlist(self.maaList)
        if len(curSel):
            self.MAAContainer.select_set(indexSel)
            
    def moveUp_cb(self, event=None):
        """Callback of the 'Move Up' button. Moves selected MAA entry up one position in the
        MAA Chooser."""
        sel = self.MAAContainer.getcurselection()
        if not len(sel): return
        index = self.maaList.index(sel[0])
        maa = self.animator.maas[index]
        self.animator.moveMAA(maa, index-1)
        self.refreshGUI()
        #self.MAAContainer.setvalue("%05d: %s"%(maa[1],maa[0].name))
        self.MAAContainer.setvalue(self.maaList[index-1])
        self.selectionCommand_cb()

        
    def moveDown_cb(self, event=None):
        """Callback of the 'Move Down' button. Moves selected MAA entry down one position in the
        MAA Chooser."""
        sel = self.MAAContainer.getcurselection()
        if not len(sel):return
        index = self.maaList.index(sel[0])
        maa = self.animator.maas[index]
        self.animator.moveMAA(maa, index+1)
        self.refreshGUI()
        #self.MAAContainer.setvalue("%05d: %s"%(maa[1],maa[0].name))
        self.MAAContainer.setvalue(self.maaList[index+1])
        self.selectionCommand_cb()


    def delete_cb(self, event=None):
        """Callback of the 'Delete' button. Deletes selected MAA from the MAA Chooser and the
        Sequence Animator's maas list.
        """
        sel = self.MAAContainer.getcurselection()
        if len(sel) == 0:
            return
        index = self.maaList.index(sel[0])
        maa, position = self.animator.maas[index]
        self.animator.removeMAA(maa, position)
        
        
    def orient_cb(self, event=None):
        """Callback of the 'Orinetation' button.
        """
        sel = self.MAAContainer.getcurselection()
        if len(sel)==0:
            return
        index = self.maaList.index(sel[0])
        maa, position = self.animator.maas[index]
        if hasattr(maa, "interpolateOrient"):
            maa.interpolateOrient = self.forceOrientTk.get()
        else:
            maa.forceOrient = self.forceOrientTk.get()
        
        
    def rendering_cb(self, event=None):
        """Callback of the 'Rendering' button.
        """
        sel = self.MAAContainer.getcurselection()
        if len(sel)==0:
            return
        index = self.maaList.index(sel[0])
        maa, position = self.animator.maas[index]
        if hasattr(maa, "interpolateRendering"):
            maa.interpolateRendering = self.forceRenderingTk.get()
        else:
            maa.forceRendering = self.forceRenderingTk.get()
        
 
    def sort_cb(self, tag):
        """Callback of the 'Sort Poly.' radio button.
        """
        curSel = self.MAAContainer.getcurselection()
        if len(curSel)==0:
            return
        index = self.maaList.index(curSel[0])
        maa, position = self.animator.maas[index]
        maa.sortPoly = tag

        
    def edit_cb(self, event=None):
        """Callback of the 'Edit ...' button.
        displays MAA editor for the currently slected clip
        """
        sel = self.MAAContainer.getcurselection()
        if len(sel) == 0:return
        index = self.maaList.index(sel[0])
        maa, position = self.animator.maas[index]

        kw = maa.editorKw
        args = maa.editorArgs
        kw['master'] = self.master
        editor =  maa.editorClass( *args, **kw)
        editor.edit(maa)
        # check if the maa has been added more than once to the sequence animator:
        for i , _maa in enumerate(self.animator.maas):
            if _maa[0] == maa and i < index:
                index = i
                position = _maa[1]
                break
        self.update(index, position)
        

    def update(self, index, position):
        self.animator.updatePositions(index, position)
        self.refreshGUI()
        self.pl.update()
        
        
    def selectionCommand_cb(self, event=None):
        """This function is called when an MAA is selected in the MAA Chooser.
        """
        sel = self.MAAContainer.getcurselection()
        self.upb.configure(state='disabled')
        self.downb.configure(state='disabled')
        self.deleteb.configure(state='disabled')
            
        if len(sel)==0:
            return

        self.deleteb.configure(state='normal')

        index = self.maaList.index(sel[0])
        
        if index > 0:
            self.upb.configure(state='normal')

        if index < len(self.maaList)-1:
            self.downb.configure(state='normal')
        maa, pos = self.animator.maas[index]

        if hasattr(maa, "interpolateOrient"):
            self.orientb.configure(state='normal')
            self.forceOrientTk.set(maa.interpolateOrient)
            self.actionGroup._tag.configure(text = 'interpolate')
            self.balloon.bind(self.orientb, "Interpolate orientation during playback")
        elif hasattr(maa, 'forceOrient'):
            self.orientb.configure(state='normal')
            self.forceOrientTk.set(maa.forceOrient)
            self.actionGroup._tag.configure(text = 'force')
            self.balloon.bind(self.orientb, "Force the original orientation on the first frame of this action")
        else:
            self.orientb.configure(state='disabled')
            
        if hasattr(maa, "interpolateRendering"):
            self.renderingb.configure(state='normal')
            self.forceRenderingTk.set(maa.interpolateRendering)
            self.balloon.bind(self.renderingb, "Interpolate rendering during playback")
        elif hasattr(maa, 'forceRendering'):
            self.renderingb.configure(state='normal')
            self.forceRenderingTk.set(maa.forceRendering)
            self.balloon.bind(self.renderingb, "Force the original rendering on the first frame of this action")
        else:
            self.renderingb.configure(state='disabled')
            
        if maa.editorClass:
            self.editb.configure(state='normal')
        else:
            self.editb.configure(state='disabled')
        
           
        self.startW.setvalue(maa.startFlag)
        self.offsetw.setvalue(maa.startOffset)
        

    def setStartFlag_cb(self, startFlag = None):
        """Callback of the 'Start' radio buttons. Sets a new starting
        position of the selected maa."""
        #print "setStartFlag_cb", startFlag
        sel = self.MAAContainer.getcurselection()
        if not len(sel):return
        index = self.maaList.index(sel[0])
        maa, position = self.animator.maas[index]
        position, index  = self.animator.computePosition(maa, startFlag=startFlag)
        maa.startFlag = startFlag

        self.animator.updatePositions(index, position-maa.startOffset)
        self.refreshGUI()
        #self.MAAContainer.setvalue(self.maaList[index])
        # make sure the player end frame is correct
        self.pl.update()

                
    def setOffset_cb(self, text=None, factor=None, increment=None, **kw):
        # text is current content of entry
        # factor is 1 for increment and -1 for decrement
        # increment is value of increment megawidget option
        """Callback of the 'offset' entry field.
        Sets maa.startOffset for the currently selected action

        Has to return the coutner value
        """
        sel = self.MAAContainer.getcurselection()
        if not len(sel):
            return 0
        
        if text is not None: # incrment or decrement arrow was used
            value = int(text)+(factor*increment)
        else: # return was hit in entry
            value = int(self.offsetw.get())
            
        index = self.maaList.index(sel[0])
        maa, oldpos = self.animator.maas[index]

        # remove offset form the current position
        position = oldpos - maa.startOffset

        maa.startOffset = value

        self.animator.updatePositions(index, position)

        self.refreshGUI()

        # make sure the player end frame is correct
        self.pl.update()

        return value
