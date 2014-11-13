package aphid

import "html/template"
import "github.com/strickyak/rye"

func AddAphidTemplateFunctions(t *template.Template) {
  fm := make(template.FuncMap)
  fm["Contents"] = func (p rye.P) interface{} {
    return p.Contents()
  }
  t.Funcs(fm)
}
