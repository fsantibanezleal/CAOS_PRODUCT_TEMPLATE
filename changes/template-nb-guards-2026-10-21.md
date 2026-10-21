- **The notebook runner's temp root** (NB-041, NB-042). `scripts/run_notebooks.py --check` writes its copies to a fresh folder under
  the temp root the caller names, `--tmp DIR` or the environment variable `CAOS_TEMP_ROOT`, and removes it after the run. Without a temp
  root it stops with exit 2; it no longer falls back to the system temp folder, and it leaves no bytecode cache in the repository.
- **The re-implementation guard covers the product's method packages** (NB-043 to NB-046). The optional `product.json` key
  `method_packages` (a list of PyPI distribution names, `[]` in the template) declares them. `scripts/check_notebooks.py` reads the public
  top-level functions and classes of each installed package with `ast`, never by importing it, and fails a notebook cell that defines
  one of them, naming the notebook, the cell, the name and the package. A package without an exact `name==version` line in
  `notebooks/requirements.txt` is a finding; a package not installed where the static check runs is an info line (CI stays light), and
  `scripts/run_notebooks.py` fails before any notebook executes. An exact pin may now carry extras (`name[extra]==version`).
- **The PyPI pin check** (NB-047). `python scripts/check_notebooks.py --pypi` (opt-in, never in CI, ADR-0074) reads
  `https://pypi.org/pypi/<name>/<version>/json` for the pin of each method package and fails on anything but HTTP 200, so a Setup cell never
  tells a reader to install a version that is not published.
