### Added
- `core/readiness.py`: computes `data/derived/readiness.json` from the contract catalog and the repository (states available, partial, stale, provider, training, missing; reasons in English and Spanish from the catalog's Missing-data table); `python data-pipeline/run.py readiness` writes it, every bake ends by writing it, and `scripts/check_readiness.py` (stdlib) fails CI when the committed document is stale.
- `model/baseline.py`: the surrogate slot's analytic baseline (the SIR peak fraction), the bundle validator `is_valid_bundle`, and `train.load_released`; `run.py all --no-train` never trains and reports the released bundle or, when none is valid, the baseline.
- The dormant API serves `GET /api/readiness`; contract tests for readiness, the surrogate swap (baseline and trained bundle behind one slot) and the API (every response checked against `api.openapi.json`, on the bake and on the provider fixture tree).

### Changed
- `train.predict` clamps its output to [0, 1]; `evaluate.run` takes `None` for no released bundle.
- `app` settings are read when instantiated, so `DATA_DIR` set after import takes effect.
- `requirements-api.txt` records the verified pins (`fastapi==0.143.0`, `uvicorn[standard]==0.54.0`) as comments, uncommented when the API lane is activated.

### Fixed
- The API answered `GET /api/cases` with `{"cases": []}` (a body that is not an index) when the index was absent; it now answers 503 with state `missing` and the reason, and an unknown case or artifact stays 404.
