case $# in
  2 ) : ok ;;
  * ) echo "Usage: src /dest" >&2 ; exit 3 ;;
esac
case $2 in
  /* ) : ok ;;
  * ) echo "Usage: src /dest" >&2 ; exit 3 ;;
esac

S="$1"
D="$2"
shift
shift

cd "$S"

for a in $(find . -name f.\*) 
do
  b=$(echo $a | sed -e 's;/[df][.];/;g')
  echo ... $b
  mkdir -p  $D/$(dirname $b)
  cat $( cd $a ; ls -t `pwd`/r.* | head -1 ) >  $D/$b 
done
