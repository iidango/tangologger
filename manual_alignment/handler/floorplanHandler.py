#! /usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os
import cv2

import mylogger


def plotShotPoses(shots, floorplan, dataset_path, out_fn):
    """
    :type shots: dict[str, scripts.myopensfm.types.Shot]
    :type floorplan: scripts.myopensfm.types.Floorplan
    :type dataset_path: str
    :type out_fn: str
    """

    floorplans_path = os.path.join(dataset_path, "floorplans")

    floorplan_img = cv2.imread(os.path.join(floorplans_path, floorplan.id))
    # floorplan_img *= 0
    # floorplan_img += 255


    for shot in shots:
        pose = shots[shot].pose
        xyz = pose.getXYZ()

        # load and convert to image coordinate
        x = floorplan_img.shape[1]/2 + int(floorplan.metadata.pix_per_meter * xyz[0])
        y = floorplan_img.shape[0]/2 - int(floorplan.metadata.pix_per_meter * xyz[1])

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
        xy = floorplan.pose2pix(pose)

        datas.append((shot, xy[0], xy[1], shots[shot].metadata.capture_time))

    datas.sort()

    with open(os.path.join(dataset_path, out_fn), 'w') as f:
        writer = csv.writer(f, lineterminator='\n')  # 改行コード（\n）を指定しておく
        writer.writerows(datas)  # 2次元配列も書き込める
        mylogger.logger.info("save " + os.path.join(dataset_path, out_fn))

