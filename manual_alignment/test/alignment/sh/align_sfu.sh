#!/bin/sh

TEST_NUM=$1    # /local-scratch/iida/project/navimap/floorplan/ml/test204/tmp3


python ../test_alignment_2d.py $TEST_NUM tasc1_8000_e tasc1_8000 $TEST_NUM/../data/floorplan/
python ../test_alignment_2d.py $TEST_NUM tasc1_9000_w tasc1_9000 $TEST_NUM/../data/floorplan/
