# Discovery and Review Entry Points - 20 September 2026

## Delivered

- Repository topics: `latin-squares`, `combinatorics`, `quasigroups`,
  `computational-mathematics`, `reproducible-research`; confirmed through GitHub.
- [A bounded Python example](../examples/README.md): the explicit order-8 loop
  validates as FFF over all 84 line pairs; the order-3 negative control is TTT
  over all 9 line pairs. Complete expected outputs and input hashes are included.
- [Three focused review tasks](../REVIEW_TASKS.md), also published in
  [Discussion #1](https://github.com/Noetheon/fff-latin-squares/discussions/1).
  GitHub's discussion UI confirmed the pinned state with "Edit pinned discussion"
  and "Unpin discussion" controls.
- A 1280 x 640, 95,604-byte [social preview](../assets/social-preview.png),
  built from an editable HTML/CSS layout and the unaltered public PDF cover.
  The website publishes Open Graph and Twitter-card image metadata.
- An explicitly unpublished Reddit draft in
  [community outreach](../COMMUNITY_OUTREACH.md). No external forum post or
  moderator message was sent. AI-written text is not offered for venues that
  prohibit it.

## Outstanding Repository Setting

The image and website metadata are published, but the separate GitHub repository
social-preview upload is **not complete**. The browser's direct file chooser
was denied and the native picker could not be reliably controlled. No browser
permission was broadened. GitHub's API still reported
`usesCustomOpenGraphImage=false` at this check.

To finish, select `assets/social-preview.png` under the repository's
Settings -> General -> Social preview. Do not confuse website Open Graph
metadata with this independent GitHub setting. External preview caches may lag.

## Checks Actually Run

- `python3 -B -m unittest discover -s tests -v`: 16 tests passed.
- `python3 -B tools/verify_public_release.py`: public-manifest verification passed.
- `python3 -B tools/verify_public_release.py --pdf-metadata`: passed with the
  external Poppler tools on PATH; both author fields are empty, with no embedded
  files or PDF JavaScript. An initial false positive from a newline-crossing
  author regex was fixed and covered for LF/CRLF and empty/nonempty authors.
- `python3 -B tools/check_theorem_records.py --output .audit/outreach-theorem-records`:
  all 13 numerical/status record checks passed. Historical package-layout checks
  remain incomplete by export design, not silently reclassified as passing.
- 29 relative documentation destinations checked, none missing.
- Public text checked for the maintainer's personal-name variants, machine-local
  user paths and unintended cross-platform identity disclosure: no matches.
- New payload checked for raw archives, PDF additions, caches, binaries and logs:
  none staged. The two PDFs, manuscripts, proof notes, frozen runs and
  `PUBLIC_PROJECTION.json` remain unchanged.
- `git diff --check` and `git diff --cached --check`: passed.
- [GitHub CI](https://github.com/Noetheon/fff-latin-squares/actions/runs/35480646856)
  and [Pages deployment](https://github.com/Noetheon/fff-latin-squares/actions/runs/35480646001)
  passed for implementation commit `dd36b43de313061f0a3ffbf5b9f5ce78c16564b8`.

## Browser Observations

The published page was inspected at 1470 x 780 and 390 x 844 pixels: meaningful
content, loaded page-preview images, no horizontal overflow or detected clipped
headings/paragraphs/buttons/navigation. Desktop console inspection returned no
warnings or errors. The example link, review links and AI/review boundaries
were visible. A subsequent example-link navigation check was interrupted by a
browser-control timeout and is not recorded as a passed interaction test.
This is bounded visual QA, not accessibility certification.

No theorem status changed, no large mathematical search was launched, and no
independent expert review or complete public artifact archive is asserted.
