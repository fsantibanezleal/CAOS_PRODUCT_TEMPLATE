"""scripts/check_internal_names.py: the tier names and the claim ids never reach a reader (template 0.14.000)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_internal_names as cin  # noqa: E402


def _nb(cells: list[tuple[str, str]], title: str = "Euler against a higher-order solver", outputs: str = "") -> dict:
    out = []
    for kind, text in cells:
        cell = {"cell_type": kind, "id": f"c{len(out)}", "metadata": {}, "source": [text]}
        if kind == "code":
            cell.update({"execution_count": 1, "outputs": [{"output_type": "stream", "name": "stdout", "text": [outputs]}]})
        out.append(cell)
    return {"cells": out, "metadata": {"caos": {"title": title, "level": 3}}, "nbformat": 4, "nbformat_minor": 5}


def _repo(tmp: Path, files: dict[str, str | dict]) -> Path:
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(content) if isinstance(content, dict) else content, encoding="utf-8")
    return tmp


CLEAN_NB = _nb([("markdown", "# Euler against RK45\n\n**Question:** how much accuracy does a step buy?"),
                ("markdown", "## Comparison\n\nSciPy's RK45, the published method, on the same system."),
                ("code", "# Run RK45 beside the engine\nprint('error', 0.01)"),
                ("markdown", "## References\n\n- Doe (2020), A state-of-the-art survey of solvers.")])


def test_a_clean_product_passes(tmp_path):
    root = _repo(tmp_path, {"notebooks/en/01-topic/03-a-higher-order-solver.ipynb": CLEAN_NB, "README.md": "# Product\n\nIt solves the model.\n"})
    assert cin.check(root) == []


def test_a_cited_title_in_references_is_kept(tmp_path):
    root = _repo(tmp_path, {"README.md": "# P\n\n## References\n\n- Roe (2021), Beyond the state of the art in ODEs.\n"})
    assert cin.check(root) == []


def test_every_reader_surface_of_a_notebook_is_read(tmp_path):
    nb = _nb([("markdown", "# State of the art: solvers"),
              ("markdown", "## Estado del arte\n\nEl método más allá del estado del arte."),
              ("code", "# the SOTA solver, claim BS-2\nplt.title('beyond-SOTA')"),
              ], title="Beyond the state of the art: solvers", outputs="M-4 wins")
    root = _repo(tmp_path, {"notebooks/es/01-topic/07-state-of-the-art-solvers.ipynb": nb})
    found = "\n".join(cin.check(root))
    for piece in ("the file name names a tier", "caos.title", "cell 0", "cell 1", "cell 2", "cell 2 output", "'BS-2'", "'SOTA'",
                  "'M-4'", "'estado del arte'"):
        assert piece.lower() in found.lower(), (piece, found)


def test_a_level_4_file_name_with_the_tier_prefix_fails(tmp_path):
    root = _repo(tmp_path, {"notebooks/en/01-topic/08-beyond-the-dependence-band.ipynb": CLEAN_NB})
    assert any("the file name names a tier" in f for f in cin.check(root))


def test_the_app_strings_are_read_and_its_identifiers_are_not(tmp_path):
    ts = ("const tier = 'sota';\nexport const TITLE = { en: 'State of the art', es: 'Estado del arte' };\n"
          "// a comment about the beyond the state of the art plan is code, not a string\nconst id = 'BS-13';\n")
    root = _repo(tmp_path, {"frontend/src/pages/Methodology.tsx": ts, "frontend/src/pages/Methodology.test.tsx": ts})
    found = cin.check(root)
    assert any("Methodology.tsx:2:" in f for f in found) and any("'BS-13'" in f for f in found)
    assert not any(":3:" in f for f in found), found
    assert not any("test.tsx" in f for f in found)
    assert not any("'sota'" in f.lower() and ":1:" in f for f in found), found


def test_manuscripts_and_their_product_json_titles_are_read_but_not_the_bibliography(tmp_path):
    tex = ("\\section{The state of the art}\nText.\n\\begin{thebibliography}{9}\n\\bibitem{a} A state of the art review.\n"
           "\\end{thebibliography}\n")
    product = {"manuscripts": [{"kind": "technical-report", "title": "A beyond-SOTA method for the model"}]}
    root = _repo(tmp_path, {"manuscripts/report/main.tex": tex, "manuscripts/report/refs.bib": "@article{x, title={State of the art}}",
                            "product.json": product})
    found = cin.check(root)
    assert any("main.tex:1:" in f for f in found)
    assert not any("main.tex:4:" in f for f in found) and not any("refs.bib" in f for f in found)
    assert any("manuscripts[0].title" in f for f in found)


def test_the_tier_words_banking_needs_stay_allowed(tmp_path):
    root = _repo(tmp_path, {"README.md": "# P\n\nTier 1 capital, the classical Merton model and the methods of each tier.\n"})
    assert cin.check(root) == []


def test_the_command_line_exits_1_with_findings_and_0_when_clean(tmp_path):
    bad = _repo(tmp_path / "bad", {"README.md": "# P\n\n## State of the art\n"})
    good = _repo(tmp_path / "good", {"README.md": "# P\n\n## Comparison\n"})
    script = str(ROOT / "scripts" / "check_internal_names.py")
    r_bad = subprocess.run([sys.executable, script, str(bad)], capture_output=True, text=True)
    r_good = subprocess.run([sys.executable, script, str(good)], capture_output=True, text=True)
    assert r_bad.returncode == 1 and "README.md:3" in r_bad.stdout and cin.RULE in r_bad.stdout
    assert r_good.returncode == 0, r_good.stdout
