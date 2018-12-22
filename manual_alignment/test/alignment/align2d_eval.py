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
from mysettings import FileManager, DLConfig
from cand_selector import selector1
import align2d_config

import logging
from logging import basicConfig, Formatter, FileHandler, getLogger, INFO
# log_format = '[%(asctime)s %(levelname)s] %(name)s: %(message)s'
log_format = '[%(asctime)s %(levelname)s] %(message)s'
formatter = Formatter(log_format)
basicConfig(level=INFO, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")
logger = getLogger(__name__)
fh = FileHandler('./log.txt')
fh.setFormatter(formatter)
logger.addHandler(fh)

def find_neighbor_caididate(cands, target, dist=25):    # dist in pix
    tx, ty, tz = target['x'], target['y'], target['z']
    for i, cand in enumerate(cands):
        if (cand['x'] - tx)**2 + (cand['y'] - ty)**2 + (cand['z'] - tz)**2 < dist**2:
            return i, cand
    return None, None

def run(config):
    # get target pairs
    target_pairs = config.get_target_pairs()
    # for dn in target_pairs:
    #     logger.info('target pairs: {}'.format(dn))
    #     for floor in target_pairs[dn]:
    #         logger.info('    {}'.format(floor))

    results = {}
    for data_name in target_pairs:
        results[data_name] = {}
        for floor in target_pairs[data_name]:
            # load align result
            # logger.info('load align result from {}'.format(config.fm.align_result_fp(data_name, floor)))
            data = config.fm.load_align_result(data_name, floor)
            if data is None:
                logger.warning('{}-{} eval result not found'.format(data_name, floor))
                continue

            actual_result = data['actual_result']

            if floor not in actual_result or len(actual_result[floor]) == 0:    # data_name does not belong to floor
                continue
            actual = actual_result[floor][0]
            logger.info('{} - {} actual score: {:.8f} ({}, {}, {})'
                .format(data_name, floor, actual['score'], actual['x'], actual['y'], actual['z']))

            # load single align cands
            # logger.info('load single align cands from {}'.format(config.fm.single_align_cands_fp(data_name, floor)))
            align_result = config.fm.load_single_align_cands(data_name, floor)

            rank, cand = find_neighbor_caididate(align_result['candidates'], actual)

            if rank is None:
                logger.info('actual postion not found...')
            else:
                logger.info('appear in {}th candidate: {:.8f}, ({}, {}, {})'.format(rank, cand['score'], cand['x'], cand['y'], cand['z']))
            results[data_name][floor] = {'actual': actual, 'rank': rank, 'cand': cand}

        
    logger.info('evaluation result')
    for dn in results:
        for floor in results[dn]:
            result = results[dn][floor]
            if result['rank'] is None:
                logger.info('[{} - {}] {} not found'
                    .format(dn, floor, [result['actual']['x'], result['actual']['y'], result['actual']['z']]))
            else:
                logger.info('[{} - {}] {} is appear in {}th cand'
                    .format(dn, floor, [result['actual']['x'], result['actual']['y'], result['actual']['z']], result['rank']))
    config.fm.save_single_align_eval(results)
    logger.info('save eval result to {}'.format(config.fm.single_align_eval_fp()))

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
    parser.add_argument('--sort_by_z', default=False, action='store_true', help='sort by z(default=False)')
    args = parser.parse_args()

    # set args
    config = align2d_config.Align2dConfig(args)

    run(config)
