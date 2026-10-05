# Changelog

All notable changes to this template. Versions are X.XX.XXX; VERSION is the single source; every release is tagged.

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
