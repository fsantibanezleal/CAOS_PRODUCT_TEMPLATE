# Notebooks / Cuadernos

The didactic layer of the product: notebooks that teach, step by step and on the product's own data, how its methods
work, where each method stands against the state of the art and what the product adds beyond it. They import the
product's methods and never re-implement them. The rule is `CAOS_MANAGE` `conventions/product-notebooks.md`, carried by
the template from release 0.10.000 (guide: [`docs/guides/08_notebooks.md`](../docs/guides/08_notebooks.md)).

La capa didáctica del producto: cuadernos que enseñan, paso a paso y con los datos propios del producto, cómo
funcionan sus métodos, dónde queda cada método frente al estado del arte y qué agrega el producto más allá. Importan los
métodos del producto y nunca los reimplementan.

## The two trees / Los dos árboles

| Language | Index | Folder |
|---|---|---|
| English | [en/README.md](en/README.md) | [en/](en/) |
| Español | [es/README.md](es/README.md) | [es/](es/) |

The two trees hold the same notebooks at the same relative paths (the slugs are English, so the mirror is checkable);
each notebook is written wholly in its tree's language. Topics run from simple to complex, notebooks inside a topic by
level: 1 fundamentals, 2 the method in practice, 3 state of the art, 4 beyond the state of the art.

Los dos árboles tienen los mismos cuadernos en las mismas rutas relativas (los nombres están en inglés, así que el
espejo se puede comprobar); cada cuaderno está escrito entero en el idioma de su árbol.

## Run them / Correrlos

```bash
./scripts/setup.sh --notebooks             # .venv-notebooks from notebooks/requirements.txt (setup.ps1 -Notebooks on Windows)
python scripts/run_notebooks.py            # executes every notebook top to bottom in a fresh kernel and writes the outputs in place
python scripts/run_notebooks.py --check    # executes copies, writes nothing, fails on any error (a local release gate, never CI)
python scripts/check_notebooks.py          # the static check: layout, mirror, levels, anatomy, metadata, clean, pins (CI and local)
```

Only the runner writes a notebook's outputs; the committed notebooks are the runner's output. To read one, open it on
GitHub or in any Jupyter client (select the `.venv-notebooks` kernel to run it).

## The example set / El conjunto de ejemplo

The template's example product (the SIR epidemic model) ships two topics. A product replaces them with its own;
`scripts/check_template_residue.py` lists them until it does.

- `01-getting-started`: the problem, the baked traces, a first run of the engine, then the method step by step.
- `02-threshold-and-final-size`: the threshold, the final size, and the state of the art that the research basis names.

`requirements.txt` pins the notebook environment exactly: the product's PyPI packages first, then the runtime that
executes the notebooks.
