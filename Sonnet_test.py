# $ LD_LIBRARY_PATH=/usr/local/lib/ rye run Sonnet_test.py 

from . import Sonnet
from lib import data

SNIPPET = '''
// Compiler template
local CCompiler = {
    cFlags: [],
    out: "a.out",
    local flags_str = std.join(" ", self.cFlags),
    local files_str = std.join(" ", self.files),
    cmd: "%s %s %s -o %s" % [self.compiler, flags_str, files_str, self.out],
};

// GCC specialization
local Gcc = CCompiler { compiler: "gcc" };

// Another specialization
local Clang = CCompiler { compiler: "clang" };

// Mixins - append flags
local Opt = { cFlags: super.cFlags + ["-O3", "-DNDEBUG"] };
local Dbg = { cFlags: super.cFlags + ["-g"] };

// Output:
{
    targets: [
        Gcc { files: ["a.c", "b.c"] },
        Clang { files: ["test.c"], out: "test" },
        Clang + Opt { files: ["test2.c"], out: "test2" },
        Gcc + Opt + Dbg { files: ["foo.c", "bar.c"], out: "baz" },
    ]
}
'''

EXPECT = {"targets": [{"files": ["a.c", "b.c"], "out": "a.out", "cFlags": [], "cmd": "gcc  a.c b.c -o a.out", "compiler": "gcc"}, {"cFlags": [], "cmd": "clang  test.c -o test", "compiler": "clang", "files": ["test.c"], "out": "test"}, {"out": "test2", "cFlags": ["-O3", "-DNDEBUG"], "cmd": "clang -O3 -DNDEBUG test2.c -o test2", "compiler": "clang", "files": ["test2.c"]}, {"cFlags": ["-O3", "-DNDEBUG", "-g"], "cmd": "gcc -O3 -DNDEBUG -g foo.c bar.c -o baz", "compiler": "gcc", "files": ["foo.c", "bar.c"], "out": "baz"}]}

s = Sonnet.RunFile('demo.jsonnet.conf')
p = data.Eval(s)
must EXPECT == p
print '---------------------------'
print s
print '---------------------------'
print p
print '---------------------------'
print 'OKAY Sonnet_test'
