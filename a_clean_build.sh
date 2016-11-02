#!/bin/bash
set -x

rm -rf /tmp/APHID
mkdir -p /tmp/APHID/src
cd /tmp/APHID/src
export GOPATH=/tmp/APHID
mkdir -p github.com/strickyak

go get github.com/strickyak/prego
go get github.com/strickyak/rye
( cd github.com/strickyak/rye ; make )
go get github.com/strickyak/aphid
( cd github.com/strickyak/aphid ; make )
