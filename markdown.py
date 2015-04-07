from go import regexp
from go import html/template
from go import github.com/microcosm-cc/bluemonday
from go import github.com/russross/blackfriday
from lib import data

FRONT_MATTER = regexp.MustCompile(`(?s)^(\s*{\s*\n.*?\n\s*}\s*\n)(.*)$`)

def Process(text):
  f = None
  m = FRONT_MATTER.FindStringSubmatch(text)
  if m:
    _, front, text = m
    f = data.Eval(front)
    
  unsafe = blackfriday.MarkdownCommon(text)
  html = bluemonday.UGCPolicy().SanitizeBytes(unsafe)
  return f, go_cast(template.HTML, html)
