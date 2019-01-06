# Resize a jpeg image.
# Demo Usage:
#    resize H W in.jpg out.jpg

from go import "github.com/nfnt/resize"
from go import image, image.gif, image.jpeg, image.png
from go import bytes, os

MAX_IMG_SIZE = 10 * 1024 * 1024  # 10MB

JPEG_OPTIONS = setattrs(go_new(jpeg.Options), Quality=90)

def main(argv):
  w, h, filein, fileout = argv
  img = jpeg.Decode(os.Open(filein))
  newimg = resize.Resize(int(w), int(h), img, resize.NearestNeighbor)

  fd = os.Create(fileout)
  with defer fd.Close():
    jpeg.Encode(fd, newimg, JPEG_OPTIONS)

# THUMBS are (w, h) and must be increasing in size.
THUMBS = [(320, 240), (640, 480), (1024, 768), (1600, 1200)]

def MakeThumbnailsNoBody(bund, path, pw, rev, suffix, writeFileFn, readFileFn):
  #say 'FRODO MakeThumbnailsNoBody', bund.bname, path, pw, rev, suffix
  revs = sorted(bund.ListRevs(path, varient='r'))
  #say 'FRODO MakeThumbnailsNoBody/ListRevs', path, revs
  rev = revs[-1]

  is_dir, ts, sz = bund.Stat3(path, pw, rev=rev, varient='r', nodir=True)
  #say 'FRODO MakeThumbnailsNoBody/Stat3', is_dir, ts, sz
  if sz < 16 or sz > MAX_IMG_SIZE:
    raise 'bad size for an image: %d' % sz

  body = readFileFn(bund, path, pw, raw=False, rev=rev)
  MakeThumbnails(bund, path, body, pw, suffix, writeFileFn)

def MakeThumbnails(bund, path, body, pw, suffix, writeFileFn):
  #say 'FRODO MakeThumbnails', bund.bname, path, len(body), pw, suffix
  assert suffix
  sz = len(body)
  if sz < 16 or sz > MAX_IMG_SIZE:
    raise 'bad size for an image: %d' % sz

  img, what_format = image.Decode(bytes.NewBuffer(body))
  b = img.Bounds()
  width = b.Max.X - b.Min.X
  height = b.Max.Y - b.Min.Y

  for targ_w, targ_h in THUMBS:
    #say 'FRODO Thumbnails', targ_w, targ_h
    i = resize.Thumbnail(targ_w, targ_h, img, resize.Bilinear)
    if i == img:
      #say 'FRODO BREAK', targ_w, targ_h
      break  # Original image suffices for remaining sizes.
    else:
      b = i.Bounds()
      w = b.Max.X - b.Min.X
      h = b.Max.Y - b.Min.Y
      varient = 'v_%d_%d_%s' % (w, h, what_format)
      bb = bytes.NewBuffer(None)
      switch what_format:
        case 'jpeg':
          jpeg.Encode(bb, i, JPEG_OPTIONS)
        case 'png':
          png.Encode(bb, i)
        case 'gif':
          gif.Encode(bb, i, None)
        default:
          raise 'Unknown format: %q' % what_format
      #say 'FRODO writeFileFn', bund.bname, path, len(bb.Bytes()), pw, 0, False, varient, suffix, targ_w, targ_h
      writeFileFn(bund, path, bb.Bytes(), pw=pw, mtime=0, raw=False, varient=varient, suffix=suffix)
