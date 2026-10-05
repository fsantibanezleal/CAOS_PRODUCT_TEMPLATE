# CAOS product template

[![CI](https://img.shields.io/github/actions/workflow/status/fsantibanezleal/CAOS_PRODUCT_TEMPLATE/ci.yml?branch=main&label=CI)](https://github.com/fsantibanezleal/CAOS_PRODUCT_TEMPLATE/actions)
[![License](https://img.shields.io/github/license/fsantibanezleal/CAOS_PRODUCT_TEMPLATE)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fsantibanezleal/CAOS_PRODUCT_TEMPLATE?label=version&sort=semver)](https://github.com/fsantibanezleal/CAOS_PRODUCT_TEMPLATE/tags)

The repository every CAOS product starts from (ADR-0057). It is a working product on the first day: an offline
pipeline that bakes cases and checks them, committed artifacts that a web workbench replays, a live engine that
re-runs a case in the browser, five documentation pages, and the guards and the measured gate that keep all of it
honest. The domain is a placeholder (the SIR epidemic model) so that every part has something real to carry.

A product is made from it with one command, and from then on the guards list what of the example remains until it
is replaced.

## What is in it

| Part | Where | What holds it |
|---|---|---|
| The pipeline: named stages, seeded, each case checked against its expected ranges | `data-pipeline/` | `tests/`, run in a sandbox that fails if a test writes a committed artifact |
| Contract 1, ingestion: bad values rejected with a reason, unusual ones flagged | `data-pipeline/pipeline/io/contract.py` | `tests/test_contract.py` |
| Contract 2, artifacts: index, manifests and traces, bilingual, versioned | `data/derived/` | `scripts/check_artifacts.py`, `frontend/src/lib/contract.test.ts` (both directions) |
| The live engine, a TypeScript port of the Python one | `frontend/src/engine/` | `frontend/src/engine/sir.parity.test.ts` (every baked trace, first-order convergence) |
| The web: the workbench and five documentation routes on the shared shell | `frontend/src/` | `npm run gate` (`caos-shell-gate`: every route, tab and case, five sizes, both themes, both languages) |
| The design, every requirement with the gate that fails it | `docs/design/` | `scripts/check_sdd.py` |
| One version, one deploy place, no example left behind | `VERSION`, `deploy/TARGET` | `scripts/check_version_coherence.py`, `scripts/check_deploy_place.py`, `scripts/check_template_residue.py` |

## Run it

```bash
./scripts/setup.sh                       # .venv-pipeline with the pinned pipeline requirements (setup.ps1 on Windows)
./scripts/precompute.sh                  # the canonical bake into data/derived (a release operation, never CI)
.venv-pipeline/bin/python -m pytest      # the pipeline tests, sandboxed (.venv-pipeline/Scripts/python.exe on Windows)
cd frontend
npm ci
npm run build                            # copies the declared artifacts, type-checks, bundles, materialises the routes
npm test                                 # contract both ways, engine parity, the artifact layer
npm run preview                          # serves dist/ the way GitHub Pages does
npm run gate                             # the measured gate on the build
```

## Make a product from it

Create the product repository from this template on GitHub, clone it, and run:

```bash
python scripts/instantiate.py --slug <slug> --name "<Name>" --repo <Repository> \
  --deploy pages --domain <slug>.fasl-work.com --visibility public \
  --tagline-en "<one line>" --tagline-es "<una línea>"
```

It writes the product's identity, licence, version and deploy place, removes the template's sentinel and blueprint
files, bakes, tests and builds once, and prints what of the example remains. The full procedure, and what the
product replaces next, is [docs/guides/00_instantiate.md](docs/guides/00_instantiate.md).

## The rules it carries

- Write the SDD before the code; every requirement names its gate (ADR-0075).
- The research is binding: every engine the research selected is pinned, documented in `docs/frameworks/` and run
  by the pipeline.
- Canonical science is offline. CI runs cheap checks; the bake and the pipeline tests run on a workstation; a deploy
  publishes the committed artifacts and never recomputes them (ADR-0069, ADR-0074).
- The web is built on the shared shell and measured before it ships; the base carries the rules, so a product does
  not re-implement them (ADR-0078).
- English in the repository; every reader-facing string in English and Spanish (ADR-0011, ADR-0066).

Licensed under the MIT License (see [LICENSE](LICENSE)).
