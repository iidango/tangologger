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
import mylogger

IN_CAMERAPOSE_FILENAME = "*_cameraPose.csv"

OUT_RECONSTRUCTION_FILENAME = "tangoCameraPose.json"

GEAR360_CAMERA = types.SphericalCamera()
GEAR360_CAMERA.id = "gear360"
GEAR360_CAMERA.width = 3840
GEAR360_CAMERA.height = 1920

THETA_CAMERA = types.SphericalCamera()
THETA_CAMERA.id = "theta"
THETA_CAMERA.width = 1920
THETA_CAMERA.height = 960

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("data_dir", help="path to data_dir to be processed")
    parser.add_argument("video_fn", help="path to video")
    parser.add_argument("fps", type=float, default=3., nargs='?',help="output frame per second(default 3., 0 for max)")
    parser.add_argument("delay", type=float, default=0., nargs='?',help="video delay(default 0.)")
    parser.add_argument("max_frame_num", type=int, default=0, nargs='?',help="max frame num")
    parser.add_argument("-t", "--theta", default=False, action="store_true", help="theta video(rotate 180 degree)")
    parser.add_argument("-n", "--no_video", default=False, action="store_true", help="no video")
    args = parser.parse_args()

    data_dir = args.data_dir

    if args.theta:
        rotate = math.pi
    else:
        rotate = 0.0

    # OUT_RECONSTRUCTION_FILENAME = "tangoCameraPose_tmp{}.json".format(args.delay)    # tmp

    # load cameraPose file
    cameraPose_in_fn_list = glob.glob(os.path.join(data_dir, IN_CAMERAPOSE_FILENAME))
    reconstructions = []
    if args.theta:
        camera = THETA_CAMERA
    else:
        camera = GEAR360_CAMERA

    for fn in cameraPose_in_fn_list:
        if args.no_video or not os.path.exists(args.video_fn):
            mylogger.logger.info('load tango pose without video')
            reconstructions.append(tangoPoseHandler.loadTangoPose(fn, camera, args.fps))
        else:
            mylogger.logger.info('load tango pose with video: {}'.format(args.video_fn))
            reconstructions.append(tangoPoseHandler.loadTangoPoseWithVideo(fn, camera, args.video_fn, args.fps, args.delay, args.max_frame_num, rotate))

    # save reconstruction file
    recon_out_fn = os.path.join(args.data_dir, OUT_RECONSTRUCTION_FILENAME)
    reconstructionHandler.saveReconstructions(reconstructions, recon_out_fn)

