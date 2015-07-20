# slash.tcl

proc Action/ {} {
  e "This is the Action/ function."
  e "<p> globals: [info globals]"
  e "<p> locals: [info locals]"
  e "<p> commands: [info commands]"
  e "<p> macros: [info macros]"
}
