#!/usr/bin/env python3
"""Every committed document against its schema file (docs/contracts/schemas/), with jsonschema alone.

Validates the documents of the bake (``data/derived``: the index, every manifest, the traces the manifests name, the
readiness), of the provider tree (``docs/contracts/fixtures/data/derived``), the contract examples
(``docs/contracts/examples``) and the released model bundle (``models/surrogate.json``). The generated TypeScript types
do not encode a ``pattern`` or a ``minItems``; this check does, so a schema change the committed documents violate
fails CI (review finding F5). It uses the registry of ``tests/contracts/contract_schemas.py`` (one place resolves a
schema reference), so it needs only ``jsonschema`` (4.26.0) and its ``referencing``, no pipeline and no numpy.

An absent manifest or artifact is not reported here: scripts/check_artifacts.py tells a declared-partial bake from an
undeclared absence. An absent index is an error (no inventory, nothing to validate).

Exit 0 and ``documents: N valid``; exit 1 listing each error. Usage: python scripts/check_documents.py [repo_root]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "tests" / "contracts"))

import contract_schemas as cs  # noqa: E402  (the schema registry, shared with the contract tests)

EXAMPLES = {"params-record.json": "params-record", "surrogate-model.json": "surrogate-model"}


def artifact_paths(manifest: dict) -> list[str]:
    """The artifact paths a manifest names, in either form of contract 2."""
    if isinstance(manifest.get("artifacts"), list):
        return [a["path"] for a in manifest["artifacts"] if isinstance(a, dict) and isinstance(a.get("path"), str)]
    single = manifest.get("artifact")
    return [single["path"]] if isinstance(single, dict) and isinstance(single.get("path"), str) else []


class Report:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.valid = 0
        self.errors: list[str] = []

    def label(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def check(self, path: Path, schema: str, component: bool = False) -> dict | None:
        """Validate the document at ``path``; return it when it is JSON (valid or not), None when it is not."""
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self.errors.append(f"{self.label(path)}: not readable as JSON ({exc})")
            return None
        found = cs.component_errors(schema, doc) if component else cs.errors(schema, doc)
        if found:
            self.errors += [f"{self.label(path)}: [{schema}] {e}" for e in found]
        else:
            self.valid += 1
        return doc if isinstance(doc, dict) else None


def check_tree(rep: Report, derived: Path) -> None:
    """The index, the manifests it lists, the artifacts they name and the readiness of one data/derived layout."""
    index_path = derived / "manifests" / "index.json"
    if not index_path.is_file():
        rep.errors.append(f"{rep.label(index_path)}: absent (no inventory to validate)")
        return
    index = rep.check(index_path, "case-index")
    for entry in (index or {}).get("cases", []):
        manifest_path = derived / str(entry.get("manifest_path", ""))
        if not manifest_path.is_file():
            continue
        manifest = rep.check(manifest_path, "case-manifest")
        for rel in artifact_paths(manifest or {}):
            artifact = derived / rel
            if artifact.is_file():
                rep.check(artifact, "trace")
    readiness = derived / "readiness.json"
    if readiness.is_file():
        rep.check(readiness, "readiness")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE
    rep = Report(root)
    check_tree(rep, root / "data" / "derived")
    fixtures = root / "docs" / "contracts" / "fixtures" / "data" / "derived"
    if fixtures.is_dir():
        check_tree(rep, fixtures)
    examples = root / "docs" / "contracts" / "examples"
    for name, schema in EXAMPLES.items():
        if (examples / name).is_file():
            rep.check(examples / name, schema)
    if (examples / "api-unavailable.json").is_file():
        rep.check(examples / "api-unavailable.json", "UnavailableBody", component=True)
    bundle = root / "models" / "surrogate.json"
    if bundle.is_file():
        rep.check(bundle, "surrogate-model")
    if rep.errors:
        print("documents: INVALID")
        for e in rep.errors:
            print(f"  - {e}")
        return 1
    print(f"documents: {rep.valid} valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
