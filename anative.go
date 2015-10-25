package aphid

import (
	// External requirements.
	_ "github.com/BurntSushi/toml"
	_ "github.com/gdamore/mangos"
	_ "github.com/huandu/skiplist"
	_ "github.com/microcosm-cc/bluemonday"
	_ "github.com/russross/blackfriday"
	_ "golang.org/x/crypto/scrypt"
	_ "github.com/syndtr/goleveldb/leveldb"
)

import (
	// Yak requirements.
	_ "github.com/strickyak/redhed"
	_ "github.com/strickyak/rye"
	_ "github.com/yak-labs/chirp-lang"
	_ "github.com/yak-labs/chirp-lang/goapi/default"
	_ "github.com/yak-labs/chirp-lang/http"
	_ "github.com/yak-labs/chirp-lang/img"
	_ "github.com/yak-labs/chirp-lang/posix"
	_ "github.com/yak-labs/chirp-lang/rpc"
	_ "github.com/yak-labs/chirp-lang/ryba"
)

import (
	_ "io"
)
