#cloud-boothook
#!/usr/bin/python
# vim: syntax=python

# Contact: svallero@to.infn.it
 
import os
import urllib2
from subprocess import Popen,PIPE

# Define logfile
logname = '/var/log/cloud-init-preconfig.log'
# Import script with definition of logger and some useful function 
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

# Set proxy for yum
proxy='https://proxy2.to.infn.it:3128'
filename = '/etc/yum.conf' 
file = open(filename) 
if 'proxy' not in file:
  logger.info('adding proxy to yum configuration...')
  try:
    # write yum.conf
    cmd = ('echo "proxy='+proxy+'" >> '+filename+'')
    DPopen(cmd,'True')
    # global setting
    cmd = ('export https_proxy='+proxy+'')
    DPopen(cmd,'True')
  except:
    logger.error('could not patch '+filename+'!')
