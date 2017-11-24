#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import sys
import math
import os

def calcStraightDistance(f):
    data = np.loadtxt(f, delimiter=',')
    dist = math.sqrt((data[0,1]-data[-1,1])**2 + (data[0, 2]-data[-1,2])**2 + (data[0, 3]-data[-1,3])**2)
    return dist

fs = [i for i in os.listdir(sys.argv[1]) if "dcCameraPose.csv" in i]

dist_sum = 0.
count = 0
for f in fs:
    abs_error = abs(30. - calcStraightDistance(f))
    print("{}: {}".format(f, abs_error))
    dist_sum += abs_error
    count += 1
print("sum    : {}".format(dist_sum))
print("count  : {}".format(count))
print("average: {}".format(dist_sum/count))
