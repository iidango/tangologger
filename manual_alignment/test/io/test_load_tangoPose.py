#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import glob
import math
import yaml
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
    parser.add_argument("fps", type=float, default=3., nargs='?',help="output frame per second(default 3., 0 for max)")
    parser.add_argument("max_frame_num", type=int, default=0, nargs='?',help="max frame num")
    parser.add_argument("video_name", nargs='?', help="video name")
    parser.add_argument("delay", type=float, nargs='?',help="video delay")
    parser.add_argument("-t", "--theta", default=False, action="store_true", help="theta video(rotate 180 degree)")
    parser.add_argument("-n", "--no_video", default=False, action="store_true", help="no video")
    parser.add_argument("-m", "--meta", nargs='?', type=str, default='meta.yaml', help="load meta yaml file(default: meta.yaml)")
    parser.add_argument("-o", "--o_meta", nargs='?', type=str, help="output meta yaml file")
    args = parser.parse_args()

    data_dir = args.data_dir
    fps = args.fps
    max_frame_num = args.max_frame_num
    no_video = args.no_video

    meta = args.meta
    o_meta = args.o_meta
    if meta is not None:
        meta_fn = os.path.join(data_dir, meta)
        mylogger.logger.info('load meta yaml file: {}'.format(meta_fn))
        with open(meta_fn, 'r') as f:
            meta = yaml.load(f)
        if not 'video' in meta:
            meta['video'] = {}
            meta['video']['name'] = ''
            meta['video']['delay'] = 0.0
            meta['video']['theta'] = False
            no_video = True


    video_name = args.video_name if args.video_name is not None else meta['video']['name']
    delay = args.delay if args.delay is not None else meta['video']['delay']
    is_theta = True if args.theta or meta['video']['theta'] else False
    rotate = math.pi if is_theta else 0.
    video_range = None if 'start' not in meta['video'] else [meta['video']['start'], meta['video']['end']]
    if video_range is not None:
        mylogger.logger.info('video range: {}'.format(video_range))

    video_fn = os.path.join(data_dir, video_name)

    # load cameraPose file
    cameraPose_in_fn_list = glob.glob(os.path.join(data_dir, IN_CAMERAPOSE_FILENAME))
    reconstructions = []
    if is_theta:
        camera = THETA_CAMERA
    else:
        camera = GEAR360_CAMERA

    for fn in cameraPose_in_fn_list:
        if no_video or not os.path.exists(video_fn):
            mylogger.logger.info('load tango pose without video')
            reconstructions.append(tangoPoseHandler.loadTangoPose(fn, camera, fps))
        else:
            mylogger.logger.info('load tango pose with video: {}'.format(video_name))
            reconstructions.append(tangoPoseHandler.loadTangoPoseWithVideo(fn, camera, video_fn, fps, delay, max_frame_num, rotate, video_range))

    # save reconstruction file
    recon_out_fn = os.path.join(args.data_dir, OUT_RECONSTRUCTION_FILENAME)
    reconstructionHandler.saveReconstructions(reconstructions, recon_out_fn)

