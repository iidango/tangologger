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
import numpy as np
import csv
import cv2
import glob
import yaml
import pickle
from multiprocessing import Pool
import shutil
import pickle
from mysettings import FileManager, DLConfig
from cand_selector import selector3 as cand_selector
import align2d_config

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

def run(config):
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

            # load align result
            logger.info('load align result from {}'.format(config.fm.align_result_fp(data_name, floor)))
            data = config.fm.load_align_result(data_name, floor)
            align_result = data['align_result']
            actual_result = data['actual_result']
            range_x, range_y, range_z, z_list = data['range_x'], data['range_y'], data['range_z'], data['floor_heights']

            # merge results
            logger.info('start merge {} results'.format(len(align_result)))
            # align_result, output_grid_num = cand_selector.select_cand(config, align_result, range_x, range_y, range_z)
            align_result, output_grid_num = cand_selector.select_cand(config, align_result, range_x, range_y, z_list)
            logger.info('finish merge neighbor results to {}'.format(len(align_result)))
            logger.info('align result distribution {}'.format(output_grid_num))

            # save align result
            # out_info_fn = os.path.join(target_floor_dir, 'align_result_e.yaml'if eval_entire else 'align_result.yaml')
            # out_info_fn = os.path.join(target_floor_dir, 'align_result.yaml')
            data = {}
            data['candidates'] = align_result
            if floor in actual_result:    # save actual result 
                data['actual_result'] = actual_result[floor] 
            config.fm.save_single_align_cands(data_name, floor, data)
            logger.info('save {} scores to {}'.format(len(align_result), config.fm.single_align_cands_fp(data_name, floor)))

            if config.plot_distribution:
                distribution_plot_data[floor] = []
                for result in align_result:
                    distribution_plot_data[floor].append(result['score'])
                    if len(distribution_plot_data[floor]) > 5:
                        break

            ####################
            # plot result
            ####################
            shots = [os.path.splitext(os.path.basename(x))[0] + '.png' for x in score_fn_list]

            def save_plot_result(info, out_img_fn, plot_all=False):
                # load base image
                fp_img = cv2.imread(fp_fn)

                trax = int(info['x'])
                tray = int(info['y'])

                # plot trajectory
                if plot_all:
                    for shot in tra_dict:
                        x, y = tra_dict[shot][0] + trax, tra_dict[shot][1] + tray
                        if y in range(fp_img.shape[0]) and x in range(fp_img.shape[1]):
                            cv2.circle(fp_img, (x, y), 5, (255, 0, 0), -1)
                else:
                    for shot in shots:
                        if shot not in tra_dict:
                            logger.warning('shot({}) not found in trajectocy'.format(shot))
                            continue
                        x, y = tra_dict[shot][0] + trax, tra_dict[shot][1] + tray

                        if y in range(fp_img.shape[0]) and x in range(fp_img.shape[1]):
                            if shot in info['fire']:
                                cv2.circle(fp_img, (x, y), 5, (0, 0, 255), -1)
                            elif shot in info['in_floor']:
                                cv2.circle(fp_img, (x, y), 5, (255, 0, 0), -1)
                            else:
                                cv2.circle(fp_img, (x, y), 5, (0, 0, 0), -1)

                cv2.imwrite(out_img_fn, fp_img)
                logger.info("save {}".format(out_img_fn))

            if config.plot_result:
                # data['candidates'].sort(key=lambda x: x['z'])
                # data['candidates'].sort(key=lambda x: -x['score'])

                # # sort by z
                # if config.sort_by_z:
                #     data['candidates'].sort(key=lambda x: x['z'])

                # create output dir
                alignment_result_dir = os.path.join(target_floor_dir, 'alignment_result')
                if os.path.exists(alignment_result_dir):
                    logger.info('remove: {}'.format(alignment_result_dir))
                    shutil.rmtree(alignment_result_dir)
                os.mkdir(alignment_result_dir)

                for i, info in enumerate(data['candidates']):
                    out_img_fn = os.path.join(alignment_result_dir, 
                        '{:04d}_{:04d}_{}_{}_{}.png'.format(i, int(info['score']*10000), info['x'], info['y'], info['z']))
                    save_plot_result(info, out_img_fn, config.plot_all_track_points)
            
                if config.calc_correct and floor in actual_result:
                    # remove existing file
                    remove_fn_list = glob.glob(os.path.join(target_floor_dir, 'actual*.png'))
                    for f in remove_fn_list:
                        os.remove(f)
                        logger.info('remove {}'.format(f))

                    for actual in actual_result[floor]:
                        if actual is not None:
                            save_plot_result(actual, os.path.join(target_floor_dir, 
                                'actual_{:04d}_{}_{}_{}.png'.format(int(actual['score']*10000), actual['x'], actual['y'], actual['z'])))
        
        ######################################
        ## plot distribution
        ######################################
        if config.plot_distribution:
            plt.figure()
            plt.title(data_name)
            x_val = 0
            label = []
            label_x = []
            if config.calc_correct and actual_result is not None:
                vals = []
                actual_label = ''
                for floor in actual_result:
                    for actual in actual_result[floor]:
                        if actual is not None:
                            vals.append(actual['score'])
                            actual_label += 'ac_{}\n'.format(floor)
                plt.bar(range(x_val, x_val+len(vals)), vals, align='center')
                label.append(actual_label)
                label_x.append(x_val + len(vals)/2.0 - 1)
                x_val += len(vals) + 1
            for k in distribution_plot_data.keys():
                vals = []
                for val in distribution_plot_data[k]:
                    vals.append(val)
                plt.bar(range(x_val, x_val+len(vals)), vals, align='center')
                label.append(k)
                label_x.append(x_val+len(vals)/2.0 - 1)
                x_val += len(vals) + 1
            plt.xticks(label_x, label)
            o_fn = config.fm.distribution_fp(data_name)
            plt.savefig(o_fn)
            logger.info('save distribution to {}'.format(o_fn))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='create score map')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, default='alignment2d_config.yaml', help='load config yaml file(defalut=alignment2d_config.yaml)')
    # parser.add_argument('-a', '--plot_all', default=False, action='store_true', help='create for all floor(default=False)')
    parser.add_argument('-j', '--process_num', nargs='?', type=int, default='4', help='process number(default=4)')
    # parser.add_argument('-m', '--mask_dir', nargs='?', type=str, default=None, help='path to walkable mask dir')
    parser.add_argument('-p', '--plot_all_track_points', default=False, action='store_true', help='plot all track points(default=False)')
    args = parser.parse_args()

    # set args
    config = align2d_config.Align2dConfig(args)

    run(config)
