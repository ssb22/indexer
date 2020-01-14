#!/bin/bash

# Shell script to add 'Copy' functionality to Offline HTML Indexer output
# assuming use of the standalone Android app viewer.
# Version 1.3, Silas S. Brown 2014-15, public domain, no warranty

# OHI output must be in the current directory when run.
# Also works with multiple OHI outputs in a non-merged
# collection (subdirectories with a master index.html)

if ! test -e index.html; then echo Wrong directory; exit 1; fi
for N in [0-9]*.html; do if test -e "$N"; then python2 -c 'import sys,re ; sys.stdout.write(re.sub(u"([\u4e00-\ua6ff]([\u3000-\uffe0]*[\u4e00-\ua6ff])*)","<button onClick=\"ca()\">Copy</button><span>\\1</span>",sys.stdin.read().decode("utf-8")).encode("utf-8"))' < $N | sed -e 's,/script>,/script><script>function ca(t) { clipboard.append((window.event.target||window.event.srcElement).nextSibling.innerHTML); location.href="index.html"}</script>,' > n && mv n $N; fi; done &&
for N in */[0-9]*.html; do if test -e "$N"; then python2 -c 'import sys,re ; sys.stdout.write(re.sub(u"([\u4e00-\ua6ff]([\u3000-\uffe0]*[\u4e00-\ua6ff])*)(?![^\"]*\">)","<button onClick=\"ca()\">Copy</button><span>\\1</span>",sys.stdin.read().decode("utf-8")).encode("utf-8"))' < $N | sed -e 's,/script>,/script><script>function ca(t) { clipboard.append((window.event.target||window.event.srcElement).nextSibling.innerHTML); location.href="../index.html"}</script>,' > n && mv n $N; fi; done &&
sed -e 's,<form,<script>var c=clipboard.get(); if(c.length) document.write(c+'"'"' <button onClick="clipboard.clear();location.reload()">Clear</button>'"'"')</script><form,' < index.html > n && mv n index.html
