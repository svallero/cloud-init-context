#!/bin/bash

#
# Vers. 3 Uso pbsinfo.rb (Tue Jan 24 19:19:50 CET 2012 Dario)
# Vers. 2 Tolte 2 slot per cert (Mon Dec 19 11:12:35 CET 2011 Ste.)
#

#NUMSLOT=`/root/scripts/quanteslot.sh | grep -v "to.infn.it"`
NUMSLOT=`/root/scripts/pbsinfo.rb -s`
date
NUMSLOTNEW=`expr ${NUMSLOT} - 2`

echo "Setting MAXJOB to ${NUMSLOTNEW}" 
/usr/bin/changeparam QOSCFG[normal] MAXJOB=${NUMSLOTNEW}
