#!/bin/sh

PREFIX=$1

rm $PREFIX/images/*
rm $PREFIX/images_northup/*
python ../test_load_tangoPose.py $PREFIX -m meta.yaml
python ../test_set_floorplan.py $PREFIX -m meta.yaml
python ../test_adjust_img_direction.py $PREFIX 
