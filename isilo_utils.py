#!/usr/bin/env python2.7
# Legacy code for helping to write dictionaries to iSilo files
# Silas S. Brown 2010(?)

import unicodedata, os

def init_character_pictures(allText):
    global allChars ; allChars = {}
    if type(allText)==file: allText=allText.read()
    if not type(allText)==type(u""): allText=allText.decode('utf-8')
    for c in allText: allChars[ord(c)]=1
    assert not os.system("which imgserver"), "Please install imgserver from Web Access Gateway"
    os.system("imgserver 2>/dev/null >/dev/null & # already running doesn't matter")
    for l in allChars.keys()[:]:
        try: open("%04X.gif" % l)
        except: os.system("wget -q -O %04X.gif http://localhost:7080/s/%04X" % (l,l))
        try: ll=len(open("%04X.gif" % l).read())
        except: ll=0
        if not ll: del allChars[l]
    os.system("killall imgserver") # needed for make -j to exit

def picify(s):
    if not type(s)==type(u""): s=s.decode('utf-8')
    r=[]
    for c in s:
        if ord(c) in allChars: r.append('<IMG SRC="%04X.gif">' % ord(c)) # don't worry about height/width for iSilo
        else: r.append(c.encode('utf-8')) # TODO is this charset fully supported by all versions of iSilo?  treatment of errors ?
    return ''.join(r)

def makeDx(dxList,prefix):
    letters = {}
    for i in range(len(dxList)): dxList[i] = (dxList[i][0].lower()+" ",)+dxList[i]
    dxList.sort()
    for i in range(len(dxList)):
        if not dxList[i][0][0] in letters: letters[dxList[i][0][0]] = {}
        noDiacritics = u''.join((c for c in unicodedata.normalize('NFD',dxList[i][0].decode('utf-8')[1:]) if not unicodedata.category(c).startswith('M')))
        lllist=filter(lambda x:ord('a')<=ord(x)<=ord('z'), noDiacritics) # 1st ascii letter after the 1st letter (e.g. A1bing2 = b)
        if lllist:
            if not lllist[0] in letters[dxList[i][0][0]]: letters[dxList[i][0][0]][lllist[0]] = []
            letters[dxList[i][0][0]][lllist[0]].append(dxList[i][1:])
    for l in letters.keys():
        o=open(prefix+l+".html",'w')
        o.write('<HTML><BODY>')
        o.write(' '.join([('<A HREF="#%s">%s%s</A>' % (ll,l,ll)) for ll in sorted(letters[l].keys())])+'<P>')
        for ll in sorted(letters[l].keys()):
            o.write('<A NAME="%s"></A>' % ll)
            for dxEntry,count in letters[l][ll]:
                o.write('* <A HREF="%d.html">%s</A><BR>' % (count,picify(dxEntry)))
        o.write('</BODY></HTML>')
    return " ".join([('<A HREF="%s%s.html">%s</A>' % (prefix,l,l.upper())) for l in sorted(letters.keys())])

def compile_iSilo(prefix,title,index_html):
    open("index.html","w").write('<HTML><BODY>'+index_html+'</BODY></HTML>')
    open(prefix+".ixl","w").write('<?xml version="1.0"?>'+"""
<iSiloXDocumentList>
  <iSiloXDocument>
    <LinkOptions>
     <MaximumDepth value="255"/> 
    </LinkOptions>   
    <DocumentOptions>
      <CharSet>UTF-8</CharSet>
    </DocumentOptions>
    <Source>
      <Sources>
        <Path>index.html</Path>
      </Sources>
      <CharSet>UTF-8</CharSet>
    </Source>
    <Targets>
      <Export                   value="all"/>
    </Targets>
    <Destination>
      <Title>%s</Title>
      <Files>
        <Path>%s.pdb</Path>
      </Files>
    </Destination>
    <ImageOptions>
      <Images                   value="include"/>
      <Compress                 value="yes"/>
      <LossyLevel               value="none"/>
    </ImageOptions>
    <SecurityOptions>
      <Convert                  value="allow"/>
      <CopyBeam                 value="allow"/>
      <CopyAndPaste             value="allow"/>
      <Modify                   value="allow"/>
      <Print                    value="allow"/>
      <Expiration>
        <Expires                value="no"/>
      </Expiration>
    </SecurityOptions>
    <TextOptions>
      <ProcessLineBreaks        value="yes"/>
      <ConvertSingleLineBreaks  value="yes"/>
      <Preformatted             value="no"/>
      <UseMonospaceFont         value="no"/>
    </TextOptions>
</iSiloXDocument>
</iSiloXDocumentList>""" % (title,prefix))
    r=os.system("iSiloXC -x %s.ixl" % prefix)
    assert not r, "iSiloXC failed to run"
    assert os.path.exists(prefix+".pdb"), "iSiloXC output failed to appear"
