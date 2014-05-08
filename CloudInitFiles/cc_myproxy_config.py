#part-handler
# vi: syntax=python ts=4

# Contact: svallero@to.infn.it

import commands
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

# Define global because needed in different functions
myproxy_config_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-myproxy_config.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/myproxy_config-config"])

########################


def handle_part(data,ctype,filename,payload):

  # data: the cloudinit object
  # ctype: '__begin__', '__end__', or the specific mime-type of the part
  # filename: the filename for the part, or dynamically generated part if
  #           no filename is given attribute is present
  # payload: the content of the part (empty for begin or end)
  
  if ctype == "__begin__":
     return
  if ctype == "__end__":
     return

  logger.info('==== received ctype=%s filename=%s ====' % (ctype,filename))

  # Payload should be interpreted as yaml since configuration is given in cloud-config format
  cfg = util.load_yaml(payload)
  
  # If there isn't a myproxy_config reference in the configuration don't do anything
  if 'myproxy_config' not in cfg:
     logger.error('myproxy_config configuration was not found!')
     return 
 
  logger.info('ready to configure PX')
  global myproxy_config_cfg 
  myproxy_config_cfg = cfg['myproxy_config'] 
  
  logger.info('Copying certificate to /etc/grid-security/myproxy...')
  try:
     md = ('mkdir /etc/grid-security/myproxy/')
     DPopen(cmd, 'True')
  except:
     logger.error('could not create /etc/grid-security/myproxy!')
     return
  for item in ['hostcert.pem','hostkey.pem']:
     try:
        cmd = ('cp /etc/grid-security/'+item+' /etc/grid-security/myproxy/')
        DPopen(cmd, 'True')
     except:
        logger.error('could not copy '+item+'!')
        return
     try:
        cmd = ('chown myproxy:myproxy /etc/grid-security/myproxy/'+item+'')
        DPopen(cmd, 'True')
     except:
        logger.error('could change ownership of '+item+'!')
        return


  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
