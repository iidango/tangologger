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
from multiprocessing import Pool

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
    parser.add_argument('-p', '--process_num', nargs='?', type=int, default='4', help='process number(default=4)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    target_floors = args.target_floors
    targets = args.targets
    plot_all = args.plot_all
    process_num = args.process_num

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

    hit_shot_count_threshold = 20 if config is None else config['setting']['hit_shot_count_threshold']
    floor_voxel_count_threshold = 10 if config is None else config['setting']['floor_voxel_count_threshold']

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
                # logger.info('target floor not found: {}'.format(floor))
                continue
            logger.info('target floor: {}'.format(floor))

            fp_fn = os.path.join(floorplans_dir, floor + '.png')
            fp_img = cv2.imread(fp_fn)

            # load score
            score_fn_list = glob.glob(os.path.join(target_floor_dir, 'score/*.csv'))
            score_fn_list.sort()
            score_fn_list = score_fn_list[::decimate]
            logger.info('load {} scores'.format(len(score_fn_list)))
            target_tra_dict = {}
            range_x, range_y, range_z = None, None, None
            score_yxz_dict = {}
            floormask_yxz_dict = {}
            score_map_count = None

            # create range_x and range_y
            ##  get floor mask size
            score_fn = score_fn_list[0]
            floor_minx, floor_miny = 1000000000, 1000000000
            floor_maxx, floor_maxy = 0, 0
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
            ### == entire start ==
            range_x = range(-(maxx-floor_minx), floor_maxx-minx, align_step[0])
            range_y = range(-(maxy-floor_miny), floor_maxy-miny, align_step[1])
            ### == entire end ==
            ### == min start ==
            # range_x = range(-(minx-floor_minx), floor_maxx-maxx, align_step[0])
            # range_y = range(-(miny-floor_miny), floor_maxy-maxy, align_step[1])
            ### == min end ==
            range_z = range(int(math.floor(minz)), int(math.ceil(maxz)), align_step[2])
            logger.info('floor mask size = ({}, {})'.format(floor_maxx - floor_minx, floor_maxy - floor_miny))
            logger.info('range x: {} to {}'.format(range_x[0], range_x[-1]))
            logger.info('range y: {} to {}'.format(range_y[0], range_y[-1]))
            logger.info('range z: {} to {}'.format(range_z[0], range_z[-1]))
            logger.info('total num: {}x{}x{}={}'.format(len(range_x), len(range_y), len(range_z), len(range_x)*len(range_y)*len(range_z)))

            ## load score map from csv
            score_map_dict = {}
            for score_fn in score_fn_list:
                shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                score_map = np.zeros((fp_img.shape[0], fp_img.shape[1], 1), dtype=float)
                score_map += -1    # for out-range of floormask
                with open(score_fn, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        x = int(row[0])
                        y = int(row[1])
                        score = float(row[2])
                        score_map[int(y-crop_step/2):int(y+crop_step/2), int(x-crop_step/2):int(x+crop_step/2)] = score
                score_map_dict[shot_name] = score_map
            logger.info('load score map from csv')

            # create score map of each translation(len(range_y)*len(range_x))
            logger.info('start to create score map of each translation')
            results = [[] for z in range(len(range_z))]

            def calc_score(arg):
                tra_y = arg[0]
                tra_x = arg[1]
                result = [None for z in range(len(range_z))]

                # count number of shots which hit floor
                hit_shot_list = []
                for score_fn in score_fn_list:
                    shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                    xyz = tra_dict[shot_name]
                    y = xyz[1] + tra_y
                    x = xyz[0] + tra_x
                    if y < 0 or y >= score_map_dict[shot_name].shape[0] or \
                                    x < 0 or x >= score_map_dict[shot_name].shape[1] or \
                                    score_map_dict[shot_name][xyz[1] + tra_y][xyz[0] + tra_x] < 0:    # out of range
                        continue
                    hit_shot_list.append(shot_name)
                if len(hit_shot_list) < hit_shot_count_threshold:
                    return result
                # count number of shots which hit each voxel
                count_yxz = np.zeros((fp_img.shape[0], fp_img.shape[1], len(range_z)), dtype=int)
                floor_voxel_count = [0 for z in range(len(range_z))]
                hit_shot_z_list = [[] for z in range(len(range_z))]
                for shot_name in hit_shot_list:
                    xyz = tra_dict[shot_name]
                    y = ((xyz[1] + tra_y)//crop_step) * crop_step
                    x = ((xyz[0] + tra_x)//crop_step) * crop_step
                    # z = int(math.floor((xyz[2] - range_z[0])/align_step[2]))
                    z = int((xyz[2] - range_z[0])//align_step[2])
                    if count_yxz[y, x, z] == 0:
                        floor_voxel_count[z] += 1
                    count_yxz[y:y+crop_step, x:x+crop_step, z] += 1
                    hit_shot_z_list[z].append(shot_name)
                # sum scores for each voxel
                for z in range(len(range_z)):
                    if floor_voxel_count[z] < floor_voxel_count_threshold:
                        continue
                    score = 0.0
                    in_floor = hit_shot_z_list[z]
                    fire = []
                    c = 0
                    for shot_name in hit_shot_z_list[z]:
                        xyz = tra_dict[shot_name]
                        y = xyz[1] + tra_y
                        x = xyz[0] + tra_x
                        s = score_map_dict[shot_name][y][x]
                        if s > fire_threshold:
                            fire.append(shot_name)
                        score += s/float(count_yxz[y][x][z])

                    # average
                    score /= float(floor_voxel_count[z])

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
            out_info_fn = os.path.join(target_floor_dir, 'align_result.yaml')
            data = {}
            data['candidates'] = align_result
            with open(out_info_fn, 'w') as f:
                f.write(yaml.dump(data, default_flow_style=False))
            logger.info('save {} scores to {}'.format(len(align_result), out_info_fn))

