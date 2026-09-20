# Project Website

The [public website](https://noetheon.github.io/fff-latin-squares/) is a static
English-language interface to the same research dossier. It works by opening
`index.html` locally or through GitHub Pages, with no build step, JavaScript,
third-party fonts, external scripts or analytics.

## Discovery Revision: 20 September 2026

The subsequent presentation refinement adds a static, accessible order-8 table
with its illustrative row-pair cycle decomposition, full three-view check counts,
a runnable command, and a table JSON download. A regression test parses the
displayed table from HTML, compares every cell with the frozen example, and
checks its cycles with the existing standard-library validator. The highlighted
pair is explicitly not offered as a substitute for checking all 84 pairs.
The paper entries now distinguish their subjects more clearly, and the review
action opens the pinned discussion directly. No scientific payload is changed.

The repository social-preview image was uploaded and GitHub's API confirmed
`usesCustomOpenGraphImage=true` on 20 September 2026. This completes the separate
repository setting, in addition to the website's Open Graph metadata.

The website and repository entry points now link a small table checker and
[three bounded review tasks](REVIEW_TASKS.md). Open Graph and Twitter-card
metadata refer to `assets/social-preview.png`, a 1280 x 640 PNG under 1 MB.
The image retains the AI-origin and non-peer-reviewed disclosure and uses the
actual compact dossier cover. It introduces no new result or review endorsement.

`assets/social-preview.html` is its editable HTML/CSS source. The optional
renderer is `node tools/render_social_preview.cjs`; it uses externally supplied
Playwright/Chrome and records input/output hashes in
`verification/social-preview-sources.json`. Fonts/browser versions can change
rendered bytes, so byte-identical output across platforms is not promised.
Do not replace the unaltered PDF-cover asset with a generated paper image.

GitHub's repository social preview is a separate repository setting; changing
the website metadata alone does not set it. External sites may cache previews.
The pinned review discussion and repository topics are likewise GitHub metadata,
not claims covered by the mathematical evidence checks.

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
