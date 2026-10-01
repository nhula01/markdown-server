"""Build the document library for GitHub Pages (including project URL prefixes)."""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

parser = argparse.ArgumentParser()
parser.add_argument('--base-path', default='/markdown-server')
parser.add_argument('--output', default='_site')
args = parser.parse_args()
base = args.base_path.rstrip('/')
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
(out / '.nojekyll').touch()
(out / 'style.css').write_text(app.CSS)


def write_page(path, title, body, raw=None):
    target = out / path
    target.parent.mkdir(parents=True, exist_ok=True)
    html = app.page(title, body, raw).decode()
    html = html.replace('href="/style.css"', f'href="{base}/style.css"')
    html = html.replace('href="/"', f'href="{base}/"')
    html = html.replace('href="/raw/', f'href="{base}/raw/')
    target.write_text(html, encoding='utf-8')

links = []
for name in app.files():
    source = app.resolve(name)
    if source.stat().st_size > app.MAX_TEXT:
        raise ValueError(f'Markdown exceeds size limit: {name}')
    target = out / 'raw' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    # Keep .md in the URL so relative Markdown links resolve consistently.
    write_page('docs/' + name + '/index.html', source.stem,
               app.PARSER.render(source.read_text(encoding='utf-8')), name)
    links.append(f'<li><a href="{base}/docs/{quote(name,safe="/")}/">{app.escape(name)}</a></li>')

# Rewrite relative Markdown/image links to match static directory routes.
from posixpath import dirname, normpath
import re
for name in app.files():
    target = out / 'docs' / name / 'index.html'
    html = target.read_text()
    def rewrite(match):
        attr, url = match.groups()
        if url.startswith(('/', '#')) or ':' in url:
            return match.group(0)
        path, marker, fragment = url.partition('#')
        resolved = normpath(dirname(name) + '/' + path) if dirname(name) else normpath(path)
        suffix = '/' if resolved.lower().endswith('.md') else ''
        return f'{attr}="{base}/docs/{resolved}{suffix}{marker}{fragment}"'
    html = re.sub(r'(href|src)="([^"]+)"', rewrite, html)
    target.write_text(html)
for source in app.ROOT.rglob('*'):
    name = source.relative_to(app.ROOT).as_posix()
    if source.suffix.lower() in app.IMAGES:
        source = app.resolve(name)
        target = out / 'docs' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

pdf_links = []
for name in app.pdf_files():
    source = app.resolve(name, app.PDF_ROOT)
    if source.stat().st_size > app.MAX_PDF:
        raise ValueError(f'PDF exceeds size limit: {name}')
    target = out / 'pdfs' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    url = f'{base}/pdfs/{quote(name,safe="/")}?v={version}'
    write_page('notebooks/' + name + '/index.html', source.stem,
               f'<h1>{app.escape(source.stem)}</h1><p><a href="{url}">Open or download PDF</a></p>'
               f'<iframe title="{app.escape(source.stem,quote=True)}" src="{url}" width="100%" height="1100"></iframe>')
    pdf_links.append(f'<li><a href="{base}/notebooks/{quote(name,safe="/")}/">{app.escape(name)}</a></li>')
write_page('index.html', 'My book', '<h1>My book</h1><h2>Handwritten notebooks</h2><ul class="files">'
           + ''.join(pdf_links) + '</ul><h2>Markdown documents</h2><ul class="files">' + ''.join(links) + '</ul>')
print(f'Built {len(links)} Markdown documents and {len(pdf_links)} PDFs in {out}')
