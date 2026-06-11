from typing import List

from src.config.loader import load_subject_config

_CONFIDENCE_LEVELS = ["low", "medium", "high"]


def normalize_listings(parsed: List[dict], subject: str) -> List[dict]:
    config = load_subject_config(subject)
    unit_conversion = config["normalize"]["unit_conversion"]

    result = []
    for item in parsed:
        normalized = dict(item)

        brand = normalized.get("brand")
        normalized["brand"] = brand.lower() if brand else None

        total_liter, incomplete = _convert_to_liter(normalized.get("unit-quantity", {}), unit_conversion)
        normalized["unit_conversion_incomplete"] = incomplete

        price = normalized.get("price")
        normalized["price_per_liter"] = price / total_liter if price is not None and total_liter else None

        if incomplete and "parse_confidence" in normalized:
            normalized["parse_confidence"] = _downgrade_confidence(normalized["parse_confidence"])

        result.append(normalized)

    return result


def _convert_to_liter(units: dict, unit_conversion: dict) -> tuple[float | None, bool]:
    if not units:
        return None, True

    # "liter" selalu jadi acuan ukuran kalau ada (mis. "2 liter" per botol/jeriken/curah).
    # Kalau gak ada, coba satuan lain yang punya konversi tetap di config (jeriken, kg, dll).
    base_unit = "liter" if "liter" in units else next((u for u in units if u in unit_conversion), None)
    if base_unit is None:
        return None, True

    base_liter = units[base_unit] * unit_conversion[base_unit]

    # Satuan lain (karton, botol, pcs, dll) dianggap pengali bertingkat,
    # misal {"liter": 2, "karton": 1, "botol": 6} -> 1 karton = 6 botol x 2 liter = 12 liter
    multiplier = 1.0
    for unit, qty in units.items():
        if unit != base_unit:
            multiplier *= qty

    return base_liter * multiplier, False


def _downgrade_confidence(confidence: str) -> str:
    idx = _CONFIDENCE_LEVELS.index(confidence)
    return _CONFIDENCE_LEVELS[max(idx - 1, 0)]
