#!/bin/sh

# PREFIX=/local-scratch/iida/project/navimap/floorplan/data/sfu/tasc1_8000_c
PREFIX=$1

rm $PREFIX/images/*
rm $PREFIX/images_northup/*
python ../test_load_tangoPose.py $PREFIX R0010227_er.MP4 3 0.3 -t
python ../test_set_floorplan.py $PREFIX tasc1_8000.png 0 0 0.08 -21.5 -15.5 1.8
python ../test_adjust_img_direction.py $PREFIX
