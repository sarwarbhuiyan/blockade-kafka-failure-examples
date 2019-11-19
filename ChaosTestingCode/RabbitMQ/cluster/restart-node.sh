#!/bin/bash

set -e

if [ $1 = "rabbitmq1" ]; then
    blockade restart rabbitmq1
    R1_ID=$(blockade status | grep rabbitmq1 | awk '{ print $2 }')
    R2_IP_ADDR=$(blockade status | grep rabbitmq2 | awk '{ print $4 }')
    R3_IP_ADDR=$(blockade status | grep rabbitmq3 | awk '{ print $4 }')
    docker exec -it $R1_ID bash -c "cp /etc/hosts ~/hosts.new && echo $R2_IP_ADDR rabbitmq2 cluster_rabbitmq2 >> ~/hosts.new && cp -f ~/hosts.new /etc/hosts"
    docker exec -it $R1_ID bash -c "cp /etc/hosts ~/hosts.new && echo $R3_IP_ADDR rabbitmq3 cluster_rabbitmq3 >> ~/hosts.new && cp -f ~/hosts.new /etc/hosts"
    echo "rabbitmq1 restarted"
elif [ $1 = "rabbitmq2" ]; then
    # node 2 does not have rabbitmq-server as pid 1 and so stopping the container causes an unclean shutdown
    # therefore we do a controlled stop first
    R2_ID=$(blockade status | grep rabbitmq2 | awk '{ print $2 }')    
    docker exec -it $R2_ID rabbitmqctl stop_app
    
    # restart the container
    blockade restart rabbitmq2
    
    # update the hosts file again for visibility
    R1_IP_ADDR=$(blockade status | grep rabbitmq1 | awk '{ print $4 }')
    R3_IP_ADDR=$(blockade status | grep rabbitmq3 | awk '{ print $4 }')    
    docker exec -it $R2_ID bash -c "cp /etc/hosts ~/hosts.new && echo $R3_IP_ADDR rabbitmq3 cluster_rabbitmq3 >> ~/hosts.new && cp -f ~/hosts.new /etc/hosts"
    echo "rabbitmq2 restarted"

elif [ $1 = "rabbitmq3" ]; then
    # node 3 does not have rabbitmq-server as pid 1 and so stopping the container causes an unclean shutdown
    # therefore we do a controlled stop first
    R3_ID=$(blockade status | grep rabbitmq3 | awk '{ print $2 }')    
    docker exec -it $R3_ID rabbitmqctl stop_app
        
    # restart the container
    blockade restart rabbitmq3
    
    # update the hosts file again for visibility
    R1_IP_ADDR=$(blockade status | grep rabbitmq1 | awk '{ print $4 }')
    R2_IP_ADDR=$(blockade status | grep rabbitmq2 | awk '{ print $4 }')
    docker exec -it $R3_ID bash -c "cp /etc/hosts ~/hosts.new && echo $R2_IP_ADDR rabbitmq2 cluster_rabbitmq2 >> ~/hosts.new && cp -f ~/hosts.new /etc/hosts"
    echo "rabbitmq3 restarted"
fi
