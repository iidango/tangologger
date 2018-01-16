#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import glob
import csv
import datetime

# IN_CAMERAPOSE_FILENAME = "*_cameraPose.csv"
OUT_CAMERAPOSE_FILENAME = "pose.txt"

# IN_WIFI_FILENAME = "*_wifi.csv"
OUT_WIFI_FILENAME = "wifi.txt"
OUT_WIFI_CSV_FILENAME = "wifi_processed.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="convert data format")
    parser.add_argument("data_dir", help="path to data_dir to be processed")
    parser.add_argument("-p", "--pose_fn", nargs='?', type=str, default='*_cameraPose.csv', help="tango pose file name(defult=*_cameraPose.csv)")
    parser.add_argument("-w", "--wifi_fn", nargs='?', type=str, default='*_wifi.csv', help="wifi file name(defult=*_wifi.csv)")
    parser.add_argument("-u", "--unit", default='sec', nargs="?", help="'sec'(default) or 'nanosec'")
    parser.add_argument("-s", "--sync_wifi", default=True, action="store_false", help="sync wifi timestamp with pose data")
    args = parser.parse_args()

    data_dir = args.data_dir
    sync_wifi = args.sync_wifi
    unit = args.unit
    camerapose_fn = glob.glob(os.path.join(data_dir, args.pose_fn))[0]
    wifi_fn = glob.glob(os.path.join(data_dir, args.wifi_fn))[0]

    # convert tango camera pose data
    print('convert {}'.format(camerapose_fn))
    out_camerapose_fn = os.path.join(data_dir, OUT_CAMERAPOSE_FILENAME)
    with open(camerapose_fn, 'r') as in_f:
        with open(out_camerapose_fn, 'w') as out_f:
            reader = csv.reader(in_f)
            for row in reader:
                if unit == 'sec':
                    timestamp = float(row[0])    # sec
                elif unit == 'nanosec':
                    timestamp = float(timestamp)/(10**9)    # sec to nano sec
                tx = row[1]
                ty = row[2]
                tz = row[3]
                q1 = row[4]
                q2 = row[5]
                q3 = row[6]
                q4 = row[7]
                out_f.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(timestamp, tx, ty, tz, q1, q2, q3, q4))
            if sync_wifi:
                pose_end_t = float(row[0])
    print('save {}'.format(out_camerapose_fn))

    # convert wifi data
    print('convert {}'.format(wifi_fn))
    if sync_wifi:
        with open(wifi_fn, 'r') as in_f:
            reader = csv.reader(in_f)
            wifi_end_t = None
            for row in reader:
                wifi_end_t = float(row[0])
        pw_t_diff = 0.0 if 2000 < datetime.datetime.fromtimestamp(wifi_end_t).year < 2050 else pose_end_t - wifi_end_t

    out_wifi_fn = os.path.join(data_dir, OUT_WIFI_FILENAME)
    out_wifi_csv_fn = os.path.join(data_dir, OUT_WIFI_CSV_FILENAME)
    with open(wifi_fn, 'r') as in_f:
        with open(out_wifi_fn, 'w') as out_f:
            with open(out_wifi_csv_fn, 'w') as out_f_csv:
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
                    if len(ap_dic[bssid]) != 0 and ap_dic[bssid][-1] == timestamp_seen:
                        continue

                    ap_dic[bssid].append(timestamp_seen)
                    if unit == 'sec':
                        timestamp_req = float(timestamp_req) + pw_t_diff
                        timestamp_seen = float(timestamp_seen) + pw_t_diff
                    elif unit == 'nanosec':
                        timestamp_req = (float(timestamp_req) + pw_t_diff)/(10**9)    # sec to nanosec
                        timestamp_seen = (float(timestamp_seen) + pw_t_diff)/(10**9)    # sec to nanosec

                    out_f.write('{}\t{}\t{}\n'.format(timestamp_seen, bssid, level))
                    out_f_csv.write('{},{},{}\n'.format(timestamp_seen, bssid, level))

    print('save {}'.format(out_wifi_fn))
    print('save {}'.format(out_wifi_csv_fn))
