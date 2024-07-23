#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (should work in either Python 2 or Python 3)

"""RISC OS character set utilities - v0.2
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
    if escape_StrongHelp:
        for c in u"\\<{*": l=l.replace(c,u"\\"+c)
    l = re.sub(use_sidney,lambda m:'{f Sidney}'+m.group()+'{f}',l)
    return b"".join(
        findChar(c)
        for c in re.sub(
                "(?<=[^f])fi",u"\ufb01",
                re.sub("(?<=[^f])fl",u"\ufb02",
                       l)))

import unicodedata, re
def bchr(bytecode): return bytecode.to_bytes(1,'little') if type("")==type(u"") else chr(bytecode)
charset = dict((bchr(c).decode('latin1'),bchr(c)) for c in list(range(127))+list(range(0xA0,256)))
homerton_additions = u"€Ŵŵ--Ŷŷ-----…™‰•‘’‹›“”„–—−Œœ†‡ﬁﬂ" # System font also has arrows etc but these are not in Homerton/Corpus/Trinity (or FreeSans/FreeSerif which has both bold and italic variants); NewHall doesn't have anything before •
charset.update(dict((homerton_additions[i],bchr(0x80+i)) for i in range(32) if not homerton_additions[i]=='-'))
sidney = u" !∀#∃%&϶()*+,-./0123456789:;<=>?≅ΑΒXΔΕΦΓΗΙ-ΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ[∴]⊥_-αβχδεϕγηιφκλμνοπθρστυ-ωξψζ{|}~-----------------------------------′≤∕∞ƒ♣♦♥♠↔←↑→↓°±″≥×∝-•÷≠≡≈…│─↲ℵℑℜ℘⊗⊕⊘∩∪⊃⊇⊄⊂⊆∈∉∠∇®©™∏√⋅¬∧∨⇔⇐⇑⇒⇓◇----∑" # then part integrals
use_sidney = re.compile(u"["+u"".join(c for c in sidney if not c in charset)+u"]+")
charset.update(dict((sidney[i],bchr(0x20+i)) for i in range(len(sidney)) if not sidney[i] in charset))
charset.update({u"✅":b"{f WIMPSymbol}\x80{f}",u"❌":b"{f WIMPSymbol}\x84{f}"}) # unlikely to be repeated, so don't group font selection

logged_missing = set()
def findChar(c):
    if c in charset: return charset[c]
    b = u''.join(re.findall(u'[ -~]',unicodedata.normalize('NFD',c))).encode('latin1')
    if b: return b # alnum w. diacritics stripped
    if not c in logged_missing:
        sys.stderr.write("Warning: dropping character %x (%s)\n" % (ord(c),c))
        logged_missing.add(c)
    return b""
