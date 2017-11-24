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
tangoLogger/manual_alignment/test/io/sh

2. align trajectory with floorplan image  
tangoLogger/manual_alignment/test/io/sh  

Please check and run sample scripts  
```
$ cd tangoLogger/manual_alignment/test/io/sh
$ ./tasc1_8000_c.sh ../../../../sfu_sample_novideo/tasc1_8000/tasc1_8000_c
```
Then you will find 2dtrajectory.csv, floorplan_trajectory.png etc. in sfu_sample_novideo/tasc1_8000/tasc1_8000_c  
You can align trajactory by changing argument for ../test_set_floorplan.py(rotx roty rotz trax tray traz)

#### Other ####
You can also check 3D trajectory using viewer(modified version of https://github.com/mapillary/OpenSfM)
