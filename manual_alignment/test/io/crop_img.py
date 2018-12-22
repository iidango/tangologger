#! /usr/bin/env python
#! -*- coding: utf-8 -*-
'''
conver panorama image to perspective
'''

import sys
import os
import re
from PIL import Image
import numpy as np
import argparse
import cv2
from math import pi, sin, cos, tan, atan2, hypot, floor
from multiprocessing import Pool

# convert using an inverse transformation
def convertFace(img_in, img_out, faceSize, z_offset, direction):
    inSize = [faceSize*2, faceSize*4]

    for y_out in range(img_out.shape[0]):
        for x_out in range(img_out.shape[1]):
            # calc x, y, z coordinate
            a = (y_out - img_out.shape[0]/2) / float(faceSize/2)
            b = (x_out - img_out.shape[1]/2) / float(faceSize/2)

            if direction == 0:    # front
                (x,y,z) = (- b, 1.0, - a + z_offset)
            elif direction == 1:    # back
                (x,y,z) = (b, - 1.0, - a + z_offset)
            else:    # front
                (x,y,z) = (- b, 1.0, - a + z_offset)

            # if faceIdx == 0: # back
            #     (x,y,z) = (-1.0, 1.0 - a, 1.0 - b)
            # elif faceIdx == 1: # left
            #     (x,y,z) = (a - 1.0, -1.0, 1.0 - b)
            # elif faceIdx == 2: # front
            #     (x,y,z) = (1.0, a - 1.0, 1.0 - b)
            # elif faceIdx == 3: # right
            #     (x,y,z) = (b, 1.0, a)
            # elif faceIdx == 4: # top
            #     (x,y,z) = (b - 1.0, a - 1.0, 1.0)
            # elif faceIdx == 5: # bottom
            #     (x,y,z) = (1.0 - b, a - 1.0, -1.0)

            theta = atan2(y,x) # range -pi to pi
            r = hypot(x,y)
            phi = atan2(z,r) # range -pi/2 to pi/2

            # source img coords
            uf = 0.5 * inSize[1] * (theta + pi) / pi
            vf = 0.5 * inSize[1] * (pi/2 - phi) / pi

            # Use bilinear interpolation between the four surrounding pixels
            # ui = floor(uf)  # coord of pixel to bottom left
            # vi = floor(vf)
            ui = int(uf)  # coord of pixel to bottom left
            vi = int(vf)
            u2 = ui+1       # coords of pixel to top right
            v2 = vi+1
            mu = uf-ui      # fraction of way across pixel
            nu = vf-vi

            # Pixel values of four corners
            A = img_in[vi % inSize[0], ui % inSize[1]]
            B = img_in[vi % inSize[0], u2 % inSize[1]]
            C = img_in[v2 % inSize[0], ui % inSize[1]]
            D = img_in[v2 % inSize[0], u2 % inSize[1]]

            # interpolate
            (r,g,b) = (
                A[0]*(1-mu)*(1-nu) + B[0]*(mu)*(1-nu) + C[0]*(1-mu)*nu+D[0]*mu*nu,
                A[1]*(1-mu)*(1-nu) + B[1]*(mu)*(1-nu) + C[1]*(1-mu)*nu+D[1]*mu*nu,
                A[2]*(1-mu)*(1-nu) + B[2]*(mu)*(1-nu) + C[2]*(1-mu)*nu+D[2]*mu*nu )

            img_out[y_out, x_out] = (int(round(r)), int(round(g)), int(round(b)))

def convert(arg):
    fn = arg[0]
    dist_dir = arg[1]
    h_aov = arg[2]
    v_aov = arg[3]
    z_offset = arg[4]
    direction = arg[5]
    img_in = cv2.imread(fn)
    size_in = img_in.shape[0:2]
    size_out = (int(size_in[0] * v_aov/180), int(size_in[1] * h_aov/360))

    out_fn = os.path.join(dist_dir, os.path.basename(fn))
    img_out = np.zeros((size_out[0], size_out[1], 3))
    convertFace(img_in, img_out, size_in[0]/2, z_offset, direction)
    cv2.imwrite(out_fn, img_out)
    print('save: ' + out_fn)

def run(src_dir, dist_dir, h_aov, v_aov, z_offset, direction, process_num = None):

    if not os.path.exists(dist_dir):
        print('create output dir: {}'.format(dist_dir))
        os.mkdir(dist_dir)

    con_args = [[os.path.join(src_dir, i), dist_dir, h_aov, v_aov, z_offset, direction] for i in os.listdir(src_dir) if re.search(r'(jpg|JPG|png|PNG)', i)]
    # con_args = con_args[:1]

    if not os.path.isdir(dist_dir):
        os.makedirs(dist_dir)

    if process_num is None:
        for con_arg in con_args:
            convert(con_arg)
    else:
        p = Pool(process_num)
        p.map_async(convert, con_args).get(9999999)
        p.close()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Convert panorama images to cube perspective images')
    parser.add_argument('src_dir', help='path to panorama images dir')
    parser.add_argument('dist_dir', help='path to panorama images dir')
    parser.add_argument('-w', '--h_aov', default=67.3802, nargs='?', type=float, help='horizontal angle of view')
    parser.add_argument('-v', '--v_aov', default=47.925, nargs='?', type=float, help='vertical angle of view')
    parser.add_argument('-z', '--z_offset', default=-0.25, nargs='?', type=float, help='z offset')
    parser.add_argument('-p', '--process', default=None, nargs='?', type=int, help='process num')
    parser.add_argument('-d', '--direction', default=0, nargs='?', type=int, help='crop direction(0(default): front, 1: back)')
    args = parser.parse_args()
    run(args.src_dir, args.dist_dir, args.h_aov, args.v_aov, args.z_offset, args.direction, process_num=args.process)

