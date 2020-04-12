#!/bin/sh
puppet module install puppetlabs-stdlib
tar -czf puppet-cbsr.tar.gz *
puppet module install --force puppet-cbsr.tar.gz
puppet apply $1.pp
rm -f puppet-cbsr.tar.gz