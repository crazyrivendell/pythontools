# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

from transform.transcode import H265_to_H264


if __name__ == "__main__":
    # trans = H265_to_H264(src="/home/wuminlai/Work/temp/8k/beijing_4k_3dv/",
    #                      dst="/home/wuminlai/Work/temp/8k/H264/beijing_4k_3dv")
    # trans.transcode()
    # trans = H265_to_H264(src="/home/wuminlai/Work/temp/8k/onthehill_4k_3dv/",
    #                      dst="/home/wuminlai/Work/temp/8k/H264/onthehill_4k_3dv")
    # trans.transcode()
    trans = H265_to_H264(src="/home/wuminlai/Work/temp/offcenter/4K/H265/Lamborghini-adertisement-4kx4k_360x180_sphere_tb/",
                         dst="/home/wuminlai/Work/temp/offcenter/4K/H264/Lamborghini-adertisement-4kx4k_360x180_sphere_tb")
    trans.transcode()
    trans = H265_to_H264(src="/home/wuminlai/Work/temp/offcenter/4K/H265/temple_4kx4k_360x180_sphere_tb/",
                         dst="/home/wuminlai/Work/temp/offcenter/4K/H264/temple_4kx4k_360x180_sphere_tb")
    trans.transcode()
    trans = H265_to_H264(src="/home/wuminlai/Work/temp/offcenter/4K/H265/wasterecycle_4kx4k_360x180_sphere_3dv/",
                         dst="/home/wuminlai/Work/temp/offcenter/4K/H264/wasterecycle_4kx4k_360x180_sphere_3dv")
    trans.transcode()
