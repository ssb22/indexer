"""Python 3 utilities for reading literature with
macOS voices, using different voices for different
characters in the dialogue

v0.1 (c) 2024 Silas S. Brown.  License: Apache 2
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Where to find history:
# on GitHub at https://github.com/ssb22/indexer
# and on GitLab at https://gitlab.com/ssb22/indexer
# and on BitBucket https://bitbucket.org/ssb22/indexer
# and at https://gitlab.developers.cam.ac.uk/ssb22/indexer
# and in China: https://gitee.com/ssb22/indexer

import tempfile, re, os, sys

def getAIFF(voiceParams,text):
    """Clean up text, speak it using given voice
    and return the AIFF filename.
    Interprets <em> tags around single words,
    removes other tags, and replaces curved
    apostrophes with straight ones.
    Retries in event of say failure."""

    text = text.strip()
    text = re.sub("<em>([A-Za-z0-9’]+)</em>",r"[[slnc 100]]\1[[slnc 100]]",text) # 0.1sec silence is about the only emphasis that works (Mac emphasis tags not currently working on macOS)
    text = re.sub("<[^<]*>","",text) # rm tags
    text = re.sub("(?i)(?<=[a-z])’(?=[a-z])","'",text) # Mac voices need straight apostrophes
    
    f = tempnam("aiff") ; f0 = None
    while True:
        if "[[" in voiceParams:
            # If voiceParams includes a pitch
            # override or something, Mac voices
            # cannot read text from file and also
            # pitch override from command line,
            # and attempting to do so can result
            # in no output at all.  Therefore we
            # have to put the text on the command
            # line.
            assert "'" in voiceParams or '"' in voiceParams, f"please ensure these parameters are properly quoted for the shell: '{voiceParams}'"
            assert not '"' in text, f"please remove straight double quotes from text '{text}'"
            r=os.system(f'say -o {f} {voiceParams} "{text}"')
        else:
            if not f0:
                f0 = tempnam("txt")
                open(f0,'w').write(text)
            r=os.system(f'say {voiceParams} -o {f} -f {f0}')
        if r: print ("Retrying after failed say") # in case the voices got stuck and you had to do "killall say" e.g. after a laptop suspend
        else: break
    if f0: os.remove(f0)
    return f

def mixVoices(voiceParamList,text):
    """Synthesises text using one or more voice
    parameters simultaneously, for use when more
    than one character is speaking together; drops
    through to single voice if there's just one.
    Requires a sox binary in the PATH if voices
    need to be mixed."""
    aiffs = [getAIFF(p,text)
             for p in voiceParamList]
    if len(aiffs) > 1:
        a2 = tempnam("aiff")
        os.system(f'sox -m {" ".join(aiffs)} {a2}') # TODO: stereo positions? (but final output is currently mono) ; TODO: may need a small volume boost, especially if 3 voices mixed, but depends on the voices (mixing 3 identical copies seems to get the same)
        for a in aiffs: os.remove(a)
        aiffs = [a2]
    return aiffs[0]

def voiceParamsAndStrings(paragraph, voiceMap):
    """Splits a narrative paragraph into different
    voices, by reading it as follows:
    
    voiceName**paragraph = whole paragraph is read
    in the character voiceName
    
    voiceName1/voiceName2/...**text1/text2/...
    = use voiceName1 to read text1, voiceName2 to
    read text2, and so on; if more texts than
    voices are supplied, the voice pattern repeats
    (might be useful for alternating languages)
    
    voiceName*paragraph = voiceName reads just the
    parts inside curved double quotes, rest is
    read by narrator
    
    voice1,voice2*paragraph = voice1 reads the
    first set of double quotes, voice2 reads all
    subsequent sets of double quotes, and narrator
    reads the rest.  (Similarly for 3+ voices.)
    
    Additionally, any voice in the list can be
    made up of more than one voice to mix together
    by using +
    
    No * = use narrator for whole paragraph.
    
    voiceMap maps voice names to parameters, and
    must include a "narrator" entry, e.g.:
    voiceMap={"narrator":"-v 'Daniel (Enhanced)'"}
    To install more voices, try System Settings /
    Accessibility / Spoken Content / System voice
    / Manage voices (as of macOS 14).  You can
    also change pitch / speed / etc of some voices
    using e.g. "-r 80 '[[pbas 40]]'" (doesn't work
    well with all voices though).
    
    Return value is the list of (paramsList, text)
    for each part of the paragraph.
    
    Any sentence boundary (assumed to be
    represented as 2 spaces) is preserved, in case
    the caller needs to track where sentences
    change for transcript timings etc."""

    r = []
    if '**' in paragraph:
        voice,text = paragraph.split('**')
        assert text, "voice with blank text"
        if '/' in voice:
            tl = text.split('/')
            vl = voice.split('/')*len(tl)
            for v,t in zip(vl,tl): r.append(([voiceMap[vv] for vv in v.split('+')],t))
        else: r.append(([voiceMap[v] for v in voice.split('+')],text))
    elif '*' in paragraph:
        voiceL,text = paragraph.split('*')
        voiceL = voiceL.split(',')
        curVoice = ""
        while text.strip():
            if voiceL:
                curVoice = voiceL[0]
                voiceL = voiceL[1:]
            if not '“' in text:
                r.append(([voiceMap["narrator"]],text))
                text = "" ; continue
            beforeQuote,text = text.split('“',1)
            if re.search("[^ -/:-?]",beforeQuote): r.append(([voiceMap["narrator"]],beforeQuote))
            if '”' in text: quotedPart,text = text.split('”',1)
            else: quotedPart,text = text,"" # quote to be continued next paragraph
            if text.startswith("  "): quotedPart,text = quotedPart+"  ",text[2:] # otherwise the 2-space sentence boundary will get removed in next loop iteration's beforeQuote.strip(), and we want the caller to get it
            r.append(([voiceMap[v] for v in curVoice.split('+')],quotedPart))
        if text=="  ": r[-1]=(r[-1][0],r[-1][1]+"  ") # keep sentence break after, as above
    else:r.append(([voiceMap["narrator"]],paragraph)) # all narrator
    return r

def synth_chapter(txt,get_sentence_timings=False,
                  no_paraBreak_regex_list=[]):
    """Synthesises all the paragraphs one per line
    returning a list suitable for catAndDelete.
    Omits paragraph-break delays before any
    paragraph that contains a regular expression
    from no_paraBreak_regex_list (use for example
    to specify text indicating a speaker was
    interrupted so the change can be more hasty).
    Paragraphs ending .wav are assumed to be
    filenames to be included as-is.  If
    get_sentence_timings is True, we yield None
    after every sentence."""
    needParagraphBreak = False
    numParas = len(txt.split('\n'))
    for paraNo,para in enumerate(txt.split('\n')):
        sys.stderr.write(f"\r synth {paraNo}/{numParas}"), sys.stderr.flush()
        if para.endswith(".wav"): yield para
        elif not para: continue
        elif needParagraphBreak and not any(re.search(r,para) for r in no_paraBreak_regex_list):
            if '**' in para: para=para.replace('**','**[[slnc 300]]',1)
            elif '*' in para: para=para.replace('*','*[[slnc 300]]',1)
            else: para='[[slnc 300]]'+para
        needParagraphBreak = True
        if get_sentence_timings: para = para.rstrip() + "  " # ensure ends sentence
        for voices,text in voiceParamsAndStrings(para,voiceMap):
            if get_sentence_timings:
              while "  " in text:
                text0,text = text.split("  ",1)
                if text0: yield mixVoices(voices,text0)
                yield mixVoices([""],"[[slnc 300]]") # end-of-sentence pause (0.3 -> 0.5, TODO: would it be faster just to generate silence with sox)
                yield None # time marker
            if text.strip():
                yield mixVoices(voices,text)
    yield mixVoices([""],"[[slnc 1700]]") # give them a chance to stop before starting next chapter in a podcast browser (1.7 -> 1.9)
    sys.stderr.write("\n")

def catAndDelete(output, iterable):
    """Uses sox to concatenate a collection of
    AIFF or WAV files from iterable, saving the
    result to {output}.wav.  If all input is AIFF
    then mono is assumed, otherwise we standardise
    on stereo (for when music is included).
    Any AIFF files in the input are deleted, but
    WAV files are not deleted.
    
    If iterable includes any 'None' values, this
    is taken to mean that a timestamp is required
    at this point in the audio.  The function
    returns a list of collected timestamps if any.
    """
    l = list(iterable)
    if not(all(i.endswith(".aiff") for i in l if i)):
        # not all is aiff: standardise on stereo
        for i in l:
            if i and i.endswith(".aiff"): os.system(f"sox {i} -c 2 -r 44100 {i.replace('.aiff','-2.aiff')} && mv {i.replace('.aiff','-2.aiff')} {i}")
    toCat = [] ; catted = [] ; cumTime = 0
    timestamps = []
    def flushCat():
        if toCat:
            while len(toCat) > 50: # as below
                cmd(f"sox {' '.join(toCat[:50])} toCat{len(toCat)}.aiff")
                delAiff(toCat[:50])
                n = f"toCat{len(toCat)}.aiff"
                del toCat[:50]
                toCat.insert(0,n)
            cmd(f"sox {' '.join(toCat)} out{len(catted)}.aiff")
            catted.append(f"out{len(catted)}.aiff")
            del toCat[:]
    for i in l:
        if i: toCat.append(i)
        else: # i==None: a timestamp
            flushCat()
            cumTime+=AIFF(catted[-1]).info.length
            timestamps.append(cumTime)
    flushCat() ; delAiff(l)
    while len(catted) > 50: # work around 'too many open files' sox error (TODO: is 50 too conservative?)
        cmd(f"sox {' '.join(catted[:50])} {len(catted)}.aiff")
        delAiff(catted[:50])
        catted = [f"{len(catted)}.aiff"]+catted[50:]
    cmd(f"sox {' '.join(catted)} {output}.wav")

class SentenceBreakCount:
    r"""Class of objects to be used in
    re.sub('  ',obj) to add numbered </span> and
    <span> around sentence breaks (the start and
    end will still need <span> and </span>), for
    use when preparing transcripts with sentence
    level timing, e.g. for Anemone DAISY Maker.
    To pass multiple paragraphs through this (if
    represented one per line without blank lines)
    first do .replace('\n','  </p><p>')
    then after the re.sub use cleanup_spans"""
    global_uid = 0
    def __init__(self,
                 pageNoChangeDict = {}):
        """If pageNoChangeDict is supplied, it is
        a map of (relative sentence number -> new
        page number) and Anemone-compatible new
        page markup is inserted when that break
        occurs.  Note that the first sentence
        *break* is 1, so the first *sentence* is
        0 and must be handled separately by the
        caller when it begins a new page number"""
        self.C = 0
        self.pageNoChangeDict = pageNoChangeDict
    def __call__(self,*args):
        SentenceBreakCount.global_uid += 1
        self.C += 1
        return f'</span>  <span {f"""data-no="{self.pageNoChangeDict[self.C]}" """ if self.C in self.pageNoChangeDict else ""}data-pid="SentenceBreak-{SentenceBreakCount.global_uid}">'

def cleanup_spans(chapterText):
    "Clean up <span> markup added by SentenceBreakCount etc"
    chapterText=re.sub(' *(<span[^>]*>)</p><p>',r'</p><p>\1',chapterText) # paragraph breaks go before their new spans, not at the start
    chapterText=re.sub('(?:<p>)?<span([^>]*>)<h([1-6])>([^<]*)</h[1-6]></span>(?:</p>)?',r'<h\2\1\3</h\2>',chapterText) # spans around headings: transfer the data to the heading, remove the span and also any paragraph that had been placed around this construct
    return chapterText

def markers_dict_from_timings(chapterText,
                              timings):
    """Takes chapterText returned by cleanup_spans
    and timings returned by catAndDelete, and uses
    them to make a markers dictionary suitable for
    passing to Anemone DAISY Maker"""
    return {"markers":
            [{"id":p,"time":t}
             for p,t in zip(
                     (m.group(1) for m in
                      re.finditer(
                          'data-pid="([^"]*)"',
                          chapterText)),
                     [0]+timings)]}

def markers_dict_from_previous_smil(
        chapterText,
        previousSmilFilename):
    """For incremental updates of DAISY 3 files:
    calculates markers from a .smil file from a
    previously-generated Anemone DAISY Maker zip,
    instead of needing to re-synthesise, in the
    case where this chapter has not changed but
    another has"""
    return {"markers":
            [{"id":p,"time":t}
             for p,t in zip(
                     (m.group(1) for m in
                      re.finditer(
                          'data-pid="([^"]*)"',
                          chapterText)),
                     re.findall('(?<=clipBegin=")[0-9:.]+(?=")',open(previousSmilFilename).read()))]} # (to add DAISY 2 support, will need clip-begin="npt=..." parsing instead)

def labelSentencesForTeX(paragraph):
    """Adds <tex-literal> markup for ohi_latex to
    track the page numbers of each sentence,
    assuming sentences are separated by '  '"""
    c = SLCount()
    return re.sub("[^ ].*?(?=  |$)",lambda m:(' '.join([m.group().split()[0]+c()]+m.group().split()[1:]) if m.group() else ""),paragraph) # don't put sentence label BEFORE the first word, because adding a label before the first word of a paragraph has been known to occasionally affect LaTeX's widows/orphans weighting, changing the pagination.  Put it at the end of the first word of the sentence instead.
class SLCount:
    "used by labelSentencesForTeX" # (but must be at global scope or its global_uid will get reset when labelSentencesForTeX is called)
    global_uid = 0
    def __call__(self):
        SLCount.global_uid += 1
        return r"<tex-literal>\label{SentenceLabel"+str(SLCount.global_uid)+r"}</tex-literal>"

def readSentenceLabelPageNosFromAux(aux_filename):
    """Reads the .aux file left after the
    ohi_latex run on labelSentencesForTeX output
    and returns a list of (page number, chapter
    name) for each sentence, so you can detect
    chapter changes and page changes, and create
    pageNoChangeDict dictionaries for
    SentenceBreakCount objects (you might need
    custom logic for headings etc)"""
    return [l[l.index("}{{")+3:].split('}{')[1:3] for l in open(aux_filename) if l.startswith(r'\newlabel{SentenceLabel')] # (if any chapters are not numbered, their chapter numbers will be incorrect here, so use chapter names)

def tempnam(extension):
    "Get a temporary filename with the given extension (adds dot before it)"
    return tempfile.NamedTemporaryFile(suffix="."+extension,delete=False).name

def delAiff(L):
    "Deletes any AIFF files (only) listed in L"
    for i in L:
        if i and i.endswith(".aiff"):
            try: os.remove(i)
            except: pass # probably already rm'd

def cmd(c):
    "Run a command via os.system checking success"
    if not os.system(c):
        raise Exception(f"Command failed: {c}")
