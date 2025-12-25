#!/usr/bin/env python3
"""
Anemone 1.991 (https://ssb22.user.srcf.net/anemone)
(c) 2023-25 Silas S. Brown.  License: Apache 2

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

def anemone(*files,**options) -> list[str]:
    """This function can be called by scripts that
    import anemone: simply put the equivalent of
    the command line into 'files' and 'options'.

    You can also specify a JSON dictionary instead
    of the name of a JSON file, and/or an HTML
    string instead of the name of an HTML file
    (this can also be done on the command line
    with careful quoting).

    Additionally, you can set the options
    warning_callback, info_callback and/or
    progress_callback.  These are Python callables
    to log an in-progress conversion (useful for
    multi-threaded UIs).  warning_callback and
    info_callback each take a string, and
    progress_callback takes an integer percentage.
    If warning_callback or info_callback is set,
    the corresponding information is not written
    to standard error.

    If you do not give this function any arguments
    it will look at the system command line.

    Return value is a list of warnings, if any."""

    try:
        R=Run(*files,**options)
        R.check() ; R.import_libs(files)
        R.set_thread_limit()
        R.write_all(R.get_texts())
        return R.warnings
    except AnemoneError: raise
    except Exception as e: raise AnemoneError("Unhandled",e) # ensure wrapped

def populate_argument_parser(args) -> None:
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
    args.add_argument("--auto-markers-model",
                      default="",help="""
instead of accepting JSON timing markers, guess
them using speech recognition with the
whisper-cli command and this voice model
(currently only at paragraph level, and
every paragraph matching marker-attribute
will be included)""")
    args.add_argument("--marker-attribute",
                      default="data-pid",help="""
the attribute used in the HTML to indicate a
segment number corresponding to a JSON time marker
entry, default is data-pid""")
    args.add_argument("--marker-attribute-prefix",
                      default="", help="""
When extracting all text for chapters that don't
have timings, ignore any marker attributes whose
values don't start with the given prefix""")
    args.add_argument("--page-attribute",
                      default="data-no",help="""
the attribute used in the HTML to indicate a page number, default is data-no""")
    args.add_argument("--image-attribute",
                      default="data-zoom",help="""
the attribute used in the HTML to indicate an
absolute image URL to be included in the DAISY
file, default is data-zoom""")
    args.add_argument("--line-breaking-classes",
                      default="",help="""
comma-separated list of classes used in HTML SPAN
tags to substitute for line and paragraph breaks""")
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
to do it instead""")
    args.add_argument("--reload",dest="refetch",
                      action="store_true",help="""
if images etc have already been fetched from URLs,
fetch them again without If-Modified-Since""")
    args.add_argument("--delay",default=0,help="""
minimum number of seconds between URL fetches (default none)""")
    args.add_argument("--retries",default=0,help="""
number of times to retry URL fetches on timeouts
and unhandled exceptions (default no retries)""")
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
(this requires LAME or miniaudio/lameenc)""")
    args.add_argument("--max-threads",
                      default=0, help="""
Maximum number of threads to use for MP3 re-coding.
If set to 0 (default), the number of CPU cores is
detected and used, and, if called as a module, multiple
threads calling anemone() share the same pool of
MP3 re-coding threads.  This is usually most efficient.
If set to anything other than 0, a local pool of threads
is used for MP3 re-coding (instead of sharing the pool
with any other anemone() instances) and it is limited to
the number of threads you specify.
If calling anemone as a module and you want to limit the
pool size but still have a shared pool, then don't set this
but instead call set_max_shared_workers().""")
# Both can be overridden by the environment variable
# ANEMONE_THREAD_LIMIT (e.g. 0 for unlimited).
    args.add_argument("--allow-jumps",
                      action="store_true",help="""
Allow jumps in heading levels e.g. h1 to h3 if the
input HTML does it.  This seems OK on modern
readers but might cause older reading devices to
give an error.  Without this option, headings are
promoted where necessary to ensure only
incremental depth increase.""") # might cause older reading devices to give an error: and is also flagged up by the validator
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
titles.  Use blank titles for chapters that
already have them in the markup.""")
    args.add_argument("--toc-titles",
                      default="",help="""
Comma-separated list of titles to use for the
table of contents.  This can be set if you need
more abbreviated versions of the chapter titles
in the table of contents, while leaving the
full versions in the chapters themselves.
Again you may use a list instead of a
comma-separated string if using the module.
Any titles missing or blank in this list will
be taken from the full chapter titles instead.""")
    args.add_argument("--chapter-heading-level",default=1,help="Heading level to use for chapters that don't have titles")
    args.add_argument("--warnings-are-errors",action="store_true",help="Treat warnings as errors")
    args.add_argument("--ignore-chapter-skips",action="store_true",help="Don't emit warnings or errors about chapter numbers being skipped")
    args.add_argument("--dry-run",action="store_true",help="Don't actually output DAISY, just check the input and parameters")
    args.add_argument("--version",action="store_true",help="Just print version number and exit (takes effect only if called from the command line)")

generator=__doc__.strip().split('\n')[0] # string we use to identify ourselves in HTTP requests and in Daisy files

def get_argument_parser():
    "populates an ArgumentParser for Anemone"

    from argparse import ArgumentParser
    if __name__=="__main__": AP=ArgumentParser
    else:
        # module: wrap it so errors don't exit
        class AP(ArgumentParser):
            def error(self, message):
                raise AnemoneError(message)
    args = AP(
        prog="anemone",
        description=generator,
        fromfile_prefix_chars='@')
    populate_argument_parser(args)
    return args

import time, sys, os, re, json, traceback, tempfile, difflib

if __name__ == "__main__" and "--version" in sys.argv:
    print (generator)
    raise SystemExit

import textwrap, inspect
from collections import namedtuple as NT
from functools import reduce
from subprocess import run, PIPE, getoutput
from zipfile import ZipFile, ZIP_DEFLATED
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from urllib.parse import unquote
from pathlib import Path # Python 3.5+
from shutil import which
from io import BytesIO

class DocUpdater:
    """Utility class to copy the argument parser
    help text into the module help text, so you
    can read via: import anemone; help(anemone)"""
    def __init__(self,p):
        self.p = p
        self.p.__doc__ += "\nOptions when run as a command-line utility:\n"
    def add_argument(self,*args,**kwargs):
        self.p.__doc__ += f"\n* {(chr(10)+'  ').join(textwrap.wrap((args[0]+': ' if args[0].startswith('--') else '')+re.sub(chr(10)+' *',' ',kwargs['help']).strip(),50))}\n"
populate_argument_parser(DocUpdater(
    sys.modules[__name__]))

def error(m) -> None:
    """Anemone error handler.  If running as an
    application, print message and error-exit.  If
    running as a module, raise an AnemoneError."""

    if __name__=="__main__": sys.stderr.write(f"Error: {m}\n"),sys.exit(1)
    else: raise AnemoneError(str(m))
class AnemoneError(Exception):
    # "About the beach are a broken spar, A pale anemone's torn sea-star
    # And scattered scum of the waves' old war, as the tide comes tumbling in." - Cale Young Rice
    """This exception type is used by Anemone to
    signal parameter errors etc to its caller when
    it is being called as a module.  If the
    environment variable ANEMONE_DEBUG is set,
    it will also report its construction on the
    standard error stream regardless of how the
    calling code handles it (might be useful to
    diagnose misbehaving calling environments)"""
    def __init__(self, message, exception=None):
        if exception is not None:
            if __name__=="__main__" or "ANEMONE_DEBUG" in os.environ:
                sys.stderr.write(traceback.format_exc())
            tb = exception.__traceback__
            while tb.tb_next: tb = tb.tb_next
            message += f""" {exception.__class__.__name__
            }: {exception} {
            f"at line {tb.tb_lineno} (v{version})" if
            tb.tb_frame.f_globals['__name__'] == __name__
            else f'''at {tb.tb_frame.f_globals['__name__']
            }:{tb.tb_lineno}'''}"""
        Exception.__init__(self,message)
        if "ANEMONE_DEBUG" in os.environ:
            sys.stderr.write(f"Got AnemoneError: {message}\n")

# These must be defined before Run for type hints:
PageInfo = NT('PageInfo',['duringId','pageNo'])
TagAndText = NT('TagAndText',['tag','text'])
TextsAndTimesWithPages = NT('TextsAndTimesWithPages',['textsAndTimes','pageInfos'])
ChapterTOCInfo = NT('ChapterTOCInfo',['hTag','hLine','itemNo'])
BookTOCInfo = NT('BookTOCInfo',['hTag','hLine','recNo','itemNo'])
del NT

class Run():
  """The parameters we need for an Anemone run.
  Constructor can either parse args from the
  command line, or from anemone() caller."""
  def __init__(self,*inFiles,**kwargs):
    R = self
    R.audioData,R.filenameTitles,R.filenameExt = [],[],[]
    R.jsonData = []
    R.textData,R.htmlData = [],[]
    R.imageFiles,R.outputFile = [],None
    R.warnings = []
    if inFiles: # being called as a module
        R.__dict__.update(
            get_argument_parser().parse_args(
                ["placeholder"] +
                [a for k,v in kwargs.items()
                 for a in
                 ['--'+k.replace('_','-'),str(v)]
                 if type(v) in [str,int,float]])
            .__dict__)
        R.files = inFiles # may mix dict + string, even in same category especially if using "skip", so don't separate types
    else: # being called from the command line
        R.__dict__.update(get_argument_parser().parse_args().__dict__)
    R.__dict__.update((k,v)
                      for k,v in kwargs.items()
                      if type(v) not in [str,int,float,type(None)]) # (None means keep the default from parse_args; boolean and bytes we might as well handle directly; list e.g. merge_books should bypass parser; ditto session object for cache, a type we can't even name here if requests_cache is not installed)
    # Ensure numeric arguments are not strings (since at least some versions of argparse will return strings if defaults overridden)
    for k in ['delay','retries','max_threads']:
        try: R.__dict__[k] = float(R.__dict__[k])
        except ValueError: error(f"{k} must be a number")
    R.__dict__['retries'] = int(R.__dict__['retries']) # "2.0" OK but "2.1" would loop if not take int
    for k in ['merge_books','chapter_titles','toc_titles',
              'line_breaking_classes']:
        if not isinstance(R.__dict__[k],list):
            if not isinstance(R.__dict__[k],str): error(f"{k} must be Python list or comma-separated string")
            R.__dict__[k]=R.__dict__[k].split(',') # comma-separate if coming from the command line, but allow lists to be passed in to the module
            if R.__dict__[k]==['']:
                R.__dict__[k] = []
    try: R.bookTitlesAndNumChaps = [
            (n,int(v))
            for n,v in [
                    (b if isinstance(b,tuple)
                     else b.split('/'))
                    for b in R.merge_books if b]]
    except: error(f"Unable to parse merge-books={R.merge_books}") # noqa: E722
    # also ensure merge_books extra headings sync'd with toc_titles:
    insertPt = 0
    for _,nc in R.bookTitlesAndNumChaps:
        R.toc_titles.insert(insertPt,"")
        insertPt += nc+1
    R.progress_loopStart(len(R.files),15)
    htmlSeen = {}
    for i,f in enumerate(R.files):
        R.progress(i)
        fOrig = f
        if isinstance(f,dict):
            # support direct JSON pass-in as dict
            R.jsonData.append(f)
            R.check_for_JSON_transcript()
            continue
        elif f=="skip": # we're 'full text some audio' and we're skipping audio for a chapter
            R.jsonData.append(None) ; continue
        elif isinstance(f,str) and f.lower().endswith(f"{os.extsep}zip"):
            if R.outputFile: error(f"Only one {os.extsep}zip output file may be specified")
            R.outputFile = f ; continue
        elif isinstance(f,str) and re.match("https?://",f):
            try: f=fetch(f,R.cache,R.refresh,R.refetch,R.delay,R.user_agent,R.retries,R)
            except HTTPError as e:
                error(f"Unable to fetch {f}: {e}")
        elif delimited(f,'{','}'): pass # handled below
        elif delimited(f,'<','>'): pass # handled below
        elif isinstance(f,bytes) and (f.startswith(b"RIFF") or f.startswith(b"ID3") or f.startswith(b"\xFF")): # audio data passed in to anemone() function
            R.audioData.append(f)
            R.filenameTitles.append("untitled")
            R.filenameExt.append("wav" if f.startswith(b"RIFF") else "mp3")
            continue
        elif not os.path.isfile(f): error(f"File not found: {f}")
        else: f = open(f,"rb").read()
        if delimited(f,'{','}'):
            try: f = json.loads(f)
            except: error(f"Could not parse JSON {fOrig}") # noqa: E722
            R.jsonData.append(f)
            R.check_for_JSON_transcript()
        elif delimited(f,'<','>'):
            fToShow = fOrig
            if len(fToShow) > 103:
                fToShow = fToShow[:50]+"..."+fToShow[-50:]
            if f in htmlSeen: error(f"Duplicate HTML input documents: {htmlSeen[f]} (document {R.htmlData.index(f)+1}) and {fToShow} (document {len(R.htmlData)+1})")
            R.htmlData.append(f)
            htmlSeen[f] = fToShow
        elif fOrig.lower().endswith(f"{os.extsep}mp3") or fOrig.lower().endswith(f"{os.extsep}wav"):
            R.audioData.append(f)
            R.filenameTitles.append(
                (fOrig[fOrig.rfind('/')+1:] if
                 re.match('https?://',fOrig)
                 else os.path.split(fOrig)[1])
                [:fOrig.rindex('.' if re.match('https?://',fOrig)
                               else os.extsep)])
            R.filenameExt.append(fOrig[fOrig.rindex(os.extsep)+1:])
        elif fOrig.lower().endswith(f"{os.extsep}txt"):
            try: f = f.decode('utf-8').strip()
            except UnicodeDecodeError: error(f"Couldn't decode {fOrig} as UTF-8")
            R.textData.append(f)
        else: error(f"Format of '{fOrig}' has not been recognised")
    R.progress(len(R.files))
    if R.htmlData: # check for text-only DAISY:
        if not R.jsonData:
            R.jsonData=[None]*len(R.htmlData)
        if not R.audioData:
            R.audioData=[None]*len(R.htmlData)
            R.filenameTitles=[""]*len(R.htmlData)
            R.filenameExt=[""]*len(R.htmlData)
    # and check for full-text part-audio DAISY:
    if len(R.jsonData) > len(R.audioData):
        for c,i in enumerate(R.jsonData):
            if i is None:
                R.audioData.insert(c,None)
                R.filenameTitles.insert(c,"")
                R.filenameExt.insert(c,"")
    if not R.outputFile:
        R.outputFile=f"output_daisy{os.extsep}zip"
    if not R.title: R.title=re.sub("(?i)[ _-]daisy[0-9]?$","",R.outputFile.replace(f"{os.extsep}zip",""))
  def check(self) -> None:
    """Checks we've got everything.
    You may omit calling this if you're creating
    a temporary Run just to call something like
    check_for_JSON_transcript and get its HTML."""
    R = self
    if R.htmlData and not R.auto_markers_model and any(a and not j for a,j in zip(R.audioData,R.jsonData)): error("Full text and audio without time markers is not yet implemented (but you can give an empty markers list if you want to combine a whole chapter into one navigation point)")
    if R.jsonData and not R.htmlData: error("Time markers without full text is not implemented")
    if R.htmlData and R.textData: error("Combining full text with title-only text files is not yet implemented.  Please specify full text for everything or just titles for everything, not both.")
    if R.jsonData and not len(R.audioData)==len(R.jsonData): error(f"If JSON marker files are specified, there must be exactly one JSON file for each recording file.  We got f{len(R.jsonData)} JSON files and f{len(R.audioData)} recording files.")
    if R.textData and not len(R.audioData)==len(R.textData): error(f"If text files are specified, there must be exactly one text file for each recording file.  We got f{len(R.textData)} text files and f{len(R.audioData)} recording files.")
    if R.htmlData and not len(R.audioData)==len(R.htmlData): error(f"If HTML documents with audio are specified, there must be exactly one HTML document for each recording.  We got f{len(R.htmlData)} HTML documents and f{len(R.audioData)} recordings.")
    if not R.htmlData and not R.textData and not R.audioData: error("No input given")
    if not re.match("[a-z]{2,3}($|-)",R.lang): R.warning(f"lang '{R.lang}' doesn't look like a valid ISO-639 language code") # this should perhaps be an error
    if R.date and not re.match("([+-][0-9]*)?[0-9]{4}-[01][0-9]-[0-3][0-9]$",R.date): error("date (if set) should be in ISO 8601's YYYY-MM-DD format")
    s = set()
    for t in ['marker_attribute',
              'page_attribute',
              'image_attribute']:
        v=R.__dict__[t] ; s.add(v)
        if not re.match(r"[^"+chr(0)+"- /=>'"+'"'+"]+$",v) or '\n' in v:
            if __name__=="__main__":
                t="--"+t.replace("_","-")
            error(f"{t} must be a valid HTML attribute name")
    if not len(s)==3: error("marker_attribute, page_attribute and image_attribute must be different")
    # Do a few checks on the filename (but not its full path).
    # Run constructor guarantees R.outputFile ends with ".zip":
    outDir,filename = os.path.split(R.outputFile[:-4])
    outRpt = f"{filename}{f' (in {R.outputFile})' if outDir else ''}"
    if "daisy" not in filename: R.warning(f"Output filename {outRpt} does not contain 'daisy'")
    if filename==f"output_daisy{os.extsep}zip": R.warning(f"Outputting to default filename {outRpt}.  It's better to set an output filename that identifies the publication.")
    if not re.sub("[._-]","",filename.replace("daisy","")): R.warning(f"Output filename {outRpt} does not seem to contain any meaningful publication identifier")
    if re.search('[%&?@*#{}<>!:+`=|$]',filename): R.warning(f"Output filename {outRpt} contains characters not allowed on Microsoft Windows")
    if re.search('[ "'+"']",filename): R.warning(f"Space or quote in output filename may complicate things for command-line users: {outRpt}")
  def set_thread_limit(self) -> None:
    "Set max_threads for MP3 recoding or speech recognition"
    if self.max_threads:
        # allow override by ANEMONE_THREAD_LIMIT, but only if max_threads is actually set (otherwise we'll use the shared worker with that limit)
        self.max_threads = int(os.environ.get("ANEMONE_THREAD_LIMIT",self.max_threads))
        if self.max_threads < 1: error(f"max-threads, if specified, should be at least 1: {self.max_threads}")
  def import_libs(self,files) -> None:
    """Checks availability of, and imports, the
       libraries necessary for our run.  Not all
       of them are needed on every run: for
       example, if we're making a DAISY book with
       no audio, we won't need Mutagen."""
    R = self
    global mutagen, BeautifulSoup
    if R.audioData and any(R.audioData):
        try: import mutagen, mutagen.mp3
        except ImportError: error('Anemone needs the Mutagen library to determine play lengths.\nPlease do: pip install mutagen\nIf you are unable to use pip, it may also work to download mutagen source and move its "mutagen" directory to the current directory.')
    if R.htmlData:
        try: from bs4 import BeautifulSoup
        except ImportError: error('Anemone needs the beautifulsoup4 library to parse HTML.\nPlease do: pip install beautifulsoup4\nIf you are unable to use pip, it may also work to download beautifulsoup4 source and move its "bs4" directory to the current directory.')
    if R.mp3_recode or any(f.strip().lower().
                           endswith(
                               f"{os.extsep}wav")
                           for f in files
                           if isinstance(f,str)):
        check_we_got_LAME()
    if R.auto_markers_model and not which('whisper-cli'):
        error("auto-markers-model requires whisper-cli in PATH")
  def warning(self,warningText:str,action:str="") -> None:
    """Logs a warning (or an error if
       warnings_are_errors is set)"""
    if self.warnings_are_errors:error(warningText)
    warningText += action # (the action that will be taken if not warnings_are_errors)
    self.warnings.append(warningText)
    if not __name__=="__main__" and "ANEMONE_DEBUG" in os.environ:
        sys.stderr.write(f"Anemone-Warning: {warningText}\n") # even if warning_callback overridden, do this as well
    try: self.warning_callback(warningText)
    except Exception as e: raise AnemoneError("warning_callback exception",e) # don't ignore: might mean a GUI app is shutting down and we need to remove an in-progress zip before a timeout
  def info(self,text:str,newline:bool=True)->None:
      if "info_callback" in self.__dict__:
          if text:
              try: self.info_callback(text)
              except Exception as e: raise AnemoneError("info_callback exception",e) # don't ignore, as above
          if "ANEMONE_DEBUG" not in os.environ: return
      sys.stderr.write(f"{text}{chr(10) if newline else ''}")
      sys.stderr.flush()
  def warning_callback(self,text:str) -> None:
     "overridden by passing in a callable"
     sys.stderr.write(f"WARNING: {text}\n")
  def progress_loopStart(self,i:int,frac:int) -> None:
      """Helps with progress logging when
         progress_callback is set.  Prepares for a
         loop of 'i' iterations to take 'frac' %
         of the total progress."""
      if "next_base_percent" in self.__dict__:
          self.base_percent = self.next_base_percent
      else: self.base_percent = 0
      self.prog_N,self.prog_D = frac,max(1,i)
      if not i: self.progress(1) # empty loop: just say all 'done'
      self.next_base_percent = self.base_percent + frac
      assert self.next_base_percent <= 100
  def progress(self,i:int) -> None:
      "logs progress if progress_callback is set"
      if "progress_callback" not in self.__dict__:
          return
      if "old_progress" not in self.__dict__:
          self.old_progress = 0
      percentage = self.base_percent + int(
          i * self.prog_N / self.prog_D)
      if percentage <= self.old_progress: return
      try: self.progress_callback(percentage)
      except Exception as e: raise AnemoneError("progress_callback exception",e) # don't ignore, as above
      self.old_progress = percentage
  def check_for_JSON_transcript(self) -> None:
    """Checks to see if the last thing added to
    the Run object is a JSON podcast transcript,
    and converts it to HTML + time markers"""
    R = self
    if isinstance(R.jsonData[-1].get(
            "segments",None),list) and all(
                isinstance(s,dict) and
                "startTime" in s and "body" in s
                for s in R.jsonData[-1]["segments"]): # looks like JSON transcript format instead of markers format
        curSpeaker=None ; bodyList = []
        for s in R.jsonData[-1]["segments"]:
            bodyList.append(s["body"])
            s=s.get("speaker",curSpeaker)
            if not s==curSpeaker:
                curSpeaker,bodyList[-1] = s,f"[{s}] {bodyList[-1]}"
                if len(bodyList)>1:
                    bodyList[-2] += "<br>"
        R.htmlData.append(' '.join(
            f'<span {R.marker_attribute}="{R.marker_attribute_prefix}{i}">{c}</span>' for i,c in enumerate(bodyList) if c))
        R.jsonData[-1]={"markers":[
            {"id":f"{i}","time":t}
            for i,t in enumerate(
                    s["startTime"] for s in R.jsonData[-1]["segments"])
            if bodyList[i]]}
  def get_null_jsonData(self,h) -> dict:
    """Generate no-audio JSON for internal use
    when making text-only DAISY files from HTML,
    or no-timings JSON for an audio+text chapter.
    In this case we assume any element with any
    marker-attribute should be extracted."""
    if self.marker_attribute == 'id' and not self.marker_attribute_prefix and not hasattr(self,"warned_about_prefix"):
        self.warning("You've set marker attribute to 'id' and have chapters without audio-timing data.  This results in ALL text with ANY id being extracted for those chapters.  To avoid including site 'furniture' you might want to set marker_attribute_prefix.")
        self.warned_about_prefix = True
    return {'markers':
         [{'id':i[self.marker_attribute],'time':0}
          for i in BeautifulSoup(h,'html.parser')
          .find_all(**{self.marker_attribute:
                       True})
          if i[self.marker_attribute].startswith(
                  self.marker_attribute_prefix)]}
  def get_texts(self) -> list:
    """Gets the text markup required for the run,
    extracting it from HTML (guided by JSON IDs)
    if we need to do that."""
    R = self
    if R.textData: return R.textData # section titles only, from text files
    elif not R.htmlData: return R.filenameTitles # section titles only, from sound filenames
    recordingTexts = []
    for h,j,audioData,filenameExt in zip(R.htmlData,R.jsonData,R.audioData,R.filenameExt):
        if j is None: # skip audio this chapter
            j = R.get_null_jsonData(h)
            include_alt_tags_in_text = True
        else: include_alt_tags_in_text = False # because we won't be able to match it up to the audio
        markers = j['markers']
        if not markers: # empty markers list
            markers = R.get_null_jsonData(h)['markers']
            # - rely on merge0lenSpans to merge whole chapter
        want_pids, markerDxToWantPidDx = [], {}
        for i,m in enumerate(markers):
            err = checkJsonAttr(m,"id")
            if err:
                R.warning(f"Cannot process JSON {len(recordingTexts)+1} marker {i+1}: {err}",".  Ignoring this marker.")
            else:
                markerDxToWantPidDx[i] = len(want_pids)
                want_pids.append(jsonAttr(m,"id"))
        extractor = PidsExtractor(R,want_pids)
        extractor.handle_soup(
            BeautifulSoup(h, 'html.parser'),
            include_alt=include_alt_tags_in_text)
        rTxt = []
        for i in range(len(markers)):
            if i not in markerDxToWantPidDx: continue # bad id on this one
            err = checkJsonAttr(markers[i],"time")
            if err:
                R.warning(f"Cannot process JSON {len(recordingTexts)+1} marker {i+1}: {err}",".  Ignoring this marker.")
                continue
            try: rTxt.append(parseTime(jsonAttr(markers[i],"time")))
            except ValueError:
                R.warning(f"JSON {len(recordingTexts)+1} marker {i+1} has invalid timestamp",".  Ignoring this marker.")
                continue
            if want_pids[markerDxToWantPidDx[i]] in extractor.id_to_content:
                tag,content = extractor.id_to_content[want_pids[markerDxToWantPidDx[i]]]
                content = ''.join(content).strip()
                rTxt.append(TagAndText(tag,content_fixes(content)))
                if want_pids[markerDxToWantPidDx[i]] in want_pids[:markerDxToWantPidDx[i]]:
                    warnList = [str(x+1) for x in range(len(markers)) if want_pids[markerDxToWantPidDx[x]]==want_pids[markerDxToWantPidDx[i]]]
                    R.warning(f"In JSON {len(recordingTexts)+1}, paragraph ID {want_pids[markerDxToWantPidDx[i]]} has {len(warnList)} markers ({', '.join(warnList)}), should be only one. Check for wrong IDs or missing new document.")
            else:
                R.warning(f"JSON {len(recordingTexts)+1} marker {i+1} marks paragraph ID {want_pids[markerDxToWantPidDx[i]]} which is not present in HTML {len(recordingTexts)+1}",".  Anemone will make this a blank paragraph.")
                rTxt.append(TagAndText('p',''))
        if R.auto_markers_model: fixup_times(rTxt,R.auto_markers_model,audioData,filenameExt,R.max_threads if R.max_threads else shared_executor_maxWorkers)
        recordingTexts.append(
            TextsAndTimesWithPages(rTxt,extractor.pageNos))
    return recordingTexts
  def write_all(self,recordingTexts) -> None:
    """Writes the DAISY zip and everything in it.
    Each item of recordingTexts is either 1 text
    for section title of whole recording, or a
    TextsAndTimesWithPages i.e. ([TagAndText,time,
    TagAndText,time,TagAndText],[PageInfo,...])"""
    R = self
    assert len(R.audioData) == len(recordingTexts)
    assert recordingTexts
    headings = R.getHeadings(recordingTexts)
    if R.dry_run:
        return R.info(
            f"""Dry run: {len(R.warnings) if
            R.warnings else 'no'} warning{'' if
            len(R.warnings)==1 else 's'
            } for {R.outputFile}""")
    merge0lenSpans(recordingTexts,headings,R.audioData)
    if R.mp3_recode and any(R.audioData) or any(
            not ext.lower()=="mp3" for dat,ext in zip(R.audioData,R.filenameExt) if dat): # parallelise lame if possible
        if not __name__=="__main__":
            R.info(
                f"Making {R.outputFile}...") # especially if repeatedly called as a module, better print which outputFile we're working on BEFORE the mp3s as well as after
        if R.max_threads:
            executor = ThreadPoolExecutor(max_workers=R.max_threads)
            cCount = cpu_count()
            if cCount and R.max_threads > cCount:
                R.warning(f"""specified max {R.max_threads
                } recode threads but detected only {cCount} CPUs""")
        else: executor = shared_executor
        recodeTasks=[(executor.submit(
            (recodeMP3 if R.mp3_recode or
             not ext.lower()=="mp3" else lambda x,r,m:x),
            dat, R, ext.lower()=="mp3") if dat else None)
                        for dat,ext in zip(R.audioData,R.filenameExt)]
        R.audioData = [not not d for d in R.audioData] # save RAM: can drop original MP3 once each chapter finishes re-coding, even if ahead of collector waiting for longer earlier chapter
    else: executor,recodeTasks = None,None
    try: R.write_all0(recordingTexts,headings,recodeTasks)
    except: # unhandled exception: clean up
        if R.max_threads and executor:
            try: executor.shutdown(wait=False)
            except: pass # (can't do it) # noqa: E722
        try: os.remove(R.outputFile) # incomplete
        except: pass # noqa: E722
        raise
    if R.max_threads and executor: executor.shutdown()
  def write_all0(self,recordingTexts,headings,recodeTasks) -> None:
    "Service method for write_all"
    R = self
    d,_ = os.path.split(R.outputFile)
    if d:
        Path(d).mkdir(parents=True,exist_ok=True)
    z = ZipFile(R.outputFile,"w",ZIP_DEFLATED,
                True)
    R.dataSectors = R.catalogueEntries = 0
    def writestr(n,s):
        if isinstance(s,str):
            L = len(s.encode('utf-8'))
        else: L = len(s) # bytes or bytearray
        R.dataSectors += (L+2047)//2048 # ISO 9660 sectors on a CD-ROM
        R.catalogueEntries += 1
        # Although 50+ files per catalogue sector is possible on 8.3, RockRidge can reduce this to 8, and Joliet adds a separate directory so we'd better double the expected number of cat sectors
        # Also 16 sectors are unused before start
        # 333,000 sectors on original 650M CD-ROM,
        # we can probably increase that if 650M CDs are not in use, but some non-CD readers can still go wrong when files greatly exceed this size
        if 2*((R.catalogueEntries+7)//8) + R.dataSectors + 16 > 333000 \
           and not hasattr(R,"warnedFull"):
            R.warnedFull = True
            R.warning(f"{R.outputFile} is too big for some DAISY readers")
        z.writestr(n,s)
    def D(s): return s.replace("\n","\r\n") # in case old readers require DOS line endings
    hasFullText = any(
        isinstance(t,TextsAndTimesWithPages)
        for t in recordingTexts)
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

    - This message was added by the DAISY tool
    {generator}
    not by the producers of the DAISY publication.
""")) # (it's iOS users that need this apparently, as Apple systems see the zip extension and automatically unpack it.  But we do need to manually unpack if writing to a CD-ROM for old devices.)
    # Have asked on https://apple.stackexchange.com/questions/474687/can-i-modify-my-zip-so-ios-wont-auto-unpack-it-on-download
    secsSoFar = 0
    durations = [] ; curP = 1
    R.progress_loopStart(len(recordingTexts),70)
    for recNo in range(1,len(recordingTexts)+1):
        rTxt = recordingTexts[recNo-1]
        if R.audioData[recNo-1]:
            if recodeTasks is not None:
                R.info(f"""Adding {
                    recNo:04d}.mp3...""",False)
                R.audioData[recNo-1] = recodeTasks[recNo-1].result()
                recodeTasks[recNo-1] = True # clear extra ref so data dropped below
            secsThisRecording = mutagen.mp3.MP3(BytesIO(R.audioData[recNo-1])).info.length
        else: secsThisRecording = 0
        if secsThisRecording > 3600:
            R.warning(f"""Recording {recNo
            } is long enough to cause ~{
            secsThisRecording*.0001:.1f
            }sec synchronisation error on some readers""") # seems lame v3.100 can result in timestamps being effectively multiplied by ~1.0001 on some players but not all, causing slight de-sync on 1h+ recordings (bladeenc may avoid this but be lower quality overall; better to keep the recordings shorter if possible)
        durations.append(secsThisRecording)
        if R.audioData[recNo-1]:
            writestr(f"{recNo:04d}.mp3",
                 R.audioData[recNo-1])
            R.audioData[recNo-1] = True # save RAM: drop once used
            if recodeTasks is not None: R.info(" done")
        writestr(f'{recNo:04d}.smil',D(
            R.section_smil(recNo,secsSoFar,
                         secsThisRecording,curP,
                         rTxt.textsAndTimes if
                           isinstance(rTxt,
                           TextsAndTimesWithPages)
                           else rTxt)))
        writestr(f'{recNo:04d}.{"xml" if R.daisy3 else "htm"}',
                 D(R.text_htm(
                     (rTxt.textsAndTimes[
                         (1 if
                          isinstance(
                              rTxt.textsAndTimes
                              [0],float) else 0)
                         ::2]
                      if isinstance(rTxt,TextsAndTimesWithPages)
                      else [TagAndText('h1',rTxt)]),
                     curP)))
        secsSoFar += secsThisRecording
        curP += (1+len(rTxt.textsAndTimes)//2
                 if isinstance(rTxt,TextsAndTimesWithPages) else 1)
        R.progress(recNo)
    R.progress_loopStart(len(R.imageFiles),15)
    for n,u in enumerate(R.imageFiles):
        writestr(f'{n+1}{u[u.rindex("."):]}',
                 fetch(u,R.cache,R.refresh,
                       R.refetch,R.delay,
                       R.user_agent,R.retries,R)
                 if re.match("https?://",u)
                 else open(u,'rb').read())
        R.progress(n+1)
    if not R.date:
        R.date = "%d-%02d-%02d" % time.localtime(
                                  )[:3]
    if R.daisy3:
        writestr('dtbook.2005.basic.css',D(d3css))
        writestr('package.opf',D(R.package_opf(
            hasFullText, len(recordingTexts),
            secsSoFar)))
        writestr('text.res',D(textres))
    else: writestr('master.smil',D(
            R.master_smil(headings,secsSoFar)))
    writestr(
        'navigation.ncx' if R.daisy3
        else 'ncc.html',
        D(R.ncc_html(
            headings,hasFullText,secsSoFar,
            [timeAdjust(
                t.textsAndTimes if isinstance(t,TextsAndTimesWithPages) else t,
                durations[i])
             for i,t in enumerate(
                     recordingTexts)],
            [(t.pageInfos if isinstance(
                t,TextsAndTimesWithPages) else [])
             for t in recordingTexts])))
    if not R.daisy3: writestr('er_book_info.xml',D(er_book_info(durations))) # not DAISY standard but EasyReader can use this
    z.close()
    R.info(f"Wrote {R.outputFile}")
  def getHeadings(self,recordingTexts) -> list:
    """Gets headings from recordingTexts for the
    DAISY's NCC / OPF data"""
    R = self
    ret = [] ; cvChaps = [] ; chapNo = 0
    for t in recordingTexts:
        chapNo += 1
        if R.bookTitlesAndNumChaps and chapNo==R.bookTitlesAndNumChaps[0][1]+1:
            del R.bookTitlesAndNumChaps[0]
            if not R.bookTitlesAndNumChaps:
                error("merge-books did not account for all files (check the counts)")
            chapNo = 1
        if not isinstance(t,
                          TextsAndTimesWithPages):
            if R.bookTitlesAndNumChaps and chapNo==1: error("merge-books with non-HTML not yet implemented")
            ret.append(t) ; continue # title only
        textsAndTimes,pages = t ; first = None
        chapHeadings = [] ; v=0
        while v < len(textsAndTimes):
            u = textsAndTimes[v]
            if isinstance(u,float): # time
               v += 1 ; continue
            tag,text = u
            if first is None: first = v
            if not tag.startswith('h'):
                v += 1 ; continue
            if v//2 - 1 == first//2 and not textsAndTimes[first].tag.startswith('h'): # chapter starts with non-heading followed by heading: check the non-heading for "Chapter N" etc
                nums=re.findall("[1-9][0-9]*",
                        textsAndTimes[first].text)
                if len(nums)==1:
                    textsAndTimes[first] = TagAndText(tag,textsAndTimes[first].text.replace(chr(160),' ').replace(chr(0x202F),' ')+" <br />"+text) # for document (nb content_fixes won't be run so close the br tag or EasyReader shows no text at all; include leading space because at least some versions of EasyReader ignore the br; replace any no-break space because 'Chapter N' is more likely to be a search query and EasyReader 12 can't match normal space to no-break space in search)
                    text=f"{nums[0]}: {text}" # for TOC
                    del textsAndTimes[first+1:v+1] ; v = first
            chapHeadings.append(ChapterTOCInfo(
                tag, re.sub('<[^>]*>','',text),
                v//2))
            v += 1
        if chapHeadings:
            if R.chapter_titles:
                cTitle = R.chapter_titles.pop(0)
                if cTitle.strip():
                    R.warning(f"Title override for chapter {chapNo} is {cTitle} but there's already a title in the markup",".  Ignoring override.")
        else: # not chapHeadings
            # This'll be a problem, as master_smil and ncc_html need headings to refer to the chapter at all.  (Well, ncc_html can also do it by page number if we have them, but we haven't tested all DAISY readers with page number only navigation, and what if we don't even have page numbers?)
            # So let's see if we can at least get a chapter number.
            if first is not None: nums=re.findall(
                    "[1-9][0-9]*",
                    textsAndTimes[first].text)
            else:
                R.warning(f"Chapter {chapNo} is completely blank!  (Is {'--marker-attribute' if __name__=='__main__' else 'marker_attribute'} set correctly?)")
                nums = [] ; first = 0 ; textsAndTimes.append(TagAndText('p',''))
            chapterNumberTextFull = chapterNumberText = nums[0] if len(nums)==1 and not nums[0]=="1" else str(chapNo)
            if int(chapterNumberText) > chapNo:
                if R.bookTitlesAndNumChaps:
                    # Must keep this in sync with the skip
                    R.bookTitlesAndNumChaps[0] = [
                        R.bookTitlesAndNumChaps[0][0],
                        R.bookTitlesAndNumChaps[0][1] +
                        int(chapterNumberText)-chapNo]
                if not R.ignore_chapter_skips:
                    R.warning(f"""Skipping chapter{
                    f' {chapNo}'
                    if int(chapterNumberText) == chapNo + 1
                    else f's {chapNo}-{int(chapterNumberText)-1}'}""")
                chapNo = int(chapterNumberText) # so it's in sync, in case there's more than one number in the 1st para later and we have to fall back on automatic count
            if R.chapter_titles:
                chapterNumberTextFull = R.chapter_titles.pop(0)
                if not chapterNumberTextFull:
                    R.warning(f"Title override for chapter {chapNo} is blank",f".  Setting to {chapterNumberText}")
                    chapterNumberTextFull = chapterNumberText
                elif chapterNumberText not in chapterNumberTextFull:
                    R.warning(f"Title for chapter {chapNo} is '{chapterNumberTextFull}' which does not contain the expected '{chapterNumberText}' ({'' if len(nums)==1 and not nums[0]=='1' else 'from automatic numbering as nothing was '}extracted from '{textsAndTimes[first].text.replace(chr(10),' / ')}')")
            # In EasyReader 10 on Android, unless there is at least one HEADING (not just div), navigation display is non-functional.  And every heading must point to a 'real' heading in the text, otherwise EasyReader 10 will delete all the text in Daisy 2, or promote something to a heading in Daisy 3 (this is not done by Thorium Reader).  And (tested on EasyReader 12) any heading in the text NOT in the table of contents is not displayed in heading style by EasyReader (ok in Thorium).
            # (EasyReader 10 on Android also inserts a newline after every span class=sentence if it's a SMIL item, even if there's no navigation pointing to it)
            # So let's add a "real" start-of-chapter heading before the text, with time 0.001 second if we don't know the time from the first time marker (don't set it to 0 or Thorium can have issues)
            if first==1 and textsAndTimes[0]:
                first = 0 # for the insert below: put it before the non-zero opening time marker
            else: textsAndTimes.insert(first,(textsAndTimes[first-1] if first else 0)+0.001)
            textsAndTimes.insert(first,TagAndText(
                f'h{R.chapter_heading_level}',
                chapterNumberTextFull)) # we'll ref this
            chapHeadings=[ChapterTOCInfo(
                f'h{R.chapter_heading_level}',
                chapterNumberTextFull,
                first//2)] # points to our extra heading
            if textsAndTimes[first+2].text.startswith(chapterNumberText):
                textsAndTimes[first+2]=TagAndText(
                    textsAndTimes[first+2].tag,
                    textsAndTimes[first+2].text[
                        len(chapterNumberText):].strip()) # because we just had the number as a heading, so we don't also need it repeated as 1st thing in text
            first += 2 # past the heading we added
            if first+2<len(textsAndTimes) and re.search("[1-9][0-9]*",textsAndTimes[first+2].text):
              v2 = int(re.findall(
                  "[1-9][0-9]*",
                  textsAndTimes[first+2].text)[0]) # might not start at 2, might start at 13 or something, but does it then increase incrementally:
              if [re.findall(
                      "[1-9][0-9]*",
                      textsAndTimes[f].text)[:1]
                  for f in range(
                          first+4,
                          len(textsAndTimes),2)
                  if textsAndTimes[f].text]==[
                          [str(n)]
                          for n in range(
                                  v2+1,
                                  v2+(len(textsAndTimes)-first)//2
                                  -sum(1 for f in range(
                                      first+4,
                                      len(textsAndTimes),
                                      2)
                                       if not textsAndTimes[f].text))]: # looks like we're dealing with consecutive chapter and verse numbers with no other headings, so add chapter to the verse numbers for search
                textsAndTimes[first]=TagAndText(textsAndTimes[first].tag,f"{chapterNumberText}:{'' if re.match(chr(92)+'s*[1-9]',textsAndTimes[first].text) else '1 '}{re.sub('^'+chr(92)+'s*([1-9][0-9]*)( |'+chr(0x202F)+'|'+chr(0xA0)+')*',chr(92)+'1 '+chr(92)+'2 ',textsAndTimes[first].text)}") # (1st vs might not be 1)
                for f in range(first+2,len(textsAndTimes),2):
                    textsAndTimes[f]=TagAndText(textsAndTimes[f].tag,re.sub("([1-9][0-9]*)( |\u202F|\xA0)*",chapterNumberText+r":\1 \2 ",textsAndTimes[f].text,1))
                cvChaps.append(len(ret)+1)
        if R.bookTitlesAndNumChaps:
            chapHeadings=[
                ChapterTOCInfo(
                    f'h{int(i.hTag[1:])+1}' # add 1 to each heading level
                    if i.hTag.startswith('h')
                    else i.hTag,
                    i.hLine,i.itemNo)
                for i in chapHeadings]
            if chapNo==1: chapHeadings.insert(
                    0,
                    ChapterTOCInfo(
                        'h1',
                        R.bookTitlesAndNumChaps[0][0], # the book title: must point to a real heading for similar reason as above. If there's substantial text before 1st heading, we might want to change this code to insert a heading in the text with 0.001s audio or something instead of doing this. May also need to in-place change recordingTexts adding 1 to all headings: don't do this unless inserting h1.
                        chapHeadings[0].itemNo))
        ret.append(chapHeadings)
    if len(R.bookTitlesAndNumChaps)>1 or R.bookTitlesAndNumChaps and not chapNo==R.bookTitlesAndNumChaps[0][1]: R.warning("merge-books specified more files than given")
    if len(cvChaps) not in [0,len(ret)]: R.warning(f"Verse-indexed only {len(cvChaps)} of {len(ret)} chapters.  Missing: {', '.join(str(i) for i in range(1,len(ret)+1) if i not in cvChaps)}")
    return ret
  def ncc_html(self, headings = [],
             hasFullText:bool = False,
             totalSecs = 0,
             recTimeTxts = [],
             pageNos=[]) -> str:
    """Returns the Navigation Control Centre (NCC)
    recTimeTxts includes 0 and total
    pageNos is [[PageInfo,...],...]"""
    R = self
    numPages = sum(len(L) for L in pageNos)
    maxPageNo = max((
        max(
            (int(i.pageNo) for i in PNs),
            default=0)
        for PNs in pageNos),default=0)
    headingsR = R.normaliseDepth(hReduce(headings,R.toc_titles)) # (hType,hText,recNo,textNo)
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">' if R.daisy3 else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"'
    if R.daisy3
    else f'html lang="{R.lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{R.lang}">
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
    <meta name="dc:type" content="{"text" if hasFullText or not any(R.audioData) else "sound"}" />
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
    <meta name="ncc:multimediaType" content="{
    "textNcc" if not any(R.audioData) else
    "textPartAudio" if hasFullText and not all(R.audioData) else
    "audioFullText" if hasFullText else "audioNcc" }" />
    <meta name="{'dtb' if R.daisy3 else 'ncc'
    }:depth" content="{max(int(h.hTag[1:])
    for h in headingsR if h.hTag.startswith('h'))}" />
    <meta name="ncc:files" content="{ 2
    + sum(1 for a in R.audioData if a)
    + len(headings)*(2 if hasFullText else 1)
    + len(R.imageFiles)}" />
  </head>
  {f'<docTitle><text>{R.title}</text></docTitle>'
    if R.daisy3 else ''}
  {f'<docAuthor><text>{R.creator}</text></docAuthor>'
    if R.daisy3 else ''}
  <{'navMap id="navMap"' if R.daisy3 else 'body'}>"""+''.join((f"""
    <navPoint id="s{s+1}" class="{t.hTag}" playOrder="{s+1}">
      <navLabel><text>{t.hLine}</text>{'' if recTimeTxts[t.recNo][2*t.itemNo]==recTimeTxts[t.recNo][2*t.itemNo+2] else f'''<audio src="{t.recNo+1:04d}.mp3" clipBegin="{hmsTime(recTimeTxts[t.recNo][2*t.itemNo])}" clipEnd="{hmsTime(recTimeTxts[t.recNo][2*t.itemNo+2])}"/>'''}</navLabel>
      <content src="{t.recNo+1:04d}.smil#pr{t.recNo+1}.{t.itemNo}"/>
    {'</navPoint>'*numDaisy3NavpointsToClose(s,headingsR)}""" if R.daisy3 else ''.join(f"""
    <span class="page-normal" id="page{N
    }"><a href="{r+1:04d}.smil#t{r+1}.{after}">{N
    }</a></span>""" for r,PNs in enumerate(
        pageNos) for (PO,(after,N)) in enumerate(
            PNs) if (r,after)<=t[2:4] and (
                not s or (r,after) >
                headingsR[s-1][2:4]))+f"""
    <{t.hTag} class="{'section' if s or
                R.allow_jumps else 'title'
                }" id="s{s+1}">
      <a href="{t.recNo+1:04d}.smil#t{t.recNo+1
                }.{t.itemNo}">{t.hLine}</a>
    </{t.hTag}>""") for s,t in enumerate(
        headingsR))+('</navMap><pageList id="page">'+''.join(f"""
    <pageTarget class="pagenum" type="normal" value="{N}" id="page{N}" playOrder="{len(headingsR)+sum(len(P) for P in pageNos[:r])+PO+1}">
      <navLabel><text>{N}</text></navLabel>
      <content src="{r+1:04d}.smil#pr{r+1}.{after}"/>
    </pageTarget>""" for r,PNs in enumerate(pageNos) for (PO,(after,N)) in enumerate(PNs))+"""
  </pageList>
</ncx>""" if R.daisy3 else """
  </body>
</html>"""))
  def imageParagraph(self,text:str) -> str:
    """Pulls out our normalised <img> markup for
       use after the paragraph"""
    R = self
    return f"""{'<p><imggroup>' if R.daisy3 and
    re.search('<img src="',text) else ''}{''.join(
    re.findall('<img src="[^"]*" [^/]*/>',text))
    }{'</imggroup></p>' if R.daisy3 and re.search(
    '<img src="',text) else ''}"""
  def daisy3OpenLevelTags(self, tag:str, num:int, paras:list[TagAndText]) -> str:
    """Gives the <levelN> tags that should be
       placed before the current point in the
       DAISY 3 format"""
    if not self.daisy3: return ''
    elif not tag.startswith('h'):
        if num: return '' # will have been started
        else: return '<level1>'
    return ''.join(
        f'<level{n}>'
        for n in range(
                min(
                    int(tag[1:]),
                    1+next(
                        int(paras[p].tag[1:])
                        for p in range(
                                num-1,-1,-1)
                        if paras[p].tag
                        .startswith('h')))
                if any(
                        paras[p].tag
                        .startswith('h')
                        for p in range(
                                num-1,-1,-1))
                else 1,
                int(tag[1:])+1))
  def daisy3CloseLevelTags(self, tag:str, num:int,
                           paras:list[TagAndText]
                           ) -> str:
    """Gives the </levelN> tags that should be
       placed before the current point in the
       DAISY 3 format"""
    if not self.daisy3 or not num+1==len(paras) \
       and not paras[num+1].tag.startswith('h'):
        return ''
    return ''.join(
        f'</level{n}>'
        for n in range(
                next(
                    int(paras[p].tag[1:])
                    for p in range(num,-1,-1)
                    if paras[p].tag
                    .startswith('h')
                ) if any(
                    paras[p].tag.startswith('h')
                    for p in range(num,-1,-1)
                ) else 1,
                0 if num+1==len(paras)
                else int(paras[num+1].tag[1:])-1,
                -1))
  def normaliseDepth(self, items:list) -> list:
    """Ensure that heading items' depth conforms
    to DAISY standard, in a BookTOCInfo list"""

    if self.allow_jumps: return items
    curDepth = 0
    for i in range(len(items)):
      ii = items[i] # TagAndText or BookTOCInfo
      if ii[0].lower().startswith('h'):
        depth = int(ii[0][1:])
        if depth > curDepth+1:
            if isinstance(ii,BookTOCInfo):
                items[i]=BookTOCInfo(
                    f'h{curDepth+1}',ii.hLine,
                    ii.recNo,ii.itemNo)
            else: items[i]=TagAndText(
                    f'h{curDepth+1}',ii.text)
            curDepth += 1
        else: curDepth = depth
    return items
  def master_smil(self,headings = [],
                totalSecs = 0):
    "Compile the master smil for a DAISY file"
    R = self
    headings = hReduce(headings,R.toc_titles)
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
    <ref title="{deHTML(t.hLine)}" src="{
  t.recNo+1:04d}.smil#t{t.recNo+1}.{t.itemNo
  }" id="ms_{s+1:04d}" />"""
                    for s,t in
                    enumerate(headings))+"""
  </body>
</smil>
"""
  def section_smil(self, recNo:int = 1,
                 totalSecsSoFar:float = 0,
                 secsThisRecording:float = 0,
                 startP:int = 0,
                 textsAndTimes = []) -> str:
    "Compile a section SMIL for a DAISY file"
    R = self
    textsAndTimes = timeAdjust(textsAndTimes,
                               secsThisRecording)
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
{'<!DOCTYPE smil PUBLIC "-//NISO//DTD dtbsmil 2005-2//EN" "http://www.daisy.org/z3986/2005/dtbsmil-2005-2.dtd">'
    if R.daisy3
    else '<!DOCTYPE smil PUBLIC "-//W3C//DTD SMIL 1.0//EN" "http://www.w3.org/TR/REC-smil/SMIL10.dtd">'}
{'<smil xmlns="http://www.w3.org/2001/SMIL20/">'
    if R.daisy3
    else '<smil>'}
  <head>
    {'<meta name="dtb:uid" content=""/>'
    if R.daisy3
    else '<meta name="dc:format" content="Daisy 2.02" />'}
    <meta name="{'dtb' if R.daisy3
    else 'ncc'}:generator" content="{generator}" />
    <meta name="{'dtb' if R.daisy3
    else 'ncc'}:totalElapsedTime" content="{
    hmsTime(totalSecsSoFar)}" />""" + (
        "" if R.daisy3 else f"""
    <meta name="ncc:timeInThisSmil" content="{
        hmsTime(secsThisRecording)}" />
    <meta name="title" content="{
        deHTML(textsAndTimes[1][1])}" />
    <meta name="dc:title" content="{
        deHTML(textsAndTimes[1][1])}" />
    <layout>
      <region id="textView" />
    </layout>""")+f"""
  </head>
  <body>
    <seq id="sq{recNo}" dur="{
    hmsTime(secsThisRecording) if R.daisy3
    else f'{secsThisRecording:.3f}s'}" fill="remove">"""+"".join(f"""
      <par {'' if R.daisy3
    else 'endsync="last" '}id="pr{recNo}.{i//2}">
        <text id="t{recNo}.{i//2}" src="{
    recNo:04d}.{'xml' if R.daisy3 else 'htm'
    }#p{startP+i//2}" />
        {'' if R.daisy3
    or textsAndTimes[i-1]==textsAndTimes[i+1]
    else f'<seq id="sq{recNo}.{i//2}a">'}
          {'' if
    textsAndTimes[i-1]==textsAndTimes[i+1]
    else f'''<audio src="{recNo:04d}.mp3" clip{
    'B' if R.daisy3 else '-b'}egin="{
    hmsTime(textsAndTimes[i-1]) if R.daisy3 else
    f'npt={textsAndTimes[i-1]:.3f}s'}" clip{
    'E' if R.daisy3 else '-e'}nd="{
    hmsTime(textsAndTimes[i+1]) if R.daisy3 else
    f'npt={textsAndTimes[i+1]:.3f}s'}" id="aud{
    recNo}.{i//2}" />'''}
        {'' if R.daisy3 or
    textsAndTimes[i-1]==textsAndTimes[i+1]
    else '</seq>'}
      </par>{''.join(f'<par><text id="t{recNo}.{i//2}.{j}" src="{recNo:04d}.xml#{re.sub(".*"+chr(34)+" id=.","",imageID)}"/></par>'
    for j,imageID in enumerate(re.findall(
    '<img src="[^"]*" id="[^"]*',
    textsAndTimes[i][1]))) if R.daisy3 else ''
    }""" for i in range(1,len(textsAndTimes),2))+"""
    </seq>
  </body>
</smil>
""") # (do not omit text with 0-length audio altogether, even in Daisy 2: unlike image tags after paragraphs, it might end up not being displayed by EasyReader etc.  Omitting audio does NOT save being stopped at the beginning of the chapter when rewinding by paragraph: is this a bug or a feature?)
  def package_opf(self, hasFullText:bool,
                numRecs:int,
                totalSecs:float) -> str:
    "Make the package OPF for a DAISY 3 file"
    R = self
    return deBlank(f"""<?xml version="1.0" encoding="utf-8"?>
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
         <dc:Type>{"text" if hasFullText or not any(R.audioData) else "sound"}</dc:Type>
      </dc-metadata>
      <x-metadata>
         <meta name="dtb:multimediaType" content="{"audioFullText" if hasFullText else "audioNcc"}"/>
         <meta name="dtb:totalTime" content="{hmsTime(totalSecs)}"/>
         <meta name="dtb:multimediaContent" content="{','.join((['audio'] if any(R.audioData) else [])+(['text'] if hasFullText or not any(R.audioData) else [])+(['image'] if R.imageFiles else []))}"/>
         <meta name="dtb:narrator" content="{deHTML(R.reader)}"/>
         {'<meta name="dtb:audioFormat" content="MP3"/>' if any(R.audioData) else ''}
         <meta name="dtb:producedDate" content="{R.date}"/>
      </x-metadata>
   </metadata>
   <manifest>
      <item href="package.opf" id="opf" media-type="text/xml"/>"""+''.join(f"""
      <item href="{i:04d}.mp3" id="opf-{i
      }" media-type="audio/mpeg"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i+1}{u[u.rindex("."):]
      }" id="opf-{i+numRecs+1
      }" media-type="image/{u[u.rindex(".")+1:]
      .lower().replace("jpg","jpeg")}"/>""" for i,u in enumerate(R.imageFiles))+f"""
      <item href="dtbook.2005.basic.css" id="opf-{
      len(R.imageFiles)+numRecs+1}" media-type="text/css"/>"""+''.join(f"""
      <item href="{i:04d}.xml" id="opf-{i+len(
      R.imageFiles)+numRecs+1}" media-type="application/x-dtbook+xml"/>""" for i in range(1,numRecs+1))+''.join(f"""
      <item href="{i:04d}.smil" id="{i
      :04d}" media-type="application/smil+xml"/>""" for i in range(1,numRecs+1))+"""
      <item href="navigation.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>
      <item href="text.res" id="resource" media-type="application/x-dtbresource+xml"/>
   </manifest>
   <spine>"""+"".join(f"""
      <itemref idref="{i:04d}"/>""" for i in range(1,numRecs+1))+"""
   </spine>
</package>
""")
  def text_htm(self, paras:list[TagAndText], offset:int=0) -> str:
    """Format the text, as htm for DAISY 2 or xml
    for DAISY 3.
    paras = TagAndText list, text is xhtml i.e. & use &amp; etc."""
    R = self
    return deBlank(f"""<?xml version="1.0"{
    ' encoding="utf-8"' if R.daisy3 else ''
    }?>{'<?xml-stylesheet type="text/css" href="dtbook.2005.basic.css"?>' if R.daisy3 else ''}
{'<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">'
    if R.daisy3
    else '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'}
<{'dtbook xmlns="http://www.daisy.org/z3986/2005/dtbook/" version="2005-2"'
    if R.daisy3
    else f'html lang="{R.lang}" xmlns="http://www.w3.org/1999/xhtml"'} xml:lang="{R.lang}">
    <head>
        {'<meta name="dt:version" content="1.0" />' if R.daisy3 else ''}
        {f'<meta name="dc:Title" content="{deHTML(R.title)}"/>'
    if R.daisy3 else f'<title>{R.title}</title>'}
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
"""+"\n".join(f"""{
R.daisy3OpenLevelTags(tag,num,paras)}{
'<p>' if addPbeforeTag(tag,num,paras) else ''
}<{tag} id=\"p{num+offset}\"{
(' class="word"' if len(text.split())==1 else
' class="sentence"') if tag=='span' else ''}>{
re.sub(" *<br />$","",removeImages(text))}</{tag
}>{'</p>' if closePafterTag(tag,text,num,paras)
else ''}{R.imageParagraph(text)}{
R.daisy3CloseLevelTags(tag,num,paras)}""" for num,(tag,text) in enumerate(R.normaliseDepth(paras)))+f"""
    </{'bodymatter></book' if R.daisy3 else 'body'}>
</{'dtbook' if R.daisy3 else 'html'}>
""")

class PidsExtractor:
    """Go through the HTML, extracting the
    paragraphs whose IDs we want, and moving any
    images to their relevant ID'd paragraph (we
    assume all images with an image_attribute
    should be kept, and others are site decoration
    etc).  Also pick up on any page-number tags
    and note where they were."""

    def __init__(self, R:Run, want_pids:list[str]):
        self.R = R
        self.want_pids = want_pids # IDs we want
        self.id_to_content = {} # our main output
        self.pageNos = [] # secondary output for page-number based navigation
        self.pageNoGoesAfter = 0 # want_pids index
        self.previous_pid_tagname = None
        self.previous_pid_contents = None
        self.images_before_first_pid = []
        self.seen_heading = False

    def handle_soup(self,t,addTo=None,
                    include_alt=False) -> None:
        """Recursively scan through the HTML.
        t is a BeautifulSoup tree node.
        addTo is the list of data for the ID that
        is currently being extracted, if any: we
        can append to this.
        include_alt is True if we want to repeat
        the ALT tags of included images in text"""

        if not t.name: # data or comment
            if t.PREFIX: pass # ignore comment, doctype etc
            elif addTo is not None: # collect text
                addTo.append(str(t).replace('&','&amp;').replace('<','&lt;'))
            return
        # ok, it's a tag:
        tag=tagRewrite.get(t.name,t.name)
        attrs = t.attrs
        imgURL = attrs.get(self.R.image_attribute,None)
        if imgURL and (re.match(
                "https?://.*[.][^/]*$",
                imgURL)or os.path.isfile(imgURL)):
            # Write the 'img' markup for the DAISY document.
            # Will be moved to after the paragraph by text_htm
            # because DAISY images cannot occur inside paragraphs.
            image_index = self.R.imageFiles.index(imgURL) if imgURL in self.R.imageFiles else len(self.R.imageFiles)
            img = f'''<img src="{
            image_index+1}{
            imgURL[imgURL.rindex("."):]
            }" {f'id="i{image_index}"'
            if self.R.daisy3 else ""} />'''
            if imgURL not in self.R.imageFiles:
                self.R.imageFiles.append(imgURL)
            if "alt" not in attrs:
                for k in attrs.keys():
                    if k.endswith("-alt"): # data-img-att-alt or whatever: treat same as "alt"
                        attrs["alt"] = attrs[k]
                        break
            if include_alt and "alt" in attrs:
                # DAISY3 standard does not list alt as a valid attribute for img, so we have to put the text in afterwards
                img += f'<br>{attrs["alt"]}<br>' # images will be moved to *after* these by text_htm; if we want an option for the image *before* the ALT, we'd need to put these in the *next* paragraph or change text_htm
            if addTo is not None:addTo.append(img)
            elif self.previous_pid_contents is not None: self.previous_pid_contents.append(img)
            else: self.images_before_first_pid.append(img)
        this_tag_has_a_pid_we_want = False
        if attrs.get(self.R.marker_attribute,None) in self.want_pids:
            this_tag_has_a_pid_we_want = True
            self.previous_pid_tagname = tag
            a = attrs[self.R.marker_attribute]
            self.pageNoGoesAfter = self.want_pids.index(a)
            self.id_to_content[a] = ((tag if re.match('h[1-6]$',tag) or tag=='span' else 'p'),[])
            addTo = self.id_to_content[a][1]
        elif addTo is not None and tag in allowedInlineTags: addTo.append(f'<{allowedInlineTags[tag]}>')
        elif addTo is not None and tag=='a': self.lastAStart = len(addTo)
        elif addTo is not None and tag=='span' and any(
                c in self.R.line_breaking_classes for c in
                attrs.get("class",[])):
            addTo.append('<br>') # (not <p> because if the document is span-based we'll likely end up replacing it with a <br> below anyway, and most DAISY readers treat them the same)
        pageNo=attrs.get(self.R.page_attribute,"")
        if re.match("(?i)[ivxlm]",pageNo):
            self.R.warning("Support of Roman page numbers not yet implemented",f": ignoring page marker for {pageNo}") # we will need to change ncc_html to support 'front' pages (not just 'normal' pages) if supporting this
            pageNo = None
        if pageNo: self.pageNos.append(PageInfo(self.pageNoGoesAfter,pageNo))
        # Now the recursive call:
        if not tag=='rt':
          for c in t.children:
            self.handle_soup(c,addTo,include_alt)
        # And now the end tag:
        if addTo is not None:
            if this_tag_has_a_pid_we_want:
                self.seen_heading = tag.startswith("h")
                if self.images_before_first_pid and self.seen_heading and not (
                        tag.startswith("h")
                        and any("<br" in i
                            for i in self.images_before_first_pid)): # (don't include ALTs as part of the heading, and ALT or otherwise don't risk putting before first heading especially if we'll rewrite number to be part of it)
                    addTo += self.images_before_first_pid
                    self.images_before_first_pid=None
                self.previous_pid_contents = addTo
            elif tag in allowedInlineTags: addTo.append(f'</{allowedInlineTags[tag]}>')
            elif tag=="a" and re.match('[!-.:-~]$',"".join(addTo[self.lastAStart:]).strip()):
                # remove single-character link, probably to footnote (we won't know if it's in the audio or not, we're not supporting jumps and the symbols might need normalising)
                # but don't remove numbers (might be paragraph numbers etc) or non-ASCII (might be single-character CJK word)
                del addTo[self.lastAStart:]
        elif tag=='p' and self.previous_pid_contents and self.previous_pid_tagname=='span':
            # if paragraphs contain spans and it's the spans that are identified, ensure we keep this break in the surrounding structure
            self.previous_pid_contents.append("<br>")

def delimited(s,start:int,end:int) -> bool:
    """Checks to see if a string or binary data
    is delimited by start and end, converting as
    needed, after stripping"""
    if isinstance(s,bytes):
        s = s.replace(b"\xEF\xBB\xBF",b"").strip() # just in case somebody's using UTF-8 BOMs
        return s.startswith(start.encode('latin1')) and s.endswith(end.encode('latin1'))
    else: # string; assume no BOM to skip
        s = s.strip()
        return s.startswith(start) and s.endswith(end)

def fixup_times(textsAndTimes,model,audioData,filenameExt,numCPUs):
    if not isinstance(textsAndTimes[0],float):
        textsAndTimes.insert(0, 0.0)
    check = ''.join(i[1] for i in textsAndTimes[1::2]).lower()
    looks_alphabetic = len(re.findall('[a-z]',check)) > len(check)/2
    if looks_alphabetic: make_tokens = lambda x:re.findall('[a-z]+',x.lower())
    elif len(check.split())>5: make_tokens = lambda x:x.split()
    else: make_tokens = lambda x:list(x) # CJK?
    parasTokens = [make_tokens(re.sub('<[^>]*>','',i[1])) for i in textsAndTimes[1::2]]
    tFile=tempfile.NamedTemporaryFile(suffix=os.extsep+filenameExt,delete=False).name
    open(tFile,'wb').write(audioData)
    recogTokens,tokenNo_to_time = [], {}
    cmd = f'whisper-cli -p {numCPUs} -m "{model}" -f "{tFile}" -ml 1 -sow'
    sys.stderr.write(f"Running {cmd}... "),sys.stderr.flush()
    out = getoutput(cmd)
    for L in out.split("\n"):
        m = re.match(r"\[([0-9]{2}:[0-5][0-9]:[0-5][0-9]\.[0-9]{3}) --> ([0-9]{2}:[0-5][0-9]:[0-5][0-9]\.[0-9]{3})\]  (.*)$",L.rstrip())
        if m:
            startTime,endTime,word = m.groups()
            tokenNo_to_time[len(recogTokens)] = startTime
            recogTokens += make_tokens(word)
            tokenNo_to_time[len(recogTokens)] = endTime
    sys.stderr.write("done\n")
    if not recogTokens: error(f"auto-markers-model: no words recognised, whisper-cli output was: {out}")
    known_tokens,known_breaks = [],[]
    for p in parasTokens:
        known_tokens += p
        known_breaks.append(len(known_tokens))
    del known_breaks[-1] # end of text is obvious
    matches = difflib.SequenceMatcher(a=known_tokens,b=recogTokens).get_matching_blocks()
    n = 2
    for m in matches:
        while known_breaks and m.a+m.size >= known_breaks[0]:
            s = m.b+max(0,known_breaks.pop(0)-m.a)
            while s and s not in tokenNo_to_time: s -= 1
            textsAndTimes[n] = parseTime(tokenNo_to_time[s])
            n += 2
    os.remove(tFile)

def load_miniaudio_and_lameenc() -> bool:
    """Tries to load the miniaudio and lameenc
    libraries.  If this fails (returning False)
    then we have to use an external binary LAME"""
    try:
        import miniaudio as M
        import lameenc as L
        global miniaudio, lameenc
        miniaudio, lameenc = M, L
        return True
    except: return False # noqa: E722 (ImportError or anything wrong with those libraries = can't use either)

def check_we_got_LAME() -> None:
    """Complains if LAME is not available on
    this system, either as miniaudio + lameenc
    imports, or as a binary.  Makes a little
    extra effort to find a binary on Windows."""

    if which('lame'): return
    if load_miniaudio_and_lameenc(): return
    if sys.platform=='win32': # some machines have it here:
        os.environ["PATH"] += r";C:\Program Files (x86)\Lame for Audacity;C:\Program Files\Lame for Audacity"
        if which('lame'): return
    error("""Anemone requires the LAME program to encode/recode MP3s.
Please either install the miniaudio and lameenc pip libraries,
or make the 'lame' binary available, and then try again.""")

tagRewrite = { # used by get_texts
    'legend':'h3', # used in fieldset
}
allowedInlineTags={
    # like tagRewrite but allows the tag inline
    # (rewrite <b> and <i> to <strong> and <em>)
    # Do not add more tags to this without
    # carefully checking what DAISY readers do.
    'br':'br',
    'strong':'strong', 'b':'strong',
    'em':'em', 'i':'em'}
assert 'rt' not in allowedInlineTags, "if allowing this, need to revise rt suppression logic" # and would have to rely on rp parens for most readers, so if a text has a LOT of ruby it could get quite unreadable

def content_fixes(content:str) -> str:
    """Miscellaneous fixes for final XML/XHTML
    to work around some issues with readers"""
    content = easyReader_em_fix(content)
    content = re.sub('([A-Za-z])(\xb7|\u02b9)([A-Za-z])',r'\1\3',content) # pronunciation diacritics that have caused trouble for screen readers and Braille displays on FSReader (regex: only in alphabetic languages)
    content = re.sub('( *</?br> *)+',' <br />',content) # allow line breaks inside paragraphs, in case any in mid-"sentence", but collapse them because readers typically add extra space to each, plus add a space beforehand in case any reader doesn't render the linebreak (e.g. EasyReader 10 in a sentence span)
    return content

def easyReader_em_fix(content:str) -> str:
    """EasyReader 10 workaround: it does not show
    strong or em, which is OK but it puts space
    around it: no good if it happened after a "("
    or similar, so delete those occurrences.
    Also, delete anything like </strong><strong>
    (off and on again) as this would add space for
    no good reason."""
    while True:
        c2 = re.sub(
            r"<(?P<tag>(strong|em))>(.*?)</(?P=tag)>",
            lambda m:easyReader_em_fix(m.group(3))
            if m.start() and
            content[m.start()-1] not in ' >'
            or m.end()<len(content) and
            content[m.end()] not in ' <'
            else f"<{m.group(1)}>{easyReader_em_fix(m.group(3))}</{m.group(1)}>",
            string = content) # rm aftr open paren
        c2 = re.sub(
            r"</(?P<tag>(strong|em))><(?P=tag)>",
            "",c2) # rm e.g. </strong><strong>
        if c2==content: break
        content = c2 # and re-check
    return content

def jsonAttr(d:dict,suffix:str) -> str:
    """Returns the value of a dictionary key whose
    name ends with the given lower-case suffix
    (after converting names to lower case).  Used
    for checking JSON for things like paragraphId
    if you know only that it ends with 'Id'.  It
    is assumed that there is exactly one such item
    (use checkJsonAttr first to check it)."""
    return str(d[[k for k in d.keys() if k.lower().endswith(suffix)][0]])
def checkJsonAttr(d:dict,suffix:str) -> str:
    """Checks that a dictionary is suitable for jsonAttr
    i.e. it contains exactly one key whose name ends with
    the given lower-case suffix (after converting names to
    lower case).  Returns an error message, or None."""
    keys = [k for k in d.keys() if k.lower().endswith(suffix)]
    if not keys: return f"Nothing ends with '{suffix}' in {repr(list(d.keys()))}"
    if len(keys)>1: return f"More than one item ends with '{suffix}' in {repr(list(d.keys()))}"

def parseTime(t:str) -> float:
    """Parses a string containing seconds,
    minutes:seconds or hours:minutes:seconds
    (decimal fractions of seconds allowed),
    and returns floating-point seconds"""

    tot = 0.0 ; mul = 1
    for u in reversed(t.split(':')):
        tot += float(u)*mul ; mul *= 60
    return tot

def merge0lenSpans(recordingTexts:list, headings:list, hasAudio:list) -> None:
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

    for cT,cH,hA in zip(recordingTexts,headings,hasAudio):
        if not hA or not isinstance(cT,TextsAndTimesWithPages): continue
        textsAndTimes,pages = cT
        i=0
        while i < len(textsAndTimes)-2:
            while i < len(textsAndTimes)-2 and \
                  isinstance(textsAndTimes[i],TagAndText) and \
            (0 if i==0 else textsAndTimes[i-1])>=\
            textsAndTimes[i+1]: # 0-length, or -ve due to 0.001 below
              if textsAndTimes[i].tag==textsAndTimes[i+2].tag: # tag identical
                textsAndTimes[i] = TagAndText(textsAndTimes[i].tag, f"{textsAndTimes[i].text}{' ' if textsAndTimes[i].tag=='span' else '<br />'}{textsAndTimes[i+2].text}") # new combined item
                del textsAndTimes[i+1:i+3] # old
                for hI,hV in enumerate(cH):
                    if hV.itemNo > i//2: cH[hI]=ChapterTOCInfo(hV.hTag,hV.hLine,hV.itemNo-1)
                for pI,pInfo in enumerate(pages):
                    if pInfo.duringId > i//2: pages[pI]=PageInfo(pInfo.duringId-1,pInfo.pageNo)
              else: # tag different: can't merge, but can still help Thorium Reader by not putting a completely 0-length paragraph
                textsAndTimes[i+1] = textsAndTimes[i-1] + 0.001
            i += 1

def recodeMP3(dat:bytes, R:Run, hasMP3ext:bool=False) -> bytes:
    """Takes MP3 or WAV data, re-codes it
    as suitable for DAISY, and returns the bytes
    of new MP3 data for putting into DAISY ZIP"""

    if load_miniaudio_and_lameenc():
        # Preferred method: use these 2 libraries
        # (works with a range of input file types)
        pcm = miniaudio.decode(dat,nchannels=1,sample_rate=44100)
        del dat # might save RAM if ThreadPoolExecutor doesn't still have a ref to the submitted task's parameter
        enc = lameenc.Encoder()
        enc.set_bit_rate(64)
        enc.set_channels(1)
        enc.set_quality(0)
        enc.set_in_sample_rate(pcm.sample_rate)
        pcm=pcm.samples.tobytes() # save a bit of RAM: don't keep pcm object when we need only its bytes going forward
        mp3=enc.encode(pcm) # can take time
        return mp3 + enc.flush()

    # Fallback method: use LAME external binary.

    # Players like FSReader can get timing wrong if mp3 contains
    # too many tags at the start (e.g. images).
    # eyed3 clear() won't help: it zeros out bytes without changing indices.
    # To ensure everything is removed, better decode to raw PCM and re-encode.
    # The --decode option has been in LAME since 2000; don't worry about LAME's ./configure --disable-decoder: that is an option for building cut-down libraries, not the command-line frontend
    decodeJob = run(["lame","-t","--decode"]+(["--mp3input"] if hasMP3ext else [])+["-","-o","-"],input=dat,check=True,stdout=PIPE,stderr=PIPE)
    # (On some LAME versions, the above might work
    # with AIFF files too, but we say MP3 or WAV.
    # Some LAME versions can't take WAV from stdin
    # only raw when encoding, but ok if --decode)
    del dat
    m = re.search(b'(?s)([0-9.]+) kHz, ([0-9]+).*?([0-9]+) bit',decodeJob.stderr)
    if not m: error("lame did not give expected format for frequency, channels and bits output")
    return run(["lame","--quiet","-r","-s",
                m.group(1).decode('latin1')]+
               (['-a'] if m.group(2)==b'2' else [])+
               ['-m','m',
                '--bitwidth',m.group(3).decode('latin1'),
                "-",
                "--resample","44.1",
                "-b","64",
                "-q","0","-o","-"],
               input=decodeJob.stdout,check=True,stdout=PIPE).stdout

def fetch(url:str,
          cache = "cache", # not necessarily str
          refresh:bool = False,
          refetch:bool = False,
          delay:int = 0,
          user_agent = None,
          retries:int = 0,
          info = None) -> bytes:
    """Fetches a URL, with delay and/or cache.

    cache: the cache directory (None = don't save)
    or a requests_cache session object to do it

    refresh: if True, send an If-Modified-Since
    request if we have a cached item (the date of
    modification may be the timestamp of the file
    in the cache, not necessarily the actual last
    modified time as given by the server)

    refetch: if True, reload unconditionally
    without first checking the cache

    delay: number of seconds between fetches
    (tracked globally from last fetch)

    user_agent: the User-Agent string to use, if
    not using Python's default User-Agent

    retries: number of times to retry a fetch
    if it times out or unhandled exception

    info: an optional Run instance to take the log
    (otherwise we use standard error)"""

    if not info: # no Run instance: use standard error and a global last request time
        class MockInfo:
            def info(self,text:str,newline:bool=True):
                sys.stderr.write(f"{text}{chr(10) if newline else ''}"), sys.stderr.flush()
        global _globalMockInfo
        try: _globalMockInfo
        except NameError: _globalMockInfo = MockInfo()
        info = _globalMockInfo
    if delay and not hasattr(info,"_last_request_time"):
        info._last_request_time = 0
    ifModSince = None
    headers = {"User-Agent":user_agent} if user_agent else {}
    if hasattr(cache,"get"):
        # if we're given a requests_cache session,
        # use that instead of our own caching code
        is_recent_requestsCache_version = "only_if_cached" in inspect.getfullargspec(cache.request).args
        if not refresh and not refetch and is_recent_requestsCache_version:
            # if the cache can tell us it has it,
            # we don't even have to say "Fetching"
            r = cache.request('GET',url,
                              only_if_cached=True)
            if r.status_code == 200:
                return r.content
        if delay and not is_recent_requestsCache_version:
            if not hasattr(info,"_last_request_warned"):
                info._last_request_warned = True
                info.info("Using the parameter 'delay' with a requests_cache object requires a version of requests_cache that supports the only_if_cached parameter.  Your requests_cache seems too old.  Ignoring 'delay'.")
                # otherwise we'd have to unconditionally delay even for things we already have cached
        info.info(f"Fetching {url}...",False)
        if delay and is_recent_requestsCache_version:
            time.sleep(min(0,info._last_request_time+delay-time.time()))
        try:
           if 'force_refresh' in inspect.getfullargspec(cache.request).args:
              r = cache.request('GET',url,
                          headers = headers,
                          timeout = 20,
                          refresh = refresh,
                          force_refresh=refetch)
           else: # old requests_cache v0.9 (in Ubuntu 24.04) can't use force_refresh etc
              r = cache.request('GET',url,
                          headers = headers,
                          timeout = 20)
        except Exception as e:
            info._last_request_time = time.time()
            if retries:
                info.info(f" error, retrying ({retries} {'try' if retries==1 else 'tries'} left)")
                return fetch(url,cache,refresh,refetch,delay,user_agent,retries-1,info)
            info.info(" error")
            raise HTTPError("",500,f"{e}",{},None)
        info._last_request_time = time.time()
        if r.status_code == 200:
            info.info(" fetched")
            return r.content
        else:
            info.info(" bad status")
            raise HTTPError("",r.status_code,"unexpected HTTP code",{},None)

    # Fallback to our own filesystem-based code
    # for quick command-line use if you want to
    # manually manage the cache (delete parts of
    # it by directory etc) :
    if cache:
      fn = re.sub('[%&?@*#{}<>!:+`=|$]', # these characters need to be removed on Windows's filesystem
                  '', # hope no misguided webmaster makes two URLs identical apart from those characters; if they do, please use a requests_cache session instead of this fallback code...
                  cache+os.sep+unquote(re.sub('.*?://','',url))
                  .replace('/',os.sep))
      if fn.endswith(os.sep): fn += "index.html"
      fn = os.sep.join(f.replace('.',os.extsep)
                       for f in fn.split(os.sep)) # just in case we're on RISC OS (not tested)
      fnExc = fn+os.extsep+"exception"
      if os.path.exists(fn):
        if refetch: pass # ignore already dl'd
        elif refresh:
            ifModSince=os.stat(fn).st_mtime
        else: return open(fn,'rb').read()
      elif os.path.exists(fnExc) and not refetch and not refresh: raise HTTPError("",int(open(fnExc).read()),"HTTP error on last fetch",{},None) # useful especially if a wrapper script is using our fetch() for multiple chapters and stopping on a 404
      Path(os.path.split(fn)[0]).mkdir(parents=True,exist_ok=True)
    info.info(f"Fetching {url}...",False)
    if delay: time.sleep(min(0,info._last_request_time+delay-time.time()))
    if ifModSince:
        t = time.gmtime(ifModSince)
        headers["If-Modified-Since"]=f"{'Mon Tue Wed Thu Fri Sat Sun'.split()[t.tm_wday]}, {t.tm_mday} {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[t.tm_mon-1]} {t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d} GMT"
    url2 = ''.join(
        (chr(b) if b < 128 else f"%{b:02x}")
        for b in url.encode('utf-8'))
    try: dat = urlopen(Request(url2,headers=headers)).read()
    except Exception as e:
        info._last_request_time = time.time()
        if not isinstance(e,HTTPError):
            if retries:
                info.info(f" error {e}, retrying ({retries} {'try' if retries==1 else 'tries'} left)")
                return fetch(url,cache,refresh,refetch,delay,user_agent,retries-1,info)
            e = HTTPError("",500,f"{e}",{},None)
        if e.getcode()==304 and cache:
            info.info(" no new data")
            return open(fn,'rb').read()
        else:
            info.info(f"error {e.getcode()}")
            if cache: open(fnExc,"w").write(
                    str(e.getcode()))
            raise
    info._last_request_time = time.time()
    if cache:
        open(fn,'wb').write(dat)
        info.info(" saved")
    else: info.info(" fetched")
    return dat

def addPbeforeTag(tag:str, num:int, paras:list) -> bool:
    "Decides whether a <p> should be added before the current tag"
    return tag=='span' and (
        num==0
        or not paras[num-1].tag=="span"
        or paras[num-1].text.endswith("<br />"))
def closePafterTag(tag:str, text:str, num:int, paras:list) -> bool:
    "Decides whether a </p> should be added after closing the current tag"
    return tag=='span' and (
        text.endswith("<br />")
        or num+1==len(paras)
        or not paras[num+1].tag=='span')

def removeImages(text:str) -> str:
    "Removes our normalised <img> markup from text"
    return re.sub('<img src="[^"]*" [^/]*/>','',text)

def numDaisy3NavpointsToClose(s:int, headingsR:list[BookTOCInfo]) -> int:
    """Calculates the number of DAISY 3 navigation
    points that need closing after index s"""

    thisTag = headingsR[s]
    thisDepth = int(thisTag.hTag[1])
    if s+1==len(headingsR): nextDepth = 1
    else:
        nextTag = headingsR[s+1]
        nextDepth = int(nextTag.hTag[1])
    if thisDepth == nextDepth: return 1 # same heading level
    headingNums_closed = ''.join(
        ('' if not i.hTag.startswith('h')
         else i.hTag[1]
         if int(i.hTag[1])>=nextDepth
         else '0')
        for i in reversed(headingsR[:s+1])
    ).split('0',1)[0]
    if thisDepth: D=thisDepth
    elif headingNums_closed: D=int(headingNums_closed[0])
    else: D=nextDepth
    N = sum(1 for j in range(nextDepth,D+1)
            if str(j) in headingNums_closed)
    return N+(1 if thisDepth is None else 0)

def hReduce(headings:list,overrides:list) -> list[BookTOCInfo]:
    """Convert a list of ChapterTOCInfo lists (or
    text strings for unstructured chapters) into a
    single BookTOCInfo list"""
    ret = reduce(lambda a,b:a+b,[
        ([BookTOCInfo(hType,hText,recNo,textNo)
          for (hType,hText,textNo) in i]
         if isinstance(i,list) else
         [BookTOCInfo('h1',i,recNo,0)])
        for recNo,i in enumerate(headings)],[])
    for i,o in enumerate(overrides):
        if o.strip():
            hType,_,n,t = ret[i]
            ret[i] = BookTOCInfo(hType,o.strip(),n,t)
    return ret

def timeAdjust(textsAndTimes,secsThisRecording:float) -> None:
    """Ensure textsAndTimes starts at the
    beginning of the recording, and ends at the
    end.  Necessary for some players to play all
    of the audio."""
    if not isinstance(textsAndTimes,list):
        textsAndTimes=[textsAndTimes]
    return [0.0]+textsAndTimes[
        (1 if isinstance(textsAndTimes[0],float)
         else 0) :
        (-1 if isinstance(textsAndTimes[-1],float)
         else len(textsAndTimes))
    ] + [secsThisRecording]

def deBlank(s:str) -> str:
    """Remove blank lines from s
    (does not currently remove the first line if
    blank).  Used so that optional items can be
    placed on their own lines in our format-string
    templates for DAISY markup.
    """
    return re.sub("\n( *\n)+","\n",s)

def hmsTime(secs:float) -> str:
    """Formats a floating-point number of seconds
    into the DAISY standard hours:minutes:seconds
    with fractions to 3 decimal places.  (Some
    old DAISY readers can crash if more than 3
    decimals are used, so we must stick to 3)"""

    return f"{int(secs/3600)}:{int(secs/60)%60:02d}:{secs%60:06.3f}"

def deHTML(t:str) -> str:
    """Remove HTML tags from t, collapse
    whitespace and escape quotes so it can be
    included in an XML attribute"""

    return re.sub(r'\s+',' ',re.sub('<[^>]*>','',t)).replace('"','&quot;').strip()

def er_book_info(durations:list[float]) -> str:
    """Return the EasyReader book info.
    durations = list of secsThisRecording"""

    return """<?xml version="1.0" encoding="utf-8"?>
<book_info>
    <smil_info>"""+"".join(f"""
        <smil nr="{s}" Name="{s+1:04d}.smil" dur="{d:f}"/>""" for s,d in enumerate(durations))+"""
    </smil_info>
</book_info>
"""

d3css = """/* Simplified from Z39.86 committee CSS:
  removed non-dark background (allow custom).

  NOTE: most DAISY readers IGNORE this css.
  We provide it to be standards compliant,
  but customising it will likely NOT work.   */

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
# text.res also should not be customised:
textres = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE resources
  PUBLIC "-//NISO//DTD resource 2005-1//EN" "http://www.daisy.org/z3986/2005/resource-2005-1.dtd">
<resources xmlns="http://www.daisy.org/z3986/2005/resource/" version="2005-1"><!-- SKIPPABLE NCX --><scope nsuri="http://www.daisy.org/z3986/2005/ncx/"><nodeSet id="ns001" select="//smilCustomTest[@bookStruct='LINE_NUMBER']"><resource xml:lang="en" id="r001"><text>Row</text></resource></nodeSet><nodeSet id="ns002" select="//smilCustomTest[@bookStruct='NOTE']"><resource xml:lang="en" id="r002"><text>Note</text></resource></nodeSet><nodeSet id="ns003" select="//smilCustomTest[@bookStruct='NOTE_REFERENCE']"><resource xml:lang="en" id="r003"><text>Note reference</text></resource></nodeSet><nodeSet id="ns004" select="//smilCustomTest[@bookStruct='ANNOTATION']"><resource xml:lang="en" id="r004"><text>Annotation</text></resource></nodeSet><nodeSet id="ns005" select="//smilCustomTest[@id='annoref']"><resource xml:lang="en" id="r005"><text>Annotation reference</text></resource></nodeSet><nodeSet id="ns006" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']"><resource xml:lang="en" id="r006"><text>Page</text></resource></nodeSet><nodeSet id="ns007" select="//smilCustomTest[@bookStruct='OPTIONAL_SIDEBAR']"><resource xml:lang="en" id="r007"><text>Optional sidebar</text></resource></nodeSet><nodeSet id="ns008" select="//smilCustomTest[@bookStruct='OPTIONAL_PRODUCER_NOTE']"><resource xml:lang="en" id="r008"><text>Optional producer note</text></resource></nodeSet></scope><!-- ESCAPABLE SMIL --><scope nsuri="http://www.w3.org/2001/SMIL20/"><nodeSet id="esns001" select="//seq[@bookStruct='line']"><resource xml:lang="en" id="esr001"><text>Row</text></resource></nodeSet><nodeSet id="esns002" select="//seq[@class='note']"><resource xml:lang="en" id="esr002"><text>Note</text></resource></nodeSet><nodeSet id="esns003" select="//seq[@class='noteref']"><resource xml:lang="en" id="esr003"><text>Note reference</text></resource></nodeSet><nodeSet id="esns004" select="//seq[@class='annotation']"><resource xml:lang="en" id="esr004"><text>Annotation</text></resource></nodeSet><nodeSet id="esns005" select="//seq[@class='annoref']"><resource xml:lang="en" id="esr005"><text>Annotation reference</text></resource></nodeSet><nodeSet id="esns006" select="//seq[@class='pagenum']"><resource xml:lang="en" id="esr006"><text>Page</text></resource></nodeSet><nodeSet id="esns007" select="//seq[@class='sidebar']"><resource xml:lang="en" id="esr007"><text>Optional sidebar</text></resource></nodeSet><nodeSet id="esns008" select="//seq[@class='prodnote']"><resource xml:lang="en" id="esr008"><text>Optional producer note</text></resource></nodeSet></scope><!-- ESCAPABLE DTBOOK --><scope nsuri="http://www.daisy.org/z3986/2005/dtbook/"><nodeSet id="ns009" select="//annotation"><resource xml:lang="en" id="r009"><text>Annotation</text></resource></nodeSet><nodeSet id="ns010" select="//blockquote"><resource xml:lang="en" id="r010"><text>Quote</text></resource></nodeSet><nodeSet id="ns011" select="//code"><resource xml:lang="en" id="r011"><text>Code</text></resource></nodeSet><nodeSet id="ns012" select="//list"><resource xml:lang="en" id="r012"><text>List</text></resource></nodeSet><nodeSet id="ns018" select="//note"><resource xml:lang="en" id="r018"><text>Note</text></resource></nodeSet><nodeSet id="ns013" select="//poem"><resource xml:lang="en" id="r013"><text>Poem</text></resource></nodeSet><nodeSet id="ns0014" select="//prodnote[@render='optional']"><resource xml:lang="en" id="r014"><text>Optional producer note</text></resource></nodeSet><nodeSet id="ns015" select="//sidebar[@render='optional']"><resource xml:lang="en" id="r015"><text>Optional sidebar</text></resource></nodeSet><nodeSet id="ns016" select="//table"><resource xml:lang="en" id="r016"><text>Table</text></resource></nodeSet><nodeSet id="ns017" select="//tr"><resource xml:lang="en" id="r017"><text>Table row</text></resource></nodeSet></scope></resources>"""

def set_max_shared_workers(nWorkers:int = 0) -> None:
    """Sets the maximum number of shared workers used to recode MP3s.
       These workers are shared between any concurrent anemone()
       calls that don't have max_threads parameters."""
    global shared_executor, shared_executor_maxWorkers
    nWorkers = int(os.environ.get("ANEMONE_THREAD_LIMIT",nWorkers))
    cCount = cpu_count()
    if not nWorkers: nWorkers = cCount
    if not nWorkers: nWorkers = 1 # cpu_count None = can't determine
    if nWorkers < 0: error("max shared workers cannot be negative")
    if cCount and nWorkers > cCount:
        sys.stderr.write(f"WARNING: {nWorkers} shared workers exceeds {cCount} CPUs\n")
    try: old,oMax = shared_executor,shared_executor_maxWorkers
    except NameError: old,oMax = None,0
    if not nWorkers==oMax:
        shared_executor_maxWorkers = nWorkers
        shared_executor = ThreadPoolExecutor(max_workers=nWorkers)
        if old: old.shutdown()
set_max_shared_workers()
version = float(__doc__.split()[1])

if __name__ == "__main__": anemone()

# __all__ cuts down what's listed in help(anemone), w/out stopping other things being available via dir() and help(symbol).  Might be useful especially because the default help() lists all classes, including namedtuple classes, with all default methods, before even getting to the anemone() function.  They can have other things *after* anemone(), but we want them to see anemone() as near to the top of the documentation as possible.  So let's take out the classes (except AnemoneError).
__all__ = sorted(n for n,s in globals().items()
                 if (isinstance(s,type(anemone))
                     or n=='version' or n=='AnemoneError')
                 and n not in ['run','unquote',
                               'urlopen','which'])

# ruff check anemone.py
# ruff: noqa: E401 # multiple imports on one line
# - sorry, I can't see what's wrong with that
# ruff: noqa: E402 # import not at top of file
# - sorry but I like having the docs first...
# ruff: noqa: E701 # colon without newline
# - sorry, coding in large print with wraparound on means newlines are more of an overhead
# ruff: noqa: E702 # semicolon statements - ditto
# ruff: noqa: E731 # I can assign a lambda if it's brief can't I?
