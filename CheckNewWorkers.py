#!/usr/bin/python

# This script reads a list of newly instantiated WNs ("NewWorkers.log") and does:
# - connect to each worker and check for CloudInit summary file
# - get list of errors from summary file
# - chech if node is in PBS and in which state
# - mark for deletion nodes which finished the context with errors, 
#   which should be "offline" in PBS (output written in "DeleteWorkers.log")
# - print a summary table 

# mailto: svallero@to.infn.it

import os
import sys 
import xmldict
from termcolor import colored
import getpass
import shlex
from subprocess import Popen, PIPE
import prettytable
import datetime


# Some configuration 
infilename='NewWorkers.log'
summaryfilename='/var/log/cloud-summary.log'
ce='t2-ce-01.to.infn.it'
outfilename='DeleteWorkers.log'
outfile=open(outfilename,'wb')
outfile.write(''+str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+'\n')

# Command to be run at nodes to check summary file
#cmd_node='cat '+summaryfilename+' | grep "OK"'
cmd_node='cat '+summaryfilename+' | grep "ERROR"'

# Get root password for WNs and CE
print colored('Insert password for root...','green')
passwd = getpass.getpass()

# Creating prettytable
table = prettytable.PrettyTable(["ON ID", "Name", "Finished", "OK", "PBS state","Marked for deletion"])



print colored('Reading list of newly created nodes...','green')
infile=open(infilename)

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
 
# loop on all newly instantiated workers 
for line in infile.readlines():
   # init some variable
   finished='False'
   isok='False'
   inpbs='False'
   val='-'
   delete='False'
  
   if 'CE' not in line: # skip date
     on_id,hostname=line.split()
     print colored('Connecting to node '+hostname+'','green')
     print colored('Removing known_hosts entry...','yellow')
     os.system('ssh-keygen -R '+hostname+'')
     cmd=('sshpass -p '+passwd+' ssh -o StrictHostKeyChecking=no root@'+hostname+' '+cmd_node+'') 
     connect = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
     outdata,errdata = connect.communicate() 
     print colored('Checking for summary logfile...','yellow')
     if errdata:
        if 'No such file or directory' in errdata:
           finished='False'
           print 'Not found yet.'
        elif 'Warning: Permanently added' in errdata:
           finished='True'
        else: 
           # some other error, print it on screen
           finished='?'
           print colored(errdata,'red')
     else:
        finished='True'  
     
     if finished == 'True':
        print colored('Checking for errors...','yellow')
        if outdata:
           # some error detected, print it on screen 
           isok='False'
           print colored(outdata,'red')
        else:
           isok='True'
     else:
        isok='?'
     
     print colored('Check if node is in PBS...','yellow')
     if hostname in pbs_short:
        inpbs='True'
        val= pbs_short[hostname] # pbs-state
     else:
        inpbs='False'
        print ('Not yet...')


     # check if marked for deletion
     if finished=='True' and isok=='False': # contex finished with errors 
        delete='True' # it should be deleted anyway!
        if inpbs == 'True': # if added to PBS
           if 'offline' in val or 'down' in val: # it should be offline
              print colored('Node is up with errors (offline/down in PBS).','red')
              print colored('It should be excluded from PBS and shutdown.','red')
           else:
              delete = 'FATAL'
              print colored('Node is up with errors and '+val+' in PBS!!!','red')
              print colored('*** This should not have happened!!! ***','red')
              print colored('It should be EXCLUDED FROM PBS AS SOON AS POSSIBLE and shutdown.','red')
        if inpbs == 'False': # it was not even added to PBS
              print colored('Node is up with errors (but not in PBS).','red')
              print colored('It should be shutdown.','red')

     # write to table
     table.add_row([on_id,hostname, finished, isok, val, delete])
     # write to file candidates for deletion
     if delete != 'False':  
       outfile.write(''+on_id+' '+hostname+'\n')
print ''
print table
print ''
print colored('List of nodes marked for deletion in: ', 'green')
os.system('ls -rtlh '+outfilename+'')

