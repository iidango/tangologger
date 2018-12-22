#! /usr/bin/env python
# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import sys
sys.path.append('../../../..')


from mysettings import FileManager, DLConfig

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


class Align2dConfig(object):
    def __init__(self, args):
        args = vars(args)

        self.fm = FileManager(args.get('test_num_dir'))
        self.fm.set_data_config(args.get('data'))

        self.target_floors = args.get('target_floors')
        self.targets = args.get('targets')
        self.mask_dir = self.fm.wmask_dir()

        # self.plot_all = args.plot_all
        self.process_num = args.get('process_num')
        self.load_align_result = False
        self.plot_result = True
        self.load_wmask = True
        self.create_mask_from_score = False
        # self.eval_voxel = False
        # self.calc_correct = False if self.load_align_result else True
        self.calc_correct = True
        self.plot_distribution = True
        self.plot_all_track_points = args.get('plot_all_track_points', False)

        # load config file
        parameter = self.fm.get_config(args.get('config'))
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
        self.non_floor_score = parameter.get('non_floor_score', 0.0)
        self.search_grid_size = parameter.get('search_grid_size', 1)
        self.crop_voxel_ratio_x = self.crop_step // self.align_voxel_size[0]
        self.crop_voxel_ratio_y = self.crop_step // self.align_voxel_size[1]

    def get_target_pairs(self):
        return self.fm.get_target_pairs(self.target_floors, self.targets)
