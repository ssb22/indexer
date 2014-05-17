#!/usr/bin/env python

# Online HTML Indexer v1.06 (c) 2013-14 Silas S. Brown.

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# Configuration
# -------------

# You can change these variables here, but if you do then
# it might be more difficult to upgrade to newer versions
# of this script.  However, any file called ohi_config.py
# (in the current directory or 1 level up) will be read.

html_filename = "input.html" # set this to whatever
# - and when that file changes, this script will update
# files with that plus .index, .header and .footer
# (it might be a good idea to do a separate run of this
# script, from the command line, to perform that update,
# especially if you're on a slow machine and the webserver
# has a short timeout; note that the update does NOT have
# to be done on the same machine, as long as the resulting
# files can be copied across)
# (another speedup is to get a small wrapper script to
# import ohi_online; the compiled version can then be used
# after the first time)

alphabet = "abcdefghijklmnopqrstuvwxyz" # set to None for all characters and case-sensitive; any headings not containing ANY of these characters will be put in as-is anyway

# ignore_text_in_parentheses NOT available in the online version because it could make it impossible to fetch entries that differ from others only in parenthetical additions (unless you merge the entries, which might not be a good idea)

more_sensible_punctuation_sort_order = True

remove_utf8_diacritics = True # or False, for removing diacritics in index headings (not in main text);
# assumes UTF-8.  (Letters with diacritics will be treated as though they did not have any.)

frontpage_lookup_prompt = "Lookup: "
shorter_lookup_prompt   = "Lookup: "

lines_before = 5 ; lines_after = 10
max_show_more = 50 ; increment = 10

between_before_and_after = "<br>"
# For more compactness, try this instead:
# between_before_and_after = " | "
# (depends on what sort of data you have though)

# You can override these functions if you want:
def preprocess_result(markup): return markup
def links_to_related_services(query): return "" # e.g. "Here | <a href...>Somewhere else</a>"

code_to_run_when_DOM_changes = ""
# you can set this to any Javascript to run after our JS
# manages to change the DOM (on capable browsers), e.g. to
# fix some typography when browser support is detected

web_adjuster_extension_mode = False
web_adjuster_extension_url = "http://example.org/ohi.cgi"
# (if you set the above, this module's handle() will work
# - see Web Adjuster 'extensions' option for more details.
# Otherwise we just behave as a CGI script.)

# ------------------------------------------

# allow overrides:
import sys ; sys.path = ['.','..'] + sys.path
try: from ohi_config import *
except ImportError: pass

if not web_adjuster_extension_mode:
    import cgitb ; cgitb.enable() # remove this if you don't want tracebacks in the browser

import mmap, os, cgi, urllib, re

def create_linemap(fName):
    f = open(fName,"rb")
    lm = LineMap(f.fileno(), 0, access=mmap.ACCESS_READ)
    lm.f = f # ensure not closed by gc
    return lm
class LineMap(mmap.mmap): # might fail in old Python versions where mmap isn't a class
    def linesAround(self,txt,linesBefore,linesAfter):
        "returns (before,line,after), up to numLines lines either side of the line appropriate for txt"
        self.seek(self.bisect(txt))
        linesBefore = sum(self.back_line() for i in xrange(linesBefore))
        return [self.readline() for i in xrange(linesBefore)],self.readline(),[x for x in [self.readline() for i in xrange(linesAfter)] if x]
    def bisect(self,txt,lo=0,hi=-1):
        "returns pos of start of appropriate line"
        if hi==-1: hi=len(self)
        elif hi <= lo:
            # return self.lineStart(hi)
            # ammendment: if only the first few characters matched, it's possible that the PREVIOUS entry will match more characters (positioning is rarely helped by an inserted character, e.g. a pinyin shen/sheng confusion, and we probably want to draw more attention to the previous entries in this case, especially if the following entries are completely different e.g. 'shi'; TODO: could even do full 'first entry that matches as many characters as possible' logic)
            ret = self.lineStart(hi)
            if ret==0 or self[ret:ret+len(txt)]==txt: return ret
            txt2 = txt
            while len(txt2)>1 and not self[ret:ret+len(txt2)]==txt2: txt2 = txt2[:-1]
            ret2 = self.lineStart(ret-1)
            if self[ret2:ret2+len(txt2)+1]==txt[:len(txt2)+1]: return ret2
            else: return ret
        lWidth,uWidth = int((hi-lo)/2),int((hi-lo+1)/2)
        lLmid = self.lineStart(lo+lWidth)
        if self.lineAt(lLmid) < txt: return self.bisect(txt,lo+uWidth,self.lineStart(hi)) # mid NOT lMid as latter doesn't shorten the interval; lHi instead of hi does
        else: return self.bisect(txt,lo,lLmid) # similar
    def lineStart(self,pos):
        return self.rfind("\n",0,pos)+1
    def lineAt(self,pos):
        self.seek(pos) ; return self.readline()
    def back_line(self):
        p = self.tell()
        if not p: return 0
        elif self[p-1]=='\n':
            self.seek(self.lineStart(p-1))
        else: self.seek(self.lineStart[p])
        return 1

if alphabet and more_sensible_punctuation_sort_order: alphaOnly = lambda x: re.sub('([;,]);+',r'\1',''.join(c for c in x.lower().replace('-',' ').replace(',','~COM~').replace(';',',').replace('~COM~',';').replace(' ',';') if c in alphabet+',;')) # gives ; < , == space (useful if ; is used to separate definitions and , is used before extra words to be added at the start; better set space EQUAL to comma, not higher, or will end up in wrong place if user inputs something forgetting the comma)
elif alphabet: alphaOnly = lambda x: ''.join(c for c in x.lower() if c in alphabet)
elif more_sensible_punctuation_sort_order: alphaOnly = lambda x: re.sub('([;,]);+',r'\1',x.replace('-',' ').replace(',','~COM~').replace(';',',').replace('~COM~',';').replace(' ',';'))
else: alphaOnly = lambda x:x
if more_sensible_punctuation_sort_order: undo_alphaOnly_swap = lambda x:x.replace(';',' ').replace(',',';')
else: undo_alphaOnly_swap = lambda x:x
if remove_utf8_diacritics:
    _ao = alphaOnly ; import unicodedata
    alphaOnly = lambda x: _ao(u''.join((c for c in unicodedata.normalize('NFD',x.decode('utf-8')) if not unicodedata.category(c).startswith('M'))).encode('utf-8'))

def load(fName):
  txt = create_linemap(fName)
  try:
    if os.stat(fName).st_mtime <= os.stat(fName+".index").st_mtime:
      return txt,create_linemap(fName+".index"),open(fName+".header").read(),open(fName+".footer").read()
  except OSError: pass
  ret = {}
  contentStart = 0 ; header="" ; tag = ""
  altTags = [] # TODO: Document this.  Two adjacent tags with absolutely nothing in between (not even whitespace) = provide alternate labels to the same fragment.  This feature has not yet been implemented in the offline version, although it could be done by duplicating the fragment.
  for m in re.finditer(r'<a name="([^"]*)"></a>',txt):
    # First, output the content from the PREVIOUS tag:
    if contentStart and contentStart==m.start():
        # oops, previous tag has NO content, so treat it as an 'alternate heading' to the tag we're about to have:
        altTags.append(tag)
    else:
        for ttag in [tag]+altTags:
            tag2 = alphaOnly(ttag)
            if not tag2: tag2 = ttag
            if contentStart:
                if not tag2 in ret: ret[tag2] = (ttag,[])
                ret[tag2][1].append("\t"+str(contentStart)+"\t"+str(m.start()))
            else: # we're on the first tag
                assert not altTags
                header=txt[:m.start()]
        altTags = []
    # Now look at the new tag:
    tag = m.group(1) ; contentStart = m.end()
  footer = txt[contentStart:]
  if not header.strip(): header='<html><head><meta name="mobileoptimized" content="0"><meta name="viewport" content="width=device-width"></head><body>'
  if not footer.strip(): footer = '</body></html>'
  ret = [tag2+"\t"+ttag+"".join(rest)+"\n" for tag2,(ttag,rest) in ret.iteritems()] ; ret.sort()
  open(fName+".index","w").write("".join(ret))
  open(fName+".header","w").write(header)
  open(fName+".footer","w").write(footer)
  return txt,create_linemap(fName+".index"),header,footer

if web_adjuster_extension_mode: cginame = web_adjuster_extension_url[web_adjuster_extension_url.rindex('/')+1:]
else:
  cginame = os.sep+sys.argv[0] ; cginame=cginame[cginame.rindex(os.sep)+1:]

def queryForm(prompt): return "<form action=\""+cginame+"\">"+prompt+'<input type="text" name="q"><input type="Submit" value="OK"></form>'
def out(html="",req=None):
  if not html: html='<script><!--\ndocument.forms[0].q.focus();\n//--></script>' # TODO: else which browsers need <br> after the </form> in the line below?
  html = queryForm(shorter_lookup_prompt)+html
  if req:
      req.set_header('Content-type','text/html; charset=utf-8')
      req.write(header+html+footer)
  else: print "Content-type: text/html; charset=utf-8\n\n"+header+html+footer
def link(l,highl=""):
  l,lTxt,rest = l.split('\t',2)
  highl = highl.decode('utf-8') # TODO: configurable charset?
  while highl and not l.startswith(highl.encode('utf-8')): highl=highl[:-1]
  highl = highl.encode('utf-8')
  i = j = 0
  for c in highl:
    matched = (lTxt[i]==c)
    if matched or (alphabet and not lTxt[i] in alphabet and not lTxt[i] in l):
      i += 1
      if matched: j = i
    else: break
  if j: lTxt = '<b>'+lTxt[:j]+'</b>'+lTxt[j:]
  return '<a href="'+cginame+'?q='+urllib.quote(undo_alphaOnly_swap(l))+'&e=1" onclick="return tryInline(this)">'+lTxt+'</a>' # (this gives a 'click to expand/collapse' option on browsers that support it, TODO: configurable?  option to have onMouseOver previews somewhere??  careful as could run into trouble with user CSS files)
  # (Could shorten l to the shortest unique part of the word, but that might not be a good idea if the data can change while users are online)
  
def redir(base,rest,req=None):
  if not base:
      if web_adjuster_extension_mode: base = web_adjuster_extension_url
      else: base=os.environ.get("SCRIPT_URI",cginame) # cginame would make it a relative redirect, which might or might not work with the browser/server
  if req:
      req.set_status(302)
      req.set_header("Location",base+rest)
      return
  print "Status: 302" # TODO: check this works on all servers
  print "Location: "+base+rest
  print

def main(req=None):
  if req: query = req.request.arguments
  elif web_adjuster_extension_mode:
      load(html_filename)
      sys.stderr.write("Index is now up-to-date\n")
      return
  else: query = cgi.parse()
  def qGet(k,default=""):
      v = query.get(k,default)
      if type(v)==list: v=v[0]
      return v
  q = qGet("q")
  a = int(qGet("a",lines_after))
  b = int(qGet("b",lines_before))
  e = qGet("e")
  if q and not e and a==lines_after and b==lines_before and not query.get("t",""): return redir("","?q="+urllib.quote(undo_alphaOnly_swap(q))+"&t=1#e",req=req)
  global header,footer
  txt,index,header,footer = load(html_filename)
  if not q: return out(req=req)
  q,q0 = alphaOnly(q),q
  if not q: q = q0
  if e:
    ranges = index.linesAround(q,0,0)[1].split("\t")[2:]
    toOut = preprocess_result("<hr>".join(txt[int(a):int(b)] for a,b in zip(ranges[::2], ranges[1::2])))
    if e=="2":
        if req:
            req.set_header('Content-type','text/plain; charset=utf-8')
            req.write(toOut)
        else: print "Content-type: text/plain; charset=utf-8\n\n"+toOut # for the XMLHttpRequest
        return
    else: return out(toOut,req=req)
  b4,line,aftr = index.linesAround(q,b,a)
  lnks = links_to_related_services(q0)
  if lnks: lnks += '<hr>'
  def more(a,b,tag,label): return ('<a name="%s" href="%s?q=%s&a=%d&b=%d#%s">%s</a>' % (tag,cginame,urllib.quote(undo_alphaOnly_swap(q)),a,b,tag,label)) # 'after' version of this works only if it's at the very bottom of the page, so the words above it are still on-screen when jumping to its hash
  if b < max_show_more and len(b4)==b: moreBefore = more(a,min(b+increment,max_show_more),"b","&lt;&lt; more")+between_before_and_after
  else: moreBefore = '<a name="b"></a>'
  if a < max_show_more and len(aftr)==a: moreAfter = between_before_and_after+more(min(a+increment,max_show_more),b,"a","more &gt;&gt;")
  else: moreAfter = '<a name="a"></a>'
  if not '<' in between_before_and_after: tableStyle,tableAround = ' style="display:inline-table"',between_before_and_after
  else: tableStyle,tableAround = "",""
  out(lnks+moreBefore+"""<script><!--
  function tryInline(l) { l.onclick=function(){return false}; if(!(XMLHttpRequest&&l.innerHTML)) return true; var n=document.createElement("div"); l.parentNode.insertBefore(n,l.nextSibling); n.innerHTML="Loading"; if(n.innerHTML!="Loading") return true; n.setAttribute("style","border:thin blue solid"); function g(h){l.myStuff=h;n.innerHTML=h;l.onclick=function(){l.parentNode.removeChild(n);l.onclick=function(){return tryInline(l)};return false};"""+code_to_run_when_DOM_changes+"""}; if(l.myStuff) g(l.myStuff);else{var req=new XMLHttpRequest();req.open("GET",l.href.replace("&e=1","&e=2"),true);req.onreadystatechange=function(){if(req.readyState==4)g(req.responseText)};req.send()}return false }
//--></script>"""+between_before_and_after.join(link(l) for l in b4)+tableAround+'<table border'+tableStyle+'><tr><td><a id="e" name="e"></a>'+link(line,q)+'</td></tr></table>'+tableAround+between_before_and_after.join(link(l) for l in aftr)+moreAfter,req=req)

def handle(url,req):
    if url.startswith(web_adjuster_extension_url):
        main(req)
        return True

if __name__=="__main__": main()
