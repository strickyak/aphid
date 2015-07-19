say TCL-Bund $Bund
foreach cname [rycall $ListFiles $Bund "/chunks"] {
  say TCL-cname $cname
  if {[string match *.tcl $cname]} {
    set x [rycall $ReadFile $Bund "/chunks/$cname"]
    say TCL-YES $cname [string length $x]
    #eval $x
  }
}

proc @HandleWikiUrl {} {
  global Path Query Form

}

proc @Out {args} {
  upvar 2 Buf buf
  set sep ""
  foreach a $args {
    $buf WriteString $sep
    $buf WriteString $a
    set sep " "
  }
}

set Zygote [interp]
$Zygote Alias <frame> Out @Out

$Zygote Eval {
  list
}

proc HandleWiki {clone} {
  if {[regexp {^/(@[-a-z0-9_]+)?/*([0-9]+)[.]?([-a-z0-9_]+)?[.]?([^ +/@]+)?[ +/@]?(.*)$} [cred path] - site page verb object filename]} {
    $clone Eval [list set Site $site]
    $clone Eval [list set Page $page]
    $clone Eval [list set Verb $verb]
    $clone Eval [list set Object $object]
    $clone Eval [list set Filename $filename]

    $clone Eval {
      Out Frodo One Two Three * $Site * $Page * $Verb * $Object * $Filename
    }
  } else {
    $clone Eval {
      Out NO MATCH -- [cred path]
    }
  }
}

proc Handle {} {
  set clone [$Zygote Clone]
  $clone CopyCredFrom -
  $clone Eval [list set Buf [/bytes/NewBufferString ""]]

  say w [cred w]
  say r [cred r]
  say path [cred path]
  foreach stuff [cred form] {
    say stuff $stuff
  }
  set e [catch { HandleWiki $clone } what]

  case $e in {
    0 {
          [[cred w] Header] Set Content-Type text/html
          say NANDO_Get [[[cred w] Header] Get Content-Type]
          [cred w] WriteString [[$clone Eval {set Buf}] String]
          say NANDO_9
          list OKAY-NANDO-000
    }
    307 {
                  set url [lindex [split $what "\n"] 0]
                  set rh [/net/http/RedirectHandler $url 307]
                  $rh ServeHTTP [cred w] [cred r]
    }
    default {
                  # TODO: something better.
                  [cred w] Write [[ht cat "***ERROR***  $e: $what  ***ERROR***"] Html]
    }
  }
}
