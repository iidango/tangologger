#!/bin/sh

TEST_NUM=$1    # /local-scratch/iida/project/navimap/floorplan/ml/test204/tmp3
DATA_NAME=$2    # zengaku_1f_s_all
FLOOR_NAME=$3    # zengaku_1f_s


python ../test_alignment_2d.py $TEST_NUM $DATA_NAME $FLOOR_NAME $TEST_NUM/../data/floorplan/ -s 5 -f zengaku_1f_n zengaku_1f_s zengaku_2f_n zengaku_2f_s zengaku_3f_n zengaku_3f_s
