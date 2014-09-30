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

Parts = ''

# Define logfile
logname = '/var/log/cloud-init-localfs.log'
#logname = '/tmp/cloud-init-localfs.log'
# Import script with definition of logger and some useful function 
# to avoid duplicating the same code on all modules
response = urllib2.urlopen('http://one-master.to.infn.it/cloud-init-files/header.py')
exec (response.read())

########################

def list_types():
    # return a list of mime-types that are handled by this module
    return(["text/localfs-config"])

########################

def list_of_partitions(params):
  # List of partitions
  # for the time being only: cvmfs, home, tmp and swap are allowed
  # percent of Vg can be specified for each 
  # (swap refers to free space, should be configured last) 
  # only cvmfs mount-point can be configured
  # (one could implement more flexibility in the future)

  # define defaults
  cvmfs_percent = str(0)
  cvmfs_mount = '/var/lib/cvmfs'
  home_percent = str(58)
  home_mount = '/home'
  tmp_percent = str(8)
  tmp_mount = '/tmp' 
  swap_percent = str(100)
   
  # get configuration
  if 'parts' in params:
    parts_args = params['parts']
    for prop_name, value in parts_args.iteritems():
      if prop_name == 'cvmfs':
        cvmfs_percent = str(value)
      if prop_name == 'cvmfs_mount':
        cvmfs_mount = str(value)
      if prop_name == 'home':
        home_percent = str(value)
      if prop_name == 'tmp':
        tmp_percent = str(value)
      if prop_name == 'swap':
        swap_percent = str(value)

  cvmfs_percent += '%VG' 
  home_percent += '%VG' 
  tmp_percent += '%VG' 
  swap_percent += '%FREE' 

  Cvmfs=['cvmfs',cvmfs_percent, cvmfs_mount] 
  Home=['home',home_percent, '/home'] 
  Tmp=['tmp',tmp_percent, '/tmp']
  Swap =['swap',swap_percent, 'swap']
 
  global Parts     
  #Parts = ['cvmfs:'+cvmfs_percent+'%VG:'+cvmfs_mount+' home:'+home_percent+'%VG:/home tmp:'+tmp_percent+'%VG:/tmp swap:'+swap_percent+'%FREE:swap']  
  Parts = [Cvmfs, Home, Tmp, Swap]  
  logger.info('list of partitions that will be created:')
  logger.info(Parts)

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
  # If there isn't a localfs reference in the configuration don't do anything
  if 'localfs' not in cfg:
    logger.error('localfs configuration was not found!')
    return


  logger.info('ready to setup localfs...')
  localfs_cfg = cfg['localfs']
  logger.info(' configuring localfs...')
  
  # Name of volume group
  Vg = 'attached'
  # External disk (specified in the template)
  Dev='/dev/vdb'
  if 'extdisk' in localfs_cfg:
    Dev = localfs_cfg['extdisk']
     
  # List of partitions
  if 'parts' in localfs_cfg:
    list_of_partitions(localfs_cfg)

    # If structure already exists skip this section
    try:
      cmd = ('vgdisplay '+Vg+' > /dev/null 2>&1')
      DPopen(cmd,'True') 
    except:
      logger.info('local filesystem structure not yet created, Im doing it now...')

      try:
         cmd = ('dd if=/dev/zero of='+Dev+' count=100 bs=100')
         DPopen(cmd,'True') 
      except:
         logger.error('dd command failed!')
         return 

      logger.info('creating physical volume...')
      try:
         cmd = ('pvcreate '+Dev+'')
         DPopen(cmd,'True') 
      except:
         logger.error('could not create physical volume!')
         return
  
      logger.info('creating volume group...')
      try:
         cmd = ('vgcreate '+Vg+' '+Dev+'')
         DPopen(cmd,'True') 
      except:
         logger.error('could not create volume group!')
         return
  
      Lv = ''
      Size = ''
      Mount = ''
      for p in Parts:
         Lv = p[0] 
         Size = p[1] 
         Mnt = p[2]
         if (Size == '0%VG'):
           continue 
         logger.info('creating logical volume '+Lv+'...') 
         try:
           cmd = ('lvcreate -l '+Size+' -n '+Lv+' '+Vg+'')
           DPopen(cmd,'True') 
         except:
           logger.error('could not create logical volume!')
           return
         logger.info('creating mount point '+Mnt+'...') 
         try:
           cmd = ('mkdir -p '+Mnt+'')
           DPopen(cmd,'True') 
         except:
           logger.error('could not create mount point!')
           return
         if Mnt == 'swap':
           logger.info(''+Lv+' making swap space...') 
           try:
             cmd = ('mkswap /dev/'+Vg+'/'+Lv+'')
             DPopen(cmd,'True') 
           except:
             logger.error('ERROR: unable to make swap!')
           logger.info('activating swap...') 
           try:
             cmd = ('swapon /dev/'+Vg+'/'+Lv+'')
             DPopen(cmd, 'True') 
           except:
             logger.error('unable to activate swap!')
           logger.info(''+Lv+' adding to fstab...') 
           try:
             cmd = ('echo "/dev/'+Vg+'/'+Lv+' swap swap defaults 0 0" >> /etc/fstab')
             DPopen(cmd,'True') 
           except:
             logger.error('unable to add to fstab!')
         else:  
           logger.info(''+Lv+' making filesystem...')
           try:
             cmd = ('mkfs.xfs -L '+Lv+' /dev/'+Vg+'/'+Lv+'')
             DPopen(cmd, 'True') 
           except:
             logger.error('unable to make filesystem!')
           logger.info('mounting filesystem to '+Mnt+'...')
           try:
             cmd = ('mount -t xfs /dev/'+Vg+'/'+Lv+' '+Mnt+'')
             DPopen(cmd,'True') 
           except:
             logger.error('unable to mount filesystem!')
           if Lv == 'tmp':
             logger.info('adjusting permission for tmp dir...')
             cmd = ('chmod 1777 '+Mnt+'')
             DPopen(cmd,'True') 
           logger.info(''+Lv+' adding to fstab...') 
           try:
             cmd = ('echo "/dev/'+Vg+'/'+Lv+' '+Mnt+' xfs defaults 0 0" >> /etc/fstab')
             DPopen(cmd,'True') 
           except:
             logger.error('ERROR: unable to add to fstab!')
  elif 'mounts' in localfs_cfg:
    mounts_cfg=localfs_cfg['mounts'] 
    for mnt in mounts_cfg:
       logger.info('mounting: '+str(mnt)+'...') 
       Dev=mnt[0]
       Mnt=mnt[1]
       Fs=mnt[2]
       logger.info('considering device '+Dev+'...')
       if 'swap' in Mnt: # SWAP
         logger.info('making swap space...') 
         try:
           cmd = ('mkswap /dev/'+Dev+'')
           DPopen(cmd,'True') 
         except:
           logger.error('ERROR: unable to make swap!')
         logger.info('activating swap...') 
         try:
           cmd = ('swapon /dev/'+Dev+'')
           DPopen(cmd, 'True') 
         except:
           logger.error('unable to activate swap!')
       else: # OTHER MOUNTS
         # this makes me loose time? maybe do just for /home
         logger.info('check if device is formatted...')
         try:
           #cmd='blkid | grep /dev/'+Dev+''
           cmd='blkid'
           proc=Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
         except: 
           logger.error('could not check device with blkid!')
           return 
         out,err= proc.communicate()
         if Dev not in out:
           logger.info('device is not formatted, doing it now...')
           try:
             cmd=('mkfs -t '+Fs+' /dev/'+Dev+'')
             DPopen(cmd,'True') 
           except:
             logger.error('could not format device!')
         else:
           logger.info('...yes!') 
         logger.info('creating mount point...')
         try:
           cmd = ('mkdir -p '+Mnt+'')
           DPopen(cmd,'True') 
         except:
           logger.error('could not create mount point!')
           return
         logger.info('mounting filesystem to '+Mnt+'...')
         try:
           cmd = ('mount -t '+Fs+' /dev/'+Dev+' '+Mnt+'')
           DPopen(cmd,'True') 
         except:
           logger.error('unable to mount filesystem!')
         if 'tmp' in Mnt:
           logger.info('adjusting permission for tmp dir...')
           cmd = ('chmod 1777 '+Mnt+'')
           DPopen(cmd,'True') 

       logger.info('adding to fstab...') 
       try:
         cmd = ('echo "/dev/'+Dev+' '+Mnt+' '+Fs+' '+mnt[3]+' '+str(mnt[4])+' '+str(mnt[5])+' " >> /etc/fstab')
         DPopen(cmd,'True') 
       except:
         logger.error('unable to add to fstab!')

  else: 
    logger.error('Neither parts nor mount specified, doing nothing!')

  logger.info('==== end ctype=%s filename=%s' % (ctype, filename))
