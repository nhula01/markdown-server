"""A collected edition assembled from public topic notebooks at build time."""
from functools import lru_cache
from html import escape
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader, PdfWriter
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


def build(names, root):
    """Return PDF bytes and 1-based page starts; source files are read only."""
    groups = sections(names)
    writer = PdfWriter()
    available = [(t, notes) for t, notes in groups if notes]
    count = sum(len(notes) for _, notes in available)
    writer.add_page(_front_page('Physics, with intuition.', 'The collected handwritten notebook', [
        ('Phi Hung Nguyen', 22), ('Optical sciences and quantum physics', 17),
        (f'{count} available notebooks across {len(available)} topics', 15),
        ('An evolving collection, rebuilt with each publication.', 13)]))
    # Reserve the contents sheet so source-page destinations are known.
    writer.add_blank_page(width=595, height=842)
    entries = []
    for number, (topic, notes) in enumerate(groups, 1):
        if not notes:
            entries.append({'title': topic['title'], 'page': None, 'notes': []})
            continue
        start = len(writer.pages) + 1
        writer.add_page(_front_page(topic['title'], f'Topic {number:02d}', [(Path(n).stem, 19) for n in notes]))
        parent = writer.add_outline_item(topic['title'], start-1)
        entry = {'title': topic['title'], 'page': start, 'notes': []}
        for name in notes:
            page = len(writer.pages) + 1
            source = PdfReader(root / name)
            for original in source.pages:
                writer.add_page(original)
            writer.add_outline_item(Path(name).stem, page-1, parent=parent)
            entry['notes'].append({'name': name, 'title': Path(name).stem, 'page': page, 'pages': len(source.pages)})
        entries.append(entry)
    lines = []
    for i, entry in enumerate(entries, 1):
        destination = f"p. {entry['page']}" if entry['page'] else 'notes to come'
        lines.append((f"{i:02d}   {entry['title']}  /  {destination}", 17))
    lines += [('', 10), ('Use PDF bookmarks to jump to any notebook.', 12)]
    contents = _front_page('Contents', 'Available notes and the topics still to come', lines)
    writer.pages[1].merge_page(contents)
    writer.add_metadata({'/Title': 'Physics, with intuition - Collected notebook', '/Author': 'Phi Hung Nguyen'})
    stream = BytesIO(); writer.write(stream)
    return stream.getvalue(), entries


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
    return f'''<div class="breadcrumbs"><a href="/">← Home</a></div><header class="page-intro"><p class="eyebrow">The collected notebook</p><h1>Physics, with intuition.</h1><p class="lead">The available handwritten notes, gathered in topic order.</p><p class="muted">Rebuilt whenever the collection is published. Topics without notes remain marked as coming.</p><div class="actions"><a class="button" href="#handwritten-notes">Read the book ↓</a><a class="section-link" href="{url}" download>Download PDF ↗</a></div></header><div class="chapter-layout"><aside class="chapter-sidebar book-contents" aria-label="Book contents"><h2>Contents</h2><ol>{''.join(navigation)}</ol></aside><section id="handwritten-notes"><div class="pdf-reader" data-pdf-url="{url}" data-title="Collected notebook" data-page="1"><div class="pdf-controls"><div><button type="button" data-pdf-previous aria-label="Previous PDF page" disabled>←</button><select data-pdf-select aria-label="PDF page" disabled></select><button type="button" data-pdf-next aria-label="Next PDF page" disabled>→</button></div><div><button type="button" data-pdf-zoom-out aria-label="Zoom out" disabled>−</button><button type="button" data-pdf-zoom-in aria-label="Zoom in" disabled>+</button></div></div><p data-pdf-status role="status">Loading the collected notebook…</p><div class="pdf-surface"><canvas role="img" aria-label="Collected notebook page"></canvas></div></div><p class="file-source">The handwriting is preserved; covers, topic dividers, and bookmarks organize this edition.</p><noscript><a href="{url}">Read the collected PDF</a></noscript></section></div>'''
