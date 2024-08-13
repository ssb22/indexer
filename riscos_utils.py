# -*- coding: utf-8 -*-
# (should work in either Python 2 or Python 3)

"""RISC OS character set utilities - v0.3
(c) 2021, 2024 Silas S. Brown.  License: Apache 2
"""

def riscTxt(l,escape_StrongHelp=False):
    """Convert l into RISC OS / StrongHelp chars
    applying fi/fl ligatures (but not em-dash and
    curved-quote transforms: we assume that's been
    done before we got the text).
    Set escape_StrongHelp to True if you've not
    embedded StrongHelp links etc in the text."""
    if not type(l)==type(u""): l=l.decode('utf-8')
    log_missing(l)
    if escape_StrongHelp:
        for c in u"\\<{*": l=l.replace(c,u"\\"+c)
    l = u''.join(c if c in charset else u''.join(d for d in unicodedata.normalize('NFD',c) if d in charset) for c in l) # remove any combining marks we can't do, leaving basic Latin or Greek, plus drop any characters we can't do at all (they've already been reported by log_missing)
    l = re.sub(use_sidney,lambda m:'{f Sidney}'+m.group()+'{f}',l) # ensure Greek is in Sidney font
    return b"".join(
        charset[c] for c in re.sub(
            "(?<=[^f])fi",u"\ufb01",
            re.sub("(?<=[^f])fl",u"\ufb02",l)))

import unicodedata, re
def bchr(bytecode): return bytecode.to_bytes(1,'little') if type("")==type(u"") else chr(bytecode)
charset = dict((bchr(c).decode('latin1'),bchr(c)) for c in list(range(127))+list(range(0xA0,256)))
homerton_additions = u"€Ŵŵ--Ŷŷ-----…™‰•‘’‹›“”„–—−Œœ†‡ﬁﬂ" # System font also has arrows etc but these are not in Homerton/Corpus/Trinity (or FreeSans/FreeSerif which has both bold and italic variants); NewHall doesn't have anything before •
charset.update(dict((homerton_additions[i],bchr(0x80+i)) for i in range(32) if not homerton_additions[i]=='-'))
sidney = u" !∀#∃%&∍()*+,−./0123456789:;<=>?≅ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ[∴]⊥_-αβχδεφγηιϕκλμνοπθρστυϖωξψζ{|}~----------------------------------ϒ′≤⁄∞ƒ♣♦♥♠↔←↑→↓°±″≥×∝∂•÷≠≡≈…⏐⎯↵ℵℑℜ℘⊗⊕∅∩∪⊃⊇⊄⊂⊆∈∉∠∇®©™∏√⋅¬∧∨⇔⇐⇑⇒⇓◊⟨---∑⎛⎜⎝⎡⎢⎣⎧⎨⎩⎪-⟩∫⌠⎮⌡⎞⎟⎠⎤⎥⎦⎫⎬⎭" # similar to Symbol (but 0x60 ` is an overbar for the next character, however it assumes a fixed width and does not play well with dots, so not sure how well it would work for e.g. pinyin tone 1 marks).  Homerton and Trinity (and Corpus) do have a few more diacritic combinations in other code pages, but unclear how to change StrongHelp's codepage.
use_sidney = re.compile(u"["+u"".join(c for c in sidney if not c in charset)+u"]+")
charset.update(dict((sidney[i],bchr(0x20+i)) for i in range(len(sidney)) if not sidney[i] in charset))
selwyn = u" ✁✂✃✄❁✆-✈✉☛☞✌✍✎✏✐✑✒✓❂✕✖✗-✙✚✛✜✝✞✟✠✡✢✣✤✥✦✧-✩✪✫✬✭✮✯✰✱✲✳✴✵✶✷✸✹✺✻✼✽✾✿❀☎✔✘❄--❐❑❒◆----❏---▼▲-❖◗❘❙❚❛❜❝❞-------------------❬❱❰❨❪❳❮❯❲❭❫❩❴❵-❡❢❣❤❥❦❧♣♦♥♠①②③④⑤⑥⑦⑧⑨⑩❶❷❸❹❺❻❼❽❾❿➀➁➂➃➄➅➆➇➈➉➊➋➌➍➎➏➐➑➒➓➔→↔↕➘➙➚➛➜-➞➟➠➡➢➣➤➥➦-➨➩➪➫➬➭➮➯-➱➲➳➴➵➶➷➸➹➺➻➼➽➾" # similar to Zapf Dingbats but some codepoint swaps
charset.update(dict((selwyn[i],b"{f Selwyn}"+bchr(0x20+i)+b"{f}") for i in range(len(selwyn)) if not selwyn[i] in charset)) # unlikely to be repeated, so don't group font selection

logged_missing = set()
def log_missing(l):
    for c in l:
        if not c in charset and not u''.join(d for d in unicodedata.normalize('NFD',c) if d in charset) and not c in logged_missing:
            sys.stderr.write("Warning: dropping character %x (%s)\n" % (ord(c),c))
            logged_missing.add(c)
