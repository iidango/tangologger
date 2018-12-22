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
import csv
import glob
import yaml
import pickle
import time
from multiprocessing import Pool

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='create score map')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
    parser.add_argument('-m', '--mask_dir', nargs='?', type=str, default=None, help='path to walkable mask dir to be aligned(default=<test_num_dir>/wmask)')
    parser.add_argument('-p', '--parameter', nargs='?', type=str, default='parameter.yaml', help='load parameter yaml file(default=parameter.yaml)')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, help='load config yaml file')
    parser.add_argument('-a', '--plot_all', default=False, action='store_true', help='create for all floor(default=False)')
    parser.add_argument('-o', '--target_data_config', nargs='?', type=str, default=None, help='target data config(default: same as data)')
    parser.add_argument('-j', '--process_num', nargs='?', type=int, default='4', help='process number(default=4)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    mask_dir = os.path.join(test_num_dir, args.mask_dir) if args.mask_dir is None else args.mask_dir
    target_floors = args.target_floors
    targets = args.targets
    plot_all = args.plot_all
    process_num = args.process_num
    parameter_fn = os.path.join(test_num_dir, args.parameter)
    data_dir = os.path.join(test_num_dir, os.path.splitext(args.data)[0])
    data_config_fn = os.path.join(test_num_dir, args.data)
    target_data_config_fn = data_config_fn if args.target_data_config is None else os.path.join(test_num_dir, args.target_data_config)
    # results_dir = data_dir
    results_dir = os.path.join(data_dir, 'score')
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)

    # logger setting
    log_fn = os.path.join(os.path.join(data_dir), 'log.txt')
    import logging
    logger = logging.getLogger('testLogger')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('(PID:%(process)d)[%(asctime)s][%(levelname)s] %(message)s')
    fh = logging.FileHandler(log_fn)
    logger.addHandler(fh)
    fh.setFormatter(formatter)
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    sh.setFormatter(formatter)
    logger.info('Start Logging: {}'.format(log_fn))
    # logger setting done

    # set parameters
    logger.info('load meta yaml file: {}'.format(parameter_fn))
    with open(parameter_fn, 'r') as f:
        parameter = yaml.load(f)
    crop_size = parameter['setting']['crop_size']
    crop_step = parameter['setting']['crop_step']

    pix_per_meter = parameter['setting']['pix_per_meter']
    crop_size = parameter['setting']['crop_size']
    crop_step = parameter['setting']['crop_step']
    align_step = parameter['setting']['align_step']
    align_voxel_size = parameter['setting']['align_voxel_size']
    decimate = parameter['setting']['align_decimate']

    fire_threshold = parameter['setting']['fire_threshold']
    good_consistency_threshold = parameter['setting']['good_consistency_threshold']

    hit_shot_count_threshold = parameter['setting']['hit_shot_count_threshold']
    floor_voxel_count_threshold = parameter['setting']['floor_voxel_count_threshold']

    max_save_num = parameter['setting']['max_save_num']
    max_save_znum = parameter['setting']['max_save_znum']

    # load datasets
    logger.info('load target data yaml file: {}'.format(target_data_config_fn))
    with open(target_data_config_fn, 'r') as f:
        data_config = yaml.load(f)
    floorplans_dir = data_config['path']['floorplans']
    datasets_dir = data_config['path']['datasets']

    # load target pairs
    target_pairs = {}
    if target_floors is None:
        target_floors = []
        for floor in data_config['floors']:
            if data_config['floors'][floor]['val']:
                target_floors.append(floor)
    if targets is None:
        targets = []
        for dn in data_config['datasets']:
            if data_config['datasets'][dn] is not None and 'target' in data_config['datasets'][dn] and data_config['datasets'][dn]['target']:
                target_pairs[dn] = target_floors
    else:
        for target in targets:
            target_pairs[target] = target_floors

    # print target pairs
    for dn in target_pairs:
        logger.info('target pairs: {}'.format(dn))
        for floor in target_pairs[dn]:
            logger.info('    {}'.format(floor))

    # load walkable masks
    walable_mask_dict = {}
    for floor in target_floors:
        # load walkable area mask
        mask_fn = os.path.join(mask_dir, floor + '.png')
        mask_img = cv2.imread(mask_fn)
        mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
        mask_img = cv2.dilate(mask_img, np.ones((5, 5), np.uint8), iterations=1)
        mask = mask_img != 0
        walable_mask_dict[floor] = mask

    for data_name in target_pairs:
        target_dir = os.path.join(results_dir, data_name)
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

        tra_fn = os.path.join(datasets_dir, '{}/2dtrajectory.csv'.format(data_name))
        tra_dict = {}
        with open(tra_fn, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                k = row[0]
                x = int(row[1])
                y = int(row[2])
                z = float(row[4]) * pix_per_meter    # z will come in meter
                tra_dict[k] = [x, y, z]
        logger.info('load {} trajectory points from {}'.format(len(tra_dict), tra_fn))

        minx, miny, minz = 1000000000, 1000000000, 1000000000
        maxx, maxy, maxz = 0, 0, 0
        for shot in tra_dict:
            x, y, z = tra_dict[shot]
            if x < minx:
                minx = x
            if y < miny:
                miny = y
            if z < minz:
                minz = z
            if x > maxx:
                maxx = x
            if y > maxy:
                maxy = y
            if z > maxz:
                maxz = z
        logger.info('trajectory size = ({}, {}, {})'.format(maxx-minx, maxy-miny, int(math.ceil(maxz-minz))))

        # calc soore for each floor
        for floor in target_pairs[data_name]:
            target_floor_dir = os.path.join(target_dir, floor)
            if not os.path.exists(target_floor_dir):
                os.mkdir(target_floor_dir)

            # create range_x and range_y
            ##  get walkable area mask size
            mask = walable_mask_dict[floor]
            mask_i = np.where(mask == True)
            mask_minx, mask_miny = min(mask_i[1]), min(mask_i[0])
            mask_maxx, mask_maxy = max(mask_i[1]), max(mask_i[0])

            range_x = range(-(maxx-mask_minx), mask_maxx-minx, align_step[0])
            range_y = range(-(maxy-mask_miny), mask_maxy-miny, align_step[1])
            range_z = range(int(math.floor(minz)), int(math.ceil(maxz)), align_step[2])
            logger.info('walkable mask size = ({}, {})'.format(mask_maxx - mask_minx, mask_maxy - mask_miny))
            logger.info('range x: {} to {}'.format(range_x[0], range_x[-1]))
            logger.info('range y: {} to {}'.format(range_y[0], range_y[-1]))
            logger.info('range z: {} to {}'.format(range_z[0], range_z[-1]))
            logger.info('total num: {}x{}x{}={}'.format(len(range_x), len(range_y), len(range_z), len(range_x)*len(range_y)*len(range_z)))

            # create score map of each translation(len(range_y)*len(range_x))
            logger.info('start to create score map of each translation')
            results = [[] for z in range(len(range_z))]

            def calc_score(arg):
                tra_y = arg[0]
                tra_x = arg[1]
                result = [None for z in range(len(range_z))]
                hit_shot_z_list = [[] for z in range(len(range_z))]

                # count number of shots which hit floor
                hit_shot_list = []
                for shot_name in tra_dict:
                    xyz = tra_dict[shot_name]
                    y = xyz[1] + tra_y
                    if y < 0 or y >= mask.shape[0]:
                        continue
                    x = xyz[0] + tra_x
                    if x < 0 or x >= mask.shape[1]:
                        continue
                    if mask[xyz[1] + tra_y][xyz[0] + tra_x] == False:    # out of range
                        continue
                    z = int((xyz[2] - range_z[0])//align_step[2])
                    hit_shot_z_list[z].append(shot_name)
                for z in range(len(range_z)):
                    if len(hit_shot_z_list[z]) < hit_shot_count_threshold:
                        continue
                    score = len(hit_shot_z_list[z])/float(len(list(tra_dict.keys())))
                    in_floor = hit_shot_z_list[z]
                    fire = []

                    if score < good_consistency_threshold:
                        continue
                    sub_result = {}
                    sub_result['x'] = int(tra_x)
                    sub_result['y'] = int(tra_y)
                    sub_result['z'] = - int(range_z[z])
                    sub_result['score'] = float(score)
                    sub_result['in_floor'] = in_floor
                    sub_result['fire'] = fire
                    result[z] = sub_result

                return result

            # calc score for each
            for tra_y in range_y:
                arg = []
                for tra_x in range_x:
                    arg.append([tra_y, tra_x])
                p = Pool(process_num)
                result = p.map_async(calc_score, arg).get(9999999)
                for r in result:
                    for z in range(len(range_z)):
                        if r[z] is not None:
                            results[z].append(r[z])
                p.close()

            logger.info('finish to count number of shots 2d!!')

            # save results
            logger.info('creating result dict to save')
            align_result = []
            for z in range(len(range_z)):
                results[z].sort(key=lambda x: -x['score'])
                if len(results[z]) == 0:
                    continue
                for i, result in enumerate(results[z]):
                    if i > max_save_znum - 1:
                        break
                    align_result.append(result)

            # save align result
            out_info_fn = os.path.join(target_floor_dir, 'align_result_e.yaml')
            data = {}
            data['candidates'] = align_result
            with open(out_info_fn, 'w') as f:
                f.write(yaml.dump(data, default_flow_style=False))
            logger.info('save {} scores to {}'.format(len(align_result), out_info_fn))

