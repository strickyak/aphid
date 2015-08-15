set -ex
P='http://localhost:10080/@stash1'
T="/tmp/systest_$$"
PW="pw_$$"
rm -rf $T/
mkdir -p $T

rm -rf __tmp__stash_systest_10

# Build and run daemon.
rye build aphid.py
aphid/aphid --admin_init_pw="$PW" $MORE stash_systest.laph:job:systest_10 >$T/aphid.log 2>&1 </dev/null &
DAEMON=$!
trap "kill $DAEMON" 0 1 2 3
sleep 1

# Default / page.
curl -u "admin:$PW" -o $T/2 "$P/"
grep 'Click.*here.*to log in' $T/2

# List page, with admin login.
curl -u "admin:$PW" -o $T/3 "$P/list"
cat -n $T/3
grep 'Users:' $T/3
grep 'Files:' $T/3
grep 'Actions:' $T/3

# Form to add user.
curl -u "admin:$PW" -o $T/4 "$P/add_user"
grep 'form.method=.POST.*action=.*submit_add_user' $T/4

# Add user "amy", "bob", & "chas".
curl -u "admin:$PW"  \
  -d 'new_user_name=amy&new_full_name=User Amy&new_passwd=/amy/&new_admin=yes&submit=Submit' \
  http://localhost:10080/@stash1/submit_add_user

curl -u "admin:$PW"  \
  -d 'new_user_name=bob&new_full_name=User Robert&new_passwd=/bob/&new_admin=no&submit=Submit' \
  http://localhost:10080/@stash1/submit_add_user

curl -u "admin:$PW"  \
  -d 'new_user_name=chas&new_full_name=User Charles&new_passwd=/chas/&new_admin=no&submit=Submit' \
  http://localhost:10080/@stash1/submit_add_user

#
curl -u "amy:/amy/" -o $T/5 "$P/list"
cat -n $T/5
curl -u "bob:/bob/" -o $T/6 "$P/list"
cat -n $T/6
curl -u "chas:/chas/" -o $T/7 "$P/list"
cat -n $T/7
grep "Administrator Account" $T/5
grep "Administrator Account" $T/6
grep "Administrator Account" $T/7
grep "User Amy" $T/5
grep "User Amy" $T/6
grep "User Robert" $T/6
grep "User Amy" $T/7
grep "User Robert" $T/7
grep "User Charles" $T/7

curl -u "chas:/chas/" -o $T/8 "$P/upload"
grep "Pick which file to upload" $T/8

date > $T/111
curl -u "chas:/chas/" -o $T/9 -F "file=@$T/111;filename=charles.txt" -F submit=submit -F Title="Date Today by Charles" -F to_bob=bob -F to_amy=amy "$P/submit_upload"
cat -n $T/9 || true

mount > $T/112
curl -u "bob:/bob/" -o $T/19 -F "file=@$T/112;filename=robert.txt" -F submit=submit -F Title="Mounts by Robert" "$P/submit_upload"
cat -n $T/19 || true

curl -u "amy:/amy/" -o $T/15 "$P/list"
cat -n $T/15
curl -u "bob:/bob/" -o $T/16 "$P/list"
cat -n $T/16
curl -u "chas:/chas/" -o $T/17 "$P/list"
cat -n $T/17

test "$T/15 $T/16 $T/17" = "$(echo $(grep -l charles[.]txt $T/15 $T/16 $T/17))"
test "$T/15 $T/16" = "$(echo $(grep -l robert[.]txt $T/15 $T/16 $T/17))"

curl -u "amy:/amy/" -o $T/25 "$P/view?f=robert.txt"
curl -u "bob:/bob/" -o $T/26 "$P/view?f=robert.txt"
curl -u "chas:/chas/" -o $T/27 "$P/view?f=robert.txt"
fgrep "$(head -1 $T/112)" $T/25
fgrep "$(head -1 $T/112)" $T/26
fgrep "has not been shared with you" $T/27

curl -u "amy:/amy/" -o $T/35 "$P/view?f=charles.txt"
curl -u "bob:/bob/" -o $T/36 "$P/view?f=charles.txt"
curl -u "chas:/chas/" -o $T/37 "$P/view?f=charles.txt"
fgrep "$(head -1 $T/111)" $T/35
fgrep "$(head -1 $T/111)" $T/36
fgrep "$(head -1 $T/111)" $T/37

echo OKAY $0 DONE.
