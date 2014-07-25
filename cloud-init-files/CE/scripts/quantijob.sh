#!/bin/bash

nodi=`pbsnodes -a | awk '/^t2/'`

queued=`qstat -1n | grep "Q " | wc -l`

tot=0


for nodo in ${nodi}			# Set up a loop control

do					# Begin the loop
    
    echo -n "${nodo} "	                 
    slot=`pbsnodes ${nodo} | grep "np ="`
    slot=`echo ${slot}  | sed 's/np = //g'`
    RET=`pbsnodes ${nodo} | grep "state =" |sed 's/state =//'| sed 's/ //g'`
    nodo=`echo ${nodo}  | sed 's/.to.infn.it//g'`
    running=`qstat -1n | grep R | grep ${nodo} | wc -l`
    if `echo ${RET} | grep "down" 1>/dev/null 2>&1`
    then
    #  echo  " DOWN" 
      for (( c=1; c<=${slot}; c++ )) do echo -n "x"; done;
   
    elif `echo ${RET} | grep "offline" 1>/dev/null 2>&1`
    then
    #  echo " OFFLINE"
      for (( c=1; c<=${slot}; c++ )) do echo -n "o"; done;

    elif `echo ${RET} | grep "free" 1>/dev/null 2>&1` 
    then
    #   echo  " FREE"
       tot=`expr ${tot} + ${slot}`
       for (( c=1; c<=${slot}; c++ )) do echo -n "-"; done;

    elif `echo ${RET} | grep "busy" 1>/dev/null 2>&1`
    then
    #   echo  " BUSY"
       tot=`expr ${tot} + ${slot}`
       for (( c=1; c<=${slot}; c++ )) do echo -n "-"; done;

    elif `echo ${RET} | grep "job-exclusive" 1>/dev/null 2>&1`
    then 
    #    echo  " JOB-EXCLUSIVE"
        tot=`expr ${tot} + ${slot}`
        for (( c=1; c<=${slot}; c++ )) do echo -n "-"; done;
 
    fi
    echo -n "|"
    for (( c=1; c<=${running}; c++ )) do echo -n "-"; done; 
    echo " " 
    totslot=`expr ${totslot} + ${slot}`
    totjobs=`expr ${totjobs} + ${running}`

done				  
echo "           Slot ${totslot}/${tot} | running ${totjobs}   ${queued} queued"
