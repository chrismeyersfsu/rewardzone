#!/bin/bash
forever start -o out.log -e err.log -c ./venv.sh rewardzone.py
