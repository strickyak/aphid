set -vex

for x in iotanu
do
  test -n "$x"
  H="$x.yak.net"

  ssh -n root@$H "killall aphid || echo None"
  ssh -n root@$H "mkdir -p /opt/lupin /opt/disk /opt/lupin/var"
  scp -C *.pem lupin.laph prod.lupin.sh root@$H:/opt/lupin/
  scp -C lupin.ring root@$H:/opt/lupin/var/
  rsync -av --compress --compress-level=9 aphid/aphid root@$H:/opt/lupin/
  rsync -av --compress --compress-level=9 lupin-seed/ root@$H:/opt/lupin/lupin-seed/

  ssh -n root@$H "nohup sh /opt/lupin/prod.lupin.sh & sleep 1"
done
