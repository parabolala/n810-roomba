#!/bin/sh
IP_ADDR=$(ifconfig wlan0 | grep inet| cut -d":" -f2 | cut -d" " -f1)

python n810roomba/testserver.py -H $IP_ADDR
