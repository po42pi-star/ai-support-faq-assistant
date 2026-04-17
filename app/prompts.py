from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_system_prompt() -> str:
    p = ROOT / "docs" / "system_prompt.md"
    # fallback for running from workspace root
    if not p.exists():
        p = Path("docs") / "system_prompt.md"
    return p.read_text(encoding="utf-8")

