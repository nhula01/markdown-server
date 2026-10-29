# Notebook previews

The user requires notebook previews and reading-guide popups to copy the
corresponding section of `/Users/nph/Documents/MyBrain/Optimum.md` verbatim.
This applies to current and future notebooks. Do not rewrite, summarize,
correct grammar, change equations, or invent starting points or connections.
Preserve all section text; an empty section has no preview yet.
LaTeX delimiters are rendered by locally hosted KaTeX for display only. Keep
the original LaTeX in the catalog and render both popups and expanded guides.

Refresh the public copy using:

```sh
.venv/bin/python scripts/update-reading-guides.py /Users/nph/Documents/MyBrain/Optimum.md
```

The source heading `Crystals` maps to `Crystal`, and `Lorentz Oscilator`
maps to `Oscillator Model`. Keep any future title aliases explicit. The website
builder reads only the public catalog, not the private vault. Do not publish
unrelated vault files.

# Chapter pages and connections

Chapter pages surround the handwritten PDFs with questions, contents, the
verbatim Optimum reading guide, and explicit connections. The user removed
the Physical picture and Key idea sections; do not add them back.
Edit `site/chapters.json` for tags, verified PDF contents page numbers, and
the connection graph. Never rewrite the Optimum previews and guides.
Unwritten connection destinations must remain clearly marked as planned.
Use PDF page counts and the last PDF Git change for publication metadata.
Keep the original PDF bytes and existing reader/download URLs intact.

Calligraphic initials belong only to page titles, not navigation or every
subheading. Search must index all public tags, questions,
Optimum guides, topic outlines, and research. Do not index the private vault.

# Curated leads

The user authorizes generated question-based reading trails and edits them in
`/Users/nph/Documents/MyBrain/Follow a thread.md`. The public `site/leads.md`
is refreshed by `scripts/update-leads.py`; only `##` questions and numbered
`[[Exact notebook title]]` links are imported. Preserve the user’s edits. Do not
import other vault prose. Published PDFs automatically replace planned steps.
Every chapter links into the same homepage explorer. Keep the verbatim Optimum
guides separate; do not restore Physical picture or Key idea sections.


# Scheduled chapter context and collected book

The weekly official-export routine must also review chapter context for every new
or substantively changed notebook: verified contents page numbers, Key connections,
Follow a lead, and any handwritten Activator. Read the authorized PDF first.
Transcribe an activator verbatim into `site/chapters.json` as
`"activator": {"text": "exact source wording", "page": 1}` with its actual page.
Do not invent an activator for a note that has none. Keep Optimum guides separate
and verbatim. Curate connections and question leads from the notebook's actual
content; preserve the user's edits. Add generated leads to the editable
`/Users/nph/Documents/MyBrain/Follow a thread.md` and refresh `site/leads.md`.
Commit reviewed chapter/catalog/art files in a scoped context commit before
running the PDF publishing script. Never include unrelated changes.

`book_content.py` assembles only published notebooks assigned to the public topic
catalog, in catalog order. Notebook-desk files are excluded until categorized.
The site build automatically regenerates `/book/physics-with-intuition.pdf` with
a cover, contents, topic dividers, and bookmarks. Original notebook pages are
appended without rasterizing; original PDF files remain byte-identical. Verify
book navigation and page destinations after adding or reordering notes.
