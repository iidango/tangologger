/*
 * model
 */

function createFloorplan(reconstruction, floorplan_name){
    var url = urlParams.file;
    var floorplan = new THREE.Object3D();
    floorplan.name = floorplan_name;
    var data = reconstruction.floorplans[floorplan_name + '.png'];

    var t = data.translation;
    var offset_t = new THREE.Vector3(t[0], t[1], t[2]);
    floorplan.position.add(offset_t);

    var r = data.rotation;
    floorplan.rotation.x = r[0];
    floorplan.rotation.y = r[1];
    floorplan.rotation.z = r[2];

    var rate = data.pix_per_meter;
    var w = data.width/rate;
    var h = data.height/rate;

    if (options.floorplanMesh){
        // add floorplan image
        var fp_floorplanPrefix = '/data/floorplans/';
        var fp_loader = new THREE.TextureLoader();
        var floorplan_map = fp_loader.load(fp_floorplanPrefix + floorplan_name + '.png');
        floorplan_map.minFilter = THREE.LinearFilter;
        var geometry = new THREE.PlaneGeometry(w, h);
        var material = new THREE.MeshBasicMaterial({
            map: floorplan_map, 
            side: THREE.DoubleSide,
            alphaTest: 0.5,
            transparent: false, 
            // opacity: 0.9,
            // depthTest: false,
            // color: 0xaaaaaa    // floor color
            color: options.floorplan_colors[floorplan_name],
        });
        var mesh = new THREE.Mesh(geometry, material);
        mesh.name = 'floor_image';
        mesh.position.add(new THREE.Vector3(0, 0, 0));
        floorplan.add(mesh);

    }

    // set random offset to avoi over rapping
    floorplan.position.z += 3 * Math.random();

    return floorplan;
}

function createCameraLines(reconstruction) {
    var lines = [];

    // apply offset
    if (reconstruction.hasOwnProperty('metadata')){
        if (reconstruction.metadata.hasOwnProperty('shots_offset')){
            let shots_rotation = reconstruction.metadata.shots_offset.rotation;
            let shots_translation = reconstruction.metadata.shots_offset.translation;

            let s_r_vec = new THREE.Vector3(shots_rotation[0], shots_rotation[1], shots_rotation[2]);
            let s_t_vec = new THREE.Vector3(shots_translation[0], shots_translation[1], shots_translation[2]);

            let rt_shots_offset = new THREE.Matrix4().getInverse(getRt(shots_rotation, shots_translation));

            for (var shot_id in reconstruction.shots) {
                if (reconstruction.shots.hasOwnProperty(shot_id)) {
                    let r = reconstruction.shots[shot_id].rotation;
                    let t = reconstruction.shots[shot_id].translation;

                    let r_vec = new THREE.Vector3(r[0], r[1], r[2]);
                    let t_vec = new THREE.Vector3(t[0], t[1], t[2]);

                    let rt = getRt(r, t);
                    rt.multiplyMatrices(rt, rt_shots_offset);

                    let new_r = getRotationVector(new THREE.Matrix3().setFromMatrix4(rt));
                    let new_t = new THREE.Vector3().setFromMatrixPosition(rt);

                    reconstruction.shots[shot_id].rotation = new_r.toArray();
                    reconstruction.shots[shot_id].translation = new_t.toArray();
                }
            }
        }
    }

    for (var shot_id in reconstruction.shots) {
        if (reconstruction.shots.hasOwnProperty(shot_id)) {
            // var lineMaterial = new THREE.LineBasicMaterial({color: 'red'})
            var lineMaterial = new THREE.LineBasicMaterial();
            lineMaterial.color = options.cameraColor;
            var linegeo = cameraLineGeo(reconstruction, shot_id);
            var line = new THREE.Line(linegeo, lineMaterial, THREE.LineSegments);
            line.reconstruction = reconstruction;
            line.shot_id = shot_id;
            line.name = shot_id;
            lines.push(line);
        }
    }
    return lines;
}

function updateCameraLines() {
    for (var i = 0; i < camera_lines.length; ++i) {
        // var linegeo = cameraLineGeo(camera_lines[i].reconstruction, camera_lines[i].shot_id);
        // camera_lines[i].geometry.vertices = linegeo.vertices;
        // camera_lines[i].geometry.verticesNeedUpdate = true;

        var linegeo = cameraLineGeo(camera_lines[i].reconstruction, camera_lines[i].shot_id);
        camera_lines[i].geometry.dispose();
        camera_lines[i].geometry = linegeo;
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

function createAxis(){
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
    var line = new THREE.Line(linegeo, lineMaterial, THREE.LineSegments);
    return line;
}

function createGrid(){
    var grid = new THREE.Object3D();
    {
        var ggrid_linegeo = new THREE.Geometry();
        var N = 20;
        var scale = 2;
        for (var k = 0; k <= 2 * N; ++k) {
            ggrid_linegeo.vertices.push(
                new THREE.Vector3(scale * (k - N), scale * (-N), 0),
                new THREE.Vector3(scale * (k - N), scale * ( N), 0),
                new THREE.Vector3(scale * (-N), scale * (k - N), 0),
                new THREE.Vector3(scale * ( N), scale * (k - N), 0)
            );
        }
        var ggrid_lineMaterial = new THREE.LineBasicMaterial({color: 0x555555});
        var ggrid_line = new THREE.Line(ggrid_linegeo, ggrid_lineMaterial, THREE.LineSegments);
        grid.add(ggrid_line);
    }
    return grid;
}
