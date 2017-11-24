var urlParams;
var f1;
var container, camera, controls, scene, renderer;
var mouse = new THREE.Vector2();
var hoverCamera, raycaster, parentTransform;
var selectedCamera;
var imagePlane, imagePlaneCamera;
var imagePlaneOld, imagePlaneCameraOld;
var scene_group, grid_group;
var pointCloudMaterial;
var reconstructions;
var reconstruction_visibles = [];
var reconstruction_groups = [];
var point_clouds = [];
var camera_lines = [];
var gps_lines = [];
var floorplans = [];
var imagePlanes = [];
var imagePlaneCameras = [];
var imageMaterials = [];
var num_preview_plane = 5;
var moveSpeed = 0.2;
var turnSpeed = 0.1;
var previousShot = undefined;
var validMoves;
var movingMode = 'orbit';
var savedOptions = {
    cameraSize: 0,
    pointSize: 0,
    showThumbnail: false,
    showImagePlane: true,
    drawGrid: false,
    drawGPS: false
};

var options = {
    cameraSize: 0.9,
    pointSize: 0.7,
    imagePlaneSize: 50,
    showThumbnail: true,
    showImagePlane: false,
    drawGrid: true,
    drawGPS: false,
    animationSpeed: 0.1,
    imagePlaneOpacity: 1,
    // cameraColor: new THREE.Color(0xFFFFFF),
    cameraColor: new THREE.Color(0x0000FF),
    hoverCameraColor: new THREE.Color(0xFF8888),
    selectedCameraColor: new THREE.Color(0xFFFF88),
    reconstruction_visibles: {},
    resolution: 'original',
    allNone: function () {
        var someone = false;
        for (var r = 0; r < reconstructions.length; ++r) {
            if (options.reconstruction_visibles[r]) {
                someone = true;
                break;
            }
        }
        for (var r = 0; r < reconstructions.length; ++r) {
            options.reconstruction_visibles[r] = !someone;
            reconstruction_groups[r].traverse(function (object) {
                object.visible = !someone;
            });
        }
        render();
    }
};

getData();

function addDatGui(){
    var gui = new dat.GUI();

    f1 = gui.addFolder('Options');
    f1.add(options, 'pointSize', 0, 10)
        .listen()
        .onChange(setPointSize);
    f1.add(options, 'cameraSize', 0, 2)
        .listen()
        .onChange(setCameraSize);
    f1.add(options, 'imagePlaneSize', 1, 200)
        .onChange(function(value) {
            options.imagePlaneSize *= 1.5;
            imagePlane.geometry = imagePlaneGeo(imagePlaneCameraOld.reconstruction, imagePlaneCameraOld.shot_id);
            options.imagePlaneSize /= 1.5;
            imagePlane.geometry = imagePlaneGeo(imagePlaneCamera.reconstruction, imagePlaneCamera.shot_id);
            render();
        });
    f1.add(options, 'animationSpeed', 0, 0.2)
        .onChange(function(value) {
            controls.animationSpeed = value;
            invokeJourneyWrapper(function () { journeyWrapper.updateInterval(); });
        });
    f1.add(options, 'resolution', [ '320', '640', 'original' ] );
    f1.add(options, 'showThumbnail')
        .listen()
        .onChange(setShowThumbnail);
    f1.add(options, 'drawGrid')
        .listen()
        .onChange(setDrawGrid);
    f1.add(options, 'showImagePlane')
        .listen()
        .onChange(setShowImagePlane);
    f1.add(options, 'drawGPS')
        .listen()
        .onChange(setDrawGPS);
    f1.open();


    var f3 = gui.addFolder('Reconstructions')
    f3.add(options, 'allNone');
    options.reconstruction_visibles = [];
    for (var r = 0; r < reconstructions.length; ++r) {
        options.reconstruction_visibles[r] = true;
        f3.add(options.reconstruction_visibles, r, true)
            .onChange(
                (function(rr) {
                    return function (value) {
                        reconstruction_groups[rr].traverse(
                            function (object) { object.visible = value; } );
                        render();
                    }
                })(r)
            ).listen();
    }
    f3.close();

    gui.close();
}

function setPointSize(value) {
    options.pointSize = value;
    pointCloudMaterial.size = value;
    for (var i = 0; i < point_clouds.length; ++i) {
        point_clouds[i].visible = (value > 0);
    }
    render();
}

function setCameraSize(value) {
    options.cameraSize = value;
    for (var r = 0; r < reconstructions.length; ++r) {
        updateCameraLines(reconstructions[r]);
    }
    render();
}

function setShowThumbnail(value) {
    options.showThumbnail = value;
    $('#info').css('visibility', value ? 'visible' : 'hidden');
}

function setShowImagePlane(value) {
    options.showImagePlane = value;
    imagePlane.visible = value;
    if (movingMode === 'walk') {
        imagePlaneOld.visible = value;
    } else {
        imagePlaneOld.visible = false;
    }
    render();
}

function setDrawGrid(value) {
    options.drawGrid = value;
    grid_group.visible = value;
    render();
}

function setDrawGPS(value) {
    options.drawGPS = value;
    for (var i = 0; i < gps_lines.length; ++i) {
        gps_lines[i].visible = value;
    }
    render();
}

function setMovingMode(mode) {
    if (mode != movingMode) {
        movingMode = mode;
        if (mode == 'orbit') {
            invokeJourneyWrapper(function () { journeyWrapper.stop(); journeyWrapper.addShowPathController(); });
            resetWalkMode();
            swapOptions();
            controls.noRotate = false;
            controls.noLookAround = false;
            controls.noPan = false;
            controls.noZoom = false;
            controls.noKeys = false;
            controls.animationPosition.z += 10;
            controls.dollyOut(4);
            imagePlane.material.depthWrite = true;
            imagePlaneOld.material.depthWrite = true;
            $('#navigation').hide();
        } else if (mode == 'walk') {
            invokeJourneyWrapper(function () { journeyWrapper.removeShowPathController(); });
            swapOptions();
            // controls.noRotate = true;
            // controls.noLookAround = true;
            // controls.noPan = true;
            // controls.noZoom = true;
            // controls.noKeys = true;
            imagePlane.material.depthWrite = false;
            imagePlaneOld.material.depthWrite = false;
            $('#navigation').show();
        }
    }
}

function resetWalkMode() {
    previousShot = undefined;
}

function swapOptions() {
    var tmpOptions = {
        pointSize: savedOptions.pointSize,
        cameraSize: savedOptions.cameraSize,
        showThumbnail: savedOptions.showThumbnail,
        showImagePlane: savedOptions.showImagePlane,
        drawGrid: savedOptions.drawGrid,
        drawGPS: savedOptions.drawGPS
    };

    savedOptions.pointSize = options.pointSize;
    savedOptions.cameraSize = options.cameraSize;
    savedOptions.showThumbnail = options.showThumbnail;
    savedOptions.showImagePlane = options.showImagePlane;
    savedOptions.drawGrid = options.drawGrid;
    savedOptions.drawGPS = options.drawGPS;

    setPointSize(tmpOptions.pointSize);
    setCameraSize(tmpOptions.cameraSize);
    setShowThumbnail(tmpOptions.showThumbnail);
    setShowImagePlane(tmpOptions.showImagePlane);
    setDrawGrid(tmpOptions.drawGrid);
    setDrawGPS(tmpOptions.drawGPS);
}

function imageURL(shot_id) {
    var url = urlParams.file;
    var slash = url.lastIndexOf('/');
    var imagePath = '/images' + options.resolution.replace('original', '')
    return url.substring(0, slash) + imagePath +'/' + shot_id;
}
function floorplanURL(floorplan_id) {
    var url = urlParams.file;
    var slash = url.lastIndexOf('/');
    var floorplanPath = '/floorplans'
    return url.substring(0, slash) + floorplanPath +'/' + floorplan_id;
}

function parseUrl() {
    var match,
        pl     = /\+/g,  // Regex for replacing addition symbol with a space
        search = /([^&=]+)=?([^&]*)/g,
        decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
        hash  = window.location.hash.substring(1);

    urlParams = {};
    while (match = search.exec(hash))
       urlParams[decode(match[1])] = decode(match[2]);
}

function invokeJourneyWrapper(action) {
    if (typeof journeyWrapper != "undefined") {
        return action();
    }
}

function getData() {
    parseUrl();

    if ('res' in urlParams) options.resolution = urlParams.res;

    jQuery.getJSON(urlParams.file, function(data) {
        if ('cameras' in data) {
            reconstructions = [data];
        } else {
            reconstructions = data;
        }
        $('#loading').remove();
        init();
        animate();

        invokeJourneyWrapper(function () { journeyWrapper.initialize(); });
    });
}

function rotate(vector, angleaxis) {
    var v = new THREE.Vector3(vector[0], vector[1], vector[2]);
    var axis = new THREE.Vector3(angleaxis[0],
                                 angleaxis[1],
                                 angleaxis[2]);
    var angle = axis.length();
    axis.normalize();
    var matrix = new THREE.Matrix4().makeRotationAxis(axis, angle);
    v.applyMatrix4(matrix);
    return v;
}

function opticalCenter(shot) {
    var angleaxis = [-shot.rotation[0],
                     -shot.rotation[1],
                     -shot.rotation[2]];
    var Rt = rotate(shot.translation, angleaxis);
    Rt.negate();
    return Rt;
}

function viewingDirection(shot) {
    var angleaxis = [-shot.rotation[0],
                     -shot.rotation[1],
                     -shot.rotation[2]];
    return rotate([0,0,1], angleaxis);
}

function pixelToVertex(cam, shot, u, v, scale) {
    // Projection model:
    // xc = R * x + t
    // u = focal * xc / zc
    // v = focal * yc / zc
    var focal = cam.focal || 0.3;
    var zc = scale;
    var xc = u / focal * zc;
    var yc = v / focal * zc;

    var xct = [xc - shot.translation[0],
               yc - shot.translation[1],
               zc - shot.translation[2]];


    var angleaxis = [-shot.rotation[0],
                     -shot.rotation[1],
                     -shot.rotation[2]];

    return rotate(xct, angleaxis);
}

function initCameraLines(reconstruction) {
    var lines = []
    for (var shot_id in reconstruction.shots) {
        if (reconstruction.shots.hasOwnProperty(shot_id)) {
            var lineMaterial = new THREE.LineBasicMaterial({size: 0.1 })
            lineMaterial.color = options.cameraColor;
            var linegeo = cameraLineGeo(reconstruction, shot_id);
            var line = new THREE.Line(linegeo, lineMaterial, THREE.LinePieces);
            line.reconstruction = reconstruction;
            line.shot_id = shot_id;
            lines.push(line);
        }
    }
    return lines;
}

function updateCameraLines() {
    for (var i = 0; i < camera_lines.length; ++i) {
        var linegeo = cameraLineGeo(camera_lines[i].reconstruction, camera_lines[i].shot_id);
        camera_lines[i].geometry.vertices = linegeo.vertices;
        camera_lines[i].geometry.verticesNeedUpdate = true;
    }
}

function cameraLineGeo(reconstruction, shot_id) {
    var shot = reconstruction.shots[shot_id];
    var cam = reconstruction.cameras[shot.camera];
    var ocenter = opticalCenter(shot);
    var dx = cam.width / 2.0 / Math.max(cam.width, cam.height);
    var dy = cam.height / 2.0 / Math.max(cam.width, cam.height);
    var top_left     = pixelToVertex(cam, shot, -dx, -dy, options.cameraSize);
    var top_right    = pixelToVertex(cam, shot,  dx, -dy, options.cameraSize);
    var bottom_right = pixelToVertex(cam, shot,  dx,  dy, options.cameraSize);
    var bottom_left  = pixelToVertex(cam, shot, -dx,  dy, options.cameraSize);
    var linegeo = new THREE.Geometry();
    linegeo.vertices.push(ocenter);
    linegeo.vertices.push(top_left);
    linegeo.vertices.push(ocenter);
    linegeo.vertices.push(top_right);
    linegeo.vertices.push(ocenter);
    linegeo.vertices.push(bottom_right);
    linegeo.vertices.push(ocenter);
    linegeo.vertices.push(bottom_left);
    linegeo.vertices.push(top_left);
    linegeo.vertices.push(top_right);
    linegeo.vertices.push(top_right);
    linegeo.vertices.push(bottom_right);
    // linegeo.vertices.push(bottom_right);
    // linegeo.vertices.push(bottom_left);
    linegeo.vertices.push(bottom_left);
    linegeo.vertices.push(top_left);
    return linegeo;
}

function imagePlaneGeo(reconstruction, shot_id) {
    var shot = reconstruction.shots[shot_id];
    var cam = reconstruction.cameras[shot.camera];

    if ('vertices' in shot) {
        var geometry = new THREE.Geometry();
        for (var i = 0; i < shot['vertices'].length; ++i) {
            geometry.vertices.push(
                new THREE.Vector3(
                    shot['vertices'][i][0],
                    shot['vertices'][i][1],
                    shot['vertices'][i][2]
                )
            );
        }
        for (var i = 0; i < shot['faces'].length; ++i) {
            var v0 = shot['faces'][i][0];
            var v1 = shot['faces'][i][1];
            var v2 = shot['faces'][i][2];

            geometry.faces.push(new THREE.Face3(v0, v1, v2));
        }
        return geometry;
    } else {
        if (cam.projection_type == "spherical" || cam.projection_type == "equirectangular") {
            return imageSphereGeoFlat(cam, shot);
        } else {
            return imagePlaneGeoFlat(cam, shot);
        }
    }
}

function imagePlaneGeoFlat(cam, shot) {
    var geometry = new THREE.Geometry();
    var dx = cam.width / 2.0 / Math.max(cam.width, cam.height);
    var dy = cam.height / 2.0 / Math.max(cam.width, cam.height);
    var top_left     = pixelToVertex(cam, shot, -dx, -dy, options.imagePlaneSize);
    var top_right    = pixelToVertex(cam, shot,  dx, -dy, options.imagePlaneSize);
    var bottom_right = pixelToVertex(cam, shot,  dx,  dy, options.imagePlaneSize);
    var bottom_left  = pixelToVertex(cam, shot, -dx,  dy, options.imagePlaneSize);

    geometry.vertices.push(
        top_left,
        bottom_left,
        bottom_right,
        top_right
    );
    geometry.faces.push(
        new THREE.Face3(0, 1, 3),
        new THREE.Face3(1, 2, 3)
    );
    return geometry;
}

function imageSphereGeoFlat(cam, shot) {
    geometry = new THREE.SphereGeometry(
        options.imagePlaneSize,
        20,
        40
    );
    var center = pixelToVertex(cam, shot, 0, 0, 0);
    geometry.applyMatrix(new THREE.Matrix4().makeTranslation(center.x, center.y, center.z));
    return geometry;
}

function createImagePlaneMaterial(cam, shot, shot_id) {
    var imageTexture = THREE.ImageUtils.loadTexture(imageURL(shot_id));
    imageTexture.minFilter = THREE.LinearFilter;

    var material = new THREE.ShaderMaterial({
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: true,
        uniforms: {
            projectorMat: {
                 type: 'm4',
                 value: projectorCameraMatrix(cam, shot)
            },
            projectorTex: {
                type: 't',
                value: imageTexture
            },
            opacity: {
                type: 'f',
                value: options.imagePlaneOpacity
            },
            focal: {
                type: 'f',
                value: cam.focal
            },
            k1: {
                type: 'f',
                value: cam.k1
            },
            k2: {
                type: 'f',
                value: cam.k2
            },
            scale_x: {
                type: 'f',
                value: Math.max(cam.width, cam.height) / cam.width
            },
            scale_y: {
                type: 'f',
                value: Math.max(cam.width, cam.height) / cam.height
            }
        },
        vertexShader:   imageVertexShader(cam),
        fragmentShader: imageFragmentShader(cam)
    });

    return material;
}

function imageVertexShader(cam) {
    return $('#vertexshader').text();
}

function imageFragmentShader(cam) {
    if (cam.projection_type == 'equirectangular' || cam.projection_type == 'spherical')
        return $('#fragmentshader_equirectangular').text();
    else if (cam.projection_type == 'fisheye')
        return $('#fragmentshader_fisheye').text();
    else
        return $('#fragmentshader').text();
}

function projectorCameraMatrix(cam, shot) {
    var angleaxis = shot.rotation;
    var axis = new THREE.Vector3(angleaxis[0],
                                 angleaxis[1],
                                 angleaxis[2]);
    var angle = axis.length();
    axis.normalize();
    var rotation = new THREE.Matrix4().makeRotationAxis(axis, angle);
    var t = shot.translation;
    var translation = new THREE.Vector3(t[0], t[1], t[2]);
    rotation.setPosition(translation);

    return rotation;

    if (cam.projection_type == 'equirectangular' || cam.projection_type == 'spherical')
        return rotation
    var dx = cam.width / Math.max(cam.width, cam.height) / cam.focal;
    var dy = cam.height / Math.max(cam.width, cam.height) / cam.focal;
    var projection = new THREE.Matrix4().makeFrustum(-dx, +dx, +dy, -dy, -1, -1000);
    return projection.multiply(rotation);
}

function getRt(rotation, translation){
    var axis = new THREE.Vector3(rotation[0], rotation[1], rotation[2]);
    var angle = axis.length();
    axis.normalize();
    var rt = new THREE.Matrix4().makeRotationAxis(axis, angle);

    var translation = new THREE.Vector3(translation[0], translation[1], translation[2]);
    rt.setPosition(translation);

    return rt;
}

function getRotationVector(r_mtx){
    var r_mtx_T = new THREE.Matrix3().copy(r_mtx).transpose();

    var rx = (r_mtx.elements[5] - r_mtx_T.elements[5])/2;
    var ry = (r_mtx.elements[6] - r_mtx_T.elements[6])/2;
    var rz = (r_mtx.elements[1] - r_mtx_T.elements[1])/2;

    var sin_theta = new THREE.Vector3(rx, ry, rz).length();
    var theta = Math.PI - Math.asin(sin_theta);

    rx = theta / sin_theta * rx;
    ry = theta / sin_theta * ry;
    rz = theta / sin_theta * rz;

    return new THREE.Vector3(rx, ry, rz);
}


function init() {
    raycaster = new THREE.Raycaster();
    raycaster.precision = 0.01;

    renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor( 0x202020, 0.0);
    renderer.sortObjects = false;

    container = document.getElementById( 'ThreeJS' );
    container.appendChild(renderer.domElement);

    camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.03, 10000);
    camera.position.x = 50;
    camera.position.y = 50;
    camera.position.z = 50;
    camera.up = new THREE.Vector3(0,0,1);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.addEventListener('change', render);

    window.addEventListener('resize', onWindowResize, false);
    renderer.domElement.addEventListener('mousemove', onDocumentMouseMove, false);
    renderer.domElement.addEventListener('mousedown', onDocumentMouseDown, false);
    window.addEventListener( 'keydown', onKeyDown, false );

    scene_group = new THREE.Object3D();
    pointCloudMaterial = new THREE.PointCloudMaterial({
          size: options.pointSize,
          vertexColors: true,
        });
    for (var r = 0; r < reconstructions.length; ++r) {
        var reconstruction = reconstructions[r];
        reconstruction_groups[r] = new THREE.Object3D();
        var group = reconstruction_groups[r];

        // apply offset
        if (reconstruction.hasOwnProperty('metadata')){
            if (reconstruction.metadata.hasOwnProperty('shots_offset')){
                var shots_rotation = reconstruction.metadata.shots_offset.rotation;
                var shots_translation = reconstruction.metadata.shots_offset.translation;

                var s_r_vec = new THREE.Vector3(shots_rotation[0], shots_rotation[1], shots_rotation[2]);
                var s_t_vec = new THREE.Vector3(shots_translation[0], shots_translation[1], shots_translation[2]);

                var rt_shots_offset = new THREE.Matrix4().getInverse(getRt(shots_rotation, shots_translation));

                for (var shot_id in reconstruction.shots) {
                    if (reconstruction.shots.hasOwnProperty(shot_id)) {
                        var r = reconstruction.shots[shot_id].rotation;
                        var t = reconstruction.shots[shot_id].translation;

                        var r_vec = new THREE.Vector3(r[0], r[1], r[2]);
                        var t_vec = new THREE.Vector3(t[0], t[1], t[2]);

                        var rt = getRt(r, t);
                        rt.multiplyMatrices(rt, rt_shots_offset);

                        var new_r = getRotationVector(new THREE.Matrix3().setFromMatrix4(rt));
                        var new_t = new THREE.Vector3().setFromMatrixPosition(rt);

                        reconstruction.shots[shot_id].rotation = new_r.toArray();
                        reconstruction.shots[shot_id].translation = new_t.toArray();
                    }
                }
            }
        }


        // Points.
        var points = new THREE.Geometry();
        for (var point_id in reconstruction.points) {
            if (reconstruction.points.hasOwnProperty(point_id)) {
                var p = reconstruction.points[point_id].coordinates;
                var c = reconstruction.points[point_id].color;
                var color = new THREE.Color();
                color.setRGB(c[0] / 255., c[1] / 255., c[2] / 255.)
                points.vertices.push(new THREE.Vector3(p[0], p[1], p[2]));
                points.colors.push(color);
            }
        }
        var point_cloud = new THREE.PointCloud(points, pointCloudMaterial);
        point_clouds.push(point_cloud);
        group.add(point_cloud);

        // Cameras.
        var lines = initCameraLines(reconstruction);
        for (var i = 0; i < lines.length; ++i) {
            group.add(lines[i]);
            camera_lines.push(lines[i]);
        }

        // GPS positions
        for (var shot_id in reconstruction.shots) {
            if (reconstruction.shots.hasOwnProperty(shot_id)) {
                var shot = reconstruction.shots[shot_id];
                var ocenter = opticalCenter(shot);
                var gps = shot.gps_position;

                if (gps){
                    var linegeo = new THREE.Geometry();
                    linegeo.vertices.push(
                        ocenter,
                        new THREE.Vector3(gps[0], gps[1], gps[2])
                    );
                    var lineMaterial = new THREE.LineBasicMaterial({ color: 0xff00ff });
                    var line = new THREE.Line(linegeo, lineMaterial, THREE.LinePieces);
                    line.visible = options.drawGPS;
                    group.add(line);
                    gps_lines.push(line);
                }
            }
        }

        // floorplan image
        // light
        var light = new THREE.AmbientLight( 0xffffff );
        group.add( light );
        for (var floorplan_id in reconstruction.floorplans) {
            var floorplan_map = THREE.ImageUtils.loadTexture(floorplanURL(floorplan_id));

            // var geometry = new THREE.PlaneGeometry( 1754, 1240);
            var rate = reconstruction.floorplans[floorplan_id].pix_per_meter
            var w = reconstruction.floorplans[floorplan_id].width/rate
            var h = reconstruction.floorplans[floorplan_id].height/rate
            var geometry = new THREE.PlaneGeometry(w, h);

            var floorplan = new THREE.Mesh(
                geometry,
                new THREE.MeshPhongMaterial({map: floorplan_map, side: THREE.DoubleSide, color: 0xFFFFFF})
            );

            var t = reconstruction.floorplans[floorplan_id].translation
            var offset_t = new THREE.Vector3(t[0], t[1], t[2])
            floorplan.position.add(offset_t)

            var r = reconstruction.floorplans[floorplan_id].rotation
            floorplan.rotation.x = r[0]
            floorplan.rotation.y = r[1]
            floorplan.rotation.z = r[2]

            group.add( floorplan );
            floorplans.push(floorplan)
        }

        scene_group.add(group);
    }


    // Image plane
    imagePlaneCamera = camera_lines[0];
    var shot = imagePlaneCamera.reconstruction.shots[imagePlaneCamera.shot_id];
    var cam = imagePlaneCamera.reconstruction.cameras[shot.camera];

    imagePlane = new THREE.Mesh(imagePlaneGeo(imagePlaneCamera.reconstruction,
                                              imagePlaneCamera.shot_id),
                                createImagePlaneMaterial(cam, shot, imagePlaneCamera.shot_id));
    imagePlane.visible = options.showImagePlane;

    imagePlaneCameraOld = camera_lines[0];
    imagePlaneOld = new THREE.Mesh(imagePlaneGeo(imagePlaneCameraOld.reconstruction,
                                                 imagePlaneCameraOld.shot_id),
                                createImagePlaneMaterial(cam, shot, imagePlaneCameraOld.shot_id));
    imagePlaneOld.visible = options.showImagePlane;

    scene_group.add(imagePlane);
    scene_group.add(imagePlaneOld);


    // Axis
    grid_group = new THREE.Object3D();
    var linegeo = new THREE.Geometry();
    linegeo.vertices = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(1, 0, 0),
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 1, 0),
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 0, 1)
    ];
    linegeo.colors = [
        new THREE.Color( 0xff0000 ),
        new THREE.Color( 0xff0000 ),
        new THREE.Color( 0x00ff00 ),
        new THREE.Color( 0x00ff00 ),
        new THREE.Color( 0x0000ff ),
        new THREE.Color( 0x0000ff )
    ];
    var lineMaterial = new THREE.LineBasicMaterial({
        color: 0xffffff,
        vertexColors: THREE.VertexColors
    });
    var line = new THREE.Line(linegeo, lineMaterial, THREE.LinePieces);
    grid_group.add(line);

    // Ground grid
    {
        var linegeo = new THREE.Geometry();
        var N = 20;
        var scale = 2;
        for (var i = 0; i <= 2 * N; ++i) {
            linegeo.vertices.push(
                new THREE.Vector3(scale * (i - N), scale * (-N), 0),
                new THREE.Vector3(scale * (i - N), scale * ( N), 0),
                new THREE.Vector3(scale * (-N), scale * (i - N), 0),
                new THREE.Vector3(scale * ( N), scale * (i - N), 0)
            );
        }
        var lineMaterial = new THREE.LineBasicMaterial({color: 0x555555});
        var line = new THREE.Line(linegeo, lineMaterial, THREE.LinePieces);
        grid_group.add(line);
    }
    scene_group.add(grid_group);

    scene = new THREE.Scene();
    scene.add(scene_group);

    addDatGui();

    setShowThumbnail(true);
    if ('img' in urlParams) {
        for (var i = 0; i < camera_lines.length; ++i) {
            if (camera_lines[i].shot_id.indexOf(urlParams.img) > -1) {
                var initialCamera = camera_lines[i];
                setMovingMode('walk');
                setImagePlaneCamera(initialCamera);
                navigateToShot(initialCamera);
                break;
            }
        }
    }

    if (camera_lines.length < 50) {
        preloadAllImages();
    }

    render();
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    render();
}

function onDocumentMouseMove(event) {
    event.preventDefault();
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;
    render();
}

function reconstruction_of_shot(reconstructions, shot_id) {
    for (var r = 0; r < reconstructions.length; ++r) {
        if (shot_id in reconstructions[r]['shots']) {
            return reconstructions[r];
        }
    }
    return undefined;
}

function reconstruction_id_of_shot(reconstructions, shot_id) {
    for (var r = 0; r < reconstructions.length; ++r) {
        if (shot_id in reconstructions[r]['shots']) {
            return r;
        }
    }
    return undefined;
}

function setSelectedCamera(cameraObject) {
    var r = cameraObject.reconstruction;
    var shot_id = cameraObject.shot_id;
    var shot = r['shots'][shot_id];
    var image_url = imageURL(shot_id);
    if (selectedCamera !== undefined) {
        selectedCamera.material.linewidth = 1;
        selectedCamera.material.color = options.cameraColor;
    }
    selectedCamera = cameraObject;
    selectedCamera.material.linewidth = 5;
    selectedCamera.material.color = options.selectedCameraColor;
    var image_tag = document.getElementById('image');
    image_tag.src = image_url;
    var text = document.getElementById('text');
    text.innerHTML = shot_id;

    invokeJourneyWrapper(function () { journeyWrapper.showPath(); });
}

function setImagePlaneCamera(cameraObject) {
    var r = cameraObject.reconstruction;
    var shot_id = cameraObject.shot_id;
    var shot = r['shots'][shot_id];
    var cam = r['cameras'][shot['camera']];

    if (previousShot !== cameraObject.shot_id) {
        previousShot = cameraObject.shot_id
        var image_url = imageURL(shot_id);
        if (selectedCamera !== cameraObject) {
            setSelectedCamera(cameraObject);
        }

        if (imagePlaneCamera !== undefined) {
            if (imagePlaneCameraOld === undefined || imagePlaneCamera.shot_id !== cameraObject.shot_id) {
                imagePlaneCameraOld = imagePlaneCamera;
                imagePlaneOld.material.uniforms.projectorTex.value = imagePlane.material.uniforms.projectorTex.value;
                imagePlaneOld.material.uniforms.projectorMat.value = imagePlane.material.uniforms.projectorMat.value;
                imagePlane.material.uniforms.focal.value = imagePlane.material.uniforms.focal.value;
                imagePlane.material.uniforms.k1.value = imagePlane.material.uniforms.k1.value;
                imagePlane.material.uniforms.k2.value = imagePlane.material.uniforms.k2.value;
                imagePlane.material.uniforms.scale_x.value = imagePlane.material.uniforms.scale_x.value;
                imagePlane.material.uniforms.scale_y.value = imagePlane.material.uniforms.scale_y.value;
                imagePlaneOld.material.vertexShader = imagePlane.material.vertexShader;
                imagePlaneOld.material.fragmentShader = imagePlane.material.fragmentShader;
                imagePlaneOld.material.needsUpdate = true;

                imagePlaneOld.geometry.dispose();
                imagePlaneOld.geometry = imagePlaneGeo(imagePlaneCameraOld.reconstruction, imagePlaneCameraOld.shot_id);
            }

            if (movingMode === 'walk') {
                options.imagePlaneOpacity = 1;
            }
        }

        imagePlaneCamera = cameraObject;
        imagePlane.material.dispose();
        imagePlane.geometry.dispose();
        imagePlane.material = createImagePlaneMaterial(cam, shot, shot_id);
        imagePlane.geometry = imagePlaneGeo(r, shot_id);
    }
}

function setImagePlaneCameraList(cameraObject, id) {
    var r = cameraObject.reconstruction;
    var shot_id = cameraObject.shot_id;
    var shot = r['shots'][shot_id];
    var cam = r['cameras'][shot['camera']];
    var image_url = imageURL(shot_id);

    imagePlaneCameras[id] = cameraObject;
    imageMaterials[id].map = THREE.ImageUtils.loadTexture(image_url, null, render);
    imageMaterials[id].map.minFilter = THREE.LinearFilter;
    imagePlanes[id].geometry = imagePlaneGeo(r, shot_id);
    imagePlanes[id].visible = true;
}

function onDocumentMouseDown(event) {
    window.focus();
    if (hoverCamera !== undefined) {
        if (movingMode !== 'walk') {
            if (selectedCamera !== hoverCamera) {
                setSelectedCamera(hoverCamera);
                setImagePlaneCamera(hoverCamera);
            } else {
                setMovingMode('walk');
                setImagePlaneCamera(selectedCamera);
                navigateToShot(selectedCamera);
            }
        }
        render();
    }
}

function navigateToShot(camera) {
    var reconstruction = camera.reconstruction;
    var shot = reconstruction['shots'][camera.shot_id];
    var cam = reconstruction['cameras'][shot['camera']];
    controls.goto_shot(cam, shot);
}

function hideImagePlanesList(){
    for (var i =0; i < num_preview_plane; ++i) {
        imagePlanes[i].visible = false;
    }
}

function angleBetweenVector2(x1, y1, x2, y2) {
    var a = Math.atan2(y2, x2) - Math.atan2(y1, x1);
    if (a > Math.PI) return a - 2 * Math.PI;
    else if (a < -Math.PI) return a + 2 * Math.PI;
    else return a;
}

function computeValidMoves() {
    var currentPosition = controls.animationPosition;
    var currentTarget = controls.animationTarget;
    var currentDir = currentTarget.clone().sub(currentPosition);
    var turnAngle = undefined;

    var wantedMotionDirs = {
        STEP_LEFT: new THREE.Vector3(-currentDir.y, currentDir.x, 0),
        STEP_RIGHT: new THREE.Vector3(currentDir.y, -currentDir.x, 0),
        STEP_FORWARD: new THREE.Vector3(currentDir.x, currentDir.y, 0),
        STEP_BACKWARD: new THREE.Vector3(-currentDir.x, -currentDir.y, 0),
        TURN_LEFT: new THREE.Vector3(0, 0, 0),
        TURN_RIGHT: new THREE.Vector3(0, 0, 0),
        TURN_U: new THREE.Vector3(0, 0, 0)
    }

    var wantedDirs = {
        STEP_LEFT: new THREE.Vector3(currentDir.x, currentDir.y, 0),
        STEP_RIGHT: new THREE.Vector3(currentDir.x, currentDir.y, 0),
        STEP_FORWARD: new THREE.Vector3(currentDir.x, currentDir.y, 0),
        STEP_BACKWARD: new THREE.Vector3(currentDir.x, currentDir.y, 0),
        TURN_LEFT: new THREE.Vector3(-currentDir.y, currentDir.x, 0),
        TURN_RIGHT: new THREE.Vector3(currentDir.y, -currentDir.x, 0),
        TURN_U: new THREE.Vector3(-currentDir.x, -currentDir.y, 0)
    }

    var min_d = {};
    var closest_line = {};
    var turn_threshold;
    for (var k in wantedMotionDirs) {
        if (wantedMotionDirs.hasOwnProperty(k)) {
            min_d[k] = 999999999999;
            closest_line[k] = undefined;
        }
    }

    for (var i = 0; i < camera_lines.length; ++i) {
        var line = camera_lines[i];
        var r = line.reconstruction;
        var shot_id = line.shot_id;
        var shot = r['shots'][shot_id];
        var oc = opticalCenter(shot);
        var dir = viewingDirection(shot);
        var motion = oc.clone().sub(currentPosition);
        var d = currentPosition.distanceTo(oc);
        var rid = reconstruction_id_of_shot(reconstructions, shot_id);
        var visible = options.reconstruction_visibles[rid];
        if (!visible) continue;

        for (var k in wantedMotionDirs) {
            if (wantedMotionDirs.hasOwnProperty(k)) {
                var turn = angleBetweenVector2(wantedDirs[k].x, wantedDirs[k].y, dir.x, dir.y);
                var driftAB = angleBetweenVector2(wantedMotionDirs[k].x, wantedMotionDirs[k].y, motion.x, motion.y);
                var driftBA = driftAB - turn;
                var drift = Math.max(driftAB, driftBA);
                if (k.lastIndexOf('STEP', 0) === 0) {
                    turn_threshold = 0.5
                    if (Math.abs(turn) < turn_threshold && Math.abs(drift) < 0.5 && d > 0.01 && d < 20) {
                        if (d < min_d[k]) {
                            min_d[k] = d;
                            closest_line[k] = line;
                        }
                    }
                } else if (k.lastIndexOf('TURN', 0) === 0) {
                    if (Math.abs(turn) < 0.7 && d < 15) {
                        if (d < min_d[k]) {
                            min_d[k] = d;
                            closest_line[k] = line;
                        }
                    }
                }
            }
        }
    }
    return closest_line;
}

function walkOneStep(motion_type) {
    var line = validMoves[motion_type];
    if (line !== undefined) {
        setImagePlaneCamera(line);
        navigateToShot(line);
    }

    invokeJourneyWrapper(function () { journeyWrapper.stop(); });
}

function onKeyDown(event) {
    if (movingMode == 'walk') {
        var validKey = true;

        switch (event.keyCode) {
            case 37: // left arrow
                if (event.shiftKey) {
                    walkOneStep('TURN_LEFT');
                } else {
                    walkOneStep('STEP_LEFT');
                }
                break;
            case 38: // up arrow
                walkOneStep('STEP_FORWARD');
                break;
            case 39: // right arrow
                if (event.shiftKey) {
                    walkOneStep('TURN_RIGHT');
                } else {
                    walkOneStep('STEP_RIGHT');
                }
                break;
            case 40: // down arrow
                if (event.shiftKey) {
                    walkOneStep('TURN_U');
                } else {
                    walkOneStep('STEP_BACKWARD');
                }
                break;
            case 27: // ESC
                setMovingMode('orbit');
                break;
            case 83: // S
                invokeJourneyWrapper(function () { journeyWrapper.toggle(); });
            default:
                validKey = false;
                break;
        }

        if (validKey) {
            event.preventDefault();
        }
    }
}

function preloadAllImages() {
    for (var i = 0; i < camera_lines.length; ++i) {
        var shot_id = camera_lines[i].shot_id;
        var image_url = imageURL(shot_id);
        var temp_img = new Image();
        temp_img.src = image_url;
    }
}

function preloadValidMoves() {
    for (var k in validMoves) {
        if (validMoves.hasOwnProperty(k)) {
            var line = validMoves[k];
            if (line !== undefined) {
                var shot_id = line.shot_id;
                var image_url = imageURL(shot_id);
                var temp_img = new Image();
                temp_img.src = image_url;
            }
        }
    }
}

function updateValidMovesWidget() {
    $('#nav-left').css('visibility',
        (validMoves.STEP_LEFT === undefined) ? 'hidden':'visible');
    $('#nav-right').css('visibility',
        (validMoves.STEP_RIGHT === undefined) ? 'hidden':'visible');
    $('#nav-forward').css('visibility',
        (validMoves.STEP_FORWARD === undefined) ? 'hidden':'visible');
    $('#nav-backward').css('visibility',
        (validMoves.STEP_BACKWARD === undefined) ? 'hidden':'visible');
    $('#nav-turn-left').css('visibility',
        (validMoves.TURN_LEFT === undefined) ? 'hidden':'visible');
    $('#nav-turn-right').css('visibility',
        (validMoves.TURN_RIGHT === undefined) ? 'hidden':'visible');
    $('#nav-u-turn').css('visibility',
        (validMoves.TURN_U === undefined) ? 'hidden':'visible');
}

function animate() {
    requestAnimationFrame(animate);
    imagePlane.material.uniforms.opacity.value = 1 - options.imagePlaneOpacity;
    if (imagePlaneOld !== undefined) {
        imagePlaneOld.material.uniforms.opacity.value = 1;
    }
    if (invokeJourneyWrapper(function () { return journeyWrapper.isStarted() && journeyWrapper.isSmooth(); }) !== true) {
        options.imagePlaneOpacity *= 1 - options.animationSpeed;
    }

    controls.update();
}

function render() {
    validMoves = computeValidMoves();
    updateValidMovesWidget();
    if (invokeJourneyWrapper(function () { return journeyWrapper.isStarted(); }) !== true) {
        preloadValidMoves();
    }

    // Handle camera selection.
    if (hoverCamera !== undefined && hoverCamera !== selectedCamera) {
        hoverCamera.material.linewidth = 1;
        hoverCamera.material.color = options.cameraColor;
    }
    var vector = new THREE.Vector3(mouse.x, mouse.y, 1).unproject(camera);
    raycaster.set(camera.position, vector.sub(camera.position).normalize());
    var intersects = raycaster.intersectObjects(camera_lines, true);
    hoverCamera = undefined;
    for (var i = 0; i < intersects.length; ++i) {
        if (intersects[i].distance > 1.5 * options.cameraSize
            && intersects[i].object.visible) {
            hoverCamera = intersects[i].object;
            if (hoverCamera !== selectedCamera) {
                hoverCamera.material.linewidth = 2;
                hoverCamera.material.color = options.hoverCameraColor;
            }
            break;
        }
    }

    // Render.
    renderer.render(scene, camera);
}

/**
* added for floorplan by iida 2017/08
**/