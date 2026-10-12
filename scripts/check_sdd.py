#!/usr/bin/env python3
"""T10, the SDD gate (ADR-0075, ADR-0078): a design document exists, and every requirement names a gate that is real.

Mirrored from CAOS_OreFlow's scripts/check_sdd.py (the validated reference, 2026-09-28), with two additions: the
ADR-fit section ADR-0078 requires in every SDD, and named TypeScript test cases (``file.test.ts::name``) checked the
way pytest cases are. Hardened after the adversarial reviews of the shell's port (PR #100) and of release 0.05.000
(CAOS_MANAGE ``wip/product-template/review-0-05-000-guards-2026-10-11.md``): a gate is a live test, never a name that
only appears in a string, a comment, another test's body or a skipped test.

Checks, in increasing strength:

0. **The executive brief** (CAOS_MANAGE ``conventions/problem-context-first.md``): a ``## Executive brief`` section right
   after ``Problem and non-goals`` with the parts Initiative, Outcomes, Positioning and Credibility in order, none
   empty; Initiative with a quantified statement and its source or assumption; Outcomes a three-row table whose proof
   points each hold a number and a source; Positioning exactly four bullets; Credibility three questions with
   answers and a ``Limits:`` line; no equation anywhere in it. Guide: ``docs/guides/06_executive-brief.md``.
1. ``docs/design/SDD.md`` has the twelve sections the convention requires, each a level-2 heading ``## <name>`` (an
   optional ``N.`` prefix) outside code fences and HTML comments, once, in order, each with a non-blank line under it;
   a research basis citing at least three distinct sources (a DOI counts once however it is written; example,
   localhost and ``.example`` hosts count for none) and a line starting ``UNVERIFIED:``; a resources table with a row
   for each of bake, tests, build and deploy and no empty or placeholder cell (``-``, ``?``, TODO, unknown, n/a, TBD).
2. Every requirement of a live feature (a row ``| ID | statement | gate |`` of
   ``docs/design/features/<slug>/requirements.md``) is stated with SHALL and has a gate cell. Every line that starts
   with ``|`` is a row: one that is indented, has fewer than three cells or has an empty or malformed ID is a finding,
   and every ID-like token of the file must be the ID of a row (a requirement written as a bullet is a finding). IDs are
   unique across all features. A folder of ``features/`` with no ``requirements.md`` is a finding.
3. **The named gate exists and can fail.** A gate cell names at least one file in backticks. Every named file is on
   disk inside the repository. ``path::name`` names a test in a Python test file (``tests/**`` or ``test_*.py``) or a
   TypeScript one (``*.test.ts``, ``*.test.tsx``, ``*.spec.*``): the name is a module-level ``def test_*`` (or a method of
   a ``class Test*``) found by parsing the file, or the whole first string argument of an ``it(``/``test(`` call that
   starts its line (not inside a string, a comment or another test's body), and it is not skipped (``@pytest.mark.skip``,
   ``skipif(True)``, ``pytestmark``, ``pytest.skip`` at module level or first in the body; ``.skip``, ``.todo``, ``xit``,
   ``{ skip: true }``). ``describe`` is not a gate. A plain path (no ``::``) is a gate only when it is a test file or a
   script under ``scripts/`` or ``frontend/scripts/``, never a document or data file.
4. **Every live feature has a ``validation.md``** (``| requirement | adversarial check | gate |``) listing each
   requirement ID exactly once, the check stated as what was planted or refuted, and the gate naming a real test that
   is adversarial: a test under ``tests/adversarial/``, or one whose name starts with ``adversarial`` (Python
   ``test_adversarial_...``, TypeScript ``it('adversarial: ...')``). Anything else proves the requirement passes, not that
   it can fail. A conditional skip (``skipif(<condition>)``, ``pytest.importorskip``) is a precondition, not a skip: such
   a test runs where its tool exists, and a requirement whose only gate needs a tool CI does not install is proven locally.

Check 3 is the one that matters: a requirement can name ``tests/test_nothing.py::test_imaginary`` and pass check 2
while verifying nothing, which is the failure the rule exists for.

``Status: planned`` and ``Status: superseded`` (one ``Status:`` line, live when absent) take a feature out of check 3 and
4 only when it is listed with a reason in ``docs/design/features/.status-allow`` (one ``<feature>: <reason>`` per line),
reviewed with the pull request that adds it; otherwise the status is a finding. A planned feature still names the file
each gate will have (counted apart, never reported as a real gate).

Standard library only; exit 1 on any finding. Usage: ``python scripts/check_sdd.py [repo_root]``.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SDD = ROOT / "docs" / "design" / "SDD.md"
FEATURES = ROOT / "docs" / "design" / "features"
ALLOW = FEATURES / ".status-allow"

SECTIONS = (
    "Problem and non-goals", "Research basis", "Sizing and contracts", "Technology and versions", "Resources", "Lanes",
    "Method ladder", "Cases", "Oracles", "Deploy driver", "Risks and kill criteria", "ADR fit",
)
BRIEF = "Executive brief"
BRIEF_PARTS = ("Initiative", "Outcomes", "Positioning", "Credibility")
GUIDE = "see docs/guides/06_executive-brief.md"
OUTCOMES_HEAD = ["capability", "business outcome", "proof point"]
FENCE = re.compile(r"^\s*(```+|~~~+)")
HEADING = re.compile(r"^(?P<hashes>#{2,3}) (?P<title>.+?)\s*$")
LEVEL2 = re.compile(r"^## (?:\d+[.)]?\s+)?(?P<title>.+?)\s*$")
NUMBER = re.compile(r"(?<![A-Za-z\d-])\d")
CITED = re.compile(r"^(?P<claim>.+?)\s*\((?P<kind>source|assumption):\s*(?P<value>.+)\)\s*[.]?\s*$")
BULLET = re.compile(r"^\s*[-*+] ")
VALUE_POINT = re.compile(r"^[-*+] \*\*[^*]+\*\*: \S.*$")
QUESTION = re.compile(r"^\s*- Q: \S")
ANSWER = re.compile(r"^\s+A: \S")
LIMITS = re.compile(r"^\s*Limits: \S")
MIN_SOURCES = 3
SOURCE = re.compile(r"\b10\.\d{4,9}/[^\s)>\]|]+|https?://[^\s)>\]|]+")
UNVERIFIED = re.compile(r"^\s*(?:[-*+]\s+)?(?:\*\*)?UNVERIFIED(?:\*\*)?\s*:", re.M)
PLACEHOLDER = {"-", "?", "todo", "unknown", "n/a", "na", "tbd", "..."}
RESOURCE_HEAD = ["stage", "memory", "disk", "time", "where it runs"]
RESOURCE_STAGES = ("bake", "tests", "build", "deploy")  # training is listed when the product trains
VALIDATION_HEAD = ["requirement", "adversarial check", "gate"]
ID_OK = re.compile(r"^[A-Z]{2,}-\d+[a-z]?$")
ID_TOKEN = re.compile(r"(?<![A-Za-z0-9-])(?!ADR-)[A-Z]{2,}-\d{3}[a-z]?\b")
TICKED = re.compile(r"`([^`]+)`")
FILE_LIKE = re.compile(r"^[\w./<>*-]+\.(py|ts|tsx|mjs|js|json|md|yml|yaml)(::[^`]+)?$")
STATUS_ANY = re.compile(r"^Status:\s*(\S*)\s*$", re.M | re.I)
HTML_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.S)
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".sh", ".ps1"}
PLACEHOLDER_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "example.com", "example.org", "example.net", "example.edu"}


# ---------------------------------------------------------------- markup

def strip_fences(text: str) -> str:
    """The text without fenced code blocks (``` and ~~~, closed by the same fence; an unclosed one runs to the end)."""
    out: list[str] = []
    fence: str | None = None
    for line in text.replace("\r\n", "\n").split("\n"):
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
            else:
                out.append(line)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip().lstrip(fence[0]).strip():
            fence = None
    return "\n".join(out)


def strip_comments(text: str) -> str:
    return HTML_COMMENT.sub("", text.replace("\r\n", "\n"))


def strip_markup(text: str) -> str:
    """The text a reader sees as structure: no fenced blocks and no HTML comments."""
    return strip_comments(strip_fences(text))


def section_text(text: str, name: str) -> str | None:
    """The body of the ``## <name>`` section of already-stripped text (up to the next ``## `` heading), None when absent."""
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if (m := LEVEL2.match(ln)) and m["title"].lower() == name.lower()), None)
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


# ---------------------------------------------------------------- the SDD sections

def canonical_source(raw: str) -> str | None:
    """One key per work: a DOI however written, or a URL; None for a placeholder (example, localhost, .example hosts)."""
    raw = raw.rstrip(".,;")
    m = re.match(r"^https?://(?:dx\.)?doi\.org/(10\..+)$", raw, re.I)
    if m:
        return "doi:" + m[1].lower()
    if raw.startswith("10."):
        return "doi:" + raw.lower()
    m = re.match(r"^https?://([^/:?#]+)(?::\d+)?([^?#]*)(\?[^#]*)?", raw, re.I)
    if not m:
        return None
    host = m[1].lower().removeprefix("www.")
    labels = host.split(".")
    if host in PLACEHOLDER_HOSTS or labels[-1] in {"example", "test", "invalid", "localhost"} or (len(labels) > 1 and labels[-2] == "example"):
        return None
    return host + m[2].rstrip("/") + (m[3] or "")


def research_findings(body: str) -> list[str]:
    out: list[str] = []
    keys = {k for m in SOURCE.finditer(body) if (k := canonical_source(m.group(0)))}
    if len(keys) < MIN_SOURCES:
        out.append(f"SDD.md research basis cites {len(keys)} sources (distinct DOIs 10.x/y or http URLs, none of them a "
                   f"placeholder); at least {MIN_SOURCES} are required")
    if not UNVERIFIED.search(body):
        out.append("SDD.md research basis has no line starting 'UNVERIFIED:' (write 'UNVERIFIED: none' when everything was confirmed)")
    return out


def stage_label(cell: str) -> list[str]:
    """The words naming a stage in the first cell of a resources row (before any parenthesis or colon)."""
    return re.findall(r"[a-z]+", re.split(r"[(:]", cell)[0].lower())


def resources_findings(body: str) -> list[str]:
    rows = table_rows(body, RESOURCE_HEAD)
    if rows is None:
        return [f"SDD.md Resources has no table with the columns {' | '.join(RESOURCE_HEAD)}"]
    out: list[str] = []
    for cells in rows:
        label = cells[0] or "(unnamed)"
        if len(cells) != len(RESOURCE_HEAD) or any(not c for c in cells):
            out.append(f"SDD.md Resources row {label!r} has an empty cell")
        for c in cells:
            if c.lower().strip("`*_ ") in PLACEHOLDER:
                out.append(f"SDD.md Resources row {label!r} has a placeholder cell {c!r}; write a measured or bounded value")
        if any(re.search(r"\bTBD\b", c, re.I) for c in cells):
            out.append(f"SDD.md Resources row {label!r} says TBD; write a measured or bounded value")
    named = [stage_label(c[0]) for c in rows if c]
    for stage in RESOURCE_STAGES:
        if not any(w and w[0] == stage and not set(w[1:]) & set(RESOURCE_STAGES) for w in named):
            out.append(f"SDD.md Resources has no row for the {stage} (one row per stage, its name first in the first cell)")
    return out


def sections_findings(text: str) -> list[str]:
    """The twelve sections: present once as ``## <name>`` outside fences and comments, in order, each with a body."""
    lines = strip_markup(text).split("\n")
    heads = [(i, m["title"].lower()) for i, ln in enumerate(lines) if (m := LEVEL2.match(ln))]
    titles = [t for _, t in heads]
    out: list[str] = []
    last = -1
    for name in SECTIONS:
        low = name.lower()
        if low not in titles:
            out.append(f"SDD.md has no section for {name!r} (a level-2 heading '## {name}' outside a code fence or a comment)")
            continue
        if titles.count(low) > 1:
            out.append(f"SDD.md has more than one section {name!r}")
        at = titles.index(low)
        start = heads[at][0]
        end = heads[at + 1][0] if at + 1 < len(heads) else len(lines)
        if not any(ln.strip() for ln in lines[start + 1:end]):
            out.append(f"SDD.md section {name!r} is empty")
        if at < last:
            out.append(f"SDD.md section {name!r} is out of order")
        last = max(last, at)
    return out


# ---------------------------------------------------------------- the executive brief

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
    text = strip_comments(text)
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
    out += sections_findings(text)
    stripped = strip_markup(text)
    research = section_text(stripped, "Research basis")
    resources = section_text(stripped, "Resources")
    if research is not None:
        out += research_findings(research)
    if resources is not None:
        out += resources_findings(resources)
    return out


# ---------------------------------------------------------------- is this name a test that can fail?

def _is_skip_mark(node: ast.AST) -> bool:
    """``pytest.mark.skip``, ``pytest.mark.skip(...)``, ``pytest.mark.skipif(True, ...)``, ``unittest.skip(...)``."""
    call = node.func if isinstance(node, ast.Call) else node
    chain: list[str] = []
    while isinstance(call, ast.Attribute):
        chain.append(call.attr)
        call = call.value
    if not isinstance(call, ast.Name):
        return False
    chain = [call.id, *reversed(chain)]
    if chain[-2:] == ["mark", "skip"] or (chain[0] == "unittest" and chain[-1] == "skip"):
        return True
    if chain[-2:] == ["mark", "skipif"] and isinstance(node, ast.Call):
        first = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "condition"), None)
        return isinstance(first, ast.Constant) and first.value is True
    return False


def _unconditional_skip_call(stmt: ast.stmt) -> bool:
    """A statement that is ``pytest.skip(...)`` (not ``importorskip``, which is a precondition)."""
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
        return False
    f = stmt.value.func
    return isinstance(f, ast.Attribute) and f.attr == "skip" and isinstance(f.value, ast.Name) and f.value.id == "pytest"


def _module_skipped(tree: ast.Module) -> bool:
    for stmt in tree.body:
        if _unconditional_skip_call(stmt):
            return True
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in stmt.targets):
            marks = stmt.value.elts if isinstance(stmt.value, (ast.List, ast.Tuple)) else [stmt.value]
            if any(_is_skip_mark(m) for m in marks):
                return True
    return False


def py_test_state(path: Path, name: str) -> str:
    """'ok', 'skipped', 'absent' or 'unparsable' for a test of a Python file (parsed, so a def in a string or a comment is no test)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError):
        return "unparsable"
    target = name.split("[")[0]
    if not target.startswith("test"):
        return "absent"  # a helper or a fixture of a test file is not a test
    candidates: list[tuple[ast.AST, bool]] = []  # (function, skipped by its class)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target:
            candidates.append((node, False))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            class_skipped = any(_is_skip_mark(d) for d in node.decorator_list)
            candidates += [(f, class_skipped) for f in node.body
                           if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name == target]
    if not candidates:
        return "absent"
    if _module_skipped(tree):
        return "skipped"
    for fn, class_skipped in candidates:
        if not class_skipped and not any(_is_skip_mark(d) for d in fn.decorator_list) and not any(_unconditional_skip_call(s) for s in fn.body):
            return "ok"
    return "skipped"


def mask_ts(src: str) -> tuple[str, dict[int, int]]:
    """TypeScript source with comments blanked and the content of string and template literals replaced by ``_``, plus
    {index of an opening quote: index of its closing quote}. What is left is code only."""
    out = list(src)
    spans: dict[int, int] = {}
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            out[i:j] = " " * (j - i)
            i = j
        elif c == "/" and src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out[i:j] = [ch if ch == "\n" else " " for ch in src[i:j]]
            i = j
        elif c in "'\"`":
            j = i + 1
            while j < n and src[j] != c and not (c != "`" and src[j] == "\n"):
                j += 2 if src[j] == "\\" else 1
            if j < n and src[j] == c:
                out[i + 1:j] = [ch if ch == "\n" else "_" for ch in src[i + 1:j]]
                spans[i] = j
                i = j + 1
            else:
                i = j
        else:
            i += 1
    return "".join(out), spans


def ts_test_state(path: Path, name: str) -> str:
    """'ok', 'skipped' or 'absent' for the test (an ``it(`` or ``test(`` call starting its line, outside strings, comments
    and other tests' bodies) whose whole first string argument is ``name``."""
    src = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    code, spans = mask_ts(src)
    call = re.compile(r"^[ \t]*(?P<x>x?)(?:test|it)(?P<mods>(?:\.\w+)*)\s*\(\s*(?P<q>['\"`])", re.M)
    found = "absent"
    inside_until = -1
    for m in call.finditer(code):
        if m.start() < inside_until:
            continue  # nested in the body of an earlier test
        open_paren = code.index("(", m.start("x"))
        depth, k = 0, open_paren
        while k < len(code):
            depth += (code[k] == "(") - (code[k] == ")")
            k += 1
            if depth == 0:
                break
        inside_until = k
        q = m.start("q")
        end = spans.get(q)
        if end is None or re.sub(r"\\(['\"`\\])", r"\1", src[q + 1:end]) != name:
            continue
        options = re.match(r"\s*,\s*\{([^}]*)\}", code[end + 1:])
        mods = [x for x in m["mods"].split(".") if x]
        if m["x"] or {"skip", "todo", "skipIf"} & set(mods) or (options and re.search(r"\b(?:skip|todo)\s*:\s*(?!false\b)(?=\S)", options.group(1))):
            found = "skipped"
            continue
        return "ok"
    return found


def test_state(path: Path, name: str) -> str:
    return py_test_state(path, name) if path.suffix == ".py" else ts_test_state(path, name)


# ---------------------------------------------------------------- gates

def is_test_file(rel: str) -> bool:
    p = Path(rel)
    if p.suffix == ".py":
        return rel.startswith("tests/") or p.name.startswith("test_") or p.name.endswith("_test.py")
    if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs"}:
        return bool(re.search(r"\.(test|spec)\.[jt]sx?$|\.(test|spec)\.mjs$", p.name)) or rel.startswith("tests/")
    return False


def is_script(rel: str) -> bool:
    return rel.startswith(("scripts/", "frontend/scripts/")) and Path(rel).suffix in CODE_SUFFIXES


def adversarial_name(rel: str, name: str) -> bool:
    base = name.split("[")[0]
    return rel.startswith("tests/adversarial/") or base.startswith(("test_adversarial", "adversarial"))


def gate_findings(rel: str, rid: str, gate: str, *, adversarial: bool = False) -> list[str]:
    out: list[str] = []
    named = [t for t in TICKED.findall(gate) if FILE_LIKE.match(t)]
    if not named:
        return [f"{rel} {rid}: the gate names no file ({gate.strip()[:80]!r})"]
    for target in named:
        path_part, sep, test = target.partition("::")
        path = (ROOT / path_part).resolve()
        if not (path == ROOT or ROOT in path.parents):
            out.append(f"{rel} {rid}: names {path_part!r}, which resolves outside the repository")
            continue
        if not path.is_file():
            out.append(f"{rel} {rid}: names {path_part!r}, which does not exist")
            continue
        if not sep:
            if not (is_test_file(path_part) or is_script(path_part)):
                out.append(f"{rel} {rid}: {path_part} is neither a test file nor a script under scripts/ or frontend/scripts/; "
                           "a plain path gate cannot be a document or a data file")
            continue
        if path.suffix not in {".py", ".ts", ".tsx"} or not is_test_file(path_part):
            out.append(f"{rel} {rid}: {path_part}::{test} names a test in {path_part}, which is not a Python or TypeScript test file")
            continue
        state = test_state(path, test)
        if state == "skipped":
            out.append(f"{rel} {rid}: {path_part} test {test!r} is skipped or todo, so it cannot fail")
        elif state in {"absent", "unparsable"}:
            why = "cannot be parsed" if state == "unparsable" else f"defines no live test {test!r}"
            out.append(f"{rel} {rid}: {path_part} {why} (a test {test!r}: a def at module level or in a Test class, or an "
                       "it( or test( call that starts its line, with the whole name)")
        elif adversarial and not adversarial_name(path_part, test):
            out.append(f"{rel} {rid}: {path_part}::{test} is not adversarial; a validation gate is a test under tests/adversarial/ "
                       "or one named test_adversarial_... or it('adversarial: ...')")
    return out


def validation_findings(feature: Path, rel: str, ids: list[str]) -> list[str]:
    """validation.md of a live feature: every requirement ID exactly once, a stated check, an adversarial gate that is real."""
    vpath = feature / "validation.md"
    vrel = vpath.relative_to(ROOT).as_posix()
    if not vpath.is_file():
        return [f"{rel}: the feature has no validation.md ({vrel})"]
    rows = table_rows(strip_markup(vpath.read_text(encoding="utf-8")), VALIDATION_HEAD)
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
        out.extend(gate_findings(vrel, rid, cells[2], adversarial=True))
    for rid in ids:
        if seen.get(rid, 0) == 0:
            out.append(f"{vrel} {rid}: no validation row")
        elif seen[rid] > 1:
            out.append(f"{vrel} {rid}: listed more than once")
    return out


# ---------------------------------------------------------------- requirements files

def allowed() -> dict[str, str]:
    """``.status-allow``: feature -> reason (an entry with no reason is no entry)."""
    if not ALLOW.is_file():
        return {}
    out: dict[str, str] = {}
    for ln in ALLOW.read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.lstrip().startswith("#"):
            area, _, reason = ln.partition(":")
            if reason.strip():
                out[area.strip()] = reason.strip()
    return out


def requirement_rows(text: str) -> tuple[list[dict[str, str]], list[str]]:
    """Every table line outside a code fence: the parsed ``| ID | statement | gate |`` rows and the malformed ones."""
    rows: list[dict[str, str]] = []
    bad: list[str] = []
    for line in strip_markup(text).split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|", 2)]
        if cells[0].lower() == "id" or (cells[0] and set(cells[0]) <= set("-: ")):
            continue
        if len(cells) < 3 or not cells[0] or line != line.lstrip() or not stripped.endswith("|"):
            bad.append(stripped[:80])
            continue
        rows.append({"id": cells[0], "statement": cells[1], "gate": cells[2]})
    return rows, bad


def main() -> int:
    findings = sdd_findings()
    live = planned = 0
    skipped: list[str] = []
    pending: list[str] = []
    seen: dict[str, str] = {}
    listed = allowed()
    folders = sorted(p for p in FEATURES.iterdir() if p.is_dir() and not p.name.startswith(".")) if FEATURES.is_dir() else []
    if not folders:
        findings.append("docs/design/features/ has no feature folder (<feature>/requirements.md)")
    for folder in folders:
        req = folder / "requirements.md"
        rel = req.relative_to(ROOT).as_posix()
        if not req.is_file():
            findings.append(f"{rel}: the feature folder {folder.name} has no requirements.md")
            continue
        text = req.read_text(encoding="utf-8")
        marks = [m.group(1).lower() for m in STATUS_ANY.finditer(strip_markup(text))]
        if len(marks) > 1:
            findings.append(f"{rel}: more than one Status line")
        state = marks[0] if marks else "live"
        if state not in {"live", "planned", "superseded"}:
            findings.append(f"{rel}: Status {state!r} is not live, planned or superseded")
            continue
        if state != "live" and folder.name not in listed:
            findings.append(f"{rel}: Status {state} takes the feature out of the gate; list it with its reason in "
                            "docs/design/features/.status-allow ('<feature>: <reason>')")
            continue
        if state == "superseded":
            skipped.append(folder.name)
            continue
        rows, bad = requirement_rows(text)
        findings.extend(f"{rel}: malformed requirement row (indented, fewer than three cells, no closing pipe or an empty ID): {b!r}" for b in bad)
        row_ids = {r["id"] for r in rows}
        for token in sorted(set(ID_TOKEN.findall(strip_markup(text))) - row_ids):
            findings.append(f"{rel}: {token} appears outside the ID column of a requirement row (a bullet, a split row or a lost row)")
        if not rows:
            findings.append(f"{rel}: no requirement rows")
        if state == "planned":
            pending.append(folder.name)
        for r in rows:
            rid = r["id"]
            if not ID_OK.match(rid):
                findings.append(f"{rel} {rid!r}: the ID does not match the form AB-001")
            elif rid in seen:
                findings.append(f"{rel} {rid}: duplicate ID (first in {seen[rid]})")
            else:
                seen[rid] = rel
            if "SHALL" not in r["statement"]:
                findings.append(f"{rel} {rid}: the statement has no SHALL")
            if state == "planned":
                planned += 1
                if not any(FILE_LIKE.match(t) for t in TICKED.findall(r["gate"])):
                    findings.append(f"{rel} {rid}: the planned gate names no file ({r['gate'].strip()[:80]!r})")
                continue
            live += 1
            if not r["gate"].strip():
                findings.append(f"{rel} {rid}: no gate")
                continue
            findings.extend(gate_findings(rel, rid, r["gate"]))
        if rows and state != "planned":
            findings.extend(validation_findings(folder, rel, [r["id"] for r in rows]))
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
