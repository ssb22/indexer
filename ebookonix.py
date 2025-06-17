"""
ebookonix v0.2
Convenience functions to generate ONIX XML for zero-cost e-books.
(Run from the command line to generate XML for a single book.)
Not yet tested with a library, but validated with onixcheck"""

import langcodes
import re, time

def onix_message(products,
                 sender="",name="",phone="",email=""):
   """Creates a complete ONIX For Books XML message.
   products is a list of return values of onix_product().
   Sender organisation, contact name, phone and email may
   be provided."""
   return _deBlank(f"""<?xml version="1.0" encoding="UTF-8"?>
<ONIXMessage release="3.1" xmlns="http://ns.editeur.org/onix/3.1/reference">
 <Header>
  <Sender>
    <SenderName>{sender}</SenderName>
    <ContactName>{name}</ContactName>
    {f'<TelephoneNumber>{phone}</TelephoneNumber>' if phone else ''}
    {f'<EmailAddress>{email}</EmailAddress>' if email else ''}
  </Sender>
  <MessageRepeat>1</MessageRepeat>
  <SentDateTime>{'%d%02d%02d' % time.localtime()[:3]}</SentDateTime>
 </Header>
{chr(10).join(products)}
</ONIXMessage>
""")

def onix_product(url,title,lang_iso="en",
                 date=2000, # year (4 digits), year-quarter (5 digits), year-month (6 digits) or year-month-day (8 digits)
                 idCode="",
                 idType="ISBN", # or ISSN, DOI etc (see below)
                 # and see https://ns.editeur.org/onix/en/5
                 # (if ISSN, we assume the issue is carried by the date)
                 deweyCode="",deweyTxt="",
                 publisher="",publisherWebsite=""):
    """Creates an ONIX XML fragment for a book product.
    We use ProductForm ED = digital download
    and UnpricedItemType 01 = free of charge.
    url is the EPUB URL, PDF URL, list of MP3 URLs, etc"""
    if type(url)==list: urls = url
    else: urls = [url]
    def ext(u): return u.rsplit('.',1)[1]
    if not all(ext(u)==ext(urls[0]) for u in urls): raise Exception("URL list (e.g. MP3) must all be same extension")
    if urls[0].lower().endswith("daisy.zip"): format="daisy"
    else: format = ext(urls[0])
    list175 = {"mp3":"A103","wav":"A104","aac":"A107","ogg":"A108",
               "daisy":"A210", # we assume DAISY 3 with audio + text, for others see https://ns.editeur.org/onix/en/175
               "epub":"E150", # but use E101 if we're not sure there's ALT text for the images etc
               "html":"E105","pdf":"E107","rtf":"E109","mp4":"D105",
               "txt":"E112","azw3":"E116","pdb":"E125","brf":"E146"}
    if idType.upper()[:4]=="ISBN": idTypeCode = '15' if len(re.sub('[^0-9X]','',idCode))==13 else '02' # ISBN-13 or ISBN-10
    elif idType.upper()=="DOI": idTypeCode = '06'
    elif idType.upper()[:4]=="ISSN": idTypeCode = '34'
    else: idTypeCode = '01' # proprietary, and idType specified
    return _deBlank(f""" <Product>
  <RecordReference>{idCode}-{lang_iso}-{date}-{format}</RecordReference>
  <NotificationType>03</NotificationType>
  <RecordSourceType>01</RecordSourceType>
  <RecordSourceName>{publisher}</RecordSourceName>
  <ProductIdentifier>
    <ProductIDType>{idTypeCode}</ProductIDType>
    {f'<IDTypeName>{idType}</IDTypeName>' if idTypeCode=='01' else ''}
    <IDValue>{ensureIssnIs13(idCode) if idTypeCode=='34' else idCode}</IDValue>
  </ProductIdentifier>
  <DescriptiveDetail>
    <ProductComposition>00</ProductComposition>
    <ProductForm>ED</ProductForm>
    <ProductFormDetail>{list175.get(format.lower(),"E100")}</ProductFormDetail>
    <TitleDetail>
      <TitleType>01</TitleType>
      <TitleElement>
        <TitleElementLevel>01</TitleElementLevel>
        <TitleText language="{langcodes.Language.get(lang_iso).to_alpha3()}">{title}</TitleText>
      </TitleElement>
    </TitleDetail>
    <NoEdition/>
    <Language>
      <LanguageRole>01</LanguageRole>
      <LanguageCode>{langcodes.Language.get(lang_iso).to_alpha3()}</LanguageCode>
    </Language>
    {f'''<Subject>
      <MainSubject/>
      <SubjectSchemeIdentifier>01</SubjectSchemeIdentifier>
      <SubjectCode>{deweyCode}</SubjectCode>
      <SubjectHeadingText>{deweyTxt}</SubjectHeadingText>
    </Subject>''' if deweyCode and deweyTxt else ''}
  </DescriptiveDetail>
  <PublishingDetail>
    <Publisher>
      <PublishingRole>01</PublishingRole>
      <PublisherName>{publisher}</PublisherName>
      {f'''<Website>
        <WebsiteRole>01</WebsiteRole>
        <WebsiteLink>{publisherWebsite}</WebsiteLink>
      </Website>''' if publisherWebsite else ''}
    </Publisher>
    <PublishingStatus>04</PublishingStatus>
    <PublishingDate>
      <PublishingDateRole>01</PublishingDateRole>
      <Date dateformat="{{4:'05',5:'03',6:'01',8:'00'}[len(str(date))]}">{str(date).replace("-","")}</Date>
    </PublishingDate>
    <CopyrightStatement>
      <CopyrightYear>{str(date)[:4]}</CopyrightYear>
      <CopyrightOwner>
        <CorporateName>{publisher}</CorporateName>
      </CopyrightOwner>
    </CopyrightStatement>
  </PublishingDetail>
  <ProductionDetail>
    <ProductionManifest>
      <BodyManifest>
{''.join(f'''
        <BodyResource>
          <ResourceFileLink>{u}</ResourceFileLink>
        </BodyResource>''' for u in urls)}
      </BodyManifest>
    </ProductionManifest>
  </ProductionDetail>
  <ProductSupply>
    <Market>
      <Territory>
        <RegionsIncluded>WORLD</RegionsIncluded>
      </Territory>
    </Market>
    <MarketPublishingDetail>
      <MarketPublishingStatus>04</MarketPublishingStatus>
    </MarketPublishingDetail>
    <SupplyDetail>
      <Supplier>
        <SupplierRole>01</SupplierRole>
        <SupplierName>{publisher}</SupplierName>
        {f'''<Website>
          <WebsiteRole>01</WebsiteRole>
          <WebsiteLink>{publisherWebsite}</WebsiteLink>
        </Website>''' if publisherWebsite else ''}
      </Supplier>
      <ProductAvailability>21</ProductAvailability>
      <UnpricedItemType>01</UnpricedItemType>
    </SupplyDetail>
  </ProductSupply>
 </Product>""")

def ensureIssnIs13(issn):
   "Ensures that an ISSN code is in ISSN-13 format as required by ONIX"
   issn = issn.replace("-","")
   if len(issn)==8:
      issn = "977"+issn[:7]
      return f"{issn}00{(10-(sum(int(c)*(3 if i%2 else 1) for i,c in enumerate(issn))%10))%10}"
   else: return issn

def _deBlank(s):
   "Remove blank lines from s"
   return re.sub("\n( *\n)+","\n",s)

if __name__=="__main__":
   from argparse import ArgumentParser
   args = ArgumentParser(
      prog="ebookonix",description="generate ONIX XML for zero-cost e-books")
   args.add_argument("--sender",help="Sender organisation",required=True)
   args.add_argument("--publisher",help="Publisher organisation (default same as sender)",default="")
   args.add_argument("--website",help="Publisher website",default="")
   args.add_argument("--contact",help="Contact person",required=True)
   args.add_argument("--phone",help="Contact phone",default="")
   args.add_argument("--email",help="Contact email",default="")
   args.add_argument("--url",help="book URL",required=True)
   args.add_argument("--title",help="book title",required=True)
   args.add_argument("--lang",help="language ISO code",default="en")
   args.add_argument("--date",help="publication date as year (4 digits), year-quarter (5 digits), year-month (6 digits) or year-month-day (8 digits)",default=str(time.localtime()[0]))
   args.add_argument("--code",help="ID code (ISBN=..., ISSN=..., DOI=..., other=...)",required=True)
   args.add_argument("--deweyCode",help="Dewey code",default="")
   args.add_argument("--deweyTxt",help="Dewey code text",default="")
   args = args.parse_args()
   idType,idCode = args.code.split('=')
   if not args.publisher: args.publisher = args.sender
   print(onix_message([onix_product(args.url,args.title,args.lang,args.date,idCode,idType,args.deweyCode,args.deweyTxt,args.publisher,args.website)],args.sender,args.contact,args.phone,args.email))
