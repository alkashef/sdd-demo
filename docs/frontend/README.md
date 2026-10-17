# Front-end visual reference

The approved look for `src/web/` (DEC-019, DEC-020). The user approved it on 2026-10-17.
It shows how the pages look and behave. Requirements stay in `docs/spec.md`. Structure and
module rules stay in `docs/design.md` and `.claude/rules/`.

## Files

| File | Shows |
| --- | --- |
| `job-view.dc.html` | Job view: job text panel, foldable ranked candidate cards (JOB-002, JOB-003, RNK-003, REC-001). |
| `candidate-view.dc.html` | Candidate view: raw CV beside the attributes, then the ranked job descriptions (CND-001 to CND-003). |
| `job-view-service-unavailable.dc.html` | Job view when the LLM calls failed: failure panel, "Not available" values (ERR-001, ERR-002, MIS-001, MIS-002). |

The `.dc.html` files are design-tool sources. They are a visual reference, not code to copy: they
need the design tool's runtime to open. Build the real pages from plain HTML, CSS and JavaScript
(`.claude/rules/javascript.md`, `.claude/rules/ui-design.md`). The dummy names, scores and texts in
them are invented.

## Layout

- Page: header, navigation, main, footer. The page is fluid up to 1440 px, with 24 px gutters.
- Header (`app-header`): stays at the top while the page scrolls (`position: sticky`). Left: the
  logo mark and "CV Matcher". Right: "N candidates · N job descriptions" in the muted colour.
- Navigation: 260 px wide. Section "Job descriptions", then section "Candidates". Each item shows a
  label (job title or candidate name), then the file name below it in the small muted size. The
  selected item has the tint background and primary-colour label. It scrolls with the page.
- Main: flex, wraps below the navigation on a phone (`flex: 999 1 560px`, `min-width: 0`).
- Footer: "Runs locally at 127.0.0.1:8000." and the OpenAI data-flow notice (DEC-006).
- Responsive: no horizontal scroll from phone to wide desktop. Facts and stats use
  `repeat(auto-fit, minmax(…, 1fr))` grids.

## Views

**Job view.** Heading: job title, file name (small, muted), then "All N candidates, best match
first." as meta. Under it the "Job description text" panel (`<details open>`, scroll box with a
maximum height). Then one card per candidate, best match first.

**Candidate card.** A `<details open>`. The summary line holds a chevron, the rank circle, the
name with the file name below it, and the match score with its bar. Folded, only the summary line
shows. The body holds, in order: the recommendation row (pill "Interview" or "Skip", then the
reason), the six extracted facts, the skill chips, and the six calculated attributes.

- Extracted facts: Current title, Location, Highest degree, Last job, Countries worked, Companies.
- Calculated attributes: Total employment, Jobs held, Average per job, Employment gaps, Since
  graduation, Employed now.

**Candidate view.** Heading: name, file name, then the current title as meta. Two columns that
wrap: the raw CV text (monospace, scroll box) and, beside it, three cards: "Extracted attributes"
(facts and skill chips), "Calculated attributes", "Best-matching job descriptions" (rank, title,
file name, score and bar; no recommendation).

**Failure state.** An amber `role="alert"` panel above the heading: one sentence that names the
cause, and a "Failure list" `<details open>` of item and cause. Rankings, raw texts and lists stay.
A candidate whose name is missing shows its file name as the label and "Name not available" below
it. The recommendation row shows a grey "Not available" pill. The attributes show "Not available".

## Rules for values

- A missing value shows the text "Not available" in the muted colour and italic (MIS-001).
- A score shows two decimals. The bar width is the score as a percentage.
- A last job with an unknown end shows "Not available" for the end. "Present" only for a current
  job (DEC-015).
- The recommendation pill differs by icon and label as well as colour.

## Tokens (`theme.css`)

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#F6F7FC` | Page background, inset boxes |
| `--surface` | `#FFFFFF` | Header, footer, cards |
| `--line` | `#E4E7F3` | Borders |
| `--ink` | `#151833` | Text |
| `--muted` | `#5A6080` | Secondary text, file names, labels |
| `--primary` | `#5B3DF5` | Accent: logo, rank, score, selection |
| `--tint` | `#EEEAFF` | Selected item, rank circle, chips background |
| `--chip-ink` | `#3F26C9` | Chip text |
| `--mint` | `#19D3A5` | Score bar fill |
| `--track` | `#E9E6FF` | Score bar track |
| `--mint-bg`, `--mint-ink` | `#D6F8EC`, `#0A6B52` | "Interview" pill |
| `--coral-bg`, `--coral-ink` | `#FFE7E2`, `#A32A1C` | "Skip" pill |
| `--sun-bg`, `--sun-ink`, `--sun-line` | `#FFF4D1`, `#6B4A00`, `#F5D77A` | Failure panel |
| `--neutral-bg`, `--neutral-ink` | `#ECEEF7`, `#3F4560` | "Not available" pill |

Text pairs meet a 4.5:1 contrast ratio. Add the maximum height of the scroll boxes as one more
token (DEC-020).

## Type and shape

- Font: the system font stack (`system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue",
  sans-serif`). The raw CV uses the system monospace stack. No custom font, no image.
- Sizes: page heading 28 px bold; card name 17 px bold; body 14 px; file names and footer 12 px;
  field labels 11 px bold, uppercase, letter-spaced; score 22 px bold.
- Cards: 16 px radius, 1 px `--line` border, 20 px padding, 12 to 20 px gaps. No shadow, no
  gradient, no animation.
- Every control has hover text and a visible focus ring (2 px `--primary`).
