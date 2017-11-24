#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import math
import cv2
import numpy as np
import mylogger
from handler import reconstructionHandler
from handler import tangoPoseHandler

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"

IN_IMAGE_DIR = "images"
OUT_IMAGE_DIR = "images_northup"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("src_dir", help="path to src_dir to be processed")
    parser.add_argument("dst_dir", help="path to dst_dir to be output")
    args = parser.parse_args()

    # load reconstruction file
    recon_in_fn = os.path.join(args.src_dir, IN_RECONSTRUCTION_FILENAME)
    reconstructions = reconstructionHandler.loadReconstruction(recon_in_fn, apply_shotoffset=True)

    # create output dir
    input_im_dir = os.path.join(args.src_dir, IN_IMAGE_DIR)
    output_im_dir = os.path.join(args.dst_dir, OUT_IMAGE_DIR)
    if not os.path.exists(output_im_dir):
        mylogger.logger.info("create " + output_im_dir)
        os.mkdir(output_im_dir)

    # c = 0
    # load shots
    for reconstruction in reconstructions:
        for shot in reconstruction.shots:
            pose = reconstruction.shots[shot].pose

            ori_img = cv2.imread(os.path.join(input_im_dir, shot))
            pos = reconstruction.shots[shot].pose
            r_vec = reconstruction.shots[shot].viewing_direction()
            angle_rad = np.arctan2(r_vec[0], r_vec[1])
            angle_rad = (angle_rad - math.pi/2.) % (2*math.pi)    # set north direction to center

            # slide img
            north_up_img = tangoPoseHandler.slideToNorth(ori_img, angle_rad)

            # resize
            north_up_img = cv2.resize(north_up_img, (224, 224))

            out_fn = os.path.join(output_im_dir, shot)
            cv2.imwrite(out_fn, north_up_img)
            mylogger.logger.info("save " + out_fn)

            # c += 1
            # if c > 100:
            #     break


