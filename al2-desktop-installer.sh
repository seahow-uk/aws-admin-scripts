#!/bin/bash

# script that will set up a MATE desktop on an Amazon Linux 2 instance
# It will also install all of the desktop utilities for MATE
#
# OPTIONS:
#
# (neither of these is required)
#
# --p <password> 
#       VNC password will be set to Aws2022 unless you specify your own with --p
#
# --r <runasuser>
#       VNC will run as root unless you tell it a different user to run as 
#
# example:
#       ./al2-desktop.sh --p 0neD1rect10nRulez2001! --r ec2-user
#       
#
# once this script is complete, you should be able to VNC to this on port 5901

# Set your defaults here

r=${r:-root}
p=${p:-Aws2022}

while [ $# -gt 0 ]; do
     if [[ $1 == *"--"* ]]; then
          param="${1/--/}"
          declare $param="$2"
     fi
     shift
done

# Assumption here is you just deployed this AL2 instance, so lets update
yum update -y

# Now install the packages we will need
amazon-linux-extras install mate-desktop1.x python3.8 firefox epel -y
yum install tigervnc-server tigervnc-server-module expect -y

# create and execute an expect script so we don't have to interact with the password thing
echo "#!/usr/bin/expect -f" >>runvncpasswd.sh
echo "set timeout -1" >>runvncpasswd.sh
echo "spawn vncpasswd" >>runvncpasswd.sh
echo "expect \"Password:\"" >>runvncpasswd.sh
echo "send -- \"$VNCPASS\r\"" >>runvncpasswd.sh
echo "expect \"Verify:\"" >>runvncpasswd.sh
echo "send -- \"$VNCPASS\r\"" >>runvncpasswd.sh
echo "expect \"Would you like to enter a view-only password (y/n)?\"" >>runvncpasswd.sh
echo "send -- \"n\r\"" >>runvncpasswd.sh
echo "expect eof" >>runvncpasswd.sh
chmod 700 runvncpasswd.sh
./runvncpasswd

# delete the expect script as we don't want someone coming along and finding the clear text
rm ./runvncpasswd

# set the configuration files
mkdir /etc/tigervnc
echo ":1=root" >>/etc/tigervnc/vncserver.users
echo "securitytypes=vncauth,tlsvnc" >>/etc/tigervnc/vncserver-config-mandatory
echo "desktop=sandbox" >>/etc/tigervnc/vncserver-config-mandatory
echo "geometry=1920x1200" >>/etc/tigervnc/vncserver-config-mandatory
bash -c 'echo PREFERRED=/usr/bin/mate-session > /etc/sysconfig/desktop'
cp /lib/systemd/system/vncserver@.service /etc/systemd/system/vncserver@.service
sed -i 's/<USER>/root/' /etc/systemd/system/vncserver@.service
systemctl daemon-reload
systemctl enable vncserver@:1.service
systemctl start vncserver@:1.service

# install all the various widgets and utilities for MATE desktop
yum install mate* -y

