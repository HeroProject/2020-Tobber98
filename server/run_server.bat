@echo off
SET VAGRANT_HOME=.vagrant
vagrant halt
vagrant plugin install vagrant-vbguest
vagrant up --provision
vagrant ssh -c "hostname --all-ip-addresses"
echo Press any key to stop the server...
pause>nul
echo Shutting down!
vagrant halt
