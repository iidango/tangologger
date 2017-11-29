package com.projecttango.java.logger;

import android.os.Environment;
import android.util.Log;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.math.BigDecimal;
import java.util.ArrayList;

/**
 * Created by iida on 20170606.
 */

public class SensorData {
    protected static final String OUTPUT_PATH = Environment.getExternalStorageDirectory() + "/" + "tangoLogger" + "/";

    protected ArrayList<Double> mTimestamp;
    protected ArrayList<Double> mX;
    protected ArrayList<Double> mY;
    protected ArrayList<Double> mZ;
    protected String type;

    public SensorData() {
        this(null);
    }
    public SensorData(String type) {
        this.type = type;
        this.mTimestamp = new ArrayList<>();
        this.mX = new ArrayList<>();
        this.mY = new ArrayList<>();
        this.mZ = new ArrayList<>();
    }

    public void addData(double t, double x, double y, double z){
        this.mTimestamp.add(t);
        this.mX.add(x);
        this.mY.add(y);
        this.mZ.add(z);
    }
    public void addTimestamp(double t){
        this.mTimestamp.add(t);
    }
    public void addX(double x){
        this.mX.add(x);
    }
    public void addY(double y){
        this.mY.add(y);
    }
    public void addZ(double z){
        this.mZ.add(z);
    }
    public void setType(String type){
        this.type = type;
    }

    public double[] get(int i){
        return new double[] {mTimestamp.get(i), mX.get(i), mY.get(i), mZ.get(i)};
    }

    public double getTimestamp(int i){
        return mTimestamp.get(i);
    }
    public double getX(int i){
        return mX.get(i);
    }
    public double getY(int i){
        return mY.get(i);
    }
    public double getZ(int i){
        return mZ.get(i);
    }
    public String getType(){
        return type;
    }

    public int size(){
        return mTimestamp.size();
    }
    public int sizeTimestamp(){
        return mTimestamp.size();
    }
    public int sizeX(){
        return mX.size();
    }
    public int sizeY(){
        return mY.size();
    }
    public int sizeZ(){
        return mZ.size();
    }

    public boolean isValid(){
        return mTimestamp.size() == mX.size() && mTimestamp.size() == mY.size() && mTimestamp.size() == mZ.size();
    }

    public boolean save(String fn, int digits, double offset){
        for (int i = 0; i < sizeTimestamp(); i++){
            double t = mTimestamp.get(i);
            mTimestamp.set(i, t*Math.pow(10, digits) + offset);
        }
        return save(fn);
    }

    public boolean save(String fn){
        try {
            String filePath = OUTPUT_PATH + fn;
            File file = new File(filePath);
            if (!file.exists()){
                Log.e("error", fn + " exists. OverWrite");
            }
            file.getParentFile().mkdir();

            FileOutputStream fos = new FileOutputStream(file, true);
            OutputStreamWriter osw = new OutputStreamWriter(fos, "UTF-8");
            BufferedWriter bw = new BufferedWriter(osw);

            // header
            boolean writeHeader = false;
            if (writeHeader){
                bw.write("timestamp,x,y,z");
                bw.newLine();
            }

            // write data
            for (int i = 0; i < this.size(); i++){
                String data = "";
                data += BigDecimal.valueOf(this.getTimestamp(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getX(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getY(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getZ(i)).toPlainString();

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
