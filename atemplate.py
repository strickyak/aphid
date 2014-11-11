from go import html/template

T = template.New("atemplate.py")

T.Parse('''
  <html><head>
    <title>{{.Title}}</title>
  </head><body>
    <div class="HeadBar">{{template "HeadBar" .}}</div>
    <h1 style="background: #E0EBF5;">{{.Title}}</h1>
    {{.Content}}
    <div class="FootBar">{{template "FootBar" .}}</div>
  </body></html>
''')

T.Parse('''{{define "HeadBar"}}
  <table width=100% border=1 cellpadding=8><tr>
  <td>{{.HeadBox}}
  </tr></table>
{{end}}''')

T.Parse('''{{define "FootBar"}}
  <table width=100% border=0 cellpadding=8 style="background: #E0EB55;"><tr>
  <td>{{.FootBox}}
  </tr></table>
{{end}}''')

T.Parse('''{{define "WikiView"}}
{{end}}''')

T.Parse('''{{define "Nothing"}}
{{end}}''')
