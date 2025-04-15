"""OPDS XML, tested in EDRLab Thorium Reader 2.4 and 3.0"""

def wrap_opds(entries = [],
              output_url="https://example.org/opds.xml",
              catalogue_title="OPDS Catalogue"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <id>{url2urn(output_url)}</id>
  <link rel="self" href="{output_url}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
  <link rel="start" href="{output_url}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
  <link rel="up" href="{output_url}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
  <title>{catalogue_title}</title>
  <updated>{isotime(time.time())}</updated>
  {chr(10).join(entries)}
</feed>
"""

def opds_entry(title,
               jpeg_url="https://example.org/image.jpg",
               daisy_url="https://example.org/book_daisy.zip",
               lang_iso="en",publisher="",author="",
               created=0, updated=0):
    return f"""  <entry>
    <title>{title}</title>
    <updated>{isotime(updated)}</updated>
    <author><name>{author}</name></author>
    <dc:language>{lang_iso}</dc:language>
    <dc:publisher>{publisher}</dc:publisher>
    <dc:issued>{isotime(created)}</dc:issued>
    <link rel="http://opds-spec.org/image" href="{jpeg_url}" type="image/jpeg"/>
    <link rel="http://opds-spec.org/acquisition" href="{daisy_url}" type="application/zip"/>
  </entry>"""

from uuid import UUID
from hashlib import sha256
url2urn = lambda u:UUID(sha256(bytes(u,"utf-8")).hexdigest()[:32]).urn
import datetime, time
utc = datetime.timezone(datetime.timedelta())
isotime = lambda t:datetime.datetime.fromtimestamp(t,utc).isoformat(timespec='seconds')
