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

Export PDFs to `pdfs/` in this checkout. The home page automatically lists them;
`/notebooks/Open%20Systems/Input%20Output.pdf` embeds the notebook and
`/pdfs/Open%20Systems/Input%20Output.pdf` serves its original PDF. Refreshing
shows updated exports at the same URL. `PDF_ROOT` overrides the PDF directory.
PDFs are limited to 100 MiB. Only PDFs intended for publication belong here.
Docker builds include `pdfs/`; rebuild/redeploy the image after each Git push,
or mount a PDF directory at `/app/pdfs` for live filesystem updates.

On your Mac:

```sh
brew tap jeffsteinbok/remarkablesync
brew install remarkablesync
RemarkableSync config
```

The Homebrew formula uses `RemarkableSync` (capital R); other installations may
use `reMarkableSync`. Choose Cloud in the wizard and complete pairing yourself.
Set the PDF directory to this checkout's `pdfs/`, keep backups outside the repo,
and disable Markdown/OCR export. Then run the default PDF-only pipeline:

```sh
RemarkableSync sync --cloud
```

Edit one notebook on the tablet, allow Cloud sync, rerun, and verify its PDF
changes with `git status --short -- pdfs`. Open the PDF to confirm handwriting.
Only after this succeeds, run `zsh scripts/sync-remarkable.zsh` to sync, commit
PDF changes, and push. It preserves unrelated staged files and retries pushes.
Git credentials must work without a prompt for scheduled runs.

For daily sync at 18:00 local time, edit the absolute script/log paths in
`scripts/com.nhula01.remarkable-sync.plist.example`, copy it to
`~/Library/LaunchAgents/com.nhula01.remarkable-sync.plist`, then load it with
`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nhula01.remarkable-sync.plist`.
The example is deliberately inactive until the changed-PDF test succeeds.
The Mac must be available to run the job. Remove the job with
`launchctl bootout gui/$(id -u)/com.nhula01.remarkable-sync`.

### Free hosting with GitHub Pages

In the repo's **Settings → Pages**, choose **GitHub Actions** as the source.
The `Publish GitHub Pages` workflow builds and publishes the library on every
push to `main`. The expected address is https://nhula01.github.io/markdown-server/.
PDF exports trigger the same deployment automatically, without running a Python
server online. Static notebook URLs include the `/markdown-server/` prefix.

Preview the static build with `.venv/bin/python scripts/build-pages.py`;
the generated `_site/` directory is ignored by Git. The Flask-free Python server
and Docker deployment remain available as alternatives.
