# Guide: make a product from this template

The product's research and plan come first, and its SDD (`docs/design/SDD.md`) is written before any code
(ADR-0075). This guide starts after that.

## 1. Create the repository and instantiate

Create the repository from the template on GitHub (`gh repo create <owner>/<Repository> --template
fsantibanezleal/CAOS_PRODUCT_TEMPLATE`), clone it, set up the pipeline environment (`scripts/setup.sh`), and run:

```bash
python scripts/instantiate.py --slug <slug> --name "<Name>" --repo <Repository> \
  --deploy pages --domain <slug>.fasl-work.com --visibility public \
  --tagline-en "<one line>" --tagline-es "<una línea>"
```

- `--deploy` is the one deploy place, decided now: `pages` (a static site) or `vps` (only for a product with an
  active backend). The other place's files are removed; `scripts/check_deploy_place.py` keeps it that way.
- `--visibility private` hides every source link in the app.
- `--domain` writes a CNAME file into `frontend/public/` for Pages; without it the site is a project page under the repository
  name, and the deploy builds with that base path.

The script writes `product.json`, the frontend package name, `VERSION` (0.01.000), a fresh `CHANGELOG.md`, the MIT
`LICENSE`, `deploy/TARGET` and a product `README.md`; it deletes `.template-source` and `.vscode/`;
then it bakes, tests and builds once and runs `scripts/check_template_residue.py`. That list is the work that
follows.

## 2. Write the specification area, then fix the contracts

The map is [`docs/design/README.md`](../design/README.md). In this order, each step with its guard
(`scripts/check_sdd.py`, `check_tech_matrix.py`, `check_contract_versions.py`, `check_contracts.py`,
`check_readiness.py`, `check_skeleton.py`; CI runs them all):

1. **Research basis.** Before the plan, research the real state of the art and persist it. In
   [`docs/design/SDD.md`](../design/SDD.md) replace the example's `Research basis`: what was decided, each claim with
   a DOI or URL (at least three distinct works), and a line starting `UNVERIFIED:` (`UNVERIFIED: none` if so). Never write it
   from memory.
2. **Executive view.** The first thing the product writes after its research and before its sizing, and the first
   thing to do after instantiating: `instantiate.py` leaves the example's `content/executive.json` and its three
   illustrations in `frontend/public/executive/` in place, to be replaced, not kept. Frame the problem space the
   product works in, for a decision maker, general (never a client, never a pitch): the title, the key statement, two or
   three headline figures, the five sub-tabs (the pain, the context, the current situation, the trends, the proposal with
   the 4 C's), a linked source for every figure and claim, and three illustrations (the pain, the situation, the
   proposal). Point the SDD's `Executive brief` section at the file with `Data file: content/executive.json` (it restates
   nothing). It is the core of the product ("anyone can write code and release an app, but tailored on a real problem
   context is the expected core"), `scripts/check_sdd.py` fails without a valid file, and the product lands on it: the
   root opens the Introduction's executive view, the App is at `/app` and stays the leftmost tab (the header order is always
   App, Introduction, Methodology, Implementation, Experiments, Benchmark; every documentation route takes the full width). The bearers, roles, approaches and 4 C's are small flip cards (a title of
   at most 8 words and a back of at most 40, in Spanish 10 and 50; a group of five is a carousel), and an illustration that
   explains a change is animated with a `prefers-reduced-motion` block that shows its final frame. How to write it: [guide 06](06_executive-brief.md);
   the technical view and the other pages: [guide 07](07_documentation-pages.md).
3. **Sizing.** Contract-first parallel delivery (ADR-0080): size the product (repositories, components, modules with
   their owner units, every boundary, the machine limits, the parallel units with disjoint write scopes) in the
   coordination records, and summarise it in `Sizing and contracts`. Fill `Technology and versions` with every pinned
   dependency (`| component | package | version | use | alternative considered |`; Python pins exact with `==`, a
   package.json range only with a lock that records it, and the table holds the locked version) and `Resources`
   with one row each for the bake, the training (if any), the tests, the build and the deploy payload, memory, disk
   and time measured or bounded (no TBD, no placeholder cell).
4. **Contracts.** Write them in [`docs/contracts/catalog.md`](../contracts/catalog.md): one row per boundary and per
   model slot, each with its schema file, an example, the tests of both sides, its missing-data behavior and a
   provider (a fixture, a simulator, a stub, or a baseline for a model slot). Replace the example's rows, schemas
   and provider tree with the product's, add a History row per contract, and run
   `python scripts/check_contract_versions.py --update` to create the lock. Regenerate the web's types
   (`cd frontend && npm run contracts:types`), recompute the readiness (`python data-pipeline/run.py readiness`), and
   run `scripts/check_contracts.py` until it passes. From now on a schema change needs a version bump and a History
   row whose kind is the semver step, and a breaking change needs a major one; CI checks it against the base ref
   (`check_contract_versions.py --base`, which needs the `fetch-depth: 0` checkout the workflow has). The rules are
   in the catalog.
5. **Requirements and tests, red first.** Per feature, `docs/design/features/<feature>/requirements.md` (SHALL, each
   with its gate); write the tests and watch them fail for the right reason before the code.
6. **Adversarial validation.** Per feature, `validation.md`: for every requirement the check that tries to break it
   (what was planted or refuted) and the test that does it, which must be adversarial: under `tests/adversarial/`, or
   named `test_adversarial_...` (`it('adversarial: ...')` in TypeScript). A requirement and a validation row never
   name a test that is skipped, only a name in a string or comment, or a prefix of a title. A feature whose status is
   planned or superseded is listed with its reason in `docs/design/features/.status-allow`. Add the planted-defect tests
   of the product's own guards to `tests/adversarial/`.

The walking skeleton comes next: the site built on the provider tree
(`CAOS_DATA_ROOT=docs/contracts/fixtures/data/derived npm run build`) and the API serving it, deployed so the UI and
the integration are checked from the first week. Every provider is labelled on the site by the readiness document
and listed by `scripts/check_skeleton.py` until its real producer replaces it; none may remain at a release.

## 3. Replace the example, unit by unit

Build vertically: each unit (a method, a case family, a page) is finished, with its code, tests and documentation,
before the next starts; units whose write scopes are disjoint are built at once, against the fixed contracts.

1. **The engine.** Replace `data-pipeline/pipeline/model/` and the stage bodies with the method ladder of the SDD.
   Each method meets its acceptance criterion (ADR-0069) and gets a card in `docs/frameworks/`, its dependency
   pinned in `data-pipeline/requirements.txt` (or the precompute or GPU file).
2. **Contract 1.** Rewrite `data-pipeline/pipeline/io/contract.py` for the product's raw data (columns, units,
   ranges, outlier policy) with a sample in `data/examples/`, to the params-record schema the catalog fixed (the
   test holds the schema's bounds equal to the code's); update `tests/test_contract.py`,
   `tests/contracts/test_params_record.py` and `data/README.md`.
3. **The cases.** Rewrite `data-pipeline/pipeline/cases/` and the registry: bilingual titles, categories and expected
   bands, and numeric expected ranges for every case (`core/expect.py` fails the bake outside them). Set the default
   case. Document the coverage matrix in `docs/cases/`.
4. **Contract 2.** Rename the schema ids (`example.*`) to the product's and change the trace and manifest shapes as
   the method needs, in the schema files first (bump the catalog row's version), then the producers, the generated
   types (`npm run contracts:types`) and the descriptors in `frontend/src/lib/contract.types.ts`: the build fails
   while the generated types are not current, and `tests/contracts/` and `contract.test.ts` fail on any key or type
   that one side has and the other does not.
5. **The live engine.** If a method runs live, port it to `frontend/src/engine/` and hold it to the baked artifacts
   with a parity test, as `sir.parity.test.ts` does. If none can, the workbench replays only and declares
   `replayOnly`.
6. **The workbench.** Rewrite `frontend/src/workbench/`: the case's question groups, its variants, its parameters
   and live values in the rail. Views are `PlotCard`s with lane, provenance and the selection key; curves go in a
   `UPlotChart`, categories in a `BarChart`, anything else in a `Stage` whose labels are measured with the shell's text
   kit (`fitLabel`, `niceTicks`); a table sits above the drawing of the same numbers. A product that is not about
   cases (a hub, an explorer, a console) replaces the workbench with the shell's `SurfacePage` and runs the gate with
   `--workbench ''`. The structure, tokens, icons and numbers are the shell's (its `docs/`); write CSS only for the
   product's own widgets, never for a shell class (`check_web_baseline.py`). **The App opens Focus mode for every case** (shell
   0.14.0, ADR-0070): `CaseWorkbench` takes `focus`, which puts a Focus button in the rail head that opens the open group in
   the full viewport (`?focus=1` beside `?case=` and `?view=`; Escape or the exit button returns to the same case, group
   and sub-view). `npm run gate` always passes `--require-focus`, so a workbench without `focus` fails the gate (G18). A
   surface product that has no workbench runs the gate with `--workbench ''` and has no Focus control to require.
7. **The pages and the diagrams.** Rewrite `frontend/src/pages/` from the product's dossiers (equations with
   captions, references with DOIs that resolve) and the five diagrams in `frontend/src/architecture/` (bilingual,
   shell tokens only).
8. **The SDD requirements.** Replace `docs/design/features/workbench/` with the product's features; every
   requirement names a test or guard that exists, and every feature has its `validation.md`.

## 4. Verify, then release

In separate steps: the sandboxed tests, the canonical bake (`scripts/precompute.sh`), `scripts/check_artifacts.py`,
`npm run build`, `npm test`, `npm run gate`, and every guard in `.github/workflows/ci.yml`. Read the gate's
captures yourself (`frontend/gate-output/index.html` shows every capture by route, the failures first): the gate
measures, it does not judge content.

A release bumps `VERSION`, `frontend/package.json` and the top of `CHANGELOG.md` together, merges `develop` into
`main` through a pull request, and tags `vX.XX.XXX`. The deploy runs after CI succeeds on `main` and checks the live
site; after it, run the gate against the deployed origin: `npm run gate -- --url https://<domain>`.

On GitHub Pages, before the first deploy, enable Pages with the Actions source and set the custom domain by API
(the Pages runbook in `deploy/`, kept only in a Pages product).
