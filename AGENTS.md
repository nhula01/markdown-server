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
