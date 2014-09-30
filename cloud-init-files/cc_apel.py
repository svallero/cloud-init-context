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

# Define logfile
logname = '/var/log/cloud-init-apel.log'
#logname = '/tmp/cloud-init-apel.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://one-master.to.infn.it/cloud-init-files/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/apel-config"])

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
  
  # If there isn't an apel reference in the configuration don't do anything
  if 'apel' not in cfg:
     logger.error('apel configuration was not found!')
     return 
 
  logger.info('ready to configure APEL')
  global apel_cfg 
  apel_cfg = cfg['apel'] 
  
  if 'parser.cfg' in apel_cfg:
     os.mkdir('/etc/apel') 
     try:
         val = apel_cfg['parser.cfg']
         get_embedded('parser.cfg', val, '/etc/apel/')
     except:
        logger.error('could not write configuration file!')
        return
  try:
     cmd=('echo "00 19 * * * root /usr/bin/apelparser" > /etc/cron.d/apel')
     DPopen(cmd, 'True')
  except:
     logger.error('could not add apelparser to crontab!')
     return
 
  
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
