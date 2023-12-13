#!/usr/bin/env python3

generator = "Anemone 0.1 (http://ssb22.user.srcf.net/anemone)"

from argparse import ArgumentParser
args = ArgumentParser(prog="anemone",description=generator)
args.add_argument("files",metavar="file",nargs="+",help="file name of: an MP3 recording, a text file containing its title, a JSON file containing its time markers, an HTML file containing its full text, or the output ZIP file.  Only one output file may be specified, but any number of the other files can be included.  Nice files only please, this code is not fully tested on messy markup.")
args.add_argument("--lang",default="en",
                help="the ISO 639 language code of the publication")
args.add_argument("--title",default="",help="the title of the publication")
args.add_argument("--creator",default="",help="the creator name, if known")
args.add_argument("--publisher",default="",help="the publisher name, if known")
args.add_argument("--reader",default="",help="the name of the reader who voiced the recordings, if known")
args.add_argument("--date",help="the publication date as YYYY-MM-DD, default is current date")
args.add_argument("--attribute",default="data-pid",help="the attribute used in the HTML to indicate segment numbers corresponding to JSON marker entries")

import time, sys, os, re, json
from functools import reduce
from zipfile import ZipFile
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
    if not textFiles and not htmlFiles: errExit("Please add either text files or HTML files")
    if not outputFile: outputFile=f"output_daisy{os.extsep}zip"
    global title
    if not title: title=outputFile.replace(f"{os.extsep}zip","").replace("_daisy","")
def errExit(m):
    sys.stderr.write(f"Error: {m}\n") ; sys.exit(1)

def main():
    parse_args()
    write_all(get_texts())

def get_texts():
    if textFiles: return [open(f).read().strip() for f in textFiles] # section titles only (TODO: option to read these from MP3 filenames?)
    recordingTexts = []
    for h,j in zip(htmlFiles,jsonFiles):
        markers = json.load(open(j))['markers']
        want_pids = [str(m[[k for k in m.keys() if k.lower().endswith("id")][0]]) for m in markers]
        id_to_content = {}
        allowedInlineTags=['em','i','b','strong'] # TODO: are inline links allowed for footnotes and references?  will need to rewrite their destinations if so
        class PidsExtractor(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.addTo = None
            def handle_starttag(self,tag,attrs):
                attrs = dict(attrs)
                if attrs.get(attribute,None) in want_pids:
                    self.theStartTag = tag
                    a = attrs[attribute]
                    id_to_content[a] = (('h1' if tag.startswith('h') else tag if tag=='span' else 'p'),[]) # TODO: multiple heading depths (here and elsewhere)
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
            if i: rTxt.append(parseTime(markers[i]['startTime']))
            tag,content = id_to_content[want_pids[i]]
            content = ''.join(content).strip()
            rTxt.append((tag,content))
        recordingTexts.append(rTxt)
    return recordingTexts

def parseTime(t):
    tot = 0.0 ; mul = 1
    for u in reversed(t.split(':')):
        tot += float(u)*mul ; mul *= 60
    return tot

def write_all(recordingTexts):
    "each item is: 1 text for section title of whole recording, or [(type,text),time,(type,text),time,(type,text)]"
    assert len(recordingFiles) == len(recordingTexts)
    headings = [([u[1] for u in t if type(u)==tuple and u[0].startswith('h')] if type(t)==list else t) for t in recordingTexts] # TODO: multi-depth headings (currently we're making them all h1 in the TOC)
    hasFullText = any(type(t)==list for t in recordingTexts)
    z = ZipFile(outputFile,"w")
    secsSoFar = 0
    durations = [] ; pSoFar = 0
    for recNo in range(1,len(recordingTexts)+1):
        secsThisRecording = MP3(recordingFiles[recNo-1]).info.length
        durations.append(secsThisRecording)
        z.writestr(f"aud{recNo:04d}.mp3",open(recordingFiles[recNo-1],'rb').read())
        z.writestr(f'{recNo:04d}.smil',section_smil(recNo,secsSoFar,secsThisRecording,pSoFar,recordingTexts[recNo-1]))
        secsSoFar += secsThisRecording
        pSoFar += (1+len(recordingTexts[recNo-1])//2 if type(recordingTexts[recNo-1])==list else 1)
    z.writestr('master.smil',master_smil(headings,secsSoFar))
    z.writestr('ncc.html',ncc_html(headings,hasFullText,secsSoFar))
    z.writestr('er_book_info.xml',er_book_info(durations)) # not DAISY standard but EasyReader can use this
    z.writestr('text.htm',text_htm(reduce(lambda a,b:a+b,[(t[::2] if type(t)==list else [('h1',t)]) for t in recordingTexts])))
    z.close()
    sys.stderr.write(f"Wrote {outputFile}\n")

def ncc_html(headings = [],
             hasFullText = False,
             totalSecs = 0):
    "Returns the Navigation Control Centre (NCC)"
    # h1..h6 (ncc:depth set to highest: TODO)

    # TODO can we extract page numbers from the html?
    # NCC can have
    # <span class="value" id="value"><a href="smil#fragment">span content</a></span>
    # class page-front or page-normal (or page-special) for iv, 1, ...

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
    <meta name="ncc:maxPageNormal" content="0" />
    <meta name="ncc:pageNormal" content="0" />
    <meta name="ncc:pageSpecial" content="0" />
    <meta name="ncc:tocItems" content="{len(headings)}" />
    <meta name="ncc:totalTime" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{totalSecs%60:02f}" />
    <meta name="ncc:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}" />
    <meta name="ncc:depth" content="1" />
    <meta name="ncc:files" content="{(3 if hasFullText else 2)+len(headings)*2}" />
  </head>
  <body>"""+''.join(f"""
    <h1 class="section" id="s{s+1}.0">
      <a href="{s+1:04d}.smil#t{s+1}.0">{t[0] if type(t)==list else t}</a>
    </h1>""" for s,t in enumerate(headings))+"""
  </body>
</html>
"""

def master_smil(headings = [],
                totalSecs = 0):
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
    <ref title="{t[0] if type(t)==list else t}" src="{s+1:04d}.smil" id="ms_{s+1:04d}" />""" for s,t in enumerate(headings))+"""
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
        <text id="t{recNo}.{i//2}" src="text.htm#p{startP+i//2}" />
        <seq id="sq{recNo}.{i//2}a">
          <audio src="aud{recNo:04d}.mp3" clip-begin="npt={textsAndTimes[i-1]:f}s" clip-end="npt={textsAndTimes[i+1]:f}s" id="aud{recNo}.{i//2}" />
        </seq>
      </par>""" for i in range(1,len(textsAndTimes),2))+"""
    </seq>
  </body>
</smil>
"""

def deHTML(t): return re.sub('<[^>]*>','',t).replace('"','&quot;') # for inclusion in attributes

def text_htm(paras):
    "paras = [(type,text),(type,text),...], type=h1/p/span, text is xhtml i.e. & use &amp; etc"
    return f"""<?xml version="1.0"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="{lang}" xml:lang="{lang}" xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<title>{title}</title>
		<meta content="text/html; charset=utf-8" http-equiv="content-type"/>
		<meta name="GENERATOR" content="{generator}"/>
	</head>
	<body>
"""+"\n".join(f"<{tag} id=\"p{num}\"{' class='+chr(34)+'sentence'+chr(34) if tag=='span' else ''}>{text}{'' if tag=='p' else ('</'+tag+'>')}{'' if tag.startswith('h') or (num+1<len(paras) and paras[num+1][0]=='span') else '</p>'}" for num,(tag,text) in enumerate(paras))+"""
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
