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
    parser = argparse.ArgumentParser(description="set floorplan ")
    parser.add_argument("alignment_fn", type=str, help="path to alignment yaml file")
    parser.add_argument("output_fn", type=str, help="path to output json file")
    parser.add_argument("-z", "--z_expand", nargs='?', type=float, default=5., help="expand z axis(defaut=5)")
    parser.add_argument("-s", "--shot_subsample", nargs='?', type=int, default=10, help="expand z axis(defaut=10)")
    parser.add_argument("-d", "--datasets_prefix", nargs='?', type=str, default=None, help="datasets_path_prefix")
    parser.add_argument("-f", "--floorplans_prefix", nargs='?', type=str, default=None, help="floorplans_path_prefix")

    args = parser.parse_args()
    alignment_fn = args.alignment_fn
    output_fn = args.output_fn
    z_expand = args.z_expand
    shot_subsample_num = args.shot_subsample
    datasets_prefix = args.datasets_prefix
    floorplans_prefix = args.floorplans_prefix

    mylogger.logger.info('load alignment yaml file: {}'.format(alignment_fn))
    with open(alignment_fn, 'r') as f:
        data = yaml.load(f)
    datasets_dir = data['path']['datasets']
    floorplans_dir = data['path']['floorplans']
    pix_per_meter = data['setting']['pix_per_meter']    # 10

    floor_names = list(data['floorplans'].keys()) if 'floorplans' in data else []
    track_names = list(data['tracks'].keys()) if 'tracks' in data else []

    mylogger.logger.info('load {} floorplans'.format(floor_names))
    for floor in floor_names:
        mylogger.logger.info('    {}'.format(floor))
    mylogger.logger.info('load {} tracks'.format(track_names))
    for track in track_names:
        mylogger.logger.info('    {}'.format(track))

    reconstructions = []

    # load floorplans
    for floor in floor_names:
        recon_floor = types.Reconstruction()
        recon_floor.metadata.name = 'floorplans'
        # recon_floor.metadata.prefix = floorplans_dir.split('/')[-1]
        floorplans_dir_prefix = os.path.relpath(floorplans_dir if floorplans_prefix is None else floorplans_prefix, os.path.abspath(output_fn))
        recon_floor.metadata.prefix = floorplans_dir_prefix

        floorplan = types.Floorplan()
        floorplan.id = floor
        if 'trax' not in data['floorplans'][floor]['alignment'] or data['floorplans'][floor]['alignment']['trax'] is None:
            continue
        t = [data['floorplans'][floor]['alignment']['trax'], data['floorplans'][floor]['alignment']['tray'], data['floorplans'][floor]['alignment']['traz']]
        floorplan.pose = types.Pose(translation=np.array(t))
        floorplan.metadata.pix_per_meter = pix_per_meter

        floorplan.set_dataroot(floorplans_dir)
        fp_img = floorplan.get_img()
        floorplan.metadata.width = fp_img.shape[1]
        floorplan.metadata.height = fp_img.shape[0]
        recon_floor.add_floorplan(floorplan)
        reconstructionHandler.setExpandAxis(recon_floor, [1.0, 1.0, z_expand])
        mylogger.logger.info('set floorplan: {}'.format(floor))

        reconstructions.append(recon_floor)

    # load tracks
    for track in track_names:
        dataset_dir = os.path.join(datasets_dir, track)
        # print(dataset_dir)
        recon_in_fn = os.path.join(dataset_dir, IN_RECONSTRUCTION_FILENAME)
        recon = reconstructionHandler.loadReconstruction(recon_in_fn)[0]
        recon.metadata.name = track
        # recon.metadata.prefix = os.path.join(datasets_dir.split('/')[-1], track)
        recon_dir_prefix = os.path.join(os.path.relpath(datasets_dir if datasets_prefix is None else datasets_prefix, os.path.abspath(output_fn)), track)
        recon.metadata.prefix = recon_dir_prefix

        if 'trax' not in data['tracks'][track]['alignment'] or data['tracks'][track]['alignment']['trax'] is None:
            continue
        r = [data['tracks'][track]['alignment']['rotx'], data['tracks'][track]['alignment']['roty'], data['tracks'][track]['alignment']['rotz']]
        t = [data['tracks'][track]['alignment']['trax'], data['tracks'][track]['alignment']['tray'], data['tracks'][track]['alignment']['traz']]
        shots_offset = types.Pose()
        shots_offset.rotation = np.array(r)
        shots_offset.translation = np.array(t)
        shots_offset_rt = np.identity(4, dtype=float)
        shots_offset_rt[:3, :4] = shots_offset.get_Rt()

        reconstructionHandler.subsampleShot(recon, shot_subsample_num)
        reconstructionHandler.setOffset(recon, shots_offset_rt)
        reconstructionHandler.setExpandAxis(recon, [1.0, 1.0, z_expand])

        mylogger.logger.info('set track: {}'.format(track))
        reconstructions.append(recon)

    # save reconstruction file
    reconstructionHandler.saveReconstructions(reconstructions, output_fn)

