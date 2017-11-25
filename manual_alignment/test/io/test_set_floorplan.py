#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import copy
import numpy as np
import yaml
from handler import reconstructionHandler, floorplanHandler
from utils import types
import mylogger

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose.json"
OUT_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("data_dir", type=str, help="path to data_dir to be processed")
    parser.add_argument("floorplan_fn", type=str, help="floorplan image name")
    parser.add_argument("rotx", nargs='?', type=float, help="x element of rotation vecrtor")
    parser.add_argument("roty", nargs='?', type=float, help="y element of rotation vecrtor")
    parser.add_argument("rotz", nargs='?', type=float, help="z element of rotation vecrtor")
    parser.add_argument("trax", nargs='?', type=float, help="x element of translation")
    parser.add_argument("tray", nargs='?', type=float, help="y element of translation")
    parser.add_argument("traz", nargs='?', type=float, help="z element of translation")
    parser.add_argument("-m", "--meta", nargs='?', type=str, help="load meta yaml file")

    args = parser.parse_args()
    data_dir = args.data_dir
    fp_name = os.path.basename(args.floorplan_fn)
    meta = args.meta
    if meta is None:
        rotx = args.rotx
        roty = args.roty
        rotz = args.rotz
        trax = args.trax
        tray = args.tray
        traz = args.traz
    else:
        meta_fn = os.path.join(data_dir, meta)
        mylogger.logger.info('load meta yaml file: {}'.format(meta_fn))
        with open(meta_fn, 'r') as f:
            data = yaml.load(f)
        rotx = data[fp_name]['manual_alignment']['rotx']
        roty = data[fp_name]['manual_alignment']['roty']
        rotz = data[fp_name]['manual_alignment']['rotz']
        trax = data[fp_name]['manual_alignment']['trax']
        tray = data[fp_name]['manual_alignment']['tray']
        traz = data[fp_name]['manual_alignment']['traz']


    # load reconstruction file
    recon_in_fn = os.path.join(data_dir, IN_RECONSTRUCTION_FILENAME)
    reconstructions = reconstructionHandler.loadReconstruction(recon_in_fn)

    floorplan = types.Floorplan()
    floorplan.id = fp_name
    floorplan.pose = types.Pose(translation=np.array([0, 0, 0]))
    # floorplan.metadata.pix_per_meter = args.ppm
    floorplan.metadata.pix_per_meter = 10.0    # fix

    floorplan.set_dataroot(data_dir)
    fp_img = floorplan.get_img()
    floorplan.metadata.width = fp_img.shape[1]
    floorplan.metadata.height = fp_img.shape[0]

    shots_offset = types.Pose()
    # shots_offset.rotation = np.array([0, 0, 1.635])
    # shots_offset.translation = np.array([15.5, -21.5, 1.5])
    shots_offset.rotation = np.array([rotx, roty, rotz])
    shots_offset.translation = np.array([trax, tray, traz])

    reconstructions[0].metadata.shots_offset = shots_offset
    reconstructions[0].add_floorplan(floorplan)


    # plot shots pose to floorlpan
    tmp_reconstruction = copy.deepcopy(reconstructions[0])
    shots_offset = np.identity(4, dtype=float)
    shots_offset[:3, :4] = tmp_reconstruction.metadata.shots_offset.get_Rt()
    reconstructionHandler.setOffset(tmp_reconstruction, shots_offset)
    floorplanHandler.plotShotPoses(tmp_reconstruction.shots, floorplan, data_dir, "floorplan_trajectory.png")
    floorplanHandler.save2DTrajectory(tmp_reconstruction.shots, floorplan, data_dir, TRAJECTORY_FILENAME)

    # save reconstruction file
    recon_out_fn = os.path.join(data_dir, OUT_RECONSTRUCTION_FILENAME)
    reconstructionHandler.saveReconstructions(reconstructions, recon_out_fn)

    # save parameters for yaml
    data = {}
    data[floorplan.id] = {}
    data[floorplan.id]['manual_alignment'] = {}
    data[floorplan.id]['manual_alignment']['rotx'] = args.rotx
    data[floorplan.id]['manual_alignment']['roty'] = args.roty
    data[floorplan.id]['manual_alignment']['rotz'] = args.rotz
    data[floorplan.id]['manual_alignment']['trax'] = args.trax
    data[floorplan.id]['manual_alignment']['tray'] = args.tray
    data[floorplan.id]['manual_alignment']['traz'] = args.traz
    if meta is None:
        meta_fn = os.path.join(data_dir, 'meta.yaml')
        with open(meta_fn, 'w') as f:
            f.write(yaml.dump(data, default_flow_style=False))


