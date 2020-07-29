import os
import random
import collections

# Wave Function Collapse algorithm for 1D
# For an input string generates string of similar structure, respecting all constrains in an input string.
# Example: 
# INPUT: "AAXBBX", N=2, cellnum=8: 
# OUTPUT: "XAAAXBXBXBBBXAAA"
# 
# Example:
# INPUT: "DOG", N=3, cellnum=5
# OUTPUT: "OGDOGDOGDOGDOGD"

EMPTY_INDICATOR = 'EMPTY-CELL'


class WFC:
    def __init__(self, inputstr:str, n:int, cellsCount:int):
        self.input = inputstr
        self.n = n
        self.cellsCount = cellsCount
        self.initPatterns()
        self.initConstrains()
        self.reset()
        self.finalstate = list()

    def initPatterns(self):
        
        """
        Returns a dict of patterns (key, value), where key is a found pattern and value is number of pattern appearing in input.
        
        Does count patterns that wrap (example: 'ADAM' N=3, will find pattern MAD).
        """
        input = self.input
        self.patterns = dict()
        i = self.n
        #If we want all patterns at most N len:
        #for i in range(2,N+1):
        wrapinput = input[len(input)-i+1:len(input)] + input 
        chunks = [wrapinput[j:j+i] for j in range(0, len(wrapinput))]
        for k in chunks:
            if len(k)==i:
                self.patterns.setdefault(k,0)
                self.patterns[k]+=1
        return self.patterns

    def initCells(self):
        """
        Makes every cell a superposition of all possible states.
        """
        self.cells = list()
        for i in range(self.cellsCount):
            cell = list()
            for key in self.patterns.keys():
                cell.append(key)
            self.cells.append(cell)

    def initConstrains(self):
        self.constrains = list()
        for i in self.patterns.keys():
            for j in self.patterns.keys():
                checkstr = i+j
                foundpatterns = getPatternsNoWrap(checkstr,self.n)
                if set(foundpatterns)<=set(self.patterns.keys()):
                    self.constrains.append([i,j])

    def __observe(self):
        """
        Selects cell with minimal entropy and chooses a state randomly.
        """
        min = len(self.patterns)+1
        minid = -1
        for id,i in enumerate(self.cells):
            if self.finalstate[id]==EMPTY_INDICATOR:
                if(len(i)<min):
                    minid = id
                    min = len(i)

        #Random one of possible choices at cell with minimal entropy
        #Possible change: random distribution using number of patterns that appeared in input
        self.finalstate[minid] = self.cells[minid][random.randint(0,len(self.cells[minid])-1)]
        self.cells[minid] = [self.finalstate[minid]]
        return minid

    def __validate(self, cellA:list, cellB:list):
        """Removes all unavailable states from cellB looking from the perspective of cellA."""
        newcell = list()
        for j in cellB:
            for i in cellA:
                if [i,j] in self.constrains:
                    if j not in newcell:
                        newcell.append(j)

        haschanged = collections.Counter(cellB) != collections.Counter(newcell)
        cellB[:]=newcell
        return haschanged

    def __propagate(self, pos:int):
        """
        Propagate change to other cells, reducing possibilites of their states. 
        """
        
        #Update right neighbour
        nextpos = (pos+1)%len(self.cells)
        haschanged = False
        if self.cells[pos]:
            haschanged = self.__validate(self.cells[pos], self.cells[nextpos])

        if haschanged:
            self.__propagate(nextpos)
        else:
            return
    
    def generate(self):
        self.finalstate = list()
        for i in range(len(self.cells)):
            self.finalstate.append(EMPTY_INDICATOR)

        while EMPTY_INDICATOR in self.finalstate:
            pos = self.__observe()
            self.__propagate(pos)

        self.reset()
        return ''.join([str(elem) for elem in self.finalstate])

    def reset(self):
        self.initCells()


def getPatternsWrap(input:str, N:int):
    """
    Returns a dict of patterns (key, value), where key is a found pattern and value is number of pattern appearing in input.
    
    Does count patterns that wrap (example: 'ADAM' N=3, will find pattern MAD).
    """
    patterns = dict()
    i = N
    #If we want all patterns at most N len:
    #for i in range(2,N+1):
    wrapinput = input[len(input)-i+1:len(input)] + input 
    chunks = [wrapinput[j:j+i] for j in range(0, len(wrapinput))]
    for k in chunks:
        if len(k)==i:
            patterns.setdefault(k,0)
            patterns[k]+=1
    return patterns

def getPatternsNoWrap(input:str, N:int):
    """
    Returns a dict of patterns (key, value), where key is a found pattern and value is number of pattern appearing in input.
    
    Does not count patterns that wrap (example: 'ADAM' N=3, won't find pattern MAD).
    """
    patterns = dict()
    i = N
    #If we want all patterns at most N len:
    #for i in range(2,N+1):
    chunks = [input[j:j+i] for j in range(0, len(input))]
    for k in chunks:
        if len(k)==i:
            patterns.setdefault(k,0)
            patterns[k]+=1
    return patterns
    
if __name__ == "__main__":
    print("Input string:")
    inputstr = input()
    print("Input N parameter for WFC algorithm:")
    N = int(input())
    print("Input number of cells of N-size to fill in with patterns:")
    cellCount = int(input())
    print("Number of strings to generate:")
    count = int(input())
    wfc = WFC(inputstr, N, cellCount)
    for i in range(count):
        print(wfc.generate())
        