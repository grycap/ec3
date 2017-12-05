#!/bin/bash
HOST=$1
NET_NAME=$2
NET_NAMESPACE_SUFFIX=$3
IP=$4
MAC=$5

docker stop ${NET_NAME}_console_${HOST} 2>/dev/null
docker rm ${NET_NAME}_console_${HOST} 2>/dev/null
docker run -d -i --name ${NET_NAME}_console_${HOST} --net=${NET_NAME} alpine ash 
mkdir -p /var/run/netns  
ln -s -f /var/run/docker/netns/*-${NET_NAMESPACE_SUFFIX} /var/run/netns
ip netns exec $(ls /var/run/docker/netns/*-${NET_NAMESPACE_SUFFIX} | xargs -n 1 basename) ip neighbor add $IP lladdr $MAC dev vxlan0
ip netns exec $(ls /var/run/docker/netns/*-${NET_NAMESPACE_SUFFIX} | xargs -n 1 basename) ip neighbor replace $IP lladdr $MAC dev vxlan0
docker exec -i ${NET_NAME}_console_${HOST} ip addr show eth0
