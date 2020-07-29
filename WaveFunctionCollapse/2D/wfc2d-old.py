import os
import random
import collections
from PIL import Image, ImageChops, ImageDraw, ImageSequence
import pathlib
import glob
import hashlib
from pandas import *
import copy
import cProfile

DIR=str(pathlib.Path(__file__).parent.absolute())
DIR_OUTPUT = os.path.join(DIR,"output")
ROTATIONS = False

def initWorkspace():
    files = glob.glob(DIR_OUTPUT+"/*")
    for f in files:
        os.remove(f)

def imgHash(img:Image):
    return hashlib.md5(img.tobytes()).hexdigest()

def crop(img, x, y, w, h):
    box = (x, y, x+w, y+h)
    area = img.crop(box)
    return area

def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst

def createPatternsFromFile(filename:str, N:int):
    """
    Creates NxN patterns from image with given filename. Returns a dict (k,v) where k = hash of img, v = img.
    """
    patterns = dict()
    imgsrc = Image.open(os.path.join(DIR,"input",filename)).convert('RGB')
    imgwrap = crop(imgsrc,0,0,imgsrc.width,imgsrc.height)

    img = Image.new('RGB', (imgsrc.width + N, imgsrc.height + N))
    img.paste(imgsrc,(0,0))
    img.paste(imgwrap,(0,imgsrc.height))
    img.paste(imgwrap,(imgsrc.width,0))
    img.paste(imgwrap,(imgsrc.width,imgsrc.height))
    #imgwrap.show()
    #img.show()
    for x in range(img.size[0]-N):
        for y in range(img.size[1]-N):
            pattern = crop(img, x, y,N,N)
            key = f"pat_{x}_{y}_r{0}"
            pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
            key = imgHash(pattern)
            patterns.setdefault(key,0)
            patterns[key] = pattern.copy()
            #print(f"----- {imgHash(patterns[key])} ------ {key}")

            if ROTATIONS:
                for i in range(1,4):
                    pattern.rotate(90)
                    key = f"pat_{x}_{y}_r{i}"
                    #pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
                    key = imgHash(pattern)
                    patterns.setdefault(key,0)
                    patterns[key] = pattern.copy()

    #print(patterns)
    #img.show()
    return patterns

def patternsFromImages(img1:Image, img2:Image, dir:list):
    patterns = dict()
    if dir[0]!=0:
        concatenated = get_concat_h(img1,img2)
        for x in range(img1.width):
            pattern = crop(concatenated,x,0,img1.width,img1.height)
            key = imgHash(pattern)
            patterns.setdefault(key,0)
            patterns[key] = pattern.copy()
            if ROTATIONS:
                for i in range(1,4):
                    pattern.rotate(90)
                    key = imgHash(pattern)
                    patterns.setdefault(key,0)
                    patterns[key] = pattern.copy()
        return patterns
    elif dir[1]!=0:
            concatenated = get_concat_v(img1,img2)
            for y in range(img1.height):
                pattern = crop(concatenated,0,y,img1.width,img1.height)
                key = imgHash(pattern)
                patterns.setdefault(key,0)
                patterns[key] = pattern.copy()
                if ROTATIONS:
                    for i in range(1,4):
                        pattern.rotate(90)
                        key = imgHash(pattern)
                        patterns.setdefault(key,0)
                        patterns[key] = pattern.copy()
            return patterns
    return []

def initializeCells(patterns:dict, n:int):
    """
    Makes every cell a superposition of all possible states.
    """
    cells = list()
    for i in range(n):
        cellrow = list()
        for j in range(n):
            cell = list()
            for key in patterns.keys():
                cell.append(key)
            cellrow.append(cell)
        cells.append(cellrow)
    return cells

    
def observe(patterns:dict, cells:list):
    """
    Selects cell with minimal entropy and chooses a state randomly.
    """
    min = len(patterns)+1
    minidx = -1
    minidy = -1
    for idrow,i in enumerate(cells):
        for id, j in enumerate(cells[idrow]):
            if len(j)>1:
                if(len(j)<=min):
                    minidx = idrow
                    minidy = id
                    min = len(j)

    #Random one of possible choices at cell with minimal entropy
    #Possible change: random distribution using number of patterns that appeared in input
    #finalstate[minid] = cells[minid][random.randint(0,len(cells[minid])-1)]
    #print(f"MINI: {min}")
    """    while True:
        minidx = random.randint(0,len(cells)-1)
        minidy = random.randint(0,len(cells)-1)
        m = len(cells[minidx][minidy])
        if m==min:
            break
    """
    cells[minidx][minidy] = [cells[minidx][minidy][random.randint(0,len(cells[minidx][minidy])-1)]]

    return [minidx, minidy]

def hasFinished(cells):
    for idrow,i in enumerate(cells):
        for id, j in enumerate(cells[idrow]):
            if len(j)>1:
                return False
    return True

def hasError(cells):
    for idrow,i in enumerate(cells):
        for id, j in enumerate(cells[idrow]):
            if not j:
                return True
    return False

def imageFromCells(patterns, cells, n, size):
    outputImage = Image.new('RGB',(n*size,n*size),color=(128,128,128))
    for idrow,i in enumerate(cells):
        for id, j in enumerate(cells[idrow]):
            if j:
                pattern = patterns[j[0]]
                outputImage.paste(pattern, (idrow*n, id*n))
    return outputImage

def propagate(patterns:dict, cells:list, pos:list, dir:list):
    """
    Propagate change to other cells, reducing possibilites of their states. 
    """
    #print(f"Propagatin: {pos}, with dir: {dir}")
    #Update right neighbour
    nextposx = (pos[0]+dir[0])%len(cells)
    nextposy = (pos[1]+dir[1])%len(cells)
    haschanged = False
    if cells[pos[0]][pos[1]]:
        haschanged = validate(patterns, cells[pos[0]][pos[1]], cells[nextposx][nextposy], dir)
        
    if haschanged:
        propagate(patterns, cells, [nextposx,nextposy],[1,0])
        propagate(patterns, cells, [nextposx,nextposy],[-1,0])
        propagate(patterns, cells, [nextposx,nextposy],[0,1])
        propagate(patterns, cells, [nextposx,nextposy],[0,-1])
    else:
        return

def validate(patterns:dict, cellA:list, cellB:list, dir:list):
    """Removes all unavailable states from cellB looking from the perspective of cellA."""
    newcell = list()
    for j in cellB:
        for i in cellA:
            newpatterns=patternsFromImages(patterns[j],patterns[i],dir)
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

def WFC(filename:str, n:int, outputCellCount:int):
    patterns = createPatternsFromFile(filename,n)
    cells = initializeCells(patterns, outputCellCount)
    try:
        k=0
        
        while True:
            cellscopy = copy.deepcopy(cells)
            if hasError(cellscopy):
                print("Copy error?")

            pos=observe(patterns, cells)
            propagate(patterns,cells,pos,[1,0])
            propagate(patterns,cells,pos,[-1,0])
            propagate(patterns,cells,pos,[0,1])
            propagate(patterns,cells,pos,[0,-1])

            if hasError(cells):
                #print("ERRORED")
                cells = copy.deepcopy(cellscopy)
                continue

            imageFromCells(patterns,cells,n,outputCellCount).save(os.path.join(DIR_OUTPUT,f"frame{k}.png"))
            k=k+1

            if hasFinished(cells):
                imageFromCells(patterns,cells,n,outputCellCount).show()
                return 
    except:
        print("Found exception: \n-----------")
        print(DataFrame(cells))
        imageFromCells(patterns,cells,n,outputCellCount).save(os.path.join(DIR_OUTPUT,f"EXCEPTION.png"))
        

initWorkspace()
WFC("input3.png",2,8)



