#!/bin/sh

# PREFIX=/local-scratch/iida/project/navimap/floorplan/data/sfu/tasc1_8000_c
PREFIX=$1

python ../test_load_tangoPose.py $PREFIX -m meta.yaml
python ../test_set_floorplan.py $PREFIX -m meta.yaml
