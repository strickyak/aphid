from go import bytes, io/ioutil, os, regexp
from go import html/template
from go import github.com/BurntSushi/toml
from go import github.com/microcosm-cc/bluemonday
from go import github.com/russross/blackfriday
from lib import data
from . import util

JS_FRONT_MATTER = regexp.MustCompile(`(?s)^({\s*\n.*?\n}\s*\n)(.*)$`)
TOML_FRONT_MATTER = regexp.MustCompile(`(?s)^[+][+][+]\s*\n(.*?\n)[+][+][+]\s*\n(.*)$`)

CR = regexp.MustCompile("\r")

HACK_JS = regexp.MustCompile(`([a-z][-a-z0-9_]+)[:]`)
def EvalJS(s):
  # HACK to quote keys that were written in jsonnet.
  t = str(HACK_JS.ReplaceAll(s, `"$1":`))
  #say s
  #say t
  f = data.Eval(t)
  return f

def EvalToml(s):
  f = util.NativeMap(dict())
  toml.Decode(s, f)
  return f

def EncodeToml(x):
  say x
  b = go_new(bytes.Buffer)
  toml.NewEncoder(b).Encode(x)
  z = str(b)
  say z
  return z

def TranslateMarkdown(s):
  if s and s.strip():
    t = blackfriday.MarkdownCommon(s)
    html = bluemonday.UGCPolicy().SanitizeBytes(t)
  html = html if html else ''
  return go_cast(template.HTML, html)

def ProcessWithFrontMatter(text):
  say text
  text = CR.ReplaceAllString(text, "")
  m1 = JS_FRONT_MATTER.FindStringSubmatch(text)
  m2 = TOML_FRONT_MATTER.FindStringSubmatch(text)
  f = None
  if m1:
    _, front, md = m1
    f = EvalJS(front)
  elif m2:
    _, front, md = m2
    f = EvalToml(front)
  else:
    md = text
    f = None

  h = TranslateMarkdown(md)
  say f, md, h 
  return f, md, h 

def main(args):
  s = ioutil.ReadAll(os.Stdin)
  f, md, h = ProcessWithFrontMatter(s)
  print >> os.Stderr, repr(f)
  print h
