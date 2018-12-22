const Z_RATIO = 3;
// const BACKGROUND = {
//     image: '/navimap/floorplan/viewer/images/sfu_background/zoom2_satellite.png', 
//     // image: '/navimap/floorplan/viewer/images/sfu_background/zoom2_map.png', 
//     width: 1500, 
//     height: 1000, 
//     x: 30, 
//     y:70, 
//     z: -10, 
//     rot_z: 0.23, 
//     scale:  0.62, 
// };
const BACKGROUND = {
    // image: '/navimap/floorplan/viewer/images/sfu_background/zoom3_satellite.png', 
    image: '/navimap/floorplan/viewer/images/sfu_background/zoom3_map.png', 
    width: 1500, 
    height: 1000, 
    x: -90, 
    y: 30, 
    z: -10, 
    rot_z: 0.23, 
    scale:  0.7, 
};
// const BACKGROUND = {
//     image: '/navimap/floorplan/viewer/images/sfu_background/zoom4_satellite.png', 
//     // image: '/navimap/floorplan/viewer/images/sfu_background/zoom4_map.png', 
//     width: 1500, 
//     height: 1000, 
//     x: -60, 
//     y: 150, 
//     z: -10, 
//     rot_z: 0.23, 
//     scale:  1.15, 
// };

// var COLOR_LIST = Object.keys(THREE.ColorKeywords)
var COLOR_LIST = ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure',
    'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet',
    'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral',
    'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan',
    'darkgoldenrod', 'darkgray', 'darkgreen', 'darkgrey', 'darkkhaki', 'darkmagenta',
    'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen',
    'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet',
    'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick',
    'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold',
    'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink',
    'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen',
    'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgray',
    'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue',
    'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen',
    'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid',
    'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise',
    'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite',
    'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid',
    'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff',
    'peru', 'pink', 'plum', 'powderblue', 'purple', 'rebeccapurple', 'red', 'rosybrown',
    'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell',
    'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey', 'snow',
    'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise',
    'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen'
];

var BUILDING = {
    'aq': ['aq_1000', 'aq_2000', 'aq_3000'], 
    'asb': ['asb_8000', 'asb_9000', 'asb_10000'], 
    'bh': ['bh_9000', 'bh_10000', 'bh_11000'], 
    'sh': ['sh_9000', 'sh_10000'], 
    'ssb': ['ssb_5000', 'ssb_6000', 'ssb_7000', 'ssb_8000', 'ssb_9000'], 
    'ssc': ['ssc_6000', 'ssc_7000', 'ssc_8000', 'ssc_9000', 'ssc_10000'], 
    'tasc1': ['tasc1_7000', 'tasc1_8000', 'tasc1_9000'], 
    'tasc2': ['tasc2_6000', 'tasc2_7000', 'tasc2_8000', 'tasc2_9000'], 
};

var BUILDING_MODEL = {
    'aq': [/*{base: 'aq_1000', height: -40*2*Z_RATIO, down: 0}, */{base: 'aq_3000', height: -40*3*Z_RATIO, down: 40*3*Z_RATIO}], 
    'asb': [/*{base: 'asb_8000', height: -40*1.2*Z_RATIO, down: 0}, */{base: 'asb_9000', height: -40*2*Z_RATIO, down: 40*3*Z_RATIO}], 
    'bh': [{base: 'bh_9000', height: -40*3*Z_RATIO, down: 40*3*Z_RATIO}], 
    'sh': [{base: 'sh_10000', height: -40*1*Z_RATIO, down: 40*4*Z_RATIO}], 
    'ssb': [{base: 'ssb_6000', height: -40*4*Z_RATIO, down: 0}], 
    'ssc': [/*{base: 'ssc_7000', height: -40*1*Z_RATIO, down: 0}, */{base: 'ssc_8000', height: -40*2*Z_RATIO, down: 40*3*Z_RATIO}], 
    'tasc1': [{base: 'tasc1_7000', height: -40*3*Z_RATIO, down: 0}], 
    'tasc2': [{base: 'tasc2_6000', height: -40*4*Z_RATIO, down: 0}], 
};

var BUILDING_COLOR = {
    'aq': 'green', 
    'asb': 'skyblue', 
    'bh': 'purple', 
    'sh': 'cyan', 
    'ssb': 'olive', 
    'ssc': 'salmon', 
    'tasc1': 'red', 
    'tasc2': 'indigo', 
};

var FLOOR_COLOR = {
    'aq_1000': BUILDING_COLOR['aq'], 
    'aq_2000': BUILDING_COLOR['aq'], 
    'aq_3000': BUILDING_COLOR['aq'], 
    'asb_8000': BUILDING_COLOR['asb'], 
    'asb_9000': BUILDING_COLOR['asb'], 
    'asb_10000': BUILDING_COLOR['asb'], 
    'bh_9000': BUILDING_COLOR['bh'], 
    'bh_10000': BUILDING_COLOR['bh'], 
    'bh_11000': BUILDING_COLOR['bh'], 
    'sh_9000': BUILDING_COLOR['sh'], 
    'sh_10000': BUILDING_COLOR['sh'], 
    'ssb_5000': BUILDING_COLOR['ssb'], 
    'ssb_6000': BUILDING_COLOR['ssb'], 
    'ssb_7000': BUILDING_COLOR['ssb'], 
    'ssb_8000': BUILDING_COLOR['ssb'], 
    'ssb_9000': BUILDING_COLOR['ssb'], 
    'ssc_6000': BUILDING_COLOR['ssc'], 
    'ssc_7000': BUILDING_COLOR['ssc'], 
    'ssc_8000': BUILDING_COLOR['ssc'], 
    'ssc_9000': BUILDING_COLOR['ssc'], 
    'ssc_10000': BUILDING_COLOR['ssc'], 
    'tasc1_7000': BUILDING_COLOR['tasc1'], 
    'tasc1_8000': BUILDING_COLOR['tasc1'], 
    'tasc1_9000': BUILDING_COLOR['tasc1'], 
    'tasc2_6000': BUILDING_COLOR['tasc2'], 
    'tasc2_7000': BUILDING_COLOR['tasc2'], 
    'tasc2_8000': BUILDING_COLOR['tasc2'], 
    'tasc2_9000': BUILDING_COLOR['tasc2'], 
};

var BUILDING_HEIGHT = {
    'aq_1000': -40*Z_RATIO, 
    'aq_2000': -40*Z_RATIO, 
    'aq_3000': -40*Z_RATIO, 
    'asb_8000': -40*Z_RATIO, 
    'asb_9000': -40*Z_RATIO, 
    'asb_10000': -40*Z_RATIO, 
    'bh_9000': -40*Z_RATIO, 
    'bh_10000':-40*Z_RATIO, 
    'bh_11000':-40*Z_RATIO, 
    'sh_9000': -40*Z_RATIO, 
    'sh_10000':-40*Z_RATIO, 
    'ssb_5000':-40*Z_RATIO, 
    'ssb_6000': -40*Z_RATIO, 
    'ssb_7000': -40*Z_RATIO, 
    'ssb_8000': -40*Z_RATIO, 
    'ssb_9000': -40*Z_RATIO, 
    'ssc_6000': -40*Z_RATIO, 
    'ssc_7000': -35*Z_RATIO, 
    'ssc_8000': -35*Z_RATIO, 
    'ssc_9000': -40*Z_RATIO, 
    'ssc_10000': -40*Z_RATIO, 
    'tasc1_7000': -40*Z_RATIO, 
    'tasc1_8000': -40*Z_RATIO, 
    'tasc1_9000': -40*Z_RATIO, 
    'tasc2_6000': -40*Z_RATIO, 
    'tasc2_7000': -40*Z_RATIO, 
    'tasc2_8000': -40*Z_RATIO, 
    'tasc2_9000': -40*Z_RATIO, 
};

const VIEW_MODE = {
    FIRST_PERSON: 0, 
    THIRD_PERSON: 1, 
};

var frame = 0;
var urlParams;
var f1;
var container, fp_camera, tp_camera, fp_controls, tp_controls, scene, renderer;
let tp_scene, fp_scene;
var mouse = new THREE.Vector2();
let active_view = undefined;
// let split_view = true;
let split_view = false;
let split_view_ratio = 0.5;
let tp_mouse = new THREE.Vector2();
let fp_mouse = new THREE.Vector2();
var hoverCamera, raycaster, parentTransform;
var selectedCamera;
var followTarget;
var imagePlane, imagePlaneCameraLine;
var imagePlaneOld, imagePlaneCameraLineOld;
var preLoadedImageMaterials = {};
var scene_group, grid_group, sub_group;
var pointCloudMaterial;
var reconstructions;
var recon_floorplans = [];
var recon_tracks = [];
var track_groups = [];
var track_names = [];
var floorplan_groups = [];
var floorplan_names = [];
var building_groups = [];
var building_names = [];
var point_clouds = [];
var camera_lines = [];
var imageMaterials = [];
var num_preview_plane = 5;
var moveSpeed = 0.2;
var turnSpeed = 0.1;
var previousShot = undefined;
var validMoves;
var MOVINGMODE = {
    ORBIT: 1, 
    WALK: 2, 
    NONE: 3, 
};
var movingMode = MOVINGMODE.ORBIT;
var WALKMODE = {
    FLOORPLAN: 1, 
    PANORAMA: 2, 
    NONE: 3
};
var walkMode = WALKMODE.PANORAMA;
var savedOptions = {    // initial option for walkmode
    cameraSize: 0.05,
    pointSize: 0,
    showNaviPosition: false,
    showThumbnail: false,
    showImagePlane: true,
    showTracks: false,
    showFloorplans: true,
    showBuildings: true,
    drawGrid: false,
};
var naviStatus = {
    running: false, 
    waypoints: [],
    related_floors: [],
    current_floor: undefined,
    next_posi: 0, 
    current_pos: 0, 
    file: '/navimap/floorplan/viewer/js/testRoute.csv', 
};
var naviOptions = {    // initial option for walkmode
    followTargetSize: 10,
    speed: 1, 
};

var options = {
    cameraSize: 0.35,
    pointSize: 0.7,
    imagePlaneSize: 10,
    showNaviPosition: false,
    showThumbnail: true,
    showImagePlane: false,
    showTracks: true,
    // showTracks: false,
    showFloorplans: true,
    // showBuildings: true,
    showBuildings: false,
    drawGrid: true,
    animationSpeed: 0.1,
    imagePlaneOpacity: 1,
    cameraColor: new THREE.Color(0x0000FF),
    hoverCameraColor: new THREE.Color(0xFF8888),
    selectedCameraColor: new THREE.Color(0xFFFF88),
    floorplanColor: new THREE.Color(0x00FF00),
    cameraLineLength: 1,
    walkingModeCameraLineLength: 5,
    selectedCameraLineLength: 5,
    track_colors: {}, 
    track_visibles: {},
    floorplan_colors: {}, 
    floorplan_visibles: {},
    building_colors: {}, 
    resolution: 'original',
    building3Dmesh: true, 
    floorplanMesh: true, 
    turn_angle_threshold: 0.2, 
    turn_dist_threshold: 5, 
    camera_near_dist: 20, 
};

let naviDirection = new THREE.Vector3(0, 0.1, 0);
let naviDirection_z = 0.0;
let naviPosOffset = new THREE.Vector3(0, 0, 0.03);

var tmp1, tmp2, tmp3, tmp4, tmp5, tmp6;