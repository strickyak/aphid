package aphid

import "github.com/microcosm-cc/bluemonday"
import "github.com/russross/blackfriday"

import (
	"io"
)

var _ = bluemonday.UGCPolicy
var _ = blackfriday.MarkdownCommon

// net/http.ServerContent needs a ReadSeeker.  This is ours.

func NewReadSeekerHack(buf []byte) io.ReadSeeker {
	return &readSeekerHack{buf: buf, sz: int64(len(buf))}
}

type readSeekerHack struct {
	buf []byte
	pos int64
	sz  int64
}

func (h *readSeekerHack) Read(p []byte) (int, error) {
	n := copy(p, h.buf[h.pos:])
	h.pos += int64(n)
	//println("Read", len(p), h.pos, n)
	if n < 1 {
		return 0, io.EOF
	}
	return n, nil
}

func (h *readSeekerHack) Seek(offset int64, whence int) (int64, error) {
	switch whence {
	case 0:
		h.pos = offset
	case 1:
		h.pos += offset
	case 2:
		h.pos = h.sz + offset
	default:
		panic("readSeekerHack Seek bad whence")
	}
	if h.pos < 0 {
		h.pos = 0
	}
	if h.pos > h.sz {
		h.pos = h.sz
	}
	//println("Seek", offset, whence, h.pos)
	return h.pos, nil
}
