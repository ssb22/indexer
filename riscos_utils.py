#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (should work in either Python 2 or Python 3)

"""RISC OS character set utilities - v0.1
(c) 2021, 2024 Silas S. Brown.  License: Apache 2
"""

def bchr(bytecode): return bytecode.to_bytes(1,'little') if type("")==type(u"") else chr(bytecode)
charset = dict((bchr(c).decode('latin1'),bchr(c)) for c in list(range(127))+list(range(0xA0,256)))
homerton_additions = u"€Ŵŵ--Ŷŷ-----…™‰•‘’‹›“”„–—−Œœ†‡ﬁﬂ" # System font also has arrows etc but these are not in Homerton/Corpus/Trinity (or FreeSans/FreeSerif which has both bold and italic variants); NewHall doesn't have anything before •
charset.update(dict((homerton_additions[i],bchr(0x80+i)) for i in range(32) if not homerton_additions[i]=='-'))
stronghelp_escapes = {u"<":br"\<",u"{":br"\{",u"*":br"\*",u"\\":br"\\"}
def riscTxt(l,escape_StrongHelp=False):
    """Convert l into RISC OS / StrongHelp chars
    applying fi/fl ligatures (but not em-dash and
    curved-quote transforms: we assume that's been
    done before we got the text).
    Set escape_StrongHelp to True if you've not
    embedded StrongHelp links etc in the text."""
    if not type(l)==type(u""): l=l.decode('utf-8')
    return b"".join(findChar(c,escape_StrongHelp) for c in re.sub("(?<=[^f])fi",u"\ufb01",re.sub("(?<=[^f])fl",u"\ufb02",l)))
import unicodedata, re
logged_missing = set()
def findChar(c,escape_StrongHelp=False):
    if escape_StrongHelp and c in stronghelp_escapes: return stronghelp_escapes[c]
    if c in charset: return charset[c]
    b = u''.join(re.findall(u'[ -~]',unicodedata.normalize('NFD',c))).encode('latin1')
    if b: return b # alnum w. diacritics stripped
    if not c in logged_missing:
        sys.stderr.write("Warning: dropping character %x (%s)\n" % (ord(c),c))
        logged_missing.add(c)
    return b""
