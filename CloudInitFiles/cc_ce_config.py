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
ce_config_cfg = 0
rootdir = '/root/scripts'

# Define logfile
logname = '/var/log/cloud-init-ce_config.log'
#logname = '/tmp/cloud-init-ce_config.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://srm-dom0.to.infn.it/test/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/ce_config-config"])

########################

def get_tarfile(): 
  logger.info('download .tar archieve with yaim configuration files...')

  if 'repo' in ce_config_cfg:
     repo = ce_config_cfg['repo']
  else:
     logger.error('repo not specified!')
     return

  tarfile = ce_config_cfg['tarfile']
  
  origin = ''+repo+'/'+tarfile+''
  destination = ''+rootdir+'/'+tarfile+''
  # downloading .tar file  
  try:
    cmd = ('wget -O '+destination+' '+origin+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not download .tar file!')
    return

  logger.info('preparing yaim...')
  try:
    cmd = ('tar zxvf '+destination+' -C '+rootdir+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not unpack .tar file!')
    return
  logger.warning('files will not be moved into place (TODO)!!!')
########################

def get_embedded(embed_block, repo):

  if repo:
    logger.info('fetching file '+embed_block+' from repo: '+repo+'...') 
    try:
      value = urllib2.urlopen(''+repo+'/'+embed_block+'')
    except:
      logger.error('could not fetch configuration file!')
      return
    content = value.read()
  else:  
    logger.info('writing configuration file '+embed_block+'...') 
    value = ce_config_cfg[embed_block]
    content = value
  filename = os.path.basename(embed_block)
  text_file = open(filename, "w")
  text_file.write(content)
  text_file.close()
  logger.info(''+filename+' written')

  if embed_block.startswith('scripts'):
    dest = rootdir
  elif embed_block.startswith('cloudities'):
    dest = '/opt/cloudities'
  elif embed_block.startswith('keys'):
    dest = '/home/qmanager/.ssh'
  elif embed_block.startswith('servercontext'):
    dest = '/opt/cloudities/server-context'
  elif embed_block.startswith('maui'):
    dest = '/var/spool/maui'
  
  logger.info('moving file into place...')
  try:
    cmd = ('mv '+filename+' '+dest+'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not move file into place!')
    return
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
  if 'ce_config' not in cfg:
     logger.error('ce_config configuration was not found!')
     return 
 
  logger.info('ready to configure CE')
  global ce_config_cfg 
  ce_config_cfg = cfg['ce_config'] 
  
  if 'name' in ce_config_cfg:
     name = ce_config_cfg['name']
     logger.info('configuring CE: '+name+'')
  else:
     logger.error('CE name not specified!')
     return 

  # configure public network
  logger.info('configuring public network...')
  # TODO change back to eth1!!!
  cmd = ('/sbin/ifconfig eth1 | grep "inet addr" | awk -F: \'{print $2}\' | awk \'{print $1}\'')
  status,ip = commands.getstatusoutput(cmd)
  if not ip:
     logger.error('public ip not found!')
     return
  if not status:
     logger.info('found public ip: '+ip+'')
     mac='02:00'
     for block in str(ip).split('.'):
        hx = hex(int(block)).upper()[2:].zfill(2)
        mac+=(':'+hx+'')
     logger.info('assigned mac address: '+mac+'')
  else:
     logger.error('could not determine public ip!')

  wan_mask = '255.255.255.192'  
  if 'wan_mask' in ce_config_cfg:
     wan_mask = ce_config_cfg['wan_mask']
     logger.info('assigning wan mask: '+wan_mask+'')
  
  os.environ['WAN_MASK'] = wan_mask
  os.environ['WAN_MAC'] = mac
  os.environ['WAN_IP'] = ip
  cmd = ('''cat > /etc/sysconfig/network-scripts/ifcfg-eth1 << EOF
DEVICE=eth1
NETMASK=$WAN_MASK
HWADDR=$WAN_MAC
BOOTPROTO=static
IPADDR=$WAN_IP
ONBOOT=yes
GATEWAY=193.206.184.62
EOF''')
  try:
    DPopen(cmd, 'True')
  except:
    loger.error('could not write file: /etc/sysconfig/network-scripts/ifcfg-eth1 !')

  # create user qmanager
  logger.info('creating user "qmanager"')
  try:
     cmd = ('/usr/sbin/useradd -u 5353 -g nobody -d /home/qmanager -s /bin/bash qmanager')
     DPopen(cmd, 'True') 
  except:
     logger.error('could not create user "qmanager"!')
     return

  # create directory structure  
  logger.info('creating directory structure...') 
  try:
    logger.info('creating /home/qmanager/.ssh')
    cmd = ('mkdir -p /home/qmanager/.ssh')
    DPopen(cmd, 'True') 
    logger.info('creating /root/scripts')
    cmd = ('mkdir -p /root/scripts')
    DPopen(cmd, 'True') 
    logger.info('creating /opt/cloudities')
    cmd = ('mkdir -p /opt/cloudities')
    DPopen(cmd, 'True') 
    logger.info('creating /opt/cloudities/server-context')
    cmd = ('mkdir -p /opt/cloudities/server-context')
    DPopen(cmd, 'True') 
  except:
     logger.error('could not create directory structure!')
     return
   
  # copy scripts into place
  logger.info('copying scripts into place...') 

  repo = 0
  if 'repo' in ce_config_cfg:
    repo = ce_config_cfg['repo']

  for block in ce_config_cfg:
    if block == 'tarfile':
      # incomplete, files are not moved to proper place (TODO)
      get_tarfile()
    elif (block == 'scripts' or block == 'cloudities' or block == 'keys'  or block == 'servercontext' or block == 'mauicfg'):
      if not repo:
        logger.error('repository for "files" not specified')  
        return
      for file in ce_config_cfg[block]:
        get_embedded(file, repo) 
    elif block != 'name' and block != 'repo':
      logger.info('reading embedded files...')
      get_embedded(block, '') 

  # setting proper permissions
  logger.info('setting proper permissions to /home/qmanager/.ssh...') 
  try:
     cmd = ('chown -R qmanager:nobody /home/qmanager/.ssh')
     DPopen(cmd, 'True')
  except:
     logger.error('could not change permissions!')
     return
 
  # add qmanager to sudoers 
  logger.info('adding "qmanager" to sudoers...')
  try:
     cmd = ('echo "qmanager  ALL = NOPASSWD: /opt/cloudities/server-context/ssh-hosts-keys" >> /etc/sudoers')
     DPopen(cmd, 'True')
  except:
     logger.error('could not write /etc/sudoers file!')
     return 
  logger.info('patching /etc/sudoers...')
  try:
     cmd = ('sed -i -e i\'s/^Defaults\s\+requiretty/#Defaults   requiretty/\' /etc/sudoers')
     DPopen(cmd, 'True')
  except:
     logger.error('could not patch file /etc/sudoers!')
     return 
  
  # restorecon   
  logger.info('restoring security context (restorecon) for /home/qmanager/.ssh/*...')
  try:
     cmd = ('/sbin/restorecon /home/qmanager/.ssh/*')
     DPopen(cmd, 'True')
  except:
     logger.error('could not run restorecon!')
     return 
  
  # install ruby
  logger.info('installing ruby...')
  try:
     cmd = ('yum --enablerepo=epel -y install ruby')
     DPopen(cmd, 'True')
  except:
     logger.error('could not install ruby!')
     return 

  cmd = ('yum clean all')
  DPopen(cmd, 'True')
  
  # add qmanager as pbs manager 
  logger.info('adding qmanager as torque server manager...')
  try:
    cmd = ('qmgr -c \'set server managers += qmanager@'+name+'\'')
    DPopen(cmd, 'True')
  except:
    logger.error('could not set torque manager!')
    return
 
  # start maui
  logger.info('starting maui...')
  try:
    cmd = ('/sbin/service maui restart')
    DPopen(cmd, 'True')
  except:
    logger.error('could not start maui!')
    return

  # disable queues
  logger.info('disabling all the queues but "cert" at the beginning...') 
  try:
    cmd = ('for i in `qstat -q | grep -v Queue | grep -v "cert" | grep R | cut -d"-" -f1`; do qmgr -c "s q $i enabled=false"; done')   
    DPopen(cmd, 'True')
  except:
    logger.error('could not disable queues!')
    return  

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
