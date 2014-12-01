package aphid
//
//import "bytes"
//
//const ChunkMagic = 199
//
//type bbuf struct {
//	*bytes.Buffer
//}
//
//func NewBuffer() *bbuf {
//	return &bbuf{Buffer: new(bytes.Buffer)}
//}
//
//func (b *bbuf) Write4(a int64) {
//	if a > 0xFFFFFFFF {
//		panic("too big for Write4")
//	}
//	if a < 0 {
//		panic("got negative for Write4")
//	}
//	b.WriteByte(byte((a >> 24) & 255)) // Big Endian.
//	b.WriteByte(byte((a >> 16) & 255))
//	b.WriteByte(byte((a >> 8) & 255))
//	b.WriteByte(byte((a >> 0) & 255))
//}
//
//func (b *bbuf) Write8(a int64) {
//	b.Write4((a >> 32) & 0xFFFFFFFF) // Big Endian.
//	b.Write4((a >> 0) & 0xFFFFFFFF)  // Big Endian.
//}
//
//func (b *bbuf) Read4() int64 {
//	w, err := b.ReadByte()
//	if err != nil {
//		panic(err)
//	}
//	x, err := b.ReadByte()
//	if err != nil {
//		panic(err)
//	}
//	y, err := b.ReadByte()
//	if err != nil {
//		panic(err)
//	}
//	z, err := b.ReadByte()
//	if err != nil {
//		panic(err)
//	}
//	return (int64(w) << 24) | (int64(x) << 16) | (int64(y) << 8) | int64(z)
//}
//
//func (b *bbuf) Read8() int64 {
//	y := int64(b.Read4())
//	z := int64(b.Read4())
//	return (y << 32) | z
//}
//
//func (b *bbuf) WriteChunk(a []byte) {
//	if len(a) > 0x7FFFFFFF {
//		panic("Way Too Big")
//	}
//	b.WriteByte(ChunkMagic) // magic.
//	b.Write4(int64(len(a)))
//	b.Write(a)
//}
//
//func (b *bbuf) ReadChunk() []byte {
//	magic, err := b.ReadByte()
//	if err != nil {
//		panic(err)
//	}
//	if magic != ChunkMagic {
//		panic(err)
//	}
//	n := int(b.Read4())
//	s := make([]byte, n)
//	i := 0
//	for i < n {
//		c, err := b.Read(s[i:])
//		if err != nil {
//			panic(err)
//		}
//		i += c
//	}
//	return s
//}
