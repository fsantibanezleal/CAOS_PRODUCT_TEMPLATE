#!/usr/bin/env python3
"""The technology matrix of the SDD is the pinned dependencies, exactly (ADR-0075, ADR-0080; rule 11 section 12).

The SDD section ``Technology and versions`` holds one table ``| component | package | version | use | alternative
considered |``. This guard reads every pin of ``requirements-precompute.txt``, ``requirements-dev.txt``,
``requirements-gpu.txt`` and ``data-pipeline/requirements.txt`` (each file that exists, ``-r`` includes followed) and
``frontend/package.json`` (dependencies and devDependencies) and fails, naming each one, when

- a pinned package is absent from the table, or its version differs;
- a table row names a package or a version that is not pinned;
- a requirement is not pinned (a range, a bare name) or a package.json range is not resolved by
  ``frontend/package-lock.json`` (the lock is the pin of a range: the table then holds the locked version).

Pins are compared by normalised name (lower case, ``_`` and ``.`` as ``-``, extras dropped) and version; a git pin
(``name @ git+https://...@ref``) is compared by its ref. Standard library only (CI installs nothing).

Usage: ``python scripts/check_tech_matrix.py [repo_root]``. Exit 0 consistent, 1 on any mismatch.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SDD = ROOT / "docs" / "design" / "SDD.md"
PY_FILES = ("requirements-precompute.txt", "requirements-dev.txt", "requirements-gpu.txt", "data-pipeline/requirements.txt")
HEAD = ["component", "package", "version", "use", "alternative considered"]
EXACT = re.compile(r"^\d+(\.\d+){0,2}([-+.][0-9A-Za-z.-]+)?$")
PIN = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*==\s*(?P<version>[^\s;#]+)")
GIT = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*@\s*git\+\S+?@(?P<ref>[^\s#;]+)")
NAME = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)")


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def python_pins(findings: list[str]) -> dict[str, tuple[str, str]]:
    """name -> (version, source) for every pin of the requirements files, ``-r`` includes followed."""
    pins: dict[str, tuple[str, str]] = {}
    seen: set[Path] = set()

    def read(path: Path) -> None:
        if path in seen or not path.is_file():
            return
        seen.add(path)
        rel = path.relative_to(ROOT).as_posix()
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split(" #")[0].strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("-r ", "--requirement ")):
                read((path.parent / line.split(None, 1)[1].strip()).resolve())
                continue
            if line.startswith("-"):
                continue
            m = PIN.match(line) or None
            g = GIT.match(line)
            if m:
                pins[norm(m["name"])] = (m["version"], rel)
            elif g:
                pins[norm(g["name"])] = (g["ref"], rel)
            else:
                n = NAME.match(line)
                findings.append(f"{rel}: {n['name'] if n else line!r} is unpinned (use name==version or a git ref): {line!r}")

    for rel in PY_FILES:
        read((ROOT / rel).resolve())
    return pins


def node_pins(findings: list[str]) -> dict[str, tuple[str, str]]:
    pkg = ROOT / "frontend" / "package.json"
    if not pkg.is_file():
        return {}
    doc = json.loads(pkg.read_text(encoding="utf-8"))
    lock_path = ROOT / "frontend" / "package-lock.json"
    locked: dict = json.loads(lock_path.read_text(encoding="utf-8")).get("packages", {}) if lock_path.is_file() else {}
    pins: dict[str, tuple[str, str]] = {}
    for section in ("dependencies", "devDependencies"):
        for name, spec in sorted(doc.get(section, {}).items()):
            if EXACT.match(spec):
                pins[norm(name)] = (spec, "frontend/package.json")
                continue
            resolved = locked.get(f"node_modules/{name}", {}).get("version")
            if resolved:
                pins[norm(name)] = (resolved, "frontend/package-lock.json")
            else:
                findings.append(f"frontend/package.json: {name} is unpinned ({spec!r}) and frontend/package-lock.json does not resolve it")
    return pins


def table_versions(findings: list[str]) -> dict[str, str] | None:
    if not SDD.is_file():
        findings.append(f"{SDD.relative_to(ROOT).as_posix()} is missing")
        return None
    text = SDD.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("## ") and "technology and versions" in ln.lower()), None)
    if start is None:
        findings.append("SDD.md has no section 'Technology and versions'")
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    table: dict[str, str] | None = None
    for line in lines[start + 1:end]:
        if not line.strip().startswith("|"):
            if table is not None:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if table is None:
            if [c.lower() for c in cells] == HEAD:
                table = {}
        elif not all(re.fullmatch(r":?-{3,}:?", c) for c in cells) and len(cells) >= 3:
            package = norm(cells[1].strip("`"))
            if package in table:
                findings.append(f"SDD.md technology table lists {package} more than once")
            table[package] = cells[2].strip("`").strip()
    if table is None:
        findings.append(f"SDD.md 'Technology and versions' has no table with the columns {' | '.join(HEAD)}")
    return table


def main() -> int:
    findings: list[str] = []
    pins = {**python_pins(findings), **node_pins(findings)}
    table = table_versions(findings)
    if table is not None:
        for name, (version, source) in sorted(pins.items()):
            if name not in table:
                findings.append(f"{name} {version} is pinned in {source} but absent from the SDD technology table")
            elif table[name] != version:
                findings.append(f"{name}: {source} pins {version}, the SDD technology table says {table[name]}")
        for name, version in sorted(table.items()):
            if name not in pins:
                findings.append(f"{name} {version} is in the SDD technology table but pinned in no requirements file or package.json")
    if findings:
        print("TECH MATRIX CHECK FAILED:")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"check_tech_matrix: OK, {len(pins)} pinned dependencies, all in the SDD technology table with the same version")
    return 0


if __name__ == "__main__":
    sys.exit(main())
