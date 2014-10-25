"""
Package flag parses command line flags, similar to golang's flag package.

Three kinds of command line arguments are understood:

  * Flags with dashes and equals, like "--flag_test_b" or "--flag_test_s=foo".
    You can omit "=value" and the value will be "1" or 1 or True.
    The same flag should not be repeated (or last value wins).

  * Triples with double colons, which are like "::name::key::value".
    name and key cannot be empty; value can be empty.
    These are for things where repeated dash flags would be nice.

  * All other arguments.

Usage:
See flag_test_b, flag_test_i, & flag_test_s below for how
to declare them.
See "Munch" inside main() for how to process them.

The value of a flag is in the .X field of the object.

You can run the main to investigate and test:
$ rye run flag.py -- --flag_test_b --flag_test_i=-44  --flag_test_s=fubar   ::a::b::c ::a::d::e ::b::x::y  ::c::d::e::f::g::h:: opposable thumb

"""
from go import regexp

Flags = {}
Triples = {}

FLAG_RE = regexp.MustCompile('^[-][-]?(.+?)([=](.*))?$')
TRIPLE_RE = regexp.MustCompile('^[:][:](.+?)[:][:](.+?)[:][:](.*)$')

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
      f.Set()
    args = args[1:]

  while args:
    m = TRIPLE_RE.FindStringSubmatch(args[0])
    if not m:
      break
    _, name, k, v = m
    t = Triples.setdefault(name, {})
    t[k] = v
    args.pop(0)

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
  
  def Set(x="1"):
    .X = str(x)

class Int:
  def __init__(name, dflt, doc):
    .name = name
    .dflt = dflt
    .X = int(dflt)
    .doc = doc
    Flags[name] = self

  def Value():
    return .X
  
  def Set(x=1):
    .X = int(x)

class Bool:
  def __init__(name, dflt, doc):
    .name = name
    .dflt = dflt
    .X = bool(dflt)
    .doc = doc
    Flags[name] = self

  def Value():
    return .X
  
  def Set(x=True):
    .X = bool(x)
  
flag_test_b = Bool('flag_test_b', False, 'Test flag for Bool')
flag_test_i = Int('flag_test_i', 0, 'Test flag for Int')
flag_test_s = String('flag_test_s', '', 'Test flag for String')

def main(argv):
  "Show me the flags and triples."
  argv = Munch(argv)
  for k, v in sorted(Flags.items()):
    print '--%s = %#v' % (k, v.X)
  for n, t in sorted(Triples.items()):
    for k, v in sorted(t.items()):
      print '%q [ %q ] = %q' % (n, k, v)
  for a in argv:
    print "Arg: %q" % a
pass
