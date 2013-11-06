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

# Define global variables
grid_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-grid_config.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/grid_config-config"])

########################

def ConfigAddNode(ce, NCores):
  logger.info('fetching createhost-rsa...')
  filename = 'createhost-rsa'
  val = grid_cfg[filename]
  get_embedded(filename, val, '/tmp') 
  cmd = ('chmod 0400 /tmp/'+filename+'')
  DPopen(cmd, 'True')

  logger.info('invoking remote addition by performing ssh...')    
  try:
    cmd = ('echo '+Ncores+' | ssh qmanager@'+ce+' -i /tmp/'+filename+' -o StrictHostKeyChecking=yes')
    DPopen(cmd, 'True')
  except: 
    logger.error('error: could not perform remote addition of node!')

  cmd = ('rm -f /tmp/'+filename+'')
  DPopen(cmd, 'True')
  return

########################

def ConfigMomLoads(NCores):
  cmd = ('echo  "'+NCores+' + 1.0" | bc')
  IdealLoad = DPopen(cmd).read()
  IdealLoad = IdealLoad.strip() 
  
  cmd = ('echo  "'+NCores+' * 1.5" | bc') 
  MaxLoad = DPopen(cmd).read() 
  MaxLoad = MaxLoad.strip() 

  MomConf = '/etc/torque/mom/config'

  logger.info('writing pbs_mom config file ('+MomConf+')...')
  try:
    cmd = ('egrep -v "\\$ideal_load|\\$max_load" '+MomConf+' > '+MomConf+'.0')
    DPopen(cmd, 'True')
    cmd = ('echo "\\$ideal_load '+IdealLoad+'" >> '+MomConf+'.0')
    DPopen(cmd, 'True')
    cmd = ('echo "\\$max_load '+MaxLoad+'" >> '+MomConf+'.0')
    DPopen(cmd, 'True')
    cmd = ('mv -f '+MomConf+'.0 '+MomConf+'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not write pbs_mom config!')
    return


  logger.info('Starting pbs_mom...')
  try:
    cmd = ('service pbs_mom start')
    DPopen(cmd, 'True')
  except:
    logger.error('could not start pbs_mom!')
    return

########################

def ConfigMunge():
  # Copying the Torque Server Munge key to the worker-node
  logger.info('fetching munge.key...')
  filename = 'munge.key'
  val = grid_cfg[filename]
  get_embedded(filename, val, '/etc/munge') 
  try:
    cmd = ('chown munge:munge /etc/munge/'+filename+'')
    DPopen(cmd, 'True')
    cmd = ('chmod 0400 /etc/munge/'+filename+'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not change permissions to munge.key!')
 
  logger.info('restarting Munge service...')
  try:
    cmd = ('/sbin/service munge restart')
    DPopen(cmd, 'True')
    cmd = ('/sbin/chkconfig munge on')
    DPopen(cmd, 'True')
  except:
    logger.error('could not restart Munge service!') 

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

  # If there isn't a grid_config reference in the configuration don't do anything
  if 'grid_config' not in cfg:
    logger.error('worker-node will not be configured for GRID!!!')
    return
  else:
    grid_cfg = cfg['grid_config']
    if 'ce' in grid_cfg:
      ce  = grid_cfg['ce']
    else:
      logger.error('error: computing element (ce) not defined!')
      return

    # Restart "fetch-crl service"
    try:
      logger.info('re-starting "fetch-crl service"')
      cmd = ('service fech-crl restart')
      DPopen(cmd, 'True')
    except:
      logger.error('error: could not restart service "fetch-crl"!') 
      return 
    
    # Get the number of cores
    logger.info('getting number of cores...')
    try:
      cmd = ('grep -c bogomips /proc/cpuinfo')
      NCores = DPopen(cmd).read()
      NCores = NCores.strip()
    except:
      logger.error('could not determine the number of cores!')
      return

    # Add node to pbs queue
    try:
      logger.info('adding node to LRMS...')
      ConfigAddNode(ce, NCores)
    except:
      logger.error('error: could not add node to local pbs system!')
      return

    # Configure Mom loads
    try:
      legger.info('configuring pbs_mom loads...')
      ConfigMomLoads(NCores)
    except:
      logger.error('error: could not configure pbs_mom loads!')
      return

    # Configure Munge
    try:
      logger.info('configuring Munge...')
      ConfigMunge()
    except:
      logger.error('could not configure Munge!')
      return     
 
    # Configure server-name
    logger.info('setting pbs server name (ce)...')
    try:
      cmd = ('echo "'+ce+'" > /var/lib/torque/server_name')
      DPopen(cmd, 'True') 
      cmd = ('sed -i -e \'s/localhost/'+ce+'/g\' /etc/torque/mom/config')
      DPopen(cmd, 'True') 
    except:
      logger.error('could not set pbs server name!')
      return
    
    logger.info('restarting pbs_mom...')
    try:
      cmd = ('/sbin/service pbs_mom restart')
      DPopen(cmd, 'True') 
    except:
      logger.error('could not restart pbs_mom!')
      return
 
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
