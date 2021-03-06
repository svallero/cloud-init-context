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

# Define global because needed in different functions
yaimhome = '/opt/glite/yaim'
igiyaim_cfg = 0

# Define logfile
logname = '/var/log/cloud-init-igiyaim.log'
#logname = '/tmp/cloud-init-igiyaim.log'
# Import script with definition of logger and some useful function
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://one-master.to.infn.it/cloud-init-files/header.py')
exec (response.read())

########################

def list_types():
  # return a list of mime-types that are handled by this module
  return(["text/igiyaim-config"])

########################

def get_tarfile(): 
  logger.info('download .tar archieve with yaim configuration files...')

  if 'repo' in igiyaim_cfg:
     repo = igiyaim_cfg['repo']
  else:
     logger.error('repo not specified!')
     return

  tarfile = igiyaim_cfg['tarfile']
  
  origin = ''+repo+'/'+tarfile+''
  destination = ''+yaimhome+'/'+tarfile+''
  # downloading .tar file  
  try:
    cmd = ('wget -O '+destination+' '+origin+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not download .tar file!')
    return

  logger.info('preparing yaim...')
  try:
    cmd = ('tar zxvf '+destination+' -C '+yaimhome+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not unpack .tar file!')
    return

########################

def get_embedded(embed_block, repo):

  if not os.path.exists(''+yaimhome+'/production'):
    logger.info('creating directory structure in '+yaimhome+'...')
    try:
      #cmd = ('mkdir '+yaimhome+'/production')
      #DPopen(shlex.split(cmd), 'False')
      os.mkdir(''+yaimhome+'/production')
      #cmd = ('mkdir '+yaimhome+'/production/siteinfo')
      #DPopen(shlex.split(cmd), 'False')
      os.mkdir(''+yaimhome+'/production/siteinfo')
      #cmd = ('mkdir '+yaimhome+'/production/siteinfo/services')
      #DPopen(shlex.split(cmd), 'False')
      os.mkdir(''+yaimhome+'/production/siteinfo/services')
      #cmd = ('mkdir '+yaimhome+'/production/siteinfo/vo.d')
      #DPopen(shlex.split(cmd), 'False')
      os.mkdir(''+yaimhome+'/production/siteinfo/vo.d')
    except:
      logger.error('could not create directory structure!')
      return
  if repo:
    logger.info('fetching configuration file '+embed_block+' from repo: '+repo+'...') 
    try:
      value = urllib2.urlopen(''+repo+'/'+embed_block+'')
    except:
      logger.error('could not fetch configuration file!')
      return
    content = value.read()
  else:  
    logger.info('writing configuration file '+embed_block+'...') 
    value = igiyaim_cfg[embed_block]
    content = value
  text_file = open(embed_block, "w")
  text_file.write(content)
  text_file.close()
  logger.info(''+embed_block+' written')

  if embed_block.endswith('.conf'):
    dest = ''+yaimhome+'/production/'
  elif embed_block.endswith('.def'):
    dest = ''+yaimhome+'/production/siteinfo/'
  elif embed_block.startswith('glite-') or embed_block.startswith('se_storm_'):
    dest = ''+yaimhome+'/production/siteinfo/services/'
  elif embed_block.startswith('vo-'):
    tmp = embed_block[3:]
    cmd = ('mv '+embed_block+' '+tmp+'')
    DPopen(shlex.split(cmd), 'False')
    embed_block=tmp
    dest = ''+yaimhome+'/production/siteinfo/vo.d/'
  logger.info('moving file into place...')
  try:
    cmd = ('mv '+embed_block+' '+dest+'')
    DPopen(shlex.split(cmd), 'False')
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
  
  # If there isn't a igiyaim reference in the configuration don't do anything
  if 'igiyaim' not in cfg:
    logger.error('igiyaim configuration was not found!')
    return 
 
  logger.info('ready to setup Igi-Yaim')
  global igiyaim_cfg 
  igiyaim_cfg = cfg['igiyaim'] 

  
                                
  if 'yaimhome' in igiyaim_cfg:
     global yaimhome
     yaimhome = igiyaim_cfg['yaimhome']
  
  if 'repo' in igiyaim_cfg:
     repo = igiyaim_cfg['repo']

  for block in igiyaim_cfg:
    if block == 'tarfile':
      get_tarfile()
    elif block == 'files':
      if not repo:
        logger.error('repository for "files" not specified')  
        return
      for file in igiyaim_cfg['files']:
        get_embedded(file, repo) 
    elif block != 'yaimhome' and block != 'repo' and block != 'type':
      logger.info('reading embedded files...')
      get_embedded(block, '') 

  type='wn'
  if 'type' in igiyaim_cfg:
     type = igiyaim_cfg['type']
  # for workernodes
  if type == 'wn':
     logger.info('configuring WN...')
     #logger.info('patching file "$yaimhome/node-info.d/wn_torque_noafs"...')
     #try:
     #  cmd = ('grep -v "config_ntp" '+yaimhome+'/node-info.d/wn_torque_noafs > '+yaimhome+'/node-info.d/wn_torque_noafs.0')
     #  DPopen(cmd, 'True')
     #  cmd = ('mv '+yaimhome+'/node-info.d/wn_torque_noafs.0 '+yaimhome+'/node-info.d/wn_torque_noafs') 
     #  DPopen(cmd, 'True')
     #except:
     #  logger.error('could not patch file "$yaimhome/node-info.d/wn_torque_noafs"')
     #  return

     #try:
     #  cmd = ('/sbin/service iptables stop')
     #  DPopen(shlex.split(cmd), 'False')
     #  cmd = ('/usr/sbin/setenforce 0')
     #  DPopen(shlex.split(cmd), 'False')
     #except:
     #  logger.error('failed to disable firewall and selinux!') 
     #  return

     logger.info('writing dummy munge.key...') 
     os.system('mkdir -p /etc/munge') 
     os.system('echo "dummy" > /etc/munge/munge.key');
     os.system('chown munge:munge /etc/munge/munge.key')
     logger.info('go yaim...')
     try :
        cmd = ('echo `hostname -f` > '+yaimhome+'/production/wn-list.conf')
        DPopen(cmd, 'True')
        #cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def -n WN_torque_noafs 2>&1 > /var/log/yaim.log')
        cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def -n WN -n TORQUE_client 2>&1 > /var/log/yaim.log')
        DPopen(cmd, 'True')
     except:
       logger.error('failed to configure with yaim.') 
       return

  # for ce
  elif type == 'ce':
     logger.info('configuring CE...')
     logger.info('starting pbs server...')
     try:
        cmd = ('/etc/init.d/pbs_server start')
        DPopen(cmd, 'True')   
     except:
        logger.error('failed to start pbs server!')
     #logger.info('stopping selinux...')
     #try:
     #  cmd = ('/usr/sbin/setenforce 0')
     #  DPopen(shlex.split(cmd), 'False')
     #except:
     #  logger.error('failed to stop selinux!')
     #  return 
     
     try:
        logger.info('go yaim...')
        cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def  -n  creamCE -n TORQUE_server -n TORQUE_utils 2>&1 > /var/log/yaim.log') 
        DPopen(cmd, 'True')   
     except:
        logger.error('failed to configure with yaim!') 
        return

  # for se
  elif type == 'se':
     logger.info('configuring SE...')
     logger.info('applying some patch...')
     try:
        cmd = ('sed -i -e "s/config_ntp//" /opt/glite/yaim/node-info.d/*') 
        DPopen(cmd, 'True')   
     except:
        logger.error('failed to patch files in /opt/glite/yaim/node-info.d/!')  

     #logger.info('sourcing java home path in /tmp/je.sh (dirty hack)...')
     #try:
     #   cmd = ('source /tmp/je.sh') 
     #   DPopen(cmd, 'True')   
     #except:
     #   logger.error('failed to source /tmp/je.sh!')  

     try:
        logger.info('go yaim...')
        #cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def  -n se_storm_backend -n se_storm_frontend -n se_storm_gridftp 2>&1') 
        cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def  -n se_storm_backend -n se_storm_frontend -n se_storm_gridftp 2>&1 > /var/log/yaim.log') 
        DPopen(cmd, 'True')   
     except:
        logger.error('failed to configure with yaim!') 

  #SB: This is for myproxy. Maybe it would be better to make a catchall default 
  #SB: that just passes the type to yaim and let it handle unknown types?       
  #SV: yes
  #elif type == 'PX':
  #   try:
  #      logger.info('go yaim...')
  #      cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def  -n PX  2>&1 ') 
  #      DPopen(cmd, 'True')   
  #   except:
  #      logger.error('failed to configure with yaim!') 
  else:
     try:
        logger.info('go yaim...')
        logger.info('configuration type: '+type+'')
        cmd = (''+yaimhome+'/bin/yaim -c -d 6 -s '+yaimhome+'/production/siteinfo/site-info.def  -n '+type+'  2>&1 ') 
        DPopen(cmd, 'True')   
     except:
        logger.error('failed to configure with yaim!') 

  #else:
  #   logger.error('unknown configuration type!'); 
  
  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))	       
