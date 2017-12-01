#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import glob
import csv

# IN_CAMERAPOSE_FILENAME = "*_cameraPose.csv"
OUT_CAMERAPOSE_FILENAME = "pose.txt"

# IN_WIFI_FILENAME = "*_wifi.csv"
OUT_WIFI_FILENAME = "wifi.txt"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="convert data format")
    parser.add_argument("data_dir", help="path to data_dir to be processed")
    parser.add_argument("-p", "--pose_fn", nargs='?', type=str, default='*_cameraPose.csv', help="tango pose file name(defult=*_cameraPose.csv)")
    parser.add_argument("-w", "--wifi_fn", nargs='?', type=str, default='*_wifi.csv', help="wifi file name(defult=*_wifi.csv)")
    args = parser.parse_args()

    data_dir = args.data_dir
    camerapose_fn = glob.glob(os.path.join(data_dir, args.pose_fn))[0]
    wifi_fn = glob.glob(os.path.join(data_dir, args.wifi_fn))[0]

    # convert tango camera pose data
    print('convert {}'.format(camerapose_fn))
    out_camerapose_fn = os.path.join(data_dir, OUT_CAMERAPOSE_FILENAME)
    with open(camerapose_fn, 'r') as in_f:
        with open(out_camerapose_fn, 'w') as out_f:
            reader = csv.reader(in_f)
            for row in reader:
                timestamp = row[0]
                timestamp = float(timestamp)/(10**9)    # sec to nano sec
                tx = row[1]
                ty = row[2]
                tz = row[3]
                q1 = row[4]
                q2 = row[5]
                q3 = row[6]
                q4 = row[7]
                out_f.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(timestamp, tx, ty, tz, q1, q2, q3, q4))
    print('save {}'.format(out_camerapose_fn))

    # convert wifi data
    print('convert {}'.format(wifi_fn))
    out_wifi_fn = os.path.join(data_dir, OUT_WIFI_FILENAME)
    with open(wifi_fn, 'r') as in_f:
        with open(out_wifi_fn, 'w') as out_f:
            reader = csv.reader(in_f)
            ap_dic = {}
            for row in reader:
                timestamp_req = row[0]
                bssid = row[1]
                ssid = row[2]    # not used
                level = row[3]
                timestamp_seen = row[4]

                # skip duplicated scan
                if bssid not in ap_dic:
                    ap_dic[bssid] = []
                    ap_dic[bssid].append(timestamp_seen)
                if ap_dic[bssid][-1] == timestamp_seen:
                    continue

                ap_dic[bssid].append(timestamp_seen)
                # timestamp_seen = float(timestamp_seen)/(10**6)    # sec to microsec

                out_f.write('{}\t{}\t{}\n'.format(timestamp_seen, bssid, level))
    print('save {}'.format(out_wifi_fn))
