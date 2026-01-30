from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


def use_llm() -> bool:
    v = os.getenv("USE_LLM", "true").strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def get_model_name() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _openai_client():
    # OpenAI Python SDK v1.x
    from openai import OpenAI  # type: ignore
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def llm_json(system: str, user: str, *, schema_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Minimal JSON-only LLM call.
    If USE_LLM=false, raises (caller should fallback).
    """
    if not use_llm():
        raise RuntimeError("USE_LLM=false")

    client = _openai_client()
    model = get_model_name()

    # We keep it robust by requesting strict JSON in plain text.
    # (Avoids depending on newer structured-output features.)
    prompt = user
    if schema_hint:
        prompt = f"{user}\n\nReturn ONLY valid JSON matching this schema:\n{schema_hint}"

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    text = resp.choices[0].message.content or "{}"

    # Best-effort: extract JSON object from response
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return {}
    return json.loads(m.group(0))
