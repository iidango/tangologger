#!/bin/sh

# DATASET=/local-scratch/iida/project/navimap/floorplan/ml/floorplan_candidate/2
DATASET=$1
CROP_STEP=$2
CROP_SIZE=150

# nu
python ../test_heatmap_floor.py $DATASET eng2_1f $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET eng2_2f $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET eng2_3f $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET eng2_4f $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET zengaku_1f_n $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET zengaku_1f_s $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET zengaku_2f_s $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET zengaku_2f_n $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET zengaku_3f_n $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET zengaku_3f_s $CROP_SIZE $CROP_STEP

# sfu
python ../test_heatmap_floor.py $DATASET tasc1_7000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET tasc1_8000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET tasc1_9000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET tasc2_6000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET tasc2_7000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET tasc2_8000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET tasc2_9000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET aq_1000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET aq_2000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET aq_3000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET aq_4000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET aq_5000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET aq_6000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET asb_8000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET asb_9000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET asb_10000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssb_5000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssb_6000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssb_7000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssb_8000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssb_9000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssc_6000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssc_7000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssc_8000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssc_9000 $CROP_SIZE $CROP_STEP
python ../test_heatmap_floor.py $DATASET ssc_10000 $CROP_SIZE $CROP_STEP

