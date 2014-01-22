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
import urllib2 
import ntpath

# Define global variables
certificate_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-certificate.log'
#logname = '/tmp/cloud-init-certificate.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/certificate-config"])

#######################

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
  
  # If there isn't a certificate reference in the configuration don't do anything
  if 'certificate' not in cfg:
    logger.error('certificate configuration was not found!')
    return 
 
  logger.info('ready to configure host certificate')
  certificate_cfg = cfg['certificate'] 

  # configure hostname if specified
  if 'name' in certificate_cfg:
     logger.info('configuring the hostname...')
     name = certificate_cfg['name']
  
     try:
       cmd = ('hostname '+name+'') 
       DPopen(cmd, 'True')
     except:
       logger.error('could not configure the hostname!')
       return

  logger.info('copying the "certificate" files...')
 
  logger.info('creating dir /etc/grid-security...')
  try: 
    cmd = ('mkdir -p /etc/grid-security') 
    DPopen(cmd, 'True')
  except:
    logger.error('could not create dir!')
    return 
  for block in certificate_cfg:
    if block != 'repo' and block != 'name':
      val = certificate_cfg[block]
      get_embedded(block, val, '/etc/grid-security/')
      logger.info('changing permissions...')
      if ('cert' in block):
         try:
            cmd = ('mv /etc/grid-security/'+block+' /etc/grid-security/hostcert.pem')
            DPopen(cmd, 'True')
         except:
            logger.error('could not rename '+block+' in hostcert.pem!')
            return
         block = 'hostcert.pem' 
         perm = 644
      elif ('key' in block):
         try:
            cmd = ('mv /etc/grid-security/'+block+' /etc/grid-security/hostkey.pem')
            DPopen(cmd, 'True')
         except:
            logger.error('could not rename '+block+' in hostkey.pem!')
            return
         block = 'hostkey.pem' 
         perm = 400
      try:
         cmd = ('chmod '+str(perm)+' /etc/grid-security/'+block+'')
         DPopen(cmd, 'True')
      except:
         logger.error('failed to change file permissions!')       

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
