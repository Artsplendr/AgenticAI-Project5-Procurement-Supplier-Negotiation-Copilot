from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from owpa.schemas.deal_state import DealState
from owpa.schemas.supplier_memory import SupplierMemory


def _read_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON file not found: {p.resolve()}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_suppliers_fixture(path: str | Path) -> List[SupplierMemory]:
    """
    Loads data/fixtures/suppliers.json
    Expected shape:
      { "suppliers": [ {SupplierMemory...}, ... ] }
    """
    raw = _read_json(path)
    suppliers_raw = raw.get("suppliers")
    if not isinstance(suppliers_raw, list):
        raise ValueError("Invalid suppliers fixture: expected top-level key 'suppliers' as a list")

    suppliers: List[SupplierMemory] = []
    for item in suppliers_raw:
        suppliers.append(SupplierMemory.model_validate(item))
    return suppliers


def build_supplier_index(suppliers: List[SupplierMemory]) -> Dict[str, SupplierMemory]:
    """
    Builds a case-insensitive index by supplier name and by supplier_id.
    """
    index: Dict[str, SupplierMemory] = {}
    for s in suppliers:
        index[s.supplier_id.strip().lower()] = s
        index[s.name.strip().lower()] = s
    return index


def get_supplier(
    suppliers: List[SupplierMemory],
    *,
    supplier_name: Optional[str] = None,
    supplier_id: Optional[str] = None,
) -> SupplierMemory:
    """
    Retrieve SupplierMemory by name or id (case-insensitive).
    Raises KeyError if not found.
    """
    if not supplier_name and not supplier_id:
        raise ValueError("Provide supplier_name or supplier_id")

    index = build_supplier_index(suppliers)

    if supplier_id:
        key = supplier_id.strip().lower()
        if key in index:
            return index[key]

    if supplier_name:
        key = supplier_name.strip().lower()
        if key in index:
            return index[key]

        # Slightly more forgiving: try substring match if exact not found
        matches = [s for s in suppliers if key in s.name.strip().lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise KeyError(
                f"Ambiguous supplier name '{supplier_name}'. Matches: {[m.name for m in matches]}"
            )

    raise KeyError(f"Supplier not found. name={supplier_name!r}, id={supplier_id!r}")


def load_playbook(path: str | Path) -> dict:
    """
    Loads playbook_wtg_ltsa.json and returns it as a dict.
    Keep playbook as dict for flexibility (MVP).
    """
    return _read_json(path)


def load_deal_state(path: str | Path) -> DealState:
    """
    Loads a DealState JSON (e.g., sample_deal_state.json).
    """
    raw = _read_json(path)
    return DealState.model_validate(raw)
