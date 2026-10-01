"""Curated questions and trails, edited in an Obsidian-compatible public note."""
import re
import unicodedata
from html import escape
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).parent


def parse_leads(text):
    leads = []
    current = None
    for line in text.splitlines():
        if line.startswith('## '):
            question = line[3:].strip()
            slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', question).encode('ascii', 'ignore').decode().lower()).strip('-')
            if not slug or any(lead['id'] == slug for lead in leads):
                raise ValueError('Lead questions must be nonempty and unique')
            current = {'id': slug, 'question': question, 'steps': []}
            leads.append(current)
        elif re.match(r'^\d+\. ', line) and current is not None:
            match = re.fullmatch(r'\d+\. \[\[([^\[\]|#\n]+)\]\]\s*', line)
            if not match:
                raise ValueError('Trail steps must be numbered [[Exact notebook title]] links')
            title = match[1].strip()
            if not title or title in current['steps']:
                raise ValueError('Trail steps must have unique nonempty titles')
            current['steps'].append(title)
    if not leads or any(len(lead['steps']) < 2 for lead in leads):
        raise ValueError('Every lead needs at least two steps')
    return leads


def leads():
    return parse_leads((ROOT / 'site/leads.md').read_text())


def step(title, names):
    import chapter_content
    for name in names:
        if Path(name).stem == title:
            return {'title': title, 'url': chapter_content.chapter_url(name), 'status': 'Handwritten note'}
    for slug, concept in chapter_content.CONCEPTS.items():
        if concept['title'] == title:
            return {'title': title, 'url': '/connections/' + slug + '/', 'status': 'Planned chapter'}
    # New titles can be drafted in the vault before their PDFs or concept pages exist.
    return {'title': title, 'url': '/notes/', 'status': 'Planned chapter'}


def for_note(title):
    result = []
    for lead in leads():
        if title in lead['steps'][:-1]:
            result.append({**lead, 'steps': lead['steps'][lead['steps'].index(title):]})
    return result


def index(names, search_entries):
    starts = [entry for entry in search_entries if entry['status'] == 'Handwritten note']
    return {'starts': starts, 'leads': [{**lead, 'steps': [step(title, names) for title in lead['steps']]} for lead in leads()]}


def related_notes(title, names):
    published = {Path(name).stem for name in names}
    return list(dict.fromkeys('note:' + prior for lead in leads() if title in lead['steps']
                              for prior in lead['steps'][:lead['steps'].index(title)] if prior in published))


def explorer():
    return '''<section id="follow-thread" class="section thread-explorer" aria-labelledby="thread-title">
    <h2 id="thread-title">Follow a thread</h2><p class="lead">Choose a note. See where the idea leads.</p>
    <div class="thread-picker"><label for="thread-query">Where do you want to start?</label>
    <div class="thread-input"><input id="thread-query" type="search" autocomplete="off" placeholder="Search notes, ideas, or tags…" aria-controls="thread-options"><button type="button" id="thread-clear" aria-label="Choose another starting note" hidden>×</button></div>
    <p id="thread-status" class="muted" role="status" aria-live="polite">Loading starting notes…</p>
    <ul id="thread-options" aria-label="Starting notes"></ul></div>
    <div id="thread-origin" hidden></div><div id="thread-leads"></div><div id="thread-trail" hidden></div>
    <noscript><p><a href="/notes/">Browse the notebook</a> and follow the question leads at the end of each chapter.</p></noscript></section>'''


def chapter_leads(title):
    cards = []
    for lead in for_note(title):
        href = '/?' + urlencode({'start': title, 'lead': lead['id']}) + '#follow-thread'
        trail = ' → '.join(lead['steps'][1:])
        cards.append(f'<li><a href="{escape(href, quote=True)}"><strong>{escape(lead["question"])}</strong><span>{escape(trail)}</span><small>Follow this lead →</small></a></li>')
    body = '<ul class="chapter-leads">' + ''.join(cards) + '</ul>' if cards else '<p class="muted">No curated leads from this note yet. Choose another starting note in the explorer.</p>'
    return f'<section class="follow-lead" id="follow-lead"><p class="kicker">Finished this note?</p><h2>Follow a lead</h2>{body}<p><a class="section-link" href="/?{escape(urlencode({"start": title}), quote=True)}#follow-thread">Explore all leads →</a></p></section>'
