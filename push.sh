set -ex
test -x au/au || rye build au.py
au/au --bund=fugio --dir=dir --server=localhost:8181 push
au/au --bund=newt --dir=dir --server=localhost:8181 push
