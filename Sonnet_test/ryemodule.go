package Sonnet_test

import . "github.com/strickyak/rye"
import "fmt"
import "io"
import "os"
import "reflect"
import "runtime"
import i_Sonnet "github.com/strickyak/aphid/Sonnet"
import i_E "github.com/strickyak/aphid/eval"

var _ = fmt.Sprintf
var _ = io.EOF
var _ = os.Stderr
var _ = reflect.ValueOf
var _ = runtime.Stack
var _ = MkInt

var eval_module_once bool

func Eval_Module() P {
	if eval_module_once == false {
		_ = inner_eval_module()
		eval_module_once = true
	}
	return ModuleObj
}
func inner_eval_module() P {
	// @ 61 @ from
	G_Sonnet = i_Sonnet.Eval_Module()
	// $ 61 $ from
	// @ 82 @ from
	G_E = i_E.Eval_Module()
	// $ 82 $ from
	// @ 107 @ SNIPPET
	// @@@@@@ AssignAFromB: <class 'tr.Tvar'> <tr.Tvar object at 0x7f7380ca2490> None
	G_SNIPPET = litS_d2350d98c3ff5d7ed8f16203325887b2
	// $ 107 $ SNIPPET
	// @ 904 @ EXPECT
	// @@@@@@ AssignAFromB: <class 'tr.Tvar'> <tr.Tvar object at 0x7f7380ca27d0> None
	G_EXPECT = MkDictV(litS_aa6f6d62574dedec24672f4ae1c9ca26, MkListV(MkDictV(litS_45b963397aa40d4a0063e0d85e4fe7a1, MkListV(litS_8eb7504957a50f21c60999d5f146e8e0, litS_4e28e05897892c5707f8ae02929ef952), litS_c68271a63ddbc431c307beb7d2918275, litS_5dea70ffcfe47719904eb37cf7b21591, litS_9b2dd9e935f9eae70348f522c5746404, MkListV(), litS_dfff0a7fa1a55c8c1a4966c19f6da452, litS_b0198eba43c8450b61c03edeb54f8966, litS_87f75ce3f908a819a9a2c77ffeffcc38, litS_e0d511356bd44120af49cc96c9dcf3b3), MkDictV(litS_9b2dd9e935f9eae70348f522c5746404, MkListV(), litS_dfff0a7fa1a55c8c1a4966c19f6da452, litS_2bf4e4101aed1a07314cdd1d6ff0e686, litS_87f75ce3f908a819a9a2c77ffeffcc38, litS_2c5517db7bc397f9b14ae357a7ce54ff, litS_45b963397aa40d4a0063e0d85e4fe7a1, MkListV(litS_d02a618fa88f46a768e6df00dddaad2a), litS_c68271a63ddbc431c307beb7d2918275, litS_098f6bcd4621d373cade4e832627b4f6), MkDictV(litS_c68271a63ddbc431c307beb7d2918275, litS_ad0234829205b9033196ba818f7a872b, litS_9b2dd9e935f9eae70348f522c5746404, MkListV(litS_1ec1effec8bc51870b35e140487c521e, litS_adf9628c834f5142ac0e2092e3de2d00), litS_dfff0a7fa1a55c8c1a4966c19f6da452, litS_a1c41d8a3b48ad1942f959bc439327ec, litS_87f75ce3f908a819a9a2c77ffeffcc38, litS_2c5517db7bc397f9b14ae357a7ce54ff, litS_45b963397aa40d4a0063e0d85e4fe7a1, MkListV(litS_054a537f807fed494884560f8073369a)), MkDictV(litS_9b2dd9e935f9eae70348f522c5746404, MkListV(litS_1ec1effec8bc51870b35e140487c521e, litS_adf9628c834f5142ac0e2092e3de2d00, litS_ef07c065bf3b6a37452f81f6ce4e7ea2), litS_dfff0a7fa1a55c8c1a4966c19f6da452, litS_347a97e98b8d352581d53faaa3613e3f, litS_87f75ce3f908a819a9a2c77ffeffcc38, litS_e0d511356bd44120af49cc96c9dcf3b3, litS_45b963397aa40d4a0063e0d85e4fe7a1, MkListV(litS_6ae72bb15a7d1834b42ae042a58f7a4d, litS_5a5cac1bf9efb917f1c7bb386bc231c9), litS_c68271a63ddbc431c307beb7d2918275, litS_73feffa4b7f6bb68e44cf984c85f6e88)))
	// $ 904 $ EXPECT
	// @ 1429 @ s
	// @@@@@@ AssignAFromB: <class 'tr.Tvar'> <tr.Tvar object at 0x7f7382ab9a90> None
	// Sonnet <tr.Timport object at 0x7f7380c9ae50> ['github.com', 'strickyak', 'aphid', 'Sonnet'] RunFile
	G_s = call_1(i_Sonnet.G_RunFile, litS_fcfb2b1a47d228544d919b73fae71ad1)
	// $ 1429 $ s
	// @ 1469 @ p
	// @@@@@@ AssignAFromB: <class 'tr.Tvar'> <tr.Tvar object at 0x7f7382ab9c10> None
	// E <tr.Timport object at 0x7f7380ca2350> ['github.com', 'strickyak', 'aphid', 'eval'] Eval
	G_p = call_1(i_E.G_Eval, G_s)
	// $ 1469 $ p
	// @ 1483 @ must
	if true {
		left_11, right_12 := G_EXPECT, G_p
		if !(left_11.EQ(right_12)) {
			panic(fmt.Sprintf("Assertion Failed:  (%s) ;  left: (%s) ;  op: %s ;  right: (%s) ", "must EXPECT == p", left_11.Repr(), "EQ", right_12.Repr()))
		}
	}
	// $ 1483 $ must
	// @ 1500 @ print
	fmt.Fprintln(CurrentStdout(), litS_2acdcbbe90b5dff7aab49da61731c8ce.String())
	// $ 1500 $ print
	// @ 1536 @ print
	fmt.Fprintln(CurrentStdout(), G_s.String())
	// $ 1536 $ print
	// @ 1544 @ print
	fmt.Fprintln(CurrentStdout(), litS_2acdcbbe90b5dff7aab49da61731c8ce.String())
	// $ 1544 $ print
	// @ 1580 @ print
	fmt.Fprintln(CurrentStdout(), G_p.String())
	// $ 1580 $ print
	// @ 1588 @ print
	fmt.Fprintln(CurrentStdout(), litS_2acdcbbe90b5dff7aab49da61731c8ce.String())
	// $ 1588 $ print
	// @ 1624 @ print
	fmt.Fprintln(CurrentStdout(), litS_9082875fed0e298d02bc976b2f30da24.String())
	// $ 1624 $ print
	return None
}

//(begin tail)
///////////////////////////////

func G_1_main(a_argv P) P {

	return None
}

///////////////////////////////
// name: main
// args: ['argv']
// dflts: [None]
// star: None
// starstar: None
// body: <tr.Tsuite object at 0x7f7382ad0410>
type pFunc_main struct{ PCallSpec }

func (o *pFunc_main) Contents() interface{} {
	return G_main
}
func (o pFunc_main) Call1(a0 P) P {
	return G_1_main(a0)
}

func (o pFunc_main) CallV(a1 []P, a2 []P, kv1 []KV, kv2 map[string]P) P {
	argv, star, starstar := SpecCall(&o.PCallSpec, a1, a2, kv1, kv2)
	_, _, _ = argv, star, starstar
	return G_1_main(argv[0])
}

//(end tail)

var G_E P        // *PModule
var G_EXPECT P   // P
var G_SNIPPET P  // P
var G_Sonnet P   // *PModule
var G___name__ P // P
var G_main P     // *pFunc_main
var G_p P        // P
var G_s P        // P

func init /*New_Module*/ () {
	G_E = None
	G_EXPECT = None
	G_SNIPPET = None
	G_Sonnet = None
	G___name__ = MkStr("Sonnet_test")
	G___name__.SetSelf(G___name__)
	G_main = &pFunc_main{PCallSpec: PCallSpec{Name: "main", Args: []string{"argv"}, Defaults: []P{nil}, Star: "None", StarStar: "None"}}
	G_main.SetSelf(G_main)
	G_p = None
	G_s = None
}

var ModuleMap = map[string]*P{
	"E":        &G_E,
	"EXPECT":   &G_EXPECT,
	"SNIPPET":  &G_SNIPPET,
	"Sonnet":   &G_Sonnet,
	"__name__": &G___name__,
	"main":     &G_main,
	"p":        &G_p,
	"s":        &G_s,
}

var ModuleObj = MakeModuleObject(ModuleMap, "github.com/strickyak/aphid/Sonnet_test")

var litS_054a537f807fed494884560f8073369a = MkStr("test2.c")
var litS_098f6bcd4621d373cade4e832627b4f6 = MkStr("test")
var litS_1ec1effec8bc51870b35e140487c521e = MkStr("-O3")
var litS_2acdcbbe90b5dff7aab49da61731c8ce = MkStr("---------------------------")
var litS_2bf4e4101aed1a07314cdd1d6ff0e686 = MkStr("clang  test.c -o test")
var litS_2c5517db7bc397f9b14ae357a7ce54ff = MkStr("clang")
var litS_347a97e98b8d352581d53faaa3613e3f = MkStr("gcc -O3 -DNDEBUG -g foo.c bar.c -o baz")
var litS_45b963397aa40d4a0063e0d85e4fe7a1 = MkStr("files")
var litS_4e28e05897892c5707f8ae02929ef952 = MkStr("b.c")
var litS_5a5cac1bf9efb917f1c7bb386bc231c9 = MkStr("bar.c")
var litS_5dea70ffcfe47719904eb37cf7b21591 = MkStr("a.out")
var litS_6ae72bb15a7d1834b42ae042a58f7a4d = MkStr("foo.c")
var litS_73feffa4b7f6bb68e44cf984c85f6e88 = MkStr("baz")
var litS_87f75ce3f908a819a9a2c77ffeffcc38 = MkStr("compiler")
var litS_8eb7504957a50f21c60999d5f146e8e0 = MkStr("a.c")
var litS_9082875fed0e298d02bc976b2f30da24 = MkStr("OKAY Sonnet_test")
var litS_9b2dd9e935f9eae70348f522c5746404 = MkStr("cFlags")
var litS_a1c41d8a3b48ad1942f959bc439327ec = MkStr("clang -O3 -DNDEBUG test2.c -o test2")
var litS_aa6f6d62574dedec24672f4ae1c9ca26 = MkStr("targets")
var litS_ad0234829205b9033196ba818f7a872b = MkStr("test2")
var litS_adf9628c834f5142ac0e2092e3de2d00 = MkStr("-DNDEBUG")
var litS_b0198eba43c8450b61c03edeb54f8966 = MkStr("gcc  a.c b.c -o a.out")
var litS_c68271a63ddbc431c307beb7d2918275 = MkStr("out")
var litS_d02a618fa88f46a768e6df00dddaad2a = MkStr("test.c")
var litS_d2350d98c3ff5d7ed8f16203325887b2 = MkStr("\x0a// Compiler template\x0alocal CCompiler = {\x0a    cFlags: [],\x0a    out: \x22a.out\x22,\x0a    local flags_str = std.join(\x22 \x22, self.cFlags),\x0a    local files_str = std.join(\x22 \x22, self.files),\x0a    cmd: \x22%s %s %s -o %s\x22 % [self.compiler, flags_str, files_str, self.out],\x0a};\x0a\x0a// GCC specialization\x0alocal Gcc = CCompiler { compiler: \x22gcc\x22 };\x0a\x0a// Another specialization\x0alocal Clang = CCompiler { compiler: \x22clang\x22 };\x0a\x0a// Mixins - append flags\x0alocal Opt = { cFlags: super.cFlags + [\x22-O3\x22, \x22-DNDEBUG\x22] };\x0alocal Dbg = { cFlags: super.cFlags + [\x22-g\x22] };\x0a\x0a// Output:\x0a{\x0a    targets: [\x0a        Gcc { files: [\x22a.c\x22, \x22b.c\x22] },\x0a        Clang { files: [\x22test.c\x22], out: \x22test\x22 },\x0a        Clang + Opt { files: [\x22test2.c\x22], out: \x22test2\x22 },\x0a        Gcc + Opt + Dbg { files: [\x22foo.c\x22, \x22bar.c\x22], out: \x22baz\x22 },\x0a    ]\x0a}\x0a")
var litS_dfff0a7fa1a55c8c1a4966c19f6da452 = MkStr("cmd")
var litS_e0d511356bd44120af49cc96c9dcf3b3 = MkStr("gcc")
var litS_ef07c065bf3b6a37452f81f6ce4e7ea2 = MkStr("-g")
var litS_fcfb2b1a47d228544d919b73fae71ad1 = MkStr("demo.jsonnet.conf")

type i_0 interface {
	Call0() P
}

func call_0(fn P) P {
	switch f := fn.(type) {
	case i_0:
		return f.Call0()
	case ICallV:
		return f.CallV([]P{}, nil, nil, nil)
	}
	panic(fmt.Sprintf("No way to call: %v", fn))
}

type i_1 interface {
	Call1(P) P
}

func call_1(fn P, a_0 P) P {
	switch f := fn.(type) {
	case i_1:
		return f.Call1(a_0)
	case ICallV:
		return f.CallV([]P{a_0}, nil, nil, nil)
	}
	panic(fmt.Sprintf("No way to call: %v", fn))
}
