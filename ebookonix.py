"""
ebookonix v0.6 (c) 2025 Silas S. Brown.  License: Apache 2
Generate ONIX XML for zero-cost e-books.
Run from the command line to generate XML for a single book.
Or use as a module (see doc strings).
Not yet tested with a library, but validated with onixcheck"""

import langcodes # pip install langcodes
import re, time
from argparse import ArgumentParser
from xml.sax.saxutils import escape as E

def onix_message(products,
                 sender="",name="",phone="",email="") -> str:
   """Creates a complete ONIX For Books XML message.
   products is a list of return values of onix_product().
   Sender organisation, contact name, phone and email may
   be provided."""
   return _deBlank(f"""<?xml version="1.0" encoding="UTF-8"?>
<ONIXMessage release="3.1" xmlns="http://ns.editeur.org/onix/3.1/reference">
 <Header>
  <Sender>
    <SenderName>{E(sender)}</SenderName>
    <ContactName>{E(name)}</ContactName>
    {f'<TelephoneNumber>{E(phone)}</TelephoneNumber>' if phone else ''}
    {f'<EmailAddress>{E(email)}</EmailAddress>' if email else ''}
  </Sender>
  <MessageRepeat>1</MessageRepeat>
  <SentDateTime>{'%d%02d%02d' % time.localtime()[:3]}</SentDateTime>
 </Header>
{chr(10).join(products)}
</ONIXMessage>
""")

def onix_product(url,title:str,lang_iso:str="en",
                 author:str="",
                 authorIsCorporate:bool=False,
                 date=2000, # year (4 digits), year-quarter (5 digits), year-month (6 digits) or year-month-day (8 digits)
                 idCode:str="",
                 idType:str="ISBN", # ISSN, DOI etc (see below)
                 # and see https://ns.editeur.org/onix/en/5
                 issn:str="",
                 issnTitlePrefix:str="",
                 issnTitleWithoutPrefix:str="",
                 deweyCode:str="",deweyTxt:str="",
                 bisacHeadings:[str]=[],
                 keywords:str="",synopsis:str="",
                 hasImageDescriptions:bool=False,
                 publisher:str="",copyright:str="",
                 publisherWebsite:str="")->str:
    """Creates an ONIX XML fragment for a book product.
    We use ProductForm ED = digital download
    and UnpricedItemType 01 = free of charge.
    url is the EPUB URL, PDF URL, list of MP3 URLs, etc"""
    if isinstance(url,list):
       if not url: raise Exception("url cannot be empty list")
       urls = url
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
    datelen2format = {4:'05',5:'03',6:'01',8:'00'}
    return _deBlank(f""" <Product>
  <RecordReference>{E(idCode)}-{lang_iso}-{date}-{E(format)}</RecordReference>
  <NotificationType>03</NotificationType>
  <RecordSourceType>01</RecordSourceType>
  <RecordSourceName>{E(publisher)}</RecordSourceName>
  <ProductIdentifier>
    <ProductIDType>{E(idTypeCode)}</ProductIDType>
    {f'<IDTypeName>{E(idType)}</IDTypeName>' if idTypeCode=='01' else ''}
    <IDValue>{ensureIssnIs13(idCode) if idTypeCode=='34' else E(idCode)}</IDValue>
  </ProductIdentifier>
  <DescriptiveDetail>
    <ProductComposition>00</ProductComposition>
    <ProductForm>ED</ProductForm>
    <ProductFormDetail>{list175.get(format.lower(),"E100")}</ProductFormDetail>
    {'''<ProductFormFeature>
      <ProductFormFeatureType>09</ProductFormFeatureType>
      <ProductFormFeatureValue>15</ProductFormFeatureValue>
    </ProductFormFeature>''' if hasImageDescriptions else ''}
    {f'''<Collection>
      <CollectionType>10</CollectionType>
      <CollectionIdentifier>
        <CollectionIDType>02</CollectionIDType>
        <IDValue>{issn}</IDValue>
      </CollectionIdentifier>
      <TitleDetail>
        <TitleType>02</TitleType>
        <TitleElement>
          <TitleElementLevel>02</TitleElementLevel>
          {f'<TitlePrefix language="{langcodes.Language.get(lang_iso).to_alpha3()}">{issnTitlePrefix}</TitlePrefix>' if issnTitlePrefix else '<NoPrefix/>'}
          <TitleWithoutPrefix language="{langcodes.Language.get(lang_iso).to_alpha3()}">{issnTitleWithoutPrefix}</TitleWithoutPrefix>
        </TitleElement>
      </TitleDetail>
    </Collection>''' if issn and issnTitleWithoutPrefix else ''}
    <TitleDetail>
      <TitleType>01</TitleType>
      <TitleElement>
        <TitleElementLevel>01</TitleElementLevel>
        <TitleText language="{langcodes.Language.get(lang_iso).to_alpha3()}">{E(title)}</TitleText>
      </TitleElement>
    </TitleDetail>
    {f'''<Contributor>
      <ContributorRole>A01</ContributorRole>
      <{'Corporate' if authorIsCorporate else 'Person'}Name>{author}</{'Corporate' if authorIsCorporate else 'Person'}Name>
    </Contributor>''' if author else '<NoContributor/>'}
    <NoEdition/>
    <Language>
      <LanguageRole>01</LanguageRole>
      <LanguageCode>{langcodes.Language.get(lang_iso).to_alpha3()}</LanguageCode>
    </Language>
    {f'''<Subject>
      <MainSubject/>
      <SubjectSchemeIdentifier>01</SubjectSchemeIdentifier>
      <SubjectCode>{E(deweyCode)}</SubjectCode>
      <SubjectHeadingText>{E(deweyTxt)}</SubjectHeadingText>
    </Subject>''' if deweyCode and deweyTxt else ''}
    {''.join(f'''<Subject>
      {'<MainSubject/>' if b==bisacHeadings[0] else ''}
      <SubjectSchemeIdentifier>10</SubjectSchemeIdentifier>
      <SubjectSchemeVersion>2016</SubjectSchemeVersion>
      <SubjectCode>{E(b)}</SubjectCode>
    </Subject>''' for b in bisacHeadings) if bisacHeadings else ''}
    {f'''<Subject>
      <SubjectSchemeIdentifier>20</SubjectSchemeIdentifier>
      <SubjectHeadingText>{E(keywords)}</SubjectHeadingText>
    </Subject>''' if deweyCode and deweyTxt else ''}
  </DescriptiveDetail>
  {f'''<CollateralDetail>
    <TextContent>
      <TextType>03</TextType>
      <ContentAudience>03</ContentAudience>
      <Text>{E(synopsis)}</Text>
    </TextContent>
  </CollateralDetail>''' if synopsis else ''}
  <PublishingDetail>
    <Publisher>
      <PublishingRole>01</PublishingRole>
      <PublisherName>{E(publisher)}</PublisherName>
      {f'''<Website>
        <WebsiteRole>01</WebsiteRole>
        <WebsiteLink>{E(publisherWebsite)}</WebsiteLink>
      </Website>''' if publisherWebsite else ''}
    </Publisher>
    <PublishingStatus>04</PublishingStatus>
    <PublishingDate>
      <PublishingDateRole>01</PublishingDateRole>
      <Date dateformat="{datelen2format[len(str(date))]}">{str(date).replace("-","")}</Date>
    </PublishingDate>
    <CopyrightStatement>
      <CopyrightYear>{str(date)[:4]}</CopyrightYear>
      <CopyrightOwner>
        <CorporateName>{E(copyright)}</CorporateName>
      </CopyrightOwner>
    </CopyrightStatement>
  </PublishingDetail>
  <ProductionDetail>
    <ProductionManifest>
      <BodyManifest>
{''.join(f'''
        <BodyResource>
          <ResourceFileLink>{E(u)}</ResourceFileLink>
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
        <SupplierName>{E(publisher)}</SupplierName>
        {f'''<Website>
          <WebsiteRole>01</WebsiteRole>
          <WebsiteLink>{E(publisherWebsite)}</WebsiteLink>
        </Website>''' if publisherWebsite else ''}
      </Supplier>
      <ProductAvailability>21</ProductAvailability>
      <UnpricedItemType>01</UnpricedItemType>
    </SupplyDetail>
  </ProductSupply>
 </Product>""")

def ensureIssnIs13(issn:str) -> str:
   "Ensures that an ISSN code is in ISSN-13 format as required by ONIX"
   issn = issn.replace("-","")
   if len(issn)==8:
      if not str(11-(sum(int(a)*b for a,b in zip(issn[:7],range(8,1,-1)))%11)).replace('10','X')==issn[7]:
         raise Exception(f"wrong ISSN-8 checksum in {issn}")
      issn = "977"+issn[:7]
      return f"{issn}00{(10-(sum(int(c)*(3 if i%2 else 1) for i,c in enumerate(issn))%10))%10}"
   else: return issn

def _deBlank(s:str) -> str:
   "Remove blank lines from s"
   return re.sub("\n( *\n)+","\n",s)

def main():
   args = ArgumentParser(
      prog="ebookonix",description="generate ONIX XML for zero-cost e-books")
   args.add_argument("--sender",help="Sender organisation",required=True)
   args.add_argument("--publisher",help="Publisher organisation (default same as sender)",default="")
   args.add_argument("--copyright",help="Copyright holder (default same as publisher)",default="")
   args.add_argument("--website",help="Publisher website",default="")
   args.add_argument("--contact",help="Contact person",required=True)
   args.add_argument("--phone",help="Contact phone",default="")
   args.add_argument("--email",help="Contact email",default="")
   args.add_argument("--url",help="book URL",required=True)
   args.add_argument("--title",help="book title",required=True)
   args.add_argument("--author",help="book author (if known)")
   args.add_argument("--authorIsCorporate",default=False,action='store_true',help="specifies that the author is a corporation not a person")
   args.add_argument("--lang",help="language ISO code",default="en")
   args.add_argument("--date",help="publication date as year (4 digits), year-quarter (5 digits), year-month (6 digits) or year-month-day (8 digits)",default=str(time.localtime()[0]))
   args.add_argument("--code",help="ID code (ISBN=..., ISSN=..., DOI=..., other=...)",required=True)
   args.add_argument("--issn",help="ISSN code of surrounding collection (used with issnTitle options)",default="")
   args.add_argument("--issnTitlePrefix",help="ISSN title prefix e.g. The",default="")
   args.add_argument("--issnTitleWithoutPrefix",help="rest of ISSN title",default="")
   args.add_argument("--deweyCode",help="Dewey code",default="")
   args.add_argument("--deweyTxt",help="Dewey code text",default="")
   args.add_argument("--bisacHeadings",help="Comma-separated list of BISAC heading codes, main heading first")
   args.add_argument("--keywords",help="Semicolon-separated list of keywords for the subject")
   args.add_argument("--synopsis",help="Synopsis text")
   args.add_argument("--hasImageDescriptions",default=False,action='store_true',help="Declare that image descriptions are provided")
   args = args.parse_args()
   idType,idCode = args.code.split('=')
   if not args.publisher: args.publisher = args.sender
   if not args.copyright: args.copyright = args.publisher
   print(onix_message([onix_product(
      args.url,args.title,args.lang,args.date,
      args.author,args.authorIsCorporate,
      idCode,idType,
      args.issn,args.issnTitlePrefix,args.issnTitleWithoutPrefix,
      args.deweyCode,args.deweyTxt,
      args.bisacHeadings.split(','),args.keywords,
      args.synopsis,
      args.hasImageDescriptions,
      args.publisher,args.copyright,
      args.website)],args.sender,args.contact,args.phone,args.email))

if __name__=="__main__": main()

# ruff: noqa: E401 # multiple imports on one line
# ruff: noqa: E701 # colon without newline
# ruff: noqa: E702 # semicolon statements
