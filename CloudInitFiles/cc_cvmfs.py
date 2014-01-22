#part-handler
# vi: syntax=python ts=4

# Author: Cristovao Cordeiro <cristovao.cordeiro@cern.ch>			
# Modified by: svallero@to.infn.it

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
import urllib2
import sys
import os

# Define logfile
logname = '/var/log/cloud-init-cvmfs.log'
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/cvmfs-config"])

########################

def install_cvmfs(version, rhel):
  logger.info('entering CVMFS installation...')  
  arch = platform.machine()       # Platform info
  # cvmfs and cvmfs-keys package url
  cvmfs_rpm_url = 'https://ecsft.cern.ch/dist/cvmfs/cvmfs-'+version+'/cvmfs-'+version+'-1.el'+str(rhel)+'.'+arch+'.rpm'
  logger.info('Pakcage ulr: '+cvmfs_rpm_url+'') 
  cvmfs_keys_rpm_url = 'https://ecsft.cern.ch/dist/cvmfs/cvmfs-keys/cvmfs-keys-1.4-1.noarch.rpm'
  # Downloading cvmfs and cvmfs-keys.rpm file to /home path
  try:
    cmd = ('wget --no-check-certificate -O /tmp/cvmfs.rpm '+cvmfs_rpm_url+'') 
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not retrieve package '+cvmfs_rpm_url+'!')
    return
  try:
    cmd = ('wget --no-check-certificate -O /tmp/cvmfs-keys.rpm '+cvmfs_keys_rpm_url+'') 
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not retrieve package '+cvmfs_keys_rpm_url+'!')
    return 
  
  # Install cvmfs packages
  try:
    cmd = ('yum --nogpgcheck -y localinstall /tmp/cvmfs.rpm /tmp/cvmfs-keys.rpm')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('CVMFS installation from the yum repository has failed!')
    return

  # Base setup
  try: 
    cmd = ('cvmfs_config setup')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not setup cvmfs!')
    return

  # Start autofs and make it starting automatically after reboot 
  try:
    cmd = ('service autofs start')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not start autofs service')
    return
  
  try:   
    cmd = ('chkconfig autofs on')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not chkconfig autofs on')
    return

  try: 
    cmd = ('cvmfs_config chksetup')
  except:
    logger.error('could not chksetup cvmfs!')
    return


########################

def config_cvmfs(lfile, dfile, cmsfile, params):
  quota_aux_var = 1   # Aux varibale to check whether to write default quota-limit value or not   
  
  if 'local' in params:
    local_args = params['local']
    try:
      flocal = open(lfile, 'w')
    except:
      logger.error('could not open file: '+lfile+'')
      return 
    for prop_name, value in local_args.iteritems():
      if prop_name == 'repositories':
        flocal.write('CVMFS_REPOSITORIES='+value+'\n')
      if prop_name == 'cache-base':
        flocal.write('CVMFS_CACHE_BASE='+value+'\n')
      if prop_name == 'default-domain':
        flocal.write('CVMFS_DEFAULT_DOMAIN='+value+'\n')
      if prop_name == 'http-proxy':
        flocal.write('CVMFS_HTTP_PROXY='+value+'\n')
      if prop_name == 'quota-limit':
        flocal.write('CVMFS_QUOTA_LIMIT='+str(value)+'\n')
        quota_aux_var = 0
      if prop_name == 'strict-mount':
        flocal.write('CVMFS_STRICT_MOUNT=='+value+'\n')
      if prop_name == 'cms-local-site':
         try:
           cmslocal = open(cmsfile, 'w')
         except:
           logger.error('could not open file: '+cmsfile+'')
           return 
         cmslocal.write('export CMS_LOCAL_SITE='+str(value)+'\n')
         cmslocal.close()

    # Close the file
    flocal.close()

  if 'domain' in params:
    domain_args = params['domain']
    if 'server' in domain_args:
      try:
        fdomain = open(dfile, 'w')
      except:
        logger.error('could not open file: '+dfile+'')
        return 
      fdomain.write('CVMFS_SERVER_URL='+domain_args['server']+'\n')
      fdomain.close()

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

  # If there isn't a cvmfs reference in the configuration don't do anything
  if 'cvmfs' not in cfg:
    logger.error('cvmfs configuration was not found!')
    return
  
  logger.info('ready to setup cvmfs...')
  cvmfs_cfg = cfg['cvmfs']
  
  # Add dirs to path
  sys.path.append('/usr/bin') 
  sys.path.append('/sbin') 

  logger.info('configuring cvmfs...')
  Installation = False
  if 'install' in cvmfs_cfg:
    Installation = cvmfs_cfg['install']
    if Installation == True:
      if 'version' in cvmfs_cfg:
        version = cvmfs_cfg['version']
      else:
 		version = '2.1.14'       
      if 'el' in cvmfs_cfg:
        el = cvmfs_cfg['el']
      else:
 		el = 6       
      install_cvmfs(version, el)	    

  LocalFile = '/etc/cvmfs/default.local'
  DomainFile = '/etc/cvmfs/domain.d/cern.ch.local'
  CMS_LocalFile = '/etc/cvmfs/config.d/cms.cern.ch.local'
  
  config_cvmfs(LocalFile, DomainFile, CMS_LocalFile, cvmfs_cfg)

  logger.info('starting cvmfs...')
  # Start cvmfs
  try:
    cmd = ('cvmfs_config reload')
    DPopen(shlex.split(cmd), 'False') 
    cmd = ('cvmfs_config probe')
    DPopen(shlex.split(cmd), 'False') 
  except:
    logger.error('could not start cvmfs!')
    return 

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
