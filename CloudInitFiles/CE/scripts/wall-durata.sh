#!/bin/bash

for ora in {00..71}                     # Set up a loop control
do         
dora=`printf "%02d" ${ora}`
echo -n "${dora} "
running=`qstat -f | grep resources_used.walltime | grep " ${dora}:" |wc| awk '{print $1}'` 
#echo "running ${running}"
echo -n "|"
for (( c=1; c<=${running}; c++ )) do echo -n "-"; done;
echo
done
