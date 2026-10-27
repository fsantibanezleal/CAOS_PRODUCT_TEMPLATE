"""The example notebooks (the SIR set under notebooks/): what their text must hold, and the residue guard listing them. They need the
template's example, so they live here and instantiate.py removes them with the example; a product states the same rules for its own
notebooks in its own tests. The static check on synthetic trees stays in tests/test_check_notebooks.py."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from test_check_notebooks import CHECK

ROOT = Path(__file__).resolve().parents[2]


def test_the_committed_set_covers_both_languages_and_a_level_three() -> None:
    trees = {lang: sorted(p.relative_to(ROOT / "notebooks" / lang).as_posix() for p in (ROOT / "notebooks" / lang).rglob("*.ipynb")) for lang in ("en", "es")}
    assert trees["en"] == trees["es"] and len(trees["en"]) >= 5
    levels = {json.loads((ROOT / "notebooks" / "en" / rel).read_text(encoding="utf-8"))["metadata"]["caos"]["level"] for rel in trees["en"]}
    assert levels == {1, 2, 3}


def test_the_example_notebooks_import_the_engine_and_never_redefine_it() -> None:
    engine = CHECK.engine_names(ROOT)
    assert "simulate" in engine
    for path in (ROOT / "notebooks").rglob("*.ipynb"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        code = "\n".join(CHECK.text_of(c["source"]) for c in doc["cells"] if c["cell_type"] == "code")
        assert "from pipeline.model.sir import simulate" in code, path.name
        assert not (CHECK.defined_names(code) & engine), path.name


def test_the_residue_guard_lists_the_example_notebooks(tmp_path: Path) -> None:
    """An instantiated product (no sentinel) sees the example notebooks as residue to replace, like the rest of the example."""
    product = tmp_path / "product"
    shutil.copytree(ROOT / "notebooks", product / "notebooks")
    for n in range(12):
        (product / "src").mkdir(exist_ok=True)
        (product / "src" / f"m{n}.py").write_text("x = 1\n", encoding="utf-8")
    shutil.copytree(ROOT / "scripts", product / "scripts", ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
    subprocess.run(["git", "init", "-q"], cwd=product, check=True)
    r = subprocess.run([sys.executable, str(product / "scripts" / "check_template_residue.py"), str(product)], capture_output=True, text=True, cwd=product)
    assert r.returncode == 1 and "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb" in r.stdout, r.stdout


def cells_of(lang: str, rel: str) -> list[dict]:
    return json.loads((ROOT / "notebooks" / lang / rel).read_text(encoding="utf-8"))["cells"]


@pytest.mark.parametrize("lang", ["en", "es"])
def test_the_convergence_cell_names_the_case_it_runs(lang: str) -> None:
    """F1: the figure is titled EX02_epidemic, so the cell binds that case itself instead of reusing the last loop variable."""
    cells = cells_of(lang, "01-getting-started/02-the-method-step-by-step.ipynb")
    cell = next(c for c in cells if c["cell_type"] == "code" and "steps = [1.0, 0.5" in CHECK.text_of(c["source"]))
    code = CHECK.text_of(cell["source"])
    body = [ln for ln in code.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert body[0] == 'p = params_of("EX02_epidemic")', body[0]
    printed = "".join(CHECK.text_of(o.get("text", "")) for o in cell["outputs"])
    assert "0.933717" in printed and "0.300894" not in printed, printed  # EX02's first attack rate, not EX04's


@pytest.mark.parametrize("lang,fixed,stale", [("en", "0.000002", "about 0.00005 for the cases that ended"),
                                              ("es", "0,000002", "cerca de 0,00005 en los casos que terminaron")])
def test_the_fast_burn_difference_is_stated_for_both_cases(lang: str, fixed: str, stale: str) -> None:
    """F12: the derived relation differs from level 2 by 0.00005 for the epidemic case and 0.000002 for the fast burn."""
    text = "\n".join(CHECK.text_of(c["source"]) for c in cells_of(lang, "02-threshold-and-final-size/03-next-generation-matrix-and-final-size-derivation.ipynb"))
    assert fixed in text and stale not in text


def test_the_spanish_final_size_notebook_uses_one_decimal_separator() -> None:
    """F13: the Spanish prose writes its decimals with a comma, every number of the notebook's prose, in the same cell too."""
    import re
    for c in cells_of("es", "02-threshold-and-final-size/02-the-final-size.ipynb"):
        if c["cell_type"] == "markdown":
            prose = re.sub(r"`[^`]*`|https?://\S+|10\.\d{4,9}/\S+", "", CHECK.text_of(c["source"]))
            assert not re.search(r"\d\.\d", prose), prose[:200]


def test_the_final_size_solver_is_imported_by_the_notebooks_and_defined_in_none() -> None:
    """F14: a method is imported, never defined in a notebook; the solver lives in data-pipeline/pipeline/oracles.py."""
    assert "final_size" in CHECK.engine_names(ROOT)
    users = 0
    for path in (ROOT / "notebooks").rglob("*.ipynb"):
        code = "\n".join(CHECK.text_of(c["source"]) for c in json.loads(path.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code")
        assert "final_size" not in CHECK.defined_names(code), path.name
        if "final_size(" in code:
            users += 1
            assert "from pipeline.oracles import final_size" in code, path.name
    assert users == 6
