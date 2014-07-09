##
## Author Michel Sanner Feb 2009
##
## Copyrights TSRI and M. Sanner
##

from mglutil.events import Event, EventHandler

from Scenario2.multipleActorsActions import MultipleActorsActions


class AddMAAToClipBoardEvent(Event):
    """
    Event object created when a MAA is added to the clipboard

    eventObject <- AddMAAToClipBoardEvent(maa)

    maa is an instance of a MultipleActorsActions. It will be available in
    the event object as the .object attribute
    """
    def __init__(self, maa):

        assert isinstance(maa, MultipleActorsActions)
        Event.__init__(self)
        self.object = maa


class RemoveMAAFromClipBoardEvent(Event):
    """
    Event object created when a MAA is removed from the clipboard

    eventObject <- RemoveMAAFromClipBoardEvent(maa)

    maa is an instance of a MultipleActorsActions. It will be available in
    the event object as the .object attribute
    """

    def __init__(self, maa):

        assert isinstance(maa, MultipleActorsActions)
        Event.__init__(self)
        self.object = maa



class Clipboard(EventHandler):
    """
    Scenario clipboard class.

    This class holds a list of MultipleActorActions objects
    """

    def __init__(self):
        """
        Clipboard object constructor

        clipbardObject <- Clipboard()
        """
        EventHandler.__init__(self)
        self.maas = []


    def addMaa(self, maa, checkForDuplicates=True):
        """
        add a MultipleActorsActions (MAA) to this clipboard

        Bool <- Clipboard.addMAA(maa, checkForDuplicates=True)

        maa is an instance of a MultipleActorsActions
        if checkForDuplicates is True the same maa cannot be added twice
        
        Returns True if the MAA is added succefully and False else.
        A MAA cannot be added if this MAA is already on the Clipboard

        if the MAA is add an AddMAAToClipBoard is created and dispatched
        """
        assert isinstance(maa, MultipleActorsActions)

        # check if maa can be added
        if checkForDuplicates and maa in self.maas:
            return False

        # add maa
        self.maas.append(maa)

        # create and dispatch event
        self.dispatchEvent(AddMAAToClipBoardEvent(maa))

        return True


    def removeMaa(self, maa):
        """
        remove a MultipleActorsActions (MAA) from this clipboard

        Bool <- Clipboard.removeMaa(maa)

        maa is an instance of a MultipleActorsActions

        Returns True if the MAA is removed succefully or False 
        if the MAA is not found

        if the MAA is add an RemoveMAAToClipBoard is created and dispatched
        """
        assert isinstance(maa, MultipleActorsActions)

        # check if maa can be removed
        if maa not in self.maas:
            return False
        
        # remove maa
        self.maas.remove(maa)
        
        # create and dispatch event
        self.dispatchEvent(RemoveMAAFromClipBoardEvent(maa))

        return True


