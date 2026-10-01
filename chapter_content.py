"""Chapter context and the connection graph; PDFs remain independent objects."""
import io
import json
import re
import subprocess
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.anchors import anchors_plugin
from pypdf import PdfReader

import site_content

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / 'site/chapters.json').read_text())
CHAPTERS = CONFIG['chapters']
CONCEPTS = CONFIG['concepts']
GROUPS = [('prerequisites', 'Prerequisites'), ('leads_to', 'Leads to'), ('appears_in', 'Appears again in')]


def math_renderer(text, options):
    delimiter = '$$' if options['display_mode'] else '$'
    return '<span class="math-source">' + escape(delimiter + text + delimiter) + '</span>'


MARKDOWN = MarkdownIt('js-default').use(dollarmath_plugin, renderer=math_renderer).use(anchors_plugin, min_level=2, max_level=3)


def markdown(stem):
    chapter = CHAPTERS.get(stem, {})
    path = ROOT / 'chapters' / (chapter.get('slug', '') + '.md')
    return path.read_text() if path.is_file() else ''


def chapter_url(name):
    return '/notebooks/' + quote(name, safe='/') + '/'


def resolve_connection(target, names):
    kind, key = target.split(':', 1)
    if kind == 'note':
        name = next((n for n in names if Path(n).stem == key), None)
        if name:
            return key, chapter_url(name), ''
        topic = site_content.topic_for(key + '.pdf')
        return key, '/notes/' + topic['slug'] + '/' if topic else '/notes/', 'Outline'
    if kind == 'concept':
        return CONCEPTS[key]['title'], '/connections/' + key + '/', 'Planned chapter'
    if kind == 'topic':
        topic = next(t for t in site_content.TOPICS if t['slug'] == key)
        status = 'Topic' if site_content.topic_notes(topic, names) else 'Outline'
        return topic['title'], '/notes/' + key + '/', status
    if kind == 'page' and key == 'research':
        return 'Reservoir computing · Research', '/research/', 'Research'
    raise ValueError('Unknown connection: ' + target)


def connection_list(targets, names):
    links = []
    for target in targets:
        label, url, status = resolve_connection(target, names)
        badge = f'<span class="connection-status">{escape(status)}</span>' if status else ''
        links.append(f'<li><a href="{url}">{escape(label)}<span aria-hidden="true"> ↗</span>{badge}</a></li>')
    return '<ul class="connection-list">' + ''.join(links) + '</ul>' if links else '<p class="muted">Connections to come.</p>'


def backlinks(target, names):
    return ['note:' + Path(name).stem for name in names
            if any(target in CHAPTERS.get(Path(name).stem, {}).get(key, []) for key, _ in GROUPS)]


@lru_cache(maxsize=256)
def _pdf_metadata(path_string, modified, size):
    path = Path(path_string)
    result = {}
    data = path.read_bytes()
    if b'%%EOF' in data[-2048:]:
        try:
            reader = PdfReader(io.BytesIO(data))
            result['pages'] = len(reader.pages)
        except Exception:
            pass  # Unknown metadata must never prevent reading the original PDF.
    # Last publication change, rather than a checkout timestamp or guessed author date.
    try:
        relative = path.relative_to(ROOT)
        stamp = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', str(relative)],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        if stamp:
            date = datetime.fromisoformat(stamp).astimezone(ZoneInfo('America/Phoenix'))
            result['updated'] = date.date().isoformat()
            result['updated_label'] = f'{date:%b} {date.day}, {date.year}'
    except (ValueError, OSError, subprocess.CalledProcessError):
        pass
    return result


def pdf_metadata(path):
    stat = path.stat()
    return _pdf_metadata(str(path), stat.st_mtime_ns, stat.st_size)


def viewer(name, url, names, metadata=None):
    stem = Path(name).stem
    chapter = CHAPTERS.get(stem, {})
    topic = site_content.topic_for(name)
    parent = f'/notes/{topic["slug"]}/' if topic else '/notes/'
    parent_title = topic['title'] if topic else 'Notebook desk'
    ordered = site_content.topic_notes(topic, names) if topic else [n for n in names if site_content.topic_for(n) is None]
    index = ordered.index(name) if name in ordered else 0
    sequence = f'{index + 1:02d}'
    metadata = metadata or {}
    facts = []
    if metadata.get('pages'):
        count = metadata['pages']; facts.append(f'{count} {"page" if count == 1 else "pages"}')
    if metadata.get('updated'):
        facts.append(f'PDF updated <time datetime="{metadata["updated"]}">{metadata["updated_label"]}</time>')
    facts.append('Working note')
    toc = []
    for item in chapter.get('contents', []):
        page = item['page']
        if metadata.get('pages') and page > metadata['pages']:
            continue
        toc.append(f'<li><a data-pdf-page="{page}" href="{escape(url, quote=True)}#page={page}"><span>{escape(item["title"])}</span><small>p. {page}</small></a></li>')
    contents = '<ol class="chapter-contents">' + ''.join(toc) + '</ol>' if toc else '<p class="muted">Contents awaiting an outline.</p>'
    guide = site_content.CATALOG.get('reading_guides', {}).get(stem, '')
    reading_guide = f'<details class="chapter-guide"><summary>Reading guide · verbatim from Optimum</summary><div class="guide-verbatim">{escape(guide)}</div></details>' if guide.strip() else ''
    body = MARKDOWN.render(markdown(stem))
    if not body:
        body = '<h2 id="physical-picture">Physical picture</h2><p>The context for this working notebook is still taking shape.</p>'
    groups = ''.join(f'<section><h3>{label}</h3>{connection_list(chapter.get(key, []), names)}</section>' for key, label in GROUPS)
    incoming = backlinks('note:' + stem, names)
    linked_from = f'<section class="linked-from"><h3>Linked from</h3>{connection_list(incoming, names)}</section>' if incoming else ''
    neighbors = []
    for offset, label, arrow in [(-1, 'Previous note', '←'), (1, 'Next note', '→')]:
        position = index + offset
        if 0 <= position < len(ordered):
            other = ordered[position]
            neighbors.append(f'<a href="{chapter_url(other)}"><small>{label}</small><span>{arrow} {escape(Path(other).stem)}</span></a>')
    tags = ''.join(f'<span>{escape(tag)}</span>' for tag in chapter.get('tags', []))
    return f'''<article class="chapter">
        <div class="breadcrumbs"><a href="{parent}">← {escape(parent_title)}</a></div>
        <header class="chapter-header"><p class="eyebrow">{escape(parent_title)} / {sequence}</p><h1>{escape(stem)}</h1>
        <p class="lead">{escape(chapter.get('question', 'A handwritten working notebook.'))}</p>
        <div class="chapter-meta">{'<span aria-hidden="true"> · </span>'.join(facts)}</div>
        <div class="actions"><a class="button" href="#handwritten-notes">Read handwritten notes ↓</a><a class="section-link" href="#connections">Follow the connections →</a></div></header>
        <div class="chapter-layout"><aside class="chapter-sidebar" aria-label="Chapter contents"><h2>In this note</h2>{contents}
        <nav aria-label="Chapter context"><a href="#physical-picture">Physical picture</a><a href="#connections">Key connections</a></nav><div class="chapter-tags">{tags}</div></aside>
        <div class="chapter-main"><section id="handwritten-notes" class="handwriting"><div class="pdf-toolbar"><span class="kicker">The handwritten source</span><a href="{escape(url, quote=True)}">Open PDF ↗</a></div>
        <div class="pdf-reader" data-pdf-url="{escape(url, quote=True)}" data-title="{escape(stem, quote=True)}" data-page="1"><div class="pdf-controls"><div><button type="button" data-pdf-previous aria-label="Previous PDF page" disabled>←</button><select data-pdf-select aria-label="PDF page" disabled></select><button type="button" data-pdf-next aria-label="Next PDF page" disabled>→</button></div><div><button type="button" data-pdf-zoom-out aria-label="Zoom out" disabled>−</button><button type="button" data-pdf-zoom-in aria-label="Zoom in" disabled>+</button></div></div><p data-pdf-status role="status" aria-live="polite">Loading handwritten notes…</p><div class="pdf-surface"><canvas role="img" aria-label="{escape(stem, quote=True)} · handwritten page"></canvas></div></div>
        <noscript><iframe class="pdf-frame" title="{escape(stem, quote=True)} · handwritten notes" src="{escape(url, quote=True)}#page=1" width="100%" height="1100"></iframe></noscript><p class="file-source">Original reMarkable export. Use Open PDF to read or download the original file.</p></section>
        <div class="chapter-prose">{body}{reading_guide}</div>
        <section id="connections" class="chapter-connections"><h2>Key connections</h2><div class="connection-groups">{groups}</div>{linked_from}</section>
        <nav class="chapter-pagination" aria-label="Reading order">{''.join(neighbors)}</nav></div></div></article>'''


def concept_page(slug, names):
    concept = CONCEPTS[slug]
    topic = next(t for t in site_content.TOPICS if t['slug'] == concept['topic'])
    return f'''<div class="breadcrumbs"><a href="/notes/{topic['slug']}/">← {escape(topic['title'])}</a></div>
        <header class="page-intro"><p class="eyebrow">A connection to follow · Planned chapter</p><h1>{escape(concept['title'])}</h1><p class="lead">{escape(concept['description'])}</p><p class="notice">A dedicated handwritten chapter is still to come. Follow the existing notes connected to this idea below.</p></header>
        <section><h2>Connected handwritten notes</h2>{connection_list(backlinks('concept:' + slug, names), names)}</section>
        <p class="actions"><a class="section-link" href="/notes/{topic['slug']}/">Explore {escape(topic['title'])} →</a></p>'''


def home_trails(names):
    trails = []
    for label, stems in [('From fields to material response', ['Electromagnetic Pieces', "Maxwell's Equations", 'Linear Light']),
                         ('From atoms to optical properties', ['Crystal', 'Electrons in Crystals', 'Linear Light']),
                         ('From motion to propagation', ['Oscillator Model', 'Linear Light'])]:
        links = [f'<a href="{chapter_url(name)}">{escape(stem)}</a>' for stem in stems
                 for name in names if Path(name).stem == stem]
        if len(links) > 1:
            trails.append(f'<article><h3>{label}</h3><p>{" <span aria-hidden=\"true\">→</span> ".join(links)}</p></article>')
    if not trails:
        return ''
    return '<section class="section home-trails"><h2>Follow a thread</h2><p class="muted">Start with a physical picture, then follow it into a different part of the notebook.</p>' + ''.join(trails) + '</section>'


def plain_text(html):
    from html import unescape
    return unescape(re.sub('<[^>]+>', ' ', html))


def search_index(names, documents=(), document_root=None):
    entries = []
    for name in names:
        stem = Path(name).stem; chapter = CHAPTERS.get(stem, {}); topic = site_content.topic_for(name)
        guide = site_content.CATALOG.get('reading_guides', {}).get(stem, '')
        connections = [resolve_connection(target, names)[0] for key, _ in GROUPS for target in chapter.get(key, [])]
        entries.append({'title': stem, 'category': topic['title'] if topic else 'Notebook desk', 'url': chapter_url(name),
                        'status': 'Handwritten note', 'summary': chapter.get('question', ''), 'tags': chapter.get('tags', []),
                        'text': '\n'.join([guide, plain_text(MARKDOWN.render(markdown(stem))), chapter.get('summary', ''), *connections, *(item['title'] for item in chapter.get('contents', []))])})
    for topic in site_content.TOPICS:
        entries.append({'title': topic['title'], 'category': 'Topics', 'url': '/notes/' + topic['slug'] + '/',
                        'status': 'Topic' if site_content.topic_notes(topic, names) else 'Outline',
                        'summary': topic['question'], 'tags': [], 'text': '\n'.join([topic['description'], *topic['outline']])})
    for slug, concept in CONCEPTS.items():
        entries.append({'title': concept['title'], 'category': 'Connections', 'url': '/connections/' + slug + '/',
                        'status': 'Planned chapter', 'summary': concept['description'], 'tags': [], 'text': ''})
    entries.append({'title': 'Reservoir computing', 'category': 'Research', 'url': '/research/', 'status': 'Research',
                    'summary': 'Dynamics, memory, and information.', 'tags': ['quantum', 'reservoir', 'non-Markovian', 'feedback'],
                    'text': plain_text(site_content.research())})
    if document_root:
        for name in documents:
            path = (document_root / name).resolve()
            if not path.is_relative_to(document_root) or path.stat().st_size > 2 * 1024 * 1024:
                continue
            entries.append({'title': path.stem, 'category': 'Written documents', 'url': '/docs/' + quote(name, safe='/') + '/',
                            'status': 'Markdown', 'summary': '', 'tags': [], 'text': plain_text(MARKDOWN.render(path.read_text()))})
    return entries
