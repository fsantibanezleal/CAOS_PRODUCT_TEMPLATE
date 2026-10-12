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


BRIEF = """### Initiative

A regional health authority's epidemiology unit owns the question of when to act on a rising outbreak.

- A response that starts after day 24 comes after the peak of 27345 infected people (source: https://doi.org/10.1007/BF00178324)
- The cost of one avoidable closure week is 2 million USD (assumption: a round figure chosen only to show the format)

### Outcomes

| capability | business outcome | proof point |
|---|---|---|
| replay of a baked case | the planner sees the whole course before a meeting | 5 cases baked in 0.2 s (source: https://example.org/bake) |
| live re-run | a what-if answered while the room waits | 0.08 ms per run (assumption: the lane budget is far above any value measured here) |
| a labelled limit | no one mistakes the example for a forecast | 1 of 1 pages states it (source: docs/limits.md) |

### Positioning

- **Faster**: the planner waits no more than one meeting for the course of an outbreak.
- **Cheaper**: one workstation runs every case, so no cluster is bought.
- **Clearer**: each curve is labelled with its limits so a director can repeat it.
- **Checked**: every number traces to a committed artifact, so an auditor can re-run it.

### Credibility

- Q: Is this a forecast of our region?
  A: No. It is a teaching model with textbook assumptions and no real data; the limit is stated on every page.
- Q: How do we know the numbers are right?
  A: Each is read from a committed artifact and the live engine matches the baked one to 0.005 people.
- Q: What does it cost to run?
  A: One workstation and 0.2 s per bake; the measured resources are in the design document.

Limits: closed, homogeneous, deterministic population; the example carries no real data.
"""


def sdd_text(research: str = RESEARCH, resources: str = RESOURCES, skip: str = "", brief: str | None = BRIEF,
             brief_after: str = "Problem and non-goals") -> str:
    out = ["# SDD\n"]
    for name in SECTIONS:
        if name == skip:
            continue
        body = {"Research basis": research, "Resources": resources}.get(name, "text\n")
        out.append(f"## {name}\n\n{body}\n")
        if name == brief_after and brief is not None:
            out.append(f"## Executive brief\n\n{brief}\n")
    return "\n".join(out)


def sdd_tree(tmp: Path, *, validation: str | None, sdd: str | None = None) -> Path:
    (tmp / "docs" / "design" / "features" / "f").mkdir(parents=True)
    (tmp / "tests").mkdir()
    (tmp / "docs" / "limits.md").write_text("limits\n", encoding="utf-8")
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


# ---------------------------------------------------------------- check_sdd: the executive brief

GUIDE = "docs/guides/06_executive-brief.md"


def brief_run(tmp_path, brief: str | None = BRIEF, **kw):
    return run("check_sdd.py", str(sdd_tree(tmp_path, validation=GOOD_VALIDATION, sdd=sdd_text(brief=brief, **kw))))


def test_brief_a_complete_brief_passes(tmp_path):
    r = brief_run(tmp_path)
    assert r.returncode == 0, r.stdout


def test_brief_missing_section_fails_and_points_at_the_guide(tmp_path):
    r = brief_run(tmp_path, brief=None)
    assert r.returncode == 1 and "Executive brief" in r.stdout and GUIDE in r.stdout


def test_brief_at_the_end_of_the_sdd_fails(tmp_path):
    r = brief_run(tmp_path, brief_after="ADR fit")
    assert r.returncode == 1 and "right after" in r.stdout and "Problem and non-goals" in r.stdout


def test_brief_after_another_section_fails(tmp_path):
    r = brief_run(tmp_path, brief_after="Research basis")
    assert r.returncode == 1 and "right after" in r.stdout


def test_brief_four_empty_headings_fail(tmp_path):
    empty = "### Initiative\n\n### Outcomes\n\n### Positioning\n\n### Credibility\n"
    r = brief_run(tmp_path, brief=empty)
    assert r.returncode == 1
    for name in ("Initiative", "Outcomes", "Positioning", "Credibility"):
        assert f"{name} is empty" in r.stdout


def test_brief_a_missing_subsection_is_named(tmp_path):
    r = brief_run(tmp_path, brief=BRIEF.replace("### Positioning", "### Value"))
    assert r.returncode == 1 and "'Positioning'" in r.stdout


def test_brief_subsections_out_of_order_fail(tmp_path):
    swapped = BRIEF.replace("### Initiative", "### @@").replace("### Outcomes", "### Initiative").replace("### @@", "### Outcomes")
    r = brief_run(tmp_path, brief=swapped)
    assert r.returncode == 1 and "order" in r.stdout


def test_brief_a_heading_inside_a_code_fence_does_not_count(tmp_path):
    fenced = BRIEF.replace("### Credibility", "```\n### Credibility\n```")
    r = brief_run(tmp_path, brief=fenced)
    assert r.returncode == 1 and "'Credibility'" in r.stdout


def test_brief_crlf_and_trailing_spaces_in_headings_pass(tmp_path):
    text = sdd_text(brief=BRIEF.replace("### Initiative", "### Initiative   ")).replace("## Executive brief", "## Executive brief  ")
    tree = sdd_tree(tmp_path, validation=GOOD_VALIDATION)
    (tree / "docs/design/SDD.md").write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    r = run("check_sdd.py", str(tree))
    assert r.returncode == 0, r.stdout


def test_brief_initiative_without_a_quantified_statement_fails(tmp_path):
    bad = BRIEF.replace("after day 24 comes after the peak of 27345 infected people", "comes after the peak of many infected people")
    bad = bad.replace("2 million USD", "a significant amount")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "Initiative" in r.stdout and "quantified" in r.stdout


def test_brief_many_and_significant_and_several_are_not_numbers(tmp_path):
    for word in ("many", "significant", "several"):
        bad = BRIEF.replace("after day 24 comes after the peak of 27345 infected people", f"comes after the peak of {word} infected people")
        bad = bad.replace("2 million USD", f"{word} dollars")
        r = brief_run(tmp_path / word, brief=bad)
        assert r.returncode == 1 and "quantified" in r.stdout, word


def test_brief_a_source_path_not_in_the_repository_fails(tmp_path):
    ghost = BRIEF.replace("https://doi.org/10.1007/BF00178324", "docs/nowhere.md")
    r = brief_run(tmp_path, brief=ghost)
    assert r.returncode == 1 and "docs/nowhere.md" in r.stdout


def test_brief_a_source_path_in_the_repository_passes(tmp_path):
    ok = BRIEF.replace("https://doi.org/10.1007/BF00178324", "`docs/limits.md`")
    r = brief_run(tmp_path, brief=ok)
    assert r.returncode == 0, r.stdout


def test_brief_a_source_path_outside_the_repository_fails(tmp_path):
    out = BRIEF.replace("https://doi.org/10.1007/BF00178324", "../outside.md")
    (tmp_path / "outside.md").write_text("x\n", encoding="utf-8")
    r = brief_run(tmp_path / "repo", brief=out)
    assert r.returncode == 1 and "outside.md" in r.stdout


def test_brief_a_doi_source_passes(tmp_path):
    r = brief_run(tmp_path, brief=BRIEF.replace("https://doi.org/10.1007/BF00178324", "10.1007/BF00178324"))
    assert r.returncode == 0, r.stdout


def test_brief_an_assumption_needs_a_reason_of_five_words(tmp_path):
    short = BRIEF.replace("a round figure chosen only to show the format", "a round figure")
    r = brief_run(tmp_path, brief=short)
    assert r.returncode == 1 and "assumption" in r.stdout and "five words" in r.stdout


def test_brief_outcomes_with_two_rows_fail(tmp_path):
    two = "\n".join(ln for ln in BRIEF.splitlines() if "a labelled limit" not in ln) + "\n"
    r = brief_run(tmp_path, brief=two)
    assert r.returncode == 1 and "Outcomes" in r.stdout and "at least 3" in r.stdout


def test_brief_outcomes_proof_point_without_a_number_fails(tmp_path):
    bad = BRIEF.replace("5 cases baked in 0.2 s", "cases baked quickly")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "proof point" in r.stdout and "replay of a baked case" in r.stdout


def test_brief_outcomes_proof_point_without_a_source_fails(tmp_path):
    bad = BRIEF.replace(" (source: https://example.org/bake)", "")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "proof point" in r.stdout


def test_brief_outcomes_without_the_table_fails(tmp_path):
    bad = BRIEF.replace("| capability | business outcome | proof point |", "| a | b | c |")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "capability | business outcome | proof point" in r.stdout


def test_brief_positioning_with_three_or_five_bullets_fails(tmp_path):
    three = "\n".join(ln for ln in BRIEF.splitlines() if "**Checked**" not in ln) + "\n"
    r = brief_run(tmp_path, brief=three)
    assert r.returncode == 1 and "exactly 4" in r.stdout
    five = BRIEF.replace("### Credibility", "- **Fifth**: another problem it answers.\n\n### Credibility")
    r = brief_run(tmp_path / "b", brief=five)
    assert r.returncode == 1 and "exactly 4" in r.stdout


def test_brief_positioning_bullet_without_the_value_point_form_fails(tmp_path):
    bad = BRIEF.replace("- **Faster**: the planner", "- Faster, the planner")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "Positioning" in r.stdout and "value point" in r.stdout


def test_brief_credibility_with_two_questions_fails(tmp_path):
    cut = [ln for ln in BRIEF.splitlines() if "What does it cost to run" not in ln and "One workstation and 0.2 s per bake" not in ln]
    r = brief_run(tmp_path, brief="\n".join(cut) + "\n")
    assert r.returncode == 1 and "Credibility" in r.stdout and "at least 3" in r.stdout


def test_brief_a_question_without_an_answer_does_not_count(tmp_path):
    bad = BRIEF.replace("  A: One workstation and 0.2 s per bake; the measured resources are in the design document.", "")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "at least 3" in r.stdout


def test_brief_credibility_without_a_limits_line_fails(tmp_path):
    bad = BRIEF.replace("Limits:", "Caveat:")
    r = brief_run(tmp_path, brief=bad)
    assert r.returncode == 1 and "Limits:" in r.stdout


def test_brief_an_equation_in_the_brief_fails(tmp_path):
    plants = ("The rate is $R_0 = b / g$ here.", "The rate is \\(R_0\\) here.", "```math\nR_0 = b / g\n```")
    for n, plant in enumerate(plants):
        bad = BRIEF.replace("### Outcomes", plant + "\n\n### Outcomes", 1)
        r = brief_run(tmp_path / str(n), brief=bad)
        assert r.returncode == 1 and "equation" in r.stdout, plant


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
