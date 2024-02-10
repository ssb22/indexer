#!/usr/bin/env python3
"""
Anemone 0.99 (http://ssb22.user.srcf.net/anemone)
(c) 2023-24 Silas S. Brown.  License: Apache 2
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

def anemone(*files,**options):
    """This function can be called by scripts that
    import anemone: simply put the equivalent of
    the command line into 'files' and 'options'.
    Not thread-safe."""
    parse_args(*files,**options)
    write_all(get_texts())

from argparse import ArgumentParser
generator=__doc__.strip().split('\n')[0]
args = ArgumentParser(prog="anemone",description=generator,fromfile_prefix_chars='@')
args.add_argument("files",metavar="file",nargs="+",help="file name of: an MP3 recording, a text file containing its title (if no full text), a JSON file containing its time markers, an XHTML file containing its full text, or the output ZIP file.  Only one output file may be specified, but any number of the other files can be included; URLs may be given if they are to be fetched (HTML assumed if no extension).  If only MP3 files are given then titles are taken from their filenames.  You may also specify @filename where filename contains a list of files one per line.")
args.add_argument("--lang",default="en",
                help="the ISO 639 language code of the publication (defaults to en for English)")
args.add_argument("--title",default="",help="the title of the publication")
args.add_argument("--url",default="",help="the URL or ISBN of the publication")
args.add_argument("--creator",default="",help="the creator name, if known")
args.add_argument("--publisher",default="",help="the publisher name, if known")
args.add_argument("--reader",default="",help="the name of the reader who voiced the recordings, if known")
args.add_argument("--date",help="the publication date as YYYY-MM-DD, default is current date")
args.add_argument("--marker-attribute",default="data-pid",help="the attribute used in the HTML to indicate a segment number corresponding to a JSON time marker entry, default is data-pid")
args.add_argument("--page-attribute",default="data-no",help="the attribute used in the HTML to indicate a page number, default is data-no")
args.add_argument("--image-attribute",default="data-zoom",help="the attribute used in the HTML to indicate an absolute image URL to be included in the DAISY file, default is data-zoom")
args.add_argument("--refresh",action="store_true",help="if images etc have already been fetched from URLs, ask the server if they should be fetched again (use If-Modified-Since)")
args.add_argument("--reload",dest="refetch",action="store_true",help="if images etc have already been fetched from URLs, fetch them again without If-Modified-Since")
args.add_argument("--daisy3",action="store_true",help="Use the Daisy 3 format (ANSI/NISO Z39.86) instead of the Daisy 2.02 format.  This may require more modern reader software, and Anemone does not yet support Daisy 3 only features like tables in the text.")
args.add_argument("--mp3-recode",action="store_true",help="re-code the MP3 files to ensure they are constant bitrate and more likely to work with the more limited DAISY-reading programs like FSReader 3 (this option requires LAME)")
args.add_argument("--allow-jumps",action="store_true",help="Allow jumps in things like heading levels, e.g. h1 to h3 if the input HTML does it.  This seems OK on modern readers but might cause older reading devices to give an error.  Without this option, headings are promoted where necessary to ensure only incremental depth increase, and extra page numbers are inserted if numbers are skipped.") # might cause older reading devices to give an error: and is also flagged up by the validator

import time, sys, os, re, json, math, time
from functools import reduce
from subprocess import run, PIPE
from zipfile import ZipFile, ZIP_DEFLATED
from html.parser import HTMLParser
from mutagen.mp3 import MP3 # pip install mutagen
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.parse import unquote
from pathlib import Path # Python 3.5+

def parse_args(*inFiles,**kwargs):
    global recordingFiles, jsonFiles, textFiles, htmlFiles, imageFiles, outputFile, files
    recordingFiles,jsonFiles,textFiles,htmlFiles,imageFiles,outputFile=[],[],[],[],[],None
    if inFiles: globals().update(args.parse_args(list(inFiles)+['--'+k.replace('_','-') for k,v in kwargs.items() if v==True]+[a for k,v in kwargs.items() for a in ['--'+k.replace('_','-'),str(v)] if not v==True]).__dict__)
    else: globals().update(args.parse_args().__dict__)
    for f in files:
        if f.endswith(f"{os.extsep}zip"):
            if outputFile: errExit(f"Only one {os.extsep}zip output file may be specified")
            outputFile = f ; continue
        if re.match("https*://",f): f=fetch(f,1)
        if not os.path.exists(f): errExit(f"File not found: {f}")
        if f.endswith(f"{os.extsep}mp3"):
            recordingFiles.append(f)
        elif f.endswith(f"{os.extsep}json"):
            jsonFiles.append(f)
        elif f.endswith(f"{os.extsep}txt"):
            textFiles.append(f)
        elif f.endswith(f"{os.extsep}html") or not os.extsep in f.rsplit(os.sep,1)[-1]:
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

def get_texts():
    if textFiles: return [open(f).read().strip() for f in textFiles] # section titles only, from text files
    elif not htmlFiles: return [r[:r.rindex(f"{os.extsep}mp3")] for r in recordingFiles] # section titles only, from MP3 filenames
    recordingTexts = [] ; highestPage = [0]
    for h,j in zip(htmlFiles,jsonFiles):
        markers = json.load(open(j))['markers']
        want_pids = [jsonAttr(m,"id") for m in markers]
        id_to_content = {}
        pageNos = []
        allowedInlineTags=[] # Dolphin EasyReader does not render <strong> and <em>, and constructs like "(<em>Publication name</em>" result in incorrect space after "(" so best leave it out.  TODO: does any reader allow inline links for footnotes and references?  will need to rewrite their destinations if so
        assert not 'rt' in allowedInlineTags, "if allowing this, need to revise rt suppression logic" # and would have to rely on rp parens for most readers, so if a text has a LOT of ruby it could get quite unreadable
        class PidsExtractor(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.addTo = None
                self.suppress = 0
                self.imgsMaybeAdd = None
                self.pageNoGoesAfter = 0
            def handle_starttag(self,tag,attrs):
                attrs = dict(attrs)
                imgURL = attrs.get(image_attribute,None)
                if imgURL and re.match("https*://.*[.][^/]*$",imgURL) and not (self.addTo==None and self.imgsMaybeAdd==None):
                    img = f'<img src="{(imageFiles.index(imgURL) if imgURL in imageFiles else len(imageFiles))+1}{imgURL[imgURL.rindex("."):]}" {f"""id="i{imageFiles.index(imgURL) if imgURL in imageFiles else len(imageFiles)}" """ if daisy3 else ""}/>' # will be moved after paragraph by text_htm
                    if not imgURL in imageFiles:
                        imageFiles.append(imgURL)
                    if self.addTo==None: self.imgsMaybeAdd.append(img)
                    else: self.addTo.append(img)
                pageNo = attrs.get(page_attribute,None)
                if pageNo:
                    if not allow_jumps:
                        for i in range(highestPage[0]+1, int(pageNo)): pageNos.append((self.pageNoGoesAfter,str(i))) # TODO: is this really the best place to put them if we don't know where they are?  Page 1 might be the title page, etc
                    pageNos.append((self.pageNoGoesAfter,pageNo))
                    highestPage[0] = int(pageNo)
                if attrs.get(marker_attribute,None) in want_pids:
                    self.theStartTag = tag
                    a = attrs[marker_attribute]
                    self.pageNoGoesAfter = want_pids.index(a)
                    id_to_content[a] = ((tag if re.match('h[1-6]$',tag) or tag=='span' else 'p'),[])
                    if self.imgsMaybeAdd: self.imgsMaybeAddTo += self.imgsMaybeAdd # and imgsMaybeAdd will be reset to [] when this element is closed
                    self.addTo = id_to_content[a][1]
                elif not self.addTo==None and tag in allowedInlineTags: self.addTo.append(f'<{tag}>')
                elif tag=='rt': self.suppress += 1
            def handle_endtag(self,tag):
                if self.suppress and tag=='rt': self.suppress -= 1
                elif not self.addTo==None:
                    if tag==self.theStartTag:
                        self.highestImage,self.imgsMaybeAddTo, self.imgsMaybeAdd = len(imageFiles),self.addTo,[] # if we find any images (not in an id'd element) after the end of the id'd element, we might want to add them in with any inside it, but only if there's another id'd element after them i.e. not if they're just random decoration at the bottom of the page
                        self.addTo = None
                    elif tag in allowedInlineTags: self.addTo.append(f'</{tag}>')
                if tag=='html' and self.imgsMaybeAdd and hasattr(self,'highestImage'): del imageFiles[self.highestImage:] # do not include ones that were only in imgsMaybeAdd at the end of the page (and not also elsewhere)
            def handle_data(self,data):
                if not self.addTo==None and not self.suppress:
                    self.addTo.append(data.replace('&','&amp;').replace('<','&lt;'))
        PidsExtractor().feed(open(h).read())
        rTxt = []
        for i in range(len(markers)):
            if i: rTxt.append(parseTime(jsonAttr(markers[i],"time")))
            if want_pids[i] in id_to_content:
                tag,content = id_to_content[want_pids[i]]
                content = ''.join(content).strip()
                rTxt.append((tag,content))
            else:
                sys.stderr.write(f"Warning: JSON file {j} marker {i+1} marks paragraph ID {want_pids[i]} which is not present in corresponding HTML file {h}.  Anemone will make this a blank paragraph.\n")
                rTxt.append(('p',''))
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
    headings = getHeadings(recordingTexts)
    hasFullText = any(type(t)==tuple for t in recordingTexts)
    if mp3_recode: # parallelise lame if possible
        executor = ThreadPoolExecutor(max_workers=cpu_count())
        recordings=[executor.submit(lambda *_:run(["lame","--quiet",f,"-m","m","--resample","44.1","-c","--cbr","-b","96","-q","0","-o","-"],check=True,stdout=PIPE).stdout) for f in recordingFiles]
    z = ZipFile(outputFile,"w",ZIP_DEFLATED,False)
    def D(s): return s.replace("\n","\r\n") # in case old readers require DOS line endings
    if hasFullText: z.writestr("0000.txt",D(f"""
    If you're reading this, it likely means your
    operating system has unpacked the ZIP file
    and is showing you its contents.  While it
    is possible to extract recordings and text
    this way, it is better to send the whole ZIP
    to a DAISY reader so that its recordings and
    text can be connected with each other.  If
    you are using EasyReader, you might want to
    close this file and navigate up a level to
    find the original ZIP file so it can be sent
    to EasyReader as a whole.  Some other DAISY
    readers need to be pointed at the {'OPF' if daisy3 else 'NCC'} file
    instead, or at the whole directory.
""")) # TODO: message in other languages?
    # (it's iOS users that need the above, apparently.  Can't DAISY have a non-ZIP extension so Apple systems don't automatically unpack it?  but we do need to manually unpack if writing to a CD-ROM for old devices.  Can't Apple look at some kind of embedded "don't auto-unpack this zip" request?)
    secsSoFar = 0
    durations = [] ; pSoFar = 0
    for recNo in range(1,len(recordingTexts)+1):
        secsThisRecording = MP3(recordingFiles[recNo-1]).info.length
        rTxt = recordingTexts[recNo-1]
        durations.append(secsThisRecording)
        if mp3_recode: sys.stderr.write(f"Adding {recNo:04d}.mp3..."),sys.stderr.flush()
        z.writestr(f"{recNo:04d}.mp3",recordings[recNo-1].result() if mp3_recode else open(recordingFiles[recNo-1],'rb').read())
        if mp3_recode: sys.stderr.write(" done\n")
        z.writestr(f'{recNo:04d}.smil',D(section_smil(recNo,secsSoFar,secsThisRecording,pSoFar,rTxt[0] if type(rTxt)==tuple else rTxt)))
        z.writestr(f'{recNo:04d}.{"xml" if daisy3 else "htm"}',D(text_htm((rTxt[0][::2] if type(rTxt)==tuple else [('h1',rTxt)]),pSoFar)))
        secsSoFar += secsThisRecording
        pSoFar += (1+len(rTxt[0])//2 if type(rTxt)==tuple else 1)
    for n,u in enumerate(imageFiles): z.writestr(f'{n+1}{u[u.rindex("."):]}',fetch(u))
    if daisy3:
        z.writestr('dtbook.2005.basic.css',D(d3css))
        z.writestr('package.opf',D(package_opf(hasFullText,len(recordingTexts),secsSoFar)))
        z.writestr('text.res',D(textres))
    else: z.writestr('master.smil',D(master_smil(headings,secsSoFar)))
    z.writestr('navigation.ncx' if daisy3 else 'ncc.html',D(ncc_html(headings,hasFullText,secsSoFar,[(t[1] if type(t)==tuple else []) for t in recordingTexts])))
    if not daisy3: z.writestr('er_book_info.xml',D(er_book_info(durations))) # not DAISY standard but EasyReader can use this
    z.close()
    sys.stderr.write(f"Wrote {outputFile}\n")

def getHeadings(recordingTexts):
    ret = []
    for t in recordingTexts:
        if not type(t)==tuple: # title only
            ret.append(t) ; continue
        textsAndTimes,pages = t ; first = None
        chap = []
        for v,u in enumerate(textsAndTimes):
            if not type(u)==tuple: continue
            tag,text = u
            if first==None: first = v
            if not tag.startswith('h'):
                continue
            if v//2 - 1 == first//2 and not textsAndTimes[first][0].startswith('h'): # chapter starts with non-heading followed by heading: check the non-heading for "Chapter N" etc, extract number
                nums=re.findall("[1-9][0-9]*",textsAndTimes[first][1])
                if len(nums)==1: text=f"{nums[0]}: {text}"
            chap.append((tag,re.sub('<img src.*?/>','',text),v//2))
        ret.append(chap)
    return ret

import locale
locale.setlocale(locale.LC_TIME, "C") # for %a and %b in strftime (shouldn't need LC_TIME elsewhere)
refetch = refresh = False # so anyone importing the module can call fetch() before anemone(), e.g. to download a list of URLs from somewhere
def fetch(url,returnFilename=False):
    fn = 'cache/'+unquote(re.sub('.*?://','',url))
    if fn.endswith('/'): fn += "index.html"
    ifModSince = None
    if os.path.exists(fn):
        if refetch: pass # ignore already dl'd
        elif refresh:
            ifModSince=os.stat(fn).st_mtime
        elif returnFilename: return fn
        else: return open(fn,'rb').read()
    sys.stderr.write("Fetching "+url+"...")
    sys.stderr.flush()
    try: dat = urlopen(Request(url,headers=({"If-Modified-Since":time.strftime("%a, %d %b %Y %H:%M:%S GMT",time.gmtime(ifModSince))} if ifModSince else {}))).read()
    except HTTPError as e:
        if e.getcode()==304:
            sys.stderr.write(" no new data\n")
            if returnFilename: return fn
            else: return open(fn,'rb').read()
        else: raise
    if '/' in fn: Path(fn[:fn.rindex('/')]).mkdir(parents=True,exist_ok=True)
    sys.stderr.write(" saved\n")
    open(fn,'wb').write(dat)
    if returnFilename: return fn
    else: return dat

def ncc_html(headings = [],
             hasFullText = False,
             totalSecs = 0, pageNos=[]):
    """Returns the Navigation Control Centre (NCC)
    pageNos is [[(goesAfter,pageNo),...],...]"""
    pages = max([max([int(N) for after,N in PNs],default=0) for PNs in pageNos],default=0)
    # TODO: we assume all pages are 'normal' pages
    # (not 'front' pages in Roman letters etc)
    headingsR = normaliseDepth(HReduce(headings))
    global date
    if not date: date = "%04d-%02d-%02d" % time.localtime()[:3]
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">' if daisy3 else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"' if daisy3 else f'html lang="{lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{lang}">
  <head>
    {'<meta name="dtb:uid" content=""/>' if daisy3 else '<meta content="text/html; charset=utf-8" http-equiv="Content-type" />'}
    {f'<meta name="dtb:totalPageCount" content="{pages}" />' if daisy3 else ''}
    {f'<meta name="dtb:maxPageNumber" content="{pages}" />' if daisy3 else ''}
    {'' if daisy3 else f'<title>{title}</title>'}
    <meta name="dc:creator" content="{creator}" />
    <meta name="dc:date" content="{date}" scheme="yyyy-mm-dd" />
    <meta name="dc:language" content="{lang}" scheme="ISO 639" />
    <meta name="dc:publisher" content="{deHTML(publisher)}" />
    <meta name="dc:title" content="{deHTML(title)}" />
    <meta name="dc:type" content="text" />
    <meta name="dc:identifier" content="{url}" />
    <meta name="dc:format" content="{'ANSI/NISO Z39.86-2005' if daisy3 else 'Daisy 2.02'}" />
    <meta name="ncc:narrator" content="{reader}" />
    <meta name="ncc:producedDate" content="{date}" />
    <meta name="{'dtb' if daisy3 else 'ncc'}:generator" content="{generator}" />
    <meta name="ncc:charset" content="utf-8" />
    <meta name="ncc:pageFront" content="0" />
    <meta name="ncc:maxPageNormal" content="{pages}" />
    <meta name="ncc:pageNormal" content="{pages}" />
    <meta name="ncc:pageSpecial" content="0" />
    <meta name="ncc:tocItems" content="{len(headingsR)+sum(len(PNs) for PNs in pageNos)}" />
    <meta name="ncc:totalTime" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{math.ceil(totalSecs%60):02d}" />
    <meta name="ncc:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}" />
    <meta name="{'dtb' if daisy3 else 'ncc'}:depth" content="{max(int(h[0][1:]) for h in headingsR)}" />
    <meta name="ncc:files" content="{2+len(headings)*(3 if hasFullText else 2)+len(imageFiles)}" />
  </head>
  {f'<docTitle><text>{title}</text></docTitle>' if daisy3 else ''}
  {f'<docAuthor><text>{creator}</text></docAuthor>' if daisy3 else ''}
  <{'navMap' if daisy3 else 'body'}>"""+''.join((f"""
    <navPoint id="s{s+1}" class="{t[0]}" playOrder="{s+1}">
      <navLabel><text>{t[1]}</text></navLabel>
      <content src="{t[2]+1:04d}.smil#t{t[2]+1}.{t[3]}"/>
    {'</navPoint>'*sum(1 for j in range((1 if s+1==len(headingsR) else int(headingsR[s+1][0][1])),int(t[0][1])+1) if str(j) in ''.join((i[0][1] if i[0][1]>=('1' if s+1==len(headingsR) else headingsR[s+1][0][1]) else '0') for i in reversed(headingsR[:s+1])).split('0',1)[0])}""" if daisy3 else f"""
    <{t[0]} class="{'section' if s or allow_jumps else 'title'}" id="s{s+1}">
      <a href="{t[2]+1:04d}.smil#t{t[2]+1}.{t[3]}">{t[1]}</a>
    </{t[0]}>""") for s,t in enumerate(headingsR))+('</navMap><pageList>' if daisy3 else '')+''.join(''.join((f"""
    <pageTarget class="pagenum" type="normal" value="{N}" id="page{N}" playOrder="{len(headingsR)+sum(len(P) for P in pageNos[:r])+PO+1}">
      <navLabel><text>{N}</text></navLabel>
      <content src="{r+1:04d}.smil#t{r+1}.{after}"/>
    </pageTarget>""" if daisy3 else f"""
    <span class="page-normal" id="page{N}"><a href="{r+1:04d}.smil#t{r+1}.{after}">{N}</a></span>""") for (PO,(after,N)) in enumerate(PNs)) for r,PNs in enumerate(pageNos))+f"""
  </{'pageList' if daisy3 else 'body'}>
</{'ncx' if daisy3 else 'html'}>
""")

def HReduce(headings): return reduce(lambda a,b:a+b,[([(hType,hText,recNoOffset,hOffset) for (hType,hText,hOffset) in i] if type(i)==list else [('h1',i,recNoOffset,0)]) for recNoOffset,i in enumerate(headings)],[])

def normaliseDepth(items):
    if allow_jumps: return items
    curDepth = 0
    for i in range(len(items)):
      if items[i][0].lower().startswith('h'):
        depth = int(items[i][0][1:])
        if depth > curDepth+1: items[i]=(f'h{curDepth+1}',)+items[i][1:]
        curDepth = depth
    return items

def master_smil(headings = [],
                totalSecs = 0):
    headings = HReduce(headings)
    return f"""<?xml version="1.0"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">
<smil>
  <head>
    <meta name="dc:title" content="{deHTML(title)}" />
    <meta name="dc:format" content="Daisy 2.02" />
    <meta name="ncc:generator" content="{generator}" />
    <meta name="ncc:timeInThisSmil" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{totalSecs%60:06.3f}" />
    <layout>
      <region id="textView" />
    </layout>
  </head>
  <body>"""+''.join(f"""
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
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">' if daisy3 else '<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">'}
{'<smil xmlns="http://www.w3.org/2001/SMIL20/">' if daisy3 else '<smil>'}
  <head>
    {'<meta name="dtb:uid" content=""/>' if daisy3 else '<meta name="dc:format" content="Daisy 2.02" />'}
    <meta name="{'dtb' if daisy3 else 'ncc'}:generator" content="{generator}" />
    <meta name="{'dtb' if daisy3 else 'ncc'}:totalElapsedTime" content="{int(totalSecsSoFar/3600)}:{int(totalSecsSoFar/60)%60:02d}:{totalSecsSoFar%60:06.3f}" />""" + ("" if daisy3 else f"""
    <meta name="ncc:timeInThisSmil" content="{int(secsThisRecording/3600)}:{int(secsThisRecording/60)%60:02d}:{secsThisRecording%60:06.3f}" />
    <meta name="title" content="{deHTML(textsAndTimes[1][1])}" />
    <meta name="dc:title" content="{deHTML(textsAndTimes[1][1])}" />
    <layout>
      <region id="textView" />
    </layout>""")+f"""
  </head>
  <body>
    <seq id="sq{recNo}" dur="{secsThisRecording:.3f}s">"""+"".join(f"""
      <par {'' if daisy3 else 'endsync="last" '}id="pr{recNo}.{i//2}">
        <text id="t{recNo}.{i//2}" src="{recNo:04d}.{'xml' if daisy3 else 'htm'}#p{startP+i//2}" />
        {'' if daisy3 else f'<seq id="sq{recNo}.{i//2}a">'}
          <audio src="{recNo:04d}.mp3" clip{'B' if daisy3 else '-b'}egin="{'' if daisy3 else 'npt='}{textsAndTimes[i-1]:.3f}s" clip{'E' if daisy3 else '-e'}nd="{'' if daisy3 else 'npt='}{textsAndTimes[i+1]:.3f}s" id="aud{recNo}.{i//2}" />
        {'' if daisy3 else '</seq>'}
      </par>{''.join(f'<par><text id="t{recNo}.{i//2}.{j}" src="{recNo:04d}.xml#{re.sub(".*"+chr(34)+" id=.","",imageID)}"/></par>' for j,imageID in enumerate(re.findall('<img src="[^"]*" id="[^"]*',textsAndTimes[i][1]))) if daisy3 else ''}""" for i in range(1,len(textsAndTimes),2))+"""
    </seq>
  </body>
</smil>
""")
def deBlank(s): return re.sub("\n *\n","\n",s)

def deHTML(t): return re.sub('<[^>]*>','',t).replace('"','&quot;') # for inclusion in attributes

def package_opf(hasFullText,numRecs,totalSecs):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE package
  PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"
         unique-identifier="uid">
   <metadata>
      <dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
         <dc:Format>ANSI/NISO Z39.86-2005</dc:Format>
         <dc:Language>{lang}</dc:Language>
         <dc:Date>{date}</dc:Date>
         <dc:Publisher>{publisher}</dc:Publisher>
         <dc:Title>{title}</dc:Title>
         <dc:Identifier id="uid"/>
         <dc:Creator>{creator}</dc:Creator>
         <dc:Type>text</dc:Type>
      </dc-metadata>
      <x-metadata>
         <meta name="dtb:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}"/>
         <meta name="dtb:totalTime" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{math.ceil(totalSecs%60):02d}"/>
         <meta name="dtb:multimediaContent" content="audio,text{',image' if imageFiles else ''}"/>
         <meta name="dtb:narrator"
               content="{deHTML(reader)}"/>
         <meta name="dtb:producedDate"
               content="{date}"/>
      </x-metadata>
   </metadata>
   <manifest>
      <item href="package.opf" id="opf" media-type="text/xml"/>"""+''.join(f"""
      <item href="{i:04d}.mp3" id="opf-{i}" media-type="audio/mpeg"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i+1}{u[u.rindex("."):]}" id="opf-{i+numRecs+1}" media-type="image/{u[u.rindex(".")+1:].lower().replace("jpg","jpeg")}"/>""" for i,u in enumerate(imageFiles))+f"""
      <item href="dtbook.2005.basic.css" id="opf-{len(imageFiles)+numRecs+1}" media-type="text/css"/>"""+''.join(f"""
      <item href="{i:04d}.xml" id="opf-{i+len(imageFiles)+numRecs+1}" media-type="application/x-dtbook+xml"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i:04d}.smil" id="{i:04d}" media-type="application/smil+xml"/>""" for i in range(1,numRecs+1))+f"""
      <item href="navigation.ncx"
            id="ncx"
            media-type="application/x-dtbncx+xml"/>
      <item href="text.res"
            id="resource"
            media-type="application/x-dtbresource+xml"/>
   </manifest>
   <spine>"""+"".join(f"""
      <itemref idref="{i:04d}"/>""" for i in range(1,numRecs+1))+"""
   </spine>
</package>
"""

def text_htm(paras,offset=0):
    "paras = [(type,text),(type,text),...], type=h1/p/span, text is xhtml i.e. & use &amp; etc"
    return deBlank(f"""<?xml version="1.0"{' encoding="utf-8"' if daisy3 else ''}?>{'<?xml-stylesheet type="text/css" href="dtbook.2005.basic.css"?>' if daisy3 else ''}
{'<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">' if daisy3 else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-2"' if daisy3 else f'html lang="{lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{lang}">
    <head>
        {f'<meta name="dc:Title" content="{deHTML(title)}"/>' if daisy3 else f'<title>{title}</title>'}
        {'<meta name="dtb:uid" content=""/>' if daisy3 else '<meta content="text/html; charset=utf-8" http-equiv="content-type"/>'}
        <meta name="generator" content="{generator}"/>
    </head>
    <{'book' if daisy3 else 'body'}>
        {f'<frontmatter><doctitle>{title}</doctitle></frontmatter><bodymatter>' if daisy3 else ''}
"""+"\n".join(f"""{''.join(f'<level{n}>' for n in range(min(int(tag[1:]),next(int(paras[p][0][1:]) for p in range(num-1,-1,-1) if paras[p][0].startswith('h'))+1) if any(paras[P][0].startswith('h') for P in range(num-1,-1,-1)) else 1,int(tag[1:])+1)) if daisy3 and tag.startswith('h') else ''}{'<level1>' if daisy3 and not num and not tag.startswith('h') else ''}<{tag} id=\"p{num+offset}\"{' class="sentence"' if tag=='span' else ''}>{re.sub('<img src="[^"]*" [^/]*/>','',text)}{'' if tag=='p' else ('</'+tag+'>')}{'' if tag.startswith('h') or (num+1<len(paras) and paras[num+1][0]=='span') else '</p>'}{'<p><imggroup>' if daisy3 and re.search('<img src="',text) else ''}{''.join(re.findall('<img src="[^"]*" [^/]*/>',text))}{'</imggroup></p>' if daisy3 and re.search('<img src="',text) else ''}{''.join(f'</level{n}>' for n in range(next(int(paras[p][0][1:]) for p in range(num,-1,-1) if paras[p][0].startswith('h')) if any(paras[P][0].startswith('h') for P in range(num,-1,-1)) else 1,0 if num+1==len(paras) else int(paras[num+1][0][1:])-1,-1)) if daisy3 and (num+1==len(paras) or paras[num+1][0].startswith('h')) else ''}""" for num,(tag,text) in enumerate(normaliseDepth(paras)))+f"""
        </{'bodymatter></book' if daisy3 else 'body'}>
</{'dtbook' if daisy3 else 'html'}>
""")

def er_book_info(durations):
    "durations = list of secsThisRecording"
    return """<?xml version="1.0" encoding="utf-8"?>
<book_info>
    <smil_info>"""+"".join(f"""
        <smil nr="{s}" Name="{s+1:04d}.smil" dur="{d:f}"/>""" for s,d in enumerate(durations))+"""
    </smil_info>
</book_info>
"""

d3css = """/* Simplified from Z39.86 committee CSS, removed non-dark background (allow custom) */
dtbook { display:block; width: 100% }
head { display: none }
book {
 display: block;
 font-family: arial, verdana, sans-serif;
 line-height: 1.5em;
 margin-top: 4em;
 margin-bottom: 2em;
 margin-left: 6em;
 margin-right: 6em;
}
bodymatter {
  display: block; margin-top: 1em; margin-bottom: 1em }
h1, h2, h3, h4, h5, h6 {
  display: block; font-weight: bold; margin-bottom: 0.5em }
h1 { font-size: 1.7em; margin-top: 1.5em }
h2 { font-size: 1.5em; margin-top: 1.2em }
h3 { font-size: 1.4em; margin-top: 1.0em }
h4 { font-size: 1.3em; margin-top: 1.0em }
h5 { font-size: 1.2em; margin-top: 1.0em }
h6 { margin-top: 1.0em }
p { display: block; margin-top: 0.7em }
a { display: inline; text-decoration: underline }
em { display: inline; font-style: italic }
strong { display: inline; font-weight: bold }
span { display: inline; }
"""
textres = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE resources
  PUBLIC "-//NISO//DTD resource 2005-1//EN" "http://www.daisy.org/z3986/2005/resource-2005-1.dtd">
<resources xmlns="http://www.daisy.org/z3986/2005/resource/" version="2005-1"><!-- SKIPPABLE NCX --><scope nsuri="http://www.daisy.org/z3986/2005/ncx/"><nodeSet id="ns001" select="//smilCustomTest[@bookStruct='LINE_NUMBER']"><resource xml:lang="en" id="r001"><text>Row</text></resource></nodeSet><nodeSet id="ns002" select="//smilCustomTest[@bookStruct='NOTE']"><resource xml:lang="en" id="r002"><text>Note</text></resource></nodeSet><nodeSet id="ns003" select="//smilCustomTest[@bookStruct='NOTE_REFERENCE']"><resource xml:lang="en" id="r003"><text>Note reference</text></resource></nodeSet><nodeSet id="ns004" select="//smilCustomTest[@bookStruct='ANNOTATION']"><resource xml:lang="en" id="r004"><text>Annotation</text></resource></nodeSet><nodeSet id="ns005" select="//smilCustomTest[@id='annoref']"><resource xml:lang="en" id="r005"><text>Annotation reference</text></resource></nodeSet><nodeSet id="ns006" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']"><resource xml:lang="en" id="r006"><text>Page</text></resource></nodeSet><nodeSet id="ns007" select="//smilCustomTest[@bookStruct='OPTIONAL_SIDEBAR']"><resource xml:lang="en" id="r007"><text>Optional sidebar</text></resource></nodeSet><nodeSet id="ns008" select="//smilCustomTest[@bookStruct='OPTIONAL_PRODUCER_NOTE']"><resource xml:lang="en" id="r008"><text>Optional producer note</text></resource></nodeSet></scope><!-- ESCAPABLE SMIL --><scope nsuri="http://www.w3.org/2001/SMIL20/"><nodeSet id="esns001" select="//seq[@bookStruct='line']"><resource xml:lang="en" id="esr001"><text>Row</text></resource></nodeSet><nodeSet id="esns002" select="//seq[@class='note']"><resource xml:lang="en" id="esr002"><text>Note</text></resource></nodeSet><nodeSet id="esns003" select="//seq[@class='noteref']"><resource xml:lang="en" id="esr003"><text>Note reference</text></resource></nodeSet><nodeSet id="esns004" select="//seq[@class='annotation']"><resource xml:lang="en" id="esr004"><text>Annotation</text></resource></nodeSet><nodeSet id="esns005" select="//seq[@class='annoref']"><resource xml:lang="en" id="esr005"><text>Annotation reference</text></resource></nodeSet><nodeSet id="esns006" select="//seq[@class='pagenum']"><resource xml:lang="en" id="esr006"><text>Page</text></resource></nodeSet><nodeSet id="esns007" select="//seq[@class='sidebar']"><resource xml:lang="en" id="esr007"><text>Optional sidebar</text></resource></nodeSet><nodeSet id="esns008" select="//seq[@class='prodnote']"><resource xml:lang="en" id="esr008"><text>Optional producer note</text></resource></nodeSet></scope><!-- ESCAPABLE DTBOOK --><scope nsuri="http://www.daisy.org/z3986/2005/dtbook/"><nodeSet id="ns009" select="//annotation"><resource xml:lang="en" id="r009"><text>Annotation</text></resource></nodeSet><nodeSet id="ns010" select="//blockquote"><resource xml:lang="en" id="r010"><text>Quote</text></resource></nodeSet><nodeSet id="ns011" select="//code"><resource xml:lang="en" id="r011"><text>Code</text></resource></nodeSet><nodeSet id="ns012" select="//list"><resource xml:lang="en" id="r012"><text>List</text></resource></nodeSet><nodeSet id="ns018" select="//note"><resource xml:lang="en" id="r018"><text>Note</text></resource></nodeSet><nodeSet id="ns013" select="//poem"><resource xml:lang="en" id="r013"><text>Poem</text></resource></nodeSet><nodeSet id="ns0014" select="//prodnote[@render='optional']"><resource xml:lang="en" id="r014"><text>Optional producer note</text></resource></nodeSet><nodeSet id="ns015" select="//sidebar[@render='optional']"><resource xml:lang="en" id="r015"><text>Optional sidebar</text></resource></nodeSet><nodeSet id="ns016" select="//table"><resource xml:lang="en" id="r016"><text>Table</text></resource></nodeSet><nodeSet id="ns017" select="//tr"><resource xml:lang="en" id="r017"><text>Table row</text></resource></nodeSet></scope></resources>"""

if __name__ == "__main__": anemone()
