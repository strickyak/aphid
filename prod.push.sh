set -vex

for x
do
  test -n "$x"
  H="$x.yak.net"

  ssh root@$H "killall amain || echo None"

  ssh root@$H "mkdir -p /opt/aphid"
  scp prod.one.sh root@$H:/opt/aphid/
  rsync -av amain/amain root@$H:/opt/aphid/amain
  rsync -av b.one/ root@$H:/opt/aphid/b.one/

  ssh -n root@$H "nohup sh /opt/aphid/prod.one.sh </dev/null >/tmp/prod.one.log 2>&1 & sleep 1"
done
