# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import os
import urllib.request
import xml.etree.ElementTree as ElementTree
import re
import time
import json


class Stat(object):
    def __init__(self, url="", path=""):
        self.url = url
        self.path = path
        if self.path == "":
            self.path = self.base_path

        self.base_url = self.parse_url(url)

    @property
    def base_path(self):
        return os.path.dirname(os.path.abspath(__file__))

    def parse_name(self, basename):
        match = re.search(r"\A(?P<name>.+)_(?P<resolution>\d{1,4}x\d{1,4})_(?P<fov>\d{1,3}x\d{1,3})"
                          r"_(?P<warping>sphere|cube|cubemap|offcenter|offcube)_(?P<layout>tb|3dv|lr|mono)_(?P<offset>.+)\Z",
                          basename, re.I | re.L)

        if match:
            return 1, match.group(1), match.group(2).lower(), match.group(3).lower(), match.group(4).lower(), \
                   match.group(5), match.group(6)
        else:
            print("default")
            return 0, "demo", "3840x1920", "360x180", "cubemap", "mono", "OFFCENTERZ-0.5"

    def parse_url(self, url):
        match = re.search(r"^((http)s?://)?(localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                          r"(:\d+)?(/stat)\Z",
                          url, re.I | re.L)
        if match:
            print(match.groupdict())
            return match.group(3).lower()
        else:
            # return {}
            return "127.0.0.1"

    def parse_offcenter(self, name):
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
                    return 4
                elif pitch == "90":
                    return 5
        return 0

    def update_dict(self, dic, key_a, key_b, val):
        if key_a in dic:
            dic[key_a].update({key_b: val})
        else:
            dic.update({key_a: {key_b: val}})

    def cycle(self):
        while(1):
            try:
                with urllib.request.urlopen(self.url) as f:
                    html = f.read().decode('utf-8')
                    tree = ElementTree.fromstring(html)
                    for server in tree.iter("server"):
                        for application in server.iter("application"):
                            offset_list = dict()
                            print(application.tag, ":")
                            app = application.find("name").text
                            print("-", app)
                            for stream in application.iter("stream"):
                                # print(stream.tag)
                                stream_name = stream.find("name").text
                                uri = stream_name + ".m3u8"
                                print("--", stream_name)
                                # name, layout, resolution, warping, offset = stream_name.split("_")
                                status, name, resolution, fov, warping, layout, offset = self.parse_name(stream_name)
                                if status == 0:
                                    continue
                                masterlist = name + "_" + resolution + "_" + fov + "_" + warping + "_" + layout
                                # dic["offset"] = offset
                                # offset_list.update(dic)
                                self.update_dict(offset_list, masterlist, offset, uri)

                            # produce masterlist.m3u8
                            for key, value in offset_list.items():
                                hls_file = os.path.join(self.path, key + ".m3u8")
                                rtmp_file = os.path.join(self.path, key + ".json")

                                l = list()
                                default_uri = None
                                with open(hls_file, "w+") as f1, open(rtmp_file, "w+") as f2:
                                    f1.write("#EXTM3U\n\n")
                                    for offset_, uri_ in value.items():
                                        f1.write("#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID=\"MVC\",NAME=\"{0}\", DEFAULT=YES,URI=\"{1}\"\n".format(offset_, uri_))

                                        dic = dict()
                                        dic["Name"] = offset_
                                        dic["ID"] = self.parse_offcenter(offset_)
                                        dic["URL"] = "rtmp://" + self.base_url + "/" + app + "/" + os.path.splitext(uri_)[0]
                                        if offset_ == "OFFCENTERZ-0.5":
                                            dic["MainView"] = True
                                            default_uri = uri_
                                        l.append(dic)
                                    f1.write("\n#EXT-X-STREAM-INF:BANDWIDTH=8000000,CODECS=\"...\",VIDEO=\"MVC\"\n")
                                    f1.write("{0}".format(default_uri))
                                    f1.close()
                                    print("update HLS", hls_file)
                                    test = {}
                                    test["streams"] = l
                                    j = json.dumps(test, sort_keys=True)
                                    f2.write("{0}".format(j))
                                    f2.close()
                                    print("update RTMP", rtmp_file)
            except Exception as e:
                print("error {0}".format(str(e)))
            time.sleep(3)


if __name__ == "__main__":
    # http://192.168.50.19:8080/stat
    # http://r730.kandao.tech/offcenter/HLS/H265/8M/Concert_360x180_offcube_lr.m3u8
    # http://r730.kandao.tech/offcenter/HLS/H265/8M/beijing_360x180_offcube_lr.m3u8
    # http://r730.kandao.tech/offcenter/HLS/H265/8M/onthehill_360x180_offcube_lr.m3u8
    # http://r730.kandao.tech/offcenter/HLS/H265/8M/brug3_360x180_offcube_mono.m3u8
    # http://r730.kandao.tech/offcenter/HLS/H265/8M/brug_360x180_offcube_mono.m3u8
    # http://r730.kandao.tech/offcenter/HLS/H264/4M/clock1080p_360x180_offcube_lr.m3u8
    
    stat = Stat(url="http://192.168.50.26/stat", path="/home/wuminlai/Work/study/python/pythontools/nginx_stat")
    stat.cycle()


