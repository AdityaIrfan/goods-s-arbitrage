from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd

from src.storage import silver

# urutan prioritas satuan "asli" yang paling mungkin jadi acuan harga di postingan
_UNIT_PRIORITY = ["karton", "jeriken", "botol", "pcs", "sachet", "liter", "kg"]
_AUTO_APPROVE_CONFIDENCE = {"high", "medium"}


def load_listings(validated: List[dict], subject: str, dedup_data: Optional[pd.DataFrame] = None) -> dict:
    ready_bronze_ids = None
    if dedup_data is not None:
        ready = dedup_data[(dedup_data["dedup_status"] == "ready") & (~dedup_data["is_duplicate"])]
        ready_bronze_ids = set(ready["id"])

    parsed_at = datetime.now(timezone.utc).isoformat()
    approved_rows = []
    pending_rows = []

    for item in validated:
        if ready_bronze_ids is not None and item["bronze_id"] not in ready_bronze_ids:
            continue

        row = _to_silver_row(item, subject, parsed_at)

        if item["parse_confidence"] in _AUTO_APPROVE_CONFIDENCE and not item["is_flagged"]:
            approved_rows.append(row)
        else:
            pending_row = dict(row)
            pending_row["review_status"] = "pending"
            pending_row["flag_reasons"] = item["flag_reasons"]
            pending_rows.append(pending_row)

    approved_filename = silver.save(subject, pd.DataFrame(approved_rows, columns=list(silver.silver_schema.columns.keys())))
    pending_filename = silver.save_pending(subject, pd.DataFrame(pending_rows, columns=list(silver.pending_schema.columns.keys())))

    return {
        "approved": len(approved_rows),
        "pending": len(pending_rows),
        "approved_file": approved_filename,
        "pending_file": pending_filename,
    }


def _to_silver_row(item: dict, subject: str, parsed_at: str) -> dict:
    units = item.get("unit-quantity", {})
    price_raw = item.get("price")
    price_per_liter = item.get("price_per_liter")

    return {
        "id": item["id"],
        "bronze_id": item["bronze_id"],
        "brand": item.get("brand"),
        "product_type": _product_type(subject, item.get("brand")),
        "price_raw": price_raw,
        "price_per_liter": price_per_liter,
        "unit_original": next((u for u in _UNIT_PRIORITY if u in units), None),
        # 1 unit_original setara berapa liter, dibalik dari price_raw / price_per_liter
        "quantity_per_unit": price_raw / price_per_liter if price_raw is not None and price_per_liter else None,
        "min_order": None,
        "city": item.get("location"),
        "province": None,
        "delivery_coverage": None,
        "parsed_at": parsed_at,
        "parse_confidence": item["parse_confidence"],
    }


def _product_type(subject: str, brand: Optional[str]) -> Optional[str]:
    if brand is None:
        return None
    return f"{subject} curah" if brand == "curah" else f"{subject} kemasan"
