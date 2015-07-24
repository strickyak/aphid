# slash.tcl

proc Action/ {} {
  e "This is the Action/ function."
  e "\n<p> globals: [info globals]"
  e "\n<p> locals: [info locals]"
  e "\n<p> commands: [info commands]"
  e "\n<p> macros: [info macros]"

  set h,l [ReadWikiHeadersAndLines "/smilax/$Page/@wik"]
  set h [Reify $h]

  e "\n<p> headers: $h"
  e "\n<p> lines: $l"

  if {[info exists h(markup)] && $h(markup) == "md"} {
    e "\n<p>markdown: <hr> [TranslateMarkdown $md]"
  }
}
