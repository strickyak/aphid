from go import fmt, log, os, time

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
  t = int(secs*1000000) * time.Microsecond
  #say 'Before', secs, t, NowMillis()
  time.Sleep(t)
  #say 'After', secs, t, NowMillis()

def Fatal(f, *v):
  log.Printf("F/ " + f, *v)
  Exit(13)

def Err(f, *v):
  log.Printf("E/ " + f, *v)

def Warn(f, *v):
  log.Printf("W/ " + f, *v)

def Throw(f, *v):
  err = fmt.Sprintf(f, *v)
  log.Printf("T/ %s", err)
  raise err

def Note(f, *v):
  log.Printf("N/ " + f, *v)

def Info(f, *v):
  log.Printf("I/ " + f, *v)

Status = 0
def SetExitStatus(status):
  global Status
  Status = status if status > Status else Status

def Exit(status):
  Status = status if status > Status else Status
  if Status:
    Note('Exiting with status %d', Status)
  os.Exit(Status)
  raise 'NOTREACHED'

