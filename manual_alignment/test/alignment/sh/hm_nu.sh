#!/bin/sh

TEST_NUM=$1    # /local-scratch/iida/project/navimap/floorplan/ml/test204/tmp3
DATA_NAME=$2    # zengaku_1f_s_all
FLOOR_NAME=$3    # zengaku_1f_s

python ../test_heatmap.py $TEST_NUM $DATA_NAME $FLOOR_NAME $TEST_NUM/../data/floorplan $TEST_NUM/../data/panorama/ -f eng2_1f eng2_2f eng2_3f eng2_4f zengaku_1f_n zengaku_1f_s zengaku_2f_n zengaku_2f_s zengaku_3f_n zengaku_3f_s

