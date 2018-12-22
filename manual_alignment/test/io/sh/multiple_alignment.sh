#!/bin/sh

# PREFIX=/local-scratch/iida/project/navimap/floorplan/data/tasc1
PREFIX=$1

python ../test_apply_alignment.py $PREFIX.yaml $PREFIX.json
