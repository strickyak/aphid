from go import encoding/base64

def CheckBasicAuth(w, r, realm, usersToPws):
  """
  CheckBasicAuth returns the username, if valid, or it returns None.
  If it returned None, it has already sent 401, and the caller should do nothing more.
  """
  try:
    a = r.Header.Get('Authorization')
    if not a:
      raise 'Missing Authorization'
    style, encoded = a.split(' ', 1)
    must style == 'Basic'
    decoded = str(base64.StdEncoding.DecodeString(encoded))
    user, pw = decoded.split(':', 1)
    if user is None:
      raise 'Empty User Name'
    wanted = usersToPws.get(user)
    if wanted is None:
      raise 'Bad User Name'
    if wanted != pw:
      raise 'Bad Password'
    return user
  except:
    w.Header().Set("WWW-Authenticate", 'Basic realm="%s"' % realm)
    w.WriteHeader(401)
    w.Write('401 Unauthorized\n')
    return None

def GetBasicPw(w, r, realm):
  say realm
  try:
    a = r.Header.Get('Authorization')
    say a
    if not a:
      raise 'Missing Authorization'
    style, encoded = a.split(' ', 1)
    must style == 'Basic'
    decoded = str(base64.StdEncoding.DecodeString(encoded))
    user, pw = decoded.split(':', 1)
    say user, pw
    return user, pw
  except:
    say 401
    w.Header().Set("WWW-Authenticate", 'Basic realm="%s"' % realm)
    w.WriteHeader(401)
    w.Write('401 Unauthorized\n')
    return None

