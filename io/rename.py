#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os


EXT_FILTERS = [".mp4", ".m3u8"] # we should not rename .ts file, whose name is included by m3u8
FB_FILTERS = ["Factory Farms",
              "Gatorade   360° Bryce Harper Virtual Reality Experience",
              "空客A380豪华VR体验",
              "The Hidden Worlds of the National Parks 360° VR Video",
              ]

FN_FILTERS = [fn + "_360x180_cube_lr" for fn in FB_FILTERS]


def rename(base_dir):
    for parent, dn, ffns in os.walk(base_dir):
        for ffn in ffns:
            fn, fext = os.path.splitext(ffn)
            if fext not in EXT_FILTERS:
                continue
            if fn not in FN_FILTERS:
                continue
            fb = FB_FILTERS[FN_FILTERS.index(fn)]
            src = os.path.join(parent, ffn)
            dst = os.path.join(parent, fb + "_360x180_cube_mono" + fext)
            os.rename(src, dst)

