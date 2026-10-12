"""Unit tests of the spec-area guards (0.05.000): check_sdd (research basis, resources, validation), check_tech_matrix
and check_contract_versions. Each test builds a small throwaway tree, runs the real script on it as a subprocess and
asserts its exit code and message. The whole-repository plants are in tests/adversarial/."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True)


# ---------------------------------------------------------------- check_sdd

SECTIONS = ("Problem and non-goals", "Research basis", "Sizing and contracts", "Technology and versions", "Resources",
            "Lanes", "Method ladder", "Cases", "Oracles", "Deploy driver", "Risks and kill criteria", "ADR fit")
RESEARCH = ("- Kermack 1927, https://doi.org/10.1098/rspa.1927.0118\n- Miller 2012, doi 10.1007/s11538-012-9749-6\n"
            "- Hethcote 2000, https://doi.org/10.1137/S0036144500371907\n\nUNVERIFIED: none\n")
RESOURCES = ("| stage | memory | disk | time | where it runs |\n|---|---|---|---|---|\n"
             "| bake | 120 MB | 1 MB | 0.1 s | workstation |\n| tests | 200 MB | 5 MB | 10 s | workstation |\n"
             "| build | 400 MB | 2 MB | 8 s | workstation |\n| deploy payload | 0 | 2 MB | 5 s | CI |\n")


def sdd_text(research: str = RESEARCH, resources: str = RESOURCES, skip: str = "") -> str:
    out = ["# SDD\n"]
    for name in SECTIONS:
        if name == skip:
            continue
        body = {"Research basis": research, "Resources": resources}.get(name, "text\n")
        out.append(f"## {name}\n\n{body}\n")
    return "\n".join(out)


def sdd_tree(tmp: Path, *, validation: str | None, sdd: str | None = None) -> Path:
    (tmp / "docs" / "design" / "features" / "f").mkdir(parents=True)
    (tmp / "tests").mkdir()
    (tmp / "tests" / "test_x.py").write_text("def test_a():\n    pass\n\ndef test_b():\n    pass\n", encoding="utf-8")
    (tmp / "docs" / "design" / "SDD.md").write_text(sdd if sdd is not None else sdd_text(), encoding="utf-8")
    (tmp / "docs" / "design" / "features" / "f" / "requirements.md").write_text(
        "| ID | Requirement | Gate |\n|---|---|---|\n"
        "| FX-001 | THE x SHALL a. | `tests/test_x.py::test_a` |\n| FX-002 | THE x SHALL b. | `tests/test_x.py::test_b` |\n",
        encoding="utf-8")
    if validation is not None:
        (tmp / "docs" / "design" / "features" / "f" / "validation.md").write_text(validation, encoding="utf-8")
    return tmp


GOOD_VALIDATION = ("| requirement | adversarial check | gate |\n|---|---|---|\n"
                   "| FX-001 | a NaN parameter is rejected | `tests/test_x.py::test_a` |\n"
                   "| FX-002 | a planted drift fails | `tests/test_x.py::test_b` |\n")


def test_sdd_clean_tree_passes(tmp_path):
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION)))
    assert r.returncode == 0, r.stdout


def test_sdd_missing_new_section_is_named(tmp_path):
    t = sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=sdd_text(skip="Technology and versions"))
    r = run("check_sdd.py", str(t))
    assert r.returncode == 1 and "Technology and versions" in r.stdout


def test_sdd_old_contracts_section_name_no_longer_counts(tmp_path):
    text = sdd_text().replace("## Sizing and contracts", "## Contracts")
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=text)))
    assert r.returncode == 1 and "Sizing and contracts" in r.stdout


def test_sdd_research_with_two_sources_fails(tmp_path):
    two = ("- Kermack 1927, 10.1098/rspa.1927.0118\n- Miller 2012, https://doi.org/10.1007/s11538-012-9749-6\n\n"
           "UNVERIFIED: none\n")
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=sdd_text(research=two))))
    assert r.returncode == 1 and "research basis" in r.stdout.lower() and "2" in r.stdout


def test_sdd_research_without_an_unverified_line_fails(tmp_path):
    no = RESEARCH.replace("UNVERIFIED: none", "all fine")
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=sdd_text(research=no))))
    assert r.returncode == 1 and "UNVERIFIED" in r.stdout


def test_sdd_resources_with_an_empty_cell_or_tbd_fails(tmp_path):
    empty = RESOURCES.replace("| 120 MB |", "|  |")
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=sdd_text(resources=empty))))
    assert r.returncode == 1 and "empty" in r.stdout
    tbd = RESOURCES.replace("10 s", "TBD")
    r = run("check_sdd.py", str(sdd_tree(tmp_path / "b", validation=GOOD_VALIDATION, sdd=sdd_text(resources=tbd))))
    assert r.returncode == 1 and "TBD" in r.stdout


def test_sdd_resources_without_the_required_stages_fails(tmp_path):
    short = "\n".join(RESOURCES.splitlines()[:4]) + "\n"  # bake and tests only
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=sdd_text(resources=short))))
    assert r.returncode == 1 and "build" in r.stdout and "deploy" in r.stdout


def test_sdd_feature_without_validation_fails(tmp_path):
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=None)))
    assert r.returncode == 1 and "validation.md" in r.stdout


def test_sdd_validation_missing_a_requirement_fails(tmp_path):
    only_one = "\n".join(GOOD_VALIDATION.splitlines()[:3]) + "\n"
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=only_one)))
    assert r.returncode == 1 and "FX-002" in r.stdout and "no validation row" in r.stdout


def test_sdd_validation_listing_a_requirement_twice_or_an_unknown_one_fails(tmp_path):
    twice = GOOD_VALIDATION + "| FX-001 | again | `tests/test_x.py::test_a` |\n"
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=twice)))
    assert r.returncode == 1 and "FX-001" in r.stdout and "more than once" in r.stdout
    unknown = GOOD_VALIDATION + "| FX-009 | ghost | `tests/test_x.py::test_a` |\n"
    r = run("check_sdd.py", str(sdd_tree(tmp_path / "b", validation=unknown)))
    assert r.returncode == 1 and "FX-009" in r.stdout


def test_sdd_validation_gate_naming_a_renamed_test_fails(tmp_path):
    renamed = GOOD_VALIDATION.replace("test_b", "test_renamed")
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=renamed)))
    assert r.returncode == 1 and "test_renamed" in r.stdout


def test_sdd_validation_gate_without_a_named_test_or_an_empty_check_fails(tmp_path):
    no_test = GOOD_VALIDATION.replace("`tests/test_x.py::test_b`", "`tests/test_x.py`")
    r = run("check_sdd.py", str(sdd_tree(tmp_path, validation=no_test)))
    assert r.returncode == 1 and "names no test" in r.stdout
    empty = GOOD_VALIDATION.replace("a planted drift fails", " ")
    r = run("check_sdd.py", str(sdd_tree(tmp_path / "b", validation=empty)))
    assert r.returncode == 1 and "adversarial check" in r.stdout


def test_sdd_superseded_and_planned_features_need_no_validation(tmp_path):
    t = sdd_tree(tmp_path, validation=None)
    req = t / "docs" / "design" / "features" / "f" / "requirements.md"
    req.write_text("Status: superseded\n\n" + req.read_text(encoding="utf-8"), encoding="utf-8")
    assert run("check_sdd.py", str(t)).returncode == 0
    req.write_text(req.read_text(encoding="utf-8").replace("Status: superseded", "Status: planned"), encoding="utf-8")
    assert run("check_sdd.py", str(t)).returncode == 0


# ---------------------------------------------------------------- check_tech_matrix

TABLE_HEAD = "| component | package | version | use | alternative considered |\n|---|---|---|---|---|\n"


def tech_tree(tmp: Path, rows: list[tuple[str, str]]) -> Path:
    (tmp / "docs" / "design").mkdir(parents=True)
    (tmp / "data-pipeline").mkdir()
    (tmp / "frontend").mkdir()
    (tmp / "requirements-precompute.txt").write_text("-r data-pipeline/requirements.txt\n", encoding="utf-8")
    (tmp / "requirements-dev.txt").write_text(
        "# comment\npytest==9.1.1\ninterpret-core[required]==0.7.9\n"
        "riskvalidation @ git+https://example.org/r.git@v1.2.3\n", encoding="utf-8")
    (tmp / "data-pipeline" / "requirements.txt").write_text("numpy==2.4.6\n", encoding="utf-8")
    (tmp / "frontend" / "package.json").write_text(json.dumps(
        {"dependencies": {"react": "19.3.0", "katex": "^0.16.47"}, "devDependencies": {"vite": "8.3.2"}}),
        encoding="utf-8")
    (tmp / "frontend" / "package-lock.json").write_text(json.dumps({"packages": {
        "": {}, "node_modules/katex": {"version": "0.16.47"}, "node_modules/react": {"version": "19.3.0"},
        "node_modules/vite": {"version": "8.3.2"}}}), encoding="utf-8")
    table = TABLE_HEAD + "".join(f"| c | `{p}` | `{v}` | u | a |\n" for p, v in rows)
    (tmp / "docs" / "design" / "SDD.md").write_text(f"## Technology and versions\n\n{table}\n## Resources\n",
                                                     encoding="utf-8")
    return tmp


GOOD_ROWS = [("pytest", "9.1.1"), ("interpret-core", "0.7.9"), ("riskvalidation", "v1.2.3"), ("numpy", "2.4.6"),
             ("react", "19.3.0"), ("katex", "0.16.47"), ("vite", "8.3.2")]


def test_tech_matrix_clean_tree_passes(tmp_path):
    r = run("check_tech_matrix.py", str(tech_tree(tmp_path, GOOD_ROWS)))
    assert r.returncode == 0 and "7 pinned" in r.stdout, r.stdout


def test_tech_matrix_a_pin_changed_only_in_requirements_fails(tmp_path):
    t = tech_tree(tmp_path, GOOD_ROWS)
    (t / "data-pipeline" / "requirements.txt").write_text("numpy==2.5.0\n", encoding="utf-8")
    r = run("check_tech_matrix.py", str(t))
    assert r.returncode == 1 and "numpy" in r.stdout and "2.5.0" in r.stdout and "2.4.6" in r.stdout


def test_tech_matrix_a_pin_missing_from_the_table_and_a_row_not_pinned_fail(tmp_path):
    rows = [r for r in GOOD_ROWS if r[0] != "vite"] + [("scipy", "1.0.0")]
    r = run("check_tech_matrix.py", str(tech_tree(tmp_path, rows)))
    assert r.returncode == 1 and "vite" in r.stdout and "scipy" in r.stdout


def test_tech_matrix_an_unpinned_python_requirement_fails(tmp_path):
    t = tech_tree(tmp_path, GOOD_ROWS)
    (t / "data-pipeline" / "requirements.txt").write_text("numpy>=2.0\n", encoding="utf-8")
    r = run("check_tech_matrix.py", str(t))
    assert r.returncode == 1 and "numpy" in r.stdout and "unpinned" in r.stdout


def test_tech_matrix_a_range_the_lock_does_not_resolve_fails(tmp_path):
    t = tech_tree(tmp_path, GOOD_ROWS)
    (t / "frontend" / "package-lock.json").write_text(json.dumps({"packages": {"": {}}}), encoding="utf-8")
    r = run("check_tech_matrix.py", str(t))
    assert r.returncode == 1 and "katex" in r.stdout and "unpinned" in r.stdout


def test_tech_matrix_a_missing_table_fails(tmp_path):
    t = tech_tree(tmp_path, GOOD_ROWS)
    (t / "docs" / "design" / "SDD.md").write_text("## Resources\n", encoding="utf-8")
    r = run("check_tech_matrix.py", str(t))
    assert r.returncode == 1 and "Technology and versions" in r.stdout


# ---------------------------------------------------------------- check_contract_versions

CAT_HEAD = "| id | version | owner | schema file | example |\n|---|---|---|---|---|\n"
HIST_HEAD = "## History\n\n| contract | version | date | change | kind |\n|---|---|---|---|---|\n"
FIRST = "| a | 1.0.0 | 2026-10-11 | first | initial |\n| b | 1.0.0 | 2026-10-11 | first | initial |\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def versions_tree(tmp: Path, *, version: str = "1.0.0", lock_version: str = "1.0.0",
                  history: str | None = None) -> Path:
    (tmp / "docs" / "contracts" / "schemas").mkdir(parents=True)
    schema = tmp / "docs" / "contracts" / "schemas" / "a.schema.json"
    schema.write_bytes(b'{\n  "type": "object"\n}\n')
    (tmp / "docs" / "contracts" / "catalog.md").write_text(
        "## Contracts\n\n" + CAT_HEAD + f"| a | {version} | o | docs/contracts/schemas/a.schema.json | e |\n"
        "| b | 1.0.0 | o | - | e |\n\n" + (history if history is not None else HIST_HEAD + FIRST), encoding="utf-8")
    (tmp / "docs" / "contracts" / "versions.lock.json").write_text(json.dumps(
        {"a": {"version": lock_version, "schema": "docs/contracts/schemas/a.schema.json",
               "sha256": digest(schema)}}), encoding="utf-8")
    return tmp


def test_versions_clean_tree_passes_and_a_row_without_schema_is_skipped(tmp_path):
    r = run("check_contract_versions.py", "--repo-root", str(versions_tree(tmp_path)))
    assert r.returncode == 0, r.stdout


def test_versions_a_schema_edit_without_a_bump_fails(tmp_path):
    t = versions_tree(tmp_path)
    (t / "docs" / "contracts" / "schemas" / "a.schema.json").write_bytes(b'{"type": "string"}\n')
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "without a version bump" in r.stdout and "a" in r.stdout
    assert run("check_contract_versions.py", "--repo-root", str(t), "--update").returncode == 1  # bump first


def test_versions_a_bump_without_updating_the_lock_fails_and_update_fixes_it(tmp_path):
    t = versions_tree(tmp_path, version="1.1.0", history=HIST_HEAD + FIRST + "| a | 1.1.0 | 2026-10-12 | field | minor |\n")
    (t / "docs" / "contracts" / "schemas" / "a.schema.json").write_bytes(b'{"type": "string"}\n')
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "--update" in r.stdout
    u = run("check_contract_versions.py", "--repo-root", str(t), "--update")
    assert u.returncode == 0 and "1.0.0" in u.stdout and "1.1.0" in u.stdout, u.stdout
    assert run("check_contract_versions.py", "--repo-root", str(t)).returncode == 0


def test_versions_a_lowered_version_fails_and_update_refuses(tmp_path):
    t = versions_tree(tmp_path, version="1.0.0", lock_version="1.2.0")
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "goes down" in r.stdout
    assert run("check_contract_versions.py", "--repo-root", str(t), "--update").returncode == 1


def test_versions_a_row_without_a_history_entry_for_its_version_fails(tmp_path):
    t = versions_tree(tmp_path, history=HIST_HEAD + "| b | 1.0.0 | 2026-10-11 | first | initial |\n")
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "no History entry" in r.stdout and "a" in r.stdout


def test_versions_an_empty_or_missing_history_fails(tmp_path):
    r = run("check_contract_versions.py", "--repo-root", str(versions_tree(tmp_path, history=HIST_HEAD)))
    assert r.returncode == 1 and "History" in r.stdout
    r = run("check_contract_versions.py", "--repo-root", str(versions_tree(tmp_path / "b", history="")))
    assert r.returncode == 1 and "History" in r.stdout


def test_versions_a_missing_lock_says_to_run_update(tmp_path):
    t = versions_tree(tmp_path)
    (t / "docs" / "contracts" / "versions.lock.json").unlink()
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "--update" in r.stdout
    assert run("check_contract_versions.py", "--repo-root", str(t), "--update").returncode == 0


def test_versions_the_digest_ignores_line_endings(tmp_path):
    t = versions_tree(tmp_path)
    schema = t / "docs" / "contracts" / "schemas" / "a.schema.json"
    schema.write_bytes(schema.read_bytes().replace(b"\n", b"\r\n"))
    assert b"\r\n" in schema.read_bytes()
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 0, r.stdout


def test_versions_a_catalog_row_missing_from_the_lock_or_a_stale_lock_row_fails(tmp_path):
    t = versions_tree(tmp_path)
    lock = t / "docs" / "contracts" / "versions.lock.json"
    good = json.loads(lock.read_text(encoding="utf-8"))
    lock.write_text("{}", encoding="utf-8")
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "not in the lock" in r.stdout
    lock.write_text(json.dumps({**good, "ghost": {"version": "1.0.0", "schema": "x", "sha256": "0"}}), encoding="utf-8")
    r = run("check_contract_versions.py", "--repo-root", str(t))
    assert r.returncode == 1 and "ghost" in r.stdout


# ---------------------------------------------------------------- check_ci_budget (the one suite CI may run)

def ci_tree(tmp: Path, step: str) -> Path:
    (tmp / ".github" / "workflows").mkdir(parents=True)
    (tmp / "data-pipeline").mkdir()
    (tmp / ".github" / "workflows" / "ci.yml").write_text(
        "name: CI\non:\n  push:\n    branches: [main, develop]\nconcurrency:\n  group: g\njobs:\n  checks:\n"
        f"    runs-on: ubuntu-latest\n    timeout-minutes: 10\n    steps:\n      - name: s\n        run: {step}\n", encoding="utf-8")
    return tmp


def test_ci_budget_allows_the_adversarial_suite_and_nothing_else_of_pytest(tmp_path):
    ok = run("check_ci_budget.py", str(ci_tree(tmp_path / "a", "pip install pytest==9.1.1 && python -m pytest tests/adversarial -q")))
    assert ok.returncode == 0, ok.stdout
    bad = run("check_ci_budget.py", str(ci_tree(tmp_path / "b", "python -m pytest tests -q")))
    assert bad.returncode == 1 and "runs the test suite in CI" in bad.stdout
