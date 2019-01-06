import markdown

def main(args):
  for a in args:
    say a
    fd = open(a)
    with defer fd.close():
      t = fd.read()
      f, h = markdown.Process(t)
      say f
      say h
      say '############################'
