"""Build the document library for GitHub Pages (including project URL prefixes)."""
import argparse
import hashlib
import shutil
import sys
import re
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
import site_content
import chapter_content
import lead_content

parser = argparse.ArgumentParser()
parser.add_argument('--base-path', default='/markdown-server')
parser.add_argument('--output', default='_site')
args = parser.parse_args()
base = args.base_path.rstrip('/')
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
(out / '.nojekyll').touch()
# Version HTML navigation as well as CSS/PDF assets. Previously cached pages
# otherwise retain an old stylesheet URL when reached through the menu.
site_version = hashlib.sha256(b''.join(
    (Path(app.__file__).parent / name).read_bytes()
    for name in ['app.py', 'site_content.py', 'chapter_content.py', 'lead_content.py', 'site/leads.md', 'assets/leads.js', 'assets/theme.js', 'assets/style.css', 'assets/math.js', 'assets/search.js', 'assets/pdf-reader.js', 'site/catalog.json', 'site/chapters.json', 'scripts/build-pages.py']
)
  + b''.join(name.encode() + hashlib.sha256(app.resolve(name, root).read_bytes()).digest()
            for root, names in [(app.ROOT, app.files()), (app.PDF_ROOT, app.pdf_files())]
            for name in names)).hexdigest()[:16]
(out / 'style.css').write_text(app.CSS)
shutil.copytree(Path(app.__file__).parent / 'assets/fonts', out / 'assets/fonts', dirs_exist_ok=True)
shutil.copytree(Path(app.__file__).parent / 'assets/vendor', out / 'assets/vendor', dirs_exist_ok=True)
shutil.copyfile(Path(app.__file__).parent / 'assets/math.js', out / 'assets/math.js')
shutil.copyfile(Path(app.__file__).parent / 'assets/search.js', out / 'assets/search.js')
shutil.copyfile(Path(app.__file__).parent / 'assets/leads.js', out / 'assets/leads.js')
shutil.copyfile(Path(app.__file__).parent / 'assets/theme.js', out / 'assets/theme.js')
shutil.copyfile(Path(app.__file__).parent / 'assets/pdf-reader.js', out / 'assets/pdf-reader.js')


def write_page(path, title, body, raw=None):
    target = out / path
    target.parent.mkdir(parents=True, exist_ok=True)
    active = "notes" if path.startswith(("notes/", "notebooks/", "connections/")) else path.split("/")[0]
    html = app.page(title, body, raw, active=active).decode()
    # Prefix all local links, leaving external URLs and fragments intact.
    html = re.sub(r'(href|src|data-pdf-url)="/(?!/)', lambda match: f'{match[1]}="{base}/', html)
    def version_page_link(match):
        url = match[1]
        if url.startswith(base + '/') and url.endswith('/'):
            return f'href="{url}?v={site_version}"'
        return match[0]
    html = re.sub(r'href="([^"]+)"', version_page_link, html)
    target.write_text(html, encoding='utf-8')

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

for name in app.pdf_files():
    source = app.resolve(name, app.PDF_ROOT)
    if source.stat().st_size > app.MAX_PDF:
        raise ValueError(f'PDF exceeds size limit: {name}')
    target = out / 'pdfs' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    url = f'/pdfs/{quote(name,safe="/")}?v={version}'
    write_page('notebooks/' + name + '/index.html', source.stem,
               site_content.viewer(name, url, app.pdf_files(), chapter_content.pdf_metadata(source)))
for route, title, body in site_content.pages(app.pdf_files(), app.files()):
    write_page(route + 'index.html', title, body)
for slug, concept in chapter_content.CONCEPTS.items():
    write_page('connections/' + slug + '/index.html', concept['title'], chapter_content.concept_page(slug, app.pdf_files()))
index = chapter_content.search_index(app.pdf_files(), app.files(), app.ROOT)
leads_index = lead_content.index(app.pdf_files(), index)
for lead in leads_index['leads']:
    for step in lead['steps']:
        step['url'] = base + step['url'] + '?v=' + site_version
for entry in index:
    entry['url'] = base + entry['url'] + '?v=' + site_version
(out / 'leads-index.json').write_text(__import__('json').dumps(leads_index, ensure_ascii=False))
(out / 'search-index.json').write_text(__import__('json').dumps(index, ensure_ascii=False))
print(f'Built {len(app.files())} Markdown documents and {len(app.pdf_files())} PDFs in {out}')
