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
