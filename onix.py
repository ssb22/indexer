"""ONIX XML, not yet tested"""

import langcodes
import re

def onix_message(products,
                 sender="",name="",phone="",email=""):
   return f"""<?xml version="1.0" encoding="UTF-8"?>
<ONIXMessage release="3.1" xmlns="http://ns.editeur.org/onix/3.1/reference">
 <Header>
  <Sender>
    <SenderName>{sender}</SenderName>
    <ContactName>{name}</ContactName>
    <TelephoneNumber>{phone}</TelephoneNumber>
    <EmailAddress>{email}</EmailAddress>
  </Sender>
 </Header>
{chr(10).join(products)}
</ONIXMessage>
"""

def onix_product(title,lang_iso="en",year=2000,
                 idCode="",
                 idType="ISBN", # https://ns.editeur.org/onix/en/5 (but see code below)
                 form="", # audio-download etc or leave undefined, see https://ns.editeur.org/onix/en/150 (but see code below)
                 deweyCode="",deweyTxt="",
                 sender="",publisher="",publisherWebsite=""):
    return f""" <Product>
  <RecordSourceName>{sender}</RecordSourceName>
  <ProductIdentifier>
    <ProductIDType>{('15' if len(re.sub('[^0-9X]','',idCode))==13 else '02') if idType=="ISBN" else '01'}</ProductIDType>
    {'' if idType=="ISBN" else f'<IDTypeName>{idType}</IDTypeName>'}
    <IDValue>{idCode}</IDValue>
  </ProductIdentifier>
  <DescriptiveDetail>
    <ProductComposition>00</ProductComposition>
    <ProductForm>{'AA' if form=='audio' else 'AJ' if form=='audio-download' else 'BA' if form=='book' else 'BF' if form=='pamphlet' else 'VA' if form=='video' else '00'}</ProductForm>
    <TitleDetail>
      <TitleType>01</TitleType>
      <TitleElement>
        <TitleElementLevel>01</TitleElementLevel>
        <TitleText>{title}</TitleText>
      </TitleElement>
    </TitleDetail>
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
 </Product>"""
