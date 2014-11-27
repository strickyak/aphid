from go import html/template
from go import github.com/microcosm-cc/bluemonday
from go import github.com/russross/blackfriday

def Process(input):
  unsafe = blackfriday.MarkdownCommon(input)
  html = bluemonday.UGCPolicy().SanitizeBytes(unsafe)
  return go_cast(template.HTML, html)
