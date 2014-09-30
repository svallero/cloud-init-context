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
import ntpath

# Define logfile
logname = '/var/log/cloud-init-igiinstall.log'
#logname = './cloud-init-igiinstall.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://one-master.to.infn.it/cloud-init-files/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/igiinstall-config"])

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
  
  # If there isn't a igiyaim reference in the configuration don't do anything
  if 'igiinstall' not in cfg:
    logger.error('igiinstall configuration was not found!')
    return 
 
  logger.info('ready to install igi software')
  igiinstall_cfg = cfg['igiinstall'] 

  logger.info('installing Igi repos...')
  
  # define some default
  # ...
  cmd = ('yum clean all')                             
  DPopen(cmd, 'True') 
  if 'repos' in igiinstall_cfg:
    repos = igiinstall_cfg['repos']
    for rep in repos:
      if '.rpm' in rep:
        try:
          cmd = ('yum -y install '+rep+'')
          DPopen(shlex.split(cmd), 'False') 
        except:
          logger.error('could not install repo '+rep+'!')
          return 
      elif '.repo' in rep:
        try:
          head, tail = ntpath.split(rep)
          cmd = ('wget -O /etc/yum.repos.d/'+tail+' '+rep+'')
          DPopen(shlex.split(cmd), 'False') 
        except:
          logger.error('could not install repo '+rep+'!')
          return 
      else:
        logger.error('unknown repo type, expected .rpm or .repo!')
         
  # Install some base package
  #logger.info('installing some yum addon...')
  #try:
  #  cmd = ('yum -y install yum-priorities yum-protectbase epel-release')
  #  DPopen(shlex.split(cmd), 'False')
  #except:
  #  logger.error('could not install yum addons!')
  #  return

  # Install custom packages 
  logger.info('installing custom packages...')
  if 'packages' in igiinstall_cfg:
    packages = igiinstall_cfg['packages']
    for pack in packages:
      try:
        #if 'igi-wn' in pack:
        cmd = ('yum -y --enablerepo=epel install '+pack+'')
        DPopen(shlex.split(cmd), 'False')
        #else:
        #  cmd = ('yum -y install '+pack+'')
        if 'java' in pack:
          try:
            javaname = pack.replace('java','jre')
            #cmd = ('echo "export JAVA_HOME=/usr/lib/jvm/'+javaname+'" > /tmp/je.sh')
            #DPopen(cmd, 'True')
            os.environ["JAVA_HOME"] = '/usr/lib/jvm/'+javaname+''
          except:  
            logger.error('could not export java path!') 
            return
      except:
        logger.error('could not install package '+pack+'')
        return 
   
  # Clean yum cache
  logger.info('cleaning-up yum cache...')
  os.system('yum clean all')  


  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
