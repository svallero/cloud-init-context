#!/bin/sh

jobs=`qstat  | cut -f1 -d " " | grep '^[0-9]'`


for job in ${jobs}			# Set up a loop control

do					# Begin the loop
    
#    echo "${job}"	                 # Display the result
    state=`qstat -f ${job} | grep "job_state"`
    coda=`qstat -f ${job} | grep "queue "`
    prio=`checkjob -v ${job} | grep Prio`
    echo -e "${job} ${coda} \t${state} ${prio}"

done				  	 # End of lo 
