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
  print "There is something wrong with this module installation. Please verify and rerun."
  import sys
  sys.exit(0)

import platform
import urllib
import sys
import os
import yaml    
import ntpath
import urllib2
# Define global variables
puppetconfig_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-puppetconfig.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/puppetconfig-config"])

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
  
  # If there isn't a puppetconfig reference in the configuration don't do anything
  if 'puppetconfig' not in cfg:
    logger.error('puppetconfig configuration was not found!')
    return 
 
  logger.info('ready to configure puppet')
  global puppetconfig_cfg
  puppetconfig_cfg = cfg['puppetconfig'] 

  
  logger.info('installing puppet...')
  try:
    cmd = ('yum -y --enablerepo=epel install puppet')
    DPopen(shlex.split(cmd), 'False') 
  except:
    logger.error('could not install puppet!')
    return 

  logger.info('removing old puppet keys...')
  try:
    cmd = ('rm -rf /var/lib/puppet/ssl') 
    DPopen(cmd, 'True')
  except:
    logger.error('could not remove old puppet keys!')
    return

  logger.info('retrieving the key to perform remote clean-up...')
  filename = 'puppetremote-rsa'  
  for block in puppetconfig_cfg:
    if block != 'se' and block != 'options':
      val = puppetconfig_cfg[block]
      get_embedded(block, val, '/tmp') 
      cmd = ('chmod 0400 /tmp/'+block+'')
      DPopen(cmd, 'True')

  logger.info('performing remote cleanup...')
  # the remote machine should be configured to bind the
  # corresponding public key to a command that cleans up the machine from the
  # Puppet certificates list
  if 'se' in puppetconfig_cfg:
    se = puppetconfig_cfg['se']
  else:
    logger.error('SE not specified!')
    return
  try:
    cmd = ('ssh puppetremote@'+se+' -i /tmp/'+filename+' -o StrictHostKeyChecking=yes')  
    DPopen(cmd, 'True')
    cmd = ('rm -f /tmp/'+filename+'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not perform remote cleanup!')  

  logger.info('configuring Puppet...')
  if 'options' in puppetconfig_cfg:
    options = puppetconfig_cfg['options']
    string = ''
    for opt in options:
      string += ''.join((' --', opt))
  else:
    logger.error('options not specified!')
    return

  # for sandbox test
  #return
   
  try:
    cmd = ('puppet agent '+string+'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not configure Puppet!')

  logger.info('starting Puppet...')
  try:
    cmd = ('service puppet start')
    DPopen(cmd, 'True')
  except:
    logger.error('could not start Puppet!') 
   
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
