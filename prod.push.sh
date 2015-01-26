set -vex

for x
do
  test -n "$x"
  H="$x.yak.net"

  : ssh -n root@$H "killall amain || echo None"
  ssh -n root@$H "killall aphid || echo None"

  ssh -n root@$H "mkdir -p /opt/aphid"
  # rsync -ave "ssh -C" aphid/aphid root@$H:/opt/aphid/
  # rsync -ave "ssh -C" --bwlimit=1000 aphid/aphid root@$H:/opt/aphid/
  scp -C *.pem *.conf prod.two.sh prod.ring root@$H:/opt/aphid/
  rsync -ave "ssh -C" aphid/aphid root@$H:/opt/aphid/

  # rsync -av b.one/ root@$H:/opt/aphid/b.one/

  ssh -n root@$H "nohup sh /opt/aphid/prod.two.sh </dev/null >/tmp/prod.two.log 2>&1 & sleep 1"
done
