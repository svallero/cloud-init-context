######### HEADER STARTS HERE #############################

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
import logging

# Define logger
#logname = '/var/log/cloud-init-localfs.log'
#logname = 'test.log'
if not logname:
  logname = 'default.log'
loggername = (logname.strip('.log'))+('-logger')
logger = logging.getLogger(loggername)
logger.setLevel(logging.DEBUG)
logging.addLevelName(14, 'OK')
# create file handler which logs even debug messages
fh = logging.FileHandler(logname)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

##########################################################

def DPopen(command, shell):
  # Debug-Popen
  # Calls Popen and streams output to logger
  if shell == 'True':
    # This has to be used when there is a | or > in the command,
    # in order to use 'subprocess' and be able to raise exceptions 
    # (maybe not the most elegant way of doing it...)
    # It would be  simpler with 'os.system',
    # but it is deprecated (and does not raise exceptions!)
    proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
  else:
    proc = Popen(command, stdout=PIPE, stderr=PIPE)
    
  out,err= proc.communicate()
      
  for outline in out.splitlines():
    logger.debug(outline)
 
  for errline in err.splitlines():
    logger.debug(errline)

  # Returns output code for exceptions
  proc.wait()
  code = proc.returncode  
  if code != 0:
    raise error()

##########################################################

def get_embedded(file, content, destination):
  
  logger.info('getting embedded file...')
  text_file = open(file, "w")
  text_file.write(content)
  text_file.close()
  logger.info(''+file+' written')

  try:
    cmd = ('mv '+file+' '+destination+'/'+file+'')
    DPopen(shlex.split(cmd), 'False')
  except:
    logger.error('could not move file into place!')  

######### HEADER ENDS HERE ###############################

