import os
import random
import collections
from PIL import Image, ImageChops, ImageDraw, ImageSequence, ImagePalette
import pathlib
import glob
import hashlib
from pandas import *
import copy
import cProfile
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as animation
import numpy
import math
import calendar
import time

DIR=str(pathlib.Path(__file__).parent.absolute())
DIR_OUTPUT = os.path.join(DIR,"output")
DIR_INPUT = os.path.join(DIR,"input")
ROTATIONS = False

def cellsDirs(pos, size):
    """
    Returns all possible directions in a position within a 2D array of given size.
    """
    x, y = pos
    width, height = size
    dirs = []

    if x > 0: dirs.append([-1,0])
    if x < width-1: dirs.append([1,0])
    if y > 0: dirs.append([0,-1])
    if y < height-1: dirs.append([0,1])

    return dirs

def cellsDirsNoPos():
    """
    Returns all possible directions.
    """
    dirs = []
    dirs.append([-1,0])
    dirs.append([1,0])
    dirs.append([0,-1])
    dirs.append([0,1])

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

def smart_get_concat(im1,im2,dir):
    if dir[0]!=0:
        return get_concat_h(im1,im2)
    else:
        return get_concat_v(im1,im2)

def createPatternsFromImages(img1:Image, img2:Image, dir:list):
    """
    Returns all patterns created from concatenation of two images with given direction.
    """
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

def createPatternsFromImage(imgsrc:Image, N:int):
    """
    Creates NxN patterns from image with given filename. Returns a dict (k,v) where k = hash of img, v = img.
    """
    patterns = dict()
    imgwrap = crop(imgsrc,0,0,imgsrc.width,imgsrc.height)

    img = Image.new('RGB', (imgsrc.width+N, imgsrc.height+N))
    img.paste(imgsrc,(0,0))
    img.paste(imgwrap,(0,imgsrc.height))
    img.paste(imgwrap,(imgsrc.width,0))
    img.paste(imgwrap,(imgsrc.width,imgsrc.height))

    for x in range(img.size[0]-N):
        for y in range(img.size[1]-N):
            pattern = crop(img, x, y,N,N)
            key = f"pat_{x}_{y}_r{0}"
            key = imgHash(pattern)
            patterns.setdefault(key,0)
            patterns[key] = pattern.copy()
            if ROTATIONS:
                for i in range(1,4):
                    pattern = pattern.rotate(90)
                    key = f"pat_{x}_{y}_r{i}"
                    key = imgHash(pattern)
                    patterns.setdefault(key,0)
                    patterns[key] = pattern.copy()
    
    return patterns


class WFC2D:
    def __init__(self, inputimg:Image, N:int, cellCount:int):
        self.inputimg = inputimg
        self.N = N
        self.cellCount = cellCount
        self.__initPatterns(show=True)
        self.__initConstraints(show=False)
        self.__initCells()
        self.animation_frames_plt = list()
        self.animation_frames_gif = list()

    def __initPatterns(self,show=True):
        self.patterns = createPatternsFromImage(self.inputimg, self.N)
        print(f"Finished initing patterns. Total number of patterns: {len(self.patterns)}")
        
        #Makes simple patterns plot.
        if not show:
            return
        s = math.sqrt(len(self.patterns))+1
        fig = plt.figure(figsize=(self.N*4,self.N*4))
        for i,pattern in enumerate(self.patterns.values(),1):
            fig.add_subplot(s,s,i)
            plt.axis('off')
            plt.imshow(pattern)
        fig.canvas.set_window_title('Patterns')
        plt.show()
        plt.close()

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
                    val = len(j)
                    if(val<min):
                        minidx = idrow
                        minidy = id
                        min = val

        #Random one of possible choices at cell with minimal entropy
        #Possible change: random distribution using number of patterns that appeared in input
        
        if minidx == -1:
            return False

        self.cells[minidx][minidy] = [self.cells[minidx][minidy][random.randint(0,len(self.cells[minidx][minidy])-1)]]
        
        return [minidx, minidy]

    def imageFromCells(self):
        """
        Creates image from cells. Each cell has a list of possible patterns, if it's length is 1, then it means it is collapsed and we can
        map it to our patterns to create one unique image.
        """
        outputImage = Image.new('RGB',(self.N*self.cellCount,self.N*self.cellCount),color=(128,128,128))
        for idrow,i in enumerate(self.cells):
            for id, j in enumerate(self.cells[idrow]):
                if len(j):
                    pattern = self.patterns[j[0]]
                    outputImage.paste(pattern, (idrow*self.N, id*self.N))
        return outputImage


    def __initConstraints(self,show=True):
        self.constraints = list()
        for keyi,itemi in self.patterns.items():
            for keyj,itemj in self.patterns.items():
                for dir in cellsDirsNoPos():
                    foundpatterns = createPatternsFromImages(itemi, itemj, dir)
                    if set(foundpatterns)<=set(self.patterns.keys()):
                        self.constraints.append([keyi,keyj, dir])

        print(f"Finished calculating constraints. Total number of constraints: {len(self.constraints)}")

        #Makes a simple constraints plots.
        if not show:
            return
        fig = plt.figure(figsize=(self.N*4,self.N*4))
        s = math.sqrt(len(self.constraints))+1
        for i,c in enumerate(self.constraints,1):
            fig.add_subplot(s,s,i)
            plt.axis('off')
            im = smart_get_concat(self.patterns[c[0]],self.patterns[c[1]],c[2])

            plt.imshow(im)
        fig.canvas.set_window_title('Constraints')
        plt.show()
        plt.close()


    def __stackpropagate(self, pos:list):
        """Propagates constraint information to all neighbours. Repeat until no changes"""
        stack = [pos]

        while len(stack)>0:
            current_pos=stack.pop()
            for dir in cellsDirs(current_pos,[self.cellCount,self.cellCount]):
                next_pos_x = (current_pos[0]+dir[0])
                next_pos_y = (current_pos[1]+dir[1])

                for tile in set(self.cells[next_pos_x][next_pos_y]):
                    #Check if any combinations match with constraints for a given tile
                    possible_tile = any([cur_tile,tile,dir] in self.constraints for cur_tile in self.cells[current_pos[0]][current_pos[1]])

                    #If not, this tile is invalid, remove it and propagate information to the neighbours
                    if not possible_tile:
                        self.cells[next_pos_x][next_pos_y].remove(tile)
                        if [next_pos_x, next_pos_y] not in stack:
                            stack.append([next_pos_x,next_pos_y])

    def __hasError(self):
        for idrow, i in enumerate(self.cells):
            for id, j in enumerate(self.cells[idrow]):
                if not j:
                    return True
        return False

    def generate(self):
        fig = plt.figure()
        fig.canvas.set_window_title("Output")
        try:
            k=0
            while True:
                im = self.imageFromCells()
                #Copy current frame into plt and gif list
                #matplotlib forces you to specify ffmpeg libs
                #PILLOW can create gifs automatically, so we use it
                #to make things easier.
                self.animation_frames_plt.append([plt.imshow(im,animated=True)])
                self.animation_frames_gif.append(im.convert('P',palette=Image.ADAPTIVE))
                k=k+1

                cells_copy = copy.deepcopy(self.cells)

                pos=self.__observe()
                if pos==False:
                    break
                self.__stackpropagate(pos)
                
                if k>self.cellCount*self.cellCount*4:
                    print("Possible error: deadlock. Restart program or change input.")
                    self.__reset()
                    return

                if self.__hasError():
                    self.cells = copy.deepcopy(cells_copy)
                    continue

                
        except:
            print("Found exception: \n")
            print(DataFrame(self.cells))
            self.imageFromCells().save(os.path.join(DIR_OUTPUT,f"EXCEPTION.png"))
            raise
        
        
        ani = animation.ArtistAnimation(fig,self.animation_frames_plt,interval=50,repeat=False)
        self.animation_frames_gif[0].save(os.path.join(DIR_OUTPUT,"out.gif"),format='GIF',save_all=True,append_images=self.animation_frames_gif[1:],duration=20,loop=0)
        plt.show()

    def __reset(self):
        print("Reseting data...")
        self.__initCells()
        self.animation_frames_plt=list()
        self.animation_frames_gif=list()
        
if __name__ == "__main__":
    initWorkspace()
    print("Input filename (only .png images files from input folder):")
    fname = input()
    print("N parameter for NxN patterns:")
    n = int(input())
    print("Number of cells (with NxN size) that will make CxC image:")
    c = int(input())
    wfc = WFC2D(Image.open(os.path.join(DIR_INPUT,fname)), n, c)
    wfc.generate()



