 indexer
Offline HTML Indexer etc from http://ssb22.user.srcf.net/indexer/
(also mirrored at http://ssb22.gitlab.io/indexer/ just in case)

This is a Python program (compatible with both Python 2 and Python 3), for creating large indices of HTML text which can be queried using simple Javascript that works on many mobile phone browsers without needing an Internet connection or a Web server. This is useful if you want to load a dictionary or other reference onto your phone (or computer) for use when connectivity is not available.

The input HTML should be interspersed with anchors like this: `<a name="xyz"></a>` where xyz is the index heading for the following text. There should be one such anchor before each entry and an extra anchor at the end of the text; everything before the first anchor is counted as the “header” and everything after the last as the “footer”. If these are empty, a default “mobile friendly” HTML header and footer specifying UTF-8 encoding will be added. Anchors may be linked from other entries; these links are changed as necessary.

By default, the input HTML is read from standard input, and the output is written to the current directory as a set of HTML files, each limited to 64 Kb so as not to overload a mobile browser. Opening any of these HTML files should display a textbox that lets you type the first few letters of the word you wish to look up; the browser will then jump to whatever heading is alphabetically nearest to the typed-in text. (By default, only alphabetical letters are significant and diacritical marks are stripped from the index, but this can be changed.)

As an example, `c2h.py` is a simple CEDICT to HTML script can produce offline HTML files for CEDICT.

Users of the Android platform might also wish to make an APK from the HTML. `ohi-addCopy.sh` is a shell script to add Copy buttons to any hanzi strings to the HTML files, which should work when it’s put into an APK using [html2apk](http://ssb22.user.srcf.net/indexer/html2apk.html) (but they won’t work in standalone HTML).

Online version
--------------

Although the offline files will also work online, in bandwidth-limited situations you might be better using the `ohi_online.py` lookup CGI which works from the same input as ohi.py (see start of file for configuration, and there are options for running it as a [Web Adjuster](http://ssb22.user.srcf.net/adjuster/) extension if desired). This version can also take multiple adjacent anchors, giving alternate labels to the same fragment; there should not be any whitespace between adjacent anchors.

Print version
-------------
The script `ohi_latex.py` works from the same input as `ohi.py` and can be used to help make a printed reference. It includes a simple HTML to LaTeX converter with support for CJK (including Pinyin), Greek, Braille, IPA, Latin diacritics, miscellaneous symbols etc, and PDF features such as cross-referencing should work. Line breaks are automatically added between entries, unless their anchor names end with `*` in which case they are separated by semicolons for saving paper when adding large numbers of short “see” entries. If the input has no anchors then `ohi_latex` will just convert simple HTML/Unicode into LaTeX.

Anemone DAISY maker
-------------------
from http://ssb22.user.srcf.net/indexer/anemone.html
(also mirrored at http://ssb22.gitlab.io/indexer/anemone.html just in case)

`anemone.py` is a Python 3 script to put together a DAISY file from HTML text, MP3 audio recordings and time index data.  It produces DAISY 2.02 files.  It currently can produce one of two different types of digital talking book:

1. Full audio with basic Navigation Control Centre only: this requires a list of MP3 files for the audio, one MP3 per section, and the title of each section can be placed either in a separate text file or in the filename of the MP3 file.

2. Full audio with full text: this requires MP3 files for the audio, corresponding XHTML files for the text, and corresponding JSON files for the timing synchronisation.  Each JSON file is expected to contain a list called `"markers"` whose items contain `"id"` (or `"paragraphId"` or anything else ending id) and `"time"` (or `"startTime"` or anything else ending time), which can be in seconds, minutes:seconds or hours:minutes:seconds.  The IDs in these JSON files should have corresponding attributes in the XHTML, by default data-pid but this can be changed with a command-line option.

All files are placed on the command line, and Anemone assumes the correspondences are ordered.  So for example if MP3, HTML and JSON files are given, Anemone assumes the first-listed MP3 file corresponds with the first-listed HTML file and the first-listed JSON file, and so on for the second, third, etc.  With most sensible file naming schemes, you should be able to use shell wildcards like `*` when passing the files to Anemone.  You may also set the name of an output file ending `zip`; the suffix `_daisy.zip` is common.  The title, publisher, language etc of the book should be set via command-line options: run the program with `--help` to see all.

The daisy anemone is a sea creature on the rocky Western shores of Britain and Ireland; the Dorset Wildlife Trust says it's "usually found in deep pools or hiding in holes or crevices, or buried in the sediment with only tentacles displayed".  Similarly this script has no interactive user interface; it hides away on the command line.

### Behaviour of DAISY readers in 2024

* Dolphin EasyReader 10 (iOS, Android and Chromebook): is able to open the ZIP and play the audio while highlighting the paragraphs in a ‘full audio plus full text’ book

* Dolphin EasyReader 10 (Windows): ZIP needs to be unpacked separately and NCC file opened

* JAWS FSReader 3 (Windows): ZIP needs to be unpacked separately and NCC file opened; may work better without JAWS running; synchronisation with audio seems to require --mp3-recode

* HumanWare Brailliant: does not show text if there is audio (hopefully it can still be used for navigation)

* Pronto Notetaker: ZIP needs to be unpacked to a “Daisy” folder on SD or USB, and the device just plays the audio

* US Library of Congress NLS Player: unpack the ZIP onto a blank USB stick of capacity 4 GB or less—plays; navigation works if you use --mp3-recode

* HumanWare Victor Reader Stream: ZIP needs to be unpacked into "Other Books"; audio plays, device can navigate by section

* HIMS QBraille XL: can display the text (after opening with Space and Enter); does not play audio

Copyright and Trademarks
------------------------

© Silas S. Brown, licensed under Apache 2.

* Android is a trademark of Google LLC.

* Apache is a registered trademark of The Apache Software Foundation.

* Javascript is a trademark of Oracle Corporation in the US.

* MP3 is a trademark that was registered in Europe to Hypermedia GmbH Webcasting but I was unable to confirm its current holder.

* Python is a trademark of the Python Software Foundation.

* Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.

* Windows is a registered trademark of Microsoft Corp.

* Any other trademarks I mentioned without realising are trademarks of their respective holders.
