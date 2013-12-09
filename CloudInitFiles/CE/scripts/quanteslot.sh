#!/bin/bash

nodi=`pbsnodes -a | awk '/^t2/'`

tot=0

for nodo in ${nodi}                     # Set up a loop control

do                                      # Begin the loop
    
    echo -n "${nodo}"                    
    slot=`pbsnodes ${nodo} | grep "np ="`
    slot=`echo ${slot}  | sed 's/np = //g'`
   RET=`pbsnodes ${nodo} | grep "state =" |sed 's/state =//'| sed 's/ //g'`
   if `echo ${RET} | grep "down" 1>/dev/null 2>&1`
   then
      echo  " DOWN" 
   elif `echo ${RET} | grep "offline" 1>/dev/null 2>&1`
   then
      echo " OFFLINE"
   elif `echo ${RET} | grep "free" 1>/dev/null 2>&1` 
   then
       echo  " FREE"
       tot=`expr ${tot} + ${slot}`
   elif `echo ${RET} | grep "busy" 1>/dev/null 2>&1`
   then
       echo  " BUSY"
       tot=`expr ${tot} + ${slot}`
   elif `echo ${RET} | grep "job-exclusive" 1>/dev/null 2>&1`
   then 
        echo  " JOB-EXCLUSIVE"
        tot=`expr ${tot} + ${slot}`
   fi

done                              
echo "${tot}"
