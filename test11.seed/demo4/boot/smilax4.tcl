proc @Out {args} {
  upvar 1 Buf buf
  set sep ""
  foreach a args {
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

proc Handle {} {
  set clone [$Zygote Clone]
  $clone CopyCredFrom -

  $clone Eval [list set Buf [/bytes/NewBufferString ""]]

  $clone Eval {
    say [cred w]
    say [cred r]
    set ww [/bytes/NewBufferString "Bilbo"]
    Out Frodo

    set e [catch {
            Out Zaldo
    } what]

    case $e in {
      0 {
          [[cred w] Header] Set Content-Type text/html
          say NANDO_Get [[[cred w] Header] Get Content-Type]
          say NANDO_4pre $ww
          say NANDO_4 [$ww String]
          [cred w] Write [$ww String]
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
                  [cred w] Write [[ht cat "{}{}{}" $what "{}{}{}"] Html]
      }
    }
  }
}
