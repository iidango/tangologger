package com.projecttango.java.logger;

import android.util.Log;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.math.BigDecimal;
import java.util.ArrayList;

/**
 * Created by iida on 20170615.
 */

public class PoseData extends SensorData{
    private ArrayList<Double> mRotQ1;
    private ArrayList<Double> mRotQ2;
    private ArrayList<Double> mRotQ3;
    private ArrayList<Double> mRotQ4;

    public PoseData(){
        super();
        mRotQ1 = new ArrayList<>();
        mRotQ2 = new ArrayList<>();
        mRotQ3 = new ArrayList<>();
        mRotQ4 = new ArrayList<>();
    }

    public void addData(double t, double x, double y, double z, double rotQ1, double rotQ2, double rotQ3, double rotQ4){
        this.addTimestamp(t);
        this.addX(x);
        this.addY(y);
        this.addZ(z);
        this.addRotQ1(rotQ1);
        this.addRotQ2(rotQ2);
        this.addRotQ3(rotQ3);
        this.addRotQ4(rotQ4);
    }

    public void addRotQ1(double rotQ1){
        this.mRotQ1.add(rotQ1);
    }
    public void addRotQ2(double rotQ2){
        this.mRotQ2.add(rotQ2);
    }
    public void addRotQ3(double rotQ3){
        this.mRotQ3.add(rotQ3);
    }
    public void addRotQ4(double rotQ4){
        this.mRotQ4.add(rotQ4);
    }

    public double getRotQ1(int i){
        return mRotQ1.get(i);
    }
    public double getRotQ2(int i){
        return mRotQ2.get(i);
    }
    public double getRotQ3(int i){
        return mRotQ3.get(i);
    }
    public double getRotQ4(int i){
        return mRotQ4.get(i);
    }

    public int sizeRotQ1(){
        return mRotQ1.size();
    }
    public int sizeRotQ2(){
        return mRotQ2.size();
    }
    public int sizeRotQ3(){
        return mRotQ3.size();
    }
    public int sizeRotQ4(){
        return mRotQ4.size();
    }

    @Override
    public boolean isValid(){
        return sizeTimestamp() == sizeX()
                && sizeTimestamp() == sizeY()
                && sizeTimestamp() == sizeZ()
                && sizeTimestamp() == sizeRotQ1()
                && sizeTimestamp() == sizeRotQ2()
                && sizeTimestamp() == sizeRotQ3()
                && sizeTimestamp() == sizeRotQ4();
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
                bw.write("timestamp,x,y,z,rotQ1,rotQ2,rotQ3,rotQ4");
                bw.newLine();
            }

            // write data
            for (int i = 0; i < this.size(); i++){
                String data = "";
                data += BigDecimal.valueOf(this.getTimestamp(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getX(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getY(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getZ(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getRotQ1(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getRotQ2(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getRotQ3(i)).toPlainString();
                data += "," + BigDecimal.valueOf(this.getRotQ4(i)).toPlainString();

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

    public boolean loadFile(File f, int header){
        try {
            BufferedReader br = new BufferedReader(new FileReader(f));

            // skip header line
            for (int i = 0; i < header; i++) {
                br.readLine();
            }

            String line;
            while ((line = br.readLine()) != null) {
                String[] data = line.split(",", 0);

                if (data.length < 8) {
                    continue;
                }

                this.addTimestamp(Double.valueOf(data[0]));
                this.addX(Double.valueOf(data[1]));
                this.addY(Double.valueOf(data[2]));
                this.addZ(Double.valueOf(data[3]));
                this.addRotQ1(Double.valueOf(data[4]));
                this.addRotQ2(Double.valueOf(data[5]));
                this.addRotQ3(Double.valueOf(data[6]));
                this.addRotQ4(Double.valueOf(data[7]));
            }
            br.close();
            return true;
        } catch (IOException e) {
            System.out.println(e);
            return false;
        }
    }
}
