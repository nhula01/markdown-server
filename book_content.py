"""A collected edition assembled from public topic notebooks at build time."""
from functools import lru_cache
from html import escape
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.generic import NameObject, TextStringObject
from reportlab.lib.utils import simpleSplit
import chapter_content
import lead_content
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import site_content

BOOK_PATH = '/book/physics-with-intuition.pdf'


def sections(names):
    return [(topic, site_content.topic_notes(topic, names)) for topic in site_content.TOPICS]


def cover_card(names):
    count = sum(len(notes) for _, notes in sections(names))
    return f'''<aside class="collected-book" aria-label="Collected notebook"><a class="book-object" href="/book/" aria-label="Read Physics, with intuition: the collected notebook"><span class="book-spine" aria-hidden="true"></span><span class="book-cover"><span class="book-edition">THE COLLECTED NOTEBOOK</span><span class="book-title">Physics,<br>with <em>Intuition.</em></span><span class="book-rule" aria-hidden="true"></span><span class="book-author">Phi Hung Nguyen</span><span class="book-caption">Optics · Quantum physics</span></span></a><p class="book-description">{count} notebooks · nine topics · one growing book</p><a class="section-link" href="/book/">Open the book →</a></aside>'''


def _front_page(title, subtitle, lines=()):
    stream = BytesIO()
    c = canvas.Canvas(stream, pagesize=(595, 842), invariant=1)
    c.setFillColor(HexColor('#faf8f1')); c.rect(0, 0, 595, 842, fill=1, stroke=0)
    c.setStrokeColor(HexColor('#d8d6cd')); c.line(48, 745, 547, 745)
    c.setFillColor(HexColor('#5f6d7d')); c.setFont('Helvetica', 10)
    c.drawString(48, 770, 'PHYSICS, WITH INTUITION / PHI HUNG NGUYEN')
    c.setFillColor(HexColor('#292c30')); c.setFont('Times-Roman', 34)
    c.drawString(48, 665, title)
    c.setFont('Times-Italic', 17); c.drawString(48, 627, subtitle)
    y = 566
    for text, size in lines:
        c.setFont('Times-Roman', size); c.drawString(48, y, text); y -= 31
    c.setFont('Helvetica', 9); c.setFillColor(HexColor('#687078'))
    c.drawString(48, 48, 'Working notes. Original handwritten pages follow in topic order.')
    c.showPage(); c.save()
    return PdfReader(BytesIO(stream.getvalue())).pages[0]


def _context_pages(title, names, included):
    """Typeset existing public context; retain logical links until pagination ends."""
    chapter = chapter_content.CHAPTERS.get(title, {})
    rows = [('heading', 'Read this notebook', None),
            ('link', 'Read handwritten notes', 'source:' + title)]
    if chapter.get('activator'):
        rows.append(('link', 'Activator - return to the handwritten starting point', 'activator:' + title))
    for key, label in chapter_content.GROUPS:
        targets = chapter.get(key, [])
        if not targets:
            continue
        rows.append(('heading', label, None))
        for target in targets:
            label, url, status = chapter_content.resolve_connection(target, names)
            if 'note:' + label in included:
                target = 'note:' + label
            internal = target in included
            suffix = '' if internal else ' [' + (status or 'Online chapter') + ']'
            rows.append(('link', label + suffix, target if internal else url))
    leads = lead_content.for_note(title)
    if leads:
        rows.append(('heading', 'Follow a lead', None))
        for lead in leads:
            rows.append(('question', lead['question'], None))
            for i, step_title in enumerate(lead['steps'][1:], 1):
                step = lead_content.step(step_title, names)
                key = 'note:' + step_title
                internal = key in included
                suffix = '' if internal else ' [' + step['status'] + ']'
                rows.append(('link', f'{i:02d}   {step_title}' + suffix, key if internal else step['url']))
    rows.append(('heading', 'Keep exploring', None))
    rows.append(('link', 'Return to the book contents', 'contents'))
    rows.append(('link', 'Open this chapter on the website', chapter_content.chapter_url(next(n for n in names if Path(n).stem == title))))
    result = []; stream = BytesIO(); c = canvas.Canvas(stream, pagesize=(595,842), invariant=1)
    links = []; y = 0; branch_top = 0; continuation = False
    def begin():
        nonlocal y, branch_top
        c.setFillColor(HexColor('#faf8f1')); c.rect(0,0,595,842,fill=1,stroke=0)
        c.setFillColor(HexColor('#5f6d7d')); c.setFont('Helvetica',10)
        c.drawString(48,770,'FOLLOW THE CONNECTIONS' + (' / CONTINUED' if continuation else ''))
        c.setFillColor(HexColor('#292c30')); c.setFont('Times-Roman',26)
        lines = simpleSplit(title,'Times-Roman',26,495)
        y=715
        for line in lines: c.drawString(48,y,line); y-=31
        y-=12
        if not continuation:
            activator=chapter.get('activator',{})
            core=activator.get('text') or chapter.get('question') or title
            label='ACTIVATOR / THE CENTRAL IDEA' if activator else 'THE CHAPTER QUESTION' if chapter.get('question') else 'THE NOTEBOOK'
            c.setFont('Helvetica-Bold',9); c.setFillColor(HexColor('#526477'))
            c.drawCentredString(297, y-8, label)
            y-=34
            node_lines=simpleSplit(core,'Times-Roman',17,430)
            top=y+49
            c.setFont('Times-Roman',17); c.setFillColor(HexColor('#292c30'))
            for line in node_lines: c.drawCentredString(297,y,line); y-=23
            c.setStrokeColor(HexColor('#9aa4ac')); c.setLineWidth(.7)
            c.roundRect(62,y+7,471,top-y-4,8,fill=0,stroke=1)
            if activator:
                links.append(((62,y+7,533,top+3),'activator:'+title,'Read the original activator'))
            c.line(297,y+7,297,y-9); c.line(36,y-9,297,y-9)
            y-=30
        branch_top=y+20
    def finish():
        c.setStrokeColor(HexColor('#bac1c5')); c.setLineWidth(.5); c.line(36,branch_top,36,y+15)
        c.setFillColor(HexColor('#687078')); c.setFont('Helvetica',9)
        c.drawString(48,35,'Underlined entries are clickable. Planned chapters open their website outline.')
        c.showPage()
    begin()
    for kind, text, target in rows:
        font = 'Helvetica-Bold' if kind == 'heading' else 'Times-Italic' if kind == 'question' else 'Times-Roman'
        size = 11 if kind == 'heading' else 15
        lines = simpleSplit(text,font,size,490)
        height = len(lines)*20 + (17 if kind == 'heading' else 8)
        if y-height-(55 if kind == 'heading' else 0) < 70:
            finish(); result.append(links); links=[]; continuation=True; begin()
        if kind == 'heading':
            y-=10
            c.setStrokeColor(HexColor('#9aa4ac')); c.setLineWidth(.6)
            c.line(36,y+16,36,y-9); c.line(36,y+5,44,y+5)
            c.circle(36,y+5,2,fill=0,stroke=1)
        c.setFont(font,size); c.setFillColor(HexColor('#526477') if target else HexColor('#292c30'))
        for line in lines:
            c.drawString(48,y,line)
            if target:
                width=c.stringWidth(line,font,size)
                c.setStrokeColor(HexColor('#9aa4ac')); c.setLineWidth(.4); c.line(48,y-3,48+width,y-3)
                links.append(((46,y-5,50+width,y+16),target,text))
            y-=20
        y-=17 if kind == 'heading' else 8
    finish(); result.append(links); c.save()
    pdf=PdfReader(BytesIO(stream.getvalue()))
    return [(page, links) for page,links in zip(pdf.pages,result)]


def build(names, root):
    """Assemble original pages with native PDF links between chapter contexts."""
    groups = sections(names)
    writer = PdfWriter()
    available = [(t, notes) for t, notes in groups if notes]
    count = sum(len(notes) for _, notes in available)
    included = {'note:' + Path(n).stem for _, notes in available for n in notes}
    included.update('topic:' + t['slug'] for t,notes in available)
    writer.add_page(_front_page('Physics, with intuition.', 'The connected handwritten notebook', [
        ('Phi Hung Nguyen', 22), ('Optical sciences and quantum physics', 17),
        (f'{count} available notebooks across {len(available)} topics', 15),
        ('Open the contents - follow the connections.', 13)]))
    writer.add_blank_page(width=595, height=842)
    destinations = {'contents': 1}; pending = []; entries = []
    pending.append((0,(46,463,540,490),'contents','Open the contents'))
    for number, (topic, notes) in enumerate(groups, 1):
        if not notes:
            entries.append({'title': topic['title'], 'page': None, 'notes': []})
            continue
        start = len(writer.pages) + 1
        destinations['topic:' + topic['slug']] = start-1
        writer.add_page(_front_page(topic['title'], f'Topic {number:02d}', [(Path(n).stem, 19) for n in notes]))
        divider_index=start-1
        parent = writer.add_outline_item(topic['title'], divider_index)
        entry = {'title': topic['title'], 'page': start, 'notes': []}
        for i, name in enumerate(notes):
            title=Path(name).stem; page=len(writer.pages)+1
            destinations['note:' + title] = page-1
            pending.append((divider_index,(46,560-i*31,545,585-i*31),'note:'+title,title))
            context = _context_pages(title,names,included)
            for context_page, links in context:
                index=len(writer.pages); writer.add_page(context_page)
                pending.extend((index,rect,target,label) for rect,target,label in links)
            source_start=len(writer.pages)+1
            destinations['source:' + title]=source_start-1
            source = PdfReader(root / name)
            activator=chapter_content.CHAPTERS.get(title,{}).get('activator',{})
            if activator:
                original_page=activator['page']
                if not 1 <= original_page <= len(source.pages):
                    raise ValueError('Activator page is outside notebook: ' + title)
                destinations['activator:'+title]=source_start+original_page-2
            for original in source.pages: writer.add_page(original)
            bookmark=writer.add_outline_item(title,page-1,parent=parent)
            writer.add_outline_item('Handwritten notes',source_start-1,parent=bookmark)
            entry['notes'].append({'name':name,'title':title,'page':page,'source_page':source_start,'pages':len(source.pages)})
        entries.append(entry)
    lines=[]
    for i,entry in enumerate(entries,1):
        destination=f"p. {entry['page']}" if entry['page'] else 'notes to come'
        lines.append((f"{i:02d}   {entry['title']}  /  {destination}",17))
        if entry['page']:
            pending.append((1,(46,560-i*31+31,545,585-i*31+31),'topic:'+groups[i-1][0]['slug'],entry['title']))
    lines += [('',10),('Click a topic, then follow its chapter connections.',12)]
    writer.pages[1].merge_page(_front_page('Contents','The book is a collection of connected ideas',lines))
    for page_index, rect, target, label in pending:
        if target in destinations:
            annotation=Link(rect=rect,target_page_index=destinations[target])
        elif target.startswith('/'):
            annotation=Link(rect=rect,url='https://nhula01.github.io/markdown-server'+target)
        else:
            raise ValueError('Unresolved book connection: '+target)
        annotation[NameObject('/Contents')]=TextStringObject(label)
        added=writer.add_annotation(page_number=page_index,annotation=annotation)
        if target in destinations:
            added['/Dest'][0]=writer.pages[destinations[target]].indirect_reference
    writer.add_metadata({'/Title':'Physics, with intuition - Connected notebook','/Author':'Phi Hung Nguyen'})
    stream=BytesIO(); writer.write(stream)
    return stream.getvalue(),entries


@lru_cache(maxsize=2)
def cached_build(root_string, signature):
    return build([name for name, _, _ in signature], Path(root_string))


def edition(names, root):
    signature = tuple((name, (root/name).stat().st_mtime_ns, (root/name).stat().st_size) for name in names)
    return cached_build(str(root), signature)


def page(entries, version=''):
    url = BOOK_PATH + ('?v=' + version if version else '')
    navigation = []
    for entry in entries:
        if entry['page'] is None:
            navigation.append(f'<li><span>{escape(entry["title"])}</span><small>Notes to come</small></li>')
            continue
        notes = ''.join(f'<li><a data-pdf-page="{note["page"]}" href="{url}#page={note["page"]}">{escape(note["title"])}<small>p. {note["page"]}</small></a></li>' for note in entry['notes'])
        navigation.append(f'<li><a data-pdf-page="{entry["page"]}" href="{url}#page={entry["page"]}">{escape(entry["title"])}</a><ol>{notes}</ol></li>')
    return f'''<div class="breadcrumbs"><a href="/">← Home</a></div><header class="page-intro"><p class="eyebrow">The collected notebook</p><h1>Physics, with intuition.</h1><p class="lead">The available handwritten notes, gathered in topic order.</p><p class="muted">Follow clickable connections, activators, and question leads between chapters. Planned chapters open the website outline.</p><div class="actions"><a class="button" href="#handwritten-notes">Read the book ↓</a><a class="section-link" href="{url}" download>Download PDF ↗</a></div></header><div class="chapter-layout"><aside class="chapter-sidebar book-contents" aria-label="Book contents"><h2>Contents</h2><ol>{''.join(navigation)}</ol></aside><section id="handwritten-notes"><div class="pdf-reader" data-pdf-url="{url}" data-title="Collected notebook" data-book-links="true" data-page="1"><div class="pdf-controls"><div><button type="button" data-pdf-previous aria-label="Previous PDF page" disabled>←</button><select data-pdf-select aria-label="PDF page" disabled></select><button type="button" data-pdf-next aria-label="Next PDF page" disabled>→</button></div><div><button type="button" data-pdf-zoom-out aria-label="Zoom out" disabled>−</button><button type="button" data-pdf-zoom-in aria-label="Zoom in" disabled>+</button></div></div><p data-pdf-status role="status">Loading the collected notebook…</p><div class="pdf-surface"><canvas role="img" aria-label="Collected notebook page"></canvas></div></div><p class="file-source">Click the underlined connections and leads on chapter pages to move through the book. The handwriting is preserved.</p><noscript><a href="{url}">Read the collected PDF</a></noscript></section></div>'''
