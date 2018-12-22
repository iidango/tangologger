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

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument('test_num_dir', type=str, help='path to data name dir to be processed')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, help='load config yaml file')
    parser.add_argument('-a', '--plot_all', default=False, action='store_true', help='create for all floor(default=False)')
    parser.add_argument('-d', '--results_dir', nargs='?', type=str, default='results', help='results dir name(default=results)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    target_floors = args.target_floors
    targets = args.targets
    plot_all = args.plot_all

    results_dir = os.path.join(test_num_dir, args.results_dir)

    # logger setting
    log_fn = os.path.join(os.path.join(test_num_dir), 'log.txt')
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

    config = None
    if args.config is not None:
        config_fn = os.path.join(test_num_dir, args.config)
        logger.info('load meta yaml file: {}'.format(config_fn))
        with open(config_fn, 'r') as f:
            config = yaml.load(f)

    pix_per_meter = 10 if config is None else config['setting']['pix_per_meter']
    crop_size = 150 if config is None else config['setting']['crop_size']
    crop_step = 10 if config is None else config['setting']['crop_step']
    align_step = [5, 5, 10] if config is None else config['setting']['align_step']
    align_voxel_size = [10, 10, 20] if config is None else config['setting']['align_voxel_size']
    decimate = 1 if config is None else config['setting']['align_decimate']

    fire_threshold = 0.5 if config is None else config['setting']['fire_threshold']
    good_consistency_threshold = 0.5 if config is None else config['setting']['good_consistency_threshold']
    count_threshold = 20 if config is None else config['setting']['count_threshold']

    max_save_num = 100 if config is None else config['setting']['max_save_num']
    max_save_znum = 30 if config is None else config['setting']['max_save_znum']

    datasets_dir = config['path']['datasets']
    floorplans_dir = config['path']['floorplans']

    # load target pairs
    target_pairs = {}
    if target_floors is None:
        target_floors = []
        for floor in config['floors']:
            if config['floors'][floor]['target']:
                target_floors.append(floor)
    if targets is None:
        targets = []
        for dn in config['datasets']:
            if 'target_floor_all' in config['datasets'][dn] and config['datasets'][dn]['target_floor_all']:
                target_pairs[dn] = target_floors
            elif 'target_floor' in config['datasets'][dn]:
                floors = []
                if config['datasets'][dn]['target_floor'] is None:
                    continue
                for floor in config['datasets'][dn]['target_floor']:
                    floors.append(floor)
                target_pairs[dn] = floors
    else:
        for target in targets:
            target_pairs[target] = target_floors

    # print target pairs
    for dn in target_pairs:
        logger.info('target pairs: {}'.format(dn))
        for floor in target_pairs[dn]:
            logger.info('    {}'.format(floor))

    for data_name in target_pairs:
        target_dir = os.path.join(results_dir, data_name)

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

        minx = 1000000000
        miny = 1000000000
        minz = 1000000000
        maxx = 0
        maxy = 0
        maxz = 0
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
        for floor in target_pairs[data_name]:
            logger.info('target floor: {}'.format(floor))
            target_floor_dir = os.path.join(target_dir, floor)
            if not os.path.exists(target_floor_dir):
                logger.info('target floor not found: {}'.format(floor))
                continue

            fp_fn = os.path.join(floorplans_dir, floor + '.png')
            fp_img = cv2.imread(fp_fn)

            # load score
            score_fn_list = glob.glob(os.path.join(target_floor_dir, 'score/*.csv'))
            score_fn_list.sort()
            score_fn_list = score_fn_list[::decimate]
            logger.info('load {} scores'.format(len(score_fn_list)))
            target_tra_dict = {}
            range_x = None
            range_y = None
            range_z = None
            score_yxz_dict = {}
            floormask_yxz_dict = {}
            for score_fn in score_fn_list:
                # create range_x and range_y
                if range_x is None:
                    # get floor mask size
                    floor_minx = 1000000000
                    floor_miny = 1000000000
                    floor_maxx = 0
                    floor_maxy = 0
                    with open(score_fn, 'r') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            x = int(row[0])
                            y = int(row[1])
                            if x < floor_minx:
                                floor_minx = x
                            if y < floor_miny:
                                floor_miny = y
                            if x > floor_maxx:
                                floor_maxx = x
                            if y > floor_maxy:
                                floor_maxy = y
                    floor_minx -= int(crop_step/2)
                    floor_miny -= int(crop_step/2)
                    floor_maxx += int(crop_step/2)
                    floor_maxy += int(crop_step/2)
                    logger.info('floor mask size = ({}, {})'.format(floor_maxx - floor_minx, floor_maxy - floor_miny))
                    # range_x = range(-(minx+maxx+floor_minx), floor_maxx-minx, align_step[0])
                    # range_y = range(-(miny+maxy+floor_miny), floor_maxy-miny, align_step[1])
                    # range_z = range(int(math.floor(minz)), int(math.ceil(maxz)), align_step[2])
                    range_x = range(-(maxx-floor_minx), floor_maxx-minx, align_step[0])
                    range_y = range(-(maxy-floor_miny), floor_maxy-miny, align_step[1])
                    range_z = range(int(math.floor(minz)), int(math.ceil(maxz)), align_step[2])

                    logger.info('range x: {} to {}'.format(range_x[0], range_x[-1]))
                    logger.info('range y: {} to {}'.format(range_y[0], range_y[-1]))
                    logger.info('range z: {} to {}'.format(range_z[0], range_z[-1]))
                    logger.info('total num: {}x{}x{}={}'.format(len(range_x), len(range_y), len(range_z), len(range_x)*len(range_y)*len(range_z)))

                # create score map of each translation(len(range_y)*len(range_x))
                shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                score_map = np.zeros((range_y[-1] + maxy + align_step[1], range_x[-1] + maxx + align_step[1], 1), dtype=float)
                score_map += -1    # for out-range of floormask
                with open(score_fn, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        x = int(row[0])
                        y = int(row[1])
                        score = float(row[2])
                        score_map[int(y-crop_step/2):int(y+crop_step/2),
                        int(x-crop_step/2):int(x+crop_step/2)] = score
                score_yxz = np.zeros((len(range_y), len(range_x), len(range_z)), dtype=float)
                score_yxz += -1    # for out-range of floormask
                xyz = tra_dict[shot_name]
                z = int(math.floor((xyz[2] - range_z[0])/align_step[2]))
                for y, tra_y in enumerate(range_y):
                    for x, tra_x in enumerate(range_x):
                        if xyz[1] + tra_y < 0 or xyz[0] + tra_x < 0:    # out of range
                            continue
                        score = score_map[xyz[1] + tra_y][xyz[0] + tra_x]
                        score_yxz[y][x][z] = score
                score_yxz_dict[shot_name] = score_yxz
                floormask_yxz_dict[shot_name] = score_yxz > -1
                # logger.info('finish to create score xyz for {}'.format(shot_name))
            logger.info('finish to create score map!!')

            # save scores
            # logger.info('saving score_xyz_dict to {}'.format(os.path.join(target_floor_dir, 'score_xyz_dict.pickle')))
            # with open(os.path.join(target_floor_dir, 'score_xyz_dict.pickle'), mode='wb') as f:
            #     pickle.dump(score_xyz_dict, f)
            #     logger.info('done!!')
            # logger.info('save floormask_xyz_dict to {}'.format(os.path.join(target_floor_dir, 'floormask_xyz_dict.pickle')))
            # with open(os.path.join(target_floor_dir, 'floormask_xyz_dict.pickle'), mode='wb') as f:
            #     pickle.dump(floormask_xyz_dict, f)
            #     logger.info('done!!')

            logger.info('summing up score')
            # create floormask ranking
            floormask_sum = np.zeros((len(range_y), len(range_x), len(range_z)), dtype=float)
            for shot_name in floormask_yxz_dict:
                floormask_sum += 1*floormask_yxz_dict[shot_name]

            # sort by index
            floormask_sum_1 = floormask_sum.reshape(-1)
            floormask_rank_1 = np.argsort(floormask_sum_1)[::-1]
            # get xyz
            floormask_rank = []
            for i in range(floormask_rank_1.shape[0]):
                val = floormask_rank_1[i]
                y = int(val/(floormask_sum.shape[1] * floormask_sum.shape[2]))
                val -= y * (floormask_sum.shape[1] * floormask_sum.shape[2])
                x = int(val/(floormask_sum.shape[2]))
                val -= x * floormask_sum.shape[2]
                z = val
                floormask_rank.append([x, y, z])

            # create score ranking
            score_sum = np.zeros((len(range_y), len(range_x), len(range_z)), dtype=float)
            for shot_name in score_yxz_dict:
                score_sum += score_yxz_dict[shot_name] * floormask_yxz_dict[shot_name]
            score_mean = score_sum/(floormask_sum + 1e-10)
            # sort by index
            score_mean_1 = score_mean.reshape(-1)
            score_rank_1 = np.argsort(score_mean_1)[::-1]
            # get xyz
            score_rank = []
            for i in range(score_rank_1.shape[0]):
                val = score_rank_1[i]
                y = int(val/(score_sum.shape[1] * score_sum.shape[2]))
                val -= y * (score_sum.shape[1] * score_sum.shape[2])
                x = int(val/(score_sum.shape[2]))
                val -= x * score_sum.shape[2]
                z = val

                score_rank.append([y, x, z])

            # fetch align info
            logger.info('creating result dict to save')
            align_info = []
            z_count = [0] * len(range_z)
            for i in range(len(score_rank)):
                info = {}
                y, x, z = score_rank[i]
                info['x'] = int(range_x[x])
                info['y'] = int(range_y[y])
                info['z'] = int(range_z[z])
                info['score'] = float(score_mean[y, x, z])
                info['in_floor'] = []
                for shot in floormask_yxz_dict:
                    if floormask_yxz_dict[shot][y, x, z]:
                        info['in_floor'].append(shot)
                info['fire'] = []
                for shot in score_yxz_dict:
                    if score_yxz_dict[shot][y, x, z] > fire_threshold:
                        info['fire'].append(shot)
                if len(info['fire']) < count_threshold:
                    continue

                if z_count[z] > max_save_znum - 1:
                    continue
                z_count[z] += 1

                align_info.append(info)
                if len(align_info) > max_save_num - 1:
                    break
            logger.info('z distribution {}'.format(z_count))

            # save align info
            out_info_fn = os.path.join(target_floor_dir, 'align_info.yaml')
            data = {}
            data['candidates'] = align_info
            with open(out_info_fn, 'w') as f:
                f.write(yaml.dump(data, default_flow_style=False))
            logger.info('save {} scores to {}'.format(len(align_info), out_info_fn))

