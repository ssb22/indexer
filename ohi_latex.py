#!/usr/bin/env python

# ohi_latex: Offline HTML Indexer for LaTeX
# v1.0 (c) 2014 Silas S. Brown

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
# Includes a simple HTML to LaTeX converter with Unicode
# support (e.g. Chinese, Pinyin, Japanese, Greek, Russian,
# Braille, IPA, Latin diacritics and miscellaneous symbols)

# Configuration
# -------------

infile = None # None = standard input, or set a "filename"
outfile = "index.tex" # None = standard output, but if a filename is set then pdflatex will be run also

import sys
if '--createspace' in sys.argv:
  # these settings should work for CreateSpace's 7.5x9.25in printing service (max 828 pages per volume).  Not tested.
  geometry = "paperwidth=7.5in,paperheight=9.25in,twoside,inner=0.8in,outer=0.5in,tmargin=0.5in,bmargin=0.5in,columnsep=8mm" # inner=0.75in but suggest more if over 600 pages
  links_and_bookmarks = False # I have no idea what happens if you submit a PDF that contains links and bookmarks; they say don't do it, so best not!
elif '--lulu' in sys.argv:
  # these settings should work for Lulu's Letter-size printing service (max 740 pages per volume).  Not tested.
  geometry = "paperwidth=8.5in,paperheight=11in,twoside,inner=0.8in,outer=0.5in,tmargin=0.5in,bmargin=0.5in,columnsep=8mm"
  links_and_bookmarks = False
else:
  # these settings should work on most laser printers but I don't know about binding; should be OK for on-screen use
  geometry = "a4paper,lmargin=10mm,rmargin=10mm,tmargin=10mm,bmargin=15mm,columnsep=8mm"
  links_and_bookmarks = True

# You probably don't want to change the below for the print version:
alphabet = "abcdefghijklmnopqrstuvwxyz" # set to None for all characters and case-sensitive
ignore_text_in_parentheses = True # or False, for parentheses in index headings
more_sensible_punctuation_sort_order = True
remove_utf8_diacritics = True # for sorting purposes only

# --------------------------------------------------------

import unicodedata,htmlentitydefs,re,sys,os

def makeLatex(unistr):
  "Convert unistr into a LaTeX document"
  # init the lookup stuff INSIDE this function,
  # so it's not done unless makeLatex is actually used
  sys.stderr.write("makeLatex initialising... ")
  simple_html2latex_noregex = {
    # we add a non-standard 'twocols' tag:
    '<twocols>':r'\begin{multicols}{2}','</twocols>':r'\end{multicols}',
    # we add a non-standard 'sc' tag for small caps:
    '<sc>':r'\textsc{','</sc>':'}',
    # only very simple HTML is supported:
    '<html>':'','</html>':'','<body>':'','</body>':'',
    '<br>':r'\vskip -0.5\baselineskip{}'+'\n', # nicer to TeX's memory than \\ (-0.5\baselineskip is necessary because we're using parskip)
    '<p>':r'\medskip{}'+'\n', '\n':' ',
    '</p>':'', # assumes there'll be another <p>
    '<!--':'%', '-->':'\n', # works if no newlines in the comment
    '<i>':r'\em{}', '<em>':r'\em{}',
    '<b>':r'\bf{}', '<strong>':r'\bf{}',
    '</i>':r'\rm{}', '</em>':r'\rm{}', '</b>':r'\rm{}', '</strong>':r'\rm{}', # assumes well-formed
    '<u>':r'\uline{','</u>':'}',
    '<s>':r'\sout{','<strike>':r'\sout{',
    '</s>':'}', '</strike>':'}',
    '<big>':"\Large{}",
    '<small>':r"\offinterlineskip\lineskip2pt\footnotesize{}", # (The 'offinterlineskip' turns off the normal line spacing and makes line spacing effectively irregular depending on the height of each line; can be useful for saving paper if you have lots of additional text in 'small'; not sure if there's a way to turn interline skip back on for the rest of the paragraph etc)
    '</big>':"\normalsize{}",'</small>':r"\normalsize{}",
    '</a>':'}', # for simple_html2latex_regex below
    '<hr>':r"\medskip\hrule{}",
  }
  global anchorsHad ; anchorsHad = {}
  def safe_anchor(match,txt):
    match = match.group(1)
    if not match in anchorsHad: anchorsHad[match]=str(len(anchorsHad))
    return txt % anchorsHad[match]
  if links_and_bookmarks: href=r"\\href{\1}{"
  else:
    href = "" ; safe_anchor=lambda m:"" # just delete them
    del simple_html2latex_noregex['</a>']
  simple_html2latex_regex = {
    '<tex-literal>(.*?)</tex-literal>':r"\1",
    '<a href="#([^"]*)">':lambda m:safe_anchor(m,r"\hyperlink{%s}{"),
    '<a name="([^"]*)">':lambda m:safe_anchor(m,r"\hypertarget{%s}{\rule{0pt}{1ex}"), # the \rule{0pt}{1ex} is to make sure there's some text there, otherwise the target will be on the baseline which is what Acroread will scroll to
    '<a href="([^#][^"]*)">':href,
    # and support simple 1-word versions without quotes (TODO but we don't honour these in anchors when splitting the document into fragments)
    '<a href=#([^ >]*)>':lambda m:safe_anchor(m,r"\hyperlink{%s}{"),
    '<a name=([^"][^ >]*)>':lambda m:safe_anchor(m,r"\hypertarget{%s}{\rule{0pt}{1ex}"),
    '<a href=([^#"][^ >]*)>':href,
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
    u"\xB0":"$^{\\circ}$",
    u"\xB1":"$\\pm$",
    u"\xB2":"$^2$",
    u"\xB3":"$^3$",
    u"\xB4":"$^{\\prime}$",
    u"\xB5":"$\mu$", # micro sign
    u"\xB6":"\\P{}",
    u"\xB7":"\\textperiodcentered{}",
    u"\xB8":"\\c{}",
    u"\xB9":"$^1$",
    u"\xBB":"\\guillemotright{}",
    u"\xBC":"$\frac14$",
    u"\xBD":"$\frac12$",
    u"\xBE":"$\frac34$",
    u"\xC2":"\\^A",
    u"\xC3":"\\~A",
    u"\xC4":"\\\"A",
    u"\xC5":"\\AA{}",
    u"\xC6":"\\AE{}",
    u"\xC7":"\\c{C}",
    u"\xCA":"\\^E",
    u"\xCB":"\\\"E",
    u"\xCC":"\\\`I",
    u"\xCD":"\\\'I",
    u"\xCE":"\\^I",
    u"\xCF":"\\\"I",
    u"\xD1":"\\~N",
    u"\xD4":"\\^O",
    u"\xD5":"\\~O",
    u"\xD6":"\\\"O",
    u"\xD7":"$\\times$",
    u"\xD8":"\\O{}",
    u"\xD9":"\\\`U",
    u"\xDA":"\\\'U",
    u"\xDB":"\\^U",
    u"\xDF":"\\ss{}",
    u"\xE2":"\\^a",
    u"\xE3":"\\~a",
    u"\xE4":"\\\"a",
    u"\xE5":"\\aa{}",
    u"\xE6":"\\ae{}",
    u"\xE7":"\\c{c}",
    u"\xEA":"\\^e",
    u"\xEB":"\\\"e",
    u"\xEC":"\\\`i",
    u"\xED":"\\\'i",
    u"\xEE":"\\^i",
    u"\xEF":"\\\"i",
    u"\xF0":"\\textipa{D}",
    u"\xF1":"\\~n",
    u"\xF4":"\\^o",
    u"\xF5":"\\~o",
    u"\xF6":"\\\"o",
    u"\xF7":"$\\div$",
    u"\xF8":"\\o{}",
    u"\xF9":"\\\`u",
    u"\xFA":"\\\'u",
    u"\xFB":"\\^u",
    u"\xFD":"\\'y",
    u"\xFF":"\\\"y",
    # (TODO: any we missed in latin1.def, or other ISO-8859 codepages?)
    u"\u0103":"\\breve{a}",
    u"\u0106":"\\'C",
    u"\u0107":"\\'c",
    u"\u010c":"\\v{C}",
    u"\u010d":"\\v{c}",
    u"\u010e":"\\v{D}",
    u"\u012A":"\\=I",
    u"\u012B":"\\=i",
    u"\u0139":"\\'L",
    u"\u013A":"\\'l",
    u"\u013E":"\\v{l}", # l with caron
    u"\u0141":"\\L{}",
    u"\u0142":"\\l{}",
    u"\u0144":"\\'n",
    u"\u014B":"\\textipa{N}",
    u"\u014F":"\\breve{o}",
    u"\u0152":"\\OE{}",
    u"\u0153":"\\oe{}",
    u"\u0154":"\\'R",
    u"\u0155":"\\'r",
    u"\u0158":"\\v{R}",
    u"\u0159":"\\v{r}",
    u"\u015A":"\\'S",
    u"\u015B":"\\'s",
    u"\u015F":"\\c{s}",
    u"\u0160":"\\v{S}",
    u"\u0161":"\\v{s}",
    u"\u0163":"\\c{t}",
    u"\u0164":"\\v{T}",
    u"\u016A":"\\=U",
    u"\u016B":"\\=u",
    u"\u0179":"\\'Z",
    u"\u017A":"\\'z",
    u"\u017b":"\\.Z",
    u"\u017c":"\\.z",
    u"\u017d":"\\v{Z}",
    u"\u017e":"\\v{z}",
    u"\u01cf":"\\v{I}",
    u"\u01d0":"\\v{i}",
    u"\u01d3":"\\v{U}",
    u"\u01d4":"\\v{u}",
    u"\u01D5":"\\={\"U}",
    u"\u01D6":"\\={\"u}",
    u"\u01D7":"\\'{\"U}",
    u"\u01D8":"\\'{\"u}",
    u"\u01D9":"\\v{\"U}",
    u"\u01DA":"\\v{\"u}",
    u"\u01DB":"\\`{\"U}",
    u"\u01DC":"\\`{\"u}",
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
    u"\u2000":"\\hskip 1ex {}", # ?
    u"\u2001":"\\hskip 1em {}",
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
    u"\u2022":"$\\bullet$",
    u"\u2027":"\\textperiodcentered{}", # = 0xb7 ?
    u"\u202f":"\\nolinebreak\\thinspace{}",
    u"\u2070":"$^0$",
    u"\u2074":"$^4$",
    u"\u2075":"$^5$",
    u"\u2076":"$^6$",
    u"\u2077":"$^7$",
    u"\u2078":"$^8$",
    u"\u2079":"$^9$",
    u"\u20AC":"\\euro{}",
    u"\u2190":"$\\leftarrow$",
    u"\u2192":"$\\rightarrow$",
    u"\u2197":"$\\nearrow$",
    u"\u2198":"$\\searrow$",
    u"\u21D2":"$\\Rightarrow$",
    u"\u21d0":"$\\Leftarrow$",
    u"\u221E":"$\\infty$",
    u"\u2260":"$\\neq$",
    u"\u25c7":"$\\diamondsuit$",
    u"\u25cf":"$\\bullet$",
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
        latex_special_chars[c2]="\\shortstack{\\raisebox{-1.5ex}[0pt][0pt]{\\"+accent+r"{}}\\"+textGreek(c)+"}"
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
  # Also we might need to support some HTML entities:
  for k,v in htmlentitydefs.name2codepoint.items():
    v = unichr(v)
    if v in latex_special_chars: latex_special_chars['&'+k+';']=latex_special_chars[v]
  latex_preamble = {
    # TODO: if not odd number of \'s before?  (but OK if
    # accidentally include a package not really needed)
    r"\begin{CJK}":r"\usepackage{CJK}",
    r"\begin{multicols}":r"\usepackage{multicol}",
    r"\braille":"\\usepackage[puttinydots]{braille}",
    r"\checkmark":"\\usepackage{amssymb}",
    r"\euro":"\\usepackage{eurosym}",
    r"\href":"\\usepackage[hyperfootnotes=false]{hyperref}",
    r"\hyper":"\\usepackage[hyperfootnotes=false]{hyperref}",
    r'\sout':"\\usepackage[normalem]{ulem}",
    r"\textipa":"\\usepackage[safe]{tipa}",
    r'\text':"\\usepackage{textgreek}",
    r'\uline':"\\usepackage[normalem]{ulem}",
    }
  latex_special_chars.update(simple_html2latex_noregex)
  latex_regex1 = dict((re.escape(k),v.replace('\\','\\\\')) for (k,v) in latex_special_chars.items())
  latex_regex1.update(simple_html2latex_regex)
  # and figure out the range of all other non-ASCII chars:
  needToMatch = []
  taken=sorted(ord(k) for k in latex_special_chars.keys() if len(k)==1 and ord(k)>=0x80)
  start=0x80 ; taken.append(0xfffd)
  while taken:
      if start<taken[0]:
          if start==taken[0]-1: needToMatch.append(unichr(start))
          else: needToMatch.append(unichr(start)+'-'+unichr(taken[0]-1)) # (OK in some cases we can also dispense with the '-' but let's not worry too much about that)
      start = taken[0]+1 ; taken=taken[1:]
  latex_regex1['['+''.join(needToMatch)+']+']=matchAllCJK
  # done init
  sys.stderr.write("making tex... ")
  global currentCJKfamily ; currentCJKfamily=None
  unistr = subDict(latex_regex1,unistr)
  ret = r'\documentclass[12pt]{article}\usepackage[T1]{fontenc}\usepackage{pinyin}\PYdeactivate\usepackage{parskip}\usepackage{microtype}\raggedbottom\clubpenalty1000\widowpenalty10000\usepackage['+geometry+']{geometry}'+'\n'.join(set(v for (k,v) in latex_preamble.items() if k in unistr))+r'\begin{document}\pagestyle{empty}'+unistr
  if currentCJKfamily: ret += r"\end{CJK}"
  ret += r'\end{document}'+'\n'
  sys.stderr.write('done\n')
  if TeX_unhandled_chars: sys.stderr.write("Warning: makeLatex treated these characters as 'missing': "+" ".join(("U+%04X" % c) for c in sorted(ord(x) for x in TeX_unhandled_chars))+"\n")
  return ret

# CJK-LaTeX families that go well with Computer Modern.
# Problem is a lot of characters are missing from typical
# TeX distributions.  You could use XeTeX, but then
# you're likely to have a font setup nightmare (unless
# you want to typeset everything in Arial Unicode MS etc)
# and it's not easy to put old CJK-LaTeX onto XeTeX.
cjk_latex_families = [
    # Arphic fonts (Chinese) :
    ('gb2312', 'gbsn'), # TODO: or gkai for emphasized
    ('big5', 'bsmi'), # TODO: or bkai
    # Wadalab fonts (Japanese) :
    ('sjis', 'min'),
    # other families e.g. 'song' are likely to complain about missing stuff e.g. cyberb50
    ]
def bestCodeAndFamily(hanziStr): return max((codeMatchLen(hanziStr,code),-count,code,family) for count,(code,family) in zip(xrange(9),cjk_latex_families))[-2:] # (the 'count' part means if all other things are equal the codes listed here first will be preferred)
def codeMatchLen(hanziStr,code): return (hanziStr+'?').encode(code,'replace').decode(code).index('?')
TeX_unhandled_chars = set()
def TeX_unhandled_char(u):
    TeX_unhandled_chars.add(u)
    return r"\thinspace\allowbreak{\footnotesize\fbox{$^{\rm ?}$%04X}}\thinspace\allowbreak{}" % ord(u)
def matchAllCJK(match):
    global currentCJKfamily # TODO: put it in an object?
    hanziStr = match.group()
    r = []
    while hanziStr:
        code,family = bestCodeAndFamily(hanziStr)
        mLen = codeMatchLen(hanziStr,code)
        if mLen:
            if currentCJKfamily==family: pass
            elif currentCJKfamily: r.append(r"\CJKfamily{"+family+"}")
            else: r.append(r"\begin{CJK}{UTF8}{"+family+"}")
            currentCJKfamily = family
            r.append(hanziStr[:mLen])
        else:
            r.append(TeX_unhandled_char(hanziStr[0]))
            mLen = 1
        hanziStr = hanziStr[mLen:]
    return u"".join(r)

def subDict(d,txt):
    "In txt, replace all keys in d with their values (keys are regexps and values are regexp-substitutes or callables)"
    k = d.keys()
    k.sort(lambda x,y: cmp(len(y),len(x))) # longest 1st (this is needed by Python regexp's '|' operator)
    k2 = k[:]
    for c in latex_special_chars.keys():
        c = re.escape(c)
        if c in d: k2.remove(c) # handled separately for speed
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
    return re.sub(u'|'.join(k),func,txt)

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
allLinks=set(re.findall(ur'<a href="#[^"]*">',theDoc)+re.findall(ur'<a href=#[^>]*>',theDoc))
def tag(n):
  # for this version, we want to put the tags in only if they are actually used
  if n and ('<a href="#'+n+'">' in allLinks or '<a href=#'+n+'>' in allLinks): return '<a name="%s"></a>' % n
  else: return ''
texDoc = [] ; thisLetter=chr(0) ; sepNeeded="";inSmall=0
for x,origX,y in fragments:
  if x and not x.startswith(thisLetter) and not x.startswith(thisLetter.lower()) and 'a'<=x[0].lower()<='z': # new letter section (TODO: optional?)
    thisLetter = x[0].upper()
    if inSmall: texDoc.append("</small>")
    if links_and_bookmarks: texDoc.append("<tex-literal>\\section*{\\pdfbookmark{%s}{anchor%s}%s}</tex-literal>" % (thisLetter,thisLetter,thisLetter))
    else: texDoc.append("<tex-literal>\\section*{%s}</tex-literal>" % thisLetter)
    sepNeeded = "" ; inSmall=0
  make_entry_small = (origX.endswith('*') and not '<small>' in y) # TODO: optional? + document that we do this?
  if make_entry_small and not inSmall:
    texDoc.append("<small>") ; inSmall = 1
  elif inSmall and not make_entry_small:
    texDoc.append("</small>") ; inSmall = 0
  if sepNeeded=='; ' and not origX.endswith('*'):
    sepNeeded='<br>'
  texDoc.append(sepNeeded+tag(origX)+y) # must be origX so href can work; will all be substituted for numbers anyway
  if origX.endswith('*'): sepNeeded='; '
  else: sepNeeded='<br>'
#if inSmall: texDoc.append("</small>") # not really needed at end of doc if we just translate it to \normalsize{}
texDoc = makeLatex(header+''.join(texDoc)+footer)
outf.write(texDoc.encode('utf-8'))
if outfile:
  outf.close()
  if r'\hyper' in texDoc: passes=2
  else: passes=1 # TODO: any other values? (below line supports any)
  r=os.system("&&".join(['pdflatex -draftmode -file-line-error -halt-on-error "'+outfile+'"']*(passes-1)+['pdflatex -file-line-error -halt-on-error "'+outfile+'"']))
  assert not r, "pdflatex failure"
  pdffile = re.sub(r"\.tex$",".pdf",outfile)
  if links_and_bookmarks: os.system('if which qpdf 2>/dev/null >/dev/null; then echo Running qpdf 1>&2 && qpdf --encrypt "" "" 128 --print=full --modify=all -- "'+pdffile+'" /tmp/a.pdf && mv /tmp/a.pdf "'+pdffile+'"; fi') # this can help enable annotations on old versions of acroread (for some reason).  Doesn't really depend on links_and_bookmarks, but I'm assuming if you have links_and_bookmarks switched off you're sending it to printers and therefore don't need to enable annotations for people who have old versions of acroread.
  if sys.platform=="darwin": os.system('open "'+pdffile+'"') # TODO: is this always a good idea? (+ don't put this before the above qpdf: even though there's little chance of the race condition failing, Preview can still crash after qpdf finishes)
