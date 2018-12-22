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
    parser = argparse.ArgumentParser(description='create score map')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
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
    target_floors = args.target_floors
    targets = args.targets
    plot_all = args.plot_all
    process_num = args.process_num
    parameter_fn = os.path.join(test_num_dir, args.parameter)
    data_dir = os.path.join(test_num_dir, os.path.splitext(args.data)[0])
    data_config_fn = os.path.join(test_num_dir, args.data)
    target_data_config_fn = data_config_fn if args.target_data_config is None else os.path.join(test_num_dir, args.target_data_config)
    results_dir = os.path.join(data_dir, 'score')

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
            # if 'target_floor_all' in config['datasets'][dn] and config['datasets'][dn]['target_floor_all']:
            #     target_pairs[dn] = target_floors
            # elif 'target_floor' in config['datasets'][dn]:
            #     floors = []
            #     if config['datasets'][dn]['target_floor'] is None:
            #         continue
            #     for floor in config['datasets'][dn]['target_floor']:
            #         floors.append(floor)
            #     target_pairs[dn] = floors
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

        meta_fn = os.path.join(datasets_dir, '{}/meta.yaml'.format(data_name))
        with open(meta_fn, 'r') as f:
            meta = yaml.load(f)
        logger.info('load meta data {}'.format(meta_fn))

        for floor_fn in meta['floorplans']:
            target_floor_dir = os.path.join(target_dir, os.path.splitext(floor_fn)[0])
            if not os.path.exists(target_floor_dir):
                logger.info('target floor not found: {}'.format(target_floor_dir))
                continue
            logger.info('target floor: {}'.format(floor_fn))

            fp_fn = os.path.join(floorplans_dir, floor_fn)
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

            ## load score map from csv
            score_map_dict = {}
            for score_fn in score_fn_list:
                shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                score_map = np.zeros((fp_img.shape[0], fp_img.shape[1], 1), dtype=float)
                # score_map = np.zeros((fp_img.shape[0]//align_voxel_size[1], fp_img.shape[1]//align_voxel_size[0], 1), dtype=float)
                score_map += -1    # for out-range of floormask
                with open(score_fn, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        x = int(row[0])
                        y = int(row[1])
                        score = float(row[2])
                        score_map[int(y-crop_step/2):int(y+crop_step/2), int(x-crop_step/2):int(x+crop_step/2)] = score
                        # score_map[(y-crop_step/2)//align_voxel_size[1]:(y+crop_step/2)//align_voxel_size[1], (x-crop_step/2)//align_voxel_size[0]:(x+crop_step/2)//align_voxel_size[0]] = score    # center to topleft
                score_map_dict[shot_name] = score_map
            logger.info('load score map from csv')

            # create score map of each translation(len(range_y)*len(range_x))
            logger.info('start to create score map of each translation')
            # results = [[] for z in range(len(range_z))]

            # calc_score
            def calc_score(arg):
                tra_y = arg[0]
                tra_x = arg[1]
                tra_z = arg[2]

                # count number of shots which hit floor
                hit_shot_list = []
                count_yx = np.zeros((fp_img.shape[0], fp_img.shape[1]), dtype=int)
                # floor_voxel_count = 0
                floor_voxel_count = 0
                for score_fn in score_fn_list:
                    shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                    if shot_name not in tra_dict:

                        continue
                    xyz = tra_dict[shot_name]
                    # y = (xyz[1] + tra_y) // align_voxel_size[1]
                    # x = (xyz[0] + tra_x) // align_voxel_size[0]
                    y = ((xyz[1] + tra_y)//crop_step) * crop_step
                    x = ((xyz[0] + tra_x)//crop_step) * crop_step
                    z = xyz[2] + tra_z
                    if not (-align_step[2]/2 < z < align_step[2]/2):
                        continue
                    if y < 0 or y >= score_map_dict[shot_name].shape[0] or \
                                    x < 0 or x >= score_map_dict[shot_name].shape[1] or \
                                    score_map_dict[shot_name][y][x] < 0:    # out of range
                        continue

                    if count_yx[y, x] == 0:
                        floor_voxel_count += 1
                    count_yx[y:y+crop_step, x:x+crop_step] += 1
                    hit_shot_list.append(shot_name)

                # sum scores for each voxel
                score = 0.0
                fire = []
                c = 0
                for shot_name in hit_shot_list:
                    xyz = tra_dict[shot_name]
                    # y = (xyz[1] + tra_y) // align_voxel_size[1]
                    # x = (xyz[0] + tra_x) // align_voxel_size[0]
                    y = int(xyz[1] + tra_y)
                    x = int(xyz[0] + tra_x)
                    s = score_map_dict[shot_name][y][x]
                    if s > fire_threshold:
                        fire.append(shot_name)
                    score += s/float(count_yx[y][x])

                # average
                score /= float(floor_voxel_count)

                result = {}
                result['x'] = int(tra_x)
                result['y'] = int(tra_y)
                result['z'] = int(tra_z)
                result['score'] = float(score)
                result['in_floor'] = hit_shot_list
                result['fire'] = fire

                return result

            # get tra_x, tra_y, tra_z
            tra_floor_fn = os.path.join(datasets_dir, '{}/2dtrajectory_{}.csv'.format(data_name, os.path.splitext(floor_fn)[0]))
            tra_floor_dict = {}
            c = 0
            tra_x = 0
            tra_y = 0
            tra_z = 0
            with open(tra_floor_fn, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    k = row[0]
                    tra_x += int(row[1]) - tra_dict[k][0]
                    tra_y += int(row[2]) - tra_dict[k][1]
                    tra_z += float(row[4]) * pix_per_meter - tra_dict[k][2]
                    c += 1
            tra_x /= c
            tra_y /= c
            tra_z /= c
            logger.info('translation: ({}, {}, {})'.format(tra_x, tra_y, tra_z))
            result = calc_score([tra_y, tra_x, tra_z])

            # save results
            logger.info('creating result dict to save')
            out_info_fn = os.path.join(target_floor_dir, 'actual_score.yaml')
            data = {}
            data['actual'] = result
            with open(out_info_fn, 'w') as f:
                f.write(yaml.dump(data, default_flow_style=False))

            # plot data
            # load base image
            fp_img = cv2.imread(fp_fn)

            trax = int(result['x'])
            tray = int(result['y'])

            # plot trajectory
            for shot in score_fn_list:    # here will cause error if DECIMATE is different with align info
                shot = os.path.splitext(os.path.basename(shot))[0] + '.png'
                if shot not in tra_dict:
                    continue
                x, y = tra_dict[shot][0] + trax, tra_dict[shot][1] + tray

                if y in range(fp_img.shape[0]) and x in range(fp_img.shape[1]):
                    if shot in result['fire']:
                        cv2.circle(fp_img, (x, y),  5, (0, 0, 255), -1)
                    elif shot in result['in_floor']:
                        cv2.circle(fp_img, (x, y),  5, (255, 0, 0), -1)
                    else:
                        cv2.circle(fp_img, (x, y),  5, (0, 0, 0), -1)

            # save image file
            out_img_fn = os.path.join(target_floor_dir, 'actual_{}.png'.format(result['z']))
            cv2.imwrite(out_img_fn, fp_img)
            logger.info("save {}".format(out_img_fn))
            break

