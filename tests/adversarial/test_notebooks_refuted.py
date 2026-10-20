"""Adversarial plants for the notebooks (NB-) and the README by areas (RP-): each requirement is attacked on a copy of the
committed example set, with the real guard run as a subprocess. The unplanted copy is the control: it passes, so a plant that
fails proves the rule and not a broken copy. The tests need only the standard library and pytest, so CI runs them.

The execution gate (``scripts/run_notebooks.py --check``) needs the notebook environment, which CI does not install: its two
plants skip without ``.venv-notebooks``."""
from __future__ import annotations

import base64
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from planting import ROOT, guard, make_tree

NOTEBOOK_PYTHON = next((p for p in (ROOT / ".venv-notebooks" / "Scripts" / "python.exe", ROOT / ".venv-notebooks" / "bin" / "python") if p.is_file()), None)
EN = "notebooks/en/02-threshold-and-final-size"
ES = "notebooks/es/02-threshold-and-final-size"
FOLDERS = ("frontend", "app", "data-pipeline", "notebooks", "data", "docs/contracts", "docs", "tests", "scripts", "deploy")


@pytest.fixture(scope="module")
def base(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("nb-base")
    make_tree(dest, "notebooks", "docs/design/SDD.md", ".github", "data/derived", "README.md", "data-pipeline",
              "scripts/check_notebooks.py", "scripts/check_readme_areas.py", "scripts/check_tech_matrix.py", "scripts/run_notebooks.py",
              "scripts/instantiate.py", "scripts/check_template_residue.py", "VERSION", "requirements*.txt", "frontend/package.json", "frontend/package-lock.json", "pyproject.toml")
    return dest


@pytest.fixture
def repo(base: Path, tmp_path: Path) -> Path:
    dest = tmp_path / "repo"
    shutil.copytree(base, dest)
    return dest


def jedit(repo: Path, rel: str, change) -> None:
    """Load a notebook of the copy, change it, write it back."""
    path = repo / rel
    doc = json.loads(path.read_text(encoding="utf-8"))
    change(doc)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def both(repo: Path, rel: str, change) -> None:
    """The same change in the English notebook and its Spanish counterpart (the mirror stays intact)."""
    jedit(repo, f"notebooks/en/{rel}", change)
    jedit(repo, f"notebooks/es/{rel}", change)


def fails(repo: Path, *needles: str, script: str = "check_notebooks.py") -> None:
    r = guard(repo, script)
    assert r.returncode == 1, f"the plant passed {script}:\n{r.stdout}"
    for needle in needles:
        assert needle in r.stdout, f"{needle!r} not in:\n{r.stdout}"


def first_code(doc: dict) -> dict:
    return next(c for c in doc["cells"] if c["cell_type"] == "code")


def test_the_unplanted_copy_passes_both_checks(repo: Path) -> None:
    assert guard(repo, "check_notebooks.py", ok_marker="check_notebooks: OK").returncode == 0
    assert guard(with_dirs(repo), "check_readme_areas.py", ok_marker="check_readme_areas: OK").returncode == 0


def test_a_missing_spanish_index_is_found(repo: Path) -> None:
    (repo / "notebooks" / "es" / "README.md").unlink()
    fails(repo, "notebooks/es/README.md", "layout")


def test_a_spanish_notebook_deleted_breaks_the_mirror(repo: Path) -> None:
    (repo / ES / "03-next-generation-matrix-and-final-size-derivation.ipynb").unlink()
    fails(repo, "mirror", "03-next-generation-matrix-and-final-size-derivation.ipynb")


def test_a_numbering_gap_in_both_trees_is_found(repo: Path) -> None:
    for tree in (EN, ES):
        (repo / tree / "02-the-final-size.ipynb").rename(repo / tree / "04-the-final-size.ipynb")
    fails(repo, "numbering", "no gap or repeat")


def test_a_level_that_decreases_is_found(repo: Path) -> None:
    both(repo, "02-threshold-and-final-size/01-the-threshold.ipynb", lambda d: d["metadata"]["caos"].update(level=3))
    fails(repo, "levels", "decreases inside the topic")


def test_a_topic_without_level_two_is_found(repo: Path) -> None:
    both(repo, "01-getting-started/02-the-method-step-by-step.ipynb", lambda d: d["metadata"]["caos"].update(level=1))
    fails(repo, "no level 2 notebook")


def test_a_missing_reason_for_level_three_is_found(repo: Path) -> None:
    index = repo / "notebooks" / "en" / "README.md"
    text = index.read_text(encoding="utf-8")
    assert "No level 3:" in text
    index.write_text(text.replace("No level 3:", "Level 3 left out:"), encoding="utf-8")
    fails(repo, "01-getting-started", "no level 3 notebook and its row gives no reason")


def test_a_notebook_dropped_from_the_index_is_found(repo: Path) -> None:
    index = repo / "notebooks" / "es" / "README.md"
    text = index.read_text(encoding="utf-8")
    index.write_text(text.replace("01-the-threshold.ipynb", "elided.ipynb"), encoding="utf-8")
    fails(repo, "notebooks/es/README.md", "is not listed")


def test_an_sdd_claim_without_a_level_four_notebook_is_found(repo: Path) -> None:
    sdd = repo / "docs" / "design" / "SDD.md"
    text = sdd.read_text(encoding="utf-8")
    assert "None claimed." in text
    sdd.write_text(text.replace("None claimed.", "- BS-1: a component beyond the state of the art, with its evidence and its source.", 1), encoding="utf-8")
    fails(repo, "BS-1", "covered by no level 4 notebook")
    # a notebook claiming what the SDD does not list is found too
    sdd.write_text(text, encoding="utf-8")
    both(repo, "02-threshold-and-final-size/03-next-generation-matrix-and-final-size-derivation.ipynb", lambda d: d["metadata"]["caos"].update(beyond=["BS-7"]))
    fails(repo, "BS-7")


def test_a_renamed_section_is_found(repo: Path) -> None:
    def rename(doc: dict) -> None:
        for c in doc["cells"]:
            if c["cell_type"] == "markdown" and c["source"][0].startswith("## Results"):
                c["source"][0] = "## Findings\n"
    jedit(repo, "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb", rename)
    fails(repo, "'## Results' is missing", "'## Findings' is not a section of the anatomy")


def test_a_title_cell_turned_into_code_is_found(repo: Path) -> None:
    def retype(doc: dict) -> None:
        doc["cells"][0].update(cell_type="code", execution_count=None, outputs=[])
    jedit(repo, "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb", retype)
    fails(repo, "the first cell is not a markdown cell")


def test_a_code_cell_stripped_of_its_comment_is_found(repo: Path) -> None:
    def strip(doc: dict) -> None:
        cell = first_code(doc)
        cell["source"] = [ln for ln in cell["source"] if not ln.lstrip().startswith("#")]
    jedit(repo, "notebooks/es/01-getting-started/02-the-method-step-by-step.ipynb", strip)
    fails(repo, "carries no comment line")


def test_a_data_path_that_does_not_exist_is_found(repo: Path) -> None:
    both(repo, "01-getting-started/01-the-problem-and-the-data.ipynb", lambda d: d["metadata"]["caos"]["data"].append("data/derived/never-baked/trace.json"))
    fails(repo, "data path 'data/derived/never-baked/trace.json'")
    jedit(repo, "notebooks/en/01-getting-started/02-the-method-step-by-step.ipynb", lambda d: d["metadata"]["caos"].update(packages=["numpy==1.0.0"]))
    fails(repo, "'numpy==1.0.0' is not a pin of notebooks/requirements.txt")


def test_widgets_metadata_is_found(repo: Path) -> None:
    jedit(repo, "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb", lambda d: d["metadata"].update(widgets={"state": {}}))
    fails(repo, "notebook metadata beyond kernelspec, language_info and caos")
    jedit(repo, "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb", lambda d: d["metadata"].pop("widgets"))
    jedit(repo, "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb", lambda d: first_code(d)["metadata"].update(execution={"iopub.execute_input": "t"}))
    fails(repo, "metadata beyond tags")


def test_an_execution_count_gap_is_found(repo: Path) -> None:
    def gap(doc: dict) -> None:
        codes = [c for c in doc["cells"] if c["cell_type"] == "code"]
        codes[2]["execution_count"] = 9
    jedit(repo, "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb", gap)
    fails(repo, "expected 3")


def test_a_planted_traceback_is_found(repo: Path) -> None:
    jedit(repo, "notebooks/en/01-getting-started/02-the-method-step-by-step.ipynb", lambda d: first_code(d)["outputs"].append(
        {"output_type": "error", "ename": "KeyError", "evalue": "x", "traceback": ["Traceback"]}))
    fails(repo, "an error output (KeyError)")
    jedit(repo, "notebooks/es/01-getting-started/01-the-problem-and-the-data.ipynb", lambda d: first_code(d)["outputs"].append(
        {"output_type": "stream", "name": "stderr", "text": "warning\n"}))
    fails(repo, "a stderr stream")


def test_a_machine_path_and_a_token_in_an_output_are_found(repo: Path) -> None:
    jedit(repo, "notebooks/en/02-threshold-and-final-size/01-the-threshold.ipynb", lambda d: first_code(d)["outputs"].append(
        {"output_type": "stream", "name": "stdout", "text": "C:\\Users\\someone\\Documents\\x.csv\n"}))
    fails(repo, "holds a machine path")
    jedit(repo, "notebooks/es/02-threshold-and-final-size/02-the-final-size.ipynb", lambda d: d["cells"][1].update(
        source=d["cells"][1]["source"] + ["\n", "\n", "ghp_" + "Q1w2E3r4T5y6U7i8O9p0A1s2D3f4G5h6"]))
    fails(repo, "holds a token pattern")


def test_an_image_above_the_limit_is_found(repo: Path) -> None:
    big = base64.b64encode(b"\x01" * 500_000).decode()
    jedit(repo, "notebooks/en/01-getting-started/02-the-method-step-by-step.ipynb", lambda d: first_code(d)["outputs"].append(
        {"output_type": "display_data", "data": {"image/png": big}, "metadata": {}}))
    fails(repo, "an image (image/png)", "byte limit")


def test_a_cell_deleted_from_the_spanish_counterpart_is_found(repo: Path) -> None:
    def drop(doc: dict) -> None:
        del doc["cells"][-1]
    jedit(repo, "notebooks/es/01-getting-started/01-the-problem-and-the-data.ipynb", drop)
    fails(repo, "not a full counterpart")


def test_a_source_missing_from_the_sdd_is_found(repo: Path) -> None:
    both(repo, "01-getting-started/01-the-problem-and-the-data.ipynb", lambda d: d["metadata"]["caos"]["sources"].append("https://doi.org/10.1000/never-researched"))
    fails(repo, "'https://doi.org/10.1000/never-researched' is not a source the SDD lists")


def test_a_copy_of_the_engine_in_a_cell_is_found(repo: Path) -> None:
    jedit(repo, "notebooks/en/01-getting-started/02-the-method-step-by-step.ipynb", lambda d: first_code(d).update(
        source=["# my own copy of the engine\n", "def simulate(p, dt=0.25):\n", "    return p"]))
    fails(repo, "defines 'simulate'", "import it instead of re-implementing it")


def test_ci_executing_the_notebooks_is_found(repo: Path) -> None:
    (repo / ".github" / "workflows" / "notebooks.yml").write_text("on: push\njobs:\n  x:\n    steps:\n      - run: python scripts/run_notebooks.py --check\n", encoding="utf-8")
    fails(repo, "notebooks.yml", "the execution is a local release gate, never CI")
    (repo / ".github" / "workflows" / "notebooks.yml").unlink()
    ci = repo / ".github" / "workflows" / "ci.yml"
    ci.write_text(ci.read_text(encoding="utf-8").replace("python scripts/check_notebooks.py", "python scripts/other.py"), encoding="utf-8")
    fails(repo, "no step runs `python scripts/check_notebooks.py`")


def test_an_unpinned_notebook_requirement_is_found(repo: Path) -> None:
    req = repo / "notebooks" / "requirements.txt"
    req.write_text(req.read_text(encoding="utf-8") + "nbconvert>=7\n", encoding="utf-8")
    fails(repo, "'nbconvert>=7' is not an exact pin")
    r = guard(repo, "check_tech_matrix.py")
    assert r.returncode == 1 and "nbconvert" in r.stdout


def test_the_runner_strips_what_was_planted_in_the_metadata() -> None:
    spec = importlib.util.spec_from_file_location("run_notebooks_under_test", ROOT / "scripts" / "run_notebooks.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    nb = {"cells": [{"cell_type": "code", "id": "a", "source": "1", "execution_count": 1, "outputs": [], "metadata": {
        "execution": {"shell.execute_reply": "2026-10-20T10:00:00"}, "scrolled": True}}],
        "metadata": {"kernelspec": {"display_name": "Python 3.13 (x)", "language": "python", "name": "python3"},
                     "language_info": {"name": "python", "version": "3.13.1"}, "caos": {}, "widgets": {}, "vscode": {"interpreter": "x"}},
        "nbformat": 4, "nbformat_minor": 5}
    clean = runner.strip_volatile(nb)
    assert set(clean["metadata"]) == {"kernelspec", "language_info", "caos"} and clean["metadata"]["language_info"] == {"name": "python"}
    assert clean["cells"][0]["metadata"] == {}


def run_release_gate(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(NOTEBOOK_PYTHON), str(repo / "scripts" / "run_notebooks.py"), *args], capture_output=True, encoding="utf-8",
                          errors="replace", cwd=repo, timeout=600)


@pytest.mark.skipif(NOTEBOOK_PYTHON is None, reason="the notebook environment is not built (scripts/setup.sh --notebooks)")
def test_a_raising_notebook_fails_the_release_gate(repo: Path) -> None:
    only = "notebooks/en/02-threshold-and-final-size/01-the-threshold.ipynb"
    assert run_release_gate(repo, "--check", "--only", only).returncode == 0
    jedit(repo, only, lambda d: first_code(d).update(source=["# this cell raises\n", "raise RuntimeError('planted')"]))
    r = run_release_gate(repo, "--check", "--only", only)
    assert r.returncode == 1 and "01-the-threshold.ipynb" in r.stdout and "RuntimeError" in r.stdout


@pytest.mark.skipif(NOTEBOOK_PYTHON is None, reason="the notebook environment is not built (scripts/setup.sh --notebooks)")
def test_a_missing_artifact_stops_the_run_naming_its_path(repo: Path) -> None:
    only = "notebooks/en/02-threshold-and-final-size/01-the-threshold.ipynb"
    (repo / "data" / "derived" / "manifests" / "EX02_epidemic.json").unlink()
    r = run_release_gate(repo, "--check", "--only", only)
    assert r.returncode == 1 and "EX02_epidemic.json" in r.stdout, r.stdout


# ---------------------------------------------------------------- the README by areas

def with_dirs(repo: Path) -> Path:
    for folder in FOLDERS:
        (repo / folder).mkdir(parents=True, exist_ok=True)
    return repo


def readme_edit(repo: Path, old: str, new: str) -> None:
    path = repo / "README.md"
    text = path.read_text(encoding="utf-8")
    assert old in text, f"README.md does not contain {old!r}: the plant would change nothing"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_a_readme_without_areas_is_found(repo: Path) -> None:
    readme_edit(with_dirs(repo), "## Areas", "## What is in it")
    fails(repo, "no section '## Areas'", script="check_readme_areas.py")


def test_a_dropped_area_row_is_found(repo: Path) -> None:
    text = (repo / "README.md").read_text(encoding="utf-8")
    kept = "\n".join(ln for ln in text.split("\n") if not ln.startswith("| Notebooks |"))
    (repo / "README.md").write_text(kept, encoding="utf-8")
    fails(with_dirs(repo), "the area 'Notebooks' has no row", script="check_readme_areas.py")


def test_a_row_with_no_status_is_found(repo: Path) -> None:
    readme_edit(with_dirs(repo), "| active | The committed derived artifacts", "| somewhere in between | The committed derived artifacts")
    fails(repo, "the area 'Data' has no status", script="check_readme_areas.py")
    readme_edit(repo, "dormant: this solution does not require it at the moment", "dormant")
    fails(repo, "'API' is dormant with no reason", script="check_readme_areas.py")


def test_a_dead_folder_link_is_found(repo: Path) -> None:
    with_dirs(repo)
    shutil.rmtree(repo / "deploy")
    fails(repo, "links 'deploy/', which does not exist", script="check_readme_areas.py")


def test_a_packages_row_without_pypi_is_found(repo: Path) -> None:
    readme_edit(with_dirs(repo), "[numpy 2.4.6](https://pypi.org/project/numpy/2.4.6/), [source](https://github.com/numpy/numpy)", "numpy")
    fails(repo, "links no package on PyPI", script="check_readme_areas.py")


def test_an_instantiate_that_drops_the_areas_writes_a_failing_readme(repo: Path) -> None:
    path = repo / "scripts" / "instantiate.py"
    text = path.read_text(encoding="utf-8")
    assert "*areas(a)," in text
    path.write_text(text.replace("*areas(a),", ""), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("instantiate_planted", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import argparse
    args = argparse.Namespace(slug="demo", name="Demo", repo="CAOS_Demo", deploy="pages", domain="", visibility="public",
                              tagline_en="One.", tagline_es="Una.", holder="H", year=2026, no_run=True)
    (repo / "README.md").write_text(module.readme(args), encoding="utf-8")
    fails(with_dirs(repo), "no section '## Areas'", script="check_readme_areas.py")


def test_the_example_notebooks_left_in_a_product_are_listed(repo: Path, tmp_path: Path) -> None:
    product = tmp_path / "product"
    shutil.copytree(repo / "notebooks", product / "notebooks")
    shutil.copytree(repo / "scripts", product / "scripts")
    for n in range(12):
        (product / "src").mkdir(exist_ok=True)
        (product / "src" / f"m{n}.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=product, check=True)
    r = subprocess.run([sys.executable, str(product / "scripts" / "check_template_residue.py"), str(product)], capture_output=True, text=True, cwd=product)
    assert r.returncode == 1 and "notebooks/en/01-getting-started/01-the-problem-and-the-data.ipynb" in r.stdout, r.stdout
