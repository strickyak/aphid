from . import flag
#from go import html
from go import os
from go import path/filepath

def ReadAlbumDirs(input_dir):
  f = os.Open(input_dir)
  with defer f.Close():
    names = f.Readdirnames(-1)
    for name in names:
      stat = os.Stat(filepath.Join(input_dir, name))
      if stat.IsDir():
        yield name

def RenderDir(album_names, output_dir):
  index = filepath.Join(output_dir, 'index.html')
  f = os.Create(index)
  with defer f.Close():
    f.Write('<html><body><h3>Gallery %s</h3> <ul>\n' % output_dir)
    for name in album_names:
      f.Write('<li><a href="%s">%q</a></li>\n' % (name, name))

def ReadPhotosInDir(input_dir):
  f = os.Open(input_dir)
  with defer f.Close():
    names = f.Readdirnames(-1)
    for name in names:
      stat = os.Stat(filepath.Join(input_dir, name))
      if stat.IsDir() == False:
        yield name

def RenderAlbum(photo_names, output_dir):
  index = filepath.Join(output_dir, 'index.html')
  f = os.Create(index)
  with defer f.Close():
    f.Write('<html><body><h3>Album %s</h3> <ul>\n' % output_dir)
    for name in photo_names:
      f.Write('<li><a href="%s"><img src="%s" /></a></li>\n' % (name, name))

def LinkPhotos(photo_names, input_dir, output_dir):
  for photo in photo_names:
    photo_orig = filepath.Join(input_dir, photo)
    photo_dest = filepath.Join(output_dir, photo)
    os.Link(photo_orig, photo_dest)


input_dir = flag.String('input', '', 'The input directory.')
output_dir = flag.String('output', '', 'The output directory.')

def main(argv):
  argv = flag.Munch(argv)

  album_dirs = list(ReadAlbumDirs(input_dir.X))
  RenderDir(album_dirs, output_dir.X)
  for dir in album_dirs:
    photo_dir = filepath.Join(input_dir.X, dir)
    output_dir = filepath.Join(output_dir.X, dir)
    photos = list(ReadPhotosInDir(photo_dir))
    os.MkdirAll(output_dir, os.ModePerm)
    RenderAlbum(photos, output_dir)
    LinkPhotos(photos, photo_dir, output_dir)
