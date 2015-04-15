from go import regexp
from go import html/template
from go import github.com/microcosm-cc/bluemonday
from go import github.com/russross/blackfriday
from lib import data
from . import sonnet

FRONT_MATTER = regexp.MustCompile(`(?s)^({\s*\n.*?\n}\s*\n)(.*)$`)

CRLF = regexp.MustCompile("\r")

def Process(text):
  text = CRLF.ReplaceAllString(text, "")
  f = None
  m = FRONT_MATTER.FindStringSubmatch(text)
  if m:
    _, front, text = m
    say front, text
    try:
      js = sonnet.RunSnippet(front)
      f = data.Eval(js)
    except as ex:
      print
      say ex
      print
      raise ex
    say front, text, f
    
  say text
  unsafe = blackfriday.MarkdownCommon(text)
  say unsafe
  html = bluemonday.UGCPolicy().SanitizeBytes(unsafe)
  say html
  return f, go_cast(template.HTML, html)
