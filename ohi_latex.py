#!/usr/bin/env python

# ohi_latex: Offline HTML Indexer for LaTeX
# v1.148 (c) 2014-18 Silas S. Brown

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# See comments in ohi.py for what this is about.
# This version basically takes the same input and uses
# pdflatex to make a PDF from it instead of HTML fragments.

# Includes a simple HTML to LaTeX converter with support for
# CJK (including Pinyin), Greek, Braille, IPA, Latin diacritics
# and miscellaneous symbols.  You could use this alone by
# giving standard input without any 'a name' tags.

# Configuration
# -------------

infile = None # None = standard input, or set a "filename"
outfile = "index.tex" # None = standard output, but if a filename is set then pdflatex will be run also

import sys
if '--lulu' in sys.argv:
  # These settings worked for Lulu's Letter-size printing service (max 740 pages per volume).  Tested 2015-05.
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
elif '--createspace' in sys.argv:
  # these settings should work for CreateSpace's 7.5x9.25in printing service (max 828 pages per volume).  Not tested.
  outfile = "index-createspace.tex"
  geometry = "paperwidth=7.5in,paperheight=9.25in,twoside,inner=0.8in,outer=0.5in,tmargin=0.5in,bmargin=0.5in,columnsep=8mm,includehead,headsep=0pt" # inner=0.75in but suggest more if over 600 pages
  multicol=r"\columnsep=14pt\columnseprule=.4pt"
  twocol_columns = 2 # or 3 at a push
  page_headings = True
  whole_doc_in_footnotesize=True ; links_and_bookmarks = False ; class_options="" ; remove_adjacent_see = 2 ; suppress_adjacent_see = 1 # (see 'lulu' above for these 5)
elif '--a4compact' in sys.argv:
  # these settings should work on most laser printers and MIGHT be ok for binding depending on who's doing it
  outfile = "index-a4compact.tex"
  geometry = "a4paper,twoside,inner=0.8in,outer=10mm,tmargin=10mm,bmargin=10mm,columnsep=8mm,includehead,headsep=0pt"
  multicol=r"\columnsep=14pt\columnseprule=.4pt"
  twocol_columns = 3
  page_headings = True
  whole_doc_in_footnotesize=True ; links_and_bookmarks = False ; class_options="" ; remove_adjacent_see = 2 ; suppress_adjacent_see = 1 # (see 'lulu' above for these 5)
else:
  # these settings should work on most laser printers but I don't know about binding; should be OK for on-screen use
  geometry = "a4paper,lmargin=10mm,rmargin=10mm,tmargin=10mm,bmargin=15mm,columnsep=8mm"
  multicol=""
  twocol_columns = 2
  page_headings = False # TODO: ?  (add includehead to the geometry if setting True)
  whole_doc_in_footnotesize=False
  links_and_bookmarks = True
  remove_adjacent_see = 0
  suppress_adjacent_see = 0
  class_options="12pt"

# You probably don't want to change the below for the print version:
alphabet = "abcdefghijklmnopqrstuvwxyz" # set to None for all characters and case-sensitive
ignore_text_in_parentheses = True # or False, for parentheses in index headings
more_sensible_punctuation_sort_order = True
remove_utf8_diacritics = True # for sorting purposes only

# --------------------------------------------------------

import unicodedata,htmlentitydefs,re,sys,os,string

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
    '<big>':"\Large{}",
    '<small>':r"\offinterlineskip\lineskip2pt\footnotesize{}", # (The 'offinterlineskip' turns off the normal line spacing and makes line spacing effectively irregular depending on the height of each line; can be useful for saving paper if you have lots of additional text in 'small'; not sure if there's a way to turn interline skip back on for the rest of the paragraph etc)
    '</big>':r"\normalsize{}",'</small>':r"\normalsize{}",
    '</a>':'}', # for simple_html2latex_regex below
    '<hr>':r"\medskip\hrule{}",
    # '<center>':r"{\centering ",'</center>':r"\par}", # OK if you'll only ever use that tag after a <p> or whatever
    '<center>':r"\begin{center}",'</center>':r"\end{center}",
    '<vfill>':r'\vfill{}',
    '<ruby><rb>':r'\stack{','</rb><rt>':'}{','</rt></ruby>':'}', # only basic <ruby><rb>...</rb><rt>...</rt></ruby> is supported by this; anything else will likely make an un-TeX'able file
    '<h2>':r'\section*{','</h2>':'}',
    '<h3>':r'\subsection*{','</h3>':'}',
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
    '((https?|s?ftp)://[!-#%-(*-;=-Z^-z|~]*)':lambda m:"\\nolinkurl{"+m.group(1).replace("&amp;",r"\&").replace("%",r"\%").replace("_",r"\_").replace('#',r'\#')+"}", # matches only the characters we can handle (and additionally does not match close paren, since that's often not part of a URL when it's quoted in text; TODO: stop at &gt; ?)
    '([a-z][a-z.]+\\.(com|net|org)/[!-#%-(*-;=-Z^-z|~]*)':lambda m:"\\nolinkurl{"+m.group(1).replace("&amp;",r"\&").replace("%",r"\%").replace("_",r"\_").replace('#',r'\#')+"}",
    }
  global latex_special_chars
  latex_special_chars = {
    '\\':"$\\backslash$",
    '~':"$\\sim$",u"\u223c":"$\\sim$",
    '^':"\\^{}",
    u"\xA0":"~",
    u"\xA3":"\\pounds{}",
    u"\xA7":"\\S{}",
    u"\xA9":"\\copyright{}",
    u"\xAB":"\\guillemotleft{}", # unavailable in OT1 but should be OK if using [T1]fontenc, which we should probably be doing anyway
    u"\xAC":"$\\lnot$",
    u"\xAD":"\\-", # soft hyphen
    u"\xAE":"\\textregistered{}",
    u"\xB0":"$^{\\circ}$", # or \usepackage{textcomp} and have \textdegree{} (not sure which is better)
    u"\xB1":"$\\pm$",
    u"\xB2":r"\raisebox{-0.3ex}{$^2$}",
    u"\xB3":r"\raisebox{-0.3ex}{$^3$}",
    u"\xB4":"$^{\\prime}$",
    u"\xB5":"$\mu$", # micro sign
    u"\xB6":"\\P{}",
    u"\xB7":"\\textperiodcentered{}",
    u"\xB8":"\\c{}",
    u"\xB9":r"\raisebox{-0.3ex}{$^1$}",
    u"\xBB":"\\guillemotright{}",
    u"\xBC":"$\\frac14$",
    u"\xBD":"$\\frac12$",
    u"\xBE":"$\\frac34$",
    u"\xC6":"\\AE{}",
    u"\xD7":"$\\times$",
    u"\xD8":"\\O{}",
    u"\xDF":"\\ss{}",
    u"\xE6":"\\ae{}",
    u"\xF0":"\\textipa{D}",
    u"\xF7":"$\\div$",
    u"\xF8":"\\o{}",
    # (TODO: any we missed in latin1.def, or other ISO-8859 codepages?)
    u"\u0141":"\\L{}",
    u"\u0142":"\\l{}",
    u"\u014B":"\\textipa{N}",
    u"\u0152":"\\OE{}",
    u"\u0153":"\\oe{}",
    u"\u0218": "\\makebox[0pt]{\\raisebox{-0.3ex}[0pt][0pt]{\\kern 1.2ex ,}}S", # Romanian hack
    u"\u0219":"\\makebox[0pt]{\\raisebox{-0.3ex}[0pt][0pt]{\\kern 0.8ex ,}}s", # ditto
    u"\u021A":"\\makebox[0pt]{\\raisebox{-0.3ex}[0pt][0pt]{\\kern 1.5ex ,}}T", # ditto
    u"\u021B":"\\makebox[0pt]{\\raisebox{-0.3ex}[0pt][0pt]{\\kern 0.8ex ,}}t", # ditto
    u"\u0250":"\\textipa{5}",
    u"\u0251":"\\textipa{A}",
    u"\u0252":"\\textipa{6}",
    u"\u0254":"\\textipa{O}",
    u"\u0258":"\\textipa{9}",
    u"\u0259":"\\textipa{@}",
    u"\u025A":"\\textipa{\\textrhookschwa}",
    u"\u025B":"\\textipa{E}",
    u"\u025C":"\\textipa{3}",
    u"\u0261":"\\textipa{g}",
    u"\u0265":"\\textipa{4}",
    u"\u0266":"\\textipa{H}",
    u"\u0268":"\\textipa{1}",
    u"\u026A":"\\textipa{I}",
    u"\u026F":"\\textipa{W}",
    u"\u0271":"\\textipa{M}",
    u"\u0275":"\\textipa{8}",
    u"\u0278":"\\textipa{F}",
    u"\u0279":"\\textipa{\\textturnr}",
    u"\u027E":"\\textipa{R}",
    u"\u0281":"\\textipa{K}",
    u"\u0283":"\\textipa{S}",
    u"\u0289":"\\textipa{0}",
    u"\u028A":"\\textipa{U}",
    u"\u028B":"\\textipa{V}",
    u"\u028C":"\\textipa{2}",
    u"\u028E":"\\textipa{L}",
    u"\u028F":"\\textipa{Y}",
    u"\u0292":"\\textipa{Z}",
    u"\u0294":"\\textipa{P}",
    u"\u0295":"\\textipa{Q}",
    u"\u02C8":"\\textipa{\"}",
    u"\u02CC":"\\textipa{\\textsecstress}",
    u"\u02D0":"\\textipa{:}",
    u"\u02D1":"\\textipa{;}",
    u"\u2002":"\\hskip 1ex {}", # ?
    u"\u2003":"\\hskip 1em {}",
    u"\u2009":"\\thinspace{}",
    u"\u2013":"--{}",
    u"\u2014":"---",
    u"\u2018":"`{}",
    u"\u2019":"'{}",
    u"\u201b":"`{}",
    u"\u201c":"``",
    u"\u201d":"''",
    u"\u2020":"\\dag{}",
    u"\u2022":"$\\bullet$",
    u"\u2027":"\\textperiodcentered{}", # = 0xb7 ?
    u"\u202f":"\\nolinebreak\\thinspace{}",
    u"\u2070":"$^0$",
    u"\u2074":r"\raisebox{-0.3ex}{$^4$}",
    u"\u2075":r"\raisebox{-0.3ex}{$^5$}",
    u"\u2076":r"\raisebox{-0.3ex}{$^6$}",
    u"\u2077":r"\raisebox{-0.3ex}{$^7$}",
    u"\u2078":r"\raisebox{-0.3ex}{$^8$}",
    u"\u2079":r"\raisebox{-0.3ex}{$^9$}",
    u"\u20AC":"\\euro{}",
    u"\u2122":"\\textsuperscript{TM}",
    u"\u2190":"$\\leftarrow$",
    u"\u2191":"$\\uparrow$",
    u"\u2192":"$\\rightarrow$",
    u"\u2193":"$\\downarrow$",
    u"\u2194":"$\\leftrightarrow$",
    u"\u2195":"$\\updownarrow$",
    u"\u2196":"$\\nwarrow$",
    u"\u2197":"$\\nearrow$",
    u"\u2198":"$\\searrow$",
    u"\u2199":"$\\swarrow$",
    u"\u21A6":"$\\mapsto$",
    u"\u21D0":"$\\Leftarrow$",
    u"\u21D1":"$\\Uparrow$",
    u"\u21D2":"$\\Rightarrow$",
    u"\u21D3":"$\\Downarrow$",
    u"\u21D4":"$\\Leftrightarrow$",
    u"\u21D5":"$\\Updownarrow$",
    u"\u221E":"$\\infty$",
    u"\u2260":"$\\neq$",
    u"\u25c7":"$\\diamondsuit$",
    u"\u25cf":"$\\bullet$",
    u"\u2654":"\\symking{}",u"\u2655":"\\symqueen{}",
    u"\u2656":"\\symrook{}",u"\u2657":"\\symbishop{}",
    u"\u2658":"\\symknight{}",u"\u2659":"\\sympawn{}",
    # TODO: black versions of the above (U+265A-F)
    u"\u266d":"$\\flat$",
    u"\u266e":"$\\natural$",
    u"\u266f":"$\\sharp$",
    u"\u2713":"$\\checkmark$",
    u"\u2714":"\\textbf{$\\checkmark$}",
    u"\u2756":"$\\diamondsuit$",
    u"\u293b":"$\\searrow\\nearrow$", # ?
    u"\u2AA4":"\\shortstack{$><$\\$><$}", # ?
    u"\uFB00":"ff",
    u"\uFB01":"fi",
    u"\uFB02":"fl",
    u"\uFB03":"ffi",
    u"\uFB04":"ffl",
    }
  latex_special_chars.update(dict((c,'$'+c+'$') for c in '|<>[]')) # always need math mode
  latex_special_chars.update(dict((c,'\\'+c) for c in '%&#$_{}')) # always need \ escape
  latex_special_chars.update(dict((unichr(0x2800+p),"\\braillebox{"+"".join(chr(ord('1')+b) for b in range(8) if p & (1<<b))+"}") for p in xrange(256))) # Braille - might as well
  for c in range(0x3b1,0x3ca)+range(0x391,0x3aa): # Greek stuff:
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
  toned_pinyin_syllables = "a ai an ang ao ba bai ban bang bao bei ben beng bi bian biao bie bin bing bo bu ca cai can cang cao ce cen ceng cha chai chan chang chao che chen cheng chi chong chou chu chua chuai chuan chuang chui chun chuo ci cong cou cu cuan cui cun cuo da dai dan dang dao de dei deng di dian diao die ding diu dong dou du duan dui dun duo e ei en eng er fa fan fang fei fen feng fiao fo fou fu ga gai gan gang gao ge gei gen geng gong gou gu gua guai guan guang gui gun guo ha hai han hang hao he hei hen heng hong hou hu hua huai huan huang hui hun huo ji jia jian jiang jiao jie jin jing jiong jiu ju juan jue jun ka kai kan kang kao ke kei ken keng kong kou ku kua kuai kuan kuang kui kun kuo la lai lan lang lao le lei leng li lia lian liang liao lie lin ling liu long lou lu luan lun luo lv lve ma mai man mang mao mei men meng mi mian miao mie min ming miu mo mou mu na nai nan nang nao ne nei nen neng ni nian niang niao nie nin ning niu nong nou nu nuan nuo nv nve o ou pa pai pan pang pao pei pen peng pi pian piao pie pin ping po pou pu qi qia qian qiang qiao qie qin qing qiong qiu qu quan que qun ran rang rao re ren reng ri rong rou ru rua ruan rui run ruo sa sai san sang sao se sen seng sha shai shan shang shao she shei shen sheng shi shou shu shua shuai shuan shuang shui shun shuo si song sou su suan sui sun suo ta tai tan tang tao te tei teng ti tian tiao tie ting tong tou tu tuan tui tun tuo wa wai wan wang wei wen weng wo wu xi xia xian xiang xiao xie xin xing xiong xiu xu xuan xue xun ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun za zai zan zang zao ze zei zen zeng zha zhai zhan zhang zhao zhe zhei zhen zheng zhi zhong zhou zhu zhua zhuai zhuan zhuang zhui zhun zhuo zi zong zou zu zuan zui zun zuo".split()
  def num2marks(o): return o.replace("a1",u'\u0101').replace("ai1",u'\u0101i').replace("ao1",u'\u0101o').replace("an1",u'\u0101n').replace("ang1",u'\u0101ng').replace("o1",u'\u014d').replace("ou1",u'\u014du').replace("e1",u'\u0113').replace("ei1",u'\u0113i').replace("en1",u'\u0113n').replace("eng1",u'\u0113ng').replace("i1",u'\u012b').replace("in1",u'\u012bn').replace("ing1",u'\u012bng').replace("ong1",u'\u014dng').replace("ou1",u'\u014du').replace("u1",u'\u016b').replace("un1",u'\u016bn').replace("v1",u'\u01d6').replace("a2",u'\xe1').replace("ai2",u'\xe1i').replace("ao2",u'\xe1o').replace("an2",u'\xe1n').replace("ang2",u'\xe1ng').replace("o2",u'\xf3').replace("ou2",u'\xf3u').replace("e2",u'\xe9').replace("ei2",u'\xe9i').replace("en2",u'\xe9n').replace("eng2",u'\xe9ng').replace("i2",u'\xed').replace("in2",u'\xedn').replace("ing2",u'\xedng').replace("o2",u'\xf3').replace("ong2",u'\xf3ng').replace("ou2",u'\xf3u').replace("u2",u'\xfa').replace("un2",u'\xfan').replace("v2",u'\u01d8').replace("a3",u'\u01ce').replace("ai3",u'\u01cei').replace("ao3",u'\u01ceo').replace("an3",u'\u01cen').replace("ang3",u'\u01ceng').replace("o3",u'\u01d2').replace("ou3",u'\u01d2u').replace("e3",u'\u011b').replace("ei3",u'\u011bi').replace("en3",u'\u011bn').replace("eng3",u'\u011bng').replace("er1",u'\u0113r').replace("er2",u'\xe9r').replace("er3",u'\u011br').replace("er4",u'\xe8r').replace("Er1",u'\u0112r').replace("Er2",u'\xc9r').replace("Er3",u'\u011ar').replace("Er4",u'\xc8r').replace("i3",u'\u01d0').replace("in3",u'\u01d0n').replace("ing3",u'\u01d0ng').replace("o3",u'\u01d2').replace("ong3",u'\u01d2ng').replace("ou3",u'\u01d2u').replace("u3",u'\u01d4').replace("un3",u'\u01d4n').replace("v3",u'\u01da').replace("a4",u'\xe0').replace("ai4",u'\xe0i').replace("ao4",u'\xe0o').replace("an4",u'\xe0n').replace("ang4",u'\xe0ng').replace("o4",u'\xf2').replace("ou4",u'\xf2u').replace("e4",u'\xe8').replace("ei4",u'\xe8i').replace("en4",u'\xe8n').replace("eng4",u'\xe8ng').replace("i4",u'\xec').replace("in4",u'\xecn').replace("ing4",u'\xecng').replace("o4",u'\xf2').replace("ong4",u'\xf2ng').replace("ou4",u'\xf2u').replace("u4",u'\xf9').replace("un4",u'\xf9n').replace("v4",u'\u01dc').replace("A1",u'\u0100').replace("Ai1",u'\u0100i').replace("Ao1",u'\u0100o').replace("An1",u'\u0100n').replace("Ang1",u'\u0100ng').replace("O1",u'\u014c').replace("Ou1",u'\u014cu').replace("E1",u'\u0112').replace("Ei1",u'\u0112i').replace("En1",u'\u0112n').replace("Eng1",u'\u0112ng').replace("Ou1",u'\u014cu').replace("A2",u'\xc1').replace("Ai2",u'\xc1i').replace("Ao2",u'\xc1o').replace("An2",u'\xc1n').replace("Ang2",u'\xc1ng').replace("O2",u'\xd3').replace("Ou2",u'\xd3u').replace("E2",u'\xc9').replace("Ei2",u'\xc9i').replace("En2",u'\xc9n').replace("Eng2",u'\xc9ng').replace("Ou2",u'\xd3u').replace("A3",u'\u01cd').replace("Ai3",u'\u01cdi').replace("Ao3",u'\u01cdo').replace("An3",u'\u01cdn').replace("Ang3",u'\u01cdng').replace("O3",u'\u01d1').replace("Ou3",u'\u01d1u').replace("E3",u'\u011a').replace("Ei3",u'\u011ai').replace("En3",u'\u011an').replace("Eng3",u'\u011ang').replace("Ou3",u'\u01d1u').replace("A4",u'\xc0').replace("Ai4",u'\xc0i').replace("Ao4",u'\xc0o').replace("An4",u'\xc0n').replace("Ang4",u'\xc0ng').replace("O4",u'\xd2').replace("Ou4",u'\xd2u').replace("E4",u'\xc8').replace("Ei4",u'\xc8i').replace("En4",u'\xc8n').replace("Eng4",u'\xc8ng').replace("Ou4",u'\xd2u').replace("v5",u"\xfc").replace("ve5",u"\xfce")
  py_protected = "a chi cong ding ge hang le min mu ne ni nu o O pi Pi Re tan xi Xi".split()
  for p in toned_pinyin_syllables+[(x[0].upper()+x[1:]) for x in toned_pinyin_syllables]:
    for t in "1 2 3 4 5".split():
        m = num2marks(p+t)
        if m==p+t: continue
        p=p.replace('Long','LONG').replace('long','Long')
        if p in py_protected: latex_special_chars[m]='\\PYactivate\\'+p+t+"\\PYdeactivate{}"
        else: latex_special_chars[m]='\\'+p+t
  # Make sure everything's normalized:
  for k,v in latex_special_chars.items():
    k2 = my_normalize(k)
    if not k==k2:
      assert not k2 in latex_special_chars, repr(k)+':'+repr(v)+" is already covered by "+repr(k2)+":"+repr(latex_special_chars[k2]) # but this won't catch cases where it's already covered by matchAccentedLatin (however we might not want it to, e.g. pinyin overrides)
      latex_special_chars[k2] = v
      del latex_special_chars[k]
  latex_preamble = {
    # TODO: if not odd number of \'s before?  (but OK if
    # accidentally include a package not really needed)
    r"\CJKfamily":r"\usepackage{CJK}",
    r"\begin{multicols}":r"\usepackage{multicol}",
    r"\braille":"\\usepackage[puttinydots]{braille}",
    r"\checkmark":"\\usepackage{amssymb}",
    r"\euro":"\\usepackage{eurosym}",
    r"\markboth":"\\usepackage{fancyhdr}", # TODO: what if page_headings is set on a document that contains no anchors and therefore can't be tested in unistr ?
    r"\href":"\\usepackage[hyperfootnotes=false]{hyperref}",
    r"\hyper":"\\usepackage[hyperfootnotes=false]{hyperref}",
    r'\nolinkurl':"\\usepackage[hyperfootnotes=false]{hyperref}", # or "\\url":"\\usepackage{url}", but must use hyperref instead if might be using hyperref for other things (see comments above)
    r'\sout':"\\usepackage[normalem]{ulem}",
    r'\stack':r"\newsavebox\stackBox\def\fitbox#1{\sbox\stackBox{#1}\ifdim \wd\stackBox >\columnwidth \vskip 0pt \resizebox*{\columnwidth}{!}{#1} \vskip 0pt \else{#1}\fi}\def\stack#1#2{\fitbox{\shortstack{\raisebox{0pt}[2.3ex][0ex]{#2} \\ \raisebox{0pt}[1.9ex][0.5ex]{#1}}}}", # (I also gave these measurements to Wenlin; they work for basic ruby with rb=hanzi rt=pinyin)
    r'\sym':"\\usepackage{chessfss}",
    r"\textipa":"\\usepackage[safe]{tipa}",
    r'\text':"\\usepackage{textgreek}",
    r'\uline':"\\usepackage[normalem]{ulem}",
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
  latex_regex1 = dict((handleK(k),handleV(k,v)) for (k,v) in latex_special_chars.items())
  latex_regex1.update(simple_html2latex_regex)
  latex_regex1[u'[A-Za-z0-9][\u0300-\u036f]+']=matchAccentedLatin ; latex_regex1[u'[\u02b0-\u036f]']=lambda m:TeX_unhandled_accent(m.group())
  # and figure out the range of all other non-ASCII chars:
  needToMatch = []
  taken=sorted([ord(k) for k in latex_special_chars.keys() if len(k)==1 and ord(k)>=0x80]+range(0x2b0,0x370))
  start=0x80 ; taken.append(0xfffd)
  while taken:
      if start<taken[0]:
          if start==taken[0]-1: needToMatch.append(unichr(start))
          else: needToMatch.append(unichr(start)+'-'+unichr(taken[0]-1)) # (OK in some cases we can also dispense with the '-' but let's not worry too much about that)
      start = taken[0]+1 ; taken=taken[1:]
  latex_regex1['['+''.join(needToMatch)+']+']=matchAllCJK
  # done init
  sys.stderr.write("making tex... ")
  unistr = my_normalize(decode_entities(unistr)) # TODO: even in anchors etc? (although hopefully remove_utf8_diacritics is on)
  global used_cjk,emphasis ; used_cjk=emphasis=False
  mySubDict = subDict(latex_regex1)
  unistr = mySubDict(unistr)
  ret = r'\documentclass['+class_options+r']{article}\usepackage[T1]{fontenc}\usepackage{pinyin}\PYdeactivate\usepackage{parskip}\usepackage{microtype}\raggedbottom\usepackage['+geometry+']{geometry}'+'\n'.join(set(v for (k,v) in latex_preamble.items() if k in unistr))+r'\begin{document}'
  if page_headings: ret += r'\pagestyle{fancy}\fancyhead{}\fancyfoot{}\fancyhead[LE]{\rightmark}\fancyhead[RO]{\leftmark}\thispagestyle{empty}'
  else: ret += r'\pagestyle{empty}'
  if used_cjk: ret += r"\begin{CJK}{UTF8}{}"
  if whole_doc_in_footnotesize: ret += r'\footnotesize{}'
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
  if TeX_unhandled_chars: sys.stderr.write("Warning: makeLatex treated these characters as 'missing':\n"+"".join(explain_unhandled(c) for c in sorted(ord(x) for x in TeX_unhandled_chars)))
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
TeX_unhandled_chars = set()
def TeX_unhandled_char(u):
    TeX_unhandled_chars.add(u)
    return r"\thinspace\allowbreak{\footnotesize\fbox{$^{\rm ?}$%04X}}\thinspace\allowbreak{}" % ord(u)
def TeX_unhandled_accent(combining_or_modifier_unichr):
    TeX_unhandled_chars.add(combining_or_modifier_unichr) # for the warning
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
    if len(tex_accent)>1 or tex_accent in string.letters or len(l)>1: l="\\"+tex_accent+"{"+l+"}"
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
        else:
            if not ord(hanziStr[0])==0x200b: r.append(TeX_unhandled_char(hanziStr[0]))
            mLen = 1
        hanziStr = hanziStr[mLen:]
    return u"".join(r)

def subDict(d):
    "Returns a function on txt which replaces all keys in d with their values (keys are regexps and values are regexp-substitutes or callables)"
    k = d.keys() ; kPinyin = []
    k.sort(lambda x,y: cmp(len(y),len(x))) # longest 1st (this is needed by Python regexp's '|' operator)
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
            m=re.match(i,mg)
            if not m: continue
            if m.end()==len(mg):
                return re.sub(i,d[i],match.group())
        assert 0, "shouldn't get here, match="+repr(match.group())+" d="+repr(d.items())
    return lambda txt: re.sub(u'|'.join(k),func,txt)

# -------------------------------------------------

if infile:
    sys.stderr.write("Reading from "+infile+"... ")
    infile = open(infile)
else:
    sys.stderr.write("Reading from standard input... ")
    infile = sys.stdin
if outfile: outf = open(outfile,'w')
else: outf = sys.stdout
theDoc = unicodedata.normalize('NFC',infile.read().decode('utf-8'))
fragments = re.split(ur'<a name="([^"]*)"></a>',theDoc)
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
  fragments = zip(map(alphaOnly,fragments[::2]), fragments[::2], fragments[1::2])
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
  allLinks=set(re.findall(ur'<a href="#[^"]*">',theDoc)+re.findall(ur'<a href=#[^>]*>',theDoc))
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
outf.write(texDoc.encode('utf-8'))
if outfile:
  outf.close()
  if '--dry-run' in sys.argv: sys.exit()
  if r'\hyper' in texDoc: passes=2
  else: passes=1 # TODO: any other values? (below line supports any)
  sys.stderr.write("Running pdflatex... ")
  r=os.system("&&".join(['pdflatex -draftmode -file-line-error -halt-on-error "'+outfile+'" >/dev/null']*(passes-1)+['pdflatex -file-line-error -halt-on-error "'+outfile+'" >/dev/null'])) # >/dev/null added because there'll likely be many hbox warnings; log file is more manageable than having them on-screen
  assert not r, "pdflatex failure (see "+outfile.replace(".tex",".log")+")"
  sys.stderr.write("done\n")
  pdffile = re.sub(r"\.tex$",".pdf",outfile)
  if links_and_bookmarks: os.system('if which qpdf 2>/dev/null >/dev/null; then /bin/echo -n "Running qpdf..." 1>&2 && qpdf --encrypt "" "" 128 --print=full --modify=all -- "'+pdffile+'" "/tmp/q'+pdffile+'" && mv "/tmp/q'+pdffile+'" "'+pdffile+'" && echo " done" 1>&2 ; fi') # this can help enable annotations on old versions of acroread (for some reason).  Doesn't really depend on links_and_bookmarks, but I'm assuming if you have links_and_bookmarks switched off you're sending it to printers and therefore don't need to enable annotations for people who have old versions of acroread.
  if sys.platform=="darwin" and not "--no-open" in sys.argv:
    os.system('open "'+pdffile+'"') # (don't put this before the above qpdf: even though there's little chance of the race condition failing, Preview can still crash after qpdf finishes)
    import time ; time.sleep(1) # (give 'open' a chance to finish opening the file before returning control to the shell, in case the calling script renames the file or something)
