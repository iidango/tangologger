"""Basic types for building a reconstruction."""

import numpy as np
import cv2
import os
import csv
import glob
import mylogger


class Pose(object):
    """Defines the pose parameters of a camera.

    The extrinsic parameters are defined by a 3x1 rotation vector which
    maps the camera rotation respect to the origin frame (rotation) and
    a 3x1 translation vector which maps the camera translation respect
    to the origin frame (translation).

    Attributes:
        rotation (vector): the rotation vector.
        translation (vector): the rotation vector.
    """

    def __init__(self, rotation=np.zeros(3), translation=np.zeros(3)):
        self.rotation = rotation
        self.translation = translation

    @property
    def rotation(self):
        """Rotation in angle-axis format."""
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = np.asarray(value, dtype=float)

    @property
    def translation(self):
        """Translation vector."""
        return self._translation

    @translation.setter
    def translation(self, value):
        self._translation = np.asarray(value, dtype=float)

    def transform(self, point):
        """Transform a point from world to this pose coordinates."""
        return self.get_rotation_matrix().dot(point) + self.translation

    def transform_inverse(self, point):
        """Transform a point from this pose to world coordinates."""
        return self.get_rotation_matrix().T.dot(point - self.translation)

    def get_rotation_matrix(self):
        """Get rotation as a 3x3 matrix."""
        return cv2.Rodrigues(self.rotation)[0]

    def set_rotation_matrix(self, rotation_matrix):
        """Set rotation as a 3x3 matrix."""
        R = np.array(rotation_matrix, dtype=float)
        self.rotation = cv2.Rodrigues(R)[0].ravel()

    def get_origin(self):
        """The origin of the pose in world coordinates."""
        return -self.get_rotation_matrix().T.dot(self.translation)

    def set_origin(self, origin):
        """Set the origin of the pose in world coordinates.

        >>> pose = Pose()
        >>> pose.rotation = np.array([0., 1., 2.])
        >>> origin = [1., 2., 3.]
        >>> pose.set_origin(origin)
        >>> np.allclose(origin, pose.get_origin())
        True
        """
        self.translation = -self.get_rotation_matrix().dot(origin)

    def get_Rt(self):
        """Get pose as a 3x4 matrix (R|t)."""
        Rt = np.empty((3, 4))
        Rt[:, :3] = self.get_rotation_matrix()
        Rt[:, 3] = self.translation
        return Rt

    def get_Rt4(self):
        """Get pose as a 4x4 matrix (R|t).
        :return np.array Rt:
        """
        Rt = np.identity(4, dtype=float)
        Rt[:3, :3] = self.get_rotation_matrix()
        Rt[:3, 3] = self.translation
        return Rt

    def compose(self, other):
        """Get the composition of this pose with another.

        composed = self * other
        """
        selfR = self.get_rotation_matrix()
        otherR = other.get_rotation_matrix()
        R = np.dot(selfR, otherR)
        t = selfR.dot(other.translation) + self.translation
        res = Pose()
        res.set_rotation_matrix(R)
        res.translation = t
        return res

    def inverse(self):
        """Get the inverse of this pose."""
        inverse = Pose()
        R = self.get_rotation_matrix()
        inverse.set_rotation_matrix(R.T)
        inverse.translation = -R.T.dot(self.translation)
        return inverse

    def getXYZ(self):
        """
        get xyz coord
        :rtype xyz: numpy.array
        """
        return self.transform_inverse(np.array([0, 0, 0]))

    def transposeWorldCoordinate(self, rt, inv = False):
        """
        :type pose: scripts.myopensfm.types.pose
        :type rt: numpy.array
        :type inv: bool
        :rtype new_pose: scripts.myopensfm.types.pose
        """
        rt = rt if inv else np.linalg.inv(rt)

        transposed = np.dot(self.get_Rt(), rt)

        self.set_rotation_matrix(transposed[:3,:3])
        self.translation = transposed[:3, 3].T

class ShotMetadata(object):
    """Defines GPS data from a taken picture.

    Attributes:
        orientation (int): the exif orientation tag (1-8).
        capture_time (real): the capture time.
        gps_dop (real): the GPS dop.
        gps_position (vector): the GPS position.
    """

    def __init__(self):
        self.orientation = None
        self.gps_dop = None
        self.gps_position = None
        self.accelerometer = None
        self.compass = None
        self.capture_time = None
        self.skey = None


class ShotMesh(object):
    """Triangular mesh of points visible in a shot

    Attributes:
        vertices: (list of vectors) mesh vertices
        faces: (list of triplets) triangles' topology
    """

    def __init__(self):
        self.vertices = None
        self.faces = None


class Camera(object):
    """Abstract camera class.

    A camera is unique defined for its identification description (id),
    the projection type (projection_type) and its internal calibration
    parameters, which depend on the particular Camera sub-class.

    Attributes:
        id (str): camera description.
        projection_type (str): projection type.
    """

    pass


class PerspectiveCamera(Camera):
    """Define a perspective camera.

    Attributes:
        widht (int): image width.
        height (int): image height.
        focal (real): estimated focal lenght.
        k1 (real): estimated first distortion parameter.
        k2 (real): estimated second distortion parameter.
        focal_prior (real): prior focal lenght.
        k1_prior (real): prior first distortion parameter.
        k2_prior (real): prior second distortion parameter.
    """

    def __init__(self):
        """Defaut constructor."""
        self.id = None
        self.projection_type = 'perspective'
        self.width = None
        self.height = None
        self.focal = None
        self.k1 = None
        self.k2 = None
        self.focal_prior = None
        self.k1_prior = None
        self.k2_prior = None

    def project(self, point):
        """Project a 3D point in camera coordinates to the image plane."""
        # Normalized image coordinates
        xn = point[0] / point[2]
        yn = point[1] / point[2]

        # Radial distortion
        r2 = xn * xn + yn * yn
        distortion = 1.0 + r2 * (self.k1 + self.k2 * r2)

        return np.array([self.focal * distortion * xn,
                         self.focal * distortion * yn])

    def pixel_bearing(self, pixel):
        """Unit vector pointing to the pixel viewing direction."""
        point = np.asarray(pixel).reshape((1, 1, 2))
        distortion = np.array([self.k1, self.k2, 0., 0.])
        x, y = cv2.undistortPoints(point, self.get_K(), distortion).flat
        l = np.sqrt(x * x + y * y + 1.0)
        return np.array([x / l, y / l, 1.0 / l])

    def pixel_bearings(self, pixels):
        """Unit vector pointing to the pixel viewing directions."""
        points = pixels.reshape((-1, 1, 2)).astype(np.float64)
        distortion = np.array([self.k1, self.k2, 0., 0.])
        up = cv2.undistortPoints(points, self.get_K(), distortion)
        up = up.reshape((-1, 2))
        x = up[:, 0]
        y = up[:, 1]
        l = np.sqrt(x * x + y * y + 1.0)
        return np.column_stack((x / l, y / l, 1.0 / l))

    def back_project(self, pixel, depth):
        """Project a pixel to a fronto-parallel plane at a given depth."""
        bearing = self.pixel_bearing(pixel)
        scale = depth / bearing[2]
        return scale * bearing

    def get_K(self):
        """The calibration matrix."""
        return np.array([[self.focal, 0., 0.],
                         [0., self.focal, 0.],
                         [0., 0., 1.]])

    def get_K_in_pixel_coordinates(self, width=None, height=None):
        """The calibration matrix that maps to pixel coordinates.

        Coordinates (0,0) correspond to the center of the top-left pixel,
        and (width - 1, height - 1) to the center of bottom-right pixel.

        You can optionally pass the width and height of the image, in case
        you are using a resized versior of the original image.
        """
        w = width or self.width
        h = height or self.height
        f = self.focal * max(w, h)
        return np.array([[f, 0, 0.5 * (w - 1)],
                         [0, f, 0.5 * (h - 1)],
                         [0, 0, 1.0]])


class FisheyeCamera(Camera):
    """Define a fisheye camera.

    Attributes:
        widht (int): image width.
        height (int): image height.
        focal (real): estimated focal lenght.
        k1 (real): estimated first distortion parameter.
        k2 (real): estimated second distortion parameter.
        focal_prior (real): prior focal lenght.
        k1_prior (real): prior first distortion parameter.
        k2_prior (real): prior second distortion parameter.
    """

    def __init__(self):
        """Defaut constructor."""
        self.id = None
        self.projection_type = 'fisheye'
        self.width = None
        self.height = None
        self.focal = None
        self.k1 = None
        self.k2 = None
        self.focal_prior = None
        self.k1_prior = None
        self.k2_prior = None

    def project(self, point):
        """Project a 3D point in camera coordinates to the image plane."""
        x, y, z = point
        l = np.sqrt(x**2 + y**2)
        theta = np.arctan2(l, z)
        theta_d = theta * (1.0 + theta**2 * (self.k1 + theta**2 * self.k2))
        s = self.focal * theta_d / l
        return np.array([s * x, s * y])

    def pixel_bearing(self, pixel):
        """Unit vector pointing to the pixel viewing direction."""
        point = np.asarray(pixel).reshape((1, 1, 2))
        distortion = np.array([self.k1, self.k2, 0., 0.])
        x, y = cv2.fisheye.undistortPoints(point, self.get_K(), distortion).flat
        l = np.sqrt(x * x + y * y + 1.0)
        return np.array([x / l, y / l, 1.0 / l])

    def pixel_bearings(self, pixels):
        """Unit vector pointing to the pixel viewing directions."""
        points = pixels.reshape((-1, 1, 2)).astype(np.float64)
        distortion = np.array([self.k1, self.k2, 0., 0.])
        up = cv2.fisheye.undistortPoints(points, self.get_K(), distortion)
        up = up.reshape((-1, 2))
        x = up[:, 0]
        y = up[:, 1]
        l = np.sqrt(x * x + y * y + 1.0)
        return np.column_stack((x / l, y / l, 1.0 / l))

    def back_project(self, pixel, depth):
        """Project a pixel to a fronto-parallel plane at a given depth."""
        bearing = self.pixel_bearing(pixel)
        scale = depth / bearing[2]
        return scale * bearing

    def get_K(self):
        """The calibration matrix."""
        return np.array([[self.focal, 0., 0.],
                         [0., self.focal, 0.],
                         [0., 0., 1.]])

    def get_K_in_pixel_coordinates(self, width=None, height=None):
        """The calibration matrix that maps to pixel coordinates.

        Coordinates (0,0) correspond to the center of the top-left pixel,
        and (width - 1, height - 1) to the center of bottom-right pixel.

        You can optionally pass the width and height of the image, in case
        you are using a resized versior of the original image.
        """
        w = width or self.width
        h = height or self.height
        f = self.focal * max(w, h)
        return np.array([[f, 0, 0.5 * (w - 1)],
                         [0, f, 0.5 * (h - 1)],
                         [0, 0, 1.0]])


class SphericalCamera(Camera):
    """A spherical camera generating equirectangular projections.

    Attributes:
        widht (int): image width.
        height (int): image height.
    """

    def __init__(self):
        """Defaut constructor."""
        self.id = None
        self.projection_type = 'equirectangular'
        self.width = None
        self.height = None

    def project(self, point):
        """Project a 3D point in camera coordinates to the image plane."""
        x, y, z = point
        lon = np.arctan2(x, z)
        lat = np.arctan2(-y, np.sqrt(x**2 + z**2))
        return np.array([lon / (2 * np.pi), -lat / (2 * np.pi)])

    def pixel_bearing(self, pixel):
        """Unit vector pointing to the pixel viewing direction."""
        lon = pixel[0] * 2 * np.pi
        lat = -pixel[1] * 2 * np.pi
        x = np.cos(lat) * np.sin(lon)
        y = -np.sin(lat)
        z = np.cos(lat) * np.cos(lon)
        return np.array([x, y, z])

    def pixel_bearings(self, pixels):
        """Unit vector pointing to the pixel viewing directions."""
        lon = pixels[:, 0] * 2 * np.pi
        lat = -pixels[:, 1] * 2 * np.pi
        x = np.cos(lat) * np.sin(lon)
        y = -np.sin(lat)
        z = np.cos(lat) * np.cos(lon)
        return np.column_stack([x, y, z]).astype(float)


class Shot(object):
    """Defines a shot in a reconstructed scene.

    A shot here is refered as a unique view inside the scene defined by
    the image filename (id), the used camera with its refined internal
    parameters (camera), the fully camera pose respect to the scene origin
    frame (pose) and the GPS data obtained in the moment that the picture
    was taken (metadata).

    Attributes:
    :param str id: picture filename.
    :param Camera camera: camera.
    :param Pose pose: extrinsic parameters.
    :param ShotMetadata metadata: GPS, compass, capture time, etc.
    :param FPCScoreMap fpc_score: floorplan corresponding score map
    """

    def __init__(self):
        """Defaut constructor."""
        self.id = None
        self.camera = None
        self.pose = None
        self.metadata = None
        self.mesh = None
        self.fpc_score = None

    def project(self, point):
        """Project a 3D point to the image plane."""
        camera_point = self.pose.transform(point)
        return self.camera.project(camera_point)

    def back_project(self, pixel, depth):
        """Project a pixel to a fronto-parallel plane at a given depth.

        The plane is defined by z = depth in the shot reference frame.
        """
        point_in_cam_coords = self.camera.back_project(pixel, depth)
        return self.pose.transform_inverse(point_in_cam_coords)

    def viewing_direction(self):
        """The viewing direction of the shot.

        That is the positive camera Z axis in world coordinates.
        """
        return self.pose.get_rotation_matrix().T.dot([0, 0, 1])

    def get_FPCScore(self):
        """
        fpc score in current position
        :return float:
        """

        if self.fpc_score is None:
            return 0

        pix = self.fpc_score.floorplan.pose2pix(self.pose)

        if pix[0] in range(self.fpc_score.floorplan.metadata.width)\
                and pix[1] in range(self.fpc_score.floorplan.metadata.height):
            return self.fpc_score.score_map[pix[1], pix[0]]
        else:
            return 0

    def setFPCScore(self, floorplan, score_fn, window_size=(150, 150), step=20):
        """

        :param Floorplan floorplan:
        :param str score_dir:
        :return bool:
        """

        if not os.path.exists(score_fn):
            mylogger.logger.warn('score file not found: {}'.format(score_fn))
            return False

        fpc_score_map = FPCScoreMap()
        fpc_score_map.floorplan = floorplan
        fpc_score_map.pix_per_meter = floorplan.metadata.pix_per_meter
        fpc_score_map.crop_size = window_size
        fpc_score_map.crop_step = step

        score_map = np.zeros((floorplan.metadata.height, floorplan.metadata.width, 1), dtype=float)

        with open(score_fn, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                x = int(row[0])
                y = int(row[1])
                score = float(row[2])
                score_map[int(y-step/2):int(y+step/2),
                int(x-step/2):int(x+step/2)] = score
        fpc_score_map.score_map = score_map
        self.fpc_score = fpc_score_map

        return True

class Point(object):
    """Defines a 3D point.

    Attributes:
        id (int): identification number.
        color (list(int)): list containing the RGB values.
        coordinates (list(real)): list containing the 3D position.
        reprojection_error (real): the reprojection error.
    """

    def __init__(self):
        """Defaut constructor"""
        self.id = None
        self.color = None
        self.coordinates = None
        self.reprojection_error = None

class Floorplan(object):
    """Defines a floorplan image.

    Attributes:
        id (str): filename.
        pose (Pose): extrinsic parameters.
        metadata (FloorplanMetadata): floorplan meta data.
    """

    def __init__(self):
        """Defaut constructor."""
        self.id = None
        self.pose = None
        self.metadata = FloorplanMetadata()

    def get_file_path(self):
        return os.path.join('floorplans', self.id)

    def set_dataroot(self, dataroot):
        self.metadata.dataroot = dataroot

    def get_img(self, dataroot_dir=None):
        """
        
        :param str dataroot_dir: path to data root dir
        :return: 
        """

        if dataroot_dir is None:
            dataroot_dir = self.metadata.dataroot

        fn = os.path.join(dataroot_dir, self.get_file_path())
        return cv2.imread(fn)

    def pose2pix(self, pose):
        """
        :param Pose pose:
        :return (int, int) x, y:
        """
        xyz = pose.transform_inverse(np.array([0, 0, 0]))
        # load and convert to image coordinate
        x = self.metadata.width/2 + int(self.metadata.pix_per_meter * xyz[0])
        y = self.metadata.height/2 - int(self.metadata.pix_per_meter * xyz[1])

        return (int(x), int(y))

    def pix2coord(self, pix):
        """
        :param pix (float, float):
        :return (float, float) x, y:
        """

        x = (pix[0] - self.metadata.width/2)/self.metadata.pix_per_meter
        y = - (pix[1] - self.metadata.height/2)/self.metadata.pix_per_meter

        return (x, y)

    def get_1pixCoord(self):
        """
        get 1pix size in coordinate
        :return (float, float) x, y:
        """
        return self.pix2coord((self.metadata.width/2 + 1, self.metadata.height/2 + 1))

    def get_topLeftCoord(self):
        """
        :return (int, int) x, y:
        """
        return self.pix2coord((0, 0))


class FloorplanMetadata(object):
    """Defines metadata of floorplan.

    Attributes:
        pix_per_meter (float): pixcel per meter.
        width (int): width.
        height (int): height.
        dataroot (str): data_root_dir.
    """

    def __init__(self):
        self.pix_per_meter = None
        self.width = None
        self.height = None
        self.dataroot = None

class GroundControlPointObservation(object):
    """A ground control point observation.

    Attributes:
        id: identification of the
        lla: latitue, longitude and altitude
        coordinates: x, y, z coordinates in topocentric reference frame
        shot_id: the shot where the point is observed
        shot_coordinates: 2d coordinates of the observation
    """

    def __init__(self):
        self.lla = None
        self.coordinates = None
        self.shot_id = None
        self.shot_coordinates = None

class ReconstructionMetadata(object):
    """Defines metadata of floorplan.

    Attributes:
        name (str): name.
        offset (Pose): world coordinate off set.
        shots_offset (Pose): shots off set.
        points_offset (Pose): pointss off set.
        floorplans_offset (Pose): floorplans off set.
        fps (float): fps.
        video_delay (float): video dela.
    """

    def __init__(self):
        self.name = ""
        self.offset = Pose()
        self.shots_offset = Pose()
        self.points_offset = Pose()
        self.floorplans_offset = Pose()
        self.fps = 0.
        self.video_delay = 0.

class Reconstruction(object):
    """Defines the reconstructed scene.

    Attributes:
      cameras (Dict(Camera)): List of cameras.
      shots   (Dict(Shot)): List of reconstructed shots.
      points  (Dict(Point)): List of reconstructed points.
      floorplans  (Dict(Floorplan)): List of floorplan.
      metadata  (ReconstructionMetadata): offset etc.
    """

    def __init__(self):
        """Defaut constructor"""
        self.cameras = {}
        self.shots = {}
        self.points = {}
        self.floorplans = {}
        self.metadata = ReconstructionMetadata()

    def add_camera(self, camera):
        """Add a camera in the list

        :param camera: The camera.
        """
        self.cameras[camera.id] = camera

    def get_camera(self, id):
        """Return a camera by id.

        :return: If exists returns the camera, otherwise None.
        """
        return self.cameras.get(id)

    def add_shot(self, shot):
        """Add a shot in the list

        :param shot: The shot.
        """
        self.shots[shot.id] = shot

    def get_shot(self, id):
        """Return a shot by id.

        :return: If exists returns the shot, otherwise None.
        """
        return self.shots.get(id)

    def add_point(self, point):
        """Add a point in the list

        :param point: The point.
        """
        self.points[point.id] = point

    def get_point(self, id):
        """Return a point by id.

        :return: If exists returns the point, otherwise None.
        """
        return self.points.get(id)

    def add_floorplan(self, floorplan):
        """Add a floorpalan in the list

        :param floorplan: The floorplan.
        """
        self.floorplans[floorplan.id] = floorplan

    def get_floorplan(self, id):
        """Return a floorplan by id.

        :return: If exists returns the floorplan, otherwise None.
        """
        return self.floorplans.get(id)

class FPCScoreMap(object):
    """Defines a floorplan corresponding score.

    Attributes:
      id (str): filename of floorplan coressesponding score csv file.
      floorplan (Floorplan): floorplan
      crop_size   ((int, int): crop window size.
      crop_step  (int): crop window sliding step size.
      pix_per_meter (float): pixcel per meter.
      score_map (np.array): correspondin map(y, x, score)
    """

    def __init__(self, id='', floorplan=None, crop_size=(150,150), crop_step=20, pix_per_meter=1, score_map=None):
        """constructor.
        :param str id:
        :param Floorplan floorplan:
        :param (int, int) crop_size:
        :param int crop_step:
        :param float pix_per_meter:
        :param np.array score_map:
        """
        self.id = id
        self.floorplan = floorplan
        self.crop_size = crop_size
        self.crop_step = crop_step
        self.pix_per_meter = pix_per_meter
        self.score_map = score_map

class Trajectory(object):
    """Defines the trajectory.

    Attributes:
      id (str): filename.
      shots   (List(Shot)): List of shots.
    """

    def __init__(self):
        """Defaut constructor.

        """
        self.id = ''
        self.shots = []

    def add_shot(self, shot):
        """

        :param Shot shot:
        """
        self.shots.append(shot)

    def get_ShotsDict(self):
        """
        :return Dict(Shot) shots:
        """
        shots = {}
        for s in self.shots:
            shots[s.id] = s
        return shots

    def sort(self):
        """
        sort shots by capture_time
        :return:
        """
        self.shots.sort(key=lambda x:x.metadata.capture_time)

    def applyRt(self, rt, inv=True):
        """
        
        :param np.array rt: 
        :param bool inv:
        :return:
        """

        for shot in self.shots:
            shot.pose.transposeWorldCoordinate(rt, inv=inv)

    def setToTopLeft(self, floorplan):
        """
        set Trajectoy to top left of floorplan
        
        :param Trajectopry trajectory: 
        :param Floorplan floorplan: 
        :return np.array rt:
        """

        minx, miny, maxx, maxy = self.pixRange(floorplan)

        top_left = floorplan.pix2coord((minx, miny))
        fp_top_left = floorplan.get_topLeftCoord()
        offset = Pose()
        offset.rotation = np.array([0, 0, 0])
        offset.translation = np.array([fp_top_left[0]-top_left[0], fp_top_left[1]-top_left[1], 0])

        rt = np.linalg.inv(offset.get_Rt4())
        self.applyRt(rt)

        return rt

    def pixRange(self, floorplan):
        """
        get range in pix

        :param Trajectopry trajectory:
        :param Floorplan floorplan:
        :return np.array rt:
        """

        fp_img = floorplan.get_img()
        minx = fp_img.shape[1]
        miny = fp_img.shape[0]
        maxx = 0
        maxy = 0
        for shot in self.shots:
            pose = shot.pose
            x, y = floorplan.pose2pix(pose)
            if x < minx:
                minx = x
            if y < miny:
                miny = y
            if x > maxx:
                maxx = x
            if y > maxy:
                maxy = y

        return minx, miny, maxx, maxy

    def translate(self, floorplan, x, y):
        """
        translate trajectory by pix
        
        :param Floorplan floorplan: 
        :param x float:
        :param y float:
        :return np.array rt:
        """

        pix_size = floorplan.get_1pixCoord()
        offset = Pose()
        offset.rotation = np.array([0, 0, 0])
        offset.translation = np.array([x*pix_size[0], y*pix_size[1], 0])

        rt = np.linalg.inv(offset.get_Rt4())
        self.applyRt(rt)

        return rt

    def translateTo(self, floorplan, x, y):
        """
        translate trajectory to pix(x, y)
        
        :param Trajectopry trajectory: 
        :param Floorplan floorplan: 
        :param x int:
        :param y int:
        :return np.array rt:
        """
        self.setToTopLeft(floorplan)
        return self.translate(floorplan, x, y)

    def setFPCScore(self, floorplan, score_dir, window_size=(150, 150), step=20):
        """

        :param Floorplan floorplan:
        :param str score_dir:
        :return:
        """

        for shot in self.shots:
            score_fn = os.path.join(score_dir, '.'.join(shot.id.split('.')[:-1]) + '.csv')
            shot.setFPCScore(floorplan, score_fn, window_size, step)

    def sumScore(self):
        """
        sum fpc score of current position
        :return float score:
        """
        score = 0.0

        for shot in self.shots:
            score += shot.get_FPCScore()

        return score

