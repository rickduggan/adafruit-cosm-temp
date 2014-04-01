#!/bin/bash
# use forever to keep restarting app

# -a = append logs, -f = stream logs to stdout
forever --spinSleepTime=60000 -a -f -l ./adafruit-cosm-temp.log -o ./adafruit-cosm-temp.sys.log -e ./adafruit-cosm-temp.err.log start -c sudo /usr/bin/python ./adafruit-cosm-temp.py
