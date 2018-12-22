#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json

import numpy as np

import mylogger
from utils import io
from utils import types


def loadReconstruction(fn, apply_shotoffset = False):
    """
    :type fn: str
    :rtype reconstructions: list[scripts.myopensfm.types.Reconstruction]
    """
    with open(fn) as f:
        mylogger.logger.info("loading " + fn)
        reconstructions = io.reconstructions_from_json(json.load(f))
        mylogger.logger.info("Done")

    if apply_shotoffset:
        mylogger.logger.info("Apply shot offset")
        for reconstruction in reconstructions:
            shots_offset = np.identity(4, dtype=float)
            shots_offset[:3, :4] = reconstruction.metadata.shots_offset.get_Rt()
            setOffset(reconstruction, shots_offset)

    return reconstructions

def saveReconstructions(reconstructions, fn):
    """
    :type reconstructions: list[scripts.myopensfm.types.Reconstruction]
    :type fn: str
    """
    # with open(fn, 'wb') as f:
    with open(fn, 'w') as f:    # for python3
        mylogger.logger.info("saving " + fn)
        obj = io.reconstructions_to_json(reconstructions)
        io.json_dump(obj, f)
        mylogger.logger.info("Done")

def ignorePoints(reconstruction):
    """
    :type reconstruction: scripts.myopensfm.types.Reconstruction
    """
    reconstruction.points = {}

def addAxisPoint(reconstruction):
    """
    :type reconstruction: scripts.myopensfm.types.Reconstruction
    """
    for shot in reconstruction.shots:
        pose = reconstruction.shots[shot].pose

        center_point = types.Point()
        center_point.id = shot
        center_point.color = [255, 255, 255]
        center_point.coordinates = pose.getXYZ()
        reconstruction.add_point(center_point)

        x_point = types.Point()
        x_point.id = "x" + shot
        x_point.color = [255, 0, 0]
        x_point.coordinates = pose.transform_inverse(np.array([1, 0, 0]))
        reconstruction.add_point(x_point)
        y_point = types.Point()
        y_point.id = "y" + shot
        y_point.color = [0, 255, 0]
        y_point.coordinates = pose.transform_inverse(np.array([0, 1, 0]))
        reconstruction.add_point(y_point)
        z_point = types.Point()
        z_point.id = "z" + shot
        z_point.color = [0, 0, 255]
        z_point.coordinates = pose.transform_inverse(np.array([0, 0, 1]))
        reconstruction.add_point(z_point)

        # z_point = types.Point()
        # z_point.id = "direction" + shot
        # z_point.color = [255, 0, 0]
        # z_point.coordinates = reconstruction.shots[shot].viewing_direction() + center_point.coordinates
        # reconstruction.add_point(z_point)

def setOffset(reconstruction, rt):
    """
    :type reconstruction: scripts.myopensfm.types.Reconstruction
    :type rt: numpy.array
    """
    rt = np.linalg.inv(rt)

    for s in reconstruction.shots:
        shot = reconstruction.shots[s]
        shot.pose.transposeWorldCoordinate(rt, inv = True)

def subsampleShot(reconstruction, num):
    """
    :type reconstruction: scripts.myopensfm.types.Reconstruction
    :type num: sampling number
    """

    s_list = []
    for s in reconstruction.shots:
        shot = reconstruction.shots[s]
        s_list.append(shot)

    s_list.sort(key=lambda x:x.id)
    s_list = s_list[::num]

    reconstruction.shots = {}
    for s in s_list:
        reconstruction.add_shot(s)

def setExpandAxis(reconstruction, scale_xyz):
    """
    
    :type reconstruction: scripts.myopensfm.types.Reconstruction
    :type rt: numpy.array
    """

    for s in reconstruction.shots:
        shot = reconstruction.shots[s]
        xyz = shot.pose.getXYZ()
        rt = np.array([[1, 0, 0, xyz[0] * (scale_xyz[0]-1)],
                       [0, 1, 0, xyz[1] * (scale_xyz[1]-1)],
                       [0, 0, 1, xyz[2] * (scale_xyz[2]-1)],
                       [0, 0, 0, 1]], dtype=float)
        shot.pose.transposeWorldCoordinate(rt)
        # break

    for f in reconstruction.floorplans:
        floorplan = reconstruction.floorplans[f]
        xyz = floorplan.pose.getXYZ()
        rt = np.array([[1, 0, 0, xyz[0] * (scale_xyz[0]-1)],
                       [0, 1, 0, xyz[1] * (scale_xyz[1]-1)],
                       [0, 0, 1, xyz[2] * (scale_xyz[2]-1)],
                       [0, 0, 0, 1]], dtype=float)
        floorplan.pose.transposeWorldCoordinate(rt)

def applyAll(reconstructions, func):
    """
    :type reconstructions: List[scripts.myopensfm.types.Reconstruction]
    """
    for reconstruction in reconstructions:
        func(reconstruction)

def createTrajectory(reconstruction):
    """
    :param Reconstruction reconstruction:
    :return Trajectory trajectory:
    """

    trajectory = types.Trajectory()
    trajectory.id = reconstruction.metadata.name

    for s in reconstruction.shots:
        trajectory.add_shot(reconstruction.shots[s])

    trajectory.sort()
    return trajectory

