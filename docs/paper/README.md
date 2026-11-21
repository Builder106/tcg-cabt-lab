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

- The submission has no open `\todo`. Its reproducibility paragraph says the code, plans, reports and checkpoints will be released after the review period, with no link. After acceptance, replace that sentence with a public link. Hosting an anonymous copy for reviewers was tried and dropped (see the 21 November note below).
- The novelty sentence in the introduction is limited to arXiv and the 2026 competition write-ups (see `novelty-search.md`). Widen the search if time allows.
- Check that no file or metadata names the authors.
- The CoG organizers answered the preprint question by email: papers presented at CoG are published through IEEE, so IEEE's preprint policy applies, and posting a preprint is allowed, with the policy details to be checked. They also said a submission is a single PDF with no attachments, and that a URL in a footnote in the paper body is fine. A footnote link is therefore allowed but not required.
- Preprint rules from the IEEE Author Center conference page (read 18 November 2026): the preprint may go on arXiv, TechRxiv, an institutional repository or a personal site, before or during review. Its first screen must say "This work has been submitted to the IEEE for possible publication. Copyright may be transferred without notice, after which this version may no longer be accessible." After acceptance it must be replaced with the IEEE citation and DOI, or with the accepted version plus the IEEE copyright notice. The submission to CMT stays anonymous and must not link to the preprint.
- IEEE author support replied that Zenodo is not an approved preprint site for papers submitted to IEEE conferences. Use TechRxiv or arXiv for the preprint, or an author or employer site. Zenodo remains fine for a code and data archive, which is not an IEEE article, once review ends.
- Anonymous hosting for reviewers (21 November 2026): OSF no longer creates projects (new projects stopped on 16 November 2026, existing ones go read-only on 19 February 2027). A Zenodo draft preview page embeds the draft owner's full name, affiliation and username in its HTML even when the author field says Anonymous, so it cannot be used for double-blind review. Whatever host is used, scan the full page HTML a stranger receives, not only the API data. The paper promises a release after review instead.
- As of 19 November 2026 TechRxiv has closed submissions during a move to a new platform, with no reopening date. arXiv has needed a personal endorsement for new authors since 21 January 2026, and its content policy lists undergraduate research as typically not accepted. A personal or employer website is allowed by IEEE and has no gatekeeper.
- `refs.bib` page numbers for NeurIPS, NIPS and AAAI papers come only from Semantic Scholar and are left out. Add them from the proceedings if the template needs them.
