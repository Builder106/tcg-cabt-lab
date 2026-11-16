# Paper skeleton: IEEE CoG 2027 (Track 01, full paper)

Double-blind, 8 pages including references, IEEE two-column. `ieee/IEEEtran.cls` (V1.8b) and `ieee/IEEEtran.bst` are the unmodified CTAN files, distributed under the LPPL.

## Build

The numbers, table rows and figure data come from the three study reports, so none are typed by hand:

```sh
python3 docs/paper/make_results.py
```

Compile on the VM, which has pdflatex, bibtex and pgfplots (the Mac install lacks pgfplots). From `docs/paper/`:

```sh
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

Rasterize and look at every page before trusting a clean log.

## Files

- `main.tex`: the paper. Open items are `\todo{...}` markers and print in bold.
- `refs.bib`: checked references. Author names use only the forms verified in `related-work.md` and `novelty-search.md`.
- `make_results.py`: writes `generated/`.
- `related-work.md`, `novelty-search.md`: the evidence behind the related-work text.

## Before submission

- Replace every `\todo` (search `main.tex` for `TODO`) and `refs.bib` TODO comments.
- Widen the literature search, then keep, soften or drop the novelty sentence in the introduction.
- Use an anonymized link for the artifact. Check that no file or metadata names the authors.
- Ask the CoG program chairs about the preprint policy under double-blind review (portal opens 27 November 2026).
- Confirm the template against the CoG 2027 author instructions.
