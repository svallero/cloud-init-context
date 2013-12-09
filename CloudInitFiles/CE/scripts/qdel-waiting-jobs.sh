#|/bin/bash
# [dberzano] qdel -p on all waiting jobs
# Anche chiamato "lo sturoduro"
qstat -1n | grep ' W ' | awk '{ print $1 }' | xargs -L1 qdel -p
