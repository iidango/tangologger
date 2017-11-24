#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import glob
import math
from utils import types
from handler import tangoPoseHandler, reconstructionHandler

IN_CAMERAPOSE_FILENAME = "*_cameraPose.csv"

OUT_RECONSTRUCTION_FILENAME = "tangoCameraPose.json"

TEST_CAMERA = types.SphericalCamera()
TEST_CAMERA.id = "gear360"
TEST_CAMERA.width = 3840
TEST_CAMERA.height = 1920

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("src_dir", help="path to src_dir to be processed")
    parser.add_argument("dst_dir", help="path to dst_dir to be output")
    parser.add_argument("video_fn", help="path to video")
    parser.add_argument("fps", type=float, default=3., nargs='?',help="output frame per second(default 3.)")
    parser.add_argument("delay", type=float, default=0., nargs='?',help="video delay(default 0.)")
    parser.add_argument("max_frame_num", type=int, default=0, nargs='?',help="max frame num")
    parser.add_argument("-t", "--theta", default=False, action="store_true", help="theta video(rotate 180 degree)")
    args = parser.parse_args()

    if args.theta:
        rotate = math.pi
    else:
        rotate = 0.0

    # OUT_RECONSTRUCTION_FILENAME = "tangoCameraPose_tmp{}.json".format(args.delay)    # tmp

    # load cameraPose file
    cameraPose_in_fn_list = glob.glob(os.path.join(args.src_dir, IN_CAMERAPOSE_FILENAME))
    reconstructions = []
    for fn in cameraPose_in_fn_list:
        # reconstructions.append(tangoPoseHandler.loadTangoPose(fn, TEST_CAMERA))
        reconstructions.append(
            tangoPoseHandler.loadTangoPoseWithVideo(fn, TEST_CAMERA, args.video_fn, args.fps, args.delay, args.max_frame_num, rotate))

    # save reconstruction file
    recon_out_fn = os.path.join(args.dst_dir, OUT_RECONSTRUCTION_FILENAME)
    reconstructionHandler.saveReconstructions(reconstructions, recon_out_fn)

