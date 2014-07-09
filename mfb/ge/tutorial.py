from bge import logic
from bge import events
from bge import render
from bgl import *

from . import bgui

# native python modules
import os, time, math


class Tutorial():
	'''Tutorial state machine'''
	def __init__(self):
		self._state = None 				# the current state of the FSM
		self.highlight = [] 			# list of widget used for highlighting

		# instantiate state list
		self.stateList()

	def start(self):
		''' start the tut'''
		self.state = self.quickStart0


	@property
	def state(self):
		return self._state

	@state.setter
	def state(self, value):
		if self._state:
			# unregister all previous callbacks
			for event, callback in self._state['listeners'].items():
				event.unregister(self.genericPluggableHandler)
			# clear old UI
			self.hideTutorialBox()

		if value:
			# register new callback for this state
			for event, callback in value['listeners'].items():
				event.register(self.genericPluggableHandler)

			# show ui
			if 'options' in value:
				arg = '\"\"\"' + value['message'] + '\"\"\" , \"\"\"' + value['prompt'] + '\"\"\" , ' + value['options']
				e = 'self.showTutorialBox(' + arg + ')'
				eval(e)
			else:
				self.showTutorialBox(value['message'], value['prompt'])

			if 'highlight' in value:
				try:
					widget = eval(value['highlight'])
				except:
					print("Warning: no widget found to highlight")
					widget = None

				if widget:
					size = widget.size[:]
					pos = widget.position[:]
					w1 = bgui.Frame(widget, 'tutorialHighlight1', sub_theme='tutorialHighlight1', pos=[0,0], options=bgui.BGUI_NO_FOCUS|bgui.BGUI_FILLED)
					w2 = bgui.Frame(widget, 'tutorialHighlight2', sub_theme='tutorialHighlight2', pos=[0,0], options=bgui.BGUI_NO_FOCUS|bgui.BGUI_FILLED)
					w3 = bgui.Frame(widget, 'tutorialHighlight3', sub_theme='tutorialHighlight3', pos=[0,0], options=bgui.BGUI_NO_FOCUS|bgui.BGUI_FILLED)
					w1.z_index = 9998
					w2.z_index = 9998
					w3.z_index = 9998
					self.highlight = [w1, w2, w3]

		# save state
		self._state = value


	def genericPluggableHandler(self, event):
		''' handles all obervable events by jumping to a new state'''
		if 'condition' in self.state:
			if not eval(self.state['condition']):
				logic.logger.new('Condition not met for tutorial to continue', 'WARNING')
				return

		for listener, state in self.state['listeners'].items():
			if event == listener.name:
				if type(state) is str:
					self.state = eval(state)
				else:
					if state:
						print("Warning: Unknown nextState type")

					# either way, set state to None
					self.state = None




	def stateList(self):

		self.quickStart0 = {
			'message'  : "Hello and welcome to Molecular Flipbook! This software allows you to create simple molecular animations. Let's take a minute and go over the basics.",
			'prompt'   : "Click anywhere to continue the tutorial",
			'listeners': {logic.pluggable.system.leftClick: 'self.quickStart1'}
		}

		self.quickStart1 = {
			'message'  : "Great! The application is divided into several regions. In the centre of it is the 3D space.",
			'prompt'   : "Click to continue.",
			'listeners': {logic.pluggable.system.leftClick: 'self.quickStart2'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart2 = {
			'message'  : "First, let's import a protein into the scene.",
			'prompt'   : "Click on the Import Button on the left",
			'listeners': {logic.pluggable.view.importDialogOn: 'self.quickStart3'},
			'highlight': "logic.gui.groupicons.children['importBtn']"
		}

		self.quickStart3 = {
			'message'  : "You can select a PDB file from your computer, or fetch one from the PDB database with the 4 character PDB code.",
			'prompt'   : 'Click the “Browse Local” button or type in a PDB code (for example, 2PTC)',
			'options'  : 'offset = [0,-20], options=bgui.BGUI_CENTERX|bgui.BGUI_TOP',
			'listeners': {logic.pluggable.loader.validFile: 'self.quickStart4'}
		}

		self.quickStart4 = {
			'message'  : "Good! A large PDB might take some time to load.",
			'prompt'   : 'Click on Load PDB button to bring it into the scene',
			'options'  : 'offset = [0,-20], options=bgui.BGUI_CENTERX|bgui.BGUI_TOP',
			'listeners': {logic.pluggable.loader.loadPDB: 'self.quickStart5', logic.pluggable.loader.loadPDBError: 'self.quickStart5Error'},
			'highlight': "logic.gui.importDialog.panel.children['loadPDBBtn']"
		}

		self.quickStart5 = {
			'message'  : "Tada! You've successfully imported something into the scene.",
			'prompt'   : 'Click to continue',
			'listeners': {logic.pluggable.system.leftClick: 'self.quickStart6'},
			'condition': 'len(logic.mvb.objects) > 0',
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart5Error = {
			'message'  : "Oh no! It looks like this PDB cannot be imported fully.",
			'prompt'   : "Let us know and we will try to fix it. Try importing a different PDB",
			'listeners': {logic.pluggable.system.leftClick: 'self.quickStart6'},
			'condition': 'len(logic.mvb.objects) > 0',
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart6 = {
			'message'  : "The protein resides in a 3D space. You can explore this space by panning the view around.",
			'prompt'   : "To pan the view, right click and drag. Or Ctrl + left click.",
			'listeners': {logic.pluggable.view.moved: 'self.quickStart7'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart7 = {
			'message'  : "You can also rotate around the protein.",
			'prompt'   : "To rotate the view around, left click and drag",
			'listeners': {logic.pluggable.view.rotated: 'self.quickStart8'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart8 = {
			'message'  : "Finally, you can also zoom in and out of the scene.",
			'prompt'   : "To zoom, use the scroll wheel (or the + and - key on the keyboard)",
			'listeners': {logic.pluggable.view.zoomed: 'self.quickStart9'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart9 = {
			'message'  : "If you are ever lost in the 3D space, we have a handy function to reset the view.",
			'prompt'   : "Press the 'F' key to reset the view.",
			'listeners': {logic.pluggable.view.reset: 'self.quickStart10'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.quickStart10 = {
			'message'  : "That's it for the introduction. The help panel to the right has additional tutorials",
			'prompt'   : 'To continue the tutorials, clicke on "2. Object Manipulation"',
			'listeners': {logic.pluggable.system.leftClick: None},
			'highlight': "logic.gui.children['helpPane']"
		}

		#-----------------------------------------

		self.manipulation0 = {
			'message'  : "In this tutorial, you will learn about positioning the proteins in 3D space.",
			'prompt'   : 'Import at least one PDB in order to start this tutorial',
			'listeners': {logic.pluggable.system.leftClick: 'self.manipulation1'},
			'condition': 'len(logic.mvb.objects) > 0',
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.manipulation1 = {
			'message'  : "To manipulate a protein, you must first select it. ",
			'prompt'   : 'Left click on a protein to select it',
			'listeners': {logic.pluggable.system.leftClick: 'self.manipulation1a'},
			'condition': 'any(logic.mvb.preActiveObj)',
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.manipulation1a = {
			'message'  : "Selected objects are highlighted in green in the Outliner. ",
			'prompt'   : 'You can also select objects from the Outliner',
			'listeners': {logic.pluggable.system.leftClick: 'self.manipulation2'},
			'highlight': "logic.gui.outlinerPane"
		}

		self.manipulation2 = {
			'message'  : "You can use a special handle to manipulate your protein in three dimensions. The handle shows up when one or more protein is selected.",
			'prompt'   : 'Try Shift + Left Click to select multiple proteins',
			'listeners': {logic.pluggable.system.leftClick: 'self.manipulation3'},
			'highlight': "logic.gui.children['resolutionGate']"
		}


		self.manipulation3 = {
			'message'  : "The arrows on the handle can be used to move the protein.",
			'prompt'   : 'Click and drag one of the arrows to move your protein',
			'listeners': {logic.pluggable.edit.moved: 'self.manipulation4', logic.pluggable.edit.rotated: 'self.manipulation3R'},
			'highlight': "logic.gui.children['resolutionGate']"
		}


		self.manipulation3R = {
			'message'  : "You rotated the protein. Try move the protein first using the arrows on the handle.",
			'prompt'   : 'Click and drag one of the arrows to move your protein',
			'listeners': {logic.pluggable.edit.moved: 'self.manipulation4', logic.pluggable.edit.rotated: 'self.manipulation3R'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.manipulation4 = {
			'message'  : "The black dot in the middle of the handles can also be used to move the protein.",
			'prompt'   : 'Click and drag the black dot to move your protein',
			'listeners': {logic.pluggable.edit.moved: 'self.manipulation5', logic.pluggable.edit.rotated: 'self.manipulation3R'},
			'highlight': "logic.gui.children['resolutionGate']"
		}


		self.manipulation5 = {
			'message'  : "Good, you moved the protein. The circles on the handle can be used to rotate your protein.",
			'prompt'   : 'Click and drag the circle to rotate your protein',
			'listeners': {logic.pluggable.edit.rotated: 'self.manipulation6', logic.pluggable.edit.moved: 'self.manipulation5M'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.manipulation5M = {
			'message'  : "You moved the protein. Try rotating the protein using the circles on the handle.",
			'prompt'   : 'Click and drag the circle to rotate your protein',
			'listeners': {logic.pluggable.edit.rotated: 'self.manipulation6', logic.pluggable.edit.moved: 'self.manipulation5M'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.manipulation6 = {
			'message'  : "Remember, you can reset the view to see all the object at a glance.",
			'prompt'   : "Press the 'F' key to reset the view.",
			'listeners': {logic.pluggable.view.reset: 'self.manipulation7'},
			'highlight': "logic.gui.children['resolutionGate']"
		}


		self.manipulation7 = {
			'message'  : "Nicely Done! This is all for now!",
			'prompt'   : 'Click "3. Timeline" for the next tutorial',
			'listeners': {logic.pluggable.system.leftClick: None},
			'highlight': "logic.gui.children['helpPane']"

		}

		#-----------------------------------------

		self.timeline0 = {
			'message'  : "In this tutorial, you will learn about the timeline at the bottom of the screen. You’ll be using it to build your animation.",
			'prompt'   : 'Import at least one object in order to start this tutorial',
			'condition': 'len(logic.mvb.objects) > 0',
			'listeners': {logic.pluggable.system.leftClick: 'self.timeline1'},
			'highlight': "logic.gui.children['timeline']"
		}

		self.timeline1 = {
			'message'  : "Each slide represents a step in your animation.  In the beginning, you only have one slide, but you’ll need more than one to create an animation!",
			'prompt'   : 'Click the “+” button to duplicate the current slide.',
			'listeners': {logic.pluggable.timeline.addSlide: 'self.timeline2'},
			'highlight': "list(logic.gui.timeline.children['timelineScroll'].children.items())[0][1]"
		}

		self.timeline2 = {
			'message'  : "We’ve now duplicated the slide.  Let’s change some things to make the two slides different.",
			'prompt'   : 'With slide #2 selected, Try moving or rotating one of your proteins.',
			'listeners': {logic.pluggable.edit.moved: 'self.timeline3', logic.pluggable.edit.rotated: 'self.timeline3'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.timeline3 = {
			'message'  : "By adjusting the placement of proteins on each slide, you can create animations. Other properties such as color and shading can also be animated over time.",
			'prompt'   : 'Try changing the shading or display mode.',
			'listeners': {logic.pluggable.timeline.keyframe: 'self.timeline4'},
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.timeline4 = {
			'message'  : "Now you can play through your animation using the play button.",
			'prompt'   : 'Click on the Play button to play through your movie.',
			'listeners': {logic.pluggable.timeline.play: 'self.timeline5'},
			'highlight': "logic.gui.timeline.children['timeLinePlayBtn']"
		}

		self.timeline5 = {
			'message'  : "You can change the number of seconds it takes to transition between slides by changing the value between slides.",
			'prompt'   : 'Change the interval by using your middle mouse (scroll) button.',
			'listeners': {logic.pluggable.timeline.intervalChange: 'self.timeline6'},
			'highlight': "logic.gui.timeline.children['timelineScroll']"
		}

		self.timeline6 = {
			'message'  : "You can also delete slides.",
			'prompt'   : 'Click the "-" button to remove a slide',
			'listeners': {logic.pluggable.timeline.deleteSlide: 'self.timeline7'},
			'highlight': "logic.gui.timeline.children['timelineScroll']"
		}

		self.timeline7 = {
			'message'  : "Super!  That's all there is to the timeline. Feel free to keep playing around to create a longer animation!",
			'prompt'   : 'Click "4. Protein Appearance" for the next tutorial',
			'listeners': {logic.pluggable.system.leftClick: None},
			'highlight': "logic.gui.children['helpPane']"

		}

		#-----------------------------------------

		self.appearance0 = {
			'message'  : "In this tutorial, you will learn how to change the appearance of the proteins and the world.",
			'prompt'   : 'Click anywhere to start',
			'listeners': {logic.pluggable.system.leftClick: 'self.appearance1'},
		}

		self.appearance1 = {
			'message'  : "You can change the color of your proteins using the Shading button.",
			'prompt'   : 'Click on the Shading button to open the Shading window.',
			'listeners': {logic.pluggable.system.leftClick: 'self.appearance2'},
			'condition': "logic.options.view == 'SHADING'",
			'highlight': "logic.gui.groupicons.children['shadingBtn']"
		}

		self.appearance2 = {
			'message'  : "At least one protein need to be selected for us to change its color",
			'prompt'   : 'Click on a protein to select it',
			'listeners': {logic.pluggable.system.leftClick: 'self.appearance3'},
			'condition': 'any(logic.mvb.preActiveObj)',
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.appearance3 = {
			'message'  : "",
			'prompt'   : 'Use the color picker to apply a color to the protein.',
			'listeners': {logic.pluggable.timeline.keyframe: 'self.appearance4'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.appearance4 = {
			'message'  : "If there’s a color that you’d like to save for later, you can use the Swatch panel.",
			'prompt'   : 'Click on one of the gray squares to save the current color.',
			'listeners': {logic.pluggable.system.leftClick: 'self.appearance5'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.appearance5 = {
			'message'  : "In the Shading tool, you can also change the style of the protein surface.",
			'prompt'   : 'Use the Surface Style selector to pick a look for the protein.',
			'listeners': {logic.pluggable.timeline.keyframe: 'self.appearance6'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.appearance6 = {
			'message'  : "We have another tool, the Display tool, that will allow you to visualize your protein as a ribbon.",
			'prompt'   : 'Click on the Display button to open the Display window.',
			'listeners': {logic.pluggable.system.leftClick: 'self.appearance7'},
			'condition': 'logic.options.view == "REPRESENTATION"',
			'highlight': "logic.gui.groupicons.children['displayBtn']"
		}

		self.appearance7 = {
			'message'  : "Let’s see that protein as a ribbon.",
			'prompt'   : 'With a protein selected, click on the “Ribbon” button.',
			'listeners': {logic.pluggable.system.leftClick: 'self.appearance8'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.appearance8 = {
			'message'  : "Sweet! Remember that colors and display modes can also be animated over time.",
			'prompt'   : 'Click "5. Blobber" for the next tutorial',
			'listeners': {logic.pluggable.system.leftClick: None},
			'highlight': "logic.gui.children['helpPane']"
		}

		#-----------------------------------------

		self.blobber0 = {
			'message'  : "In this tutorial, you will learn about the unique blobber tool",
			'prompt'   : 'Click anywhere to start',
			'listeners': {logic.pluggable.system.leftClick: 'self.blobber1'},
		}

		self.blobber1 = {
			'message'  : "The Blobber tool can be used to create a protein blobby for which there isn’t a crystal structure or PDB.",
			'prompt'   : 'Click on the Blobber button to open the Blobber window.',
			'listeners': {logic.pluggable.system.leftClick: 'self.blobber2'},
			'condition': 'logic.options.view == "CREATE"',
			'highlight': "logic.gui.groupicons.children['blobberBtn']"
		}

		self.blobber2 = {
			'message'  : "To create a blobby, first you need to input a molecular weight.",
			'prompt'   : 'Click on the Molecular Weight field and change the value, if you’d like.',
			'listeners': {logic.pluggable.system.leftClick: 'self.blobber3'},
		}


		self.blobber3 = {
			'message'  : "The Blobber tool makes spherical blobs by default, but you can also make them tall or squat.",
			'prompt'   : 'Try changing the diameter or height slider to create a non-spherical blobby',
			'listeners': {logic.pluggable.system.leftClick: 'self.blobber4'},
		}


		self.blobber4 = {
			'message'  : "The preview of the shape can be seen in the 3d view. When you’ve perfected the shape and size of your blob,",
			'prompt'   : 'Click “OK” to finalize your blobby object.',
			'listeners': {logic.pluggable.panel.createBlobby: 'self.blobber5'},
		}


		self.blobber5 = {
			'message'  : "Very nice! Blobbies behave like regular objects, you can move them, change their colors, and animate them.",
			'prompt'   : 'Click "6. Protein Editor" for the next tutorial',
			'listeners': {logic.pluggable.system.leftClick: None},
			'highlight': "logic.gui.children['helpPane']"
		}

		#-----------------------------------------

		self.editor0 = {
			'message'  : "The protein editor allows you to add markers on a protein. e.g. to show where phosphorylation or other posttranslational modifications might occur.",
			'prompt'   : 'Click on the Editor button',
			'listeners': {logic.pluggable.system.leftClick: 'self.editor1'},
			'condition': 'logic.options.view == "EDITOR"',
			'highlight': "logic.gui.groupicons.children['editorBtn']"
		}

		self.editor1 = {
			'message'  : "The protein editor works with any PDB object.",
			'prompt'   : 'Select a PDB object to view its chain data',
			'listeners': {logic.pluggable.system.leftClick: 'self.editor2'},
			'condition': '[obj for obj in logic.mvb.activeObjs if logic.mvb.getMVBObject(obj).pdbData]',
			'highlight': "logic.gui.children['resolutionGate']"
		}

		self.editor2 = {
			'message'  : "Try creating a marker on your protein!",
			'prompt'   : 'Click on an amino acid in the sequence to select a marker.',
			'listeners': {logic.pluggable.panel.rData: 'self.editor3'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.editor3 = {
			'message'  : "Selected amino acid is marked by a 'v'.",
			'prompt'   : 'Click on the Add Marker button to mark the selected amino acid.',
			'listeners': {logic.pluggable.panel.rData: 'self.editor4'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.editor4 = {
			'message'  : "Wunderbar! Markers can be deleted in the same way, by selecting the animo acid and click on the Remove Marker button.",
			'prompt'   : 'Click "7. Creating a Movie" for the next tutorial',
			'listeners': {logic.pluggable.system.leftClick: None},
			'highlight': "logic.gui.children['helpPane']"
		}
		#-----------------------------------------

		self.movie0 = {
			'message'  : "Your masterpiece is ready, and now you’re ready to create a movie!",
			'prompt'   : 'Click on the Export button to open the Export window.',
			'listeners': {logic.pluggable.system.leftClick: 'self.movie1'},
			'condition': "logic.options.view == 'FINALIZE'",
			'highlight': "logic.gui.groupicons.children['renderBtn']"
		}

		self.movie1 = {
			'message'  : "You can change the video size, and name of the project in the Export window.",
			'prompt'   : 'Change some setting is you like, or click to continue.',
			'listeners': {logic.pluggable.system.leftClick: 'self.movie2'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.movie2 = {
			'message'  : "You can export a single slide as an image, or the entire animation as a video.",
			'prompt'   : '',
			'listeners': {logic.pluggable.system.leftClick: 'self.movie3'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.movie3 = {
			'message'  : "Click on Export to start rendering your movie.",
			'prompt'   : 'Flipbook will show you the finished animation when finished.',
			'listeners': {logic.pluggable.system.leftClick: 'self.movie4'},
			'highlight': "logic.gui.children['optionsPane']"
		}

		self.movie4 = {
			'message'  : "When you are happy with your animation, you can save it to disk or publish it to the web.",
			'prompt'   : 'Have fun using Molecular Flipbook!',
			'highlight': "logic.gui.groupicons.children['publishBtn']",
			'listeners': {logic.pluggable.system.leftClick: None},
		}


	def hideTutorialBox(self):
		'''remove the tutorial box'''
		# kill main dialog
		logic.gui.children['tutBoxO'].kill()
		# kill highlight
		self.hideHighlight()

	def hideHighlight(self):
		'''remove the highlight'''
		for widget in self.highlight:
			widget.kill()
		self.highlight = []

	def showTutorialBox(self, message="", prompt="", offset=[0,0], options=bgui.BGUI_CENTERX):
		'''create the tutorial box'''
		root = logic.gui
		pos = [int(root.size[0]/2-225), int(root.size[1]/2+75)]
		frameOuter = bgui.Frame(root, 'tutBoxO', size=[460,110], radius=10, pos=pos, offset=offset, sub_theme='lowOpacityDark', options=options)
		frameOuter.z_index = 9999		# always on top
		frameOuter.frozen = True		# click through
		frameInner = bgui.Frame(frameOuter, 'tutBoxI', size=[450,100], radius=6,  pos=[5,5])
		frameInner.frozen = True		# click through
		message = bgui.TextBlock(frameInner, 'msg', text=message, size=[420,60], pos=[15,30], sub_theme='whiteBlock')
		message.frozen = True
		prompt = bgui.Label(frameInner, 'ppt', text=prompt, pos=[10,20], sub_theme='whiteLabelBold', options=bgui.BGUI_CENTERX)
		prompt.frozen =True
		tutClose = bgui.ImageButton(frameInner, 'tutClose', size=[20,20], pos=[428,78], sub_theme="close")
		tutClose.on_left_release = self.endTutorial

	def endTutorial(self, widget):
		''' end the tutorial session by setting state to None'''
		self.state = None


def init():
	try:
		logic.pluggable
	except:
		raise Exception('Pluggable system is not availalbe')
		return None

	return Tutorial()
