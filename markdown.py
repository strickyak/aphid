from go import regexp
from go import html/template
from go import github.com/BurntSushi/toml
from go import github.com/microcosm-cc/bluemonday
from go import github.com/russross/blackfriday
from lib import data
from . import sonnet, util

JS_FRONT_MATTER = regexp.MustCompile(`(?s)^({\s*\n.*?\n}\s*\n)(.*)$`)
TOML_FRONT_MATTER = regexp.MustCompile(`(?s)^[+][+][+]\s*\n(.*?\n)[+][+][+]\s*\n(.*)$`)

CR = regexp.MustCompile("\r")

def EvalJSonnet(s):
  js = sonnet.RunSnippet(s)
  f = data.Eval(js)
  return f

def EvalToml(s):
  f = util.NativeMap(dict())
  toml.Decode(s, f)
  return f

def TranslateMarkdown(s):
  t = blackfriday.MarkdownCommon(s)
  html = bluemonday.UGCPolicy().SanitizeBytes(t)
  return go_cast(template.HTML, html)

def ProcessWithFrontMatter(text):
  say text
  text = CR.ReplaceAllString(text, "")
  m1 = JS_FRONT_MATTER.FindStringSubmatch(text)
  m2 = TOML_FRONT_MATTER.FindStringSubmatch(text)
  f = None
  if m1:
    _, front, text = m1
    f = EvalJSonnet(front)
  elif m2:
    _, front, text = m2
    f = EvalToml(front)

  h = TranslateMarkdown(text)
  say f, h 
  return f, h 
