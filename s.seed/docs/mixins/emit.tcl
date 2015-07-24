uproc ILink { {pg {}} {vrb {}} {fil {}} args } {
	if { $pg=="" } {
		set z $Page
	} else {
		set z $pg
	}
	if { $fil=="-" } {
		# dont add any query stuff
		if { $vrb=="" } {
			return $z
		} else {
			return $z.$vrb
		}
	} elseif { $fil!="" } {
		error unsupported
	}
	if { $vrb=="" } {
		append z "[eval xuser $args]"
	} else {
		append z ".$vrb[eval xuser $args]"
	}
	set z
}

uproc EmitTop { {title -} } {
	EmitHtmlStart $title
	FLUSH
	if {![info exists Nobar]} {
		EmitTopPre $title
	FLUSH
		EmitTopBar $title
	FLUSH
		EmitTopMid $title
	FLUSH
	}
	EmitTopTitle $title
	FLUSH
	if {![info exists Nobar]} {
		EmitTopPost $title
	FLUSH
	}
}


uproc EmitDocType {} { out {<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">} }
uproc EmitRootTagBegin {} { out {<html>} }
uproc EmitRootTagEnd {} { out {</html>} }

uproc EmitHeadTag {title} { 
	out {<head>}

# strick 2011-10-30: This made the problem worse; Autodetect would no longer correct it.
#  out {
#    <meta charset="UTF-8" />
#    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
#  }

	out [RenderHeadTitleTag $title]
	out [RenderHeadMetaTags]
	out [RenderHeadStyleSheetLink]
	out {</head>}
}

uproc RenderHeadStyleSheetLink {} {}
uproc RenderHeadTitleTag {title} {
	set ptitle [ttl.p $Page]
	return "<title>[Ampize [expr {$title=="-"? $ptitle: $title}]]</title>"
}
uproc RenderHeadMetaTags {} {
	switch -glob -- $Verb {
		calendar* - folderindex* -
		error* - change* - history* - delta* - map* - search* - *new* -
		*create* - edit* - *attach* - *upload* - old {
			return {	<meta name="ROBOTS" content="NOINDEX, NOFOLLOW" />}
		}
	}
	return {}
}
uproc EmitBodyTagBegin {} { out {<body>} }
uproc EmitBodyTagEnd {} { out {</body>} }

uproc EmitHtmlStart {title} {
	global page verb query
	# detect Discussion messages by Title format
	set ptitle [ttl.p $Page]
	if {[regexp {^Discussion #([0-9]+) Message:} $ptitle 0 discussion]} { set query(discussion) $discussion }
	if {[regexp {^WebLog #([0-9]+) Topic:} $ptitle 0 weblog]} { 
		set query(weblog) $weblog 
		set title [disuglify-title $ptitle]
	}

	EmitDocType
	EmitRootTagBegin
	EmitHeadTag $title

	out "<body [NormalColorAttrs] >"
}

uproc EmitTopPre {title} {

#out {<small>Warning: We are being slashdotted by <a href=http://boingboing.net>boingboing</a>, so this server may be sluggish for a day or so.  Actually -- we're disabling attachments over 1MB for now; huge file downloads were clogging the server slots. </small><br>}

	if [info exists MixinErrors] {
		out {Warning: Server Errors <ul>}
		foreach {k v} [array get MixinErrors] {
			out "<li>[AmpizeRaw [string range "mixin $k: $v" 0 500]]</li>"
		}
		out {</ul>}
		FLUSH
	}
}
uproc EmitTopPost {title} {}
uproc EmitTopMid {title} {
	global page verb query

	if [info exists Nav] {
		if [info exists Archival] { set suffix .html 
		} else { set suffix "" }
		out {<div align="center"><tt>}
		foreach p $Nav {
			set tit [Ampize [disuglify-title [ttl.p $p]]]
			if { $Page == $p } { out "*$tit* "
			} else { out "\[<a href=\"$p$suffix\">$tit</a>] " }
		}
		out {</tt></div>}
	}

	if { $page != 0 && ( $verb=="" || $verb=="html" ) } expand-header 
}

uproc EmitMoreTopBarButtonsAfterIndex {} {
}

uproc EmitTopBar {title} {
	global page verb query
	if {[info exists Archival]} {
		set stuff .html
	} else {
		set stuff ""
	}

	set ptitle [ttl.p $Page]

		set volPage [v.p $page]
		set volName [Ampize [vn.v $volPage]]

		EmitDarkBoxBegin 
		out <tr>
		out {<td nowrap align="left" valign="top"><tt><small>}


		if {$title=="-"} {out "[clickable-title $ptitle]"}
		out {</small></tt></td> }

		out {<td align="right"><tt>}

		if {! [info exists Archival]} {
		  if { $verb == "changes" } { EmitHtmlNoNewline "*Changes*&nbsp;&nbsp;&nbsp;"
		  } else { EmitHtmlNoNewline "\[<a href=\"$page.changes[auser]\" title=\"List all accessible wiki pages from most to least recently modified.\">Changes</a>]&nbsp;&nbsp;&nbsp;" }

		  if { $verb == "calendar" } { EmitHtmlNoNewline "*Calendar*&nbsp;&nbsp;&nbsp;"
		  } else { EmitHtmlNoNewline "\[<a href=\"$page.calendar[auser]\" title=\"Calendar of events\">Calendar</a>]&nbsp;&nbsp;&nbsp;" }

		  if { $verb == "search" } { EmitHtmlNoNewline "*Search*&nbsp;&nbsp;&nbsp;"
		  } else { EmitHtmlNoNewline "\[<a href=\"$page.search[auser]\" title=\"Search all accessible pages in this wiki.\">Search</a>]&nbsp;&nbsp;&nbsp;" }

		  if { $verb == "index" } { EmitHtmlNoNewline "*Index*&nbsp;&nbsp;&nbsp;"
		  } else { EmitHtmlNoNewline "\[<a href=\"$page.index[auser]\" title=\"List all accessible pages in this wiki.\">Index</a>]&nbsp;&nbsp;&nbsp;" }

		  EmitMoreTopBarButtonsAfterIndex

		  set allvols10 [AllVolumesAtLevel 10]
		  if { [llength $allvols10] > 1 } {
			out {</tt></td></tr><tr><td colspan="2" align="right"><tt><small><br>}
			foreach x $allvols10 {
				lappend avt [list [vn.v $x] $x]
			}

			foreach pair [lsort $avt] {

				set x [lindex $pair 1]
				set ax [Ampize [lindex $pair 0]]
				if { $Volume == $x } { out "*${ax}* "
				#} elseif { $Volume == $x } { out "*\[<a href=\"$x\">${ax}::</a>\]* " 
				} else { out "\[<a href=\"$x\" title=\"Home page of the ${ax} wiki volume\">${ax}</a>\] " }
			}
			out {</small> &nbsp; }
		  }
		} else {

		  if { $verb == "index" } { out {*Index* &nbsp; }
		  } else { out "\[<a href=\"$Volume.flatindex.html\">Index</a>] &nbsp; " }
		}

		out { </tt></td>}
		out </tr>

		# special "back" buttons
		if {
			[regexp -nocase {^Calendar: ([0-9][0-9][0-9][0-9])-([0-9][0-9])} $ptitle - yyyy mm ] ||
			[info exists query(weblog)] ||
			[info exists query(discussion)] ||
			[string length [Mget topbuttons]]
		} {
			out {<tr><td>&nbsp;</td><td align="center"><tt>}

			if {[regexp -nocase {^Calendar: ([0-9][0-9][0-9][0-9])-([0-9][0-9])} $ptitle - yyyy mm ]} {
				out "<b>\[<a href=\"$page.calendar?around=$yyyy-$mm\">Back to Calendar</a>]</b> &nbsp; "
			}

			if {[info exists query(weblog)]} { 
				out "<b>\[<a href=\"$query(weblog)$stuff\">Back to weblog: [Ampize [ttl.p $query(weblog)]]</a>]</b> &nbsp; "
			}
			if {[info exists query(discussion)]} { 
				out "<b>\[<a href=\"$query(discussion)$stuff\">Back to discussion: [\
					Ampize [disuglify-title [ttl.p $query(discussion)]]]</a>]</b> &nbsp; "
			}

			foreach {label link} [Mget topbuttons] {
				out "\[<a href=\"$link\">[Ampize $label]</a>] &nbsp; "
			}

			out {</tt></td></tr>}
		}

	 EmitDarkBoxEnd 
}

uproc EmitLimitedTopBar { title {displayChangesButton 1} {displayCalendarButton 1} {displaySearchButton 1} {displayIndexButton 1} } {
	global page verb query
	if {[info exists Archival]} {
		set stuff .html
	} else {
		set stuff ""
	}

	set ptitle [ttl.p $Page]

		set volPage [v.p $page]
		set volName [Ampize [vn.v $volPage]]

		EmitDarkBoxBegin 
		out <tr>
		out {<td nowrap align="left" valign="top"><tt><small>}

		if { $page == $volPage && $verb == "" } { out "$volName\::" 
		} else { out "<a href=\"$volPage$stuff[auser]\" title=\"Home page of the $volName wiki volume\">$volName</a>\:: " }

		if {$title=="-"} {out "[clickable-title $ptitle]"}
		out {</small></tt></td> }

		out {<td align="right"><tt>}

		if {! [info exists Archival]} {
		  if { $displayChangesButton } {
		  	if { $verb == "changes" } { EmitHtmlNoNewline "*Changes*&nbsp;&nbsp;&nbsp;"
			  } else { EmitHtmlNoNewline "\[<a href=\"$page.changes[auser]\" title=\"List all accessible wiki pages from most to least recently modified.\">Changes</a>]&nbsp;&nbsp;&nbsp;" }
		  }

		  if { $displayCalendarButton } {
		    if { $verb == "calendar" } { EmitHtmlNoNewline "*Calendar*&nbsp;&nbsp;&nbsp;"
		    } else { EmitHtmlNoNewline "\[<a href=\"$page.calendar[auser]\" title=\"Calendar of events\">Calendar</a>]&nbsp;&nbsp;&nbsp;" }
		  }

		  if { $displaySearchButton } {
		    if { $verb == "search" } { EmitHtmlNoNewline "*Search*&nbsp;&nbsp;&nbsp;"
		    } else { EmitHtmlNoNewline "\[<a href=\"$page.search[auser]\" title=\"Search all accessible pages in this wiki.\">Search</a>]&nbsp;&nbsp;&nbsp;" }
		  }

		  if { $displayIndexButton } {
		    if { $verb == "index" } { EmitHtmlNoNewline "*Index*&nbsp;&nbsp;&nbsp;"
		    } else { EmitHtmlNoNewline "\[<a href=\"$page.index[auser]\" title=\"List all accessible pages in this wiki.\">Index</a>]&nbsp;&nbsp;&nbsp;" }
		  }

		  EmitMoreTopBarButtonsAfterIndex

		  set allvols10 [AllVolumesAtLevel 10]
		  if { [llength $allvols10] > 1 } {
			out {</tt></td></tr><tr><td colspan="2" align="right"><tt><small><br>}
			foreach x $allvols10 {
				lappend avt [list [vn.v $x] $x]
			}

			foreach pair [lsort $avt] {

				set x [lindex $pair 1]
				set ax [Ampize [lindex $pair 0]]
				if { $Volume == $x } { out "*${ax}* "
				#} elseif { $Volume == $x } { out "*\[<a href=\"$x\">${ax}::</a>\]* " 
				} else { out "\[<a href=\"$x\" title=\"Home page of the ${ax} wiki volume\">${ax}</a>\] " }
			}
			out {</small> &nbsp; }
		  }
		} else {

		  if { $verb == "index" } { out {*Index* &nbsp; }
		  } else { out "\[<a href=\"$Volume.flatindex.html\">Index</a>] &nbsp; " }
		}

		out { </tt></td>}
		out </tr>

		# special "back" buttons
		if {
			[regexp -nocase {^Calendar: ([0-9][0-9][0-9][0-9])-([0-9][0-9])} $ptitle - yyyy mm ] ||
			[info exists query(weblog)] ||
			[info exists query(discussion)] ||
			[string length [Mget topbuttons]]
		} {
			out {<tr><td>&nbsp;</td><td align="center"><tt>}

			if {[regexp -nocase {^Calendar: ([0-9][0-9][0-9][0-9])-([0-9][0-9])} $ptitle - yyyy mm ]} {
				out "<b>\[<a href=\"$page.calendar?around=$yyyy-$mm\">Back to Calendar</a>]</b> &nbsp; "
			}

			if {[info exists query(weblog)]} { 
				out "<b>\[<a href=\"$query(weblog)$stuff\">Back to weblog: [Ampize [ttl.p $query(weblog)]]</a>]</b> &nbsp; "
			}
			if {[info exists query(discussion)]} { 
				out "<b>\[<a href=\"$query(discussion)$stuff\">Back to discussion: [\
					Ampize [disuglify-title [ttl.p $query(discussion)]]]</a>]</b> &nbsp; "
			}

			foreach {label link} [Mget topbuttons] {
				out "\[<a href=\"$link\">[Ampize $label]</a>] &nbsp; "
			}

			out {</tt></td></tr>}
		}

	 EmitDarkBoxEnd 
}

uproc EmitTopTitle {title} {
	global page verb query
	if {[info exists Archival]} {
		set stuff .html
	} else {
		set stuff ""
	}

	set ptitle [ttl.p $Page]

	# detect Discussion messages by Title format
	if {[regexp {^Discussion #([0-9]+) Message:} $ptitle 0 discussion]} { set query(discussion) $discussion }
	if {[regexp {^WebLog #([0-9]+) Topic:} $ptitle 0 weblog]} { 
		set query(weblog) $weblog 
		set title [disuglify-title $ptitle]
	}



	if { $title == "-" } {
		out "<h2>[Ampize [ttl.p $Page]]</h2>"
	} else {
		out "<h2>[Ampize $title]</h2>"
	}
	FLUSH
}

proc clickable-title title {

	set aa [split $title :]
	set len [llength $aa]
	set z ""
	set grow ""
	for {set i 0} {$i < $len} {incr i} {
		set a [string trim [lindex $aa $i]]
		if { $i>0 } { append grow ": " }
		append grow $a
		if { $i+1 == $len } {
			#if [llength [WikiLinkBack $Page]] {
				#append z "<a href=\"$Page.linkedfrom\">[Ampize $a]</a>"
			#} else {
				append z "[Ampize $a]"
			#}
		} else {
			set pg [lindex [pages-of-title $grow] 0]
			if { $pg == "" } {
				append z "[Ampize $a] "
				append z "<a href=\"$Page.folderindex[xuser folder $grow]\" title=\"List pages in the wiki folder named just before the colon.\">:</a> "
			} else {
				set u "$pg"
				set t "[Ampize $a]"
				append z "<a href=\"$u[auser]\" title=\"Go to the named page.\">$t</a> "
				append z "<a href=\"$Page.folderindex[xuser folder $grow]\" title=\"List pages in the wiki folder named just before the colon.\">:</a> "
			}
		}
	}
	set kids [WikiTitleBackKeys [string tolower "$title:*"]]
	if [llength $kids] {
		append z " <a href=\"$Page.folderindex[xuser folder $grow]\" title=\"List pages in the wiki folder named just before the colon.\">:</a> "
	}
	set z
}

proc expand-header {} {
		set title [ttl.p $Page]
		set lower [string tolower [CanonicalTitle $title]]

		set hlist {}

		while {[regexp {^(.*)[:](.*)$} $lower - front back]} {
			set h [ pages-of-title "$front: header"]
			## bad.1 HACK
			set h [lindex $h end]
			set h [lindex $h end]
			set h [lindex $h end]
			if { $h!="" } { set hlist [ concat [list $h] $hlist]   ;# push on front }
			set lower $front
		}
		set h [ pages-of-title "header"]
			set h [lindex $h end]
			set h [lindex $h end]
			set h [lindex $h end]
		if { $h!="" } { set hlist [ concat [list $h] $hlist]   ;# push on front }

incr Headfoot
		 foreach h $hlist {
		   eval {
			if [string length $h] {
				set f [OpenFile [dir-of-page $h] $h.wik]
				ReadInfos $f

				set old $Page
				markup $f
				set $Page old
				CloseFile $f
			}
		   }
		}
incr Headfoot -1
	
}

proc expand-footer {} {
FLUSH
		set title [ttl.p $Page]
		set lower [string tolower [CanonicalTitle $title]]

		set hlist {}

		while {[regexp {^(.*)[:](.*)$} $lower - front back]} {
			set h [pages-of-title "$front: footer"]
			## bad.1 HACK
			set h [lindex $h end]
			set h [lindex $h end]
			set h [lindex $h end]
			if { $h!="" } { lappend hlist $h }
			set lower $front
		}
		set h [pages-of-title "footer"]
			set h [lindex $h end]
			set h [lindex $h end]
			set h [lindex $h end]
		if { $h!="" } { lappend hlist $h }

incr Headfoot
		foreach h $hlist {
		   eval {
			if [string length $h] {
				set f [OpenFile [dir-of-page $h] $h.wik]
				ReadInfos $f

				set old $Page
				markup $f
				set $Page old
				CloseFile $f
			}
		   }
		}
incr Headfoot -1
	
}

proc show-notes {} {
	if {[llength $Note]} {
		out {<dt><small>Notes</small></dt>}
		set i 0
		foreach n $Note {
			incr i
			out "<dd><small><a name=\"note_$i\"><tt><b>Note $i:</b> [AmpizeRaw $n]</tt></a></small></dd>"
		}
	}
}

proc show-backlinks-list {} {
	set bb [WikiLinkBack $Page]
	if [llength $bb] {
		out {<dt><small> This page is referenced by the following pages: </small></dt>}
		set z {}
		foreach b $bb {
			set p [p.path $b]
			set t [ttl.p $p]
			if {[regexp -nocase {^trash:} $t]} continue
			lappend z [list $p $t]
		}
		foreach pair [lsort -index 1 -dictionary $z] {
			set p [lindex $pair 0]
			set t [lindex $pair 1]
			out "<dd><small><a href=\"$p\">[Ampize $t]</a></small></dd>"
		}
	} else {
		out {<dt><small>(No back references.)</small></dt><dd></dd>}
	}
}

uproc AddBottomBarButton {url name {level 50}} {
	if { [auth.p $Page] >= $level } {
		lappend Bottom_button $url $name
	}
}

uproc EmitBottom {} {
	EmitBottomPre
	FLUSH
	if ![info exists Nobar] {
		EmitBottomBar
	FLUSH
		EmitBottomMid
	FLUSH
		EmitBottomNotes
	FLUSH
		EmitBottomPost
	FLUSH
	}
	EmitHtmlFinish
	FLUSH
}

uproc EmitBottomMid {} {}
uproc EmitBottomPre {} {
	global page verb query

	if { $page != 0 && ( $verb=="" || $verb=="html" ) } expand-footer
}

uproc EmitBottomBar {} {
	global page verb query

	EmitDarkBoxBegin 

	out {<tr><td align="right"> <tt>}

	if {$USER=="?"} {
	    foreach {url name} $Bottom_button {
		out "\[<a href=\"$url\">[Ampize $name]</a>] &nbsp;"
	    }

		if { $page != 0 } { 
		    catch {
				set mtime [FileMtime [dir-of-page $page] $page.wik]
				set day [clock format $mtime -format "%Y-%m-%d" ]
				out "(last modified $day) &nbsp; &nbsp; &nbsp; "
		    }
		}
		if { $page==0 } {
			set goto 1
		} else {
			set goto $page
		}
		out "\[<a href=\"$goto.login[auser]\" title=\"Authorized users may login to the wiki in order to Create and Edit pages, and upload files to pages.\">Login</a>]"

	} else {

	    foreach {url name} $Bottom_button {
		out "\[<a href=\"$url\">[Ampize $name]</a>] &nbsp;"
	    }

	    if { [info exists HideAdmin] && ![info exists query(admin)] } {
			# It is confusing to have [Edit] [Attach] on a /discussion or /weblog page
			#   so we just put Curator instead.
			out "\[<a href=\"$page[xuser admin 1]\">Curator</a>]"

	    } elseif { $verb=="" || $verb=="attach" || $verb=="history" } {

			catch {
				set mtime [FileMtime [dir-of-page $page] $page.wik]
				set day [clock format $mtime -format "%Y-%m-%d" ]
				#set time [clock format $mtime -format "%H:%M" ]
				out "(modified $day) &nbsp;"
			}

			if { $verb == "" } { out {*View* &nbsp; }
			} else { out "\[<a href=\"$page[auser]\">View</a>] &nbsp; " }

			if { $verb == "edit" } { out {*Edit* &nbsp; }
			} else { out "\[<a href=\"$page.edit[auser]\" title=\"Edit the contents of this page.\">Edit</a>] &nbsp; " }

			if { $verb == "attach" } { out {*Attach* &nbsp; }
			} else { out "\[<a href=\"$page.attach[auser]\" title=\"Upload files from your computer which you want associated with this wiki page.\">Attach</a>] &nbsp; " }

			if { $verb == "history" } { out {*History* &nbsp; }
			} else { out "\[<a href=\"$page.history[auser]\" title=\"List revisions of this page.\">History</a>] &nbsp; " }
		}

		if [string match new* $verb] {
			out { &nbsp; }
		} else {
			out "\[<a href=\"$Page.new[auser]\" title=\"Create a new wiki page and edit it.\">Create&nbsp;Page</a>] &nbsp; "
		}
	}
	out {</tt></td></tr>}
	EmitDarkBoxEnd
}

uproc EmitBottomNotes {} {
	global page verb query

	NoteIfAdmin " vols >= 10 : [AllVolumesAtLevel 10]"
	NoteIfAdmin " vols >= 50 : [AllVolumesAtLevel 50]"

	out {<dl>}
	show-notes
	out {</dl>}
}

uproc EmitBottomPost {} {
	global page verb query
	if {$verb==""} {
		out {<dl>}
		show-backlinks-list
		out {</dl>}
	}
}
	
uproc EmitHtmlFinish {} {
	EmitBodyTagEnd
	EmitRootTagEnd
	FLUSH
	return
}


