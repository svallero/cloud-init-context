#part-handler
# vi: syntax=python ts=4

# Contact: svallero@to.infn.it
import subprocess
from subprocess import Popen, PIPE
import shlex
import cloudinit.util as util
try:
  import cloudinit.CloudConfig as cc
except ImportError:
  import cloudinit.config as cc
except:
  print "ERROR: there is something wrong with this module installation. Please verify and rerun!"
  import sys
  sys.exit(0)

import platform
import urllib
import sys
import os
import urllib2

# Define logfile
logname = '/var/log/cloud-init-sharedsw.log'
#logname = '/tmp/cloud-init-sharedsw.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/sharedsw-config"])

########################

def install_lustre(repo,client,modules):
  logger.info('entering shared-software installation...')  

  # client and module package url
  logger.info('download Lustre kernel-specific client and modules...')
  client_rpm_url = 'http://'+repo+'/'+client+''
  modules_rpm_url = 'http://'+repo+'/'+modules+''
  # downloading rpms file to /tmp
  try:
    cmd = ('wget --no-check-certificate -O /tmp/client.rpm '+client_rpm_url+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not retrieve package '+client_rpm_url+'!')
    return
  try:
    cmd = ('wget --no-check-certificate -O /tmp/modules.rpm '+modules_rpm_url+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not retrieve package '+modules_rpm_url+'!')
    return
  

  # Install packages
  try:
    cmd = ('yum --nogpgcheck -y localinstall /tmp/client.rpm /tmp/modules.rpm') 
    DPopen(shlex.split(cmd),'False')
  except:
    logger.error('Lustre installation from the yum repository has failed!')
    return

########################

def handle_part(data,ctype,filename,payload):

  # data: the cloudinit object
  # ctype: '__begin__', '__end__', or the specific mime-type of the part
  # filename: the filename for the part, or dynamically generated part if
  #           no filename is given attribute is present
  # payload: the content of the part (empty for begin or end)
  
  if ctype == "__begin__":
     #print "my handler is beginning"
     return
  if ctype == "__end__":
     #print "my handler is ending"
     return

  logger.info('==== received ctype=%s filename=%s ====' % (ctype,filename))

  # Payload should be interpreted as yaml since configuration is given in cloud-config format
  cfg = util.load_yaml(payload)
  
  # If there isn't a sharedsw reference in the configuration don't do anything
  if 'sharedsw' not in cfg:
    logger.error('sharedsw configuration was not found!')
    return 
 
  logger.info('ready to setup shared-software area via Lustre')
  sharedsw_cfg = cfg['sharedsw'] 

  # Install lustre modules for specific kernel version
  # ... lustre server needs to be upgraded at some point and all this stuff will get easier...
  
  if 'rpms' in sharedsw_cfg:
     rpms_cfg = sharedsw_cfg['rpms']
     repo = ''
     client = ''
     modules = ''
     if 'repository' in rpms_cfg:
       repo = rpms_cfg['repository']
     else:
       logger.error('no rpm repository specified!')
       return
     if 'client' in rpms_cfg:
       client = rpms_cfg['client']
     else:
       logger.error('no client rpm specified!')
       return
     if 'modules' in rpms_cfg:
       modules = rpms_cfg['modules']
     else:
       logger.error('no modules rpm specified!')
       return

  install_lustre(repo, client, modules)
 
  # Lustre master (IP)
  if 'lustre-master' in sharedsw_cfg:
     lustre_master = sharedsw_cfg['lustre-master']
  else:
    logger.error('no lustre-master specified!')
    return
  # Desired filesystem
  if 'filesystem' in sharedsw_cfg:
     filesystem = sharedsw_cfg['filesystem']
  else:
    logger.error('no filesystem specified!')
    return
  # Desired mount-point 
  if 'mount-point' in sharedsw_cfg:
    mount_point = sharedsw_cfg['mount-point']
  else:
    mount_point = '/opt/exp_software'
  # Write fstab
  logger.info('removing old entry in fstab...')
  # remove old entry 
  try:
    cmd = ('cat /etc/fstab | grep -v "'+lustre_master+'@" >> /etc/fstab.0')  
    DPopen(cmd,'True')
    cmd = ('mv /etc/fstab.0 /etc/fstab')
    DPopen(cmd, 'True')
    #os.system('cat /etc/fstab | grep -v "'+lustre_master+'@" >> /etc/fstab.0')  
    #os.system('mv /etc/fstab.0 /etc/fstab')
  except:
    logger.error('could not remove old entry in fstab!') 
  # new entry
  try:
    logger.info('adding new entry in fstab...')
    #cmd = ('echo "'+lustre_master+'@tcp0:/'+filesystem+' '+mount_point+' lustre defaults,localflock,_netdev 0 0" >> /etc/fstab')
    cmd = ('echo "'+lustre_master+'@tcp0:/'+filesystem+' '+mount_point+' lustre defaults,localflock,_netdev,user_xattr 0 0" >> /etc/fstab')
    DPopen(cmd,'True')
    #os.system('echo "'+lustre_master+'@tcp0:/expsoft '+mount_point+' lustre defaults,localflock,_netdev 0 0" >> /etc/fstab')
  except:
    logger.error('could not add new entry in fstab!') 
  # now mount
  logger.info('mounting shared-software area...')
  try:
    cmd = ('mkdir -p '+mount_point+'')
    DPopen(shlex.split(cmd), 'False')
    cmd = ('mount '+mount_point+'')
    DPopen(shlex.split(cmd), 'False')
  except:
     logger.error('could not mount shared-software area!')
     return

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
