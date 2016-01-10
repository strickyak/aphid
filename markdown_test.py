from . import markdown
from rye_lib import data

File1 = `{
  "foo": "bar",
}
one
two
three
`

front, md, back = markdown.ProcessWithFrontMatter(File1)
say front, md, back
must front == dict(foo='bar')
must str(back) == '<p>one\ntwo\nthree</p>\n'

File2 = `{
  "foo": "bar",
}
one
two
three
`

front, md, back = markdown.ProcessWithFrontMatter(File2)
say front, md, back
must front == dict(foo='bar')
must str(back) == '<p>one\ntwo\nthree</p>\n'

File3 = `{nando}`  # Has no front matter.

front, md, back = markdown.ProcessWithFrontMatter(File3)
say front, md, back
must front is None 
must str(back) == '<p>{nando}</p>\n'

pass
