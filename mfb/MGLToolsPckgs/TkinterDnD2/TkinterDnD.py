'''Python wrapper for the tkDnD tk extension, which adds native drag and drop support for windows and unix systems.'''
import Tkinter
import Tix

def _require(tkroot):
    '''Internal function.'''
    master = tkroot
    import os, sys
    from os import path
    # Togl is expected to be 

    # build path to directory containing Togl
    from opengltk.OpenGL import Tk
    ToglPath = path.dirname(path.abspath(Tk.__file__))
    # get TCL interpreter auto_path variable
    tclpath = master.tk.globalgetvar('auto_path')

    # ToglPath not already in there, add it
    from string import split
    if ToglPath not in tclpath:
        tclpath = (ToglPath,) + tclpath
        master.tk.globalsetvar('auto_path', tclpath )
    tkdndver = tkroot.tk.call('package', 'require', 'tkdnd')
    return tkdndver

class DnDEvent:
    """Internal class. Container for the properties of a drag-and-drop event."""
    pass

class DnDWrapper:
    '''Internal class.'''
    _subst_format_dnd = ('%A', '%a', '%b', '%C', '%c', '%CST', '%CTT', '%D', '%e',
                         '%L', '%m', '%ST', '%T', '%t', '%TT', '%W', '%X', '%Y')
    _subst_format_str_dnd = " ".join(_subst_format_dnd)
    Tkinter.BaseWidget._subst_format_dnd = _subst_format_dnd
    Tkinter.BaseWidget._subst_format_str_dnd = _subst_format_str_dnd
    
    def _substitute_dnd(self, *args):
        """Internal function."""
        if len(args) != len(self._subst_format_dnd):
            return args
        def getint_event(s):
            try:
                return int(s)
            except ValueError:
                return s
        def getints_event(l):
            try:
                return self._getints(l)
            except ValueError:
                return l
        def splitlist_event(s):
            try:
                return self.tk.splitlist(s)
            except ValueError:
                return s
        A, a, b, C, c, CST, CTT, D, e, L, m, ST, T, t, TT, W, X, Y = args
        ev = DnDEvent()
        ev.action = A
        ev.actions = splitlist_event(a)
        ev.button = getint_event(b)
        ev.code = C
        ev.codes = splitlist_event(c)
        ev.commonsourcetypes = splitlist_event(CST)
        ev.commontargettypes = splitlist_event(CTT)
        ev.data = D
        ev.name = e
        ev.types = splitlist_event(L)
        ev.modifiers = splitlist_event(m)
        ev.supportedsourcetypes = splitlist_event(ST)
        ev.sourcetypes = splitlist_event(t)
        ev.type = T
        ev.supportedtargettypes = splitlist_event(TT)
        try:
            ev.widget = self._nametowidget(W)
        except KeyError:
            ev.widget = W
        ev.x_root = getint_event(X)
        ev.y_root = getint_event(Y)
        return (ev,)
    Tkinter.BaseWidget._substitute_dnd = _substitute_dnd
    
    def drag_source_register(self, button=None, *dndtypes):
        '''This command will register SELF as a drag source. A drag source is
        a widget than can start a drag action. This command can be executed
        multiple times on a widget. When SELF is registered as a drag source,
        optional DNDTYPES can be provided. These DNDTYPES will be provided during a
        drag action, and it can contain platform independent or platform
        specific types. Platform independent are DND_Text for dropping text
        portions and DND_Files for dropping a list of files (which can contain
        one or multiple files) on SELF. However, these types are
        indicative/informative. SELF can initiate a drag action with even a
        different type list. Finally, button is the mouse button that will be
        used for starting the drag action. It can have any of the values 1
        (left mouse button), 2 (middle mouse button - wheel) and
        3 (right mouse button). If button is not specified, it defaults to 1.'''
        self.tk.call('tkdnd::drag_source', 'register', self._w, dndtypes, button)
    Tkinter.BaseWidget.drag_source_register = drag_source_register
    
    def drag_source_unregister(self):
        '''This command will stop SELF from being a drag source. Thus, window
        will stop receiving events related to drag operations. It is an error
        to use this command for a window that has not been registered as a
        drag source with drag_source_register().'''
        self.tk.call('tkdnd::drag_source', 'unregister', self._w)
    Tkinter.BaseWidget.drag_source_unregister = drag_source_unregister
    
    def drop_target_register(self, *dndtypes):
        '''This command will register SELF as a drop target. A drop target is
        a widget than can accept a drop action. This command can be executed
        multiple times on a widget. When SELF is registered as a drop target,
        optional DNDTYPES can be provided. These types list can contain one or
        more types that SELF will accept during a drop action, and it can
        contain platform independent or platform specific types. Platform
        independent are DND_Text for dropping text portions and DND_Files for
        dropping a list of files (which can contain one or multiple files) on
        SELF.'''
        self.tk.call('tkdnd::drop_target', 'register', self._w, dndtypes)
    Tkinter.BaseWidget.drop_target_register = drop_target_register
    
    def drop_target_unregister(self):
        '''This command will stop SELF from being a drop target. Thus, SELF
        will stop receiving events related to drop operations. It is an error
        to use this command for a window that has not been registered as a
        drop target with drop_target_register().'''
        self.tk.call('tkdnd::drop_target', 'unregister', self._w)
    Tkinter.BaseWidget.drop_target_unregister = drop_target_unregister
    
    def platform_specific_types(self, *dndtypes):
        '''This command will accept a list of types that can contain platform
        independnent or platform specific types. A new list will be returned,
        where each platform independent type in DNDTYPES will be substituted by
        one or more platform specific types. Thus, the returned list may have
        more elements than DNDTYPES.'''
        return self.tk.split(self.tk.call('tkdnd::platform_specific_types', dndtypes))
    Tkinter.BaseWidget.platform_specific_types = platform_specific_types
    
    def platform_independent_types(self, *dndtypes):
        '''This command will accept a list of types that can contain platform
        independnent or platform specific types. A new list will be returned,
        where each platform specific type in DNDTYPES will be substituted by one
        or more platform independent types. Thus, the returned list may have
        more elements than DNDTYPES.'''
        return self.tk.split(self.tk.call('tkdnd::platform_independent_types', dndtypes))
    Tkinter.BaseWidget.platform_independent_types = platform_independent_types
    
    def get_dropfile_tempdir(self):
        '''This command will return the temporary directory used by TkDND for
        storing temporary files. When the package is loaded, this temporary
        directory will be initialised to a proper directory according to the
        operating system. This default initial value can be changed to be the
        value of the following environmental variables: TKDND_TEMP_DIR, TEMP, TMP.'''
        return self.tk.call('tkdnd::GetDropFileTempDirectory')
    Tkinter.BaseWidget.get_dropfile_tempdir = get_dropfile_tempdir
    
    def set_dropfile_tempdir(self, tempdir):
        '''This command will change the temporary directory used by TkDND for
        storing temporary files to TEMPDIR.'''
        self.tk.call('tkdnd::SetDropFileTempDirectory', tempdir)
    Tkinter.BaseWidget.set_dropfile_tempdir = set_dropfile_tempdir
    
    def _dnd_bind(self, what, sequence, func, add, needcleanup=1):
        """Internal function."""
        if type(func) is Tkinter.StringType:
            self.tk.call(what + (sequence, func))
        elif func:
            funcid = self._register(func, self._substitute_dnd,
                        needcleanup)
            #cmd = ('%sif {"[%s %s]" == "break"} break\n'
            #       %
            #       (add and '+' or '',
            #    funcid, self._subst_format_str_dnd))
            cmd = '%s%s %s' %(add and '+' or '', funcid, self._subst_format_str_dnd)
            self.tk.call(what + (sequence, cmd))
            return funcid
        elif sequence:
            return self.tk.call(what + (sequence,))
        else:
            return self.tk.splitlist(self.tk.call(what))
    Tkinter.BaseWidget._dnd_bind = _dnd_bind
    
    def dnd_bind(self, sequence=None, func=None, add=None):
        '''Bind to this widget at drag and drop event SEQUENCE a call
        to function FUNC.
        SEQUENCE may be one of the following:
        <<DropEnter>>, <<DropPosition>>, <<DropLeave>>, <<Drop>>, <<Drop:type>>,
        <<DragInitCmd>>, <<DragEndCmd>>'''
        return self._dnd_bind(('bind', self._w), sequence, func, add)
    Tkinter.BaseWidget.dnd_bind = dnd_bind

class Tk(Tkinter.Tk, DnDWrapper):
    '''Creates a new instance of a Tkinter.Tk() window; all methods of the
    DnDWrapper class apply to this window and all its child widgets.'''
    def __init__(self, *args, **kw):
        Tkinter.Tk.__init__(self, *args, **kw)
        self.TkdndVersion = _require(self)

class TixTk(Tix.Tk, DnDWrapper):
    '''Creates a new instance of a Tix.Tk() window; all methods of the
    DnDWrapper class apply to this window and all its child widgets.'''
    def __init__(self, *args, **kw):
        Tix.Tk.__init__(self, *args, **kw)
        self.TkdndVersion = _require(self)
