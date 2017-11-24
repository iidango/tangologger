#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import copy
import numpy as np
import mylogger
from handler import reconstructionHandler
from handler import floorplanHandler
from utils import types

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose.json"
OUT_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("src_dir", type=str, help="path to src_dir to be processed")
    parser.add_argument("dst_dir", type=str, help="path to dst_dir to be output")
    parser.add_argument("floorplan_fn", type=str, help="path to floorplan image file")
    parser.add_argument("ppm", type=float, help="NOT USED: pixel per meter(9.8516666667, 11.81, 23.62)")
    parser.add_argument("rotx", type=float, help="x element of rotation vecrtor")
    parser.add_argument("roty", type=float, help="y element of rotation vecrtor")
    parser.add_argument("rotz", type=float, help="z element of rotation vecrtor")
    parser.add_argument("trax", type=float, help="x element of translation")
    parser.add_argument("tray", type=float, help="y element of translation")
    parser.add_argument("traz", type=float, help="z element of translation")
    parser.add_argument("width", type=int, nargs='?', default=1754, help="NOT USED: width of floorplan img(default=1754)")
    parser.add_argument("height", type=int, nargs='?', default=1240, help="NOT USED: height of floorplan img(default=1754)")

    args = parser.parse_args()

    # load reconstruction file
    recon_in_fn = os.path.join(args.src_dir, IN_RECONSTRUCTION_FILENAME)
    reconstructions = reconstructionHandler.loadReconstruction(recon_in_fn)

    floorplan = types.Floorplan()
    floorplan.id = os.path.basename(args.floorplan_fn)
    floorplan.pose = types.Pose(translation=np.array([0, 0, 0]))
    # floorplan.metadata.pix_per_meter = 59.05/6    # zengaku
    # floorplan.metadata.pix_per_meter = 59.05/5  # eng2f
    # floorplan.metadata.pix_per_meter = 59.05/2.5  # sfu
    # floorplan.metadata.pix_per_meter = args.ppm
    floorplan.metadata.pix_per_meter = 10.0    # fix

    floorplan.set_dataroot(args.src_dir)
    fp_img = floorplan.get_img()
    floorplan.metadata.width = fp_img.shape[1]
    floorplan.metadata.height = fp_img.shape[0]

    shots_offset = types.Pose()
    # shots_offset.rotation = np.array([0, 0, 1.635])
    # shots_offset.translation = np.array([15.5, -21.5, 1.5])
    shots_offset.rotation = np.array([args.rotx, args.roty, args.rotz])
    shots_offset.translation = np.array([args.trax, args.tray, args.traz])

    reconstructions[0].metadata.shots_offset = shots_offset
    reconstructions[0].add_floorplan(floorplan)


    # plot shots pose to floorlpan
    tmp_reconstruction = copy.deepcopy(reconstructions[0])
    shots_offset = np.identity(4, dtype=float)
    shots_offset[:3, :4] = tmp_reconstruction.metadata.shots_offset.get_Rt()
    reconstructionHandler.setOffset(tmp_reconstruction, shots_offset)
    floorplanHandler.plotShotPoses(tmp_reconstruction.shots, floorplan, args.src_dir, "floorplan_camera.png")
    floorplanHandler.save2DTrajectory(tmp_reconstruction.shots, floorplan, args.src_dir, TRAJECTORY_FILENAME)

    # save reconstruction file
    recon_out_fn = os.path.join(args.dst_dir, OUT_RECONSTRUCTION_FILENAME)
    reconstructionHandler.saveReconstructions(reconstructions, recon_out_fn)

