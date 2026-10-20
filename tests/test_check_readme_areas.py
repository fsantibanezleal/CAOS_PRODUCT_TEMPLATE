"""The README-by-areas gate (scripts/check_readme_areas.py): one plant per rule, built in a temporary repository, a control,
the committed README, and the README that scripts/instantiate.py writes for a product."""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load("check_readme_areas")
FOLDERS = ["frontend", "app", "data-pipeline", "notebooks", "data", "docs/contracts", "docs", "tests", "scripts", "deploy"]

ROWS = {
    "Web": "| Web | [`frontend/`](frontend/) | active | the workbench |",
    "API": "| API | [`app/`](app/) | dormant: this solution does not require it at the moment | the API |",
    "Core pipelines": "| Core pipelines | [`data-pipeline/`](data-pipeline/) | active | the bake |",
    "Packages": "| Packages | (PyPI) [numpy](https://pypi.org/project/numpy/) | active: consumes numpy | the packages |",
    "Notebooks": "| Notebooks | [`notebooks/`](notebooks/) | active | the notebooks |",
    "Data": "| Data | [`data/`](data/) | active | the artifacts |",
    "Contracts": "| Contracts | [`docs/contracts/`](docs/contracts/) | active | the catalog |",
    "Documentation": "| Documentation | [`docs/`](docs/) | active | the SDD |",
    "Tests and gates": "| Tests and gates | [`tests/`](tests/), [`scripts/`](scripts/) | active | the suites |",
    "Deploy": "| Deploy | [`deploy/`](deploy/) | active: GitHub Pages | where |",
}


def readme(rows: dict[str, str] | None = None, head: str = "## Areas") -> str:
    body = "\n".join((rows or ROWS).values())
    return f"# Product\n\nPurpose.\n\n{head}\n\n| Area | Folder | Status | What it holds |\n|---|---|---|---|\n{body}\n\n## Run it\n\ntext\n"


def make(tmp_path: Path, text: str) -> Path:
    for f in FOLDERS:
        (tmp_path / f).mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text(text, encoding="utf-8")
    return tmp_path


def found(root: Path, *needles: str) -> bool:
    return any(all(n in f for n in needles) for f in CHECK.findings_of(root))


def test_a_complete_readme_passes(tmp_path: Path) -> None:
    assert CHECK.findings_of(make(tmp_path, readme())) == []


def test_a_readme_without_the_areas_section_is_found(tmp_path: Path) -> None:
    assert found(make(tmp_path, readme(head="## What is in it")), "no section '## Areas'")
    (tmp_path / "README.md").unlink()
    assert found(tmp_path, "README.md: missing")
    # a heading inside a code fence is not the section
    root = make(tmp_path, "# P\n\n```\n## Areas\n```\n")
    assert found(root, "no section '## Areas'")


def test_an_area_without_its_row_is_found(tmp_path: Path) -> None:
    for area in ROWS:
        rows = {k: v for k, v in ROWS.items() if k != area}
        assert found(make(tmp_path, readme(rows)), f"the area {area!r} has no row"), area
    rows = dict(ROWS, Web=ROWS["Web"] + "\n" + ROWS["Web"])
    assert found(make(tmp_path, readme(rows)), "'Web'", "more than one row")


def test_a_row_without_a_status_is_found(tmp_path: Path) -> None:
    rows = dict(ROWS, Data="| Data | [`data/`](data/) | in progress | the artifacts |")
    assert found(make(tmp_path, readme(rows)), "'Data'", "no status")
    rows = dict(ROWS, API="| API | [`app/`](app/) | dormant | the API |")
    assert found(make(tmp_path, readme(rows)), "'API'", "dormant with no reason")
    rows = dict(ROWS, API="| API | [`app/`](app/) | dormant: not needed | the API |")
    assert found(make(tmp_path, readme(rows)), "'API'", "dormant with no reason")
    rows = dict(ROWS, Web="| Web | [`frontend/`](frontend/) | active |  |")
    assert found(make(tmp_path, readme(rows)), "'Web'", "no 'What it holds' cell")


def test_a_folder_link_that_does_not_exist_is_found(tmp_path: Path) -> None:
    root = make(tmp_path, readme())
    shutil.rmtree(root / "notebooks")
    assert found(root, "'Notebooks'", "links 'notebooks/', which does not exist")
    rows = dict(ROWS, Web="| Web | [`web/`](web/) | active | the workbench |")
    assert found(make(tmp_path, readme(rows)), "'Web'", "does not link its folder frontend/")
    rows = dict(ROWS, **{"Tests and gates": "| Tests and gates | [`tests/`](tests/) | active | the suites |"})
    assert found(make(tmp_path, readme(rows)), "'Tests and gates'", "does not link its folder scripts/")


def test_the_packages_row_must_link_pypi(tmp_path: Path) -> None:
    rows = dict(ROWS, Packages="| Packages | (PyPI) | active: none yet | the packages |")
    assert found(make(tmp_path, readme(rows)), "'Packages'", "links no package on PyPI")


def test_the_template_readme_states_every_area() -> None:
    assert CHECK.findings_of(ROOT) == []
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## What is in it" not in text and "## Areas" in text


def test_the_readme_instantiate_writes_states_every_area(tmp_path: Path) -> None:
    """A product made from the template starts with a README that passes the check (the CI step runs on the first push)."""
    spec = importlib.util.spec_from_file_location("instantiate", ROOT / "scripts" / "instantiate.py")
    inst = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inst)
    args = argparse.Namespace(slug="demo", name="Demo", repo="CAOS_Demo", deploy="pages", domain="demo.example.org", visibility="public",
                              tagline_en="One line.", tagline_es="Una línea.", holder="H", year=2026, no_run=True)
    text = inst.readme(args)
    assert "## Areas" in text and re.search(r"setup\.sh --notebooks", text)
    assert CHECK.findings_of(make(tmp_path, text)) == []


def test_instantiate_leaves_a_passing_readme_and_the_notebooks(tmp_path: Path) -> None:
    """The whole instantiate step, on a copy: the product README passes, the example notebooks stay (the residue guard lists them)."""
    product = tmp_path / "p"
    for rel in ("scripts", "docs", "deploy", ".github", "frontend/package.json", "frontend/package-lock.json", "product.json", "VERSION",
                "CHANGELOG.md", "LICENSE", ".template-source", "notebooks", "data-pipeline", "tests", "data", "app"):
        src = ROOT / rel
        if src.is_dir():
            shutil.copytree(src, product / rel, ignore=shutil.ignore_patterns("__pycache__", "node_modules", ".venv*", "dist"))
        elif src.is_file():
            (product / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, product / rel)
    (product / "frontend" / "public").mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(product / "scripts" / "instantiate.py"), "--slug", "demo", "--name", "Demo", "--repo", "CAOS_Demo",
                        "--deploy", "pages", "--domain", "demo.example.org", "--visibility", "public", "--tagline-en", "One line.",
                        "--tagline-es", "Una linea.", "--no-run"], capture_output=True, text=True, cwd=product)
    assert r.returncode == 0, r.stdout + r.stderr
    check = subprocess.run([sys.executable, str(product / "scripts" / "check_readme_areas.py"), str(product)], capture_output=True, text=True, cwd=product)
    assert check.returncode == 0, check.stdout
    assert (product / "notebooks" / "en" / "README.md").is_file() and not (product / ".template-source").exists()


@pytest.mark.parametrize("area", [a for a, _ in CHECK.AREAS])
def test_every_conventional_area_is_a_row_of_the_template_readme(area: str) -> None:
    assert re.search(rf"^\| {re.escape(area)} \|", (ROOT / "README.md").read_text(encoding="utf-8"), re.M), area
