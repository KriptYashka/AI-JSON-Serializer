from configparser import ConfigParser
from dataclasses import dataclass, field
from os import environ
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.ini"


@dataclass(frozen=True)
class ModelProfile:
    name: str
    models: list[str]
    temperature: float
    max_tokens: int


def _load_ini() -> ConfigParser:
    cfg = ConfigParser()
    cfg.read(str(_CONFIG_PATH))
    return cfg


def _parse_profiles(cfg: ConfigParser) -> dict[str, ModelProfile]:
    profiles: dict[str, ModelProfile] = {}
    prefix = "profile."
    for section in cfg.sections():
        if not section.startswith(prefix):
            continue
        name = section[len(prefix):]
        raw_models = cfg.get(section, "models", fallback="")
        models = [m.strip() for m in raw_models.split(",") if m.strip()]
        profiles[name] = ModelProfile(
            name=name,
            models=models,
            temperature=float(cfg.get(section, "temperature", fallback="0.7")),
            max_tokens=int(cfg.get(section, "max_tokens", fallback="4096")),
        )
    return profiles


_cfg = _load_ini()
_openrouter = _cfg["openrouter"] if "openrouter" in _cfg else {}


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default_factory=lambda: environ.get("OPENROUTER_API_KEY", _openrouter.get("api_key", "")))
    base_url: str = _openrouter.get("base_url", "https://openrouter.ai/api/v1")
    timeout: int = int(_openrouter.get("timeout", "60"))
    default_profile: str = _openrouter.get("default_profile", "")
    cheap_profile: str = _openrouter.get("cheap_profile", "cheap")
    expensive_profile: str = _openrouter.get("expensive_profile", "expensive")
    profiles: dict[str, ModelProfile] = field(default_factory=lambda: _parse_profiles(_cfg))


settings = Settings()
