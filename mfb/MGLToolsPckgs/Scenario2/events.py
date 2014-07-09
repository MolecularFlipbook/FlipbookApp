##
## Author Michel Sanner Feb 2009
##
## Copyrights TSRI and M. Sanner
##

from mglutil.events import Event, EventHandler
from Scenario2.multipleActorsActions import MultipleActorsActions, MAAGroup

class AddMAAEvent(Event):
    """
    Event object created when a MAA is added to a target

    eventObject <- AddMAAEvent(maa)

    maa is an instance of a MultipleActorsActions. It will be available in
    the event object as the .object attribute
    """
    def __init__(self, maa):

        assert isinstance(maa, MAAGroup) or isinstance(maa, MultipleActorsActions)
        Event.__init__(self)
        self.object = maa


class RemoveMAAEvent(Event):
    """
    Event object created when a MAA is removed from the clipboard

    eventObject <- RemoveMAAEvent(maa)

    maa is an instance of a MultipleActorsActions. It will be available in
    the event object as the .object attribute
    """

    def __init__(self, maa):

        assert isinstance(maa, MAAGroup) or isinstance(maa, MultipleActorsActions)
        Event.__init__(self)
        self.object = maa


class CurrentFrameEvent(Event):
    """
    Event object created when the current frame changes in the sequence animator

    eventObject <- currentFrameEvent(frame)

    frame is a 0-based integer
    """

    def __init__(self, frame):

        Event.__init__(self)
        self.frame = frame


class PlayerStartEvent(Event):
    """
    Event object created when the player starts playing an animation

    eventObject <- PlayerStartEvent()

    frame is a 0-based integer
    """

    def __init__(self, frame):

        Event.__init__(self)
        self.frame = frame


class PlayerStopEvent(Event):
    """
    Event object created when the player stops playing an animation

    eventObject <- PlayerStopEvent()

    frame is a 0-based integer
    """

    def __init__(self, frame):

        Event.__init__(self)
        self.frame = frame
