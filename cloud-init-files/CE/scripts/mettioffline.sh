#!/bin/sh

#for I in 33 34 36
for I in {11..36}
do
  echo "----------------------------------------------------------------"
#  echo "qmgr -c \"create node t2-wn-0$I.to.infn.it\""
#  qmgr -c "create node t2-wn-0$I.to.infn.it"

#  echo "qmgr -c \"set node t2-wn-0$I.to.infn.it properties = lcgpro\""
#  qmgr -c "set node t2-wn-0$I.to.infn.it properties = lcgpro"

#  echo "qmgr -c \"set node t2-wn-0$I.to.infn.it np = 1\"" 
#  qmgr -c "set node t2-wn-0$I.to.infn.it np = 1"  
 
  echo "qmgr -c \"set node t2-wn-0$I.to.infn.it state = offline\""
  qmgr -c "set node t2-wn-0$I.to.infn.it state = offline"  

done
