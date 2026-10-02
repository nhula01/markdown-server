"""Editorial pages shared by the local server and the GitHub Pages build.

Only curated topic descriptions are public; the source Obsidian vault is never
read or copied by the site builder. Notebook files keep their original paths.
"""
import json
from html import escape
from pathlib import Path
from urllib.parse import quote
from topic_art import diagram

CATALOG = json.loads((Path(__file__).parent / 'site/catalog.json').read_text())
TOPICS = CATALOG['topics']


def topic_for(name):
    stem = Path(name).stem
    for topic in TOPICS:
        if stem in topic['notebooks'] or topic['slug'] in Path(name).parts:
            return topic
    return None


def topic_notes(topic, names):
    matching = [name for name in names if topic_for(name) == topic]
    order = list(topic['notebooks'])
    return sorted(matching, key=lambda name: (order.index(Path(name).stem) if Path(name).stem in order else len(order), name))


def topic_status(topic, names):
    count = len(topic_notes(topic, names))
    if count:
        return f'<span class="dot"></span>{count} handwritten {"note" if count == 1 else "notes"}'
    return '<span class="dot planned"></span>Outline · notes to come'


def topic_cards(names, selected=None):
    selected = TOPICS if selected is None else selected
    return ''.join(f'''<article class="topic-card" id="{topic['slug']}">
        <div class="topic-top"><span class="number">{TOPICS.index(topic)+1:02d}</span><span class="symbol" aria-hidden="true">{topic['symbol']}</span></div>
        <h3><a href="/notes/{topic['slug']}/">{escape(topic['title'])}</a></h3>
        <p>{escape(topic['description'])}</p>
        <div class="meta">{topic_status(topic, names)}</div></article>''' for topic in selected)


def notebook_list(names, numbered=False):
    import hashlib
    items = []
    for position, name in enumerate(names, 1):
        stem = Path(name).stem
        guide = CATALOG.get('reading_guides', {}).get(stem)
        identifier = 'guide-' + hashlib.sha256(name.encode()).hexdigest()[:12]
        if guide and guide.strip():
            content = f'<span class="guide-verbatim">{escape(guide)}</span>'
        else:
            content = '<span class="guide-part"><strong>Guide in preparation</strong><span>This notebook does not have a reading guide in Optimum yet.</span></span>'
        artwork = diagram(topic_for(name), stem) if numbered else ''
        number = f'<span class="notebook-order" aria-label="Note {position}">{position:02d}</span>' if numbered else ''
        items.append(f'''<li>{number}<div class="note-entry"><div class="note-title"><h3><a class="note-link" aria-describedby="{identifier}" href="/notebooks/{quote(name, safe='/')}/">{escape(stem)}</a></h3>
            <span class="note-popover" id="{identifier}" role="tooltip"><span class="guide-label">Reading guide · from Optimum</span>{content}</span></div>
            <details class="reading-guide"><summary>Reading guide</summary><div class="guide-inline">{content}</div></details></div>{artwork}</li>''')
    list_class = 'notebook-list numbered' if numbered else 'notebook-list'
    return f'<ul class="{list_class}">' + ''.join(items) + '</ul>'


def initials(text):
    """Calligraphic capitals remain real text, including for screen readers."""
    import re
    return re.sub(r'\b([A-Z])(?=[a-z]|\b)', r'<span class="initial">\1</span>', text)


def decorate_headings(body):
    import re
    def decorate(match):
        parts = re.split(r'(<[^>]+>)', match[2])
        return match[1] + ''.join(part if part.startswith('<') else initials(part) for part in parts) + match[3]
    return re.sub(r'(<h1\b[^>]*>)(.*?)(</h1>)', decorate, body, flags=re.DOTALL)


def home(names):
    from chapter_content import home_trails
    trails = home_trails(names)
    return f'''<section class="hero"><div><p class="eyebrow">Optical sciences · Quantum physics</p>
        <h1>Physics,<br>with <em>Intuition.</em></h1>
        <p class="lead">Handwritten notes on optics and quantum physics.</p>
        <p class="muted">Phi Hung Nguyen · University of Arizona</p>
        <div class="actions"><a class="button" href="/notes/">Explore the notes <span aria-hidden="true">↗</span></a></div></div><aside class="margin-note"><p class="kicker">In the margins</p><p class="handwritten notebook-motto">Without a physical picture what actually is happening in the world, mathematics are just numbers, beautiful numbers, but no science.</p><span class="page-number">Notebook / 01</span></aside></section>
        <section class="section profile-grid"><div class="prose"><h2>A notebook for understanding</h2><p>This site is where I’m collecting the ideas I learn through my PhD: from the foundations of optics to quantum dynamics and information.</p><p>I want the notes to preserve the intuition — what a system is doing, why an approximation works, and how one idea connects to another. The mathematics matters; the aim is to make its physical meaning visible.</p></div><div class="prose"><h2>How to read the collection</h2><p>The handwritten notebooks are working notes rather than finished textbooks. Topic pages distinguish available PDFs from planned material, and the collection will grow as I write and revise.</p><p>For a starting point, explore <a href="/notes/fields-and-waves/">Fields & waves</a> or <a href="/notes/light-and-matter/">Light & matter</a>.</p></div></section>

        {trails}<section class="section"><div class="section-head"><h2>A map of the ideas</h2><a class="section-link" href="/notes/">All nine topics <span class="arrow" aria-hidden="true">→</span></a></div>
        <div class="topic-grid home">{topic_cards(names, TOPICS[:6])}</div></section>'''


def notes(names, documents=()):
    sidebar = '<aside class="toc" aria-label="Topics"><p class="kicker">In this notebook</p>' + ''.join(f'<a href="#{t["slug"]}">{escape(t["title"])}</a>' for t in TOPICS) + '</aside>'
    unfiled = [n for n in names if topic_for(n) is None]
    extras = ''
    if unfiled:
        extras += '<section class="section"><h2>Notebook desk</h2><p class="muted">Recent exports waiting to be placed in a topic.</p>' + notebook_list(unfiled) + '</section>'
    if documents:
        extras += '<details><summary>Additional written documents</summary><ul class="files">' + ''.join(f'<li><a href="/docs/{quote(n, safe="/")}/">{escape(Path(n).stem)}</a></li>' for n in documents) + '</ul></details>'
    available_topics = [t['title'] for t in TOPICS if topic_notes(t, names)]
    availability = ('Handwritten PDFs are available in ' + ', '.join(available_topics) + '; other topic pages outline notes to come.') if available_topics else 'The topic pages outline the planned notes; uncategorized exports appear on the notebook desk below.'
    return f'''<header class="page-intro"><p class="eyebrow">A PhD notebook</p><h1>Notes on the way.</h1><p class="lead">Ideas in optics and quantum physics, explained through the physical picture first. Choose a topic to follow its connections.</p>
        <p class="notice">The collection is taking shape. {escape(availability)}</p></header>
        <div class="notes-layout">{sidebar}<div><div class="topic-grid">{topic_cards(names)}</div>{extras}</div></div>
        <section class="section review-invitation"><div><p class="kicker">A little, every day</p><h2>Return to an idea.</h2><p>Recall a physical picture. Check the notebook. Come back when it is time to remember again.</p></div><a class="button" href="/notes/review/">Daily review →</a></section>'''


def topic_page(topic, names):
    available = topic_notes(topic, names)
    current = notebook_list(available, numbered=True) if available else '<p class="muted">No notebooks published yet.</p>'
    return f'''<div class="breadcrumbs"><a href="/notes/">Notes</a> / {escape(topic['title'])}</div>
        <header class="page-intro"><p class="eyebrow">Topic {TOPICS.index(topic)+1:02d} · <span aria-hidden="true">{topic['symbol']}</span></p><h1>{escape(topic['title'])}</h1><p class="lead">{escape(topic['question'])}</p></header>
        <section aria-label="Notebooks in reading order">{current}</section>'''


def research(embedded=False):
    content = '''<header class="page-intro"><p class="eyebrow">Research</p><h1>Quantum reservoir computing and photon correlations in open quantum systems.</h1><p class="lead">I study how small, open quantum systems process information and generate correlated light. One direction uses delayed feedback in an atom–mirror system as a memory resource for quantum reservoir computing. Another develops operator-language Feynman rules for Lindblad dynamics to calculate non-Gaussian photon correlations in driven, dissipative systems.</p></header>
        <section><div class="section-head"><h2>Selected work</h2><a class="section-link" href="https://scholar.google.com/citations?user=QoKlMzMAAAAJ&amp;hl=en">Google Scholar ↗</a></div>
        <article class="publication"><div class="year">2026</div><div><p class="kicker">Preprint · arXiv:2610.00667</p><h2><a href="https://arxiv.org/abs/2610.00667">Operator-language Feynman rules for driven-dissipative quantum systems: from mean field to non-Gaussian photon correlations</a></h2><p class="authors">Peter Ehlers, <strong>Phi Hung Nguyen</strong>, and Daniel Soh</p><p>Feynman rules for Lindblad dynamics in the operator language of quantum optics. The framework uses perturbation theory around solvable generators to calculate non-Gaussian photon correlations and photon-counting cumulants in driven, dissipative systems.</p></div></article>
        <article class="publication"><div class="year">2026</div><div><p class="kicker">Preprint · arXiv:2608.10382</p><h2><a href="https://arxiv.org/abs/2608.10382">A Single Atom in Front of a Mirror is a Universal Reservoir Computer</a></h2><p class="authors">Peter J. Ehlers, <strong>Phi Hung Nguyen</strong>, Kanu Sinha, Noelle Daigle, Travis W. Sawyer, Hendra I. Nurdin, and Daniel Soh</p><p>A minimal atom–mirror system as a reservoir for temporal computation. The work connects physical memory, accessible modes, and measurement settings to universal approximation under specified operating conditions.</p></div></article>
        <article class="publication"><div class="year">2026</div><div><p class="kicker">Conference proceeding · CLEO · JTU.96</p><h2><a href="https://doi.org/10.1364/CLEO_AT.2026.JTU.96">The Minimalistic Non-Markovian Quantum Reservoir Computer for Real-world Applications</a></h2><p class="authors"><strong>Phi Hung Nguyen</strong>, Peter J. Ehlers, Kanu Sinha, and Daniel Soh</p><p>Using an atom in front of a mirror for reservoir computing, with the sampling interval and atom–mirror distance as handles on the dynamics and performance.</p><div class="actions"><a class="section-link" href="https://doi.org/10.1364/CLEO_AT.2026.JTU.96">Publisher record ↗</a></div></div></article></section>
        <section class="section"><h2>Questions that connect the work</h2><div class="research-themes"><article><h3>Physical memory</h3><p>How can delayed feedback turn a small quantum system into a richer dynamical resource?</p><a class="section-link" href="/notes/open-quantum-systems/">Open quantum systems →</a></article><article><h3>Useful dynamics</h3><p>Which features of a physical response matter for learning from a time-dependent signal?</p><a class="section-link" href="/notes/learning-and-reservoirs/">Learning & reservoirs →</a></article><article><h3>What we measure</h3><p>How do measurement choices reveal the information available in a quantum system?</p><a class="section-link" href="/notes/quantum-information/">Quantum information →</a></article></div></section>'''

    if embedded:
        content = content.replace('<header class="page-intro">', '<header class="page-intro" id="research">', 1).replace('<h1>', '<h2>', 1).replace('</h1>', '</h2>', 1)
    return content


def about():
    return f'''<div class="about-header"><header class="page-intro"><p class="eyebrow">About</p><h1>Phi Hung Nguyen</h1><p class="lead">PhD student in Optical Sciences at the University of Arizona, and a member of the Soh Lab.</p></header>
        <aside class="profile-links"><p class="kicker">Elsewhere</p><a href="{escape(CATALOG['scholar'], quote=True)}">Google Scholar ↗</a><a href="{escape(CATALOG['linkedin'], quote=True)}">LinkedIn ↗</a><a href="https://optics.arizona.edu/person/phi-hung-nguyen">University profile ↗</a><a href="https://wp.optics.arizona.edu/danielsoh/people/">Soh Lab ↗</a></aside></div>{research(embedded=True)}'''


def viewer(name, url, names=(), metadata=None):
    from chapter_content import viewer as chapter_viewer
    return chapter_viewer(name, url, names, metadata)


def pages(names, documents=()):
    yield '', 'Physics, with intuition', home(names)
    yield 'notes/', 'Notes', notes(names, documents)
    import review_content
    yield 'notes/review/', 'Daily review', review_content.page()
    yield 'review/', 'Daily review', review_content.page()
    yield 'research/', 'About', about()
    yield 'about/', 'About', about()
    for topic in TOPICS:
        yield 'notes/' + topic['slug'] + '/', topic['title'], topic_page(topic, names)
