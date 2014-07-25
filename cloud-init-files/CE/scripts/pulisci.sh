#!/bin/sh

#604800 secondi = 7 giorni
DELTAT=604800
NODELISTFILE=/var/local/nodelistfile
DOWNLISTFILE=/tmp/downnodeslistfile
NODOTROVATO=/tmp/downnodefnd

pbsnodes -l   |  cut -d '.' -f1 > ${DOWNLISTFILE}

touch ${NODELISTFILE}

DOWNNODES=( `cat ${DOWNLISTFILE} `)

for node in "${DOWNNODES[@]}"
do
###echo $node
ping  -q -c 10 $node 2>&1 >/dev/null

if [ $? -gt 0 ]; 
 then 
### echo "$node is unreachable ";

 grep $node ${NODELISTFILE} >${NODOTROVATO}
 if [ $? -gt 0 ];
  then ORA=`date`;
   echo -n $ORA
   echo "non trovato .. aggiunto"
  NOW=`date +"%s"`
  echo "$node ${NOW} ${NOW}" >> ${NODELISTFILE}
 else
###  echo " trovato";
  NOW=`date +"%s"`
  FIRSTIME=`grep $node ${NODELISTFILE} |  cut -d ' ' -f2`
###  echo ${FIRSTIME}
  sed -i s/${FIRSTIME}/${NOW}/ ${NODELISTFILE}
 fi
 
else
  ORA=`date`;
  echo -n $ORA
  echo "$node is reachable  elimino $node"  
  sed -i "/$node/d" ${NODELISTFILE}
fi

done


#--- Step 2 : delay


while read inputline
do
  HOST="$(echo $inputline | cut -d" " -f1)"
  TIME1="$(echo $inputline | cut -d" " -f2)"
  TIME2="$(echo $inputline | cut -d" " -f3)"
  DIFF=$[${TIME1}  -  ${TIME2}]
  ORA=`date`
  echo -n $ORA

  echo -n "node ${HOST} is unreach for ${DIFF} sec. "

  if [[ "${DIFF}" -gt "${DELTAT}" ]];
    then
    echo "more than ${DELTAT} "
  else
    echo
  fi
done < ${NODELISTFILE}

