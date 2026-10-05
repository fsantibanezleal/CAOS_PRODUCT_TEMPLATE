# Changelog

All notable changes to this template. Versions are X.XX.XXX; VERSION is the single source; every release is tagged.

## [0.02.004], 2026-10-05

One defect found while CAOS_Contraste built its case C05 (issue #13), and the base on the shell 0.7.2. The fix
carries a test that fails without it (`tests/test_guards.py`).

### Changed

- The web runs on `@fasl-work/caos-app-shell` 0.7.2 (0.7.1 and 0.7.2 published to npm on 2026-10-05): it carries the
  fixes of the known shell defects 14 to 18 (scientific notation for tiny magnitudes, the workbench rows that no
  longer shrink, the key under every chart of several series, the gate's pointer probe) and 21 (an integer axis ticks
  only at integers, and the gate fails a repeated tick label), so a product instantiated from this release starts on
  them and carries no override for them.

### Fixed

- The residue marker for the example's immunisation variants (`\bCOVERAGE\b`) matched inside a hyphenated identifier,
  because a hyphen is a word boundary: Contraste's finding id `F-SCALED-COVERAGE` failed the guard in its pipeline and
  in every artifact that carries the finding. The token counts only when no word character or hyphen touches it, as
  the placeholder-name marker already does; the example's constant is still caught.

## [0.02.003], 2026-10-05

Eight defects found while CAOS_Contraste replaced the example and ran its first full gate (issue #10). Each fix
carries a test that fails without it (`tests/test_guards.py`, `tests/test_dormant_api.py`).

### Fixed

- The residue guard flagged its own tests in every product (`tests/test_guards.py` must name the placeholder it looks
  for); its tests are now part of the guard's own set.
- The residue guard never read `.sh` and `.ps1` files, so `scripts/precompute.sh` and `scripts/precompute.ps1`
  shipped the example's case id in every product; they are scanned now, and their comments name a `<case-id>`.
- `scripts/precompute.ps1` found the pipeline interpreter in `.venv-pipeline` and then ran the global `python`; it
  runs the environment's interpreter.
- The template's instantiate test failed in every product (it needs the `.template-source` sentinel that instantiation
  deletes); it runs only in the template repository.
- The web's unit tests read only `.test.ts`, so a product's component tests (`.test.tsx`) never ran; Vitest includes
  both.
- The dormant `app/` read the example's manifest shape (`artifact.path`, `trace_schema`), so it broke in a product whose
  manifests differ. It serves the committed documents unchanged: `/api/cases`, `/api/cases/{id}/manifest` and
  `/api/artifacts/{path}` (any artifact a manifest names, in either form of contract 2), nothing outside
  `data/derived`; the example DTOs are gone.
- Template prose survived instantiation in files a product keeps: `pyproject.toml`, `requirements-precompute.txt`,
  `requirements-gpu.txt`, `tests/conftest.py`, `data-pipeline/pipeline/io/formats.py` and the framework card template
  now say what is true in any product. A new residue marker catches prose about the example engine in the files a
  product rewrites.
- `read_csv_rows` read a spreadsheet's UTF-8 export with its byte-order mark in the first header; it drops it.

## [0.02.002], 2026-10-05

Six defects found while CAOS_Contraste replaced the example (issue #7). Each fix carries a test that plants the
failure (`tests/test_guards.py`, `frontend/src/lib/declared.test.ts`, `frontend/src/lib/contract.test.ts`).

### Fixed

- `scripts/instantiate.py` renamed the package in `frontend/package.json` but left the template's name and version in
  `frontend/package-lock.json`, which the residue guard then flagged; it now renames both places of the lockfile.
- The residue guard's placeholder-name marker matched the template's own Vite plugin name `caos-product-html`, a
  finding no product could clear without editing base code; it now matches the placeholder name only.
- `scripts/check_doc_paths.py` failed on the gates of a requirements file opened `Status: planned`, which
  `scripts/check_sdd.py` allows: the two guards contradicted each other on the first day of every unit. The gates of
  a planned feature's `requirements.md` are now skipped there (and only there).
- `scripts/instantiate.py` left the template's own guide to instantiating (`docs/guides/00_instantiate.md`) and its
  index line in the product, where it names the example's feature folder; it now removes both.

### Added

- A case manifest may name several artifacts (`artifacts: [{path, bytes, lane, gate, ...}]`, one per variant baked
  apart) as well as one (`artifact`); `frontend/scripts/declared.mjs` holds the rule for the build and its test, and
  `scripts/check_artifacts.py` checks each artifact's bytes and lane. The index may declare further files to serve
  (`files`, a product's contract declarations say), copied and checked like the rest.
- `conform()` gains a nullable kind (`{ nullable: Kind }`), for an optional bound or an absent reference.
- `scripts/check_artifacts.py`, `scripts/check_doc_paths.py` and `scripts/check_template_residue.py` take an optional
  repository root, so their tests run them on a planted tree.

## [0.02.001], 2026-10-05

Found instantiating CAOS_Contraste, the first product made from 0.02.000 (by copying into its existing repository).

### Fixed

- The residue and doc-path guards read tracked files only, so in a product instantiated by copying (nothing
  committed yet) the residue guard reported "OK, no example content in 2 tracked files": a check that passed with
  nothing to check. Both now read tracked and untracked files (ignored ones excluded), and refuse a tree with too
  few files to be a product.
- `.template-version` recorded the product repository's own HEAD as if it were the template's commit; it now records
  the template release and its tag (`CAOS_PRODUCT_TEMPLATE 0.02.001 (tag v0.02.001)`).

## [0.02.000], 2026-10-04

The base fix of 2026-10-04 (ADR-0078, the recurring-failures history): the template now carries the rules every
product kept re-deriving, each with the gate that fails when it is broken.

### Added

- The frontend on shell 0.7: the six standard routes, one `CaseWorkbench` (case picker, immunisation variants, the
  two rates and the live values in the rail; Dynamics, Validation, Compare and Context in the instrument), five
  documentation pages with captioned equations and references whose DOIs resolve, a not-found page, and five
  bilingual architecture diagrams inlined with the shell's tokens.
- The live lane as a TypeScript port of the engine, with a parity test against every baked trace and a
  first-order convergence test against the final-size relation.
- The contract 2 mirror as interfaces and run-time descriptors, and a test that reads every committed artifact
  against them in both directions, types included.
- The artifact layer: root-absolute URLs with `?v=VERSION`, JSON only, declared loading state.
- Expected ranges per case (`core/expect.py`): the bake fails on a result outside them, and the manifest carries
  them to the web. Bilingual titles, categories and expected bands; the index names the default case.
- Build: `VITE_BASE` or `/`, one React and one router, the pre-paint script, `build.json` with the commit, every
  route materialised, `404.html`; `npm run preview` serves the build as Pages does; `npm run gate` runs the
  measured gate.
- Guards: `check_version_coherence.py`, `check_sdd.py` (mirrored from OreFlow, with the ADR-fit section and named
  TypeScript tests), `check_web_baseline.py`, `check_doc_paths.py`, `check_deploy_place.py`, `check_live.py`; the
  residue guard rewritten on content markers; the test sandbox with a session guard on committed artifacts.
- `scripts/instantiate.py`, the MIT `LICENSE`, `deploy/TARGET`, the example's SDD and feature requirements.
- CI: a web job, `pipefail` on every step, a workflow parse check, every guard; the deploy runs only after CI
  succeeds on the same commit and checks the live site.

### Fixed

- The epidemic case promised an attack rate between 0.7 and 0.9; its engine produces 0.924 (the final size for
  R0 = 2.75 is 0.920). The band now says what the engine and the theory say, and is checked.
- A test rewrote the committed EX02 manifest with its own seed and metrics; tests now run in a sandbox.
- The version was written in three places and read from none; it is read from VERSION everywhere.
- The nginx template answered a missing artifact with the app; it now answers 404 and includes the MIME table.
- Documentation that named files which no longer exist (the Pyodide worker, `architecture.ts.txt`, the old SVG
  folder, `docs/data-contract.md`) and links into a private repository.

### Removed

- The stub frontend, the Pyodide worker stub and `pipeline/live.py` (nothing called it), the root
  `requirements.txt` of the former Python live lane, and `STRUCTURE.md` (a pre-template blueprint).

## [0.01.000], 2026-06-20

### Added
- Initial instantiation from the CAOS product-repo template (ADR-0057).
- Offline `data-pipeline/` (`pipeline`): the two data contracts (ingestion + artifact), the named staged
  pipeline (preprocess → feature_extraction → train → infer → evaluate → export), the seeded RNG, the compact
  trace, the manifest, and the measured live-vs-precompute gate.
- EXAMPLE engine: a deterministic SIR epidemic (numpy-only, Pyodide-safe), **replace with the product's
  research-chosen SOTA engine**.
- Cases-by-category registry (4 regimes + 1 degenerate control); a live-lane entrypoint (`live.py`); tests for
  both contracts + pipeline determinism.
