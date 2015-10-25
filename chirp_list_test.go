package aphid_test

import "github.com/strickyak/aphid"
import "testing"

func ExpectInt(t *testing.T, expect, got int) {
	if got != expect {
		t.Errorf("got %d expect %d", got, expect)
	}
}
func Expect(t *testing.T, expect, got string) {
	if got != expect {
		t.Errorf("got %q expect %q", got, expect)
	}
}

func TestJoinChirpList(t *testing.T) {
	s1 := aphid.JoinChirpList([]string{"abc", "def", "ghi"})
	if s1 != "abc def ghi" {
		t.Errorf("got %q", s1)
	}
	a1 := aphid.ParseChirpList(s1)
	ExpectInt(t, 3, len(a1))
	Expect(t, "abc", a1[0])
	Expect(t, "def", a1[1])
	Expect(t, "ghi", a1[2])

	s2 := aphid.JoinChirpList([]string{"abc def", "def ghi", "ghi xyz"})
	if s2 != "{abc def} {def ghi} {ghi xyz}" {
		t.Errorf("got %q", s2)
	}
	a2 := aphid.ParseChirpList(s2)
	ExpectInt(t, 3, len(a2))
	Expect(t, "abc def", a2[0])
	Expect(t, "def ghi", a2[1])
	Expect(t, "ghi xyz", a2[2])

	s3 := aphid.JoinChirpList([]string{"abc \n", "def \001", "\xFF xyz"})
	if s3 != "{abc \\x0a} {def \\x01} {\\xff xyz}" {
		t.Errorf("got %q", s3)
	}
	a3 := aphid.ParseChirpList(s3)
	ExpectInt(t, 3, len(a3))
	Expect(t, "abc \n", a3[0])
	Expect(t, "def \001", a3[1])
	Expect(t, "\xFF xyz", a3[2])
}
