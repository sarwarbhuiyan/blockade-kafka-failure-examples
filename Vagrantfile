
VAGRANTFILE_API_VERSION = "2"
BOX_NAME = ENV['BOX_NAME'] || "ubuntu/xenial64"

script = <<SCRIPT
#!/bin/bash -e

if [ ! -f /etc/default/docker ]; then
  echo "/etc/default/docker not found -- is docker installed?" >&2
  exit 1
fi

apt-get update
apt-get -y install python-pip python-virtualenv python-dev python3-dev

pip install blockade
pip install confluent_kafka

apt-get install kafkacat

SCRIPT


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = BOX_NAME

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  config.vm.provider :virtualbox do |vb, override|
    vb.memory = "16384"
    vb.cpus = 4
  end

  # there are obviously vagrant versions with a
  # broken 'docker' provisioner that can be fixed
  # by invoking an 'apt-get update' *before* docker itself
  config.vm.provision "shell", inline: "apt-get update"
  config.vm.provision "docker",
     images: ["confluentinc/cp-zookeeper:5.3.1", "confluentinc/cp-kafka:5.3.1"]


  # kick off the tests automatically
  config.vm.provision "shell", inline: script

end
