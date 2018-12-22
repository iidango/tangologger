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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("data_dir", type=str, help="path to data_dir to be processed")
    parser.add_argument("--meta", nargs='?', type=str, default='meta.yaml', help="load meta yaml file(default=meta.yaml)")
    parser.add_argument("-r", "--show_ref", default=True, action="store_false", help="show reference trac(default True)")
    parser.add_argument("-w", "--plot_whole_trajectory", default=True, action="store_false", help="plot whole trajectory(default True)")

    # TODO
    print('TODO!!!! z coord in trajctory csv might be strange when set manual alignment rot y!!!!!')

    args = parser.parse_args()
    data_dir = args.data_dir
    meta = args.meta
    show_ref = args.show_ref
    plot_whole_trajectory = args.plot_whole_trajectory

    # load reconstruction file
    recon_in_fn = os.path.join(data_dir, IN_RECONSTRUCTION_FILENAME)
    reconstructions = reconstructionHandler.loadReconstruction(recon_in_fn)
    reconstruction = reconstructionHandler.loadReconstruction(recon_in_fn)[0]

    meta_fn = os.path.join(data_dir, meta)
    mylogger.logger.info('load meta yaml file: {}'.format(meta_fn))
    with open(meta_fn, 'r') as f:
        data = yaml.load(f)

    for fp_name in data['floorplans']:
        mylogger.logger.info('align with {}'.format(fp_name))

        rotx = data['floorplans'][fp_name]['manual_alignment']['rotx']
        roty = data['floorplans'][fp_name]['manual_alignment']['roty']
        rotz = data['floorplans'][fp_name]['manual_alignment']['rotz']
        trax = data['floorplans'][fp_name]['manual_alignment']['trax']
        tray = data['floorplans'][fp_name]['manual_alignment']['tray']
        traz = data['floorplans'][fp_name]['manual_alignment']['traz']

        # create new floorplan
        floorplan = types.Floorplan()
        floorplan.id = fp_name
        floorplan.pose = types.Pose(translation=np.array([0, 0, 0]))
        floorplan.metadata.pix_per_meter = 10.0    # fix
        floorplan.set_dataroot(os.path.join(data_dir, 'floorplans'))
        fp_img = floorplan.get_img()
        floorplan.metadata.width = fp_img.shape[1]
        floorplan.metadata.height = fp_img.shape[0]

        # create Trajectory for the floorplan
        trajectory_all = reconstructionHandler.createTrajectory(reconstruction)
        t0 = trajectory_all.shots[0].metadata.capture_time

        target_shots_id = []

        # add all shots
        if 'clip_t' not in data['floorplans'][fp_name] and 'clip_i' not in data['floorplans'][fp_name]:
            mylogger.logger.info('clip not found. set whole trajectory')
            for s in trajectory_all.shots:
                target_shots_id.append(s.id)
        # add shots in clip
        else:
            clips_t = data['floorplans'][fp_name]['clip_t'] if 'clip_t' in data['floorplans'][fp_name] else {}
            clips_i = data['floorplans'][fp_name]['clip_i'] if 'clip_i' in data['floorplans'][fp_name] else {}
            for s in trajectory_all.shots:
                t = s.metadata.capture_time - t0
                image_num = int(s.id.split('.')[0])
                for clip in clips_t:
                    if (clip['start'] <= t) and ((clip['end'] > t) if clip['end'] != -1 else True):
                        target_shots_id.append(s.id)
                for clip in clips_i:
                    if (image_num < int(clip['start'])) and ((int(clip['end']) > image_num) if clip['end'] != -1 else True):
                        target_shots_id.append(s.id)

        shots_offset = types.Pose()
        shots_offset.rotation = np.array([rotx, roty, rotz])
        shots_offset.translation = np.array([trax, tray, traz])

        # plot shots pose to floorlpan
        tmp_reconstruction = copy.deepcopy(reconstructions[0])
        offset = np.identity(4, dtype=float)
        offset[:3, :4] = shots_offset.get_Rt()
        reconstructionHandler.setOffset(tmp_reconstruction, offset)

        target_shots = {}
        no_target_shots = {}
        for shot in tmp_reconstruction.shots:
            if shot in target_shots_id:
                target_shots[shot] = tmp_reconstruction.shots[shot]
            elif show_ref:
                no_target_shots[shot] = tmp_reconstruction.shots[shot]
        floorplanHandler.plotShotPoses(target_shots, floorplan, data_dir, 'trajectory_{}.png'.format(fp_name.split('.')[0]), no_target_shots)
        floorplanHandler.save2DTrajectory(target_shots, floorplan, data_dir, '2dtrajectory_{}.csv'.format(fp_name.split('.')[0]))

    if plot_whole_trajectory:
        tmp_reconstruction = copy.deepcopy(reconstructions[0])
        shots_offset = types.Pose()
        shots_offset.rotation = np.array([rotx, roty, rotz])
        shots_offset.translation = np.array([0.0, 0.0, 0.0])
        offset = np.identity(4, dtype=float)
        offset[:3, :4] = shots_offset.get_Rt()
        reconstructionHandler.setOffset(tmp_reconstruction, offset)

        whole_trajectory = types.Trajectory()
        for shot in tmp_reconstruction.shots:
            whole_trajectory.add_shot(tmp_reconstruction.shots[shot])
        whole_trajectory.sort()
        whole_trajectory.setToTopLeft(floorplan)

        floorplanHandler.save2DTrajectory(whole_trajectory.get_ShotsDict(), floorplan, data_dir, '2dtrajectory.csv')


