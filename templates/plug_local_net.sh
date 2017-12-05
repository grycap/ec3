#!/bin/bash
# This script mounts an overlay network passed as argument in the front end host and registers in the namespace of every slave node the IP and MAC of this host node.
# It also requires the script plug_remote.sh which is copied in all the nodes.
#
# Example: ./plug_local_net.sh bigsea-net
# The network should have been created already
# A consul keystore is required:
# sudo docker run -dit --name consul -p 8500:8500 consul consul agent -server -dev -ui -client 0.0.0.0
# sudo docker network create --driver overlay --subnet=10.0.9.0/24 bigsea-net

NET_NAME=$1
NETNS_DIR=/var/run/netns
NODEPREFIX=bsintwn

# In order to access the namespace of the overlay network, we must create a container with such network. We reuse the name to avoid overloading with idle containers.
docker stop ${NET_NAME}_console_fe 2> /dev/null
docker rm ${NET_NAME}_console_fe 2> /dev/null 
docker run -d -i --name ${NET_NAME}_console_fe --net=${NET_NAME} alpine ash 

# Then we get the namespace of the network, which is preceeded by a number "1-", "2-" and so on, depending on some external factors. The same network may have different prefixes in different nodes.
DOCKERNET_ID=$(docker inspect -f "{{.ID}}" ${NET_NAME})
NET_NAMESPACE_SUFFIX="$(echo ${DOCKERNET_ID} | sed -e 's/^\(..........\).*$/\1/')"
NET_NAMESPACE="$(ls /var/run/docker/netns/*-${NET_NAMESPACE_SUFFIX} | xargs -n 1 basename)"
echo "Network $NET_NAME has suffix $NET_NAMESPACE_SUFFIX and namespace $NET_NAMESPACE"

# Then we create a VETH pair and plug the peer 1 in the bridge br0 of the namespace
# The script checks if the VETH pair already exists and removes it.
VETHPAIR0=red0
VETHPAIR1=red1
MAC="02:42:0a:00:0a:dc"
RANGE=$(docker network inspect  -f "{{(index (index .IPAM.Config) 0).Subnet}}" ${NET_NAME})
IPMASK=$(echo $RANGE | sed -e 's/^\([0-9]*\.[0-9]*\.[0-9]*\)\.[0-9]*\//\1\.220\//') 
IP=$(echo $RANGE | sed -e 's/^\([0-9]*\.[0-9]*\.[0-9]*\)\.[0-9]*\/.*$/\1\.220/') 

echo "Net ${NET_NAME} has ${NET_NAMESPACE} Namespace"

if [ ! -d $NETNS_DIR ]; then

  echo "Creating a namespace link in the host and assiging IP: $IP to VETH: $VETHPAIR0"
  sleep 3

  mkdir -p ${NETNS_DIR}
  ln -s /var/run/docker/netns/${NET_NAMESPACE} ${NETNS_DIR}

  if [[ ! -z $(ip link show $VETHPAIR0 2>/dev/null) ]]
  then 
     echo "Deleting existing previous $VETHPAIR0"
     ip link delete $VETHPAIR0
  fi

  if [[ ! -z $(ip link show $VETHPAIR1 2>/dev/null) ]]
  then 
     echo "Deleting existing previous $VETHPAIR1"
     ip link delete $VETHPAIR1
  fi

  echo "Creating VETH pair"
  ip link add $VETHPAIR0 mtu 1450 type veth peer name $VETHPAIR1 mtu 1450
  ip link set dev $VETHPAIR1 netns ${NET_NAMESPACE}

  echo "Plugging VETH pair"
  ip netns exec ${NET_NAMESPACE} ip link set dev $VETHPAIR1 master br0
  ip netns exec ${NET_NAMESPACE} ip link set dev $VETHPAIR1 up

  # Then, it assigns an IP and a MAC to the peer 0 of the VETH pair

  echo "Aading IP and MAC VETH pair"
  ip addr add dev $VETHPAIR0 $IPMASK
  ip link set dev $VETHPAIR0 address $MAC
  ip link set dev $VETHPAIR0 up

fi
# The most hacking part is to update the ARP tables in the working nodes, by adding the IP and the MAC manually.
# This requires to create a container in the node to make the NAMESPACE visible in the node.
# In the case that this is executed twice, the IP can exist, so we use add and replace to ensure that at least one of this operations work.
# All the logic is inside the plug_remote.sh script.
# Finally, we ping the container from the master to trigger the completion of the ARP tables. THIS IS NECESSARY.
#
# NOTE: We have not tested the possibility of updating the ARP table inside the Docker.
# NOTE2: The part in the SSH must be executed as part of the working node configuration, but, the front needs to know the IP of the container. 

echo "Updating routing table in nodes"
for host in $(cat /etc/hosts | grep "$NODEPREFIX" | grep -v 127.0.0.1 | awk '{print $1}' ) 
do  
  echo "In $host"
  REMOTE_OUT=$(ssh $host ./var/tmp/plug_remote.sh $host ${NET_NAME} ${NET_NAMESPACE_SUFFIX} $IP $MAC)
  CONT_IP=$(echo $REMOTE_OUT | sed -e 's/^.* inet \([0-9\.]*\).*$/\1/')
  echo "Container IP:$CONT_IP"
  ping -c 1 $CONT_IP
  sleep 10
done

