#!/bin/bash
# deploy on r730 machine
# careful if the folder "/media" of r730 is used

# kill before run
/usr/bin/killall -9 inotifywait
/bin/sleep 2
/usr/bin/killall -9 rsync
/bin/sleep 2


# loacl file path  
src=/data
# server module name
des=data
# passwd file, different from server passwd file ,only have a single passwd
rsync_passwd_file=/home/kandao/workspace/rms/scripts/rsync_copy/rsyncd_client.passwd
# server host,we can rsync the folders/files to different servers
ip=portal.kandao.tech
# server auth name
user=root

# check
if [ ! -e "${src}" ] || [ ! -e "/usr/bin/inotifywait" ] || [ ! -e "/usr/bin/rsync" ] || [ ! -e "${rsync_passwd_file}" ]; then 
	echo "Check File and Folder"
	exit 1 
fi
# need cd into local path
cd ${src}
/usr/bin/inotifywait -mrq --format  '%Xe %w%f' -e modify,create,delete,attrib,close_write,move ./ | while read file
do
		INO_EVENT=$(echo $file | awk '{print $1}')
        INO_FILE=$(echo $file | awk '{print $2}')
        echo "-------------------------------$(date)------------------------------------"
        echo $file
        # create,modify,close_write,move to
        if [[ $INO_EVENT =~ 'CREATE' ]] || [[ $INO_EVENT =~ 'MODIFY' ]] || [[ $INO_EVENT =~ 'CLOSE_WRITE' ]] || [[ $INO_EVENT =~ 'MOVED_TO' ]]
        then
				echo 'CREATE or MODIFY or CLOSE_WRITE or MOVED_TO'
                rsync -avzctRP --password-file=${rsync_passwd_file} $(dirname ${INO_FILE}) --exclude-from=/data/rsyncexclude.txt ${user}@${ip}::${des}
        fi
        # delete move from
        if [[ $INO_EVENT =~ 'DELETE' ]] || [[ $INO_EVENT =~ 'MOVED_FROM' ]]
        then
                echo 'DELETE or MOVED_FROM'
                rsync -avztRP --password-file=${rsync_passwd_file} $(dirname ${INO_FILE}) --exclude-from=/data/rsyncexclude.txt ${user}@${ip}::${des}
        fi
        # touch chgrp chmod chown
        if [[ $INO_EVENT =~ 'ATTRIB' ]]
        then
                echo 'ATTRIB'
                if [ ! -d "$INO_FILE" ]
                then
                        rsync -avzctRP --password-file=${rsync_passwd_file} $(dirname ${INO_FILE}) --exclude-from=/data/rsyncexclude.txt ${user}@${ip}::${des}
                fi
        fi
done
