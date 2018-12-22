#!/bin/sh

TEST_NUM=$1    # /local-scratch/iida/project/navimap/floorplan/ml/test204/tmp3


python ../plot_alignment_result.py $TEST_NUM zengaku_1f_s_all zengaku_1f_s $TEST_NUM/../data/floorplan/ align_info.txt -s 5 -f zengaku_1f_n zengaku_1f_s zengaku_2f_n zengaku_2f_s zengaku_3f_n zengaku_3f_s
