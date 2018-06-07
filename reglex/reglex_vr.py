# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import os
import re


def parse(basename):
    pass


def parse_fov(basename):
    match = re.search(r"_(?P<fov>\d{1,3}x\d{1,3})", basename, re.I | re.L)
    if match:
        return match.group()[1:]
    else:
        return "360x180"


def parse_warp(basename):
    match = re.search(r"_(sphere|mono360|cubemap|cube)", basename, re.I | re.L)
    if match:
        return match.group()[1:]
    else:
        return "360x180"


def parse_attribute(basename):
    # parse spe
    match = re.search(r"(?P<spatial>_sa)?(?P<fov>_\d{1,3}x\d{1,3})_(?P<warping>sphere|cube|cubemap|offcenter)"
                      r"_(?P<layout>tb|lr|lr|mono)\Z", basename, re.I | re.L)

    if match:
        return match.groupdict()
    else:
        return None


def parse_name(basename):
    # parse spe
    match = re.search(r"(?P<spatial>_sa)?(?P<fov>_\d{1,3}x\d{1,3})_(?P<warping>sphere|cube|cubemap|offcenter)"
                      r"_(?P<layout>tb|lr|lr|mono)\Z", basename, re.I | re.L)

    return match


def parse_vr_attr_by_basename(basename):
    match = re.search(r"(?P<spatial>_sa)?_(?P<fov>\d{1,3}x\d{1,3})_(?P<warping>sphere|cube|cubemap|offcenter)"
                      r"_(?P<layout>tb|lr|lr|mono)\Z", basename, re.I | re.L)

    if match:
        print(match.groupdict())
        return match.group(2).lower(), match.group(3).lower(), match.group(4).lower(),
    else:
        # return {}
        return "360x180", "sphere", "tb"


def parse_url(url):
    match = re.search(r"^((http)s?://)?(localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                      r"(:\d+)?(/stat)\Z",
                      url, re.I | re.L)
    if match:
        print(match.groupdict())
        return match.group(3).lower()
    else:
        # return {}
        return "127.0.0.1"

# /rms/v1/distribute/action/
def parse_rms_request(path):
    match = re.search(r"/(?P<project>rms)/(?P<api_version>v\d{1,3})/(?P<module>[a-zA-Z]+)"
                      r"/(?P<action>[a-zA-Z]+)/\Z", path, re.I | re.L)

    if match:
        print(match.groupdict())
        return match.group(2).lower(), match.group(3).lower(), match.group(4).lower(),
    else:
        # return {}
        return "360x180", "sphere", "tb"

def parse_offcenter(name):
    match = re.search(r"OFFCENTERZ(?P<OFFCENTERZ>-?([1-9]\d*\.\d*|0\.\d*[1-9]\d*|0?\.0+|0))"
                      r"(-PITCH(?P<PITCH>-?[1-9]\d*))?"
                      r"(-YAW(?P<YAW>-?[1-9]\d*))?", name, re.I | re.L)
    if match:
        offcenterZ = match.groupdict().get("OFFCENTERZ")
        pitch = match.groupdict().get("PITCH")
        yaw = match.groupdict().get("YAW")
        print(offcenterZ, pitch, yaw)
        if offcenterZ != "-0.5":
            return 0
        if pitch == "45":
            if yaw == "270":
                return 17
            elif yaw == "180":
                return 16
            elif yaw == "90":
                return 15
            elif yaw is None:
                return 14
        elif pitch == "-45":
            if yaw == "270":
                return 13
            elif yaw == "180":
                return 12
            elif yaw == "90":
                return 11
            elif yaw is None:
                return 10
        if pitch is None:
            if yaw == "315":
                return 9
            elif yaw == "225":
                return 8
            elif yaw == "135":
                return 7
            elif yaw == "45":
                return 6
            elif yaw == "270":
                return 3
            elif yaw == "90":
                return 2
            elif yaw == "180":
                return 1
        if yaw is None:
            if pitch == "-90":
                return 5
            elif pitch == "90":
                return 4
    return 0


def parse_progress(str):
    match = re.search(r" (?P<progress>\d{1,3})%", str, re.I | re.L)
    if match:
        print(match.group())
        progress = match.groupdict().get("progress")
        print(progress)



if __name__ == "__main__":
    # [^_360x180$|^180x180$][{_sphere|_mono360}|{_cubemap|_cube}]_{lr|tb|3dh|3dv}
    # (_360x180|_180x180)(_sphere|_mono360)(_cubemap|_cube)_(lr|tb|3dh|3dv)
    # s = parse_fov("aaa_180x180_bbb_360x180.mp4")
    # print(s)
    #
    # s = parse_warp("aaa_180x180_cube.mp4")
    # print(s)
    #
    # s = parse_vr_attr_by_basename("_360x180_sphere_mono")
    # print(s)
    # s = parse_rms_request("/rms/v1/distribute/action/")
    # print(s)

    # s = parse_offcenter("asd_OFFCENTERZ-0.5-YAW90-PITCH-135")
    # print(s)

    parse_progress("1550K .......... .......... .......... .......... .......... 42% 28.4M 3s")

