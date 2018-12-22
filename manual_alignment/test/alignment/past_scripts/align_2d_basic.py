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

from handler import  reconstructionHandler
from handler import floorplanHandler
from alignment import align
from utils import types

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument('test_num_dir', type=str, help='path to data name dir to be processed')
    parser.add_argument('data_name', type=str, help='data name')
    parser.add_argument('floor', type=str, help='floor name of the data')
    parser.add_argument('floorplan_dir', type=str, help='path to floorplan dir')
    parser.add_argument('crop_step', nargs='?', type=int, default=10, help='crop step size(default=10)')
    parser.add_argument('-f', '--floor_names', nargs='*', type=str, default=[], help='target floor names(default=all)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    data_name = args.data_name
    floor = args.floor
    floorplan_dir = args.floorplan_dir
    crop_step = args.crop_step
    floor_names = args.floor_names
    data_name_dir = os.path.join(test_num_dir, data_name)

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

    # set target floorplan
    if len(floor_names) == 0:    # all floorplans
        floor_names = [x for x in os.listdir(data_name_dir) if not 0 is x.find('.')]
    logger.info('target floor names')
    logger.info(floor_names)

    # main
    tra_fn = os.path.join(floorplan_dir, 'trajectory/{}/{}.csv'.format(floor, data_name))
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

    for floor_name in floor_names:
        target_dir = os.path.join(data_name_dir, floor_name)
        fp_fn = os.path.join(floorplan_dir, 'floorplans/' + floor_name + '.png')
        logger.info('align to {}'.format(fp_fn))
        fp_img = cv2.imread(fp_fn)

        # load score
        score_fn_list = glob.glob(os.path.join(target_dir, 'score/*.csv'))
        score_fn_list.sort()
        logger.info('load {} scores'.format(len(score_fn_list)))

        score_map_dic = {}
        for score_fn in score_fn_list:
            shot_name = os.path.splitext(os.path.basename(score_fn))[0]+'.png'
            score_map = np.zeros((fp_img.shape[0], fp_img.shape[1], 1), dtype=float)

            with open(score_fn, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    x = int(row[0])
                    y = int(row[1])
                    score = float(row[2])
                    score_map[int(y-crop_step/2):int(y+crop_step/2),
                    int(x-crop_step/2):int(x+crop_step/2)] = score
            score_map_dic[shot_name] = score_map


        # search the most high score
        x_best = 0
        y_best = 0
        score_best = 0.0

        logger.debug('start to search highest score')
        for y in range(-miny, fp_img.shape[0] - maxy, crop_step/2):
            for x in range(-minx, fp_img.shape[1] - maxx, crop_step/2):
                score = 0.
                for shot in score_map_dic:
                    s = score_map_dic[shot][tra_dict[shot][1] + y, tra_dict[shot][0] + x]
                    if s is None:
                        continue
                    else:
                        score += s

                if score > score_best:
                    score_best = score
                    x_best = x
                    y_best = y
                    # mylogger.logger.info('update score!!:{} in ({},{})'.format(score_best, x_best, y_best))
        logger.info('best score:{} in ({},{})'.format(score_best, x_best, y_best))

        # plot and save trajectory
        data = []
        for shot in tra_dict:
            x, y = tra_dict[shot][0] + x_best, tra_dict[shot][1] + y_best
            data.append((shot, x, y))

            cv2.circle(fp_img, (x, y),  5, (255, 0, 0), -1)
        data.sort()

        # save image file
        out_img_fn = os.path.join(target_dir, 'trajectory_aligned.png')
        cv2.imwrite(out_img_fn, fp_img)
        logger.info("save {}".format(out_img_fn))

        # save csv file
        out_csv_fn = os.path.join(target_dir, 'trajectory_aligned.csv')
        with open(out_csv_fn, 'w') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerows(data)
        logger.info("save {}".format(out_csv_fn))

        # save align info
        out_info_fn = os.path.join(target_dir, 'align_info.txt')
        with open(out_info_fn, 'w') as f:
            f.write('x_best,{}\n'.format(x_best))
            f.write('y_best,{}\n'.format(y_best))
            f.write('score_best,{}\n'.format(score_best))
            f.write('num,{}\n'.format(len(score_map_dic)))
            f.write('score_average,{}\n'.format(score_best/len(score_map_dic)))
        logger.info("save {}".format(out_info_fn))

