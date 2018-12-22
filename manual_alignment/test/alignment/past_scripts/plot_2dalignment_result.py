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
import shutil
import yaml

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument('test_num_dir', type=str, help='path to data name dir to be processed')
    parser.add_argument('-p', '--parameter', nargs='?', type=str, default='parameter.yaml', help='load parameter yaml file(default=parameter.yaml)')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, help='load config yaml file')
    # parser.add_argument('-d', '--results_dir', nargs='?', type=str, default='results', help='results dir name(default=results)')
    parser.add_argument('-o', '--target_data_config', nargs='?', type=str, default=None, help='target data config(default: same as data)')
    parser.add_argument('-z', '--sort_by_z', default=False, action='store_true', help='sort by z(default=False)')
    parser.add_argument('-m', '--merge', default=False, action='store_true', help='merge results(default=False)')
    # parser.add_argument('--eval_entire', default=True, action='store_false', help='calc score by entire average(default=True)')
    parser.add_argument('--reset_output', default=False, action='store_true', help='reset output dir(default=False)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    target_floors = args.target_floors
    targets = args.targets
    sort_by_z = args.sort_by_z
    merge = args.merge
    parameter_fn = os.path.join(test_num_dir, args.parameter)
    data_dir = os.path.join(test_num_dir, os.path.splitext(args.data)[0])
    data_config_fn = os.path.join(test_num_dir, args.data)
    target_data_config_fn = data_config_fn if args.target_data_config is None else os.path.join(test_num_dir, args.target_data_config)
    results_dir = os.path.join(data_dir, 'score')
    # eval_entire = args.eval_entire
    reset_output = args.reset_output

    # results_dir = os.path.join(test_num_dir, args.results_dir)

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

    logger.info('load meta yaml file: {}'.format(parameter_fn))
    with open(parameter_fn, 'r') as f:
        parameter = yaml.load(f)

    decimate = parameter['setting']['align_decimate']
    voxel_size = parameter['setting']['align_voxel_size']

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
                tra_dict[k] = [x, y]
        logger.info('load {} trajectory points from {}'.format(len(tra_dict), tra_fn))

        minx = 1000000000
        miny = 1000000000
        maxx = 0
        maxy = 0
        for shot in tra_dict:
            x, y = tra_dict[shot]
            if x < minx:
                minx = x
            if y < miny:
                miny = y
            if x > maxx:
                maxx = x
            if y > maxy:
                maxy = y
        logger.info('trajectory size = ({}, {})'.format(maxx-minx, maxy-miny))
        for floor in target_pairs[data_name]:
            target_floor_dir = os.path.join(target_dir, floor)
            if not os.path.exists(target_floor_dir):
                logger.warning('target floor not found: {}'.format(floor))
                continue
            fp_fn = os.path.join(floorplans_dir, floor + '.png')

            logger.info('align to {}'.format(fp_fn))
            fp_img = cv2.imread(fp_fn)

            # load score
            score_fn_list = glob.glob(os.path.join(target_floor_dir, 'score/*.csv'))
            score_fn_list.sort()
            score_fn_list = score_fn_list[::decimate]
            score_fn_list = [os.path.splitext(os.path.basename(x))[0] + '.png' for x in score_fn_list]
            if len(score_fn_list) == 0:    # plot entire trajectory if score not found
                score_fn_list = list(tra_dict.keys())
                logger.info('plort entire trajectory')
            logger.info('load {} scores'.format(len(score_fn_list)))

            # load good data
            # align_info_fn = os.path.join(target_floor_dir, 'align_result_e.yaml'if eval_entire else 'align_result.yaml')
            align_info_fn = os.path.join(target_floor_dir, 'align_result.yaml')
            if not os.path.exists(align_info_fn):
                logger.warning('align info not found: {}'.format(target_floor_dir))
                continue
            logger.info('load align info yaml file: {}'.format(align_info_fn))
            with open(align_info_fn, 'r') as f:
                data = yaml.load(f)

            data['candidates'].sort(key=lambda x: x['z'])
            data['candidates'].sort(key=lambda x: -x['score'])

            # sort by z
            if sort_by_z:
                data['candidates'].sort(key=lambda x: x['z'])

            # merge results
            if merge:
                valid_cands = []
                for cand in data['candidates']:
                    if len(list(filter(lambda x: abs(cand['x'] - x['x']) < voxel_size[0] * 3 and abs(cand['y'] - x['y']) < voxel_size[1] * 2 and abs(cand['z'] - x['z']) < voxel_size[2] * 1, valid_cands))) == 0:
                        valid_cands.append(cand)
                data['candidates'] = valid_cands

            # create output dir
            alignment_result_dir = os.path.join(target_floor_dir, 'alignment_result')
            if os.path.exists(alignment_result_dir):
                logger.info('remove: {}'.format(alignment_result_dir))
                shutil.rmtree(alignment_result_dir)
            os.mkdir(alignment_result_dir)

            for i, info in enumerate(data['candidates']):
                # load base image
                fp_img = cv2.imread(fp_fn)

                trax = int(info['x'])
                tray = int(info['y'])

                # plot trajectory
                for shot in score_fn_list:    # here will cause error if DECIMATE is different with align info
                    if shot not in tra_dict:
                        continue
                    x, y = tra_dict[shot][0] + trax, tra_dict[shot][1] + tray

                    if y in range(fp_img.shape[0]) and x in range(fp_img.shape[1]):
                        if shot in info['fire']:
                            cv2.circle(fp_img, (x, y),  5, (0, 0, 255), -1)
                        elif shot in info['in_floor']:
                            cv2.circle(fp_img, (x, y),  5, (255, 0, 0), -1)
                        else:
                            cv2.circle(fp_img, (x, y),  5, (0, 0, 0), -1)

                # save image file
                # if sort_by_z:
                #     out_img_fn = os.path.join(alignment_result_dir, '{:04d}_{}.png'.format(i, info['z']))
                # else:
                #     out_img_fn = os.path.join(alignment_result_dir, '{:04d}.png'.format(i))
                out_img_fn = os.path.join(alignment_result_dir, '{:04d}_{:04d}_{}.png'.format(i, int(info['score']*10000), info['z']))
                cv2.imwrite(out_img_fn, fp_img)
                logger.info("save {}".format(out_img_fn))
