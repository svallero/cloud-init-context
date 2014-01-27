#cloud-boothook
#!/usr/bin/python
# vim: syntax=python

# Contact: svallero@to.infn.it
 
import os
import urllib2
from subprocess import Popen,PIPE

# Define logfile
logname = '/var/log/cloud-init-preconfig.log'
#logname = '/tmp/cloud-init-preconfig.log'
# Import script with definition of logger and some useful function 
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
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

# Keep system up to date
#logger.info('running yum update...')
#try:
#   cmd = ('yum -y update')
#   DPopen(cmd, 'True')
#except:
#   logger.error('could not update yum!') 

# Installing some package
logger.info('installing basic tools...')
try:
   cmd = ('yum -y install lvm2 xfsprogs yum-priorities yum-protectbase epel-release ruby')
   DPopen(cmd, 'True')
except:
   logger.error('could not install basic tools!')

logger.info('cleaning-up yum cache...')
cmd = ('yum clean all')
DPopen(cmd, 'True')

# Off iptables and selinux
logger.info('stopping iptables...')
try:
   cmd = ('/sbin/service iptables stop')
   DPopen(cmd, 'True')
except:
   logger.error('could not stop iptables!')

logger.info('chkconfig iptables off...')
try:
    cmd = ('/sbin/chkconfig iptables off')
    DPopen(cmd, 'True')
except:
    logger.error('could not chkconfig iptables off!')

logger.info('stopping selinux...')
try:
    cmd = ('/usr/sbin/setenforce 0')
    DPopen(shlex.split(cmd), 'False')
except:
    logger.error('failed to stop selinux!')

#logger.info('removing ssh keys and restarting sshd daemon...')
#try:
#    cmd = ('rm -f /etc/ssh/ssh*key*')
#    DPopen(cmd, 'True')
#except:
#    logger.error('could not remove /etc/ssh/ssh*key*!')
#

logger.info('running cloud-init ssh module...')
try:
   cmd = ('cloud-init single --name ssh')
   DPopen(cmd, 'True')
except:
   logger.error('failed to run ssh module!')

logger.info('starting sshd service...')
try:
    cmd = ('service sshd start')
    DPopen(cmd, 'True')
except:
    logger.error('could not start sshd!')

