#!/bin/bash

set -e

blockade destroy
#find ./volumes ! -name '.*' ! -type d -exec rm -f -- {} +
blockade up
sleep 5
bash update-hosts.sh
sleep 5
bash create-topic.sh kafka1 test1
