#!/bin/sh

# Run it in the dir where "WriteMIME.py" is!
# This scripts instantiates a number of WNs uing the EC2 API

# mailto: svallero@to.infn.it

# Configuration goes here: ########
##number=2
number=1
slots=8 # can be 6 or 8
config_file="config/ConfigureWN.ccfg"
list_modules="IncludeModules.txt"
image="ami-00000344"
flavour="t2.wn.${slots}slot"
outfile="NewWorkers.log"
###################################

echo -e "\e[32mI'm going to instantiate $number nodes with the following configuration:\e[0m"
echo -e "\e[33mConfiguration file:\e[0m $config_file"
echo -e "\e[33mList of modules:\e[0m $list_modules"
echo -e "\e[33mBase image:\e[0m $image"
echo -e "\e[33mFlavour:\e[0m $flavour (= $slots job slots)"

echo -e "\e[32mIs this ok (yes/no)?\e[0m"
read conf
if [ "$conf" == "yes" ]; then
  echo "I go for it..."
else
  echo "Aborting."
  exit
fi

echo -e "\e[32mWriting temporary list...\e[0m"
echo "${list_modules}:x-include-url" > tmp.txt
echo "${config_file}:multiple-config" >> tmp.txt
echo -e "\e[32mCreating user-data archive...\e[0m"
name=`echo $config_file | grep -o -P '(?<=Configure).*(?=.ccfg)'`
userdata="userdata${name}.txt.gz"
./WriteMIME.py tmp.txt
ls -rtlh $userdata
echo $PWD/$userdata
rm tmp.txt
echo -e "\e[32mRunning command:\e[0m"
echo `date` > $outfile
cmd="euca-run-instances $image -t $flavour -f $userdata -n $number"
echo $cmd 


$cmd | sed 1d | \
#euca-describe-instances | sed 1d | \
while read i
do
  a=($i)
  id_on=${a[1]}
  ip_last=`echo ${a[3]} | cut -c 11-13`
  ip_last_z=`printf %03d $ip_last`
  echo "$id_on t2-vwn-$ip_last_z.to.infn.it" >> $outfile
done
 
echo -e "\e[32mList of new instances and hostnames written in:\e[0m"
ls -rtlh $outfile
