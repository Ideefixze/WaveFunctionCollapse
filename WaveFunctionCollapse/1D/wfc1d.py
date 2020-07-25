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

def countPatterns(input:str, N:int):
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

def countPatternsNoWrap(input:str, N:int):
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

def initializeCells(patterns:dict, n:int):
    """
    Makes every cell a superposition of all possible states.
    """
    cells = list()
    for i in range(n):
        cell = list()
        for key in patterns.keys():
            cell.append(key)
        cells.append(cell)
    return cells

def observe(patterns:dict, cells:list, finalstate:list):
    """
    Selects cell with minimal entropy and chooses a state randomly.
    """
    min = len(patterns)+1
    minid = -1
    for id,i in enumerate(cells):
        if finalstate[id]==EMPTY_INDICATOR:
            if(len(i)<min):
                minid = id
                min = len(i)

    #Random one of possible choices at cell with minimal entropy
    #Possible change: random distribution using number of patterns that appeared in input
    finalstate[minid] = cells[minid][random.randint(0,len(cells[minid])-1)]
    cells[minid] = [finalstate[minid]]
    return minid


def validate(patterns:dict, cellA:list, cellB:list):
    """Removes all unaviable states from cellB looking from the perspective of cellA."""

    newcell = list()
    for j in cellB:
        for i in cellA:
            checkstr = i+j
            newpatterns=countPatternsNoWrap(checkstr, len(i))
            #If there is at least one 
            valok = True
            for k in newpatterns:
                if k not in patterns:
                    valok=False
                    break

            if valok and j not in newcell:
                newcell.append(j)

    haschanged = collections.Counter(cellB) != collections.Counter(newcell)
    cellB[:]=newcell
    return haschanged        

def propagate(patterns:dict, cells:list, pos:int):
    """
    Propagate change to other cells, reducing possibilites of their states. 
    """
    #Update right neighbour
    nextpos = (pos+1)%len(cells)
    haschanged = False
    if cells[pos]:
        haschanged = validate(patterns, cells[pos], cells[nextpos])
        
    if haschanged:
        propagate(patterns, cells, nextpos)
    else:
        return


def WFC(data:str, n:int, outputCellCount:int):
    patterns = countPatterns(data, n)
    cells = initializeCells(patterns,outputCellCount)
    finalstate = list()
    for i in range(outputCellCount):
        finalstate.append(EMPTY_INDICATOR)

    while EMPTY_INDICATOR in finalstate:
        pos = observe(patterns,cells,finalstate)
        propagate(patterns,cells,pos)

    print(''.join([str(elem) for elem in finalstate]))
    
if __name__ == "__main__":
    print("Input string:")
    inputstr = input()
    print("Input N parameter for WFC algorithm:")
    N = int(input())
    print("Input number of cells of N-size to fill in with patterns:")
    cellCount = int(input())
    print("Number of strings to generate:")
    count = int(input())
    for i in range(count):
        WFC(inputstr, N, cellCount)