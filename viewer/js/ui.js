/*
 * ui
 */

function addDatGui(){
    var gui = new dat.GUI();

    f1 = gui.addFolder('Options');
    // f1.add(options, 'pointSize', 0, 10)
    //     .listen()
    //     .onChange(setPointSize);
    f1.add(options, 'cameraSize', 0, 2)
        .listen()
        .onChange(setCameraSize);
    f1.add(options, 'imagePlaneSize', 1, 200)
        .onChange(function(value) {
            options.imagePlaneSize *= 1.5;
            imagePlane.geometry = imagePlaneGeo(imagePlaneCameraLineOld.reconstruction, imagePlaneCameraLineOld.shot_id);
            options.imagePlaneSize /= 1.5;
            imagePlane.geometry = imagePlaneGeo(imagePlaneCameraLine.reconstruction, imagePlaneCameraLine.shot_id);
            render();
        });
    // f1.add(options, 'animationSpeed', 0, 0.2)
    //     .onChange(function(value) {
    //         tp_controls.animationSpeed = value;
    //         invokeJourneyWrapper(function () { journeyWrapper.updateInterval(); });
    //     });
    // f1.add(options, 'resolution', [ '320', '640', 'original' ] );
    // f1.add(options, 'showThumbnail')
    //     .listen()
    //     .onChange(setShowThumbnail);
    f1.add(options, 'drawGrid')
        .listen()
        .onChange(setDrawGrid);
    // f1.add(options, 'showNaviPosition')
    //     .listen()
    //     .onChange(setShowNaviPosition);
    // f1.add(options, 'showImagePlane')
    //     .listen()
    //     .onChange(setShowImagePlane);
    f1.add(options, 'showTracks')
        .listen()
        .onChange(setShowTracks);
    f1.add(options, 'showFloorplans')
        .listen()
        .onChange(setShowFloorplans);
    // f1.add(options, 'showBuildings')
    //     .listen()
    //     .onChange(setShowBuildings);
    f1.close();

    var f3 = gui.addFolder('tracks');
    options.track_visibles = {};
    for (var r = 0; r < recon_tracks.length; ++r) {
        options.track_visibles[r] = true;
        var name = recon_tracks[r].metadata.name;
        options.track_visibles[name] = true;
        f3.add(options.track_visibles, name, true)
            .onChange(
                (function(rr) {
                    return function (value) {
                        track_groups[rr].traverse(
                            function (object) { object.visible = value; } );
                        render();
                    };
                })(r)
            ).listen();
    }
    f3.close();

    var f4 = gui.addFolder('floorplans');
    options.floorplan_visibles = {};
    for (r = 0; r < recon_floorplans.length; ++r) {
        options.floorplan_visibles[r] = {};
        name = Object.keys(recon_floorplans[r].floorplans)[0].split('.')[0];
        options.floorplan_visibles[name] = true;
        f4.add(options.floorplan_visibles, name, true)
            .onChange(
                (function(rr) {
                    return function (value) {
                        floorplan_groups[rr].traverse(
                            function (object) { object.visible = value; } );
                        render();
                    };
                })(r)
            ).listen();
    }
    f4.close();

    gui.close();
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

function setPointSize(value) {
    if(pointCloudMaterial === undefined) return;
    options.pointSize = value;
    pointCloudMaterial.size = value;
    for (var i = 0; i < point_clouds.length; ++i) {
        point_clouds[i].visible = (value > 0);
    }
    render();
}

function setCameraSize(value) {
    options.cameraSize = value;
    for (var r = 0; r < recon_tracks.length; ++r) {
        updateCameraLines(recon_tracks[r]);
    }
    render();
}

function setShowThumbnail(value) {
    options.showThumbnail = value;
    $('#info').css('visibility', value ? 'visible' : 'hidden');
}

function setShowNaviPosition(value) {
    options.showNaviPosition = value;
    followTarget.visible = value;
    render();
}

function setShowImagePlane(value) {
    options.showImagePlane = value;
    imagePlane.visible = value;
    if (movingMode === MOVINGMODE.WALK) {
        imagePlaneOld.visible = value;
    } else if(movingMode == MOVINGMODE.ORBIT){
        imagePlaneOld.visible = false;
    }
    render();
}

function setDrawGrid(value) {
    options.drawGrid = value;
    grid_group.visible = value;
    render();
}

function setShowTracks(value) {
    options.showTracks = value;
    scene_group.getObjectByName('tracks').visible = value;
    render();
}

function setShowFloorplans(value) {
    options.showFloorplans = value;
    scene_group.getObjectByName('floorplans').visible = value;
    render();
}

function setShowBuildings(value) {
    options.showBuildings = value;
    scene_group.getObjectByName('buildings').visible = value;
    render();
}

function setMovingMode(mode) {
    if(!split_view){
        if (mode != movingMode) {
            movingMode = mode;
            if (mode == MOVINGMODE.ORBIT) {
                invokeJourneyWrapper(function () { journeyWrapper.stop(); journeyWrapper.addShowPathController(); });
                resetWalkMode();
                swapOptions();
                imagePlane.material.depthWrite = true;
                imagePlaneOld.material.depthWrite = true;
                $('#navigation').hide();
                tp_controls.enabled = true;
                fp_controls.enabled = false;
                fp_controls.reset();
                scene_group.getObjectByName('floorplans').visible = true;
            } else if (mode == MOVINGMODE.WALK) {
                invokeJourneyWrapper(function () { journeyWrapper.removeShowPathController(); });
                swapOptions();
                imagePlane.material.depthWrite = false;
                imagePlaneOld.material.depthWrite = false;
                $('#navigation').show();
                tp_controls.enabled = false;
                fp_controls.enabled = true;
                tp_controls.reset();
                scene_group.getObjectByName('floorplans').visible = false;
            }
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
        showNaviPosition: savedOptions.showNaviPosition,
        showImagePlane: savedOptions.showImagePlane,
        showTracks: savedOptions.showTracks,
        showFloorplans: savedOptions.showFloorplans,
        drawGrid: savedOptions.drawGrid,
    };

    savedOptions.pointSize = options.pointSize;
    savedOptions.cameraSize = options.cameraSize;
    savedOptions.showThumbnail = options.showThumbnail;
    savedOptions.showNaviPosition = options.showNaviPosition;
    savedOptions.showImagePlane = options.showImagePlane;
    savedOptions.showTracks = options.showTracks;
    savedOptions.showFloorplans = options.showFloorplans;
    savedOptions.drawGrid = options.drawGrid;

    setPointSize(tmpOptions.pointSize);
    setCameraSize(tmpOptions.cameraSize);
    setShowThumbnail(tmpOptions.showThumbnail);
    setShowNaviPosition(tmpOptions.showNaviPosition);
    setShowImagePlane(tmpOptions.showImagePlane);
    setShowTracks(tmpOptions.showTracks);
    setShowFloorplans(tmpOptions.showFloorplans);
    setDrawGrid(tmpOptions.drawGrid);
}

function changeMovingMode(mode){
    if(movingMode === mode) return;
    switch(mode){
    case MOVINGMODE.ORBIT:
        setMovingMode(mode);
        selectedCamera.visible = true;
        break;
    case MOVINGMODE.WALK:
        setMovingMode(mode);
        var reconstruction = selectedCamera.reconstruction;
        var shot = reconstruction['shots'][selectedCamera.shot_id];
        var cam = reconstruction['cameras'][shot['camera']];
        fp_controls.animationTarget = pixelToVertex(cam, shot, 0, 0, 0.1);
        fp_controls.animationPosition = pixelToVertex(cam, shot, 0, 0, 0);

        selectedCamera.visible = false;
        navigateToShot(selectedCamera);
        break;
    default:
        console.log('moving mode not found' + mode);
        break;
    }
}

function setWalkMode(mode){
    walkMode = mode;
    switch(walkMode){
    case WALKMODE.FLOORPLAN:
        $('#walkMode').text('change view mode');
        setShowImagePlane(false);
        setShowFloorplans(true);
        fp_camera.far = 1000;
        fp_camera.updateProjectionMatrix();
        break;
    case WALKMODE.PANORAMA:
        $('#walkMode').text('change view mode');
        setShowImagePlane(true);
        setShowFloorplans(false);
        fp_camera.far = 15;
        fp_camera.updateProjectionMatrix();
        break;
    default:
        console.log('invalid walk mode: ' + mode);
        break;
    }

}

function toggleWalkMode(){
    if(movingMode !== MOVINGMODE.WALK) return;
    if(walkMode === WALKMODE.FLOORPLAN){
        setWalkMode(WALKMODE.PANORAMA);
    }else{
        setWalkMode(WALKMODE.FLOORPLAN);
    }
}

function changeCamereLinesColor(index, color){
    options.track_colors[track_names[index]] = color;
    for(var i = 0; i < track_groups[index].children.length; i++){
        track_groups[index].children[i].material.color = color;
    }
    return;
}

function setTrackColorDifferent(){
    for(var i = 0; i < track_groups.length; i++){
        // var hex = Math.random() * 0xffffff;
        var c = new THREE.Color(COLOR_LIST[i + 10]);
        changeCamereLinesColor(i, c);
    }
}

function onKeyDown(event) {
    if (movingMode == MOVINGMODE.WALK) {
        var validKey = true;

        switch (event.keyCode) {
        case 37: // left arrow
            // if (event.shiftKey) {
            //     walkOneStep('TURN_LEFT');
            // } else {
            //     walkOneStep('STEP_LEFT');
            // }
            break;
        case 38: // up arrow
            // walkOneStep('STEP_FORWARD');
            break;
        case 39: // right arrow
            // if (event.shiftKey) {
            //     walkOneStep('TURN_RIGHT');
            // } else {
            //     walkOneStep('STEP_RIGHT');
            // }
            break;
        case 40: // down arrow
            // if (event.shiftKey) {
            //     walkOneStep('TURN_U');
            // } else {
            //     walkOneStep('STEP_BACKWARD');
            // }
            break;
        case 27: // ESC
            changeMovingMode(MOVINGMODE.ORBIT);
            break;
        case 83: // S
            // invokeJourneyWrapper(function () { journeyWrapper.toggle(); });
            break;
        default:
            validKey = false;
            break;
        }

        if (validKey) {
            event.preventDefault();
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

function enableSplitView(){
    setShowImagePlane(true);
    setShowThumbnail(false);
    navigateToShot(imagePlaneCameraLineOld);
    navigateToShot(imagePlaneCameraLine);
    movingMode = MOVINGMODE.NONE;
    walkMode = WALKMODE.NONE;
}

function disableSplitView(){
    setShowImagePlane(false);
}
