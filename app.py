import json, mimetypes, os
from html import escape
from pathlib import Path
from urllib.parse import quote
from wsgiref.simple_server import make_server
from markdown_it import MarkdownIt

ROOT=Path(os.getenv("MD_ROOT","content")).resolve()
PARSER=MarkdownIt("js-default")
IMAGES={".png",".jpg",".jpeg",".gif",".webp",".avif",".ico"}
MAX_TEXT=2*1024*1024
MAX_IMAGE=10*1024*1024
CSS=""":root{color-scheme:light dark;font-family:system-ui,sans-serif;line-height:1.65}body{max-width:900px;margin:0 auto;padding:32px 24px;background:light-dark(#faf9f6,#151719);color:light-dark(#202627,#e4e8e9)}a{color:light-dark(#17626b,#7fd7dd);text-underline-offset:3px}nav{display:flex;gap:20px;padding-bottom:18px;border-bottom:1px solid #8885;font-size:14px}main{padding-top:22px}h1,h2,h3{line-height:1.25}pre{overflow:auto;background:light-dark(#eef0ed,#22272a);padding:18px;border-radius:8px}code{font-family:ui-monospace,monospace}blockquote{border-left:3px solid #47a3ac;margin-left:0;padding-left:20px;color:light-dark(#566366,#b2bfc2)}table{border-collapse:collapse;display:block;overflow:auto}th,td{border:1px solid #8885;padding:8px 14px}img{max-width:100%;height:auto}li{margin:6px 0}.files{list-style:none;padding:0}.files li{padding:12px 0;border-bottom:1px solid #8883}.muted{color:light-dark(#617073,#a9b8bb);font-size:14px}hr{border:0;border-top:1px solid #8885}"""

def resolve(name):
    parts=name.split("/")
    if not name or "\\" in name or "\x00" in name or any(p.startswith(".") or not p for p in parts):
        raise FileNotFoundError
    file=(ROOT/name).resolve()
    if not file.is_relative_to(ROOT) or not file.is_file():
        raise FileNotFoundError
    return file

def files():
    return sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
        if p.suffix.lower()==".md" and p.is_file() and p.resolve().is_relative_to(ROOT)
        and not any(x.startswith(".") for x in p.relative_to(ROOT).parts))

def page(title,body,raw=None):
    download=f'<a href="/raw/{quote(raw,safe="/")}">Raw Markdown</a>' if raw else ''
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · Markdown server</title><link rel="stylesheet" href="/style.css"></head><body><nav><a href="/">Markdown server</a>{download}</nav><main>{body}</main></body></html>'.encode()

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
        elif path=="/":
            names=files()
            links=''.join(f'<li><a href="/docs/{quote(n,safe="/")}">{escape(n)}</a></li>' for n in names)
            body=page("Files",f'<h1>Your Markdown files</h1><p class="muted">{len(names)} documents</p><ul class="files">{links}</ul>' if names else '<h1>Your Markdown files</h1><p>Add .md files to the content folder to get started.</p>')
        elif path.startswith(("/docs/","/raw/")):
            raw=path.startswith("/raw/"); name=path.split("/",2)[2]; file=resolve(name)
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
    headers=[("Content-Type",kind),("Content-Length",str(len(body))),("X-Content-Type-Options","nosniff"),("Cache-Control","no-cache"),("Content-Security-Policy","default-src 'none'; style-src 'self'; img-src 'self' https: data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")]+extra
    start_response(status,headers)
    return [] if method=="HEAD" else [body]

if __name__=="__main__":
    port=int(os.getenv("PORT","8000"))
    with make_server("127.0.0.1",port,application) as server:
        print(f"Markdown server: http://127.0.0.1:{port} (content: {ROOT})",flush=True)
        server.serve_forever()
