"""whatrobot taxonomy — tooling for the whatro.bot robot and component taxonomy.

Licence: MIT (tooling). The data under data/ and dist/ is CC BY 4.0.

This package is designed to run from a checkout (``pip install -e .``): it reads data/ and VERSION
from the repository root, which is the parent of this package directory.
"""
from pathlib import Path

__all__ = ["ROOT", "DATA", "DIST", "version"]

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"


def version() -> str:
    """Current taxonomy version from VERSION — read on every call so `release` sees the new value."""
    vf = ROOT / "VERSION"
    return vf.read_text(encoding="utf-8").strip() if vf.exists() else "unstable"
