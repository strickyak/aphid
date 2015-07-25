# smilax4.tcl
proc @HandleWikiUrl {} {
  global Path Query Form

}

proc @e {args} {
  upvar 2 Buf buf
  set sep ""
  foreach a $args {
    $buf WriteString $sep
    $buf WriteString $a
    set sep " "
  }
}
proc @ListFiles {args} { ListFiles $Bund {*}$args }
proc @ReadFile {args} { ReadFile $Bund {*}$args }
proc @ReadWikiHeadersAndLines {filename} { ReadWikiHeadersAndLines $Bund $filename }
proc @Reify x { $x reify }

set Zygote [interp]
$Zygote Alias <frame> e @e
$Zygote Alias <frame> ListFiles @ListFiles
$Zygote Alias <frame> ReadFile @ReadFile
$Zygote Alias <frame> ReadWikiHeadersAndLines @ReadWikiHeadersAndLines
$Zygote Alias <frame> TranslateMarkdown TranslateMarkdown
$Zygote Alias <frame> Reify @Reify

$Zygote Eval {
  proc uproc {name varz body} {
    proc $name $varz $body
  }
}

proc EvalMixinsInZygote {} {
  foreach fname [@ListFiles "/mixins"] {
    if {[string match *.tcl $fname]} {
      set mname [lindex [split $fname "."] end]
      set x [@ReadFile "/mixins/$fname"]
      $Zygote Eval "mixin $mname { $x }"
    }
  }
}
EvalMixinsInZygote

proc HandleWiki {clone} {
  if {[regexp {^/(@[-a-z0-9_]+)?/*([0-9]+)[.]?([-a-z0-9_]+)?[.]?([^ +/@]+)?[ +/@]?(.*)$} [cred path] - site page verb object filename]} {
    $clone Eval [say set Site $site]
    $clone Eval [say set Page $page]
    $clone Eval [say set Verb $verb]
    $clone Eval [say set Object $object]
    $clone Eval [say set Filename $filename]

    $clone Eval {
      e Frodo One Two Three * $Site * $Page * $Verb * $Object * $Filename
      e <p>
      Action/$Verb
    }
  } else {
    $clone Eval {
      e NO MATCH -- [cred path]
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
      [cred w] Write "\n\n\n***ERROR***  $e: $what  ***ERROR***"
    }
  }
}
