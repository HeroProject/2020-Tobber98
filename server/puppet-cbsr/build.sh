#!/bin/sh
/opt/puppetlabs/bin/puppet module install puppetlabs-stdlib
tar -czf puppet-cbsr.tar.gz *
/opt/puppetlabs/bin/puppet module install --force puppet-cbsr.tar.gz
/opt/puppetlabs/bin/puppet apply $1.pp
rm -f puppet-cbsr.tar.gz