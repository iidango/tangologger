/*
 * renderer
 */
/* global 
 *     Z_RATI: false
 *     COLOR_LIST: false
 *     FLOOR_COLOR: false
 *     BUILDING_MODEL: false
 *     BUILDING_COLOR: false
 *     BUILDING_HEIGHT: false
 *     VIEW_MODE: false
 * 
 *     frame: true
 *     f1: true
 *     urlParams: true
 *     container: true
 *     fp_camera: true
 *     tp_camera: true
 *     fp_controls: true
 *     tp_controls: true
 *     scene: true
 *     fp_scene: true
 *     renderer: true
 *     mouse: true
 *     active_view: true
 *     split_view: true
 *     split_view_ratio: true
 *     tp_mouse: true
 *     fp_mouse: true
 *     hoverCamera: true
 *     raycaster: true
 *     parentTransform: true
 *     selectedCamera: true
 *     followTarget: true
 *     imagePlane: true
 *     imagePlaneCameraLine: true
 *     imagePlaneOld: true
 *     imagePlaneCameraLineOld: true
 *     preLoadedImageMaterials: true
 *     scene_group: true
 *     grid_group: true
 *     sub_group: true
 *     pointCloudMaterial: true
 *     reconstructions: true
 *     recon_floorplans: ture
 *     recon_tracks: true
 *     track_groups: true
 *     track_names: true
 *     floorplan_groups: true
 *     floorplan_names: true
 *     building_groups: true
 *     building_names: true
 *     point_clouds: true
 *     camera_lines: true
 *     imageMaterials: true
 *     num_preview_plan: true
 *     moveSpeed: true
 *     turnSpeed: true
 *     previousShot: true
 *     validMoves: true
 *     MOVINGMODE: false
 *     movingMode: true
 *     WALKMODE: false
 *     walkMode: true
 *     savedOptions: true
 *     naviStatus: true
 *     naviOptions: true
 *     options: true
 * 
 *     getData: false
 *     onKeyDown: false
 *     createBuilding: false
 *     createFloorplan: false
 *     createCameraLines: false
 *     createImagePlane: false
 *     createAxis: false
 *     createGrid: false
 *     createBackground: false
 *     createFollowTarget: false
 *     imagePlaneGeo: false
 *     createImagePlaneMaterial: false
 *     setImagePlanePosition: false
 *     addDatGui: false
 *     setShowThumbnail: false
 *     imageURL: false
 *     changeMovingMode: false
 *     preLoadNearImage: false
 *     stopNavigation: false
 *     endNavigation: false
 *     setNavigatedFloor: false
 *     setCurrentFloor: false
 *     updateNaviFloorView: false
 *     enableSplitView: false
 *     floorplanReconstructionFromName: false
 */

getData();

function initCameras(){
    // third person camera
    tp_camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 10000);
    tp_camera.position.x = 50;
    tp_camera.position.y = 50;
    tp_camera.position.z = 50;
    tp_camera.up = new THREE.Vector3(0,0,1);
    tp_controls = new THREE.OrbitControls(tp_camera, renderer.domElement);
    tp_controls.addEventListener('change', render);
    tp_controls.noRotate = false;
    tp_controls.noLookAround = false;
    tp_controls.noPan = false;
    tp_controls.noZoom = false;
    tp_controls.noKeys = false;
    tp_controls.animationPosition.z += 10;
    tp_controls.dollyOut(4);

    // first person camera
    fp_camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.03, 150);
    fp_camera.position.x = 50;
    fp_camera.position.y = 50;
    fp_camera.position.z = 50;
    fp_camera.up = new THREE.Vector3(0,0,1);
    fp_camera.far = 10;
    fp_controls = new THREE.OrbitControls(fp_camera, renderer.domElement);
    fp_controls.addEventListener('change', render);
    fp_controls.noRotate = false;
    fp_controls.noLookAround = false;
    // fp_controls.noPan = true;
    // fp_controls.noZoom = true;
    // fp_controls.noKeys = true;
    fp_controls.noPan = false;
    fp_controls.noZoom = false;
    fp_controls.noKeys = false;
}

function init() {
    raycaster = new THREE.Raycaster();
    raycaster.precision = 0.01;

    renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    // renderer.setClearColor( 0x202020, 0.0);
    renderer.setClearColor( 0xffffff);
    // renderer.setClearColor(0xeeeeee);
    renderer.sortObjects = true;

    container = document.getElementById( 'ThreeJS' );
    container.appendChild(renderer.domElement);

    initCameras();

    window.addEventListener('resize', onWindowResize, false);
    renderer.domElement.addEventListener('mousemove', onDocumentMouseMove, false);
    renderer.domElement.addEventListener('mousedown', onDocumentMouseDown, false);
    window.addEventListener( 'keydown', onKeyDown, false );

    scene_group = new THREE.Object3D();

    // light
    var light = new THREE.AmbientLight(0xffffff);
    light.name = 'AmbientLight';
    scene_group.add(light);

    // floorplans
    var floorplans = new THREE.Object3D();
    floorplans.name = 'floorplans';
    for (var i = 0; i < recon_floorplans.length; ++i) {
        var reconstruction = recon_floorplans[i];
        for (var floorplan_id in recon_floorplans[i].floorplans) {
            var floorplan_name = floorplan_id.split('.')[0];    // remove .png
            floorplan_names.push(floorplan_name);
            // options.floorplan_colors[floorplan_name] = options.floorplanColor.clone();
            options.floorplan_colors[floorplan_name] = new THREE.Color(FLOOR_COLOR[floorplan_name]);

            var floorplan = createFloorplan(reconstruction, floorplan_name);

            floorplan_groups.push(floorplan);
            floorplans.add(floorplan);
        }
    }
    floorplans.visible = options.showFloorplans;
    scene_group.add(floorplans);

    // tracks
    var tracks = new THREE.Object3D();
    tracks.name = 'tracks';
    for (var r = 0; r < recon_tracks.length; ++r) {
        reconstruction = recon_tracks[r];
        var group = new THREE.Object3D();
        group.name = reconstruction.metadata.name;
        track_groups.push(group);
        track_names.push(reconstruction.metadata.name);
        options.track_colors[reconstruction.metadata.name] = options.cameraColor.clone();
        tracks.add(group);

        // Cameras.
        var lines = createCameraLines(reconstruction);
        for (var j = 0; j < lines.length; ++j) {
            group.add(lines[j]);
            camera_lines.push(lines[j]);
        }
    }
    tracks.visible = options.showTracks;
    scene_group.add(tracks);

    grid_group = new THREE.Object3D();
    grid_group.name = 'grid';
    grid_group.visible = options.drawGrid;
    // Axis
    // var axis = createAxis();
    // grid_group.add(axis);
    // Ground grid
    // var grid = createGrid();
    // grid_group.add(grid);
    // background image
    // var background = createBackground();
    // grid_group.add(background);

    // append all scene
    scene = new THREE.Scene();
    scene.add(scene_group);
    scene.add(grid_group);
    scene.add(sub_group);

    // append fp_scene
    fp_scene = new THREE.Scene();
    fp_scene.add(imagePlane);

    addDatGui();

    setShowThumbnail(options.showThumbnail);

    if(split_view){
        enableSplitView();
    }
    render();
}

function setSelectedCamera(cameraObject) {
    var r = cameraObject.reconstruction;
    var shot_id = cameraObject.shot_id;
    var shot = r['shots'][shot_id];
    var image_url = imageURL(r, shot_id);
    if (selectedCamera !== undefined) {
        if (movingMode === MOVINGMODE.WALK){
            selectedCamera.material.linewidth = options.walkingModeCameraLineLength;
            selectedCamera.material.color = options.track_colors[selectedCamera.parent.name];
            selectedCamera.visible = true;
        }else{
            selectedCamera.material.linewidth = options.cameraLineLength;
            selectedCamera.material.color = options.track_colors[selectedCamera.parent.name];
        }
    }
    selectedCamera = cameraObject;
    selectedCamera.material.linewidth = options.selectedCameraLineLength;
    selectedCamera.material.color = options.selectedCameraColor;
    if (movingMode === MOVINGMODE.WALK){
        selectedCamera.visible = false;
    }

    var image_tag = document.getElementById('image');
    image_tag.src = image_url;
    var text = document.getElementById('image_text');
    text.innerHTML = cameraObject.parent.name + '/' + shot_id;
}

function setImagePlaneCameraLine(cameraObject) {
    var r = cameraObject.reconstruction;
    var shot_id = cameraObject.shot_id;
    var shot = r['shots'][shot_id];
    var cam = r['cameras'][shot['camera']];

    if (previousShot !== cameraObject.shot_id) {
        previousShot = cameraObject.shot_id;
        if (selectedCamera !== cameraObject) {
            setSelectedCamera(cameraObject);
        }

        // imagePlaneOld.material.dispose();
        imagePlaneOld.material = imagePlane.material;
        imagePlaneCameraLineOld = imagePlaneCameraLine;
        imagePlaneCameraLine = cameraObject;

        var image_url = imageURL(imagePlaneCameraLine.reconstruction, imagePlaneCameraLine.shot_id);
        imagePlane.material = image_url in preLoadedImageMaterials? preLoadedImageMaterials[image_url]: createImagePlaneMaterial(cam, shot, imagePlaneCameraLine.shot_id, imagePlaneCameraLine.reconstruction);
        setImagePlanePosition();
    }
}

function onWindowResize() {
    tp_camera.aspect = window.innerWidth / window.innerHeight;
    tp_camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    render();
}

function onDocumentMouseMove(event) {
    let h = window.innerHeight;
    let w = window.innerWidth;
    let x = event.clientX;
    let y = event.clientY;
    event.preventDefault();
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;

    if(split_view){
        tp_mouse.x = (x / w) * 2 - 1;
        tp_mouse.y = - (y / (h * split_view_ratio)) * 2 + 1;

        fp_mouse.x = (x / w) * 2 - 1;
        fp_mouse.y = - ((y - h * split_view_ratio) / (h * (1 - split_view_ratio))) * 2 + 1;
        // console.log('mouse: ' + mouse.x + ', ' + mouse.y);
        // console.log('tp_mouse: ' + tp_mouse.x + ', ' + tp_mouse.y);
        // console.log('fp_mouse: ' + fp_mouse.x + ', ' + fp_mouse.y);

        active_view = y < h * split_view_ratio ? VIEW_MODE.THIRD_PERSON: VIEW_MODE.FIRST_PERSON;
        switch(active_view){
        case VIEW_MODE.THIRD_PERSON:
            tp_controls.enabled = true;
            fp_controls.enabled = false;
            break;
        case VIEW_MODE.FIRST_PERSON:
            tp_controls.enabled = false;
            fp_controls.enabled = true;
            break;
        default:
            console.log('invalid view mode!!: ' + active_view);
            break;
        }
        
    }
    render();
}

function onDocumentMouseDown(event) {
    window.focus();
    if (hoverCamera === undefined) return;

    if(!split_view){
        switch(movingMode){
        case MOVINGMODE.ORBIT:
            if (selectedCamera !== hoverCamera) {
                setSelectedCamera(hoverCamera);
                setImagePlaneCameraLine(hoverCamera);
            } else {
                changeMovingMode(MOVINGMODE.WALK);
            }
            break;
        case MOVINGMODE.WALK:
            if (selectedCamera !== hoverCamera){
                navigateToShot(hoverCamera);
            }
            break;
        default:
            console.log('moving mode not found' + movingMode);
            break;
        }
    }
    render();
}

function navigateToShot(camera) {
    setImagePlaneCameraLine(camera);

    var reconstruction = camera.reconstruction;
    var shot = reconstruction['shots'][camera.shot_id];
    var cam = reconstruction['cameras'][shot['camera']];

    if(naviStatus.running){
        fp_controls.goto_shot(cam, shot, true);
    }else{
        fp_controls.goto_shot(cam, shot, false);
    }
}

function animate() {
    frame += 1;
    requestAnimationFrame(animate);
    // imagePlane.material.uniforms.opacity.value = 1 - options.imagePlaneOpacity;
    if (imagePlaneOld !== undefined) {
        imagePlaneOld.material.uniforms.opacity.value = 1;
    }

    if(split_view){
        tp_controls.update();
        fp_controls.update();
    }else if (movingMode == MOVINGMODE.ORBIT){
        tp_controls.update();
    }else if (movingMode == MOVINGMODE.WALK){
        fp_controls.update();
    }

    // navigation
    if(naviStatus.running && frame%naviOptions.speed == 0){
        var next_pos = naviStatus.waypoints[naviStatus.next_posi].position;
        // if(naviStatus.waypoints[naviStatus.next_posi].floor != undefined){
        //     console.log(naviStatus.waypoints[naviStatus.next_posi].floor.name);
        // }
        followTarget.position.set(next_pos[0], next_pos[1], next_pos[2]);

        var next_floor = naviStatus.waypoints[naviStatus.next_posi].floor;
        if(naviStatus.current_floor != next_floor){
            updateNaviFloorView(next_floor);
        }

        // move follow target
        // fp_camera.position.set(followTarget.position.x, followTarget.position.y, followTarget.position.z);
        if(split_view || movingMode == MOVINGMODE.WALK){
            var next_shot = naviStatus.waypoints[naviStatus.next_posi].shot;
            navigateToShot(next_shot);
        }

        naviStatus.current_pos = next_pos;
        naviStatus.current_floor = next_floor;
        naviStatus.next_posi += 1;
        if(naviStatus.next_posi === naviStatus.waypoints.length){
            // stopNavigation();
            endNavigation();
        }
    }

    render();
}

function tp_render(){
    let left = 0;
    let top = 0;
    let width = window.innerWidth;
    let height = window.innerHeight * split_view_ratio;
    renderer.setViewport( left, top, width, height );
    renderer.setScissor( left, top, width, height );
    renderer.setScissorTest( true );

    // Render.
    renderer.render(scene, tp_camera);
}

function fp_render(){
    let left = 0;
    let top = window.innerHeight * split_view_ratio;
    let width = window.innerWidth;
    let height = window.innerHeight;
    renderer.setViewport( left, top, width, height );
    renderer.setScissor( left, top, width, height );
    renderer.setScissorTest( true );

    // Render.
    renderer.render(fp_scene, fp_camera);
}

function render() {
    let current_camera, current_mouse;
    if (split_view){
        current_camera = active_view == VIEW_MODE.FIRST_PERSON ? fp_camera: tp_camera;
        current_mouse = active_view == VIEW_MODE.FIRST_PERSON ? fp_mouse: tp_mouse;
    }else{
        current_camera = movingMode == MOVINGMODE.WALK ? fp_camera: tp_camera;
        current_mouse = mouse;
    }

    // Handle camera selection.
    if (hoverCamera !== undefined && hoverCamera !== selectedCamera) {
        hoverCamera.material.linewidth = 1;
        hoverCamera.material.color = options.track_colors[hoverCamera.parent.name];
    }

    // mouse vector
    // TODO raycaster for split view and first person camera may not work...
    raycaster.setFromCamera(current_mouse, current_camera);
    var intersects = raycaster.intersectObjects(camera_lines);
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
    // renderer.render(scene, current_camera);
    if(split_view){
        tp_render();
        fp_render();
    }else{
        renderer.render(scene, current_camera);
    }
}
