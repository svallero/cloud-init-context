#!/bin/bash

for ora in {0..47}                     # Set up a loop control
do         
echo -n "${ora} "
running=`qstat -1n | grep "R ${ora}"|wc| awk '{print $1}'`
#echo "running ${running}"
echo -n "|"
for (( c=1; c<=${running}; c++ )) do echo -n "-"; done;
echo
done
