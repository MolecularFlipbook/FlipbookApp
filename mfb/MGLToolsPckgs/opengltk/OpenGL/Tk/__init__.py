from Tkinter import _default_root, Tk

if _default_root is None:
	_default_root = Tk()
        _default_root.withdraw()
        
#toglInstallDir = '/tsri/python/sun4SunOS5/lib/ '
#path = _default_root.tk.globalgetvar('auto_path')
#_default_root.tk.globalsetvar('auto_path', (toglInstallDir,) + path )

#_default_root.tk.call('lappend', 'auto_path',
#                      '/mgl/ms1/python/dev/opengltk/OpenGL/Tk/')
#
#_default_root.tk.call('package', 'require', 'Togl')
#
#                      os.path.join( \
#				  os.path.dirname(__file__), \
#				  sys.platform + "-tk" + _default_root.getvar("tk_version")))
