#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Should work on either Python 2 or Python 3

# Simple CEDICT (or ADSO-dict) to HTML filter, v1.3
# Silas S. Brown 2013, 2020, public domain, no warranty

# Input on stdin, output on stdout
# to pipe to Offline HTML Indexer

# Where to find history:
# on GitHub at https://github.com/ssb22/indexer
# and on GitLab at https://gitlab.com/ssb22/indexer
# and on BitBucket https://bitbucket.org/ssb22/indexer
# and at https://gitlab.developers.cam.ac.uk/ssb22/indexer
# and in China: git clone https://gitee.com/ssb22/indexer

def asUni(s):
    if type(s)==type(u""): return s
    else: return s.decode('utf-8','replace')
def asStr(s):
    if type(s)==type(""): return s
    else: return s.encode('utf-8')

import re,sys ; comments=[]
for line in sys.stdin:
 if line.startswith("#"): comments.append(line[1:].strip())
 elif '[' in line and '/' in line:
  for h in [line[line.index('[')+1:line.index(']')]]+\
      line[line.index('/')+1:line.rindex('/')].split('/'):
   if h: print ('<a name="'+h+'"></a>'+\
      asStr(asUni(re.sub(r"([A-Za-z][1-5])([aAeEoO])",r"\1'\2",line.\
             replace(h,'<b>'+h+'</b>'))).\
      replace(u"a1",u"ā").replace(u"ai1",u"āi").\
      replace(u"ao1",u"āo").replace(u"an1",u"ān").\
      replace(u"ang1",u"āng").replace(u"o1",u"ō").\
      replace(u"ou1",u"ōu").replace(u"e1",u"ē").\
      replace(u"ei1",u"ēi").replace(u"en1",u"ēn").\
      replace(u"eng1",u"ēng").replace(u"i1",u"ī").\
      replace(u"in1",u"īn").replace(u"ing1",u"īng").\
      replace(u"o1",u"ō").replace(u"ong1",u"ōng").\
      replace(u"ou1",u"ōu").replace(u"u1",u"ū").\
      replace(u"un1",u"ūn").replace(u"v1",u"ǖ").\
      replace(u"a2",u"á").replace(u"ai2",u"ái").\
      replace(u"ao2",u"áo").replace(u"an2",u"án").\
      replace(u"ang2",u"áng").replace(u"o2",u"ó").\
      replace(u"ou2",u"óu").replace(u"e2",u"é").\
      replace(u"ei2",u"éi").replace(u"en2",u"én").\
      replace(u"eng2",u"éng").replace(u"i2",u"í").\
      replace(u"in2",u"ín").replace(u"ing2",u"íng").\
      replace(u"o2",u"ó").replace(u"ong2",u"óng").\
      replace(u"ou2",u"óu").replace(u"u2",u"ú").\
      replace(u"un2",u"ún").replace(u"v2",u"ǘ").\
      replace(u"a3",u"ǎ").replace(u"ai3",u"ǎi").\
      replace(u"ao3",u"ǎo").replace(u"an3",u"ǎn").\
      replace(u"ang3",u"ǎng").replace(u"o3",u"ǒ").\
      replace(u"ou3",u"ǒu").replace(u"e3",u"ě").\
      replace(u"ei3",u"ěi").replace(u"en3",u"ěn").\
      replace(u"eng3",u"ěng").replace(u"i3",u"ǐ").\
      replace(u"er1",u"ēr").replace(u"er2",u"ér").\
      replace(u"er3",u"ěr").replace(u"er4",u"èr").\
      replace(u"Er1",u"Ēr").replace(u"Er2",u"Ér").\
      replace(u"Er3",u"Ěr").replace(u"Er4",u"Èr").\
      replace(u"in3",u"ǐn").replace(u"ing3",u"ǐng").\
      replace(u"o3",u"ǒ").replace(u"ong3",u"ǒng").\
      replace(u"ou3",u"ǒu").replace(u"u3",u"ǔ").\
      replace(u"un3",u"ǔn").replace(u"v3",u"ǚ").\
      replace(u"a4",u"à").replace(u"ai4",u"ài").\
      replace(u"ao4",u"ào").replace(u"an4",u"àn").\
      replace(u"ang4",u"àng").replace(u"o4",u"ò").\
      replace(u"ou4",u"òu").replace(u"e4",u"è").\
      replace(u"ei4",u"èi").replace(u"en4",u"èn").\
      replace(u"eng4",u"èng").replace(u"i4",u"ì").\
      replace(u"in4",u"ìn").replace(u"ing4",u"ìng").\
      replace(u"o4",u"ò").replace(u"ong4",u"òng").\
      replace(u"ou4",u"òu").replace(u"u4",u"ù").\
      replace(u"un4",u"ùn").replace(u"v4",u"ǜ").\
      replace(u"a5",u"a").replace(u"e5",u"e").\
      replace(u"i5",u"i").replace(u"o5",u"o").\
      replace(u"u5",u"u").replace(u"n5",u"n").\
      replace(u"g5",u"g").replace(u"v5",u"ü").\
      replace(u"r5",u"r").\
      replace(u"A1",u"Ā").replace(u"Ai1",u"Āi").\
      replace(u"Ao1",u"Āo").replace(u"An1",u"Ān").\
      replace(u"Ang1",u"Āng").replace(u"O1",u"Ō").\
      replace(u"Ou1",u"Ōu").replace(u"E1",u"Ē").\
      replace(u"Ei1",u"Ēi").replace(u"En1",u"Ēn").\
      replace(u"Eng1",u"Ēng").replace(u"Ou1",u"Ōu").\
      replace(u"A2",u"Á").replace(u"Ai2",u"Ái").\
      replace(u"Ao2",u"Áo").replace(u"An2",u"Án").\
      replace(u"Ang2",u"Áng").replace(u"O2",u"Ó").\
      replace(u"Ou2",u"Óu").replace(u"E2",u"É").\
      replace(u"Ei2",u"Éi").replace(u"En2",u"Én").\
      replace(u"Eng2",u"Éng").replace(u"Ou2",u"Óu").\
      replace(u"A3",u"Ǎ").replace(u"Ai3",u"Ǎi").\
      replace(u"Ao3",u"Ǎo").replace(u"An3",u"Ǎn").\
      replace(u"Ang3",u"Ǎng").replace(u"O3",u"Ǒ").\
      replace(u"Ou3",u"Ǒu").replace(u"E3",u"Ě").\
      replace(u"Ei3",u"Ěi").replace(u"En3",u"Ěn").\
      replace(u"Eng3",u"Ěng").replace(u"Ou3",u"Ǒu").\
      replace(u"A4",u"À").replace(u"Ai4",u"Ài").\
      replace(u"Ao4",u"Ào").replace(u"An4",u"Àn").\
      replace(u"Ang4",u"Àng").replace(u"O4",u"Ò").\
      replace(u"Ou4",u"Òu").replace(u"E4",u"È").\
      replace(u"Ei4",u"Èi").replace(u"En4",u"Èn").\
      replace(u"Eng4",u"Èng").replace(u"Ou4",u"Òu").\
      replace(u"A5",u"A").replace(u"E5",u"E").\
      replace(u"O5",u"O")))
   print ('<p>')
print ('<a name=""></a>')
if comments: print ('<hr>Data was adapted from '+"<br>".join(comments))
else: sys.stderr.write("c2h.py warning: input does not include copyright comments\n")
