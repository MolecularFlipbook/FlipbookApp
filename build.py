# Run with Python3

import argparse
import sys
import os
import shutil
import time
import struct


verbose = False

def doRelease(platform):
	print('Making a release for platform: %s' % platform)
	startTime = time.time()
	pwd = os.path.dirname(os.path.realpath(__file__))
	print('Working directory: %s' % pwd)

	print('Creating release folder', end='...')
	sys.stdout.flush()
	try:
		os.makedirs('release')
		print('Done')
	except Exception as E:
		print('Error', E)
		return

	ignored = shutil.ignore_patterns('*.pyc', '__pycache__', '.git', '*.bak', '*.original', '.svn*', '.CVS', 'datafiles', '*.old', 'test', 'tests', 'blenderplayer.exe', 'tzdata', 'deprecated')

	# check debug/release flag
	try:
		import mfb.ge.settings as settings
		if settings.useDebug:
			print('Warning: useDebug is set to True, you probably want to set it to False')
			print('Aborting')
			return
	except:
		pass
	


	print('Copying Files to release', end='...')
	sys.stdout.flush()
	
	if 'mac' in platform:
		shutil.copytree('mfb/binMac/flipbook.app', 'release/Molecular Flipbook.app', ignore=ignored)
		shutil.copy('mfb/binMac/ffmpeg', 'release/Molecular Flipbook.app/Contents/MacOS/ffmpeg')
		shutil.copytree('mfb/extraMac', 'release/Molecular Flipbook.app/Contents/Resources/extraMac', ignore=ignored)
	if 'win' in platform:
		doCleanRelease()
		shutil.copytree('mfb/binWin', 'release', ignore=ignored)
		shutil.copy('mfb/binWin/ffmpeg.exe', 'release/ffmpeg.exe')
		shutil.copytree('mfb/extraWin', 'release/extraWin', ignore=ignored)
		packBinary('mfb/binWin/blenderplayer.exe', 'mfb/MolecularFlipbook.blend', 'release/MolecularFlipbook.exe')

	if 'mac' in platform:
		shutil.copytree('mfb/creator', 'release/Molecular Flipbook.app/Contents/Resources/creator', ignore=ignored)
		shutil.copytree('mfb/ge', 'release/Molecular Flipbook.app/Contents/Resources/ge', ignore=ignored)
		shutil.copytree('mfb/shaders', 'release/Molecular Flipbook.app/Contents/Resources/shaders')
		shutil.copytree('mfb/textures', 'release/Molecular Flipbook.app/Contents/Resources/textures')
		shutil.copy('mfb/MolecularFlipbook.blend', 'release/Molecular Flipbook.app/Contents/Resources/game.blend')
	if 'win' in platform:
		shutil.copytree('mfb/creator', 'release/creator', ignore=ignored)
		shutil.copytree('mfb/ge', 'release/ge', ignore=ignored)
		shutil.copytree('mfb/shaders', 'release/shaders')
		shutil.copytree('mfb/textures', 'release/textures')
	print('Done')

	print('Copying MGLToolsPckgs to release', end='...')
	sys.stdout.flush()
	if 'mac' in platform:
		shutil.copytree('mfb/MGLToolsPckgs/mglutil', 'release/Molecular Flipbook.app/Contents/Resources/MGLToolsPckgs/mglutil', ignore=ignored)
		shutil.copytree('mfb/MGLToolsPckgs/MolKit', 'release/Molecular Flipbook.app/Contents/Resources/MGLToolsPckgs/MolKit', ignore=ignored)
		shutil.copytree('mfb/MGLToolsPckgs/PyBabel', 'release/Molecular Flipbook.app/Contents/Resources/MGLToolsPckgs/PyBabel', ignore=ignored)
		shutil.copytree('mfb/MGLToolsPckgs/Volume', 'release/Molecular Flipbook.app/Contents/Resources/MGLToolsPckgs/Volume', ignore=ignored)
	if 'win' in platform:
		shutil.copytree('mfb/MGLToolsPckgs/mglutil', 'release/MGLToolsPckgs/mglutil', ignore=ignored)
		shutil.copytree('mfb/MGLToolsPckgs/MolKit', 'release/MGLToolsPckgs/MolKit', ignore=ignored)
		shutil.copytree('mfb/MGLToolsPckgs/PyBabel', 'release/MGLToolsPckgs/PyBabel', ignore=ignored)
		shutil.copytree('mfb/MGLToolsPckgs/Volume', 'release/MGLToolsPckgs/Volume', ignore=ignored)
	print('Done')

	
	name = time.strftime('%Y%m%d')
	name += platform

	if 'mac' in platform:
		if 'zip' in platform:
			print('Zipping', end='...')
			sys.stdout.flush()
			shutil.make_archive(name, 'zip', 'release')
		else:
			print('Done')
	if 'win' in platform:
		if 'zip' in platform:
			print('Zipping', end='...')
			sys.stdout.flush()
			shutil.make_archive(name, 'zip', 'release')
		else:
			print('Windows release is ready for installer script.')
	

	elapsedTime = time.time() - startTime
	print('Completed in %d seconds' % elapsedTime)


def doCleanRelease():
	print('Cleaning Release folder...')
	fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'release')
	try:
		shutil.rmtree(fpath)
	except Exception as E:
		print(E)
		return

	print('%s Removed' % fpath)

def doCleanTemp():
	print('Cleaning Temp folder...')
	fpath = os.path.join(os.path.expanduser('~/Flipbook'))
	try:
		shutil.rmtree(fpath)
	except Exception as E:
		print(E)
		return
	
	print('%s Removed' % fpath)

# -------------------------------------------------------------------------------
def packBinary(player_path, blend_path, output_path):

	file = open(player_path, 'rb')
	player_d = file.read()
	offset = file.tell()
	file.close()
	
	# Create a tmp blend file (Blenderplayer doesn't like compressed blends)
	# assert Blend file isn't compressed.
	
	# Get the blend data
	blend_file = open(blend_path, 'rb')
	blend_d = blend_file.read()
	blend_file.close()

	# Create a new file for the bundled runtime
	output = open(output_path, 'wb')
	
	# Write the player and blend data to the new runtime
	print("Writing runtime...", end=" ")
	output.write(player_d)
	output.write(blend_d)
	
	# Store the offset (an int is 4 bytes, so we split it up into 4 bytes and save it)
	output.write(struct.pack('B', (offset>>24)&0xFF))
	output.write(struct.pack('B', (offset>>16)&0xFF))
	output.write(struct.pack('B', (offset>>8)&0xFF))
	output.write(struct.pack('B', (offset>>0)&0xFF))
	
	# Stuff for the runtime
	output.write(b'BRUNTIME')
	output.close()
	
	print("All Done")
	
# -------------------------------------------------------------------------------

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Help build MFB from source')
	parser.add_argument('action', help='Required. Actions to take (release, make)')
	parser.add_argument('options', help='Required. Options for the action. (mac, win, all)')
	parser.add_argument('--verbose', '-v', default=False, help='Show more information')
	args = parser.parse_args()

	verbose = args.verbose

	if args.action == 'release':
		doCleanRelease()
		doRelease(platform = args.options)
		
	elif args.action == 'clean':
		if args.options == 'all':
			doCleanRelease()
			doCleanTemp()
		if args.options == 'temp':
			doCleanTemp()
		if args.options == 'release':
			doCleanRelease()

	else:
		print('Invalid action:', args.action)

