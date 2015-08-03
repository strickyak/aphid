from go import bufio, bytes, fmt, html, log, reflect, regexp, sort, sync, time
from go import html/template, net/http, io/ioutil
from go import crypto/sha256, crypto/aes, crypto/rand, crypto/cipher
from go import github.com/golang/crypto/scrypt
from go import encoding/base64
from . import A, atemplate, bundle, dh, markdown, pubsub, util
from . import adapt, basic, flag
from lib import data

ADMIN_INIT_PW = flag.String('admin_init_pw', '', 'initial admin password')

MAX_UPLOAD_SIZE = 50*1024*1024  # 50MB.

Encode = base64.URLEncoding.EncodeToString
Decode = base64.URLEncoding.DecodeString

MATCH_FILENAME = regexp.MustCompile('.*filename="([^"]+)"').FindStringSubmatch

def H(s):
  return '%x' % s[:6]

class User:
  def __init__(string=None, username=None, pw=None, fullname=None, admin=None):
    """Provide, by kw, either string or username, pw, fullname, admin."""
    if string:
      d = data.Eval(string)
      .fullname = d['fullname']
      .username = d['username']
      .admin = d['admin']
      .pw = d['pw'] # DEBUG
      .nonce = d['nonce']
      .salt = d['salt']
      #.scrypt_ = d['scrypt'] # DEBUG
      .pwhash = d['pwhash']
      .symhash = d['symhash'] # DEBUG
      say 'LOAD esecret:', .username, .pw, H(.salt), H(.symhash)
      .public = d['public']
      must type(.public) == str, '%T' % .public
      .secret = d['secret'] # DEBUG
      .esecret = d['esecret']
    else:
      .fullname = fullname
      .username = username
      .admin = admin
      .pw = pw  # DEBUG
      .nonce = RandomBytes(12)
      .salt = RandomBytes(12)
      scrypt_ = SCrypt(pw, .salt, '')
      #.scrypt = scrypt_  # DEBUG
      .pwhash = sha256.Sum256(scrypt_ + ':pwhash')
      symhash = sha256.Sum256(scrypt_ + ':symhash')
      .symhash = symhash #DEBUG
      say 'MAKE esecret:', username, pw, H(.salt), H(scrypt_), H(symhash)
      dh_ = dh.Forge('', '', dh.GROUP) # DEBUG
      .dh = dh_
      .public = dh_.Public()
      must type(.public) == str, '%T' % .public
      .secret = dh_.Secret() # DEBUG
      .esecret = Seal(key=symhash, nonce=.nonce, plaintext=dh_.Secret(), extra='esecret:%s' % .username)

  def __str__():
    return repr(dict(
      fullname=.fullname,
      username=.username,
      admin=.admin,
      pw=.pw, # DEBUG
      nonce=.nonce,
      salt=.salt,
      # scrypt=.scrypt_, # DEBUG
      pwhash=.pwhash,
      symhash=.symhash, # DEBUG
      public=.public,
      secret=.secret, # DEBUG
      esecret=.esecret))

  def CheckPassword(pw):
    scrypt2 = SCrypt(pw, .salt, '')
    pwhash2 = sha256.Sum256(scrypt2 + ':pwhash')
    if pwhash2 != .pwhash:
      raise 'Wrong password'
    return True

  def Secret(pw):
    scrypt_ = SCrypt(pw, .salt, '')
    symhash = sha256.Sum256(scrypt_ + ':symhash')
    say 'GET esecret:', .username, pw, H(.salt), H(scrypt_), H(symhash)
    secret = str(Unseal(key=symhash, nonce=.nonce, ciphertext=.esecret, extra='esecret:%s' % .username))
    if .secret:  # DEBUG
      must secret == .secret  # DEBUG
    return secret

  def MutualKey(pw, otherUser):
    must type(.public) == str, '%T' % .public
    dh1 = dh.DhSecret("bogus1", "bogus2", dh.GROUP, dh.Big(.public), dh.Big(.Secret(pw)))
    must type(otherUser.public) == str, '%T' % .public
    mutKey = dh1.MutualKey(str(otherUser.public))

  def SealKeyToSelf(pw, curlyname, now, plainkey):
    scrypt2 = SCrypt(pw, .salt, '')
    symhash2 = sha256.Sum256(scrypt2 + ':symhash')
    nonce2 = RandomBytes(12)
    extra2 = 'for_owner:%d:%s:%s' % (now.Unix(), .username, curlyname)
    ekey = str(Seal(key=symhash2, nonce=nonce2, plaintext=plainkey, extra=extra2))
    return dict(ekey=ekey, nonce=nonce2, extra=extra2)

  def SealKeyToOther(pw, rcpt, curly, now, plainkey):
    dh3 = dh.DhSecret(None, None, dh.GROUP, dh.Big(rcpt.public), dh.Big(.Secret(pw)))
    mutual_key = dh3.MutualKey(rcpt.public)
    nonce3 = RandomBytes(12)
    extra3 = 'for_others:%d:%s:%s:%s' % (now.Unix(), .username, rcpt.username, curly)
    ekey = str(Seal(mutual_key, nonce3, plainkey, extra3)),
    return dict(ekey=ekey, nonce=nonce3, extra=extra3)

def RandomBytes(n):
  z = mkbyt(n)
  n = rand.Read(z)
  must n == n
  return z

RE_ABNORMAL_CHARS = regexp.MustCompile('[^-A-Za-z0-9_.]')
def CurlyEncode(s):
  if not s:
    return '{}'
  return RE_ABNORMAL_CHARS.ReplaceAllStringFunc(s, lambda c: '{%d}' % ord(c))

def Seal(key, nonce, plaintext, extra):
  c = cipher.NewGCM(aes.NewCipher(key))
  z = c.Seal(None, nonce, plaintext, extra)
  say '%x'%key[:6], '%x'%nonce[:6], extra, '%x'%plaintext[:6], 'SealDebug->', '%x'%(z[:6])
  return z

def Unseal(key, nonce, ciphertext, extra):
  c = cipher.NewGCM(aes.NewCipher(key))
  say '%x'%key[:6], '%x'%nonce[:6], extra, '%x'%ciphertext[:6], 'UnsealDebug->........'
  z = c.Open(None, nonce, ciphertext, extra)
  say '%x'%key[:6], '%x'%nonce[:6], extra, '%x'%ciphertext[:6], 'UnsealDebug->', '%x'%(z[:6])
  return z

def Encrypt(key, src):
  key = byt(key)
  must len(key) == 32
  src = byt(src)
  must len(src) == 32
  c = aes.NewCipher(key)
  dst = mkbyt(32)
  c.Encrypt(dst, src)
  return dst

def Decrypt(key, src):
  key = byt(key)
  must len(key) == 32
  src = byt(src)
  must len(src) == 32
  c = aes.NewCipher(key)
  dst = mkbyt(32)
  c.Decrypt(dst, src)
  return dst

def SCrypt(pw, salt, flavor):
  return scrypt.Key(byt(pw), byt(salt) + "::" + byt(flavor), 16384, 8, 1, 32)

def Strip(s):
  return str(s).strip(' \t\n\r')

USERNAME_PAT = regexp.MustCompile('^[a-z0-9_]+$')
def MustUserName(s):
  if not USERNAME_PAT.FindString(s):
    raise 'Bad characters in username %q  (must be a-z 0-9 and _)' % s
  return s

ASCII_PAT = regexp.MustCompile('^[!-~]+$')
def MustAscii(s):
  if not ASCII_PAT.FindString(s):
    raise 'Bad characters in %q  (must be printable ascii)' % s
  return s

ASCII_SPACE_PAT = regexp.MustCompile('^[ !-~]+$')
def MustAsciiSpace(s):
  if not ASCII_SPACE_PAT.FindString(s):
    raise 'Bad characters in %q  (must be printable ascii or space)' % s
  return s

class StashMaster:
  def __init__(aphid, bname, bund, config):
    .mu = go_new(sync.Mutex)
    .aphid = aphid
    .bus = aphid.bus
    .bname = bname
    .bund = bund
    .mu = go_new(sync.Mutex)
    .LoadTemplates()
    .Reload()

  def LoadTemplates():
    .t = template.New('main')
    .t.Funcs(util.TemplateFuncs())
    .t.Parse(TEMPLATES)

  def Reload():
    .mu.Lock()
    with defer .mu.Unlock():
      .users = {}
      .meta = {}
      for fname in bundle.ListFiles(.bund, '/stash'):
        say fname
        if len(fname) > 5:
          name = fname[5:]  # Remove "user." or "meta." or "data."
          fpath = '/stash/' + fname
          if fname.startswith('user.'):
            try:
              x = bundle.ReadFile(.bund, fpath)
              .users[name] = User(string=x)
            except as ex:
              log.Printf("Reload: Cannot read %q: %v", fpath, ex)
          if fname.startswith('meta.'):
            try:
              x = bundle.ReadFile(.bund, fpath)
              .meta[name] = data.Eval(x)
            except as ex:
              log.Printf("Reload: Cannot read %q: %v", fpath, ex)

      say .users
      if not .users.get('admin'):
        say .users
        if not ADMIN_INIT_PW.X:
          raise 'Initial admin pw must be provided by --admin_init_pw='
        nu = User(username='admin', pw=ADMIN_INIT_PW.X, fullname='Administrator Account', admin=True)
        .users['admin'] = nu
        bundle.WriteFile(.bund, '/stash/user.admin', str(nu))

      tmp_users = dict([(k, util.NativeMap(dict(fullname=v.fullname, username=v.username, admin=("1" if v.admin else ""))))
                        for k, v in .users.items()])
      tmp_users = dict([(k, util.NativeMap(dict(fullname=v.fullname, username=v.username, admin=v.admin)))
                        for k, v in .users.items()])
      .Users = util.NativeMap(tmp_users)
      .Meta = util.NativeMap(.meta)

  def Handle2(w, r):
    host, extra, path, base = util.HostExtraPathRoot(r)
    say host, extra, path, base

    try:
      return StashHandler(self, w, r, host, path, base)
    except as ex:
      say ex
      w.Header().Set('Content-Type', 'text/html')
      htex = html.EscapeString('%v' % ex)
      print >>w, '<br><br>\n\n*** ERROR *** <br><br>\n\n*** %s ***\n\n***' % htex
      raise ex

class StashHandler:
  def __init__(master, w, r, host, path, base):
    .master = master
    .w = w
    .r = r
    .host = host
    .path = path
    .base = base

    master.mu.Lock()
    with defer master.mu.Unlock():
      .d = dict(Users=master.Users, Meta=master.Meta,
                R=r, Host=host, Path=path, Base=base,
                Title='Stash of Files')

    realm = 'Stash-%s' % master.bund.bname
    .username = '?'
    .u = None
    if path != '/':
      try:
        .username, .pw = basic.GetBasicPw(w, r, realm)
        say .username, .pw, Strip(.pw)
        .u = .master.users[.username]
        .u.CheckPassword(.pw)
      except as ex:
        log.Printf("BASIC AUTH: %q %v", .username, ex)
        return basic.Fails(w, r, realm)

    .r.ParseForm()
    say '%v' % .r.Form
    say '%v' % .r.PostForm

    switch path:

      default:
        .Emit('HOME')

      case '/':
        .Emit('HOME')

      case '/logout':
        return basic.Fails(w, r, realm)

      case '/admin':
        if not .u.admin:
          return basic.Fails(w, r, realm)
        .Emit('HOME')

      case '/list':
        z = {}
        for k, v in master.meta.items():
          if .username == v['owner'] or .username in v['for_others']:
            z[k] = v
          elif .u.admin:  # But no key!
            z['~~' + k + '~~'] = v
        .d['Files'] = util.NativeMap(z)
        .d['Admin'] = True if .u.admin else None
        .Emit('LIST')

      case '/view':
        fname = Strip(.r.Form['f'][0])
        .d['Title'] = 'File: %q' % fname

        datum = bundle.ReadFile(.master.bund, '/stash/data.' + fname)
        meta = bundle.ReadFile(.master.bund, '/stash/meta.' + fname)

        plain, content_type = .DecryptDataWithMeta(datum, meta)

        if fname.lower().endswith('.jpg') or fname.lower().endswith('.jepg'):
          .EmitJpg(plain)

        else:
          .d['Text'] = plain
          .Emit('VIEW')

      case '/add_user':
        if not .u.admin:
          raise 'Cannot add user: You are not an admin.'
        .d['Title'] = 'Add a new user'
        .Emit('ADD_USER')

      case '/submit_add_user':
        if not .u.admin:
          raise 'Cannot add user: You are not an admin.'

        button = MustAscii(Strip(.r.PostForm['submit'][0]))
        say button
        if button != 'Save':  # Cancel.
          http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

        newuser = MustUserName(Strip(.r.PostForm['new_user_name'][0]))
        newname = MustAsciiSpace(Strip(.r.PostForm['new_full_name'][0]))
        newpw = MustAsciiSpace(Strip(.r.PostForm['new_passwd'][0]))
        newadmin = MustAscii(Strip(.r.PostForm['new_admin'][0]))

        # Check that the user doesn't already exist.
        if .master.users.get(newuser):
          raise 'User %q already exists.' % newuser

        nu = User(username=newuser, pw=newpw, fullname=newname, admin=newadmin.lower()[0] == 'y')

        # Write the JSON to the new users's user file.
        bundle.WriteFile(.master.bund, '/stash/user.%s' % newuser, str(nu))
        .master.Reload()
        http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

      case '/upload':
        UserList = dict([(k, v.fullname) for k, v in master.users.items()])
        .d['Title'] = 'Upload a file and share it.'
        .d['Users'] = util.NativeMap(UserList)
        .Emit('UPLOAD')

      case '/submit_upload':
        .r.ParseMultipartForm(MAX_UPLOAD_SIZE)
        say '%v' % .r
        say '%v' % .r.Host
        say '%v' % .r.RequestURI
        say '%v' % .r.Form
        say '%v' % .r.PostForm
        say '%v' % .r.MultipartForm
        button = MustAscii(Strip(.r.Form.get('submit')))
        say button
        if button != 'Save':  # Cancel.
          http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

        cd = r.MultipartForm.File['file'][0].Header.Get('Content-Disposition')
        match = MATCH_FILENAME(cd)
        say match
        if match:
          f = match[1]
        say f
        if f:
          fname = r.MultipartForm.File['file'][0].Filename
          say fname
          curly = CurlyEncode(fname)
          say curly
          fd = r.MultipartForm.File['file'][0].Open()
          contents = ioutil.ReadAll(fd)
          title = .r.Form.Get('title')

          # Encrypt the contents with a random key.
          filekey = RandomBytes(32)
          nonce = RandomBytes(12)
          extra = 'filekey:%s:%s' % (.username, curly)  # Username & Filename.
          ciphertext = Seal(filekey, nonce, contents, extra)
          now = time.Now()
          bundle.WriteFile(.master.bund, '/stash/data.%s' % curly, ciphertext)

          for_owner = .u.SealKeyToSelf(.pw, curly, now, filekey)

          # Chosen recipients.
          recipients = [.r.Form.get(k)
                        for k in .r.Form.keys()
                        if k.startswith('to_')]

          # Always add admins.
          recipients += [k for k, v in .master.users.items() if v.admin and k not in recipients]
          
          for_others = dict([(rcpt, .u.SealKeyToOther(.pw, .master.users.get(rcpt), curly, now, filekey))
                             for rcpt in recipients
                             if rcpt != .username
                             and .master.users.get(rcpt)])

          bundle.WriteFile(.master.bund, '/stash/meta.%s' % curly, repr(dict(
            title=title,
            curly=curly,
            owner=.username,
            date=now.Format('2006-01-02 15:04:05'),
            seconds=now.Unix(),
            length=len(contents),
            nonce=nonce,
            extra=extra,
            for_owner=for_owner,
            for_others=for_others,
            )))

          .master.Reload()

        http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

  def Emit(tname):
    .w.Header().Set('Content-Type', 'text/html')
    .master.t.ExecuteTemplate(.w, tname, util.NativeMap(.d))

  def EmitJpg(contents):
    .w.Header().Set('Content-Type', 'image/jpeg')
    bw = bufio.NewWriter(.w)
    bw.Write(contents)
    bw.Flush()

  def DecryptDataWithMeta(datum, meta):
    m = data.Eval(meta)
    say 'UnsealDebug BEGIN', m
    if .username == m['owner']:
      fo = m['for_owner']
      say .username, fo
      ekey = fo['ekey']
      scrypt2 = SCrypt(.pw, .u.salt, '')
      keykey = sha256.Sum256(scrypt2 + ':symhash')
      say .username, .pw, .u.salt, H(scrypt2), H(keykey)
      nonce2 = fo['nonce']
      extra2 = fo['extra']
      say H(nonce2), H(extra2)
      # Decrypt the decryption key for the datum.
      say 'UnsealDebug Decrypt for Owner', H(scrypt2), H(keykey), H(nonce2), H(extra2), .username
      key = str(Unseal(key=keykey, nonce=nonce2, ciphertext=ekey, extra=extra2))
    else:
      fo = m['for_others']
      for_me = fo.get(.username)
      if not for_me:
        raise 'This document %q has not been shared with you %q.' % (m.get('curly'), .username)
      ekey = for_me['ekey']
      keykey = .u.MutualKey(.pw, .master.users[m['owner']])
      nonce2 = for_me['nonce']
      extra2 = for_me['extra']
      # Decrypt the decryption key for the datum.
      say 'UnsealDebug Decrypt for Other', keykey, nonce2, extra2, for_me, .u, m['owner'], .master.users[m['owner']]
      key = str(Unseal(key=keykey, nonce=nonce2, ciphertext=ekey, extra=extra2))

    # Decrypt the datum.
    nonce = m['nonce']
    extra = m['extra']
    say H(nonce), H(extra)
    say 'UnsealDebug Datum', key, nonce, extra
    plain = str(Unseal(key=key, nonce=nonce, ciphertext=datum, extra=extra))
    say 'UnsealDebug END', m
    return plain, 'text/plain'



TEMPLATES = `
{{define "HEAD"}}
  <html><head>
    <title>{{.TItle}}</title>
  </head><body>
    <h2>{{.Title}}</h2>
    {{/* <p>ALL = {{.All}} */}}
    <p>
{{end}}

{{define "TAIL"}}
  </body></html>
{{end}}

{{define "HOME"}}
  {{ template "HEAD" $ }}
    Until we implement login,
    you can <a href="{{$.Base}}list">list</a> all files.
  {{ template "TAIL" $ }}
{{end}}

{{define "LIST"}}
  {{ template "HEAD" $ }}
    <b>Users:</b>
      <ul>
        {{ range $.Users | KV }}
          <li> <b>{{.K}}:</b> &nbsp; {{.V.fullname}}
               {{ if .V.admin }}
                 &nbsp; <b>(admin) </b>
               {{ end }}
        {{ else }}
          <li> (There are no users.)
        {{ end }}
      </ul>
    <b>Files:</b>
      <ul>
        {{ range $.Files | KV }}
          <li> <a href="{{$.Base}}view?f={{.K}}">{{.K}}</a>
        {{ else }}
          <li> (There are no files.)
        {{ end }}
      </ul>
    <b>Actions:</b>
      <ul>
          <li> <a href="{{$.Base}}upload">Upload a new file.</a>
        {{ if .Admin }}
          <li> <a href="{{$.Base}}add_user">Add a new user.</a>
        {{ end }}
      </ul>
  {{ template "TAIL" $ }}
{{end}}

{{define "VIEW"}}
  {{ template "HEAD" $ }}
    <div class="Text">
      <pre>{{ .Text }}</pre>
    </div>
  {{ template "TAIL" $ }}
{{end}}

{{define "ADD_USER"}}
  {{ template "HEAD" $ }}
    <div class="Form">
      <form method="POST" action="{{$.Base}}submit_add_user">

        Create a new user:
        <p>
        User Name: &nbsp; <input type=text size=20 name=new_user_name>
        <p>
        Full Name: &nbsp; <input type=text size=80 name=new_full_name>
        <p>
        Password: &nbsp; <input type=text size=24 name=new_passwd>
        <p>
        Admin: &nbsp; <input type=text size=5 name=new_admin value="no">
        <p>
        <input type=submit name=submit value=Save> &nbsp; &nbsp;
        <input type=reset name=reset value=reset> &nbsp; &nbsp;
        <input type=submit name=submit value=Cancel> &nbsp; &nbsp;

      </form>
    </div>
  {{ template "TAIL" $ }}
{{end}}
{{define "UPLOAD"}}
  {{ template "HEAD" $ }}
    <form method="POST" action="{{$.Base}}submit_upload" enctype="multipart/form-data">

      Share this upload with: <br>
      {{ range $.Users | KV }}
             &nbsp; &nbsp; &nbsp;
             <input type=checkbox name="to_{{.K}}" value="{{.K}}">
             {{.K}} ( {{.V}} )<br>
      {{ end }}
      <br>
      <br>
      Give a Title to the file: <input type=text size=80 name=title>
      <br>
      <br>
      Upload a new attachment:
      <input type="file" name="file">
      <br>
      <br>
      <input type=submit name=submit value=Save> &nbsp; &nbsp;
      <input type=reset name=reset value=Reset> &nbsp; &nbsp;
      <input type=submit name=submit value=Cancel> &nbsp; &nbsp;

    </form>
  {{ template "TAIL" $ }}
{{end}}
`
