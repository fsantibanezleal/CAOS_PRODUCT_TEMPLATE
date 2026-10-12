"""Helpers of the adversarial tests: run a guard as a subprocess and plant one defect in a copy."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def guard(repo: Path, script: str, *args: str, ok_marker: str | None = None) -> subprocess.CompletedProcess:
    """Run ``repo/scripts/<script>`` as the CI does and prove that it ran: the script file exists, and the process
    returned an exit code and wrote to stdout. A guard that was never run cannot satisfy a caller's assertions."""
    path = repo / "scripts" / script
    assert path.is_file(), f"{script} is not in the copy"
    r = subprocess.run([sys.executable, str(path), *args], capture_output=True, encoding="utf-8", errors="replace", cwd=repo, timeout=120)
    assert isinstance(r.returncode, int) and r.stdout.strip(), f"{script} printed nothing (exit {r.returncode}): {r.stderr[:300]}"
    if ok_marker is not None and r.returncode == 0:
        assert ok_marker in r.stdout, r.stdout
    return r


def edit(repo: Path, rel: str, old: str, new: str, *, count: int = 1) -> None:
    """Replace ``old`` by ``new`` in a file of the copy; fails when ``old`` is absent (a plant that plants nothing)."""
    path = repo / rel
    text = path.read_bytes().decode("utf-8")
    assert old in text, f"{rel} does not contain {old!r}: the plant would change nothing"
    path.write_bytes(text.replace(old, new, count).encode("utf-8"))
