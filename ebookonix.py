"""
ebookonix v0.1
Convenience functions to generate ONIX XML for zero-cost e-books.
Not yet tested with a library, but validated with onixcheck"""

import langcodes
import re, time

def onix_message(products,
                 sender="",name="",phone="",email=""):
   return deBlank(f"""<?xml version="1.0" encoding="UTF-8"?>
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

def onix_product(url,title,lang_iso="en",year=2000,
                 idCode="",
                 idType="ISBN", # https://ns.editeur.org/onix/en/5 (but see code below)
                 deweyCode="",deweyTxt="",
                 publisher="",publisherWebsite=""):
    # we use ProductForm ED = digital download
    # and UnpricedItemType 01 = free of charge
    if type(url)==list: urls = url # can be list of MP3s etc
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
    return deBlank(f""" <Product>
  <RecordReference>{idCode}-{lang_iso}-{year}-{format}</RecordReference>
  <NotificationType>03</NotificationType>
  <RecordSourceType>01</RecordSourceType>
  <RecordSourceName>{publisher}</RecordSourceName>
  <ProductIdentifier>
    <ProductIDType>{('15' if len(re.sub('[^0-9X]','',idCode))==13 else '02') if idType=="ISBN" else '01'}</ProductIDType>
    {'' if idType=="ISBN" else f'<IDTypeName>{idType}</IDTypeName>'}
    <IDValue>{idCode}</IDValue>
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
    <Subject>
      <MainSubject/>
      <SubjectSchemeIdentifier>01</SubjectSchemeIdentifier>
      <SubjectCode>{deweyCode}</SubjectCode>
      <SubjectHeadingText>{deweyTxt}</SubjectHeadingText>
    </Subject>
  </DescriptiveDetail>
  <PublishingDetail>
    <Publisher>
      <PublishingRole>01</PublishingRole>
      <PublisherName>{publisher}</PublisherName>
      <Website>
        <WebsiteRole>01</WebsiteRole>
        <WebsiteLink>{publisherWebsite}</WebsiteLink>
      </Website>
    </Publisher>
    <PublishingStatus>04</PublishingStatus>
    <PublishingDate>
      <PublishingDateRole>01</PublishingDateRole>
      <Date dateformat="05">{year}</Date>
    </PublishingDate>
    <CopyrightStatement>
      <CopyrightYear>{year}</CopyrightYear>
      <CopyrightOwner>
        <CorporateName>{publisher}</CorporateName>
      </CopyrightOwner>
    </CopyrightStatement>
  </PublishingDetail>
  <ProductionDetail>
    <ProductionManifest>
      <BodyManifest>
{chr(10).join(f'<BodyResource><ResourceFileLink>{u}</ResourceFileLink></BodyResource>' for u in urls)}
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
        <Website>
          <WebsiteRole>01</WebsiteRole>
          <WebsiteLink>{publisherWebsite}</WebsiteLink>
        </Website>
      </Supplier>
      <ProductAvailability>21</ProductAvailability>
      <UnpricedItemType>01</UnpricedItemType>
    </SupplyDetail>
  </ProductSupply>
 </Product>""")

def deBlank(s): return re.sub("\n( *\n)+","\n",s)
