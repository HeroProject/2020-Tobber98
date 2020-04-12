#!/bin/sh
puppet module install puppetlabs-stdlib
tar -czf puppet-cbsr.tar.gz /var/puppet-cbsr
puppet module install --force puppet-cbsr.tar.gz
puppet apply /var/puppet-cbsr/vagrant.pp
rm -f puppet-cbsr.tar.gz