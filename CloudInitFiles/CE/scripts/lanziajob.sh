#!/bin/sh
#
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-011.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-012.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-023.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-024.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-015.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-026.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-037.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-028.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-029.to.infn.it $i; done
for i in `qstat -1n | grep W | cut -d"." -f1 | head -5`; do qrun -H t2-wn-030.to.infn.it $i; done
