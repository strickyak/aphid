package aphid

import "io"

func WrapRead(r io.Reader, n int) ([]byte, bool) {
  buf := make([]byte, n)
  count, err := r.Read(buf)
  println("YYY WrapRead", r, n, count, err)
  if err == nil {
    return buf[:count], false
  }
  if err == io.EOF {
    return buf[:count], true
  }
  // TODO: might we be throwing away some bytes?
  panic(err)
}

func WrapReadAt(r io.ReaderAt, n int, pos int64) ([]byte, bool) {
  buf := make([]byte, n)
  count, err := r.ReadAt(buf, pos)
  println("YYY WrapReadAt", r, n, pos, count, err)
  if err == nil {
    return buf[:count], false
  }
  if err == io.EOF {
    return buf[:count], true
  }
  // TODO: might we be throwing away some bytes?
  panic(err)
}

func WrapWrite(w io.Writer, data []byte) (int) {
  n := len(data)
  for n > 0 {
    c, err := w.Write(data)
    if err != nil {
      panic(err)
    }
    n -= c
    if n < 1 {
      break
    }
    data = data[c:]
  }
  return 0
}


