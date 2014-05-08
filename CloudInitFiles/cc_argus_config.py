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
argus_config_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-argus_config.log'
#logname = '/tmp/cloud-init-ce_config.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/argus_config-config"])

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
  
  # If there isn't a ce_config reference in the configuration don't do anything
  if 'argus_config' not in cfg:
     logger.error('argus_config configuration was not found!')
     return 
 
  logger.info('ready to configure ARGUS')
  global argus_config_cfg 
  argus_config_cfg = cfg['argus_config'] 
  

  # install fetch-crl
  #logger.info('installing "fetch-crl"')
  #try:
  #   cmd = ('yum -y install fetch-crl')
  #   DPopen(cmd, 'True') 
  #except:
  #   logger.error('could not install "fetch-crl"!')
  #   return
  try:
     logger.info('starting "fetch-crl"...')
     cmd = ('/usr/sbin/fetch-crl')
     DPopen(cmd, 'True') 
  except:
     logger.info('some trouble starting "fetch-crl"!')
  #   return
  try:
     logger.info('chkconfig "fetch-crl-cron" on...')
     cmd = ('/sbin/chkconfig fetch-crl-cron on')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not chkconfig "fetch-crl-cron" on!')
     return
  try:
     logger.info('starting "fetch-crl-cron"...')
     cmd = ('/sbin/service fetch-crl-cron start')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not start "fetch-crl-cron"!')
     return
  
  # policies for WNs
  logger.info('determining policies for WNs...')
  if 'wn_policies' in argus_config_cfg:
     script=argus_config_cfg['wn_policies']
  else:
     logger.error('script to get WN policies not defined!')
     return 
  try:
     value = urllib2.urlopen(script)
     fscript = open('script.sh','w')
     fscript.write(value.read())
     fscript.close()    
     os.system('chmod +x script.sh') 
  except:
     logger.error('could not fetch script to get WN policies!')
     return 
  try:
     cmd=('./script.sh > my-policy.spl')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not write policies file!')
     return

  # need to restart PAP or policy setting will fail
  logger.info('restarting PAP...')
  try:
     cmd = ('service argus-pap restart')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not restart PAP!')
     return
     
  try:
     cmd=('pap-admin  add-policies-from-file  my-policy.spl')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not add policies to PAP!')
     return

  # other policies
  logger.info('setting other policies...')
  for res in argus_config_cfg:
     if 'resource' in res:
        res_cfg=argus_config_cfg[res]
        if 'name' in res_cfg:
           name=res_cfg['name']
           logger.info('resource: '+name+'')
        else:
           logger.error('resource name not specified!')
           return 
        if 'vos' in res_cfg:
           vos=res_cfg['vos']
           for vo in vos:
              logger.info('adding vo: '+vo+'')
              try:
                 cmd = ('pap-admin add-policy permit --resource "'+name+'" --action ".*" vo="'+vo+'" --obligation "http://glite.org/xacml/obligation/local-environment-map"') 
                 DPopen(cmd, 'True') 
              except:
                 logger.error('could not add VO '+vo+'!')
                 return
        else:
           logger.error('VOs not specified!')
           return 
 
  try:
     cmd = ('argus-pdp restart')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not add VO '+vo+'!')
     return
  
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
