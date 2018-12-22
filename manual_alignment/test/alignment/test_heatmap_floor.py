# coding: utf-8

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import glob
import cv2
from alignment import heatmap

# usage:
#     /usr/bin/python2.7 /grad/1/iida/project/navimap/floorplan/scripts/test/alignment/test_heatmap.py /grad/1/iida/project/floorplan/alignment/nu/test6/tmp2 /grad/1/iida/project/floorplan/alignment/nu/test6/val
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='alignment script')
    parser.add_argument('data_dir', type=str, help='path to data dir to be processed')
    parser.add_argument('data_name', type=str, help='data name to be processed')
    parser.add_argument('crop_size', nargs='?', type=int, default=150, help='crop window size(default=150)')
    parser.add_argument('crop_step', nargs='?', type=int, default=10, help='crop step size(default=10)')
    args = parser.parse_args()

    # set args
    data_dir = args.data_dir    # = '/grad/1/iida/project/floorplan/alignment/nu/test6/tmp2'
    data_name = args.data_name    # = 'eng2_2f_w'
    crop_size = args.crop_size
    crop_step = args.crop_step

    dataset_dir = os.path.join(data_dir, data_name)

    # logger setting
    log_fn = os.path.join(data_dir, 'log.txt')
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

    # main
    score_fn = os.path.join(dataset_dir, 'floor_mask.csv')

    # fp_fn = os.path.join(data_dir, '../val/floorplan/floorplans/{}/floorplan.png'.format(data_name))
    # fp_fn = os.path.join(data_dir, '../data/floorplan/floorplans/{}.png'.format(data_name))
    fp_fn = os.path.join(data_dir, '../../data/floorplan/floorplans/{}.png'.format(data_name))
    o_fn = os.path.join(dataset_dir, 'floor_mask.png')
    hm_img = heatmap.getOverlayHeatmap(score_fn, fp_fn, window_size=(crop_size, crop_size), step=crop_step)
    cv2.imwrite(o_fn, cv2.cvtColor(hm_img, cv2.COLOR_RGB2BGR))

    logger.info('save to {}'.format(o_fn))

