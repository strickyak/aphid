package main
import "os"
import "github.com/strickyak/rye"
import MY "github.com/strickyak/aphid/Sonnet_test"

    var _ = os.Args
    func main() {
  

      defer rye.Flushem()
      MY.G___name__ = rye.MkStr("__main__")
      MY.Eval_Module()
  
      MY.G_1_main(rye.MkStrs(os.Args[1:]))
}
