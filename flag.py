from go import regexp

Flags = {}

FLAG_RE = regexp.MustCompile('^[-][-]?([A-Za-z0-9_]+)([=](.*))?$')

def Munch(args):
  # Consume flags beginning with '-' or '--'.
  while args:
    m = FLAG_RE.FindStringSubmatch(args[0])
    if not m:
      break
    _, name, valued, value = m
    f = Flags.get(name)
    if not f:
      raise 'No such flag', name
    if valued:
      f.Set(value)
    else:
      f.SetEnabled()
    args = args[1:]

  # Consume '--' as a flags-stopper.
  if args and args[0] == '--':
    args = args[1:]

  # Return the remaining args.
  return args


class String:
  def __init__(name, dflt, doc):
    .name = name
    .dflt = dflt
    .X = str(dflt)
    .doc = doc
    Flags[name] = self

  def Value():
    return .X
  
  def Set(x):
    .X = str(x)
  
  def SetEnabled(x):
    raise 'String-typed flag needs a value', .name


class Int:
  def __init__(name, dflt, doc):
    .name = name
    .dflt = dflt
    .X = int(dflt)
    .doc = doc
    Flags[name] = self

  def Value():
    return .X
  
  def Set(x):
    .X = int(x)
  
  def SetEnabled(x):
    raise 'Int-typed flag needs a value', .name
  

class Bool:
  def __init__(name, dflt, doc):
    .name = name
    .dflt = dflt
    .X = bool(dflt)
    .doc = doc
    Flags[name] = self

  def Value():
    return .X
  
  def Set(x):
    .X = bool(x)
  
  def SetEnabled(x):
    .X = True

pass
