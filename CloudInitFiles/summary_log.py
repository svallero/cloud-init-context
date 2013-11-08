#!/usr/bin/python
import os
import urllib2

# Write below list of strings to be ignored
exceptions = ['The munge key file /etc/munge/munge.key is not found']

logname = '/var/log/cloud-summary.log'
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

print 'Scanning for ERRORs in custom part-handler log-files...'
files=os.popen('ls /var/log/cloud-init-*').read()
for file in files.splitlines(): 
   errors = False 
   # write stuff only if file is not empty
   if (os.stat(file).st_size != 0):
     fh = open(file)
     for line in fh:
       if 'ERROR' in line:
         if not any(e in line for e in exceptions):
           logger.error(file)
           errors  = True
           break 
         else:
           # in case of the munge.key error I want to skip also the following
           # line, but need to check if it's ok also in case of other exceptions
           line = fh.next()       
           
     if not errors:
       logger.log(14,file)   
print ('Summary written in '+logname+'')
