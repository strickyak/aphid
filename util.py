from go import os, regexp, reflect, sort, html/template
from go import path as PATH

def PrettyPrint(x, w=os.Stdout, pre=''):
  switch type(x):
    case dict:
      for k, v in sorted(x.items()):
        print >>w, pre + '. [', repr(k), ']'
        PrettyPrint(v, w, pre+'.   ')
    case list:
      for e in x:
        PrettyPrint(e, w, pre+'- ')
    default:
      print >>w, pre + '@ ', repr(x)

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

#MATCH_HOST_IN_PATH = regexp.MustCompile('/+@([-A-Za-z0-9.]+)($|/.*$)').FindStringSubmatch
MATCH_HOST_IN_PATH = regexp.MustCompile('/@([-A-Za-z0-9.]+)([*]+|@\\w+)?($|/.*$)').FindStringSubmatch

def ConvertToNanos(x):
  x = int(x)
  if x < 5000000000:
    return x * 1000000000
  if x < 5000000000000:
    return x * 1000000
  if x < 5000000000000000:
    return x * 1000
  return x


def HostExtraPathRoot(r):
  path = r.URL.Path
  m = MATCH_HOST_IN_PATH(path)
  if m:
    return m[1], m[2], m[3], '/@%s%s/' % (m[1], m[2])
  return r.Host, '', path, '/'

def ParseQuery(r):
  r.ParseForm()
  query = {}
  for k, v in r.Form.items():
    say k, v
    if len(v):
      # Assume single values.
      query[k] = v[0]
  return query

def ConstructQueryFromDict(d):
  return '&'.join(['%s=%v' % (k, v) for k, v in d.items()])

native: `
  type KeyVal struct { K string; V interface{} }

   func Func_KV(a interface{}) []KeyVal {
        var z []string
        for _, k := range reflect.ValueOf(a).MapKeys() {
          z = append(z, k.Interface().(string))
        }
        i_sort.Strings(z)
        var zz []KeyVal
        for _, k := range z {
          zz = append(zz, KeyVal{ K: k, V: reflect.ValueOf(a).MapIndex(reflect.ValueOf(k)).Interface() })
        }
        return zz
    }
    func Func_Keys(a interface{}) []string {
        var z []string
        for _, k := range reflect.ValueOf(a).MapKeys() {
          z = append(z, k.Interface().(string))
        }
        i_sort.Strings(z)
        return z
    }
    func Func_Repr(a interface{}) string {
        if s, ok := a.(P); ok {
          return s.Repr()
        }
        return fmt.Sprintf("%#v", a)
    }
    func Func_String(a interface{}) string {
      switch t := a.(type) {
        case string:
          return t
        case fmt.Stringer:
          return t.String()
      }
      return fmt.Sprintf("%v", a)
    }
    func Func_JoinPaths(a interface{}, b interface{}) string {
        s1 := Func_String(a)
        s2 := Func_String(b)
        return i_PATH.Join(s1, s2)
    }
`

def TemplateFuncs():
  native:
    `
      m := make(i_template.FuncMap)
      m["KV"] = Func_KV
      m["Keys"] = Func_Keys
      m["Repr"] = Func_Repr
      m["String"] = Func_String
      m["JoinPaths"] = Func_JoinPaths
      return MkGo(m)
    `

native:
  `type NativeSlice []interface{}`
native:
  `type NativeMap map[string]interface{}`

def NativeSlice(vec):
  native:
    `
      z := make(NativeSlice, a_vec.Self.Len())
      for i, e := range a_vec.Self.List() {
         z[i] = e.Self.Contents()
      }
      return MkGo(z)
    `
def NativeMap(d):
  native:
    `
      z := make(NativeMap)
      for k, v := range a_d.Self.Dict() {
         z[k] = v.Self.Contents()
      }
      return MkGo(z)
    `

def NativeDeeply(a):
  switch type(a):
    case dict:
      return NativeMap(dict([(k, NativeDeeply(v)) for k, v in a.items()]))
    case set:
      return NativeMap(dict([(k, True) for k in a]))
    case list:
      return NativeSlice([NativeDeeply(e) for e in a])
    case tuple:
      return NativeSlice([NativeDeeply(e) for e in a])
  native:
    ` return MkGo(a_a.Self.Contents()) `

pass
