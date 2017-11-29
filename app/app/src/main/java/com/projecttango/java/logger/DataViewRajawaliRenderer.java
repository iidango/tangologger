/*
 * Copyright 2014 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.projecttango.java.logger;

import android.content.Context;
import android.graphics.Color;
import android.view.MotionEvent;

import com.projecttango.java.logger.rajawali.FrustumAxes;
import com.projecttango.java.logger.rajawali.Grid;

import org.rajawali3d.materials.Material;
import org.rajawali3d.math.Quaternion;
import org.rajawali3d.math.vector.Vector3;
import org.rajawali3d.primitives.Line3D;
import org.rajawali3d.renderer.RajawaliRenderer;

import java.util.Stack;

/**
 * Renderer for Point Cloud data.
 */
public class DataViewRajawaliRenderer extends RajawaliRenderer {

    private static final float CAMERA_NEAR = 0.01f;
    private static final float CAMERA_FAR = 200f;
    private final int MAX_NUMBER_OF_TRAJECTORY = 1000;

    private TouchViewHandler mTouchViewHandler;

    // Objects rendered in the scene.
    private FrustumAxes mFrustumAxes;
    private Grid mGrid;

    // trajectoty
    private Line3D mTrajectory; // camera trajectory
    private Stack mTrajectoryPoints; // camera trajectory

    public DataViewRajawaliRenderer(Context context) {
        super(context);
        mTouchViewHandler = new TouchViewHandler(mContext, getCurrentCamera());
        mTouchViewHandler.setThirdPersonView();
    }

    @Override
    protected void initScene() {
        mGrid = new Grid(100, 1, 1, 0xFFCCCCCC);
        mGrid.setPosition(0, -1.3f, 0);
        getCurrentScene().addChild(mGrid);

        mFrustumAxes = new FrustumAxes(3);
        getCurrentScene().addChild(mFrustumAxes);

        // Indicate four floats per point since the point cloud data comes
        // in XYZC format.
        getCurrentScene().setBackgroundColor(Color.WHITE);
        getCurrentCamera().setNearPlane(CAMERA_NEAR);
        getCurrentCamera().setFarPlane(CAMERA_FAR);
        getCurrentCamera().setFieldOfView(37.5);

        mTrajectoryPoints = new Stack();
        mTrajectoryPoints.add(new Vector3(0, 0, 0));
        mTrajectory = new Line3D(mTrajectoryPoints, 3, 0x00ff00);
        Material material = new Material();
        mTrajectory.setMaterial(material);
        getCurrentScene().addChild(mTrajectory);
    }
    

    /**
     * Updates our information about trajectory.
     * NOTE: This needs to be called from the OpenGL rendering thread.
     */
    public void renderTrajectory(PoseData pData) {
        getCurrentScene().removeChild(mTrajectory);

        // render new trajectory
        mTrajectoryPoints = new Stack();
        int frec = pData.size() / MAX_NUMBER_OF_TRAJECTORY;
        for (int i = 0; i < pData.size(); i++){
            if (i % frec == 0){   // rerender trajectory
                mTrajectoryPoints.add(new Vector3(pData.getX(i), pData.getY(i), pData.getZ(i)));}
        }
        mTrajectory = new Line3D(mTrajectoryPoints, 3, 0x00ff00);
        Material material = new Material();
        mTrajectory.setMaterial(material);
        getCurrentScene().addChild(mTrajectory);
    }

    /**
     * Updates our information about the current device pose.
     * NOTE: This needs to be called from the OpenGL rendering thread.
     */
    public void updateView() {
        Quaternion quaternion = new Quaternion(1, 0, 0, 0);
        mFrustumAxes.setPosition(0, 0, 0);
        // Conjugating the Quaternion is needed because Rajawali uses left-handed convention for
        // quaternions.
        mFrustumAxes.setOrientation(quaternion.conjugate());
        mTouchViewHandler.updateCamera(new Vector3(0, 0, 0),
                quaternion);
    }

    @Override
    public void onOffsetsChanged(float v, float v1, float v2, float v3, int i, int i1) {
    }

    @Override
    public void onTouchEvent(MotionEvent motionEvent) {
        mTouchViewHandler.onTouchEvent(motionEvent);
    }
}
