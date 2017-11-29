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

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.hardware.display.DisplayManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import org.rajawali3d.scene.ASceneFrameCallback;
import org.rajawali3d.surface.RajawaliSurfaceView;

import java.io.File;
import java.util.ArrayList;

/**
 * Main Activity class for visualizing log data.
 * logic is delegated to the {@link DataViewRajawaliRenderer} class.
 */
public class ShowDataActivity extends Activity{
    private static final String TAG = ShowDataActivity.class.getSimpleName();
    private static final String DATA_PATH = SensorData.OUTPUT_PATH;
    private static final String CAMERAPOSE_LOG_FILE = "_cameraPose.csv";  // TODO stringに逃がす

    private static final String UX_EXCEPTION_EVENT_DETECTED = "Exception Detected: ";
    private static final String UX_EXCEPTION_EVENT_RESOLVED = "Exception Resolved: ";

    private DataViewRajawaliRenderer mRenderer;
    private RajawaliSurfaceView mSurfaceView;

    private Button mSelectFileButton;
    private TextView mSelectedFileNameTextView;
    private File mSelectedFile;
    private PoseData mSelectedPoseData;
    private File[] mFileList;
    private ArrayList<Integer> mFileIndex;
    private boolean mUpdateTrajectory;  // rerender trajectory flag
    private loadFileTask mLoadFileTask;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_show_data_view);

        Intent intent = getIntent();

        mSurfaceView = (RajawaliSurfaceView) findViewById(R.id.gl_surface_view);

        mRenderer = new DataViewRajawaliRenderer(this);
        setupRenderer();

        DisplayManager displayManager = (DisplayManager) getSystemService(DISPLAY_SERVICE);
        if (displayManager != null) {
            displayManager.registerDisplayListener(new DisplayManager.DisplayListener() {
                @Override
                public void onDisplayAdded(int displayId) {
                }

                @Override
                public void onDisplayChanged(int displayId) {
                    synchronized (this) {
                    }
                }

                @Override
                public void onDisplayRemoved(int displayId) {
                }
            }, null);
        }
        setupTextViewsAndButtons();
    }

    @Override
    protected void onResume() {
        super.onResume();
    }

    /**
     * Sets Texts views to display statistics of Poses being received. This also sets the buttons
     * used in the UI. Note that this needs to be called after TangoService and Config
     * objects are initialized since we use them for the SDK-related stuff like version number,
     * etc.
     */
    private void setupTextViewsAndButtons() {
        mSelectFileButton = (Button) findViewById(R.id.select_file_button);
        mSelectedFileNameTextView = (TextView) findViewById(R.id.selected_file_name_textview);
    }

    @Override
    protected void onPause() {
        super.onPause();
    }

    /**
     * Sets Rajawali surface view and its renderer. This is ideally called only once in onCreate.
     */
    public void setupRenderer() {
        mSurfaceView.setEGLContextClientVersion(2);
        mRenderer.getCurrentScene().registerFrameCallback(new ASceneFrameCallback() {
            @Override
            public void onPreFrame(long sceneTime, double deltaTime) {
                // NOTE: This will be executed on each cycle before rendering; called from the
                // OpenGL rendering thread.

                // render trajectory
                if(mUpdateTrajectory){
                    mRenderer.renderTrajectory(mSelectedPoseData);
                    Log.i(TAG, "Render Trajectory");
                    mUpdateTrajectory = false;
                }
                mRenderer.updateView();
            }

            @Override
            public boolean callPreFrame() {
                return true;
            }

            @Override
            public void onPreDraw(long sceneTime, double deltaTime) {

            }

            @Override
            public void onPostFrame(long sceneTime, double deltaTime) {

            }
        });
        mSurfaceView.setSurfaceRenderer(mRenderer);
    }


    @Override
    public boolean onTouchEvent(MotionEvent event) {
        mRenderer.onTouchEvent(event);
        return true;
    }

    /**
     * The "Select File" button has been clicked.
     * Defined in {@code activity_position_view.xml}
     */
    public void selectFileClicked(View view) {
        // create candiate file list
        File dir = new File(DATA_PATH);
        File[] files = dir.listFiles();
        mFileList = dir.listFiles();
        ArrayList<String> file_names = new ArrayList<>();
        mFileIndex = new ArrayList<>();
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file.getName().endsWith(CAMERAPOSE_LOG_FILE)) {
                file_names.add(file.getName());
                mFileIndex.add(i);
            }
        }

        file_names.add("Cancel");
        final String[] items = (String[])file_names.toArray(new String[0]);

        // show select box
        new AlertDialog.Builder(this)
                .setTitle("Select File")
                .setItems(items, new DialogInterface.OnClickListener(){
                            @Override
                            public void onClick(DialogInterface dialog, int which) {
                                if (which < mFileIndex.size()){
                                    File filePath = mFileList[mFileIndex.get(which)];

                                    Toast.makeText(ShowDataActivity.this,
                                            "Selected File: " + filePath,
                                            Toast.LENGTH_LONG).show();

                                    setSelectedFile(filePath);
                                    mLoadFileTask = new loadFileTask();
                                    mLoadFileTask.execute();
                                }
                            }
                        }
                )
                .show();
    }

    /**
     * Display toast on UI thread.
     *
     * @param resId The resource id of the string resource to use. Can be formatted text.
     */
    private void showsToastAndFinishOnUiThread(final int resId) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(ShowDataActivity.this,
                        getString(resId), Toast.LENGTH_LONG).show();
                finish();
            }
        });
    }

    private void setSelectedFile(File f){
        mSelectedFile = f;
    }

    public class loadFileTask extends AsyncTask<Void, Void, Boolean> {
        @Override
        protected void onPreExecute() {
            mUpdateTrajectory = false;
            mSelectedFileNameTextView.setText("loading: " + mSelectedFile.getAbsolutePath());
        }

        @Override
        protected Boolean doInBackground(Void... params) {
            mSelectedPoseData = new PoseData();
            return mSelectedPoseData.loadFile(mSelectedFile, 1);
        }

        @Override
        protected void onPostExecute(Boolean result) {
            if (result) {
                Log.i(TAG, "Success to load file");
                mSelectedFileNameTextView.setText(mSelectedFile.getAbsolutePath());
                mUpdateTrajectory = true;
            } else {
                Log.i(TAG, "Faile to load file");
                mSelectedFileNameTextView.setText("faile to load: " + mSelectedFile.getAbsolutePath());
            }
        }
    }
}
