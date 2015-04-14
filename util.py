from go import regexp, reflect, sort, html/template

def Nav(top, *keys):
  """Navigate cascaded dicts from top dictionary through keys, making dicts as needed."""
  d = top
  for key in keys:
    if key in d:
      d = d[key]
    else:
      t = {}
      d[key] = t
      d = t
  return d

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

native:
  `type NativeSlice []interface{}`
native:
  `type NativeMap map[string]interface{}`

def NativeSlice(vec):
  native:
    `
      z := make(NativeSlice, a_vec.Len())
      for i, e := range a_vec.List() {
         z[i] = e.Contents()
      }
      return MkGo(z)
    `
def NativeMap(d):
  native:
    `
      z := make(NativeMap)
      for k, v := range a_d.Dict() {
         z[k] = v.Contents()
      }
      return MkGo(z)
    `
pass
