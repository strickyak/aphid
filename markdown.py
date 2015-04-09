from go import regexp
from go import html/template
from go import github.com/microcosm-cc/bluemonday
from go import github.com/russross/blackfriday
from lib import data
from . import sonnet

FRONT_MATTER = regexp.MustCompile(`(?s)^({\s*\n.*?\n}\s*\n)(.*)$`)

def Process(text):
  f = None
  m = FRONT_MATTER.FindStringSubmatch(text)
  if m:
    _, front, text = m
    js = sonnet.RunSnippet(front)
    f = data.Eval(js)
    say front, text, f
    
  unsafe = blackfriday.MarkdownCommon(text)
  html = bluemonday.UGCPolicy().SanitizeBytes(unsafe)
  return f, go_cast(template.HTML, html)
