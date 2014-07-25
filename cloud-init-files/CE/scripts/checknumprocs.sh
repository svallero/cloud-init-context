#!/bin/bash

date +%T-%F

/usr/sbin/lsof | awk -f /root/scripts/lookatprocnum.awk | sort -k 1n

echo "------------------------------------------------------------------"
