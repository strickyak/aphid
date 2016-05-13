#from . import util

def Resolve(root, path):
  words = [e for e in path.split('/') if e]
  context = [ 1 ]
  envs = []
  say 'RESOLVE', path, words

  z = None
  sofar = '/'
  for w in words + [None]:
    say 'RESOLVE WORD', w, context

    # Return for terminals.
    if w is None and z is not None:
      say path, z
      return z

    if z is not None:
      raise 'Got result %q before path %q is finished, at level %q' % (z, path, w)

    # Build the env for this level.
    env = dict()
    env['__path'] = sofar

    # For each input context, we append 5tuples for all vars to the env. 
    for c in context:
      d = root[c]
      say c, d

      def appendNormalKeyValuesToEnv(d_):
        for k, v in d_.items():
          if k.startswith('__'): continue
          if k not in env: env[k] = []
          say (context, c, d_, k, v)
          env[k].append( (context, c, d_, k, v) )
        pass

      appendNormalKeyValuesToEnv(d)
      #for k, v in d.items():
      #  if k.startswith('__'): continue
      #  if k not in env: env[k] = []
      #  say (context, c, d, k, v)
      #  env[k].append( (context, c, d, k, v) )

      baseContexts = []
      def followBases(child):
        # We may have a chain of __base to merge in.
        base = child.get('__base')
        if not base:
          return

        say child, base
        must type(base) is str
        must base
        bb = [e for e in base.split('/') if e]
        must bb
        must len(bb) == 1  # We don't handle long bases yet.
        b0 = bb[0]

        # b0 is the name we are looking for, and found_b0 is a list of those we found.
        # Once we find at least one b0 at a level, we don't go up farther.
        found_b0 = []
        for up in Reversed(envs):
          say b0, up
          for got_b0 in up.get(b0):
            say b0, up, got_b0
            cx_, c_, d_, k_, v_ = got_b0
            say cx_, c_, d_, k_, v_
            if type(v_) is int:  # Int is a link to another Tuple.
              found_b0.append(v_)
          say b0, got_b0, found_b0
          if found_b0:
            break
        say b0, found_b0
        if not found_b0:
          raise 'Cannot find base key %q in context %s' % (base, str(c))
        for child_num_ in found_b0:
          child_ = root[child_num_]
          appendNormalKeyValuesToEnv(child_)
          followBases(child_)
        baseContexts += found_b0
      followBases(d)
        
    envs.append(env)
    print 'BEFORE LEVEL %q OF %q' % (str(w), path)
    #util.PrettyPrint(env)

    # Return for tuple results.
    if w is None:
      z = set([e for e in env.keys() if not e.startswith('__')])
      say path, z
      return z

    # Build the context for the next level.
    nextContext = []
    answers = env.get(w)  # Get answer from env we built above.
    say w, answers, z
    if not answers:
      raise 'Key %q not found in context %s' % (w, repr(context))

    keys = []
    for (cx, c, d, k, v) in answers:
      say (cx, c, d, k, v)
      keys.append(k)
      say keys, type(v), v, z
      if type(v) is int:
        say v
        nextContext.append(v)
        say nextContext
      if type(v) is str and z is None:
        say v
        z = v
    context = nextContext
    say context

    sofar = '%s/%s' % (sofar, w)

  raise 'NOTREACHED'

def Reversed(vec):
  z = [e for e in vec]
  z.reverse()
  return z

def main(_):
  root = {
      1: dict(OLD=3, NEW=7),
      3: dict(info=4, P=5, Q=6),
      4: dict(age="old"),
      5: dict(__base="info", size="small"),
      6: dict(__base="P", size="medium"),
      7: dict(__base="OLD", info=8),
      8: dict(__enhance=True, age="new"),
      }

  print
  print
  must Resolve(root, '/') == set(["NEW", "OLD"])
  print
  print
  must Resolve(root, '/OLD') == set(["P", "Q", "info"])
  print
  print
  must Resolve(root, '/NEW') == set(["P", "Q", "info"])
  print

  print
  must Resolve(root, '/OLD/P/size') == 'small'
  print
  print
  must Resolve(root, '/OLD/Q/size') == 'medium'
  print
  print
  must Resolve(root, '/OLD/P/age') == 'old'
  print
  print
  must Resolve(root, '/OLD/Q/age') == 'old'
  print

  print
  must Resolve(root, '/NEW/P/size') == 'small'
  print
  print
  must Resolve(root, '/NEW/Q/size') == 'medium'
  print
  print
  must Resolve(root, '/NEW/P/age') == 'new'
  print
  print
  must Resolve(root, '/NEW/Q/age') == 'new'
  print
