# README #

Manual alignment scripts for tango logger

### Manual alignment tango trajectory ###
#### pull data from android device ####
tangoLogger/misc/pullData.sh
```
$ cd <DATA_DIR>
$ /path/to/pullData.sh <DATA_NAME>
```

You should also put floorplan image(10 pix per meter) data to <DATA_DIR>  
DATA_DIR/floorplans/FLOOR_NAME.png

#### manual alignment ####
Please refer tangoLogger/manual_alignment/test/io/sh/tasc1_8000_c.sh

1. load tango trajectory and create json file(It's necessary even if you don't have video)  
tangoLogger/manual_alignment/test/io/test_load_tangoPose.py

2. align trajectory with floorplan image  
tangoLogger/manual_alignment/test/io/test_set_floorplan.py  

Please check and run sample scripts  
```
$ cd tangoLogger/manual_alignment/test/io/sh
$ ./manual_alignment.sh ../../../../sfu_sample_novideo/tasc1_8000/tasc1_8000_c
```
Then you will find 2dtrajectory.csv, floorplan_trajectory.png etc. in sfu_sample_novideo/tasc1_8000/tasc1_8000_c  
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

#### Other ####
You can also check 3D trajectory using viewer(modified version of https://github.com/mapillary/OpenSfM)
