from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    # Fixtures
    suppliers_fixture_path: Path
    playbook_path: Path
    # State store
    state_store_path: Path

    # Model
    openai_model: str

    # Rules
    require_snippet_for_numbers: bool


def _bool_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> AppConfig:
    suppliers_fixture_path = Path(
        os.getenv("SUPPLIERS_FIXTURE_PATH", "./data/fixtures/suppliers.json")
    )
    playbook_path = Path(os.getenv("PLAYBOOK_PATH", "./data/fixtures/playbook_wtg_ltsa.json"))
    state_store_path = Path(os.getenv("STATE_STORE_PATH", "./outputs/state_store.jsonl"))

    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    require_snippet_for_numbers = _bool_env("REQUIRE_CITATION_FOR_NUMBERS", True)

    return AppConfig(
        suppliers_fixture_path=suppliers_fixture_path,
        playbook_path=playbook_path,
        state_store_path=state_store_path,
        openai_model=openai_model,
        require_snippet_for_numbers=require_snippet_for_numbers,
    )
