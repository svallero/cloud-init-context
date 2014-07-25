#!/bin/bash

FILE=`/sbin/sysctl fs.file-nr`
NOW=`/bin/date`

echo -n "${NOW} " 
echo ${FILE}

