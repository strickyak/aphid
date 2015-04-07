from . import markdown
from lib import data

File1 = `{
  'foo': 'bar',
}
one
two
three
`

front, back = markdown.Process(File1)
say front, back
must front == dict(foo='bar')
must str(back) == '<p>one\ntwo\nthree</p>\n'

File2 = `
           {
  'foo': 'bar',
           }
one
two
three
`

front, back = markdown.Process(File2)
say front, back
must front == dict(foo='bar')
must str(back) == '<p>one\ntwo\nthree</p>\n'

File3 = `{nando}`

front, back = markdown.Process(File3)
say front, back
must front == dict(foo='bar')
must str(back) == '<p>one\ntwo\nthree</p>\n'

pass
