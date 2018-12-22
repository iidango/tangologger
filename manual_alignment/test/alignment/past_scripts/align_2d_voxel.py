#! /usr/bin/env python
# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import sys
sys.path.append('../../../..')

import argparse
import math
import cv2
import numpy as np
import csv
import glob
import yaml
import pickle
from multiprocessing import Pool
import shutil
import pickle
import copy
from mysettings import FileManager, DLConfig
import align_2d_cand

import logging
from logging import basicConfig, Formatter, FileHandler, getLogger, DEBUG
# log_format = '[%(asctime)s %(levelname)s] %(name)s: %(message)s'
log_format = '[%(asctime)s %(levelname)s] %(message)s'
formatter = Formatter(log_format)
basicConfig(level=DEBUG, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")
logger = getLogger(__name__)
fh = FileHandler('./log.txt')
fh.setFormatter(formatter)
logger.addHandler(fh)

class Config(object):
    def __init__(self, args):
        self.fm = FileManager(args.test_num_dir)
        self.fm.set_data_config(args.data)

        self.target_floors = args.target_floors
        self.targets = args.targets
        self.mask_dir = self.fm.wmask_dir()

        # self.plot_all = args.plot_all
        self.process_num = args.process_num
        self.eval_voxel = False
        self.load_align_result = False
        self.sort_by_z = args.sort_by_z
        self.merge = True
        self.plot_result = args.plot_result
        self.load_wmask = True
        self.create_mask_from_score = False
        # self.calc_correct = False if self.load_align_result else True
        self.calc_correct = True
        self.plot_distribution = True

        parameter = self.fm.get_config(args.config)
        self.pix_per_meter = parameter.get('pix_per_meter')
        self.crop_step = parameter.get('crop_step')
        self.align_step = parameter.get('align_step')
        self.align_voxel_size = parameter.get('align_voxel_size')
        self.merge_neighbor = parameter.get('merge_neighbor')
        self.decimate = parameter.get('align_decimate')
        self.fire_threshold = parameter.get('fire_threshold')
        self.good_consistency_threshold = parameter.get('good_consistency_threshold')
        self.hit_shot_count_threshold = parameter.get('hit_shot_count_threshold')
        self.floor_voxel_count_threshold = parameter.get('floor_voxel_count_threshold')
        self.max_save_num = parameter.get('max_save_num')
        self.max_save_grid_num = parameter.get('max_save_grid_num')
        self.non_floor_score = parameter.get('non_floor_score', None)
        self.search_grid_size = parameter.get('search_grid_size', 1)
        self.floor_height_in_step = self.align_voxel_size[2]//self.align_step[2]
        self.crop_voxel_ratio_x = self.crop_step//self.align_voxel_size[0]
        self.crop_voxel_ratio_y = self.crop_step//self.align_voxel_size[1]

    def get_target_pairs(self):
        return self.fm.get_target_pairs(self.target_floors, self.targets)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='create score map')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, default='alignment2d_config.yaml', help='load config yaml file(defalut=alignment2d_config.yaml)')
    # parser.add_argument('-a', '--plot_all', default=False, action='store_true', help='create for all floor(default=False)')
    parser.add_argument('-j', '--process_num', nargs='?', type=int, default='4', help='process number(default=4)')
    parser.add_argument('-m', '--mask_dir', nargs='?', type=str, default=None, help='path to walkable mask dir')
    # parser.add_argument('--load_align_result', default=False, action='store_true', help='load align result(default=False)')
    parser.add_argument('--sort_by_z', default=False, action='store_true', help='sort by z(default=False)')
    # parser.add_argument('--merge', default=False, action='store_true', help='merge results(default=False)')
    parser.add_argument('--plot_result', default=False, action='store_true', help='plot results(default=False)')
    # parser.add_argument('--eval_voxel', default=False, action='store_true', help='calc score by each voxel. non floor shot cannot be evaluated(20180521). (default=False).')
    args = parser.parse_args()

    # set args
    config = Config(args)

    # get target pairs
    target_pairs = config.get_target_pairs()
    for dn in target_pairs:
        logger.info('target pairs: {}'.format(dn))
        for floor in target_pairs[dn]:
            logger.info('    {}'.format(floor))

    for data_name in target_pairs:
        distribution_plot_data = {}

        # load trajectory
        tra_fn = config.fm.trajectory_fp(data_name)
        tra_dict = {}
        with open(tra_fn, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                k = row[0]
                x = int(row[1])
                y = int(row[2])
                z = float(row[4]) * config.pix_per_meter    # z will come in meter
                tra_dict[k] = [x, y, z]
        logger.info('load {} trajectory points from {}'.format(len(tra_dict), tra_fn))

        # calc trajectory size
        minx, miny, minz = 1000000000, 1000000000, 1000000000
        maxx, maxy, maxz = 0, 0, 0
        for shot in tra_dict:
            x, y, z = tra_dict[shot]
            minx, miny, minz = min(minx, x), min(miny, y), min(minz, z)
            maxx, maxy, maxz = max(maxx, x), max(maxy, y), max(maxz, z)
        logger.info('trajectory size = ({}, {}, {})'.format(maxx-minx, maxy-miny, int(math.ceil(maxz-minz))))

        actual_result = {}

        # calc soore for each floor
        for floor in target_pairs[data_name]:
            target_floor_dir = config.fm.t_floor_dir(data_name, floor)
            if not os.path.exists(target_floor_dir):
                logger.info('target floor not found: {}'.format(target_floor_dir))
                continue
            logger.info('target floor: {}'.format(floor))

            fp_fn = config.fm.floorplan_fp(floor)
            fp_img = cv2.imread(fp_fn)

            # load score
            score_fn_list = config.fm.score_fp_list(data_name, floor)
            score_fn_list.sort()
            score_fn_list = score_fn_list[::config.decimate]
            logger.info('load {} scores'.format(len(score_fn_list)))

            logger.info('create align result...')
            target_tra_dict = {}
            range_x, range_y, range_z = None, None, None
            score_yxz_dict = {}
            floormask_yxz_dict = {}
            score_map_count = None

            # create range_x and range_y
            floor_minx, floor_miny = 1000000000, 1000000000
            floor_maxx, floor_maxy = 0, 0
            ##  get floor mask size
            if config.load_wmask:
                if config.create_mask_from_score:    # create  load mask from score
                    score_fn = score_fn_list[0]
                    with open(score_fn, 'r') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            x = int(row[0])
                            y = int(row[1])
                            floor_minx, floor_miny = min(floor_minx, x), min(floor_miny, y)
                            floor_maxx, floor_maxy = max(floor_maxx, x), max(floor_maxy, y)
                else:    # create mask from mask image
                    mask_fn = config.fm.wmask_fp(floor)
                    mask_img = cv2.imread(mask_fn)
                    mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
                    # mask_img = cv2.dilate(mask_img, np.ones((5, 5), np.uint8), iterations=1)
                    # mask_img = cv2.dilate(mask_img, np.ones((5, 5), np.uint8), iterations=1)

                    mask_map = np.zeros((fp_img.shape[0]//config.align_voxel_size[0], fp_img.shape[1]//config.align_voxel_size[1]), dtype=bool)
                    mask_map_voxel = np.zeros((fp_img.shape[0], fp_img.shape[1]), dtype=bool)
                    for y in range(config.crop_voxel_ratio_y//2, mask_map.shape[0], config.crop_voxel_ratio_y):
                        for x in range(config.crop_voxel_ratio_y//2, mask_map.shape[1], config.crop_voxel_ratio_x):
                            if np.sum(mask_img[y*config.align_voxel_size[1]-config.crop_step//2: y*config.align_voxel_size[1]+config.crop_step//2, 
                                    x*config.align_voxel_size[0]-config.crop_step//2: x*config.align_voxel_size[0]+config.crop_step//2] > 0) > 0:
                                mask_map[y-config.crop_voxel_ratio_y//2:y+config.crop_voxel_ratio_y//2, x-config.crop_voxel_ratio_x//2:x+config.crop_voxel_ratio_x//2] = True
                                # mask_map_voxel[y*align_voxel_size[1]-crop_step//2: y*align_voxel_size[1]+crop_step//2, x*align_voxel_size[0]-crop_step//2: x*align_voxel_size[0]+crop_step//2] = True

                    # create range_x and range_y
                    ##  get walkable area mask size
                    mask_i = np.where(mask_map == True)
                    floor_minx, floor_miny = min(mask_i[1]) * config.align_voxel_size[1], min(mask_i[0]) * config.align_voxel_size[0]
                    floor_maxx, floor_maxy = max(mask_i[1]) * config.align_voxel_size[1], max(mask_i[0]) * config.align_voxel_size[0]
                    # create not floor map
                    not_floor = mask_map == False

                    # cv2.imwrite('/mnt/host/share/tmp/{}_mask_map.png'.format(floor), mask_map*255)
                    # cv2.imwrite('/mnt/host/share/tmp/{}_mask_ori.png'.format(floor), mask_img)
                    # cv2.imwrite('/mnt/host/share/tmp/{}_mask.png'.format(floor), mask_map_voxel*255)
                    # cv2.imwrite('/mnt/host/share/tmp/{}_mask.png'.format(floor), cv2.addWeighted(fp_img, 0.5, cv2.cvtColor((mask_map_voxel*255).astype(np.uint8), cv2.COLOR_GRAY2BGR), 0.5, 0.0))
                    # cv2.imwrite('/mnt/host/share/tmp/{}_mask_ori.png'.format(floor), cv2.addWeighted(fp_img, 0.5, cv2.cvtColor(mask_img.astype(np.uint8), cv2.COLOR_GRAY2BGR), 0.5, 0.0))
                    # cv2.imwrite('/mnt/host/share/tmp/{}.png'.format(floor), fp_img)
            else:    # not load wmask
                pass

            floor_minx -= int(config.crop_step/2)
            floor_miny -= int(config.crop_step/2)
            floor_maxx += int(config.crop_step/2)
            floor_maxy += int(config.crop_step/2)
            range_x = list(range(-(maxx-floor_minx), floor_maxx-minx, config.align_step[0]))
            range_y = list(range(-(maxy-floor_miny), floor_maxy-miny, config.align_step[1]))
            range_z = list(range(int(math.floor(minz)) - config.align_voxel_size[2], int(math.ceil(maxz)), config.align_step[2]))

            logger.info('floor mask size = ({}, {})'.format(floor_maxx - floor_minx, floor_maxy - floor_miny))
            logger.info('range x: {} to {}'.format(range_x[0], range_x[-1]))
            logger.info('range y: {} to {}'.format(range_y[0], range_y[-1]))
            logger.info('range z: {} to {}'.format(range_z[0], range_z[-1]))
            logger.info('total num: {}x{}x{}={}'.format(len(range_x), len(range_y), len(range_z), len(range_x)*len(range_y)*len(range_z)))

            ## load score map from csv
            score_map_dict = {}
            for score_fn in score_fn_list:
                shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                # score_map = np.zeros((fp_img.shape[0], fp_img.shape[1], 1), dtype=float)
                score_map = np.zeros((fp_img.shape[0]//config.align_voxel_size[1], fp_img.shape[1]//config.align_voxel_size[0], 1), dtype=float)

                score_map_voxel = np.zeros((fp_img.shape[0], fp_img.shape[1]), dtype=float)    # for debug
                if config.load_wmask and config.create_mask_from_score:
                    score_map += -1    # for out-range of floormask
                with open(score_fn, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        x = (int(row[0]) - config.crop_step//2)//config.align_voxel_size[0]    # center to topleft
                        y = (int(row[1]) - config.crop_step//2)//config.align_voxel_size[1]    # center to topleft

                        if config.load_wmask and not config.create_mask_from_score and mask_map[y][x] == False:
                            # score_map[int(y-crop_step/2)//align_voxel_size[1]:int(y+crop_step/2)//align_voxel_size[1],
                            #           int(x-crop_step/2)//align_voxel_size[0]:int(x+crop_step/2)//align_voxel_size[0]] = -1
                            score_map[y: y + config.crop_voxel_ratio_y,
                                    x: x + config.crop_voxel_ratio_x] = -1
                            continue

                        score = float(row[2])
                        # score_map[int(y-crop_step/2):int(y+crop_step/2), int(x-crop_step/2):int(x+crop_step/2)] = score
                        # score_map[int(y-crop_step/2)//align_voxel_size[1]:int(y+crop_step/2)//align_voxel_size[1],
                        #           int(x-crop_step/2)//align_voxel_size[0]:int(x+crop_step/2)//align_voxel_size[0]] = score
                        score_map[y: y + config.crop_voxel_ratio_y,
                                x: x + config.crop_voxel_ratio_x] = score    # center to topleft
                        score_map_voxel[y*config.align_voxel_size[1]:y*config.align_voxel_size[1]+config.crop_step, 
                                        x*config.align_voxel_size[0]:x*config.align_voxel_size[0]+config.crop_step] = score

                if config.load_wmask and not config.create_mask_from_score:
                    score_map[not_floor] = -1
                score_map_dict[shot_name] = score_map
                # cv2.imwrite('/mnt/host/share/tmp/{}_score_index.png'.format(shot_name), score_map*255)
                # cv2.imwrite('/mnt/host/share/tmp/{}_score_single.png'.format(shot_name), cv2.addWeighted(fp_img, 0.5, cv2.cvtColor((score_map_voxel*255).astype(np.uint8), cv2.COLOR_GRAY2BGR), 0.5, 0.0))
                # cv2.imwrite('/mnt/host/share/tmp/{}_score.png'.format(shot_name), score_map_voxel*255)
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
                not_hit_shot_list = []
                for score_fn in score_fn_list:
                    shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
                    if shot_name not in tra_dict:
                        continue
                    xyz = tra_dict[shot_name]
                    y = (xyz[1] + tra_y) // config.align_voxel_size[1]
                    x = (xyz[0] + tra_x) // config.align_voxel_size[0]
                    if y < 0 or y >= score_map_dict[shot_name].shape[0] or \
                                    x < 0 or x >= score_map_dict[shot_name].shape[1] or \
                                    score_map_dict[shot_name][y][x] < 0:    # out of range
                        not_hit_shot_list.append(shot_name)
                        continue
                    hit_shot_list.append(shot_name)
                if len(hit_shot_list) < config.hit_shot_count_threshold:
                    return result
                # count number of shots which hit each voxel
                # count_yxz = np.zeros((fp_img.shape[0], fp_img.shape[1], len(range_z)), dtype=int)
                count_yxz = np.zeros((fp_img.shape[0]//config.align_voxel_size[1], fp_img.shape[1]//config.align_voxel_size[0], len(range_z)), dtype=int)
                floor_voxel_count = [0 for z in range(len(range_z))]
                hit_shot_z_list = [[] for z in range(len(range_z))]
                for shot_name in hit_shot_list:
                    xyz = tra_dict[shot_name]
                    # y = ((xyz[1] + tra_y)//crop_step) * crop_step
                    # x = ((xyz[0] + tra_x)//crop_step) * crop_step
                    y = (xyz[1] + tra_y)//config.align_voxel_size[1]
                    x = (xyz[0] + tra_x)//config.align_voxel_size[0]

                    # z = int(math.floor((xyz[2] - range_z[0])/align_step[2]))
                    z = int((xyz[2] - range_z[0])//config.align_step[2])
                    for i in range(config.floor_height_in_step):
                        z_i = z - i
                        if count_yxz[y, x, z_i] == 0:
                            floor_voxel_count[z_i] += 1
                        # count_yxz[y:y+crop_step, x:x+crop_step, z] += 1
                        count_yxz[y, x, z_i] += 1
                        hit_shot_z_list[z_i].append(shot_name)
                # sum scores for each voxel
                for z in range(len(range_z)):
                    if floor_voxel_count[z] < config.floor_voxel_count_threshold:
                        continue
                    score = 0.0
                    in_floor = hit_shot_z_list[z]
                    fire = []
                    c = 0
                    for shot_name in hit_shot_z_list[z]:
                        xyz = tra_dict[shot_name]
                        y = (xyz[1] + tra_y) // config.align_voxel_size[1]
                        x = (xyz[0] + tra_x) // config.align_voxel_size[0]
                        s = score_map_dict[shot_name][y][x]
                        if s > config.fire_threshold:
                            fire.append(shot_name)
                        score += s/float(count_yxz[y][x][z]) if config.eval_voxel else s
                    
                    # add non floor shot score
                    if not config.eval_voxel and config.non_floor_score is not None:
                        score += config.non_floor_score * len(not_hit_shot_list)

                    # average
                    score /= float(floor_voxel_count[z]) if config.eval_voxel else float(len(score_fn_list))

                    if score < config.good_consistency_threshold:
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
                p = Pool(config.process_num)
                result = p.map_async(calc_score, arg).get(9999999)
                for r in result:
                    for z in range(len(range_z)):
                        if r[z] is not None:
                            results[z].append(r[z])
                p.close()

            logger.info('finish to count number of shots 2d!!')

            logger.info('creating result dict to save')
            align_result = []
            for z in range(len(range_z)):
                results[z].sort(key=lambda x: -x['score'])
                if len(results[z]) == 0:
                    continue
                logger.info('max score in z={:3d} is {:.8f}({}, {})(in {} candidates)'.format(-range_z[z], results[z][0]['score'], results[z][0]['x'], results[z][0]['y'], len(results[z])))
                for i, result in enumerate(results[z]):
                    # if i > max_save_znum - 1:
                    #     break
                    align_result.append(result)

            if config.calc_correct:
                # get tra_x, tra_y, tra_z
                tra_floor_fn = config.fm.trajectory_floor_fp(data_name, floor)
                tra_fn = config.fm.trajectory_fp(data_name)    # for getting tra_z
                if not os.path.exists(tra_floor_fn) or not os.path.exists(tra_fn):
                    logger.info('{} does not belong to {}'.format(data_name, floor))
                else:
                    tra_floor_dict = {}
                    c = 0
                    tra_x, tra_y, tra_z = 0, 0, 0
                    #  calc tra_x and tra_y and tra_z
                    with open(tra_floor_fn, 'r') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            k = row[0]
                            tra_x += int(row[1]) - tra_dict[k][0]
                            tra_y += int(row[2]) - tra_dict[k][1]
                            tra_z += float(row[4]) * config.pix_per_meter - tra_dict[k][2]
                            c += 1
                    tra_x /= c
                    tra_y /= c
                    tra_z /= c
                    tra_x, tra_y, tra_z = int(tra_x), int(tra_y), int(tra_z)
                    print(tra_x, tra_y, tra_z)
                    # tra_z = - range_z[int((- tra_z - range_z[0])//config.align_step[2])]

                    actual = calc_score([tra_y, tra_x])
                    # actual = [tmp for tmp in actual if tmp is not None]
                    for r in actual:
                        if r is not None:
                            logger.debug('actual results: {} ({}, {}, {})'.format(r['score'], r['x'], r['y'], r['z']))

                    # get actual z 
                    # actual = [tmp for tmp in actual if tmp is not None and tmp['z']==tra_z]
                    tra_z_index = int((- tra_z - range_z[0])//config.align_step[2])
                    max_shot_num = 0
                    actual_tmp = None
                    for i in range(max(tra_z_index - 2, 0), min(tra_z_index + 2, len(actual))):    # find max shot num around tra_z
                        if actual[i] is not None and len(actual[i]['in_floor']) > max_shot_num:
                            actual_tmp = actual[i]
                            max_shot_num = len(actual[i]['in_floor'])
                    if actual is None:
                        logger.warning('actual score cannot be calculated...')
                    else:
                        logger.info('actual score on {}: {:.8f} ({}, {}, {})'.format(floor, actual_tmp['score'], actual_tmp['x'], actual_tmp['y'], actual_tmp['z']))
                        actual = [actual_tmp]
                    actual_result[floor] = actual

            data = {'align_result': align_result, 'actual_result': actual_result, 'range_x': range_x, 'range_y': range_y, 'range_z': range_z}
            config.fm.save_align_result(data_name, floor, data)
            logger.info('save align result to {}'.format(config.fm.align_result_fp(data_name, floor)))

        if config.plot_result:
            logger.info('select and plot candidates: {}'.format(config.fm.align_result_fp(data_name, floor)))
            config_tmp = copy.copy(config)
            config_tmp.targets = [data_name]
            config_tmp.target_floors = target_pairs[data_name]
            align_2d_cand.run(config_tmp)
