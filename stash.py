from go import bufio, bytes, fmt, log, reflect, regexp, sort, sync, time
from go import html/template, net/http, io/ioutil
from go import crypto/sha256, crypto/aes, crypto/rand, crypto/cipher
from go import github.com/golang/crypto/scrypt
from go import encoding/base64
from . import A, atemplate, bundle, dh, markdown, pubsub, util
from . import adapt, basic, flag
from lib import data

Encode = base64.URLEncoding.EncodeToString
Decode = base64.URLEncoding.DecodeString

MATCH_FILENAME = regexp.MustCompile('.*filename="([^"]+)"').FindStringSubmatch

RE_ABNORMAL_CHARS = regexp.MustCompile('[^-A-Za-z0-9_.]')
def CurlyEncode(s):
  if not s:
    return '{}'
  return RE_ABNORMAL_CHARS.ReplaceAllStringFunc(s, lambda c: '{%d}' % ord(c))

def Seal(key, nonce, plaintext, extra):
  c = cipher.NewGCM(aes.NewCipher(key))
  return c.Seal(None, nonce, plaintext, extra)

def Unseal(key, nonce, ciphertext, extra):
  c = cipher.NewGCM(aes.NewCipher(key))
  return c.Open(None, nonce, ciphertext, extra)

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
          name = fname[5:]
          fpath = '/stash/' + fname
          if fname.startswith('user.'):
            try:
              x = bundle.ReadFile(.bund, fpath)
              .users[name] = data.Eval(x)
            except as ex:
              log.Printf("Reload: Cannot read %q: %v", fpath, ex)
          if fname.startswith('meta.'):
            try:
              x = bundle.ReadFile(.bund, fpath)
              .meta[name] = data.Eval(x)
            except as ex:
              log.Printf("Reload: Cannot read %q: %v", fpath, ex)
      .Users = util.NativeMap(.users)
      .Meta = util.NativeMap(.meta)

  def Handle2(w, r):
    host, extra, path, base = util.HostExtraPathRoot(r)
    say host, extra, path, base

    try:
      return StashHandler(self, w, r, host, path, base)
    except as ex:
      say ex
      print >>w, '<br><br>\n\n*** ERROR *** <br><br>\n\n*** %s ***\n\n***' % ex
      raise ex
      return # raise ex

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
    username = '?'
    u = None
    if path != '/':
      try:
        username, pw = basic.GetBasicPw(w, r, realm)
        u = .master.users[username]
        h = '%x' % sha256.Sum256(Strip(pw))
        if h != u['pw']:
          raise 'Bad username %q or password %q' % (username, h)
        .d['User'] = username
        pass
      except as ex:
        log.Printf("BASIC AUTH: %q %v", username, ex)
        return basic.Fails(w, r, realm)

    .r.ParseForm()
    switch path:

      default:
        .Emit('HOME')

      case '/':
        .Emit('HOME')

      case '/list':
        z = {}
        for f in bundle.ListFiles(.master.bund, '/stash'):
          z[f] = f
        .d['Files'] = master.Meta
        .Emit('LIST')

      case '/view':
        fname = Strip(.r.Form['f'][0])
        .d['Title'] = 'File: %q' % fname
        .d['Text'] = bundle.ReadFile(.master.bund, '/stash/data.' + fname)
        .Emit('VIEW')

      case '/add_user':
        if not u.get('admin'):
          raise 'Cannot add user: You are not an admin.'
        .d['Title'] = 'Add a new user'
        .Emit('ADD_USER')

      case '/submit_add_user':
        if not u.get('admin'):
          raise 'Cannot add user: You are not an admin.'

        button = MustAscii(Strip(.r.PostForm['submit'][0]))
        say button
        if button != 'Save':  # Cancel.
          http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

        say '%v' % .r.Form
        say .r.Form.keys()
        say .r.Form.items()
        say '%v' % .r.PostForm
        say .r.PostForm.keys()
        say .r.PostForm.items()
        newuser = MustUserName(Strip(.r.PostForm['new_user_name'][0]))
        newname = MustAsciiSpace(Strip(.r.PostForm['new_full_name'][0]))
        newpw = MustAsciiSpace(Strip(.r.PostForm['new_passwd'][0]))
        newadmin = MustAscii(Strip(.r.PostForm['new_admin'][0]))

        # Check that the user doesn't already exist.
        if .master.users.get(newuser):
          raise 'User %q already exists.' % newuser

        # Random salt & random nonce.
        salt = mkbyt(12)
        n = rand.Read(salt)
        must n == 12
        nonce = mkbyt(12)
        n = rand.Read(nonce)
        must n == 12

        # Use SCrypt for two hashes: pwhash to check pw, symhash for key to encrypt dh2.Secret().
        pwhash = SCrypt(newpw, salt, "pwhash")
        symhash = SCrypt(newpw, salt, "symhash")

        # Forge a new Diffee-Hellman Public/Secret key pair, and encrypt the Secret.
        dh2 = dh.Forge(newuser, newname, dh.GROUP)
        pt2 = dh2.Secret()
        ct2=Encode(Seal(key=symhash, nonce=nonce, plaintext=pt2, extra=newuser))

        # JSON record of this user's info.
        j = repr(dict(
                 fullname=newname,
                 salt='%x' % salt,
                 nonce='%x' % nonce,
                 pwhash='%x' % pwhash,
                 symhash='%x' % symhash,
                 admin=newadmin.lower().startswith('y'),
                 public=dh2.Public(),
                 secret=ct2
                 ))

        # Check that we can decrypt it.
        ct3 = data.Eval(j)['secret']
        pt3 = Unseal(key=symhash, nonce=nonce, ciphertext=Decode(ct3), extra=newuser)
        must str(pt3) == pt2

        # Write the JSON to the new users's user file.
        bundle.WriteFile(.master.bund, '/stash/user.%s' % newuser, j)
        .master.Reload()
        http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

      case '/upload':
        UserList = dict([(k, v.get('fullname')) for k, v in master.users.items()])
        .d['Title'] = 'Upload a file and share it.'
        .d['Users'] = util.NativeMap(UserList)
        .Emit('UPLOAD')

      case '/submit_upload':
        .r.ParseMultipartForm(10*1024*1024)
        say '%v' % .r
        say '%v' % .r.Host
        say '%v' % .r.RequestURI
        say '%v' % .r.Form
        say '%v' % .r.PostForm
        say '%v' % .r.MultipartForm
        #button = MustAscii(Strip(.r.PostForm['submit'][0]))
        button = Strip(.r.Form.get('submit'))
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
          cfname = CurlyEncode(fname)
          say cfname
          fd = r.MultipartForm.File['file'][0].Open()
          stuff = ioutil.ReadAll(fd)

          bundle.WriteFile(.master.bund, '/stash/data.%s' % cfname, stuff)

          recipients = sorted([.r.Form.get(k) for k in .r.Form.keys() if k.startswith('to_')])
          bundle.WriteFile(.master.bund, '/stash/meta.%s' % cfname, repr(dict(
            title=cfname,
            date=time.Now().Format('2006-01-02 15:04:05'),
            length=len(stuff),
            recipients=recipients,
            )))

          .master.Reload()
        http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

  def Emit(tname):
    #.d['All'] = repr(.d)
    .master.t.ExecuteTemplate(.w, tname, util.NativeMap(.d))

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
        <li> <b>{{.K}}:</b> {{.V.fullname}}: {{.V}}
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
