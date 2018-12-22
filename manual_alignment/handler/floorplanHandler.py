#! /usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import cv2
import numpy as np
import math

import mylogger


def plotShotPoses(shots, floorplan, dataset_path, out_fn, ref_shots={}):
    """
    :type shots: dict[str, scripts.myopensfm.types.Shot]
    :type floorplan: scripts.myopensfm.types.Floorplan
    :type dataset_path: str
    :type out_fn: str
    :type ref_shots: dict[str, scripts.myopensfm.types.Shot]
    """

    floorplans_path = os.path.join(dataset_path, "floorplans")

    floorplan_img = cv2.imread(os.path.join(floorplans_path, floorplan.id))
    # floorplan_img *= 0
    # floorplan_img += 255

    for shot in ref_shots:
        pose = ref_shots[shot].pose
        # load and convert to image coordinate
        x, y = floorplan.pose2pix(pose)
        cv2.circle(floorplan_img, (x, y),  5, (0, 0, 0), -1)

    for shot in shots:
        pose = shots[shot].pose
        # load and convert to image coordinate
        x, y = floorplan.pose2pix(pose)
        cv2.circle(floorplan_img, (x, y),  5, (255, 0, 0), -1)

    cv2.imwrite(os.path.join(dataset_path, out_fn), floorplan_img)
    mylogger.logger.info("save " + os.path.join(dataset_path, out_fn))

def save2DTrajectory(shots, floorplan, dataset_path, out_fn):
    """
    :type shots: dict[str, scripts.myopensfm.types.Shot]
    :type floorplan: scripts.myopensfm.types.Floorplan
    :type dataset_path: str
    :type out_fn: str
    """

    floorplans_path = os.path.join(dataset_path, "floorplans")
    floorplan_img = cv2.imread(os.path.join(floorplans_path, floorplan.id))

    datas = []

    for shot in shots:
        pose = shots[shot].pose
        # load and convert to image coordinate
        x, y = floorplan.pose2pix(pose)
        z = floorplan.heightInMeter(pose)

        r_vec = shots[shot].viewing_direction()
        angle_rad = np.arctan2(r_vec[0], r_vec[1])

        datas.append((shot, x, y, shots[shot].metadata.capture_time, z, angle_rad))
    datas.sort()

    with open(os.path.join(dataset_path, out_fn), 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(datas)
        mylogger.logger.info("save " + os.path.join(dataset_path, out_fn))

