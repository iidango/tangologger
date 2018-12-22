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
from alignment import heatmap

# usage:
#     /usr/bin/python2.7 /grad/1/iida/project/navimap/floorplan/scripts/test/alignment/test_heatmap.py /grad/1/iida/project/floorplan/alignment/nu/test6/tmp2 /grad/1/iida/project/floorplan/alignment/nu/test6/val
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='create heatmap (not used. please use test_heatmap_viz)')
    parser.add_argument('test_num_dir', type=str, help='path to data name dir to be processed')
    parser.add_argument('data_name', type=str, help='data name')
    parser.add_argument('floor', type=str, help='floor name of the data')
    parser.add_argument('floorplan_dir', type=str, help='path to floorplan dir')
    parser.add_argument('panorama_dir', type=str, help='path to panorama dir')
    parser.add_argument('crop_size', nargs='?', type=int, default=150, help='crop window size(default=150)')
    parser.add_argument('crop_step', nargs='?', type=int, default=10, help='crop step size(default=10)')
    parser.add_argument('-f', '--floor_names', nargs='*', type=str, default=[], help='target floor names(default=all)')
    args = parser.parse_args()

    # set args
    test_num_dir = args.test_num_dir
    data_name = args.data_name
    floor = args.floor
    floorplan_dir = args.floorplan_dir
    panorama_dir = args.panorama_dir
    crop_size = args.crop_size
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
    data_pano_dir = os.path.join(panorama_dir, '{}/{}'.format(floor, data_name))
    logger.info('load panorama from {}'.format(data_pano_dir))

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

    for floor_name in floor_names:
        target_dir = os.path.join(data_name_dir, floor_name)
        fp_fn = os.path.join(floorplan_dir, 'floorplans/' + floor_name + '.png')
        logger.info('plot to {}'.format(fp_fn))

        # create dir
        heatmap_dir = os.path.join(target_dir, 'heatmap/')
        if not os.path.exists(heatmap_dir):
            os.mkdir(heatmap_dir)
        # load score
        score_fn_list = glob.glob(os.path.join(target_dir, 'score/*.csv'))
        score_fn_list.sort()
        logger.info('load {} scores'.format(len(score_fn_list)))

        for score_fn in score_fn_list:
            o_fn = os.path.splitext(os.path.join(heatmap_dir, os.path.basename(score_fn)))[0]+'.png'
            hm_img = heatmap.getOverlayHeatmap(score_fn, fp_fn)    # heat map image

            pano_fn = os.path.join(data_pano_dir, os.path.splitext(os.path.basename(score_fn))[0] + '.png')

            # plot correct position if the correct floor
            if floor == floor_name:
                p = tra_dict[pano_fn.split('/')[-1]]
                cv2.circle(hm_img, (p[0], p[1]), 10, (255, 0, 0), -1)

            # create image fig(panorama and heatmap)
            plt.figure(figsize=(16, 12))
            G = gridspec.GridSpec(2, 5)

            ax = plt.subplot(G[0, 0])
            ax.tick_params(labelbottom="off", bottom="off")
            ax.tick_params(labelleft="off", left="off")
            ax.set_xticklabels([])
            plt.imshow(cv2.cvtColor(cv2.imread(pano_fn), cv2.COLOR_BGR2RGB))

            ax = plt.subplot(G[0:, 1:])
            ax.tick_params(labelbottom="off", bottom="off")
            ax.tick_params(labelleft="off", left="off")
            ax.set_xticklabels([])
            plt.imshow(hm_img)

            plt.tight_layout()
            plt.savefig(o_fn)
            plt.close('all')
            logger.info('save to {}'.format(o_fn))

    logger.info('All Process Done!!')
