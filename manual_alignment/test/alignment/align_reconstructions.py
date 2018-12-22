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

from handler import  reconstructionHandler
from handler import floorplanHandler
from alignment import align
from utils import types
import mylogger

IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
TRAJECTORY_FILENAME = "2dtrajectory.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("dataroot_dir", help="path to dataroot dir to be referenced")
    parser.add_argument("data_dir", help="path to data dir to be processed")
    parser.add_argument('data_name', type=str, help='data name to be processed')
    args = parser.parse_args()

    dataroot = os.path.join(args.dataroot_dir, args.data_name)
    dataset = os.path.join(args.data_dir, args.data_name)

    # load reconstruction file
    recon_in_fn = os.path.join(dataroot, IN_RECONSTRUCTION_FILENAME)
    reconstructions = reconstructionHandler.loadReconstruction(recon_in_fn, apply_shotoffset=True)

    for reconstruction in reconstructions:
        # load first floorplan
        floorplan = reconstruction.floorplans[reconstructions[0].floorplans.keys()[0]]
        floorplan.set_dataroot(os.path.join(dataroot, 'floorplans'))
        fp_img = floorplan.get_img()
        pix_per_meter = floorplan.metadata.pix_per_meter

        # create trajectory
        mylogger.logger.info('create trajectory')
        trajectory = reconstructionHandler.createTrajectory(reconstruction)

        # create corresponding score map
        mylogger.logger.info('set floorplan coresponding score map')
        trajectory.setFPCScore(floorplan, os.path.join(dataset, 'score'))

        # set trajectory to top left
        mylogger.logger.info('search highest score')
        x_best, y_best, score_best = align.alignTrajectory(trajectory, floorplan, 10)

        # setTrajectory to best position
        trajectory.translateTo(floorplan, x_best, y_best)

        tra_img_fn = os.path.join(dataset, 'trajectory_aligned.png')
        tra_csv_fn = os.path.join(dataset, 'trajectory_aligned.csv')
        align.saveTrajectory(trajectory, floorplan, tra_img_fn, tra_csv_fn)

