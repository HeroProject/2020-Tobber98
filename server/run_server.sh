#!/bin/bash
export VAGRANT_HOME=.vagrant
vagrant halt
vagrant plugin install vagrant-vbguest
vagrant up --provision
vagrant ssh -c "hostname --all-ip-addresses"
read -p "Press ENTER to stop the server..." key
vagrant halt
