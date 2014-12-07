case "$1" in
  *.yak.net )
    H="$1"
    shift
	;;
  * )
    break
	;;
esac

set -ex
test -n "$H"

ssh root@$H "killall amain || echo None"

ssh root@$H "mkdir -p /opt/aphid"

scp prod.one.sh root@$H:/opt/aphid/

scp amain/amain root@$H:/opt/aphid/

rsync -a b.one/ root@$H:/opt/aphid/b.one/

ssh -n root@$H "(sh /opt/aphid/prod.one.sh &) &"
