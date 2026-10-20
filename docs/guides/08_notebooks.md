# Guide: write the product's notebooks

The notebooks are the product's didactic layer: they teach a reader, step by step and on the product's own data, how
its methods work, where each method stands against the state of the art, and what the product adds beyond it. They
import the product's methods and never re-implement them; logic that exists only in a notebook is incomplete. The
rule is CAOS_MANAGE `conventions/product-notebooks.md`; this guide is how a product applies it. The template ships an
example set on the SIR model, which a product replaces (`scripts/check_template_residue.py` lists it).

## 1. Lay out the folder

```
notebooks/
  README.md          the entry (both languages): what the set teaches, how to run it
  requirements.txt   exact pins: the product's PyPI packages first, then the notebook runtime
  en/README.md       the index: topics in order, each notebook with its level, what it teaches, and a reason for a missing level 3
  en/01-<topic>/01-<notebook>.ipynb
  es/README.md       the same index, in Spanish
  es/01-<topic>/01-<notebook>.ipynb
```

- The two trees hold the same notebooks at the same relative paths; the slugs are English so the mirror is checkable.
  Each notebook is written wholly in its tree's language: prose, comments, labels and printed text.
- Topics and notebooks are numbered with two digits, contiguous from `01`. Topic `01` is the entry: install the package,
  load the product's data, get a first result. Each later topic says which earlier ones it needs.
- A topic folder holds only notebooks.

## 2. Choose the levels

| Level | Name | What it holds |
|---|---|---|
| 1 | Fundamentals | the problem in its context, the data, the idea of the method, a first run on a small real slice |
| 2 | The method in practice | the full algorithm step by step on the data, every intermediate shown, the product's validation of the result |
| 3 | State of the art | the current methods the product's research found, with sources, run or reproduced and compared with level 2 on the same data |
| 4 | Beyond the state of the art | the product's own components that go further, with the evidence |

- Every topic has levels 1 and 2. The level never decreases with the notebook number.
- A topic whose method has state-of-the-art research in the product's dossiers has a level 3 notebook. A topic without
  one says why on its row of each language's index, as `No level 3: <reason>` (`Sin nivel 3: <motivo>` in Spanish),
  four words or more.
- Every component the SDD claims beyond the state of the art has a level 4 notebook (next section).

## 3. Claim and cover a component beyond the state of the art

The SDD's section `## Beyond the state of the art` is either `None claimed.` (the example) or a list of claims, each
with an identifier of the form `BS-<n>` (the first is `BS-1`, then `BS-2`, and so on), its evidence and its source. For
each claim:

1. State it in the SDD section with its identifier, what it adds, the measured evidence and the source it goes beyond.
2. Write a level 4 notebook in each language whose `caos.beyond` lists the identifier, with the sections
   `State of the art` and `Beyond the state of the art` and the evidence: measured size and power, a reconciliation, a
   case the state of the art gets wrong.
3. `scripts/check_notebooks.py` fails an identifier no level 4 notebook covers in each language, and a notebook that
   claims one the SDD does not list.

## 4. Write each notebook

The first cell is markdown: title, level, prerequisites (the earlier notebooks), reading time. Then these second-level
sections, in this order, named in the tree's language:

| English | Spanish | Required |
|---|---|---|
| Objectives | Objetivos | always |
| Setup | Preparación | always |
| Data | Datos | always |
| Method | Método | always |
| State of the art | Estado del arte | level 3 and 4 |
| Beyond the state of the art | Más allá del estado del arte | level 4 |
| Results | Resultados | always |
| Summary | Resumen | always |
| References | Referencias | always |

- **Setup:** the install line in a markdown code block with the exact pins of `notebooks/requirements.txt`
  (`pip install <package>==<version>`), then a code cell that imports the packages and prints their versions. A product's
  own package that is not yet on PyPI is installed from its release tag, saying so. A notebook never runs `pip`.
- **Data:** the owner, the URL, the licence class and the file each source gives; read committed artifacts by a path
  relative to the repository root. No machine path, ever.
- **Method:** each equation in markdown with its source (DOI or URL), then run through the product's package, one step per
  cell. The example imports the pipeline by path (`data-pipeline/`) because it publishes no package; a product imports its
  own PyPI package.
- **Step by step:** every code cell is directly preceded by a markdown cell that says what it does and why, and carries at
  least one comment line. One idea per cell.
- **Results** interprets every figure and table: what it shows, what a validator concludes, what it does not show.
- **References** lists every source cited with its DOI or URL. Content comes from the persisted research (the dossiers,
  addenda and SDD), never from memory; each state-of-the-art claim carries its source line.
- Every random draw is seeded.

### The metadata

The notebook metadata holds `kernelspec`, `language_info` and one `caos` block; a cell's metadata holds only `tags`:

```json
"caos": {
  "language": "en",
  "topic": "01-getting-started",
  "level": 2,
  "title": "Forward Euler step by step, the threshold and the final-size oracle",
  "packages": ["numpy==2.4.6", "matplotlib==3.11.2"],
  "data": ["data/derived/manifests/index.json"],
  "sources": ["https://doi.org/10.1098/rspa.1927.0118"],
  "beyond": []
}
```

`language` is the tree, `topic` the folder, every `packages` entry an exact pin of `notebooks/requirements.txt` and written
in the notebook's text, every `data` path a file of the repository, `sources` a non-empty list of links, and `beyond` the
SDD's `BS-` identifiers a level 4 notebook demonstrates (empty below level 4). A notebook and its counterpart in the other
language carry the same level, packages, data, beyond claims and the same sequence of cell kinds.

## 5. Run and check

```bash
./scripts/setup.sh --notebooks             # .venv-notebooks from notebooks/requirements.txt (setup.ps1 -Notebooks on Windows)
python scripts/run_notebooks.py            # every notebook, top to bottom, fresh kernel, outputs written in place
python scripts/run_notebooks.py --only notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb
python scripts/run_notebooks.py --check    # executes copies in a temporary folder, writes nothing, fails on any error
python scripts/check_notebooks.py          # the static check
python scripts/check_readme_areas.py       # the README by areas
```

- Only the runner writes outputs, so execution counts run 1, 2, 3 with no gap and volatile metadata (timings, the kernel's
  version, widget state) never reaches the commit. The outputs are committed: the notebooks read as finished material on
  GitHub. A missing artifact fails the run with its path; nothing stands in for it.
- `scripts/check_notebooks.py` is static and runs in CI and locally: layout, mirror, numbering, levels and their coverage,
  anatomy, metadata, and cleanliness (no error output or stderr stream, no machine path, no token, a notebook up to 3 MB and
  an image up to 400 KB, the limits in the script). It also fails a CI workflow that executes the notebooks.
- `scripts/run_notebooks.py --check` is a local release gate: run it before every release. It never runs in CI (ADR-0074).
- The notebook environment `.venv-notebooks` is never committed; on a device with a venvs root it is a junction to it.

## 6. The README by areas

The README's `## Areas` section has one row per area (Web, API, Core pipelines, Packages, Notebooks, Data, Contracts,
Documentation, Tests and gates, Deploy) with its folder as a link, its status (`active`, or `dormant: <reason>`) and what
it holds. `scripts/check_readme_areas.py` fails a missing section, area or status and a link to a folder that does not
exist. The Packages row lists each package the product publishes or consumes for its methods with its version and its PyPI
and repository links.
