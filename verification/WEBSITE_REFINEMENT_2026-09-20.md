# Website Refinement: 20 September 2026

Scope: public presentation and bounded website verification only. No paper,
proof note, research result, frozen computation, or original projection record
was changed. This is not expert mathematical review or a new large rerun.

## Delivered

- Refined editorial typography, paper subject lists and responsive spacing.
- An accessible static order-8 example table, its row-0/row-1 cycle
  decomposition, all-view pair counts, checker command and JSON download.
- Regression checks compare the displayed table with the frozen JSON and scan
  all three views. The single displayed line pair is explicitly illustrative.
- Direct access to the existing pinned review discussion.
- Content-hashed CSS cache version, checked automatically against the file.
  A live check caught an older stylesheet cached by the browser; the versioned
  URL resolved it before the final visual checks.
- GitHub repository social preview successfully uploaded. A fresh GraphQL
  read returned `usesCustomOpenGraphImage=true`. This completes the setting
  reported as blocked in the earlier same-day discovery note; that dated note
  is retained as history. Preview caches on external services may still lag.

## Checks

Implementation commits: `4558c34f9eb03896e039463098be993373abd6da` and
`dbe93958d7d9a51a2d8e4ad582349712f9472983`.

- `python3 -B -m unittest discover -s tests -v`: 18 tests passed.
- `python3 -B tools/verify_public_release.py --pdf-metadata`: passed; Poppler
  supplied externally. Both PDFs have blank author metadata, no JavaScript
  and no embedded files. This is not a claim of authorial accountability.
- `python3 -B tools/check_theorem_records.py --output .audit/website-refinement-theorem-records`:
  all 13 theorem-relevant record checks passed. Historical package completeness
  remains false, as expected for this curated export; no exhaustive rerun.
- `git diff --check` and `git diff --cached --check`: passed before delivery.
- Changed public sources were checked for personal-name, email, private-account
  and local-path leakage; no matches. Neutral publication commit identities
  were verified. No private repository history was imported.
- GitHub Public release checks and Pages deployment succeeded for `dbe9395`.

The working manifest initially failed after intentional file edits and before
regeneration, then passed after the derived public manifest was refreshed.
Frozen scientific hashes were not rewritten.

## Browser Observations

The published page was checked through Chrome with the versioned stylesheet
`assets/site.css?v=5e09b4f60ed5` at these eight viewport sizes:

| Width | Height | Horizontal overflow | Detected clipped text | Images loaded |
| --- | --- | --- | --- | --- |
| 320 | 720 | No | None | 4/4 |
| 360 | 800 | No | None | 4/4 |
| 390 | 844 | No | None | 4/4 |
| 640 | 450 | No | None | 4/4 |
| 768 | 1024 | No | None | 4/4 |
| 1024 | 768 | No | None | 4/4 |
| 1440 | 1000 | No | None | 4/4 |
| 1920 | 1080 | No | None | 4/4 |

Visual inspection included the desktop example and narrow mobile opening/table.
The Example anchor reached its section; the keyboard skip link focused `main`;
the rights disclosure opened and closed with Enter. Temporary viewport overrides
were reset. There are zero script elements. The site remains static with no
third-party runtime or analytics. This is bounded QA, not WCAG certification.

Local `file:` browser preview was unavailable under the browser URL policy;
no workaround was used. Browser inspection was performed on the authorized
public deployment. The optional standalone Playwright CLI was not run in this
revision; its download-count assertion was updated for the added JSON link.

## Verified Payload Hashes

| File | SHA-256 |
| --- | --- |
| `index.html` | `0de1a63255a05b1836250286d6b65611ba504e11d22049006c096d64f25a667c` |
| `assets/site.css` | `5e09b4f60ed5a5ee3c744acd531791c3ff795d6ba5db8415713af73ffb63e18c` |
| Compact PDF, unchanged | `4cda05680cd7c20b1a1bce296842fc221560cf0b6dcf35c0aa1c0872ed100531` |
| Technical PDF, unchanged | `7d65bd93032c41fc62ae07da4ad5d5c60337edaab2f4e31e966998baefe5266a` |

The global power-of-two conjecture remains open. The site still distinguishes
the order-10 computational exclusion, the external census dependency,
substantial AI origin, absent independent review and reserved rights.
