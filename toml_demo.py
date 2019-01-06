from go import bytes
from go import "github.com/BurntSushi/toml"
import util

T = `
baseurl = "http://127.0.0.1:3333/"
languageCode = "en-us"
title = "Demo Web Site"
[[menu.main]]
    name = "Home"
    weight = -999
    identifier = "home"
    url = "/"

[[menu.main]]
    name = "News"
    weight = 0
    identifier = "post"
    url = "/post/"

[[menu.main]]
    name = "Tags"
    weight = 9999
    identifier = "tags"
    url = "/tags/"
`

m = util.NativeMap(dict())
say m
say toml.Decode(T, m)
print '==================='
say m
print '==================='

b = go_new(bytes.Buffer)
toml.NewEncoder(b).Encode(m)
say str(b)
print '==================='
print b
print '==================='
print 'OKAY toml_demo'
