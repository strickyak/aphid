from go import encoding.base64

def CheckBasicAuth(w, r, realm, usersToPws):
  """
  CheckBasicAuth returns the username, if valid, or it returns None.
  If it returned None, it has already sent 401, and the caller should do nothing more.
  """
  try:
    #say realm, usersToPws
    a = r.Header.Get('Authorization')
    if not a:
      raise 'Missing Authorization'
    style, encoded = a.split(' ', 1)
    #say style, encoded
    must style == 'Basic'
    decoded = str(base64.StdEncoding.DecodeString(encoded))
    user, pw = decoded.split(':', 1)
    #say user, pw, decoded
    if user is None:
      raise 'Empty User Name'
    wanted = usersToPws.get(user)
    #say wanted
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
  #say realm
  try:
    a = r.Header.Get('Authorization')
    if not a:
      raise 'Missing Authorization'
    style, encoded = a.split(' ', 1)
    must style == 'Basic'
    decoded = str(base64.StdEncoding.DecodeString(encoded))
    user, pw = decoded.split(':', 1)
    #say user, pw
    return user, pw
  except:
    Fails(w, r, realm)
    return None

def Fails(w, r, realm):
    say 401, realm
    w.Header().Set("WWW-Authenticate", 'Basic realm="%s"' % realm)
    w.WriteHeader(401)
    w.Write('401 Unauthorized\n')

pass
