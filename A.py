from go import fmt, os, time

def ParseCommaEqualsDict(s):
  d = {}
  for kv in s.split(','):
    tmp = kv.strip(' \t')
    if not tmp:
      continue
    k, v = tmp.split('=', 1)
    d[k] = v
  return d

def NowSecs():
  return time.Now().Unix()

def NowMillis():
  return time.Now().UnixNano() // 1000000

def NowNanos():
  return time.Now().UnixNano()

def Sleep(secs):
  micros = int(secs*1000000.0) * time.Microsecond
  say 'Before', secs, micros, NowMillis()
  time.Sleep(micros)
  say 'After', secs, micros, NowMillis()

def Fatal(s):
  fmt.Fprintf(os.Stderr, '\n@0 %s\n', s)
  Exit(13)

def Err(s):
  fmt.Fprintf(os.Stderr, '\n@1 %s\n', s)

def Warn(s):
  fmt.Fprintf(os.Stderr, '\n@2 %s\n', s)

def Throw(s):
  err = str(s)
  fmt.Fprintf(os.Stderr, '\n@3 %s\n' % err)
  raise err

def Note(s):
  fmt.Fprintf(os.Stderr, '\n@4 %s\n', s)

def Info(s):
  fmt.Fprintf(os.Stderr, '\n@5 %s\n', s)

def Debug(level, s):
  fmt.Fprintf(os.Stderr, '\n@%d %s\n', level + 6, s)

Status = 0
def SetExitStatus(status):
  global Status
  Status = status if status > Status else Status

def Exit(status):
  Status = status if status > Status else Status
  if Status:
    Note('Exiting with status %d' % Status)
  os.Exit(Status)
  raise 'NOTREACHED'
