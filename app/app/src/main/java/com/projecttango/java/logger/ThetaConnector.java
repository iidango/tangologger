package com.projecttango.java.logger;

import android.os.AsyncTask;
import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.Timer;
import java.util.TimerTask;


/**
 *
 * Theta Movie Recording Functions
 *
 * Created by iida on 20170612.
 */
public class ThetaConnector implements OSCAPI1 {

    /**
     * Listener for the result of the async ADF saving task.
     */
    public interface ThetaConnectorListener {
        void onTCSuccess(String result);
        void onTCFailed(String result);

        void onTPSuccess(String result);    // return file uri
        void onTPFailed(String result);

        void onStartRecordingFailed(String result);
        void onStartRecordingSuccess(String result);
        void onStopRecordingFailed(String result);
        void onStopRecordingSuccess(String result);
    }

    private static final String TAG = ThetaConnector.class.getSimpleName();
    private String mSessionId;
    private String mIpAddress;

    private Timer mCheckStatusTimer = null;
    private final static long CHECK_STATUS_PERIOD_MS = 50;

    private startMovieRecordingTask mStartMovieRecordingTask;
    private stopMovieRecordingTask mStopMovieRecordingTask;
    private syncTimeTask mSyncTimeTask;
    private setOSCv2Task mSetOSCv2Task;
    private takePictureTask mTakePictureTask;

    private ThetaConnectorListener mThetaConnectorListener;

    private TStatus mCurrentStatus;

    public enum TStatus {
        RECORDING, READY, CONNECTING
    }

    ThetaConnector(ThetaConnectorListener thetaConnectorListener){
        this("192.168.1.1", thetaConnectorListener);
    }
    ThetaConnector(String ipAddress, ThetaConnectorListener thetaConnectorListener){
        this.mIpAddress = ipAddress;
        this.mStartMovieRecordingTask = new startMovieRecordingTask();
        this.mStopMovieRecordingTask = new stopMovieRecordingTask();
        this.mSyncTimeTask = new syncTimeTask();
        this.mSetOSCv2Task = new setOSCv2Task();
        this.mTakePictureTask = new takePictureTask();
        this.mThetaConnectorListener = thetaConnectorListener;
        this.mCurrentStatus = TStatus.READY;
    }

    public startMovieRecordingTask getStartMovieRecordingTask(){
        return this.mStartMovieRecordingTask;
    }

    public stopMovieRecordingTask getStopMovieRecordingTask(){
        return this.mStopMovieRecordingTask;
    }

    public setOSCv2Task getSetOSCv2Task(){
        return this.mSetOSCv2Task;
    }

    public syncTimeTask getSynctimeTask(){
        return this.mSyncTimeTask;
    }

    @Override
    public takePictureTask getTakePictureTask() {
        return this.mTakePictureTask;

    }


    public TStatus getCurrentStatus(){
        return this.mCurrentStatus;
    }

    public class startMovieRecordingTask extends AsyncTask<Void, Void, Boolean> {
        @Override
        protected void onPreExecute() {
            mCurrentStatus = TStatus.CONNECTING;
        }

        @Override
        protected Boolean doInBackground(Void... params) {
            /* thetaVだとうまくいかなかったのでとりあえずコメントアウト．moviechaptureの"_video"を"video"にすればいけるかも
            connect();
            if (mSessionId == null) {
//                listener.onError("cannot get to start session");
                return false;
            }

            // set capture mode to movie
            String errorMessage = setMovieCaptureMode();
            if (errorMessage != null) {
                return false;
            }
            // set capture mode to movie
            errorMessage = setMovieFileFormat("mp4", 1920, 1080);
            if (errorMessage != null) {
                return false;
            }
            ここまで*/



            Boolean result = execStartCapture();

            return result;
        }

        @Override
        protected void onPostExecute(Boolean result) {
            if (result) {
                Log.i(TAG, "Success to start movie recording");
                mCurrentStatus = TStatus.RECORDING;
                mThetaConnectorListener.onStartRecordingSuccess("Success to start movie recording");
            } else {
                Log.i(TAG, "Faile to start movie recording");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onStartRecordingFailed("Faile to start movie recording");
            }
        }
    }

    public class stopMovieRecordingTask extends AsyncTask<Void, Void, Boolean> {
        @Override
        protected void onPreExecute() {
            mCurrentStatus = TStatus.CONNECTING;
        }

        @Override
        protected Boolean doInBackground(Void... params) {
            /* theta Vではいらない
            if (mSessionId == null) {
                Log.i(TAG, "cannot identify session id");
                return false;
            }
            ここまで*/

            boolean result = execStopCapture();
            return result;
        }

        @Override
        protected void onPostExecute(Boolean result) {
            if (result) {
                Log.i(TAG, "Success to stop movie recording");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onStopRecordingSuccess("Success to stop movie recording");
            } else {
                Log.i(TAG, "Faile to stop movie recording");
                mCurrentStatus = TStatus.RECORDING;
                mThetaConnectorListener.onStopRecordingFailed("Faile to stop movie recording");
            }
        }
    }

    public class setOSCv2Task extends AsyncTask<String, Void, Boolean> {
        @Override
        protected void onPreExecute() {
            mCurrentStatus = TStatus.CONNECTING;
        }

        @Override
        protected Boolean doInBackground(String... timeStamp) {
            connect();
            if (mSessionId == null) {
                Log.i(TAG, "cannot identify session id");
                return false;
            }

            String result = setOscv2();
            if (result == null){
                return true;
            }else{
                return false;
            }
        }

        @Override
        protected void onPostExecute(Boolean result) {
            if (result) {
                Log.i(TAG, "Success to set client version 2");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onTCSuccess("Success to set client version 2");
            } else {
                Log.i(TAG, "Faile to set date time zone");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onTCFailed("Faile to set date time zone");
            }
        }
    }

    public class syncTimeTask extends AsyncTask<String, Void, Boolean> {
        @Override
        protected void onPreExecute() {
            mCurrentStatus = TStatus.CONNECTING;
        }

        @Override
        protected Boolean doInBackground(String... timeStamp) {
//            connect();
//            if (mSessionId == null) {
//                Log.i(TAG, "cannot identify session id");
//                return false;
//            }

            String result = setDateTimeZone(timeStamp[0]);
            if (result == null){
                return true;
            }else{
                return false;
            }
        }

        @Override
        protected void onPostExecute(Boolean result) {
            if (result) {
                Log.i(TAG, "Success to set date time zone");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onTCSuccess("Success to set date time zone");
            } else {
                Log.i(TAG, "Faile to set date time zone");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onTCFailed("Faile to set date time zone");
            }
        }
    }

    public class takePictureTask extends AsyncTask<Void, Void, String> {

        @Override
        protected void onPreExecute() {
            mCurrentStatus = TStatus.CONNECTING;
        }

        // return null if failed
        @Override
        protected String doInBackground(Void... params) {
            connect();
            if (mSessionId == null) {
                Log.i(TAG, "cannot identify session id");
                return null;
            }

            // take picture
            String id = takePicture();
            if (id == null){
                return null;
            }

            String result = null;
            // wait to take picture
            try {
                while (true){
                    JSONObject status = checkStatus(id);
                    if(status == null){
                        continue;
                    }
                    if (status.getString("state").equals("done")){  // finish taking piucture
                        String fileUri = status.getJSONObject("results").getString("fileUri");
                        String[] tmp = fileUri.split("/");
                        result = tmp[tmp.length - 1];
                        break;
                    }else if(status.getString("state").equals("inProgress")) {  // in progress
                        // wait
                        try {
                            Thread.sleep(500); //5000msec
                        } catch (InterruptedException e) {
                        }
                        continue;
                    }
                    break;
                }
            } catch (JSONException e) {
                e.printStackTrace();
            }

            return result;
        }

        @Override
        protected void onPostExecute(String result) {
            if (result != null) {
                Log.i(TAG, "Success to take picture");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onTPSuccess(result);
            } else {
                Log.i(TAG, "Faile to take picture");
                mCurrentStatus = TStatus.READY;
                mThetaConnectorListener.onTPFailed("Faile to take picture");
            }
        }
    }

    /**
     * @param url   "/osc/state", "/osc/checkForUpdates", "/osc/commands/execute", "/osc/commands/status"
     * @param input request body
     * @return
     */
    private JSONObject postAPI(String url, JSONObject input){
        HttpURLConnection postConnection = createHttpConnection("POST", url);
        JSONObject responseData = null;
        String errorMessage = null;
        InputStream is = null;

        try {
            OutputStream os = postConnection.getOutputStream();
            os.write(input.toString().getBytes());
            postConnection.connect();
            os.flush();
            os.close();

            is = postConnection.getInputStream();
            String resStr = InputStreamToString(is);
            responseData = new JSONObject(resStr);

            // parse JSON data
            /*
            JSONObject output = new JSONObject(responseData);
            String status = output.getString("state");
            Log.i(TAG, status);

            if (status.equals("error")) {
                JSONObject errors = output.getJSONObject("error");
                errorMessage = errors.getString("message");
            }
            */
        } catch (IOException e) {
            e.printStackTrace();
            errorMessage = e.toString();
            InputStream es = postConnection.getErrorStream();
            try {
                if (es != null) {
                    String errorData = InputStreamToString(es);
                    JSONObject output = new JSONObject(errorData);
                    JSONObject errors = output.getJSONObject("error");
                    errorMessage = errors.getString("message");
                }
            } catch (IOException e1) {
                e1.printStackTrace();
            } catch (JSONException e1) {
                e1.printStackTrace();
            } finally {
                if (es != null) {
                    try {
                        es.close();
                    } catch (IOException e1) {
                        e1.printStackTrace();
                    }
                }
            }
        } catch (JSONException e) {
            e.printStackTrace();
            errorMessage = e.toString();
        } finally {
            if (is != null) {
                try {
                    is.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }

        return responseData;
    }

    private JSONObject commandsExecute(String command, JSONObject parameters) throws JSONException {
        JSONObject input= new JSONObject();
        input.put("name", command);
        input.put("parameters", parameters);

        return postAPI("/osc/commands/execute", input);
    }

    private boolean execStartCapture(){
        try{
            JSONObject parameters = new JSONObject();
            parameters.put("sessionId", mSessionId);
            JSONObject result = commandsExecute("camera._startCapture", parameters);
            if(result == null){
                result = commandsExecute("camera.startCapture", parameters);
            }

            String status = result.getString("state");

            if (status.equals("error")) {
                return false;
            }
        } catch (JSONException e1) {
            e1.printStackTrace();
            return false;
        }
        return true;
    }

    private boolean execStopCapture(){
        try{
            JSONObject parameters = new JSONObject();
            parameters.put("sessionId", mSessionId);
            JSONObject result = commandsExecute("camera._stopCapture", parameters);
            if(result == null){
                result = commandsExecute("camera.stopCapture", parameters);
            }

            String status = result.getString("state");

            if (status.equals("error")) {
                return false;
            }
            Log.i(TAG, status);
        } catch (JSONException e1) {
            e1.printStackTrace();
            return false;
        }
        return true;
    }

    private String setOptions(JSONObject options){
        HttpURLConnection postConnection = createHttpConnection("POST", "/osc/commands/execute");
        JSONObject input = new JSONObject();
        String responseData;
        String errorMessage = null;
        InputStream is = null;

        try {
            // send HTTP POST
            input.put("name", "camera.setOptions");
            JSONObject parameters = new JSONObject();
            parameters.put("sessionId", mSessionId);
            parameters.put("options", options);
            input.put("parameters", parameters);

            OutputStream os = postConnection.getOutputStream();
            os.write(input.toString().getBytes());
            postConnection.connect();
            os.flush();
            os.close();

            is = postConnection.getInputStream();
            responseData = InputStreamToString(is);

            // parse JSON data
            JSONObject output = new JSONObject(responseData);
            String status = output.getString("state");
            Log.i(TAG, status);

            if (status.equals("error")) {
                JSONObject errors = output.getJSONObject("error");
                errorMessage = errors.getString("message");
            }
        } catch (IOException e) {
            e.printStackTrace();
            errorMessage = e.toString();
            InputStream es = postConnection.getErrorStream();
            try {
                if (es != null) {
                    String errorData = InputStreamToString(es);
                    JSONObject output = new JSONObject(errorData);
                    JSONObject errors = output.getJSONObject("error");
                    errorMessage = errors.getString("message");
                }
            } catch (IOException e1) {
                e1.printStackTrace();
            } catch (JSONException e1) {
                e1.printStackTrace();
            } finally {
                if (es != null) {
                    try {
                        es.close();
                    } catch (IOException e1) {
                        e1.printStackTrace();
                    }
                }
            }
        } catch (JSONException e) {
            e.printStackTrace();
            errorMessage = e.toString();
        } finally {
            if (is != null) {
                try {
                    is.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        return errorMessage;
    }


    /**
     * Set movie mode
     * @return Error message (null is returned if successful)
     */
    private String setMovieCaptureMode() {
        String errorMessage = null;
        try{
            JSONObject options = new JSONObject();
            options.put("captureMode", "_video");

            return setOptions(options);
        } catch (JSONException e) {
            e.printStackTrace();
            errorMessage = e.toString();
        }
        return errorMessage;
    }

    /**
     * Set movie file format
     * recomended is type: "type", width:1920, height:1080
     * @return Error message (null is returned if successful)
     */
    private String setMovieFileFormat(String type, int width, int height) {
        String errorMessage = null;
        try{
            JSONObject options = new JSONObject();
            JSONObject fileFormat = new JSONObject();
            fileFormat.put("type", type);
            fileFormat.put("width", width);
            fileFormat.put("height", height);
            options.put("fileFormat", fileFormat);

            return setOptions(options);
        } catch (JSONException e) {
            e.printStackTrace();
            errorMessage = e.toString();
        }
        return errorMessage;
    }

    /**
     * Set clientVersion 2
     * Please use for THETA S
     * @return id (null is returned if error)
     */
    private String setOscv2() {
        String errorMessage = null;
        try{
            JSONObject options = new JSONObject();
            options.put("clientVersion", 2);

            return setOptions(options);
        } catch (JSONException e) {
            e.printStackTrace();
            errorMessage = e.toString();
        }
        return errorMessage;
    }

    /**
     * Set date time zone
     * @param timeStamp YYYY:MM:DD HH:MM:SS+(-)HH:MM    ex."2017:06:13 11:15:45+09:00"
     * @return id (null is returned if error)
     */
    private String setDateTimeZone(String timeStamp) {
        String errorMessage = null;
        try{
            JSONObject options = new JSONObject();
            options.put("dateTimeZone", timeStamp);

            return setOptions(options);
        } catch (JSONException e) {
            e.printStackTrace();
            errorMessage = e.toString();
        }
        return errorMessage;
    }

    /**
     * take picture
     * @return Error message (null is returned if successful)
     */
    private String takePicture() {
        try{
            JSONObject input = new JSONObject();
            input.put("name", "camera.takePicture");
            JSONObject parameters = new JSONObject();
            parameters.put("sessionId", mSessionId);
            input.put("parameters", parameters);

            JSONObject result = postAPI("/osc/commands/execute", input);
            String id = result.getString("id");

            return id;
        } catch (JSONException e) {
            e.printStackTrace();
        }
        return null;
    }

    /**
     * checkStatus
     * @return Error message (null is returned if successful)
     */
    private JSONObject checkStatus(String id) {
        try{
            JSONObject input = new JSONObject();
            input.put("id", id);

            JSONObject result = postAPI("/osc/commands/status", input);

            return result;
        } catch (JSONException e) {
            e.printStackTrace();
        }
        return null;
    }



    private class CapturedTimerTask extends TimerTask {
        private String mCommandId;

        public void setCommandId(String commandId) {
            mCommandId = commandId;
        }

        @Override
        public void run() {
            String capturedFileId = checkCaptureStatus(mCommandId);

            if (capturedFileId != null) {
//                mHttpEventListener.onCheckStatus(true);
//                mCheckStatusTimer.cancel();
//                mHttpEventListener.onObjectChanged(capturedFileId);
//                mHttpEventListener.onCompleted();
            } else {
//                mHttpEventListener.onCheckStatus(false);
            }
        }
    }

    /**
     * Check still image shooting status
     * @param commandId Command ID for shooting still images
     * @return ID of saved file (null is returned if the file is not saved)
     */
    private String checkCaptureStatus(String commandId) {
        HttpURLConnection postConnection = createHttpConnection("POST", "/osc/commands/status");
        JSONObject input = new JSONObject();
        String responseData;
        String capturedFileId = null;
        InputStream is = null;

        try {
            // send HTTP POST
            input.put("id", commandId);

            OutputStream os = postConnection.getOutputStream();
            os.write(input.toString().getBytes());
            postConnection.connect();
            os.flush();
            os.close();

            is = postConnection.getInputStream();
            responseData = InputStreamToString(is);

            // parse JSON data
            JSONObject output = new JSONObject(responseData);
            String status = output.getString("state");

            if (status.equals("done")) {
                JSONObject results = output.getJSONObject("results");
                capturedFileId = results.getString("fileUri");
            }
        } catch (IOException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        } finally {
            if (is != null) {
                try {
                    is.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }

        return capturedFileId;
    }

    /**
     * Connect to device
     * @return Session ID (null is returned if the connection fails)
     */
    private void connect(){
        HttpURLConnection postConnection = createHttpConnection("POST", "/osc/commands/execute");
        JSONObject input = new JSONObject();
        String responseData;
        String sessionId = null;
        InputStream is = null;

        try {
            // send HTTP POST
            input.put("name", "camera.startSession");

            OutputStream os = postConnection.getOutputStream();
            os.write(input.toString().getBytes());
            postConnection.connect();
            os.flush();
            os.close();

            is = postConnection.getInputStream();
            responseData = InputStreamToString(is);

            // parse JSON data
            JSONObject output = new JSONObject(responseData);
            String status = output.getString("state");

            if (status.equals("done")) {
                JSONObject results = output.getJSONObject("results");
                sessionId = results.getString("sessionId");
            } else if (status.equals("error")) {
                JSONObject errors = output.getJSONObject("error");
                String errorCode = errors.getString("code");
                if (errorCode.equals("invalidSessionId")) {
                    sessionId = null;
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        } catch (JSONException e) {
            e.printStackTrace();
        } finally {
            if (is != null) {
                try {
                    is.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        Log.i(TAG, "start session as " + sessionId);
        mSessionId = sessionId;
    }

    /**
     * Generate HTTP connection
     * @param method Method
     * @param path Path
     * @return HTTP Connection instance
     */
    private HttpURLConnection createHttpConnection(String method, String path) {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(createUrl(path));
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestProperty("Content-Type", "application/json;charset=utf-8");
            connection.setRequestProperty("Accept", "application/json");
            connection.setDoInput(true);

            if (method.equals("POST")) {
                connection.setRequestMethod(method);
                connection.setDoOutput(true);
            }

        } catch (MalformedURLException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

        return connection;
    }
    /**
     * Generate connection destination URL
     * @param path Path
     * @return URL
     */
    private String createUrl(String path) {
        StringBuilder sb = new StringBuilder();
        sb.append("http://");
        sb.append(mIpAddress);
        sb.append(path);

        return sb.toString();
    }
    /**
     * Convert input stream to string
     * @param is InputStream
     * @return String
     * @throws IOException IO error
     */
    private String InputStreamToString(InputStream is) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"));
        StringBuilder sb = new StringBuilder();
        String lineData;
        while ((lineData = br.readLine()) != null) {
            sb.append(lineData);
        }
        br.close();
        return sb.toString();
    }
}