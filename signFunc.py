import sys
import os
import subprocess
import string

from math import floor,ceil,sqrt
from shutil import rmtree
from fontTools.ttLib import TTFont
from PIL import Image

def distSq(d):
    return (d[0]*d[0]) + (d[1]*d[1])

def dist(d):
    return sqrt(distSq(d))

def get(grid, pos):
    empty = (9999.0, 9999.0)
    if pos[0] >= 0 and pos[0] < len(grid) and pos[1] >= 0 and pos[1] < len(grid[0]):
        return grid[pos[0]][pos[1]]
    else:
        return empty

def compare(grid, point, pos, offset):
    other = get(grid, (pos[0]+offset[0], pos[1]+offset[1]))
    other = (other[0]+offset[0], other[1]+offset[1])
    if distSq(other) < distSq(point):
        point = other
    return point

def generateSDF(grid):
    # Pass 0
    for y in range(len(grid[0])):
        for x in range(len(grid)):
            p = get(grid, (x,y))
            p = compare(grid, p, (x,y), (-1, 0))
            p = compare(grid, p, (x,y), ( 0,-1))
            p = compare(grid, p, (x,y), (-1,-1))
            p = compare(grid, p, (x,y), ( 1,-1))
            grid[x][y] = p
        for x in reversed(range(len(grid))):
            p = get(grid, (x,y))
            p = compare(grid, p, (x,y), ( 1, 0))
            grid[x][y] = p

    # Pass 1
    for y in reversed(range(len(grid[0]))):
        for x in reversed(range(len(grid))):
            p = get(grid, (x,y))
            p = compare(grid, p, (x,y), ( 1, 0))
            p = compare(grid, p, (x,y), ( 0, 1))
            p = compare(grid, p, (x,y), (-1, 1))
            p = compare(grid, p, (x,y), ( 1, 1))
            grid[x][y] = p
        for x in range(len(grid)):
            p = get(grid, (x,y))
            p = compare(grid, p, (x,y), (-1, 0))
            grid[x][y] = p

    return grid


def imageSDF(image, filename):
    inside = (0.0,0.0)
    empty = (9999.0, 9999.0)

    grid1 = [[None] * image.height for _ in range(image.width)]
    grid2 = [[None] * image.height for _ in range(image.width)]
    image = image.convert('L')

    for y in range(image.height):
        for x in range(image.width):
            value = image.getpixel((x,y))
            if value < 127:
                grid1[x][y] = inside
                grid2[x][y] = empty
            else:
                grid1[x][y] = empty
                grid2[x][y] = inside

    grid1 = generateSDF(grid1)
    grid2 = generateSDF(grid2)

    sdfImage = Image.new('L', image.size)
    sdf = sdfImage.load()

    for y in range(image.height):
        for x in range(image.width):
            p1 = get(grid1, (x,y))
            p2 = get(grid2, (x,y))
            d1 = dist(p1)
            d2 = dist(p2)
            d3 = int(d1 - d2)

            c = d3*6 + 128
            if c > 255:
                c = 255
            elif c < 0:
                c = 0
            # sdfImage.putpixel((x,y), c)
            sdf[x,y] = c

    sdfImage.save(filename + '.png')
    sdfImage.close()


def has_glyph(font, glyph):
    for table in font['cmap'].tables:
        if ord(glyph) in table.cmap.keys():
            return True
    return False

def gen_glyphs(filename, TEXTS_DIR, IMAGES_DIR, FONT_SIZE, TTF_PATH, size):
    print(".",end="",flush=True)
    name, ext = os.path.splitext(filename)
    input_txt = TEXTS_DIR + "/" + filename
    name_adjusted = str("{:08d}".format(int(name)))
    output_png = IMAGES_DIR + "/" + name_adjusted + ".png"
    subprocess.call(["convert", "-quiet", "-background", "black", "-size", size, "-gravity", "center", "-font", TTF_PATH, "-pointsize", FONT_SIZE, "-fill", "white", "-trim", "+repage", "-bordercolor", "black", "-border", "64", "label:@" + input_txt, output_png])

def gen_SDF(filename, IMAGES_DIR, SDF_DIR, SDF_DIR_SMALL):
    print(".",end="",flush=True)
    image = Image.open(IMAGES_DIR + "/" + filename)
    name, ext = os.path.splitext(filename)
    imageSDF(image, SDF_DIR + "/" + name)
    image.close()
    subprocess.call(["convert", "-quiet", SDF_DIR + "/" + name + ".png", "-resize", "50%", "-trim", "+repage", SDF_DIR_SMALL + "/" + "small_" + name + ".png"])
    image.close()
