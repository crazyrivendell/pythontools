# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import os
from settings import *
import platform
import subprocess
import multiprocessing

DEBUG = True

class Config(object):
    BASE_DIR = os.path.split(__file__)

    # Utils

    # system
    N_CPU = multiprocessing.cpu_count()
    PLATFORM = platform.system().upper()

    if platform.system().upper() == "WINDOWS":
        DEVICE_NULL = "NULL"
    else:
        DEVICE_NULL = "/dev/null"

    # email
    EMAIL_SENDER = "wml@kandaovr.com"
    EMAIL_DST = "wml@kandaovr.com"

    # EXECUTABLE check
    FFMPEG_EXECUTABLE = 'ffmpeg'
    FFPROBE_EXECUTABLE = 'ffprobe'
    ZIP_EXECUTABLE = '7z'

    if PLATFORM == "WINDOWS":
        FFMPEG_EXECUTABLE += ".exe"
        FFPROBE_EXECUTABLE += ".exe"
        ZIP_EXECUTABLE += ".exe"

    # check executable
    subprocess.check_output([FFMPEG_EXECUTABLE, "-h"], stderr=subprocess.STDOUT).decode("utf-8")
    subprocess.check_output([FFPROBE_EXECUTABLE, "-h"], stderr=subprocess.STDOUT).decode("utf-8")
    subprocess.check_output([ZIP_EXECUTABLE, "-h"], stderr=subprocess.STDOUT).decode("utf-8")

    def get_full_path(self, path):
        return os.path.join(Config.BASE_DIR, path)