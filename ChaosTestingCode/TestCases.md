# Failure Scenarios

## Pre-step

Open up two terminals and vagrant ssh into the VM.

In terminal 1:

```
$ cd /vagrant/ChaosTestingCode/Kafka/cluster
$ blockade up
$ bash update-hosts.sh

```

In terminal 2:

```
cd /vagrant/ChaosTestingCode/Kafka/client
```



## Scenario 1 - Fire-and-forget with a failed node and partition leader fail-over

Create the test topic:

```
bash create-topic.sh kafka1 test1
```
Keep a note of which is the leader. 

In the client terminal, start publishing 100000 at a rate of 1000/sec with acks=0
```
python producer.py 100000 0.001 0 test1
```

When it reaches 30000, kill the leader, e.g if the leader was 2, run.
```
blockade kill kafka2
```

You may or may not see warning messages in the producer output like

```
%3|1537022288.472|FAIL|rdkafka#producer-1| [thrd:172.17.0.5:9094/bootstrap]: 172.17.0.5:9094/3: Receive failed: Connection reset by peer
%3|1537022288.472|ERROR|rdkafka#producer-1| [thrd:172.17.0.5:9094/bootstrap]: 172.17.0.5:9094/3: Receive failed: Connection reset by peer
%3|1537022288.572|FAIL|rdkafka#producer-1| [thrd:172.17.0.5:9094/bootstrap]: 172.17.0.5:9094/3: Connect to ipv4#172.17.0.5:9094 failed: Connection refused
%3|1537022288.572|ERROR|rdkafka#producer-1| [thrd:172.17.0.5:9094/bootstrap]: 172.17.0.5:9094/3: Connect to ipv4#172.17.0.5:9094 failed: Connection refused
```

The producer will  end  with how many messages it thinks it has delivered with the given ack
```
Sent: 100000
Delivered: 100000
Failed: 0
```

However, what's actually reported in the high watermark?
```
bash print-hw.sh kafka2 19093 test1
```

Here the high watermark may or may not be equal to what the producer thought  it delivered
```
test1:0:99979
```


## Scenario 2 - Acks=1 with a failed node and partition leader fail-over

Recreate cluster and partition

```
bash  reset-cluster.sh
```

Now we starting sending the 100000 messages, with acks=1.

```
python producer.py 100000 0.001 1 test1
```

Kill the leader at around 30000 messages.

```
blockade kill kafka1
```

We can see some send failures:

```
Success: 10000 Failed: 0
Success: 20000 Failed: 0
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
KafkaError{code=_TRANSPORT,val=-195,str="Local: Broker transport failure"}
Success: 29974 Failed: 26
Success: 39974 Failed: 26
Success: 49974 Failed: 26
Success: 59974 Failed: 26
Success: 69974 Failed: 26
Success: 79974 Failed: 26


Success: 89974 Failed: 26
Success: 99974 Failed: 26
Sent: 100000
Delivered: 99974
Failed: 26
```

Let's check the high watermark:

```
$ bash print-hw.sh kafka1 19092 test1
test1:0:99974
```

We see that all survived the fail-over.


Let's reset the cluster

```
$ bash reset-cluster.sh
```

Let’s rerun the scenario with ten producers, each sending 100000 messages at the same time. For this I run the python script from a bash script, running concurrently as background jobs.

```
$ bash concurrent-producer-silent.sh 100000 0.0001 1 test1
```

At 10 seconds in, kill the leader.
```
$ blockade kill kafka3
```

The client shows less than 100000 acknowledgements:
```
Runs complete
Acknowledged total: 846117
```

Checking the high watermark:
```
$ bash print-hw.sh kafka1 19092 test1
test1:0:846037
```

As we can see we have less committed than what the producers received in ACKs as as such we have lost data.


Scenario 3 - Acks=all with a failed node and partition leader fail-over (No message loss)


Reset cluster as above and run the following:

```
bash concurrent-producer-silent.sh 100000 0.0001 all test1
Runs complete
Acknowledged total: 801679
```

Check high watermark:
```
$ bash print-hw.sh kafka1 19092 test1
test1:0:801683
```

The high watermark is actually higher than what was acknowledged to the producer so we have not lost any messages.


## Scenario 4 - Completely Isolate Leader from other Kafka nodes and Zookeeper with acks=1

Reset the cluster.
```
bash reset-cluster.sh
```

Let's run the simple producer again and them midway partition the leader:

```
python producer.py 100000 0.0001 1 test1
```

In my run, the leader was broker 3 so I ran:
```
blockade partition kafka3
```

I saw a lot of messages like:
```

KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
Success: 95513 Failed: 4487
Sent: 100000
Delivered: 95513
Failed: 4487

```

Let's check the high watermark.

```
$ bash print-hw.sh kafka1 19092 test1
test1:0:59925

```

This has done very poorly. We only have 59925 vs 95513 according to the ACKs the producer received.

Let's check that the failover actually happened:
```
bash print-topic-details.sh kafka2 test1
Topic:test1	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: test1	Partition: 0	Leader: 2	Replicas: 3,2,1	Isr: 2,1
```


We can check what is going on with a slow producer. Reset the cluster and run the following slow producer:

```
python slow-producer.py 100 1 1 test1
```

After a few messages, partition the leader:
```
blockade partition kafka1
```

There's a long wait period and then  messages  like:

```
ERROR! Value: 79 Offset: none Error: Local: Message timed out
ERROR! Value: 80 Offset: none Error: Local: Message timed out
ERROR! Value: 81 Offset: none Error: Local: Message timed out
ERROR! Value: 82 Offset: none Error: Local: Message timed out
ERROR! Value: 83 Offset: none Error: Local: Message timed out
ERROR! Value: 84 Offset: none Error: Local: Message timed out
Partition fail-over, messages lost: 10
Value: 85 Offset: 13
Value: 86 Offset: 14
Value: 87 Offset: 15
Value: 88 Offset: 16
```

Checking logs of the partitioned broker:

```
Caused by: java.nio.channels.UnresolvedAddressException
	at sun.nio.ch.Net.checkAddress(Net.java:101)
	at sun.nio.ch.SocketChannelImpl.connect(SocketChannelImpl.java:622)
	at org.apache.kafka.common.network.Selector.doConnect(Selector.java:233)
	... 7 more
[2019-11-19 13:09:04,996] WARN [RequestSendThread controllerId=1] Controller 1's connection to broker kafka2:19093 (id: 2 rack: null) was unsuccessful (kafka.controller.RequestSendThread)
java.io.IOException: Connection to kafka2:19093 (id: 2 rack: null) failed.
	at org.apache.kafka.clients.NetworkClientUtils.awaitReady(NetworkClientUtils.java:70)
	at kafka.controller.RequestSendThread.brokerReady(ControllerChannelManager.scala:279)
	at kafka.controller.RequestSendThread.doWork(ControllerChannelManager.scala:233)
	at kafka.utils.ShutdownableThread.run(ShutdownableThread.scala:82)
[2019-11-19 13:09:05,001] INFO [ReplicaFetcherManager on broker 1] Removed fetcher for partitions test1-0 (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:09:05,011] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Loading producer state till offset 0 with message format version 2 (kafka.log.Log)
[2019-11-19 13:09:05,012] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Completed load of log with 1 segments, log start offset 0 and log end offset 0 in 4 ms (kafka.log.Log)
[2019-11-19 13:09:05,014] INFO Created log for partition test1-0 in /var/lib/kafka/data with properties {compression.type -> producer, message.format.version -> 2.0-IV1, file.delete.delay.ms -> 60000, max.message.bytes -> 1000012, min.compaction.lag.ms -> 0, message.timestamp.type -> CreateTime, message.downconversion.enable -> true, min.insync.replicas -> 1, segment.jitter.ms -> 0, preallocate -> false, min.cleanable.dirty.ratio -> 0.5, index.interval.bytes -> 4096, unclean.leader.election.enable -> false, retention.bytes -> -1, delete.retention.ms -> 86400000, cleanup.policy -> [delete], flush.ms -> 9223372036854775807, segment.ms -> 604800000, segment.bytes -> 1073741824, retention.ms -> 604800000, message.timestamp.difference.max.ms -> 9223372036854775807, segment.index.bytes -> 10485760, flush.messages -> 9223372036854775807}. (kafka.log.LogManager)
[2019-11-19 13:09:05,016] INFO [Partition test1-0 broker=1] No checkpointed highwatermark is found for partition test1-0 (kafka.cluster.Partition)
[2019-11-19 13:09:05,017] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,019] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,019] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,020] INFO [Partition test1-0 broker=1] test1-0 starts at Leader Epoch 0 from offset 0. Previous Leader Epoch was: -1 (kafka.cluster.Partition)
[2019-11-19 13:09:05,023] INFO [ReplicaAlterLogDirsManager on broker 1] Added fetcher for partitions List() (kafka.server.ReplicaAlterLogDirsManager)
[2019-11-19 13:09:05,097] INFO [RequestSendThread controllerId=1] Controller 1 connected to kafka2:19093 (id: 2 rack: null) for sending state change requests (kafka.controller.RequestSendThread)
[2019-11-19 13:14:50,124] INFO Updated PartitionLeaderEpoch. New: {epoch:0, offset:0}, Current: {epoch:-1, offset:-1} for Partition: test1-0. Cache now contains 0 entries. (kafka.server.epoch.LeaderEpochFileCache)
[2019-11-19 13:15:05,586] WARN Client session timed out, have not heard from server in 4002ms for sessionid 0x16e83c6ee8f0001 (org.apache.zookeeper.ClientCnxn)
[2019-11-19 13:15:05,586] INFO Client session timed out, have not heard from server in 4002ms for sessionid 0x16e83c6ee8f0001, closing socket connection and attempting reconnect (org.apache.zookeeper.ClientCnxn)
[2019-11-19 13:15:07,385] INFO Opening socket connection to server zk1/172.17.0.2:2181. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)

```

It cannot update zookeeper with the latest ISR. 

New leader was broker 3. Logs:

```
[2019-11-19 13:08:51,124] INFO [Producer clientId=producer-1] Closing the Kafka producer with timeoutMillis = 0 ms. (org.apache.kafka.clients.producer.KafkaProducer)
[2019-11-19 13:08:51,127] ERROR Could not submit metrics to Kafka topic __confluent.support.metrics: Failed to construct kafka producer (io.confluent.support.metrics.BaseMetricsReporter)
[2019-11-19 13:08:53,369] INFO Successfully submitted metrics to Confluent via secure endpoint (io.confluent.support.metrics.submitters.ConfluentSubmitter)
[2019-11-19 13:09:05,017] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,049] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Loading producer state till offset 0 with message format version 2 (kafka.log.Log)
[2019-11-19 13:09:05,054] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Completed load of log with 1 segments, log start offset 0 and log end offset 0 in 21 ms (kafka.log.Log)
[2019-11-19 13:09:05,056] INFO Created log for partition test1-0 in /var/lib/kafka/data with properties {compression.type -> producer, message.format.version -> 2.0-IV1, file.delete.delay.ms -> 60000, max.message.bytes -> 1000012, min.compaction.lag.ms -> 0, message.timestamp.type -> CreateTime, message.downconversion.enable -> true, min.insync.replicas -> 1, segment.jitter.ms -> 0, preallocate -> false, min.cleanable.dirty.ratio -> 0.5, index.interval.bytes -> 4096, unclean.leader.election.enable -> false, retention.bytes -> -1, delete.retention.ms -> 86400000, cleanup.policy -> [delete], flush.ms -> 9223372036854775807, segment.ms -> 604800000, segment.bytes -> 1073741824, retention.ms -> 604800000, message.timestamp.difference.max.ms -> 9223372036854775807, segment.index.bytes -> 10485760, flush.messages -> 9223372036854775807}. (kafka.log.LogManager)
[2019-11-19 13:09:05,056] INFO [Partition test1-0 broker=3] No checkpointed highwatermark is found for partition test1-0 (kafka.cluster.Partition)
[2019-11-19 13:09:05,057] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,057] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,060] INFO [ReplicaFetcherManager on broker 3] Removed fetcher for partitions test1-0 (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:09:05,079] INFO [ReplicaFetcher replicaId=3, leaderId=1, fetcherId=0] Starting (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:09:05,082] INFO [ReplicaFetcherManager on broker 3] Added fetcher for partitions List([test1-0, initOffset 0 to broker BrokerEndPoint(1,kafka1,19092)] ) (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:09:05,094] INFO [ReplicaAlterLogDirsManager on broker 3] Added fetcher for partitions List() (kafka.server.ReplicaAlterLogDirsManager)
[2019-11-19 13:09:05,112] WARN [ReplicaFetcher replicaId=3, leaderId=1, fetcherId=0] Based on follower's leader epoch, leader replied with an unknown offset in test1-0. The initial fetch offset 0 will be used for truncation. (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:09:05,115] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Truncating to 0 has no effect as the largest offset in the log is -1 (kafka.log.Log)
[2019-11-19 13:14:50,156] INFO Updated PartitionLeaderEpoch. New: {epoch:0, offset:0}, Current: {epoch:-1, offset:-1} for Partition: test1-0. Cache now contains 0 entries. (kafka.server.epoch.LeaderEpochFileCache)
[2019-11-19 13:15:08,008] INFO Creating /controller (is it secure? false) (kafka.zk.KafkaZkClient)
[2019-11-19 13:15:08,012] INFO Result of znode creation at /controller is: OK (kafka.zk.KafkaZkClient)
[2019-11-19 13:15:08,013] INFO [Controller id=3] 3 successfully elected as the controller (kafka.controller.KafkaController)
[2019-11-19 13:15:08,013] INFO [Controller id=3] Reading controller epoch from ZooKeeper (kafka.controller.KafkaController)
[2019-11-19 13:15:08,015] INFO [Controller id=3] Initialized controller epoch to 1 and zk version 0 (kafka.controller.KafkaController)
[2019-11-19 13:15:08,016] INFO [Controller id=3] Incrementing controller epoch in ZooKeeper (kafka.controller.KafkaController)
[2019-11-19 13:15:08,018] INFO [Controller id=3] Epoch incremented to 2 (kafka.controller.KafkaController)
[2019-11-19 13:15:08,019] INFO [Controller id=3] Registering handlers (kafka.controller.KafkaController)
[2019-11-19 13:15:08,022] INFO [Controller id=3] Deleting log dir event notifications (kafka.controller.KafkaController)
[2019-11-19 13:15:08,024] INFO [Controller id=3] Deleting isr change notifications (kafka.controller.KafkaController)
[2019-11-19 13:15:08,026] INFO [Controller id=3] Initializing controller context (kafka.controller.KafkaController)
[2019-11-19 13:15:08,052] INFO [RequestSendThread controllerId=3] Starting (kafka.controller.RequestSendThread)
[2019-11-19 13:15:08,053] INFO [Controller id=3] Partitions being reassigned: Map() (kafka.controller.KafkaController)
[2019-11-19 13:15:08,054] INFO [RequestSendThread controllerId=3] Starting (kafka.controller.RequestSendThread)
[2019-11-19 13:15:08,055] INFO [Controller id=3] Currently active brokers in the cluster: Set(2, 3) (kafka.controller.KafkaController)
[2019-11-19 13:15:08,055] INFO [Controller id=3] Currently shutting brokers in the cluster: Set() (kafka.controller.KafkaController)
[2019-11-19 13:15:08,056] INFO [Controller id=3] Current list of topics in the cluster: Set(test1, __confluent.support.metrics) (kafka.controller.KafkaController)
[2019-11-19 13:15:08,056] INFO [Controller id=3] Fetching topic deletions in progress (kafka.controller.KafkaController)
[2019-11-19 13:15:08,060] INFO [Controller id=3] List of topics to be deleted:  (kafka.controller.KafkaController)
[2019-11-19 13:15:08,060] INFO [Controller id=3] List of topics ineligible for deletion: test1,__confluent.support.metrics (kafka.controller.KafkaController)
[2019-11-19 13:15:08,060] INFO [Controller id=3] Initializing topic deletion manager (kafka.controller.KafkaController)
[2019-11-19 13:15:08,061] INFO [Controller id=3] Sending update metadata request (kafka.controller.KafkaController)
```

Broker 2 logs:

```
[2019-11-19 13:09:05,199] INFO [Partition test1-0 broker=2] No checkpointed highwatermark is found for partition test1-0 (kafka.cluster.Partition)
[2019-11-19 13:09:05,200] INFO Replica loaded for partition test1-0 with initial high watermark 0 (kafka.cluster.Replica)
[2019-11-19 13:09:05,203] INFO [ReplicaFetcherManager on broker 2] Removed fetcher for partitions test1-0 (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:09:05,224] INFO [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Starting (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:09:05,226] INFO [ReplicaFetcherManager on broker 2] Added fetcher for partitions List([test1-0, initOffset 0 to broker BrokerEndPoint(1,kafka1,19092)] ) (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:09:05,230] INFO [ReplicaAlterLogDirsManager on broker 2] Added fetcher for partitions List() (kafka.server.ReplicaAlterLogDirsManager)
[2019-11-19 13:09:05,244] WARN [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Based on follower's leader epoch, leader replied with an unknown offset in test1-0. The initial fetch offset 0 will be used for truncation. (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:09:05,247] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Truncating to 0 has no effect as the largest offset in the log is -1 (kafka.log.Log)
[2019-11-19 13:14:50,148] INFO Updated PartitionLeaderEpoch. New: {epoch:0, offset:0}, Current: {epoch:-1, offset:-1} for Partition: test1-0. Cache now contains 0 entries. (kafka.server.epoch.LeaderEpochFileCache)
[2019-11-19 13:15:08,010] INFO Creating /controller (is it secure? false) (kafka.zk.KafkaZkClient)
[2019-11-19 13:15:08,015] ERROR Error while creating ephemeral at /controller, node already exists and owner '103164731905212421' does not match current session '103164731905212419' (kafka.zk.KafkaZkClient$CheckedEphemeral)
[2019-11-19 13:15:08,015] INFO Result of znode creation at /controller is: NODEEXISTS (kafka.zk.KafkaZkClient)
[2019-11-19 13:15:08,091] WARN [Broker id=2] Ignoring LeaderAndIsr request from controller 3 with correlation id 1 epoch 2 for partition test1-0 since its associated leader epoch 0 is not higher than the current leader epoch 0 (state.change.logger)
[2019-11-19 13:15:08,092] INFO [ReplicaAlterLogDirsManager on broker 2] Added fetcher for partitions List() (kafka.server.ReplicaAlterLogDirsManager)
[2019-11-19 13:15:08,146] INFO [ReplicaFetcherManager on broker 2] Removed fetcher for partitions test1-0 (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:15:08,151] INFO [ReplicaFetcherManager on broker 2] Added fetcher for partitions List([test1-0, initOffset 12 to broker BrokerEndPoint(3,kafka3,19094)] ) (kafka.server.ReplicaFetcherManager)
[2019-11-19 13:15:08,154] INFO [ReplicaFetcher replicaId=2, leaderId=3, fetcherId=0] Starting (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:15:08,154] INFO [ReplicaAlterLogDirsManager on broker 2] Added fetcher for partitions List() (kafka.server.ReplicaAlterLogDirsManager)
[2019-11-19 13:15:08,155] INFO [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Shutting down (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:15:08,161] INFO [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Error sending fetch request (sessionId=176193971, epoch=707) to node 1: java.nio.channels.ClosedSelectorException. (org.apache.kafka.clients.FetchSessionHandler)
[2019-11-19 13:15:08,162] INFO [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Stopped (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:15:08,163] INFO [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0] Shutdown completed (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:15:08,175] INFO [ReplicaFetcher replicaId=2, leaderId=3, fetcherId=0] Retrying leaderEpoch request for partition test1-0 as the leader reported an error: NOT_LEADER_FOR_PARTITION (kafka.server.ReplicaFetcherThread)
[2019-11-19 13:15:09,183] INFO [Log partition=test1-0, dir=/var/lib/kafka/data] Truncating to 12 has no effect as the largest offset in the log is 11 (kafka.log.Log)
[2019-11-19 13:16:14,285] INFO Updated PartitionLeaderEpoch. New: {epoch:1, offset:13}, Current: {epoch:0, offset:0} for Partition: test1-0. Cache now contains 1 entries. (kafka.server.epoch.LeaderEpochFileCache)
[2019-11-19 13:18:24,812] INFO [GroupMetadataManager brokerId=2] Removed 0 expired offsets in 0 milliseconds. (kafka.coordinator.group.GroupMetadataManager)
```

So we see that a completely isolated node is worse than a node failure with acks=1, as it takes a while for the broker to detect that it has lost its Zookeeper connection. While sending 100000 messages we lost alot more acknowledged messages! Those were the messages sent during this brief 15 second window where kafka1 was still accepting writes even though a new leader had been elected.



## Scenario 5 - Completely Isolate Leader from other Kafka nodes and Zookeeper with acks=all (no message loss)


Reset the cluster and run:
```
python producer.py 100000 0.0001 all test1
```

Parition the leader (in my case kafka3) from everybody:
```
blockade partition kafka3
```

Check the output of the client screen:
```
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
Success: 51029 Failed: 48971
Sent: 100000
Delivered: 51029
Failed: 48971
```


Let's check the high watermark:
```

$ bash print-hw.sh kafka1 19092 test1
test1:0:51035
```

Our high watermark is higher than the ACKs received by the producer. 

Let's check failover has happened:

```
$ bash print-topic-details.sh kafka1 test1
Topic:test1	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: test1	Partition: 0	Leader: 1	Replicas: 3,1,2	Isr: 1,2
```

Reset cluster and run this with lots of concurrent producers.

```
bash concurrent-producer-silent.sh 100000 0.0001 all test1
```

Partition the leader about 15 seconds in:

```
blockade partition kafka1
```

Client result:
```
Runs complete
Acknowledged total: 727937
```

High watermark:
```
$ bash print-hw.sh kafka2 19093 test1
test1:0:727937
```

No messages lost which is good news.


## Scenario 6 - Leader Isolated from Zookeeper only with Acks=1


This is a trickier failure scenario in which only zookeeper is isolated from leader.

Reset cluster and run producer:

```
python producer.py 100000 0.0001 1 test1
Success: 10000 Failed: 0
Success: 20000 Failed: 0
Success: 30000 Failed: 0
Success: 40000 Failed: 0
Success: 50000 Failed: 0
Success: 60000 Failed: 0
Success: 70000 Failed: 0
Success: 80000 Failed: 0
Success: 90000 Failed: 0
Success: 100000 Failed: 0
Sent: 100000
Delivered: 100000
Failed: 0

```

Midway, I ran a partition command to make the leader  not communicate with zk1:

```
blockade partition kafka1,kafka2,kafka3 zk1,kafka1,kafka3
```

Checking the high watermark:
```
bash print-hw.sh kafka2 19093 test1
test1:0:61791
```

That's a lot of messages not received.


Let's see what happens when do run the same with the  slow producer. Reset the cluster and run:

```
python slow-producer.py 100 1 1 test1
```

About half way, create the partition (in my case leader was kafka1 this time):

```
blockade partition kafka1,kafka2,kafka3 zk1,kafka2,kafka3
```

The producer should hang and then show something like:

```
ERROR! Value: 69 Offset: none Error: Local: Message timed out
ERROR! Value: 70 Offset: none Error: Local: Message timed out
ERROR! Value: 71 Offset: none Error: Local: Message timed out
ERROR! Value: 72 Offset: none Error: Local: Message timed out
ERROR! Value: 73 Offset: none Error: Local: Message timed out
ERROR! Value: 74 Offset: none Error: Local: Message timed out
ERROR! Value: 75 Offset: none Error: Local: Message timed out
ERROR! Value: 76 Offset: none Error: Local: Message timed out
ERROR! Value: 77 Offset: none Error: Local: Message timed out
ERROR! Value: 78 Offset: none Error: Local: Message timed out
ERROR! Value: 79 Offset: none Error: Local: Message timed out
ERROR! Value: 80 Offset: none Error: Local: Message timed out
ERROR! Value: 81 Offset: none Error: Local: Message timed out
ERROR! Value: 82 Offset: none Error: Local: Message timed out
ERROR! Value: 83 Offset: none Error: Local: Message timed out
ERROR! Value: 84 Offset: none Error: Local: Message timed out
ERROR! Value: 85 Offset: none Error: Local: Message timed out
ERROR! Value: 86 Offset: none Error: Local: Message timed out
ERROR! Value: 87 Offset: none Error: Local: Message timed out
ERROR! Value: 88 Offset: none Error: Local: Message timed out
ERROR! Value: 89 Offset: none Error: Local: Message timed out
Partition fail-over, messages lost: 14
Value: 90 Offset: 14
Value: 91 Offset: 15
Value: 92 Offset: 16
Value: 93 Offset: 17
Value: 94 Offset: 18
Value: 95 Offset: 19
Value: 96 Offset: 20
Value: 97 Offset: 21
Value: 98 Offset: 22
Value: 99 Offset: 23
Value: 100 Offset: 24
Sent: 100
Delivered: 40
Failed: 60
```
Only 40  delivered as far as the producer is concerned.

If we check the high watermark:
```
bash print-hw.sh kafka2 19093 test1
test1:0:25
```

Even less as far as the high watermark is concerned.

## Scenario 7 - Leader Isolated from Zookeeper only with Acks=all (no message loss)


Reset  the cluster  and run the following:

```
python producer.py 100000 0.0001 all test1

```

About half way, partition the leader from zookeeper. In my case  that was kafka1:

```
blockade partition kafka1,kafka2,kafka3 zk1,kafka2,kafka3
```

Observe the client output:
```
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}
Success: 64634 Failed: 15366
Success: 74634 Failed: 15366
Success: 84634 Failed: 15366
Sent: 100000
Delivered: 84634
Failed: 15366
```

There's a bit of timeout period when things lag until the failover happens.

Checking the high watermark:

```
$bash print-hw.sh kafka2 19093 test1
test1:0:84638
```

We can see that  we've managed to store slightly more than we acknowledged to the producer and we  have not lost any data.


Conclusion

We've shown how to create different kinds of failures and tracked what the behaviour is when ACKS=1 or ACKS=all are  used
at the producer side. We've  also  seen that failures where  brokers are partitioned or slow to respond cause  bigger 
problems  than brokers crashing.

  





