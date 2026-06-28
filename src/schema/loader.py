from pathlib import Path

import yaml

from src.schema.models import Schema

_PROMPT_DIR = Path(__file__).resolve().parent.parent.parent / "schema"


def load_schema(name: str = "common.yaml") -> Schema:
    path = _PROMPT_DIR / name
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return Schema(**raw)


def load_prompt(name: str = "normalize.txt") -> str:
    path = _PROMPT_DIR / "prompts" / name
    with open(path, encoding="utf-8") as f:
        return f.read()
