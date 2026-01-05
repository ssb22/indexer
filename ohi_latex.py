#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (works on both Python 2 and Python 3)

"""ohi_latex: Offline HTML Indexer for LaTeX
v1.5 (c) 2014-20,2023-26 Silas S. Brown
License: Apache 2

Standard input HTML can be same as for ohi.py i.e. place
<a name="word-goes-here"></a> before each dictionary entry
and an extra anchor at the end of the text (header comes
before the first and footer follows the last).
Anchors may be linked from other entries.

Output is a PDF file via pdflatex.

Includes a simple HTML to LaTeX converter with support for
CJK (including Pinyin), Greek, Braille, IPA, Latin diacritics,
mathematical Latin alphabets and miscellaneous symbols/emoji.
You can use this alone by giving standard input without any
'a name' tags.  Books can use <title> and <chapter>.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from optparse import OptionParser
opts = OptionParser(description=__doc__[:__doc__.index("Licensed under")])
opts.add_option("--infile",
                help="Input file (defaults to standard input)")
opts.add_option("--outfile",default="index.tex",
                help="Output file (use - for standard output, or set a filename for pdflatex to be run on it also)")
opts.add_option("--lulu",action="store_true",default=False,help="Use page settings for Lulu's Letter-size printing service (max 740 pages per volume, tested 2015-05)")
opts.add_option("--createspace",action="store_true",default=False,help="Use page settings for CreateSpace's 7.5x9.25in printing service (max 828 pages per volume, not tested)")
opts.add_option("--a4compact",action="store_true",default=False,help="Use page settings that should work on most laser printers and MIGHT be ok for binding depending on who's doing it")
opts.add_option("--a5",action="store_true",default=False,help="Use page settings intended for 'on-screen only' use on small devices")
opts.add_option("--compromise",action="store_true",default=False,help="Use page settings intended for compromise between A4 and Letter, with a more spacious layout")
opts.add_option("--trade",action="store_true",default=False,help="Use page settings intended for US Trade (6x9in), with the same pagination as --compromise but smaller margins.  You may combine this with --lulu for even smaller margins via magstep without pagination change.") # (pagination should be the same if system still has same versions of all LaTeX packages)
opts.add_option("--no-qpdf",action="store_true",default=False,help="Never run qpdf and don't enable links and bookmarks (use this when submitting to a print bureau; implied by --lulu and --createspace)")
opts.add_option("--chinese-book",action="store_true",default=False,help="Use a Chinese-style table of contents for books with chapters (currently turns off hyperref as it's too fragile for CJK tables of contents)")
opts.add_option("--dry-run",action="store_true",default=False,help="Don't run pdflatex or qpdf")
opts.add_option("--no-open",action="store_true",default=False,help="Don't open the resulting PDF on Mac")
opts.add_option("--version",action="store_true",default=False,help="Show version number and exit")

options, args = opts.parse_args()
assert not args,"Unknown arguments: "+repr(args)
globals().update(options.__dict__)
if outfile=="-": outfile = None

if lulu and not trade:
  if outfile=="index.tex":
    outfile = "index-lulu.tex"
  geometry = "paperwidth=8.5in,paperheight=11in,twoside,inner=0.8in,outer=0.5in,tmargin=0.5in,bmargin=0.5in,columnsep=8mm,includehead,headsep=0pt" # TODO: reduce headheight ?
  multicol=r"\columnsep=14pt\columnseprule=.4pt"
  twocol_columns = 3
  page_headings = True # taken from the anchors (make sure 'includehead' is in geometry if using this)
  whole_doc_in_footnotesize=True # if desperate to reduce page count (magnifier needed!) - I assume fully-sighted people will be OK with this for reading SHORT sections of text (e.g. dictionary lookups) because footnotesize was designed for short footnotes (and I've seen at least one commercial dictionary which fits 9 lines to the inch i.e. 8pt; footnotesize is 2pt less than the doc size, i.e. 8pt for the default 10pt if nothing is in class_options below)
  links_and_bookmarks = False # as it seems submitting a PDF with links and bookmarks increases the chance of failure in bureau printing
  remove_adjacent_see=2 # if you have a lot of alternate headings (with tags ending *) that just say "see" some other heading, you can automatically remove any that turn out to be right next to what they refer to (or to other alternates that refer to the same place), or that are within N entries of such (set to 0 to turn this off, 1 for right next to, 2 for next to but one, etc)
  suppress_adjacent_see = 1 # to save a bit more, suppress '<em>see</em>' when it occurs after this number of times in succession (0 = unlimited)
  class_options="" # (maybe set 12pt if the default is not too close to the page limit)
elif createspace:
  if outfile=="index.tex":
    outfile = "index-createspace.tex"
  geometry = "paperwidth=7.5in,paperheight=9.25in,twoside,inner=0.8in,outer=0.5in,tmargin=0.5in,bmargin=0.5in,columnsep=8mm,includehead,headsep=0pt" # inner=0.75in but suggest more if over 600 pages
  multicol=r"\columnsep=14pt\columnseprule=.4pt"
  twocol_columns = 2 # or 3 at a push
  page_headings = True
  whole_doc_in_footnotesize=True ; links_and_bookmarks = False ; class_options="" ; remove_adjacent_see = 2 ; suppress_adjacent_see = 1 # (see 'lulu' above for these 5)
elif a4compact:
  if outfile=="index.tex":
    outfile = "index-a4compact.tex"
  geometry = "a4paper,twoside,inner=0.8in,outer=10mm,tmargin=10mm,bmargin=10mm,columnsep=8mm,includehead,headsep=0pt"
  multicol=r"\columnsep=14pt\columnseprule=.4pt"
  twocol_columns = 3
  page_headings = True
  whole_doc_in_footnotesize=True ; links_and_bookmarks = False ; class_options="" ; remove_adjacent_see = 2 ; suppress_adjacent_see = 1 # (see 'lulu' above for these 5)
elif a5:
  geometry = "a5paper,lmargin=3mm,rmargin=3mm,tmargin=3mm,bmargin=3mm,columnsep=8mm"
  multicol=""
  twocol_columns = 2
  page_headings = False
  whole_doc_in_footnotesize=False
  links_and_bookmarks = not no_qpdf
  remove_adjacent_see = 0
  suppress_adjacent_see = 0
  class_options="12pt"
elif compromise or trade:
  if trade and lulu: geometry="paperwidth=171.236mm,paperheight=256.854mm,twoside,inner=22.832mm,outer=14.404mm,tmargin=24.27mm,bmargin=29.184mm,columnsep=11.236mm" # for \mag=890
  elif trade: geometry="paperwidth=6in,paperheight=9in,lmargin=9.2mm,rmargin=9.2mm,tmargin=10mm,bmargin=15.2mm,columnsep=10mm"
  else: geometry = "a4paper,paperheight=11in,lmargin=38mm,rmargin=38mm,tmargin=30mm,bmargin=46mm,columnsep=10mm"
  multicol="" ; twocol_columns = 2
  page_headings=whole_doc_in_footnotesize=False
  links_and_bookmarks = not no_qpdf and not lulu
  remove_adjacent_see=suppress_adjacent_see=0
  class_options="12pt"
else:
  # these settings should work on most laser printers but I don't know about binding; should be OK for on-screen use
  geometry = "a4paper,lmargin=10mm,rmargin=10mm,tmargin=10mm,bmargin=15mm,columnsep=8mm"
  multicol=""
  twocol_columns = 2
  page_headings = False # TODO: ?  (add includehead to the geometry if setting True)
  whole_doc_in_footnotesize=False
  links_and_bookmarks = not no_qpdf
  remove_adjacent_see = 0
  suppress_adjacent_see = 0
  class_options="12pt"

# You probably don't want to change the below for the print version:
alphabet = "abcdefghijklmnopqrstuvwxyz" # set to None for all characters and case-sensitive
ignore_text_in_parentheses = True # or False, for parentheses in index headings
more_sensible_punctuation_sort_order = True
remove_utf8_diacritics = True # for sorting purposes only

# Where to find history:
# on GitHub at https://github.com/ssb22/indexer
# and on GitLab at https://gitlab.com/ssb22/indexer
# and on BitBucket https://bitbucket.org/ssb22/indexer
# and at https://gitlab.developers.cam.ac.uk/ssb22/indexer
# and in China: https://gitee.com/ssb22/indexer

# --------------------------------------------------------

try: import htmlentitydefs # Python 2
except ImportError: # Python 3
  import html.entities as htmlentitydefs
  xrange,unichr,unicode = range,chr,str
import unicodedata,re,sys,os
try: from string import letters # Python 2
except: from string import ascii_letters as letters # Python 3
try: reduce # Python 2
except: from functools import reduce # Python 3

def makeLatex(unistr):
  "Convert unistr into a LaTeX document"
  # init the lookup stuff INSIDE this function,
  # so it's not done unless makeLatex is actually used
  sys.stderr.write("makeLatex initialising... ")
  simple_html2latex_noregex = {
    # we add a non-standard 'twocols' tag:
    '<twocols>':multicol+r'\begin{multicols}{'+str(twocol_columns)+'}','</twocols>':r'\end{multicols}',
    # and a non-standard 'sc' tag for small caps:
    '<sc>':r'\textsc{','</sc>':'}',
    # and a non-standard 'normal-size' tag which takes effect only if whole_doc_in_footnotesize (for printing intros etc at normal size when this is the case)
    '<normal-size>':"","</normal-size>":"", # (overriden below)
    # and HTML tags (only very simple HTML is supported) :
    '<html>':'','</html>':'','<body>':'','</body>':'',
    '<br>':r'\vskip -0.5\baselineskip{}'+'\n', # nicer to TeX's memory than \\ (-0.5\baselineskip is necessary because we're using parskip)
    '<p>':r'\vskip \medskipamount{}'+'\n', '\n':' ',
    '</p>':'', # assumes there'll be another <p>
    '<!--':'%', '-->':'\n', # works if no newlines in the comment
    '<i>':EmOn, '<em>':EmOn, # track it for CJK also
    '<b>':r'\bf{}', '<strong>':r'\bf{}',
    '</i>':EmOff, '</em>':EmOff, '</b>':r'\rm{}', '</strong>':r'\rm{}', # assumes well-formed
    '<u>':r'\uline{','</u>':'}',
    '<s>':r'\sout{','<strike>':r'\sout{',
    '</s>':'}', '</strike>':'}',
    '<big>':r"\Large{}",
    '<small>':r"\offinterlineskip\lineskip2pt\footnotesize{}", # (The 'offinterlineskip' turns off the normal line spacing and makes line spacing effectively irregular depending on the height of each line; can be useful for saving paper if you have lots of additional text in 'small'; not sure if there's a way to turn interline skip back on for the rest of the paragraph etc)
    '</big>':r"\normalsize{}",'</small>':r"\normalsize{}",
    '<biggest>':r"\Huge{}",'</biggest>':r"\normalsize{}",
    '</a>':'}', # for simple_html2latex_regex below
    '<hr>':r"\medskip\hrule{}",
    # '<center>':r"{\centering ",'</center>':r"\par}", # OK if you'll only ever use that tag after a <p> or whatever
    '<center>':r"\begin{center}",'</center>':r"\end{center}",
    '<vfill>':r'\vfill{}',
    '<ruby><rb>':r'\stack{','</rb><rt>':'}{','</rt></ruby>':'}', # only basic <ruby><rb>...</rb><rt>...</rt></ruby> is supported by this; anything else will likely make an un-TeX'able file
    '<h1>':r'\part*{','</h1>':'}',
    '<h1 numbered>':r'\part{',
    '<chapter>':r'\chapter{','</chapter>':'}',
    '<h2>':r'\section*{','</h2>':'}',
    '<h2 numbered>':r'\section{',
    '<h3>':r'\subsection*{','</h3>':'}',
    '<h3 numbered>':r'\subsection{',
    '<title>':r'\title{','</title>':'}%title\n',
    '<code>':r'{\tt ','</code>':'}',
    '<sup>':r'$^{\rm ','</sup>':'}$',
  }
  if whole_doc_in_footnotesize: simple_html2latex_noregex.update({"<big>":r"\normalsize{}","</big>":r"\footnotesize{}","<normal-size>":r"\normalsize{}","</normal-size>":r"\footnotesize{}","<small>":"","</small>":""})
  anchorsHad = {}
  def safe_anchor(match,templateTeX):
    # map all anchors to numbers, so they're "safe" for TeX no matter what characters they originally contained, and then put them in the template TeX
    match = match.group(1)
    if not match in anchorsHad: anchorsHad[match]=str(len(anchorsHad))
    return templateTeX % anchorsHad[match]
  if links_and_bookmarks: href=r"\\href{\1}{"
  else:
    href,simple_html2latex_noregex['</a>'],safe_anchor = "","",lambda *args:"" # just delete them
    if page_headings: safe_anchor = lambda *args:r"\rule{0pt}{1ex}" # keep that to try to make sure mark is on same page as entry
  if page_headings:
    old_safe_anchor = safe_anchor
    def safe_anchor(match,templateTeX):
      # a version that puts in a \markboth command for running headings as well
      ret = old_safe_anchor(match,templateTeX)
      if templateTeX.startswith(r"\hypertarget"):
        mark = mySubDict(re.sub('[;,]? .*','',match.group(1))) # just the 1st word (TODO: lstrip before this?)
        # if whole_doc_in_footnotesize: mark = r'\footnotesize{}'+mark  # TODO: ? (don't know if this actually saves much without tweaking headheight as well)
        if r'\PYactivate' in mark:
          mark = mark.replace(r'\PYactivate','').replace(r'\PYdeactivate','')
          b4,aftr = r'\PYactivate',r'\PYdeactivate{}' # activate/deactivate pinyin around the WHOLE markboth command, since TeX doesn't like doing it in the middle; hope this doesn't result in any kind of conflict from any other commands being used within the mark
        else: b4,aftr = "",""
        mark = re.sub(r"\\shortstack{\\raisebox{-1.5ex}[^{]*{[^{]*{}}([^}]*){}}",r"\1",mark) # LaTeX doesn't like shortstacks in marks, so may have to ditch some of the rarer accents above Greek letters
        ret += b4+r"\markboth{"+mark+"}{"+mark+"}"+aftr
      return ret
  simple_html2latex_regex = {
    '<tex-literal>(.*?)</tex-literal>':r"\1",
    '<a href="#([^"]*)">':lambda m:safe_anchor(m,r"\hyperlink{%s}{"),
    '<a name="([^"]*)">':lambda m:safe_anchor(m,r"\hypertarget{%s}{\rule{0pt}{1ex}"), # the \rule{0pt}{1ex} is to make sure there's some text there, otherwise the target will be on the baseline which is what Acroread will scroll to
    '<a href="([^#][^"]*)">':href,
    # and support simple 1-word versions without quotes (TODO but we don't honour these in anchors when splitting the document into fragments)
    '<a href=#([^ >]*)>':lambda m:safe_anchor(m,r"\hyperlink{%s}{"),
    '<a name=([^"][^ >]*)>':lambda m:safe_anchor(m,r"\hypertarget{%s}{\rule{0pt}{1ex}"),
    '<a href=([^#"][^ >]*)>':href,
    # URLs: the following commented-out line is OK for \usepackage{url}, but NOT if hyperref is also present (it faults on the & character)
    # '((https?|s?ftp)://[!-;=-{}]*)':lambda m:"\\url|"+m.group(1).replace("&amp;","&")+"|", # TODO: other entities? (regexp misses out | and also < because we want it to stop at the next tag)
    # Because we might have hyperref, using this instead:
    '((https?|s?ftp|gemini)://[!-#%-(*-;=-Z^-z|~]*)':lambda m:"\\nolinkurl{"+m.group(1).replace("&amp;",r"\&").replace("%",r"\%").replace("_",r"\_").replace('#',r'\#')+"}", # matches only the characters we can handle (and additionally does not match close paren, since that's often not part of a URL when it's quoted in text; TODO: stop at &gt; ?)
    '([a-z][a-z.]+\\.(com|net|org)/[!-#%-(*-;=-Z^-z|~]*)':lambda m:"\\nolinkurl{"+m.group(1).replace("&amp;",r"\&").replace("%",r"\%").replace("_",r"\_").replace('#',r'\#')+"}",
    '<img src=["]([^"]*)["]>':r'\\includegraphics[width=0.9\\columnwidth]{\1}',
    '<img src=["]([^"]*svg)["]>':r'\\resizebox{1\\columnwidth}{!}{\\includesvg{\1}}', # don't use \includesvg[width=] as that doesn't always resize all text used
    }
  global latex_special_chars
  latex_special_chars = dict((nonBMPstr(u),r"\protect\usym{%X}" % u) for L,H in [(0x2600,0x27C0),(0x1F000,0x1F100),(0x1F300,0x1F650),(0x1F680,0x1F700)] for u in range(L,H)) # utfsym fallback
  for L in range(26): # mathematical letters often misused by "write fancy fonts on social media" utilities:
    latex_special_chars[nonBMPstr(0x1D400+L)]=r"$\mathbf{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D41A+L)]=r"$\mathbf{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D434+L)]=r"$\mathit{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D44E+L)]=r"$\mathit{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D468+L)]=r"$\boldsymbol{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D482+L)]=r"$\boldsymbol{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D49C+L)]=r"$\mathcal{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D4B6+L)]=r"$\mathcal{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D4D0+L)]=r"$\mathbfcal{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D4EA+L)]=r"$\mathbfcal{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D504+L)]=r"$\mathfrak{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D51E+L)]=r"$\mathfrak{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D538+L)]=r"$\mathbb{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D552+L)]=r"$\mathbb{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D56C+L)]=r"$\mathbffrak{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D586+L)]=r"$\mathbffrak{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D5A0+L)]=r"$\mathsf{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D5BA+L)]=r"$\mathsf{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D5D4+L)]=r"$\mathbf{\mathsf{"+chr(ord('A')+L)+"}}$"
    latex_special_chars[nonBMPstr(0x1D5EE+L)]=r"$\mathbf{\mathsf{"+chr(ord('a')+L)+"}}$"
    latex_special_chars[nonBMPstr(0x1D608+L)]=r"$\mathsfit{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D622+L)]=r"$\mathsfit{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D63C+L)]=r"$\mathbfsfit{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D656+L)]=r"$\mathbfsfit{"+chr(ord('a')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D670+L)]=r"$\mathtt{"+chr(ord('A')+L)+"}$"
    latex_special_chars[nonBMPstr(0x1D68A+L)]=r"$\mathtt{"+chr(ord('a')+L)+"}$"
    if L<10:
      latex_special_chars[nonBMPstr(0x1D7CE+L)]=r"$\mathbf{"+chr(ord('0')+L)+"}$"
      latex_special_chars[nonBMPstr(0x1D7D8+L)]=r"$\mathbb{"+chr(ord('0')+L)+"}$"
      latex_special_chars[nonBMPstr(0x1D7E2+L)]=r"$\mathsf{"+chr(ord('0')+L)+"}$"
      latex_special_chars[nonBMPstr(0x1D7EC+L)]=r"$\mathbf{\mathsf{"+chr(ord('0')+L)+"}}$"
      latex_special_chars[nonBMPstr(0x1D7F6+L)]=r"$\mathtt{"+chr(ord('0')+L)+"}$"
  latex_special_chars[nonBMPstr(0x1F912)]=latex_special_chars[nonBMPstr(0x1F321)] # face with thermometer -> thermometer
  latex_special_chars[nonBMPstr(0x1F916)]=r"\mbox{\raisebox{-0.3ex}{\begin{tikzpicture}[x=0.8ex,y=0.8ex,baseline=0pt]\draw[rounded corners=0.5pt] (0,0) rectangle (2,2);\fill (0.6,1.3) circle (0.2);\fill (1.4,1.3) circle (0.2);\end{tikzpicture}}}" # some approximation of the "robot" emoji
  latex_special_chars.update({
    '\\':r"$\backslash$",
    '~':r"$\sim$",u"\u223c":r"$\sim$",
    '^':r"\^{}",
    "...":r'\ldots{}',
    "LaTeX":r"\LaTeX{}","TeX":r"\TeX{}",
    u"\xA0":"~",
    u"\xA3":r"\pounds{}",
    u"\xA7":r"\S{}",
    u"\xA9":r"\copyright{}",
    u"\xAB":r"\guillemotleft{}", # unavailable in OT1 but should be OK if using [T1]fontenc, which we should probably be doing anyway
    u"\xAC":r"$\lnot$",
    u"\xAD":r"\-", # soft hyphen
    u"\xAE":r"\textregistered{}",
    u"\xB0":r"$^{\circ}$", # or \usepackage{textcomp} and have \textdegree{} (not sure which is better)
    u"\xB1":r"$\pm$",
    u"\xB2":r"\raisebox{-0.3ex}{$^2$}",
    u"\xB3":r"\raisebox{-0.3ex}{$^3$}",
    u"\xB4":r"$^{\prime}$",
    u"\xB5":r"$\mu$", # micro sign
    u"\xB6":r"\P{}",
    u"\xB7":r"\textperiodcentered{}",
    u"\xB8":r"\c{}",
    u"\xB9":r"\raisebox{-0.3ex}{$^1$}",
    u"\xBB":r"\guillemotright{}",
    u"\xBC":r"\sfrac14",
    u"\xBD":r"\sfrac12",
    u"\xBE":r"\sfrac34",
    u"\xC6":r"\AE{}",
    u"\xD7":r"$\times$",
    u"\xD8":r"\O{}",
    u"\xDF":r"\ss{}",
    u"\xE6":r"\ae{}",
    u"\xF0":r"\textipa{D}",
    u"\xF7":r"$\div$",
    u"\xF8":r"\o{}",
    # (TODO: any we missed in latin1.def, or other ISO-8859 codepages?)
    u"\u0141":r"\L{}",
    u"\u0142":r"\l{}",
    u"\u014B":r"\textipa{N}",
    u"\u0152":r"\OE{}",
    u"\u0153":r"\oe{}",
    u"\u0218":r"\makebox[0pt]{\raisebox{-0.3ex}[0pt][0pt]{\kern 1.2ex ,}}S", # Romanian hack
    u"\u0219":r"\makebox[0pt]{\raisebox{-0.3ex}[0pt][0pt]{\kern 0.8ex ,}}s", # ditto
    u"\u021A":r"\makebox[0pt]{\raisebox{-0.3ex}[0pt][0pt]{\kern 1.5ex ,}}T", # ditto
    u"\u021B":r"\makebox[0pt]{\raisebox{-0.3ex}[0pt][0pt]{\kern 0.8ex ,}}t", # ditto
    u"\u0250":r"\textipa{5}",
    u"\u0251":r"\textipa{A}",
    u"\u0252":r"\textipa{6}",
    u"\u0254":r"\textipa{O}",
    u"\u0258":r"\textipa{9}",
    u"\u0259":r"\textipa{@}",
    u"\u025A":r"\textipa{\textrhookschwa}",
    u"\u025B":r"\textipa{E}",
    u"\u025C":r"\textipa{3}",
    u"\u0261":r"\textipa{g}",
    u"\u0265":r"\textipa{4}",
    u"\u0266":r"\textipa{H}",
    u"\u0268":r"\textipa{1}",
    u"\u026A":r"\textipa{I}",
    u"\u026F":r"\textipa{W}",
    u"\u0271":r"\textipa{M}",
    u"\u0275":r"\textipa{8}",
    u"\u0278":r"\textipa{F}",
    u"\u0279":r"\textipa{\textturnr}",
    u"\u027E":r"\textipa{R}",
    u"\u0281":r"\textipa{K}",
    u"\u0283":r"\textipa{S}",
    u"\u0289":r"\textipa{0}",
    u"\u028A":r"\textipa{U}",
    u"\u028B":r"\textipa{V}",
    u"\u028C":r"\textipa{2}",
    u"\u028E":r"\textipa{L}",
    u"\u028F":r"\textipa{Y}",
    u"\u0292":r"\textipa{Z}",
    u"\u0294":r"\textipa{P}",
    u"\u0295":r"\textipa{Q}",
    u"\u02C8":r'\textipa{"}',
    u"\u02CC":r"\textipa{\textsecstress}",
    u"\u02D0":r"\textipa{:}",
    u"\u02D1":r"\textipa{;}",
    u"\u1D17":r"\tikz[baseline=-0.5ex]{\draw[line width=0.4pt, line cap=round] (0,0) arc[start angle=180, end angle=360, radius=0.4ex];}",
    u"\u2002":r"\hskip 1ex {}", # ?
    u"\u2003":r"\hskip 1em {}",
    u"\u2009":r"\thinspace{}",
    u"\u2013":"--{}",
    u"\u2014":"---",
    u"\u2018":"`{}",
    u"\u2019":"'{}",
    u"\u201b":"`{}",
    u"\u201c":"``",
    u"\u201d":"''",
    u"\u2020":r"\dag{}",
    u"\u2022":r"$\bullet$",
    u"\u2027":r"\textperiodcentered{}", # = 0xb7 ?
    u"\u202f":r"\nolinebreak\\thinspace{}",
    u"\u2070":"$^0$",
    u"\u2074":r"\raisebox{-0.3ex}{$^4$}",
    u"\u2075":r"\raisebox{-0.3ex}{$^5$}",
    u"\u2076":r"\raisebox{-0.3ex}{$^6$}",
    u"\u2077":r"\raisebox{-0.3ex}{$^7$}",
    u"\u2078":r"\raisebox{-0.3ex}{$^8$}",
    u"\u2079":r"\raisebox{-0.3ex}{$^9$}",
    u"\u20AC":r"\euro{}",
    u"\u210D":r"$\mathbb{H}$",
    u"\u210E":r"$h$",
    u"\u2115":r"$\mathbb{N}$",
    u"\u2119":r"$\mathbb{P}$",
    u"\u211D":r"$\mathbb{R}$",
    u"\u2122":r"\textsuperscript{TM}",
    u"\u2150":r"\sfrac17",
    u"\u2151":r"\sfrac19",
    u"\u2152":r"\sfrac1{10}",
    u"\u2153":r"\sfrac13",
    u"\u2154":r"\sfrac23",
    u"\u2155":r"\sfrac15",
    u"\u2156":r"\sfrac25",
    u"\u2157":r"\sfrac35",
    u"\u2158":r"\sfrac45",
    u"\u2159":r"\sfrac16",
    u"\u215A":r"\sfrac56",
    u"\u215B":r"\sfrac18",
    u"\u215C":r"\sfrac38",
    u"\u215D":r"\sfrac58",
    u"\u215E":r"\sfrac78",
    u"\u2190":r"$\leftarrow$",
    u"\u2191":r"$\uparrow$",
    u"\u2192":r"$\rightarrow$",
    u"\u2193":r"$\downarrow$",
    u"\u2194":r"$\leftrightarrow$",
    u"\u2195":r"$\updownarrow$",
    u"\u2196":r"$\nwarrow$",
    u"\u2197":r"$\nearrow$",
    u"\u2198":r"$\searrow$",
    u"\u2199":r"$\swarrow$",
    u"\u21A6":r"$\mapsto$",
    u"\u21C4":r"$\rightleftarrows$",
    u"\u21D0":r"$\Leftarrow$",
    u"\u21D1":r"$\Uparrow$",
    u"\u21D2":r"$\Rightarrow$",
    u"\u21D3":r"$\Downarrow$",
    u"\u21D4":r"$\Leftrightarrow$",
    u"\u21D5":r"$\Updownarrow$",
    u"\u221E":r"$\infty$",
    u"\u2260":r"$\neq$",
    u"\u25c7":r"$\diamondsuit$",
    u"\u25cf":r"$\bullet$",
    u"\u2654":r"\symking{}",u"\u2655":r"\symqueen{}",
    u"\u2656":r"\symrook{}",u"\u2657":r"\symbishop{}",
    u"\u2658":r"\symknight{}",u"\u2659":r"\sympawn{}",
    # TODO: black versions of the above (U+265A-F)
    u"\u266d":r"$\flat$",
    u"\u266e":r"$\natural$",
    u"\u266f":r"$\sharp$",
    u"\u26ac":r"$\circ$",
    u"\u2713":r"$\checkmark$",
    u"\u2714":r"\textbf{$\checkmark$}",
    u"\u2756":r"$\diamondsuit$",
    u"\u293b":r"$\searrow\nearrow$", # ?
    u"\u2AA4":r"\shortstack{$><$\\$><$}", # ?
    u"\uFB00":"ff",
    u"\uFB01":"fi",
    u"\uFB02":"fl",
    u"\uFB03":"ffi",
    u"\uFB04":"ffl",
    })
  latex_special_chars.update(dict((c,'$'+c+'$') for c in '|<>[]')) # always need math mode
  latex_special_chars.update(dict((c,'\\'+c) for c in '%&#$_{}')) # always need \ escape
  latex_special_chars.update(dict( # Braille patterns
    (unichr(0x2800+p),"\\braillebox{"+"".join(
      chr(ord('1')+b) for b in range(8) if p & (1<<b))+"}"
     +("" if p else r"\allowbreak{}")) for p in xrange(256)))
  for c in list(range(0x3b1,0x3ca))+list(range(0x391,0x3aa)): # Greek stuff:
    if c==0x3a2: continue
    if c>=0x3b1: textGreek=lambda c:'\\text'+unicodedata.name(unichr(c)).replace('FINAL ','VAR').split()[-1].lower().replace('cron','kron').replace('amda','ambda')+'{}'
    else: textGreek=lambda c:'\\text'+unicodedata.name(unichr(c)).split()[-1][0]+unicodedata.name(unichr(c)).split()[-1][1:].lower().replace('cron','kron').replace('amda','ambda')+'{}'
    latex_special_chars[unichr(c)]=textGreek(c)
    for mark,accent in [('oxia',"'"),('tonos',"'"),('varia',"`"),("perispomeni","~")]: # TODO: psili like a little ')', dasia (its opposite), etc; also some have more than one diacritic (e.g. psili and perispomeni vertically stacked, dasia (or psili) and oxia horizontally??) (+ TODO at low priority can we get any difference between the tonos and the oxia)
        try: c2 = unicodedata.lookup(unicodedata.name(unichr(c))+" with "+mark)
        except KeyError: continue
        latex_special_chars[my_normalize(c2)]="\\shortstack{\\raisebox{-1.5ex}[0pt][0pt]{\\"+accent+r"{}}\\"+textGreek(c)+"}"
  # For pinyin, use pinyin package (it has kerning tweaks)
  # (leaving out rare syllables like "den" from below because it's not always defined and it seems to cause more trouble than it's worth)
  toned_pinyin_syllables = """a ai an ang ao ba
    bai ban bang bao bei ben beng bi bian biao bie
    bin bing bo bu ca cai can cang cao ce cen ceng
    cha chai chan chang chao che chen cheng chi
    chong chou chu chua chuai chuan chuang chui
    chun chuo ci cong cou cu cuan cui cun cuo da
    dai dan dang dao de dei deng di dian diao die
    ding diu dong dou du duan dui dun duo e ei en
    eng er fa fan fang fei fen feng fiao fo fou fu
    ga gai gan gang gao ge gei gen geng gong gou
    gu gua guai guan guang gui gun guo ha hai han
    hang hao he hei hen heng hong hou hu hua huai
    huan huang hui hun huo ji jia jian jiang jiao
    jie jin jing jiong jiu ju juan jue jun ka kai
    kan kang kao ke kei ken keng kong kou ku kua
    kuai kuan kuang kui kun kuo la lai lan lang
    lao le lei leng li lia lian liang liao lie lin
    ling liu long lou lu luan lun luo lv lve ma
    mai man mang mao mei men meng mi mian miao mie
    min ming miu mo mou mu na nai nan nang nao ne
    nei nen neng ni nian niang niao nie nin ning
    niu nong nou nu nuan nuo nv nve o ou pa pai
    pan pang pao pei pen peng pi pian piao pie pin
    ping po pou pu qi qia qian qiang qiao qie qin
    qing qiong qiu qu quan que qun ran rang rao re
    ren reng ri rong rou ru rua ruan rui run ruo
    sa sai san sang sao se sen seng sha shai shan
    shang shao she shei shen sheng shi shou shu
    shua shuai shuan shuang shui shun shuo si song
    sou su suan sui sun suo ta tai tan tang tao te
    tei teng ti tian tiao tie ting tong tou tu
    tuan tui tun tuo wa wai wan wang wei wen weng
    wo wu xi xia xian xiang xiao xie xin xing
    xiong xiu xu xuan xue xun ya yan yang yao ye
    yi yin ying yo yong you yu yuan yue yun za zai
    zan zang zao ze zei zen zeng zha zhai zhan
    zhang zhao zhe zhei zhen zheng zhi zhong zhou
    zhu zhua zhuai zhuan zhuang zhui zhun zhuo zi
    zong zou zu zuan zui zun zuo""".split()
  def num2marks(o): return reduce(lambda s,x:s.replace(*x),[
      ("a1",u'\u0101'),("ai1",u'\u0101i'),("ao1",u'\u0101o'),
      ("an1",u'\u0101n'),("ang1",u'\u0101ng'),("o1",u'\u014d'),
      ("ou1",u'\u014du'),("e1",u'\u0113'),("ei1",u'\u0113i'),
      ("en1",u'\u0113n'),("eng1",u'\u0113ng'),("i1",u'\u012b'),
      ("in1",u'\u012bn'),("ing1",u'\u012bng'),("ong1",u'\u014dng'),
      ("ou1",u'\u014du'),("u1",u'\u016b'),("un1",u'\u016bn'),
      ("v1",u'\u01d6'),("a2",u'\xe1'),("ai2",u'\xe1i'),
      ("ao2",u'\xe1o'),("an2",u'\xe1n'),("ang2",u'\xe1ng'),
      ("o2",u'\xf3'),("ou2",u'\xf3u'),("e2",u'\xe9'),("ei2",u'\xe9i'),
      ("en2",u'\xe9n'),("eng2",u'\xe9ng'),("i2",u'\xed'),
      ("in2",u'\xedn'),("ing2",u'\xedng'),("o2",u'\xf3'),
      ("ong2",u'\xf3ng'),("ou2",u'\xf3u'),("u2",u'\xfa'),
      ("un2",u'\xfan'),("v2",u'\u01d8'),("a3",u'\u01ce'),
      ("ai3",u'\u01cei'),("ao3",u'\u01ceo'),("an3",u'\u01cen'),
      ("ang3",u'\u01ceng'),("o3",u'\u01d2'),("ou3",u'\u01d2u'),
      ("e3",u'\u011b'),("ei3",u'\u011bi'),("en3",u'\u011bn'),
      ("eng3",u'\u011bng'),("er1",u'\u0113r'),("er2",u'\xe9r'),
      ("er3",u'\u011br'),("er4",u'\xe8r'),("Er1",u'\u0112r'),
      ("Er2",u'\xc9r'),("Er3",u'\u011ar'),("Er4",u'\xc8r'),
      ("i3",u'\u01d0'),("in3",u'\u01d0n'),("ing3",u'\u01d0ng'),
      ("o3",u'\u01d2'),("ong3",u'\u01d2ng'),("ou3",u'\u01d2u'),
      ("u3",u'\u01d4'),("un3",u'\u01d4n'),("v3",u'\u01da'),
      ("a4",u'\xe0'),("ai4",u'\xe0i'),("ao4",u'\xe0o'),
      ("an4",u'\xe0n'),("ang4",u'\xe0ng'),("o4",u'\xf2'),
      ("ou4",u'\xf2u'),("e4",u'\xe8'),("ei4",u'\xe8i'),
      ("en4",u'\xe8n'),("eng4",u'\xe8ng'),("i4",u'\xec'),
      ("in4",u'\xecn'),("ing4",u'\xecng'),("o4",u'\xf2'),
      ("ong4",u'\xf2ng'),("ou4",u'\xf2u'),("u4",u'\xf9'),
      ("un4",u'\xf9n'),("v4",u'\u01dc'),("A1",u'\u0100'),
      ("Ai1",u'\u0100i'),("Ao1",u'\u0100o'),("An1",u'\u0100n'),
      ("Ang1",u'\u0100ng'),("O1",u'\u014c'),("Ou1",u'\u014cu'),
      ("E1",u'\u0112'),("Ei1",u'\u0112i'),("En1",u'\u0112n'),
      ("Eng1",u'\u0112ng'),("Ou1",u'\u014cu'),("A2",u'\xc1'),
      ("Ai2",u'\xc1i'),("Ao2",u'\xc1o'),("An2",u'\xc1n'),
      ("Ang2",u'\xc1ng'),("O2",u'\xd3'),("Ou2",u'\xd3u'),
      ("E2",u'\xc9'),("Ei2",u'\xc9i'),("En2",u'\xc9n'),
      ("Eng2",u'\xc9ng'),("Ou2",u'\xd3u'),("A3",u'\u01cd'),
      ("Ai3",u'\u01cdi'),("Ao3",u'\u01cdo'),("An3",u'\u01cdn'),
      ("Ang3",u'\u01cdng'),("O3",u'\u01d1'),("Ou3",u'\u01d1u'),
      ("E3",u'\u011a'),("Ei3",u'\u011ai'),("En3",u'\u011an'),
      ("Eng3",u'\u011ang'),("Ou3",u'\u01d1u'),("A4",u'\xc0'),
      ("Ai4",u'\xc0i'),("Ao4",u'\xc0o'),("An4",u'\xc0n'),
      ("Ang4",u'\xc0ng'),("O4",u'\xd2'),("Ou4",u'\xd2u'),
      ("E4",u'\xc8'),("Ei4",u'\xc8i'),("En4",u'\xc8n'),
      ("Eng4",u'\xc8ng'),("Ou4",u'\xd2u'),("v5",u"\xfc"),
      ("ve5",u"\xfce")],o)
  py_protected = "a chi cong ding ge hang le min mu ne ni nu o O pi Pi Re tan xi Xi".split()
  for p in toned_pinyin_syllables+[(x[0].upper()+x[1:]) for x in toned_pinyin_syllables]:
    for t in "1 2 3 4 5".split():
        m = num2marks(p+t)
        if m==p+t: continue
        p=p.replace('Long','LONG').replace('long','Long')
        if p in py_protected: latex_special_chars[m]='\\PYactivate\\'+p+t+"\\PYdeactivate{}"
        else: latex_special_chars[m]='\\'+p+t
  # Make sure everything's normalized:
  for k,v in list(latex_special_chars.items()):
    k2 = my_normalize(k)
    if not k==k2:
      assert not k2 in latex_special_chars, repr(k)+':'+repr(v)+" is already covered by "+repr(k2)+":"+repr(latex_special_chars[k2]) # but this won't catch cases where it's already covered by matchAccentedLatin (however we might not want it to, e.g. pinyin overrides)
      latex_special_chars[k2] = v
      del latex_special_chars[k]
  latex_preamble = {
    # TODO: if not odd number of \'s before?  (but OK if
    # accidentally include a package not really needed)
    r"\tikz":r"\usepackage{tikz}",
    r"\boldsymbol":r"\usepackage{amsmath}",
    r"\mathfrak":r"\usepackage{amsmath}",
    r"\mathbb":    r"\usepackage[cal=dutchcal,bb=libus]{mathalpha}",
    r"\mathbfsfit":r"\usepackage[cal=dutchcal,bb=libus]{mathalpha}",
    r"\mathbffrak":r"\usepackage[cal=dutchcal,bb=libus]{mathalpha}",
    r"\mathbfcal": r"\usepackage[cal=dutchcal,bb=libus]{mathalpha}",
    r"\mathsfit":  r"\usepackage[cal=dutchcal,bb=libus]{mathalpha}",
    r"\mathcal":   r"\usepackage[cal=dutchcal,bb=libus]{mathalpha}",
    r"\calligra":r"\usepackage{calligra}",
    r"\CJKfamily":r"\usepackage{CJK}",
    r"\begin{multicols}":r"\usepackage{multicol}",
    r"\braille":r"\usepackage[puttinydots]{braille}",
    r"\usym":r"\usepackage{utfsym}",
    r"\sfrac":r"\usepackage{xfrac}",
    r"\checkmark":r"\usepackage{amssymb}",
    r'\rightleftarrows':r"\usepackage{amssymb}",
    r"\euro":r"\usepackage{eurosym}",
    r"\markboth":r"\usepackage{fancyhdr}", # TODO: what if page_headings is set on a document that contains no anchors and therefore can't be tested in unistr ?
    r"\title":r"\usepackage[hyperfootnotes=false]{hyperref}", # as will get tableofcontents
    r"\texorpdfstring":r"\usepackage[hyperfootnotes=false]{hyperref}",
    r"\href":r"\usepackage[hyperfootnotes=false]{hyperref}",
    r"\hyper":r"\usepackage[hyperfootnotes=false]{hyperref}",
    r"\pdfbookmark":r"\usepackage[hyperfootnotes=false]{hyperref}",
    r'\nolinkurl':r"\usepackage[hyperfootnotes=false]{hyperref}", # or r"\url":r"\usepackage{url}", but must use hyperref instead if might be using hyperref for other things (see comments above)
    r"\includegraphics":r"\usepackage{graphicx}",
    r"\definecolor":r"\usepackage{xcolor}", # may be in tex-literal
    r"\includesvg":r"\usepackage{svg}",
    r'\sout':r"\usepackage[normalem]{ulem}",
    r'\stack':r"\newsavebox\stackBox\def\fitbox#1{\sbox\stackBox{#1}\ifdim \wd\stackBox >\columnwidth \vskip 0pt \resizebox*{\columnwidth}{!}{#1} \vskip 0pt \else{#1}\fi}\def\stack#1#2{\fitbox{\shortstack{\raisebox{0pt}[2.3ex][0ex]{#2} \\ \raisebox{0pt}[1.9ex][0.5ex]{#1}}}}", # (I also gave these measurements to Wenlin; they work for basic ruby with rb=hanzi rt=pinyin)
    r'\sym':r"\usepackage{chessfss}",
    r"\textipa":r"\usepackage[safe]{tipa}",
    r'\text':r"\usepackage{textgreek} % sudo apt install texlive-science", # (if you don't have texlive-full, e.g. because it depends on vprerex and the QT libraries are messed up in Ubuntu 22)
    r'\uline':r"\usepackage[normalem]{ulem}",
    }
  latex_special_chars.update(simple_html2latex_noregex)
  def handleV(k,v):
    if type(v) in [str,unicode]:
      return v.replace('\\','\\\\')
    else: # callable, e.g. EmOn
      del latex_special_chars[k] # don't let subDict use its 'fast' mode which won't call the callable
      return v
  def handleK(k):
    endsWithLetter = re.search(u"[A-Za-z0-9][\u0300-\u036f]*$",unicode(k))
    k=re.escape(k)
    if endsWithLetter: k=unicode(k)+u"(?![\u0300-\u036f])" # DON'T match if it contains any ADDITIONAL accents (otherwise might get spurious pinyin matches)
    return k
  latex_regex1 = dict((handleK(k),handleV(k,v)) for (k,v) in list(latex_special_chars.items()))
  latex_regex1.update(simple_html2latex_regex)
  latex_regex1[u'[A-Za-z0-9][\u0300-\u036f]+']=matchAccentedLatin ; latex_regex1[u'[\u02b0-\u036f]']=lambda m:TeX_unhandled_accent(m.group())
  # and figure out the range of all other non-ASCII chars:
  needToMatch = []
  taken=sorted([ord(k) for k in latex_special_chars.keys() if len(k)==1 and 0x80<=ord(k)<0xfffd]+list(range(0x2b0,0x370)))
  start=0x80 ; taken.append(0xfffd)
  while taken:
      if start<taken[0]:
          if start==taken[0]-1: needToMatch.append(unichr(start))
          else: needToMatch.append(unichr(start)+'-'+unichr(taken[0]-1)) # (OK in some cases we can also dispense with the '-' but let's not worry too much about that)
      start = taken[0]+1 ; taken=taken[1:]
  latex_regex1['['+''.join(needToMatch)+']+']=matchAllCJK
  latex_regex1['[^'+unichr(0)+'-'+unichr(0xFFFF)+']+']=matchAllCJK # we also want to catch non-BMP with this on non-narrow builds (this will overmatch, but we fix this in matchAllCJK)
  # done init
  sys.stderr.write("making tex... ")
  unistr = my_normalize(decode_entities(unistr)) # TODO: even in anchors etc? (although hopefully remove_utf8_diacritics is on)
  global used_cjk,emphasis ; used_cjk=emphasis=False
  mySubDict = subDict(latex_regex1)
  unistr = mySubDict(unistr)
  for m in ['mathbf','mathit','boldsymbol','mathcal',
            'mathfrak','mathbb','mathbffrak','mathsf',
            r'boldsymbol{\mathcal',
            r'mathbf{\mathsf','mathsfit','mathbfsfit','mathtt']:
    # combine multiple letters in maths fonts:
    unistr=re.sub('('+re.escape('$\\'+m+'{')+'[A-Za-z0-9]'+re.escape('}}$' if '{' in m else '}$')+')+',lambda M:M.group().replace(('}' if '{' in m else '')+'}$$\\'+m+'{',''),unistr)
  unistr = unistr.replace('$$','') # we don't use display-math, so $$ must mean two adjacent bits of maths
  ret = r'\documentclass['+class_options+(((',' if class_options else '')+'twoside') if r'\chapter' in unistr else '')+']{'+('report' if r'\chapter' in unistr else 'article')+r'}\usepackage[T1]{fontenc}\usepackage{pinyin}\PYdeactivate\usepackage{parskip}'
  ret += r'\IfFileExists{microtype.sty}{\usepackage{microtype}}{\pdfadjustspacing=2\pdfprotrudechars=2}' # nicer line breaking (but the PDFs may be larger)
  ret += r'\raggedbottom'
  global geometry
  if a5 and r"\chapter" in unistr: geometry=geometry.replace("lmargin=3mm,rmargin=3mm,tmargin=3mm,bmargin=3mm","lmargin=5mm,rmargin=5mm,tmargin=4mm,bmargin=4mm")
  ret += r'\usepackage['+geometry+']{geometry}'
  if trade and lulu: ret += r'\mag=890'
  ret += '\n'.join(set(v for (k,v) in latex_preamble.items() if k in unistr))+'\n'
  assert not (r'\usepackage{CJK}' in ret and (r'\em{' in unistr or r'\bf{' in unistr)
              and any(os.path.exists(f) and
                      'Version 4.8.4 (18-Apr-2015)' in open(f).read()
                      for f in [
                          "/usr/share/texmf/tex/latex/CJK/CJK.sty",
                          "/usr/share/texlive/texmf-dist/tex/latex/CJK/CJK.sty",
                          "/usr/share/texmf-texlive/tex/latex/CJK/CJK.sty"])
              and not (os.path.exists(f) and not
                       'Version 4.8.4 (18-Apr-2015)' in open(f).read()
                       for f in [os.environ.get("HOME")+"/texmf/tex/latex/CJK/CJK.sty"])
              ), "CJK package is broken on systems like Ubuntu 22.04 LTS (fixed in 24.04 LTS): bold and emphasis will not work unless you override it with a newer CJK package in ~/texmf (or upgrade the distro)" # may also affect boldness of title etc
  if r'\title{' in unistr:
    if 'pdftitle' in os.environ: ret = ret.replace("hyperfootnotes=false]{hyperref}",("pdfauthor={"+os.environ['pdfauthor']+"}," if 'pdfauthor' in os.environ else '')+"pdftitle={"+os.environ['pdftitle']+"},hyperfootnotes=false]{hyperref}") # TODO: document that you can set pdfauthor and pdftitle in environment
    title = re.findall(r'\\title{.*?}%title',unistr,flags=re.DOTALL)[0] # might have <br>s in it
    ret += title[:title.rindex('%')]+r"\date{}\usepackage{tocloft}\usepackage{fancyhdr}\clubpenalty1000\widowpenalty1000\advance\cftchapnumwidth 0.5em\hypersetup{pdfborder={0 0 0},linktoc=all}"
    if chinese_book:
      ret=re.sub(r'\\usepackage.*?{hyperref}','',ret).replace(r'\hypersetup{pdfborder={0 0 0},linktoc=all}','').replace(r'\nolinkurl',r'\url')+r"\usepackage{url}\usepackage{CJKnumb}\setlength{\cftchapnumwidth}{4.5em}\setlength{\cftpartnumwidth}{4em}\renewcommand{\contentsname}{目录}\renewcommand{\thechapter}{第\arabic{chapter}章}\renewcommand{\thepart}{卷\CJKnumber{\arabic{part}}}\renewcommand{\partname}{}\renewcommand{\chaptername}{}"
      unistr = unistr.replace(r'\nolinkurl',r'\url')
      title = title.replace(r'\nolinkurl',r'\url')
    unistr = unistr.replace(title+'\n',"",1)
  else: title = None
  ret += r'\begin{document}'
  if used_cjk and chinese_book:
    ret += r"\begin{CJK}{UTF8}{gbsn}"
    unistr = re.sub(r"\\(part|chapter)(\[[^]]*\])?{[^}]*}",lambda m:m.group().replace(chr(0),''),unistr.replace(r'\CJKfamily{gbsn}',chr(0))).replace(chr(0),r'\CJKfamily{gbsn}')
  if r"\chapter" in unistr: ret += r'\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\fancyfoot[LE,RO]{\thepage}\fancypagestyle{plain}{\fancyhf{}\renewcommand{\headrulewidth}{0pt}\fancyhf[lef,rof]{\thepage}}'
  if title: ret += r'\maketitle\renewcommand{\cftchapleader}{\cftdotfill{\cftdotsep}}\tableofcontents\renewcommand{\baselinestretch}{1.1}\selectfont'
  if page_headings: ret += r'\pagestyle{fancy}\fancyhead{}\fancyfoot{}\fancyhead[LE]{\rightmark}\fancyhead[RO]{\leftmark}\thispagestyle{empty}'
  elif not r"\chapter" in unistr: ret += r'\pagestyle{empty}'
  # else: ret += r'\pagestyle{plain}'
  if used_cjk and not chinese_book: ret+=r"\begin{CJK}{UTF8}{}"
  if whole_doc_in_footnotesize: ret += r'\footnotesize'
  if not ret[-1]=='}': ret += '{}'
  ret += unistr # the document itself
  if used_cjk: ret += r"\end{CJK}"
  ret += r'\end{document}'+'\n'
  sys.stderr.write('done\n')
  def explain_unhandled(c):
    try: name=unicodedata.name(unichr(c))
    except: name="?"
    if any(x[0]==c for x in tex_accent_codes): name += " (matchAccentedLatin handles this for Latin letters, but the input had it with something else)"
    elif 0x2b0 <= c < 0x370: name += " (no 'missing' box was put in the TeX for this)" # see TeX_unhandled_accent (0x300+ are 'combining' and combine with previous char; below that are 'modifier' letters)
    return "U+%04X %s\n" % (c,name)
  if TeX_unhandled_codes:
    sys.stderr.write("Warning: makeLatex treated these characters as 'missing':\n"+"".join(explain_unhandled(c) for c in sorted(TeX_unhandled_codes)))
  return ret

def EmOn(*args):
    global emphasis ; emphasis=True
    return r'\em{}'
def EmOff(*args):
    global emphasis ; emphasis=False
    return r'\rm{}'

# CJK-LaTeX families that go well with Computer Modern.
# Some yitizi (variant) characters are missing from many
# TeX installations (TeXLive etc).  You could use XeTeX,
# but then you're likely to have a font setup nightmare.
# At least the following will get quite nice characters
# for the basic GB2312/Big5/JIS/KSC set (not the rarer
# yitizi that have only GB+/b5+ codes) - you could try
# uncommenting the 'song' line below, but it may not work.

# (If you have installed Cyberbit, try setting the
# CJK_LATEX_CYBERBIT_FALLBACK environment variable; we'll
# use it only as a 'fallback' for passages containing rare
# characters, because (a) the PDF won't copy/paste as well
# as Arphic and (b) it's not a language-optimised font.
# Even Cyberbit doesn't have ALL rare characters though,
# e.g. some of Unicode 3's "CJK Extension A" ones.)

# (Using for passages rather than individual characters as
# it really doesn't go well right next to other CJK fonts;
# the height etc is a bit different.  Using the other
# fonts for passages to get better language optimisation.)

cjk_latex_families = [
    ('gb2312', ('gbsn','gkai')), # Arphic Simplified
    ('big5', ('bsmi','bkai')), # Arphic Traditional
    ('sjis', 'min'), # Wadalab Japanese (TODO: kaiti?)
    ('ksc5601', 'mj'), # Korean (TODO: kaiti??)
    # ('utf-8', 'song'), # likely to say missing cyberb50
    ]

if os.environ.get('CJK_LATEX_CYBERBIT_FALLBACK',0):
  cjk_latex_families += [([(0,7),(14,15),(0x1e,0x1f),(0x20,0x27),(0x30,0x3e),(0x4e,0xa0),(0xac,0xd8),(0xe8,0xe9),(0xf0,0xf1),(0xf9,256)],'cyberbit')]

def bestCodeAndFamily(hanziStr): return max((codeMatchLen(hanziStr,code),-count,code,family) for count,(code,family) in zip(xrange(9),cjk_latex_families))[-2:] # (the 'count' part means if all other things are equal the codes listed here first will be preferred)
def codeMatchLen(hanziStr,code):
  if type(code)==list: # Unicode range list (MSB only)
    count = 0
    for c in hanziStr:
      c = int(ord(c)/256)
      if not any((x[0]<=c<x[1]) for x in code): break
      count += 1
    return count
  else: return (hanziStr+'?').encode(code,'replace').decode(code).index('?')
TeX_unhandled_codes = set()
def TeX_unhandled_code(u):
    TeX_unhandled_codes.add(u)
    return r"\thinspace\allowbreak{\footnotesize\texorpdfstring{\fbox{$^{\rm ?}$%04X}}{[?%04X]}}\thinspace\allowbreak{}" % (u,u)
def TeX_unhandled_accent(combining_or_modifier_unichr):
    TeX_unhandled_codes.add(ord(combining_or_modifier_unichr)) # for the warning
    return "" # but don't write anything to the document (TODO: or do we?  if so, change explain_unhandled also)
def my_normalize(k):
  k = unicodedata.normalize('NFD',unicode(k))
  k = re.sub(u'[\u0300-\u036f]+',lambda a:u"".join(sorted(list(a.group()))),k) # make sure combining accents are always in same order (unicodedata.normalize doesn't always do this e.g. 308 vs 30c) (TODO: if we put the ones that occur in latex_special_chars.keys() first, it might help with things like Greek where we know some accents but not others.  However this would have to be coded carefully because my_normalize is called DURING the construction of latex_special_chars.)
  k = re.sub(u'[\u1100-\u11ff\u3040-\u30ff]+',lambda a:unicodedata.normalize('NFC',a.group()),k) # as we DON'T want things like hangul being broken into jamo and kana having its voiced-sound mark separated off
  return k
def decode_entities(unistr): return re.sub('&([^&;]+);',matchEntity,unistr)
def matchEntity(m):
  mid=m.group(1)
  if mid.startswith('#'):
    mid=mid[1:]
    if mid.startswith('x'): base,mid=16,mid[1:]
    else: base=10
    try: return unichr(int(mid,base))
    except: pass
  elif mid in htmlentitydefs.name2codepoint:
    return unichr(htmlentitydefs.name2codepoint[mid])
  return m.group()
combining_codes_requiring_dotless_ij=u'\u0300\u0301\u0302\u0303\u0304'
tex_accent_codes = [
  # TeX equivalents for Unicode combining accents
  # TODO: add more to these
  (0x300,"`"),(0x301,"'"),(0x302,'^'),
  (0x303,'~'),(0x304,'='),
  (0x306,"u"),(0x307,'.'),(0x308,'"'),
  (0x30a,'r'),(0x30b,'H'),(0x30c,"v"),
  (0x323,'d'),
  (0x327,'c'),(0x328,'k'),
  (0x331,'b'),
  ]
def matchAccentedLatin(match):
  m = match.group() ; l=m[0] ; m=m[1:]
  if l in 'ij' and any(ord(c)<=0x315 for c in m): l='\\'+l # i or j with accents above need to be dotless (TODO: check this applies for all combining accents 300-315 and no others)
  for combining_code,tex_accent in tex_accent_codes:
    cc = unichr(combining_code)
    if cc in m: m=m.replace(cc,"")
    else: continue
    if len(tex_accent)>1 or tex_accent in letters or len(l)>1: l="\\"+tex_accent+"{"+l+"}"
    else: l="\\"+tex_accent+l
  for leftOver in m: l += TeX_unhandled_accent(leftOver)
  return l

def matchAllCJK(match):
    hanziStr = match.group()
    r = []
    while hanziStr:
        code,family = bestCodeAndFamily(hanziStr)
        if type(family)==tuple:
          if emphasis: family=family[1]
          else: family=family[0]
        mLen = codeMatchLen(hanziStr,code)
        if mLen:
            r.append(r"\CJKfamily{"+family+"}") # (don't try to check if it's already that: this can go wrong if it gets reset at the end of an environment like in an href)
            r.append(hanziStr[:mLen])
            global used_cjk ; used_cjk = True
        elif not ord(hanziStr[0])==0x200b:
            code,mLen = ord(hanziStr[0]),1
            if 0xD800 <= code <= 0xDFFF and len(hanziStr)>1:
              # Might be a surrogate pair on narrow Python build (e.g. on Mac)
              high,low = ord(hanziStr[0]),ord(hanziStr[1])
              if low <= 0xDBFF: high,low = low,high
              if 0xD800 <= high <= 0xDBFF and 0xDC00 <= low <= 0xDFFF:
                code = (high-0xD800)*0x400+low-0xDC00+0x10000
                mLen = 2
            if nonBMPstr(code) in latex_special_chars: # overmatched non-BMP to work around narrow build: fix up here
              r.append(latex_special_chars[nonBMPstr(code)])
              mLen = len(nonBMPstr(code))
            else:
              r.append(TeX_unhandled_code(code))
        hanziStr = hanziStr[mLen:]
    return u"".join(r)

def nonBMPstr(c):
  try: return unichr(c)
  except: return unichr(int((c-0x10000)/0x400)+0xD800)+unichr((c%0x400)+0xDC00) # surrogate pair on narrow build

def subDict(d):
    "Returns a function on txt which replaces all keys in d with their values (keys are regexps and values are regexp-substitutes or callables)"
    k = list(d.keys()) ; kPinyin = []
    k.sort(key=lambda x: -len(x)) # longest 1st (this is needed by Python regexp's '|' operator)
    pyEnd = u"(?![\u0300-\u036f])" # need to do this for keeping the regexp manageable on some platforms e.g. Mac:
    for i in k[:]:
      if unicode(i).endswith(pyEnd):
        k.remove(i) ; kPinyin.append(re.sub(u"\\\\([\u0300-\u036f])",r"\1",unicode(i)[:-len(pyEnd)]))
    omit = set(re.escape(c) for c in latex_special_chars.keys()) # handled separately for speed
    k2 = [i for i in k if not i in omit]
    k.append('(?:(?:'+'|'.join(kPinyin)+')'+pyEnd+')')
    def func(match):
        mg = match.group()
        if mg in latex_special_chars: return latex_special_chars[mg]
        # work out which key it matched, then redo the
        # sub so backslash replacements work
        for i in k2:
            m=re.match(i,mg,re.DOTALL)
            if not m: continue
            if m.end()==len(mg):
                return re.sub(i,d[i],mg,flags=re.DOTALL)
        assert 0, "shouldn't get here, match="+repr(match.group())+" d="+repr(d.items())
    return lambda txt: re.sub(u'|'.join(k),func,txt,flags=re.DOTALL) # this and other DOTALLs needed for <tex-literal> to be able to span more than one line

# -------------------------------------------------

if __name__ == "__main__":
 if version:
   print(__doc__.split("\n\n")[0]) ; sys.exit(0)
 if infile:
    sys.stderr.write("Reading from "+infile+"... ")
    infile = open(infile)
 else:
    sys.stderr.write("Reading from "+("standard input" if sys.stdin.isatty() else "pipe")+"... ")
    infile = sys.stdin
 sys.stderr.flush()
 if outfile: outf = open(outfile,'w')
 else: outf = sys.stdout
 theDoc = infile.read()
 if not type(theDoc)==type(u""): theDoc=theDoc.decode('utf-8') # Python 2
 theDoc = unicodedata.normalize('NFC',theDoc)
 fragments = re.split(u'<a name="([^"]*)"></a>',theDoc)
 if len(fragments)==1:
  # a document with no fragments - just do HTML to LaTeX
  texDoc = makeLatex(theDoc)
 else:
  # odd indices should be the tag names, even should be the HTML in between
  assert len(fragments)>3, "Couldn't find 2 or more hash tags (were they formatted correctly?)"
  assert len(fragments)%2, "re.split not returning groups??"
  header,footer = fragments[0],fragments[-1]
  fragments = fragments[1:-1]
  sys.stderr.write("%d entries\n" % len(fragments))
  def alphaOnly(x):
    if ignore_text_in_parentheses: x=re.sub(r"\([^)]*\)[;, ]*","",x)
    if alphabet: x=''.join(c for c in x.lower() if c in alphabet)
    return re.sub(r"^[@,;]*","",x) # (to make sure anything starting with a phrase in parens, numbers, etc, followed by space or punctuation, is listed according to its second word when more_sensible_punctuation_sort_order is set, and not according to that space/punctuation)
  if more_sensible_punctuation_sort_order:
      _ao1 = alphaOnly
      alphaOnly = lambda x: _ao1(re.sub('([;,]);+',r'\1',x.replace('-',' ').replace(',','~COM~').replace(';',',').replace('~COM~',';').replace(' ',';'))) # gives ; < , == space (see ohi.py)
      if alphabet:
        for c in '@,;':
          if not c in alphabet: alphabet += c
  if remove_utf8_diacritics: _ao,alphaOnly = alphaOnly, lambda x: _ao(u''.join((c for c in unicodedata.normalize('NFD',x) if not unicodedata.category(c).startswith('M'))))
  fragments = list(zip(map(alphaOnly,fragments[::2]), fragments[::2], fragments[1::2]))
  fragments.sort()
  # fragments is now a sorted (sortKey, tag, contents).
  # If necessary, remove any adjacent "see" items
  seeExp=re.compile("<a href=\"#([^\"]*)\">(.*)</a>$")
  if remove_adjacent_see:
    lastRefs = [] ; needRm = set()
    for sort,tag,item in fragments:
      if tag.endswith('*'): m=re.search(seeExp,item)
      else: m = None
      if m:
        refersTo = m.group(1)
        if refersTo in lastRefs:
          needRm.add((sort,tag,item))
        else: lastRefs.append(refersTo) # a 'see' reference - so don't allow the next one to point to the same place
      else: lastRefs.append(tag) # a proper entry - but don't allow 'see' refs to it immediately after it
      while len(lastRefs) > remove_adjacent_see:
        del lastRefs[0]
    # and just to make sure we don't have entries with 'see' refs immediately BEFORE them:
    fragments.reverse()
    lastRealItems = []
    for sort,tag,item in fragments:
      if tag.endswith('*'): m=re.search(seeExp,item)
      else: m = None
      if m:
        refersTo = m.group(1)
        if refersTo in lastRealItems:
          needRm.add((sort,tag,item))
        else: lastRealItems.append(None)
      else: lastRealItems.append(tag)
      while len(lastRealItems) > remove_adjacent_see:
        del lastRealItems[0]
    fragments.reverse()
    if needRm:
      sys.stderr.write("remove_adjacent_see: removing %d adjacent alternate headings\n" % len(needRm))
      for x in needRm: fragments.remove(x)
    if not links_and_bookmarks:
      # As the links will be removed, we can additionally merge adjacent 'see' headings with the same link anchor text (but this time keep both headings, just don't duplicate the anchor text after the 1st)
      for i in xrange(len(fragments)-1):
        if fragments[i][1].endswith('*') and fragments[i+1][1].endswith('*') and re.search(seeExp,fragments[i][2]) and re.search(seeExp,fragments[i+1][2]) and re.search(seeExp,fragments[i][2]).group(2)==re.search(seeExp,fragments[i+1][2]).group(2):
          item = fragments[i][2] ; item = item[:re.search(seeExp,item).start()].rstrip()
          if item.endswith("<em>see</em>"): item=item[:-len("<em>see</em>")].rstrip() # TODO: other languages?
          fragments[i]=fragments[i][:2]+(item,)
  if suppress_adjacent_see:
    toGo = suppress_adjacent_see
    for i in xrange(len(fragments)-1):
      if fragments[i][1].endswith('*') and re.search(seeExp,fragments[i][2]):
        if not toGo:
          fragments[i]=fragments[i][:2]+(fragments[i][2].replace("<em>see</em> ",""),) # TODO: other languages?
        else: toGo -= 1
      else: toGo = suppress_adjacent_see # reset (ordinary, non-'see' entry)
  # Now put fragments into texDoc, adding letter headings
  # and smaller-type parts as necessary:
  allLinks=set(re.findall(u'<a href="#[^"]*">',theDoc)+re.findall(u'<a href=#[^>]*>',theDoc))
  targetsHad = set()
  def refd_in_doc(n):
    # Returns whether anchor name 'n' occurs in an href (reads allLinks, and reads/writes targetsHad for a bit more speed)
    if n and (n in targetsHad or ('<a href="#'+n+'">' in allLinks or '<a href=#'+n+'>' in allLinks)):
      targetsHad.add(n) ; return True
  def tag(n):
    if refd_in_doc(n): return '<a name="%s"></a>' % n
    else: return '' # we don't want unused ones in TeX
  texDoc = [] ; thisLetter=chr(0) ; sepNeeded="";inSmall=0
  for x,origX,y in fragments:
    if x and not x.startswith(thisLetter) and not x.startswith(thisLetter.lower()) and 'a'<=x[0].lower()<='z': # new letter section (TODO: optional?)
      thisLetter = x[0].upper()
      if inSmall: texDoc.append("</small>")
      if page_headings: texDoc.append(r"<tex-literal>\markboth{%s}{%s}</tex-literal>" % (thisLetter,thisLetter)) # needed if it starts with a load of 'see' references that don't have marks
      if links_and_bookmarks: texDoc.append("<tex-literal>\\section*{\\pdfbookmark{%s}{anchor%s}%s}</tex-literal>" % (thisLetter,thisLetter,thisLetter))
      else: texDoc.append("<tex-literal>\\section*{%s}</tex-literal>" % thisLetter)
      sepNeeded = "" ; inSmall=0
    make_entry_small = (origX.endswith('*') and not '<small>' in y) # TODO: optional? + document that we do this?
    if make_entry_small and not inSmall:
      texDoc.append("<small>") ; inSmall = 1
    elif inSmall and not make_entry_small:
      texDoc.append("</small>") ; inSmall = 0
    if sepNeeded=='; ':
      if origX.endswith('*'): sepNeeded=os.environ.get("OHI_LATEX_SMALL_SEPARATOR",";")+' ' # you can set OHI_LATEX_SMALL_SEPARATOR if you want some separator other than semicolon (e.g. you can set it to just a space if you like)
      else: sepNeeded='<br>'
    texDoc.append(sepNeeded+tag(origX)+y) # must be origX so href can work; will all be substituted for numbers anyway
    if origX.endswith('*'): sepNeeded = '; '
    else: sepNeeded='<br>'
  #if inSmall: texDoc.append("</small>") # not really needed at end of doc if we just translate it to \normalsize{}
  # Now we have a document ready to convert to LaTeX:
  texDoc = makeLatex(header+''.join(texDoc)+footer)
 if not type(u"")==type(""): texDoc=texDoc.encode('utf-8') # Python 2
 outf.write(texDoc)
 if outfile:
  outf.close()
  if dry_run: sys.exit()
  if r'\tableofcontents' in texDoc: passes=3
  elif r'\hyper' in texDoc: passes=2
  else: passes=1 # TODO: any other values? (below line supports any)
  sys.stderr.write("Running pdflatex... ")
  for ext in ["aux","log","toc","out","pdf"]:
    # ensure doesn't mess up new TeX run (e.g. if required packages for TOC have changed)
    try: os.remove(re.sub(r"tex$",ext,outfile))
    except: pass
  args='-file-line-error -halt-on-error "'+outfile+'" >/dev/null' # >/dev/null added because there'll likely be many hbox warnings; log file is more manageable than having them on-screen
  if r"\usepackage{svg}" in texDoc: args="--shell-escape "+args # so it can run inkscape to convert the svg
  r=os.system("&&".join(['pdflatex -draftmode '+args]*(passes-1)+['pdflatex '+args]))
  assert not r, "pdflatex failure (see "+re.sub(r"tex$","log",outfile)+")"
  sys.stderr.write("done\n")
  pdffile = re.sub(r"tex$","pdf",outfile)
  if links_and_bookmarks: os.system('''
  # this can help enable annotations on old versions of acroread
  # (for some reason).  Doesn't really depend on links_and_bookmarks
  # but I'm assuming if you have links_and_bookmarks switched off
  # you're sending it to printers and therefore don't need to enable
  # annotations for people who have old versions of acroread
  
  if which qpdf 2>/dev/null >/dev/null; then
  /bin/echo -n "Running qpdf..." >&2 &&
  qpdf $(if qpdf --help=encryption 2>/dev/null|grep allow-weak-crypto >/dev/null; then echo --allow-weak-crypto; fi) --encrypt "" "" 128 --print=full --modify=all -- "'''+pdffile+'" "/tmp/q'+pdffile+'''" &&
  mv "/tmp/q'''+pdffile+'" "'+pdffile+'" && echo " done" >&2 ; fi')
  if sys.platform=="darwin" and not no_open and not os.environ.get("SSH_CLIENT"):
    os.system('open "'+pdffile+'"') # (don't put this before the above qpdf: even though there's little chance of the race condition failing, Preview can still crash after qpdf finishes)
    import time ; time.sleep(1) # (give 'open' a chance to finish opening the file before returning control to the shell, in case the calling script renames the file or something)
