# Markdown server

A small Python server that hosts `.md` files as readable HTML pages and provides their original Markdown. Includes a document index, nested folders, tables, code blocks, relative links, images, and a JSON file list.

## Run locally

Requires Python 3.12 or newer.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:8000>. Add Markdown documents and images to `content/`; changes appear on refresh without restarting the server. `MD_ROOT` selects another content directory, and `PORT` changes the port.

## Run with Docker

```sh
docker build -t markdown-server .
docker run --rm -p 8000:8000 markdown-server
```

To serve your own folder instead of the bundled examples:

```sh
docker run --rm -p 8000:8000 -v "$PWD/content:/app/content:ro" markdown-server
```

## Deploy

Deploy the Dockerfile on a container host, or install the requirements on a Linux server and start:

```sh
gunicorn --bind "0.0.0.0:${PORT:-8000}" --workers 2 --threads 4 app:application
```

The container listens on `PORT` (default `8000`), with `/healthz` as its health check. Put a TLS reverse proxy in front of it for an HTTPS address. GitHub stores the source code; GitHub Pages serves static sites and does not run this Python server. Creating the repository alone does not make a live server.

## Routes

| Route | Response |
| --- | --- |
| `/` | Document index |
| `/docs/<path>.md` | Rendered HTML |
| `/raw/<path>.md` | Original UTF-8 Markdown |
| `/docs/<image>` | Local PNG, JPEG, GIF, WebP, AVIF, or ICO |
| `/api/files` | JSON object with a `files` array |
| `/healthz` | Health check |

The service is read-only and has no authentication: every document in `MD_ROOT` is available to anyone who can reach the server. Keep that directory limited to documents you intend to serve. Hidden files, paths outside the content directory, and other file types are blocked. Markdown HTML is escaped and unsafe link schemes are rejected by the parser. Markdown files are limited to 2 MiB; images to 10 MiB. LaTeX and Mermaid are displayed as source rather than rendered.

## Verify

```sh
python -m unittest discover -s tests -v
```

## reMarkable handwritten notebooks

Use the official reMarkable desktop app for PDF export. In the Obsidian folder,
select the notebooks, choose Export, keep PDF selected, and save into this
checkout's `pdfs/Obsidian/` directory. Replace the existing files using the same
names to preserve their website URLs. The website serves these PDFs unchanged.

Run `zsh scripts/sync-remarkable.zsh` after export to commit PDF changes and push.
Despite its legacy filename, this script only publishes existing PDFs. It never
calls reMarkableSync or regenerates notebooks, so official exports stay intact.
It preserves unrelated staged work and retries a previously failed push.

The home page automatically lists PDFs; `/notebooks/<path>.pdf` embeds them and
`/pdfs/<path>.pdf` serves their original bytes. `PDF_ROOT` overrides the server's
PDF directory. PDFs are limited to 100 MiB. Only PDFs intended for publication
belong here. Docker builds include `pdfs/`.

A daily Codex scheduled task at 18:00 America/Phoenix exports the Obsidian
folder through the official desktop app and publishes changes. The Mac must be
awake and unlocked, Codex running, and reMarkable signed in and synced.
The task reports meaningful updates or failures and stays quiet when unchanged.

For a manual run, export into a fresh empty temporary folder, then run:

```sh
/opt/homebrew/Cellar/remarkablesync/3.0.0/libexec/bin/python scripts/import-official-pdfs.py /path/to/exports
zsh scripts/sync-remarkable.zsh
```

The import helper requires PyMuPDF. It validates PDFs before replacing files,
compares rendered pages to skip metadata-only changes, and copies changed
exports byte-for-byte. It never deletes missing notebooks. Static viewers use
content hash query parameters so changed PDFs bypass old browser caches.
The launchd example is inactive and only publishes already saved PDFs.
reMarkableSync can still back up raw files; its rendering is not used here.

### Free hosting with GitHub Pages

In the repo's **Settings → Pages**, choose **GitHub Actions** as the source.
The `Publish GitHub Pages` workflow builds and publishes the library on every
push to `main`. The expected address is https://nhula01.github.io/markdown-server/.
PDF exports trigger the same deployment automatically, without running a Python
server online. Static notebook URLs include the `/markdown-server/` prefix.

Preview the static build with `.venv/bin/python scripts/build-pages.py`;
the generated `_site/` directory is ignored by Git. The Flask-free Python server
and Docker deployment remain available as alternatives.
