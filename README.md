# indexer
This repository contains various indexing utilities from https://ssb22.user.srcf.net/indexer/
(also [mirrored on GitLab Pages](https://ssb22.gitlab.io/indexer/) just in case)
the main ones being:
1. Offline HTML Indexer
2. Online version of OHI
3. LaTeX book and dictionary builder (print OHI)
4. Anemone DAISY maker

Offline HTML Indexer
--------------------

This is a Python program (compatible with both Python 2 and Python 3), for creating large indices of HTML text which can be queried using simple Javascript that works on many mobile phone browsers without needing an Internet connection or a Web server. This is useful if you want to load a dictionary or other reference onto your phone (or computer) for use when connectivity is not available.

The input HTML should be interspersed with anchors like this: `<a name="xyz"></a>` where xyz is the index heading for the following text. There should be one such anchor before each entry and an extra anchor at the end of the text; everything before the first anchor is counted as the “header” and everything after the last as the “footer”. If these are empty, a default “mobile friendly” HTML header and footer specifying UTF-8 encoding will be added. Anchors may be linked from other entries; these links are changed as necessary.

By default, the input HTML is read from standard input, and the output is written to the current directory as a set of HTML files, each limited to 64 Kb so as not to overload a mobile browser. Opening any of these HTML files should display a textbox that lets you type the first few letters of the word you wish to look up; the browser will then jump to whatever heading is alphabetically nearest to the typed-in text. (By default, only alphabetical letters are significant and diacritical marks are stripped from the index, but this can be changed.)

As an example, `c2h.py` is a simple CEDICT to HTML script can produce offline HTML files for CEDICT.

Users of the Android platform might also wish to make an APK from the HTML. `ohi-addCopy.sh` is a shell script to add Copy buttons to any hanzi strings to the HTML files, which should work when it’s put into an APK using [html2apk](html2apk/) (but they won’t work in standalone HTML).

Online version
--------------

Although the offline files will also work online, in bandwidth-limited situations you might be better using the `ohi_online.py` lookup CGI which works from the same input as ohi.py (see start of file for configuration, and there are options for running it as a [Web Adjuster](https://ssb22.user.srcf.net/adjuster/) extension if desired). This version can also take multiple adjacent anchors, giving alternate labels to the same fragment; there should not be any whitespace between adjacent anchors.

Print version
-------------
The script `ohi_latex.py` works from the same input as `ohi.py` and can be used to help make a printed reference. It includes a simple HTML to LaTeX converter with support for CJK (including Pinyin), Greek, Braille, IPA, Latin diacritics, miscellaneous symbols etc, and PDF features such as cross-referencing should work. Line breaks are automatically added between entries, unless their anchor names end with `*` in which case they are separated by semicolons for saving paper when adding large numbers of short “see” entries. If the input has no anchors then `ohi_latex` will just convert simple HTML/Unicode into LaTeX.

Anemone DAISY maker
-------------------
from https://ssb22.user.srcf.net/indexer/anemone.html
(also [mirrored on GitLab Pages](https://ssb22.gitlab.io/indexer/anemone.html) just in case, plus you can access Anemone via `pip install anemone-daisy-maker` or `pipx run anemone-daisy-maker`)

`anemone.py` is a Python 3 script to put together a DAISY digital talking book, from HTML text and MP3 audio recordings.  It can generate the time index data via Whisper's speech recognition in some languages (this process is resilient to transcription errors and reader deviations as it checks only for paragraph-change times), or you can supply timestamps yourself in separate JSON files.  Anemone produces DAISY 2.02 files by default, or DAISY 3 (i.e. ANSI/NISO Z39.86) if an option is set.  It can produce four different types of digital talking book:

1. Full audio with basic Navigation Control Centre only: this requires a list of MP3 or WAV files for the audio, one per section, and the title of each section can be placed either in a separate text file or in the filename of the audio file.

2. Full audio with full text: this requires MP3 or WAV files for the audio, corresponding XHTML files for the text, and (unless you're using speech recognition) corresponding JSON files for the timing synchronisation.  Each JSON file is expected to contain a list called `"markers"` whose items contain `"id"` (or `"paragraphId"` or anything else ending `id`) and `"time"` (or `"startTime"` or anything else ending `time`), which can be in seconds, minutes:seconds or hours:minutes:seconds (fractions of a second are allowed in each case).  The IDs in these JSON files should have corresponding attributes in the XHTML, by default `data-pid` but this can be changed with an option.

3. Text with no audio: this requires just XHTML files, and extracts all text with a specified attribute (`data-pid` by default)

4. Text with some audio: this is a combination of the above two methods, and you’ll need to specify `skip` in the JSON file list for the chapters that do not yet have recorded audio

All files are placed on the command line, or in parameters if you’re using Anemone as a module, and Anemone assumes the correspondences are ordered.  So for example if MP3, HTML and JSON files are given, Anemone assumes the first-listed MP3 file corresponds with the first-listed HTML file and the first-listed JSON file, and so on for the second, third, etc.  With most sensible file naming schemes, you should be able to use shell wildcards like `*` when passing the files to Anemone.  You can specify a JSON dictionary instead of the name of a JSON file, and/or an HTML string instead of the name of an HTML file, either when calling `anemone()` as a library or on the command line with careful quoting.

You may also set the name of an output file ending `zip`; the suffix `_daisy.zip` is common.  The title, publisher, language etc of the book should be set via options (see below).

The daisy anemone is a sea creature on the rocky Western shores of Britain and Ireland; the Dorset Wildlife Trust says it’s “usually found in deep pools or hiding in holes or crevices, or buried in the sediment with only tentacles displayed”.  Similarly this script has no interactive user interface; it hides away on the command line, or as a library module for your Python program.

### Anemone options
If calling the program as a library, call the `anemone()` function with files as detailed above and options as keyword arguments (removing the leading `--` and converting other `-` to `_` throughout); if using the command line (or calling `anemone()` with no arguments, which reads the system command line) use options as below:
* `--lang`: the ISO 639 language code of the publication (defaults to en for English)
* `--title`: the title of the publication
* `--url`: the URL or ISBN of the publication
* `--creator`: the creator name, if known
* `--publisher`: the publisher name, if known
* `--reader`: the name of the reader who voiced the recordings, if known
* `--date`: the publication date as YYYY-MM-DD, default is current date
* `--auto-markers-model`: instead of accepting JSON timing markers, guess them using speech recognition with the `whisper-cli` command and this voice model (currently only at paragraph level, and every paragraph matching `marker-attribute` below will be included)
* `--marker-attribute`: the attribute used in the HTML to indicate a segment number corresponding to a JSON time marker entry, default is `data-pid`
* `--marker-attribute-prefix`: When extracting all text for chapters that don’t have timings, ignore any marker attributes whose values don’t start with the given prefix
* `--page-attribute`: the attribute used in the HTML to indicate a page number, default is `data-no`
* `--image-attribute`: the attribute used in the HTML to indicate an absolute image URL to be included in the DAISY file, default is `data-zoom`
* `--line-breaking-classes`: comma-separated list of classes used in HTML SPAN tags to substitute for line and paragraph breaks
* `--refresh`: if images etc have already been fetched from URLs, ask the server if they should be fetched again (use `If-Modified-Since`)
* `--cache`: path name for the URL-fetching cache (default `cache` in the current directory; set to empty string if you don’t want to save anything); when using anemone as a module, you can instead pass in a `requests_cache` session object if you want that to do it instead
* `--reload`: if images etc have already been fetched from URLs, fetch them again without `If-Modified-Since`
* `--delay`: minimum number of seconds between URL fetches (default none)
* `--retries`: number of times to retry URL fetches on timeouts and unhandled exceptions (default no retries)
* `--user-agent`: User-Agent string to send for URL fetches
* `--daisy3`: Use the Daisy 3 format (ANSI/NISO Z39.86) instead of the Daisy 2.02 format. This may require more modern reader software, and Anemone does not yet support Daisy 3 only features like tables.
* `--mp3-recode`: re-code the MP3 files to ensure they are constant bitrate and more likely to work with the more limited DAISY-reading programs like FSReader 3 (this requires LAME or miniaudio/lameenc)
* `--max-threads`: Maximum number of threads to use for MP3 re-coding. If set to 0 (default), the number of CPU cores is detected and used, and, if called as a module, multiple threads calling `anemone()` share the same pool of MP3 re-coding threads. This is usually most efficient. If set to anything other than 0, a local pool of threads is used for MP3 re-coding (instead of sharing the pool with any other `anemone()` instances) and it is limited to the number of threads you specify. If calling anemone as a module and you want to limit the pool size but still have a shared pool, then don’t set this but instead call `set_max_shared_workers()`.
* `--allow-jumps`: Allow jumps in heading levels e.g. h1 to h3 if the input HTML does it. This seems OK on modern readers but might cause older reading devices to give an error. Without this option, headings are promoted where necessary to ensure only incremental depth increase.
* `--merge-books`: Combine multiple books into one, for saving media on CD-based DAISY players that cannot handle more than one book. The format of this option is `book1/N1,book2/N2,`etc where `book1` is the book title and `N1` is the number of MP3 files to group into it (or if passing the option into the anemone module, you may use a list of tuples). All headings are pushed down one level and book name headings are added at top level.
* `--chapter-titles`: Comma-separated list of titles to use for chapters that don’t have titles, e.g. ‘Chapter N’ in the language of the book (this can help for search-based navigation). If passing this option into the anemone module, you may use a list instead of a comma-separated string, which might be useful if there are commas in some chapter titles. Use blank titles for chapters that already have them in the markup.
* `--toc-titles`: Comma-separated list of titles to use for the table of contents. This can be set if you need more abbreviated versions of the chapter titles in the table of contents, while leaving the full versions in the chapters themselves. Again you may use a list instead of a comma-separated string if using the module. Any titles missing or blank in this list will be taken from the full chapter titles instead.
* `--chapter-heading-level`: Heading level to use for chapters that don’t have titles
* `--warnings-are-errors`: Treat warnings as errors
* `--ignore-chapter-skips`: Don’t emit warnings or errors about chapter numbers being skipped
* `--dry-run`: Don’t actually output DAISY, just check the input and parameters
* `--version`: Just print version number and exit (takes effect only if called from the command line)

If using the module, you can additionally set the options `warning_callback`, `info_callback` and/or `progress_callback`.  These are Python callables to log an in-progress conversion (useful for multi-threaded UIs).  `warning_callback` and `info_callback` each take a string, and `progress_callback` takes an integer percentage.  If `warning_callback` or `info_callback` is set, the corresponding information is not written to standard error.

### Behaviour of DAISY readers in 2024

* Dolphin EasyReader 10 (iOS, Android and Chromebook): is able to open the ZIP and play the audio while highlighting the paragraphs in a ‘full audio plus full text’ book, both Daisy 2 and Daisy 3.  In very large books (over 1&nbsp;GB), loading and navigation becomes unreliable.  An Internet connection is required the first time a book is opened.

* EDRLab Thorium Reader (Windows, Mac and GNU/Linux): is able to open the ZIP and play the audio while highlighting the paragraphs in a ‘full audio plus full text’ book, both Daisy 2 and Daisy 3.  Still works in very large books but loading is slow.  Version 2.4 might be more responsive than version 3.0.

* Dolphin EasyReader 10 (Windows): is able to play audio while highlighting paragraphs in both Daisy 2 and Daisy 3, but ZIP needs to be unpacked separately and NCC or OPF file opened.  Very large (1 GB+) books can cause the program to crash when Search is used.

* JAWS FSReader 3 (Windows): is able to play audio while highlighting paragraphs in both Daisy 2 and Daisy 3, but ZIP needs to be unpacked separately and NCC or OPF file opened; may work better without JAWS running; synchronisation with audio seems to require `--mp3-recode`; images are not scaled to fit; tested working with a Braille display and audio speed changes; not tested with very large books (1GB+)

* HumanWare Brailliant: does not show text if there is audio (hopefully it can still be used for navigation); ZIP needs to be unpacked; tested both Daisy 2 and Daisy 3 (which the device calls "Niso" format)

does not show text if there is audio (hopefully it can still be used for navigation) in both Daisy 2 and Daisy 3

* Pronto Notetaker: ZIP needs to be unpacked to a “Daisy” folder on SD or USB, and the device just plays the audio; tested only with Daisy 2

* US Library of Congress NLS Player: unpack the ZIP onto a blank USB stick of capacity 4 GB or less—plays; navigation works if you use `--mp3-recode`; tested only with Daisy 2 but the documentation says Daisy 3 should work

* HumanWare Victor Reader Stream: ZIP needs to be unpacked, either to the top level of a USB device, or into a subfolder of a `$VRDTB` folder on the SD card (different books will be listed alphabetically).  If it’s unpacked at the top level of the SD card, the device can still play the MP3s and allow track or time based navigation but not section navigation, so you should use either the folder structure of the SD card or else a USB device.  If correctly set up then audio plays and device can navigate by section.  Tested with both Daisy 2 and Daisy 3.

* HumanWare Victor Reader Stratus4: When unpacking the ZIP to CD, please ensure that your CD writer does *not* create a *folder* with the same name as the ZIP: this default behaviour of Microsoft Windows does *not* result in a valid Daisy CD.  The individual *files* of the ZIP need to be written to the *top level* of the CD, *not* to a folder on it.  Otherwise, the Stratus4 will not recognise the CD as a Daisy CD and will just play the MP3s, resulting in only time and track based navigation being available.  Tested with both Daisy 2 and Daisy 3.

* HIMS QBraille XL: can display the text (after opening with Space and Enter); does not play audio; ZIP needs to be unpacked; tested only with Daisy 2

* Daisy Consortium Simply Reading 3 (app available for Android 7 and below): is able to open the ZIP and play the audio while highlighting the paragraphs in a ‘full audio plus full text’ book, although fonts for some languages might be missing on earlier Android devices

* DAISY Pipeline (2023): Please do not use this to convert an Anemone-produced Daisy 2 book to Daisy 3.  The resulting Daisy 3 is not likely to play on anything.  If Daisy 3 is required, use Anemone’s `--daisy3` option to produce it directly.

Copyright and Trademarks
------------------------

© Silas S. Brown, licensed under Apache 2.
Android is a trademark of Google LLC.
Apache is a registered trademark of The Apache Software Foundation, which from February to July 2023 acknowledged the Chiricahua Apache, the Choctaw Apache, the Fort Sill Apache, the Jicarilla Apache, the Mescalero Apache, the Lipan Apache, the Apache Tribe of Oklahoma, the Plains Apache, the San Carlos Apache, the Tonto Apache, the White Mountain Apache, the Yavapai Apache and the Apache Alliance.
Javascript is a trademark of Oracle Corporation in the US.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Mac is a trademark of Apple Inc.
Microsoft is a registered trademark of Microsoft Corp.
MP3 is a trademark that was registered in Europe to Hypermedia GmbH Webcasting but I was unable to confirm its current holder.
Python is a trademark of the Python Software Foundation.
Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.
Windows is a registered trademark of Microsoft Corp.
Any other trademarks I mentioned without realising are trademarks of their respective holders.
