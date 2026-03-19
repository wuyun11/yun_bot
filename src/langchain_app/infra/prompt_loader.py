from __future__ import annotations

from pathlib import Path


def load_prompt_relative_to(caller_file: str, relative_path: str) -> str:
    base_dir = Path(caller_file).resolve().parent
    prompt_path = (base_dir / relative_path).resolve()
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
