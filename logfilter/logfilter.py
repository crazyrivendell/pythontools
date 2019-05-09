# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

file_src = "C:/Users/kandao/AppData/Local/KDLive/kandao-stitch.dat"
file_dst = "C:/Users/kandao/AppData/Local/KDLive/kandao-stitch_filter.dat"


def IncludeOverall(str):
    if str.find('live video') < 0 and str.find('live audio') < 0:
        return False
    else:
        return True


def logfilter():
    try:
        file_object = open(file_src, "r+")
    except IOError:
        print("No Found File!")
    else:
        file_result = open(file_dst, "w+")

    for line in file_object:
        line = line.strip()
        if IncludeOverall(line):
            file_result.write(line+"\n")
        else:
            continue
    file_object.close()
    file_result.close()
    print("完成")


if __name__ == "__main__":
    logfilter()