"""
"""

MaxKF = 999999999


from clipboard import Clipboard

# create a default clipboard object that can be shared accros applications
# using scenario

class ScenarioMAATargets:
    """
    Class holding animator object that can  be targets for sending MAAs to
    """

    def __init__(self):
        self.targetNames = []
        self.targetsByName = {}

    def addAnimator(self, name, target, addingMethod):
        assert callable(addingMethod)
        self.targetNames.append(name)
        self.targetsByName[name] = (target, addingMethod)

    def addToTarget(self, name, maa):
        target, addingMethod = self.targetsByName[name]
        addingMethod(target, maa)

_MAATargets = ScenarioMAATargets()

from mglutil.util.callback import CallBackFunction

def addTargetsToMenu(menu, maa):
    for name in _MAATargets.targetNames:
        cb = CallBackFunction( _MAATargets.addToTarget, name, maa)
        menu.add_command(label='Add to '+name, command=cb)
 
# create a default clipboard object that can be shared accros applications
# using scenario

_clipboard = Clipboard()

#
# create an event handle for scenario events
from mglutil.events import EventHandler

_eventHandler = EventHandler()

