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


/**
 *
 * Theta Movie Recording Functions
 *
 * Created by iida on 20170612.
 */
public class Gear360Connector implements OSCAPI1 {

    /**
     * Listener for the result of the async ADF saving task.
     */
    public interface Gear360ConnectorListener {
        void onTPSuccess(String result);    // return file uri
        void onTPFailed(String result);
    }

    private static final String TAG = Gear360Connector.class.getSimpleName();
    private String mSessionId;
    private String mIpAddress;

    private Timer mCheckStatusTimer = null;
    private final static long CHECK_STATUS_PERIOD_MS = 50;

    private takePictureTask mTakePictureTask;

    private Gear360ConnectorListener mGear360ConnectorListener;

    private GStatus mCurrentStatus;

    public enum GStatus {
        RECORDING, READY, CONNECTING
    }

    Gear360Connector(Gear360ConnectorListener gearConnectorListener){
        this("192.168.107.1", gearConnectorListener);
    }
    Gear360Connector(String ipAddress, Gear360ConnectorListener gearConnectorListener){
        this.mIpAddress = ipAddress;
        this.mTakePictureTask = new takePictureTask();
        this.mGear360ConnectorListener = gearConnectorListener;
        this.mCurrentStatus = GStatus.READY;
    }

    @Override
    public takePictureTask getTakePictureTask() {
        return this.mTakePictureTask;

    }

    public GStatus getCurrentStatus(){
        return this.mCurrentStatus;
    }

    public class takePictureTask extends AsyncTask<Void, Void, String> {

        @Override
        protected void onPreExecute() {
            mCurrentStatus = GStatus.CONNECTING;
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
                mCurrentStatus = GStatus.READY;
                mGear360ConnectorListener.onTPSuccess(result);
            } else {
                Log.i(TAG, "Faile to take picture");
                mCurrentStatus = GStatus.READY;
                mGear360ConnectorListener.onTPFailed("Faile to take picture");
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