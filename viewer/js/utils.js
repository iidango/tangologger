/*
 * utils
 */

function getData() {
    parseUrl();

    if ('res' in urlParams) options.resolution = urlParams.res;

    jQuery.getJSON(urlParams.file, function(data) {
        if ('cameras' in data) {
            reconstructions = [data];
        } else {
            reconstructions = data;
            for (var r = 0; r < reconstructions.length; ++r) {
                var reconstruction = reconstructions[r];
                // if (reconstruction.metadata.name == 'floorplans'){
                if (Object.keys(reconstruction.floorplans).length != 0){
                    recon_floorplans.push(reconstruction);
                }
                if (Object.keys(reconstruction.shots).length != 0){
                    recon_tracks.push(reconstruction);
                }
            }
            recon_floorplans.sort(function(a,b){
                if(Object.keys(a.floorplans)[0] < Object.keys(b.floorplans)[0]){
                    return -1;
                }else{
                    return 1;
                }
            });
            recon_tracks.sort(function(a,b){
                if(a.metadata.name < b.metadata.name){
                    return -1;
                }else{
                    return 1;
                }
            });
        }
        $('#loading').remove();
        init();
        animate();
    });
}

function imageURL(reconstruction, shot_id) {
    var url = urlParams.file;
    // var slash = url.lastIndexOf('/');
    // var imagePath = '/images' + options.resolution.replace('original', '')
    // return url.substring(0, slash) + imagePath +'/' + shot_id;
    var imagePath = url + '/' + reconstruction.metadata.prefix + '/images/' + shot_id;
    return imagePath;
}
function floorplanURL(floorplan_id) {
    var url = urlParams.file
    var slash = url.lastIndexOf('/');
    var floorplanPath = '/floorplans';
    return url.substring(0, slash) + floorplanPath +'/' + floorplan_id;
}

function parseUrl() {
    var match,
        pl     = /\+/g,  // Regex for replacing addition symbol with a space
        search = /([^&=]+)=?([^&]*)/g,
        decode = function (s) { return decodeURIComponent(s.replace(pl, ' ')); },
        hash  = window.location.hash.substring(1);

    urlParams = {};
    match = search.exec(hash);
    while (match){
        urlParams[decode(match[1])] = decode(match[2]);
        match = search.exec(hash);
    }
}

function rotate(vector, angleaxis) {
    var v = new THREE.Vector3(vector[0], vector[1], vector[2]);
    var axis = new THREE.Vector3(angleaxis[0],
        angleaxis[1],
        angleaxis[2]
    );
    var angle = axis.length();
    axis.normalize();
    var matrix = new THREE.Matrix4().makeRotationAxis(axis, angle);
    v.applyMatrix4(matrix);
    return v;
}

function opticalCenter(shot) {
    var angleaxis = [-shot.rotation[0],
        -shot.rotation[1],
        -shot.rotation[2]
    ];
    var Rt = rotate(shot.translation, angleaxis);
    Rt.negate();
    return Rt;
}

function viewingDirection(shot) {
    var angleaxis = [-shot.rotation[0],
        -shot.rotation[1],
        -shot.rotation[2]
    ];
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
        zc - shot.translation[2]
    ];


    var angleaxis = [-shot.rotation[0],
        -shot.rotation[1],
        -shot.rotation[2]
    ];

    return rotate(xct, angleaxis);
}

function projectorCameraMatrix(cam, shot) {
    var angleaxis = shot.rotation;
    var axis = new THREE.Vector3(angleaxis[0],
        angleaxis[1],
        angleaxis[2]
    );
    var angle = axis.length();
    axis.normalize();
    var rotation = new THREE.Matrix4().makeRotationAxis(axis, angle);
    var t = shot.translation;
    var translation = new THREE.Vector3(t[0], t[1], t[2]);
    rotation.setPosition(translation);

    return rotation;

    // if (cam.projection_type == 'equirectangular' || cam.projection_type == 'spherical')
    //     return rotation;
    // var dx = cam.width / Math.max(cam.width, cam.height) / cam.focal;
    // var dy = cam.height / Math.max(cam.width, cam.height) / cam.focal;
    // var projection = new THREE.Matrix4().makeFrustum(-dx, +dx, +dy, -dy, -1, -1000);
    // return projection.multiply(rotation);
}

function getRt(rotation, translation){
    var axis = new THREE.Vector3(rotation[0], rotation[1], rotation[2]);
    var angle = axis.length();
    axis.normalize();
    var rt = new THREE.Matrix4().makeRotationAxis(axis, angle);

    var t = new THREE.Vector3(translation[0], translation[1], translation[2]);
    rt.setPosition(t);

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

function reconstruction_of_shot(recon_tracks, shot_id) {
    for (var r = 0; r < recon_tracks.length; ++r) {
        if (shot_id in recon_tracks[r]['shots']) {
            return recon_tracks[r];
        }
    }
    return undefined;
}

function reconstruction_id_of_shot(recon_tracks, shot_id) {
    for (var r = 0; r < recon_tracks.length; ++r) {
        if (shot_id in recon_tracks[r]['shots']) {
            return r;
        }
    }
    return undefined;
}

function angleBetweenVector2(x1, y1, x2, y2) {
    var a = Math.atan2(y2, x2) - Math.atan2(y1, x1);
    if (a > Math.PI) return a - 2 * Math.PI;
    else if (a < -Math.PI) return a + 2 * Math.PI;
    else return a;
}

function preLoadImage(camera){
    var shot_id = camera.shot_id;
    var reconstruction = camera.reconstruction;
    var shot = reconstruction.shots[shot_id];
    var cam = reconstruction.cameras[shot.camera];

    var image_url = imageURL(reconstruction, shot_id);
    if (!(image_url in preLoadedImageMaterials)){
        preLoadedImageMaterials[image_url] = createImagePlaneMaterial(cam, shot, shot_id, reconstruction);
        console.log('load: ' + image_url);
    }
}

function buildingOf(fname){
    for(var bname in BUILDING){
        if(BUILDING[bname].indexOf(fname) >= 0){
            return bname;
        }
    }
    return undefined;
}

function buildingFromName(bname){
    var found = false;
    for(var i = 0; i < building_groups.length; i++){
        if(building_groups[i].name == bname){
            found = true;
            return building_groups[i];
        }
    }
    if(!found){
        return undefined;
    }
}

function buildingFromFName(fname){
    let bname = buildingOf(fname);
    return buildingFromName(bname);
}

function floorplanFromName(fname){
    var found = false;
    for(var i = 0; i < floorplan_groups.length; i++){
        if(floorplan_groups[i].name == fname){
            found = true;
            return floorplan_groups[i];
        }
    }
    if(!found){
        return undefined;
    }
}

function floorplanReconstructionFromName(fname){
    var found = false;
    for (var i = 0; i < recon_floorplans.length; ++i) {
        var reconstruction = recon_floorplans[i];
        for (var floorplan_id in recon_floorplans[i].floorplans) {
            var name = floorplan_id.split('.')[0];    // remove .png
            if(name == fname){
                found = true;
                return reconstruction.floorplans[floorplan_id];
            }
        }
    }
    if(!found){
        return undefined;
    }
}

function vector3To2(vec3){
    return new THREE.Vector2(vec3.x, vec3.y);
}