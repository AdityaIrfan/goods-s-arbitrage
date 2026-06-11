from typing import List

from src.config.loader import load_subject_config


def validate_listings(normalized: List[dict], subject: str) -> List[dict]:
    config = load_subject_config(subject)
    price_per_liter_min = config["validate"]["price_per_liter_min"]
    price_per_liter_max = config["validate"]["price_per_liter_max"]

    result = []
    for item in normalized:
        validated = dict(item)
        flag_reasons = []

        if validated.get("price") is None:
            flag_reasons.append("price_missing")

        # "satuan tidak dikenali" -> normalize gak bisa konversi unit ke liter
        if validated.get("unit_conversion_incomplete"):
            flag_reasons.append("unit_conversion_incomplete")

        price_per_liter = validated.get("price_per_liter")
        if price_per_liter is not None and not (price_per_liter_min <= price_per_liter <= price_per_liter_max):
            flag_reasons.append("price_per_liter_out_of_range")

        # lokasi gak bisa di-resolve -> tetap nullable, bukan flag

        validated["flag_reasons"] = flag_reasons
        validated["is_flagged"] = len(flag_reasons) > 0

        result.append(validated)

    return result
