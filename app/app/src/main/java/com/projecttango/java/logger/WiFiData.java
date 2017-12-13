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

public class WiFiData extends SensorData{
    private ArrayList<String> mBSSID;
    private ArrayList<String> mSSID;
    private ArrayList<Integer> mLevel;
//    private ArrayList<Long> mTime;
    private ArrayList<Double> mTime;

    public WiFiData(){
        super();
        this.setType("wifi");
        mBSSID = new ArrayList<>();
        mSSID = new ArrayList<>();
        mLevel = new ArrayList<>();
        mTime = new ArrayList<>();
    }

    public void addData(double t, double x, double y, double z, String bssid, String ssid, int level, long time){
        this.addTimestamp(t);
        this.addX(x);
        this.addY(y);
        this.addZ(z);
        this.addBSSID(bssid);
        this.addSSID(ssid);
        this.addLevel(level);
        this.addTime(time);
    }

    public void addBSSID(String bssid){
        this.mBSSID.add(bssid);
    }
    public void addSSID(String ssid){
        this.mSSID.add(ssid);
    }
    public void addLevel(int level){
        this.mLevel.add(level);
    }
    public void addTime(double time){
        this.mTime.add(time);
    }

    public String getBSSID(int i){
        return mBSSID.get(i);
    }
    public String getSSID(int i){
        return mSSID.get(i);
    }
    public int getLevel(int i){
        return mLevel.get(i);
    }
    public double getTime(int i){
        return mTime.get(i);
    }


    public int sizeBSSID(){
        return mBSSID.size();
    }
    public int sizeSSID(){
        return mSSID.size();
    }
    public int sizeLevel(){
        return mLevel.size();
    }
    public int sizeTime(){
        return mTime.size();
    }

    @Override
    public boolean isValid(){
        return sizeTimestamp() == sizeBSSID()
                && sizeTimestamp() == sizeSSID()
                && sizeTimestamp() == sizeLevel()
                && sizeTimestamp() == sizeTime();
    }

    @Override
    public boolean save(String fn, int digits, double offset){
        save(fn.substring(0, fn.lastIndexOf(".")) + "_upt.csv");
        for (int i = 0; i < sizeTimestamp(); i++){
            double t = this.mTimestamp.get(i);
            this.mTimestamp.set(i, t*Math.pow(10, digits) + offset);

            t = mTime.get(i);
            this.mTime.set(i, t*Math.pow(10, digits+3) + offset);
        }
        return save(fn);
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
                bw.write("timestamp,bssid,ssid,level(rssi),Time");
                bw.newLine();
            }

            // write data
            for (int i = 0; i < this.size(); i++){
                String data = "";
                data += BigDecimal.valueOf(this.getTimestamp(i)).toPlainString();
                data += "," + this.getBSSID(i);
                data += "," + this.getSSID(i);
                data += "," + BigDecimal.valueOf(this.getLevel(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getTime(i)).toPlainString();

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
