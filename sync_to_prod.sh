#!/bin/sh

dest_dir='/home/cloudadm/prod/cloud-init-context/'
files='
apel/*
CheckNewWorkers.py
CreateWNBase.sh 
DeleteNewWorkers.py 
IncludeModules.txt
LaunchEWN.sh 
LaunchNewWorkers.sh
LaunchService.sh
LaunchAPEL.sh
WriteMIME.py
cloud-init-files/CE
cloud-init-files/SE
cloud-init-files/WN
cloud-init-files/*.py
config/ConfigureCE.ccfg 
config/ConfigureAPEL.ccfg 
config/ConfigureEWN.ccfg
config/ConfigureSE.ccfg
config/ConfigureWN.ccfg
config/ConfigureWNBase.ccfg
cloud.cfg
sensitivedata_CE
sensitivedata_SE
sensitivedata_WN
sensitivedata_APEL
'

rsync -av -R -L --delete --exclude=LAST_SYNC ${files} ${dest_dir}

date > ${dest_dir}/LAST_SYNC
