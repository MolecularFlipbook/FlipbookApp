from bge import logic

class Event():
	'''describes a single watchable event, listeners will be notified via callable(event)'''
	def __init__(self, name = None):
		self.name = name
		self.listeners = []

	def notify(self):
		for listener in self.listeners:
			if callable(listener):
				try:
					listener(self.name)
				except Exception as E:
					self.unregister(listener)
					print('Error notifying ', listener)
					print(E)

	def register(self, func):
		try:
			self.listeners.append(func)
		except Exception as E:
			print('Error registering', E)

	def unregister(self, func):
		try:
			self.listeners.remove(func)
		except Exception as E:
			print('Error unregistering', E)


class System():
	appStart = Event('APPSTART')
	rightClick = Event('RIGHTCLICK')
	leftClick = Event('LEFTCLICK')
	middleClick = Event('MIDDLECLICK')

class Loader():
	validFile = Event('VALIDPDB')
	loadPDB = Event('LOADPDB')
	loadPDBError = Event('LOADPDBERROR')
	loadBlobber = Event('LOADBLOBBER')

class Edit():
	displayBone = Event('DISPLAYBONE')
	displayMSMS = Event('DISPLAYMSMS')
	displayCMS = Event('DISPLAYCMS')
	moved = Event('PROTEINMOVED')
	rotated = Event('PROTEINROTATED')

class Panel():
	createMolecularWeight = Event('CREATEMOLECULARWEIGHT')
	createBlobby = Event('CREATEBLOBBY')
	rData = Event('RDATA')

class Timeline():
	addSlide = Event('ADDSLIDE')
	deleteSlide = Event('DELETESLIDE')
	moveSlide = Event('MOVESLIDE')
	keyframe = Event('KEYFRAME')
	play = Event('PLAY')
	pause = Event('PAUSE')
	intervalChange = Event('INTERVALCHANGE')

class View():
	moved = Event('MOVED')
	rotated = Event('ROTATED')
	zoomed = Event('ZOOMED')
	reset = Event('RESET')
	importDialogOn = Event('IMPORTDIALOGON')
	importDialogOff = Event('IMPORTDIALOGOFF')

class EventTree():
	''' build an event tree'''
	system = System()
	loader = Loader()
	edit = Edit()
	timeline = Timeline()
	view = View()
	panel = Panel()

def init():
	''' ran once on app start'''
	return EventTree()


