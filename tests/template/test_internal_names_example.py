"""The template's own example passes scripts/check_internal_names.py (template 0.14.000): its notebooks, indexes, README and
app strings name each method by what it is, never by its tier."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import check_internal_names as cin  # noqa: E402


def test_the_template_itself_passes():
    assert cin.check(ROOT) == [], cin.check(ROOT)
