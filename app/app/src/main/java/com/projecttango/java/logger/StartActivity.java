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
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.support.v4.app.ActivityCompat;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;
import android.widget.ToggleButton;

import com.google.atap.tangoservice.Tango;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Start Activity for Area Description example. Gives the ability to choose a particular
 * configuration and also manage Area Description Files (ADF).
 */
public class StartActivity extends Activity implements ThetaConnector.ThetaConnectorListener{
    private final int REQUEST_PERMISSION = 1000;
    // The unique key string for storing the user's input.
    public static final String USE_AREA_LEARNING =
            "com.projecttango.java.logger.usearealearning";
    public static final String GPS_ON =
            "com.projecttango.java.logger.usegps";
    public static final String WiFi_ON =
            "com.projecttango.java.logger.usewifi";
    public static final String RECORD_MOVIE_IM_ON =
            "com.projecttango.java.logger.recordmovieim";

    // Permission request action.
    public static final int REQUEST_CODE_TANGO_PERMISSION = 0;

    // UI elements.
    private ToggleButton mLearningModeToggleButton;
    private ToggleButton mUseGPSButton;
    private ToggleButton mUseWiFiButton;
    private ToggleButton mRecordMovieImButton;
    private Button mTimeSymchronizationButton;

    private boolean mIsUseAreaLearning;
    private boolean mGPSOn;
    private boolean mWiFiOn;
    private boolean mRecordMovieImOn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_start);
        setTitle(R.string.app_name);

        // Set up UI elements.
        mLearningModeToggleButton = (ToggleButton) findViewById(R.id.learning_mode);
        mUseGPSButton = (ToggleButton) findViewById(R.id.use_gps);
        mUseWiFiButton = (ToggleButton) findViewById(R.id.use_wifi);
        mRecordMovieImButton = (ToggleButton) findViewById(R.id.record_movie_im);
        mTimeSymchronizationButton = (Button) findViewById(R.id.time_synchronization);

        mIsUseAreaLearning = mLearningModeToggleButton.isChecked();
        mGPSOn = mUseGPSButton.isChecked();
        mWiFiOn = mUseWiFiButton.isChecked();
        mRecordMovieImOn = mRecordMovieImButton.isChecked();

        // request external strage access
        // nesessary for over Android 6, API 23
        if (Build.VERSION.SDK_INT >= 23) {
            checkPermission();
        }

        startActivityForResult(
                Tango.getRequestPermissionIntent(Tango.PERMISSIONTYPE_ADF_LOAD_SAVE), 0);

    }

    // confirm permission
    public void checkPermission() {
        if (ActivityCompat.checkSelfPermission(this,
                Manifest.permission.WRITE_EXTERNAL_STORAGE)== PackageManager.PERMISSION_GRANTED){
        }
        // dinyed
        else{
            requestStoragePermission();
        }
    }

    // request Permission
    private void requestStoragePermission() {
        if (ActivityCompat.shouldShowRequestPermissionRationale(this,
                Manifest.permission.WRITE_EXTERNAL_STORAGE)) {
            ActivityCompat.requestPermissions(StartActivity.this,
                    new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQUEST_PERMISSION);

        } else {
            Toast toast = Toast.makeText(this, "External Strage access is nessesary for saving file", Toast.LENGTH_SHORT);
            toast.show();

            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE,}, REQUEST_PERMISSION);

        }
    }

    /**
     * The "use gps" button has been clicked.
     * Defined in {@code activity_start.xml}
     * */
    public void useGPSClicked(View v) {
        mGPSOn = mUseGPSButton.isChecked();

        // confirm permisstion
        if (mGPSOn) {
            // GPS Premission
            // Necessary for Android 6, API 23 or more
            if (Build.VERSION.SDK_INT >= 23) {
                checkGpsPermission();
            } else {
            }
        }
    }
    /**
     * The "use wifi" button has been clicked.
     * Defined in {@code activity_start.xml}
     * */
    public void useWiFiClicked(View v) {
        mWiFiOn = mUseWiFiButton.isChecked();

        // confirm permisstion
        if (mWiFiOn) {
            WifiManager wifiManager = (WifiManager) getSystemService(WIFI_SERVICE);

            int wifiState = wifiManager.getWifiState();
            if (wifiState != WifiManager.WIFI_STATE_ENABLED){
                Toast.makeText(StartActivity.this, "please turn on wifi", Toast.LENGTH_SHORT).show();
                mUseWiFiButton.setChecked(false);
                mWiFiOn = false;
            }
        }
    }

    // check location permission
    public void checkGpsPermission() {
        // alreacy available
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
        }
        // denied
        else {
            requestLocationPermission();
        }
    }

    private void requestLocationPermission() {
        if (ActivityCompat.shouldShowRequestPermissionRationale(this,
                Manifest.permission.ACCESS_FINE_LOCATION)) {
            ActivityCompat.requestPermissions(StartActivity.this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, REQUEST_PERMISSION);

        } else {
            Toast toast = Toast.makeText(this, "Please Give Location Permission", Toast.LENGTH_SHORT);
            toast.show();

            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACCESS_FINE_LOCATION,}, REQUEST_PERMISSION);

        }
    }

    /**
     * The "record movie immediately" button has been clicked.
     * Defined in {@code activity_start.xml}
     * */
    public void recordMovieImClicked(View v) {
        mRecordMovieImOn = mRecordMovieImButton.isChecked();
    }

    /**
     * The "Learning Mode" button has been clicked.
     * Defined in {@code activity_start.xml}
     * */
    public void learningModeClicked(View v) {
        mIsUseAreaLearning = mLearningModeToggleButton.isChecked();
    }

    /**
     * The "Start" button has been clicked.
     * Defined in {@code activity_start.xml}
     * */
    public void startClicked(View v) {
        startPositionViewActivity();
    }

    /**
     * The "Show Data" button has been clicked.
     * Defined in {@code activity_show_data.xml}
     * */
    public void showDataClicked(View v) {
        showDataViewActivity();
    }

    /**
     * The "Calibration" button has been clicked.
     * Defined in {@code activity_take_shot.xml}
     * */
    public void CalibrationClicked(View v) {
        showTakeShotActivity();
    }

    /**
     * set client version 2 for THETA S
     * Defined in {@code activity_start.xml}
     * */
    public void setOscv2Clicked(View v) {
        doSetOscv2();
    }
    /**
     * The "time synchronization" button has been clicked.
     * Defined in {@code activity_start.xml}
     * */
    public void timeSynchronizationClicked(View v) {
        doTimeSynchronization();
    }

    /**
     * Start position view activity and pass in the user's configuration.
     */
    private void startPositionViewActivity() {
        Intent startAdIntent = new Intent(this, PositionViewActivity.class);
        startAdIntent.putExtra(USE_AREA_LEARNING, mIsUseAreaLearning);
        startAdIntent.putExtra(GPS_ON, mGPSOn);
        startAdIntent.putExtra(WiFi_ON, mWiFiOn);
        startAdIntent.putExtra(RECORD_MOVIE_IM_ON, mRecordMovieImOn);
        startActivity(startAdIntent);
    }

    /**
     * Show data view activity and pass in the user's configuration.
     */
    private void showDataViewActivity() {
        Intent startAdIntent = new Intent(this, ShowDataActivity.class);
        startActivity(startAdIntent);
    }

    /**
     * take picture activity and pass in the user's configuration.
     */
    private void showTakeShotActivity() {
        Intent startAdIntent = new Intent(this, TakeShotActivity.class);
        startActivity(startAdIntent);
    }

    /**
     * Start set client version 2 for THETA S
     */
    private void doSetOscv2() {
        new ThetaConnector(getResources().getString(R.string.theta_ip_address), this).getSetOSCv2Task().execute();
    }

    /**
     * Start time synchronization with theta
     */
    private void doTimeSynchronization() {
        DateFormat df = new SimpleDateFormat("yyyy:MM:dd HH:mm:ss");
//        df.setTimeZone(TimeZone.getTimeZone("UTC"));
        Date date = new Date(System.currentTimeMillis());
        String timeStamp = df.format(date) + "+00:00";
        mTimeSymchronizationButton.setText(getResources().getString(R.string.connecting));
        new ThetaConnector(getResources().getString(R.string.theta_ip_address), this).getSynctimeTask().execute(timeStamp);
    }
    @Override
    public void onStartRecordingFailed(String result){
    };
    @Override
    public void onStartRecordingSuccess(String result){
    };
    @Override
    public void onStopRecordingFailed(String result){
    };
    @Override
    public void onStopRecordingSuccess(String result){
    };
    @Override
    public void onTCSuccess(String result){
        mTimeSymchronizationButton.setText(getResources().getString(R.string.success));
    }
    @Override
    public void onTCFailed(String result){
        mTimeSymchronizationButton.setText(getResources().getString(R.string.failed));
    }
    @Override
    public void onTPSuccess(String result) {
    }
    @Override
    public void onTPFailed(String result) {
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        // The result of the permission activity.
        //
        // Note that when the permission activity is dismissed, the HelloAreaDescriptionActivity's
        // onResume() callback is called. Because the Tango Service is connected in the onResume()
        // function, we do not call connect here.
        //
        // Check which request we're responding to.
        if (requestCode == REQUEST_CODE_TANGO_PERMISSION) {
            // Make sure the request was successful.
            if (resultCode == RESULT_CANCELED) {
                Toast.makeText(this, R.string.arealearning_permission, Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }
}
