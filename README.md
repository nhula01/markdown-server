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

A Codex scheduled task exports the Obsidian
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

## Personal academic website

The site has Home, Notes, Research, and About pages. It uses an original paper-and-ink design: a faint square grid inspired by the
handwritten reMarkable PDFs, graphite text, and blue calligraphic capitals.
Pinyon Script is served locally, with its SIL Open Font License included in
`assets/fonts/OFL.txt`. The capital letters are selectable text.

`site/catalog.json` controls the nine topic titles, descriptions, reading
outlines, prerequisites, and notebook assignments. Exact notebook titles are
matched to topics without moving PDFs, so existing reader and download URLs
remain stable. New unmatched exports appear under **Notebook desk** until
assigned. PDFs under a directory matching a topic slug also join that topic.

`writing/<topic>/` contains planning folders for future notes. These folders
are not published. The MyBrain vault was used to plan the topic structure;
the builder never reads or copies that vault. Only curated descriptions and
existing official exports appear on the site. Planned pages are explicitly
marked until notebooks exist.

`reading_guides` in the catalog contains verbatim sections from
MyBrain's `Optimum.md`. Titles show these guides on hover or keyboard focus;
the **Reading guide** disclosure also works on touch screens. Empty source
sections are marked as awaiting a guide. Topic notebook order follows the
catalog's notebook assignments.
Run `scripts/update-reading-guides.py /Users/nph/Documents/MyBrain/Optimum.md`
with the project Python to refresh them. Preserve the author's exact wording
for all current and future previews, including equations and unfinished text.
Preview equations use locally hosted KaTeX 0.19.0 (MIT license included).
Inline `$...$` and `\(...\)`, plus display `$$...$$` and `\[...\]`, are
typeset in both hover previews and expanded guides. The catalog retains the
exact source text; rendering changes only its browser presentation.

Inside reMarkable, `Obsidian/Fields & waves` holds Electromagnetic Pieces and
Maxwell's Equations; `Obsidian/Light & matter` holds Crystal, Electrons in
Crystals, Oscillator Model, and Linear Light. Other notebooks remain at the
Obsidian root. The export task visits each folder individually because folder
selection cannot export PDFs. Put each folder's official exports in a separate
subdirectory of one fresh export directory. The importer reads these recursively,
rejects duplicate filenames before changing the library, and keeps the existing
flat PDF URLs stable.

Edit `site_content.py` for page copy and selected research, and
`assets/style.css` for presentation. Research entries link to their public
arXiv and publisher records; Scholar and LinkedIn link to the supplied profiles.
The server and Pages build share the same page templates. Daily PDF publishing
continues to trigger the site build without changing the official exports.

## Handwritten chapters

Each existing notebook reader URL now opens a chapter page. The original PDF
is a separate object inside that page, rendered in the browser using locally
hosted Mozilla PDF.js 6.3.289. Its Apache license and supporting assets are in
`assets/vendor/`. Contents links select actual PDF pages; page controls and
zoom work independently of the chapter’s written context. Open PDF always
links to the unchanged original export.

Chapter pages keep the verbatim Optimum reading guide and key connections
around the handwritten source. `site/chapters.json` holds each question, tags, contents
page numbers, prerequisites, onward connections, and recurring ideas.
Connections can target `note:<exact title>`, `concept:<slug>`, `topic:<slug>`,
or `page:research`. Incoming links are generated from the same graph. Planned
concept pages clearly indicate that their dedicated handwritten chapter is
still to come and link back to the related existing notebooks.

Page counts are read directly from the PDFs. “PDF updated” is the most recent
Git change to that file, not the export time or an inferred notebook edit date.
Pages checkout includes history so those dates remain accurate after deployment.
Only H1 titles receive calligraphic initials; navigation and other headings
use ordinary type.

The Search button, Cmd+K, or Ctrl+K opens a keyboard-accessible search panel.
The static build regenerates `search-index.json` from
questions, tags, verbatim Optimum guides, concepts, topic outlines, research,
and public written documents. The local server exposes the same index.
All search happens in the browser; it does not send queries to a service.

## Curated leads

The homepage’s Follow a thread explorer searches published notes using titles,
questions, tags, and Optimum text. Selecting a note reveals curated questions;
selecting a question reveals an ordered trail with published and planned steps.
Every chapter offers the same leads, starting at its position in the trail.
Selections can be shared through the homepage’s `start` and `lead` parameters.

Edit **Follow a thread.md** in the MyBrain Obsidian vault. Each `##` heading is
a question, followed by two or more numbered `[[Exact notebook title]]` links.
Reorder or add links to change the trail; add another question to create a lead.
Titles automatically resolve to handwritten chapters when a matching PDF is
published, otherwise to a planned concept page (or the notebook outline).
Questions apply to each published note before the final step of the trail.

The scheduled PDF publishing script also imports these edits. For a manual
refresh, run `python3 scripts/update-leads.py` then build/publish as usual. Only
question headings and numbered links are imported into `site/leads.md`; other
private vault content is excluded. An invalid trail aborts before overwriting
the existing public copy. `LEADS_SOURCE` overrides the vault path for sync.

## Shared daily notebook review

`/review/` offers the same daily notebooks to everyone, without accounts or a
progress backend. Each UTC date selects one focus notebook and a return to a
notebook from three days earlier. The rotation covers all available PDFs and
alternates topics where possible. Small collections use a distinct fallback.
The next seven daily selections are visible on the page. Ratings never change
the shared calendar; missed recall allows one extra attempt in the session.

Only today's completion checkmarks are saved in localStorage. The sample
`/review/?demo=1` does not save checkmarks. Recall text is neither saved nor
transmitted. PDFs are unchanged and Optimum guides remain verbatim.

The website no longer loads Supabase or sends account/progress requests.
Previously created Supabase resources remain in the user's project; the
website does not use them or delete their data.

```sh
node --test tests/review-schedule.test.mjs
python -m unittest discover -s tests -v
```

## Optional reading music

A still play/pause button appears in the corner, including immersive reading.
Playback starts off at a quiet 20% level and loads music only after Play. A small
next-song button skips through Satie's Gymnopédie No. 1, Beethoven's Moonlight
Sonata (first movement), and Chopin's Prelude Op. 28 No. 17. The playlist advances
and repeats automatically. Sources, performers, and licences are in
`assets/audio/CREDITS.md`; Musopen is credited in the page footer.

After Play, the first section change creates a persistent audio shell around a
same-origin reading frame, keeping the current review untouched until navigation. Normal section navigation, search, PDF controls, and browser
history work inside the frame while the same audio element keeps playing. The
visible URL and theme follow the reading page. Embedded pages omit their own
player, preventing duplicate playback. Reloading or leaving the website stops
music. No external music service, account, or tracking is used.

## Physics in the margins

On screens at least 1540px wide, ten foundational equations alternate quietly
between the empty outer margins. Each is typeset with local KaTeX and scales to
fit outside the 1200px paper. The decoration never intercepts clicks, and is
hidden on smaller screens, during immersive reading, and for reduced-motion
preferences. Edit the labelled equations in `assets/margin-equations.js`.
