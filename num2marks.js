// numbers to marks in gradint links iff support

// Where to find history:
// on GitHub at https://github.com/ssb22/indexer
// and on GitLab at https://gitlab.com/ssb22/indexer
// and on BitBucket https://bitbucket.org/ssb22/indexer
// and at https://gitlab.developers.cam.ac.uk/ssb22/indexer

function nums2marks() {
if(document.getElementsByTagName) {
  var b=document.getElementsByTagName("BODY")[0],
      d=document.createElement("DIV"),s=document.createElement("SPAN"),
      ffmly = "FreeSerif, Lucida Sans Unicode, Times New Roman, DejaVu Sans, serif";
  s.setAttribute("style","font-family:"+ffmly); d.appendChild(s);
  function wid(ih) { s.innerHTML=ih; b.appendChild(d); var w=s.offsetWidth; b.removeChild(d); return w };
  var i3_width=wid("\u01d0"),o3_width=wid("\u01d2"),sup6_width=wid("\u2076"),sup2_width=wid("\u00b2");
  var supports_pinyin = o3_width > i3_width; // (if proportional)
  var supports_sup = (sup6_width < wid('n') && sup2_width==sup6_width);
  if (supports_pinyin || supports_sup) {
    var links=document.getElementsByTagName("A");
    for(var i=0; i<links.length; i++) if(links[i].innerHTML) {
      if (supports_pinyin && links[i].getAttribute("href").indexOf("gradint.cgi?jsl=zh&")>-1) {
        var o=links[i].innerHTML; var n=o.replace(/a1/g,'ā').replace(/ai1/g,'āi').replace(/ao1/g,'āo').replace(/an1/g,'ān').replace(/ang1/g,'āng').replace(/o1/g,'ō').replace(/ou1/g,'ōu').replace(/e1/g,'ē').replace(/ei1/g,'ēi').replace(/en1/g,'ēn').replace(/eng1/g,'ēng').replace(/i1/g,'ī').replace(/in1/g,'īn').replace(/ing1/g,'īng').replace(/ong1/g,'ōng').replace(/ou1/g,'ōu').replace(/u1/g,'ū').replace(/un1/g,'ūn').replace(/v1/g,'ǖ').replace(/a2/g,'á').replace(/ai2/g,'ái').replace(/ao2/g,'áo').replace(/an2/g,'án').replace(/ang2/g,'áng').replace(/o2/g,'ó').replace(/ou2/g,'óu').replace(/e2/g,'é').replace(/ei2/g,'éi').replace(/en2/g,'én').replace(/eng2/g,'éng').replace(/i2/g,'í').replace(/in2/g,'ín').replace(/ing2/g,'íng').replace(/o2/g,'ó').replace(/ong2/g,'óng').replace(/ou2/g,'óu').replace(/u2/g,'ú').replace(/un2/g,'ún').replace(/v2/g,'ǘ').replace(/a3/g,'ǎ').replace(/ai3/g,'ǎi').replace(/ao3/g,'ǎo').replace(/an3/g,'ǎn').replace(/ang3/g,'ǎng').replace(/o3/g,'ǒ').replace(/ou3/g,'ǒu').replace(/e3/g,'ě').replace(/ei3/g,'ěi').replace(/en3/g,'ěn').replace(/eng3/g,'ěng').replace(/er1/g,'ēr').replace(/er2/g,'ér').replace(/er3/g,'ěr').replace(/er4/g,'èr').replace(/Er1/g,'Ēr').replace(/Er2/g,'Ér').replace(/Er3/g,'Ěr').replace(/Er4/g,'Èr').replace(/i3/g,'ǐ').replace(/in3/g,'ǐn').replace(/ing3/g,'ǐng').replace(/o3/g,'ǒ').replace(/ong3/g,'ǒng').replace(/ou3/g,'ǒu').replace(/u3/g,'ǔ').replace(/un3/g,'ǔn').replace(/v3/g,'ǚ').replace(/a4/g,'à').replace(/ai4/g,'ài').replace(/ao4/g,'ào').replace(/an4/g,'àn').replace(/ang4/g,'àng').replace(/o4/g,'ò').replace(/ou4/g,'òu').replace(/e4/g,'è').replace(/ei4/g,'èi').replace(/en4/g,'èn').replace(/eng4/g,'èng').replace(/i4/g,'ì').replace(/in4/g,'ìn').replace(/ing4/g,'ìng').replace(/o4/g,'ò').replace(/ong4/g,'òng').replace(/ou4/g,'òu').replace(/u4/g,'ù').replace(/un4/g,'ùn').replace(/v4/g,'ǜ').replace(/A1/g,'Ā').replace(/Ai1/g,'Āi').replace(/Ao1/g,'Āo').replace(/An1/g,'Ān').replace(/Ang1/g,'Āng').replace(/O1/g,'Ō').replace(/Ou1/g,'Ōu').replace(/E1/g,'Ē').replace(/Ei1/g,'Ēi').replace(/En1/g,'Ēn').replace(/Eng1/g,'Ēng').replace(/Ou1/g,'Ōu').replace(/A2/g,'Á').replace(/Ai2/g,'Ái').replace(/Ao2/g,'Áo').replace(/An2/g,'Án').replace(/Ang2/g,'Áng').replace(/O2/g,'Ó').replace(/Ou2/g,'Óu').replace(/E2/g,'É').replace(/Ei2/g,'Éi').replace(/En2/g,'Én').replace(/Eng2/g,'Éng').replace(/Ou2/g,'Óu').replace(/A3/g,'Ǎ').replace(/Ai3/g,'Ǎi').replace(/Ao3/g,'Ǎo').replace(/An3/g,'Ǎn').replace(/Ang3/g,'Ǎng').replace(/O3/g,'Ǒ').replace(/Ou3/g,'Ǒu').replace(/E3/g,'Ě').replace(/Ei3/g,'Ěi').replace(/En3/g,'Ěn').replace(/Eng3/g,'Ěng').replace(/Ou3/g,'Ǒu').replace(/A4/g,'À').replace(/Ai4/g,'Ài').replace(/Ao4/g,'Ào').replace(/An4/g,'Àn').replace(/Ang4/g,'Àng').replace(/O4/g,'Ò').replace(/Ou4/g,'Òu').replace(/E4/g,'È').replace(/Ei4/g,'Èi').replace(/En4/g,'Èn').replace(/Eng4/g,'Èng').replace(/Ou4/g,'Òu');
        if (n!=o) { links[i].innerHTML=n; if(links[i].style)links[i].style.fontFamily=ffmly; }
      } else if (supports_sup && links[i].getAttribute("href").indexOf("gradint.cgi?jsl=zh-yue&")>-1) {
        var o=links[i].innerHTML; var n=o.replace(/<sup>1<\/sup>/g,'¹').replace(/<sup>2<\/sup>/g,'²').replace(/<sup>3<\/sup>/g,'³').replace(/<sup>4<\/sup>/g,'⁴').replace(/<sup>5<\/sup>/g,'⁵').replace(/<sup>6<\/sup>/g,'⁶');
        if (n!=o) { links[i].innerHTML=n; if(links[i].style)links[i].style.fontFamily=ffmly; }
      }
    }
  }
}
} nums2marks();
