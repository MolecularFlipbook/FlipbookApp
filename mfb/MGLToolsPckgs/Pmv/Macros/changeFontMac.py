import Tkinter,string
familyVar=Tkinter.StringVar()
sizeVar=Tkinter.IntVar()
styleVar=Tkinter.StringVar()

def changeFont():
	"""Allow User to Change GUI's font"""
	global makeChange, familyVar, sizeVar, styleVar
	from ViewerFramework.gui import InputFormDescr
	def makeChange(wid,newfont):
		global makeChange
		try:
			wid.config(font=newfont)
		except :
			pass
		if len(wid.children)==0: return
		#if wid.__class__==Tkinter.Toplevel: return
		for item in wid.children.values():
			makeChange(item, newfont)	

	#familyNames=['Times','Helvetica','Courier','Symbol','Verdana']
	root=self.GUI.ROOT.tk
	familyNames=list(root.splitlist(root.call('font','families')))
	familyNames.sort()
	sizeNames=[10,12,14,16,18,20]
	styleNames=['normal','bold','bold italic']
	if familyVar.get() not in familyNames: familyVar.set(familyNames[0])
	if int(sizeVar.get()) not in sizeNames: sizeVar.set(str(sizeNames[0]))
	if styleVar.get() not in styleNames: styleVar.set(styleNames[0])

	ifd=InputFormDescr(title='Select New Font')
	ifd.append({'widgetType':Tkinter.Radiobutton,
		'name':'family',
		'listtext':familyNames,
		'groupedBy':10,
		'defaultValue':familyVar.get(),
		'wcfg':{'variable':familyVar},
		'gridcfg':{'sticky':Tkinter.W}})
	ifd.append({'widgetType':Tkinter.Radiobutton,
		'name':'size',
		'listtext':sizeNames,
		'defaultValue':sizeVar.get(),
		'wcfg':{'variable':sizeVar},
		'gridcfg':{'sticky':Tkinter.W,'row':0,'column':5}})
	ifd.append({'widgetType':Tkinter.Radiobutton,
		'name':'style',
		'listtext':styleNames,
		'defaultValue':styleVar.get(),
		'wcfg':{'variable':styleVar},
		'gridcfg':{'sticky':Tkinter.W,'row':0,'column':6}})
	val=self.getUserInput(ifd)
	if not val: return
	newfont=(val['family'],int(val['size']),val['style'])
	makeChange(self.GUI.ROOT, newfont)
	self.GUI.ROOT.option_add('*font', newfont)


attrVar=Tkinter.StringVar()
def changeAttr():
	"""UNFINISHED macro to change config option of mvGUI"""
	from ViewerFramework.gui import InputFormDescr
	global changeAttr
	def changeAttr(wid,attr,newVal):
		global changeAttr
		try:
			wid.config(attr=newVal)
		except:
			pass
		if len(wid.children)==0: return
		for item in wid.children.values():
			changeAttr(item,attr,newVal)

	configKeys=self.GUI.menuBars['menuRoot'].menubuttons['File'].config().keys()
	ifd=InputFormDescr(title='Select Attr To Change')
	ifd.append({'widgetType':Tkinter.Radiobutton,
		'name':'attrs',
		'listtext':configKeys,
		'defaultValue':attrVar.get(),
		#'wcfg':{'variable':attrVar,
				#'command':showOptions},
		'gridcfg':{'sticky':Tkinter.W}})
	val = self.getUserInput(ifd)
	if not val: return
	attr=val['attrs']
	print 'change ', attr, 'now'
	print 'good luck!'

