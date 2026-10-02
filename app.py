import hashlib, json, mimetypes, os
import site_content
import chapter_content
import lead_content
import review_content
from html import escape
from pathlib import Path
from urllib.parse import quote
from wsgiref.simple_server import make_server
from markdown_it import MarkdownIt

ROOT=Path(os.getenv("MD_ROOT","content")).resolve()
PARSER=chapter_content.MARKDOWN
IMAGES={".png",".jpg",".jpeg",".gif",".webp",".avif",".ico"}
PDF_ROOT=Path(os.getenv("PDF_ROOT","pdfs")).resolve()
MAX_PDF=100*1024*1024
MAX_TEXT=2*1024*1024
MAX_IMAGE=10*1024*1024
CSS=(Path(__file__).parent/'assets/style.css').read_text()

def resolve(name,root=None):
    root=ROOT if root is None else root
    parts=name.split("/")
    if not name or "\\" in name or "\x00" in name or any(p.startswith(".") or not p for p in parts):
        raise FileNotFoundError
    file=(root/name).resolve()
    if not file.is_relative_to(root) or not file.is_file():
        raise FileNotFoundError
    return file

def files():
    return sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
        if p.suffix.lower()==".md" and p.is_file() and p.resolve().is_relative_to(ROOT)
        and not any(x.startswith(".") for x in p.relative_to(ROOT).parts))

def pdf_files():
    return sorted(p.relative_to(PDF_ROOT).as_posix() for p in PDF_ROOT.rglob("*")
        if p.suffix.lower()==".pdf" and p.is_file() and p.resolve().is_relative_to(PDF_ROOT)
        and not any(x.startswith(".") for x in p.relative_to(PDF_ROOT).parts))

def page(title,body,raw=None,active=None):
    math_assets = ''
    vendor = '/assets/vendor/katex-0.19.0/'
    version = hashlib.sha256((Path(__file__).parent/'assets/math.js').read_bytes()).hexdigest()[:16]
    math_assets = (f'<link rel="stylesheet" href="{vendor}katex.min.css">'
                   f'<script defer src="{vendor}katex.min.js"></script>'
                   f'<script defer src="{vendor}auto-render.min.js"></script>'
                   f'<script defer src="/assets/math.js?v={version}"></script>')
    download=f'<p class="muted"><a href="/raw/{quote(raw,safe="/")}">Raw Markdown</a></p>' if raw else ''
    body=site_content.decorate_headings(body)
    if raw: body=f'<article class="document">{body}{download}</article>'
    navigation=''.join(f'<a href="/{slug}/"'+(' aria-current="page"' if active==slug else '')+f'>{label}</a>' for slug,label in [('notes','Notes'),('review','Review'),('research','Research'),('about','About')])
    theme_version = hashlib.sha256((Path(__file__).parent/'assets/theme.js').read_bytes()).hexdigest()[:16]
    theme_script = f'<script src="/assets/theme.js?v={theme_version}"></script>'
    search_version = hashlib.sha256((Path(__file__).parent/'assets/search.js').read_bytes()).hexdigest()[:16]
    search_script = f'<script defer src="/assets/search.js?v={search_version}"></script>'
    if 'class="section thread-explorer"' in body:
        lead_version = hashlib.sha256((Path(__file__).parent/'assets/leads.js').read_bytes()).hexdigest()[:16]
        search_script += f'<script defer src="/assets/leads.js?v={lead_version}"></script>'
    if 'id="daily-review"' in body:
        review_version = hashlib.sha256((Path(__file__).parent/'assets/review.js').read_bytes() + (Path(__file__).parent/'assets/review-schedule.mjs').read_bytes()).hexdigest()[:16]
        search_script += f'<script type="module" src="/assets/review.js?v={review_version}"></script>'
    if 'class="pdf-reader"' in body:
        pdf_version = hashlib.sha256((Path(__file__).parent/'assets/pdf-reader.js').read_bytes()).hexdigest()[:16]
        search_script += f'<script type="module" src="/assets/pdf-reader.js?v={pdf_version}"></script>'
    margin_version = hashlib.sha256((Path(__file__).parent/'assets/margin-equations.js').read_bytes()).hexdigest()[:16]
    search_script += f'<script defer src="/assets/margin-equations.js?v={margin_version}"></script>'
    music_version = hashlib.sha256((Path(__file__).parent/'assets/music.js').read_bytes()).hexdigest()[:16]
    search_script += f'<script defer src="/assets/music.js?v={music_version}"></script>'
    music_player = '''<aside class="reading-music" data-reading-music aria-label="Reading music"><button type="button" data-music-play aria-label="Play music" title="Play Satie · Gymnopédie No. 1" aria-pressed="false"><span data-music-icon aria-hidden="true">▶</span></button><button type="button" data-music-next aria-label="Next song" title="Next song" hidden>›</button><span class="music-status" data-music-status role="status" aria-live="polite">Off until you press Play.</span><audio preload="none" loop aria-label="Satie: Gymnopédie No. 1"></audio></aside>'''
    search_dialog = '''<dialog id="notebook-search" aria-labelledby="search-title"><div class="search-top"><h2 id="search-title">Search the notebook</h2><button type="button" data-search-close aria-label="Close search">Close <kbd>Esc</kbd></button></div><label class="search-label" for="search-query">Titles, ideas, tags, and reading guides</label><input id="search-query" type="search" autocomplete="off" placeholder="Try Maxwell, resonance, or Lindblad…" aria-controls="search-results"><p id="search-status" role="status" aria-live="polite">Type to search the notebook.</p><ul id="search-results"></ul><p class="search-help">↑ ↓ to move · Enter to open · Esc to close</p></dialog>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Intuitive handwritten notes on optics and quantum physics, and research by Phi Hung Nguyen."><title>{escape(title)} · Phi Hung Nguyen</title><link rel="stylesheet" href="/style.css?v={hashlib.sha256(CSS.encode()).hexdigest()[:16]}">{theme_script}{math_assets}{search_script}</head><body><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="header-inner"><a class="brand" href="/">Phi Hung Nguyen</a><nav aria-label="Main navigation">{navigation}<button class="search-trigger" type="button" data-search-open>Search <kbd>⌘K</kbd></button><select class="theme-select" data-theme-select aria-label="Appearance"><option value="light">Light</option><option value="dark">Dark</option></select></nav></div></header><main id="main">{body}</main><footer><p>Phi Hung Nguyen · Optical Sciences · University of Arizona</p><p><a href="/notes/">A notebook in progress</a> · <a href="{escape(site_content.CATALOG['scholar'],quote=True)}">Scholar ↗</a> · <a href="{escape(site_content.CATALOG['linkedin'],quote=True)}">LinkedIn ↗</a> · <a href="https://musopen.org/" target="_blank" rel="noopener">Music: Musopen ↗</a></p></footer>{search_dialog}{music_player}<div class="margin-equations" data-margin-equations aria-hidden="true"><div class="margin-equation"><span class="margin-equation-label"></span><span class="margin-equation-math"></span><span class="margin-equation-intuition"></span></div><div class="margin-equation"><span class="margin-equation-label"></span><span class="margin-equation-math"></span><span class="margin-equation-intuition"></span></div><div class="margin-equation"><span class="margin-equation-label"></span><span class="margin-equation-math"></span><span class="margin-equation-intuition"></span></div><div class="margin-equation"><span class="margin-equation-label"></span><span class="margin-equation-math"></span><span class="margin-equation-intuition"></span></div></div></body></html>'''.encode()

def application(environ,start_response):
    method=environ.get("REQUEST_METHOD","GET")
    status="200 OK"; kind="text/html; charset=utf-8"; extra=[]
    try:
        path=environ.get("PATH_INFO","/").encode("latin-1").decode("utf-8")
        if method not in {"GET","HEAD"}:
            status="405 Method Not Allowed"; extra=[("Allow","GET, HEAD")]
            body=page("Method not allowed","<h1>Method not allowed</h1>")
        elif path=="/healthz":
            kind="application/json"; body=b'{"status":"ok"}'
        elif path=="/style.css":
            kind="text/css; charset=utf-8"; body=CSS.encode()
        elif path.startswith(("/assets/audio/", "/assets/fonts/", "/assets/vendor/katex-0.19.0/", "/assets/vendor/pdfjs-6.3.289/")) or path in {'/assets/margin-reminders.json', '/assets/margin-equations.js', '/assets/music.js', '/assets/math.js', '/assets/search.js', '/assets/pdf-reader.js', '/assets/leads.js', '/assets/theme.js', '/assets/review.js', '/assets/review-schedule.mjs'}:
            file=resolve(path.removeprefix("/assets/"),Path(__file__).parent/'assets')
            types = {'.mp3': 'audio/mpeg', '.svg': 'image/svg+xml', '.ttf': 'font/ttf', '.woff2': 'font/woff2',
                     '.mjs': 'text/javascript; charset=utf-8', '.bcmap': 'application/octet-stream', '.pfb': 'application/octet-stream', '.wasm': 'application/wasm', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8'}
            if file.suffix not in types: raise FileNotFoundError
            kind=types[file.suffix]
            body=file.read_bytes()
        elif path=="/api/files":
            kind="application/json; charset=utf-8"; body=json.dumps({"files":files()},ensure_ascii=False).encode()
        elif path=="/review-index.json":
            kind="application/json; charset=utf-8"
            body=json.dumps(review_content.index(pdf_files()), ensure_ascii=False).encode()
        elif path=="/leads-index.json":
            kind="application/json; charset=utf-8"
            body=json.dumps(lead_content.index(pdf_files(), chapter_content.search_index(pdf_files(), files(), ROOT)), ensure_ascii=False).encode()
        elif path=="/search-index.json":
            kind="application/json; charset=utf-8"
            body=json.dumps(chapter_content.search_index(pdf_files(), files(), ROOT), ensure_ascii=False).encode()
        elif path.startswith('/connections/'):
            slug=path.removeprefix('/connections/').strip('/')
            if slug not in chapter_content.CONCEPTS: raise FileNotFoundError
            body=page(chapter_content.CONCEPTS[slug]['title'], chapter_content.concept_page(slug, pdf_files()), active='notes')
        elif path.startswith(("/pdfs/","/notebooks/")):
            viewer=path.startswith("/notebooks/"); name=path.split("/",2)[2].removesuffix("/")
            file=resolve(name,PDF_ROOT)
            if file.suffix.lower()!=".pdf": raise FileNotFoundError
            if file.stat().st_size>MAX_PDF: raise OverflowError
            if viewer:
                url="/pdfs/"+quote(name,safe="/")+"?v="+hashlib.sha256(file.read_bytes()).hexdigest()[:16]
                body=page(file.stem,site_content.viewer(name,url,pdf_files(),chapter_content.pdf_metadata(file)),active='notes')
            else:
                kind="application/pdf"; body=file.read_bytes()
        elif path=="/" or path.strip("/") in {"notes","review","research","about"} or path.startswith("/notes/"):
            route=path.strip("/")
            editorial={slug.strip("/"):(title,content) for slug,title,content in site_content.pages(pdf_files(),files())}
            if route not in editorial: raise FileNotFoundError
            title,content=editorial[route]
            body=page(title,content,active=route.split("/")[0])
        elif path.startswith(("/docs/","/raw/")):
            raw=path.startswith("/raw/"); name=path.split("/",2)[2].removesuffix("/"); file=resolve(name)
            if file.suffix.lower()==".md":
                if file.stat().st_size>MAX_TEXT: raise OverflowError
                source=file.read_text(encoding="utf-8")
                if raw:
                    kind="text/plain; charset=utf-8"; body=source.encode()
                else: body=page(file.stem,PARSER.render(source),name)
            elif not raw and file.suffix.lower() in IMAGES:
                if file.stat().st_size>MAX_IMAGE: raise OverflowError
                kind=mimetypes.guess_type(file.name)[0] or "application/octet-stream"; body=file.read_bytes()
            else: raise FileNotFoundError
        else: raise FileNotFoundError
    except (FileNotFoundError,ValueError,UnicodeError):
        status="404 Not Found"; body=page("Not found","<h1>File not found</h1><p><a href=\"/\">Browse available files</a></p>")
    except OverflowError:
        status="413 Content Too Large"; body=page("Too large","<h1>File exceeds the size limit</h1>")
    except OSError:
        status="500 Internal Server Error"; body=page("Unavailable","<h1>Unable to read this file</h1>")
    headers=[("Content-Type",kind),("Content-Length",str(len(body))),("X-Content-Type-Options","nosniff"),("Cache-Control","no-cache"),("Content-Security-Policy","default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'; worker-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https: data:; frame-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'self'; form-action 'none'")]+extra
    start_response(status,headers)
    return [] if method=="HEAD" else [body]

if __name__=="__main__":
    port=int(os.getenv("PORT","8000"))
    with make_server("127.0.0.1",port,application) as server:
        print(f"Markdown server: http://127.0.0.1:{port} (content: {ROOT})",flush=True)
        server.serve_forever()
