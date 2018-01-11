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

import android.Manifest;
import android.app.Activity;
import android.app.FragmentManager;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.hardware.display.DisplayManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.location.LocationProvider;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.provider.Settings;
import android.support.v4.app.ActivityCompat;
import android.util.Log;
import android.view.Display;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.google.atap.tangoservice.Tango;
import com.google.atap.tangoservice.TangoAreaDescriptionMetaData;
import com.google.atap.tangoservice.TangoConfig;
import com.google.atap.tangoservice.TangoCoordinateFramePair;
import com.google.atap.tangoservice.TangoErrorException;
import com.google.atap.tangoservice.TangoEvent;
import com.google.atap.tangoservice.TangoInvalidException;
import com.google.atap.tangoservice.TangoOutOfDateException;
import com.google.atap.tangoservice.TangoPointCloudData;
import com.google.atap.tangoservice.TangoPoseData;
import com.google.atap.tangoservice.TangoXyzIjData;
import com.projecttango.tangosupport.TangoSupport;
import com.projecttango.tangosupport.ux.TangoUx;
import com.projecttango.tangosupport.ux.UxExceptionEvent;
import com.projecttango.tangosupport.ux.UxExceptionEventListener;

import org.rajawali3d.scene.ASceneFrameCallback;
import org.rajawali3d.surface.RajawaliSurfaceView;

import java.nio.FloatBuffer;
import java.text.DateFormat;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import static android.os.SystemClock.elapsedRealtimeNanos;

/**
 * Main Activity class for the Point Cloud Sample. Handles the connection to the {@link Tango}
 * service and propagation of Tango point cloud data to OpenGL and Layout views. OpenGL rendering
 * logic is delegated to the {@link PositionViewRajawaliRenderer} class.
 */
public class PositionViewActivity extends Activity implements
        SetFileNameDialog.CallbackListener,
        SaveFileTask.SaveFileListener,
        ThetaConnector.ThetaConnectorListener,
        SensorEventListener,
        LocationListener {
    private static final String TAG = PositionViewActivity.class.getSimpleName();

    private static final String UX_EXCEPTION_EVENT_DETECTED = "Exception Detected: ";
    private static final String UX_EXCEPTION_EVENT_RESOLVED = "Exception Resolved: ";

    private static final int SECS_TO_MILLISECS = 1000;
    private static final DecimalFormat FORMAT_THREE_DECIMAL = new DecimalFormat("0.000");
    private static final double UPDATE_INTERVAL_MS = 100.0;

    private Tango mTango;
    private TangoConfig mConfig;
    private TangoUx mTangoUx;

    private PositionViewRajawaliRenderer mRenderer;
    private RajawaliSurfaceView mSurfaceView;

    private boolean mIsConnected = false;

    private int mDisplayRotation = 0;

    private boolean mIsLearningMode;
    private boolean mIsConstantSpaceRelocalize;

    private Button mSaveFileButton;
    private TextView mLogTextView;

    // Long-running task to save File.
    private SaveFileTask mSaveFileTask;
    private SensorData mTrajectoryData; // timestamp only
    private boolean mLoggingOn;

    // sensor data
    private SensorManager mSensorManager;
    private Sensor mAccelometerSensor;
    private SensorData mAccelometerSensorData;
    private Sensor mGyroscopeSensor;
    private SensorData mGyroscopeSensorData;
    private Sensor mMagneticSensor;
    private SensorData mMagneticSensorData;
    private Sensor mPressureSensor; // not included in phab2 pro
    private SensorData mPressureSensorData; // not included in phab2 pro

    // theta
    private Button mMovieRecordingButton;
    private ThetaConnector mThetaConnector;
    private boolean mRecordMovieIm;
    private String mCameraIpAddress;
    private boolean mConnectionSwitchEnabled = false;

    // gps
    private boolean mGPSOn;
    private final int REQUEST_PERMISSION = 1000;
    private static final int UPDATE_GPS_INTERVAL = 0; // msec
    private static final float UPDATE_GPS_DIST = 0; // m
    private LocationManager mLocationManager;
    private GPSData mGPSData;

    // wifi
    private boolean mWiFiOn;
    private WiFiData mWiFiData;
    private WifiManager mWiFiManager;
    private Thread mWiFiLogThread;
    private static final int UPDATE_WIFI_INTERVAL = 1000; // msec
    private static final int MAX_WIFILOG_NUM = 0; // 0 for all
    private Timer mWiFiTimer;
    private TimerTask mWiFiTimerTask;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_position_view);

        Intent intent = getIntent();
        mIsLearningMode = intent.getBooleanExtra(StartActivity.USE_AREA_LEARNING, false);   //  not used
        mRecordMovieIm = intent.getBooleanExtra(StartActivity.RECORD_MOVIE_IM_ON, false);
        mGPSOn = intent.getBooleanExtra(StartActivity.GPS_ON, false);
        mWiFiOn = intent.getBooleanExtra(StartActivity.WiFi_ON, false);
        mIsConstantSpaceRelocalize = false; // foad adf file

        mSurfaceView = (RajawaliSurfaceView) findViewById(R.id.gl_surface_view);
        mSaveFileButton = (Button) findViewById(R.id.save_file_button);
        mLogTextView = (TextView) findViewById(R.id.log_text_view);
        mMovieRecordingButton = (Button) findViewById(R.id.movie_recording_button);
        mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_off));

        mTangoUx = setupTangoUxAndLayout();
        mRenderer = new PositionViewRajawaliRenderer(this);
        setupRenderer();

        mLoggingOn = true;
        mTrajectoryData = new SensorData();

        mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        mAccelometerSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        mAccelometerSensorData = new SensorData(Sensor.STRING_TYPE_ACCELEROMETER);
        mGyroscopeSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        mGyroscopeSensorData = new SensorData(Sensor.STRING_TYPE_GYROSCOPE);
        mMagneticSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        mMagneticSensorData = new SensorData(Sensor.STRING_TYPE_MAGNETIC_FIELD);
        mPressureSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_PRESSURE);
        mPressureSensorData = new SensorData(Sensor.STRING_TYPE_PRESSURE);

        if(mGPSOn){
            mLocationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
            mGPSData = new GPSData();
            startGPS();
        }
        if(mWiFiOn){
            mWiFiManager = (WifiManager) getSystemService(WIFI_SERVICE);
            mWiFiData = new WiFiData();
            startWiFi();
        }

        DisplayManager displayManager = (DisplayManager) getSystemService(DISPLAY_SERVICE);
        if (displayManager != null) {
            displayManager.registerDisplayListener(new DisplayManager.DisplayListener() {
                @Override
                public void onDisplayAdded(int displayId) {
                }

                @Override
                public void onDisplayChanged(int displayId) {
                    synchronized (this) {
                        setDisplayRotation();
                    }
                }

                @Override
                public void onDisplayRemoved(int displayId) {
                }
            }, null);
        }

    }

    @Override
    protected void onResume() {
        super.onResume();

        mSensorManager.registerListener(this, mAccelometerSensor, SensorManager.SENSOR_DELAY_FASTEST);
        mSensorManager.registerListener(this, mGyroscopeSensor, SensorManager.SENSOR_DELAY_FASTEST);
        mSensorManager.registerListener(this, mMagneticSensor, SensorManager.SENSOR_DELAY_FASTEST);
        mSensorManager.registerListener(this, mPressureSensor, SensorManager.SENSOR_DELAY_FASTEST);
        mTangoUx.start();

        // Initialize Tango Service as a normal Android Service. Since we call mTango.disconnect()
        // in onPause, this will unbind Tango Service, so every time onResume gets called we
        // should create a new Tango object.
        mTango = new Tango(PositionViewActivity.this, new Runnable() {
            // Pass in a Runnable to be called from UI thread when Tango is ready; this Runnable
            // will be running on a new thread.
            // When Tango is ready, we can call Tango functions safely here only when there are no
            // UI thread changes involved.
            @Override
            public void run() {
                synchronized (PositionViewActivity.this) {
                    try {
                        TangoSupport.initialize();
                        mConfig = setTangoConfig(
                                mTango, mIsLearningMode, mIsConstantSpaceRelocalize);
                        mTango.connect(mConfig);
                        startupTango();
                        mIsConnected = true;
                    } catch (TangoOutOfDateException e) {
                        Log.e(TAG, getString(R.string.tango_out_of_date_exception), e);
                        showsToastAndFinishOnUiThread(R.string.tango_out_of_date_exception);
                    } catch (TangoErrorException e) {
                        Log.e(TAG, getString(R.string.tango_error), e);
                        showsToastAndFinishOnUiThread(R.string.tango_error);
                    } catch (TangoInvalidException e) {
                        Log.e(TAG, getString(R.string.tango_invalid), e);
                        showsToastAndFinishOnUiThread(R.string.tango_invalid);
                    } catch (SecurityException e) {
                        // Area Learning permissions are required. If they are not available,
                        // SecurityException is thrown.
                        Log.e(TAG, getString(R.string.no_permissions), e);
                        showsToastAndFinishOnUiThread(R.string.no_permissions);
                    }
                }

                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        synchronized (PositionViewActivity.this) {
                            setupTextViewsAndButtons(mTango, mIsLearningMode,
                                    mIsConstantSpaceRelocalize);
                        }
                    }
                });
            }
        });

        mLoggingOn = true;
        if (mRecordMovieIm && mThetaConnector == null) {
            mThetaConnector = new ThetaConnector(getResources().getString(R.string.theta_ip_address), this);
            mThetaConnector.getStartMovieRecordingTask().execute();
//            mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_connect));
        }
    }

    /**
     * Sets Texts views to display statistics of Poses being received. This also sets the buttons
     * used in the UI. Note that this needs to be called after TangoService and Config
     * objects are initialized since we use them for the SDK-related stuff like version number,
     * etc.
     */
    private void setupTextViewsAndButtons(Tango tango, boolean isLearningMode, boolean isLoadAdf) {
    }

    /**
     * Sets up the Tango configuration object. Make sure mTango object is initialized before
     * making this call.
     */
    private TangoConfig setTangoConfig(Tango tango, boolean isLearningMode, boolean isLoadAdf) {
        // Use default configuration for Tango Service.
        TangoConfig config = tango.getConfig(TangoConfig.CONFIG_TYPE_DEFAULT);
        // Check if learning mode.
        if (isLearningMode) {
            // Set learning mode to config.
//            config.putBoolean(TangoConfig.KEY_BOOLEAN_LEARNINGMODE, true);
            // Set enable drift correction to config.
            config.putBoolean(TangoConfig.KEY_BOOLEAN_DRIFT_CORRECTION, true);

        }
        // Check for Load ADF/Constant Space relocalization mode.
        if (isLoadAdf) {
            ArrayList<String> fullUuidList;
            // Returns a list of ADFs with their UUIDs.
            fullUuidList = tango.listAreaDescriptions();
            // Load the latest ADF if ADFs are found.
            if (fullUuidList.size() > 0) {
                config.putString(TangoConfig.KEY_STRING_AREADESCRIPTION,
                        fullUuidList.get(fullUuidList.size() - 1));
            }
        }
        return config;
    }

    @Override
    protected void onPause() {
        super.onPause();
        mSensorManager.unregisterListener(this);

        // Clear the relocalization state; we don't know where the device will be since our app
        // will be paused.
        synchronized (this) {
            try {
                mTangoUx.stop();
                mTango.disconnect();
                mIsConnected = false;
            } catch (TangoErrorException e) {
                Log.e(TAG, getString(R.string.tango_error), e);
            }
        }

        mLoggingOn = false;
        mRecordMovieIm = false;
        mGPSOn = false;
        stopGPS();
    }

    /**
     * Set up the callback listeners for the Tango Service and obtain other parameters required
     * after Tango connection.
     * Listen to updates from the Point Cloud and Tango Events and Pose.
     */
    private void startupTango() {
        ArrayList<TangoCoordinateFramePair> framePairs = new ArrayList<TangoCoordinateFramePair>();

        framePairs.add(new TangoCoordinateFramePair(TangoPoseData.COORDINATE_FRAME_START_OF_SERVICE,
                TangoPoseData.COORDINATE_FRAME_DEVICE));

        mTango.connectListener(framePairs, new Tango.TangoUpdateCallback() {
            @Override
            public void onPoseAvailable(TangoPoseData pose) {
                // logging pos data
//                logPose(pose);

                if (mLoggingOn) {
                    mTrajectoryData.addTimestamp(pose.timestamp);
                }

                // Passing in the pose data to UX library produce exceptions.
                if (mTangoUx != null) {
                    mTangoUx.updatePoseStatus(pose.statusCode);
                }
            }

            @Override
            public void onPointCloudAvailable(TangoPointCloudData pointCloud) {
            }

            @Override
            public void onTangoEvent(TangoEvent event) {
//                Log.i(TAG, "onTangoEvent");
                if (mTangoUx != null) {
                    mTangoUx.updateTangoEvent(event);
                }
            }

            @Override
            public void onFrameAvailable(int cameraId) {
                Log.i(TAG, "onFrameAvailable");
                // Check if the frame available is for the camera we want and update its frame
                // on the view.
//                if (cameraId == TangoCameraIntrinsics.TANGO_CAMERA_COLOR) {
                // Mark a camera frame as available for rendering in the OpenGL thread.
//                    mIsFrameAvailableTangoThread.set(true);
//                    mSurfaceView.requestRender();
//                }

            }

            @Override
            public void onXyzIjAvailable(TangoXyzIjData xyzIj) {
                // We are not using onXyzIjAvailable for this app.
                Log.i(TAG, "onXyzIjAvailable");
            }
        });
    }

    /**
     * Log the Position and Orientation of the given pose in the Logcat as information.
     *
     * @param pose the pose to log.
     */
    private void logPose(TangoPoseData pose) {
        StringBuilder stringBuilder = new StringBuilder();

        if (pose.baseFrame == TangoPoseData.COORDINATE_FRAME_AREA_DESCRIPTION && pose.targetFrame == TangoPoseData.COORDINATE_FRAME_DEVICE) {
            Log.i(TAG, "FRAME_AREA_DESCRIPTION POSITON!!!!!!!!!!!!!!!!!!!!");
        }

        stringBuilder.append("base frame: " +
                pose.baseFrame + ", target frame: " + pose.targetFrame);


        float translation[] = pose.getTranslationAsFloats();
        stringBuilder.append("Position: " +
                translation[0] + ", " + translation[1] + ", " + translation[2]);

        float orientation[] = pose.getRotationAsFloats();
        stringBuilder.append(". Orientation: " +
                orientation[0] + ", " + orientation[1] + ", " +
                orientation[2] + ", " + orientation[3]);

//        Log.i(TAG, stringBuilder.toString());
        showLog(stringBuilder.toString());
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

                // Prevent concurrent access from a service disconnect through the onPause event.
                synchronized (PositionViewActivity.this) {
                    // Don't execute any Tango API actions if we're not connected to the service.
                    if (!mIsConnected) {
                        return;
                    }
                    // Update current camera pose.
                    try {
                        // Calculate the device pose. This transform is used to display
                        // frustum in third and top down view, and used to render camera pose in
                        // first person view.

                        // TODO change base frame depends on their option
                        TangoPoseData lastFramePose = TangoSupport.getPoseAtTime(0,
                                TangoPoseData.COORDINATE_FRAME_AREA_DESCRIPTION, // TangoPoseData.COORDINATE_FRAME_START_OF_SERVICE,
                                TangoPoseData.COORDINATE_FRAME_DEVICE,
                                TangoSupport.TANGO_SUPPORT_ENGINE_OPENGL,
                                TangoSupport.TANGO_SUPPORT_ENGINE_OPENGL,
                                mDisplayRotation);
                        if (lastFramePose.statusCode == TangoPoseData.POSE_VALID) {
                            mRenderer.updateCameraPose(lastFramePose);
                            mRenderer.updateTrajectory(lastFramePose);
                        }
                    } catch (TangoErrorException e) {
                        Log.e(TAG, "Could not get valid transform");
                    }
                }
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

    /**
     * Sets up TangoUX and sets its listener.
     */
    private TangoUx setupTangoUxAndLayout() {
        TangoUx tangoUx = new TangoUx(this);
        tangoUx.setUxExceptionEventListener(mUxExceptionListener);
        return tangoUx;
    }

    /*
    * Set a UxExceptionEventListener to be notified of any UX exceptions.
    * In this example we are just logging all the exceptions to logcat, but in a real app,
    * developers should use these exceptions to contextually notify the user and help direct the
    * user in using the device in a way Tango Service expects it.
    * <p>
    * A UxExceptionEvent can have two statuses: DETECTED and RESOLVED.
    * An event is considered DETECTED when the exception conditions are observed, and RESOLVED when
    * the root causes have been addressed.
    * Both statuses will trigger a separate event.
    */
    private UxExceptionEventListener mUxExceptionListener = new UxExceptionEventListener() {
        @Override
        public void onUxExceptionEvent(UxExceptionEvent uxExceptionEvent) {
            String status = uxExceptionEvent.getStatus() == UxExceptionEvent.STATUS_DETECTED ?
                    UX_EXCEPTION_EVENT_DETECTED : UX_EXCEPTION_EVENT_RESOLVED;

            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_LYING_ON_SURFACE) {
                Log.i(TAG, status + "Device lying on surface");
            }
            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_FEW_DEPTH_POINTS) {
                Log.i(TAG, status + "Too few depth points");
            }
            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_FEW_FEATURES) {
                Log.i(TAG, status + "Too few features");
            }
            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_MOTION_TRACK_INVALID) {
                Log.i(TAG, status + "Invalid poses in MotionTracking");
            }
            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_MOVING_TOO_FAST) {
                Log.i(TAG, status + "Moving too fast");
            }
            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_FISHEYE_CAMERA_OVER_EXPOSED) {
                Log.i(TAG, status + "Fisheye Camera Over Exposed");
            }
            if (uxExceptionEvent.getType() == UxExceptionEvent.TYPE_FISHEYE_CAMERA_UNDER_EXPOSED) {
                Log.i(TAG, status + "Fisheye Camera Under Exposed");
            }
        }
    };

    /**
     * First Person button onClick callback.
     */
    public void onFirstPersonClicked(View v) {
        mRenderer.setFirstPersonView();
    }

    /**
     * Third Person button onClick callback.
     */
    public void onThirdPersonClicked(View v) {
        mRenderer.setThirdPersonView();
    }

    /**
     * Top-down button onClick callback.
     */
    public void onTopDownClicked(View v) {
        mRenderer.setTopDownView();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        mRenderer.onTouchEvent(event);
        return true;
    }

    /**
     * Implements SetFileNameDialog.CallbackListener.
     */
    @Override
    public void onFileNameOk(String name, String uuid) {
        saveFile(name);
    }

    /**
     * Implements SetFileNameDialog.CallbackListener.
     */
    @Override
    public void onFileNameCancelled() {
        // Continue running.
    }

    /**
     * The "Save File" button has been clicked.
     * Defined in {@code activity_position_view.xml}
     */
    public void saveFileClicked(View view) {
        if (mGPSOn) {
            stopGPS();
            mGPSOn = false;
        }
        if (mWiFiOn) {
            stopWiFi();
            mWiFiOn = false;
        }
        if (mThetaConnector != null && mThetaConnector.getCurrentStatus() == ThetaConnector.TStatus.RECORDING) {    // stop recording
            mThetaConnector.getStopMovieRecordingTask().execute();
            mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_connect));
        }
        showSetFileNameDialog();
    }

    /**
     * Save the current Area Description File.
     * Performs saving on a background thread and displays a progress dialog.
     */
    private void saveFile(String fileName) {

//        SensorData[] sensorDatas;
        ArrayList<SensorData> sensorDatas = new ArrayList<>();

        sensorDatas.add(mAccelometerSensorData);
        sensorDatas.add(mGyroscopeSensorData);
        sensorDatas.add(mMagneticSensorData);
        sensorDatas.add(mPressureSensorData);

        if (mGPSData != null){
            sensorDatas.add(mGPSData);
        }
        if (mWiFiData != null){
            sensorDatas.add(mWiFiData);
        }

        mSaveFileTask = new SaveFileTask(
                this, this, mTango, fileName, mDisplayRotation, mTrajectoryData, sensorDatas
        );
        mLoggingOn = false;
        mSaveFileTask.execute();
    }

    /**
     * Handles failed save from mSaveFileTask.
     */
    @Override
    public void onSaveFileFailed(String fileName) {
        String toastMessage = String.format(
                getResources().getString(R.string.save_file_failed_toast_format),
                fileName);
        Toast.makeText(this, toastMessage, Toast.LENGTH_LONG).show();
        mSaveFileTask = null;
    }

    /**
     * Handles successful save from mSaveFileTask.
     */
    @Override
    public void onSaveFileSuccess(String adfName) {
        String toastMessage = String.format(
                getResources().getString(R.string.save_file_success_toast_format),
                adfName);
        Toast.makeText(this, toastMessage, Toast.LENGTH_LONG).show();
        mSaveFileTask = null;
        finish();
    }

    /**
     * Shows a dialog for setting the File name.
     */
    private void showSetFileNameDialog() {
        // get current time
        DateFormat df = new SimpleDateFormat("yyyyMMddHHmm");
        Date date = new Date(System.currentTimeMillis());
        String currentTime = df.format(date);

        Bundle bundle = new Bundle();
        bundle.putString(TangoAreaDescriptionMetaData.KEY_NAME, currentTime);
        // UUID is generated after the ADF is saved.
        bundle.putString(TangoAreaDescriptionMetaData.KEY_UUID, "");

        FragmentManager manager = getFragmentManager();
        SetFileNameDialog setFileNameDialog = new SetFileNameDialog();
        setFileNameDialog.setArguments(bundle);
        setFileNameDialog.show(manager, "FileNameDialog");
    }

    /**
     * Calculates the average depth from a point cloud buffer.
     *
     * @param pointCloudBuffer
     * @param numPoints
     * @return Average depth.
     */
    private float getAveragedDepth(FloatBuffer pointCloudBuffer, int numPoints) {
        float totalZ = 0;
        float averageZ = 0;
        if (numPoints != 0) {
            int numFloats = 4 * numPoints;
            for (int i = 2; i < numFloats; i = i + 4) {
                totalZ = totalZ + pointCloudBuffer.get(i);
            }
            averageZ = totalZ / numPoints;
        }
        return averageZ;
    }

    /**
     * Query the display's rotation.
     */
    private void setDisplayRotation() {
        Display display = getWindowManager().getDefaultDisplay();
        mDisplayRotation = display.getRotation();
        Log.i(TAG, String.valueOf(mDisplayRotation));
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (!mLoggingOn) {
            return;
        }
        Sensor sensor = event.sensor;
        float[] values = event.values;
        long timestamp = event.timestamp;

        if (sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            mAccelometerSensorData.addData(timestamp, values[0], values[1], values[2]);
        }
        if (sensor.getType() == Sensor.TYPE_GYROSCOPE) {
            mGyroscopeSensorData.addData(timestamp, values[0], values[1], values[2]);
        }
        if (sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
            mMagneticSensorData.addData(timestamp, values[0], values[1], values[2]);
        }
        if (sensor.getType() == Sensor.TYPE_PRESSURE) {
            mPressureSensorData.addData(timestamp, values[0], values[1], values[2]);
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

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
                Toast.makeText(PositionViewActivity.this,
                        getString(resId), Toast.LENGTH_LONG).show();
                finish();
            }
        });
    }

    private void showLog(String txt) {
        mLogTextView.setText(txt);
    }


    /**
     * Top-down button onClick callback.
     */
    public void onMovieRecordingClicked(View v) {
        if (mThetaConnector == null) {
            mThetaConnector = new ThetaConnector(getResources().getString(R.string.theta_ip_address), this);
        }

        if (mThetaConnector.getCurrentStatus() == ThetaConnector.TStatus.READY) { // start recording
            mThetaConnector.getStartMovieRecordingTask().execute();
            mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_connect));
        } else if (mThetaConnector.getCurrentStatus() == ThetaConnector.TStatus.RECORDING) {    // stop recording
            mThetaConnector.getStopMovieRecordingTask().execute();
            mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_connect));
        }
    }



    @Override
    public void onStartRecordingFailed(String result) {
        showLog(result);
        mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_off));
    }
    @Override
    public void onStartRecordingSuccess(String result) {
        showLog(result);
        mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_on));
    }
    @Override
    public void onStopRecordingFailed(String result) {
        showLog(result);
        mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_on));
    }
    @Override
    public void onStopRecordingSuccess(String result) {
        showLog(result);
        mMovieRecordingButton.setText(getResources().getString(R.string.movie_recording_off));
        mThetaConnector = null;
    }
    @Override
    public void onTCSuccess(String result) {
    }
    @Override
    public void onTCFailed(String result) {
    }
    @Override
    public void onTPSuccess(String result) {

    }
    @Override
    public void onTPFailed(String result) {

    }


    private void enableLocationSettings() {
        Intent settingsIntent = new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS);
        startActivity(settingsIntent);
    }

    protected void startGPS() {
        final boolean gpsEnabled = mLocationManager.isProviderEnabled(LocationManager.GPS_PROVIDER);
        if (!gpsEnabled) {
            enableLocationSettings();
        }

        if (mLocationManager != null) {
            try {
                if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                    return;
                }
                mLocationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, UPDATE_GPS_INTERVAL, UPDATE_GPS_DIST, this);
//                showLog("Location Loging Run!!");
//                Log.i(TAG, "location Loging Run!!");
            } catch (Exception e) {
                e.printStackTrace();

                Toast toast = Toast.makeText(this, "Please check location permission", Toast.LENGTH_SHORT);
                toast.show();
                // return to MainActivity
                finish();
            }
        } else {
        }
//        onResume();
    }

    private void stopGPS() {
        if (mLocationManager != null) {
            Log.d("LocationActivity", "onStop()");
            // stop updating
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                return;
            }
            mLocationManager.removeUpdates(this);
        }
    }

    @Override
    public void onLocationChanged(Location location) {
        showLog(String.valueOf(location.getLongitude()) + "," + String.valueOf(location.getLatitude()));
        if (mLoggingOn){
//        mGPSData.addTimestamp((double) (new Date()).getTime() / 1000);
            mGPSData.addTimestamp(elapsedRealtimeNanos());
            mGPSData.addX(location.getLongitude());
            mGPSData.addY(location.getLatitude());
            mGPSData.addZ(location.getAltitude());
            mGPSData.addAccuracy(location.getAccuracy());
            mGPSData.addBearing(location.getBearing());
            mGPSData.addSpeed(location.getSpeed());
            mGPSData.addTime(location.getTime());
            mGPSData.addProvider(location.getProvider());

        }
    }

    public void startWiFi(){
        final Handler handler = new Handler();

        // set wifi logging task
        mWiFiTimerTask = new TimerTask(){
            @Override
            public void run() {
                if (mWiFiManager.getWifiState() == WifiManager.WIFI_STATE_ENABLED) {
                    mWiFiManager.startScan();

                    // get ap lists
                    List<ScanResult> apList = mWiFiManager.getScanResults();
                    double timestamp = elapsedRealtimeNanos();

                    // sort ap list by level(rssi)
                    Comparator<ScanResult> myComparator = new Comparator<ScanResult>(){
                        public int compare(ScanResult s1, ScanResult s2) {
                            return s2.level - s1.level;
                        }
                    };
                    Collections.sort(apList, myComparator);

                    // append data
                    int cnt = 0;
                    for (ScanResult ap: apList) {
                        mWiFiData.addTimestamp(timestamp);
                        mWiFiData.addBSSID(ap.BSSID);
                        mWiFiData.addSSID(ap.SSID);
                        mWiFiData.addLevel(ap.level);
                        mWiFiData.addTime(ap.timestamp);

                        cnt++;
                        if (MAX_WIFILOG_NUM != 0 && cnt >= MAX_WIFILOG_NUM){
                            break;
                        }
                    }

                    // access main view
                    handler.post(new Runnable() {
                        @Override
                        public void run() {
//                            Toast.makeText(PositionViewActivity.this, "wifiChanged", Toast.LENGTH_SHORT).show();
//                            Toast.makeText(PositionViewActivity.this, String.valueOf(mWiFiData.size()), Toast.LENGTH_SHORT).show();
                        }
                    });
                }
            }
        };

        mWiFiLogThread = new Thread(new Runnable() {
            @Override
            public void run() {
                mWiFiTimer = new Timer(true);
                mWiFiTimer.schedule(mWiFiTimerTask, 0, UPDATE_WIFI_INTERVAL);
            }
        });
        mWiFiLogThread.start();
    }

    public void stopWiFi(){
        mWiFiTimer.cancel();
    }

    @Override
    public void onProviderDisabled(String provider) {

    }

    @Override
    public void onProviderEnabled(String provider) {

    }

    @Override
    public void onStatusChanged(String provider, int status, Bundle extras) {
        switch (status) {
            case LocationProvider.AVAILABLE:
                Log.i(TAG, "LocationProvider.AVAILABLE");
                break;
            case LocationProvider.OUT_OF_SERVICE:
                Log.i(TAG, "LocationProvider.OUT_OF_SERVICE");
                break;
            case LocationProvider.TEMPORARILY_UNAVAILABLE:
                Log.i(TAG, "LocationProvider.TEMPORARILY_UNAVAILABLE");
                break;
        }
    }
}
