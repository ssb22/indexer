#!/bin/bash

# Shell script to add 'Copy' functionality to Offline HTML Indexer output
# assuming use of the standalone Android app viewer.
# Version 1.4, Silas S. Brown 2014-15, 2020-21, public domain, no warranty

# OHI output must be in the current directory when run.
# Also works with multiple OHI outputs in a non-merged
# collection (subdirectories with a master index.html)

# Where to find history:
# on GitHub at https://github.com/ssb22/indexer
# and on GitLab at https://gitlab.com/ssb22/indexer
# and on BitBucket https://bitbucket.org/ssb22/indexer
# and at https://gitlab.developers.cam.ac.uk/ssb22/indexer
# and in China: https://gitee.com/ssb22/indexer

if ! test -e index.html; then echo Wrong directory; exit 1; fi
for N in [0-9]*.html; do if test -e "$N"; then python2 -c 'import sys,re ; sys.stdout.write(re.sub(u"([\u4e00-\ua6ff]([\u3000-\uffe0]*[\u4e00-\ua6ff])*)","<button onClick=\"ca()\" style=\"background:#ededed;color:inherit\">Copy</button><span>\\1</span>",sys.stdin.read().decode("utf-8")).encode("utf-8"))' < "$N" | sed -e 's,/script>,/script><script>function ca(t) { clipboard.append((window.event.target||window.event.srcElement).nextSibling.innerHTML); location.href="index.html"}</script>,' > n && mv n "$N"; fi; done &&
for N in */[0-9]*.html; do if test -e "$N"; then python2 -c 'import sys,re ; sys.stdout.write(re.sub(u"([\u4e00-\ua6ff]([\u3000-\uffe0]*[\u4e00-\ua6ff])*)(?![^\"]*\">)","<button onClick=\"ca()\" style=\"background:#ededed;color:inherit\">Copy</button><span>\\1</span>",sys.stdin.read().decode("utf-8")).encode("utf-8"))' < "$N" | sed -e 's,/script>,/script><script>function ca(t) { clipboard.append((window.event.target||window.event.srcElement).nextSibling.innerHTML); location.href="../index.html"}</script>,' > n && mv n "$N"; fi; done &&
sed -e 's|<form|<script>var c=clipboard.get(); if(c.length) document.write(c+'"'"' <button onClick="clipboard.clear();location.reload()" style="background:#ededed;color:inherit">Clear</button>'"'"'); function viewZoomCtrls() { window.setTimeout(function(){ var t=document.getElementById("zI"); var r=t.getBoundingClientRect(); if (r.bottom > window.innerHeight) t.scrollIntoView(false); else if (r.top < 0) t.scrollIntoView()},200)} function zoomOut() { var l=zoom.getZoomLevel(); if (l > 0) { zoom.setZoomLevel(--l); document.getElementById("zL").innerHTML=""+zoom.getZoomPercent()+"%" } if (!l) document.getElementById("zO").disabled=true; else document.getElementById("zI").disabled=false; viewZoomCtrls()} function zoomIn() { var l=zoom.getZoomLevel(),m=zoom.getMaxZoomLevel(); if (l < m) { zoom.setZoomLevel(++l); document.getElementById("zL").innerHTML=""+zoom.getZoomPercent()+"%" } if (l==m) document.getElementById("zI").disabled=true; else document.getElementById("zO").disabled=false; viewZoomCtrls()} if(zoom.canCustomZoom()) document.write('"'"'<div style="float:right">Text size: <button id=zO onclick="zoomOut()" style="background:#ededed;color:inherit">-</button> <span id=zL>'"'"'+zoom.getZoomPercent()+'"'"'%</span> <button id=zI onclick="zoomIn()" style="background:#ededed;color:inherit">+</button></div>'"'"')</script><form|' < index.html > n && mv n index.html &&
for N in index.html */index.html; do if test -e "$N"; then sed -e 's,<input type="submit",<input style="background:#ededed;color:inherit" type="submit",g' < "$N" > n && mv n "$N"; fi; done
