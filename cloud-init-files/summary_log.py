#!/usr/bin/python

# Contact: svallero@to.infn.it

import os
import urllib2
import socket

# Write below list of strings to be ignored
# Capire come mai e cercare di eliminare gli errori TODO
#exceptions = ['The munge key file /etc/munge/munge.key is not found','install ig-vomscerts-all\' returned 1', 'File[zabbix_agentd_conf]/ensure: change from absent to file failed', 'install lcg-vomscerts-desy\' returned 1','Could not request certificate: execution expired']
exceptions = ['The munge key file /etc/munge/munge.key is not found','install ig-vomscerts-all\' returned 1', 'File[zabbix_agentd_conf]/ensure: change from absent to file failed', 'install lcg-vomscerts-desy\' returned 1']

logname = '/var/log/cloud-summary.log'
#logname = './cloud-summary.log'
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

print 'Scanning for ERRORs in custom part-handler log-files...'

logger.info('************************************************')
logger.info('In case of errors in "cloud-init-puppetconfig.log" also grep for "merr"!') 
logger.info('In case of errors in "cloud-init-igiyaim.log" also grep for "errno"!') 
logger.info('************************************************')

goodnode=True

files=os.popen('ls -rt /var/log/cloud-init-*').read()
service=False
for file in files.splitlines(): 
   if 'cloud-init-output.log' in file:
     break
   hostname = socket.gethostname()
   if ('t2-ce-01' in hostname or 'se-srm-00' in hostname):
      service = True
   elif (not os.path.getsize('/var/log/cloud-init-grid_config.log')):
      # this is in case we are creating the EWN base image
      service = True
   errors = False 
   # write stuff only if file is not empty
   if (os.stat(file).st_size != 0):
     fh = open(file)
     skip = False
     for line in fh:
       if skip:
          line = fh.next()       
       skip = False 
       if 'ERROR' in line or 'merr' in line or 'errno' in line:
         # 'merr' comes from puppet, for some reason the exception 
         # is not caught by python 
         if not any(e in line for e in exceptions):
           if errors == False:
              logger.error(file)
           errors  = True
           goodnode = False
           break 
         elif 'munge' in line:
           # in case of the munge.key error I want to skip also 
           # the following line
           skip = true  
     # now consider last line
     if 'preconfig' not in file:
        if '==== end ctype' not in line and errors == False:      
           logger.error(file)
           errors  = True
           goodnode = False

     # if no errors write: OK
     if not errors:
       logger.log(14,file)  
  
# put node offline if some error occurred
filename = 'offlinehost-rsa'
if not goodnode and not service: 
#if goodnode: 
   logger.info('*** PUTTING NODE OFFLINE NOW! ***') 
   try:
      ce=open('/var/lib/torque/server_name', 'r').read().strip()
      cmd = ('echo "`hostname -f`" | ssh qmanager@'+ce+' -i /tmp/'+filename+' -o StrictHostKeyChecking=yes')
      DPopen(cmd, 'True')
   except:
      logger.error('could not put node offline!')

cmd = ('rm -f /tmp/'+filename+'')
DPopen(cmd, 'True')

#outf=open(logname)
#outf.write('In case of errors in "cloud-init-puppetconfig.log" also grep for "merr"!') 
#outf.close()
print ('Summary written in '+logname+'')
