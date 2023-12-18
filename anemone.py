#!/usr/bin/env python3
"""
Anemone 0.5 (http://ssb22.user.srcf.net/anemone)
(c) 2023 Silas S. Brown.  License: Apache 2
Run program with --help for usage instructions.
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Where to find history:
# on GitHub at https://github.com/ssb22/indexer
# and on GitLab at https://gitlab.com/ssb22/indexer
# and on BitBucket https://bitbucket.org/ssb22/indexer
# and at https://gitlab.developers.cam.ac.uk/ssb22/indexer
# and in China: https://gitee.com/ssb22/indexer

from argparse import ArgumentParser
generator=__doc__.strip().split('\n')[0]
args = ArgumentParser(prog="anemone",description=generator)
args.add_argument("files",metavar="file",nargs="+",help="file name of: an MP3 recording, a text file containing its title, a JSON file containing its time markers, an XHTML file containing its full text, or the output ZIP file.  Only one output file may be specified, but any number of the other files can be included.  If no other files are given then titles are taken from the MP3 filenames.")
args.add_argument("--lang",default="en",
                help="the ISO 639 language code of the publication (defaults to en for English)")
args.add_argument("--title",default="",help="the title of the publication")
args.add_argument("--creator",default="",help="the creator name, if known")
args.add_argument("--publisher",default="",help="the publisher name, if known")
args.add_argument("--reader",default="",help="the name of the reader who voiced the recordings, if known")
args.add_argument("--date",help="the publication date as YYYY-MM-DD, default is current date")
args.add_argument("--marker-attribute",default="data-pid",help="the attribute used in the HTML to indicate a segment number corresponding to a JSON time marker entry, default is data-pid")
args.add_argument("--page-attribute",default="data-no",help="the attribute used in the HTML to indicate a page number, default is data-no")

import time, sys, os, re, json
from functools import reduce
from zipfile import ZipFile, ZIP_DEFLATED
from html.parser import HTMLParser
from mutagen.mp3 import MP3 # pip install mutagen

def parse_args():
    global recordingFiles, jsonFiles, textFiles, htmlFiles, outputFile
    recordingFiles,jsonFiles,textFiles,htmlFiles,outputFile=[],[],[],[],None
    globals().update(args.parse_args().__dict__)
    for f in files:
        if f.endswith(f"{os.extsep}zip"):
            if outputFile: errExit(f"Only one {os.extsep}zip output file may be specified")
            outputFile = f ; continue
        elif not os.path.exists(f): errExit(f"File not found: {f}")
        if f.endswith(f"{os.extsep}mp3"):
            recordingFiles.append(f)
        elif f.endswith(f"{os.extsep}json"):
            jsonFiles.append(f)
        elif f.endswith(f"{os.extsep}txt"):
            textFiles.append(f)
        elif f.endswith(f"{os.extsep}html"):
            htmlFiles.append(f)
        else: errExit(f"Can't handle '{f}'")
    if not recordingFiles: errExit("Creating DAISY files without audio is not yet implemented")
    if htmlFiles and not jsonFiles: errExit("Full text without time markers is not yet implemented")
    if jsonFiles and not htmlFiles: errExit("Time markers without full text is not implemented")
    if htmlFiles and textFiles: errExit("Combining full text with title-only text files is not yet implemented.  Please specify full text for everything or just titles for everything, not both.")
    if jsonFiles and not len(recordingFiles)==len(jsonFiles): errExit(f"If JSON marker files are specified, there must be exactly one JSON file for each recording file.  We got f{len(jsonFiles)} JSON files and f{len(recordingFiles)} recording files.")
    if textFiles and not len(recordingFiles)==len(textFiles): errExit(f"If text files are specified, there must be exactly one text file for each recording file.  We got f{len(textFiles)} txt files and f{len(recordingFiles)} recording files.")
    if htmlFiles and not len(recordingFiles)==len(htmlFiles): errExit(f"If HTML files are specified, there must be exactly one HTML file for each recording file.  We got f{len(htmlFiles)} HTML files and f{len(recordingFiles)} recording files.")
    if not outputFile: outputFile=f"output_daisy{os.extsep}zip"
    global title
    if not title: title=outputFile.replace(f"{os.extsep}zip","").replace("_daisy","")
def errExit(m):
    sys.stderr.write(f"Error: {m}\n") ; sys.exit(1)

def main():
    parse_args()
    write_all(get_texts())

def get_texts():
    if textFiles: return [open(f).read().strip() for f in textFiles] # section titles only, from text files
    elif not htmlFiles: return [r[:r.rindex(f"{os.extsep}mp3")] for r in recordingFiles] # section titles only, from MP3 filenames
    recordingTexts = []
    for h,j in zip(htmlFiles,jsonFiles):
        markers = json.load(open(j))['markers']
        want_pids = [jsonAttr(m,"id") for m in markers]
        id_to_content = {}
        pageNos = []
        allowedInlineTags=[] # Dolphin EasyReader does not render <strong> and <em>, and constructs like "(<em>Publication name</em>" result in incorrect space after "(" so best leave it out.  TODO: does any reader allow inline links for footnotes and references?  will need to rewrite their destinations if so
        class PidsExtractor(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.addTo = None
                self.pageNoGoesAfter = 0
            def handle_starttag(self,tag,attrs):
                attrs = dict(attrs)
                pageNo = attrs.get(page_attribute,None)
                if pageNo: pageNos.append((self.pageNoGoesAfter,pageNo))
                if attrs.get(marker_attribute,None) in want_pids:
                    self.theStartTag = tag
                    a = attrs[marker_attribute]
                    self.pageNoGoesAfter = want_pids.index(a)
                    id_to_content[a] = ((tag if re.match('h[1-6]$',tag) or tag=='span' else 'p'),[])
                    self.addTo = id_to_content[a][1]
                elif not self.addTo==None and tag in allowedInlineTags: self.addTo.append(f'<{tag}>')
            def handle_endtag(self,tag):
                if not self.addTo==None:
                    if tag==self.theStartTag: self.addTo = None
                    elif tag in allowedInlineTags: self.addTo.append(f'</{tag}>')
            def handle_data(self,data):
                if not self.addTo==None:
                    self.addTo.append(data.replace('&','&amp;').replace('<','&lt;'))
        PidsExtractor().feed(open(h).read())
        rTxt = []
        for i in range(len(markers)):
            if i: rTxt.append(parseTime(jsonAttr(markers[i],"time")))
            tag,content = id_to_content[want_pids[i]]
            content = ''.join(content).strip()
            rTxt.append((tag,content))
        recordingTexts.append((rTxt,pageNos))
    return recordingTexts

def jsonAttr(d,suffix):
    keys = [k for k in d.keys() if k.lower().endswith(suffix)]
    if not keys: errExit(f"No *{suffix} in {repr(keys)}")
    if len(keys)>1: errExit(f"More than one *{suffix} in {repr(keys)}")
    return str(d[keys[0]])
def parseTime(t):
    tot = 0.0 ; mul = 1
    for u in reversed(t.split(':')):
        tot += float(u)*mul ; mul *= 60
    return tot

def write_all(recordingTexts):
    "each item is: 1 text for section title of whole recording, or ([(type,text),time,(type,text),time,(type,text)],[(goesBefore,pageNo),...])"
    assert len(recordingFiles) == len(recordingTexts)
    headings = [([u+(v//2,) for v,u in enumerate(t[0]) if type(u)==tuple and u[0].startswith('h')] if type(t)==tuple else t) for t in recordingTexts]
    hasFullText = any(type(t)==tuple for t in recordingTexts)
    z = ZipFile(outputFile,"w",ZIP_DEFLATED,False)
    secsSoFar = 0
    durations = [] ; pSoFar = 0
    for recNo in range(1,len(recordingTexts)+1):
        secsThisRecording = MP3(recordingFiles[recNo-1]).info.length
        rTxt = recordingTexts[recNo-1]
        durations.append(secsThisRecording)
        z.writestr(f"{recNo:04d}.mp3",open(recordingFiles[recNo-1],'rb').read())
        z.writestr(f'{recNo:04d}.smil',section_smil(recNo,secsSoFar,secsThisRecording,pSoFar,rTxt[0] if type(rTxt)==tuple else rTxt))
        z.writestr(f'{recNo:04d}.htm',text_htm((rTxt[0][::2] if type(rTxt)==tuple else [('h1',rTxt)]),pSoFar))
        secsSoFar += secsThisRecording
        pSoFar += (1+len(rTxt[0])//2 if type(rTxt)==tuple else 1)
    z.writestr('master.smil',master_smil(headings,secsSoFar))
    z.writestr('ncc.html',ncc_html(headings,hasFullText,secsSoFar,[(t[1] if type(t)==tuple else []) for t in recordingTexts]))
    z.writestr('er_book_info.xml',er_book_info(durations)) # not DAISY standard but EasyReader can use this
    z.close()
    sys.stderr.write(f"Wrote {outputFile}\n")

def ncc_html(headings = [],
             hasFullText = False,
             totalSecs = 0, pageNos=[]):
    """Returns the Navigation Control Centre (NCC)
    pageNos is [[(goesAfter,pageNo),...],...]"""
    pages = max([max([int(N) for after,N in PNs],default=0) for PNs in pageNos],default=0)
    # TODO: we assume all pages are 'normal' pages
    # (not 'front' pages in Roman letters etc)
    headingsR = HReduce(headings)
    global date
    if not date: date = "%04d-%02d-%02d" % time.localtime()[:3]
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="{lang}" xml:lang="{lang}" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta content="text/html; charset=utf-8" http-equiv="Content-type" />
    <title>{title}</title>
    <meta name="dc:creator" content="{creator}" />
    <meta name="dc:date" content="{date}" scheme="yyyy-mm-dd" />
    <meta name="dc:language" content="{lang}" scheme="ISO 639" />
    <meta name="dc:publisher" content="{publisher}" />
    <meta name="dc:title" content="{title}" />
    <meta name="ncc:narrator" content="{reader}" />
    <meta name="ncc:producedDate" content="{date}" />
    <meta name="ncc:generator" content="{generator}" />
    <meta name="dc:format" content="Daisy 2.02" />
    <meta name="ncc:charset" content="utf-8" />
    <meta name="ncc:pageFront" content="0" />
    <meta name="ncc:maxPageNormal" content="{pages}" />
    <meta name="ncc:pageNormal" content="{pages}" />
    <meta name="ncc:pageSpecial" content="0" />
    <meta name="ncc:tocItems" content="{len(headingsR)}" />
    <meta name="ncc:totalTime" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{totalSecs%60:02f}" />
    <meta name="ncc:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}" />
    <meta name="ncc:depth" content="{max(int(h[0][1:]) for h in headingsR)}" />
    <meta name="ncc:files" content="{2+len(headings)*(3 if hasFullText else 2)}" />
  </head>
  <body>"""+''.join(f"""
    <{t[0]} class="section" id="s{s+1}">
      <a href="{t[2]+1:04d}.smil#t{t[2]+1}.{t[3]}">{t[1]}</a>
    </{t[0]}>""" for s,t in enumerate(headingsR))+''.join(''.join(f"""
    <span class="page-normal" id="page{N}"><a href="{r+1:04d}.smil#t{r+1}.{after}">{N}</a></span>""" for (after,N) in PNs) for r,PNs in enumerate(pageNos))+"""
  </body>
</html>
"""

def HReduce(headings): return reduce(lambda a,b:a+b,[([(hType,hText,recNoOffset,hOffset) for (hType,hText,hOffset) in i] if type(i)==list else [('h1',i,recNoOffset,0)]) for recNoOffset,i in enumerate(headings)],[])

def master_smil(headings = [],
                totalSecs = 0):
    headings = HReduce(headings)
    return f"""<?xml version="1.0"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">
<smil>
  <head>
    <meta name="dc:title" content="{title}" />
    <meta name="ncc:generator" content="{generator}" />
    <meta name="dc:format" content="Daisy 2.02" />
    <meta name="ncc:timeInThisSmil" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{totalSecs%60:02f}" />
    <layout>
      <region id="textView" />
    </layout>
  </head>
  <body>"""+'\n'.join(f"""
    <ref title="{deHTML(t[1])}" src="{t[2]+1:04d}.smil#t{t[2]+1}.{t[3]}" id="ms_{s+1:04d}" />""" for s,t in enumerate(headings))+"""
  </body>
</smil>
"""

def section_smil(recNo=1,
                 totalSecsSoFar=0,
                 secsThisRecording=0,
                 startP=0,
                 textsAndTimes=[]):
    if not type(textsAndTimes)==list: textsAndTimes=[textsAndTimes]
    textsAndTimes = [0]+textsAndTimes+[secsThisRecording]
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">
<smil>
  <head>
    <meta name="ncc:generator" content="{generator}" />
    <meta name="dc:format" content="Daisy 2.02" />
    <meta name="ncc:totalElapsedTime" content="{int(totalSecsSoFar/3600)}:{int(totalSecsSoFar/60)%60:02d}:{totalSecsSoFar%60:02f}" />
    <meta name="ncc:timeInThisSmil" content="{int(secsThisRecording/3600)}:{int(secsThisRecording/60)%60:02d}:{secsThisRecording%60:02f}" />
    <meta name="title" content="{deHTML(textsAndTimes[1][1])}" />
    <meta name="dc:title" content="{deHTML(textsAndTimes[1][1])}" />
    <layout>
      <region id="textView" />
    </layout>
  </head>
  <body>
    <seq id="sq{recNo}" dur="{secsThisRecording:f}s">"""+"".join(f"""
      <par endsync="last" id="pr{recNo}.{i//2}">
        <text id="t{recNo}.{i//2}" src="{recNo:04d}.htm#p{startP+i//2}" />
        <seq id="sq{recNo}.{i//2}a">
          <audio src="{recNo:04d}.mp3" clip-begin="npt={textsAndTimes[i-1]:f}s" clip-end="npt={textsAndTimes[i+1]:f}s" id="aud{recNo}.{i//2}" />
        </seq>
      </par>""" for i in range(1,len(textsAndTimes),2))+"""
    </seq>
  </body>
</smil>
"""

def deHTML(t): return re.sub('<[^>]*>','',t).replace('"','&quot;') # for inclusion in attributes

def text_htm(paras,offset=0):
    "paras = [(type,text),(type,text),...], type=h1/p/span, text is xhtml i.e. & use &amp; etc"
    return f"""<?xml version="1.0"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="{lang}" xml:lang="{lang}" xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<title>{title}</title>
		<meta content="text/html; charset=utf-8" http-equiv="content-type"/>
		<meta name="generator" content="{generator}"/>
	</head>
	<body>
"""+"\n".join(f"<{tag} id=\"p{num+offset}\"{' class='+chr(34)+'sentence'+chr(34) if tag=='span' else ''}>{text}{'' if tag=='p' else ('</'+tag+'>')}{'' if tag.startswith('h') or (num+1<len(paras) and paras[num+1][0]=='span') else '</p>'}" for num,(tag,text) in enumerate(paras))+"""
        </body>
</html>
"""

def er_book_info(durations):
    "durations = list of secsThisRecording"
    return """<?xml version="1.0" encoding="utf-8"?>
<book_info>
    <smil_info>"""+"".join(f"""
        <smil nr="{s}" Name="{s+1:04d}.smil" dur="{d:f}"/>""" for s,d in enumerate(durations))+"""
    </smil_info>
</book_info>
"""

if __name__ == "__main__": main()
