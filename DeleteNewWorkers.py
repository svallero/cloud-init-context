#!/usr/bin/python

# This script reads a list of nodes marked for deletion ("DeleteNodes.log") and does:
# - remove from PBS (if "offline")
# - shutdown corresponding VM in OpenNebula

# mailto: svallero@to.infn.it

# Some configuration 
infilename='DeleteWorkers.log'
ce='t2-ce-01.to.infn.it'

import os
import sys
import xmldict
from termcolor import colored
import getpass
import shlex
from subprocess import Popen, PIPE
import prettytable
import datetime


# Get root password for WNs and CE
print colored('Insert password for root...','green')
passwd = getpass.getpass()

# Read list of pbs nodes
print colored('Reading list of PBS nodes...','green')
cmd_ce=('sshpass -p '+passwd+' ssh -o StrictHostKeyChecking=no root@'+ce+' pbsnodes -x')
connect = Popen(shlex.split(cmd_ce), stdout=PIPE, stderr=PIPE)
outdata,errdata = connect.communicate()
if errdata:
  # could not query PBS server
  # print error message 
  print colored(errdata,'red')
  sys.exit()
else:
  # convert xml in python dictionary
  pbsdict = xmldict.xml_to_dict(outdata)
  pbs_short={}
  nodes=pbsdict['Data']['Node']
  for i in nodes:
     name, state = i['name'], i['state']
     # write small dictionary with hostname and PBS state
     pbs_short[name]=state

# loop on nodes marked for deletion
print colored('Reading list of nodes marked for deletion from:','green')
os.system('ls -rtlh '+infilename+'')
infile=open(infilename)
okpbs='True'
for line in infile.readlines():
   if 't2-vwn' in line: # skip date
      on_id,hostname=line.split() 
      print colored('Processing node '+hostname+'', 'green')
      # check if node is on PBS and offline
      if hostname in pbs_short:
         state= pbs_short[hostname] # pbs-state
         if state == 'offline':
            print colored('Deleting node from PBS...', 'yellow')
            cmd_del_pbs=('sshpass -p '+passwd+' ssh -o StrictHostKeyChecking=no root@'+ce+' \'qmgr -c \"delete node '+hostname+'\"\'')
            connect = Popen(cmd_del_pbs,shell='False', stdout=PIPE, stderr=PIPE)
            outdata,errdata = connect.communicate()
            if outdata:
               print outdata
            if errdata: 
               print colored(errdata,'red')
               okpbs='False' 
         else:
            print colored('Node '+hostname+' is in state '+state+' (expected offline)','red') 
            print colored('I\'m not going to delete it from PBS, please check by hand!','red')
            okpbs='False' 
      else: 
         print ('Node '+hostname+' is not on PBS, doing nothing.')

      if okpbs=='True': #node was correctly removed from pbs
         print colored('Shutting-down in OpenNebula...', 'yellow')
         cmd=('euca-terminate-instances '+on_id+'')
         connect = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
         outdata,errdata = connect.communicate()
         if outdata:
            print outdata
         if errdata: 
               print clored(errdata,'red')
      else:
         print colored('Node was not removed properly from PBS.', 'red')
         print colored('I\'m not going to shutdown the VM. Please check by hand!', 'red')
