package aphid_test

import "github.com/strickyak/aphid"
import "testing"

func TestJoinChirpList(t *testing.T) {
  s1 := aphid.JoinChirpList([]string{"abc", "def", "ghi"})
  if s1 != "abc def ghi" {
    t.Error("got %q", s1)
  }
  s2 := aphid.JoinChirpList([]string{"abc def", "def ghi", "ghi xyz"})
  if s2 != "{abc def} {def ghi} {ghi xyz}" {
    t.Error("got %q", s2)
  }
  s3 := aphid.JoinChirpList([]string{"abc \n", "def \001", "\xFF xyz"})
  if s3 != "{abc \\x0a} {def \\x01} {\\xff xyz}" {
    t.Error("got %q", s3)
  }
}
