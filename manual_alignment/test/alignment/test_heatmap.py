# coding: utf-8

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import glob
import cv2
import csv
import yaml
from alignment import heatmap

# usage:
#     /usr/bin/python2.7 /grad/1/iida/project/navimap/floorplan/scripts/test/alignment/test_heatmap.py /grad/1/iida/project/floorplan/alignment/nu/test6/tmp2 /grad/1/iida/project/floorplan/alignment/nu/test6/val
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='create heatmap')
    parser.add_argument('test_num_dir', type=str, help='path to data name dir to be processed')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-c', '--config', nargs='?', type=str, default='test_config.yaml', help='load config yaml file(default=test_config.yaml)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    target_floors = args.target_floors
    targets = args.targets

    results_dir = os.path.join(test_num_dir, 'results')
    datasets_dir = os.path.join(test_num_dir, '../data/datasets')
    floorplans_dir = os.path.join(test_num_dir, '../data/floorplan/floorplans')

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

    crop_size = 150 if config is None else config['setting']['crop_size']
    crop_step = 10 if config is None else config['setting']['crop_step']

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
        for floor in target_pairs[data_name]:
            if config is not None and not config['datasets'][data_name]['target_floor_all'] and floor not in config['datasets'][data_name]['target_floor']:
                continue

            target_dir = os.path.join(results_dir, data_name)
            target_floor_dir = os.path.join(target_dir, floor)
            fp_fn = os.path.join(floorplans_dir, floor + '.png')
            logger.info('load base floorplan image {}'.format(fp_fn))

            # create output dir
            heatmap_dir = os.path.join(target_floor_dir, 'heatmap/')
            if not os.path.exists(heatmap_dir):
                os.mkdir(heatmap_dir)
            # load score
            score_fn_list = glob.glob(os.path.join(target_floor_dir, 'score/*.csv'))
            score_fn_list.sort()
            logger.info('load {} scores'.format(len(score_fn_list)))

            target_dataset_dir = os.path.join(datasets_dir, data_name)
            for score_fn in score_fn_list:
                o_fn = os.path.splitext(os.path.join(heatmap_dir, os.path.basename(score_fn)))[0]+'.png'
                hm_img = heatmap.getOverlayHeatmap(score_fn, fp_fn)    # heat map image
                # pano_fn = os.path.join(target_dataset_dir, 'images_northup/{}.png'.format(os.path.splitext(os.path.basename(score_fn))[0]))

                hm_img = heatmap.getOverlayHeatmap(score_fn, fp_fn, window_size=(crop_size, crop_size), step=crop_step)
                cv2.imwrite(o_fn, cv2.cvtColor(hm_img, cv2.COLOR_RGB2BGR))
                logger.info('save to {}'.format(o_fn))

    logger.info('All Process Done!!')
