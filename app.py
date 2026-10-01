import hashlib, json, mimetypes, os
import site_content
from html import escape
from pathlib import Path
from urllib.parse import quote
from wsgiref.simple_server import make_server
from markdown_it import MarkdownIt

ROOT=Path(os.getenv("MD_ROOT","content")).resolve()
PARSER=MarkdownIt("js-default")
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
    download=f'<p class="muted"><a href="/raw/{quote(raw,safe="/")}">Raw Markdown</a></p>' if raw else ''
    if raw: body=f'<article class="document">{body}{download}</article>'
    navigation=''.join(f'<a href="/{slug}/"'+(' aria-current="page"' if active==slug else '')+f'>{label}</a>' for slug,label in [('notes','Notes'),('research','Research'),('about','About')])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Intuitive handwritten notes on optics and quantum physics, and research by Phi Hung Nguyen."><title>{escape(title)} · Phi Hung Nguyen</title><link rel="stylesheet" href="/style.css"></head><body><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="header-inner"><a class="brand" href="/">Phi Hung Nguyen</a><nav aria-label="Main navigation">{navigation}</nav></div></header><main id="main">{body}</main><footer><p>Phi Hung Nguyen · Optical Sciences · University of Arizona</p><p><a href="/notes/">A notebook in progress</a> · <a href="{escape(site_content.CATALOG['scholar'],quote=True)}">Scholar ↗</a> · <a href="{escape(site_content.CATALOG['linkedin'],quote=True)}">LinkedIn ↗</a></p></footer></body></html>'''.encode()

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
        elif path=="/api/files":
            kind="application/json; charset=utf-8"; body=json.dumps({"files":files()},ensure_ascii=False).encode()
        elif path.startswith(("/pdfs/","/notebooks/")):
            viewer=path.startswith("/notebooks/"); name=path.split("/",2)[2].removesuffix("/")
            file=resolve(name,PDF_ROOT)
            if file.suffix.lower()!=".pdf": raise FileNotFoundError
            if file.stat().st_size>MAX_PDF: raise OverflowError
            if viewer:
                url="/pdfs/"+quote(name,safe="/")+"?v="+hashlib.sha256(file.read_bytes()).hexdigest()[:16]
                body=page(file.stem,site_content.viewer(name,url),active='notes')
            else:
                kind="application/pdf"; body=file.read_bytes()
        elif path=="/" or path.strip("/") in {"notes","research","about"} or path.startswith("/notes/"):
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
    headers=[("Content-Type",kind),("Content-Length",str(len(body))),("X-Content-Type-Options","nosniff"),("Cache-Control","no-cache"),("Content-Security-Policy","default-src 'none'; style-src 'self'; img-src 'self' https: data:; frame-src 'self'; base-uri 'none'; frame-ancestors 'self'; form-action 'none'")]+extra
    start_response(status,headers)
    return [] if method=="HEAD" else [body]

if __name__=="__main__":
    port=int(os.getenv("PORT","8000"))
    with make_server("127.0.0.1",port,application) as server:
        print(f"Markdown server: http://127.0.0.1:{port} (content: {ROOT})",flush=True)
        server.serve_forever()
