# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

from PIL import Image
import os


class Photo(object):

    def __init__(self, src="", dst=""):
        self.src = src
        self.dst = dst

        if self.src and os.path.isfile(self.src) and os.path.exists(self.src):
            pass
        else:
            raise Exception("image file not exist")
        if self.dst and not os.path.isdir(self.dst) and not os.path.exists(self.dst):
            os.makedirs(self.dst)

    @property
    def basename(self):
        return os.path.splitext(os.path.basename(self.src))[0]

    @property
    def ext(self):
        return os.path.splitext(os.path.basename(self.src))[1]

    @property
    def path(self):
        return os.path.dirname(os.path.abspath(__file__))


class Image_BinoToMono(Photo):
    """
    description:
    crop a binocular image into a monocular
    """
    ROW = 2
    COL = 2

    def __init__(self, layout="lr", **kwargs):
        Photo.__init__(self, **kwargs)

        self.layout = layout

    def crop(self):
        basename = self.basename
        img = Image.open(self.src)
        if self.layout.upper() == "LR":
            rowheight = img.height
            colwidth = img.width // Image_BinoToMono.COL
        elif self.layout.upper() == "TB":
            rowheight = img.height //Image_BinoToMono.ROW
            colwidth = img.width
        else:
            raise Exception("Image layout error")

        # (left, upper, right, lower).
        # uses a coordinate system with (0, 0) in the upper left corner
        box = (0, 0, colwidth, rowheight)
        part = img.crop(box)
        part.load()

        _img = Image.new(img.mode, size=(colwidth, rowheight))
        _img.paste(part, (0, 0, colwidth, rowheight))

        if basename.endswith("_lr") or basename.endswith("_tb"):
            basename = basename[:-3]

        _img.save(os.path.join(self.dst, basename + "_mono" + self.ext), "JPEG", )


class Image_Crop(Photo):
    """
    description:
    crop a 8K image into some special child images
    origin:
        1.cube_lr image
        2.cube_mono image
    output:
        1.three 3840x3840 cube_lr images and three 1920x3840 cube_mono images
        2.three 1920x3840 cube_mono images
    1.cube_lr
    rol 3   5730//3=1920
    col 4   7680//4=1920
    --c0---c1---c2---c3-- 7680
    |    |    |    |    |
    r0 0 |  1 |  2 |  3 |
    |    |    |    |    |
    ---------------------
    |    |    |    |    |
    r1 4 |  5 |  6 |  7 |
    |    |    |    |    |
    ---------------------
    |    |    |    |    |
    r2 8 |  9 | 10 | 11 |
    |    |    |    |    |
    ---------------------
   5760

   image 1:ub--up and bottom
   -------------------
   | 上左(1) | 上右(3) |
   ---------------
   | 下左(9) | 下右(11)|
   -------------------
   image 2:fb--front and back
   -------------------
   | 前左(4) | 前右(6) |
   ---------------
   | 后左(5) | 后右(7)|
   -------------------
   image 3:lr--left and right
   -------------------
   | 左左(0) | 左右(2) |
   ---------------
   | 右左(8) | 右右(10)|
   -------------------
    """
    ROW = 3
    COL = 4

    def __init__(self, binocular=True, **kwargs):
        Photo.__init__(self, **kwargs)

        self.binocular = binocular

    def crop(self):
        series = []
        img = Image.open(self.src)
        basename = self.basename
        if self.binocular:
            Image_Crop.COL = 4
        else:
            Image_Crop.COL = 2
        rowheight = img.height // Image_Crop.ROW
        colwidth = img.width // Image_Crop.COL

        for r in range(Image_Crop.ROW):
            for c in range(Image_Crop.COL):
                # (left, upper, right, lower).
                # uses a coordinate system with (0, 0) in the upper left corner
                box = (c * colwidth, r * rowheight, (c + 1) * colwidth, (r + 1) * rowheight)
                part = img.crop(box)
                part.load()
                series.append(part)

        if self.binocular:
            if basename.endswith("_lr"):
                basename = basename[:-3]

            # 1 LR
            _img1 = Image.new(img.mode, size=(colwidth * 2, rowheight * 2))
            # 1.1 up and bottom
            _img1.paste(series[1],  (0,        0,         colwidth,     rowheight))
            _img1.paste(series[3],  (colwidth, 0,         2 * colwidth, rowheight))
            _img1.paste(series[9],  (0,        rowheight, colwidth,     2 * rowheight))
            _img1.paste(series[11], (colwidth, rowheight, 2 * colwidth, 2 * rowheight))
            _ud1 = _img1.resize(size=(3840, 3840), resample=Image.LANCZOS)
            _ud1.save(os.path.join(self.dst, basename + "_lr-ub" + self.ext), "JPEG", )

            # 1.2 front and back
            _img1.paste(series[4], (0,        0,         colwidth,     rowheight))
            _img1.paste(series[6], (colwidth, 0,         2 * colwidth, rowheight))
            _img1.paste(series[5], (0,        rowheight, colwidth,     2 * rowheight))
            _img1.paste(series[7], (colwidth, rowheight, 2 * colwidth, 2 * rowheight))
            _fb1 = _img1.resize(size=(3840, 3840), resample=Image.LANCZOS)
            _fb1.save(os.path.join(self.dst, basename + "_lr-fb" + self.ext), "JPEG")

            # 1.3 left and right
            _img1.paste(series[0],  (0,        0,         colwidth,     rowheight))
            _img1.paste(series[2],  (colwidth, 0,         2 * colwidth, rowheight))
            _img1.paste(series[8],  (0,        rowheight, colwidth,     2 * rowheight))
            _img1.paste(series[10], (colwidth, rowheight, 2 * colwidth, 2 * rowheight))
            _lr1 = _img1.resize(size=(3840, 3840), resample=Image.LANCZOS)
            _lr1.save(os.path.join(self.dst, basename + "_lr-lr" + self.ext), "JPEG")

            # 2 MONO
            _img2 = Image.new(img.mode, size=(colwidth, rowheight * 2))
            # 2.1 up and bottom
            _img2.paste(series[1], (0, 0, colwidth, rowheight))
            _img2.paste(series[9], (0, rowheight, colwidth, 2 * rowheight))
            _ud2 = _img2.resize(size=(1920, 3840), resample=Image.LANCZOS)
            _ud2.save(os.path.join(self.dst, basename + "_mono-ub" + self.ext), "JPEG", )

            # 2.2 front and back
            _img2.paste(series[4], (0, 0, colwidth, rowheight))
            _img2.paste(series[5], (0, rowheight, colwidth, 2 * rowheight))
            _fb2 = _img2.resize(size=(1920, 3840), resample=Image.LANCZOS)
            _fb2.save(os.path.join(self.dst, basename + "_mono-fb" + self.ext), "JPEG")

            # 2.3 left and right
            _img2.paste(series[0], (0, 0, colwidth, rowheight))
            _img2.paste(series[8], (0, rowheight, colwidth, 2 * rowheight))
            _lr2 = _img2.resize(size=(1920, 3840), resample=Image.LANCZOS)
            _lr2.save(os.path.join(self.dst, basename + "_mono-lr" + self.ext), "JPEG")
        else:
            if basename.endswith("_mono"):
                basename = basename[:-5]

            _img = Image.new(img.mode, size=(colwidth, rowheight * 2))
            # MONO
            # 1 up and bottom
            _img.paste(series[1], (0, 0, colwidth, rowheight))
            _img.paste(series[5], (0, rowheight, colwidth, 2 * rowheight))
            _ud = _img.resize(size=(1920, 3840), resample=Image.LANCZOS)
            _ud.save(os.path.join(self.dst, basename + "_mono-ub" + self.ext), "JPEG", )

            # 2 front and back
            _img.paste(series[2], (0, 0, colwidth, rowheight))
            _img.paste(series[3], (0, rowheight, colwidth, 2 * rowheight))
            _fb = _img.resize(size=(1920, 3840), resample=Image.LANCZOS)
            _fb.save(os.path.join(self.dst, basename + "_mono-fb" + self.ext), "JPEG")

            # 3 left and right
            _img.paste(series[0], (0, 0, colwidth, rowheight))
            _img.paste(series[4], (0, rowheight, colwidth, 2 * rowheight))

            _lr = _img.resize(size=(1920, 3840), resample=Image.LANCZOS)
            _lr.save(os.path.join(self.dst, basename + "_mono-lr" + self.ext), "JPEG")


if __name__ == "__main__":
    # crop = Image_Crop(src="images/temple01_360x180_cube_lr.jpg", dst="output")
    # crop.crop()
    crop = Image_BinoToMono(src="images/crossroad_8kX8K_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/hk1881_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/hkcentral_8kX8K_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/hkstar_walk_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/hkvictoria_harbour_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/japan07_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/japan08_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/japan10_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/temple01_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/temple02_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    crop = Image_BinoToMono(src="images/tsimshatusi_8kX8K_360x180_cube_lr.jpg", layout="lr", dst="images")
    crop.crop()
    # crop = Image_Crop(src="output/temple01_360x180_cube_mono.jpg", binocular=False, dst="output")
    # crop.crop()


