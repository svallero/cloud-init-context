#!/bin/bash

#
# stage-one.sh -- by Dario Berzano <dario.berzano@cern.ch>
#
# A tool to stage ONE from a given Git repository onto a build directory and to
# compile it as self-contained.
#
# Many variables are set inside this file, except source repository which must
# be given as an argument, relative to $SRCROOT (see code).
#
# This script aborts if run as root for safety reasons!
#

#
# Global variables
#

# The parent directory of all user repositories
SRCROOT='/home/oneadmin/devel'

# Source directory (under SRCROOT): will be set in Main()
SRC=''

# Base of the destination build directory
DSTBUILD_BASE='/home/oneadmin/.one-build'

# The destination running directory (ONE selfcontained)
DSTRUN='/srv/cloud/one'

# User that is supposed to run this script
SUSER='oneadmin'

# MySQL stuff
MYSQL_PWD='pp84qy7y3szMKc9v'
MYSQL_USER='oneadmin'
MYSQL_DB='one'
MYSQL_SERVER='localhost'
MYSQL_PORT='3306'
MYSQL_BACKUP_PREFIX='/home/oneadmin/backups/onedb'

# This errorcode is considered by Exec() as a skip code
ERR_SKIP=120

#
# Functions
#

# Wraps a given command and shows the output only if an error occurs (signalled
# by a nonzero return value). Output is colored
function Exec() {
  local FATAL=0
  if [ "$1" == "-f" ]; then
    FATAL=1
    shift
  fi
  local NAME="$1"
  local R
  local LOG=$(mktemp)

  shift
  echo -n "[....] $NAME"
  "$@" > $LOG 2>&1
  R=$?
  if [ $R == 0 ]; then
    echo -e "\r[ \e[32mOK\e[m ] $NAME"
  elif [ $R == $ERR_SKIP ]; then
    echo -e "\r[\e[33mNCMD\e[m] $NAME"
  else
    echo -e "\r[\e[31mFAIL\e[m] $NAME"
    if [ -s "$LOG" ]; then
      echo -e "\e[36m===== Begin of log dump =====\e[m"
      cat $LOG
      echo -e "\e[36m===== End of log dump =====\e[m"
    fi
    if [ $FATAL == 1 ]; then
      echo -e "\e[31mFatal error: aborting execution\e[m"
      rm -f $LOG
      exit 1
    fi
    R=1
  fi
  rm -f $LOG
  return $R
}

# Get current branch
function GetBranch() {
  local GITDIR="$1"
  ( cd "$GITDIR" ; git branch | grep '^*' | cut -b3- )
}

# A date including timezone in a format like this: 20120502-114128-CEST
function Date() {
  date +%Y%m%d-%H%M%S-%Z
}

# mysqldump on ONE database
function DumpOneDb() {
  mysqldump -u $MYSQL_USER --password=$MYSQL_PWD -l --databases $MYSQL_DB | \
    xz -9 > "$MYSQL_BACKUP_PREFIX"/`Date`.sql.xz
  return $?
}

# Main function
function Main() {

  local R
  local FASTSYNC=1

  # Hard syncing?
  if [ "$1" == "--hard" ]; then
    FASTSYNC=0
    shift
  fi

  # The user repository
  if [ "$1" == "" ]; then
    echo -e "\nUsage: $0 <user_repository>\n"
    exit 1
  else
    export SRC="$SRCROOT/$1"
    if [ -d "$SRC/.git" ]; then
      SRC=$(cd "$SRC" ; pwd)
      DSTBUILD="$DSTBUILD_BASE/$(basename "$SRC")"
      mkdir -p "$DSTBUILD"
      DSTBUILD=$(cd "$DSTBUILD" ; pwd)
    else
      echo -e "\e[31mSpecified Git repository does not exist!\e[m"
      exit 4
    fi
  fi

  # Check user
  if [ $(whoami) == "root" ]; then
    echo -e "\e[31mDamage protection: can not run as root!\e[m"
    exit 2
  elif [ $(whoami) != $SUSER ]; then
    echo -e "\e[31mCan be run only as $SUSER\e[m"
    exit 5
  fi

  # Some information
  echo ""
  echo "All changes will be staged onto:"
  echo "  $DSTBUILD"
  echo ""
  echo "After building, ONE will be run from:"
  echo "  $DSTRUN"
  echo ""
  echo "Files will be staged from Git repository:"
  echo "  $SRC"
  echo ""
  echo "Active branch on that repository:"
  echo "  "$(GetBranch "$SRC")
  echo ""
  echo "Destination build directory is (newer files won't be overwritten):"
  echo "  $DSTBUILD"
  echo ""
  echo "ONE self-contained destination (config files won't be overwritten):"
  echo "  $DSTRUN"
  echo ""
  echo "Destination directory of the compressed database dump:"
  echo "  $MYSQL_BACKUP_PREFIX"
  echo ""
  echo -n "Do you want to proceed? (y/n) "
  read R
  if [ ${R:0:1} != "y" ] && [ ${R:0:1} != "Y" ]; then
    echo -e "\e[31mAborted by user\e[m"
    exit 3
  fi

  # Go! Go!!
  echo ""
  echo -e "\e[33mStopping services...\e[m"

  # Preamble: stop Sunstone and ONE
  Exec "Stopping Sunstone" sunstone-server stop
  Exec "Stopping accountng" oneacctd stop
  Exec "Stopping ONE" one stop

  echo ""
  echo -e "\e[33mBackup and update...\e[m"

  # mysqldump on database
  Exec -f 'Backupping ONE database' DumpOneDb

  # This rsync is without --delete and with -u
  if [ $FASTSYNC == 1 ]; then
    Exec -f "Updating files into build directory" \
      rsync -au --exclude '*/.git' --exclude '**/.git' \
      "${SRC}/" "${DSTBUILD}/"
  else
    Exec -f "Hard-syncing files into build directory" \
      rsync -a --delete --exclude '*/.git' --exclude '**/.git' \
      "${SRC}/" "${DSTBUILD}/"
  fi

  echo ""
  echo -e "\e[33mBuild and install...\e[m"

  # Running SCons
  Exec -f "Moving into build directory" cd "$DSTBUILD"
  Exec -f "Running SCons (might take time)" scons mysql=yes

  # Installing (keeping configuration files)
  Exec -f "Checking if destination $DSTRUN exists" [ -d "$DSTRUN" ]
  if [ -e "$DSTRUN/etc/oned.conf" ]; then
    Exec -f 'Installing as self-contained: keeping current configuration' \
      ./install.sh -d "$DSTRUN" -k
  else
    Exec -f 'Installing as self-contained: new configuration will be created' \
      ./install.sh -d "$DSTRUN"
  fi

  # Sanitize environment
  unset SRC

  echo ""
  echo -e "\e[33mStarting services...\e[m"

  # Restart all services
  Exec -f "Starting ONE" one start
  Exec -f "Starting accounting" oneacctd start
  Exec -f "Starting Sunstone" sunstone-server start

  # All OK
  echo -e "\n\e[32mAll OK!\e[m"

}

#
# Entry point
#

Main "$@"
