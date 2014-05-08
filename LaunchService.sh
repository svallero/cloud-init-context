#!/bin/sh

# Run it in the dir where "WriteMIME.py" is!
# This scripts instantiates a number of WNs uing the EC2 API

# mailto: svallero@to.infn.it

# Configuration goes here: ########
config_file="ConfigureMyProxy.ccfg"
list_modules="IncludeModules.txt"
image="ami-00000363"
flavour="t2.myproxy"
outfile="NewService.log"
###################################

echo -e "\e[32mI'm going to instantiate a service with the following configuration:\e[0m"
echo -e "\e[33mConfiguration file:\e[0m $config_file"
echo -e "\e[33mList of modules:\e[0m $list_modules"
echo -e "\e[33mBase image:\e[0m $image"
echo -e "\e[33mFlavour:\e[0m $flavour"

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
#exit
rm tmp.txt

echo -e "\e[32mRunning command:\e[0m"
echo `date` > $outfile
cmd="euca-run-instances $image -t $flavour -f $userdata"
echo $cmd 


$cmd | sed 1d | \
#euca-describe-instances | sed 1d | \
while read i
do
  a=($i)
  id_on=${a[1]}
  ip_last=`echo ${a[3]} | cut -c 11-13`
  echo "$id_on t2-vwn-$ip_last.to.infn.it" >> $outfile
done
 
echo -e "\e[32mList of new instances and hostnames written in:\e[0m"
ls -rtlh $outfile
