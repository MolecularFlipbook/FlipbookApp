# hack script to get around the OS X tkinter threading limitation
# works on Python 2 and 3

import sys


try:
	import tkinter
except:
	import Tkinter as tkinter

try:
	from tkinter import filedialog
except:
	import tkFileDialog as filedialog

root = tkinter.Tk()
root.withdraw()

root.overrideredirect(True)
root.geometry('0x0+0+0')

root.deiconify()
root.lift()
root.focus_force()
root.wm_attributes("-topmost", 1)


def saveDialog():
	return filedialog.asksaveasfilename(parent=root, filetypes=[('Flipbook Sessions', '.flipbook')], defaultextension='.flipbook')

def openFlipbookDialog():
	return filedialog.askopenfilename(parent=root, filetypes = [('Flipbook Sessions', '.flipbook'), ('All', '*')])

def openPDBDialog():
	return filedialog.askopenfilename(parent=root, filetypes = [('PDB Files', '.pdb'), ('All', '*')])

def openAny():
	return filedialog.askopenfilename(parent=root)


if __name__ == '__main__':
	action = sys.argv[1]
	if action == 'save':
		out = saveDialog()
	elif action == 'openFlipbook':
		out = openFlipbookDialog()
	elif action == 'openPDB':
		out = openPDBDialog()
	elif action == 'openAny':
		out = openAny()
	else:
		out = ''

	sys.stdout.write(out)

