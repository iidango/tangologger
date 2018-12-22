# coding: utf-8

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))

import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from alignment import heatmap
import os
import glob
import cv2
import csv
import yaml

# usage:
#     /usr/bin/python2.7 /grad/1/iida/project/navimap/floorplan/scripts/test/alignment/test_heatmap_viz.py /grad/1/iida/project/floorplan/alignment/nu/test6/tmp2 /grad/1/iida/project/floorplan/alignment/nu/test6/val /local-scratch/iida/project/navimap/floorplan/data/nu/gTgghhhhhhhhhhhhhhhh
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='create score map')
    parser.add_argument('test_num_dir', help='path to data dir to be processed')
    parser.add_argument('-p', '--parameter', nargs='?', type=str, default='parameter.yaml', help='load parameter yaml file(default=parameter.yaml)')
    parser.add_argument('-d', '--data', nargs='?', type=str, default='data.yaml', help='load data yaml file(default=data.yaml)')
    parser.add_argument('-f', '--target_floors', nargs='*', type=str, help='target floor names')
    parser.add_argument('-t', '--targets', nargs='*', type=str, help='target data names')
    parser.add_argument('-a', '--plot_all', default=False, action='store_true', help='create for all floor(default=False)')
    parser.add_argument('-b', '--binary', default=False, action='store_true', help='plot binary value(default=False)')
    parser.add_argument('-c', '--config', nargs='?', type=str, default='test_config.yaml', help='load config yaml file(default=test_config.yaml)')
    parser.add_argument('-o', '--target_data_config', nargs='?', type=str, default=None, help='target data config(default: same as data)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    target_floors = args.target_floors
    targets = args.targets
    plot_all = args.plot_all
    binary = args.binary
    target_floors = args.target_floors
    parameter_fn = os.path.join(test_num_dir, args.parameter)
    data_dir = os.path.join(test_num_dir, os.path.splitext(args.data)[0])
    data_config_fn = os.path.join(test_num_dir, args.data)
    target_data_config_fn = data_config_fn if args.target_data_config is None else os.path.join(test_num_dir, args.target_data_config)
    results_dir = os.path.join(data_dir, 'score')

    # logger setting
    log_fn = os.path.join(os.path.join(data_dir), 'log.txt')
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

    # set parameters
    logger.info('load meta yaml file: {}'.format(parameter_fn))
    with open(parameter_fn, 'r') as f:
        parameter = yaml.load(f)
    crop_size = parameter['setting']['crop_size']
    crop_step = parameter['setting']['crop_step']
    normal_image = parameter['setting']['normal_image'] if 'normal_image' in parameter['setting'] else False

    # load datasets
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
        for floor in target_pairs[data_name]:
            target_dir = os.path.join(results_dir, data_name)
            target_dataset_dir = os.path.join(datasets_dir, data_name)

            # load trajectory file
            tra_fn = os.path.join(target_dataset_dir, '2dtrajectory_{}.csv'.format(floor))
            tra_dict = None
            if os.path.exists(tra_fn):
                tra_dict = {}
                with open(tra_fn, 'r') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        k = row[0]
                        x = int(row[1])
                        y = int(row[2])
                        tra_dict[k] = [x, y]
                logger.info('load {} trajectory points from {}'.format(len(tra_dict), tra_fn))
            elif not plot_all:
                logger.info('skip: {} - {}'.format(data_name, floor))
                continue

            target_floor_dir = os.path.join(target_dir, floor)
            fp_fn = os.path.join(floorplans_dir, floor + '.png')
            logger.info('load base floorplan image {}'.format(fp_fn))

            # create output dir
            if not os.path.exists(target_floor_dir):
                continue
            heatmap_viz_dir = os.path.join(target_floor_dir, 'heatmap_viz/')
            if not os.path.exists(heatmap_viz_dir):
                os.mkdir(heatmap_viz_dir)
            # load score
            score_fn_list = glob.glob(os.path.join(target_floor_dir, 'score/*.csv'))
            score_fn_list.sort()
            logger.info('load {} scores'.format(len(score_fn_list)))

            for score_fn in score_fn_list:
                if normal_image:
                    img2_fn = os.path.join(target_dataset_dir, 'images_front/{}.png'.format(os.path.splitext(os.path.basename(score_fn))[0]))
                else:
                    img2_fn = os.path.join(target_dataset_dir, 'images_northup/{}.png'.format(os.path.splitext(os.path.basename(score_fn))[0]))

                shot = os.path.basename(img2_fn)
                if not plot_all and not shot in tra_dict:
                    continue

                hm_img = heatmap.getOverlayHeatmap(score_fn, fp_fn, window_size=(crop_size, crop_size), step=crop_step, binary=binary)
                img2_img = cv2.cvtColor(cv2.imread(img2_fn), cv2.COLOR_BGR2RGB)

                # plot correct position if the correct floor
                if tra_dict is not None and shot in tra_dict:
                    p = tra_dict[shot]
                    cv2.circle(hm_img, (p[0], p[1]), 10, (255, 0, 0), -1)

                # create visualize image
                # plt.figure(figsize=(16, 12))
                fig = plt.figure(figsize=(16, 12))
                G = gridspec.GridSpec(2, 5)

                # ax = plt.subplot(G[0, 0])
                ax = fig.add_subplot(G[0, 0])
                ax.tick_params(labelbottom="off", bottom="off")
                ax.tick_params(labelleft="off", left="off")
                ax.set_xticklabels([])
                plt.imshow(img2_img)

                # ax = plt.subplot(G[0:, 1:])
                ax = fig.add_subplot(G[0:, 1:])
                ax.tick_params(labelbottom="off", bottom="off")
                ax.tick_params(labelleft="off", left="off")
                ax.set_xticklabels([])
                plt.imshow(hm_img)

                plt.tight_layout()
                out_fn = os.path.join(heatmap_viz_dir, shot)
                plt.savefig(out_fn)

                plt.close('all')
                logger.info('save: {}'.format(out_fn))
    logger.info('All Process Done!!')
