from go import html/template
from go import github.com/strickyak/aphid

Main = template.New("atemplate.py")
aphid.AddAphidTemplateFunctions(Main)
Main.Parse('''
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
    <table class="HeadBar" width=100% border=0 cellpadding=8 style="background: #EEEEEE;"><tr>
    <td>{{.HeadBox}}
    </tr></table>
  {{end}}

  {{define "FootBar"}}
    <table border="0" cellpadding="50"><tr><td>&nbsp;</tr></table>

    <table class="FootBar" width="100%" border="0" cellpadding="8" style="background: #EEEEEE;"><tr>
    <td>{{.FootBox}}
    </tr></table>
  {{end}}

  {{define "Debug"}}
    <p>
    <b>Debug:</b>
    <ul class="Debug">
      {{range .Debug | Contents}} <li> {{.}}
      {{else}} <li> (No Debug Info.)
      {{end}}
    </ul>
    <p>
  {{end}}
''')

Demo = Main.Clone().Parse('''
  {{define "Inner"}}
    <p>Begin Demo<p>{{.Content}}<p>End Demo<p>
    [Demo]
  {{end}}''')

View = Main.Clone().Parse('''
  {{define "Inner"}}
    <p>Begin Content<p>{{.Content}}<p>End Content<p>
    [View]
  {{end}}''')

Edit = Main.Clone().Parse('''
  {{define "WikiEdit"}}
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
