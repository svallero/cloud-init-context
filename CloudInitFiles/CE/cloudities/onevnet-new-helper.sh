#!/bin/bash

#
# onevnet-new-helper.sh -- by Dario Berzano <dario.berzano@cern.ch>
#
# Helper to receive commands remotely from onevnet-new.rb. It features a
# protection against Bash code injection.
#

Mode=''
VnetTpl=''

while read Line ; do

  # Make line safe against code injections
  SafeLine=$( echo "$Line" | sed -e 's/\([^ a-zA-Z0-9-]\)/\\\1/g' )

  if [ "$Mode" == '' ] ; then

    # First line is mode; also, skip initial empty lines
    Mode="$Line"

  elif [ "$Mode" == 'onevnet' ] ; then

    if [ "$VnetTpl" == '' ] ; then
      # Prepares OpenNebula vnet template
      VnetTpl=$( mktemp /tmp/onevnet-tpl-XXXXX )
    fi

    echo "$Line" >> "$VnetTpl"

  elif [ "$Mode" == 'cobbler' ] ; then

    # Adds hosts to Cobbler
    SafeLine="cobbler $SafeLine >&2"

    eval "$SafeLine" > /dev/null
    RetVal=$?

    if [ $? != 0 ] ; then
      echo "Failed: $SafeLine" >&2
      exit $RetVal
    fi

  else

    # Invalid data received from stdin
    echo 'Invalid mode, aborting.' >&2
    exit 1

  fi

done

if [ "$Mode" == 'onevnet' ] && [ "$VnetTpl" != '' ]; then

  # Adds network to OpenNebula
  onevnet create $VnetTpl >&2
  RetVal=$?

  rm -f $VnetTpl
  exit $RetVal

elif [ "$Mode" == 'cobbler' ] ; then

  # Synchronizes information with dnsmasq (hosts, ethers)
  cobbler sync > /dev/null 2>&1
  exit $?

fi
