#! /usr/bin/env python
# -*- coding: utf-8 -*-

from utils import types
from utils import io
import sys
import json
import numpy as np
import os
import csv
import cv2
import math
import mylogger


class TangoPose(types.Pose):
    """
    Define camera pose of tango output
    
    Attributes:
        rotation (vector): the rotation vector.
        translation (vector): the rotation vector.
    """

    def __init__(self, xyz=np.zeros(3), quaternion=np.zeros(4)):
        self.xyz = xyz
        self.quaternion = quaternion

    @property
    def quaternion(self):
        """Rotation in quaternion format."""
        return self._quaternion

    @quaternion.setter
    def quaternion(self, value):
        if len(value) == 4:
            value = np.array(value, dtype=float)
            if abs(np.sum(value ** 2) - 1.0) > 1e-6:
                raise ValueError('Quaternion must be normalized')
            # self._quaternion = (value if value[3] > 0 else -value)
            self._quaternion = value
        else:
            raise TypeError("quaternion must have 3 or 4 elements")

    @property
    def xyz(self):
        """xyz in world coordinate system vector."""
        return self._xyz

    @xyz.setter
    def xyz(self, value):
        self._xyz = np.asarray(value, dtype=float)

    def setRotationAndTranslation(self, rotate_to_shot_direction=True):
        rt = np.identity(4, dtype=float)
        self.xyz[0] = - self.xyz[0] # tmp
        rt[:3, 3] = self.xyz.T
        rotation_mat = np.identity(4, dtype=float)
        rotation_mat[:3, :3] = self.getRotationMatrixFromQuaternion()
        rt = np.dot(rotation_mat, rt)

        # rotate world coordinate to shot direction
        if rotate_to_shot_direction:
            shot_direction = np.array([
                [0, -1, 0, 0],
                [0, 0, -1, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1],
            ])
            rt = np.dot(rt, shot_direction)

            # tmp start
            shot_direction = np.array([
                [-1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ])
            rt = np.dot(shot_direction, rt)
            # tmp end

        rotation = cv2.Rodrigues(rt[:3,:3])[0][:,0]
        translation = rt[:3,3].T
        self.rotation = rotation
        self.translation = translation

    def getRotationMatrixFromQuaternion(self):
        x, y, z, w = self.quaternion
        x = -x  # tmp
        w = -w  # tmp
        xx2 = 2 * x * x
        yy2 = 2 * y * y
        zz2 = 2 * z * z
        ww2 = 2 * w * w
        xy2 = 2 * x * y
        wz2 = 2 * w * z
        zx2 = 2 * z * x
        wy2 = 2 * w * y
        yz2 = 2 * y * z
        wx2 = 2 * w * x

        rmat = np.zeros((3, 3), float)
        # rmat[0, 0] = 1. - yy2 - zz2
        # rmat[0, 1] = xy2 - wz2
        # rmat[0, 2] = zx2 + wy2
        # rmat[1, 0] = xy2 + wz2
        # rmat[1, 1] = 1. - xx2 - zz2
        # rmat[1, 2] = yz2 - wx2
        # rmat[2, 0] = zx2 - wy2
        # rmat[2, 1] = yz2 + wx2
        # rmat[2, 2] = 1. - xx2 - yy2
        rmat[0, 0] = 1. - zz2 - ww2
        rmat[0, 1] = yz2 - wx2
        rmat[0, 2] = wy2 + zx2
        rmat[1, 0] = yz2 + wx2
        rmat[1, 1] = 1. - xx2 - yy2 -ww2
        rmat[1, 2] = wz2 - xy2
        rmat[2, 0] = wy2 - zx2
        rmat[2, 1] = wz2 + xy2
        rmat[2, 2] = 1. - xx2 - yy2 -zz2

        return rmat

def loadTangoPose(fn, camera, fps = 3.):
    """
    csv format: timestamp(unixtime[sec]),x[m],y[m],z[m],rotQ1,rotQ2,rotQ3,rotQ4
    
    :type fn: str
    :type camera: scripts.myopensfm.types.Camera
    :type fps: float
    :rtype reconstruction: scripts.myopensfm.types.Reconstruction
    """
    reconstruction = types.Reconstruction()
    reconstruction.add_camera(camera)

    with open(fn) as f:
        reader = csv.reader(f)

        t_pose = 0.
        pre_pose_data = None
        t_video = 0.
        count = 0
        if fps == 0:
            period = 0
        else:
            period = 1./fps

        for pose_data in reader:
            if pre_pose_data is None:
                pre_pose_data = pose_data

            t_pose += float(pose_data[0]) - float(pre_pose_data[0])
            if t_pose > period * (count + 1):
                pose = TangoPose(np.array(pose_data[1:4]), np.array(pose_data[4:8]))
                pose.setRotationAndTranslation()
                metadata = types.ShotMetadata()
                metadata.capture_time = float(pose_data[0])
                shot = types.Shot()
                shot.id = "{0:08d}".format(count) + ".png"
                shot.camera = camera
                shot.pose = pose
                shot.metadata = metadata
                reconstruction.add_shot(shot)

                count += 1
            pre_pose_data = pose_data

    # with open(fn) as f:
    #     mylogger.logger.info("loading " + fn)
    #
    #     reader = csv.reader(f)
    #     count = 0
    #     for row in reader:
    #         count += 1
    #         if count%100 != 0:
    #             continue
    #
    #         pose = TangoPose(np.array(row[1:4]), np.array(row[4:8]))
    #         pose.setRotationAndTranslation()
    #         metadata = types.ShotMetadata()
    #         metadata.capture_time = float(row[0])
    #
    #         shot = types.Shot()
    #         shot.id = "{0:08d}".format(count) + ".png"
    #         shot.camera = camera
    #         shot.pose = pose
    #         shot.metadata = metadata
    #
    #         reconstruction.add_shot(shot)

        mylogger.logger.info("Done")
    return reconstruction

def slideToNorth(img, angle_rad, inv = False):
    """
    :type img: numpuy.array
    :type angle_rad: float    0 < angle_rad < 2pi
    :rtype slided_img: numpy.array
    """
    w = img.shape[1]
    slide_width = int(angle_rad/(2 * math.pi) * w)
    slided_img = np.zeros(img.shape)

    if inv:
        slided_img[:, 0:(w-slide_width), :] = img[:, slide_width:w, :]
        slided_img[:, (w-slide_width):w, :] = img[:, 0:slide_width, :]
    else:
        slided_img[:, 0:slide_width, :] = img[:, (w-slide_width):w, :]
        slided_img[:, slide_width:w, :] = img[:, 0:(w-slide_width), :]


    return slided_img

def loadTangoPoseWithVideo(fn, camera, video_fn, fps = 3.,delay = 0., max_frame_num=0, rotate=0., video_range=None):
    """
    csv format: timestamp(unixtime[sec]),x[m],y[m],z[m],rotQ1,rotQ2,rotQ3,rotQ4
    
    :type fn: str
    :type camera: scripts.myopensfm.types.Camera
    :type video_fn: str
    :type fps: float
    :type delay: float
    :type max_frame_num: int
    :type rotate: float rad
    :type video_range: (float, float) start end time
    :rtype reconstruction: scripts.myopensfm.types.Reconstruction
    """
    mylogger.logger.info("loading TangoPose({}) with Video({}) ".format(fn, video_fn))

    reconstruction = types.Reconstruction()
    reconstruction.add_camera(camera)
    reconstruction.metadata.fps = fps
    reconstruction.metadata.video_delay = delay

    # create output image dir
    images_dir = os.path.join(os.path.dirname(fn), "images")
    if not os.path.exists(images_dir):
        os.mkdir(images_dir)

    with open(fn) as f:
        reader = csv.reader(f)

        # load video and video config
        mylogger.logger.info("loading video... " + video_fn)
        video = cv2.VideoCapture(video_fn)
        video_fps = video.get(cv2.CAP_PROP_FPS)
        # video_fps = round(video.get(cv2.CAP_PROP_FPS))
        video_period = 1./video_fps
        video_total_frame_num = video.get(cv2.CAP_PROP_FRAME_COUNT)
        mylogger.logger.info("loading video Done")

        t_pose = 0.
        pre_pose_data = None
        init_pose_data = None
        t_video = 0.
        count = 0
        if fps == 0:
            period = 0
        else:
            period = 1./fps

        while True:
            ret, frame = video.read()
            if not ret:
                break

            t_video += video_period
            if video_range is not None and not (video_range[0] < t_video < video_range[1]):
                if t_video > period * (count + 1):
                    mylogger.logger.debug("skip frame {}".format(count))
                    count += 1
                continue

            if t_video > period * (count + 1):
                while True:
                    try:
                        if sys.version_info[0] == 2:
                            pose_data = reader.next()
                        if sys.version_info[0] == 3:
                            pose_data = next(reader)
                    except csv.Error:
                        print("CSV Error")
                    except StopIteration:
                        print("Iteration End")
                        break

                    if pre_pose_data is None:
                        pre_pose_data = pose_data

                    t_pose += float(pose_data[0]) - float(pre_pose_data[0])
                    if t_pose > (t_video - delay):
                        if init_pose_data is None:
                            init_pose_data = pose_data
                            print("initial post: ")
                            print(init_pose_data)

                        # pose = TangoPose(np.array(pose_data[1:4]), np.array(pose_data[4:8]))
                        # print(np.array(pose_data[1:4], dtype=float) - np.array(init_pose_data[1:4], dtype=float), np.array(pose_data[1:4]), np.array(init_pose_data[1:4]))
                        pose = TangoPose(np.array(pose_data[1:4], dtype=float) - np.array(init_pose_data[1:4], dtype=float), np.array(pose_data[4:8]))
                        pose.setRotationAndTranslation()
                        metadata = types.ShotMetadata()
                        metadata.capture_time = float(pose_data[0])
                        shot = types.Shot()
                        shot.id = "{0:08d}".format(count) + ".png"
                        shot.camera = camera
                        shot.pose = pose
                        shot.metadata = metadata
                        reconstruction.add_shot(shot)

                        # save img
                        frame = slideToNorth(frame, rotate)
                        cv2.imwrite(os.path.join(images_dir, shot.id), frame)
                        mylogger.logger.info("save frame " + shot.id)

                        count += 1
                        pre_pose_data = pose_data
                        break
                    pre_pose_data = pose_data
            if max_frame_num != 0 and count > max_frame_num:
                mylogger.logger.debug("exceed max frame num")
                break

    mylogger.logger.info("Done")
    return reconstruction
