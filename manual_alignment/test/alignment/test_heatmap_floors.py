# coding: utf-8

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import glob
import cv2
import yaml
from alignment import heatmap

# usage:
#     /usr/bin/python2.7 /grad/1/iida/project/navimap/floorplan/scripts/test/alignment/test_heatmap.py /grad/1/iida/project/floorplan/alignment/nu/test6/tmp2 /grad/1/iida/project/floorplan/alignment/nu/test6/val
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='alignment script')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
    parser.add_argument('-p', '--parameter', nargs='?', type=str, default='parameter.yaml', help='load parameter yaml file(default=parameter.yaml)')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-o', '--target_data_config', nargs='?', type=str, default=None, help='target data config(default: same as data)')
    args = parser.parse_args()


    test_num_dir = args.test_num_dir
    target_floors = args.target_floors
    parameter_fn = os.path.join(test_num_dir, args.parameter)
    data_dir = os.path.join(test_num_dir, os.path.splitext(args.data)[0])
    data_config_fn = os.path.join(test_num_dir, args.data)
    target_data_config_fn = data_config_fn if args.target_data_config is None else os.path.join(test_num_dir, args.target_data_config)
    floormask_dir = os.path.join(data_dir, 'floormask')

    # set parameters
    print('load meta yaml file: {}'.format(parameter_fn))
    with open(parameter_fn, 'r') as f:
        parameter = yaml.load(f)
    crop_size = parameter['setting']['crop_size']
    crop_step = parameter['setting']['crop_step']

    # load datasets
    print('load target data yaml file: {}'.format(target_data_config_fn))
    with open(target_data_config_fn, 'r') as f:
        data_config = yaml.load(f)
    FLOORPLANS_DIR = data_config['path']['floorplans']
    DATASETS_DIR = data_config['path']['datasets']

    if target_floors is None:
        target_floors = []
        for floor in data_config['floors']:
            if data_config['floors'][floor]['val']:
                target_floors.append(floor)

    print('target floors')
    print(target_floors)

    # main
    for floor in target_floors:
        target_dir = os.path.join(floormask_dir, floor)

        score_fn = os.path.join(target_dir, 'floor_mask.csv')
        if not os.path.exists(score_fn):
            print('score file not found: {}'.format(score_fn))
            continue

        fp_fn = os.path.join(FLOORPLANS_DIR, '{}.png'.format(floor))
        o_fn = os.path.join(target_dir, 'floor_mask.png')
        hm_img = heatmap.getOverlayHeatmap(score_fn, fp_fn, window_size=(crop_size, crop_size), step=crop_step, binary=True)
        cv2.imwrite(o_fn, cv2.cvtColor(hm_img, cv2.COLOR_RGB2BGR))

        print('save to {}'.format(o_fn))

