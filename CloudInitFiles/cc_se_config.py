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
se_config_cfg = 0
rootdir = '/root/scripts'

# Define logfile
logname = '/var/log/cloud-init-se_config.log'
#logname = '/tmp/cloud-init-se_config.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/se_config-config"])

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
  
  # If there isn't a se_config reference in the configuration don't do anything
  if 'se_config' not in cfg:
     logger.error('se_config configuration was not found!')
     return 
 
  logger.info('ready to configure SE')
  global se_config_cfg 
  se_config_cfg = cfg['se_config'] 
  
  if 'name' in se_config_cfg:
     name = se_config_cfg['name']
     logger.info('configuring SE: '+name+'')
  else:
     logger.error('SE name not specified!')
     return 

  logger.info('linking to proper mysql-connector-java.jar')
  if 'javamc' in se_config_cfg:
     javamc = se_config_cfg['javamc']
  else:
     javamc = 'mysql-connector-java-5.1.17.jar'
  try:
    cmd = ('rm -f /usr/share/java/storm-backend-server/mysql-connector-java-*.jar')  
    DPopen(cmd, 'True')
  except:
    logger.error('could not remove /usr/share/java/storm-backend-server/mysql-connector-java-*.jar')
    return
  try:
    cmd = ('ln -s /usr/share/java/'+javamc+' /usr/share/java/storm-backend-server/'+javamc+'') 
    DPopen(cmd, 'True')
  except:
    logger.error('could not link /usr/share/java/'+javamc+' to /usr/share/java/storm-backend-server/!')
    return

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
