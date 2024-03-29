#!/usr/bin/env python3
"""
Anemone 1.31 (http://ssb22.user.srcf.net/anemone)
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
    You can also specify a JSON dictionary instead
    of the name of a JSON file, and/or an HTML
    string instead of the name of an HTML file
    (this can also be done on the command line
    with careful quoting).
    If you do not give this function any arguments
    it will look at the system command line."""
    
    R=Run(*[(json.dumps(f) if type(f)==dict else f) for f in files],**options)
    if R.mp3_recode: check_we_got_LAME()
    write_all(R,get_texts(R))

def populate_argument_parser(args): # INTERNAL
    """Calls add_argument on args, with the names
    of all the command-line options, which are
    also options for anemone(), and help text."""
    # TODO: could also run this with an object that takes the help text we give it and puts it into the module documentation?
    
    args.add_argument("files",metavar="file",nargs="+",help="file name of: an MP3 recording, a text file containing its title (if no full text), a JSON file containing its time markers, an XHTML file containing its full text, or the output ZIP file.  Only one output file may be specified, but any number of the other files can be included; URLs may be given if they are to be fetched (HTML assumed if no extension).  If only MP3 files are given then titles are taken from their filenames.  You may also specify @filename where filename contains a list of files one per line.")
    args.add_argument("--lang",default="en",help="the ISO 639 language code of the publication (defaults to en for English)")
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
    args.add_argument("--cache",default="cache",help="path name for the URL-fetching cache (default 'cache' in the current directory)")
    args.add_argument("--reload",dest="refetch",action="store_true",help="if images etc have already been fetched from URLs, fetch them again without If-Modified-Since")
    args.add_argument("--delay",default=0,help="minimum number of seconds between URL fetches (default none)")
    args.add_argument("--user-agent",default=f"Mozilla/5.0 (compatible, {' '.join(generator.split()[:2])})",help="User-Agent string to send for URL fetches")
    args.add_argument("--daisy3",action="store_true",help="Use the Daisy 3 format (ANSI/NISO Z39.86) instead of the Daisy 2.02 format.  This may require more modern reader software, and Anemone does not yet support Daisy 3 only features like tables in the text.")
    args.add_argument("--mp3-recode",action="store_true",help="re-code the MP3 files to ensure they are constant bitrate and more likely to work with the more limited DAISY-reading programs like FSReader 3 (this option requires LAME)")
    args.add_argument("--allow-jumps",action="store_true",help="Allow jumps in heading levels e.g. h1 to h3 if the input HTML does it.  This seems OK on modern readers but might cause older reading devices to give an error.  Without this option, headings are promoted where necessary to ensure only incremental depth increase.") # might cause older reading devices to give an error: and is also flagged up by the validator

generator=__doc__.strip().split('\n')[0] # string we use to identify ourselves in HTTP requests and in Daisy files

def get_argument_parser(): # INTERNAL
    "Creates and populates our argument parser"
    from argparse import ArgumentParser
    args = ArgumentParser(prog="anemone",description=generator,fromfile_prefix_chars='@')
    populate_argument_parser(args)
    return args

import time, sys, os, re, json, math, time
from functools import reduce
from subprocess import run, PIPE
from zipfile import ZipFile, ZIP_DEFLATED
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.parse import unquote
from pathlib import Path # Python 3.5+
from shutil import which

def error(m): # INTERNAL
    """Main error handler.  If we're running as an
    application, print message and error-exit.  If
    we're a module, raise an exception instead."""
    
    if __name__=="__main__": sys.stderr.write(f"Error: {m}\n"),sys.exit(1)
    else: raise AnemoneError(str(m))
class AnemoneError(Exception): pass

try: from mutagen.mp3 import MP3
except ImportError: error("Anemone needs the Mutagen library to determine MP3 play lengths.\nPlease do: pip install mutagen")

class Run(): # INTERNAL
  """The parameters we need for an Anemone run.
  Constructor can either parse args from the
  command line, or from anemone() caller."""
  def __init__(R,*inFiles,**kwargs):
    # I know the convention is "self" but I am
    # working in giant print and my screen real
    # estate is important, that's why I was using
    # global variables before... 1 letter please..
    R.recordingFiles,R.jsonData = [],[]
    R.textFiles,R.htmlData = [],[]
    R.imageFiles,R.outputFile = [],None
    if inFiles: R.__dict__.update(get_argument_parser().parse_args(list(inFiles)+['--'+k.replace('_','-') for k,v in kwargs.items() if v==True]+[a for k,v in kwargs.items() for a in ['--'+k.replace('_','-'),str(v)] if not v==True and not v==False and not v==None]).__dict__) # so flag=False is ignored (as we default to False), and option=None means use the default
    else: R.__dict__.update(get_argument_parser().parse_args().__dict__)
    for f in R.files:
        f = f.strip()
        if f.endswith(f"{os.extsep}zip"):
            if R.outputFile: error(f"Only one {os.extsep}zip output file may be specified")
            R.outputFile = f ; continue
        if re.match("https?://",f): f=fetch(f,True,R.cache,R.refresh,R.refetch,R.delay,R.user_agent)
        if f.startswith('{') and f.endswith('}'):
            R.jsonData.append(json.loads(f))
            continue # don't treat as a file
        elif f.startswith('<') and f.endswith('>'):
            R.htmlData.append(f) ; continue
        elif not os.path.exists(f): error(f"File not found: {f}")
        if f.endswith(f"{os.extsep}mp3") or f.endswith(f"{os.extsep}wav"):
            if f.endswith(f"{os.extsep}wav") and not R.mp3_recode: error("wav input requires mp3 recode to be set")
            R.recordingFiles.append(f)
        elif f.endswith(f"{os.extsep}json"): R.jsonData.append(json.load(open(f,encoding="utf-8")))
        elif f.endswith(f"{os.extsep}txt"):
            R.textFiles.append(f)
        elif f.endswith(f"{os.extsep}html") or not os.extsep in f.rsplit(os.sep,1)[-1]:
            R.htmlData.append(open(f,encoding="utf-8").read())
        else: error(f"Can't handle '{f}'")
    if not R.recordingFiles: error("Creating DAISY files without audio is not yet implemented")
    if R.htmlData and not R.jsonData: error("Full text without time markers is not yet implemented")
    if R.jsonData and not R.htmlData: error("Time markers without full text is not implemented")
    if R.htmlData and R.textFiles: error("Combining full text with title-only text files is not yet implemented.  Please specify full text for everything or just titles for everything, not both.")
    if R.jsonData and not len(R.recordingFiles)==len(R.jsonData): error(f"If JSON marker files are specified, there must be exactly one JSON file for each recording file.  We got f{len(R.jsonData)} JSON files and f{len(R.recordingFiles)} recording files.")
    if R.textFiles and not len(R.recordingFiles)==len(R.textFiles): error(f"If text files are specified, there must be exactly one text file for each recording file.  We got f{len(R.textFiles)} text files and f{len(R.recordingFiles)} recording files.")
    if R.htmlData and not len(R.recordingFiles)==len(R.htmlData): error(f"If HTML documents are specified, there must be exactly one HTML document for each recording.  We got f{len(R.htmlData)} HTML documents and f{len(R.recordingFiles)} recordings.")
    if not R.outputFile: R.outputFile=f"output_daisy{os.extsep}zip"
    if not R.title: R.title=R.outputFile.replace(f"{os.extsep}zip","").replace("_daisy","")

def check_we_got_LAME(): # INTERNAL
    if which('lame'): return
    if sys.platform=='win32':
        os.environ["PATH"] += r";C:\Program Files (x86)\Lame for Audacity;C:\Program Files\Lame for Audacity"
        if which('lame'): return
    error(f"Anemone requires the LAME program to recode MP3s.\nPlease {'run the exe installer from lame.buanzo.org' if sys.platform=='win32' else 'install lame'} and try again.")

def get_texts(R): # INTERNAL
    """Gets the text markup required for the run,
    extracting it from HTML (guided by JSON IDs)
    if we need to do that."""
    
    if R.textFiles: return [open(f,encoding="utf-8").read().strip() for f in R.textFiles] # section titles only, from text files
    elif not R.htmlData: return [r[:-len(f"{os.extsep}mp3")] for r in R.recordingFiles] # section titles only, from MP3 filenames
    recordingTexts = []
    for h,j in zip(R.htmlData,R.jsonData):
        markers = j['markers']
        want_pids = [jsonAttr(m,"id") for m in markers]
        id_to_content = {}
        pageNos = []
        allowedInlineTags=['br'] # Dolphin EasyReader does not render <strong> and <em>, and constructs like "(<em>Publication name</em>" result in incorrect space after "(" so best leave it out
        assert not 'rt' in allowedInlineTags, "if allowing this, need to revise rt suppression logic" # and would have to rely on rp parens for most readers, so if a text has a LOT of ruby it could get quite unreadable
        class PidsExtractor(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.addTo = None
                self.suppress = 0
                self.imgsMaybeAdd = None
                self.pageNoGoesAfter = 0
                self.theStartTag = None
            def handle_starttag(self,tag,attrs):
                tag = tagRewrite.get(tag,tag)
                attrs = dict(attrs)
                imgURL = attrs.get(R.image_attribute,None)
                if imgURL and re.match("https?://.*[.][^/]*$",imgURL) and not (self.addTo==None and self.imgsMaybeAdd==None):
                    # TODO: might want to check attrs.get("alt",""), but DAISY3 standard does not list alt as a valid attribute for img, so we'd have to put it after with br etc (changing text_htm) and we don't know if it's in the audio or not: probably best just to leave it and rely on there being a separate caption with ID if it's in the audio
                    img = f'<img src="{(R.imageFiles.index(imgURL) if imgURL in R.imageFiles else len(R.imageFiles))+1}{imgURL[imgURL.rindex("."):]}" {f"""id="i{R.imageFiles.index(imgURL) if imgURL in R.imageFiles else len(R.imageFiles)}" """ if R.daisy3 else ""}/>' # will be moved after paragraph by text_htm
                    if not imgURL in R.imageFiles:
                        R.imageFiles.append(imgURL)
                    if self.addTo==None: self.imgsMaybeAdd.append(img)
                    else: self.addTo.append(img)
                pageNo = attrs.get(R.page_attribute,None)
                if pageNo:
                    pageNos.append((self.pageNoGoesAfter,pageNo))
                if attrs.get(R.marker_attribute,None) in want_pids:
                    self.theStartTag = tag
                    self.tagDepth = 0
                    a = attrs[R.marker_attribute]
                    self.pageNoGoesAfter = want_pids.index(a)
                    id_to_content[a] = ((tag if re.match('h[1-6]$',tag) or tag=='span' else 'p'),[])
                    if self.imgsMaybeAdd: self.imgsMaybeAddTo += self.imgsMaybeAdd # and imgsMaybeAdd will be reset to [] when this element is closed
                    self.addTo = id_to_content[a][1]
                    return
                if tag==self.theStartTag and not tag=="p": # can nest
                    self.tagDepth += 1
                if not self.addTo==None and tag in allowedInlineTags: self.addTo.append(f'<{tag}>')
                elif not self.addTo==None and tag=='a': self.lastAStart = len(self.addTo)
                elif tag=='rt': self.suppress += 1
            def handle_endtag(self,tag):
                tag = tagRewrite.get(tag,tag)
                if self.suppress and tag=='rt': self.suppress -= 1
                elif not self.addTo==None:
                    if tag==self.theStartTag and self.tagDepth == 0:
                        self.highestImage,self.imgsMaybeAddTo, self.imgsMaybeAdd = len(R.imageFiles),self.addTo,[] # if we find any images (not in an id'd element) after the end of the id'd element, we might want to add them in with any inside it, but only if there's another id'd element after them i.e. not if they're just random decoration at the bottom of the page
                        self.addTo = None
                    elif tag in allowedInlineTags: self.addTo.append(f'</{tag}>')
                    elif tag=="a" and re.match('[!-.:-~]$',"".join(self.addTo[self.lastAStart:]).strip()): del self.addTo[self.lastAStart:] # remove single-character link, probably to footnote (we won't know if it's in the audio or not, we're not supporting jumps and the symbols might need normalising) but do allow numbers (might be paragraph numbers etc) and non-ASCII (might be single-character CJK word)
                    if tag==self.theStartTag and self.tagDepth: self.tagDepth -= 1
                if tag=='html' and self.imgsMaybeAdd and hasattr(self,'highestImage'): del R.imageFiles[self.highestImage:] # do not include ones that were only in imgsMaybeAdd at the end of the page (and not also elsewhere)
            def handle_data(self,data):
                if not self.addTo==None and not self.suppress:
                    self.addTo.append(data.replace('&','&amp;').replace('<','&lt;'))
        PidsExtractor().feed(h)
        rTxt = []
        for i in range(len(markers)):
            if i: rTxt.append(parseTime(jsonAttr(markers[i],"time")))
            if want_pids[i] in id_to_content:
                tag,content = id_to_content[want_pids[i]]
                content = ''.join(content).strip()
                rTxt.append((tag,re.sub('( *</?br> *)+','<br />',content))) # (allow line breaks inside paragraphs, in case any in mid-"sentence", but collapse them because readers typically add extra space to each)
            else:
                sys.stderr.write(f"Warning: JSON {len(recordingTexts)+1} marker {i+1} marks paragraph ID {want_pids[i]} which is not present in HTML {len(recordingTexts)+1}.  Anemone will make this a blank paragraph.\n")
                rTxt.append(('p',''))
        recordingTexts.append((rTxt,pageNos))
    return recordingTexts

tagRewrite = { # used by get_texts
    'legend':'h3', # used in fieldset
}

def jsonAttr(d,suffix):
    """Returns the value of a dictionary key whose
    name ends with the given lower-case suffix
    (after converting names to lower case), after
    checking exactly one key does this.  Used for
    checking JSON for things like paragraphId if
    you know only that it ends with 'Id'"""
    
    keys = [k for k in d.keys() if k.lower().endswith(suffix)]
    if not keys: error(f"No *{suffix} in {repr(keys)}")
    if len(keys)>1: error(f"More than one *{suffix} in {repr(keys)}")
    return str(d[keys[0]])

def parseTime(t):
    """Parses a string containing seconds,
    minutes:seconds or hours:minutes:seconds
    (decimal fractions of seconds allowed),
    and returns floating-point seconds"""
    
    tot = 0.0 ; mul = 1
    for u in reversed(t.split(':')):
        tot += float(u)*mul ; mul *= 60
    return tot

def write_all(R,recordingTexts): # INTERNAL
    "each item is: 1 text for section title of whole recording, or ([(type,text),time,(type,text),time,(type,text)],[(goesBefore,pageNo),...])"
    assert len(R.recordingFiles) == len(recordingTexts)
    headings = getHeadings(recordingTexts)
    hasFullText = any(type(t)==tuple for t in recordingTexts)
    if R.mp3_recode: # parallelise lame if possible
        executor = ThreadPoolExecutor(max_workers=cpu_count())
        recordings=[executor.submit(recodeMP3,f) for f in R.recordingFiles]
    z = ZipFile(R.outputFile,"w",ZIP_DEFLATED,False)
    def D(s): return s.replace("\n","\r\n") # in case old readers require DOS line endings
    if hasFullText: z.writestr("0000.txt",D(f"""
    If you're reading this, it likely means your
    operating system has unpacked the ZIP file
    and is showing you its contents.  While it
    is possible to extract recordings and text
    this way, it is better to send the whole ZIP
    to a DAISY reader so that its recordings and
    text can be connected with each other.  If
    you are using EasyReader on a mobile device,
    close this file and navigate up a level to
    find the original ZIP file so it can be sent
    to EasyReader as a whole.  Some other DAISY
    readers need to be pointed at the {'OPF' if R.daisy3 else 'NCC'} file
    instead, or at the whole directory/folder.
""")) # TODO: message in other languages?
    # (it's iOS users that need the above, apparently.  Can't DAISY have a non-ZIP extension so Apple systems don't automatically unpack it?  but we do need to manually unpack if writing to a CD-ROM for old devices.  Can't Apple look at some kind of embedded "don't auto-unpack this zip" request?)
    secsSoFar = 0
    durations = [] ; pSoFar = 0
    for recNo in range(1,len(recordingTexts)+1):
        secsThisRecording = MP3(R.recordingFiles[recNo-1]).info.length
        rTxt = recordingTexts[recNo-1]
        durations.append(secsThisRecording)
        if R.mp3_recode: sys.stderr.write(f"Adding {recNo:04d}.mp3..."),sys.stderr.flush()
        z.writestr(f"{recNo:04d}.mp3",recordings[recNo-1].result() if R.mp3_recode else open(R.recordingFiles[recNo-1],'rb').read())
        if R.mp3_recode: sys.stderr.write(" done\n")
        z.writestr(f'{recNo:04d}.smil',D(section_smil(R,recNo,secsSoFar,secsThisRecording,pSoFar,rTxt[0] if type(rTxt)==tuple else rTxt)))
        z.writestr(f'{recNo:04d}.{"xml" if R.daisy3 else "htm"}',D(text_htm(R,(rTxt[0][::2] if type(rTxt)==tuple else [('h1',rTxt)]),pSoFar)))
        secsSoFar += secsThisRecording
        pSoFar += (1+len(rTxt[0])//2 if type(rTxt)==tuple else 1)
    for n,u in enumerate(R.imageFiles): z.writestr(f'{n+1}{u[u.rindex("."):]}',fetch(u,False,R.cache,R.refresh,R.refetch,R.delay,R.user_agent))
    if R.daisy3:
        z.writestr('dtbook.2005.basic.css',D(d3css))
        z.writestr('package.opf',D(package_opf(R,hasFullText,len(recordingTexts),secsSoFar)))
        z.writestr('text.res',D(textres))
    else: z.writestr('master.smil',D(master_smil(R,headings,secsSoFar)))
    z.writestr('navigation.ncx' if R.daisy3 else 'ncc.html',D(ncc_html(R,headings,hasFullText,secsSoFar,[(t[1] if type(t)==tuple else []) for t in recordingTexts])))
    if not R.daisy3: z.writestr('er_book_info.xml',D(er_book_info(durations))) # not DAISY standard but EasyReader can use this
    z.close()
    sys.stderr.write(f"Wrote {R.outputFile}\n")

def getHeadings(recordingTexts): # INTERNAL
    ret = []
    for txtNo,t in enumerate(recordingTexts):
        if not type(t)==tuple: # title only
            ret.append(t) ; continue
        textsAndTimes,pages = t ; first = None
        chap = []
        for v,u in enumerate(textsAndTimes):
            if not type(u)==tuple: continue # time
            tag,text = u
            if first==None: first = v
            if not tag.startswith('h'):
                continue
            if v//2 - 1 == first//2 and not textsAndTimes[first][0].startswith('h'): # chapter starts with non-heading followed by heading: check the non-heading for "Chapter N" etc
                nums=re.findall("[1-9][0-9]*",textsAndTimes[first][1])
                if len(nums)==1:
                    text=f"{nums[0]}: {text}" # for TOC
                    textsAndTimes[v-1] = (textsAndTimes[first-1] if first else 0) # for audio jump-navigation to include the "Chapter N" (TODO: option to merge the in-chapter text instead, so "Chapter N" appears as part of the heading, not scrolled past quickly?)
            chap.append((tag,re.sub('<img src.*?/>','',text),v//2))
        if not chap:
            # Chapter with no heading.
            # This'll be a problem, as master_smil and ncc_html need headings to refer to the chapter at all.  (Well, ncc_html can also do it by page number if we have them, but we haven't tested all DAISY readers with page number only navigation, and what if we don't even have page numbers?)
            # So let's see if we can at least get a chapter number.
            if not first==None: nums=re.findall("[1-9][0-9]*",textsAndTimes[first][1])
            else:
                sys.stderr.write(f"WARNING: Chapter {txtNo+1} is completely blank!  (Is {'--marker-attribute' if __name__=='__main__' else 'marker_attribute'} set correctly?)\n")
                nums = []
            chap.append(('h1',nums[0] if len(nums)==1 and not nums[0]=="1" else str(txtNo+1),first//2))
        ret.append(chap)
    return ret

def recodeMP3(f):
    """Takes an MP3 or WAV filename, re-codes it
    as suitable for DAISY, and returns the bytes
    of new MP3 data for putting into DAISY ZIP"""
    if f.endswith("wav"): return run(["lame","--quiet",f,"-m","m","--resample","44.1","-b","64","-q","0","-o","-"],check=True,stdout=PIPE).stdout # TODO: ensure lame doesn't take any headers or images embedded in the wav (if it does, we might need first to convert to headerless pcm as below)
    # If that didn't return, we have MP3 input.
    # It seems broken players like FSReader can get timing wrong if mp3 contains
    # too many tags at the start (e.g. images).
    # eyed3 clear() won't help: it zeros out bytes without changing indices.
    # To ensure everything is removed, better decode to raw PCM and re-encode :-(
    pcm = f[:-3]+"pcm" # instead of .mp3
    m = re.search(b'(?s)([0-9]+) kHz, ([0-9]+).*?([0-9]+) bit',run(["lame","-t","--decode",f,"-o",pcm],check=True,stdout=PIPE,stderr=PIPE).stderr) # hope nobody disabled --decode when building LAME (is OK on lame.buanzo.org EXEs)
    if not m: error("lame did not give expected format for frequency, channels and bits output")
    mp3bytes = run(["lame","--quiet","-r","-s",m.group(1).decode('latin1')]+(['-a'] if m.group(2)==b'2' else [])+['-m','m','--bitwidth',m.group(3).decode('latin1'),pcm,"--resample","44.1","-b","64","-q","0","-o","-"],check=True,stdout=PIPE).stdout
    os.remove(pcm) ; return mp3bytes

def fetch(url,
          returnFilename=False, # if True, returns the cached filename we saved it in, if False, return the actual data
          cache = "cache", # the cache directory
          refresh = False, # if True, send If-Modified-Since request if we have a cached item
          refetch = False, # if True, reloads
          delay = 0, # between fetches (tracked globally)
          user_agent = None):
    """Fetches a URL, with delay and cache options
    (see comments on parameters)"""
    fn = re.sub('[%&?@*#{}<>!:+`=|$]','',cache+os.sep+unquote(re.sub('.*?://','',url)).replace('/',os.sep)) # these characters need to be removed on Windows's filesystem; TODO: store original URL somewhere just in case some misguided webmaster puts two identical URLs modulo those characters??
    if fn.endswith(os.sep): fn += "index.html"
    fn = os.sep.join(f.replace('.',os.extsep) for f in fn.split(os.sep)) # just in case we're on RISC OS (not tested)
    fnExc = fn+os.extsep+"exception"
    ifModSince = None
    if os.path.exists(fn):
        if refetch: pass # ignore already dl'd
        elif refresh:
            ifModSince=os.stat(fn).st_mtime
        elif returnFilename: return fn
        else: return open(fn,'rb').read()
    elif os.path.exists(fnExc) and not refetch and not refresh: raise HTTPError("",int(open(fnExc).read()),"HTTP error on last fetch",{},None) # useful especially if a wrapper script is using our fetch() for multiple chapters and stopping on a 404
    sys.stderr.write("Fetching "+url+"...")
    sys.stderr.flush()
    if os.sep in fn: Path(fn[:fn.rindex(os.sep)]).mkdir(parents=True,exist_ok=True)
    global _last_urlopen_time
    try: _last_urlopen_time
    except: _last_urlopen_time = 0
    if delay: time.sleep(min(0,_last_urlopen_time+delay-time.time()))
    headers = {"User-Agent":user_agent} if user_agent else {}
    if ifModSince:
        t = time.gmtime(ifModSince)
        headers["If-Modified-Since"]=f"{'Mon Tue Wed Thu Fri Sat Sun'.split()[t.tm_wday]}, {t.tm_mday} {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[t.tm_mon-1]} {t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d} GMT"
    try: dat = urlopen(Request(url,headers=headers)).read()
    except HTTPError as e:
        _last_urlopen_time = time.time()
        if e.getcode()==304:
            sys.stderr.write(" no new data\n")
            if returnFilename: return fn
            else: return open(fn,'rb').read()
        else:
            open(fnExc,"w").write(str(e.getcode())) ; raise
    _last_urlopen_time = time.time()
    sys.stderr.write(" saved\n")
    open(fn,'wb').write(dat)
    if returnFilename: return fn
    else: return dat

def ncc_html(R, headings = [],
             hasFullText = False,
             totalSecs = 0, pageNos=[]):# INTERNAL
    """Returns the Navigation Control Centre (NCC)
    pageNos is [[(goesAfter,pageNo),...],...]"""
    numPages = sum(len(l) for l in pageNos)
    maxPageNo = max((max((int(N) for after,N in PNs),default=0) for PNs in pageNos),default=0)
    # TODO: we assume all pages are 'normal' pages
    # (not 'front' pages in Roman letters etc)
    headingsR = normaliseDepth(R,HReduce(headings)) # (hType,hText,recNo,textNo)
    if not R.date: R.date = "%d-%02d-%02d" % time.localtime()[:3]
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">' if R.daisy3 else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"' if R.daisy3 else f'html lang="{R.lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{R.lang}">
  <head>
    {'<meta name="dtb:uid" content=""/>' if R.daisy3 else '<meta content="text/html; charset=utf-8" http-equiv="Content-type" />'}
    {f'<meta name="dtb:totalPageCount" content="{numPages}" />' if R.daisy3 else ''}
    {f'<meta name="dtb:maxPageNumber" content="{maxPageNo}" />' if R.daisy3 else ''}
    {'' if R.daisy3 else f'<title>{R.title}</title>'}
    <meta name="dc:creator" content="{R.creator}" />
    <meta name="dc:date" content="{R.date}" scheme="yyyy-mm-dd" />
    <meta name="dc:language" content="{R.lang}" scheme="ISO 639" />
    <meta name="dc:publisher" content="{deHTML(R.publisher)}" />
    <meta name="dc:title" content="{deHTML(R.title)}" />
    <meta name="dc:type" content="text" />
    <meta name="dc:identifier" content="{R.url}" />
    <meta name="dc:format" content="{'ANSI/NISO Z39.86-2005' if R.daisy3 else 'Daisy 2.02'}" />
    <meta name="ncc:narrator" content="{R.reader}" />
    <meta name="ncc:producedDate" content="{R.date}" />
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:generator" content="{generator}" />
    <meta name="ncc:charset" content="utf-8" />
    <meta name="ncc:pageFront" content="0" />
    <meta name="ncc:maxPageNormal" content="{maxPageNo}" />
    <meta name="ncc:pageNormal" content="{numPages}" />
    <meta name="ncc:pageSpecial" content="0" />
    <meta name="ncc:tocItems" content="{len(headingsR)+sum(len(PNs) for PNs in pageNos)}" />
    <meta name="ncc:totalTime" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{math.ceil(totalSecs%60):02d}" />
    <meta name="ncc:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}" />
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:depth" content="{max(int(h[0][1:]) for h in headingsR)}" />
    <meta name="ncc:files" content="{2+len(headings)*(3 if hasFullText else 2)+len(R.imageFiles)}" />
  </head>
  {f'<docTitle><text>{R.title}</text></docTitle>' if R.daisy3 else ''}
  {f'<docAuthor><text>{R.creator}</text></docAuthor>' if R.daisy3 else ''}
  <{'navMap' if R.daisy3 else 'body'}>"""+''.join((f"""
    <navPoint id="s{s+1}" class="{t[0]}" playOrder="{s+1}">
      <navLabel><text>{t[1]}</text></navLabel>
      <content src="{t[2]+1:04d}.smil#t{t[2]+1}.{t[3]}"/>
    {'</navPoint>'*sum(1 for j in range((1 if s+1==len(headingsR) else int(headingsR[s+1][0][1])),int(t[0][1])+1) if str(j) in ''.join((i[0][1] if i[0][1]>=('1' if s+1==len(headingsR) else headingsR[s+1][0][1]) else '0') for i in reversed(headingsR[:s+1])).split('0',1)[0])}""" if R.daisy3 else ''.join(f"""
    <span class="page-normal" id="page{N}"><a href="{r+1:04d}.smil#t{r+1}.{after}">{N}</a></span>""" for r,PNs in enumerate(pageNos) for (PO,(after,N)) in enumerate(PNs) if (r,after)<=t[2:4] and (not s or (r,after)>headingsR[s-1][2:4]))+f"""
    <{t[0]} class="{'section' if s or R.allow_jumps else 'title'}" id="s{s+1}">
      <a href="{t[2]+1:04d}.smil#t{t[2]+1}.{t[3]}">{t[1]}</a>
    </{t[0]}>""") for s,t in enumerate(headingsR))+('</navMap><pageList>'+''.join(f"""
    <pageTarget class="pagenum" type="normal" value="{N}" id="page{N}" playOrder="{len(headingsR)+sum(len(P) for P in pageNos[:r])+PO+1}">
      <navLabel><text>{N}</text></navLabel>
      <content src="{r+1:04d}.smil#t{r+1}.{after}"/>
    </pageTarget>""" for r,PNs in enumerate(pageNos) for (PO,(after,N)) in enumerate(PNs))+f"""
  </pageList>
</ncx>""" if R.daisy3 else """
  </body>
</html>"""))

def HReduce(headings): return reduce(lambda a,b:a+b,[([(hType,hText,recNo,textNo) for (hType,hText,textNo) in i] if type(i)==list else [('h1',i,recNo,0)]) for recNo,i in enumerate(headings)],[]) # INTERNAL

def normaliseDepth(R,items): # INTERNAL
    "Ensure that heading items' depth conforms to DAISY standard"
    if R.allow_jumps: return items
    curDepth = 0
    for i in range(len(items)):
      if items[i][0].lower().startswith('h'):
        depth = int(items[i][0][1:])
        if depth > curDepth+1: items[i]=(f'h{curDepth+1}',)+items[i][1:]
        curDepth = depth
    return items

def master_smil(R,headings = [],
                totalSecs = 0): # INTERNAL
    "Compile the master smil for a DAISY file"
    headings = HReduce(headings)
    return f"""<?xml version="1.0"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">
<smil>
  <head>
    <meta name="dc:title" content="{deHTML(R.title)}" />
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

def section_smil(R, recNo=1,
                 totalSecsSoFar=0,
                 secsThisRecording=0,
                 startP=0,
                 textsAndTimes=[]): # INTERNAL
    "Compile a section SMIL for a DAISY file"
    if not type(textsAndTimes)==list: textsAndTimes=[textsAndTimes]
    textsAndTimes = [0]+textsAndTimes+[secsThisRecording]
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">' if R.daisy3 else '<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">'}
{'<smil xmlns="http://www.w3.org/2001/SMIL20/">' if R.daisy3 else '<smil>'}
  <head>
    {'<meta name="dtb:uid" content=""/>' if R.daisy3 else '<meta name="dc:format" content="Daisy 2.02" />'}
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:generator" content="{generator}" />
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:totalElapsedTime" content="{int(totalSecsSoFar/3600)}:{int(totalSecsSoFar/60)%60:02d}:{totalSecsSoFar%60:06.3f}" />""" + ("" if R.daisy3 else f"""
    <meta name="ncc:timeInThisSmil" content="{int(secsThisRecording/3600)}:{int(secsThisRecording/60)%60:02d}:{secsThisRecording%60:06.3f}" />
    <meta name="title" content="{deHTML(textsAndTimes[1][1])}" />
    <meta name="dc:title" content="{deHTML(textsAndTimes[1][1])}" />
    <layout>
      <region id="textView" />
    </layout>""")+f"""
  </head>
  <body>
    <seq id="sq{recNo}" dur="{secsThisRecording:.3f}s">"""+"".join(f"""
      <par {'' if R.daisy3 else 'endsync="last" '}id="pr{recNo}.{i//2}">
        <text id="t{recNo}.{i//2}" src="{recNo:04d}.{'xml' if R.daisy3 else 'htm'}#p{startP+i//2}" />
        {'' if R.daisy3 or textsAndTimes[i-1]==textsAndTimes[i+1] else f'<seq id="sq{recNo}.{i//2}a">'}
          {'' if textsAndTimes[i-1]==textsAndTimes[i+1] else f'''<audio src="{recNo:04d}.mp3" clip{'B' if R.daisy3 else '-b'}egin="{'' if R.daisy3 else 'npt='}{textsAndTimes[i-1]:.3f}s" clip{'E' if R.daisy3 else '-e'}nd="{'' if R.daisy3 else 'npt='}{textsAndTimes[i+1]:.3f}s" id="aud{recNo}.{i//2}" />'''}
        {'' if R.daisy3 or textsAndTimes[i-1]==textsAndTimes[i+1] else '</seq>'}
      </par>{''.join(f'<par><text id="t{recNo}.{i//2}.{j}" src="{recNo:04d}.xml#{re.sub(".*"+chr(34)+" id=.","",imageID)}"/></par>' for j,imageID in enumerate(re.findall('<img src="[^"]*" id="[^"]*',textsAndTimes[i][1]))) if R.daisy3 else ''}""" for i in range(1,len(textsAndTimes),2))+"""
    </seq>
  </body>
</smil>
""")
# (do not omit text with 0-length audio altogether, even in Daisy 2: unlike image tags after paragraphs, it might end up not being displayed by EasyReader etc.  Omitting audio does NOT save being stopped at the beginning of the chapter when rewinding by paragraph: is this a bug or a feature?)
def deBlank(s): return re.sub("\n *\n","\n",s) # INTERNAL (see use above)

def deHTML(t):
    "Remove HTML tags from t, collapse whitespace and escape quotes so it can be included in an XML attribute"
    return re.sub(r'\s+',' ',re.sub('<[^>]*>','',t)).replace('"','&quot;').strip()

def package_opf(R,hasFullText,numRecs,totalSecs): # INTERNAL
    "Make the package OPF for a DAISY 3 file"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE package
  PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/"
         unique-identifier="uid">
   <metadata>
      <dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
         <dc:Format>ANSI/NISO Z39.86-2005</dc:Format>
         <dc:Language>{R.lang}</dc:Language>
         <dc:Date>{R.date}</dc:Date>
         <dc:Publisher>{R.publisher}</dc:Publisher>
         <dc:Title>{R.title}</dc:Title>
         <dc:Identifier id="uid"/>
         <dc:Creator>{R.creator}</dc:Creator>
         <dc:Type>text</dc:Type>
      </dc-metadata>
      <x-metadata>
         <meta name="dtb:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}"/>
         <meta name="dtb:totalTime" content="{int(totalSecs/3600)}:{int(totalSecs/60)%60:02d}:{math.ceil(totalSecs%60):02d}"/>
         <meta name="dtb:multimediaContent" content="audio,text{',image' if R.imageFiles else ''}"/>
         <meta name="dtb:narrator"
               content="{deHTML(R.reader)}"/>
         <meta name="dtb:producedDate"
               content="{R.date}"/>
      </x-metadata>
   </metadata>
   <manifest>
      <item href="package.opf" id="opf" media-type="text/xml"/>"""+''.join(f"""
      <item href="{i:04d}.mp3" id="opf-{i}" media-type="audio/mpeg"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i+1}{u[u.rindex("."):]}" id="opf-{i+numRecs+1}" media-type="image/{u[u.rindex(".")+1:].lower().replace("jpg","jpeg")}"/>""" for i,u in enumerate(R.imageFiles))+f"""
      <item href="dtbook.2005.basic.css" id="opf-{len(R.imageFiles)+numRecs+1}" media-type="text/css"/>"""+''.join(f"""
      <item href="{i:04d}.xml" id="opf-{i+len(R.imageFiles)+numRecs+1}" media-type="application/x-dtbook+xml"/>""" for i in range(1,numRecs+1))+''.join(f"""
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

def text_htm(R,paras,offset=0): # INTERNAL
    "paras = [(type,text),(type,text),...], type=h1/p/span, text is xhtml i.e. & use &amp; etc"
    return deBlank(f"""<?xml version="1.0"{' encoding="utf-8"' if R.daisy3 else ''}?>{'<?xml-stylesheet type="text/css" href="dtbook.2005.basic.css"?>' if R.daisy3 else ''}
{'<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">' if R.daisy3 else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-2"' if R.daisy3 else f'html lang="{R.lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{R.lang}">
    <head>
        {f'<meta name="dc:Title" content="{deHTML(R.title)}"/>' if R.daisy3 else f'<title>{R.title}</title>'}
        {'<meta name="dtb:uid" content=""/>' if R.daisy3 else '<meta content="text/html; charset=utf-8" http-equiv="content-type"/>'}
        <meta name="generator" content="{generator}"/>
    </head>
    <{'book' if R.daisy3 else 'body'}>
        {f'<frontmatter><doctitle>{R.title}</doctitle></frontmatter><bodymatter>' if R.daisy3 else ''}
"""+"\n".join(f"""{''.join(f'<level{n}>' for n in range(min(int(tag[1:]),next(int(paras[p][0][1:]) for p in range(num-1,-1,-1) if paras[p][0].startswith('h'))+1) if any(paras[P][0].startswith('h') for P in range(num-1,-1,-1)) else 1,int(tag[1:])+1)) if R.daisy3 and tag.startswith('h') else ''}{'<level1>' if R.daisy3 and not num and not tag.startswith('h') else ''}{'<p>' if tag=='span' and (num==0 or not paras[num-1][0]=="span" or paras[num-1][1].endswith("<br />")) else ''}<{tag} id=\"p{num+offset}\"{(' class="word"' if len(text.split())==1 else ' class="sentence"') if tag=='span' else ''}>{re.sub("<br />$","",re.sub('<img src="[^"]*" [^/]*/>','',text))}</{tag}>{'</p>' if tag=='span' and (text.endswith("<br />") or num+1==len(paras) or not paras[num+1][0]=='span') else ''}{'<p><imggroup>' if R.daisy3 and re.search('<img src="',text) else ''}{''.join(re.findall('<img src="[^"]*" [^/]*/>',text))}{'</imggroup></p>' if R.daisy3 and re.search('<img src="',text) else ''}{''.join(f'</level{n}>' for n in range(next(int(paras[p][0][1:]) for p in range(num,-1,-1) if paras[p][0].startswith('h')) if any(paras[P][0].startswith('h') for P in range(num,-1,-1)) else 1,0 if num+1==len(paras) else int(paras[num+1][0][1:])-1,-1)) if R.daisy3 and (num+1==len(paras) or paras[num+1][0].startswith('h')) else ''}""" for num,(tag,text) in enumerate(normaliseDepth(R,paras)))+f"""
        </{'bodymatter></book' if R.daisy3 else 'body'}>
</{'dtbook' if R.daisy3 else 'html'}>
""")

def er_book_info(durations): # INTERNAL
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
