#!/bin/bash

# sean@tanagra.uk
# Nov 2022
#
# This is a script which will set up a MATE desktop on an Amazon Linux 2 instance
# It will also install all of the desktop utilities for MATE and tigervnc-server
#
# OPTIONS:
#
# (neither of these is required)
#
# --p <password> 
#       VNC password will be set to AWS@<todays date> (format: yyyymmdd) unless you do this
#       for instance, were I to not supply a password and run the script right now it would
#       set the VNC login password to "AWS@20221126".  It should go without saying that this
#       is a bad idea and meant for test labs only.
#
# --r <runasuser>
#       VNC will run as root unless you tell it a different user to run as with this
#
# example:
#       ./al2-desktop-installer.sh --p 0neD1rect10nRulez2001! --r someuser
#       
#
# once this script is complete, you should be able to VNC to this on port 5901

# Set your defaults here

TODAYSDATE=$(date +'%Y%m%d')
NOPASS="AWS@$TODAYSDATE"

r=${r:-root}
p=${p:-$NOPASS}

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
echo "#!/usr/bin/expect -f" >./runvncpasswd.sh
echo "set timeout -1" >>./runvncpasswd.sh
echo "spawn vncpasswd" >>./runvncpasswd.sh
echo "expect \"Password:\"" >>./runvncpasswd.sh
echo "send -- \"$p\r\"" >>./runvncpasswd.sh
echo "expect \"Verify:\"" >>./runvncpasswd.sh
echo "send -- \"$p\r\"" >>./runvncpasswd.sh
echo "expect \"Would you like to enter a view-only password (y/n)?\"" >>./runvncpasswd.sh
echo "send -- \"n\r\"" >>./runvncpasswd.sh
echo "expect eof" >>./runvncpasswd.sh
chmod 700 ./runvncpasswd.sh
./runvncpasswd.sh

# delete the expect script as we don't want someone coming along and finding the clear text
rm ./runvncpasswd.sh

# set the configuration files
mkdir /etc/tigervnc
echo ":1=$r" >>/etc/tigervnc/vncserver.users
echo "securitytypes=vncauth,tlsvnc" >>/etc/tigervnc/vncserver-config-mandatory
echo "desktop=sandbox" >>/etc/tigervnc/vncserver-config-mandatory
echo "geometry=1920x1200" >>/etc/tigervnc/vncserver-config-mandatory
echo "PREFERRED=/usr/bin/mate-session" > /etc/sysconfig/desktop
cp /lib/systemd/system/vncserver@.service /etc/systemd/system/vncserver@.service
sed -i "s/<USER>/$r/" /etc/systemd/system/vncserver@.service
systemctl daemon-reload
systemctl enable vncserver@:1.service
systemctl start vncserver@:1.service

# install all the default widgets and utilities for MATE desktop
yum install mate* -y

# install a GUI device manager style utility.  This one appears under Applications > System Tools > Hardware Lister
yum install lshw-gui -y

# install a GUI utility for NetworkManager.  This will appear under System > Preferences > Internet and Network > Network Connections
yum install network-manager-applet -y

# this forces the vnc server to restart after we add utilities.  for some weird reason, a temp file for xwindows gets stuck sometimes.
systemctl stop vncserver@:1.service
rm -rf  /tmp/.X11-unix/X1
systemctl start vncserver@:1.service