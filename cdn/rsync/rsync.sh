#!/bin/bash
src1=/media
src2=/webserver
#set like rsyncd.conf
rsync_passwd_file=/webserver/rsync/rsyncd_server.passwd

if [ ! -e "$src1" ] || [ ! -e "$src2" ] || [ ! -e "/usr/bin/rsync" ] || [ ! -e "$rsync_passwd_file" ]; then
echo "Check File and Folder"
exit 1
fi


rsync --daemon --config=/webserver/rsync/rsyncd.conf
