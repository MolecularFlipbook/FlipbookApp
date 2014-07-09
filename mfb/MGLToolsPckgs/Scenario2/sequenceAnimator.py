##
## Author Michel Sanner Feb 2009
##
## Copyrights TSRI and M. Sanner
##

from Scenario2 import MaxKF
from Scenario2.director import MAADirector
from Scenario2.clipboard import Clipboard
from Scenario2.events import RemoveMAAEvent

class SequenceAnimator(MAADirector):
    """
    class storing a list of MultipleActorActions objects and allowing to play
    them in sequence and to rearrange their order.
    """

    def __init__(self):
        """
        SequenceAnimator object constructor.
        SequenceAnimatorObject <- SequenceAnimator()
        """
        MAADirector.__init__(self)
        self._animNB = None # will become a reference to the notebook widget
                            #of Pmv.customAnimation command


    def addMaa_cb(self, target, maa):
        """Callback to add a new maa to the SequeneAnimator. """
        self.addMAA(maa)


    def addMAA(self, maa):
        """
        Add maa at the end of SeqenceAnimator's maas list.
        val <- addMAA(maa)
        return value: returns True if maa is added successfully, False otherwise.
        """
        #end = self.endFrame
        #if end == 0 and len(self.maas)==0:
        #    position = 0
        #else:
        #    position = end + 1
        import types

        pos = self.endFrame
        maa.startOffset = 0
        maa.startFlag = "after previous"
        val = self.addMAAat( maa,  pos)
        return val


    def addMAAat(self, maa, pos, check=True):
        MAADirector.addMAAat(self, maa,pos, check)
        maa._animNB = self._animNB
        if hasattr(maa, "maas"):
            for _maa in maa.maas:
                _maa._animNB = self._animNB
            
 

    def moveMAA(self, maa, toPos):
        """ Move maa  to specified position (toPos). Update the positions of maas
        in the director's maas list
        None <- moveMaa( maa, toPos)
        """
        # maa is a (maa, position) tuple
        fromPos = self.maas.index(maa)
        
        # remove it
        self.maas.remove(maa)
        self.maas.insert(toPos, maa)

        # renumber positions
        pos = 0
##        pos = 0
##         for i in range(len(self.maas)):
##             self.maas[i][1] = pos
##             pos += self.maas[i][0].lastPosition + 1
        self.updatePositions(0, pos)


    def removeMAA(self, maa, position):
        """
        remove maa from sequence animator and renumber the starting position of
        all MAA after the removed one.

        None <- removeMAA(maa, position)
        arguments:
           maa: instance of MAA;
           position: the specified MAA starting position (offset) in the MAADirector.
        Event:
           generates a RemoveMAA event
        """

        # remove maa
        index = self.maas.index([maa, position])
        self.maas.pop( index )

        # MS: This is done by self.updatePositions
        # update director's endFrame
        #self.endFrame -= maa.lastPosition
        
        # renumber positions
        pos = position
        if index < len(self.maas):
            nextmaa = self.maas[index]
            startFlag =  nextmaa[0].startFlag
            if startFlag == "with previous" :
                if index > 0:
                    pos = self.maas[index-1][1]
                else:
                    pos = 0
            else: # "after previous"
                if index > 0:
                    if maa.startFlag != "after previous":
                        pos = self.maas[index-1][1] + self.maas[index-1][0].lastPosition + 1
                else:
                    pos = 0

##         for i in range(index, len(self.maas)):
##             self.maas[i][1] = pos
##             pos += self.maas[i][0].lastPosition + 1
        
        self.updatePositions(index, pos)
            
        # create and dispatch event
        self.dispatchEvent(RemoveMAAEvent(maa))


    def updatePositions(self, index, position):
        """Recompute positions of maas.
        None <- updatePositions(index, position)

        arguments:
           index - the maa index (in self.maas list) from which positions
                   should be recomputed
           position - frame number at which self.maas[index] will start

        """

        nbmaas = len(self.maas)

        #print "updatePositions", "index:", index, "position" , position

        if index >= nbmaas:
            self.updateEndFrame()
            return
        # find max end position of the maas upto the specified maa index
        maxpos = 0
        for i in range(index+1):
            maa, pos = self.maas[i]
            end = pos + maa.lastPosition
            if end > maxpos:
                maxpos = end
                
        # move back to first real start
        if self.maas[index][0].startFlag== 'with previous':
            while index > 0 and self.maas[index][0].startFlag== 'with previous':
                index -= 1
       
        

        # remember which MAA was the last one seen that was nor ith previous
        lastStart = index

        # set start position for maa
        maa, startFrame = self.maas[index]
        self.maas[index][1] = position + maa.startOffset # set starting position
        # pos will be the starting position of the next MAA
        pos = position + maa.startOffset + maa.lastPosition + 1
        maxpos = max(maxpos, pos)
        # loop over remaining MAAs in list 
        for i in range(index+1,  nbmaas):
            maa, startFrame = self.maas[i] 
            startFlag = maa.startFlag
            if startFlag == "with previous":
                # set start to stat of lastStart
                self.maas[i][1] = self.maas[lastStart][1] + maa.startOffset
                
                #set pos to the last frame of current maa + 1
                pos = self.maas[lastStart][1] + maa.startOffset + \
                           maa.lastPosition + 1
                # set maxpos to the maxinum nbumber of frames covered by MAAs
                # under this parent
                maxpos = max( maxpos, pos)
                
            elif startFlag == "after previous":
                # set the starting position to pos
                self.maas[i][1] = pos + maa.startOffset
                # increment pos to the next available frame
                pos += maa.startOffset + maa.lastPosition + 1
                maxpos = max( maxpos, pos)
                # remember that this MAA was not with previous
                lastStart = i
        # set the sequenceAnimator endFrame to the the first unused frame
        if nbmaas > 0:
            #self.endFrame = pos #self.maas[-1][1]+ self.maas[-1][0].lastPosition
            self.endFrame = maxpos
        else:
            self.endFrame = 0

