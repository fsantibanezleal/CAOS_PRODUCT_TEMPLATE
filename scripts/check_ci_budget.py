"""ADR-0074 gate: CI and CD never train, never bake, and only run for develop and main.

Fails when a workflow:
  - triggers on pull_request, on a schedule, or on a push to a branch other than
    develop/main/master;
  - has no top-level concurrency group;
  - has a job without timeout-minutes;
  - runs a training, pipeline or bake entry point, or installs the precompute lane;
and when a test calls a training or bake entry point without @pytest.mark.bake.
Stdlib only, so it runs in the guards job before any install.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRUNKS = {"develop", "main", "master"}
FORBIDDEN_RUN = re.compile(
    r"requirements-precompute|data-pipeline/run\.py|\brun_all\b|\bprecompute\b|"
    r"stages\.train|--epochs\b|\bcompare_bakes\b|\bbake\b|lab\.pipeline\b|-m\s+\S+\.pipeline\b"
)
TRAIN_CALLS = {"precompute", "run_all", "train", "bake", "fit_model"}
TRAIN_KWARGS = {"epochs", "n_epochs", "max_epochs", "num_epochs"}


def check_workflow(path: Path) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    name = path.relative_to(ROOT).as_posix()
    if re.search(r"^\s{2}pull_request(_target)?\s*:", text, re.M):
        errs.append(f"{name}: pull_request trigger (ADR-0074 rule 4)")
    if re.search(r"^\s{2}schedule\s*:", text, re.M):
        errs.append(f"{name}: schedule trigger (ADR-0074 rule 4)")
    for m in re.finditer(r"^\s{4}branches\s*:\s*\[([^\]]*)\]", text, re.M):
        bad = {b.strip().strip("'\"") for b in m.group(1).split(",")} - TRUNKS - {""}
        if bad:
            errs.append(f"{name}: triggers on branches {sorted(bad)} (ADR-0074 rule 4)")
    if not re.search(r"^concurrency\s*:", text, re.M):
        errs.append(f"{name}: no top-level concurrency group (ADR-0074 rule 5)")
    in_jobs, job, has_timeout, reusable = False, None, False, False
    jobs: list[tuple[str, bool, bool]] = []
    for line in lines:
        if re.match(r"^jobs\s*:", line):
            in_jobs = True
            continue
        if in_jobs and re.match(r"^\S", line):
            in_jobs = False
        if not in_jobs:
            continue
        m = re.match(r"^  ([A-Za-z0-9_-]+)\s*:\s*$", line)
        if m:
            if job:
                jobs.append((job, has_timeout, reusable))
            job, has_timeout, reusable = m.group(1), False, False
        elif re.match(r"^    timeout-minutes\s*:", line):
            has_timeout = True
        elif re.match(r"^    uses\s*:", line):
            reusable = True
    if job:
        jobs.append((job, has_timeout, reusable))
    for j, t, r in jobs:
        if not t and not r:
            errs.append(f"{name}: job '{j}' has no timeout-minutes (ADR-0074 rule 6)")
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        if re.match(r"^\s*(-\s*)?run\s*:", line) or (i > 1 and re.match(r"^\s{10,}\S", line)):
            if FORBIDDEN_RUN.search(re.sub(r"not\s+bake", "", line)):
                errs.append(f"{name}:{i}: trains, bakes or installs the precompute lane (ADR-0074 rule 1/3)")
    return errs


def _has_bake_marker(decorators: list[ast.expr]) -> bool:
    return any("bake" in ast.unparse(d) for d in decorators)


def check_tests() -> list[str]:
    errs: list[str] = []
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module_marked = any(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in n.targets)
            and "bake" in ast.unparse(n.value)
            for n in tree.body
        )
        if module_marked:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test") or _has_bake_marker(node.decorator_list):
                continue
            for call in (c for c in ast.walk(node) if isinstance(c, ast.Call)):
                fn = call.func
                fname = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if fname in TRAIN_CALLS or any(k.arg in TRAIN_KWARGS for k in call.keywords):
                    rel = path.relative_to(ROOT).as_posix()
                    errs.append(f"{rel}:{node.lineno}: {node.name} calls {fname}() without "
                                "@pytest.mark.bake (ADR-0074 rule 2)")
                    break
    return errs


def main() -> int:
    errs: list[str] = []
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        errs += check_workflow(wf)
    if (ROOT / "tests").is_dir():
        errs += check_tests()
    for e in errs:
        print(f"::error::{e}")
    if not errs:
        print("ci budget: OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
