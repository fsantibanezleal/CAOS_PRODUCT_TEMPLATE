#!/usr/bin/env python3
"""T10, the SDD gate (ADR-0075, ADR-0078): a design document exists, and every requirement names a gate that is real.

Mirrored from CAOS_OreFlow's scripts/check_sdd.py (the validated reference, 2026-09-28), with two additions:
the ADR-fit section ADR-0078 requires in every SDD, and named TypeScript test cases (`file.test.ts::name`) checked
the way pytest cases are.

Checks, in increasing strength:

0. **The executive brief** (CAOS_MANAGE ``conventions/problem-context-first.md``): a ``## Executive brief`` section right
   after ``Problem and non-goals`` with the parts Initiative, Outcomes, Positioning and Credibility in order, none
   empty; Initiative with a quantified statement and its source or assumption; Outcomes a three-row table whose proof
   points each hold a number and a source; Positioning exactly four bullets; Credibility three questions with
   answers and a ``Limits:`` line; no equation anywhere in it. Guide: ``docs/guides/06_executive-brief.md``.
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
BRIEF = "Executive brief"
BRIEF_PARTS = ("Initiative", "Outcomes", "Positioning", "Credibility")
GUIDE = "see docs/guides/06_executive-brief.md"
OUTCOMES_HEAD = ["capability", "business outcome", "proof point"]
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(?P<hashes>#{2,3}) (?P<title>.+?)\s*$")
NUMBER = re.compile(r"(?<![A-Za-z\d-])\d")
CITED = re.compile(r"^(?P<claim>.+?)\s*\((?P<kind>source|assumption):\s*(?P<value>.+)\)\s*[.]?\s*$")
BULLET = re.compile(r"^\s*[-*+] ")
VALUE_POINT = re.compile(r"^[-*+] \*\*[^*]+\*\*: \S.*$")
QUESTION = re.compile(r"^\s*- Q: \S")
ANSWER = re.compile(r"^\s+A: \S")
LIMITS = re.compile(r"^\s*Limits: \S")
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


def outline(text: str) -> list[tuple[int, str, int]]:
    """Level-2 and level-3 headings outside code fences, as (level, title, line index)."""
    out: list[tuple[int, str, int]] = []
    fenced = False
    for i, line in enumerate(text.splitlines()):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            m = HEADING.match(line)
            if m:
                out.append((len(m["hashes"]), m["title"].strip(), i))
    return out


def is_number(text: str) -> bool:
    """Digits standing alone (a unit may follow); the 0 of R0 or the 19 of COVID-19 is part of a name, not a number."""
    return NUMBER.search(text) is not None


def cited_findings(text: str, where: str) -> list[str]:
    """A quantified statement ``<claim with a number> (source: ...)`` or ``(assumption: <reason>)``: what is wrong."""
    m = CITED.search(text.strip().lstrip("-* ").strip())
    if m is None:
        return [f"{where} has no '(source: ...)' or '(assumption: ...)' after the claim"]
    out: list[str] = []
    if not is_number(m["claim"]):
        out.append(f"{where} states no number in its claim (many, significant and several are not numbers)")
    value = m["value"].strip()
    if m["kind"] == "assumption":
        if len(value.split()) < 5:
            out.append(f"{where} gives an assumption with fewer than five words of reason ({value!r})")
        return out
    for part in (p.strip().strip("`").strip() for p in value.split(";")):
        if re.match(r"10\.\d{4,9}/\S+$", part) or re.match(r"https?://\S+$", part):
            continue
        target = (ROOT / part.split("#")[0]).resolve()
        inside = target == ROOT or ROOT in target.parents
        if not part or not inside or not target.exists():
            out.append(f"{where} cites a source that is not a DOI, an http URL or a path in the repository ({part!r})")
    return out


def brief_findings(text: str) -> list[str]:
    """The executive brief (problem-context-first): its place, four parts in order, each with its own content."""
    lines = text.splitlines()
    heads = outline(text)
    twos = [(t, i) for lv, t, i in heads if lv == 2]
    names = [t.lower() for t, _ in twos]
    if BRIEF.lower() not in names:
        return [f"SDD.md has no section {BRIEF!r} (four parts, before any development): {GUIDE}"]
    pos = names.index(BRIEF.lower())
    out: list[str] = []
    if "problem and non-goals" in names and pos != names.index("problem and non-goals") + 1:
        out.append(f"SDD.md section {BRIEF!r} must come right after 'Problem and non-goals': {GUIDE}")
    start = twos[pos][1]
    end = twos[pos + 1][1] if pos + 1 < len(twos) else len(lines)
    body = lines[start + 1:end]
    parts = [(t, i) for lv, t, i in heads if lv == 3 and start < i < end]
    found = [t for t, _ in parts]
    missing = [p for p in BRIEF_PARTS if p not in found]
    out += [f"SDD.md {BRIEF!r} has no part {p!r}: {GUIDE}" for p in missing]
    if not missing and found != list(BRIEF_PARTS):
        out.append(f"SDD.md {BRIEF!r} parts must be in this order: {', '.join(BRIEF_PARTS)}: {GUIDE}")
    joined = "\n".join(body)
    if "$" in joined or "\\(" in joined or re.search(r"^\s*(```|~~~)\s*math\b", joined, re.M | re.I):
        out.append(f"SDD.md {BRIEF!r} holds an equation ($, \\( or a math block); the brief is business language: {GUIDE}")
    for n, (title, i) in enumerate(parts):
        if title not in BRIEF_PARTS:
            continue
        stop = parts[n + 1][1] if n + 1 < len(parts) else end
        part = lines[i + 1:stop]
        if not "".join(part).strip():
            out.append(f"SDD.md {BRIEF!r}: {title} is empty: {GUIDE}")
            continue
        out += PART_CHECKS[title](part)
    return out


def initiative_findings(part: list[str]) -> list[str]:
    out: list[str] = []
    good = 0
    for line in part:
        if not (line.lstrip().startswith("- ") and CITED.search(line)):
            continue
        problems = cited_findings(line, f"Initiative statement {line.strip()[2:60]!r}")
        out += problems
        good += not problems
    if good == 0:
        out.append(f"SDD.md Initiative has no quantified statement: a line '- <claim with a number> (source: <DOI, URL or path>)' or '(assumption: <reason>)': {GUIDE}")
    return out


def outcomes_findings(part: list[str]) -> list[str]:
    rows = table_rows("\n".join(part), OUTCOMES_HEAD)
    if rows is None:
        return [f"SDD.md Outcomes has no table with the columns {' | '.join(OUTCOMES_HEAD)}: {GUIDE}"]
    out: list[str] = []
    if len(rows) < 3:
        out.append(f"SDD.md Outcomes has {len(rows)} rows; at least 3 are required (capability, business outcome, proof point): {GUIDE}")
    for cells in rows:
        label = cells[0] if cells and cells[0] else "(unnamed)"
        if len(cells) != 3 or not all(cells):
            out.append(f"SDD.md Outcomes row {label!r} has an empty cell")
            continue
        out += cited_findings(cells[2], f"SDD.md Outcomes proof point of {label!r}")
    return out


def positioning_findings(part: list[str]) -> list[str]:
    bullets = [ln.strip() for ln in part if BULLET.match(ln)]
    out: list[str] = []
    if len(bullets) != 4:
        out.append(f"SDD.md Positioning has {len(bullets)} bullets; exactly 4 are required: {GUIDE}")
    for b in bullets:
        if not VALUE_POINT.match(b):
            out.append(f"SDD.md Positioning bullet {b[:50]!r} is not '- **<value point>**: <the problem of that owner it answers>'")
    return out


def credibility_findings(part: list[str]) -> list[str]:
    pairs = 0
    for n, line in enumerate(part):
        if not QUESTION.match(line):
            continue
        nxt = next((ln for ln in part[n + 1:] if ln.strip()), "")
        pairs += bool(ANSWER.match(nxt))
    out: list[str] = []
    if pairs < 3:
        out.append(f"SDD.md Credibility has {pairs} questions with answers; at least 3 are required ('- Q: ...' then '  A: ...'): {GUIDE}")
    if not any(LIMITS.match(ln) for ln in part):
        out.append(f"SDD.md Credibility has no 'Limits:' line: {GUIDE}")
    return out


PART_CHECKS = {"Initiative": initiative_findings, "Outcomes": outcomes_findings,
               "Positioning": positioning_findings, "Credibility": credibility_findings}


def sdd_findings() -> list[str]:
    if not SDD.is_file():
        return [f"{SDD.relative_to(ROOT).as_posix()} is missing"]
    text = SDD.read_text(encoding="utf-8")
    out: list[str] = brief_findings(text)
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
