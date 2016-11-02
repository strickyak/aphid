#!/bin/bash
set -ex

rm -rf /tmp/APHID
mkdir -p /tmp/APHID/src
cd /tmp/APHID/src
export GOPATH=/tmp/APHID
mkdir -p github.com/strickyak

go get github.com/strickyak/prego
( cd github.com/strickyak/prego ; go test )
go get github.com/strickyak/rye
( cd github.com/strickyak/rye ; make )
go get github.com/strickyak/aphid
( cd github.com/strickyak/aphid ; make )
