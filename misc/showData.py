#!/usr/bin/env python
# -*- coding: utf-8 -*-

import matplotlib
import pandas
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
import folium

# read data
# data_root = "/Users/iida/Documents/naviMap/data/tango/test/201706151250"
data_root = sys.argv[1]
acc_fp = data_root + "_android.sensor.accelerometer.csv"
gyro_fp = data_root + "_android.sensor.gyroscope.csv"
mag_fp = data_root + "_android.sensor.magnetic_field.csv"
camera_fp = data_root + "_cameraPose.csv"
gps_fp = data_root + "_gpsLocation.csv"

acc_data = np.loadtxt(acc_fp, delimiter=',',  skiprows=1)
gyro_data = np.loadtxt(gyro_fp, delimiter=',',  skiprows=1)
mag_data = np.loadtxt(mag_fp, delimiter=',',  skiprows=1)
camera_data = np.loadtxt(camera_fp, delimiter=',',  skiprows=1)

# plot acc
acc_df = pandas.DataFrame(acc_data[:, 1:],
               columns=['x','y','z'],
               index=acc_data[:,0])
sen_fig = plt.figure(figsize=(15,5))
sen_ax = sen_fig.add_subplot(311)

sen_ax.plot(acc_df.index, acc_df["x"])
sen_ax.plot(acc_df.index, acc_df["y"])
sen_ax.plot(acc_df.index, acc_df["z"])

# plot gyro
gyro_df = pandas.DataFrame(gyro_data[:, 1:],
               columns=['x','y','z'],
               index=gyro_data[:,0])
sen_ax = sen_fig.add_subplot(312)

sen_ax.plot(gyro_df.index, gyro_df["x"])
sen_ax.plot(gyro_df.index, gyro_df["y"])
sen_ax.plot(gyro_df.index, gyro_df["z"])

# plot mag
mag_df = pandas.DataFrame(mag_data[:, 1:],
               columns=['x','y','z'],
               index=mag_data[:,0])
sen_ax = sen_fig.add_subplot(313)

sen_ax.plot(mag_df.index, mag_df["x"])
sen_ax.plot(mag_df.index, mag_df["y"])
sen_ax.plot(mag_df.index, mag_df["z"])

# plot drift correction camera pose
camera_df = pandas.DataFrame(camera_data[:, 1:4],
               columns=['x','y','z'],
               index=camera_data[:,0])

c_fig = plt.figure()
c_ax = Axes3D(c_fig)

c_ax.plot3D(camera_data[:, 1], camera_data[:, 2], camera_data[:, 3])
c_ax.scatter3D(camera_data[0, 1], camera_data[0, 2], camera_data[0, 3], c='red')
c_ax.scatter3D(camera_data[-1, 1], camera_data[-1, 2], camera_data[-1, 3], c='blue')

plt.show()

# gps data
print("loading gps file: " + gps_fp)
with open(gps_fp) as f:
    lines = f.readlines()

map_osm = folium.Map(location=[35.155, 136.965], zoom_start=16)
for l in lines:
    d = l.split(",")
    folium.CircleMarker(location=[float(d[2]), float(d[1])], radius=1,
                    popup='Laurelhurst Park', color='#3186cc',
                    fill_color='#3186cc').add_to(map_osm)

map_osm.save(outfile=data_root + "_gps.html")
print("out put gps plot result to " + data_root + "_gps.html")
