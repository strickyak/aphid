set -vex
rye build rbundle.py
rye build among.py

rbundle/rbundle --rbundle_bind=localhost:9901 ::bundle::one:: &
R1=$!
sleep 1

rbundle/rbundle --rbundle_bind=localhost:9902 ::bundle::two:: &
R2=$!
sleep 1

trap "kill $R1 $R2" 0 1 2 3
among/among --among_all="11=localhost:9901,12=localhost:9902" --among_me="19"
