#!/bin/bash -ex
set -ex

python ../rye/rye.py build db_util.py

T=/tmp/tmp.db_test.$$
trap "/bin/rm -rf $T" 0 1 2 3
alias u="db_util/db_util $T"

u put a 100 
u put b 200 
u put c 300 

test 100 = $(u get a)
test 200 = $(u get b)
test 300 = $(u get c)
set / $(u keys) ; test "/ a b c" = "$*"
set / $(u items) ; test "/ a == 100 b == 200 c == 300" = "$*"

u put a 10
u delete b
u put ca 310
u put cb 320
u put d 400
set / $(u keys c) ; test "/ c ca cb" = "$*"
test 10 = $(u get a)
test 400 = $(u get d)
set / $(u keys) ; test "/ a c ca cb d" = "$*"
u recover
set / $(u keys) ; test "/ a c ca cb d" = "$*"

echo OKAY $0
