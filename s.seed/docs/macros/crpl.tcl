proc kc {a args} {set a}  # K Combinator.

macro eq {a b} { string equal $a $b }
macro ne {a b} { string compare $a $b }
macro lt { a b } { expr { [ string compare $a $b ] < 0 } }
macro le { a b } { expr { [ string compare $a $b ] <= 0 } }
macro gt { a b } { expr { [ string compare $a $b ] > 0 } }
macro ge { a b } { expr { [ string compare $a $b ] >= 0 } }

macro eq- {a b} { string equal -nocase $a $b }
macro ne- {a b} { string compare -nocase $a $b }
macro lt- { a b } { expr { [ string compare -nocase $a $b ] < 0 } }
macro le- { a b } { expr { [ string compare -nocase $a $b ] <= 0 } }
macro gt- { a b } { expr { [ string compare -nocase $a $b ] > 0 } }
macro ge- { a b } { expr { [ string compare -nocase $a $b ] >= 0 } }

macro sm {a b} { string match $a $b }
macro sc {a b} { string compare $a $b }
macro sm- {a b} { string match -nocase $a $b }
macro sc- {a b} { string compare -nocase $a $b }

macro s2u {s} { string toupper $s }
macro s2l {s} { string tolower $s }
macro st {s} { string trim $s }
macro stl {s} { string trimleft $s }
macro str {s} { string trimright $s }

macro sl {s} { string length $s }
macro si {s a} { string index $s $a }
macro sr {s a b} { string range $s $a $b }
macro sa {var ARGS} { append $var {*}$ARGS }

macro l ARGS { list {*}$ARGS }
macro ll {x} { llength $x }
macro li {x a} { lindex $x $a }
macro lr {x a b} { lrange $x $a $b }
macro la {var ARGS} { lappend $var {*}$ARGS }

macro ie {var} { info exists $var }

macro 0 x {lindex $x 0}
macro 1 x {lindex $x 1}
macro 2 x {lindex $x 2}
macro 3 x {lindex $x 3}
macro 4 x {lindex $x 4}
macro 5 x {lindex $x 5}
macro 6 x {lindex $x 6}
macro 7 x {lindex $x 7}
macro 8 x {lindex $x 8}
macro 9 x {lindex $x 9}

macro 1- x {lrange $x 1 end}
macro 2- x {lrange $x 2 end}
macro 3- x {lrange $x 3 end}
macro 4- x {lrange $x 4 end}
macro 5- x {lrange $x 5 end}
macro 6- x {lrange $x 6 end}
macro 7- x {lrange $x 7 end}
macro 8- x {lrange $x 8 end}
macro 9- x {lrange $x 9 end}

macro -1 x {lindex $x end}
macro -2 x {lindex $x end-1}
macro -3 x {lindex $x end-2}
macro -4 x {lindex $x end-3}
macro -5 x {lindex $x end-4}
macro -6 x {lindex $x end-5}
macro -7 x {lindex $x end-6}
macro -8 x {lindex $x end-7}
macro -9 x {lindex $x end-8}
