# CAOS product template, a REAL product repo (not a demo)

<!-- BADGE HEADER (ADR-0065), copy this block to the top of an instantiated product README.
     Replace <OWNER>/<REPO> and the CI workflow filename. Every badge here is auto-updating and truthful.
     Allowed: CI (from Actions), license, latest version/tag, live demo, and arXiv ONLY once a real preprint exists.
     FORBIDDEN: hand-typed count/claim badges (tests N passing, languages N, coverage unless from CI, agents N, ...)
     and supply-chain-security theater (OpenSSF Scorecard, SLSA, VirusTotal) unless the repo actually ships signed
     installable binaries. A badge that states something a tool does not verify live is vanity, do not add it.
[![CI](https://img.shields.io/github/actions/workflow/status/<OWNER>/<REPO>/ci.yml?branch=main&label=CI)](https://github.com/<OWNER>/<REPO>/actions)
[![License](https://img.shields.io/github/license/<OWNER>/<REPO>)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/<OWNER>/<REPO>?label=version&sort=semver)](https://github.com/<OWNER>/<REPO>/tags)
[![Live demo](https://img.shields.io/badge/demo-live-2ea44f)](https://<SLUG>.fasl-work.com)
-->

This is the **canonical template** every Faena/CAOS data-product repo is instantiated from. It exists because
ad-hoc products (bespoke scripts, baked cases, no reproducible env, no data contract) kept shipping, they
*look* done but **cannot be applied to new data**, so they are demos, not tools. This template makes the standard
**executable**: clone it, run two scripts, and you have a reproducible offline pipeline that ingests data in a
**standard format**, processes it through **typed, seeded, tested stages**, emits **committed standard-format
artifacts + a manifest**, and feeds a web app that **replays** them, and that any third party can point at
**their own data**.

It is modelled on the validated exemplar **CAOS_SIMLAB** (`simlab/pipeline.py`, `requirements-*.txt`,
`scripts/setup+precompute`, `docs/frameworks`, `data/artifacts`, `manifests/`).

## The two data contracts (the thing that was missing everywhere)

A product is only real if data flows through **two enforced contracts**:

1. **Ingestion contract, `raw → processing`.** `data-pipeline/<slug>lab/io/contract.py` (shipped as `examplelab`) defines the required schema (columns,
   units, ranges) of an input dataset and an explicit **outlier policy** (reject / clip / flag). This is the
   *"bring your own data"* gate: a user's dataset is accepted iff it satisfies the contract. Documented in
   [docs/data-contract.md](docs/data-contract.md).
2. **Artifact contract, `processing → web`.** Every pipeline run writes a compact, standard-format artifact and a
   `manifests/<case>.json` (params, seed, run_ms, bytes, gate verdict, format/version). The web app loads **only**
   these, it never recomputes, and a TS type mirrors the manifest schema so a contract drift fails the build.

If either contract is missing, the product is a demo. CI enforces both.

## Quickstart (proves the template runs end-to-end)

```bash
# 1. create the reproducible environment (.venv + pinned per-need requirements)
./scripts/setup.sh                      # or scripts/setup.ps1 on Windows PowerShell

# 2. run the offline pipeline over every case → data/artifacts/ + manifests/
./scripts/precompute.sh                 # or scripts/precompute.ps1

# 3. the tests (determinism, both data contracts, the gate, parity)
.venv/bin/python -m pytest              # .venv/Scripts/python.exe on Windows

# 4. the web app consumes the artifacts (copy-data enforces the artifact contract)
cd web && npm install && node copy-data.mjs && npm run dev
```

## How to instantiate this template for a NEW product

See [docs/guides/00_instantiate.md](docs/guides/00_instantiate.md). In short: copy this tree, **delete the
`.template-source` sentinel** (this arms the residue guard, `scripts/check_template_residue.py`, which then
fails CI if any example lab or placeholder text survives), rename the `examplelab` package (in
`data-pipeline/`) to `<slug>lab`, **replace the EXAMPLE engine** (the SIR model in
`data-pipeline/<slug>lab/model/` + `stages/`) with your
product's research-chosen SOTA engine (the one documented in `docs/frameworks/`, pinned in
`requirements-precompute.txt`, e.g. Yade/Chrono for DEM, OR-Tools for dispatch, MintPy for InSAR), write your
ingestion contract + cases, and fill the `docs/` wiki **as you build, not at the end** (ADR-0056).

## Hard rules this template bakes in

- **The deep research is binding, not decoration.** Every engine/solver/library the research selected lives in
  `docs/frameworks/<tool>/` *and* `requirements-precompute.txt`, and the pipeline actually uses it. No hand-rolled
  substitute for a SOTA engine the research prescribed.
- **Standard formats end-to-end** (`data-pipeline/<slug>lab/io/formats.py`): domain-standard in, compact-standard out.
- **Reproducible**: pinned requirements per need; `scripts/setup`; CI installs them and runs a pipeline smoke.
- **Applicable to new data**: the ingestion contract is the bring-your-own-data door.
- **Versioned** (X.XX.XXX, CHANGELOG + tags from day 1) with **license/attribution hygiene**.

See [docs/architecture/01_overview.md](docs/architecture/01_overview.md) for the full rationale.
