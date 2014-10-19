# Resize a jpeg image.
# Usage:
#    resize H W in.jpg out.jpg

from go import github.com/nfnt/resize
from go import image/jpeg
from go import os

def main(argv):
  w, h, filein, fileout = argv
  img = jpeg.Decode(os.Open(filein))
  newimg = resize.Resize(int(w), int(h), img, resize.NearestNeighbor)

  fd = os.Create(fileout)
  with defer fd.Close():
    jpeg.Encode(fd, newimg, go_new(jpeg.Options) { Quality: 90 })
