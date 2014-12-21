set -vex
: @@@@
 rye run au.py -bund=one  find 2>/dev/null 
: @@@@
 rye run au.py  --bund=one  cat /wiki/HomePage/rfc3526.txt 2>/dev/null
: @@@@
