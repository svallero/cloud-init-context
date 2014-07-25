#!/usr/bin/python

# Contact: svallero@to.infn.it

import os
import urllib2
from datetime import datetime

logname = '/var/log/cloud-timings.log'
#logname = './cloud-timings.log'
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

def get_timediff_total(filename):
  file=open(filename)
  lines=file.readlines() 
  first=str(lines[0])
  # sometimes first line does not start  with datetime
  if '[CLOUDINIT]' not in first:
    first=str(lines[1])
  start=str(first).split(' ', 3)[2]
  for line in lines: #fa veramente schifo...
    last = line
  stop=str(last).split(' ', 3)[2]
  start=datetime.strptime(start, "%H:%M:%S")
  stop=datetime.strptime(stop, "%H:%M:%S")
  diff = stop-start
  return diff

def get_timediff_modules(filename):
  file=open(filename)
  first=file.readline()
  start=str(first).split(' ', 2)[1]
  for line in file.readlines(): #fa veramente schifo...
    last = line
  stop=str(last).split(' ', 2)[1]
  start=datetime.strptime(start, "%H:%M:%S")
  stop=datetime.strptime(stop, "%H:%M:%S")
  diff = stop-start
  return diff

# Main
logger.info('****************************************')
logger.info('MODULES TIMING:')
logger.info('****************************************')
sum_time=datetime.strptime('00:00:00', "%H:%M:%S")
files=os.popen('ls /var/log/cloud-init-*').read()
#files=os.popen('ls ./tmp/cloud-init*').read()
for file in files.splitlines(): 
   # write stuff only if file is not empty
   if (os.stat(file).st_size != 0):
     if 'cloud-init.log' in file: # this is excluded for the time being 
       tot_time=get_timediff_total(file)
     else:
       time=get_timediff_modules(file)
       sum_time += time
       logger.info('TIME: '+str(time)+' from '+file+'')
       
logger.info('****************************************')
logger.info('SUM OF MODULES TIMING: '+str(sum_time.time())+'')
logger.info('****************************************')
#logger.info('****************************************')
#logger.info('TOTAL CONTEXT TIME: '+str(tot_time)+'')
#logger.info('****************************************')
print ('Summary written in '+logname+'')
