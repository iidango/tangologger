#!/bin/sh

# PREFIX=/local-scratch/iida/project/navimap/floorplan/data/sfu/tasc1_8000_c
PREFIX=$1

rm $PREFIX/images/*
rm $PREFIX/images_northup/*
python ../test_load_tangoPose.py $PREFIX $PREFIX $PREFIX/R0010226_er.MP4 3 0.2 -t
python ../test_set_floorplan.py $PREFIX $PREFIX $PREFIX/floorplans/tasc1_8000.png 0 0 -0.03 -58.25 -15.5 1.8
python ../test_adjust_img_direction.py $PREFIX $PREFIX
