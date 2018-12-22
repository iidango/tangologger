#! /usr/bin/env python
# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import sys
sys.path.append('../../../..')
import argparse

from mysettings import FileManager, DLConfig
import align2d_config
import align2d_search
import align2d_merge
import align2d_eval
import align2d_show_eval

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='create score map')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, default='alignment2d_config.yaml', help='load config yaml file(defalut=alignment2d_config.yaml)')
    parser.add_argument('-j', '--process_num', nargs='?', type=int, default='4', help='process number(default=4)')
    parser.add_argument('--search', default=False, action='store_true', help='run search(default=False)')
    parser.add_argument('--merge', default=False, action='store_true', help='run merge(default=False)')
    parser.add_argument('--eval', default=False, action='store_true', help='run eval(default=False)')
    parser.add_argument('--show_eval', default=False, action='store_true', help='run eval(default=False)')
    args = parser.parse_args()

    # set args
    config = align2d_config.Align2dConfig(args)

    if args.search:
        logger.warning('currently, this option is not supported')
        logger.warning('please run align2d_searcy.py')
    if args.merge:
        align2d_merge.run(config)
    if args.eval:
        align2d_eval.run(config)
    if args.show_eval:
        align2d_show_eval.run(config)
