#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../../'))
sys.path.append(os.path.abspath('/grad/1/iida/mytools/python2.7/lib/python2.7/site-packages/'))

import argparse
import mylogger
from handler import reconstructionHandler

IN_RECONSTRUCTION_FILENAME = "reconstruction.json"
IN_RECONSTRUCTION_FILENAME = "tangoCameraPose_floor.json"
OUT_RECONSTRUCTION_FILENAME = "reconstruction_tangoCameraPose_floor.json"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="alignment script")
    parser.add_argument("src_dir", help="path to src_dir to be processed")
    parser.add_argument("dst_dir", help="path to dst_dir to be output")
    args = parser.parse_args()

    # load reconstruction file
    recon_in_fn = os.path.join(args.src_dir, IN_RECONSTRUCTION_FILENAME)
    reconstructions = reconstructionHandler.loadReconstruction(recon_in_fn)

    # ignore points
    reconstructionHandler.applyAll(reconstructions, reconstructionHandler.ignorePoints)

    # set offset
    # offset = np.array([
    #     [1, 0, 0, 0],
    #     [0, 1, 0, 0],
    #     [0, 0, 1, 100],
    #     [0, 0, 0, 1],
    # ])
    # for reconstruction in reconstructions:
    #     reconstructionHandler.setOffset(reconstruction, offset)

    # shot pose to xyz point
    reconstructionHandler.applyAll(reconstructions, reconstructionHandler.addAxisPoint)

    # save reconstruction file
    recon_out_fn = os.path.join(args.dst_dir, OUT_RECONSTRUCTION_FILENAME)
    reconstructionHandler.saveReconstructions(reconstructions, recon_out_fn)

