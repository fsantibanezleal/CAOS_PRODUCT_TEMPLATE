# Guide: write the executive brief

The executive brief is the first thing a CAOS product writes, before its sizing, its contracts and any code. It is
the problem in its real context, in business language, in the design document
([`docs/design/SDD.md`](../design/SDD.md), section `Executive brief`). `scripts/check_sdd.py` fails an SDD without it.
This guide is enough to write one with no other context; the binding text is the convention
`conventions/problem-context-first.md` of CAOS_MANAGE, quoted and followed here.

## 1. Why it is the core

Felipe, 2026-10-12: "it is the point of my apps. Anyone can write code and release an app, but tailored on a real
problem context is the expected core."

A CAOS app is not judged by its code, its stack or its feature list. It is judged by whether the person who owns a
real problem, in a real industry, would give it thirty more minutes. Code can be regenerated; the tailoring to a
named problem, its owner, its numbers and its limits cannot. The brief is shown first on the product's Introduction
page (see [guide 07](07_documentation-pages.md)) and reviewed against the golden rule below.

What it rules out: starting from a method, a dataset or a stack and looking for a problem afterwards; an
Introduction that begins with the physics, the mathematics or the architecture; value stated without a number, or a
number without its unit and source; a product whose owner, industry and operation cannot be named; a feature list
presented as the reason the product exists.

## 2. The golden rule

If you were the executive who owns this problem, would you give this product thirty more minutes of your time, or
delegate it down to someone on your team? Write for the executive. A part that reads like its miss (below) is not
done, whatever the guard says: the guard checks structure, a reviewer checks the rule.

## 3. The research it needs first

Never write the brief from memory. Before it, research the problem context and persist it as dated dossiers (the
same place as the product's method research, cited in `Research basis`). It answers four questions:

1. **Who owns the problem?** A role and an industry or sector, and the operation it sits in.
2. **What does it cost today?** The quantified cost of the problem or of acting late or too much, each number with
   its source (a DOI, a URL, a committed file). A number with no source is marked UNVERIFIED in the dossier and is
   not shown in the brief as a claim.
3. **What was tried?** The current practice and its gap.
4. **What would a decision maker ask?** The business questions, each with the plain answer, the evidence and the limit.

Every number in the brief traces to a dossier. A real product replaces every assumption by a sourced number from
its dossiers before its first release. The guard enforces it: in this template (the repository without a
`.template-version` file) a labelled assumption is accepted so the example can teach the format; in a product made
from it (`.template-version` present) an assumption is a finding, so no product ships on one.

## 4. The four parts, each with its hit and its miss

| Part | The hit | The miss |
|---|---|---|
| Initiative (industry and executive tailoring) | The initiative an executive owns, named by role and industry, and the quantified reason to act now, with the source of each number | Generic; no executive story or data |
| Outcomes (the transformation story) | The vision first; then each capability of the product tied to a non-technical business outcome, with a quantified proof point | A product tour; no vision or outcomes |
| Positioning (the value story) | Each value point tied back to that executive's problem (four named value points until the four C's are defined) | A list of value points not tied to the executive |
| Credibility (delivery) | The business questions that executive would ask, each answered plainly, with the evidence and the honest limits | A monologue; few questions |

A short worked example, from this template's own SDD (an SIR epidemic model, a teaching example; its brief says so):

- Initiative: "The owner is the head of the epidemiology unit of a regional health authority (public health)", then
  "In the epidemic case (reproduction number 2.75, 100000 people), infections peak at 27345 people on day 24.25 ...
  (source: data/derived/EX02_epidemic/trace.json)". A role, a sector and a number with its source.
- Outcomes: the capability "Live re-run in the browser", the outcome "A what-if ... is answered while the room waits",
  the proof point "median 0.02 to 0.08 ms per run against a budget of 1500 ms (source: docs/design/SDD.md)".
- Positioning: "**An answer in the meeting**: the what-if does not wait for an analyst, so the decision is made with
  the numbers in the room." The value point and the owner's problem it answers.
- Credibility: "Q: Is this a forecast for our region?" then "A: No. It is a teaching model ... and no real data".
  The honest answer is the one that earns the next thirty minutes.

## 5. The exact format the guard checks

A level-2 section `## Executive brief` placed right after `## Problem and non-goals`, with four level-3 parts in this
order. Headings may carry a number (`## 1. Problem and non-goals`,
`## 2. Executive brief`). The guard reads the section as a reader sees it: text inside a fenced block (``` or ~~~, each
closed only by its own marker) or an HTML comment does not count, neither its headings nor the content of a part, so
a part whose whole body is a code block is empty. CRLF and trailing spaces are fine.

```
### Initiative

<who owns it (role and sector), the initiative, in prose>

- <claim with a number and its unit> (source: <DOI, URL or a path that exists in the repository>)
- <claim with a number and its unit> (assumption: <why this value is used, at least five words>)

### Outcomes

<the vision, in prose>

| capability | business outcome | proof point |
|---|---|---|
| <capability> | <non-technical outcome> | <number and unit> (source: <...>) |

### Positioning

- **<value point>**: <the problem of that owner it answers>

### Credibility

- Q: <a business question that owner would ask>
  A: <the plain answer, with the evidence and the limit>

Limits: <what the product is not and what is not yet proven>
```

The guard fails when:

- the section is missing, is not right after `Problem and non-goals`, or a part is missing, out of order or empty;
- Initiative has no line with a number and a source or an assumption;
- Outcomes has fewer than three rows, or a proof point without a number, or without a source or an assumption;
- Positioning does not have exactly four bullets of the form above;
- Credibility has fewer than three questions each followed by an answer, or no `Limits:` line;
- a text is a placeholder or a stub: made of TBD, TODO, lorem ipsum or the like, or with too few distinct words (an
  introduction of 8, a claim of 3, a business outcome of 3, a value point's problem of 6, a question and an answer of 3
  each, `Limits:` of 5);
- Positioning repeats a value point, Outcomes repeats a capability, or Credibility's three questions are not different;
- the section holds an equation (`$`, `\(` or a fenced `math` block): the brief is business language. Write "USD", not
  a dollar sign.

A number is digits standing alone, with an optional unit: "many", "significant" and "several" are not numbers, the
0 of R0 is part of a name, and neither a date, a year (`since 2026`, `in 2026`, a lone `2026`) nor an index (`Step 1`,
`item 2`, `3.`) is the number of a claim. A source is a DOI (`10.xxxx/...`) or an `http` URL of a real work (not
example, localhost or a made-up DOI such as `10.0000/fake`), or a file that exists in the repository, never a
directory or the root (several sources are separated by `;`). An assumption (template only) needs a reason of at
least five words, in plain words, so a reader sees it is an assumption.

## 6. Common failures

- **A product tour.** Outcomes lists screens and features ("a dashboard, a map, an export"). Each row is a capability
  tied to what the owner can now do or avoid, with a number.
- **Value without a number.** "Faster decisions" is the miss; "a what-if in 0.08 ms against a 1500 ms budget" is the hit.
- **A generic owner.** "Organizations that need insight" names nobody. Name the role and the sector, and what that
  person is accountable for.
- **Positioning that lists the product's strengths.** Each value point answers a problem the owner has; say which.
- **Credibility as a monologue.** Write the questions the owner would actually ask (cost, risk, evidence, who stands
  behind a wrong number) and answer each, including "no" and "not yet".
- **A number from memory.** If it is not in a dossier, it is an assumption, written as one.

## 7. Checklist

- [ ] The research dossiers answer the four questions of section 3 and are cited in `Research basis`.
- [ ] The owner is a role in a sector, and the initiative is one sentence the owner would recognise.
- [ ] Every claim of value has a number, a unit and a source, or is an assumption labelled in plain words.
- [ ] Outcomes starts with the vision and has at least three capability rows, each tied to a business outcome.
- [ ] Positioning has four value points, each naming the problem it answers.
- [ ] Credibility has at least three business questions with plain answers, and a `Limits:` line that is honest.
- [ ] No equation, no jargon the owner would not use.
- [ ] `python scripts/check_sdd.py .` passes, and a reviewer has read it against the golden rule of section 2.

Next: [guide 07, the five documentation pages](07_documentation-pages.md) carries the brief to the page.
