#!/bin/sh

TEST_NUM=$1    # /local-scratch/iida/project/navimap/floorplan/ml/test204/tmp3
DATANAME=$2    # tasc1_8000_e
FLOORNAME=$3    # tasc1_8000

python ../test_heatmap.py $TEST_NUM $DATANAME $FLOORNAME $TEST_NUM/../data/floorplan $TEST_NUM/../data/panorama/
python ../test_alignment_2d.py $TEST_NUM $DATANAME $FLOORNAME $TEST_NUM/../data/floorplan/
