from go import html/template

PlainBase = template.New("atemplate.py")

def AddContentsFunction(t):
  "Install a template function 'UnRye' that gets the contents from a PGo."
  "Usage: {{range .Debug | UnRye}} <li> {{.}}"
  native:
    # Get the template from the argument.
    't := a_t.Contents().(*i_template.Template)'
    # We will install a FuncMap.
    'fmap := make(i_template.FuncMap)'
    # The FuncMap has one function, UnRye, that gets a P's contents.
    'fmap["UnRye"] = func (p P) interface{} {'
    '  return p.Contents()'
    '}'
    # Set the FuncMap.
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
      {{range .Debug | UnRye}} <li> {{.}}
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
    {{.Html | html}}
    { {.Html | UnRye} }
  {{end}}''')

ViewMissing = FancyBase.Clone().Parse('''
  {{define "Inner"}}
    Page {{.Subject}} does not exist.<p>
    You may <a href="{{.Subject}}{{.Dots}}edit">create</a> it.
  {{end}}''')

List = FancyBase.Clone().Parse('''
  {{define "Inner"}}
    <ul>
      {{range .List | UnRye}} <li> <a href="{{.}}">{{.}}</a>
      {{else}} <li> (Empty List.)
      {{end}}
    </ul>
  {{end}}''')

Edit = PlainBase.Clone().Parse('''
  {{define "Inner"}}
    <p>
    <!--== form ==-->
    <form method="POST" action="{{.Page}}.save...">
    <b>Title:</b> <input name=title size=80 value="{{.Title}}">
    <p>
    <textarea name=text wrap=virtual rows=30 cols=80 style="width: 95%;"
    >${{.Text}}</textarea>
    <p>
    <input type=submit value=Save> &nbsp;
    <input type=reset>
    <tt>&nbsp; <big>[<a href={{.Title}}{{.Dots}}>Cancel</a>]</big></tt>
    </form>
    <!--== form ==-->
    <p>
  {{end}}''')

# Light blue title (on golang.org): #E0EBF5
# Light gray #EEEEEE
# Light lavendar #FFE0FF;
