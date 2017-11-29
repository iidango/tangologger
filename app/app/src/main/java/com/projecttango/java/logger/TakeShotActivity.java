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
import android.annotation.TargetApi;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.ImageFormat;
import android.graphics.Matrix;
import android.graphics.RectF;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.ImageReader;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.util.Log;
import android.util.Size;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;

import static android.content.ContentValues.TAG;

/**
 * Start Activity for Area Description example. Gives the ability to choose a particular
 * configuration and also manage Area Description Files (ADF).
 */
public class TakeShotActivity extends Activity implements Gear360Connector.Gear360ConnectorListener, ThetaConnector.ThetaConnectorListener, BasicCamera.CameraInterface{

    protected static final String OUTPUT_PATH = Environment.getExternalStorageDirectory() + "/" + "tangoLogger/images" + "/";
    static final int REQUEST_CAPTURE_IMAGE = 100;
    static final int DELAY_TO_SHOT = 3000;  // msec
    static final String GEAR360 = "Gear360";
    static final String THETAS = "THETA S";
    static final String NONE = "None";
    static final String[] SPHERICAL_CAMERA_LIST = {GEAR360, THETAS, NONE};

    // UI elements.
    private LinearLayout mLayoutCameraArea;
    private Button mTakeShotButton;
    private TextView mCameraStatusTextView;
    private Button mImageSizeButton;
    private Button mGoImageListButton;
    private MJpegView mSphericalCameraView;
    private boolean mConnectionSwitchEnabled = false;
    private AutoFitTextureView mDeviceCameraView;
    private Spinner mCameraSelectSpinner;
    private String mSelectedCamera;

    private CameraDevice mBackCameraDevice;
    private CameraCaptureSession mBackCameraSession;

    private boolean mBusyNow;
    private TakeShotTask mTakeShotTask;

    private File mDevicePicFile;
    private int REQUEST_CODE_CAMERA_PERMISSION = 0x01;
    private Size mPreviewSize;
    private ImageReader mImageReader;
    private BackgroundThreadHelper mThread;
    private BasicCamera mDeviceCamera;

    private boolean mWaitingSphericalCameraNow;
    private ThetaConnector mThetaConnector;
    private Gear360Connector mGear360Connector;


    @TargetApi(Build.VERSION_CODES.LOLLIPOP)
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);


        setContentView(R.layout.activity_take_shot);

        getActionBar().setTitle(R.string.app_name);

        mLayoutCameraArea = (LinearLayout) findViewById(R.id.shoot_area);
//        mCameraStatusTextView = (TextView) findViewById(R.id.camera_status);
        mTakeShotButton = (Button) findViewById(R.id.btn_shot);

        mSphericalCameraView = (MJpegView) findViewById(R.id.live_view);
        mDeviceCameraView = (AutoFitTextureView) findViewById(R.id.device_camera_view);

        mBusyNow = false;

        // device camera
        mThread = new BackgroundThreadHelper();
        mDeviceCamera = new BasicCamera();
        mDeviceCamera.setInterface(this);

        // spherical camera
        mSelectedCamera = SPHERICAL_CAMERA_LIST[0];
        mCameraSelectSpinner = (Spinner)findViewById(R.id.select_camera_spinner);
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, SPHERICAL_CAMERA_LIST);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        mCameraSelectSpinner.setAdapter(adapter);
        mCameraSelectSpinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            //　item selected
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                Spinner spinner = (Spinner) parent;
                String item = (String) spinner.getSelectedItem();

                mSelectedCamera = item;
                Log.i(TAG, mSelectedCamera + " is selected");
            }

            // item is not selected
            public void onNothingSelected(AdapterView<?> parent) {
            }
        });
    }

    @Override
    public void onResume() {
        super.onResume();
        mThread.start();

        if (mDeviceCameraView.isAvailable()) {
            // when textureview is prepared
            openDeviceCamera(mDeviceCameraView.getWidth(), mDeviceCameraView.getHeight());
        } else {
            // regist lisnner
            mDeviceCameraView.setSurfaceTextureListener(mSurfaceTextureListener);
        }
    }

    @TargetApi(Build.VERSION_CODES.LOLLIPOP)
    @Override
    protected void onPause() {
        closeDeviceCamera();
        mThread.stop();
        super.onPause();
        // end camera session
        if (mBackCameraSession != null) {
            try {
                mBackCameraSession.stopRepeating();
            } catch (CameraAccessException e) {
                Log.e(TAG, e.toString());
            }
            mBackCameraSession.close();
        }

        if (mBackCameraDevice != null) {
            mBackCameraDevice.close();
        }
    }

    public void takeShotClicked(View v) {
        if (mBusyNow){
            Toast.makeText(TakeShotActivity.this, "Busy now... please wait", Toast.LENGTH_LONG).show();
            return;
        }
        mTakeShotTask = new TakeShotTask();
        mTakeShotTask.execute();
    }

    @TargetApi(Build.VERSION_CODES.LOLLIPOP)
    private String setUpCameraOutputs(int width, int height) {
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            for (String cameraId : manager.getCameraIdList()) {
                CameraCharacteristics characteristics = manager.getCameraCharacteristics(cameraId);

                // skip front camera
                Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
                if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) {
                    continue;
                }
                // stop setup if stream is not supported
                StreamConfigurationMap map = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                if (map == null) {
                    continue;
                }

                // capture with max size
                Size largest = Collections.max(
                        Arrays.asList(map.getOutputSizes(ImageFormat.JPEG)),
                        new CompareSizesByArea());

                setUpPreview(map.getOutputSizes(SurfaceTexture.class),
                        width, height, largest);
                configurePreviewTransform(width, height);

                mImageReader = ImageReader.newInstance(largest.getWidth(), largest.getHeight(),
                        ImageFormat.JPEG, /*maxImages*/2);
                mImageReader.setOnImageAvailableListener(
                        new ImageReader.OnImageAvailableListener() {
                            @Override
                            public void onImageAvailable(ImageReader reader) {
//                                File file = new File(getExternalFilesDir(null), "pic.jpg");
                                mThread.getHandler().post(new ImageStore(reader.acquireNextImage(), mDevicePicFile));

                                Toast.makeText(TakeShotActivity.this, "finish to take picture: " + mDevicePicFile.getName(), Toast.LENGTH_LONG).show();
                                mBusyNow = false;
                            }

                        }, mThread.getHandler());

                return cameraId;
            }
        } catch (CameraAccessException e) {
            e.printStackTrace();
        } catch (NullPointerException e) {
            // Camera2 API is not supported
            Log.e(TAG, "Camera Error:not support Camera2API");
        }

        return null;
    }

    @TargetApi(Build.VERSION_CODES.M)
    private void openDeviceCamera(int width, int height) {
        if (checkSelfPermission(Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            requestCameraPermission();
            return;
        }

        String cameraId = setUpCameraOutputs(width, height);
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            if (!mDeviceCamera.isLocked()) {
                throw new RuntimeException("Time out waiting to lock camera opening.");
            }
            manager.openCamera(cameraId, mDeviceCamera.stateCallback, mThread.getHandler());
        } catch (CameraAccessException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            throw new RuntimeException("Interrupted while trying to lock camera opening.", e);
        }
    }

    private void closeDeviceCamera() {
        mDeviceCamera.close();
        if (null != mImageReader) {
            mImageReader.close();
            mImageReader = null;
        }
    }

    //Texture Listener
    private final TextureView.SurfaceTextureListener mSurfaceTextureListener
            = new TextureView.SurfaceTextureListener() {

        @Override
        public void onSurfaceTextureAvailable(SurfaceTexture texture, int width, int height) {
            // finish to prepare SurfaceTexture
            openDeviceCamera(width, height);
        }

        @Override
        public void onSurfaceTextureSizeChanged(SurfaceTexture texture, int width, int height) {
            // recalcurate preview size
            configurePreviewTransform(width, height);
        }

        @Override
        public boolean onSurfaceTextureDestroyed(SurfaceTexture texture) {
            return true;
        }

        @Override
        public void onSurfaceTextureUpdated(SurfaceTexture texture) {
        }
    };

    @TargetApi(Build.VERSION_CODES.LOLLIPOP)
    private void setUpPreview(Size[] choices, int width, int height, Size aspectRatio) {
        // find preview size which is bigger than surface
        List<Size> bigEnough = new ArrayList<>();
        int w = aspectRatio.getWidth();
        int h = aspectRatio.getHeight();
        for (Size option : choices) {
            if (option.getHeight() == option.getWidth() * h / w &&
                    option.getWidth() >= width && option.getHeight() >= height) {
                bigEnough.add(option);
            }
        }

        // select the smallest size
        if (bigEnough.size() > 0) {
            mPreviewSize = Collections.min(bigEnough, new CompareSizesByArea());
        } else {
            Log.e(TAG, "Couldn't find any suitable preview size");
            mPreviewSize = choices[0];
        }

        // adjust aspect ratio
        int orientation = getResources().getConfiguration().orientation;
        if (orientation == Configuration.ORIENTATION_LANDSCAPE) {
            mDeviceCameraView.setAspectRatio(mPreviewSize.getWidth(), mPreviewSize.getHeight());
        } else {
            mDeviceCameraView.setAspectRatio(mPreviewSize.getHeight(), mPreviewSize.getWidth());
        }
    }

    @TargetApi(Build.VERSION_CODES.LOLLIPOP)
    private void configurePreviewTransform(int viewWidth, int viewHeight) {
        if (null == mDeviceCameraView || null == mPreviewSize) {
            return;
        }
        int rotation = getWindowManager().getDefaultDisplay().getRotation();
        Matrix matrix = new Matrix();
        RectF viewRect = new RectF(0, 0, viewWidth, viewHeight);
        RectF bufferRect = new RectF(0, 0, mPreviewSize.getHeight(), mPreviewSize.getWidth());
        float centerX = viewRect.centerX();
        float centerY = viewRect.centerY();
        if (Surface.ROTATION_90 == rotation || Surface.ROTATION_270 == rotation) {
            bufferRect.offset(centerX - bufferRect.centerX(), centerY - bufferRect.centerY());
            matrix.setRectToRect(viewRect, bufferRect, Matrix.ScaleToFit.FILL);
            float scale = Math.max((float) viewHeight / mPreviewSize.getHeight(), (float) viewWidth / mPreviewSize.getWidth());
            matrix.postScale(scale, scale, centerX, centerY);
            matrix.postRotate(90 * (rotation - 2), centerX, centerY);
        } else if (Surface.ROTATION_180 == rotation) {
            matrix.postRotate(180, centerX, centerY);
        }
        mDeviceCameraView.setTransform(matrix);
    }

    // Parmission handling for Android 6.0
    @TargetApi(Build.VERSION_CODES.M)
    private void requestCameraPermission() {
        if (shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)) {
            // show alert dialog to request permission
            new AlertDialog.Builder(this)
                    .setMessage("Request Permission")
                    .setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {
                            requestPermissions(new String[]{Manifest.permission.CAMERA}, REQUEST_CODE_CAMERA_PERMISSION);
                        }
                    })
                    .setNegativeButton(android.R.string.cancel,
                            new DialogInterface.OnClickListener() {
                                @Override
                                public void onClick(DialogInterface dialog, int which) {
                                    finish();
                                }
                            })
                    .create();
            return;
        }

        // request permission
        requestPermissions(new String[]{Manifest.permission.CAMERA}, REQUEST_CODE_CAMERA_PERMISSION);
        return;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                           String permissions[], int[] grantResults) {
        if (requestCode == REQUEST_CODE_CAMERA_PERMISSION) {
            if (grantResults.length != 1 || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                new AlertDialog.Builder(this)
                        .setMessage("Need Camera Permission")
                        .setPositiveButton(android.R.string.ok, new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface dialogInterface, int i) {
                                finish();
                            }
                        })
                        .create();
            }
            return;
        }

        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    }

    @Override
    public SurfaceTexture getSurfaceTextureFromTextureView() {
        return mDeviceCameraView.getSurfaceTexture();
    }

    @Override
    public Size getPreviewSize() {
        return mPreviewSize;
    }

    @Override
    public Handler getBackgroundHandler() {
        return mThread.getHandler();
    }

    @Override
    public Surface getImageRenderSurface() {
        return mImageReader.getSurface();
    }

    @Override
    public int getRotation() {
        return getWindowManager().getDefaultDisplay().getRotation();
    }

    /**
     * Compares two {@code Size}s based on their areas.
     */
    static class CompareSizesByArea implements Comparator<Size> {

        @TargetApi(Build.VERSION_CODES.LOLLIPOP)
        @Override
        public int compare(Size lhs, Size rhs) {
            // We cast here to ensure the multiplications won't overflow
            return Long.signum((long) lhs.getWidth() * lhs.getHeight() - (long) rhs.getWidth() * rhs.getHeight());
        }
    }

    public class TakeShotTask extends AsyncTask<Void, Void, Void> {

        @Override
        protected void onPreExecute() {
            mBusyNow = true;
        }

        @Override
        protected Void doInBackground(Void... params) {
            // wait
            try {
                Thread.sleep(DELAY_TO_SHOT);
            } catch (InterruptedException e) {
            }

            if (mSelectedCamera != NONE){
                takeSphericalCameraShot();
            }else{
                DateFormat df = new SimpleDateFormat("yyyyMMddHHmmss");
                Date date = new Date(System.currentTimeMillis());
                String currentTime = df.format(date);
                takeDeviceCameraShot(currentTime + ".jpg");
            }

            return null;
        }

        @Override
        protected void onPostExecute(Void result) {
        }
    }

    public boolean takeDeviceCameraShot(String fileName){
        Log.i(TAG, "start to take device shot");
        mDevicePicFile = new File(OUTPUT_PATH, fileName);
        mDeviceCamera.takePicture();
        return true;
    }

    public boolean takeSphericalCameraShot(){
        if (mSelectedCamera == GEAR360){
            Log.i(TAG, "start to take gear 360 shot");
            // TODO take shot from gear 360
            mGear360Connector = new Gear360Connector(getResources().getString(R.string.gear360_ip_address), this);
            mGear360Connector.getTakePictureTask().execute();
            return true;
        }
        else if (mSelectedCamera == THETAS){
            Log.i(TAG, "start to take theta S shot");
            mThetaConnector = new ThetaConnector(getResources().getString(R.string.theta_ip_address), this);
            mThetaConnector.getTakePictureTask().execute();
            return true;
        }
        return false;
    }

    @Override
    public void onStartRecordingFailed(String result){
    }
    @Override
    public void onStartRecordingSuccess(String result){
    }
    @Override
    public void onStopRecordingFailed(String result){
    }
    @Override
    public void onStopRecordingSuccess(String result){
    }
    @Override
    public void onTCSuccess(String result){
    }
    @Override
    public void onTCFailed(String result){
    }
    @Override
    public void onTPSuccess(String result) {
        Log.i(TAG, result);
        takeDeviceCameraShot(result);
    }
    @Override
    public void onTPFailed(String result) {
        Log.i(TAG, result);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
    }
}
