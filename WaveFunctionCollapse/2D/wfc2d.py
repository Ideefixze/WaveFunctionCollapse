import os
import random
import collections
from PIL import Image, ImageChops, ImageDraw, ImageSequence
import pathlib
import glob
import hashlib

DIR=str(pathlib.Path(__file__).parent.absolute())
DIR_OUTPUT = os.path.join(DIR,"output")

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

def createPatternsFromFile(filename:str, N:int, rotations:bool):
    """
    Creates NxN patterns from image with given filename. Returns a dict (k,v) where k = hash of img, v = img.
    """
    patterns = dict()
    img = Image.open(os.path.join(DIR,"input",filename)).convert('RGB')
    for x in range(img.size[0] - N):
        for y in range(img.size[1]):
            pattern = crop(img, x, y,N,N)
            key = f"pat_{x}_{y}_r{0}"
            pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
            key = imgHash(pattern)
            patterns.setdefault(key,0)
            patterns[key] = pattern.copy()
            #print(f"----- {imgHash(patterns[key])} ------ {key}")

            if rotations:
                for i in range(1,4):
                    pattern.rotate(90)
                    key = f"pat_{x}_{y}_r{i}"
                    pattern.save(fp=os.path.join(DIR_OUTPUT,key+".png"))
                    key = imgHash(pattern)
                    patterns.setdefault(key,0)
                    patterns[key] = pattern.copy()

    #print(patterns)
    #img.show()


initWorkspace()
createPatternsFromFile("input2.png",2,True)