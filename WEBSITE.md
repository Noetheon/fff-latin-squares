# Project Website

The [public website](https://noetheon.github.io/fff-latin-squares/) is a static
English-language interface to the same research dossier. It works by opening
`index.html` locally or through GitHub Pages, with no build step, JavaScript,
third-party fonts, external scripts or analytics.

## Design Revision: 19 September 2026

- Responsive navigation and direct access to both PDFs from the opening section.
- Two document entries with complete-page previews, edition scope and downloads.
- Separate evidence classes for written arguments, finite computations and the
  open global conjecture.
- Visible AI-origin and non-peer-reviewed status, plus native keyboard-operable
  disclosure sections for accountability, archive scope and rights.
- A skip link, visible focus states and reduced-motion support.

The source is `index.html` and `assets/site.css`. Page previews are rendered from
the existing public PDFs, without modifying, cropping or rewriting the papers.
The new image provenance is in
[`verification/site-preview-sources.json`](verification/site-preview-sources.json).
The compact cover preview is retained byte-for-byte from the initial release.

No scientific claim, PDF, frozen computation, projection record or historical
verification report is changed by this design revision. The original
`v0.1.0-dossier` release still identifies its original payload, not this subsequent
website revision. The updated main-branch payload has its own
`PUBLIC_MANIFEST.sha256`.

## Checks

The default standard-library checks remain:

```sh
python3 -B tools/verify_public_release.py
python3 -B -m unittest discover -s tests -v
python3 -B tools/check_theorem_records.py --output .audit/website-theorem-records
git diff --check
```

The website tests verify relative resources and anchors, PDF read/download links,
English document semantics, absence of an external runtime, and retained evidence
boundaries. Browser QA additionally checks eight widths from 320 to 1920 pixels,
overflow, rendered images, navigation, keyboard disclosure controls, the skip
link and operation with JavaScript disabled. The browser observations are saved
separately in
[`verification/site-redesign-checks.json`](verification/site-redesign-checks.json).
This is a bounded browser check, not a WCAG conformance certification or a new
mathematical verification.

Optional browser QA requires externally installed Playwright and Chrome:

```sh
node tools/check_site.cjs .audit/site
```

`PLAYWRIGHT_MODULE` may point to an external Playwright installation, and
`BROWSER_CHANNEL` may select a locally installed Chromium channel. Screenshots and
fresh reports stay under `.audit/`. A URL can be supplied as the second argument
to test the deployed page. The tool never reads a personal browser profile.

Re-rendering only the three new previews requires `pypdfium2` (and its Pillow
rendering dependency) outside the repository:

```sh
python3 -B tools/render_site_previews.py
```

The renderer checks the two input PDF hashes before rendering. Rendering
dependencies are optional and not part of the standard-library audit contract.
Regenerate the public manifest and rerun all checks before publishing changed
assets. Retain neutral publication commit identities and never import the
private project's Git history or correspondence.
