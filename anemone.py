#!/usr/bin/env python3
"""
Anemone 1.55 (http://ssb22.user.srcf.net/anemone)
(c) 2023-24 Silas S. Brown.  License: Apache 2

To use this module, either run it from the command
line, or import it and use the anemone() function.
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
    it will look at the system command line.
    Return value is a list of warnings, if any.

    Other functions below are generally for
    internal use and are of interest only if you
    want to maintain Anemone, although you might
    find {fetch(), deBlank(), version} useful."""
    
    R=Run(*[(json.dumps(f) if isinstance(f,dict) else f) for f in files],**options)
    if R.mp3_recode or any(f.strip().lower().endswith(f"{os.extsep}wav") for f in files if isinstance(f,str)): check_we_got_LAME()
    write_all(R,get_texts(R))
    return R.warnings

def populate_argument_parser(args):
    """Calls add_argument on args, with the names
    of all Anemone command-line options, which are
    also options for anemone(), and help text.
    This is also used for runtime module help."""
    
    args.add_argument("files",metavar="file",
                      nargs="+",help="""
file name of: an MP3 or WAV recording, a text file
containing its title (if no full text), an XHTML
file containing its full text, a JSON file
containing its time markers (or text plus time in
JSON transcript format), or the output ZIP file. 
Only one output file may be specified, but any
number of the other files can be included; URLs
may be given if they are to be fetched.  If only
sound files are given then titles are taken from
their filenames.  You may also specify @filename
where filename contains a list of files one per
line.""")
    args.add_argument("--lang",default="en",
                      help="""
the ISO 639 language code of the publication (defaults to en for English)""")
    args.add_argument("--title",default="",help="the title of the publication")
    args.add_argument("--url",default="",help="the URL or ISBN of the publication")
    args.add_argument("--creator",default="",help="the creator name, if known")
    args.add_argument("--publisher",default="",help="the publisher name, if known")
    args.add_argument("--reader",default="",
                      help="""
the name of the reader who voiced the recordings, if known""")
    args.add_argument("--date",help="the publication date as YYYY-MM-DD, default is current date")
    args.add_argument("--marker-attribute",
                      default="data-pid",help="""
the attribute used in the HTML to indicate a
segment number corresponding to a JSON time marker
entry, default is data-pid""")
    args.add_argument("--page-attribute",
                      default="data-no",help="""
the attribute used in the HTML to indicate a page number, default is data-no""")
    args.add_argument("--image-attribute",
                      default="data-zoom",help="""
the attribute used in the HTML to indicate an
absolute image URL to be included in the DAISY
file, default is data-zoom""")
    args.add_argument("--refresh",
                      action="store_true",help="""
if images etc have already been fetched from URLs, ask the server if they should be fetched again (use If-Modified-Since)""")
    args.add_argument("--cache",
                      default="cache",help="""
path name for the URL-fetching cache (default
'cache' in the current directory; set to empty
string if you don't want to save anything); when
using anemone as a module, you can instead pass in
a requests_cache session object if you want that
to do it instead, although the delay option is
ignored when you do this""")
    args.add_argument("--reload",dest="refetch",
                      action="store_true",help="""
if images etc have already been fetched from URLs,
fetch them again without If-Modified-Since""")
    args.add_argument("--delay",default=0,help="""
minimum number of seconds between URL fetches (default none)""")
    args.add_argument("--user-agent",default=f"Mozilla/5.0 (compatible, {' '.join(generator.split()[:2])})",help="User-Agent string to send for URL fetches")
    args.add_argument("--daisy3",
                      action="store_true",help="""
Use the Daisy 3 format (ANSI/NISO Z39.86) instead
of the Daisy 2.02 format.  This may require more
modern reader software, and Anemone does not yet
support Daisy 3 only features like tables.""")
    args.add_argument("--mp3-recode",
                      action="store_true",help="""
re-code the MP3 files to ensure they are constant
bitrate and more likely to work with the more
limited DAISY-reading programs like FSReader 3
(this option requires LAME)""")
    args.add_argument("--allow-jumps",
                      action="store_true",help="""
Allow jumps in heading levels e.g. h1 to h3 if the
input HTML does it.  This seems OK on modern
readers but might cause older reading devices to
give an error.  Without this option, headings are
promoted where necessary to ensure only
incremental depth increase.""") # might cause older reading devices to give an error: and is also flagged up by the validator
    args.add_argument("--strict-ncc-divs",
                      action="store_true",help="""
When generating Daisy 2, avoid using a heading in
the navigation control centre when there isn't a
heading in the text.  This currently applies when
spans with verse numbering are detected.  Turning
on this option will make the DAISY more conformant
to the specification, but some readers (EasyReader
10, Thorium) won't show these headings in the
navigation in Daisy 2 (but will show them anyway
in Daisy 3, so this option is applied
automatically in Daisy 3).  On the other hand,
when using verse-numbered spans without this
option, EasyReader 10 may not show any text at all
in Daisy 2 (Anemone will warn if this is the
case).  This setting cannot stop EasyReader
promoting all verses to headings (losing paragraph
formatting) in Daisy 3, which is the least bad
option if you want these navigation points to
work.""")
    args.add_argument("--merge-books",
                      default="",help="""
Combine multiple books into one, for saving media
on CD-based DAISY players that cannot handle more
than one book.  The format of this option is
book1/N1,book2/N2,etc where book1 is the book
title and N1 is the number of MP3 files to group
into it (or if passing the option into the anemone
module, you may use a list of tuples).  All
headings are pushed down one level and book name
headings are added at top level.""")
    args.add_argument("--chapter-titles",
                      default="",help="""
Comma-separated list of titles to use for chapters
that don't have titles, e.g. 'Chapter N' in the
language of the book (this can help for
search-based navigation).  If passing this option
into the anemone module, you may use a list
instead of a comma-separated string, which might
be useful if there are commas in some chapter
titles.""")
    args.add_argument("--chapter-heading-level",default=1,help="Heading level to use for chapters that don't have titles")
    args.add_argument("--dry-run",action="store_true",help="Don't actually output DAISY, just check the input and parameters")

generator=__doc__.strip().split('\n')[0] # string we use to identify ourselves in HTTP requests and in Daisy files

def get_argument_parser():
    "populates an ArgumentParser for Anemone"
    
    from argparse import ArgumentParser
    args = ArgumentParser(prog="anemone",description=generator,fromfile_prefix_chars='@')
    populate_argument_parser(args)
    return args

import time, sys, os, re, json
import textwrap
from collections import namedtuple as NT
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

class DocUpdater:
    def __init__(self,p):
        self.p = p
        self.p.__doc__ += "\nOptions when run as a command-line utility:\n"
    def add_argument(self,*args,**kwargs): self.p.__doc__ += f"\n* {(chr(10)+'  ').join(textwrap.wrap((args[0]+': ' if args[0].startswith('--') else '')+re.sub(chr(10)+' *',' ',kwargs['help']).strip(),50))}\n"
populate_argument_parser(DocUpdater(sys.modules[__name__])) ; del DocUpdater

def error(m):
    """Anemone error handler.  If running as an
    application, print message and error-exit.  If
    running as a module, raise an AnemoneError."""
    
    if __name__=="__main__": sys.stderr.write(f"Error: {m}\n"),sys.exit(1)
    else: raise AnemoneError(str(m))
class AnemoneError(Exception): pass

try: import mutagen
except ImportError: error("Anemone needs the Mutagen library to determine play lengths.\nPlease do: pip install mutagen")
from io import BytesIO

class Run():
  """The parameters we need for an Anemone run.
  Constructor can either parse args from the
  command line, or from anemone() caller."""
  def __init__(R,*inFiles,**kwargs):
    # I know the convention is "self" but I am
    # working in giant print so my screen area
    # is important, so 1 letter please...
    R.audioData,R.filenameTitles = [],[]
    R.jsonData = []
    R.textData,R.htmlData = [],[]
    R.imageFiles,R.outputFile = [],None
    R.warnings = []
    if inFiles: R.__dict__.update(get_argument_parser().parse_args(list(inFiles)+[a for k,v in kwargs.items() for a in ['--'+k.replace('_','-'),str(v)] if type(v) in [str,int]]).__dict__) # module
    else: R.__dict__.update(get_argument_parser().parse_args().__dict__) # command line
    R.__dict__.update((k,v) for k,v in kwargs.items() if type(v) not in [str,int,type(None)]) # (None means keep the default from parse_args; boolean and bytes we might as well handle directly; list e.g. merge_books should bypass parser; ditto session object for cache, a type we can't even name here if requests_cache is not installed)
    for k in ['merge_books','chapter_titles']:
        if not isinstance(R.__dict__[k],list): R.__dict__[k]=R.__dict__[k].split(',') # comma-separate if coming from the command line, but allow lists to be passed in to the module
    for f in R.files:
        fOrig = f
        if f.lower().endswith(f"{os.extsep}zip"):
            if R.outputFile: error(f"Only one {os.extsep}zip output file may be specified")
            R.outputFile = f ; continue
        if re.match("https?://",f):
            f=fetch(f,R.cache,R.refresh,R.refetch,R.delay,R.user_agent)
        elif delimited(f,'{','}'): pass
        elif delimited(f,'<','>'): pass
        elif not os.path.isfile(f): error(f"File not found: {f}")
        else: f = open(f,"rb").read()
        if delimited(f,'{','}'):
            R.jsonData.append(json.loads(f))
            check_for_JSON_transcript(R)
        elif delimited(f,'<','>'):
            R.htmlData.append(f)
        elif fOrig.lower().endswith(f"{os.extsep}mp3") or fOrig.lower().endswith(f"{os.extsep}wav"):
            R.audioData.append(f)
            R.filenameTitles.append(fOrig[:fOrig.rindex(os.extsep)])
        elif fOrig.lower().endswith(f"{os.extsep}txt"):
            R.textData.append(f.decode('utf-8').strip())
        else: error(f"Format of '{fOrig}' has not been recognised")
    if not R.audioData: error("Creating DAISY files without audio is not yet implemented")
    if R.htmlData and not R.jsonData: error("Full text without time markers is not yet implemented")
    if R.jsonData and not R.htmlData: error("Time markers without full text is not implemented")
    if R.htmlData and R.textData: error("Combining full text with title-only text files is not yet implemented.  Please specify full text for everything or just titles for everything, not both.")
    if R.jsonData and not len(R.audioData)==len(R.jsonData): error(f"If JSON marker files are specified, there must be exactly one JSON file for each recording file.  We got f{len(R.jsonData)} JSON files and f{len(R.audioData)} recording files.")
    if R.textData and not len(R.audioData)==len(R.textData): error(f"If text files are specified, there must be exactly one text file for each recording file.  We got f{len(R.textData)} text files and f{len(R.audioData)} recording files.")
    if R.htmlData and not len(R.audioData)==len(R.htmlData): error(f"If HTML documents are specified, there must be exactly one HTML document for each recording.  We got f{len(R.htmlData)} HTML documents and f{len(R.audioData)} recordings.")
    if not R.outputFile: R.outputFile=f"output_daisy{os.extsep}zip"
    if not R.title: R.title=R.outputFile.replace(f"{os.extsep}zip","").replace("_daisy","")
  def warning(R,warningText):
      R.warnings.append(warningText) ; sys.stderr.write(f"WARNING: {warningText}\n")

def delimited(s,start,end):
    """Checks to see if a string or binary data
    is delimited by start and end, converting as
    needed, after stripping"""
    if isinstance(s,bytes):
        s = s.replace(b"\xEF\xBB\xBF",b"").strip() # just in case somebody's using UTF-8 BOMs
        return s.startswith(start.encode('latin1')) and s.endswith(end.encode('latin1'))
    else: # string; assume no BOM to skip
        s = s.strip()
        return s.startswith(start) and s.endswith(end)

def check_for_JSON_transcript(R):
    """Checks to see if the last thing added to
    the Run object is a JSON podcast transcript,
    and converts it to HTML + time markers"""
    
    if isinstance(R.jsonData[-1].get("segments",None),list) and all(isinstance(s,dict) and "startTime" in s and "body" in s for s in R.jsonData[-1]["segments"]): # looks like JSON transcript format instead of markers format
        curSpeaker=None ; bodyList = []
        for s in R.jsonData[-1]["segments"]:
            bodyList.append(s["body"])
            s=s.get("speaker",curSpeaker)
            if not s==curSpeaker:
                curSpeaker,bodyList[-1] = s,f"[{s}] {bodyList[-1]}"
                if len(bodyList)>1: bodyList[-2] += "<br>"
        R.htmlData.append(' '.join(f'<span {R.marker_attribute}="{i}">{c}</span>' for i,c in enumerate(bodyList) if c))
        R.jsonData[-1]={"markers":[{"id":f"{i}","time":t} for i,t in enumerate(s["startTime"] for s in R.jsonData[-1]["segments"]) if bodyList[i]]}

def check_we_got_LAME():
    """Complains if a LAME binary is not
    available on this system.  Makes a little
    extra effort to find one on Windows."""
    
    if which('lame'): return
    if sys.platform=='win32':
        os.environ["PATH"] += r";C:\Program Files (x86)\Lame for Audacity;C:\Program Files\Lame for Audacity"
        if which('lame'): return
    error(f"Anemone requires the LAME program to encode/recode MP3s.\nPlease {'run the exe installer from lame.buanzo.org' if sys.platform=='win32' else 'install lame'} and try again.")

PageInfo = NT('PageInfo',['duringId','pageNo'])
TagAndText = NT('TagAndText',['tag','text'])
TextsAndTimesWithPages = NT('TextsAndTimesWithPages',['textsAndTimes','pageInfos'])
ChapterTOCInfo = NT('ChapterTOCInfo',['hTag','hLine','itemNo'])
BookTOCInfo = NT('BookTOCInfo',['hTag','hLine','recNo','itemNo'])
del NT

def get_texts(R):
    """Gets the text markup required for the run,
    extracting it from HTML (guided by JSON IDs)
    if we need to do that."""
    
    if R.textData: return R.textData # section titles only, from text files
    elif not R.htmlData: return R.filenameTitles # section titles only, from sound filenames
    recordingTexts = []
    for h,j in zip(R.htmlData,R.jsonData):
        markers = j['markers']
        want_pids = [jsonAttr(m,"id") for m in markers]
        id_to_content = {}
        pageNos = []
        allowedInlineTags={'br':'br','strong':'strong','em':'em','b':'strong','i':'em'}
        assert 'rt' not in allowedInlineTags, "if allowing this, need to revise rt suppression logic" # and would have to rely on rp parens for most readers, so if a text has a LOT of ruby it could get quite unreadable
        class PidsExtractor(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.addTo = None
                self.suppress = 0
                self.imgsMaybeAdd = None
                self.imgsMaybeAddTo = None
                self.pageNoGoesAfter = 0
                self.theStartTag = None
            def handle_starttag(self,tag,attrs):
                tag = tagRewrite.get(tag,tag)
                attrs = dict(attrs)
                imgURL = attrs.get(R.image_attribute,None)
                if imgURL and (re.match("https?://.*[.][^/]*$",imgURL) or os.path.isfile(imgURL)) and not (self.addTo is None and self.imgsMaybeAdd is None):
                    # TODO: might want to check attrs.get("alt",""), but DAISY3 standard does not list alt as a valid attribute for img, so we'd have to put it after with br etc (changing text_htm) and we don't know if it's in the audio or not: probably best just to leave it and rely on there being a separate caption with ID if it's in the audio
                    img = f'<img src="{(R.imageFiles.index(imgURL) if imgURL in R.imageFiles else len(R.imageFiles))+1}{imgURL[imgURL.rindex("."):]}" {f"""id="i{R.imageFiles.index(imgURL) if imgURL in R.imageFiles else len(R.imageFiles)}" """ if R.daisy3 else ""}/>' # will be moved after paragraph by text_htm
                    if imgURL not in R.imageFiles:
                        R.imageFiles.append(imgURL)
                    if self.addTo is None: self.imgsMaybeAdd.append(img)
                    else: self.addTo.append(img)
                if attrs.get(R.marker_attribute,None) in want_pids:
                    self.theStartTag = tag
                    self.tagDepth = 0
                    a = attrs[R.marker_attribute]
                    self.pageNoGoesAfter = want_pids.index(a)
                    id_to_content[a] = ((tag if re.match('h[1-6]$',tag) or tag=='span' else 'p'),[])
                    if self.imgsMaybeAdd: self.imgsMaybeAddTo += self.imgsMaybeAdd # and imgsMaybeAdd will be reset to [] when this element is closed
                    self.addTo = id_to_content[a][1]
                elif tag==self.theStartTag and not tag=="p": # can nest
                    self.tagDepth += 1
                elif self.addTo is not None and tag in allowedInlineTags: self.addTo.append(f'<{allowedInlineTags[tag]}>')
                elif self.addTo is not None and tag=='a': self.lastAStart = len(self.addTo)
                elif tag=='rt': self.suppress += 1
                pageNo = attrs.get(R.page_attribute,None)
                if pageNo: pageNos.append(PageInfo(self.pageNoGoesAfter,pageNo))
            def handle_endtag(self,tag):
                tag = tagRewrite.get(tag,tag)
                if self.suppress and tag=='rt': self.suppress -= 1
                elif self.addTo is not None:
                    if tag==self.theStartTag and self.tagDepth == 0:
                        self.highestImage,self.imgsMaybeAddTo, self.imgsMaybeAdd = len(R.imageFiles),self.addTo,[] # if we find any images (not in an id'd element) after the end of the id'd element, we might want to add them in with any inside it, but only if there's another id'd element after them i.e. not if they're just random decoration at the bottom of the page
                        self.addTo = None
                    elif tag in allowedInlineTags: self.addTo.append(f'</{allowedInlineTags[tag]}>')
                    elif tag=="a" and re.match('[!-.:-~]$',"".join(self.addTo[self.lastAStart:]).strip()): del self.addTo[self.lastAStart:] # remove single-character link, probably to footnote (we won't know if it's in the audio or not, we're not supporting jumps and the symbols might need normalising) but do allow numbers (might be paragraph numbers etc) and non-ASCII (might be single-character CJK word)
                    if tag==self.theStartTag and self.tagDepth: self.tagDepth -= 1
                elif tag=='p' and self.imgsMaybeAddTo and self.theStartTag=='span': self.imgsMaybeAddTo.append("<br>") # if paragraphs contain spans and it's the spans that are identified, ensure we keep this break in the surrounding structure
                if tag=='html' and self.imgsMaybeAdd and hasattr(self,'highestImage'): del R.imageFiles[self.highestImage:] # do not include ones that were only in imgsMaybeAdd at the end of the page (and not also elsewhere)
            def handle_data(self,data):
                if self.addTo is not None and not self.suppress:
                    self.addTo.append(data.replace('&','&amp;').replace('<','&lt;'))
        if isinstance(h,bytes):
            h = h.decode('utf-8')
        PidsExtractor().feed(h)
        rTxt = []
        for i in range(len(markers)):
            rTxt.append(parseTime(jsonAttr(markers[i],"time")))
            if want_pids[i] in id_to_content:
                tag,content = id_to_content[want_pids[i]]
                content = ''.join(content).strip()
                rTxt.append(TagAndText(tag,content_fixes(content)))
            else:
                R.warning(f"JSON {len(recordingTexts)+1} marker {i+1} marks paragraph ID {want_pids[i]} which is not present in HTML {len(recordingTexts)+1}.  Anemone will make this a blank paragraph.")
                rTxt.append(TagAndText('p',''))
        recordingTexts.append(TextsAndTimesWithPages(rTxt,pageNos))
    return recordingTexts

tagRewrite = { # used by get_texts
    'legend':'h3', # used in fieldset
}

def content_fixes(content):
    """Miscellaneous fixes for final XML/XHTML
    to work around some issues with readers"""
    content = easyReader_em_fix(content)
    content = re.sub('( *</?br> *)+',' <br />',content) # allow line breaks inside paragraphs, in case any in mid-"sentence", but collapse them because readers typically add extra space to each, plus add a space beforehand in case any reader doesn't render the linebreak (e.g. EasyReader 10 in a sentence span)
    return content

def easyReader_em_fix(content):
    """EasyReader 10 workaround: it does not show
    strong or em, which is OK but it puts space
    around it: no good if it happened after a "("
    or similar, so delete those occurrences"""
    while True:
        c2 = re.sub(r"<(?P<tag>(strong|em))>(.*?)</(?P=tag)>",lambda m:easyReader_em_fix(m.group(3)) if m.start() and content[m.start()-1] not in ' >' or m.end()<len(content) and content[m.end()] not in ' <' else f"<{m.group(1)}>{easyReader_em_fix(m.group(3))}</{m.group(1)}>",content)
        if c2==content: break
        content = c2 # and re-check
    return content

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

def write_all(R,recordingTexts):
    """Writes the DAISY zip and everything in it.
    Each item of recordingTexts is either 1 text
    for section title of whole recording, or a
    TextsAndTimesWithPages i.e. ([TagAndText,time,
    TagAndText,time,TagAndText],[PageInfo,...])"""
    
    assert len(R.audioData) == len(recordingTexts)
    headings = getHeadings(R,recordingTexts)
    if R.dry_run: return sys.stderr.write(f"Dry run: {len(R.warnings) if R.warnings else 'no'} warning{'' if len(R.warnings)==1 else 's'} for {R.outputFile}\n")
    merge0lenSpans(recordingTexts,headings)
    if R.mp3_recode or any('audio/mp3' not in mutagen.File(BytesIO(dat)).mime for dat in R.audioData): # parallelise lame if possible
        if not __name__=="__main__": sys.stderr.write(f"Making {R.outputFile}...\n"),sys.stderr.flush() # especially if repeatedly called, print which outputFile we're working on BEFORE the mp3s also
        executor = ThreadPoolExecutor(max_workers=cpu_count())
        recordingTasks=[executor.submit((recodeMP3 if R.mp3_recode or 'audio/mp3' not in mutagen.File(BytesIO(dat)).mime else lambda x:x),dat) for dat in R.audioData]
    else: executor,recordingTasks = None,None
    try: _write0(R,recordingTexts,headings,recordingTasks)
    except: # unhandled exception: clean up
        try: executor.shutdown(wait=False,cancel_futures=False) # (cancel_futures is Python 3.9+)
        except: pass # (no executor / can't do it) # noqa: E722
        try: os.remove(R.outputFile) # incomplete
        except: pass # noqa: E722
        raise
def _write0(R,recordingTexts,headings,recordingTasks):
    if os.sep in R.outputFile: Path(R.outputFile[:R.outputFile.rindex(os.sep)]).mkdir(parents=True,exist_ok=True)
    z = ZipFile(R.outputFile,"w",ZIP_DEFLATED,True)
    R.dataSectors = R.catalogueEntries = 0
    def writestr(n,s):
        if isinstance(s,bytes): L = len(s)
        else: L = len(s.encode('utf-8'))
        R.dataSectors += (L+2047)//2048 # ISO 9660 sectors on a CD-ROM
        R.catalogueEntries += 1
        # Assume roughly 64 entries per catalogue sector (TODO check), *3 for RockRidge/Joliet
        # Also 16 sectors are unused before start
        # 333,000 sectors on original 650M CD-ROM, TODO: we can probably increase that if 650M CDs are not in use, but some non-CD readers can still go wrong when files greatly exceed this size
        if 3*((R.catalogueEntries+63)//64) + R.dataSectors + 16 > 333000 and not hasattr(R,"warnedFull"):
            R.warnedFull = True
            R.warning(f"{R.outputFile} is too big for some DAISY readers")
        z.writestr(n,s)
    def D(s): return s.replace("\n","\r\n") # in case old readers require DOS line endings
    hasFullText = any(isinstance(t,TextsAndTimesWithPages) for t in recordingTexts)
    if hasFullText: writestr("0000.txt",D(f"""
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
    durations = [] ; curP = 1
    for recNo in range(1,len(recordingTexts)+1):
        rTxt = recordingTexts[recNo-1]
        secsThisRecording = mutagen.File(BytesIO(R.audioData[recNo-1])).info.length
        if secsThisRecording > 3600: R.warning(f"Recording {recNo} is long enough to cause ~{secsThisRecording*.0001:.1f}sec synchronisation error on some readers") # seems lame v3.100 can result in timestamps being effectively multiplied by ~1.0001 on some players but not all, causing slight de-sync on 1h+ recordings (bladeenc may avoid this but be lower quality overall; better to keep the recordings shorter if possible)
        durations.append(secsThisRecording)
        if recordingTasks is not None: sys.stderr.write(f"Adding {recNo:04d}.mp3..."),sys.stderr.flush()
        writestr(f"{recNo:04d}.mp3",R.audioData[recNo-1] if recordingTasks is None else recordingTasks[recNo-1].result())
        if recordingTasks is not None: sys.stderr.write(" done\n")
        writestr(f'{recNo:04d}.smil',D(section_smil(R,recNo,secsSoFar,secsThisRecording,curP,rTxt.textsAndTimes if isinstance(rTxt,TextsAndTimesWithPages) else rTxt)))
        writestr(f'{recNo:04d}.{"xml" if R.daisy3 else "htm"}',D(text_htm(R,(rTxt.textsAndTimes[(1 if isinstance(rTxt.textsAndTimes[0],float) else 0)::2] if isinstance(rTxt,TextsAndTimesWithPages) else [TagAndText('h1',rTxt)]),curP)))
        secsSoFar += secsThisRecording
        curP += (1+len(rTxt.textsAndTimes)//2 if isinstance(rTxt,TextsAndTimesWithPages) else 1)
    for n,u in enumerate(R.imageFiles): writestr(f'{n+1}{u[u.rindex("."):]}',fetch(u,R.cache,R.refresh,R.refetch,R.delay,R.user_agent) if re.match("https?://",u) else open(u,'rb').read())
    if not R.date: R.date = "%d-%02d-%02d" % time.localtime()[:3]
    if R.daisy3:
        writestr('dtbook.2005.basic.css',D(d3css))
        writestr('package.opf',D(package_opf(R,hasFullText,len(recordingTexts),secsSoFar)))
        writestr('text.res',D(textres))
    else: writestr('master.smil',D(master_smil(R,headings,secsSoFar)))
    writestr('navigation.ncx' if R.daisy3 else 'ncc.html',D(ncc_html(R,headings,hasFullText,secsSoFar,[timeAdjust(t.textsAndTimes if isinstance(t,TextsAndTimesWithPages) else t, durations[i]) for i,t in enumerate(recordingTexts)],[(t.pageInfos if isinstance(t,TextsAndTimesWithPages) else []) for t in recordingTexts])))
    if not R.daisy3: writestr('er_book_info.xml',D(er_book_info(durations))) # not DAISY standard but EasyReader can use this
    z.close()
    sys.stderr.write(f"Wrote {R.outputFile}\n")

def getHeadings(R,recordingTexts):
    """Gets headings from recordingTexts for the
    DAISY's NCC / OPF data"""
    
    ret = [] ; cvChaps = [] ; chapNo = 0
    try: bookTitlesAndNumChaps = [(n,int(v)) for n,v in [(b if isinstance(b,tuple) else b.split('/')) for b in R.merge_books if b]]
    except: error(f"Unable to parse merge-books={R.merge_books}") # noqa: E722
    for t in recordingTexts:
        chapNo += 1
        if bookTitlesAndNumChaps and chapNo==bookTitlesAndNumChaps[0][1]+1:
            del bookTitlesAndNumChaps[0]
            if not bookTitlesAndNumChaps: error("merge-books did not account for all files (check the counts)")
            chapNo = 1
        if not isinstance(t,TextsAndTimesWithPages):
            if bookTitlesAndNumChaps and chapNo==1: error("merge-books with non-HTML not yet implemented")
            ret.append(t) ; continue # title only
        textsAndTimes,pages = t ; first = None
        chapHeadings = []
        for v,u in enumerate(textsAndTimes):
            if isinstance(u,float): continue #time
            tag,text = u
            if first is None: first = v
            if not tag.startswith('h'):
                continue
            if v//2 - 1 == first//2 and not textsAndTimes[first].tag.startswith('h'): # chapter starts with non-heading followed by heading: check the non-heading for "Chapter N" etc
                nums=re.findall("[1-9][0-9]*",textsAndTimes[first].text)
                if len(nums)==1:
                    text=f"{nums[0]}: {text}" # for TOC
                    textsAndTimes[v-1] = (textsAndTimes[first-1] if first else 0) + 0.001 # for audio jump-navigation to include the "Chapter N" (TODO: option to merge the in-chapter text instead, so "Chapter N" appears as part of the heading, not scrolled past quickly?  merge0lenSpans will now do this if the chapter paragraph is promoted to heading, but beware we might not want the whole of the 'chapter N' text to be part of the TOC, just the number.  Thorium actually stops playing when it hits the 0-length paragraph before the heading, so promoting it might be better; trying the +0.001 for now to make timestamps not exactly equal)
            chapHeadings.append(ChapterTOCInfo(tag,re.sub('<img src.*?/>','',text),v//2))
        if not chapHeadings:
            # This'll be a problem, as master_smil and ncc_html need headings to refer to the chapter at all.  (Well, ncc_html can also do it by page number if we have them, but we haven't tested all DAISY readers with page number only navigation, and what if we don't even have page numbers?)
            # So let's see if we can at least get a chapter number.
            if first is not None: nums=re.findall("[1-9][0-9]*",textsAndTimes[first].text)
            else:
                R.warning(f"Chapter {chapNo} is completely blank!  (Is {'--marker-attribute' if __name__=='__main__' else 'marker_attribute'} set correctly?)")
                nums = [] ; first = 0 ; textsAndTimes.append(TagAndText('p',''))
            chapterNumberTextFull = chapterNumberText = nums[0] if len(nums)==1 and not nums[0]=="1" else str(chapNo)
            if R.chapter_titles:
                if len(R.chapter_titles)>1: chapterNumberTextFull,R.chapter_titles = R.chapter_titles[0],R.chapter_titles[1:]
                else: chapterNumberTextFull,R.chapter_titles = R.chapter_titles[0], []
                if chapterNumberText not in chapterNumberTextFull: R.warning(f"Title for chapter {chapNo} is '{chapterNumberTextFull}' which does not contain the expected '{chapterNumberText}'")
            # In EasyReader 10 on Android, unless there is at least one HEADING (not just div), navigation display is non-functional.  And every heading must point to a 'real' heading in the text, otherwise EasyReader 10 will delete all the text in Daisy 2, or promote something to a heading in Daisy 3 (this is not done by Thorium Reader)
            # (EasyReader 10 on Android also inserts a newline after every span class=sentence if it's a SMIL item, even if there's no navigation pointing to it)
            # So let's add a "real" start-of-chapter heading before the text, with time 0.001 second if we don't know the time from the first time marker (don't set it to 0 or Thorium can have issues)
            if first==1 and textsAndTimes[0]: first = 0 # for the insert below: put it before the non-zero opening time marker
            else: textsAndTimes.insert(first,(textsAndTimes[first-1] if first else 0)+0.001)
            textsAndTimes.insert(first,TagAndText(f'h{R.chapter_heading_level}',chapterNumberTextFull)) # we'll ref this
            chapHeadings=[ChapterTOCInfo(f'h{R.chapter_heading_level}',chapterNumberTextFull,first//2)] # points to our extra heading
            if textsAndTimes[first+2].text.startswith(chapterNumberText): textsAndTimes[first+2]=TagAndText(textsAndTimes[first+2].tag,textsAndTimes[first+2].text[len(chapterNumberText):].strip()) # because we just had the number as a heading, so we don't also need it repeated as 1st thing in text
            first += 2 # past the heading we added
            if first+2<len(textsAndTimes) and re.search("[1-9][0-9]*",textsAndTimes[first+2].text):
              v2 = int(re.findall("[1-9][0-9]*",textsAndTimes[first+2].text)[0]) # might not start at 2, might start at 13 or something, but does it then increase incrementally:
              if [re.findall("[1-9][0-9]*",textsAndTimes[f].text)[:1] for f in range(first+4,len(textsAndTimes),2) if textsAndTimes[f].text]==[[str(n)] for n in range(v2+1,v2+(len(textsAndTimes)-first)//2-sum(1 for f in range(first+4,len(textsAndTimes),2) if not textsAndTimes[f].text))]: # looks like we're dealing with consecutive chapter and verse numbers with no other headings, so index the verse numbers (this is resilient to blank paragraphs due to an extra timing marker somewhere, but might cause incorrect numbering if that extra timing marker is not at the end)
                v = 1
                while v < (len(textsAndTimes)-first)//2+2:
                    lastV = v
                    while lastV < (len(textsAndTimes)-first)//2+1 and (0 if v==1 else textsAndTimes[first+2*v-3])==textsAndTimes[first+2*lastV-1]: lastV += 1 # check for a span of them sharing a time
                    if any(textsAndTimes[first+2*vv-2].text for vv in range(v,lastV+1)): chapHeadings.append(ChapterTOCInfo('div' if R.daisy3 or R.strict_ncc_divs else f'h{R.chapter_heading_level+1}',f"{chapterNumberText}:{v}{'' if v==lastV else f'-{lastV}'}",first//2+v-1))
                    v = lastV + 1
                cvChaps.append(len(ret)+1)
        if bookTitlesAndNumChaps:
            chapHeadings=[ChapterTOCInfo(f'h{int(i.hTag[1:])+1}' if i.hTag.startswith('h') else i.hTag,i.hLine,i.itemNo) for i in chapHeadings] # add 1 to each heading level
            if chapNo==1: chapHeadings.insert(0,ChapterTOCInfo('h1',bookTitlesAndNumChaps[0][0],chapHeadings[0].itemNo)) # the book title (must point to a real heading for similar reason as above, TODO: if there's substantial text before 1st heading, we'll need to insert a heading in the text with 0.001s audio or something instead of doing this; may also need to in-place change recordingTexts adding 1 to all headings: don't do this unless inserting h1)
        ret.append(chapHeadings)
    if len(bookTitlesAndNumChaps)>1 or bookTitlesAndNumChaps and not chapNo==bookTitlesAndNumChaps[0][1]: R.warning("merge-books specified more files than given")
    if len(cvChaps) not in [0,len(ret)]: R.warning(f"Verse-indexed only {len(cvChaps)} of {len(ret)} chapters.  Missing: {', '.join(str(i) for i in range(1,len(ret)+1) if i not in cvChaps)}")
    if cvChaps and not R.daisy3 and not R.strict_ncc_divs: R.warning("Verse-indexing in Daisy 2 can prevent EasyReader 10 from displaying the text: try Daisy 3 instead") # (and with strict_ncc_divs, verses are not shown in Book navigation in Daisy 2)
    return ret

def merge0lenSpans(recordingTexts,headings):
    """Finds spans in the text that are marked as
    zero length in the audio, and merges them into
    their neighbours if possible.  This is so that
    the resulting DAISY file can still be
    navigable if some of the time markers are
    somehow missing in the input JSON, i.e. we
    don't know when item 1 becomes item 2, but we
    do know where item 1 starts and where item 2
    ends, so can we set the navigation to create
    a combined item for both 1 and 2."""
    
    for cT,cH in zip(recordingTexts,headings):
        if not isinstance(cT,TextsAndTimesWithPages): continue
        textsAndTimes,pages = cT
        i=0
        while i < len(textsAndTimes)-2:
            while i < len(textsAndTimes)-2 and isinstance(textsAndTimes[i],TagAndText) and (0 if i==0 else textsAndTimes[i-1])==textsAndTimes[i+1] and textsAndTimes[i].tag==textsAndTimes[i+2].tag: # tag identical and 0-length
                textsAndTimes[i] = TagAndText(textsAndTimes[i].tag, f"{textsAndTimes[i].text}{' ' if textsAndTimes[i].tag=='span' else '<br>'}{textsAndTimes[i+2].text}") # new combined item
                del textsAndTimes[i+1:i+3] # old
                for hI,hV in enumerate(cH):
                    if hV.itemNo > i//2: cH[hI]=ChapterTOCInfo(hV.hTag,hV.hLine,hV.itemNo-1)
                for pI,pInfo in enumerate(pages):
                    if pInfo.duringId > i//2: pages[pI]=PageInfo(pInfo.duringId-1,pInfo.pageNo)
            i += 1

def recodeMP3(dat):
    """Takes MP3 or WAV data, re-codes it
    as suitable for DAISY, and returns the bytes
    of new MP3 data for putting into DAISY ZIP"""

    # It seems broken players like FSReader can get timing wrong if mp3 contains
    # too many tags at the start (e.g. images).
    # eyed3 clear() won't help: it zeros out bytes without changing indices.
    # To ensure everything is removed, better decode to raw PCM and re-encode :-(
    decodeJob = run(["lame","-t","--decode"]+(["--mp3input"] if 'audio/mp3' in mutagen.File(BytesIO(dat)).mime else [])+["-","-o","-"],input=dat,check=True,stdout=PIPE,stderr=PIPE)
    # (On some LAME versions, the above might work
    # with AIFF files too, but we say MP3 or WAV.
    # Some LAME versions can't take WAV from stdin
    # only raw when encoding, but ok if --decode)
    m = re.search(b'(?s)([0-9.]+) kHz, ([0-9]+).*?([0-9]+) bit',decodeJob.stderr) # hope nobody disabled --decode when building LAME (is OK on lame.buanzo.org EXEs)
    if not m: error("lame did not give expected format for frequency, channels and bits output")
    return run(["lame","--quiet","-r","-s",m.group(1).decode('latin1')]+(['-a'] if m.group(2)==b'2' else [])+['-m','m','--bitwidth',m.group(3).decode('latin1'),"-","--resample","44.1","-b","64","-q","0","-o","-"],input=decodeJob.stdout,check=True,stdout=PIPE).stdout

def fetch(url,
          cache = "cache",
          refresh = False,
          refetch = False,
          delay = 0,
          user_agent = None):
    """Fetches a URL, with delay and/or cache.
    
    cache: the cache directory (None = don't save)
    or a requests_cache session object to do it
    (delay option is ignored when using session)

    refresh: if True, send an If-Modified-Since
    request if we have a cached item (the date of
    modification will be the timestamp of the file
    in the cache, not necessarily the actual last
    modified time as given by the server)

    refetch: if True, reload unconditionally
    without first checking the cache

    delay: number of seconds between fetches
    (tracked globally from last fetch)

    user_agent: the User-Agent string to use, if
    not using Python's default User-Agent"""
    
    ifModSince = None
    if hasattr(cache,"get"):
        # if we're given a requests_cache session,
        # use that instead of our own caching code
        r = cache.request('GET',url,headers = {"User-Agent":user_agent} if user_agent else {},refresh=refresh,force_refresh=refetch)
        if r.status_code == 200: return r.content
        else: raise HTTPError("",r.status_code,"unexpected HTTP code",{},None)

    # Fallback to our own filesystem-based code
    # for quick command-line use if you want to
    # manually manage the cache (delete parts of
    # it by directory etc) :
    if cache:
      fn = re.sub('[%&?@*#{}<>!:+`=|$]','',cache+os.sep+unquote(re.sub('.*?://','',url)).replace('/',os.sep)) # these characters need to be removed on Windows's filesystem; TODO: store original URL somewhere just in case some misguided webmaster puts two identical URLs modulo those characters??
      if fn.endswith(os.sep): fn += "index.html"
      fn = os.sep.join(f.replace('.',os.extsep) for f in fn.split(os.sep)) # just in case we're on RISC OS (not tested)
      fnExc = fn+os.extsep+"exception"
      if os.path.exists(fn):
        if refetch: pass # ignore already dl'd
        elif refresh:
            ifModSince=os.stat(fn).st_mtime
        else: return open(fn,'rb').read()
      elif os.path.exists(fnExc) and not refetch and not refresh: raise HTTPError("",int(open(fnExc).read()),"HTTP error on last fetch",{},None) # useful especially if a wrapper script is using our fetch() for multiple chapters and stopping on a 404
      Path(fn[:fn.rindex(os.sep)]).mkdir(parents=True,exist_ok=True)
    sys.stderr.write("Fetching "+url+"...")
    sys.stderr.flush()
    global _last_urlopen_time
    try: _last_urlopen_time
    except NameError: _last_urlopen_time = 0
    if delay: time.sleep(min(0,_last_urlopen_time+delay-time.time()))
    headers = {"User-Agent":user_agent} if user_agent else {}
    if ifModSince:
        t = time.gmtime(ifModSince)
        headers["If-Modified-Since"]=f"{'Mon Tue Wed Thu Fri Sat Sun'.split()[t.tm_wday]}, {t.tm_mday} {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[t.tm_mon-1]} {t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d} GMT"
    try: dat = urlopen(Request(url,headers=headers)).read()
    except HTTPError as e:
        _last_urlopen_time = time.time()
        if e.getcode()==304 and cache:
            sys.stderr.write(" no new data\n")
            return open(fn,'rb').read()
        else:
            sys.stderr.write(f"error {e.getcode()}\n")
            if cache: open(fnExc,"w").write(str(e.getcode()))
            raise
    _last_urlopen_time = time.time()
    if cache:
        open(fn,'wb').write(dat)
        sys.stderr.write(" saved\n")
    else: sys.stderr.write(" fetched\n")
    return dat

def ncc_html(R, headings = [],
             hasFullText = False,
             totalSecs = 0,
             recTimeTxts = [],
             pageNos=[]):
    """Returns the Navigation Control Centre (NCC)
    recTimeTxts includes 0 and total
    pageNos is [[PageInfo,...],...]"""
    
    numPages = sum(len(L) for L in pageNos)
    maxPageNo = max((max((int(i.pageNo) for i in PNs),default=0) for PNs in pageNos),default=0)
    # TODO: we assume all pages are 'normal' pages
    # (not 'front' pages in Roman letters etc)
    headingsR = normaliseDepth(R,hReduce(headings)) # (hType,hText,recNo,textNo)
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
    <meta name="ncc:totalTime" content="{hmsTime(totalSecs)}" />
    <meta name="ncc:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}" />
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:depth" content="{max(int(h.hTag[1:]) for h in headingsR if h.hTag.startswith('h'))+(1 if any(h.hTag=='div' for h in headingsR) else 0)}" />
    <meta name="ncc:files" content="{2+len(headings)*(3 if hasFullText else 2)+len(R.imageFiles)}" />
  </head>
  {f'<docTitle><text>{R.title}</text></docTitle>' if R.daisy3 else ''}
  {f'<docAuthor><text>{R.creator}</text></docAuthor>' if R.daisy3 else ''}
  <{'navMap id="navMap"' if R.daisy3 else 'body'}>"""+''.join((f"""
    <navPoint id="s{s+1}" class="{t.hTag}" playOrder="{s+1}">
      <navLabel><text>{t.hLine}</text>{'' if recTimeTxts[t.recNo][2*t.itemNo]==recTimeTxts[t.recNo][2*t.itemNo+2] else f'''<audio src="{t.recNo+1:04d}.mp3" clipBegin="{hmsTime(recTimeTxts[t.recNo][2*t.itemNo])}" clipEnd="{hmsTime(recTimeTxts[t.recNo][2*t.itemNo+2])}"/>'''}</navLabel>
      <content src="{t.recNo+1:04d}.smil#pr{t.recNo+1}.{t.itemNo}"/>
    {'</navPoint>'*numDaisy3NavpointsToClose(s,headingsR)}""" if R.daisy3 else ''.join(f"""
    <span class="page-normal" id="page{N}"><a href="{r+1:04d}.smil#t{r+1}.{after}">{N}</a></span>""" for r,PNs in enumerate(pageNos) for (PO,(after,N)) in enumerate(PNs) if (r,after)<=t[2:4] and (not s or (r,after)>headingsR[s-1][2:4]))+f"""
    <{t.hTag} class="{'section' if s or R.allow_jumps else 'title'}" id="s{s+1}">
      <a href="{t.recNo+1:04d}.smil#t{t.recNo+1}.{t.itemNo}">{t.hLine}</a>
    </{t.hTag}>""") for s,t in enumerate(headingsR))+('</navMap><pageList id="page">'+''.join(f"""
    <pageTarget class="pagenum" type="normal" value="{N}" id="page{N}" playOrder="{len(headingsR)+sum(len(P) for P in pageNos[:r])+PO+1}">
      <navLabel><text>{N}</text></navLabel>
      <content src="{r+1:04d}.smil#pr{r+1}.{after}"/>
    </pageTarget>""" for r,PNs in enumerate(pageNos) for (PO,(after,N)) in enumerate(PNs))+"""
  </pageList>
</ncx>""" if R.daisy3 else """
  </body>
</html>"""))

def addPbeforeTag(tag,num,paras):
    "Decides whether a <p> should be added before the current tag"
    return tag=='span' and (num==0 or not paras[num-1].tag=="span" or paras[num-1].text.endswith("<br />"))
def closePafterTag(tag,text,num,paras):
    "Decides whether a </p> should be added after closing the current tag"
    return tag=='span' and (text.endswith("<br />") or num+1==len(paras) or not paras[num+1].tag=='span')

def removeImages(text):
    "Removes our normalised <img> markup from text"
    return re.sub('<img src="[^"]*" [^/]*/>','',text)
def imageParagraph(R,text):
    "Pulls out our normalised <img> markup for use after the paragraph"
    return f"""{'<p><imggroup>' if R.daisy3 and re.search('<img src="',text) else ''}{''.join(re.findall('<img src="[^"]*" [^/]*/>',text))}{'</imggroup></p>' if R.daisy3 and re.search('<img src="',text) else ''}"""

def daisy3OpenLevelTags(R,tag,num,paras):
    "Gives the <levelN> tags that should be placed before the current point in the DAISY 3 format"
    if not R.daisy3: return ''
    elif not tag.startswith('h'):
        if num: return '' # will have been started
        else: return '<level1>'
    return ''.join(f'<level{n}>' for n in range(min(int(tag[1:]),next(int(paras[p].tag[1:]) for p in range(num-1,-1,-1) if paras[p].tag.startswith('h'))+1) if any(paras[P].tag.startswith('h') for P in range(num-1,-1,-1)) else 1,int(tag[1:])+1))
def daisy3CloseLevelTags(R,tag,num,paras):
    "Gives the </levelN> tags that should be placed before the current point in the DAISY 3 format"
    if not R.daisy3 or not num+1==len(paras) and not paras[num+1].tag.startswith('h'): return ''
    return ''.join(f'</level{n}>' for n in range(next(int(paras[p].tag[1:]) for p in range(num,-1,-1) if paras[p].tag.startswith('h')) if any(paras[P].tag.startswith('h') for P in range(num,-1,-1)) else 1,0 if num+1==len(paras) else int(paras[num+1].tag[1:])-1,-1))

def numDaisy3NavpointsToClose(s,headingsR):
    """Calculates the number of DAISY 3 navigation
    points that need closing after index s"""
    
    thisTag = headingsR[s]
    if thisTag.hTag.startswith('h'):
        thisDepth = int(thisTag.hTag[1])
    else: thisDepth = None # a div navpoint
    if s+1==len(headingsR): nextDepth = 1
    else:
        nextTag = headingsR[s+1]
        if nextTag.hTag.startswith('h'):
            nextDepth = int(nextTag.hTag[1])
        else: nextDepth = None # another div
    if thisDepth == nextDepth: return 1 # e.g. this is div and next is div, or same heading level
    elif nextDepth is None: return 0 # never close if it's heading followed by div
    headingNums_closed = ''.join(('' if not i.hTag.startswith('h') else i.hTag[1] if int(i.hTag[1])>=nextDepth else '0') for i in reversed(headingsR[:s+1])).split('0',1)[0]
    if thisDepth: D=thisDepth
    else: D=int(headingNums_closed[0]) # the heading before this div (TODO: this code assumes there will be one, which is currently true as these divs are generated only by verse numbering)
    N = sum(1 for j in range(nextDepth,D+1) if str(j) in headingNums_closed)
    return N+(1 if thisDepth is None else 0)

def hReduce(headings):
    """convert a list of ChapterTOCInfo lists (or
    text strings for unstructured chapters) into a
    single BookTOCInfo list"""
    return reduce(lambda a,b:a+b,[([BookTOCInfo(hType,hText,recNo,textNo) for (hType,hText,textNo) in i] if isinstance(i,list) else [BookTOCInfo('h1',i,recNo,0)]) for recNo,i in enumerate(headings)],[])

def normaliseDepth(R,items):
    """Ensure that heading items' depth conforms
    to DAISY standard, in a BookTOCInfo list"""
    
    if R.allow_jumps: return items
    curDepth = 0
    for i in range(len(items)):
      ii = items[i] # TagAndText or BookTOCInfo
      if ii[0].lower().startswith('h'):
        depth = int(ii[0][1:])
        if depth > curDepth+1:
            if isinstance(ii,BookTOCInfo): items[i]=BookTOCInfo(f'h{curDepth+1}',ii.hLine,ii.recNo,ii.itemNo)
            else: items[i]=TagAndText(f'h{curDepth+1}',ii.text)
            curDepth += 1
        else: curDepth = depth
    return items

def master_smil(R,headings = [],
                totalSecs = 0):
    "Compile the master smil for a DAISY file"
    headings = hReduce(headings)
    return f"""<?xml version="1.0"?>
<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">
<smil>
  <head>
    <meta name="dc:title" content="{deHTML(R.title)}" />
    <meta name="dc:format" content="Daisy 2.02" />
    <meta name="ncc:generator" content="{generator}" />
    <meta name="ncc:timeInThisSmil" content="{hmsTime(totalSecs)}" />
    <layout>
      <region id="textView" />
    </layout>
  </head>
  <body>"""+''.join(f"""
    <ref title="{deHTML(t.hLine)}" src="{t.recNo+1:04d}.smil#t{t.recNo+1}.{t.itemNo}" id="ms_{s+1:04d}" />""" for s,t in enumerate(headings))+"""
  </body>
</smil>
"""

def timeAdjust(textsAndTimes,secsThisRecording):
    """Ensure textsAndTimes starts at the
    beginning of the recording, and ends at the
    end.  Necessary for some players to play all
    of the audio."""
    if not isinstance(textsAndTimes,list): textsAndTimes=[textsAndTimes]
    return [0.0]+textsAndTimes[(1 if isinstance(textsAndTimes[0],float) else 0):(-1 if isinstance(textsAndTimes[-1],float) else len(textsAndTimes))]+[secsThisRecording]

def section_smil(R, recNo=1,
                 totalSecsSoFar=0,
                 secsThisRecording=0,
                 startP=0,
                 textsAndTimes=[]):
    "Compile a section SMIL for a DAISY file"
    textsAndTimes = timeAdjust(textsAndTimes,secsThisRecording)
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">' if R.daisy3 else '<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">'}
{'<smil xmlns="http://www.w3.org/2001/SMIL20/">' if R.daisy3 else '<smil>'}
  <head>
    {'<meta name="dtb:uid" content=""/>' if R.daisy3 else '<meta name="dc:format" content="Daisy 2.02" />'}
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:generator" content="{generator}" />
    <meta name="{'dtb' if R.daisy3 else 'ncc'}:totalElapsedTime" content="{hmsTime(totalSecsSoFar)}" />""" + ("" if R.daisy3 else f"""
    <meta name="ncc:timeInThisSmil" content="{hmsTime(secsThisRecording)}" />
    <meta name="title" content="{deHTML(textsAndTimes[1][1])}" />
    <meta name="dc:title" content="{deHTML(textsAndTimes[1][1])}" />
    <layout>
      <region id="textView" />
    </layout>""")+f"""
  </head>
  <body>
    <seq id="sq{recNo}" dur="{hmsTime(secsThisRecording) if R.daisy3 else f'{secsThisRecording:.3f}s'}" fill="remove">"""+"".join(f"""
      <par {'' if R.daisy3 else 'endsync="last" '}id="pr{recNo}.{i//2}">
        <text id="t{recNo}.{i//2}" src="{recNo:04d}.{'xml' if R.daisy3 else 'htm'}#p{startP+i//2}" />
        {'' if R.daisy3 or textsAndTimes[i-1]==textsAndTimes[i+1] else f'<seq id="sq{recNo}.{i//2}a">'}
          {'' if textsAndTimes[i-1]==textsAndTimes[i+1] else f'''<audio src="{recNo:04d}.mp3" clip{'B' if R.daisy3 else '-b'}egin="{hmsTime(textsAndTimes[i-1]) if R.daisy3 else f'npt={textsAndTimes[i-1]:.3f}s'}" clip{'E' if R.daisy3 else '-e'}nd="{hmsTime(textsAndTimes[i+1]) if R.daisy3 else f'npt={textsAndTimes[i+1]:.3f}s'}" id="aud{recNo}.{i//2}" />'''}
        {'' if R.daisy3 or textsAndTimes[i-1]==textsAndTimes[i+1] else '</seq>'}
      </par>{''.join(f'<par><text id="t{recNo}.{i//2}.{j}" src="{recNo:04d}.xml#{re.sub(".*"+chr(34)+" id=.","",imageID)}"/></par>' for j,imageID in enumerate(re.findall('<img src="[^"]*" id="[^"]*',textsAndTimes[i][1]))) if R.daisy3 else ''}""" for i in range(1,len(textsAndTimes),2))+"""
    </seq>
  </body>
</smil>
""")
# (do not omit text with 0-length audio altogether, even in Daisy 2: unlike image tags after paragraphs, it might end up not being displayed by EasyReader etc.  Omitting audio does NOT save being stopped at the beginning of the chapter when rewinding by paragraph: is this a bug or a feature?)

def deBlank(s):
    """Remove blank lines from s
    (does not currently remove the first line if
    blank).  Used so that optional items can be
    placed on their own lines in our format-string
    templates for DAISY markup.
    """
    return re.sub("\n( *\n)+","\n",s)

def hmsTime(secs):
    """Formats a floating-point number of seconds
    into the DAISY standard hours:minutes:seconds
    with fractions to 3 decimal places.  (Some
    old DAISY readers can crash if more than 3
    decimals are used, so we must stick to 3)"""
    
    return f"{int(secs/3600)}:{int(secs/60)%60:02d}:{secs%60:06.3f}"

def deHTML(t):
    """Remove HTML tags from t, collapse
    whitespace and escape quotes so it can be
    included in an XML attribute"""
    
    return re.sub(r'\s+',' ',re.sub('<[^>]*>','',t)).replace('"','&quot;').strip()

def package_opf(R,hasFullText,numRecs,totalSecs):
    "Make the package OPF for a DAISY 3 file"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE package
  PUBLIC "+//ISBN 0-9673008-1-9//DTD OEB 1.2 Package//EN" "http://openebook.org/dtds/oeb-1.2/oebpkg12.dtd">
<package xmlns="http://openebook.org/namespaces/oeb-package/1.0/" unique-identifier="{R.url}">
   <metadata>
      <dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
         <dc:Format>ANSI/NISO Z39.86-2005</dc:Format>
         <dc:Language>{R.lang}</dc:Language>
         <dc:Date>{R.date}</dc:Date>
         <dc:Publisher>{R.publisher}</dc:Publisher>
         <dc:Title>{R.title}</dc:Title>
         <dc:Identifier id="{R.url}"/>
         <dc:Creator>{R.creator}</dc:Creator>
         <dc:Type>text</dc:Type>
      </dc-metadata>
      <x-metadata>
         <meta name="dtb:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}"/>
         <meta name="dtb:totalTime" content="{hmsTime(totalSecs)}"/>
         <meta name="dtb:multimediaContent" content="audio,text{',image' if R.imageFiles else ''}"/>
         <meta name="dtb:narrator" content="{deHTML(R.reader)}"/>
         <meta name="dtb:producedDate" content="{R.date}"/>
      </x-metadata>
   </metadata>
   <manifest>
      <item href="package.opf" id="opf" media-type="text/xml"/>"""+''.join(f"""
      <item href="{i:04d}.mp3" id="opf-{i}" media-type="audio/mpeg"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i+1}{u[u.rindex("."):]}" id="opf-{i+numRecs+1}" media-type="image/{u[u.rindex(".")+1:].lower().replace("jpg","jpeg")}"/>""" for i,u in enumerate(R.imageFiles))+f"""
      <item href="dtbook.2005.basic.css" id="opf-{len(R.imageFiles)+numRecs+1}" media-type="text/css"/>"""+''.join(f"""
      <item href="{i:04d}.xml" id="opf-{i+len(R.imageFiles)+numRecs+1}" media-type="application/x-dtbook+xml"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i:04d}.smil" id="{i:04d}" media-type="application/smil+xml"/>""" for i in range(1,numRecs+1))+"""
      <item href="navigation.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>
      <item href="text.res" id="resource" media-type="application/x-dtbresource+xml"/>
   </manifest>
   <spine>"""+"".join(f"""
      <itemref idref="{i:04d}"/>""" for i in range(1,numRecs+1))+"""
   </spine>
</package>
"""

def text_htm(R,paras,offset=0):
    """Format the text, as htm for DAISY 2 or xml
    for DAISY 3.
    paras = TagAndText list, text is xhtml i.e. & use &amp; etc."""
    
    return deBlank(f"""<?xml version="1.0"{' encoding="utf-8"' if R.daisy3 else ''}?>{'<?xml-stylesheet type="text/css" href="dtbook.2005.basic.css"?>' if R.daisy3 else ''}
{'<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">' if R.daisy3 else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-2"' if R.daisy3 else f'html lang="{R.lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{R.lang}">
    <head>
        {'<meta name="dt:version" content="1.0" />' if R.daisy3 else ''}
        {f'<meta name="dc:Title" content="{deHTML(R.title)}"/>' if R.daisy3 else f'<title>{R.title}</title>'}
        {f'<meta name="dc:Creator" content="{deHTML(R.creator)}"/>' if R.daisy3 else ''}
        {f'<meta name="dc:Publisher" content="{deHTML(R.publisher)}"/>' if R.daisy3 else ''}
        {f'<meta name="dc:Date" content="{R.date}"/>' if R.daisy3 else ''}
        {f'<meta name="dc:Language" content="{R.lang}" />' if R.daisy3 else ''}
        {f'<meta name="dc:identifier" content="{R.url}" />' if R.daisy3 else ''}
        {f'<meta name="dtb:uid" content="{R.url}"/>' if R.daisy3 else '<meta content="text/html; charset=utf-8" http-equiv="content-type"/>'}
        <meta name="generator" content="{generator}"/>
    </head>
    <{'book' if R.daisy3 else 'body'}>
        {f'<frontmatter><doctitle>{R.title}</doctitle><docauthor>{R.creator}</docauthor></frontmatter><bodymatter>' if R.daisy3 else ''}
"""+"\n".join(f"""{daisy3OpenLevelTags(R,tag,num,paras)}{'<p>' if addPbeforeTag(tag,num,paras) else ''}<{tag} id=\"p{num+offset}\"{(' class="word"' if len(text.split())==1 else ' class="sentence"') if tag=='span' else ''}>{re.sub(" *<br />$","",removeImages(text))}</{tag}>{'</p>' if closePafterTag(tag,text,num,paras) else ''}{imageParagraph(R,text)}{daisy3CloseLevelTags(R,tag,num,paras)}""" for num,(tag,text) in enumerate(normaliseDepth(R,paras)))+f"""
    </{'bodymatter></book' if R.daisy3 else 'body'}>
</{'dtbook' if R.daisy3 else 'html'}>
""")

def er_book_info(durations):
    """Return the EasyReader book info.
    durations = list of secsThisRecording"""
    
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

version = float(__doc__.split()[1]) # for code importing the module to check

# __all__ cuts down what's listed in help(anemone), w/out stopping other things being available via dir() and help(symbol).  Might be useful especially because the default help() lists all classes, including namedtuple classes, with all default methods, before even getting to the anemone() function.  They can have other things *after* anemone(), but we want them to see anemone() as near to the top of the documentation as possible.  So let's take out the classes.
__all__ = sorted(n for n,s in globals().items() if (isinstance(s,type(anemone)) or n=='version') and n not in ['run','unquote','urlopen','which'])

# ruff check anemone.py
# ruff: noqa: E401 # multiple imports on one line
# - sorry, I can't see what's wrong with that
# ruff: noqa: E402 # import not at top of file
# - sorry but I like having the docs first...
# ruff: noqa: E701 # colon without newline
# - sorry, coding in large print with wraparound on means newlines are more of an overhead
# ruff: noqa: E702 # semicolon statements - ditto
