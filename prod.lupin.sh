set -vex

exec </dev/null >>/tmp/prod.lupin.log 2>&1
cd /opt/lupin
rm -rf /opt/disk/lupin_*

H=`hostname | awk -F. '{print $1}'`
/opt/lupin/aphid --ring=var/lupin.ring --admin_init_pw=/admin/ --seeddir=lupin-seed/ lupin.laph:job:$H
