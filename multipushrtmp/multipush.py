# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import os
import platform
import threading
import subprocess
import multiprocessing
from time import ctime


class MultiplePush(object):
    N_CPU = multiprocessing.cpu_count()
    FFMPEG = "ffmpeg"
    PLATFORM = platform.system().upper()
    if PLATFORM == "WINDOWS":
        FFMPEG += ".exe"

    # check executable
    subprocess.check_output([FFMPEG, "-h"], stderr=subprocess.STDOUT).decode("utf-8")

    def __init__(self):
        self.threads = []
        self.ffmpeg = MultiplePush.FFMPEG

    def push(self, src, dst, type="rtmp"):
        print("I was pushing  %s" % (ctime()))
        print('sub thread start!the thread name is:%s\r' % threading.currentThread().getName())
        if type == "rtmp":
            cmd = self.ffmpeg + " -re -i " + src + " -f flv " + dst
        else:
            raise Exception("push error: {type} not support".format(type=type))
        print(cmd)
        ret = os.system(cmd)
        if ret != 0:
            raise Exception("push error: {cmd} at {time}".format(cmd=cmd, time=ctime()))

    def run(self, params):
        i = 0
        for k in params:
            thread = threading.Thread(target=self.push, name="push_%d" % i, args=(k[0], k[1]))
            self.threads.append(thread)
            i += 1
            thread.setDaemon(True)
            thread.start()
        for t in self.threads:
            t.join()

#
#rtmp://live2.evideocloud.net/live/kandaovr
if __name__ =="__main__":
    dic = (
        ("/home/wuminlai/Work/media/offset_rtmp/bipbop_4x3/gear2/gear2_gop0.5.mp4",
        "rtmp://192.168.50.26:1935/live/demo1"),
        ("/home/wuminlai/Work/media/offset_rtmp/bipbop_4x3/gear3/gear3_gop0.5.mp4",
        "rtmp://192.168.50.26:1935/live/demo2"),
    )
    # dic = (
    #     ("/home/wuminlai/Work/media/offset_rtmp/bipbop_4x3/gear2/gear2_gop0.5.mp4",
    #      "rtmp://live2.evideocloud.net/live/kandaovr001"),
    #     ("/home/wuminlai/Work/media/offset_rtmp/bipbop_4x3/gear3/gear3_gop0.5.mp4",
    #      "rtmp://live2.evideocloud.net/live/kandaovr002"),
    # )
    multi_push = MultiplePush()
    cycle = 1
    while True:
        multi_push.run(dic)
        print("push cycle(%d) end" % cycle)
        cycle += 1

