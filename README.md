# Introduction

This repository sets up a Vagrant machine with Blockade and Jack Van Nightly's ChaosTestingCode repo and allows one to
simulate different failure scenarios in a Kafka Cluster when producing data using different levels of ACKs.

To use, run

```
vagrant up
vagrant ssh
cd /vagrant/ChaosTestingCode
```

A list of failure scenarios is available in /vagrant/ChaosTestingCode/TestCases.md

