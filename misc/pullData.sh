#! /bin/bash

adb pull /sdcard/tangoLogger/$1_android.sensor.accelerometer.csv
adb pull /sdcard/tangoLogger/$1_android.sensor.gyroscope.csv
adb pull /sdcard/tangoLogger/$1_android.sensor.magnetic_field.csv
adb pull /sdcard/tangoLogger/$1_android.sensor.pressure.csv
adb pull /sdcard/tangoLogger/$1_cameraPose.csv
adb pull /sdcard/tangoLogger/$1_wifi.csv
adb pull /sdcard/tangoLogger/$1_gpsLocation.csv
