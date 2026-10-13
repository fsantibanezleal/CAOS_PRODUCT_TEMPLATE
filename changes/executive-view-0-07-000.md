- Shell 0.13.0 (pinned exactly): the executive view standard of CAOS_MANAGE `conventions/problem-context-first.md` (decided
  2026-10-13) replaces the 0.12.0 one. BREAKING for products: `executive.schema.json` 2.0.0 replaces the 0.12.0 fields
  (`executive`, `organisation`, `initiative`, `why_now`, `vision`, `outcomes`, `dialogue`); a product rewrites its
  `content/executive.json` and its three illustrations.
- Landing: the product lands on the Introduction's executive view. `App.tsx` routes `/` and `*` to the shell's `Landing`,
  the App moves to `/app` (an old link such as `/?case=B2` is forwarded with its query string), the unused `NotFound` page
  is removed, `scripts/check_live.py` checks `/app` too. Test: `frontend/src/App.test.tsx` (WB-008).
- The example's `content/executive.json` is rewritten as an executive frame of a problem space, hospital capacity in
  respiratory seasons, for no single hospital: a landing block, the five sub-tabs (the pain, the context, the current
  situation, the trends, the proposal with the 4 C's), nine sources each a title and an https link, every figure read at its
  source. The three illustrations are redrawn as `pain.svg`, `situation.svg` and `proposal.svg` under
  `frontend/public/executive/` (scenes in theme tokens, both languages inside the drawing; the pain and the proposal share
  one hospital setting); `initiative.svg`, `problem.svg` and `solution.svg` are gone.
- `scripts/check_sdd.py` validates the file against schema 2.0.0 (it refuses an installed schema that is not 2.0.0) and holds
  what a schema cannot say, as the shell's `validateExecutive` does: the 4 C's in order, the weights of the causes at most 100,
  every action owner a role of the situation, the writing limits in both languages, no promotional or client-bound wording,
  and the sources by id (unique, every citation names one, every source is cited, https links, no file citation).
- Tests: `frontend/src/content/executive.test.ts` and `Introduction.test.tsx` are rewritten for 2.0.0; `tests/test_spec_guards.py`
  and `tests/adversarial/test_guards_reject_planted_defects.py` plant the new defects; the residue marker flags the new example.
- Docs: guide 06 is rewritten to the standard, guides 00 and 07, the SDD executive brief, the design README, the web feature
  requirements WB-002 to WB-009 and their validation follow; `docs/design/measured-resources.md` no longer says the executive
  view states the example's numbers.
