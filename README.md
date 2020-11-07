# indexer
Offline HTML Indexer etc from http://ssb22.user.srcf.net/gradint/ohi.html
(also mirrored at http://ssb22.gitlab.io/gradint/ohi.html just in case)

This is a Python program (compatible with both Python 2 and Python 3), for creating large indices of HTML text which can be queried using simple Javascript that works on many mobile phone browsers without needing an Internet connection or a Web server. This is useful if you want to load a dictionary or other reference onto your phone (or computer) for use when connectivity is not available.

The input HTML should be interspersed with anchors like this: `<a name="xyz"></a>` where xyz is the index heading for the following text. There should be one such anchor before each entry and an extra anchor at the end of the text; everything before the first anchor is counted as the “header” and everything after the last as the “footer”. If these are empty, a default “mobile friendly” HTML header and footer specifying UTF-8 encoding will be added. Anchors may be linked from other entries; these links are changed as necessary.

By default, the input HTML is read from standard input, and the output is written to the current directory as a set of HTML files, each limited to 64 Kb so as not to overload a mobile browser. Opening any of these HTML files should display a textbox that lets you type the first few letters of the word you wish to look up; the browser will then jump to whatever heading is alphabetically nearest to the typed-in text. (By default, only alphabetical letters are significant and diacritical marks are stripped from the index, but this can be changed.)

As an example, `c2h.py` is a simple CEDICT to HTML script can produce offline HTML files for CEDICT.

Users of the Android platform might also wish to make an APK from the HTML. `ohi-addCopy.sh` is a shell script to add Copy buttons to any hanzi strings to the HTML files, which should work when it’s put into an APK using [html2apk](http://ssb22.user.srcf.net/gradint/html2apk.html) (but they won’t work in standalone HTML).

Online version
--------------

Although the offline files will also work online, in bandwidth-limited situations you might be better using the `ohi_online.py` lookup CGI which works from the same input as ohi.py (see start of file for configuration, and there are options for running it as a [Web Adjuster](http://ssb22.user.srcf.net/adjuster/) extension if desired). This version can also take multiple adjacent anchors, giving alternate labels to the same fragment; there should not be any whitespace between adjacent anchors.

Print version
-------------
The script `ohi_latex.py` works from the same input as `ohi.py` and can be used to help make a printed reference. It includes a simple HTML to LaTeX converter with support for CJK (including Pinyin), Greek, Braille, IPA, Latin diacritics, miscellaneous symbols etc, and PDF features such as cross-referencing should work. Line breaks are automatically added between entries, unless their anchor names end with `*` in which case they are separated by semicolons for saving paper when adding large numbers of short “see” entries. If the input has no anchors then `ohi_latex` will just convert simple HTML/Unicode into LaTeX.

Copyright and Trademarks
------------------------

© Silas S. Brown, licensed under Apache 2.

* Android is a trademark of Google LLC.

* Apache is a registered trademark of The Apache Software Foundation.

* Javascript is a trademark of Oracle Corporation in the US.

* Python is a trademark of the Python Software Foundation.

* Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.

* Any other trademarks I mentioned without realising are trademarks of their respective holders.
