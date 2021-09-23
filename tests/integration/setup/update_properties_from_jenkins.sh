#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -i 00.00.00.00 -u xyz -p **** -I 00.00.00.00 -U zxy -P **** -w abc@in.ibm.com -r HMC910"
   echo -e "\t-i IP Add of the HMC to be created"
   echo -e "\t-u User name of the HMC"
   echo -e "\t-p Password of the HMC"
   echo -e "\t-I IP Add of the NFS Server"
   echo -e "\t-U Username of the NFS Server"
   echo -e "\t-P Password of the NFS Server"
   echo -e "\t-w w3username"
   echo -e "\t-r Release version of the HMC"
   exit 1 # Exit script after printing help
}

#while getopts "hmcip:hmcuser:hmcpass:nfsip:nfsuser:nfspass:w3user:hmcver:" opt
while getopts "i:u:p:I:U:P:w:r:" opt
do
   case "$opt" in
      i ) hmc_ip="$OPTARG" ;;
      u ) hmc_username="$OPTARG" ;;
      p ) hmc_password="$OPTARG" ;;
      I ) nfs_host="$OPTARG" ;;
      U ) nfs_host_user="$OPTARG" ;;
      P ) nfs_host_password="$OPTARG" ;;
      w ) w3user="$OPTARG" ;;
      r ) hmc_release="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$hmc_ip" ] || [ -z "$hmc_username" ] || [ -z "$hmc_password" ] || [ -z "$nfs_host" ] || [ -z "$nfs_host_user" ] || [ -z "$nfs_host_password" ] || [ -z "$w3user" ] || [ -z "$hmc_release" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

#Update the HMC and NFS Details
echo "updating hmc host in inventory_hmc file..."
sed -i "/\[host\]/!b;n;c${hmc_ip}" inventory_hmc

echo "updating nfs host in inventory_nfs file..."
sed -i "/\[host\]/!b;n;c${nfs_host}" inventory_nfs
echo "updating nfs host username in inventory_nfs file..."
sed -i "/ansible_user/c\ansible_user=${nfs_host_user}" inventory_nfs
echo "updating nfs host password in inventory_nfs file..."
sed -i "/ansible_password/c\ansible_password=${nfs_host_password}" inventory_nfs
echo "updating w3user in inventory_nfs file..."
sed -i "/w3user/c\w3user=${w3user}" inventory_nfs
echo "updating hmc_ip in inventory_nfs file..."
sed -i "/hmc_ip/c\hmc_ip=${hmc_ip}" inventory_nfs
echo "updating hmc_release in inventory_nfs file..."
sed -i "/hmc_release/c\hmc_release=${hmc_release}" inventory_nfs

echo "updating hmc_ip in integration_config.yaml file"
sed -i "/inventory_hostname:/c\inventory_hostname: ${hmc_ip}" ../integration_config.yml
echo "updating hmc_username in integration_config.yaml file"
sed -i "/username:/c\   username: ${hmc_username}" ../integration_config.yml
echo "updating hmc_password in integration_config.yaml file"
sed -i "/password:/c\   password: ${hmc_password}" ../integration_config.yml

