# README #

Manual alignment scripts for tango logger  

## dataset
Please put data in tangologger/data. 
If you want to get data, please contact me.

## data format ##
* cameraPose.csv  

Tango trajectory: timestamp(unixtime[sec]),x[m],y[m],z[m],rotQ1,rotQ2,rotQ3,rotQ4

* wifi.csv  

wifi signal data: timestamp(unixtime[sec]),bssid,ssid,level(rssi),SeenTime  
Current version of my app request wifi data every 100msec and record bssid, ssid, level, timestamp(ref https://developer.android.com/reference/android/net/wifi/ScanResult.html).  
We can change frequency if you want.  

My app also collect sensores data below

* android.sensor.accerometer.csv  
* android.sensor.gyroscope.csv  
* android.sensor.magnetic_field.csv  
* android.sensor.pressure.csv  

You can find alignment parameter in meta.yaml  

### convert data to tab splited format ###
To convert data format to tab splited format, please run misc/convertFormat.py  
```
$ python misc/convertFormat.py sfu_sample_novideo/tasc1_8000/tasc1_8000_c
```

Then, you will find pose.txt and wifi.txt in sfu_sample_novideo/tasc1_8000/tasc1_8000_c  
This conversion is not needed for my tools.

## Manual alignment tango trajectory ##
### pull data from android device ###
tangoLogger/misc/pullData.sh
```
$ cd <DATA_DIR>
$ /path/to/pullData.sh <DATA_NAME>
```

You should also put floorplan image(10 pix per meter) data to <DATA_DIR>  
DATA_DIR/floorplans/FLOOR_NAME.png

### manual alignment ###
Please refer tangoLogger/manual_alignment/test/io/sh/tasc1_8000_c.sh

1. load tango trajectory and create json file(It's necessary even if you don't have video)  
tangoLogger/manual_alignment/test/io/test_load_tangoPose.py

2. align trajectory with floorplan image  
tangoLogger/manual_alignment/test/io/test_plot_trajectorys.py  

Please check and run sample scripts  
```
$ cd tangoLogger/manual_alignment/test/io/sh
$ ./manual_alignment.sh ../../../../data/datasets/tasc1_8000_c
```
Then you will find 2dtrajectory.csv, trajectory_tasc1_8000.png etc. in data/datasets/tasc1_8000/tasc1_8000_c  
You can align trajactory by changing parameter in meta.yaml in DATA_DIR  
```
floorplans:
  tasc1_8000.png:
    manual_alignment:
      rotx: 0.0
      roty: 0.0
      rotz: 0.08
      trax: -21.5
      tray: -15.5
      traz: 1.8
```
rotations in radians and translations in meter  

### multiple data alignment ###
Multiple data alignment sample is in tangoLogger/data/floorplan_alignment.yaml(containing only floorplans) and tangoLogger/data/tasc1.yaml  
Please run below script to create json file for visualization.

```
./multiple_alignment.sh ../../../../data/tasc1
```

Then you will get tangoLogger/data/tasc1.json.  

### Visualization ###
You can also check 3D trajectory using viewer(modified version of https://github.com/mapillary/OpenSfM)  

1. Run local server  
```
$ python -m SimpleHTTPServer # python2
```
or 
```
$ python -m http.server # python3
```

2. Open html file in browser  
http://localhost:8000/viewer/index.html#file=/data/datasets/tasc1_8000_c/tangoCameraPose_floor.json
