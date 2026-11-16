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

- Replace every `\todo` (search `main.tex` for `TODO`). The remaining one is the anonymized artifact link.
- The novelty sentence in the introduction is limited to arXiv and the 2026 competition write-ups (see `novelty-search.md`). Widen the search if time allows.
- Check that no file or metadata names the authors.
- Ask the CoG program chairs about the preprint policy under double-blind review (portal opens 27 November 2026). The call for papers says double-blind, IEEE two-column, up to 8 pages with references and appendices included, Microsoft CMT, and is silent on preprints.
- `refs.bib` page numbers for NeurIPS, NIPS and AAAI papers come only from Semantic Scholar and are left out. Add them from the proceedings if the template needs them.
