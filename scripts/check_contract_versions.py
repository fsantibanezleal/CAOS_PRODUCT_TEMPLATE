#!/usr/bin/env python3
"""Contract versions are a gate, not a habit (ADR-0080, rule 11 section 12): a schema cannot change without its
catalog version moving, and every version has a history entry.

``docs/contracts/versions.lock.json`` records, for every catalog row with a schema file,
``{"version", "schema", "sha256"}``, the digest taken over the schema with line endings normalised to LF (a Windows
checkout hashes as a Linux one). The check fails when

- the lock is absent (run ``--update``) or lacks a catalog row that has a schema file, or lists a row the catalog no
  longer has (a removed contract is a deliberate major step: ``--update``);
- a schema's digest differs from the lock while the catalog version equals the lock's (a change without a bump);
- the catalog version differs from the lock's (a bump not recorded: ``--update``), or is lower than it (a version
  never goes down);
- a catalog row has no entry for its current version in ``## History`` of the catalog
  (``| contract | version | date | change | kind |``, kind one of initial, major, minor, patch), or the table is empty.

``--update`` rewrites the lock from the catalog and the schemas after a deliberate bump and prints what changed; it
refuses (exit 1) when a version went down or a schema changed under the same version. A catalog row without a
schema file is skipped by the lock. Standard library only.

Usage: ``python scripts/check_contract_versions.py [--repo-root DIR] [--update]``. Exit 0 sound, 1 on any finding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_contracts import parse_catalog  # noqa: E402  (vendored; the catalog table is parsed the one way)

KINDS = {"initial", "major", "minor", "patch"}
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
HISTORY_HEAD = ["contract", "version", "date", "change", "kind"]
NONE = {"", "-", "n/a", "na", "none", "no"}


def semver(text: str) -> tuple[int, int, int] | None:
    m = SEMVER.match(text.strip())
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def history_rows(text: str) -> list[list[str]] | None:
    """Rows of the History table under ``## History``; None when the section or its table is absent."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^##\s+History\s*$", ln)), None)
    if start is None:
        return None
    rows: list[list[str]] | None = None
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.strip().startswith("|"):
            if rows is not None:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if rows is None:
            if [c.lower() for c in cells] == HISTORY_HEAD:
                rows = []
        elif not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            rows.append(cells)
    return rows


def catalog_rows(root: Path) -> tuple[list[dict[str, str]], str]:
    path = root / "docs" / "contracts" / "catalog.md"
    text = path.read_text(encoding="utf-8")
    parsed = parse_catalog(text)
    if parsed is None:
        raise SystemExit(f"{path.relative_to(root).as_posix()}: no contract catalog table found")
    return parsed[1], text


def build_lock(root: Path, rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    lock: dict[str, dict[str, str]] = {}
    for row in rows:
        schema = row.get("schema file", "").strip()
        if schema.lower() in NONE:
            continue
        path = root / schema
        lock[row["id"]] = {"version": row["version"].strip(), "schema": schema,
                           "sha256": digest(path) if path.is_file() else ""}
    return lock


def findings_for(root: Path, rows: list[dict[str, str]], text: str, lock: dict | None) -> list[str]:
    out: list[str] = []
    fresh = build_lock(root, rows)
    for cid, entry in sorted(fresh.items()):
        if not entry["sha256"]:
            out.append(f"{cid}: the schema file {entry['schema']} does not exist")
        if semver(entry["version"]) is None:
            out.append(f"{cid}: version {entry['version']!r} is not x.y.z")
    if lock is None:
        out.append("docs/contracts/versions.lock.json is missing; run: python scripts/check_contract_versions.py --update")
    else:
        for cid, entry in sorted(fresh.items()):
            old = lock.get(cid)
            if old is None:
                out.append(f"{cid}: a catalog row with a schema file, not in the lock; run --update")
                continue
            new_v, old_v = semver(entry["version"]), semver(old.get("version", ""))
            if new_v and old_v and new_v < old_v:
                out.append(f"{cid}: the version goes down, {old['version']} in the lock to {entry['version']} in the catalog")
            elif entry["version"] != old.get("version"):
                out.append(f"{cid}: the catalog says {entry['version']}, the lock {old.get('version')}; run --update after the bump")
            elif entry["sha256"] and entry["sha256"] != old.get("sha256"):
                out.append(f"{cid}: the schema {entry['schema']} changed without a version bump (still {entry['version']}); "
                           "bump the catalog version and add its History row, then --update")
            elif entry["schema"] != old.get("schema"):
                out.append(f"{cid}: the schema path is {entry['schema']}, the lock says {old.get('schema')}; run --update")
        for cid in sorted(set(lock) - set(fresh)):
            out.append(f"{cid}: in the lock but not a catalog row with a schema file; run --update (a removed contract is a major step)")
    hist = history_rows(text)
    if not hist:
        out.append("docs/contracts/catalog.md has no History table with rows (## History: contract | version | date | change | kind)")
    else:
        have: set[tuple[str, str]] = set()
        for cells in hist:
            if len(cells) != 5 or any(not c for c in cells):
                out.append(f"History row {cells[0] if cells else '(blank)'}: an empty cell")
                continue
            if cells[4].lower() not in KINDS:
                out.append(f"History {cells[0]} {cells[1]}: kind {cells[4]!r} is not one of {', '.join(sorted(KINDS))}")
            have.add((cells[0], cells[1]))
        for row in rows:
            if (row["id"], row["version"].strip()) not in have:
                out.append(f"{row['id']}: no History entry for its current version {row['version'].strip()}")
    return out


def update(root: Path, rows: list[dict[str, str]], lock_path: Path, lock: dict | None) -> int:
    fresh = build_lock(root, rows)
    refuse: list[str] = []
    changes: list[str] = []
    for cid, entry in sorted(fresh.items()):
        old = (lock or {}).get(cid)
        if old is None:
            changes.append(f"{cid}: added at {entry['version']}")
            continue
        new_v, old_v = semver(entry["version"]), semver(old.get("version", ""))
        if new_v and old_v and new_v < old_v:
            refuse.append(f"{cid}: the version goes down, {old['version']} to {entry['version']}")
        elif entry["version"] == old.get("version") and entry["sha256"] != old.get("sha256"):
            refuse.append(f"{cid}: the schema changed under the same version {entry['version']}; bump the catalog version first")
        elif entry["version"] != old.get("version"):
            changes.append(f"{cid}: version {old.get('version')} to {entry['version']}")
    for cid in sorted(set(lock or {}) - set(fresh)):
        changes.append(f"{cid}: removed from the lock")
    if refuse:
        print("UPDATE REFUSED:")
        for r in refuse:
            print(f"  - {r}")
        return 1
    lock_path.write_text(json.dumps(fresh, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"versions.lock.json written ({len(fresh)} contracts)" + ("".join(f"\n  {c}" for c in changes) if changes else "; nothing changed"))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--update", action="store_true", help="rewrite the lock after a deliberate bump")
    args = ap.parse_args(argv)
    root = args.repo_root.resolve()
    rows, text = catalog_rows(root)
    lock_path = root / "docs" / "contracts" / "versions.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else None
    if args.update:
        code = update(root, rows, lock_path, lock)
        if code:
            return code
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    findings = findings_for(root, rows, text, lock)
    if findings:
        print("CONTRACT VERSIONS CHECK FAILED:")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"check_contract_versions: OK, {len(rows)} contracts, {len(lock or {})} locked, every version has its History entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
