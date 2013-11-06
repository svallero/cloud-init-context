#!/usr/bin/python
import os
import urllib2

logname = '/var/log/cloud-summary.log'
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

print 'Scanning for ERRORs in custom part-handler log-files...'
files=os.popen('ls /var/log/cloud-init-*').read()
for file in files.splitlines(): 
   errors = False 
   # write stuff only if file is not empty
   if (os.stat(file).st_size != 0):
     for line in open(file):
       if 'ERROR' in line:
         logger.error(file)
         errors  = True
         break 
     if not errors:
       logger.log(14,file)   
print ('Summary written in '+logname+'')
