package com.projecttango.java.logger;

import android.util.Log;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.math.BigDecimal;
import java.util.ArrayList;

/**
 * Created by iida on 20170615.
 */

public class GPSData extends SensorData{
    private ArrayList<Float> mAccuracy;
    private ArrayList<Float> mBearing;
    private ArrayList<Float> mSpeed;
    private ArrayList<Long> mTime;
    private ArrayList<String> mProvider;

    public GPSData(){
        super();
        this.setType("gpsLocation");
        mAccuracy = new ArrayList<>();
        mBearing = new ArrayList<>();
        mSpeed = new ArrayList<>();
        mTime = new ArrayList<>();
        mProvider = new ArrayList<>();
    }

    public void addData(double t, double lon, double lat, double alt, float accuracy, float bearing, float speed, long time, String provider){
        this.addTimestamp(t);
        this.addX(lon);
        this.addY(lat);
        this.addZ(alt);
        this.addAccuracy(accuracy);
        this.addBearing(bearing);
        this.addSpeed(speed);
        this.addTime(time);
        this.addProvider(provider);
    }

    public void addAccuracy(float accuracy){
        this.mAccuracy.add(accuracy);
    }
    public void addBearing(float bearing){
        this.mBearing.add(bearing);
    }
    public void addSpeed(float speed){
        this.mSpeed.add(speed);
    }
    public void addTime(long time){
        this.mTime.add(time);
    }
    public void addProvider(String provider){
        this.mProvider.add(provider);
    }

    public float getAccuracy(int i){
        return mAccuracy.get(i);
    }
    public float getBearing(int i){
        return mBearing.get(i);
    }
    public float getSpeed(int i){
        return mSpeed.get(i);
    }
    public long getTime(int i){
        return mTime.get(i);
    }
    public String getProvider(int i){
        return mProvider.get(i);
    }


    public int sizeAccuracy(){
        return mAccuracy.size();
    }
    public int sizeBearing(){
        return mBearing.size();
    }
    public int sizeSpeed(){
        return mSpeed.size();
    }
    public int sizeTime(){
        return mTime.size();
    }
    public int sizeProvider(){
        return mProvider.size();
    }

    @Override
    public boolean isValid(){
        return sizeTimestamp() == sizeX()
                && sizeTimestamp() == sizeY()
                && sizeTimestamp() == sizeZ()
                && sizeTimestamp() == sizeAccuracy()
                && sizeTimestamp() == sizeBearing()
                && sizeTimestamp() == sizeSpeed()
                && sizeTimestamp() == sizeTime()
                && sizeTimestamp() == sizeProvider();
    }

    @Override
    public boolean save(String fn){
        try {
            String filePath = OUTPUT_PATH + fn;
            File file = new File(filePath);
            if (!file.exists()){
                Log.e("warning", fn + " exists. OverWrite");
            }
            file.getParentFile().mkdir();

            FileOutputStream fos = new FileOutputStream(file, true);
            OutputStreamWriter osw = new OutputStreamWriter(fos, "UTF-8");
            BufferedWriter bw = new BufferedWriter(osw);

            // header
            boolean writeHeader = false;
            if (writeHeader){
                bw.write("timestamp,Longitude,Latitude,Altitude,Accuracy,Bearing,Speed,Time,Provider");
                bw.newLine();
            }

            // write data
            for (int i = 0; i < this.size(); i++){
                String data = "";
                data += BigDecimal.valueOf(this.getTimestamp(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getX(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getY(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getZ(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getAccuracy(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getBearing(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getSpeed(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getTime(i)).toPlainString();
                data += "," + this.getProvider(i);

                bw.write(data);
                bw.newLine();
            }

            bw.flush();
            bw.close();
            return true;
        } catch (IOException e) {
            e.printStackTrace();
        }
        return false;
    }
}
