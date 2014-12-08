package aphid

import "github.com/microcosm-cc/bluemonday"
import "github.com/russross/blackfriday"

var _ = bluemonday.UGCPolicy
var _ = blackfriday.MarkdownCommon
