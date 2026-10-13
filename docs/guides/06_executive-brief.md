# Guide: write the executive view

The executive view is the first thing a CAOS product writes, before its sizing, its contracts and any code. It is
the problem in its real context, in business language, kept in one data file, `content/executive.json`, that the
shell renders as the first view of the Introduction. This guide is enough to fill it with no other context. The
binding text is CAOS_MANAGE `conventions/problem-context-first.md` (Felipe, 2026-10-12); the shell's own guide is
its page `06_executive-view` (CAOS_APP_SHELL, folder `docs`). If they differ from this page, they win.

A product writes content. It never designs this view: the shell's `ExecutiveView` takes no children, no section can be
added, removed or reordered, and the shell's gate cannot be waived for it.

## 1. Why it is the core

Felipe, 2026-10-12: "force that, it is the point of my apps, anyone can write code and release an app, but tailored
on a real problem context is the expected core." And: "the 4 initial are the expected content on the intro sections.
The intro must have 2 visions, the executive and the technical." And: "i need clear rules so any product produces a
consistent output."

A CAOS app is judged by whether the person who owns a real problem, in a real industry, would give it thirty more
minutes. Code can be regenerated; the tailoring to a named problem, its owner, its numbers and its limits cannot.

The golden rule: "If you were the CxO sitting in that room, would you give this rep 30 more minutes of your time or
delegate them down to someone on your team?"

## 2. The four sections (Felipe's rubric, verbatim)

The four sections are the first four goals of the executive-pitch rubric, in this order, with these titles. Each must
read as the HIT, never as the MISS. The shell writes the titles and the questions; the product writes the data.

| # | Section title | Question | HIT | MISS |
|---|---|---|---|---|
| 1 | Industry & Exec Tailoring | Built for a C-suite exec? | Named exec owned initiative, quantified why they need to act now. | Generic; no exec story or data. |
| 2 | AI Transformation Story | Outcomes, not a feature tour | Vision first; each product ties to non-technical business outcome, presents quantified proof points | Product tour; no vision or outcomes. |
| 3 | 4Cs Positioning | Value story, not features dump | Ties the 4 C's back to the exec's problems. | Lists the C's without tying to the exec. |
| 4 | Delivery & Credibility | Trust them in front of a CxO? | Composed, two-way dialogue with business relevant questions. | Rushed, monologues at the exec, asks few questions. |

The names and the order of the 4 C's are Felipe's to give. Until he does, `four_cs` is absent from the file (the shell
refuses it) and section 3 shows the shell's declared pending state.

## 3. The research it needs first

Never write the view from memory. Research the problem context and persist it as dated dossiers (the same place as the
method research, cited in `Research basis`). It answers four questions:

1. **Who owns the problem?** One C-suite role in one organisation, and the operation it sits in.
2. **What does it cost today, and by when?** One quantified figure with its unit and its source (a DOI, a URL, a
   committed file), and the deadline the executive works to.
3. **What was tried?** The current practice and its gap.
4. **What would that executive ask?** The business questions, each with the plain answer, the evidence and the limit.

A figure with no primary source you read is not written. Every figure of the file has its entry in `sources`.

## 4. The data file

`content/executive.json`, English and Spanish together, valid against the shell's `executive.schema.json` (installed by
`npm ci` at `frontend/node_modules/@fasl-work/caos-app-shell/src/content/executive.schema.json`). These fields, and
nothing else; every text is `{ "en": ..., "es": ... }`.

| Section | Field | Rule |
|---|---|---|
| 1 | `executive` | One C-suite role (for example Chief Risk Officer). One, never a list. |
| 1 | `organisation` | One industry and one context (for example "a Chilean commercial bank"). One, never several regions. |
| 1 | `initiative` | One sentence: what that executive owns and must achieve. |
| 1 | `why_now` | `figure` (`value`, `unit`) and `deadline`: one figure and one date or deadline. |
| 2 | `vision` | One sentence: what changes for the executive's business. Comes first. |
| 2 | `outcomes` | 3 to 5 rows, each `capability` (what the product does, plain words), `outcome` (the business result, non-technical), `proof` (`value`, `unit` and a one-line `statement`). |
| 3 | `four_cs` | Exactly 4 rows, one per C, in Felipe's order: `c` and `exec_problem` (one sentence tying it to this executive's problem). Absent until the names are given. |
| 4 | `dialogue` | 3 to 5 pairs: `question` (a business question that executive asks) and `answer` (at most 2 sentences). |
| 1, 2 | `illustrations` | Exactly `initiative`, `problem`, `solution`, each with its SVG `file` (a path under `frontend/public/`, or one per language) and its `caption` (one sentence). |
| all | `sources` | `{ field, source }` rows: the source of every figure, by field path (`why_now.figure`, `outcomes[0].proof`, ...). Shown as numbered notes, never inline. |

Writing limits, checked by `validateExecutive` (run it in a unit test, as `frontend/src/content/executive.test.ts`
does) and by the gate on the rendered page, in both languages alike:

- every sentence at most 30 words; `answer` at most 2 sentences; `initiative`, `vision`, `proof.statement`,
  `exec_problem` and `caption` one sentence each;
- no equation, no formula, no code (a `$`, `\(`, `\[` or a TeX command fails);
- no inline citation (`(Source`, `[1]`, a parenthesised author and year): the source goes in `sources`;
- no acronym the executive would not use without its words in full the first time (a reviewer's duty).

The template ships a filled example (a hospital network's chief operating officer planning beds for the winter
respiratory season; every figure sourced or read from the example's own committed results). Replace every field.

## 5. The three illustrations

Felipe, 2026-10-12: "i need high quality diagrams, not graphs, illustrations of the initiative, the problem, the
proposed solutions." Three, authored for the product, as SVG files under `frontend/public/` (the example's are
`frontend/public/executive/`):

| Illustration | Placed in | What it shows |
|---|---|---|
| `initiative` | Section 1 | The executive in the organisation's real setting, the initiative they own and its deadline. |
| `problem` | Section 1, after the why-now | What goes wrong today in that setting, and what it costs: the actors, the systems and the failure, drawn as a scene. |
| `solution` | Section 2, after the vision | The same setting with the product in place: what it does, who uses it, and where each business outcome appears. |

Each meets this standard:

- An illustration, not a graph: a drawn scene of people, places, systems and their flow; no axes, no plotted data, no
  chart, no screenshot, no stock image, no boxes joined by arrows.
- Hand-authored SVG with a `viewBox`, inserted inline by the shell (never through an `img` tag, which cannot read the
  theme). Coloured only with the shell's theme tokens (`var(--color-...)`), `none` or `currentColor`, correct in light
  and dark. Give `text` no font family of its own.
- Labels in plain business words, in English and Spanish, inside the drawing: one file may carry both sets, each
  `text` marked `data-lang="en"` or `data-lang="es"`. Readable at the rendered size: at least 9 px once scaled to the
  column, so at a 640 wide viewBox use a font size of 18 or more and keep each label short.
- No equation, no acronym, no `data-chart`.
- One caption sentence under each, saying what the reader should take from it.
- The problem and the solution share the same setting and layout, so the change is visible between them (the example
  keeps the office, the hospital, the annex, the plaza and the wave in the same places in all three).

The shell's gate measures what a machine can: the three exist, are inline, use only tokens, declare no chart, and
every label sits inside its drawing at a readable size in both languages. Whether a drawing reads as a scene and not
as a chart in disguise is a reviewer's judgement.

## 6. The SDD names the file

The design document's `Executive brief` section (right after `Problem and non-goals`) says what the file is and where
it is, and nothing more: a short paragraph and the line

```
Data file: content/executive.json
```

It restates nothing: no part headings, no list, no table, no sentence copied from the file, at most 120 words. The
old four parts (Initiative, Outcomes, Positioning, Credibility) are not the standard.

## 7. What `scripts/check_sdd.py` fails

- `content/executive.json` is missing, is not JSON or breaks the schema (each finding names the field path, such as
  `outcomes[1].proof.unit`);
- the shell's schema is not installed (run `npm ci` in `frontend/`; the check fails rather than pass unvalidated);
- a figure has no source, or a source names a field that is not a figure;
- an illustration file is missing, leaves `frontend/public/`, or is not an SVG with a viewBox;
- the SDD has no `Executive brief` section in its place, lacks the `Data file:` line or restates the view.

## 8. Checklist

- [ ] The dossiers answer the four questions of section 3 and are cited in `Research basis`.
- [ ] One executive, one organisation, one initiative sentence they would recognise.
- [ ] One why-now figure with its unit, its deadline and its primary source.
- [ ] The vision comes first; 3 to 5 outcomes, each a plain capability, a business result and a sourced proof.
- [ ] 3 to 5 dialogue pairs, honest ("no" and "not yet" included), answers of at most 2 sentences.
- [ ] Three illustrations that are scenes, in tokens, with both languages, the problem and solution sharing a layout.
- [ ] `python scripts/check_sdd.py .` and `npm test` pass, `npm run gate` reports 0 failures, and a reviewer has read the
  rendered view against the HIT and MISS of each section and the golden rule.

Next: [guide 07, the five documentation pages](07_documentation-pages.md) carries the technical view of the page.
