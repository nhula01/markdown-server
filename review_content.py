"""Public notebook review cards; guides remain verbatim and PDFs untouched."""
from pathlib import Path
import chapter_content
import site_content
from urllib.parse import quote
from urllib.parse import urlparse
import json
import re


def auth_config():
    """Whitelist public configuration; fail builds before packaging any secret."""
    config = json.loads((Path(__file__).parent / 'site/auth.json').read_text())
    if set(config) != {'url', 'publishableKey'}:
        raise ValueError('Auth config may contain only URL and public publishableKey')
    if config == {'url': '', 'publishableKey': ''}:
        return config
    url = urlparse(config['url'])
    if (url.scheme != 'https' or not re.fullmatch(r'[a-z0-9-]+\.supabase\.co', url.netloc)
            or url.path not in ('', '/') or url.query or url.fragment
            or not re.fullmatch(r'sb_publishable_[A-Za-z0-9_-]+', config['publishableKey'])):
        raise ValueError('Use the HTTPS Supabase project URL and public publishable key; never a secret key')
    return config


def index(names):
    cards = []
    for name in names:
        stem = Path(name).stem
        topic = site_content.topic_for(name)
        chapter = chapter_content.CHAPTERS.get(stem, {})
        question = chapter.get('question', '')
        if not question.endswith('?'):
            question = f'What is the central physical idea in {stem}?'
        cards.append({'id': name, 'title': stem, 'topic': topic['title'] if topic else 'Other notes',
                      'question': question, 'url': chapter_content.chapter_url(name),
                      'pdf': '/pdfs/' + quote(name, safe='/'),
                      'guide': site_content.CATALOG.get('reading_guides', {}).get(stem, ''),
                      'contents': chapter.get('contents', [])})
    return cards


def page():
    return '''<header class="page-intro"><p class="eyebrow">A little, every day</p><h1>Return to an idea.</h1><p class="lead">Close the notebook for a moment. What can you bring back from memory?</p><p class="muted">Recall first. Check your handwriting. Leave with one clearer connection.</p></header>
    <details class="review-account"><summary>Save progress across devices · optional account</summary><p>Review as a guest, or create an account with email and password. A new account starts a separate schedule; your guest schedule stays on this device.</p><p class="review-small">Email registration is currently limited while setup is completed. Guest reviews are available to everyone.</p><form data-account-form><fieldset data-account-fields disabled><legend>Sign in or create an account</legend><label for="account-email">Email</label><input id="account-email" type="email" autocomplete="email" required maxlength="254"><label for="account-password">Password · at least 12 characters</label><input id="account-password" type="password" autocomplete="current-password" minlength="12" required maxlength="128"><div class="account-actions"><button type="submit" data-account-action="login">Sign in</button><button type="submit" data-account-action="signup">Create account</button><button type="button" data-account-reset>Forgot password?</button></div></fieldset></form><form data-account-recovery hidden><label for="account-new-password">New password · at least 12 characters</label><input id="account-new-password" type="password" autocomplete="new-password" minlength="12" required maxlength="128"><button type="submit">Update password</button></form><div class="account-actions"><button type="button" data-account-sync hidden>Sync again</button><button type="button" data-account-logout hidden>Sign out</button></div><p data-account-status role="status" aria-live="polite">Preparing account options…</p><p class="review-small">Accounts are managed by Supabase. Only notebook identifiers, recall ratings, and review dates sync. Typed recall answers are never stored or sent. Your session stays signed in on this browser until you sign out.</p></details>
    <section class="review-dashboard" aria-label="Daily review"><div class="review-stat"><strong data-review-due>—</strong><span>notebooks due</span></div><div class="review-stat"><strong data-review-today>—</strong><span>reviewed today</span></div><div class="review-stat"><strong data-review-next>—</strong><span>next review</span></div></section>
    <section id="daily-review" class="review-workspace"><div class="review-setup"><div><p class="kicker">Your daily practice</p><h2>Ten quiet minutes.</h2><p>Explain the physical picture, sketch a diagram, and connect it to another idea. Then check what you missed.</p></div><div><label for="review-topic">Choose a collection</label><select id="review-topic"><option value="">All topics</option></select><button type="button" class="button" data-review-start disabled>Start today’s review →</button><a class="review-demo-link" href="/review/?demo=1">Try a sample without saving progress ↗</a></div></div><p data-review-status role="status" aria-live="polite">Preparing your notebooks…</p>
    <article class="review-card" hidden aria-labelledby="review-title"><div class="review-card-top"><span data-review-count class="kicker"></span><span data-review-category class="kicker"></span></div><p class="review-source" data-review-notebook></p><h2 id="review-title"></h2><ol class="review-recall"><li>Explain the physical picture without looking.</li><li>Sketch the system or one equation, and say what it means.</li><li>Connect it to another concept you know.</li></ol><label for="review-response">Your recall · optional</label><textarea id="review-response" rows="3" placeholder="A few words, a sketch on paper, or explain it aloud…"></textarea><p class="review-small">Your response stays here during this session; it is not stored or sent.</p><button type="button" class="button" data-review-reveal>Check the notebook →</button>
    <section class="review-check" hidden><div class="section-head"><h3>Compare with the handwritten source</h3><a data-review-open target="_blank" rel="noopener">Open chapter ↗</a></div><div class="review-pdf-controls"><button type="button" data-review-prev aria-label="Previous handwritten page">←</button><span data-review-page role="status"></span><button type="button" data-review-forward aria-label="Next handwritten page">→</button><a data-review-pdf target="_blank" rel="noopener">Open original PDF ↗</a></div><div class="review-pdf-surface"><canvas role="img" aria-label="Handwritten notebook page"></canvas></div><details class="review-guide"><summary>Starting point · verbatim from Optimum</summary><div class="guide-verbatim" data-review-guide></div></details><p class="review-reflect">What did you miss? Correct one detail, then explain it once more without looking.</p><fieldset class="review-ratings"><legend>How well could you recall it?</legend><button type="button" data-review-grade="again"><strong>Couldn’t recall</strong><span data-interval="again"></span></button><button type="button" data-review-grade="shaky"><strong>Needed a hint</strong><span data-interval="shaky"></span></button><button type="button" data-review-grade="good"><strong>Recalled it</strong><span data-interval="good"></span></button><button type="button" data-review-grade="easy"><strong>Could teach it</strong><span data-interval="easy"></span></button></fieldset></section></article>
    <section class="review-finished" hidden><p class="kicker">A good place to stop</p><h2>Let the ideas settle.</h2><p data-review-finished></p><p>Come back tomorrow. If nothing is due, explore a new note or follow a connection.</p><a class="button" href="/notes/">Browse the notebook →</a></section></section>
    <details class="review-method"><summary>How this practice works</summary><div class="prose"><p>Attempting to retrieve an idea before checking the source makes gaps visible. Returning on separate days gives you another chance to retrieve it after some forgetting. <a href="https://www.nature.com/articles/s44159-022-00089-1">Read about spacing and retrieval practice ↗</a></p><p>A session includes up to five notebooks, with due reviews first and at most two new notebooks per day. Topics alternate where possible. “Couldn’t recall” schedules tomorrow and, when there is room, one retry at the end of the session; “Needed a hint” schedules tomorrow. Successful recall starts at three days and grows through 7, 14, 30, and 60 days. “Could teach it” starts at seven days and grows faster, up to 90 days. These intervals are a simple scheduling rule, not a measurement of your memory.</p><p>Guest schedules are saved in this browser. Optional accounts sync review ratings and dates through Supabase when connected. You can sign in on another device to continue your account schedule. Offline reviews wait on the device until they sync. Guest progress is kept separate from account progress. Notebook text and Optimum guides remain unchanged.</p></div></details><noscript><p>Daily review needs JavaScript. You can still <a href="/notes/">browse and read the notebooks</a>.</p></noscript>'''
