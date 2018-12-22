#!/bin/sh

# DATA_ROOT=/local-scratch/iida/project/navimap/floorplan/data/sfu_data
DATA_ROOT=$1

# ls $DATA_ROOT | xargs -I{} python ../test_load_tangoPose.py $DATA_ROOT/{} -m meta.yaml
ls $DATA_ROOT | xargs -I{} python ../test_plot_trajectorys.py $DATA_ROOT/{}
