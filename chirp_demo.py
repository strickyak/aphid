from go import "github.com/yak-labs/chirp-lang" as chirp
from go import bufio, os

from go import "github.com/yak-labs/chirp-lang/goapi/default" as _
from go import "github.com/yak-labs/chirp-lang/http" as _
from go import "github.com/yak-labs/chirp-lang/img" as _
from go import "github.com/yak-labs/chirp-lang/posix" as _
from go import "github.com/yak-labs/chirp-lang/rpc" as _


def main(_):
  fr = chirp.NewInterpreter()

  while True:
    bio = bufio.NewReader(os.Stdin)
    print >> os.Stderr, "\nchirp% ",
    try:
      line, truncated = bio.ReadLine()
      must not truncated
    except as e:
      if str(e) == 'EOF':
        return
      else:
        raise e

    try:
      result = fr.Eval(chirp.MkString(line))
      print result
    except as e:
      print >> os.Stderr, "\n*ERROR*\n", e
