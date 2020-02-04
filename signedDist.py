import unicodedata
from signFunc import *
import multiprocessing as mp

print("Number of processors: ", mp.cpu_count())

pool = mp.Pool(mp.cpu_count())

TEXTS_DIR = "texts"
IMAGES_DIR = "images"
SDF_DIR = "sdf_images"
SDF_DIR_SMALL = "sdf_images_small"

TTF_PATH = sys.argv[1]
FONT_SIZE = sys.argv[2]
TTF_NAME, TTF_EXT = os.path.splitext(os.path.basename(TTF_PATH))

ttf = TTFont(TTF_PATH, 0,\
             allowVID = 0, ignoreDecompileErrors = True, fontNumber = 0)

ttf.saveXML(TTF_NAME + ".ttx")

for d in [TEXTS_DIR, IMAGES_DIR, SDF_DIR, SDF_DIR_SMALL]:
    if not os.path.isdir(d):
        os.mkdir(d)

numTables = 0
fontNumber = 0

print("Generating txt",end="",flush=True)

cmap = ttf['cmap']
for y in cmap.getBestCmap().items():
    char_unicode = chr(y[0])
    char_name = y[1]
    if y[0] > 0x1f and y[0] < 0xff and has_glyph(ttf, char_unicode):
        f = open(os.path.join(TEXTS_DIR, str(y[0]) + '.txt'), 'w')
        fontNumber += 1
        f.write(char_unicode)
        f.close()
        print(".",end="",flush=True)

print("Done\n")
print(fontNumber, "Glyphs\n")

info = open(TTF_NAME + "_info.plist", 'w')

info.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>Spacing</key>\n''')

hasKern = False
try:
    kern = ttf['kern']
    hasKern = True
except:
    print("This font does not contain a Kerning Table")

# Ascenders and Descenders
try:
    glyf = ttf['glyf']
    head = ttf['head']
    hmtx = ttf['hmtx'].metrics
    # vmtx = ttf['vmtx'] if 'vmtx' in ttf else None
    unitsPerEm = head.unitsPerEm
    i = 0

    info.write("<array>\n")
    for name in cmap.getBestCmap().items():
        if name[0] > 0x1f and name[0] < 0xff and has_glyph(ttf, chr(name[0])):
            info.write("<dict>\n")
            g = glyf[name[1]]
            adv = hmtx[name[1]]
            id = name[0]
            info.write("<key>ID</key>\n" + "<integer>" + str(id) + "</integer>")
            if hasattr(g, "yMax"):
                ascender = float(FONT_SIZE) * g.yMax / (2*unitsPerEm)
                print(str(id) + "\t" + chr(name[0]) + "\tAscender: " + str("{:+03.04f}".format(ascender)),end="\t")
                info.write("<key>Ascender</key>\n" + "<real>" + str(ascender) + "</real>\n")
            else:
                print(str(id) + "\t" + chr(name[0]) + "\tAscender: 000.0000",end="\t")
                info.write("<key>Ascender</key>\n<real>0.0</real>\n")
            if hasattr(g, "yMin"):
                descender = float(FONT_SIZE) * g.yMin / (2*unitsPerEm)
                print("Descender: " + str("{:+03.04f}".format(descender)), end="\t")
                info.write("<key>Descender</key>\n" + "<real>" + str(descender) + "</real>\n")
            else:
                print("Descender: 000.0000", end="\t")
                info.write("<key>Descender</key>\n<real>0.0</real>\n")
            if adv != None:
                width = float(FONT_SIZE) * (adv[0]) / (2*unitsPerEm)
                print("Width: " + str("{:+03.04f}".format(width)), end="\t")
                info.write("<key>Width</key>\n" + "<real>" + str(width) + "</real>\n")
            else:
                print("Width: 000.0000",end="\t")
                info.write("<key>Width</key>\n<real>0.0</real>\n")
            if adv[1] != None:
                lsb = float(FONT_SIZE) * (adv[1]) / (2*unitsPerEm)
                print("LSB: " + str("{:+03.04f}".format(lsb)),end="\t")
                info.write("<key>LSB</key>\n" + "<real>" + str(lsb) + "</real>\n")
            else:
                print("LSB: 000.0000",end="\t")
                info.write("<key>LSB</key>\n" + "<real>0.0</real>\n")

            print("Position: "+ str(i))
            info.write("<key>Position</key>\n" + "<integer>" + str(i) + "</integer>\n")
            i += 1

            info.write("<key>Kerning</key>\n")
            info.write("<dict>\n")

            try:
                if hasattr(ttf['kern'], 'kernTables'):
                    print("\t\tKerning:")
                    for other in cmap.getBestCmap().items():
                        if other[0] > 0x1f and other[0] <= 0xff:
                            kernTables = ttf['kern'].kernTables
                            left = chr(name[0])
                            right = chr(other[0])
                            for subtable in kernTables:
                                value = subtable.kernTable

                                try:
                                    key = float(FONT_SIZE) * (value[(left, right)]) / (2*unitsPerEm)
                                    print("\t\t\t("+str(left)+","+str(right)+"): " + str(key))
                                    info.write("<key>"+str(left)+","+str(right)+"</key>\n" + "<real>" + str(key) + "</real>\n")
                                except:
                                    print("",end="")
            except:
                pass

            info.write("</dict>\n")
            info.write("</dict>\n")

    info.write("</array>\n")
except:
    print("Could not get Tables\n")

files = os.listdir(TEXTS_DIR)
size = str(int(FONT_SIZE)*3) + "x" + str(int(FONT_SIZE)*3)

print("Generating glyphs",end="",flush=True)

[pool.apply_async(gen_glyphs, args=(filename, TEXTS_DIR, IMAGES_DIR, FONT_SIZE, TTF_PATH, size)) for filename in files]
pool.close()
pool.join()

print("Done\n")

images = []
files = os.listdir(IMAGES_DIR)

num_symbols = 0
max_width = 0
max_height = 0

width = 0
i = 0

pool = mp.Pool(mp.cpu_count())

print("Generating SDF Glyphs",end="",flush=True)

[pool.apply_async(gen_SDF, args=(filename, IMAGES_DIR, SDF_DIR, SDF_DIR_SMALL)) for filename in files]
pool.close()
pool.join()

print("Done\n")

for filename in files:
    name, ext = os.path.splitext(filename)
    image = Image.open(SDF_DIR_SMALL + "/" + "small_" + name + ".png")
    max_width = max(max_width, image.size[0])
    width += image.size[0]
    max_height = max(max_height, image.size[1])
    num_symbols += 1

num_cols = ceil(sqrt(num_symbols))
num_rows = floor(sqrt(num_symbols))
if num_cols * num_rows < num_symbols:
    num_rows += 1

# print(num_cols, num_rows)

# numColsRows = open(TTF_NAME + "_matrix.txt", 'w')
info.write("<key>Count</key>\n<dict>\n"+ "<key>Columns</key>\n" + "<integer>" + str(num_cols) + "</integer>\n" + "<key>Rows</key>\n" + "<integer>" + str(num_rows) + "</integer>\n</dict>")

advH = ttf['hhea'].lineGap
height = float(FONT_SIZE) * advH / (2*unitsPerEm)
info.write("<key>LineGap</key>\n<real>" + str(height) + "</real>\n")

info.write("</dict>\n</plist>")

ttf.close()

info.close()
print("Font Information exported to " + TTF_NAME + "_info.plist\n")

max_height += 5

final_image = Image.new('L', (max_width * num_cols, max_height * num_rows))

files = os.listdir(SDF_DIR_SMALL)
files.sort() # MUST SORT HERE TO CREATE ATLAS IN THE PROPER ORDER !!!

x_offset = 0
y_offset = 0
print("Generating Final Texture",end="",flush=True)
for filename in files:
    print(".",end="",flush=True)
    image = Image.open(SDF_DIR_SMALL + "/" + filename)
    if x_offset + image.size[0] > final_image.size[0]:
        x_offset = 0
        y_offset += int(max_height)

    image_offset = (0, int(max_height - image.height));
    final_image.paste(image, (int(x_offset + image_offset[0]),int(y_offset + image_offset[1])))
    x_offset += int(max_width)
    image.close()
print("Done\n")

final_image.save(TTF_NAME + '.png')
final_image.close()

rmtree(TEXTS_DIR)
rmtree(IMAGES_DIR)
rmtree(SDF_DIR)
rmtree(SDF_DIR_SMALL)

print("Font exported to PNG")
