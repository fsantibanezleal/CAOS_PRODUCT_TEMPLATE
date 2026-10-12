"""Adversarial validation of the guards (0.05.000): each test copies the repository's files into a temporary tree,
plants one defect, runs the real guard as a subprocess and asserts exit 1 (or 2 where the guard says so) with the
expected message; the clean copy of every guard exits 0. Nothing here edits the repository itself.

A guard that never ran cannot pass: the helper `guard` asserts the script exists in the copy, that the process
returned an exit code and that it printed, and the clean-copy tests assert the guard's own OK line."""
from __future__ import annotations

import json
import re
from pathlib import Path

from planting import edit, guard

CLEAN = {
    "check_sdd.py": "check_sdd: OK",
    "check_tech_matrix.py": "check_tech_matrix: OK",
    "check_contract_versions.py": "check_contract_versions: OK",
    "check_readiness.py": "readiness: current",
}
CATALOG = "docs/contracts/catalog.md"


def test_every_guard_passes_on_the_clean_copy(repo: Path) -> None:
    for script, marker in CLEAN.items():
        r = guard(repo, script, ok_marker=marker)
        assert r.returncode == 0 and marker in r.stdout, f"{script}: {r.stdout}"
    r = guard(repo, "check_contracts.py", CATALOG, "--repo-root", ".")
    assert r.returncode == 0 and "OK:" in r.stdout, r.stdout
    r = guard(repo, "check_skeleton.py", CATALOG)
    assert r.returncode == 0 and "every boundary is real" in r.stdout, r.stdout


# ---------------------------------------------------------------- check_sdd

def test_sdd_a_requirement_naming_a_test_that_does_not_exist(repo: Path) -> None:
    edit(repo, "docs/design/features/workbench/requirements.md", "test_a_value_outside_its_range_is_named",
         "test_that_was_never_written")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "EX-001" in r.stdout and "test_that_was_never_written" in r.stdout, r.stdout


def test_sdd_a_feature_without_a_validation_document(repo: Path) -> None:
    (repo / "docs/design/features/workbench/validation.md").unlink()
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "workbench" in r.stdout and "validation.md" in r.stdout, r.stdout


def test_sdd_a_validation_table_that_omits_one_requirement(repo: Path) -> None:
    path = repo / "docs/design/features/contracts/validation.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [ln for ln in lines if not ln.startswith("| CT-014 ")]
    assert len(kept) == len(lines) - 1
    path.write_text("".join(kept), encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "CT-014" in r.stdout and "no validation row" in r.stdout, r.stdout


def test_sdd_a_validation_gate_naming_a_renamed_test(repo: Path) -> None:
    edit(repo, "docs/design/features/contracts/validation.md", "test_state_stale", "test_state_stale_renamed")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "test_state_stale_renamed" in r.stdout, r.stdout


def test_sdd_a_research_basis_with_two_sources(repo: Path) -> None:
    sdd = repo / "docs/design/SDD.md"
    text = sdd.read_text(encoding="utf-8")
    start = text.index("## Research basis")
    end = text.index("## Sizing and contracts")
    two = ("## Research basis\n\n- Kermack and McKendrick 1927, https://doi.org/10.1098/rspa.1927.0118\n"
           "- Miller 2012, https://doi.org/10.1007/s11538-012-9749-6\n\nUNVERIFIED: none\n\n")
    sdd.write_text(text[:start] + two + text[end:], encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "cites 2 sources" in r.stdout, r.stdout


def test_sdd_a_resources_table_with_tbd(repo: Path) -> None:
    edit(repo, "docs/design/SDD.md", "| 0.2 s |", "| TBD |")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "TBD" in r.stdout and "Resources" in r.stdout, r.stdout


def _brief_part(text: str, name: str) -> tuple[int, int]:
    """Start and end offsets of the body of a level-3 part of the executive brief."""
    start = text.index(f"### {name}\n") + len(f"### {name}\n")
    nxt = [text.find(h, start) for h in ("\n### ", "\n## ")]
    return start, min(i for i in nxt if i != -1)


def _plant_brief(repo: Path, part: str, new_body: str) -> None:
    sdd = repo / "docs/design/SDD.md"
    text = sdd.read_text(encoding="utf-8")
    a, b = _brief_part(text, part)
    sdd.write_text(text[:a] + new_body + text[b:], encoding="utf-8")


def test_sdd_the_executive_brief_removed(repo: Path) -> None:
    sdd = repo / "docs/design/SDD.md"
    text = sdd.read_text(encoding="utf-8")
    sdd.write_text(text[:text.index("## Executive brief")] + text[text.index("## Research basis"):], encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "Executive brief" in r.stdout and "06_executive-brief.md" in r.stdout, r.stdout


def test_sdd_the_executive_brief_moved_to_the_end(repo: Path) -> None:
    sdd = repo / "docs/design/SDD.md"
    text = sdd.read_text(encoding="utf-8")
    a, b = text.index("## Executive brief"), text.index("## Research basis")
    sdd.write_text(text[:a] + text[b:] + "\n" + text[a:b], encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "right after" in r.stdout, r.stdout


def test_sdd_an_emptied_subsection_of_the_brief(repo: Path) -> None:
    _plant_brief(repo, "Positioning", "\n")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "Positioning is empty" in r.stdout, r.stdout


def test_sdd_the_initiative_stripped_of_its_numbers(repo: Path) -> None:
    _plant_brief(repo, "Initiative", "\nA unit owns a problem that is costing a significant amount, for many people.\n\n"
                 "- The delay is significant (source: https://doi.org/10.1007/BF00178324)\n\n")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "Initiative" in r.stdout and "quantified" in r.stdout, r.stdout


def test_sdd_the_outcomes_cut_to_two_rows(repo: Path) -> None:
    sdd = repo / "docs/design/SDD.md"
    lines = sdd.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith("| capability | business outcome | proof point |"))
    kept = lines[:start + 4] + lines[start + 6:]  # header, separator, two rows; the last two rows dropped
    sdd.write_text("".join(kept), encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "Outcomes" in r.stdout and "at least 3" in r.stdout, r.stdout


def test_sdd_a_proof_point_that_cites_a_file_that_is_not_there(repo: Path) -> None:
    edit(repo, "docs/design/SDD.md", "(source: data/derived/manifests/EX02_epidemic.json)", "(source: data/derived/manifests/ghost.json)")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "ghost.json" in r.stdout, r.stdout


def test_sdd_the_positioning_with_three_bullets(repo: Path) -> None:
    edit(repo, "docs/design/SDD.md", "- **Nothing to procure**: the owner has no budget line for a platform, and a static site needs none.\n", "")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "Positioning" in r.stdout and "exactly 4" in r.stdout, r.stdout


def test_sdd_the_credibility_with_two_questions(repo: Path) -> None:
    sdd = repo / "docs/design/SDD.md"
    text = sdd.read_text(encoding="utf-8")
    a = text.index("- Q: What does it cost to run?")
    b = text.index("Limits: the model")
    sdd.write_text(text[:a] + text[b:], encoding="utf-8")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "Credibility" in r.stdout and "at least 3" in r.stdout, r.stdout


def test_sdd_an_equation_planted_in_the_brief(repo: Path) -> None:
    edit(repo, "docs/design/SDD.md", "### Outcomes\n", "### Outcomes\n\nThe threshold is $1 - 1/R_0$.\n")
    r = guard(repo, "check_sdd.py")
    assert r.returncode == 1 and "equation" in r.stdout, r.stdout


# ---------------------------------------------------------------- check_contract_versions

def test_versions_a_schema_edited_without_a_version_bump(repo: Path) -> None:
    edit(repo, "docs/contracts/schemas/trace.schema.json", '"type"', '"type"  ')  # whitespace is a change
    r = guard(repo, "check_contract_versions.py")
    assert r.returncode == 1 and "trace" in r.stdout and "without a version bump" in r.stdout, r.stdout


def test_versions_a_version_lowered_in_the_catalog(repo: Path) -> None:
    edit(repo, CATALOG, "| case-index | 2.0.0 |", "| case-index | 1.9.0 |")
    r = guard(repo, "check_contract_versions.py")
    assert r.returncode == 1 and "case-index" in r.stdout and "goes down" in r.stdout, r.stdout


def test_versions_a_bump_without_a_history_row(repo: Path) -> None:
    edit(repo, CATALOG, "| trace | 1.0.0 | data-pipeline", "| trace | 1.1.0 | data-pipeline")
    r = guard(repo, "check_contract_versions.py")
    assert r.returncode == 1 and "no History entry for its current version 1.1.0" in r.stdout, r.stdout


def test_versions_the_digest_is_the_same_with_windows_line_endings(repo: Path) -> None:
    lock_before = (repo / "docs/contracts/versions.lock.json").read_bytes()
    for schema in (repo / "docs/contracts/schemas").glob("*.json"):
        schema.write_bytes(schema.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    r = guard(repo, "check_contract_versions.py", ok_marker="check_contract_versions: OK")
    assert r.returncode == 0, r.stdout  # a CRLF checkout hashes as the LF one the lock was built from
    r = guard(repo, "check_contract_versions.py", "--update")
    assert r.returncode == 0, r.stdout
    assert json.loads((repo / "docs/contracts/versions.lock.json").read_text(encoding="utf-8")) == json.loads(lock_before)


# ---------------------------------------------------------------- check_tech_matrix

def test_tech_matrix_a_pin_changed_in_requirements_but_not_in_the_sdd(repo: Path) -> None:
    edit(repo, "data-pipeline/requirements.txt", "numpy==2.4.6", "numpy==2.4.7")
    r = guard(repo, "check_tech_matrix.py")
    assert r.returncode == 1 and "numpy" in r.stdout and "2.4.7" in r.stdout and "2.4.6" in r.stdout, r.stdout


def test_tech_matrix_a_package_json_range_that_the_lock_does_not_resolve(repo: Path) -> None:
    edit(repo, "frontend/package-lock.json", '"node_modules/zustand"', '"node_modules/zustand-gone"')
    r = guard(repo, "check_tech_matrix.py")
    assert r.returncode == 1 and "zustand" in r.stdout and "unpinned" in r.stdout, r.stdout


# ---------------------------------------------------------------- check_contracts, check_readiness, check_skeleton

def test_contracts_a_model_slot_without_a_baseline_provider(repo: Path) -> None:
    edit(repo, CATALOG, "| baseline:data-pipeline/pipeline/model/baseline.py |",
         "| fixture:docs/contracts/examples/surrogate-model.json |")
    r = guard(repo, "check_contracts.py", CATALOG, "--repo-root", ".")
    assert r.returncode == 1 and "surrogate-model" in r.stdout and "baseline" in r.stdout, r.stdout


def test_contracts_a_schema_file_that_does_not_exist(repo: Path) -> None:
    edit(repo, CATALOG, "docs/contracts/schemas/trace.schema.json", "docs/contracts/schemas/gone.json")
    r = guard(repo, "check_contracts.py", CATALOG, "--repo-root", ".")
    assert r.returncode == 1 and "gone.json" in r.stdout, r.stdout


def test_readiness_a_catalog_edited_without_recomputing_the_document(repo: Path) -> None:
    edit(repo, CATALOG, "Phase 2 of contract-first parallel delivery", "Phase 2 of the contract-first parallel delivery")
    r = guard(repo, "check_readiness.py")
    assert r.returncode == 1 and "readiness: stale" in r.stdout and "python data-pipeline/run.py readiness" in r.stdout, r.stdout


def test_readiness_a_row_whose_status_the_rules_do_not_know(repo: Path) -> None:
    edit(repo, CATALOG, "tests/contracts/test_surrogate.py::test_swap_baseline_and_trained | real |",
         "tests/contracts/test_surrogate.py::test_swap_baseline_and_trained | done |")
    r = guard(repo, "check_readiness.py")
    assert r.returncode == 1 and "invalid catalog" in r.stdout and "done" in r.stdout, r.stdout


def test_skeleton_a_row_still_served_by_a_provider_is_listed_with_exit_2(repo: Path) -> None:
    """The CI step turns exit 2 into a failure on main (ci.yml, 'Rows still served by a provider')."""
    edit(repo, CATALOG, "tests/contracts/test_surrogate.py::test_swap_baseline_and_trained | real |",
         "tests/contracts/test_surrogate.py::test_swap_baseline_and_trained | active |")
    r = guard(repo, "check_skeleton.py", CATALOG)
    assert r.returncode == 2 and "surrogate-model" in r.stdout and "still served by a provider" in r.stdout, r.stdout
    ci = (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert re.search(r'-eq 2 \] && \[ "\$GITHUB_REF" = "refs/heads/main" \]', ci), "the CI step no longer fails main on exit 2"


def test_skeleton_a_status_the_vocabulary_does_not_know_is_malformed(repo: Path) -> None:
    edit(repo, CATALOG, "tests/contracts/test_surrogate.py::test_swap_baseline_and_trained | real |",
         "tests/contracts/test_surrogate.py::test_swap_baseline_and_trained | finished |")
    r = guard(repo, "check_skeleton.py", CATALOG)
    assert r.returncode == 1 and "finished" in r.stdout, r.stdout
