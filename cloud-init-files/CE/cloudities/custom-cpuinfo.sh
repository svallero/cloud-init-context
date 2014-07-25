#!/bin/bash

#
# custom-cpuinfo.sh -- by Dario Berzano <dario.berzano@cern.ch>
#
# Creates a customized /proc/cpuinfo with the specified number of cores for the VM
# based on the actual /proc/cpuinfo from the current machine (hypervisor).
#

# File to read information from
Cpuinfo=/proc/cpuinfo

# Fields of cpuinfo to consider (others will be discarded)
ValidFields=(
  'vendor_id' 'cpu_family' 'model' 'model name' 'stepping' 'cpu MHz'
  'cache size' 'fpu' 'fpu_exception' 'wp' 'flags' 'bogomips' 'TLB size'
  'clflush size' 'cache_alignment' 'address sizes' 'power management'
)

# Temporary VM cpuinfo for one core (to repeat)
Temp=`mktemp /tmp/cpuinfo-XXXXX`

# Assemble temporary file be repeated: read cpuinfo for the first core only and
# consider only valid fields
cat "$Cpuinfo" | while read Line ; do
  [ "$Line" == '' ] && break

  Field=`echo $Line | cut -d: -f1`
  Field=`echo $Field`

  for ((i=0 ; i < ${#ValidFields[@]} ; i++)) ; do
    if [ "$Field" == "${ValidFields[$i]}" ] ; then
      echo "$Line" >> $Temp
    fi
  done

done

# Number of virtual cores
NVcpus=$1

# Output on stdout the new cpuinfo
for ((i=0 ; i < NVcpus ; i++)) ; do
  echo -e "processor\t: $i"
  cat $Temp
  echo ''
done

# Remove temporary file
rm -f $Temp
