package aphid

import (
	"bytes"
	"fmt"
	"strings"
)

func JoinChirpList(vec []string) string {
	var buf bytes.Buffer
	for i, s := range vec {
		if i > 0 {
			buf.WriteByte(' ')
		}
		buf.WriteString(ToChirpListElement(s))
	}
	return buf.String()
}

func ToChirpListElement(s string) string {
	if s == "" {
		return "{}"
	}

	if strings.ContainsAny(s, " \t\n\r{}\\") {
		return "{" + hexEscapeAsNeeded(s) + "}"
	}
	return s
}

func ParseChirpListOrRecover(s string) (recs []string, err interface{}) {
	defer func() {
		err = recover()
	}()
	recs = ParseChirpList(s)
	return
}

func ParseChirpList(s string) []string {
	n := len(s)
	i := 0
	z := make([]string, 0, 4)

	for i < n {
		var c byte

		// skip space
		for i < n {
			c = s[i]
			if !white(s[i]) {
				break
			}
			i++
		}
		if i == n {
			break
		}

		var buf bytes.Buffer

		// found non-white
		if c == '{' {
			i++
			c = s[i]
			b := 1
			for i < n {
				c = s[i]
				switch c {
				case '{':
					b++
				case '}':
					b--
				case '\\':
					c, i = consumeBackslashEscaped(s, i)
					i -= 1
				}
				if b == 0 {
					break
				}
				buf.WriteByte(c)
				i++
			}
			if c != '}' {
				panic(fmt.Sprintf("ParseChirpList: missing end brace: %d", c))
			}
			i++
		} else {
			for i < n {
				c = s[i]
				if white(s[i]) {
					break
				}
				if c == '\\' {
					c, i = consumeBackslashEscaped(s, i)
					i -= 1
				}
				buf.WriteByte(c)
				i++
			}
		}
		z = append(z, buf.String())
	}
	return z
}

func white(ch byte) bool {
	return ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n'
}

func consumeBackslashEscaped(s string, i int) (byte, int) {
	switch s[i+1] {
	case 'a':
		return '\a', i + 2
	case 'b':
		return '\b', i + 2
	case 'f':
		return '\f', i + 2
	case 'n':
		return '\n', i + 2
	case 'r':
		return '\r', i + 2
	case 't':
		return '\t', i + 2
	case 'v':
		return '\v', i + 2
	case 'x':
		a := unhex(s[i+2])
		b := unhex(s[i+3])
		return byte((a << 4) | b), i + 4
	}
	if s[i+1] < '0' || s[i+1] > '7' {
		return s[i+1], i + 2 // Default for all other cases is the escaped char.
	}
	if s[i+2] < '0' || s[i+2] > '7' {
		panic(fmt.Sprintf("Second character after backslash is not octal: %q.", s[i:i+3]))
	}
	if s[i+3] < '0' || s[i+3] > '7' {
		panic(fmt.Sprintf("Third character after backslash is not octal: %q.", s[i:i+4]))
	}
	a := s[i+1] - '0'
	b := s[i+2] - '0'
	c := s[i+3] - '0'
	return byte(a*64 + b*8 + c), i + 4
}

/*
func hex(x int) byte {
  if 0 <= x && x <= '9' {
    return byte(x + '0' + x)
  } else if 10 <= x && x <= 16 {
    return byte(x - 10 + 'a' + x - 10)
  } else {
    panic("bad hex int")
  }
}
*/

func unhex(b byte) int {
	if '0' <= b && b <= '9' {
		return int(b - '0')
	} else if 'a' <= b && b <= 'f' {
		return int(b - 'a' + 10)
	} else if 'A' <= b && b <= 'F' {
		return int(b - 'A' + 10)
	} else {
		panic(fmt.Sprintf("bad hex char: %d", b))
	}
}

func hexEscapeAsNeeded(s string) string {
	var buf bytes.Buffer
	n := len(s)
	for i := 0; i < n; i++ { // Iterate bytes in s.
		var b byte = s[i]
		if byteNeedsEscape(b) {
			buf.WriteString(fmt.Sprintf("\\x%02x", b))
			//// buf.WriteByte('\\')
			//// buf.WriteByte('x')
			//// buf.WriteByte(hex(int((b >> 4) & 15)))
			//// buf.WriteByte(hex(int((b >> 0) & 15)))
		} else {
			buf.WriteByte(b)
		}
	}
	return buf.String()
}

func octalEscapeAsNeeded(s string) string {
	var buf bytes.Buffer
	n := len(s)
	for i := 0; i < n; i++ { // Iterate bytes in s.
		var b byte = s[i]
		if byteNeedsEscape(b) {
			buf.WriteString(fmt.Sprintf("\\%03o", b))
		} else {
			buf.WriteByte(b)
		}
	}
	return buf.String()
}

func byteNeedsEscape(b byte) bool {
	return b < ' ' || b > '~' || b == '{' || b == '}' || b == '\\'
}
