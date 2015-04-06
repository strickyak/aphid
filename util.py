from go import regexp, reflect, sort, html/template

MATCH_HOST_IN_PATH = regexp.MustCompile('/@([-A-Za-z0-9.]+)(@\\w+)?($|/.*$)').FindStringSubmatch

def HostExtraPathRoot(r):
  path = r.URL.Path
  m = MATCH_HOST_IN_PATH(path)
  if m:
    return m[1], m[2], m[3], '/@%s%s' % (m[1], m[2])
  return r.Host, '', path, ''

def TemplateFuncs():
  native:
    `
      m := make(i_template.FuncMap)
      m["keys"] = func (a interface{}) []string {
        var z []string
        for _, k := range reflect.ValueOf(a).MapKeys() {
          z = append(z, k.Interface().(string))
        }
        i_sort.Strings(z)
        return z
      }
      return MkGo(m)
    `

pass

native:
  `type NativeMap map[string]interface{}`

def NativeExecuteTemplate(t, w, name, d):
  native:
    `
      z := make(NativeMap)
      for k, v := range a_d.Dict() {
         var val interface{} = v.Contents()

         println(fmt.Sprintf("afugio::NativeExecuteTemplate [%q] == <<<%#v>>>", k, val))
         //println(fmt.Sprintf("afugio::NativeExecuteTemplate [%q] == <<<%#v>>>", k, i_reflect.ValueOf(val)))
         //println(fmt.Sprintf("afugio::NativeExecuteTemplate [%q] == <<<%#v>>>", k, i_reflect.ValueOf(val).Type()))
         //println(fmt.Sprintf("afugio::NativeExecuteTemplate [%q] == <<<%#v>>>", k, i_reflect.ValueOf(val).Type().String()))

         z[k] = val
      }
      a_t.Contents().(*i_template.Template).ExecuteTemplate(
          a_w.Contents().(io.Writer), 
          a_name.String(),
          z)
    `
