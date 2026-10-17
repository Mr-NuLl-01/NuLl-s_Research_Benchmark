"""Rebuild offline readable article packets from the checked-in licensed originals.

Requires lxml and Pillow only for source preparation, not benchmark execution.
No network access. Original article bytes and original image retrieval identities are retained alongside compact transformed display assets.
"""
from pathlib import Path
import base64
import hashlib
import html as H
import json
import re
import zipfile
from lxml import etree, html

ROOT = Path(__file__).resolve().parent
XLINK = '{http://www.w3.org/1999/xlink}href'
SOURCES = [
    dict(id='P1', stem='weissgerber2015', title='Beyond Bar and Line Graphs: Time for a New Data Presentation Paradigm', authors='Tracey L. Weissgerber, Natasa M. Milic, Stacey J. Winham, Vesna D. Garovic', year=2015, journal='PLOS Biology 13(4): e1002128', doi='10.1371/journal.pbio.1002128', url='https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002128', license='CC BY 4.0', license_url='https://creativecommons.org/licenses/by/4.0/', original='weissgerber2015.xml', figures=3),
    dict(id='P2', stem='rougier2014', title='Ten Simple Rules for Better Figures', authors='Nicolas P. Rougier, Michael Droettboom, Philip E. Bourne', year=2014, journal='PLOS Computational Biology 10(9): e1003833', doi='10.1371/journal.pcbi.1003833', url='https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833', license='CC0 1.0 public domain dedication', license_url='https://creativecommons.org/publicdomain/zero/1.0/', original='rougier2014.xml', figures=8),
    dict(id='P3', stem='crameri2020', title='The misuse of colour in science communication', authors='Fabio Crameri, Grace E. Shephard, Philip J. Heron', year=2020, journal='Nature Communications 11: 5444', doi='10.1038/s41467-020-19160-7', url='https://www.nature.com/articles/s41467-020-19160-7', license='CC BY 4.0', license_url='https://creativecommons.org/licenses/by/4.0/', original='crameri2020.html', figures=6),
]

def img(stem, n, alt):
    b = (ROOT/'offline-figures'/f'{stem}-fig{n}.png').read_bytes()
    return f'<img alt="{H.escape(alt,quote=True)}" src="data:image/png;base64,{base64.b64encode(b).decode()}" style="max-width:100%;height:auto">'

def text(node):
    return re.sub(r'\s+', ' ', ''.join(node.itertext())).strip()

def clean_xml(node, source):
    tag = etree.QName(node).localname
    if tag == 'fig':
        number = int(re.search(r'(\d+)$',node.get('id')).group())
        caption = text(node.find('caption'))
        label = node.findtext('label') or f'Figure {number}'
        return f'<figure id="{source["id"]}-fig{number}">{img(source["stem"],number,label+": "+caption)}<figcaption><strong>{H.escape(label)}.</strong> {H.escape(caption)}</figcaption></figure>'
    if tag in {'graphic', 'media', 'ext-link'}:
        return H.escape(text(node))
    children = H.escape(node.text or '') + ''.join(clean_xml(c,source)+H.escape(c.tail or '') for c in node)
    if tag in {'title'}: return '<h4>'+children+'</h4>'
    if tag in {'p', 'list-item', 'bold', 'italic', 'sub', 'sup', 'table', 'thead', 'tbody', 'tr', 'th', 'td'}:
        mapped={'list-item':'li','bold':'strong','italic':'em'}.get(tag,tag)
        attrs=''
        if tag in {'th','td'}:
            attrs=''.join(f' {a}="{node.get(a)}"' for a in ('colspan','rowspan') if node.get(a))
        return f'<{mapped}{attrs}>'+children+f'</{mapped}>'
    if tag=='list': return '<ul>'+children+'</ul>'
    if tag=='ref': return '<p>'+children+'</p>'
    if tag in {'inline-formula','disp-formula','math'}:
        # Retain readable source math, including MathML/TeX text, without scripts.
        return '<span class="source-math">'+children+'</span>'
    return children

def plos(source):
    root=etree.parse(str(ROOT/source['original']))
    permissions=root.xpath('//permissions')[0]
    source['license_statement']=text(permissions)
    article=root.getroot()
    body=''
    for section in root.xpath('//front//abstract | //body | //back/ref-list'):
        body+=clean_xml(section,source)
    if source['id']=='P1':
        with zipfile.ZipFile(ROOT/'weissgerber2015-s1.docx') as z:
            doc=etree.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paras=[''.join(p.xpath('.//w:t/text()',namespaces=ns)) for p in doc.xpath('//w:p',namespaces=ns)]
        supplement='\n'.join(paras)
        (ROOT/'weissgerber2015-s1.txt').write_text(supplement+'\n',encoding='utf-8')
        body+='<h3>P1 S1 Text: supplied supplemental methods and results</h3><p>Verbatim text extraction from the published S1 DOCX. Paragraph order is retained; table cells are presented sequentially in the source order. Source typographical errors are retained. Other supplementary files are not supplied.</p><pre class="source-text">'+H.escape(supplement)+'</pre>'
        source['supplied_scope']='Complete main article text, bibliography and all 3 main figures; complete S1 Text DOCX as readable extraction. Other SI is not supplied.'
    else:
        source['supplied_scope']='Complete main article text, bibliography and all 8 main figures. Linked GitHub figure scripts and external references are not supplied.'
    return body

def nature(source):
    root=html.parse(str(ROOT/source['original']),parser=html.HTMLParser(encoding='utf-8'))
    rights=root.xpath('//section[@data-title="Rights and permissions"]')[0]
    source['license_statement']=text(rights)
    sections=root.xpath('//section[@data-title="Abstract" or @data-title="Introduction" or @data-title="Methods" or @data-title="Data availability" or @data-title="References"]')
    fig_index=0
    def conv(node):
        nonlocal fig_index
        tag=node.tag.lower() if isinstance(node.tag,str) else ''
        if tag in {'script','style','button','svg','picture','img','source'}:return ''
        if tag=='figure':
            fig_index+=1
            n=fig_index
            cap=text(node).replace('Full size image',' ')
            return '<figure id="P3-fig'+str(n)+'">'+img(source['stem'],n,cap)+'<figcaption>'+H.escape(cap)+'</figcaption></figure>'
        if tag=='a' and 'Full size' in text(node):return ''
        children=H.escape(node.text or '')+''.join(conv(c)+H.escape(c.tail or '') for c in node)
        if tag in {'p','h2','h3','h4','h5','ul','ol','li','strong','b','em','i','sup','sub','table','thead','tbody','tr','td','th'}:
            return f'<{tag}>'+children+f'</{tag}>'
        return children
    body=''.join(conv(s) for s in sections)
    source['supplied_scope']='Complete main article Abstract, Introduction (including boxes and all 6 figures), Methods, Data availability and References. Supplementary Notes and supplementary figures are not supplied. Scope of assessment excludes absent SI and external source code.'
    assert fig_index==6,fig_index
    return body

def main():
    packets=[]
    for source in SOURCES:
        body=nature(source) if source['id']=='P3' else plos(source)
        header=f'<p><strong>{source["id"]}: {H.escape(source["title"])}</strong><br>{H.escape(source["authors"])} ({source["year"]}). {H.escape(source["journal"])}. DOI: {H.escape(source["doi"])}.</p><p>Original: <a href="{H.escape(source["url"],quote=True)}">{H.escape(source["url"])}</a>. License: <a href="{source["license_url"]}">{source["license"]}</a>. Retrieved 2026-10-17 UTC. Display transformation: extracted and reformatted text; figures downsampled to at most 1100 px and palette-quantized to 128 colours, with original scientific content and captions retained. These display copies are for close reading; use the source data for quantitative analysis.</p>'
        source['html']=header+'<p>'+H.escape(source['supplied_scope'])+'</p>'+body
        packets.append(source)
    (ROOT/'article-packets.json').write_text(json.dumps(packets,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    download=json.loads((ROOT/'download-urls.json').read_text())
    download.update({'weissgerber2015.xml':'https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.1002128&type=manuscript','rougier2014.xml':'https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1003833&type=manuscript','crameri2020.html':SOURCES[2]['url']})
    records=[]
    for f in sorted(ROOT.rglob('*')):
        if f.is_file() and f.name not in {'manifest.json','prepare_sources.py','README.md'}:
            records.append({'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'url':download.get(f.name) if f.parent==ROOT else None,'derived_from':f.name if f.parent.name=='offline-figures' else None,'role':'display transformation' if f.parent.name=='offline-figures' else ('published original bytes' if f.name in download else 'generated readable packet')})
    manifest={'retrieved_original_images':json.loads((ROOT/'retrieved-original-images.json').read_text()),'retrieved_utc':'2026-10-17','articles':[{k:v for k,v in s.items() if k!='html'} for s in packets],'assets':records,'license_review':'Licenses verified against the specific article permissions blocks, not publisher defaults. P2 is CC0. No credit line in the supplied main figures declares an exclusion from the article license. P2 Figure 1 is an author-produced remake; its caption is retained. P3 Figure 1 attribution to the historical photograph is retained. The Nature website chrome is not embedded as article content. Source assertions, numerical definitions and typographical errors are retained as published; the benchmark makes no claim to correct the papers.'}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Readable packet bytes:',(ROOT/'article-packets.json').stat().st_size)
if __name__=='__main__':main()
