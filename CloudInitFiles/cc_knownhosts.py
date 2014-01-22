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
knownhosts_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-knownhosts.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/knownhosts-config"])

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
  
  # If there isn't a knownhosts reference in the configuration don't do anything
  if 'knownhosts' not in cfg:
    logger.error('knownhosts configuration was not found!')
    return 
 
  logger.info('ready to configure ssh known hosts')
  knownhosts_cfg = cfg['knownhosts'] 

  logger.info('copying the "ssh_known_hosts" file...')
  
  for block in knownhosts_cfg:
    if block != 'repo':
      val = knownhosts_cfg[block]
      get_embedded(block, val, '/etc/ssh/')
         
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
