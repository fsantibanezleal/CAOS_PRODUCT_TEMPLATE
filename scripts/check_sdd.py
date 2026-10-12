#!/usr/bin/env python3
"""T10, the SDD gate (ADR-0075, ADR-0078): a design document exists, and every requirement names a gate that is real.

Mirrored from CAOS_OreFlow's scripts/check_sdd.py (the validated reference, 2026-09-28), with two additions:
the ADR-fit section ADR-0078 requires in every SDD, and named TypeScript test cases (`file.test.ts::name`) checked
the way pytest cases are.

Checks, in increasing strength:

1. The repository has ``docs/design/SDD.md`` with the twelve sections the convention requires, a research basis
   with at least three sources and an UNVERIFIED list, and a resources table with no empty cell and no TBD.
2. Every requirement of a live feature (a row ``| ID | statement | gate |`` of
   ``docs/design/features/<slug>/requirements.md``) is stated with SHALL and has a gate cell.
3. **The named gate exists.** The gate cell names at least one file in backticks; every named file is on disk,
   and a named test (``path.py::test_name`` or ``path.test.ts::name``) is defined in it.

4. **Every live feature has a ``validation.md``** (``| requirement | adversarial check | gate |``) listing each
   requirement ID exactly once, the check stated as what was planted or refuted and the gate naming a real test
   (``path::name``), checked the way a requirement's gate is.

Check 3 is the one that matters: a requirement can name ``tests/test_nothing.py::test_imaginary`` and pass check 2
while verifying nothing, which is the failure the rule exists for.

``Status: superseded`` at the top of a requirements.md skips it (listed); ``Status: planned`` applies checks 1 and 2
and requires a file gate that need not exist yet (counted apart, never reported as a real gate).

Standard library only; exit 1 on any finding. Usage: ``python scripts/check_sdd.py [repo_root]``.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SDD = ROOT / "docs" / "design" / "SDD.md"
FEATURES = ROOT / "docs" / "design" / "features"

SECTIONS = (
    "Problem and non-goals", "Research basis", "Sizing and contracts", "Technology and versions", "Resources", "Lanes",
    "Method ladder", "Cases", "Oracles", "Deploy driver", "Risks and kill criteria", "ADR fit",
)
MIN_SOURCES = 3
SOURCE = re.compile(r"\b10\.\d{4,9}/[^\s)>\]]+|https?://[^\s)>\]]+")
RESOURCE_HEAD = ["stage", "memory", "disk", "time", "where it runs"]
RESOURCE_STAGES = ("bake", "tests", "build", "deploy")  # training is listed when the product trains
VALIDATION_HEAD = ["requirement", "adversarial check", "gate"]
ROW = re.compile(r"^\|\s*(?P<id>[A-Z]{2,}-\d+[a-z]?)\s*\|(?P<statement>.*?)\|(?P<gate>.*)\|\s*$")
TICKED = re.compile(r"`([^`]+)`")
FILE_LIKE = re.compile(r"^[\w./<>*-]+\.(py|ts|tsx|mjs|js|json|md|yml|yaml)(::[^`]+)?$")


def section_text(text: str, name: str) -> str | None:
    """The body of the ``## <name>`` section (up to the next ``## `` heading), None when there is no such section."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("## ") and name.lower() in ln.lstrip("#").strip().lower()), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start + 1:end])


def table_rows(text: str, head: list[str]) -> list[list[str]] | None:
    """The data rows of the first table whose header cells are ``head`` (case-insensitive), None if there is none."""
    rows: list[list[str]] | None = None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            if rows is not None:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if rows is None:
            if [c.lower() for c in cells] == head:
                rows = []
        elif not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            rows.append(cells)
    return rows


def research_findings(body: str) -> list[str]:
    out: list[str] = []
    sources = {m.group(0).rstrip(".,;") for m in SOURCE.finditer(body)}
    if len(sources) < MIN_SOURCES:
        out.append(f"SDD.md research basis cites {len(sources)} sources (a DOI 10.x/y or an http URL each); at least {MIN_SOURCES} are required")
    if "UNVERIFIED" not in body:
        out.append("SDD.md research basis has no UNVERIFIED list (write 'UNVERIFIED: none' when everything was confirmed)")
    return out


def resources_findings(body: str) -> list[str]:
    rows = table_rows(body, RESOURCE_HEAD)
    if rows is None:
        return [f"SDD.md Resources has no table with the columns {' | '.join(RESOURCE_HEAD)}"]
    out: list[str] = []
    for cells in rows:
        label = cells[0] or "(unnamed)"
        if len(cells) != len(RESOURCE_HEAD) or any(not c for c in cells):
            out.append(f"SDD.md Resources row {label!r} has an empty cell")
        if any(re.search(r"\bTBD\b", c, re.I) for c in cells):
            out.append(f"SDD.md Resources row {label!r} says TBD; write a measured or bounded value")
    stages = " ".join(c[0].lower() for c in rows if c)
    out += [f"SDD.md Resources has no row for the {stage}" for stage in RESOURCE_STAGES if stage not in stages]
    return out


def sdd_findings() -> list[str]:
    if not SDD.is_file():
        return [f"{SDD.relative_to(ROOT).as_posix()} is missing"]
    text = SDD.read_text(encoding="utf-8")
    out: list[str] = []
    for name in SECTIONS:
        body = section_text(text, name)
        if body is None:
            out.append(f"SDD.md has no section for {name!r}")
        elif name == "Research basis":
            out += research_findings(body)
        elif name == "Resources":
            out += resources_findings(body)
    return out


def test_defined(path: Path, name: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        return re.search(rf"^\s*def {re.escape(name.split('[')[0])}\(", text, re.M) is not None
    # TypeScript: it('name', ...) or test('name', ...), the name as written (a template literal prefix also counts)
    return re.search(rf"""\b(?:it|test|describe)\(\s*[`'"]{re.escape(name)}""", text) is not None


def gate_findings(rel: str, rid: str, gate: str) -> list[str]:
    out: list[str] = []
    named = [t for t in TICKED.findall(gate) if FILE_LIKE.match(t)]
    if not named:
        return [f"{rel} {rid}: the gate names no file ({gate.strip()[:80]!r})"]
    for target in named:
        path_part, _, test = target.partition("::")
        path = ROOT / path_part
        if not path.is_file():
            out.append(f"{rel} {rid}: names {path_part!r}, which does not exist")
            continue
        if test and path.suffix in {".py", ".ts", ".tsx"} and not test_defined(path, test):
            out.append(f"{rel} {rid}: {path_part} defines no test {test!r}")
    return out


def validation_findings(feature: Path, rel: str, ids: list[str]) -> list[str]:
    """validation.md of a live feature: every requirement ID exactly once, a stated check, a gate naming a real test."""
    vpath = feature / "validation.md"
    vrel = vpath.relative_to(ROOT).as_posix()
    if not vpath.is_file():
        return [f"{rel}: the feature has no validation.md ({vrel})"]
    rows = table_rows(vpath.read_text(encoding="utf-8"), VALIDATION_HEAD)
    if not rows:
        return [f"{vrel}: no table with the columns {' | '.join(VALIDATION_HEAD)} and rows"]
    out: list[str] = []
    seen: dict[str, int] = {}
    for cells in rows:
        rid = cells[0] if cells else ""
        seen[rid] = seen.get(rid, 0) + 1
        if rid not in ids:
            out.append(f"{vrel} {rid or '(blank)'}: not a requirement of this feature")
            continue
        if len(cells) != 3 or not cells[1].strip():
            out.append(f"{vrel} {rid}: the adversarial check is empty (state what was planted or refuted)")
            continue
        named = [t for t in TICKED.findall(cells[2]) if FILE_LIKE.match(t)]
        if not any("::" in t for t in named):
            out.append(f"{vrel} {rid}: the gate names no test (path::name), got {cells[2].strip()[:80]!r}")
            continue
        out.extend(gate_findings(vrel, rid, cells[2]))
    for rid in ids:
        if seen.get(rid, 0) == 0:
            out.append(f"{vrel} {rid}: no validation row")
        elif seen[rid] > 1:
            out.append(f"{vrel} {rid}: listed more than once")
    return out


def main() -> int:
    findings = sdd_findings()
    live = planned = 0
    skipped: list[str] = []
    pending: list[str] = []
    for req in sorted(FEATURES.glob("*/requirements.md")):
        rel = req.relative_to(ROOT).as_posix()
        text = req.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:6])
        if re.search(r"^Status:\s*superseded", head, re.M | re.I):
            skipped.append(req.parent.name)
            continue
        is_planned = bool(re.search(r"^Status:\s*planned", head, re.M | re.I))
        rows = [m for m in (ROW.match(line) for line in text.splitlines()) if m]
        if not rows:
            findings.append(f"{rel}: no requirement rows")
        if is_planned:
            pending.append(req.parent.name)
        for r in rows:
            if "SHALL" not in r["statement"]:
                findings.append(f"{rel} {r['id']}: the statement has no SHALL")
            if is_planned:
                planned += 1
                if not any(FILE_LIKE.match(t) for t in TICKED.findall(r["gate"])):
                    findings.append(f"{rel} {r['id']}: the planned gate names no file ({r['gate'].strip()[:80]!r})")
                continue
            live += 1
            if not r["gate"].strip():
                findings.append(f"{rel} {r['id']}: no gate")
                continue
            findings.extend(gate_findings(rel, r["id"], r["gate"]))
        if rows and not is_planned:
            findings.extend(validation_findings(req.parent, rel, [r["id"] for r in rows]))
    if findings:
        print("SDD CHECK FAILED:")
        for f in findings:
            print(f"  - {f}")
        return 1
    note = f"; superseded, not checked: {', '.join(skipped)}" if skipped else ""
    note += f"; {planned} planned requirements, gates not yet built: {', '.join(pending)}" if pending else ""
    print(f"check_sdd: OK, SDD.md complete, {live} live requirements with real gates{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
