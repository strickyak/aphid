from go import html/template

PlainBase = template.New("atemplate.py")

def AddContentsFunction(t):
  "Install a template function 'unrye' that gets the contents from a PGo."
  "Usage: {{range .Debug | unrye}} <li> {{.}}"
  native:
    't := a_t.Contents().(*i_template.Template)'
    'fmap := make(i_template.FuncMap)'
    'fmap["unrye"] = func (p P) interface{} {'
    '  return p.Contents()'
    '}'
    't.Funcs(fmap)'
# Add the above FuncMap to the PlainBase.
AddContentsFunction(PlainBase)

PlainBase.Parse('''
  {{template "Main" .}}

  {{define "Main"}}
    <html><head>
      <title>{{.Title}}</title>
    </head><body>
      {{template "HeadBar" .}}
      <h1 class="Title">{{.Title}}</h1>
      {{template "Inner" .}}
      {{template "FootBar" .}}
      {{template "Debug" .}}
    </body></html>
  {{end}}

  {{define "HeadBar"}}
  {{end}}

  {{define "FootBar"}}
  {{end}}

  {{define "Debug"}}
    <p>
    <hr>
    <p>
    <b>Debug:</b>
    <ul class="Debug">
      {{range .Debug | unrye}} <li> {{.}}
      {{else}} <li> (No Debug Info.)
      {{end}}
    </ul>
    <p>
  {{end}}
''')


FancyBase = PlainBase.Clone().Parse('''
  {{define "HeadBar"}}
    <table class="HeadBar" width=100% border=0 cellpadding=8 style="background: #EEEEEE;"><tr>
    <td>{{.HeadBox}}
    </tr></table>
  {{end}}

  {{define "FootBar"}}
    <table border="0" cellpadding="50"><tr><td>&nbsp;</tr></table> <!-- vertical spacer -->

    <table class="FootBar" width="100%" border="0" cellpadding="8" style="background: #EEEEEE;"><tr>
    <td>{{.FootBox}}
    </tr></table>
  {{end}}
''')


Demo = FancyBase.Clone().Parse('''
  {{define "Inner"}}
    <p>Begin Demo<p>{{.Content}}<p>End Demo<p>
    [Demo]
  {{end}}''')

View = FancyBase.Clone().Parse('''
  {{define "Inner"}}
    <div class="ViewInner">
      {{.Html | unrye}}
    </div>
  {{end}}''')

ViewMissing = FancyBase.Clone().Parse('''
  {{define "Inner"}}
    Page {{.Subject}} does not exist.<p>
    You may <a href="{{.Subject}}{{.Dots}}edit">create</a> it.
  {{end}}''')

List = FancyBase.Clone().Parse('''
  {{define "Inner"}}
    <ul>
      {{range .List | unrye}} <li> <a href="{{.}}">{{.}}</a>
      {{else}} <li> (Empty List.)
      {{end}}
    </ul>
  {{end}}''')

Edit = PlainBase.Clone().Parse('''
  {{define "Inner"}}
    <p>
    <!--== form ==-->
    <form method="POST" action="{{.Subject}}{{.Dots}}edit...">
    <b>Title:</b> <input name=title size=80 value="{{.Title}}">
    <p>
    <textarea name=text wrap=virtual rows=30 cols=80 style="width: 95%;"
    >{{.Text}}</textarea>
    <p>
    <input type=submit value=Save> &nbsp;
    <input type=reset>
    <tt>&nbsp; <big>[<a href={{.Title}}{{.Dots}}>Cancel</a>]</big></tt>
    </form>
  {{end}}''')

Attach = PlainBase.Clone().Parse('''
  {{define "Inner"}}
    <p>
    <!--== form ==-->
    <form method="POST" action="{{.Subject}}{{.Dots}}attach..." enctype="multipart/form-data">
    <p>
    Upload a new attachment:
    <input type="file" name="file">
    <p>
    <input type=submit value=Save> &nbsp;
    <input type=reset>
    <tt>&nbsp; <big>[<a href={{.Title}}{{.Dots}}>Cancel</a>]</big></tt>
    </form>
  {{end}}''')


# Light blue title (on golang.org): #E0EBF5
# Light gray #EEEEEE
# Light lavendar #FFE0FF;
