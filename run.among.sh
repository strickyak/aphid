set -vex
rye build amain.py
rm -f /tmp/amain /tmp/test.ring
cp -f amain/amain test.ring /tmp/

#NODES="SFO SJC ATL BKK"
#ALL="SFO=localhost:7001,SJC=localhost:7002,ATL=localhost:7003,BKK=localhost:7004"
NODES="16 17"
ALL="16=localhost:7001,17=localhost:7002"

i=1
P=""
for x in $NODES
do
  rm -rf /tmp/node.$x
  mkdir /tmp/node.$x
  cd /tmp/node.$x
  /tmp/amain \
    --a_me=$x \
    --a_all="$ALL" \
    --self_ip=127.0.0.1 \
    --a_bundle_topdir=. \
    --a_dns_bind="localhost:705$i" \
    --a_http_bind="localhost:708$i" \
    --a_rbundle_bind="localhost:700$i" \
    --a_keyring=/tmp/test.ring \
    ::bundle::rep:: \
    2>&1 &
       #>/tmp/_$x 2>&1  &
  P="$P $!"
  sleep 1
  i=`expr 1 + $i`
done
trap 'kill $P' 0 1 2 3
wait
exit 0
