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
import yaml
import ntpath
import urllib2

# Define logfile
logname = '/var/log/cloud-init-template.log'
# Import script with definition of logger and some useful function 
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

########################

def list_types():
    # return a list of mime-types that are handled by this module
    return(["text/template-config"])


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
  # If there isn't a template reference in the configuration don't do anything
  if 'template' not in cfg:
    logger.error('template configuration was not found!')
    return
  
  logger.info('ready to setup template...')
  template_cfg = cfg['template']
  logger.info(' configuring template...')

  
  # MY CODE GOES HERE !!!
  # to call a shell command do:
   try:
     cmd = ('ls -l')
     DPopen(shlex.split(cmd),'False')
   except:
     logger.error('could not execute command: '+cmd+'')
   
   # If your command contains a pipe or is quite complex, use:
   DPopen(cmd, 'True')  

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))
