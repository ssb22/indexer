import pytest, os, re, zipfile, anemone

@pytest.fixture()
def wav():
    r = os.system("sox -n test.wav synth 3 sine 300-3300")
    assert not r, "Unable to generate test sound"
    yield "test.wav" ; os.remove("test.wav")

def test_audioOnly_daisy2(wav):
    anemone.anemone(wav,'test_daisy.zip',warnings_are_errors=True)
    ncc = zipfile.ZipFile("test_daisy.zip","r").open('ncc.html').read()
    os.remove("test_daisy.zip")
    assert b'>test<' in ncc
def test_audioOnly_daisy3(wav):
    anemone.anemone(wav,'test_daisy.zip',warnings_are_errors=True,daisy3=True)
    ncx = zipfile.ZipFile("test_daisy.zip","r").open('navigation.ncx').read()
    os.remove("test_daisy.zip")
    assert b'>test<' in ncx
def test_full_daisy3(wav):
    anemone.anemone(wav,'<h1 data-pid="T">heading</h1><p data-pid="U">para</p>','{"markers":[{"id":"T","time":"1"},{"id":"U","time":"2"}]}','test_daisy.zip',warnings_are_errors=True,daisy3=True)
    z = zipfile.ZipFile("test_daisy.zip","r")
    ncx = z.open('navigation.ncx').read()
    smil = z.open('0001.smil').read()
    del z ; os.remove("test_daisy.zip")
    assert b'<navLabel><text>heading</text><audio src="0001.mp3" clipBegin="0:00:00.000" clipEnd="0:00:02.000"/></navLabel>' in ncx
    assert re.search(b'<audio src="0001.mp3" clipBegin="0:00:02.000" clipEnd="0:00:03.0[0-9][0-9]" id="aud1.1" />',smil) # small length change on recode is OK
def test_json_transcript(wav):
    anemone.anemone(wav,{"version":"1.0.0","segments":[{"speaker":"voice 1","startTime":0,"endTime":1.5,"body":"Testing 123"},{"speaker":"voice 2","startTime":1.5,"endTime":3,"body":"another voice"}]},'test_daisy.zip',warnings_are_errors=True,daisy3=True,chapter_titles="Script 1")
    z = zipfile.ZipFile("test_daisy.zip","r")
    xml = z.open('0001.xml').read()
    smil = z.open('0001.smil').read()
    del z ; os.remove("test_daisy.zip")
    assert re.search(b'<audio src="0001.mp3" clipBegin="0:00:01.500" clipEnd="0:00:03.0[0-9][0-9]" id="aud1.2" />',smil) # 1.0 = h1
    assert b'<level1><h1 id="p1">Script 1</h1>' in xml
def test_images(wav):
    anemone.anemone(wav,'<h1 data-pid="T">heading</h1><img data-zoom="http://ssb22.user.srcf.net/dorset.jpg"><p data-pid="U">para</p>','{"markers":[{"id":"T","time":"1"},{"id":"U","time":"2"}]}','test_daisy.zip',warnings_are_errors=True,daisy3=True)
    xml = zipfile.ZipFile("test_daisy.zip","r").open('0001.xml').read()
    os.remove("test_daisy.zip")
    assert b'</h1><p><imggroup><img src="1.jpg" id="i0" /></imggroup></p>' in xml
def test_verse_numbering(wav):
    anemone.anemone(wav,'<p data-pid="A">47 one</p><p data-pid="B">2 two</p><p data-pid="C">3 three</p>','{"markers":[{"id":"A","time":"0"},{"id":"B","time":"1"},{"id":"C","time":"2"}]}','test_daisy.zip',warnings_are_errors=True,ignore_chapter_skips=True,daisy3=True)
    z = zipfile.ZipFile("test_daisy.zip","r")
    xml = z.open('0001.xml').read()
    ncx = z.open('navigation.ncx').read()
    del z ; os.remove("test_daisy.zip")
    assert b'<level1><h1 id="p1">47</h1>' in xml
    assert b'<p id="p2">one</p>' in xml
    assert b'<navLabel><text>47:2</text><audio src="0001.mp3" clipBegin="0:00:01.000" clipEnd="0:00:02.000"/></navLabel>' in ncx
def test_errors(wav):
    with pytest.raises(anemone.AnemoneError) as e: anemone.anemone(wav,'<p data-pid="A">47 one</p><p data-pid="B">2 two</p><p data-pid="C">3 three</p>','{"markers":[{"id":"A","time":"0"},{"id":"B","time":"1"},{"id":"C","time":"2"}]}','test_daisy.zip',chapter_titles="Chapter 74",warnings_are_errors=True,ignore_chapter_skips=True,daisy3=True)
    assert "Title for chapter 47 is 'Chapter 74' which does not contain the expected '47' (extracted from '47 one')" in str(e.value)
    assert not os.path.exists('test_daisy.zip')
def test_warning_callback():
    warnings = []
    def wc(s): warnings.append(s)
    anemone.anemone("<p data-pid=A>one</p><p data-pid=B>two</p>","test_daisy.zip",warning_callback=wc,chapter_titles="Chapter 74")
    htm = zipfile.ZipFile("test_daisy.zip","r").open('0001.htm').read()
    os.remove("test_daisy.zip")
    assert warnings==["Title for chapter 1 is 'Chapter 74' which does not contain the expected '1' (from automatic numbering as nothing was extracted from 'one')"]
    assert b'<h1 id="p1">Chapter 74</h1>' in htm
def test_progress_callback(): # and text only
    progress = []
    def pc(s): progress.append(s)
    anemone.anemone("<p data-pid=A>one</p><p data-pid=B>two</p>","test_daisy.zip",progress_callback=pc)
    os.remove("test_daisy.zip")
    assert progress==[7,15,85,100]
def test_info_callback():
    info = []
    def ic(s): info.append(s)
    anemone.anemone("<p data-pid=A>one</p><p data-pid=B>two</p>","test_daisy.zip",info_callback=ic)
    os.remove("test_daisy.zip")
    assert info==["Wrote test_daisy.zip"]
