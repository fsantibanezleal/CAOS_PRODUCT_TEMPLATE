#!/usr/bin/env python3
"""Run the product notebooks (CAOS_MANAGE ``conventions/product-notebooks.md`` section 7, template 0.10.000).

Executes each ``notebooks/<language>/<topic>/<notebook>.ipynb`` top to bottom in a fresh kernel (``nbclient``), with the
notebook's own folder as the working directory and a timeout per notebook, then strips the volatile metadata and writes the
notebook in place: the only writer of a notebook's outputs, so execution counts run 1, 2, 3 with no gap.

    python scripts/run_notebooks.py                 # every notebook, in place
    python scripts/run_notebooks.py --only notebooks/en/01-getting-started/01-first-run.ipynb
    python scripts/run_notebooks.py --check         # executes copies under a temporary folder, writes nothing, fails on any error

It runs in ``.venv-notebooks`` (``scripts/setup.sh --notebooks`` or ``scripts/setup.ps1 -Notebooks``, built from
``notebooks/requirements.txt``): started with another interpreter, it re-runs itself in that venv. A local release gate, never CI
(ADR-0074). A missing artifact fails the notebook with its path in the error; nothing stands in for it.
Exit 0 every notebook ran, 1 on any failure, 2 on a usage or environment problem.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
VENV = ROOT / ".venv-notebooks"
# the time one notebook may take, seconds (the example's longest runs in well under a minute)
TIMEOUT_SECONDS = 600
KERNEL = "python3"
KERNELSPEC = {"display_name": "Python 3", "language": "python", "name": "python3"}
KEEP_NOTEBOOK_METADATA = ("kernelspec", "language_info", "caos")


def venv_python() -> Path | None:
    for rel in ("Scripts/python.exe", "bin/python"):
        if (VENV / rel).is_file():
            return VENV / rel
    return None


def strip_volatile(nb: dict) -> dict:
    """The notebook without what changes from run to run or machine to machine: timings, widget state, the kernel's Python
    version and every cell metadata key but ``tags``. Cell ids stay (nbformat 4.5)."""
    nb = copy.deepcopy(nb)
    meta = nb.get("metadata", {})
    nb["metadata"] = {k: meta[k] for k in KEEP_NOTEBOOK_METADATA if k in meta}
    nb["metadata"]["kernelspec"] = dict(KERNELSPEC)
    nb["metadata"]["language_info"] = {"name": "python"}
    for cell in nb.get("cells", []):
        tags = cell.get("metadata", {}).get("tags")
        cell["metadata"] = {"tags": tags} if tags else {}
    return nb


def dump(nb: dict, path: Path) -> None:
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def discover(only: str | None) -> list[Path]:
    if only:
        p = (ROOT / only).resolve() if not Path(only).is_absolute() else Path(only).resolve()
        return [p] if p.is_file() else []
    return sorted(NOTEBOOKS.glob("*/*/*.ipynb"))


def warm_matplotlib() -> None:
    """Build matplotlib's font cache before the kernels start, so its one-off message never lands in a notebook's stderr."""
    try:
        import matplotlib
        matplotlib.use("agg")
        import matplotlib.pyplot as plt
        plt.figure().text(0, 0, "warm")
        plt.close("all")
    except ImportError:
        pass


def execute(src: Path, dest: Path) -> str | None:
    """Execute ``src`` in a fresh kernel in its own folder and write the clean result to ``dest``; None when it ran, else why not."""
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    nb = nbformat.read(src, as_version=4)
    for cell in nb.cells:  # a fresh run: no stale output or count survives
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
    client = NotebookClient(nb, timeout=TIMEOUT_SECONDS, kernel_name=KERNEL, resources={"metadata": {"path": str(src.parent)}},
                            allow_errors=False)
    try:
        client.execute()
    except CellExecutionError as e:
        return f"{type(e).__name__}: {str(e).strip().splitlines()[-1] if str(e).strip() else e}"
    except Exception as e:  # a dead kernel, a timeout: the run fails and says why
        return f"{type(e).__name__}: {e}"
    dump(strip_volatile(json.loads(nbformat.writes(nb))), dest)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(prog="run_notebooks", description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="execute copies under a temporary folder; write nothing, fail on any error")
    ap.add_argument("--only", metavar="PATH", help="run one notebook (a path from the repository root)")
    ap.add_argument("--inner", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    py = venv_python()
    if not a.inner and py is not None and Path(sys.prefix).resolve() != VENV.resolve():
        return subprocess.run([str(py), __file__, "--inner", *sys.argv[1:]], cwd=ROOT).returncode
    try:
        import nbclient  # noqa: F401
        import nbformat  # noqa: F401
    except ImportError:
        print("run_notebooks: nbclient and nbformat are not installed; build the notebook environment with "
              "scripts/setup.sh --notebooks (scripts/setup.ps1 -Notebooks on Windows)")
        return 2
    books = discover(a.only)
    if not books:
        print(f"run_notebooks: no notebook to run ({a.only or 'notebooks/*/*/*.ipynb'})")
        return 2
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")  # the kernels import data-pipeline/ by path: leave no cache behind
    warm_matplotlib()
    tmp_root = Path(tempfile.mkdtemp(prefix="run-notebooks-")) if a.check else None
    failures: list[str] = []
    try:
        for book in books:
            rel = book.relative_to(ROOT).as_posix()
            if tmp_root is not None:
                # a copy of the repository's inputs at the same relative depth: the notebook reads `../../../data/...`
                work = tmp_root / "repo"
                for item in ("data", "data-pipeline", "docs", "content", "notebooks"):
                    if (ROOT / item).exists() and not (work / item).exists():
                        shutil.copytree(ROOT / item, work / item, ignore=shutil.ignore_patterns("__pycache__", ".ipynb_checkpoints"))
                work.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / "VERSION", work / "VERSION")  # the pipeline package reads it at import
                src = work / rel
            else:
                src = book
            why = execute(src, (tmp_root / "out.ipynb") if tmp_root else src)
            if why is None:
                print(f"  ran   {rel}")
            else:
                failures.append(rel)
                print(f"  FAIL  {rel}: {why}")
    finally:
        if tmp_root is not None:
            shutil.rmtree(tmp_root, ignore_errors=True)
    if failures:
        print(f"run_notebooks: {len(failures)} of {len(books)} notebooks failed: {', '.join(failures)}")
        return 1
    print(f"run_notebooks: OK, {len(books)} notebooks executed top to bottom in fresh kernels" + (" (check, nothing written)" if a.check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
