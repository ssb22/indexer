#!/usr/bin/env python3
r"""
rtfuc v1.1
(c) 2024 Silas S. Brown.  License: Apache 2

Removes unnecessary \uc1 codes from RTF files
(to work around catdoc issue described by Ubuntu bug 2076244)
and provides better ASCII fallback characters when possible
(e.g. for unrtf --text)

Also available on PyPI:
https://pypi.org/project/rtfuc/
"""

def rtfuc(in_rtf: bytes) -> bytes:
    r"""Converts input RTF data (provided as a
    byte string of the RTF file's contents) into a
    version with unnecessary \uc1 removed, and
    better fall-back ASCII characters provided
    when possible.  Returns resulting RTF data
    as another byte string."""
    
    class UCMatch:
        def __init__(self): self.uc = 1
        def __call__(self,m):
            if re.match(br"\\uc%d$" % self.uc,
                        m.group()): # unneeded \uc
                return b""
            elif re.match(br"\\uc", m.group()):
                self.uc = int(m.group[3:])
                return m.group()
            codepoint = int(m.group()[2:-1])
            if self.uc == 1:
                if ascii_ok(codepoint):
                    return chr(codepoint).encode('ascii').replace(b" ",b"{} ")
                elif codepoint==169:
                    return br"\uc3\u169(c)\uc1{}"
                elif codepoint==174:
                    return br"\uc3\u174(R)\uc1{}"
                elif codepoint==0x2122:
                    return br"\uc4\u8482(TM)\uc1{}"
                subst = m.group()[-1:]
                subst2 = get_subst(codepoint)
                if subst==b"?" and subst2:
                    subst = subst2 # use ours instead
                return br"\u%d%s" % (codepoint,subst)
            elif ascii_ok(codepoint):
                    return chr(codepoint).encode('ascii') + m.group()[-1:]
            else: return m.group()
    ucMatch = UCMatch()
    return re.sub(br"(?<!\\)\\u((c[0-9]+)|([0-9]+[^0-9\\]))",
                  ucMatch, in_rtf)

def get_subst(codepoint):
    if codepoint < 0: codepoint += 0x10000
    if codepoint == 160: return br"\'20{}" # no-break space to normal space
    elif codepoint in [0x2013,0x2014]: return b"-"
    elif codepoint in [0x2018,0x2019]: return b"'"
    elif codepoint in [0x201C,0x201D]: return b'"'
    elif codepoint in [0x2022,0x2FE6]: return b"*"
    for c in unicodedata.normalize('NFD',chr(codepoint)):
        if ascii_ok(ord(c)): # remove diacritics
            return c.encode('ascii')

def ascii_ok(codepoint):
    return 32 <= codepoint < 127 and not chr(codepoint) in "\\{}"

import re, sys, unicodedata
def main():
    if sys.stdin.isatty() or sys.stdout.isatty():
        print ("Syntax: rtfuc < in.rtf > out.rtf")
    else: sys.stdout.buffer.write(rtfuc(sys.stdin.buffer.read()))
if __name__ == "__main__": main()
