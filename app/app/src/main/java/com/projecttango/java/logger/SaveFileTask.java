package com.projecttango.java.logger;

import android.content.Context;
import android.os.AsyncTask;

import com.google.atap.tangoservice.Tango;
import com.google.atap.tangoservice.TangoPoseData;
import com.projecttango.tangosupport.TangoSupport;

import java.util.ArrayList;

import static android.os.SystemClock.elapsedRealtime;
import static java.lang.System.currentTimeMillis;

/**
 * Saves the trajectory on a background thread and shows a progress dialog while
 * saving.
 *
 * Created by iida on 20170606.
 */
public class SaveFileTask extends AsyncTask<Void, Integer, Boolean> {

    /**
     * Listener for the result of the async ADF saving task.
     */
    public interface SaveFileListener {
        void onSaveFileFailed(String fileName);
        void onSaveFileSuccess(String fileName);
    }

    Context mContext;
    SaveFileListener mCallbackListener;
    SaveFileDialog mProgressDialog;
    Tango mTango;
    String mFileName;

    // target data to save
    private int mDisplayRotation;
    private SensorData mTrajectoryData;
    private ArrayList<SensorData> mSensorDatas;

    SaveFileTask(Context context, SaveFileListener callbackListener, Tango tango, String fileName, int displayRotation, SensorData trajectoryData, ArrayList<SensorData> sensorDatas) {
        mContext = context;
        mCallbackListener = callbackListener;
        mTango = tango;
        mFileName = fileName;
        mProgressDialog = new SaveFileDialog(context);
        mDisplayRotation = displayRotation;
        mTrajectoryData = trajectoryData;
        mSensorDatas = sensorDatas;
    }

    /**
     * Sets up the progress dialog.
     */
    @Override
    protected void onPreExecute() {
        if (mProgressDialog != null) {
            mProgressDialog.show();
        }
    }

    /**
     * Performs long-running save in the background.
     */
    @Override
    protected Boolean doInBackground(Void... params) {
        try {
            /*
            // Save the ADF.
            adfUuid = mTango.saveAreaDescription();

            // Read the ADF Metadata, set the desired name, and save it back.
            TangoAreaDescriptionMetaData metadata = mTango.loadAreaDescriptionMetaData(adfUuid);
            metadata.set(TangoAreaDescriptionMetaData.KEY_NAME, mAdfName.getBytes());
            mTango.saveAreaDescriptionMetadata(adfUuid, metadata);
            */

            // create trajectory data for save
            // the trajectory may be arranged by drift correction

            // TODO change base frame depends on their option
            PoseData cameraPoseDataOutPut = new PoseData(); // without drift correction
            for (int i = 0; i < mTrajectoryData.size(); i++){
                // cameraposedata
                TangoPoseData cameraPose = TangoSupport.getPoseAtTime(mTrajectoryData.getTimestamp(i),
                        TangoPoseData.COORDINATE_FRAME_AREA_DESCRIPTION,
                        TangoPoseData.COORDINATE_FRAME_DEVICE,
                        TangoSupport.TANGO_SUPPORT_ENGINE_OPENGL,
                        TangoSupport.TANGO_SUPPORT_ENGINE_OPENGL,
                        mDisplayRotation);  // TODO displayRotatationは必要？
                if (cameraPose.statusCode == TangoPoseData.POSE_VALID) {
                    cameraPoseDataOutPut.addTimestamp(mTrajectoryData.getTimestamp(i));
                    float[] translation = cameraPose.getTranslationAsFloats();
                    cameraPoseDataOutPut.addX(translation[0]);
                    cameraPoseDataOutPut.addY(translation[1]);
                    cameraPoseDataOutPut.addZ(translation[2]);
                    float[] rotation = cameraPose.getRotationAsFloats();
                    cameraPoseDataOutPut.addRotQ1(rotation[0]);
                    cameraPoseDataOutPut.addRotQ2(rotation[1]);
                    cameraPoseDataOutPut.addRotQ3(rotation[2]);
                    cameraPoseDataOutPut.addRotQ4(rotation[3]);
                }
            }

            // save files(UNIX time(sec))
            // calc offset between systemStart and unixTime
            double systemStartedAt = (double) (currentTimeMillis() - elapsedRealtime ())/1000;
            // save trajectory data
            cameraPoseDataOutPut.save(mFileName + "_cameraPose.csv", 0, systemStartedAt);
            // save sensor datas
            for (SensorData s: mSensorDatas){
                s.save(mFileName + "_" + s.getType() + ".csv", -9, systemStartedAt);
            }

        } catch (Exception e){
            e.printStackTrace();
            return false;
        }
        return true;
    }

    /**
     * Responds to progress update events by updating the UI.
     */
    @Override
    protected void onProgressUpdate(Integer... progress) {
        if (mProgressDialog != null) {
            mProgressDialog.setProgress(progress[0]);
        }
    }

    /**
     * Dismisses the progress dialog and call the activity.
     */
    @Override
    protected void onPostExecute(Boolean result) {
        if (mProgressDialog != null) {
            mProgressDialog.dismiss();
        }
        if (mCallbackListener != null) {
            if (result) {
                mCallbackListener.onSaveFileSuccess(mFileName);
            } else {
                mCallbackListener.onSaveFileFailed(mFileName);
            }
        }
    }
}
