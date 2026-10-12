"""ADR-0074 gate: CI and CD are cheap checks, run only for develop and main.

Fails when a workflow:
  - triggers on pull_request, on a schedule, or on a push to a branch other than
    develop/main/master;
  - has no top-level concurrency group;
  - has a job without timeout-minutes;
  - installs the training stack (precompute lane, pipeline requirements, torch & co.);
  - runs a training, pipeline, bake or benchmark entry point;
  - runs a test suite in a product repo (data-pipeline/ or requirements-precompute.txt):
    tests run locally; the only exception is one command, matched whole (`re.fullmatch`) after the backslash
    line continuations of a `run:` block are joined: `[pip install pytest==X.Y.Z && ]python -m pytest tests/adversarial[ -q]`
    (the guards' planted-defect suite). A second command, another path, `..`, a config or plugin option
    (`-c`, `--rootdir`, `-o`, `--override-ini`, `-p`, `--pyargs`) or a trailing comment is a test run and a finding.
    `pip install pytest==X.Y.Z` on a line of its own installs, it does not run a suite.
Stdlib only, so it runs before any install.
Usage: python scripts/check_ci_budget.py [repo_dir]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TRUNKS = {"develop", "main", "master"}
STACK_INSTALL = re.compile(
    r"download\.pytorch\.org|(pip|uv)\s+(pip\s+)?install\b[^\n#]*("
    r"requirements-precompute|requirements-gpu|data-pipeline/requirements|"
    r"\b(torch|torchvision|tensorflow|jax|jaxlib|transformers|lightning)\b)"
)
PIPELINE_RUN = re.compile(
    r"data-pipeline/\S+\.py|\brun_all\b|\bprecompute\b|\bbenchmark\b|stages\.train|--epochs\b|"
    r"\bcompare_bakes\b|\bbake\b|lab\.pipeline\b|-m\s+\S+\.pipeline\b"
)
PYTEST = re.compile(r"(^|[\s;&|(])(python3?\s+-m\s+)?pytest\b")
PIP_INSTALL = re.compile(r"\bpip3?\s+install\b[^;&|\n]*")
# the one suite CI may run: the adversarial plants of the guards (copies of the guards' inputs, standard library and
# pytest only); the product's own tests stay local. The whole command must be this, nothing before, after or between.
ADVERSARIAL = re.compile(r"(?:pip install pytest==\d+\.\d+\.\d+ && )?python -m pytest tests/adversarial(?: -q)?")


def runs_a_suite(cmd: str) -> bool:
    """True when the command starts pytest (a ``pip install pytest==X`` only installs it)."""
    return PYTEST.search(PIP_INSTALL.sub(" ", cmd)) is not None


def logical_lines(text: str) -> list[tuple[int, str]]:
    """The file's lines as (first line number, text), a line ending in a backslash joined with the next one."""
    out: list[tuple[int, str]] = []
    pending: tuple[int, str] | None = None
    for i, raw in enumerate(text.splitlines(), 1):
        first, line = (pending[0], pending[1] + " " + raw.strip()) if pending is not None else (i, raw)
        if line.rstrip().endswith("\\"):
            pending = (first, line.rstrip()[:-1].rstrip())
            continue
        pending = None
        out.append((first, line))
    if pending is not None:
        out.append(pending)
    return out


def check_workflow(path: Path, product: bool) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    name = path.relative_to(ROOT).as_posix()
    if re.search(r"^\s{2}pull_request(_target)?\s*:", text, re.MULTILINE):
        errs.append(f"{name}: pull_request trigger (ADR-0074 rule 4)")
    if re.search(r"^\s{2}schedule\s*:", text, re.MULTILINE):
        errs.append(f"{name}: schedule trigger (ADR-0074 rule 4)")
    for m in re.finditer(r"^\s{4}branches\s*:\s*\[([^\]]*)\]", text, re.MULTILINE):
        bad = {b.strip().strip("'\"") for b in m.group(1).split(",")} - TRUNKS - {""}
        if bad:
            errs.append(f"{name}: triggers on branches {sorted(bad)} (ADR-0074 rule 4)")
    if not re.search(r"^concurrency\s*:", text, re.MULTILINE):
        errs.append(f"{name}: no top-level concurrency group (ADR-0074 rule 5)")

    in_jobs, job, has_timeout, reusable = False, None, False, False
    jobs: list[tuple[str, bool, bool]] = []
    for line in text.splitlines():
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
            errs.append(f"{name}: job '{j}' has no timeout-minutes (ADR-0074 rule 5)")

    for i, line in logical_lines(text):
        s = line.strip()
        if s.startswith("#"):
            continue
        if STACK_INSTALL.search(line):
            errs.append(f"{name}:{i}: installs the training stack (ADR-0074 rule 2)")
            continue
        is_cmd = re.match(r"^\s*(-\s*)?run\s*:", line) or re.match(r"^\s{10,}\S", line)
        if not is_cmd:
            continue
        cmd = re.sub(r"^\s*(-\s*)?run\s*:\s*(\|[+-]?|>[+-]?)?", "", line).strip()
        if PIPELINE_RUN.search(line):
            errs.append(f"{name}:{i}: trains, bakes or runs the pipeline (ADR-0074 rule 1)")
        elif product and runs_a_suite(cmd) and not ADVERSARIAL.fullmatch(cmd):
            errs.append(f"{name}:{i}: runs the test suite in CI; tests run locally (ADR-0074 rule 3)")
    return errs


def main() -> int:
    # A product has an offline lane: data-pipeline/ or a precompute requirements file.
    product = (ROOT / "data-pipeline").is_dir() or (ROOT / "requirements-precompute.txt").is_file()
    errs: list[str] = []
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        errs += check_workflow(wf, product)
    for e in errs:
        print(f"::error::{e}")
    if not errs:
        print("ci budget: OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
