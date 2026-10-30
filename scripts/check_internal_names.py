"""The internal names never reach a reader (template 0.14.000; CAOS_MANAGE ``conventions/method-tiers-and-manuscripts.md`` section 0).

Felipe, 2026-10-30: the tier names "are iternal names to refer to the app content and implementations ... that terms can never
reach the manuscripts or the app titles or sections". "Classical approach", "state of the art", "beyond the state of the art",
SOTA, "method tiers", their Spanish forms, and the claim ids ``BS-<n>`` and ``M-<n>`` sort a product's methods in its SDD, plans
and gates; a reader sees each method by its own name. This check fails a product that lets one through to:

- **notebooks** (``notebooks/**/*.ipynb``): the title (``caos.title``), every markdown cell, every code cell (comments and the text
  in code: titles, labels, legends), every printed output, and the file name; the References section keeps a cited work's own
  title as published;
- **the notebook indexes** (``notebooks/**/README.md``) and **the README** (``README.md``), References sections excepted;
- **the manuscripts** (``manuscripts/**``: ``.md``, ``.tex``, ``.txt``, ``.json``, ``.yaml``), bibliography files (``.bib``) and the
  bibliography of a source excepted;
- **``product.json``**: the titles of its ``manuscripts``;
- **the app's strings**: the string literals of ``frontend/src/**/*.ts`` and ``*.tsx`` (tests excepted), what the app shows.

The SDD, the plans, the code identifiers, ``product.json`` ``covers`` and the notebook metadata ``caos.methods`` and ``caos.beyond``
keep the names: they are where the names belong.

Usage: ``python scripts/check_internal_names.py [repo_root]``. Exit 0 clean, 1 on any finding (each ``path:line: the word``).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULE = "CAOS_MANAGE conventions/method-tiers-and-manuscripts.md section 0"
PHRASES = re.compile(
    r"state[- ]of[- ]the[- ]art|beyond[- ]the[- ]state|beyond[- ]sota|method[- ]tiers?\b|classical[- ](?:approach|tier)e?s?\b"
    r"|estado[- ]del[- ]arte|m[aá]s[- ]all[aá][- ]del[- ]estado|niveles?[- ]de[- ]m[eé]todo|enfoques?[- ]cl[aá]sicos?",
    re.IGNORECASE)
CASED = re.compile(r"\bSOTA\b|\bBS-\d+\b|\bM-\d+\b")
FILE_NAME = re.compile(r"state-of-the-art|^\d\d-beyond-|(?:^|-)sota(?:-|\.|$)", re.IGNORECASE)
REFERENCES = re.compile(r"^#{1,6}\s*(References|Referencias|Bibliography|Bibliografía)\s*$", re.IGNORECASE)
TEX_BIB = re.compile(r"\\begin\{thebibliography\}|\\bibliography\{|\\printbibliography")
# a comment or a string literal, whichever starts first: a "//" inside a string stays in the string, a quote inside a comment
# opens nothing
TOKEN = re.compile(r"(//[^\n]*|/\*.*?\*/)|('(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`)", re.DOTALL)
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".venv", "__pycache__"}


def words(text: str) -> list[str]:
    return [m.group(0) for m in PHRASES.finditer(text)] + [m.group(0) for m in CASED.finditer(text)]


def _lines(rel: str, text: str, start: int = 1) -> list[str]:
    out = []
    for n, line in enumerate(text.split("\n"), start=start):
        for w in words(line):
            out.append(f"{rel}:{n}: {w!r}")
    return out


def markdown_findings(rel: str, text: str) -> list[str]:
    """Every line of a markdown file outside a References section."""
    out, in_refs = [], False
    for n, line in enumerate(text.split("\n"), start=1):
        if line.startswith("#"):
            in_refs = bool(REFERENCES.match(line.strip()))
        if not in_refs:
            out += [f"{rel}:{n}: {w!r}" for w in words(line)]
    return out


def _output_text(cell: dict) -> str:
    parts = []
    for o in cell.get("outputs", []):
        if "text" in o:
            parts.append("".join(o["text"]) if isinstance(o["text"], list) else str(o["text"]))
        data = o.get("data", {})
        for key in ("text/plain", "text/markdown", "text/html"):
            if key in data:
                v = data[key]
                parts.append("".join(v) if isinstance(v, list) else str(v))
    return "\n".join(parts)


def notebook_findings(rel: str, nb: dict, name: str) -> list[str]:
    out = []
    if FILE_NAME.search(name):
        out.append(f"{rel}: the file name names a tier ({name})")
    title = str(nb.get("metadata", {}).get("caos", {}).get("title", ""))
    out += [f"{rel}: caos.title: {w!r}" for w in words(title)]
    for i, c in enumerate(nb.get("cells", [])):
        src = "".join(c.get("source", []))
        if c.get("cell_type") == "markdown":
            first = src.strip().split("\n", 1)[0].strip()
            if REFERENCES.match(first):
                continue
            out += [f"{rel}: cell {i}: {w!r}" for w in words(src)]
        elif c.get("cell_type") == "code":
            out += [f"{rel}: cell {i}: {w!r}" for w in words(src)]
            out += [f"{rel}: cell {i} output: {w!r}" for w in words(_output_text(c))]
    return out


def tex_findings(rel: str, text: str) -> list[str]:
    m = TEX_BIB.search(text)
    return _lines(rel, text[: m.start()] if m else text)


def app_findings(rel: str, text: str) -> list[str]:
    out = []
    for m in TOKEN.finditer(text):
        if m.group(2) is None:
            continue
        line = text.count("\n", 0, m.start()) + 1
        out += [f"{rel}:{line}: {w!r}" for w in words(m.group(2))]
    return out


def _files(root: Path, pattern: str):
    for p in sorted(root.glob(pattern)):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS):
            yield p


def check(root: Path) -> list[str]:
    root = Path(root)
    out: list[str] = []
    for p in _files(root, "notebooks/**/*.ipynb"):
        rel = p.relative_to(root).as_posix()
        try:
            nb = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            out.append(f"{rel}: unreadable notebook ({exc})")
            continue
        out += notebook_findings(rel, nb, p.name)
    for p in [*_files(root, "notebooks/**/README.md"), *([root / "README.md"] if (root / "README.md").is_file() else [])]:
        out += markdown_findings(p.relative_to(root).as_posix(), p.read_text(encoding="utf-8"))
    for p in _files(root, "manuscripts/**/*"):
        rel = p.relative_to(root).as_posix()
        if p.suffix in (".md", ".txt"):
            out += markdown_findings(rel, p.read_text(encoding="utf-8"))
        elif p.suffix == ".tex":
            out += tex_findings(rel, p.read_text(encoding="utf-8"))
        elif p.suffix in (".json", ".yaml", ".yml"):
            out += _lines(rel, p.read_text(encoding="utf-8"))
    product = root / "product.json"
    if product.is_file():
        try:
            doc = json.loads(product.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
        for k, m in enumerate(doc.get("manuscripts", []) if isinstance(doc.get("manuscripts"), list) else []):
            title = m.get("title", "") if isinstance(m, dict) else ""
            title = " ".join(title.values()) if isinstance(title, dict) else str(title)
            out += [f"product.json: manuscripts[{k}].title: {w!r}" for w in words(title)]
    for pattern in ("frontend/src/**/*.ts", "frontend/src/**/*.tsx"):
        for p in _files(root, pattern):
            if ".test." in p.name or p.name.endswith(".d.ts"):
                continue
            out += app_findings(p.relative_to(root).as_posix(), p.read_text(encoding="utf-8"))
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    findings = check(root)
    if findings:
        print(f"INTERNAL NAMES REACH A READER ({len(findings)}; {RULE}):")
        for f in findings:
            print(f"  - {f}")
        return 1
    print("check_internal_names: OK, no tier name or claim id in the notebooks, indexes, manuscripts, README or app strings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
