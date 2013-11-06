#part-handler
# vi: syntax=python ts=4

# Contact: svallero@to.infn.it

import subprocess
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

# Define logfile
logname = '/var/log/cloud-init-addons.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/addons-config"])

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

  # If there isn't a addons reference in the configuration don't do anything
  if 'addons' not in cfg:
    logger.error('addons configuration was not found!')
    return
  else:
    repos = cfg['addons']
    for repo in repos:
      logger.info('installing packages from repo '+repo+':')
      string = ''
      pkgs = repos[repo]
      for pkg in pkgs:
        string += (''+pkg+'  ')
      logger.info(string)
      try:
        if repo != 'none':
          cmd = ('yum -y install '+string+'')
        else:
          cmd = ('yum -y --enablerepo='+repo+' install '+string+'') 
        DPopen(cmd, 'True')
      except:
        logger.error('error: could not install addons!')

  
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
