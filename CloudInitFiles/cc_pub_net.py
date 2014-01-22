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
pub_net_cfg = 0
rootdir = '/root/scripts'

# Define logfile
logname = '/var/log/cloud-init-pub_net.log'
#logname = '/tmp/cloud-init-pub_net.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/CloudInitFiles/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/pub_net-config"])

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
  
  # If there isn't a pub_net reference in the configuration don't do anything
  if 'pub_net' not in cfg:
     logger.error('pub_net configuration was not found!')
     return 
 
  logger.info('ready to setup public network...')
  global pub_net_cfg 
  pub_net_cfg = cfg['pub_net'] 
  
  # set the hostname
  logger.info('setting the hostname...')
  if 'name' not in pub_net_cfg:
    logger.error('name not specified!')
    return
  name = pub_net_cfg['name']

  try:
    cmd = ('hostname '+name+'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not configure the hostname!')
    return
  logger.info('hostname set to: '+name+'')

  # configure public interface on eth1: mav, ip, netmask and gateway
  logger.info('configuring public network...')
  cmd = ('/sbin/ifconfig eth1 | grep "HWaddr" | awk \'{print $5}\'')
  status,mac = commands.getstatusoutput(cmd)
  if not mac or 'error' in mac:
     logger.error('public mac not found!')
     return
  else:
     if not status:
        logger.info('found public mac: '+mac+'')
        logger.info('assigning ip address accordingly...')
        ip = ''
        try:
           for block in str(mac).split(':'):
              dec = int(block,16)
              ip +=(''+str(dec)+'.')
           ip = ip[:-1] 
           ip = ip[4:] 
           logger.info('assigned ip address: '+ip+'')
        except:
           logger.error('could not assign ip address!')
           return 
     else:
        logger.error('could not determine public mac!')
        return

  wan_mask = '255.255.255.192'  
  if 'wan_mask' in pub_net_cfg:
     wan_mask = pub_net_cfg['wan_mask']
  logger.info('assigning wan mask: '+wan_mask+'')
  
  gateway = '193.206.184.62'  
  if 'gateway' in pub_net_cfg:
     gateway = pub_net_cfg['gateway']
  logger.info('assigning gateway: '+gateway+'')

  os.environ['WAN_MASK'] = wan_mask
  os.environ['WAN_MAC'] = mac
  os.environ['WAN_IP'] = ip
  os.environ['GATEWAY'] = gateway
  
  cmd = ('''cat > /etc/sysconfig/network-scripts/ifcfg-eth1 << EOF
DEVICE=eth1
NETMASK=$WAN_MASK
HWADDR=$WAN_MAC
BOOTPROTO=static
IPADDR=$WAN_IP
ONBOOT=yes
GATEWAY=$GATEWAY
EOF''')

  try:
    logger.info('writing /etc/sysconfig/network-scripts/ifcfg-eth1...')
    DPopen(cmd, 'True')
  except:
    loger.error('could not write file: /etc/sysconfig/network-scripts/ifcfg-eth1 !')
    return
  logger.info('restarting network...')
  try:
    cmd = ('service network restart')
    DPopen(cmd, 'True')
  except:
    loger.error('could not restart network!')
    return
    
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
