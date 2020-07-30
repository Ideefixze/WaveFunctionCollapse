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
DIR_INPUT = os.path.join(DIR,"input")
ROTATIONS = False
PROP_ID = 0

def cellsDirs(pos, size):

    x, y = pos
    width, height = size
    dirs = []

    if x > 0: dirs.append([-1,0])
    if x < width-1: dirs.append([1,0])
    if y > 0: dirs.append([0,-1])
    if y < height-1: dirs.append([0,1])

    return dirs

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

def createPatternsFromImages(img1:Image, img2:Image, dir:list):
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
                    pattern = pattern.rotate(90)
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
                        pattern = pattern.rotate(90)
                        key = imgHash(pattern)
                        patterns.setdefault(key,0)
                        patterns[key] = pattern.copy()
            return patterns
    return []

def createPatternsFromImage(imgsrc:Image, N:int):
    """
    Creates NxN patterns from image with given filename. Returns a dict (k,v) where k = hash of img, v = img.
    """
    patterns = dict()
    imgwrap = crop(imgsrc,0,0,imgsrc.width,imgsrc.height)

    img = Image.new('RGB', (imgsrc.width + N, imgsrc.height + N))
    #img = Image.new('RGB', (imgsrc.width, imgsrc.height))
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
            #pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
            key = imgHash(pattern)
            patterns.setdefault(key,0)
            patterns[key] = pattern.copy()
            #print(f"----- {imgHash(patterns[key])} ------ {key}")
            if ROTATIONS:
                for i in range(1,4):
                    pattern = pattern.rotate(90)
                    key = f"pat_{x}_{y}_r{i}"
                    #pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
                    key = imgHash(pattern)
                    patterns.setdefault(key,0)
                    patterns[key] = pattern.copy()
    for i,pattern in enumerate(patterns.values(),0):
        pattern.save(os.path.join(DIR_OUTPUT,f"pattern_{i}.png"))
    #print(patterns)
    #img.show()
    return patterns

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
                    pattern = pattern.rotate(90)
                    key = f"pat_{x}_{y}_r{i}"
                    #pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
                    key = imgHash(pattern)
                    patterns.setdefault(key,0)
                    patterns[key] = pattern.copy()

    #print(patterns)
    #img.show()
    return patterns


class WFC2D:
    def __init__(self, inputimg:Image, N:int, cellCount:int):
        self.inputimg = inputimg
        self.N = N
        self.cellCount = cellCount
        self.__initPatterns()
        self.__initConstrains()
        self.__initCells()

    def __initPatterns(self):
        self.patterns = createPatternsFromImage(self.inputimg, self.N)
        print(f"Finished initing patterns. Total number of patterns: {len(self.patterns)}")

    def __initCells(self):
        """
        Makes every cell a superposition of all possible states.
        """
        self.cells = list()
        for i in range(self.cellCount):
            cellrow = list()
            for j in range(self.cellCount):
                cell = list()
                for key in self.patterns.keys():
                    cell.append(key)
                cellrow.append(cell)
            self.cells.append(cellrow)
        
        print(f"Finished initing cells.")

    def __observe(self):
        """
        Selects cell with minimal entropy and chooses a state randomly.
        """
        min = len(self.patterns)+1
        minidx = -1
        minidy = -1
        for idrow,i in enumerate(self.cells):
            for id, j in enumerate(self.cells[idrow]):
                if len(j)>1:
                    if(len(j)<min):
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
        if minidx == -1:
            return False

        self.cells[minidx][minidy] = [self.cells[minidx][minidy][random.randint(0,len(self.cells[minidx][minidy])-1)]]

        return [minidx, minidy]

    def imageFromCells(self):
        outputImage = Image.new('RGB',(self.N*self.cellCount,self.N*self.cellCount),color=(128,128,128))
        for idrow,i in enumerate(self.cells):
            for id, j in enumerate(self.cells[idrow]):
                if j:
                    pattern = self.patterns[j[0]]
                    outputImage.paste(pattern, (idrow*self.N, id*self.N))
        return outputImage

    def __initConstrains(self):
        self.constrains = list()
        for keyi,itemi in self.patterns.items():
            for keyj,itemj in self.patterns.items():
                foundpatterns = createPatternsFromImages(itemi, itemj, [1,0])
                if set(foundpatterns)<=set(self.patterns.keys()):
                    self.constrains.append([keyi,keyj, [1,0]])

                foundpatterns = createPatternsFromImages(itemi, itemj, [-1,0])
                if set(foundpatterns)<=set(self.patterns.keys()):
                    self.constrains.append([keyi,keyj, [-1,0]])

                foundpatterns = createPatternsFromImages(itemi, itemj, [0,1])
                if set(foundpatterns)<=set(self.patterns.keys()):
                    self.constrains.append([keyi,keyj, [0,1]])

                foundpatterns = createPatternsFromImages(itemi, itemj, [0,-1])
                if set(foundpatterns)<=set(self.patterns.keys()):
                    self.constrains.append([keyi,keyj, [0,-1]])

        print(f"Finished calculating constrains. Total number of constrains: {len(self.constrains)}")

    def __propagate(self, pos:list, dir:list):
        global PROP_ID
        """
        Propagate change to other cells, reducing possibilites of their states. 
        """
        #print(f"Propagatin: {pos}, with dir: {dir}")
        #Update right neighbour
        nextposx = (pos[0]+dir[0])%len(self.cells)
        nextposy = (pos[1]+dir[1])%len(self.cells)
        haschanged = False
        if self.cells[pos[0]][pos[1]]:
            haschanged = self.__validate(self.cells[pos[0]][pos[1]], self.cells[nextposx][nextposy], dir)
            
        if haschanged:
            #self.imageFromCells().save(os.path.join(DIR_OUTPUT,f"prop{PROP_ID}.png"))
            PROP_ID+=1
            self.__propagate([nextposx,nextposy],[1,0])
            self.__propagate([nextposx,nextposy],[-1,0])
            self.__propagate([nextposx,nextposy],[0,1])
            self.__propagate([nextposx,nextposy],[0,-1])
        else:
            return

    def __stackpropagate(self, pos:list):
        stack = [pos]

        while len(stack)>0:
            currentpos=stack.pop()
            for dir in cellsDirs(currentpos,[self.cellCount,self.cellCount]):
                nextposx = (currentpos[0]+dir[0])%len(self.cells)
                nextposy = (currentpos[1]+dir[1])%len(self.cells)
                haschanged = False
                if self.cells[currentpos[0]][currentpos[1]]:
                    haschanged = self.__validate(self.cells[currentpos[0]][currentpos[1]], self.cells[nextposx][nextposy], dir)


                if haschanged:
                    stack.append((nextposx,nextposy))

    def __validate(self, cellA:list, cellB:list, dir:list):
        """Removes all unavailable states from cellB looking from the perspective of cellA."""
        newcell = list()
        for j in cellB:
            for i in cellA:
                if [i,j, dir] in self.constrains:
                    if j not in newcell:
                        newcell.append(j)
                    break   

        haschanged = collections.Counter(cellB) != collections.Counter(newcell)
        cellB[:]=newcell
        return haschanged

    def __hasError(self):
        for idrow, i in enumerate(self.cells):
            for id, j in enumerate(self.cells[idrow]):
                if not j:
                    return True
        return False

    def generate(self):
        try:
            k=0
            while True:
                if k%1==0:
                    self.imageFromCells().save(os.path.join(DIR_OUTPUT,f"frame{k}.png"))
                k=k+1

                cellscopy = copy.deepcopy(self.cells)

                pos=self.__observe()
                if pos==False:
                    break

                self.__stackpropagate(pos)
                
                if k>self.cellCount*self.cellCount*2:
                    print("Possible deadlock! Restarting...")
                    initWorkspace()
                    self.__reset()
                    self.generate()
                    return

                if self.hasError():
                    self.cells = copy.deepcopy(cellscopy)
                    continue
                
        except:
            print("Found exception: \n")
            print(DataFrame(self.cells))
            self.imageFromCells().save(os.path.join(DIR_OUTPUT,f"EXCEPTION.png"))
            raise

        self.imageFromCells().show()

    def hasError(self):
        for idrow,i in enumerate(self.cells):
            for id, j in enumerate(self.cells[idrow]):
                if not j:
                    return True
        return False

    def __reset(self):
        self.__initPatterns()
        self.__initConstrains()
        self.__initCells()
        

initWorkspace()

wfc = WFC2D(Image.open(os.path.join(DIR_INPUT,"input3.png")), 2, 10)
wfc.generate()

