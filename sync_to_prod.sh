#!/bin/sh

dest_dir='/home/cloudadm/prod/cloud-init-context/'
rsync -av -L --delete --exclude=LAST_SYNC sync_to_prod/ ${dest_dir}

date > ${dest_dir}/LAST_SYNC
