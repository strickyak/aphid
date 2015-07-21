# slash.tcl

proc Action/ {} {
  e "This is the Action/ function."
  e "\n<p> globals: [info globals]"
  e "\n<p> locals: [info locals]"
  e "\n<p> commands: [info commands]"
  e "\n<p> macros: [info macros]"

  set h,l [ReadWikiHeadersAndLines "/smilax/$Page/@wik"]

  e "\n<p> headers: $h"
  e "\n<p> lines: $l"
}
